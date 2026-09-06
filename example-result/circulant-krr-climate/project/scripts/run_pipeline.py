#!/usr/bin/env python3
"""End-to-end experiment pipeline (CPU-only, 12 cores / ~7 GB / <= 90 min).

Phases (see ideas/experiments/experiment-plan.json):
  P0  pilot gate 32x32: exactness of torus spectral solve vs dense-torus,
      torus-vs-free gap vs padding/ell sweeps
  T1a exact spectral reconstruction (torus kernel): random-pixel masks
      10/30/50% and spatial-halo masks w in {1,2,4}; LOFO over 48 held-out
      months; in-sample evaluation over a fixed pool; optimism arm
      (random vs halo masks)
  T1b FFT-preconditioned CG with masked training (free-boundary to tol):
      input masks 10/30/50%
  T2   Nino3.4 functional prediction (kernel-consistent box functional,
      Trenberth 1997 box) + zero-model ablation + direct regression head
      with 5-fold temporal-block CV (sklearn baselines there)
  B   sklearn baselines (exact subsample n in {2k,5k,10k}, Nystrom and RFF
      {500,2k,5k,10k}) on T2-direct and T1 reconstruction subset, plus
      matched-flops/bytes variant
  S   scaling: wall-clock/memory vs N at 32x32, 72x36, 144x72 + extrapolation
      model vs 7 GB cap

Every artifact JSON carries dataset.origin and simulation_marker (from the
data mode) plus resource axes (wall_clock_s, peak_rss_gb, estimated_flops,
estimated_bytes).
"""
from __future__ import annotations

import json
import os
import resource
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fft_krr as fk         # noqa: E402
import metrics as met         # noqa: E402
import baselines as bl        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "results", "raw")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

T0 = time.perf_counter()
LOG = []


def log(msg):
    el = time.perf_counter() - T0
    LOG.append((round(el, 1), msg))
    print(f"[t={el:7.1f}s] {msg}", flush=True)


def elapsed():
    return time.perf_counter() - T0


def abort_check():
    if elapsed() > 85 * 60:
        log("ABORT: cumulative wall-clock > 85 min; recording partial state")
        return True
    return False


def peak_rss_gb():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_maxrss / 1024.0 / 1024.0


def load_data():
    """Load REAL data if present, else fall back to the [simulated] generator.

    Iteration-2 (research-manager directive): the real-data route
    (results/raw/real/fields.npy + index.npy + meta.json, produced by
    scripts/convert_netcdf4.py under the constraint lift that permits h5py)
    is now the PREFERRED source; the synthetic fallback remains for
    reproducibility.
    """
    real_dir = os.path.join(RAW, "real")
    real_fields = os.path.join(real_dir, "fields.npy")
    real_meta = os.path.join(real_dir, "meta.json")
    if os.path.exists(real_fields) and os.path.exists(real_meta):
        with open(real_meta) as fh:
            meta = json.load(fh)
        if meta.get("dataset.origin", "").startswith("real"):
            fields = np.load(real_fields)
            index = np.load(os.path.join(real_dir, "index.npy"))
            log("data: REAL Kaplan SST v2 (h5py conversion; iteration-2 constraint lift)")
            return fields, index, meta
    fields_p = os.path.join(RAW, "fields.npy")
    if os.path.exists(fields_p) and os.path.exists(os.path.join(RAW, "meta.json")):
        with open(os.path.join(RAW, "meta.json")) as fh:
            meta = json.load(fh)
        if meta.get("dataset.origin", "").startswith("synthetic"):
            fields = np.load(fields_p)
            index = np.load(os.path.join(RAW, "index.npy"))
            log("data: synthetic-[simulated]-from-physics (fallback fired)")
            return fields, index, meta
    # try real fetch (bounded) then generate
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "fetch_real_data.py")],
                       timeout=320, capture_output=True)
    log(f"fetch_real_data exit={r.returncode}")
    if os.path.exists(os.path.join(RAW, "real", "real.npz")):
        d = np.load(os.path.join(RAW, "real", "real.npz"))
        log("data: REAL (stdlib-readable) - uncomment handling in executor notes")
        raise SystemExit("real data route needs manual review; use fallback")
    import data_gen
    data_gen.main()
    fields = np.load(fields_p)
    index = np.load(os.path.join(RAW, "index.npy"))
    with open(os.path.join(RAW, "meta.json")) as fh:
        meta = json.load(fh)
    log("data: synthetic-[simulated]-from-physics (fallback fired)")
    return fields, index, meta


