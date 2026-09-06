#!/usr/bin/env python3
"""Reproducible spot-check asserting the traceability report (docs/verification/
report.md) values against the committed result artifacts under results/iter2/.

ASCII-only. Read-only against artifacts; prints a summary and exits 0 iff all
asserted values match within the stated tolerance.
"""
import json, pathlib, sys

WS = pathlib.Path("/workspace/research-project-manager/projects/circulant-krr-climate/results/iter2")
fails = []
checks = 0

def near(a, b, tol):
    return abs(a - b) <= tol

def check(name, got, want, tol=5e-3, rel=False):
    global checks
    checks += 1
    ok = near(got, want, tol) if not rel else abs(got - want) <= tol * abs(want)
    if not ok:
        fails.append(f"{name}: got {got} want {want}")
    return ok

# P0
p0 = json.load(open(WS / "P0-pilot-gate-real.json"))["results"]
check("P0 matern spectral rel", p0["matern32"]["spectral_vs_dense_torus_rel"], 2.62e-12, 0.1e-12)
check("P0 rbf spectral rel", p0["rbf"]["spectral_vs_dense_torus_rel"], 1.12e-12, 0.1e-12)
check("P0 matern free gap", p0["matern32"]["torus_vs_free_gap_rel"], 0.95, 0.01, True)
check("P0 rbf free gap", p0["rbf"]["torus_vs_free_gap_rel"], 0.116, 0.003)

# T1a table (matern32 and rbf)
t1a = json.load(open(WS / "T1a-spectral-reconstruction.json"))["per_mask_metrics"]
rows = {
    "random_10%": (0.0843, 0.898, 0.2525, 0.873),
    "random_30%": (0.0856, 0.892, 0.2411, 0.893),
    "random_50%": (0.0872, 0.886, 0.2356, 0.892),
    "halo_w1":  (0.0827, 0.896, 0.2789, 0.856),
    "halo_w2":  (0.0816, 0.897, 0.2839, 0.816),
    "halo_w4":  (0.0880, 0.877, 0.3155, 0.824),
}
for m, (mR, mC, rR, rC) in rows.items():
    mv = t1a[f"matern32|{m}"]; rv = t1a[f"rbf|{m}"]
    check(f"T1a matern {m} rmse", mv["rmse_mean"], mR, 0.0005)
    check(f"T1a matern {m} cov", mv["conformal_coverage"], mC, 0.002)
    check(f"T1a rbf {m} rmse", rv["rmse_mean"], rR, 0.0005)
    check(f"T1a rbf {m} cov", rv["conformal_coverage"], rC, 0.002)
check("T1a halo_w2 decay mat", t1a["matern32|halo_w2"]["decay_subset_coverage"], 0.747, 0.002)
check("T1a halo_w4 seam mat", t1a["matern32|halo_w4"]["seam_subset_coverage"], 0.836, 0.002)
check("T1a halo_w4 decay mat", t1a["matern32|halo_w4"]["decay_subset_coverage"], 0.739, 0.002)

# T1b canonical
t1b = json.load(open(WS / "T1b-CG-masked-train.json"))
check("T1b 10% iters", t1b["rate_10%"]["iterations_mean"], 280.875, 0.02)
check("T1b 50% iters", t1b["rate_50%"]["iterations_mean"], 245.125, 0.02)
check("T1b 10% rmse", t1b["rate_10%"]["rmse_on_masked_mean"], 0.541, 0.001)
check("T1b 30% rmse", t1b["rate_30%"]["rmse_on_masked_mean"], 0.529, 0.001)

# T2
t2 = json.load(open(WS / "T2-ENSO-index.json"))["functional_vs_zero_model"]
check("T2 functional", t2["rmse_functional"], 0.0856, 0.0005)
check("T2 direct", t2["rmse_direct_head"], 0.2696, 0.0005)
check("T2 zero", t2["rmse_zero_model"], 0.7955, 0.0005)
check("T2 corr", json.load(open(WS / "T2-ENSO-index.json"))["corr_functional"], 0.997, 0.001)

# T3 table
t3 = json.load(open(WS / "T3-forecast-transfer.json"))
expected = {"1": (0.268, 0.251, 0.773, 0.241, 0.880),
            "3": (0.565, 0.562, 0.773, 0.508, 0.466),
            "6": (0.796, 0.907, 0.773, 0.766, -0.061),
            "12": (0.923, 1.154, 0.773, 0.879, -0.427)}
for h, (t, p, c, a, s) in expected.items():
    b = t3["horizons"][h]
    check(f"T3 h{h} transfer", b["transfer"]["rmse"], t, 0.002)
    check(f"T3 h{h} pers", b["persistence"]["rmse"], p, 0.002)
    check(f"T3 h{h} clim", b["climatology"]["rmse"], c, 0.002)
    check(f"T3 h{h} ar1", b["ar1"]["rmse"], a, 0.002)
    check(f"T3 h{h} skill", b["skill_vs_climatology_transfer"], s, 0.002)
check("T3 h1 margin", t3["horizons"]["1"]["margin_vs_best"], -0.0137, 0.001)
check("T3 se range lo", t3["bootstrap_se_range_all_comparisons"][0], 0.0056, 0.001)
check("T3 se range hi", t3["bootstrap_se_range_all_comparisons"][1], 0.333, 0.002)
# RESOLUTION & RATIOS (B baseline + R resolution)
rr = json.load(open(WS / "RESOLUTION-AND-RATIOS.json"))
check("R recon native", rr["resolution_sensitivity"]["native_5deg"]["rmse_mean"], 0.0853, 0.0005)
check("R recon coarse", rr["resolution_sensitivity"]["coarsened_10deg"]["rmse_mean"], 0.1667, 0.001)
check("R func native", rr["resolution_functional"]["native_5deg_box"]["rmse"], 0.0856, 0.0005)
check("R func coarse", rr["resolution_functional"]["coarsened_10deg_box"]["rmse"], 0.3825, 0.001)
check("R func corr coarse", rr["resolution_functional"]["coarsened_10deg_box"]["corr"], 0.950, 0.002)
check("B spectral rmse", rr["flop_byte_ratio_control"]["spectral_2592"]["rmse"], 0.0999, 0.0005)
check("B ridge_2000 rmse", rr["flop_byte_ratio_control"]["ridge_2000"]["rmse"], 0.824, 0.001)
check("B trivial zero", rr["trivial_baselines"]["zero_model_rmse"], 0.801, 0.001)
check("B trivial mean", rr["trivial_baselines"]["global_mean_rmse"], 0.605, 0.001)
check("B trivial climat", rr["trivial_baselines"]["per_cell_train_climatology_rmse"], 0.813, 0.001)

# S scaling + footprint
s = json.load(open(WS / "S-scaling.json"))
check("S N10368 time", s["grids"]["scaling-144x72"]["wall_clock_s"], 0.0005, 0.0002)
check("S est bytes MB", s["extrapolation"]["est_bytes"]/1e6, 41.47, 0.5)
rs = json.load(open(WS / "results_summary.json"))
check("footprint wall", rs["total_wall_clock_s"], 78.7, 0.3)
check("footprint rss", rs["peak_rss_gb"], 1.57, 0.02)

verdict = t3["aggregate_verdict"]["verdict"]
check("T3 aggregate REFUTED", 1 if verdict == "REFUTED" else 0, 1)

print(f"checks_run={checks}")
if fails:
    print("FAILS:")
    for f in fails:
        print(" -", f)
    print("CHECK_FAIL")
    sys.exit(1)
print("CHECK_OK")
