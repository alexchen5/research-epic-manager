# ISSUE hypothesis-ideation-r1: Hypothesis stage (ideation loop)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `hypothesis-ideation-r1`
- **Status:** `open`
- **Priority:** `P1`
- **Assignee(s):** `epic-manager (ideation issue-manager role)`
- **Labels:** `stage`, `hypothesis`, `ideation`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Iterative three-component ideation (problem / method / experiment design),
grounded in the stage-1 corpus (docs/literature-review/review.md and the
concept index ideas/concept-index.json). The PRIMARY research question must
be the algorithmic/methodological innovation: exact kernel ridge regression
on regular-grid climate fields via block-circulant structure exploitation
and the FFT (O(N log N) training and prediction, O(N) memory, no explicit
N-by-N kernel matrix), with the climate domain (SST anomaly fields; masked
field reconstruction and Nino3.4 index regression) as the experimental
substrate. Stop conditions: pass (all components, all ideation criteria >=
4), cap (round == ideation.max_rounds = 3), plateau. On stop: write
ideas/proposal-final.json; hypothesis gate (max_hypothesis_review_loops=2,
criteria Significance + Originality) evaluates the final proposal.

## Acceptance Criteria

- [x] >= 2 [proposal-v<n>] comments on this thread (revision history) or a
      recorded stop condition
- [x] Artifact ideas/proposal-final.json committed on branch
      hypothesis-ideation-r1, with components, revision_history,
      stop_condition, aggregate_scores, flagged
- [x] Ideation critiques dispatcher-posted as [review-critique:
      ideation-r<round>] comments
- [x] Hypothesis gate recorded in review_state.verdict_history when enabled

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Inputs at seeding: docs/literature-review/review.md,
  ideas/concept-index.json (stage 1 artifacts, merged to master).
- The thread IS the revision history: proposal-v<n> -> critiques ->
  proposal-v<n+1>.