#!/usr/bin/env python3
"""Verification of results/analyze-iter4.json (the iteration-4 analysis
artifact). Independent re-derivation, not trust:

- parses; the 6 verification flags are all true and carry method text
- pooled 2D-claim medians recomputed from A1-F1.json rows (n=90; capture via
  the positive-DST2 restriction rd2 > 0.5, verify_iter4.py convention) and
  compared to the A1-F1 pooled_2d_claim block AND to analyze-iter4 values
- per-grid support medians (w_s / s / coverage) recomputed from rows and
  compared to per_grid.support and to analyze-iter4 values
- A2 pooled speedup / convergence recomputed from A2-F2.json rows and
  compared to the artifact pooled block and to analyze-iter4 values
- A3 grf-2d method medians + tieband/strict winners recomputed from
  A3-multidomain.json rows and compared to the artifact + analyze-iter4
- T1b figures re-read from results/iter2/T1b-CG-masked-train.json and
  compared to the analyze-iter4 t1b_canonical_lock text (canonical lock)
- every iteration-3 signature figure inside analyze-iter4 sits in a string
  carrying the INVALIDATED / honest-negative attribution (bracket scan)
- no pre-fix T1b literals anywhere in analyze-iter4 (byte + word scans)
- verdicts match the iter4 artifact verdicts; ASCII-only content

Exit code 0 iff every check passes.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "results", "analyze-iter4.json")
OUT = os.path.join(ROOT, "results", "iter4")

failures = []
notes = []


def check(cond, msg):
    if cond:
        notes.append("PASS: " + msg)
    else:
        failures.append("FAIL: " + msg)


def load(p):
    return json.load(open(p, encoding="utf-8"))


def median(xs):
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.median(xs)) if xs else None


def walk(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            walk(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, out)
    elif isinstance(obj, str):
        out.append(obj)


def main():
    # 0. artifact parses
    raw = open(A, encoding="utf-8").read()
    try:
        an = load(A)
        check(True, "analyze-iter4.json parses")
    except Exception as exc:  # noqa: BLE001
        check(False, "analyze-iter4.json parses (%s)" % exc)
        print(failures)
        sys.exit(1)

    # 1. six flags, all true, with method text
    fl = an["verification"]["flags"]
    names = ["parses", "verdicts_match_artifacts", "t1b_canonical_lock",
             "iter3_only_invalidated", "no_pre_fix_figures",
             "ranges_artifact_traceable"]
    for n in names:
        check(n in fl, "flag '%s' present" % n)
        if n in fl:
            check(bool(fl[n].get("value")) is True and
                  isinstance(fl[n].get("method"), str) and len(fl[n]["method"]) > 0,
                  "flag '%s' true with method text" % n)

    # 2. pooled 2D-claim recomputation (A1-F1 rows) vs artifact + analysis
    a1 = load(os.path.join(OUT, "A1-F1.json"))
    claim = [r for r in a1["rows"] if len(r["grid"]) == 2 and r.get("f1_w_design")]
    check(len(claim) == 90, "claim rows n = 90 (%d)" % len(claim))
    red = [100.0 * (1.0 - r["gap_f1"] / r["gap_bccb"]) for r in claim
           if r["gap_bccb"] > 1e-30]
    res = [r["res_f1"] for r in claim]
    cap = []
    for r in claim:
        rd2 = 100.0 * (1.0 - r["gap_dst2"] / r["gap_bccb"])
        if r["gap_bccb"] > 1e-30 and rd2 > 0.5:
            cap.append(100.0 * (1.0 - r["gap_f1"] / r["gap_bccb"]) / rd2)
    red_dst2 = [100.0 * (1.0 - r["gap_dst2"] / r["gap_bccb"]) for r in claim]
    m_red, m_res, m_cap = median(red), median(res), median(cap)
    m_bccb = median([r["gap_bccb"] for r in claim])
    m_dst2 = median(red_dst2)
    pool = a1["pooled_2d_claim"]
    # against the execution artifact
    for expr, val, field in ((m_red, pool["median_gap_reduction_pct"], "median_gap_reduction_pct"),
                             (m_res, pool["median_relative_system_residual"], "median_relative_system_residual"),
                             (m_cap, pool["median_capture_vs_dst2_pct"], "median_capture_vs_dst2_pct"),
                             (m_bccb, pool["median_gap_bccb"], "median_gap_bccb"),
                             (m_dst2, pool["median_gap_reduction_dst2_pct"], "median_gap_reduction_dst2_pct")):
        check(val is not None and abs(val - expr) < 1e-9,
              "pooled %s recomputed == A1-F1 artifact (%.10g)" % (field, expr))
    # against the analysis artifact
    p2 = an["verdicts_by_arm"]["s1_prime_f1"]["clause_level_evidence"]["pooled_2d_claim"]
    for expr, field in ((m_red, "median_gap_reduction_pct"),
                        (m_res, "median_relative_system_residual"),
                        (m_cap, "median_capture_vs_dst2_pct"),
                        (m_bccb, "median_gap_bccb"),
                        (m_dst2, "median_gap_reduction_dst2_pct")):
        check(abs(p2[field] - expr) < 1e-9,
              "pooled %s recomputed == analyze-iter4 (%.10g)" % (field, expr))

    # 3. per-grid support medians from rows vs artifact + analysis
    for gk, dim in (("64,64", (64, 64)), ("128,128", (128, 128))):
        gr = [r for r in claim if tuple(r["grid"]) == dim]
        ws = [r["f1_w_design"]["support_w_s"] for r in gr]
        ss = [r["f1_w_design"]["support_s"] for r in gr]
        cov = [r["f1_w_design"]["coverage"] for r in gr]
        pg = a1["per_grid"][gk]["support"]
        check(pg["median_w_s"] == median(ws) and pg["max_w_s"] == max(ws),
              "%s support w_s recomputed (median %g max %g)" % (gk, median(ws), max(ws)))
        check(pg["median_s"] == median(ss), "%s support s recomputed (%g)" % (gk, median(ss)))
        check(abs(pg["median_coverage"] - median(cov)) < 1e-12,
              "%s coverage recomputed (%g)" % (gk, median(cov)))
        pg2 = an["verdicts_by_arm"]["s1_prime_f1"]["clause_level_evidence"]["per_grid_rows"][
            {("64,64"): "64x64", ("128,128"): "128x128"}[gk]]["support"]
        check(pg2["median_w_s"] == median(ws) and pg2["median_s"] == median(ss),
              "%s support medians in analyze-iter4 == recomputed" % gk)

    # 4. A2 pooled speedup / convergence from rows
    a2 = load(os.path.join(OUT, "A2-F2.json"))
    rows = a2["rows"]
    spd = [r["pcg"]["wall_s"] / r["ssam"]["wall_s"] for r in rows
           if r["pcg"].get("wall_s") and r["ssam"].get("wall_s") and
           r["pcg"]["wall_s"] > 0]
    m_spd = median(spd)
    conv_s = sum(1 for r in rows if r["ssam"]["conv"]) / len(rows)
    conv_p = sum(1 for r in rows if r["pcg"]["conv"]) / len(rows)
    m_res_s = median([r["ssam"]["rel_res"] for r in rows])
    m_res_p = median([r["pcg"]["rel_res"] for r in rows])
    m_it_s = median([r["ssam"]["iters"] for r in rows])
    m_it_p = median([r["pcg"]["iters"] for r in rows])
    po = a2["pooled"]
    check(len(rows) == 147 and po["n_rows"] == len(rows), "A2 rows n = 147")
    check(abs(po["median_speedup_vs_pcg"] - m_spd) < 1e-9,
          "A2 median speedup recomputed (%.12g)" % m_spd)
    check(abs(po["ssam_converged_frac"] - conv_s) < 1e-12 and
          abs(po["pcg_converged_frac"] - conv_p) < 1e-12, "A2 conv fractions recomputed")
    check(abs(po["median_relative_residual_ssam"] - m_res_s) < 1e-18 and
          abs(po["median_relative_residual_pcg"] - m_res_p) < 1e-18,
          "A2 median rel residuals recomputed")
    check(po["median_iters_ssam"] == m_it_s and po["median_iters_pcg"] == m_it_p,
          "A2 median iters recomputed")
    e2 = an["verdicts_by_arm"]["s2_prime_f2"]["evidence"]
    check(abs(e2["median_speedup_vs_pcg"] - m_spd) < 1e-9,
          "analyze-iter4 A2 speedup == recomputed")
    check(abs(e2["ssam"]["converged_frac"] - conv_s) < 1e-12,
          "analyze-iter4 A2 ssam conv == recomputed")
    check(e2["pcg"]["converged_frac"] == conv_p, "analyze-iter4 A2 pcg conv == recomputed")
    check(e2["ssam"]["median_relative_residual"] == m_res_s and
          e2["pcg"]["median_relative_residual"] == m_res_p,
          "analyze-iter4 A2 residual medians == recomputed")

    # 5. A3 grf-2d method medians + winners from rows
    a3 = load(os.path.join(OUT, "A3-multidomain.json"))
    r2 = [r for r in a3["rows"] if r["domain"] == "grf-2d"]
    check(len(r2) == 24 and a3["n"] == len(r2), "A3 rows n = 24 (grf-2d only)")
    med = {}
    for m in ("f1_exact", "pcg", "dense", "kiss", "rff"):
        med[m] = median([r[m]["rmse_valid"] for r in r2
                         if r[m].get("rmse_valid") is not None])
    pd = a3["per_domain"]["grf-2d"]
    check(len(r2) == 24 and pd["n_rows"] == len(r2), "A3 grf-2d rows n = 24")
    for m in med:
        check(abs(pd[m + "_median_rmse"] - med[m]) < 1e-12,
              "A3 grf-2d %s median rmse recomputed (%.12g)" % (m, med[m]))
    best = min(med, key=med.get)
    bv = med[best]
    tieband = 0.005
    tied = [k for k, v in med.items() if v <= bv * (1.0 + tieband)]
    wl = {m: median([r[m]["wall_s"] for r in r2 if r[m].get("wall_s")]) for m in med}
    wb = wl[best]
    winners = [m for m in tied if wl[m] is not None and wb is not None and
               wl[m] <= wb + 0.1]
    strict = [k for k, v in med.items() if v <= bv + 1e-15]
    check(best == "dense" and winners == ["dense"], "A3 tieband+cost winner = dense")
    check(strict == ["dense"], "A3 strict no-tieband winner = dense")
    check(a3["kiss_wins"] == 0 and a3["dense_wins"] == 1 and
          a3["benchmark_verdict"] == "REFUTED", "A3 verdict REFUTED (dense_wins 1)")
    e3 = an["verdicts_by_arm"]["benchmark_a3"]["evidence"]["per_domain_grf_2d"]
    for m in med:
        check(abs(e3[m + "_median_rmse"] - med[m]) < 1e-12,
              "analyze-iter4 A3 %s median == recomputed" % m)
    # verdict-level match: analysis verdict == artifact verdict
    check(an["verdicts_by_arm"]["benchmark_a3"]["verdict"] == a3["benchmark_verdict"],
          "analyze-iter4 benchmark verdict == A3 artifact (REFUTED)")

    # 6. T1b canonical lock re-read
    t1b = load(os.path.join(ROOT, "results", "iter2", "T1b-CG-masked-train.json"))
    got = {
        "r10": t1b["rate_10%"]["iterations_mean"], "r30": t1b["rate_30%"]["iterations_mean"],
        "r50": t1b["rate_50%"]["iterations_mean"],
        "span_min": min(f["iterations"] for k in ("rate_10%", "rate_30%", "rate_50%")
                        for f in t1b[k]["details"]),
        "span_max": max(f["iterations"] for k in ("rate_10%", "rate_30%", "rate_50%")
                        for f in t1b[k]["details"]),
        "res_min": min(f["relative_residual"] for k in ("rate_10%", "rate_30%", "rate_50%")
                       for f in t1b[k]["details"]),
        "res_max": max(f["relative_residual"] for k in ("rate_10%", "rate_30%", "rate_50%")
                       for f in t1b[k]["details"]),
        "rmse_min": min(t1b[k]["rmse_on_masked_mean"] for k in ("rate_10%", "rate_30%", "rate_50%")),
        "rmse_max": max(t1b[k]["rmse_on_masked_mean"] for k in ("rate_10%", "rate_30%", "rate_50%")),
    }
    lock = an["honest_framing"]["t1b_canonical_lock"]
    check("results/iter2/T1b-CG-masked-train.json" in lock,
          "T1b lock cites the canonical artifact path")
    nums = re.findall(r"\d+\.?\d*", lock)
    vals = [float(x) for x in nums]
    check(245.125 in vals and 276.125 in vals and 280.875 in vals,
          "T1b rate means present in lock text")
    check(233.0 in vals and 291.0 in vals, "T1b span present in lock text")
    check(abs(got["r10"] - 280.875) < 1e-9 and abs(got["r30"] - 276.125) < 1e-9 and
          abs(got["r50"] - 245.125) < 1e-9, "T1b rate means == canonical artifact")
    check(got["span_min"] == 233 and got["span_max"] == 291, "T1b span == canonical artifact")
    check(got["res_min"] > 4.6e-9 and got["res_min"] < 4.7e-9 and
          got["res_max"] > 9.8e-9 and got["res_max"] < 9.9e-9,
          "T1b residual span 4.69e-9..9.81e-9 == canonical artifact")
    check(got["rmse_min"] > 0.529 and got["rmse_max"] < 0.542,
          "T1b RMSE means 0.529-0.541 == canonical artifact")

    # 7. iteration-3 signature figures only inside INVALIDATED/honest strings
    texts = []
    walk(an, texts)
    sig3 = ["47.3574", "532.2245", "546.2021", "415.7885", "61.62", "0.7467",
            "0.7284", "0.2374x", "0.1560x", "0.1624x", "278.5", "192.0",
            "77.7", "0.3504163", "0.3504185", "1530.3", "2296.5", "0.9786",
            "44.81", "85.60", "259-384", "4.1e5", "7.4e5", "117.43",
            "896.4332", "1233", "2385", "35.6448", "-1872.63"]
    for sig in sig3:
        hits = [t for t in texts if sig in t]
        for t in hits:
            check("INVALIDATED" in t or "invalidated" in t or
                  "honest negative" in t or "motivation" in t,
                  "iter-3 figure '%s' only in attributed string" % sig)
    # the signature list itself appears only in the flag method text, which
    # also carries the attribution wording
    check(any("signature figures" in t and "INVALIDATED" in t for t in texts
              if "grep-audited" in t), "iter-3 scan method text carries attribution")

    # 8. no pre-fix literals (word-boundary tokens; digits inside real
    #    measured values such as 0.3738630620645507 do not match)
    for pat in (r"\b420\b", r"\b550\b", r"\b0\.78\b", r"\b0\.83\b",
                r"420-550", r"0\.78-0\.83"):
        check(len(re.findall(pat, raw)) == 0,
              "no pre-fix literal '%s' anywhere" % pat)

    # 9. verdict-level matches across arms
    check(an["verdicts_by_arm"]["s1_prime_f1"]["verdict"] == a1["s1_verdict"],
          "analyze S1' verdict == A1 artifact (NOT-validated-guard)")
    check(an["verdicts_by_arm"]["s2_prime_f2"]["verdict"] == a2["s2_verdict"],
          "analyze S2' verdict == A2 artifact (REFUTED)")
    a4 = load(os.path.join(OUT, "A4-tooling.json"))
    check(an["verdicts_by_arm"]["a4_tooling"]["verdict"] == "pass" and
          bool(a4["selfcheck_pass"]), "analyze A4 verdict == A4 artifact (pass)")

    # 10. ASCII-only + cross_arm values vs results_summary
    try:
        raw.encode("ascii")
        check(True, "analyze-iter4.json is ASCII-only")
    except UnicodeEncodeError:
        check(False, "analyze-iter4.json is ASCII-only")
    sm = load(os.path.join(OUT, "results_summary.json"))
    ca = an["cross_arm_summary"]
    check(abs(ca["total_wall_clock_s"] - sm["total_wall_clock_s"]) < 1e-9,
          "cross_arm total == results_summary (2571.3 s)")
    check(abs(ca["peak_rss_gb"] - sm["peak_rss_gb"]) < 1e-12,
          "cross_arm peak RSS == results_summary (1.0479583740234375 GB)")
    check(ca["hard_stop_45min"] is True and sm["hard_stop_45min"] is True,
          "45-min hard stop flag consistent")

    # 11. report
    print("=" * 72)
    print("ANALYZE-ITER4 VERIFICATION (independent re-derivation)")
    print("=" * 72)
    for n in notes:
        print(n)
    for f in failures:
        print(f)
    print("-" * 72)
    print("checks:", len(notes) + len(failures), "failures:", len(failures))
    print("S1' pooled (recomputed): gap=%.6f%% res=%.6g capture=%.4f dst2=%.6f%% "
          "bccb=%.6g" % (m_red, m_res, m_cap, m_dst2, m_bccb))
    print("A2 pooled (recomputed): speedup=%.6fx conv_ssam=%.4f conv_pcg=%.4f" %
          (m_spd, conv_s, conv_p))
    print("A3 (recomputed): best=dense winners_0.005=%s strict=%s -> %s" %
          (winners, strict, a3["benchmark_verdict"]))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()