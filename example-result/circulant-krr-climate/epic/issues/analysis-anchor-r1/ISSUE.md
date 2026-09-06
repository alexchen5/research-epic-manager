# ISSUE analysis-anchor-r1: Analysis of experiment results

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `analysis-anchor-r1`
- **Status:** `open`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched analyst)`
- **Labels:** `stage`, `analysis`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Analyze the executed results (results/*.json + EXECUTION_NOTES.md, merged to
master as 3702a4f) against the approved plan (ideas/experiments/experiment-plan.json)
and the primary research question: exact circulant-block KRR on regular-grid
fields via circulant embedding and FFT spectral shrinkage - O(N log N)
train/predict, O(N) memory - with leakage-free evaluation and resource
accounting as first-class axes (climate substrate: SST reconstruction +
Nino3.4 index).

Produce the canonical analysis artifact `results/analysis.json` and, where
evidence permits, the claims ledger `results/claims.json`: every claim is
traceable to an artifact JSON path + key, and no claim exceeds the evidence
(no overclaiming: spectral/FFT kernel techniques exist in the literature;
the contribution is the concrete circulant-block CPU implementation and the
systematic exact-vs-randomized CPU benchmark on climate fields).

## Acceptance Criteria

- [x] `results/analysis.json` on branch analysis-anchor-r1: pilot gate
      verdict (torus spectral exactness; disclosed torus-vs-free gap);
      reconstruction quality (T1a RMSE/R2/conformal coverage+width per mask)
      vs baselines incl. matched-flops/bytes; optimism gap (random vs halo);
      T1b CG outcome (convergence, iterations, RMSE vs T1a); T2 functional
      vs zero-model ablation vs direct head; scaling measured vs predicted;
      resource axes with honest claims
- [x] `results/claims.json`: every claim mapped to artifact path + key
- [x] Data mode disclosed (synthetic [simulated]) and claim scope stated
- [x] Pruned/failed arms reported honestly
- [x] Committed on analysis-anchor-r1, merged to master

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Inputs: results/*.json + EXECUTION_NOTES.md (stage 4, master 3702a4f);
  experiment-plan.json (master 06a35b1); proposal ideas/proposal-final.json.
- Merge target: master.