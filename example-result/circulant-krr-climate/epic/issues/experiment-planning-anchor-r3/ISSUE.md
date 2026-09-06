# ISSUE experiment-planning-anchor-r3: Experiment planning (iteration-4)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-planning-anchor-r3`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `experiment_planning`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Translate the gated iteration-4 hypothesis (ideas/proposal-iter4-v<n>.json,
hypothesis-ideation-r5 gate PASS) into the approved plan
(ideas/experiments/experiment-plan-iter4.json) with arms for the chosen
primary strategy (F1 DST2-embedding exact/mixed boundary solver or F2
masked-Gram preconditioned Anderson mixing) and the F3 fallback where
applicable; CPU-only 12 cores / ~2 GB cgroup / <= 45-min execution envelope
(A1 <= 20, A2 <= 18, A3 <= 7 min); pre-registered win-rule label table with
the reviewer-fixed conventions (tieband ratio-of-medians 0.5% + no-tieband
sensitivity row; cost-clause RMSE-first, cost as credibility gate, ties
reported; 222-row-pool and per-domain breakdowns in the paper; residual
tolerance convention identical to PCG KKT 1e-6; 3D floor caveat + n_neg
disclosure; strengthened grf-3d/mnist coverage toward plan scope with
budgeted disclosure); honest-framing invariants (T1b canonical lock;
EXECUTION_NOTES superseded markers; iteration-3 = invalidated history,
honest negatives only; no new-mathematics claims; single label table);
Kaplan seed 7 conventions preserved.

## Acceptance Criteria

- [ ] ideas/experiments/experiment-plan-iter4.json written with arms A1-A4,
      label table (win rules verbatim per proposal), budget (45-min
      envelope), seeds (Kaplan 7; synthetic 2D 0-19 / 3D 0-9 or budgeted
      subset disclosed; bootstrap 7), future-blind split, dense references
      (Cholesky <= 4000 subsample; 3D PCG-1e-8 reference with container
      disclosure), honest framing, meta.json n_neg disclosure convention
- [ ] plan commits into the workspace repo; planning anchor r3 resolution
      comment + ISSUE.md status resolved + manifest entry + costs entry

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: ideas/proposal-iter4-v<n>.json (gated hypothesis),
  docs/literature-review/review.md (74 entries, G9+ gap coverage, F1/F2/F3
  families), results/iter3/*.json (invalidated history, honest negatives),
  results/iter2/*.json (canonical), ideas/plan-iter3-reconciliation-notes.md
  (locked conventions). JIT-opened at hypothesis gate PASS (stage entry).