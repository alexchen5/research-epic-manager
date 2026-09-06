# ISSUE experiment-execution-anchor-r1: Experiment execution (CPU-only runs, 90-min budget)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-execution-anchor-r1`
- **Status:** `open`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched executor)`
- **Labels:** `stage`, `experiment-execution`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Execute the approved experiment plan (ideas/experiments/experiment-plan.json,
branch master, commit 06a35b1) under the hard envelope: CPU-only
(NumPy/SciPy/scikit-learn/matplotlib), 12 cores, ~7 GB RAM, total experiment
wall-clock <= 90 minutes, datasets < 2 GB.

Primary research question (algorithmic/methodological): exact kernel ridge
regression on regular-grid climate fields via circulant embedding
(Dietrich-Newsam / Wood-Chan) and FFT spectral shrinkage - O(N log N)
train/predict, O(N) memory, no explicit N-by-N Gram matrix - with
leakage-free evaluation (spatial-halo masks, temporal-block CV),
kernel-consistent off-grid Nino3.4 functional prediction, and resource
accounting (wall-clock, peak RSS, flops, bytes; accuracy-per-flop,
accuracy-per-byte) as first-class axes.

Data mode: NOAA PSL Kaplan SST v2 is netCDF-4/HDF5 (unreadable by the allowed
stack; ASCII endpoints probed unreliable), so the pre-committed
synthetic-from-physics fallback (circulant-embedded Matern fields with
Kaplan-like EOF structure, seed 20260831) is expected; every artifact carries
[simulated] markers. The executor must still attempt stdlib-readable
real-data endpoints first and record the outcome.

## Acceptance Criteria

- [x] scripts/run_pipeline.sh exists (single end-to-end target; Makefile
      `make run-all`); cumulative wall-clock logged, abort-and-record at
      85 min
- [x] P0 pilot gate: 32x32 FFT-KRR vs dense N x N KRR within tolerance
      (1e-6 inf-norm on alpha and holdout predictions, Matern 3/2 + RBF,
      lambda 1e-3) plus embedding-error sweep (padding fraction
      {0.5, 1, 2}x); failure recorded with diagnostics
- [x] T1a exact spectral reconstruction: random-pixel masks 10/30/50% and
      spatial-halo masks w in {1,2,4}; LOFO over 48 held-out months +
      spatial-block CV; RMSE/R2/conformal coverage+width per mask; optimism
      arm random-split vs block-split
- [x] T1b FFT-preconditioned CG masked training (10/30/50% inputs):
      iterations, wall-clock, peak RSS, RMSE vs T1a
- [x] T2 Nino3.4 functional regression: predictive-mean-over-box index
      (Trenberth 1997 5N-5S, 120-170W) under 5-fold temporal-block CV, plus
      zero-model interpolation ablation; report both functional-index and
      direct-regression-head results
- [x] Baselines: exact KernelRidge subsample n in {2k,5k,10k}; Nystrom
      {500,2k,5k,10k}; RFF {500,2k,5k,10k}; matched-flops/matched-bytes
      variant; wall-clock + peak RSS + estimated flops/bytes per fit
- [x] Scaling arm: wall-clock/memory at 32x32 (1024), 72x36 (2592),
      144x72 (10368); extrapolation model vs 7 GB cap (embedding storage
      threshold)
- [x] Every results JSON: dataset.origin (real | synthetic [simulated]),
      kernel, lambda, N, wall_clock_s, peak_rss_gb, estimated_flops,
      estimated_bytes, per-arm metrics
- [x] All artifacts committed on experiment-execution-anchor-r1 and merged
      to master; total recorded wall-clock <= 90 min

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Inputs: ideas/experiments/experiment-plan.json (stage 3 artifact, master);
  corpus docs/literature-review/review.md; proposal ideas/proposal-final.json.
- Ridge lambda log-sweep 8 values (1e-4 .. 1e2); kernels Matern 3/2,
  Matern 5/2, RBF, periodic-time x spatial.
- Merge target: master (stage-4 branch merged at stage exit).