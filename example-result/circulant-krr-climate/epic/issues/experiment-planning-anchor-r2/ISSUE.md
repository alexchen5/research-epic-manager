# ISSUE experiment-planning-anchor-r2: Experiment planning (iteration-3)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-planning-anchor-r2`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `experiment-planning`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Turn the gated iteration-3 hypothesis artifact (ideas/proposal-final.json,
hypothesis gate r1 PASS, route experiment_planning) into a concrete, CPU-only
experiment plan that pre-registers the two novel strategies and their win
rules before execution:

- S1 RE-ABLRC: whole-sample symmetric embedding (2H-1)x(2W-1), DCT-I-class
  (Martucci entry 45) + adaptive boundary-banded low-rank Woodbury correction
  (w = ceil(2.5*rho); rank r_2d = O(w(H+W)); 3D r_3d = w(HW+HD+WD), capped at
  24^3, r^2 ~ 215 MB at w=3; 48^3 embedding-only + PCG cross-check).
- S2 SSAM-CAM: spectral-spatial alternating minimization for the masked Gram
  system (P_m K P_m^T + lambda I) w = y_m — coefficients on observed-cell
  support; KKT-residual termination identical to the PCG reference
  (per-field final relative residual 4.69e-9..9.81e-9 in
  results/iter2/T1b-CG-masked-train.json); FISTA momentum + Anderson window
  m=5; step schedule eta_k = 0.5/(1+k/200), ceiling 500 (budget-mediated).
- Arms A1-A6 + joint S1xS2 arm; baselines (dense KRR subsample <= 4000,
  standard PCG, KISS-GP, RFF, HSS-optional); multi-domain benchmark
  (2D/3D GRFs w/ controlled boundaries, MNIST-784 infilling, Kaplan SST v2);
  win rules exactly per plan-iter3-reconciliation-notes.md (single label
  table: S1 >= 50% gap reduction w/ residual cap <= 1e-6 and w <=
  min(H,W)/8; S2 >= 3x speedup at equivalent KKT residual < 1e-6, REFUTED <
  1.5x; DCT/DST >= 50%-capture consequence; benchmark negative rules).
- Budget: CPU-only, 12 cores, ~7 GB, <= 90 min; per-arm A1<=25, A2<=30,
  A3<=20, A4<=5, A5<=5, A6<=5; amortized measurements as iteration-2.

## Acceptance Criteria

- [ ] Artifact ideas/experiments/experiment-plan-iter3.json (or .md + .json)
      written on branch experiment-planning-anchor-r2: arms A1-A6 (+ joint
      S1xS2), datasets (real Kaplan SST v2 via h5py 3.7.0 as iteration-2 with
      pre-stated simulated-from-physics fallback disclosure; synthetic 2D/3D
      GRFs with controlled free/Dirichlet/Neumann/mixed boundary conditions,
      Paciorek-Schervish non-stationary covariance, seeds 0-19 / 0-9;
      MNIST-784 infilling with held-out digits + patch masks), metrics
      (RMSE valid-only, wall-clock, peak RSS, accuracy-per-flop,
      accuracy-per-byte, iterations-to-tol, speedup, gap reduction %, KKT
      residual), CV/leakage rules (future-blind Kaplan 1856-01..2015-12 /
      2016-01..2022-12, 2023-01 excluded; valid-only denominators; seed 7
      for Kaplan/mask draws), baseline sizes and conventions, kernel/lambda
      schedule, 64x64 + 24^3 dense Cholesky reference (128x128 = PCG
      free-boundary BTTB at tol 1e-8 dense-equivalent), per-arm budget table
      summing <= 90 min.
- [ ] Win rules pre-registered exactly per plan-iter3-reconciliation-notes.md
      (single label table; w-sweep {1,2,3,4} fail-fast + monotone-residual
      guard; S1 rank-assumption falsification guard re: interior-vs-band
      residual across w-sweep).
- [ ] S2 termination = KKT residual of shared masked-Gram system, relative,
      identical convention to PCG (exact range 4.69e-9..9.81e-9 cited).
- [ ] MNIST-784 arm pre-registered: RBF on pixel coordinates, stationary BCCB
      on flattened raster (per-image solves), held-out-digit + patch-mask
      splits, no post-hoc kernel/split selection.
- [ ] Single end-to-end run script target (scripts/run_iter3.py or
      run_pipeline_iter3.sh) committing all results/iter3/*.json artifacts.
- [ ] Resource accounting mandated in every results table.

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: ideas/proposal-final.json (hypothesis artifact),
  ideas/plan-iter3-draft.md (superseded by this plan),
  ideas/plan-iter3-reconciliation-notes.md (G1+G2 items; single win-rule
  table), ideas/iter3-design-brief.md (terminology reconciled to WSS),
  results/iter2/* canonical artifacts.