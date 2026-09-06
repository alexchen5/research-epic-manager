# ISSUE experiment-planning-anchor-r1: Experiment planning

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `experiment-planning-anchor-r1`
- **Status:** `open`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `experiment-planning`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Turn the approved proposal (ideas/proposal-final.json, stop=pass, aggregate
all-4) into a concrete, CPU-only experiment plan. Primary research question
(algorithmic/methodological): exact kernel ridge regression on regular-grid
climate fields via circulant embedding (Dietrich-Newsam / Wood-Chan) and FFT
spectral shrinkage - O(N log N) train/predict, O(N) memory, no explicit N-by-N
Gram matrix - with leakage-free evaluation, kernel-consistent off-grid Nino3.4
functional prediction, and resource accounting (wall-clock, peak RSS, flops,
bytes; accuracy-per-flop/byte) as first-class axes. AI-for-climate (Kaplan SST
anomaly fields; Nino3.4/ENSO index) is the experimental substrate.

## Acceptance Criteria

- [x] Artifact ideas/experiments/experiment-plan.json written on branch
      experiment-planning-anchor-r1: arms, datasets (Kaplan SST v2 72x36 grid
      via NOAA PSL if fetchable; synthetic-from-physics fallback specified as
      circulant-embedded Matern with Kaplan-like EOF structure + simulation
      markers), metrics, CV design (spatial-halo masks w in {1,2,4};
      leave-one-field-out over 48 held-out months; 5-fold temporal-block CV
      for T2; random-split vs block-CV optimism arm), baseline component
      sizes (exact subsample n in {2k,5k,10k}; Nystrom {500,2k,5k,10k}; RFF
      {500,2k,5k,10k}), hyperparameter schedule (kernels: Matern(3/2),
      Matern(5/2), squared-exponential + periodic-time x spatial for ENSO;
      ridge lambda log-sweep of 8 values), 32x32 pilot gate (sanity vs dense
      N x N KRR), and a per-arm budget table summing well under 90 min / 7 GB
      / 12 cores
- [x] Resource accounting mandated in every results table
- [x] Simulation-marker disclosure plan for the fallback, matching the
      Evidence-Preface contract
- [x] Single end-to-end run script/Makefile target (scripts/run_pipeline.sh)
      committing all artifacts

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: ideas/proposal-final.json (stage 2 artifact) +
  forwarding notes (sample unit = grid cell; T1 train-on-complete/mask-at-test;
  circulant embedding for non-periodic lat/lon; enumerated hyperparameter/CV
  schedule; precise synthetic fallback; pilot sanity gate).
- Merge target: master (stage-3 branch merged at stage exit).