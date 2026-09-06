# ISSUE literature-review-rework-r2: Literature review rework (iteration-3 FAIL routing)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `literature-review-rework-r2`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `literature_review`, `rework`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Rework the literature review after the analysis gate FAILed on Significance
(round 2, aggregate Q4/S3/O4; loop limit max_experiment_review_loops=2
exhausted). FAIL routing per route_for_failure(analysis, [Significance]) ->
target stage `literature_review`. The rework must absorb the FAIL feedback
(the executed iteration-3 results are a rigorously provenanced
negative-result/falsification study, NOT a qualifying positive contribution:
S1 NOT-validated, S2 REFUTED, benchmark not-refuted only under a disclosed
conditional tie-resolution) and identify an angle that can clear the
Significance >= 4 bar at the next analysis gate: a novel algorithmic
strategy with a positive pre-registered win (>= 50% free-boundary gap
reduction with residual <= 1e-6 and claimable w, OR >= 3x speedup vs PCG at
equivalent residual tolerance), or a reframed qualifying contribution that
two independent reviewers will score Significance >= 4.

## Acceptance Criteria

- [ ] Updated docs/literature-review/review.md corpus with a new Gap
      Coverage section (G9+: the FAIL-feedback-informed gaps) that
      explicitly quotes the two analysis-gate FAIL reviews
      (20260902T0630-review-critique-analysis-r1.md and
      20260902T0650-review-critique-analysis-r2.md equivalents on the
      analysis anchor) and the 4 remaining actionable items (cost-clause
      parse, tieband aggregation convention, superseded-figure guard for
      EXECUTION_NOTES/analysis.json, artifact-name spelling unification)
- [ ] Gap statements re-scored with the honest negatives of iteration-3 as
      part of the evidence base (no reuse of iteration-3 results as a
      qualifying claim; they are preserved on disk as invalidated history
      and may be cited ONLY as honest negatives / falsification evidence)
- [ ] New strategy families proposed (at least 2) that target the failing
      gates (S1 residual cap via bounded-residual correction theory;
      S2 speed via a different acceleration class) with corpus anchors
      (entries 45/46-52/54/66/67 and any new entries found)
- [ ] The rework artifact feeds the next hypothesis ideation
      (hypothesis re-entry is JIT-on-stage-entry)

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Seeded as the FAIL route target of the analysis gate r2 FAIL
  (route_for_failure -> literature_review; precedent:
  literature-review-rework-r1 for the earlier hypothesis FAIL).
- Whole-stage invalidation applied at/downstream of literature_review
  (manifest results/artifacts entries removed for intermediate stages;
  files preserved on disk as invalidated history; analysis-anchor-r2
  superseded with block-linked comment; paper-writeup pre-staged draft
  removed, never registered).