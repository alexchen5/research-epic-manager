# Issue: hypothesis-ideation-r4

## Metadata

- **Epic:** circculant-krr-climate
- **Stage:** hypothesis (iteration 3 novelty-upgrade re-entry)
- **Status:** `draft` (opens when literature-review-r3 resolves)
- **Created:** 2026-09-02
- **Labels:** hypothesis, iteration-3, novelty-upgrade, ideation

## Summary

Ideate and gate the iteration-3 research hypothesis: **>= 2 novel algorithmic
strategies** that resolve the two bottleneck limitations of grid-based
circulant-block KRR — (1) the **torus boundary gap** (BCCB periodic wrapping;
~0.95 relative error on free-boundary Matérn kernels) and (2) the
**masked-inversion degradation** (PCG fallback: slow convergence, RMSE
0.53-0.54 under missing-data masks) — without O(N^2) memory or O(N^3)
compute, benchmarked multi-domain (synthetic 2D/3D non-stationary Gaussian
random fields with controlled boundary conditions; standard regular-grid ML
benchmark tasks such as grid infilling; real Kaplan SST v2 fields) against
exact dense KRR, standard PCG, KISS-GP, and Random Fourier Features, with
the pre-registered thresholds:

- **>= 3x speedup** over standard PCG at equivalent residual tolerance
  (< 1e-6), and
- **>= 50% reduction** of the free-boundary modeling gap relative to
  standard BCCB wrapping.

## Acceptance criteria

- [x] Proposal trio (problem / method / experiment_design) written to
      ideas/ seeded from the iteration-3 corpus (entries 41+, concept index
      rebuild, Gap Coverage (iteration 3) G5-G8) — `proposal-it4-v1.json`.
- [x] Ideation review loop (max 3 rounds, 2 reviewers per round, median
      aggregation, threshold 4) completes with a PASS.
- [x] Hypothesis gate (fresh loop budget) returns PASS at Significance >= 4
      and Originality >= 4 with all reviewer items pinned on the proposal.
- [x] Issue resolved with [seeding], proposal-round, [review-critique], and
      [manager-notice] comments posted.