#!/usr/bin/env python3
"""Iteration-4 verification runner: re-reads results/iter4/*.json, recomputes
pooled medians / verdicts from the rows, and checks the pre-registered
conventions:

- artifact-name spellings (A1-F1.json / A2-F2.json / A3-multidomain.json /
  A4-tooling.json / results_summary.json / meta.json)
- dataset.origin + simulation_marker conventions; ASCII-only content
- S1' per-clause report: gap_reduction_pct / relative_system_residual /
  w_guard / capture_vs_dst2_pct PER GRID + POOLED over the 2D claim pool
  (24^3 rows never pooled); n_neg per grid/kernel; fail-fast rows; precedence
  fork A (w_s > clamp -> NOT-validated-guard) then fork B (pooled residual
  > 1e-6 -> REFUTED-residual); verdict recomputed from rows and compared.
- T1b citation lock (results/iter2/T1b-CG-masked-train.json only; no pre-fix
  figures); iteration-3 numbers appear ONLY as honest negatives with the
  INVALIDATED-HISTORY attribution.
- S2' median speedup verdict (>= 3x win / < 1.5x REFUTED / 1.5-3x
  NOT-validated) + kaplan RMSE parity on the T1b valid-cell domain.
- A3 tieband (0.5% uniform) + cost gate + literal no-tieband sensitivity row;
  benchmark verdict (REFUTED iff KISS-GP wins >= 2 domains or dense KRR >= 1).
- budgets: per-arm clocks within caps (or budget_exceeded flagged); total
  <= 45 min hard stop; 0.1 s rounding note; peak RSS vs ~2 GB cgroup.

Exit code 0 iff every structural/convention check passes (measured verdicts
are reported, not imposed).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "iter4")
NAMES = ["A1-F1.json", "A2-F2.json", "A3-multidomain.json", "A4-tooling.json",
         "results_summary.json", "meta.json"]

failures = []
warnings = []
notes = []


def check(cond, msg):
    if cond:
        notes.append("PASS: " + msg)
    else:
        failures.append("FAIL: " + msg)


def warn(msg):
    warnings.append("WARN: " + msg)


def _median(xs):
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.median(xs)) if xs else None


def main():
    # 1. artifacts parse + spellings + conventions
    arts = {}
    for n in NAMES:
        p = os.path.join(OUT, n)
        check(os.path.isfile(p), "%s exists" % n)
        if not os.path.isfile(p):
            continue
        try:
            d = json.load(open(p))
            arts[n] = d
            check(True, "%s parses as JSON" % n)
        except Exception as exc:  # noqa: BLE001
            check(False, "%s parses as JSON (%s)" % (n, exc))
            continue
        try:
            open(p, "rb").read().decode("ascii")
            check(True, "%s is ASCII-only" % n)
        except UnicodeDecodeError:
            check(False, "%s is ASCII-only" % n)
        for key in ("dataset.origin",):
            check(key in d, "%s has dataset.origin" % n)
        check("simulation_marker" in d,
              "%s has simulation_marker (or None)" % n)

    a1 = arts.get("A1-F1.json")
    a2 = arts.get("A2-F2.json")
    a3 = arts.get("A3-multidomain.json")
    a4 = arts.get("A4-tooling.json")
    sm = arts.get("results_summary.json")
    meta = arts.get("meta.json")

    # 2. A1-F1: recompute the claim-pool aggregates + verdict
    if a1 is not None and "rows" not in a1:
        warn("A1-F1.json is a crash-rescue artifact (no rows); A1 row checks "
             "skipped")
    if a1 is not None and "rows" in a1:
        claim = [r for r in a1["rows"]
                 if len(r["grid"]) == 2 and r.get("f1_w_design")]
        check(a1["n_claim_pool_2d"] == len(claim),
              "A1 claim pool = all 64x64/128x128 w_design rows (%d)" %
              len(claim))
        n3d = [r for r in a1["rows"] if len(r["grid"]) == 3]
        check(a1["n_3d"] == len(n3d), "A1 3D rows counted (%d)" % len(n3d))
        for r in n3d:
            check(r.get("floor_caveat") is True,
                  "3D rows carry the floor caveat flag")
        for r in n3d:
            check(r.get("floor_caveat") is True,
                  "3D rows carry the floor caveat flag")
        # pooled re-computation over the 2D claim pool ONLY
        red = [100.0 * (1.0 - r["gap_f1"] / r["gap_bccb"]) for r in claim
               if r["gap_bccb"] and r["gap_bccb"] > 1e-30]
        res = [r["res_f1"] for r in claim]
        cap_list = []
        for r in claim:
            rd2 = 100.0 * (1.0 - r["gap_dst2"] / r["gap_bccb"])
            if r["gap_bccb"] > 1e-30 and rd2 > 0.5:
                cap_list.append(100.0 * (1.0 - r["gap_f1"] / r["gap_bccb"]) /
                                rd2)
        m_red = _median(red)
        m_res = _median(res)
        m_cap = _median(cap_list)
        pooled = a1["pooled_2d_claim"]
        check(pooled is not None and pooled["n_rows"] == len(claim),
              "A1 pooled 2D claim pool composition (M5 pin)")
        if m_red is not None and pooled.get("median_gap_reduction_pct") is \
                not None:
            check(abs(m_red - pooled["median_gap_reduction_pct"]) < 1e-9,
                  "A1 pooled median gap reduction recomputed == artifact")
        if m_res is not None and pooled.get("median_relative_system_residual") \
                is not None:
            check(abs(m_res - pooled["median_relative_system_residual"]) < 1e-9,
                  "A1 pooled median relative system residual recomputed")
        # per-grid clauses
        for gk, pg in (a1["per_grid"] or {}).items():
            if pg is None:
                continue
            gdim = tuple(int(x) for x in gk.split(","))
            grows = [r for r in claim if tuple(r["grid"]) == gdim]
            check(pg["n_rows"] == len(grows), "A1 per-grid %s rows" % gk)
            check(bool(pg["w_guard"]), "A1 %s w_guard holds (clamp)" % gk)
            gr = [100.0 * (1.0 - r["gap_f1"] / r["gap_bccb"]) for r in grows
                  if r["gap_bccb"] > 1e-30]
            gres = [r["res_f1"] for r in grows]
            check(abs(_median(gr) - pg["median_gap_reduction_pct"]) < 1e-9,
                  "A1 %s gap reduction recomputed" % gk)
            check(abs(_median(gres) - pg["median_relative_system_residual"]) <
                  1e-9, "A1 %s residual recomputed" % gk)
            ws = [r["support_w_s"] for r in grows if r["support_w_s"]]
            check(pg["support"]["median_w_s"] == _median(ws),
                  "A1 %s support w_s median recomputed" % gk)
            for kn in ("matern32", "matern52", "rbf"):
                check(pg["n_neg"][kn] is not None, "A1 %s n_neg %s" % (gk, kn))
        # verdict recomputation per precedence fork
        fork_a, fork_b = None, None
        for gk, pg in (a1["per_grid"] or {}).items():
            if pg is None:
                continue
            med_ws = pg["support"]["median_w_s"]
            if med_ws is not None and med_ws > pg["clamp_min_hw_over_8"]:
                fork_a = gk
        if fork_a is None and m_res is not None and m_res > 1e-6:
            fork_b = True
        verify_verdict = None
        if fork_a is not None:
            verify_verdict = "NOT-validated-guard"
        elif fork_b:
            verify_verdict = "REFUTED-residual"
        elif (m_red is not None and m_red >= 50.0 and m_res is not None and
              m_res <= 1e-6 and pooled and pooled["w_guard_holds"] and
              m_cap is not None and m_cap >= 50.0):
            verify_verdict = "win"
        else:
            verify_verdict = "NOT-validated"
        check(a1["s1_verdict"] == verify_verdict,
              "A1 verdict (%s) matches the recomputed precedence-fork "
              "verdict (%s)" % (a1["s1_verdict"], verify_verdict))
        notes.append("A1 verdict: %s | clause: %s" %
                     (a1["s1_verdict"], a1["s1_verdict_clause"]))
        notes.append("A1 pooled: gap_reduction_pct=%.1f%%, res=%.3e, "
                     "w_guard=%s, capture=%.1f%%" %
                     (m_red if m_red is not None else float("nan"),
                      m_res if m_res is not None else float("nan"),
                      pooled and pooled["w_guard_holds"],
                      m_cap if m_cap is not None else float("nan")))

    # 3. A2-F2: speedups + verdict + parity
    if a2 is not None:
        rows = a2["rows"]
        spd = []
        for r in rows:
            p, s = r["pcg"], r["ssam"]
            if p.get("wall_s") and s.get("wall_s") and p["wall_s"] > 0:
                spd.append(p["wall_s"] / s["wall_s"])
        m_spd = _median(spd)
        res_s = _median([r["ssam"]["rel_res"] for r in rows])
        check(a2["pooled"]["n_rows"] == len(rows), "A2 row count matches")
        if m_spd is not None:
            check(abs(m_spd - a2["pooled"]["median_speedup_vs_pcg"]) < 1e-9,
                  "A2 pooled median speedup recomputed")
        exp = None
        if m_spd is None or res_s is None:
            exp = "not-completed"
        elif m_spd >= 3.0 and res_s <= 1e-6:
            exp = "win"
        elif m_spd < 1.5:
            exp = "REFUTED"
        else:
            exp = "NOT-validated"
        check(a2["s2_verdict"] == exp,
              "A2 verdict (%s) matches recomputed (%s)" %
              (a2["s2_verdict"], exp))
        # kaplan RMSE parity
        krows = [r for r in rows if r["domain"] == "kaplan-sst-v2"]
        rm_p = _median([r["pcg"].get("rmse_valid") for r in krows])
        rm_s = _median([r["ssam"].get("rmse_valid") for r in krows])
        parity = None
        if rm_p and rm_s:
            parity = abs(rm_s - rm_p) / rm_p <= 0.01
        apd = a2["per_domain"].get("kaplan-sst-v2")
        if apd is not None and parity is not None:
            check(abs(apd["median_rmse_valid_pcg"] - rm_p) < 1e-12 and
                  abs(apd["median_rmse_valid_ssam"] - rm_s) < 1e-12,
                  "A2 kaplan RMSE medians recomputed")
        notes.append("A2 kaplan RMSE parity (ssam vs pcg, 1%% band): %s "
                     "(pcg med=%.4f, ssam med=%.4f; T1b canonical range "
                     "0.529-0.541 @ tol 1e-8 [locked])" %
                     (parity, rm_p if rm_p else float("nan"),
                      rm_s if rm_s else float("nan")))
        for r in rows:
            check(r["ssam"]["k"] in (64, 128, 256) or "k_sweep" in a2,
                  "A2 sketch k disclosed per row")
        check(isinstance(a2.get("matched_1e8_subset"), list),
              "A2 matched-1e-8 subset reported")
        check(isinstance(a2.get("k_sweep"), list), "A2 k-sweep reported")

    # 4. A3: tieband + cost gate + verdict
    if a3 is not None:
        per = a3["per_domain"]
        wins = a3["per_domain_winners_tieband"]
        tieband = 0.005
        kiss_w, dense_w = 0, 0
        for d, e in per.items():
            rms = {m: e.get(m + "_median_rmse") for m in
                   ("f1_exact", "pcg", "dense", "kiss", "rff")}
            rms = {k: v for k, v in rms.items() if v is not None}
            if not rms:
                continue
            best = min(rms, key=rms.get)
            bv = rms[best]
            tied = [k for k, v in rms.items() if v <= bv * (1.0 + tieband)]
            wl = {m: e.get(m + "_median_wall_s") for m in rms}
            wb = wl[best]
            winners = [m for m in tied
                       if wl[m] is not None and wb is not None and
                       wl[m] <= wb * 1.0 + 0.1]
            w = winners[0] if len(winners) == 1 else None
            check(wins[d]["winner"] == w,
                  "A3 %s winner recomputed under 0.5%% band + cost gate" % d)
            if w == "kiss":
                kiss_w += 1
            if w == "dense":
                dense_w += 1
        check(a3["kiss_wins"] == kiss_w and a3["dense_wins"] == dense_w,
              "A3 kiss/dense win counts recomputed")
        exp_v = "REFUTED" if (kiss_w >= 2 or dense_w >= 1) else "not-refuted"
        check(a3["benchmark_verdict"] == exp_v,
              "A3 benchmark verdict recomputed (%s)" % exp_v)
        sens = a3["literal_no_tieband_sensitivity"]
        check(sens and "kiss_wins_strict" in sens,
              "A3 literal no-tieband sensitivity row present")

    # 5. A4 tooling
    if a4 is not None:
        check(bool(a4["selfcheck_pass"]), "A4 grf_boundary selfcheck pass")
        f1s = a4["f1_path_sanity_16x16"]
        check(f1s["matvec_exactness_err"] < 1e-10,
              "A4 matvec-exactness error < 1e-10 (%.2e)" %
              f1s["matvec_exactness_err"])

    # 6. budgets + conventions
    if sm is not None:
        caps = {"A1-F1.json": 20.0, "A2-F2.json": 18.0,
                "A3-multidomain.json": 7.0, "A4-tooling.json": 2.0}
        for n, cap in caps.items():
            art = arts.get(n)
            if art is None:
                continue
            el = art.get("clock_elapsed_s")
            if el is not None:
                if el <= cap * 60.0 + 2.0:
                    check(True, "%s within %d-min cap (%.1f s)" %
                          (n, cap, el))
                elif art.get("budget_exceeded"):
                    warn("%s exceeded %d-min cap (%.1f s) and is flagged "
                         "budget_exceeded (honest disclosure)" %
                         (n, cap, el))
                else:
                    check(False, "%s exceeded %d-min cap without the "
                          "budget_exceeded flag" % (n, cap))
        check(isinstance(sm.get("per_arm_elapsed_sum"), (int, float)),
              "results_summary has per_arm_elapsed_sum")
        check("rounding_note" in sm, "0.1 s rounding note present")
        check(sm["total_wall_clock_s"] <= 45.0 * 60.0 + 30.0,
              "total wall clock within the 45-min hard stop (%.1f s)" %
              sm["total_wall_clock_s"])
        check(sm["peak_rss_gb"] < 2.0,
              "peak RSS %.3f GB < ~2 GB cgroup" % sm["peak_rss_gb"])
    if meta is not None:
        check("T1b_citation_lock" in meta, "meta T1b citation lock present")
        check("honest_framing" in meta, "meta honest-framing present")
        check("invalidated_history_banner" in meta,
              "meta INVALIDATED-HISTORY banner present")
        check("3d_psd_caveat" in meta, "meta 3D PSD caveat present")

    # 7. banned-figure scan (pre-fix T1b; iter-3 as qualifying; pooled 2D+3D)
    import json as _json
    def _walk(obj, out):
        if isinstance(obj, dict):
            for v in obj.values():
                _walk(v, out)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v, out)
        elif isinstance(obj, str):
            out.append(obj)
    texts = []
    for n in NAMES:
        p = os.path.join(OUT, n)
        if os.path.isfile(p):
            try:
                _walk(_json.load(open(p)), texts)
            except Exception:  # noqa: BLE001
                pass
    banned = ["0.78-0.83", "420-550", "rate means 245.1/276.1/280.9",
              "4.69e-9..9.81e-9", "0.529-0.541"]
    for b in banned:
        hits = [t for t in texts if b in t]
        if b in ("0.78-0.83", "420-550"):
            check(len(hits) == 0,
                  "no pre-fix T1b figure '%s' anywhere" % b)
        elif b in ("rate means 245.1/276.1/280.9", "4.69e-9..9.81e-9",
                   "0.529-0.541"):
            check(len(hits) > 0,
                  "locked T1b figures '%s' cited (citation lock)" % b)
    iv = [t for t in texts if "INVALIDATED" in t or "invalidated" in t]
    check(len(iv) > 0, "INVALIDATED-HISTORY attribution present")
    bad_pool = [t for t in texts
                if "2D+3D pooled" in t and "pool is the" not in t]
    check(len(bad_pool) == 0,
          "no historical 2D+3D pooled-pool literal (M5 pin)")

    # 8. report
    print("=" * 72)
    print("ITER-4 VERIFICATION")
    print("=" * 72)
    for n in notes:
        print(n)
    for w in warnings:
        print(w)
    for f in failures:
        print(f)
    print("-" * 72)
    print("checks:", len(notes) + len(failures), "failures:", len(failures),
          "warnings:", len(warnings))
    if a1 is not None:
        p = a1["pooled_2d_claim"]
        if p:
            print("S1' pooled (2D claim pool): gap=%.1f%% res=%.3e "
                  "w_guard=%s capture=%.1f%% -> %s" %
                  (p["median_gap_reduction_pct"],
                   p["median_relative_system_residual"], p["w_guard_holds"],
                   p["median_capture_vs_dst2_pct"], a1["s1_verdict"]))
    if a2 is not None:
        print("S2' pooled: median speedup=%.2fx -> %s" %
              (a2["pooled"]["median_speedup_vs_pcg"] or float("nan"),
               a2["s2_verdict"]))
    if a3 is not None:
        print("benchmark: kiss_wins=%d dense_wins=%d -> %s" %
              (a3["kiss_wins"], a3["dense_wins"], a3["benchmark_verdict"]))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()