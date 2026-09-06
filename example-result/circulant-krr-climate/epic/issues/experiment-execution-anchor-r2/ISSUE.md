# ISSUE experiment-execution-anchor-r2: Experiment execution (iteration-3)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-execution-anchor-r2`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `experiment-execution`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Execute the approved iteration-3 plan (ideas/experiments/experiment-plan-iter3.json,
planning anchor r2 resolved). Implement S1 RE-ABLRC (whole-sample symmetric
(2H-1)x(2W-1) DCT-I-class embedding + boundary-banded Woodbury correction,
w = ceil(2.5*rho), rank budget w(H+W) / 3D w(HW+HD+WD) capped at 24^3) and
S2 SSAM-CAM (spectral-spatial alternating minimization on the shared
masked-Gram system (P_m K P_m^T + lambda I) w = y_m, FISTA momentum,
floored-spectrum BCCB preconditioner on the FREE-BOUNDARY operator, soft
Lagrange-prox projection on observed cells, Anderson mixing m=5, KKT-residual
termination identical to the PCG reference), plus the multi-domain benchmark
(2D/3D GRFs with controlled boundaries, MNIST-784 infilling, real Kaplan SST
v2) vs dense KRR subsample, standard PCG, KISS-GP, RFF (+ HSS optional),
scaling to N ~ 1e5, ablations, and scripts/grf_boundary.py (A6). CPU-only.
Write all results to results/iter3/*.json with dataset.origin,
simulation_marker, seeds, w/rho, per-domain breakdowns, resource accounting,
and win-rule labels per the plan's label table.

## Acceptance Criteria

- [ ] scripts/grf_boundary.py (A6): boundary-controlled GRF generator
      (free/Dirichlet-zero/Neumann-zero/mixed; Paciorek-Schervish
      non-stationary covariance; seeds 0-19/0-9) with a self-check artifact
- [ ] scripts/run_iter3.py (or equivalent single end-to-end runner) executing
      arms A1-A6 within per-arm budgets (A1<=25, A2<=30, A3<=20, A4<=5, A5<=5,
      A6<=5; total <= 90 min) and writing results/iter3/*.json
- [ ] A1-boundary.json: free-boundary gap reduction (RE-ABLRC vs BCCB wrap vs
      DCT/DST comparator; dense Cholesky 64x64/24^3 + 128x128 PCG
      dense-equivalent @ 1e-8), w-sweep {1,2,3,4} monotonic-residual
      fail-fast, interior-vs-band residual, win/NOT-validated label
- [ ] A2-masked.json: SSAM-CAM vs PCG on the shared masked-Gram system at
      equivalent KKT residual < 1e-6 (primary) / 1e-8 (matched), synthetic
      64x64/128x128 masks 10/30/50% + block + Kaplan 36x72 (polar/land/random),
      speedup, iterations-to-tol, RMSE parity on the T1b valid-cell domain
- [ ] A3-multidomain.json: 4 domains x 5 methods (+HSS optional) with RMSE
      valid-only, wall-clock, peak RSS, accuracy-per-flop/byte; benchmark
      REFUTED rule applied honestly
- [ ] A4-scaling.json: N ~ 1e5 (320x320, 48^3 embedding-only + PCG
      cross-check; NO 3D Woodbury) with O(N log N)/O(N) trend
- [ ] A5-ablation.json: RE-ABLRC w/o correction; SSAM-CAM w/o Anderson, w/o
      circulant preconditioner, torus vs free operator (isolates S1 marginal)
- [ ] joint-S1xS2.json: win-rule label table applied to A1+A2 measurements
      (S1 >= 50% gap reduction w/ residual <= 1e-6 and w <= min(H,W)/8;
      S2 >= 3x speedup at KKT < 1e-6)
- [ ] results_summary.json + meta.json: pooled medians, budget tracking,
      env versions (numpy 1.24.2, scipy 1.10.1, sklearn 1.2.1, h5py 3.7.0)
- [ ] Every number traceable to a results/iter3 artifact; canonical T1b
      citation used (EXECUTION_NOTES pre-fix figures never cited)

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: ideas/experiments/experiment-plan-iter3.json (approved
  plan), ideas/proposal-final.json (hypothesis artifact),
  ideas/plan-iter3-reconciliation-notes.md (G1+G2 items; locked conventions),
  scripts/fft_krr.py + data_gen.py + metrics.py + baselines.py + run_iters2.py
  (iteration-2 code to build on), results/iter2/* canonical artifacts,
  results/raw/real/ (real Kaplan SST v2).