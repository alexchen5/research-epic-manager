# EPIC: circulant-krr-climate

## Status

**Status:** `active`
**Priority:** `P1`
**Owner(s):** epic manager (research-project-epic-manager run)
**Assigned workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
**Created:** `2026-08-31`
**Last updated:** `2026-09-02`

## Summary

Research project whose primary research question is an algorithmic /
methodological innovation in machine learning: exact kernel ridge regression
on regular-grid climate fields via block-circulant structure exploitation and
the FFT (O(N log N) training and prediction, O(N) memory, no explicit N-by-N
kernel matrix), implemented CPU-only with NumPy/SciPy on consumer hardware
(12 cores, ~7 GB RAM, <= 90 minutes total wall-clock for all runs).
AI-for-climate is the experimental substrate: sea-surface temperature anomaly
fields for masked-field reconstruction (gap-filling) and Nino3.4 (ENSO)
index regression, evaluated with honest block cross-validation against
scikit-learn baselines (exact KRR on subsamples, Nystrom, Random Fourier
Features) with wall-clock, peak RSS, accuracy-per-flop, and
accuracy-per-byte as first-class axes. The deliverable is a compiled 4-page
PDF (main text excluding references) in NeurIPS-workshop LaTeX formatting,
compiled with tectonic.

## Iteration 2 (research-manager directive, 2026-08-31)

- Re-entered at the **hypothesis ideation** step: goal = a HIGHER-SIGNIFICANCE
  direction than iteration 1.
- **Constraint modification (sanctioned):** REAL climate data is now
  permitted. The Python-stack limitation is lifted for data reading only:
  h5py (installed via apt) reads the real NOAA PSL Kaplan SST v2 monthly
  anomaly netCDF-4/HDF5 files. CPU-only 12-core / ~7 GB / <= 90-min envelope
  unchanged; scientific compute stays NumPy/SciPy/scikit-learn.
- Real data live at `results/raw/real/` (2005 months, 36x72 5-deg grid,
  Nino3.4 index validated against 1982/83, 1997/98, 2015/16 El Nino and
  1988/89 La Nina).
- Target higher-significance result: real-data replication of the exact
  torus spectral KRR benchmark (masked reconstruction + Nino3.4 functional)
  plus an honestly-framed ENSO forecast arm (h=1..12, frequency-domain
  transfer, vs persistence/climatology/AR(1)) under future-blind temporal
  holdout -- no SOTA-ENSO-skill or FFT-kernel-newness claim.
- Iteration-1 [simulated] results remain as history and benchmark
  (superseded by the iteration-2 real-data results).

## Iteration 3 (human novelty-upgrade directive, 2026-09-02)

- **Motivation (human review):** iteration-2 delivered a valid real-data
  benchmark and protocol, but novelty was judged weak; the paper must be
  upgraded into a qualifying novel ML contribution. Two technical bottlenecks
  identified: (1) the torus boundary gap (BCCB spectral wrapping imposes
  periodic boundaries; ~0.95 relative error on free-boundary Matérn kernels)
  and (2) masked-input inversion degradation (PCG fallback: slow convergence
  and RMSE 0.53-0.54 under missing-data masks).
- **Directive:** iterate AGAIN from the `literature_review` stage; develop
  **>= 2 novel algorithmic strategies** resolving the boundary/masking
  limitations of grid-based KRR without O(N^2) memory or O(N^3) compute
  (suggested: circulant boundary-padding/preconditioning; spectral-spatial
  alternating minimization; adaptive low-rank + Toeplitz correction).
- **Multi-domain benchmark** (not restricted to Kaplan SST): (a) synthetic
  2D/3D non-stationary Gaussian random fields with controlled boundary
  conditions, (b) standard regular-grid ML benchmark tasks (grid infilling /
  spatial regression), (c) real Kaplan SST v2; baselines: exact dense KRR,
  standard PCG, KISS-GP, Random Fourier Features.
- **Pre-registered thresholds:** >= 3x speedup over standard PCG at
  equivalent residual tolerance (< 1e-6); >= 50% reduction of the
  free-boundary modeling gap relative to standard BCCB wrapping.
- **Deliverable:** rewritten paper as a qualifying novel ML contribution
  (4 body pages; honest framing; every number artifact-traced) -> writeup
  gate -> finalize `synthesised` + `final_verdict APPROVE` + absolute
  `deliverable_path` -> validate_execution Checks 1-11 ALL PASS.
