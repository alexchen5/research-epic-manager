# ISSUE literature-review-rework-r1: Literature grounding rework (iteration 2, hypothesis gate routing)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `literature-review-rework-r1`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee:** `issue-manager`
- **Labels:** `stage`, `literature_review`, `rework`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Hypothesis gate round 2 exhausted the review-loop budget (2/2) with
Significance 3 / Originality 3 (median of two reviewers). Manager routing
per `route_for_failure`: hypothesis FAIL -> literature_review. This issue
extends the indexed corpus so the re-entered hypothesis can ground a
stronger Significance and Originality claim.

Corpus gaps to close (seeded from the gate feedback and the existing
concept index):

1. **Leakage-verified evaluation protocols** for kernel methods on
   spatiotemporal data: split-conformal under non-exchangeability /
   temporal-block and rolling-origin calibration; year-block and
   moving-block bootstrap significance (Diebold-Mariano vs block bootstrap
   in time series); seam/decay-phase leakage checks in rolling-origin
   forecast evaluation.
2. **ENSO (Nino3.4) forecasting state of the art:** statistical baselines
   (persistence, monthly climatology, AR(1), linear inverse models),
   machine-learning ENSO forecasts 2016-2024, the practical skill ceiling
   at h=1..12, and the standard evaluation (anomaly correlation, RMSE,
   skill score, hindcast protocols) -- to ground the Significance claim
   and the pre-registered win rule.
3. **FFT/spectral kernel KRR evaluation practices:** how
   circulant/Toeplitz spectral methods report exactness, resource
   accounting, and real-data validation (O(N log N) claims, memory,
   CPU-only scaling) -- to ground the Originality framing (the integrated
   leakage-verified real-data protocol as the contribution).

## Acceptance Criteria

- [x] docs/literature-review/review.md extended with 10-15 new annotated
      entries across the three gap topics (web-verified where possible),
      each with `<!-- annotation -->` markers consistent with the existing
      file format (15 entries 26-40, all web-verified)
- [x] ideas/concept-index.json rebuilt (concept-store CLI
      `build`/`query`) reflecting the enriched corpus; corpus stats
      (documents, entities, top co-mentions) updated (492 entities,
      120,786 co-occurrences; commit 53b1e8b)
- [x] A short gap-summary section added to the review file stating how the
      corpus now supports (a) leakage-verified evaluation protocol claims,
      (b) an honest ENSO-forecast significance framing, (c) the FFT
      resource-accounting framing ("Gap Coverage (iteration 2)" section)
- [x] Issue resolved with [seeding] + [seeded-fail-feedback] comments and
      stage artifact present (manager verification: workspace commit 53b1e8b)

## Comments

_Threaded via add-comment._