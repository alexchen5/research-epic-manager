# ISSUE hypothesis-ideation-r3: Hypothesis ideation r3 (iteration 2, re-entry after literature grounding)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `hypothesis-ideation-r3`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee:** `issue-manager`
- **Labels:** `stage`, `hypothesis`, `ideation`, `rework`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Re-entry into hypothesis ideation after the hypothesis gate round 2 loop
exhausted its budget (Significance 3 / Originality 3) and was routed to
literature_review. That rework is resolved (issue
`literature-review-rework-r1`, workspace commit 53b1e8b): 15 web-verified
annotated entries (26-40) closed the three corpus gaps (leakage-verified
evaluation protocols; ENSO forecast SOTA + standard hindcast evaluation;
FFT/spectral KRR real-data evaluation practices) and the concept index was
rebuilt (492 entities, 120,786 co-occurrences; "Gap Coverage (iteration 2)"
section in docs/literature-review/review.md).

This ideation run is seeded with:

1. **Enriched corpus** (docs/literature-review/review.md +
   ideas/concept-index.json).
2. **Hypothesis gate r2 critique items (a)-(f):** (a) grid-resolution
   sensitivity comparison + explicit ENSO-floor analysis at h=12 with the
   same bootstrap machinery; (b) real-data threat plan named in-text
   (Kaplan reconstruction-smoothing caveat, land/missing-mask handling,
   pre-stated PCG non-convergence fallback); (c) explicit seam/decay
   coverage tolerances; (d) operational Cholesky accuracy-per-flop ratio
   control (subsampled grid, same real anomaly fields, one accuracy metric,
   one flop estimate, bootstrap CI on the ratio); (e) explicit 1-3
   trailing-month discard with truncation sweep and the
   2015-excluded-vs-retained split; (f) acceptance tolerance for calibrated
   diagnostic intervals on masked-cell reconstruction.
3. **Executed real-data results** (results/iter2/*.json): P0 torus exactness
   2.62e-12 rel (free-gap reported); T1a masked reconstruction RMSE
   0.0816-0.0880 (matern32) with calendar-month conformal coverage
   diagnostics; T1b masked-input PCG convergence 245-281 iters at tol 1e-8
   (RMSE ~0.53); T2 Nino3.4 spectral functional RMSE 0.0856 vs zero-model
   0.795 vs direct ridge head 0.270 (temporal-block CV); T3 transfer forecast
   vs persistence/climatology/AR(1) with pre-registered win rules and
   truncation-sweep stability; B baselines 1.24-1.73 RMSE on pooled real
   cells; S sub-ms O(N log N) scaling, 1.55 GB peak, 108 s total.

Target: a proposal triple (problem / method / experiment_design) that gates
PASS at Significance >= 4 and Originality >= 4, grounded in the enriched
corpus and the executed real-data results, with critique items (a)-(f) pinned
in the experiment design. Honest framing invariants unchanged: no FFT-kernel
newness, no spectral-regression newness, no SOTA-ENSO-skill claims;
contribution = concrete circulant-block CPU implementation + real-data
reconstruction/index benchmark + leakage-verified evaluation protocol +
resource accounting.

## Acceptance Criteria

- [x] Proposal triple written to ideas/ (proposal-it3-v1 -> v3 final),
      seeded from the enriched corpus + critique items (a)-(f) + executed
      results
- [x] Ideation review loop completes: round 1 PASS (aggregate 4/4/4/5/4,
      threshold 4); round cap respected aggregate
- [x] Hypothesis gate (fresh budget) PASS at Significance 4 / Originality 4
      (round 1) with all critique items pinned and reviewer integrity items folded
- [x] Issue resolved with [seeding], [proposal-it3-v1/v2/v3],
      [review-critique], and [manager-notice] comments posted

## Comments

_Threaded via add-comment._