def load_small_field(tag):
    p = os.path.join(RAW, f"field_{tag}.npy")
    if os.path.exists(p):
        return np.load(p)
    import data_gen
    rng = np.random.default_rng(data_gen.SEED + 1)
    ny, nx = {"pilot": (32, 32), "scaling_72x36": (36, 72),
              "scaling_144x72": (72, 144)}[tag]
    from data_gen import sample_field, matern32_cov
    f = sample_field(rng, ny, nx, matern32_cov, 4.0, lat_amp=True)
    np.save(p, f)
    return f


# ---------------------------------------------------------------------------
# P0 pilot gate
# ---------------------------------------------------------------------------
def phase_pilot(meta):
    log("P0: pilot gate 32x32")
    ny = nx = 32
    y = load_small_field("pilot")[:ny, :nx]
    lam = 1e-3
    out = {"arm": "P0-pilot-gate", "dataset.origin": meta["dataset.origin"],
           "simulation_marker": meta.get("simulation_marker"),
           "grid": [ny, nx], "lambda": lam, "results": {}}
    for kname in ["matern32", "rbf"]:
        kf = fk.KERNELS[kname]
        spec, min_eig, n_neg = fk.torus_spectrum(ny, nx, kf, lam=0.0, floor=True)
        # dense PSD-projected torus Gram (same floored spectrum as the solve)
        N = ny * nx
        # dense matrix from the torus first-column pattern
        rows, cols = np.indices((N, N))
        iy, ix = np.divmod(rows, nx)
        jy, jx = np.divmod(cols, nx)
        cy = np.minimum(np.abs(iy - jy), ny - np.abs(iy - jy))
        cx = np.minimum(np.abs(ix - jx), nx - np.abs(ix - jx))
        c_first = fk.torus_first_column(ny, nx, kf)
        G_dense = c_first[cy % ny, cx % nx]
        G_psd_dense = np.fft.irfft2(np.maximum(np.fft.rfft2(c_first), 0.0),
                                    s=(ny, nx))[cy % ny, cx % nx]
        a_sp = fk.fit_torus(y, ny, nx, kf, lam=lam)
        a_dt = np.linalg.solve(G_psd_dense + lam * np.eye(N), y.ravel()).reshape(ny, nx)
        a_df = fk.fit_dense(y, ny, nx, kf, lam=lam)  # free-boundary dense
        e_torus = float(np.max(np.abs(a_sp - a_dt)))
        rel_torus = e_torus / max(1e-30, float(np.max(np.abs(a_dt))))
        gap = float(np.max(np.abs(a_sp - a_df)))
        rel_gap = gap / max(1e-30, float(np.max(np.abs(a_df))))
        # padding sweep: padded torus solve vs free dense (boundary behavior)
        pad_sweep = {}
        for f in [0.5, 1.0, 2.0]:
            c = fk.torus_first_column(ny, nx, kf)
            c_ext, nyc, nxc = fk.embed_torus_column(c, f)
            c_ext[0, 0] += lam
            spec = np.fft.rfft2(c_ext)
            b = np.zeros((nyc, nxc)); b[:ny, :nx] = y
            z = np.fft.irfft2(np.fft.rfft2(b) / spec, s=(nyc, nxc))
            err = float(np.max(np.abs(z[:ny, :nx] - a_df)))
            pad_sweep[f] = round(err, 6)
        # ell sweep: torus-vs-free gap decay
        ell_sweep = {}
        for ell in [1.0, 2.0, 4.0, 8.0]:
            kf2 = fk.make_kernel(kname, ell)
            a2 = fk.fit_torus(y, ny, nx, kf2, lam=lam)
            a3 = fk.fit_dense(y, ny, nx, kf2, lam=lam)
            ell_sweep[ell] = round(float(np.max(np.abs(a2 - a3))) /
                                   max(1e-30, float(np.max(np.abs(a3)))), 6)
        out["results"][kname] = {
            "spectral_vs_dense_torus_inf": e_torus,
            "spectral_vs_dense_torus_rel": rel_torus,
            "torus_vs_free_gap_inf": gap,
            "torus_vs_free_gap_rel": rel_gap,
            "min_eigenvalue_raw": min_eig,
            "n_negative_eigenvalues": n_neg,
            "padding_sweep_maxdiff_vs_free": pad_sweep,
            "ell_sweep_torus_vs_free_rel": ell_sweep,
        }
        log(f"  {kname}: torus-exactness rel={rel_torus:.2e} "
            f"free-gap rel={rel_gap:.2e}")
    # floor-eps sensitivity: rbf reconstruction RMSE vs spectral floor level
    import metrics as _m
    y36 = load_small_field("scaling_72x36")[:36, :72]
    eps_sweep = {}
    for eps in [0.0, 1e-8, 1e-6, 1e-4, 1e-2]:
        c0 = fk.torus_first_column(36, 72, fk.KERNELS["rbf"])
        sp0 = np.fft.rfft2(c0)
        sp_use = np.maximum(sp0, eps) + lam
        a = np.fft.irfft2(np.fft.rfft2(y36) / sp_use, s=(36, 72))
        mf = np.zeros(36 * 72, dtype=bool)
        rngs = np.random.default_rng(7)
        mf[rngs.choice(36 * 72, int(0.3 * 36 * 72), replace=False)] = True
        c0p = fk.torus_first_column(36, 72, fk.KERNELS["rbf"])
        P = np.fft.irfft2(np.fft.rfft2(a) * np.maximum(np.fft.rfft2(c0p), eps),
                          s=(36, 72))
        eps_sweep[eps] = float(np.sqrt(np.mean((P.ravel()[mf] - y36.ravel()[mf]) ** 2)))
    # per-grid torus-vs-free delta sweep
    grid_gap = {}
    for (gny, gnx, tag) in [(32, 32, "pilot"), (36, 72, "scaling_72x36"),
                            (72, 144, "scaling_144x72")]:
        yy = load_small_field(tag)[:gny, :gnx]
        gap_row = {}
        for kname2 in ["matern32", "rbf"]:
            kf2 = fk.KERNELS[kname2]
            a2 = fk.fit_torus(yy, gny, gnx, kf2, lam=lam)
            a3 = fk.fit_dense(yy, gny, gnx, kf2, lam=lam)
            gap_row[kname2] = round(float(np.max(np.abs(a2 - a3))) /
                                    max(1e-30, float(np.max(np.abs(a3)))), 4)
        grid_gap[tag] = gap_row
    out["floor_eps_sensitivity_rbf_rmse"] = eps_sweep
    out["grid_size_torus_vs_free_delta_rel"] = grid_gap
    passed = all(out["results"][k]["spectral_vs_dense_torus_rel"] < 1e-6
                 for k in out["results"])
    out["gate_passed"] = passed
    out["gate_definition"] = ("spectral == dense-torus to 1e-6 rel "
                              "(solve exactness for the torus kernel); "
                              "torus-vs-free gap reported per kernel/ell "
                              "(disclosed modeling qualification)")
    out["wall_clock_s"] = round(elapsed(), 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    return out


# ---------------------------------------------------------------------------
# T1a spectral reconstruction
# ---------------------------------------------------------------------------
def halo_indices(ny, nx, seeds, w):
    yy, xx = np.mgrid[0:ny, 0:nx]
    m = np.zeros((ny, nx), dtype=bool)
    for (sy, sx) in seeds:
        d = np.sqrt((yy - sy) ** 2 + (xx - sx) ** 2)
        m |= d <= w
    return m


def phase_t1a(fields, meta, seeds_fixed=None):
    log("T1a: exact spectral reconstruction")
    ny, nx = fields.shape[1], fields.shape[2]
    lam = 2e-2        # fixed after a small selection pass (see lambda_sweep)
    kernels = ["matern32", "rbf"]
    # --- lambda selection on a small validation subset (block-respecting) ---
    lam_log = np.logspace(-4, 2, 8)
    sel_field = fields[200:208]
    best = {}
    for kname in kernels:
        kf = fk.KERNELS[kname]
        errs = []
        for lv in lam_log:
            e = []
            for t in range(8):
                a = fk.fit_torus(sel_field[t], ny, nx, kf, lam=lv)
                mf = np.zeros(ny * nx, dtype=bool)
                rng = np.random.default_rng(1000 + t)
                mf[rng.choice(ny * nx, size=int(0.3 * ny * nx), replace=False)] = True
                m = mf.reshape(ny, nx)
                P = fk.predict_torus(a, ny, nx, kf)
                e.append(float(np.sqrt(np.mean((P[m] - sel_field[t][m]) ** 2))))
            errs.append(float(np.mean(e)))
        best[kname] = {"lambda": float(lam_log[int(np.argmin(errs))]),
                       "rmse": float(np.min(errs)),
                       "sweep": [float(v) for v in errs]}
    lam = max(v["lambda"] for v in best.values())
    log(f"  lambda selection done: {best}")
    # --- LOFO: 48 held-out months (12 per season), both kernels ---
    heldout = [t for s in range(4) for t in range(12 * (s + 1) - 12 + 2 * s,
                                                12 * (s + 1) + 2 * s)]
    heldout = heldout[:48] if len(heldout) >= 48 else list(range(48))
    rng = np.random.default_rng(7)
    masks = {}
    for rate in [0.1, 0.3, 0.5]:
        mf = np.zeros(ny * nx, dtype=bool)
        mf[rng.choice(ny * nx, size=int(rate * ny * nx), replace=False)] = True
        masks[f"random_{rate:.0%}"] = mf.reshape(ny, nx)
    seeds = [ (18, 36), (6, 10), (28, 55), (12, 60), (24, 25) ]
    for w in [1, 2, 4]:
        masks[f"halo_w{w}"] = halo_indices(ny, nx, seeds, w)
    rows = {}
    for kname in kernels:
        kf = fk.KERNELS[kname]
        lv = best[kname]["lambda"]
        for mname, m in masks.items():
            errs, covs, widths = [], [], []
            for t in heldout:
                a = fk.fit_torus(fields[t], ny, nx, kf, lam=lv)
                P = fk.predict_torus(a, ny, nx, kf)
                mflat = m.ravel()
                ytrue = fields[t].ravel()[mflat]
                yhat = P.ravel()[mflat]
                errs.append(met.rmse(ytrue, yhat))
                # split-conformal within this field (calib/test halves)
                idx = np.where(mflat)[0]
                half = len(idx) // 2
                if half >= 8:
                    cov, wd = met.split_conformal(ytrue[:half], yhat[:half],
                                                  ytrue[half:], yhat[half:])
                    covs.append(cov); widths.append(wd)
            rows[f"{kname}|{mname}"] = {
                "rmse_mean": float(np.mean(errs)),
                "rmse_std_over_fields": float(np.std(errs)) if len(errs) > 1 else 0.0,
                "r2": met.r2(np.concatenate(
                    [fields[t].ravel()[m.ravel()] for t in heldout]),
                    np.concatenate([fk.predict_torus(
                        fk.fit_torus(fields[t], ny, nx, kf, lam=lv),
                        ny, nx, kf).ravel()[m.ravel()] for t in heldout])),
                "conformal_coverage": float(np.mean(covs)) if covs else None,
                "conformal_coverage_std": float(np.std(covs)) if covs else None,
                "conformal_n_fields": len(covs),
                "conformal_mean_width": float(np.mean(widths)) if widths else None,
                "conformal_width_std": float(np.std(widths)) if widths else None,
                "n_heldout": len(heldout),
                "target_coverage": 0.90,
                "coverage_below_target": bool(covs and np.mean(covs) < 0.90),
            }
    # --- optimism arm: random vs halo on the same held-out fields ---
    kf = fk.KERNELS["matern32"]
    lv = best["matern32"]["lambda"]
    rand_errs, halo_errs = [], []
    for t in heldout:
        a = fk.fit_torus(fields[t], ny, nx, kf, lam=lv)
        P = fk.predict_torus(a, ny, nx, kf)
        rand_errs.append(met.rmse(fields[t][masks["random_30%"]],
                                  P[masks["random_30%"]]))
        halo_errs.append(met.rmse(fields[t][masks["halo_w2"]],
                                  P[masks["halo_w2"]]))
    out = {
        "arm": "T1a-spectral-reconstruction", "dataset.origin": meta["dataset.origin"],
        "simulation_marker": meta.get("simulation_marker"),
        "n_heldout": len(heldout), "lambda_selection": best,
        "per_mask_metrics": rows,
        "optimism_gap": {
            "random_30pct_rmse_mean": float(np.mean(rand_errs)),
            "halo_w2_rmse_mean": float(np.mean(halo_errs)),
            "gap": float(np.mean(rand_errs) - float(np.mean(halo_errs))),
        },
        "wall_clock_s": round(elapsed(), 2), "peak_rss_gb": round(peak_rss_gb(), 3),
    }
    log(f"  done; optimism gap={out['optimism_gap']['gap']:.4f}")
    return out


# ---------------------------------------------------------------------------
# T1b FFT-preconditioned CG masked training
# ---------------------------------------------------------------------------
def phase_t1b(fields, meta):
    log("T1b: FFT-preconditioned CG masked training")
    ny, nx = fields.shape[1], fields.shape[2]
    fields_use = fields[200:208]
    out = {"arm": "T1b-CG-masked-train", "dataset.origin": meta["dataset.origin"],
           "simulation_marker": meta.get("simulation_marker")}
    for rate in [0.1, 0.3, 0.5]:
        rows = []
        for t in range(8):
            rng = np.random.default_rng(2000 + t)
            obs = np.ones(ny * nx, dtype=bool)
            obs[rng.choice(ny * nx, size=int(rate * ny * nx), replace=False)] = False
            y = fields_use[t].ravel()
            alpha, iters, conv, rel_res = fk.cg_masked_solve(
                y, ny, nx, fk.KERNELS["matern32"], np.where(obs)[0],
                lam=1e-2, tol=1e-8, max_iter=3000)
            P = fk.predict_torus(alpha, ny, nx, fk.KERNELS["matern32"])
            mask = ~obs
            rows.append({
                "masked_input_rate": rate, "field": t,
                "rmse_on_masked": met.rmse(y[mask], P.ravel()[mask]),
                "iterations": iters, "converged": conv,
                "relative_residual": rel_res,
            })
        out[f"rate_{rate:.0%}"] = {
            "rmse_on_masked_mean": float(np.mean([r["rmse_on_masked"] for r in rows])),
            "iterations_mean": float(np.mean([r["iterations"] for r in rows])),
            "converged_all": all(r["converged"] for r in rows),
            "tolerance": 1e-8,
            "final_relative_residual_mean": float(np.mean([r["relative_residual"] for r in rows])),
            "details": rows,
        }
    out["wall_clock_s"] = round(elapsed(), 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    log("  done")
    return out


# ---------------------------------------------------------------------------
# T2 Nino3.4 functional prediction
# ---------------------------------------------------------------------------
def phase_t2(fields, index, meta):
    log("T2: Nino3.4 kernel-consistent functional prediction")
    ny, nx = fields.shape[1], fields.shape[2]
    rows = np.arange(17, 20)
    cols = np.arange(38, 48)
    kf = fk.KERNELS["matern32"]
    lam = 1e-2
    n = len(fields)
    pred_fun = np.empty(n)
    pred_zero = np.empty(n)
    fits = 0
    for t in range(n):
        a = fk.fit_torus(fields[t], ny, nx, kf, lam=lam)
        pred_fun[t] = fk.predict_box_functional(a, ny, nx, kf, rows, cols)
        # zero-model ablation: box mean of the observed field (no fit)
        pred_zero[t] = float(np.mean(fields[t][rows][:, cols]))
        fits += 1
        if t % 222 == 0 and t > 0:
            log(f"  functional fits {t}/{n} done")
    # per-block (temporal-block CV structure) reporting: 5 blocks of 60 months
    blk = 60
    nblk = n // blk
    block_rmse = []
    for b in range(nblk):
        sl = slice(b * blk, (b + 1) * blk)
        block_rmse.append(met.rmse(index[sl], pred_fun[sl]))
    # season-mean climatology baseline
    climo = np.empty(n)
    for moy in range(12):
        m = np.where((np.arange(n) % 12) == moy)[0]
        climo[m] = np.mean(index[m])
    # direct regression head with 5-fold temporal-block CV (sklearn)
    nfolds = 5
    nf = n - (n % nfolds)
    X = fields[:nf].reshape(nf, -1).astype(np.float64)
    y = index[:nf]
    fold_rmse = []
    for kk in range(nfolds):
        te = slice(kk * (nf // nfolds), (kk + 1) * (nf // nfolds))
        tr_idx = np.ones(nf, dtype=bool)
        tr_idx[te] = False
        yhat, dt, _m = bl.exact_krr_fit(X[tr_idx], y[tr_idx], X[te], y[te],
                                        lam=lam,
                                        gamma=bl._rbf_gamma_from_ell(4.0))
        fold_rmse.append(met.rmse(y[te], yhat))
    out = {
        "arm": "T2-ENSO-index", "dataset.origin": meta["dataset.origin"],
        "simulation_marker": meta.get("simulation_marker"),
        "box": {"rows": rows.tolist(), "cols": cols.tolist(),
                "note": "Trenberth 1997 Nino3.4: 5N-5S, 170W-120W"},
        "index_std": float(np.std(index)),
        "functional_baseline_rmse": met.rmse(index, climo),
        "functional_zero_model_ablation_rmse": met.rmse(index, pred_zero),
        "functional_rmse": met.rmse(index, pred_fun),
        "functional_r2": met.r2(index, pred_fun),
        "functional_blockcv_report": {
            "blocks": nblk, "block_size_months": blk,
            "rmse_per_block": [round(v, 4) for v in block_rmse],
            "rmse_mean": float(np.mean(block_rmse)),
        },
        "direct_head_5fold": {
            "folds": nfolds,
            "rmse_per_fold": [round(v, 4) for v in fold_rmse],
            "rmse_mean": float(np.mean(fold_rmse)),
        },
        "n_fits_functional": fits,
        "wall_clock_s": round(elapsed(), 2), "peak_rss_gb": round(peak_rss_gb(), 3),
    }
    log(f"  done: functional RMSE={out['functional_rmse']:.4f} "
        f"ablation={out['functional_zero_model_ablation_rmse']:.4f} "
        f"direct={out['direct_head_5fold']['rmse_mean']:.4f}")
    return out


# ---------------------------------------------------------------------------
# B baselines
# ---------------------------------------------------------------------------
def phase_baselines(fields, index, meta):
    log("B: scikit-learn baselines (pooled-cell reconstruction task)")
    ny, nx = fields.shape[1], fields.shape[2]
    pool_months = list(range(200, 888))
    heldout = [t for s in range(4)
               for t in range(12 * (s + 1) - 12 + 2 * s,
                              12 * (s + 1) + 2 * s)][:48]
    rng_pool = np.random.default_rng(11)
    Xs, ys = [], []
    for t in pool_months[:4]:
        idx = np.arange(ny * nx)  # all 2592 cells of each of 4 months
        yy, xx = np.divmod(idx, nx)
        Xs.append(np.stack([yy, xx], axis=1).astype(np.float64))
        ys.append(fields[t].ravel()[idx].astype(np.float64))
    X_pool = np.concatenate(Xs, axis=0)
    y_pool = np.concatenate(ys, axis=0)
    # test: 2000 cells from the 48 held-out months (same LOFO set)
    te_idx = rng_pool.choice(len(heldout) * ny * nx, 2000, replace=False)
    te_t = te_idx // (ny * nx)
    te_c = te_idx % (ny * nx)
    te_y, te_x = np.divmod(te_c, nx)
    X_te = np.stack([te_y, te_x], axis=1).astype(np.float64)
    y_te = np.array([fields[heldout[tt]].ravel()[cc]
                     for tt, cc in zip(te_t, te_c)], dtype=np.float64)
    out = {"arm": "B-baselines", "dataset.origin": meta["dataset.origin"],
           "simulation_marker": meta.get("simulation_marker"),
           "task": "pooled-cell spatial reconstruction; test = 2000 cells of "
                   "48 held-out months",
           "results": {}}
    for ntr in [2000, 5000, 10000]:
        rng = np.random.default_rng(ntr)
        tr_idx = rng.choice(len(X_pool), ntr, replace=False)
        yhat, dt, _m = bl.exact_krr_fit(X_pool[tr_idx], y_pool[tr_idx],
                                        X_te, y_te,
                                        lam=1e-2, gamma=bl._rbf_gamma_from_ell(4.0))
        out["results"][f"exact_n{ntr}"] = {
            "rmse": met.rmse(y_te, yhat), "r2": met.r2(y_te, yhat),
            "wall_clock_s": round(dt, 2), "n_train": ntr, "n_test": len(y_te),
        }
        log(f"  exact n={ntr} rmse={out['results'][f'exact_n{ntr}']['rmse']:.4f} "
            f"t={dt:.1f}s")
    for comp in [500, 2000, 5000, 10000]:
        rng = np.random.default_rng(comp)
        tr_idx = rng.choice(len(X_pool), 4000, replace=False)
        yhat, dt, info = bl.nystrom_fit(X_pool[tr_idx], y_pool[tr_idx],
                                        X_te, y_te, lam=1e-2,
                                        gamma=bl._rbf_gamma_from_ell(4.0),
                                        n_components=comp)
        out["results"][f"nystrom_{comp}"] = {
            "rmse": met.rmse(y_te, yhat), "wall_clock_s": round(dt, 2),
            "est_flops": info["est_flops"], "est_bytes": info["est_bytes"],
        }
        log(f"  nystrom {comp} rmse={out['results'][f'nystrom_{comp}']['rmse']:.4f} "
            f"t={dt:.1f}s")
    for comp in [500, 2000, 5000, 10000]:
        rng = np.random.default_rng(comp)
        tr_idx = rng.choice(len(X_pool), 4000, replace=False)
        yhat, dt, info = bl.rff_fit(X_pool[tr_idx], y_pool[tr_idx],
                                    X_te, y_te, lam=1e-2,
                                    gamma=bl._rbf_gamma_from_ell(4.0),
                                    n_components=comp)
        out["results"][f"rff_{comp}"] = {
            "rmse": met.rmse(y_te, yhat), "wall_clock_s": round(dt, 2),
            "est_flops": info["est_flops"], "est_bytes": info["est_bytes"],
        }
        log(f"  rff {comp} rmse={out['results'][f'rff_{comp}']['rmse']:.4f} "
            f"t={dt:.1f}s")
    out["wall_clock_s"] = round(elapsed(), 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    log("  done")
    return out


# ---------------------------------------------------------------------------
# S scaling
# ---------------------------------------------------------------------------
def phase_scaling(meta):
    log("S: scaling arm")
    out = {"arm": "S-scaling", "dataset.origin": meta["dataset.origin"],
           "simulation_marker": meta.get("simulation_marker"), "grids": {}}
    kf = fk.KERNELS["matern32"]
    for (ny, nx, tag) in [(32, 32, "pilot"), (36, 72, "scaling_72x36"),
                          (72, 144, "scaling_144x72")]:
        f = load_small_field(tag)
        f = np.ascontiguousarray(f[:ny, :nx], dtype=np.float64)
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
    # extrapolation: 0.25-deg global ~ 1.04M cells
    Nbig = 720 * 1440
    out["extrapolation"] = {
        "grid_025deg_N": Nbig,
        "est_fit_flops": met.est_spectral_fit_flops(720, 1440),
        "est_bytes": met.est_spectral_bytes(720, 1440),
        "peak_rss_gb_at_025deg_est": 40.0 * Nbig / (1024 ** 3),
        "note": "O(N log N) / O(N); 7 GB cap is exceeded by 0.25-deg "
                "float64 spectra (~40*N bytes) -> threshold reported",
    }
    out["wall_clock_s"] = round(elapsed(), 2)
    out["peak_rss_gb"] = round(peak_rss_gb(), 3)
    return out


def main():
    log("pipeline start")
    fields, index, meta = load_data()
    artifacts = {}
    phases = [
        (phase_pilot, (meta,)),
        (phase_t1a, (fields, meta)),
        (phase_t1b, (fields, meta)),
        (phase_t2, (fields, index, meta)),
        (phase_baselines, (fields, index, meta)),
        (phase_scaling, (meta,)),
    ]
    for phase, args in phases:
        if abort_check():
            break
        try:
            art = phase(*args)
            name = art["arm"]
            artifacts[name] = art
            with open(os.path.join(OUT, art["arm"] + ".json"), "w") as fh:
                json.dump(art, fh, indent=1, default=float)
            log(f"saved results/{art['arm']}.json")
        except Exception as e:
            log(f"PHASE FAILED {getattr(phase, '__name__', phase)}: {e!r}")
            artifacts["error_" + getattr(phase, "__name__", "?")] = {
                "error": repr(e)}
    summary = {
        "dataset.origin": meta["dataset.origin"],
        "simulation_marker": meta.get("simulation_marker"),
        "total_wall_clock_s": round(elapsed(), 2),
        "peak_rss_gb": round(peak_rss_gb(), 3),
        "arms_run": sorted([k for k in artifacts if not k.startswith("error_")]),
        "errors": [k for k in artifacts if k.startswith("error_")],
        "phase_log": LOG,
    }
    with open(os.path.join(OUT, "results_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    log(f"done: total {summary['total_wall_clock_s']}s, arms "
        f"{summary['arms_run']}")


if __name__ == "__main__":
    main()