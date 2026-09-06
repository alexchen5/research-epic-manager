# ISSUE hypothesis-ideation-r5: Hypothesis ideation (iteration-4 re-entry)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `hypothesis-ideation-r5`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `hypothesis`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Re-enter the hypothesis stage after the analysis gate routed back to
literature review (FAIL on Significance, loop cap 2 exhausted; routing
`literature_review` per `route_for_failure`). The literature rework
(literature-review-rework-r2) has updated the corpus with the
FAIL-feedback-informed Gap Coverage G9+ and ≥2 strategy families (F1
DST2-embedding exact/mixed boundary solver; F2 masked-Gram preconditioned
AM; F3 fallback negative-result+tooling framing). This ideation issue must
produce a NEW gated hypothesis proposal (proposal-iter4-v<n>.json) that:
- targets a POSITIVE pre-registered win (S-boundary: residual ≤ 1e-6 AND
  gap reduction ≥ 50% AND w ≤ min(H,W)/8 claimable; OR S-masked: speedup
  ≥ 1.5x at equivalent KKT residual vs PCG),
- OR formally adopts the negative-result + tooling framing (A6 GRF
  generator + A4 O(N log N)/O(N) scaling + Anderson-essential ablation +
  benchmark-not-refuted-with-sensitivity) as the qualifying contribution,
- honors the honest-framing invariants (no new-mathematics claims; T1b
  cited only from canonical results/iter2; EXECUTION_NOTES marked
  superseded; iteration-3 results = invalidated history, honest negatives
  only),
- fixes the reviewers' actionable items from the analysis gate r2
  (no-tieband sensitivity appendix; 222-row pool + per-domain breakdowns
  in the paper text; tieband aggregation convention written down;
  cost-clause parse RMSE-first, cost-as-credibility, ties reported;
  strengthened grf-3d/mnist coverage; superseded T1b guards; artifact-name
  spelling unification).

## Acceptance Criteria

- [ ] ideas/proposal-iter4-v<n>.json written: hypothesis statement,
      F1/F2/F3 strategy spec with win rules per the label-table
      conventions, corpus anchors (entries 45/46-52/54/66/67 + any new),
      honest-framing guards, seed 7 Kaplan conventions preserved,
      simulation_marker/disclosure where applicable
- [ ] The proposal explicitly states which gate(s) the strategy targets
      AND the falsification condition (measurement plan sketch with
      residual-tolerance and tieband conventions pre-committed)
- [ ] Honest-framing invariants checklisted in the proposal
- [ ] proposal-v<n> comments posted on this issue (thread convention)

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Seeded JIT at literature_review rework resolution (rework r2); previous
  ideation issues r1-r4 are resolved history (iterations 1-3).