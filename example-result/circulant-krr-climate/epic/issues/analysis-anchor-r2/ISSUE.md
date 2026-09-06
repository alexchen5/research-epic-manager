# ISSUE analysis-anchor-r2: Analysis (iteration-3)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `analysis-anchor-r2`
- **Status:** `superseded`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `analysis`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Synthesize the executed iteration-3 results (results/iter3/*.json, execution
anchor r2 resolved) into the analysis artifact: win-rule verdicts computed
EXACTLY per the plan's label table (ideas/experiments/experiment-plan-iter3.json),
a claim-to-artifact number-traceability ledger, honest negatives (S1
NOT-validated on the 1e-6 residual cap; S2 REFUTED -- median speedup 0.237x;
3D WSS embedding n_neg disclosure; container OOM adaptation), and the numbers
pack for the paper (pooled medians, per-domain breakdowns, resource
accounting: total 2296.5 s / 0.98 GB).

## Acceptance Criteria

- [ ] results/analysis/analysis-iter3.json (or results/analysis.json) written:
      win-rule verdicts per the plan's label table (S1 win / NOT-validated /
      REFUTED; S2 win / REFUTED <1.5x; benchmark REFUTED iff KISS-GP >= 2
      domains or dense KRR >= 1; DCT/DST 50%-capture consequence), claim-by-
      claim evidence mapping (every quantitative claim -> artifact path +
      field), honest negatives, numbers pack, resource summary (total <= 90
      min / <= 7 GB envelope; A1 arm-budget exceeded flag recorded)
- [ ] Every number in the analysis traces to a results/iter3 (or canonical
      results/iter2) artifact; T1b cited only from
      results/iter2/T1b-CG-masked-train.json (rate means 245.1/276.1/280.9
      @ tol 1e-8; span 233-291; final rel residual 4.69e-9..9.81e-9; RMSE
      0.529-0.541); EXECUTION_NOTES pre-fix figures never cited
- [ ] Honest-framing invariants honored (no new-mathematics/no-SOTA claims;
      S1 bounded-residual approximate; S2 masked-Gram equivalence
      empirically-tested; REFUTED/validated labels per plan; ties reported)

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: results/iter3/*.json (executed artifacts, execution
  anchor r2 resolved, tracker commit 43b17ba),
  ideas/experiments/experiment-plan-iter3.json (approved plan + label table),
  ideas/proposal-final.json (gated hypothesis), ideas/plan-iter3-
  reconciliation-notes.md (locked conventions), results/iter2/* canonical
  artifacts, docs/literature-review/review.md (69-entry corpus, G5-G8).