- **Iteration-3 progress (2026-09-02):** literature_review r3 resolved
  (69 entries; 56 web-verified / 13 model-knowledge; Gap Coverage G5-G8;
  concept-index 888 entities / 393,828 co-occurrences; commits 3adbd69,
  c439c6a) -> ideation r4 (r1 FAIL, r2 FAIL, r3 PASS medians 4/4/4/4/4;
  stop_condition=pass; proposal-final.json registered) -> hypothesis gate
  r1 PASS (Significance 4 / Originality 4; commits 9984d3b) -> route
  experiment_planning -> planning anchor r2 opened + seeded (commit
  131c4aa) -> plan artifact ideas/experiments/experiment-plan-iter3.json
  written by planner (workspace commit 844283a) -> planning anchor r2
  resolved (tracker commit e775478; planning stage un-gated per
  gate_config_map) -> experiment_execution anchor r2 opened + seeded
  (tracker commit 7646a39); execution worker dispatched (S1 RE-ABLRC +
  S2 SSAM-CAM + arms A1-A6 + joint S1xS2 -> results/iter3/*.json).

- Iteration-2 progress: hypothesis ideation re-entry (r3) PASS (proposal-it3-v3,
  ideation aggregate 4/4/4/5/4, gate 4/4) -> planning approved -> execution
  verified (results/iter2/, 78.7 s / 1.57 GB, fixed B-arm decode) -> analysis
  gate PASS (4/4/4) -> paper rewrite in progress (real data; T3 transfer
  REFUTED under the pre-registered bootstrap-CI win rule as the honest
  negative).

## Goals

- [x] Iteration 1 complete: all six protocol stages with review gates
      and verdict history; iteration 2 in progress (hypothesis ideation re-entry)
      experiment_planning, experiment_execution, analysis, paper_writeup)
      with review gates and verdict history recorded in project.json
- [ ] A CPU-only empirical study: the circulant-block KRR algorithm plus
      baselines executed end-to-end in <= 90 minutes wall-clock; every
      quantitative claim traces to an artifact JSON committed in the
      project workspace repo
- [ ] A compiled 4-page PDF deliverable (4 pages of main text excluding
      references) in NeurIPS-workshop LaTeX formatting via tectonic
- [ ] Writeup Clarity gate PASS (or recorded block) before finalising

## Non-Goals

- Not responsible for submitting the paper anywhere (human action)
- No GPU-scale training or reproduction of large climate-model baselines
- Not a general survey of AI-for-climate; related work is scoped to
  positioning the kernel-methods contribution
- No claims that spectral/FFT kernel techniques are new to the literature
  (the contribution is the concrete circulant-block algorithm, its
  consumer-hardware implementation, and the systematic CPU-only benchmark)

## Background & Motivation

The user brief: "AI-for-climate as the experimental substrate, but the
primary research question must be an algorithmic or methodological
innovation in machine learning", under consumer-hardware constraints
(NumPy/SciPy/scikit-learn on 12 CPU cores, 7 GB RAM, under 90 minutes
wall-clock), with a 4-page PDF deliverable. Exact kernel methods are
infeasible for large grids because of the O(N^2) kernel matrix and O(N^3)
solve; randomized approximations (Nystrom, RFF) trade accuracy for memory.
On a regular latitude/longitude grid a stationary kernel yields a
block-circulant matrix whose structure can be exploited with the FFT,
giving exact solves in O(N log N) with O(N) memory. This project turns that
structure into a tested CPU-only algorithm and benchmarks it honestly
against scikit-learn baselines on climate fields, under resource
accounting that consumer-hardware practitioners actually face.

## Scope

### In scope
- Circulant-block exact KRR algorithm and its CPU-only implementation
- SST anomaly fields (open NOAA-family source if fetchable; bundled
  synthetic-from-physics fallback with explicit simulation markers)
- Masked-field reconstruction and Nino3.4 index regression experiments
- Baselines: scikit-learn exact KRR (subsampled), Nystrom, Random Fourier
  Features; block/leave-one-field-out cross-validation
- Resource accounting (wall-clock, peak RSS, flop/memory scaling),
  calibration of predictive intervals, applicability analysis
- 4-page PDF paper (NeurIPS-workshop LaTeX, tectonic) grounded in artifacts

### Out of scope
- GPU or distributed computation
- Deep learning / neural network baselines
- Climate science claims beyond the experimental-substrate use

## Auto Issue Generation

Issues are opened just-in-time by the epic manager per stage entry of the
research-project-epic-manager protocol (anchor first, then splits, then
rework issues on gate routing). No bulk pre-generation.

## Milestones / Timeline

- `2026-08-31` -- Phase A: scoping, epic, control issue, manifest skeleton
- `2026-08-31` -- Phase B: control validation, cost ledger
- `2026-08-31` -- Phase C: JIT stage dispatch + review gates
- `2026-08-31` -- Phase D: collection and settlement
- `2026-08-31` -- Phase E: synthesis to 4-page PDF, writeup clarity gate

## Decisions & ADRs

- `2026-08-31` -- Decision: viable, proceed autonomously (brief concrete,
  environment verified, topic feasible). See orchestration-log comment.

## Risks & Dependencies

- Network fetch of NOAA SST data may fail -> bundled synthetic-from-physics
  fallback with explicit simulation markers (accepted and disclosed).
- 90-minute wall-clock cap -> all experiment scripts run end-to-end via a
  single Makefile target and are timed.
- Tectonic must compile the 4-page PDF; prior project's vendored
  neurips_2026.sty scaffold is available on this host as a fallback.

## Related Epics / Cross-links

- `ccai-neurips2026-groundup-climate` -- prior CPU-only AI-for-climate
  project (different primary question: evaluation protocol for air-quality
  networks; provides the LaTeX scaffold and honest-resources conventions)
