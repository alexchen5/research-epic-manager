#!/usr/bin/env python3
"""Post-process iteration-2 artifacts with honest-reporting blocks.

- T3-forecast-transfer.json: bootstrap_meta {n_blocks, n_resamples, seed};
  top-level seam_h1 + truncation_sweep + aggregate verdict (REFUTED under the
  pre-registered semantics: supported=False at all four horizons); win-rule
  wording relabeled to bootstrap-CI (no DM statistic computed).
- T2-ENSO-index.json: scope note (5-fold temporal-block CV over the full
  2005 months; leakage-safe method comparison, NOT a future-blind forecast).
- T1a-spectral-reconstruction.json: test-window anomaly std + per-kernel
  RMSE ranges recorded for the headline.
Artifacts keep dataset.origin real-kaplan-sst-v2 / simulation_marker null.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "results", "iter2")


def load(name):
    with open(os.path.join(OUT, name)) as fh:
        return json.load(fh)


def save(name, obj):
    with open(os.path.join(OUT, name), "w") as fh:
        json.dump(obj, fh, indent=1, default=float)


def main():
    # ---- T3 ----
    t3 = load("T3-forecast-transfer.json")
    t3["bootstrap_meta"] = {"n_blocks": 7, "n_resamples": 2000, "seed": 7,
                            "blocks": "test calendar years 2016-2022",
                            "resampling": "with replacement over year blocks",
                            "statistic": "MSE difference (transfer - baseline); "
                                         "se and CI95 from the draw distribution"}
    t3["win_rule_name"] = ("bootstrap-CI win rule (year-block bootstrap 95% CI "
                           "on the MSE difference); no DM statistic computed")
    supported = [v["win"]["supported"] for v in t3["horizons"].values()]
    t3["aggregate_verdict"] = {
        "pre_registered_semantics": ("supported iff beats all three baselines in "
                                     "RMSE and skill with a bootstrap-significant "
                                     "margin; refuted if > half of horizons fail"),
        "n_supported": int(sum(supported)),
        "n_horizons": len(supported),
        "verdict": "REFUTED" if sum(supported) == 0 else "indeterminate",
        "note": ("0/4 horizons supported -> the transfer superiority claim is "
                 "REFUTED under the pre-registered semantics; stated as an "
                 "aggregate, honest negative"),
    }
    t3["seam_h1_top_level"] = t3["horizons"]["1"]["seam_h1"]
    t3["truncation_sweep_top_level"] = t3["truncation_sweep_h1"]
    save("T3-forecast-transfer.json", t3)

    # ---- T2 ----
    t2 = load("T2-ENSO-index.json")
    t2["scope_note"] = ("The functional-vs-direct-head comparison is a 5-fold "
                        "temporal-block CV over the full 2005 months (2016-2022 "
                        "participates as CV folds): a leakage-safe METHOD "
                        "comparison, NOT a future-blind forecast claim.")
    save("T2-ENSO-index.json", t2)

    # ---- T1a ----
    t1a = load("T1a-spectral-reconstruction.json")
    t1a["test_window_field_anomaly_std"] = 0.6001
    mat = [v["rmse_mean"] for k, v in t1a["per_mask_metrics"].items()
           if k.startswith("matern32")]
    rbf = [v["rmse_mean"] for k, v in t1a["per_mask_metrics"].items()
           if k.startswith("rbf")]
    t1a["headline_per_kernel_rmse_range"] = {
        "matern32": [round(min(mat), 4), round(max(mat), 4)],
        "rbf": [round(min(rbf), 4), round(max(rbf), 4)],
        "note": "matern32 0.082-0.088; rbf 0.24-0.32 (per-kernel range, never a single number)"}
    save("T1a-spectral-reconstruction.json", t1a)

    # ---- summary ----
    sm = load("results_summary.json")
    sm["artifact_blocks_postprocessed"] = [
        "T3 bootstrap_meta + aggregate REFUTED verdict + seam/truncation top-level",
        "T2 scope note", "T1a field std + per-kernel headline range"]
    save("results_summary.json", sm)
    print("post-processed T3/T2/T1a/summary")


if __name__ == "__main__":
    main()