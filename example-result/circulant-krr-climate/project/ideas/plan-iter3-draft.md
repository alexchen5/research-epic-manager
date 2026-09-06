# Iteration-3 experiment plan (manager draft, pre-approval)

Status: DRAFT for planning-stage reconciliation (to be reconciled against the
gated proposal-it4-* and the post-gate planning issue). Not yet approved.

## Objectives (pre-registered)

- O1 Boundary: reduce the free-boundary modeling gap >= 50% vs standard BCCB
  wrapping (RE-ABLRC), measured as relative solve/prediction error vs the
  dense free-boundary reference.
- O2 Masked: >= 3x wall-clock speedup vs standard PCG at equivalent residual
  tolerance < 1e-6 (SSAM-CAM), with predictive RMSE parity.
- O3 Multi-domain: proposal beats PCG and BCCB-wrapping on >= 3 of 4 domains
  in RMSE at equal-or-lower cost; full comparison vs dense KRR / KISS-GP / RFF.
- O4 Scaling: O(N log N) timing / O(N) memory verified to N ~ 1e5.

## Arms (map to proposal-it4-* experiment_design)

| Arm | Grids | Content |
|---|---|---|
| A1_bnd | 2D 64x64, 128x128; 3D 24x24x24 | free-vs-wrap-vs-RE-ABLRC gap; seeds 0..19 |
| A2_mask | Kaplan masks (polar/land/10/30/50%), synthetic masks | PCG-ref vs SSAM-CAM; tol 1e-6/1e-8 |
| A3_multi | + regular-grid benchmark task (MNIST-784 infill) | 5 methods x 4 domains; RMSE/time/mem/flop |
| A4_scale | 2D 320x320, 3D 48x48x48 | timing/bytes vs est_* formulas |
| A5_ablate | 2D 128x128 | RE-ABLRC w/o correction; SSAM w/o mixing; SSAM w/o precond |

## Baselines (implementations, published conventions)

- dense KRR: exact Cholesky solve, subsample cap 4000 rows (CPU-only)
- standard PCG: on masked Gram (P_m K P_m^T + lam I), BTTB matvec,
  identity+floored-torus preconditioner as iter-2 T1b
- KISS-GP: inducing regular grid with local (bi/tri)linear interpolation,
  Toeplitz-BTTB inducing Gram solved via circulant machinery
- RFF: sklearn Ridge on RFF features (as iter-2 B arm)

## Data / leakage

- Kaplan SST v2 as iter-2 (train 1856-01..2015-12; test 2016-01..2022-12;
  2023-01 excluded; sentinel-aware)
- synthetic GRFs: Matérn 3/2, 5/2, RBF; non-stationary range/var fields;
  controlled boundary conditions (free / Dirichlet / mixed); seed-block CV
- regular-grid task: MNIST-784 infilling, held-out digit classes + patch masks

## Metrics

RMSE/MAE (valid-only), coverage (0.90 conformal per mask), wall-clock, peak
RSS, est flops/bytes, acc-per-flop, acc-per-byte, iterations-to-tol, speedup,
gap reduction %. All reported per-domain and aggregated with medians.

## Budget envelope

CPU-only, 12 cores, ~7 GB, <= 90 min wall per run; measurements amortized
(as iter-2); Nystrom/RFF fits capped; results written to results/iter3/.