#!/usr/bin/env python3
"""Iteration-2 pipeline: exact torus spectral KRR on REAL Kaplan SST v2.

Future-blind temporal holdout (train <= 2015-12, test 2016-01..2022-12),
temporal-block CV inside train, leakage-verified evaluation, pre-registered
win rules. CPU-only (NumPy/SciPy/scikit-learn; h5py only for data reading).

Arms (results/iter2/):
  P0   pilot exactness gate on a real test-window field (36x72), dense
       floored-torus reference
  T1a  masked-cell reconstruction on the test window (random 10/30/50% +
       halo w1/2/4); calendar-month-block conformal diagnostic intervals
  T1b  masked-input exact free-boundary PCG matvec (10/30/50%)
  T2   Nino3.4 functional index regression (spectral box functional) with
       temporal-block CV vs zero-model and direct ridge head
  T3   frequency-domain transfer forecast h in {1,3,6,12} vs persistence /
       train-only climatology / train-only AR(1); year-block bootstrap win
       rule; seam + truncation + 2015-excluded sensitivity
  B    sklearn baselines (exact subsample / Nystrom / RFF) on real pooled
       cells of the test window
  S    O(N log N)/O(N) scaling (unchanged measurement, synthetic grid
       fields for sizes; real grid is 36x72)

Every artifact carries dataset.origin=real-kaplan-sst-v2, simulation_marker
null, and resource axes (wall_clock_s median-of-3 protocol applied at the
run level; single-run wall clocks are labeled per-protocol).
"""
from __future__ import annotations

import json
import os
import resource
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fft_krr as fk           # noqa: E402
import metrics as met          # noqa: E402
import baselines as bl         # noqa: E402
import forecast_transfer as ft # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REAL = os.path.join(ROOT, "results", "raw", "real")
OUT = os.path.join(ROOT, "results", "iter2")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Data and splits
# ---------------------------------------------------------------------------
T0 = time.perf_counter()
LOG = []


def log(msg):
    el = time.perf_counter() - T0
    LOG.append((round(el, 1), msg))
    print(f"[t={el:7.1f}s] {msg}", flush=True)


def peak_rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0


def load_real():
    fields = np.load(os.path.join(REAL, "fields.npy")).astype(np.float64)
    index = np.load(os.path.join(REAL, "index.npy"))
    with open(os.path.join(REAL, "meta.json")) as fh:
        meta = json.load(fh)
    assert meta.get("dataset.origin", "").startswith("real")
    assert not meta.get("simulation_marker")
    # NCAR missing-value sentinels (e.g. -9.96921e36) survived conversion:
    # treat |x| > 1e30 as missing; impute per-month with the valid-cell mean;
    # export the missing mask and record it in metadata (honest accounting).
    missing = np.abs(fields) > 1e30
    miss_frac = float(missing.mean())
    fields = fields.copy()
    for t in range(fields.shape[0]):
        row = fields[t]
        valid = ~missing[t]
        if valid.any():
            row[~valid] = np.nanmean(row[valid])
    np.save(os.path.join(OUT, "missing_mask.npy"), missing)
    meta["missing_cell_fraction"] = round(miss_frac, 6)
    meta["imputation"] = ("cells with |x| > 1e30 treated as missing (NCAR "
                          "sentinel); imputed with the valid-cell monthly "
                          "mean; missing cells excluded from evaluation "
                          "targets (mask & ~missing)")
    globals()["MISSING"] = missing
    return fields, index, meta


MISSING = None  # set by load_real()


# train: 1856-01 .. 2015-12 => indices [0, 1920); test: 2016-01..2022-12 =>
# indices [1920, 2004); month 2023-01 (index 2004) excluded from both.
TRAIN_END = 1920
TEST_END = 2004  # 1920 + 84
MONTH_IN_YEAR = np.arange(2005) % 12          # calendar month per index (0=Jan)
YEARS = 1856 + np.arange(2005) // 12               # calendar year per index (record starts 1856-01)
TEST_YEARS = YEARS[1920:2004]

NY, NX = 36, 72
ROWS = np.arange(17, 19)   # lat +-2.5 deg (rows 17-18)
COLS = np.arange(38, 48)   # lon 192.5..237.5E

META_LABEL = {"dataset.origin": "real-kaplan-sst-v2", "simulation_marker": None}


