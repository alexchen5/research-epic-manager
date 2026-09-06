# ISSUE experiment-execution-anchor-r3: Experiment execution (iteration-4)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-execution-anchor-r3`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `experiment_execution`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Execute the approved iteration-4 plan (ideas/experiments/experiment-plan-iter4.json,
planning anchor r3 resolved). Implement F1 (DST2-embedding exact/mixed
boundary solver — dense Woodbury-center exact solve, w-clamp, support-rank
diagnostics, per-clause reporting over the 2D claim pool), contingent A2-F2
(masked-Gram preconditioned Anderson — randomized-Nystrom, KKT 1e-6
identical to PCG), A3 mult-domain benchmark (F1-exact/PCG/dense/KISS-GP/RFF
over 4 domains with strengthened coverage), A4 tooling; per-arm caps
A1<=20 / A2<=18 / A3<=7 / A4<=2 (total envelope 45 min hard-stop), seeds
Kaplan 7 / 2D 0-19 / 3D 0-9 / bootstrap 7, honest negatives in
results/iter4 (INVALIDATED-HISTORY banner for iter-3 must not be cited as
qualifying; T1b canonical lock; EXECUTION_NOTES/analysis.json superseded
markers; 0.1 s rounding note; artifact-name spellings A1-F1.json /
A2-F2.json / A3-multidomain.json / A4-tooling.json).

## Acceptance Criteria

- [ ] results/iter4/A1-F1.json (2D claim pool per-clause + pooled, support
      diagnostics, nb/cond measured, 3D per-domain rows, budget
      truncation-priority disclosure, n_neg)
- [ ] results/iter4/A2-F2.json (222-row wall-clock pool + per-domain
      breakdowns, KKT <1e-6 identical to PCG, RMSE parity rows)
- [ ] results/iter4/A3-multidomain.json (4-domain x 5-method, kiss/dense
      wins, tieband 0.5% + literal no-tieband sensitivity row, coverage
      deltas itemized)
- [ ] results/iter4/A4-tooling.json (grf_boundary selfcheck, A6-style)
- [ ] results/iter4/results_summary.json + meta.json (n_neg disclosure,
      honest_framing with classical-components guard, T1b citation lock,
      total wall clock <= 45 min envelope, peak RSS <= ~2 GB cgroup
      disclosure)
- [ ] scripts: run_iter4.py + verify_iter4.py extended from fft_krr_embed.py
      (DST2-embedding exact band solve path per WTT = M^{-1}[T,T]);
      py_compile clean
- [ ] Every number artifact-traced; win-rule labels per label table;
      REFUTED/NOT-validated attribution per pre-committed precedence;
      no EXECUTION_NOTES pre-fix figures; iter-3 cited only as
      invalidated-history honest negatives

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: ideas/experiments/experiment-plan-iter4.json (approved
  plan), ideas/proposal-iter4-v4.json (gated hypothesis),
  docs/literature-review/review.md (74 entries, G9+, F1/F2/F3),
  results/iter3/*.json (invalidated history), results/iter2/*.json
  (canonical), scripts/fft_krr_embed.py + grf_boundary.py + baselines.py
  (execution templates), ideas/plan-iter3-reconciliation-notes.md (locked
  conventions). JIT-opened at planning resolution; execution worker
  dispatched on seeding.