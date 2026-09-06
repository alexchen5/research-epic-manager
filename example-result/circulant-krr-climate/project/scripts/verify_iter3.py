#!/usr/bin/env python3
"""Verifies + completes results/iter3/*.json.

Verifies: JSON parse, required schema keys, verdicts recomputed from pooled
quantities, honest flags surfaced. Completes (in place, conservatively):
per-arm wall_clock_s from the arm clock, peak_rss_gb from the run peak
(upper bound; the run itself was arm-clock-scoped but the RSS peak is the
whole-run max -- recorded with an explicit note), win_rule_label aliases.
"""
import json
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "iter3")
REQUIRED_COMMON = ["arm", "dataset.origin", "simulation_marker", "wall_clock_s"]
problems = []
files = ["A1-boundary.json", "A2-masked.json", "A3-multidomain.json",
         "A4-scaling.json", "A5-ablation.json", "A6-tooling.json",
         "joint-S1xS2.json", "results_summary.json", "meta.json"]

sm_path = os.path.join(OUT, "results_summary.json")
peak = None
if os.path.exists(sm_path):
    try:
        peak = json.load(open(sm_path)).get("peak_rss_gb")
    except Exception:
        pass

for f in ["A1-boundary.json", "A2-masked.json", "A3-multidomain.json",
          "A4-scaling.json", "A5-ablation.json", "A6-tooling.json"]:
    p = os.path.join(OUT, f)
    if not os.path.exists(p):
        problems.append(f"missing {f}")
        continue
    try:
        d = json.load(open(p))
    except Exception as exc:
        problems.append(f"{f}: parse error {exc}")
        continue
    changed = False
    if "wall_clock_s" not in d and "clock_elapsed_s" in d:
        d["wall_clock_s"] = d["clock_elapsed_s"]
        changed = True
    if "peak_rss_gb" not in d and peak is not None:
        d["peak_rss_gb"] = peak
        d["peak_rss_note"] = ("whole-run peak RSS (upper bound); the arm "
                              "clock is arm-scoped")
        changed = True
    if f == "A1-boundary.json" and "n_negative_eigenvalues_by_grid" not in d:
        # retrocompute the n_neg disclosure table (cheap spec builds)
        import numpy as np
        import fft_krr_embed as fe
        tbl = {}
        for g in [(64, 64), (128, 128), (24, 24, 24)]:
            tbl[",".join(map(str, g))] = {}
            for kn in ("matern32", "matern52", "rbf"):
                c1 = fe.first_column_nd(g, fe.make_nd_kernel(kn))
                sp = np.fft.rfftn(fe.embed_wss_nd(c1, g)).real
                tbl[",".join(map(str, g))][kn] = int((sp < -1e-14).sum())
        d["n_negative_eigenvalues_by_grid"] = tbl
        d["n_neg_table_note"] = "retrocomputed by verify_iter3.py"
        changed = True
    for k in REQUIRED_COMMON:
        if k not in d:
            problems.append(f"{f}: missing {k}")
    if changed:
        json.dump(d, open(p, "w"), indent=1, default=float)
        print(f"{f}: filled wall_clock_s/peak_rss_gb")

a1 = json.load(open(os.path.join(OUT, "A1-boundary.json")))
a2 = json.load(open(os.path.join(OUT, "A2-masked.json")))
a3 = json.load(open(os.path.join(OUT, "A3-multidomain.json")))
js = json.load(open(os.path.join(OUT, "joint-S1xS2.json")))
sm = json.load(open(sm_path))

p1 = a1["pooled"]
red = p1["median_gap_reduction_w_design_vs_bccb_pct"]
res1 = p1["median_res_w_design"]
exp1 = ("win" if (red is not None and red >= 50.0 and res1 is not None
                  and res1 <= 1e-6) else "NOT-validated")
if a1["s1_verdict"] != exp1:
    problems.append(f"A1 verdict {a1['s1_verdict']} != recomputed {exp1}")
p2 = a2["pooled"]
spd = p2["median_speedup_ssam_vs_pcg_synthetic"]
res2 = p2["median_rel_res_ssam"]
exp2 = ("win" if (spd is not None and spd >= 3.0 and res2 is not None
                  and res2 < 1e-6) else
        ("REFUTED" if (spd is not None and spd < 1.5) else "NOT-validated"))
if a2["s2_verdict"] != exp2:
    problems.append(f"A2 verdict {a2['s2_verdict']} != recomputed {exp2}")
if js.get("s1_verdict") != a1["s1_verdict"] or js.get("s2_verdict") != a2["s2_verdict"]:
    problems.append("joint verdict mismatch")

print("iter3 artifacts verified:", not problems)
for p_ in problems:
    print("  PROBLEM:", p_)
print("A1 verdict:", a1["s1_verdict"], "| median res w_design:",
      p1["median_res_w_design"], "| median gap reduction %:",
      p1["median_gap_reduction_w_design_vs_bccb_pct"])
print("A2 verdict:", a2["s2_verdict"], "| median speedup:",
      p2["median_speedup_ssam_vs_pcg_synthetic"])
print("A3 verdict:", a3["benchmark_verdict"], "| kiss_wins:", a3["kiss_wins"],
      "| dense_wins:", a3["dense_wins"])
print("summary arms:", {k: (v.get("verdict") or v.get("selfcheck"))
                        for k, v in sm["arms"].items()})
sys.exit(1 if problems else 0)