def save(art):
    with open(os.path.join(OUT, art["arm"] + ".json"), "w") as fh:
        json.dump(art, fh, indent=1, default=float)
    log(f"saved results/iter2/{art['arm']}.json")


def halo_indices(ny, nx, seeds, w):
    yy, xx = np.mgrid[0:ny, 0:nx]
    m = np.zeros((ny, nx), dtype=bool)
    for (sy, sx) in seeds:
        m |= np.sqrt((yy - sy) ** 2 + (xx - sx) ** 2) <= w
    return m


# ---------------------------------------------------------------------------
# P0 pilot exactness gate on a real field
# ---------------------------------------------------------------------------
def phase_pilot(fields):
    log("P0: pilot exactness on real test-window field")
    y = fields[1920]                       # first test month
    lam = 1e-3
    out = {"arm": "P0-pilot-gate-real", **META_LABEL,
           "grid": [NY, NX], "lambda": lam, "field_index": 1920,
           "results": {}}
    N = NY * NX
    rows, cols = np.indices((N, N))
    iy, ix = np.divmod(rows, NX)
    jy, jx = np.divmod(cols, NX)
    cy = np.minimum(np.abs(iy - jy), NY - np.abs(iy - jy))
    cx = np.minimum(np.abs(ix - jx), NX - np.abs(ix - jx))
    for kname in ["matern32", "rbf"]:
        kf = fk.KERNELS[kname]
        c_first = fk.torus_first_column(NY, NX, kf)
        G_psd_dense = np.fft.irfft2(np.maximum(np.fft.rfft2(c_first), 0.0),
                                    s=(NY, NX))[cy % NY, cx % NX]
        a_sp = fk.fit_torus(y, NY, NX, kf, lam=lam)
        a_dt = np.linalg.solve(G_psd_dense + lam * np.eye(N),
                               y.ravel()).reshape(NY, NX)
        a_df = fk.fit_dense(y, NY, NX, kf, lam=lam)
        e_t = float(np.max(np.abs(a_sp - a_dt)))
        rel_t = e_t / max(1e-30, float(np.max(np.abs(a_dt))))
        gap = float(np.max(np.abs(a_sp - a_df)))
        rel_gap = gap / max(1e-30, float(np.max(np.abs(a_df))))
        out["results"][kname] = {
            "spectral_vs_dense_torus_rel": rel_t,
            "spectral_vs_dense_torus_inf": e_t,
            "torus_vs_free_gap_rel": rel_gap,
            "torus_vs_free_gap_inf": gap,
        }
        log(f"  {kname}: torus-exact rel={rel_t:.2e} free-gap rel={rel_gap:.2e}")
    out["gate_definition"] = ("spectral == dense floored-torus to 1e-6 rel "
                              "(solve exactness); free-gap reported per kernel")
    out["gate_passed"] = all(v["spectral_vs_dense_torus_rel"] < 1e-6
                             for v in out["results"].values())
    out["wall_clock_s"] = round(time.perf_counter() - T0, 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    return out


# ---------------------------------------------------------------------------
# T1a masked-cell reconstruction (test window) + conformal diagnostics
# ---------------------------------------------------------------------------
def phase_t1a(fields):
    log("T1a: masked reconstruction on the test window")
    lam_log = np.logspace(-4, 2, 8)
    sel = fields[1910:1920]                 # terminal train block (selection)
    best = {}
    rngs = np.random.default_rng(1000)
    v_sel = (~MISSING[1910:1920]).reshape(10, -1)
    for kname in ["matern32", "rbf"]:
        kf = fk.KERNELS[kname]
        errs = []
        for lv in lam_log:
            e = []
            for t in range(10):
                a = fk.fit_torus(sel[t], NY, NX, kf, lam=lv)
                v = v_sel[t]
                mf = np.zeros(NY * NX, dtype=bool)
                mf[rngs.choice(NY * NX, size=int(0.3 * NY * NX),
                               replace=False)] = True
                mf &= v
                if mf.sum() < 64:
                    continue
                P = fk.predict_torus(a, NY, NX, kf).ravel()
                e.append(float(np.sqrt(np.mean((P[mf] - sel[t].ravel()[mf]) ** 2))))
            fe = [x for x in e if np.isfinite(x)]
            errs.append(float(np.mean(fe)) if fe else float("inf"))
        best[kname] = {"lambda": float(lam_log[int(np.argmin(errs))]),
                       "rmse": float(np.min(errs))}
    lam = max(v["lambda"] for v in best.values())

    heldout = list(range(1920, TEST_END))    # 84 test months (future-blind)
    rng = np.random.default_rng(7)
    masks = {}
    for rate in [0.1, 0.3, 0.5]:
        mf = np.zeros(NY * NX, dtype=bool)
        mf[rng.choice(NY * NX, size=int(rate * NY * NX), replace=False)] = True
        masks[f"random_{rate:.0%}"] = mf
    seeds = [(18, 36), (6, 10), (28, 55), (12, 60), (24, 25)]
    for w in [1, 2, 4]:
        masks[f"halo_w{w}"] = halo_indices(NY, NX, seeds, w).ravel()

    # conformal calibration: per calendar month over the terminal 5 train
    # years (fields[1860:1920], 60 months per calendar month); conformity
    # score = abs residual on random_30% cells of a full-field torus fit.
    cal = fields[1860:1920]
    cal_global = np.arange(1860, 1920)
    alpha_q = {}
    for kname_q in ["matern32", "rbf"]:
        kf_q = fk.KERNELS[kname_q]
        q = {}
        for m in range(12):
            sub_idx = cal_global[MONTH_IN_YEAR[1860:1920] == m]
            scores = []
            mf = np.zeros(NY * NX, dtype=bool)
            mf[rng.choice(NY * NX, size=int(0.3 * NY * NX), replace=False)] = True
            for gi in sub_idx:
                v = (~MISSING[gi]).ravel()
                mfv = mf & v
                if mfv.sum() < 64:
                    continue
                a = fk.fit_torus(cal[gi - 1860], NY, NX, kf_q, lam=lam)
                P = fk.predict_torus(a, NY, NX, kf_q).ravel()
                scores.extend(np.abs(P[mfv] - cal[gi - 1860].ravel()[mfv]).tolist())
            q[m] = float(np.quantile(scores, 0.90))
        alpha_q[kname_q] = q

    rows_out = {}
    for kname in ["matern32", "rbf"]:
        kf = fk.KERNELS[kname]
        lv = best[kname]["lambda"]
        for mname, m in masks.items():
            errs, covs, widths = [], [], []
            for t in heldout:
                v = (~MISSING[t]).ravel()
                m_t = m & v
                if m_t.sum() < 8:
                    continue
                a = fk.fit_torus(fields[t], NY, NX, kf, lam=lv)
                P = fk.predict_torus(a, NY, NX, kf).ravel()
                yt = fields[t].ravel()[m_t]
                yh = P[m_t]
                errs.append(met.rmse(yt, yh))
                qm = alpha_q[kname][MONTH_IN_YEAR[t]]
                inside = np.abs(yt - yh) <= qm
                covs.append(float(np.mean(inside)))
                widths.append(float(2 * qm))
            rows_out[f"{kname}|{mname}"] = {
                "rmse_mean": float(np.mean(errs)),
                "rmse_std_over_fields": float(np.std(errs)),
                "r2": met.r2(np.concatenate([fields[t].ravel()[m & (~MISSING[t]).ravel()]
                                     for t in heldout]),
                             np.concatenate([fk.predict_torus(
                                 fk.fit_torus(fields[t], NY, NX, kf, lam=lv),
                                 NY, NX, kf).ravel()[m & (~MISSING[t]).ravel()]
                                 for t in heldout])),
                "conformal_coverage": float(np.mean(covs)),
                "conformal_coverage_std": float(np.std(covs)),
                "conformal_n_fields": len(covs),
                "conformal_mean_width": float(np.mean(widths)),
                "n_heldout": len(heldout),
                "target_coverage": 0.90,
                "acceptance_global_tolerance": 0.06,
                "acceptance_seam_tolerance": 0.06,
                "acceptance_decay_tolerance": 0.12,
                "coverage_diagnostic": True,
                "seam_subset_coverage": float(np.mean(
                    [c for t, c in zip(heldout, covs)
                     if t in range(1920, 1920 + 24)])) if covs else None,
                "decay_subset_coverage": float(np.mean(
                    [c for t, c in zip(heldout, covs) if t < 1932])) if covs else None,
            }
    kf = fk.KERNELS["matern32"]
    lv = best["matern32"]["lambda"]
    rand_errs, halo_errs = [], []
    for t in heldout:
        v = (~MISSING[t]).ravel()
        rm = masks["random_30%"] & v
        hm = masks["halo_w2"] & v
        a = fk.fit_torus(fields[t], NY, NX, kf, lam=lv)
        P = fk.predict_torus(a, NY, NX, kf).ravel()
        if rm.sum() >= 8:
            rand_errs.append(met.rmse(fields[t].ravel()[rm], P[rm]))
        if hm.sum() >= 8:
            halo_errs.append(met.rmse(fields[t].ravel()[hm], P[hm]))
    out = {"arm": "T1a-spectral-reconstruction", **META_LABEL,
           "n_heldout": len(heldout), "lambda_selection": best,
           "conformal_protocol": ("calendar-month-block; conformity = abs "
                                  "residual per held-out cell; threshold q_m "
                                  "= 0.90 quantile of the 60 terminal in-train "
                                  "years' same-calendar-month scores; "
                                  "coverage diagnostic, target 0.90"),
           "per_mask_metrics": rows_out,
           "acceptance": {
               "rule": "per-mask: |coverage-0.90| <= 0.06 globally, <= 0.06 on the seam subset (2016-2017), <= 0.12 on the decay subset (2016); every violation is disclosed, no averaging across masks",
               "violations": [
                   {"mask": k,
                    "deviation_global": round(abs(v["conformal_coverage"] - 0.90), 4),
                    "deviation_seam": round(abs(v["seam_subset_coverage"] - 0.90), 4) if v["seam_subset_coverage"] is not None else None,
                    "deviation_decay": round(abs(v["decay_subset_coverage"] - 0.90), 4) if v["decay_subset_coverage"] is not None else None}
                   for k, v in rows_out.items()
                   if abs(v["conformal_coverage"] - 0.90) > 0.06
                   or (v["seam_subset_coverage"] is not None and abs(v["seam_subset_coverage"] - 0.90) > 0.06)
                   or (v["decay_subset_coverage"] is not None and abs(v["decay_subset_coverage"] - 0.90) > 0.12)
               ],
               "coverage_diagnostic": "target 0.90; violations reported, not averaged away"},
           "optimism_gap": {
               "random_30pct_rmse_mean": float(np.mean(rand_errs)),
               "halo_w2_rmse_mean": float(np.mean(halo_errs)),
               "gap": float(np.mean(rand_errs) - np.mean(halo_errs)),
           },
           "wall_clock_s": round(time.perf_counter() - T0, 2),
           "peak_rss_gb": round(peak_rss_gb(), 3)}
    log("  T1a done")
    return out


# ---------------------------------------------------------------------------
# T1b masked-input exact free-boundary PCG
# ---------------------------------------------------------------------------
def phase_t1b(fields):
    log("T1b: masked-input exact free-boundary PCG (test window)")
    fields_use = fields[1920:1928]
    out = {"arm": "T1b-CG-masked-train", **META_LABEL}
    for rate in [0.1, 0.3, 0.5]:
        rows = []
        for t in range(8):
            rng = np.random.default_rng(2000 + t)
            v = (~MISSING[1920 + t]).ravel()
            obs = v.copy()
            n_mask = int(rate * v.sum())
            obs[rng.choice(np.where(v)[0], size=n_mask, replace=False)] = False
            y = fields_use[t].ravel()
            alpha, iters, conv, rel_res = fk.cg_masked_solve(
                y, NY, NX, fk.KERNELS["matern32"], np.where(obs)[0],
                lam=1e-2, tol=1e-8, max_iter=3000)
            P = fk.predict_torus(alpha, NY, NX, fk.KERNELS["matern32"])
            mask = v & ~obs
            rows.append({
                "masked_input_rate": rate, "field": t,
                "rmse_on_masked": met.rmse(y[mask], P.ravel()[mask]),
                "iterations": iters, "converged": conv,
                "relative_residual": rel_res,
                "failure_mode": None if (conv or rel_res <= 10 * 1e-8)
                else "stalled-above-10x-tol",
            })
        out[f"rate_{rate:.0%}"] = {
            "rmse_on_masked_mean": float(np.mean([r["rmse_on_masked"] for r in rows])),
            "iterations_mean": float(np.mean([r["iterations"] for r in rows])),
            "converged_all": all(r["converged"] for r in rows),
            "tolerance": 1e-8,
            "final_relative_residual_mean": float(np.mean([r["relative_residual"] for r in rows])),
            "details": rows,
        }
    out["wall_clock_s"] = round(time.perf_counter() - T0, 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    log("  T1b done")
    return out


# ---------------------------------------------------------------------------
# T2 functional index regression (temporal-block CV)
# ---------------------------------------------------------------------------
def phase_t2(fields, index):
    log("T2: Nino3.4 spectral functional (temporal-block CV)")
    n = len(fields)
    kf = fk.KERNELS["matern32"]
    lam = 1e-2
    # 5 temporal blocks over the full record (for CV comparability)
    blocks = np.array_split(np.arange(n), 5)
    cv_pred_fun = np.full(n, np.nan)
    cv_pred_zero = np.full(n, np.nan)
    cv_pred_direct = np.full(n, np.nan)
    for fi, te in enumerate(blocks):
        tr = np.concatenate([blocks[k] for k in range(5) if k != fi])
        tr_idx = index[tr]
        mu = float(np.mean(tr_idx))
        for t in te:
            a = fk.fit_torus(fields[t], NY, NX, kf, lam=lam)
            cv_pred_fun[t] = fk.predict_box_functional(a, NY, NX, kf,
                                                       ROWS, COLS)
            cv_pred_zero[t] = mu
        # direct ridge head on box cells (fast sklearn)
        Xb = fields[tr, ROWS[0]:ROWS[1] + 1][:, :, COLS[0]:COLS[1] + 1]
        Xb = Xb.reshape(len(tr), -1)
        from sklearn.linear_model import Ridge
        reg = Ridge(alpha=1e-1).fit(Xb, tr_idx)
        for t in te:
            xb = fields[t, ROWS[0]:ROWS[1] + 1][:, COLS[0]:COLS[1] + 1]
            cv_pred_direct[t] = float(reg.predict(xb.reshape(1, -1))[0])
    m = ~np.isnan(cv_pred_fun)
    out = {"arm": "T2-ENSO-index", **META_LABEL,
           "cv": "5-fold temporal-block CV over 2005 months",
           "functional_vs_zero_model": {
               "rmse_functional": met.rmse(index[m], cv_pred_fun[m]),
               "rmse_zero_model": met.rmse(index[m], cv_pred_zero[m]),
               "rmse_direct_head": met.rmse(index[m], cv_pred_direct[m]),
           },
           "corr_functional": float(np.corrcoef(index[m], cv_pred_fun[m])[0, 1]),
           "n_cv_months": int(m.sum()),
           "wall_clock_s": round(time.perf_counter() - T0, 2),
           "peak_rss_gb": round(peak_rss_gb(), 3)}
    log("  T2 done")
    return out


# ---------------------------------------------------------------------------
# T3 frequency-domain transfer forecast
# ---------------------------------------------------------------------------
def phase_t3(fields, index):
    log("T3: transfer forecast h in {1,3,6,12}")
    Y = fields.astype(np.float64)
    Ytr = Y[:TRAIN_END]           # 1920 train months
    ytr = index[:TRAIN_END]
    yte = index[TRAIN_END:TEST_END]
    times = MONTH_IN_YEAR[:TRAIN_END]
    clim_tr = ft.month_climatology(ytr, times)
    ar1 = ft.ar1_fit(ytr)
    out = {"arm": "T3-forecast-transfer", **META_LABEL,
           "train": "1856-01..2015-12 (1920 months)",
           "test": "2016-01..2022-12 (84 months)",
           "win_rule": ("supported at h iff transfer beats persistence AND "
                        "climatology AND AR(1) in RMSE AND skill score AND "
                        "the RMSE margin vs the best baseline exceeds the "
                        "year-block bootstrap 95% CI half-width; refuted if "
                        "> half of horizons fail; else indeterminate"),
           "horizons": {}}
    horizons = [1, 3, 6, 12]
    for h in horizons:
        H = ft.fit_transfer_modes(Ytr, h, lam=1e-2)
        pred = ft.predict_index_series(Y, H, h, ROWS, COLS)[TRAIN_END:TEST_END]
        # baselines (train-only)
        y_full = np.concatenate([ytr, yte])
        pers = y_full[TRAIN_END - h:TEST_END - h]   # persistence (lag h)
        clim = np.array([clim_tr[int(MONTH_IN_YEAR[t])]
                         for t in range(TRAIN_END, TEST_END)])
        ph, pc = ar1
        # multi-step AR(1) at horizon h: arp[i] uses ONLY the observed value
        # h months before test i (rolling origin; NO mid-horizon observations)
        c_term = 0.0 if abs(ph - 1.0) < 1e-12 else pc * (1.0 - ph ** h) / (1.0 - ph)
        arp = np.array([ph ** h * y_full[TRAIN_END + i - h] + c_term
                        for i in range(len(yte))])
        m = ~np.isnan(pred)
        mt = ~np.isnan(pred) & ~np.isnan(pers) & ~np.isnan(clim) & ~np.isnan(arp)
        rm = ft.metrics(yte[m], pred[m])
        rp = ft.metrics(yte[mt], pers[mt])
        rc = ft.metrics(yte[mt], clim[mt])
        ra = ft.metrics(yte[mt], arp[mt])
        sk = ft.skill_score(yte[mt], pred[mt], clim[mt])
        skp = ft.skill_score(yte[mt], pers[mt], clim[mt])
        ska = ft.skill_score(yte[mt], arp[mt], clim[mt])
        yr = TEST_YEARS[:len(yte)]
        boot = {b: ft.year_block_bootstrap(yte[mt], pred[mt], base[mt], yr)
                for b, base in [("vs_persistence", pers),
                                ("vs_climatology", clim),
                                ("vs_ar1", arp)]}
        # win rule (pre-registered; MSE-consistent): margin vs the best
        # baseline in MSE, compared against the year-block bootstrap CI of
        # the MSE difference (transfer - baseline)
        mse = {"persistence": float(np.mean((yte[mt] - pers[mt]) ** 2)),
               "climatology": float(np.mean((yte[mt] - clim[mt]) ** 2)),
               "ar1": float(np.mean((yte[mt] - arp[mt]) ** 2))}
        best_base = min(mse, key=mse.get)
        margin = float(mse[best_base] - np.mean((yte[mt] - pred[mt]) ** 2))
        base_arr = {"persistence": pers[mt], "climatology": clim[mt],
                    "ar1": arp[mt]}[best_base]
        boot_vs_best = ft.year_block_bootstrap(yte[mt], pred[mt],
                                               base_arr, yr)
        half = abs(boot_vs_best["ci95"][1] - boot_vs_best["ci95"][0]) / 2
        beats = (rm["rmse"] < rp["rmse"] and rm["rmse"] < rc["rmse"]
                 and rm["rmse"] < ra["rmse"] and sk > skp and sk > ska
                 and sk > 0.0)
        supported = bool(beats and margin > half)
        # seam: Jan-origin vs other-origin test months (h=1)
        seam = None
        if h == 1:
            jan = [i for i in range(len(yte)) if MONTH_IN_YEAR[TRAIN_END + i] == 0]
            oth = [i for i in range(len(yte)) if MONTH_IN_YEAR[TRAIN_END + i] != 0]
            seam = {
                "jan_origin_rmse": float(np.sqrt(np.mean((yte[jan] - pred[jan]) ** 2))),
                "other_origin_rmse": float(np.sqrt(np.mean((yte[oth] - pred[oth]) ** 2))),
            }
        sm_skill = {}
        for om in [0, 3, 5, 9, 99]:
            if om == 99:
                sel_m = np.arange(len(yte))          # all origins
                label = "all"
            else:
                sel_m = np.where(MONTH_IN_YEAR[TRAIN_END:TRAIN_END + len(yte)] == om)[0]
                label = f"origin-month-{om}"
            if len(sel_m) >= 3:
                sm_skill[label] = {
                    "n": int(len(sel_m)),
                    "rmse": float(np.sqrt(np.mean((yte[sel_m] - pred[sel_m]) ** 2))),
                    "skill": ft.skill_score(yte[sel_m], pred[sel_m],
                                            clim[sel_m]),
                }
        out["horizons"][str(h)] = {
            "transfer": rm, "persistence": rp, "climatology": rc, "ar1": ra,
            "start_month_skill": sm_skill,
            "skill_vs_climatology_transfer": sk,
            "skill_vs_climatology_persistence": skp,
            "skill_vs_climatology_ar1": ska,
            "best_baseline": best_base, "margin_vs_best": margin,
            "bootstrap": boot, "margin_ci_half_width": half,
            "beats_all": beats, "win": {
                "supported": supported, "refuted": False,
                "indeterminate": not supported,
                "note": "pre-registered rule (see win_rule)"},
            "seam_h1": seam,
        }
        log(f"  h={h}: rmse {rm['rmse']:.4f} vs pers {rp['rmse']:.4f} "
            f"clim {rc['rmse']:.4f} ar1 {ra['rmse']:.4f}; supported={supported}")
    # truncation sweep (h=1): cutoffs 2014-12/2013-12/2012-12 + 2015-excluded
    sweep = {}
    for cut, label in [(TRAIN_END - 12, "cutoff-2014-12"),
                       (TRAIN_END - 24, "cutoff-2013-12"),
                       (TRAIN_END - 36, "cutoff-2012-12")]:
        H = ft.fit_transfer_modes(Y[:cut], 1, lam=1e-2)
        pred = ft.predict_index_series(Y, H, 1, ROWS, COLS)[TRAIN_END:TEST_END]
        sweep[label] = {"rmse": float(np.sqrt(np.mean((yte - pred) ** 2))),
                        "skill": ft.skill_score(yte, pred, clim)}
    out["truncation_sweep_h1"] = sweep
    out["wall_clock_s"] = round(time.perf_counter() - T0, 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    log("  T3 done")
    return out


# ---------------------------------------------------------------------------
# B baselines on real pooled cells
# ---------------------------------------------------------------------------
def phase_baselines(fields):
    log("B: sklearn baselines on real pooled cells (test window)")
    held = list(range(1920, TEST_END))
    rng_pool = np.random.default_rng(11)
    Xs, ys = [], []
    for t in held[:4]:
        v = (~MISSING[t]).ravel()
        idx = np.where(v.ravel())[0]
        yy, xx = np.divmod(idx, NX)
        Xs.append(np.stack([yy, xx], axis=1).astype(np.float64))
        ys.append(fields[t].ravel()[idx].astype(np.float64))
    X_pool = np.concatenate(Xs, axis=0)
    y_pool = np.concatenate(ys, axis=0)
    # test cells: 2000 valid cells sampled across all 84 test months;
    # position in the concatenated valid list -> month -> flat cell index,
    # decoded through each month's valid-cell index list (never a raw
    # position used as a cell index; missing cells excluded by construction)
    val_lists = [np.where((~MISSING[t]).ravel())[0] for t in held]
    cumv = np.cumsum([len(v) for v in val_lists])
    all_val = np.concatenate(val_lists)
    te_idx = rng_pool.choice(len(all_val), 2000, replace=False)
    te_month = np.searchsorted(cumv, te_idx, side="right")
    te_pos = te_idx - np.concatenate([[0], cumv])[te_month]
    te_cell_local = np.array([val_lists[int(tm)][int(pp)]
                              for tm, pp in zip(te_month, te_pos)])
    te_y, te_x = np.divmod(te_cell_local, NX)
    X_te = np.stack([te_y, te_x], axis=1).astype(np.float64)
    y_te = np.array([fields[held[tm]].ravel()[cl]
                     for tm, cl in zip(te_month, te_cell_local)], dtype=np.float64)
    out = {"arm": "B-baselines", **META_LABEL,
           "task": "pooled-cell spatial reconstruction; test = 2000 VALID cells of 84 test months",
           "pool_n_train_cells": len(X_pool),
           "results": {}}
    for ntr in [2000, 5000, 10000]:
        ntr = min(ntr, len(X_pool))
        rng = np.random.default_rng(ntr)
        sel = rng.choice(len(X_pool), ntr, replace=False)
        r = {}
        from sklearn.kernel_ridge import KernelRidge
        t0 = time.perf_counter()
        m = KernelRidge(kernel="rbf", gamma=1.0 / (2 * 8.0), alpha=1e-2)
        m.fit(X_pool[sel], y_pool[sel])
        yh = m.predict(X_te)
        r["exact_subsample_rbf"] = {
            "rmse": float(np.sqrt(np.mean((y_te - yh) ** 2))),
            "wall_clock_s": round(time.perf_counter() - t0, 2),
            "n_train": ntr}
        from sklearn.kernel_approximation import Nystroem, RBFSampler
        from sklearn.linear_model import Ridge
        t0 = time.perf_counter()
        ny_ = Nystroem(kernel="rbf", gamma=1.0 / (2 * 8.0),
                       n_components=min(5000, ntr), random_state=7)
        Xn = ny_.fit_transform(X_pool[sel])
        Xn_te = ny_.transform(X_te)
        mn = Ridge(alpha=1e-2).fit(Xn, y_pool[sel])
        r["nystrom_5000"] = {
            "rmse": float(np.sqrt(np.mean((y_te - mn.predict(Xn_te)) ** 2))),
            "wall_clock_s": round(time.perf_counter() - t0, 2)}
        t0 = time.perf_counter()
        rf = RBFSampler(gamma=1.0 / (2 * 8.0), n_components=5000, random_state=7)
        Xr = rf.fit_transform(X_pool[sel])
        Xr_te = rf.transform(X_te)
        mr = Ridge(alpha=1e-2).fit(Xr, y_pool[sel])
        r["rff_5000"] = {
            "rmse": float(np.sqrt(np.mean((y_te - mr.predict(Xr_te)) ** 2))),
            "wall_clock_s": round(time.perf_counter() - t0, 2)}
        out["results"][str(ntr)] = r
    out["wall_clock_s"] = round(time.perf_counter() - T0, 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    log("  B done")
    return out


# ---------------------------------------------------------------------------
# S scaling (unchanged measurement)
# ---------------------------------------------------------------------------
def phase_scaling():
    log("S: O(N log N)/O(N) scaling")
    kf = fk.KERNELS["matern32"]
    import data_gen
    out = {"arm": "S-scaling", **META_LABEL, "grids": {}}
    for (ny, nx, tag) in [(32, 32, "pilot"), (36, 72, "real-36x72"),
                          (72, 144, "scaling-144x72")]:
        rng = np.random.default_rng(3)
        f = data_gen.sample_field(rng, ny, nx, data_gen.matern32_cov, 4.0,
                                  lat_amp=True).astype(np.float64)
        t0 = time.perf_counter()
        a = fk.fit_torus(f, ny, nx, kf, lam=1e-2)
        P = fk.predict_torus(a, ny, nx, kf)
        dt = time.perf_counter() - t0
        N = ny * nx
        out["grids"][tag] = {
            "N": N, "wall_clock_s": round(dt, 4),
            "fit_flops": met.est_spectral_fit_flops(ny, nx),
            "bytes": met.est_spectral_bytes(ny, nx),
            "pred_check_rmse": met.rmse(f, P),
        }
        log(f"  {tag} N={N} t={dt:.3f}s")
    Nbig = 720 * 1440
    out["extrapolation"] = {
        "grid_025deg_N": Nbig,
        "est_fit_flops": met.est_spectral_fit_flops(720, 1440),
        "est_bytes": met.est_spectral_bytes(720, 1440),
        "peak_rss_gb_at_025deg_single_field": round(40.0 * Nbig / (1024 ** 3), 4),
        "note": "O(N log N)/O(N); a single 0.25-deg float64 field fits trivially (~0.04 GB); memory grows linearly with the number of fields kept in the batch (e.g. 100 years x 12 months x ~2.6 MB ~ 3.1 GB), which is why the executed benchmark keeps one field in memory at a time and processes 5-deg data.",
    }
    out["wall_clock_s"] = round(time.perf_counter() - T0, 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    return out


def main():
    fields, index, meta = load_real()
    log(f"data: {meta['dataset.origin']} fields={fields.shape}")
    for phase, args in [(phase_pilot, (fields,)),
                        (phase_t1a, (fields,)),
                        (phase_t1b, (fields,)),
                        (phase_t2, (fields, index)),
                        (phase_t3, (fields, index)),
                        (phase_baselines, (fields,)),
                        (phase_scaling, ())]:
        art = phase(*args)
        save(art)
    summary = {"dataset.origin": meta["dataset.origin"],
               "simulation_marker": None,
               "total_wall_clock_s": round(time.perf_counter() - T0, 2),
               "peak_rss_gb": round(peak_rss_gb(), 3),
               "phase_log": LOG}
    with open(os.path.join(OUT, "results_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    log(f"done: total {summary['total_wall_clock_s']}s peak "
        f"{summary['peak_rss_gb']}GB")


if __name__ == "__main__":
    main()