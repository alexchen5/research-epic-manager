# Issue: literature-review-r3

## Metadata

- **Epic:** circulant-krr-climate
- **Stage:** literature_review (iteration 3 re-entry; novelty-upgrade directive)
- **Status:** `resolved`
- **Created:** 2026-09-02
- **Labels:** literature, iteration-3, novelty-upgrade, grounding

## Summary

Re-ground the indexed corpus for the iteration-3 novelty upgrade: the paper
must become a qualifying novel ML contribution by (a) developing >= 2 novel
algorithmic strategies that resolve the **torus boundary gap** and the
**masked-inversion degradation** of grid-based KRR without O(N^2) memory or
O(N^3) compute, and (b) benchmarking across multiple domains (synthetic 2D/3D
non-stationary Gaussian random fields with controlled boundary conditions,
standard regular-grid ML benchmark tasks, and the real Kaplan SST v2 fields)
against exact dense KRR, standard PCG, KISS-GP, and Random Fourier Features.

This issue re-enters the literature stage solely to ground those strategies
and benchmark domains in prior art (novelty positioning, baseline selection,
metric conventions, simulation tooling) so the ideation proposal can be
corpus-positioned and pre-registered honestly.

## Acceptance criteria

- [x] >= 12 new annotated corpus entries (web-verified where possible, with
      URLs), covering:
  1. Boundary-aware / embedding-corrected kernel solves (circulant embedding
     for simulation and conditioning — Davies-Harte / Wood-Chan lineage;
     boundary-corrected Toeplitz/BTTB embedding and padding strategies;
     KISS-GP structured interpolation; Toeplitz preconditioning theory),
  2. Spectral-spatial alternating minimization (ADMM / proximal splitting /
     half-quadratic splitting / plug-and-play priors; FISTA-type acceleration;
     any prior art applying these to kernel regression or inpainting),
  3. Low-rank + structured-Toeplitz corrections (randomized low-rank
     approximations for structured kernels; Nystrom-style corrections; the
     closest work to a "low-rank + Toeplitz/BTTB correction" idea),
  4. Non-stationary Gaussian random field simulation with controlled
     boundary conditions (2D/3D Matérn-family fields; conditioning on
     boundary values; exact/approximate samplers),
  5. Regular-grid infilling / spatial-regression benchmark tasks and their
     standard metrics (RMSE/CRPS/coverage; leakage-safe train/test splits),
  6. Masked/partial-observation kernel methods (matrix completion, masked
     GP regression, semi-supervised embeddings) — the "masked inversion"
     problem family.
- [x] New section "Gap Coverage (iteration 3)" in docs/literature-review/review.md,
      naming the gaps this iteration closes: (G5) exact free-boundary fast
      grid kernel solves, (G6) masked-input fast solves without O(N^2) memory,
      (G7) multi-domain regular-grid benchmark with pre-registered efficiency
      and boundary-margin thresholds (>= 3x PCG speedup at residual tol < 1e-6;
      >= 50% free-boundary gap reduction vs standard BCCB wrapping), (G8)
      boundary-controlled GRF simulation tooling for reproducible benchmarks.
- [x] docs/literature-review/review.md extended (entries 41+, sequential
      numbering, [web-verified]/[model-knowledge] flags, " -- " separators,
      References section with URLs); entry count >= 40 -> 52+.
- [x] ideas/concept-index.json rebuilt via the concept-store CLI
      (/workspace/.dsh/skills/research-project-epic-manager/scripts/concept_store.py);
      entities >= 492 (target 550+), co-occurrence count reported.
- [x] Commit: "iter3: literature grounding (boundary-aware solves, spectral-spatial
      AM, low-rank+Toeplitz, GRF simulation, grid benchmarks)".
- [x] Issue resolved with [seeding] and [manager-notice: grounding-resolved]
      comments; stage exits to hypothesis ideation re-entry (proposal-r1 of
      iteration-3).