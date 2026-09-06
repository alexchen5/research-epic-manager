# ISSUE hypothesis-rework-r1: Hypothesis rework (iteration 2, gate round 1)

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `hypothesis-rework-r1`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee:** `issue-manager`
- **Labels:** `stage`, `hypothesis`, `rework`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-08-31`
- **Updated:** `2026-08-31`

## Description

Iteration-2 hypothesis gate round 1 did not meet the acceptance bar on
Significance (3) or Originality (2, median of two reviewers). Rework the
selected proposal (ideas/proposal-final.json, iteration 2 = proposal-v3)
into a revised hypothesis that closes the gate feedback, then re-gate
(round 2). The honest ceiling framing (no FFT-kernel/spectral-regression/
SOTA-ENSO newness claims) is retained; the revision must make the
evaluation protocol itself the operational originality claim and sharpen
the significance framing with pre-registered decision rules.

## Acceptance Criteria

- [ ] Revised hypothesis artifact written (ideas/proposal-it2-v4.json) with:
      1) pre-registered forecast win criteria (per-h skill margin vs
         year-block bootstrap CI; supported/refuted semantics);
      2) conformal adapted to non-exchangeable seasonal/autocorrelated
         residuals (calendar-month-block calibration), coverage reported
         separately for seam-leakage and decay-phase subsets with
         tolerances;
      3) control arm: non-spectral exact KRR reference (Cholesky on a
         subsampled grid) on the SAME real data isolating the
         circulant/FFT contribution;
      4) grid-resolution sensitivity note (5 vs 1 deg) + ENSO predict
         floor at long horizons;
      5) data pinned (artifact id, h5py read path) + seed/randomness +
         per-run wall-clock/peak-memory for rerunnability;
      6) real-data threats handled: Kaplan smoothing (reconstruction-
         informed values), land/missing mask patterns, PCG-convergence
         failure-mode plan on real masked grids;
      7) seam check numeric: Dec-Jan block boundaries, training-fold
         truncation, skill change when discarding 1-3 trailing months.
- [ ] [seeded-fail-feedback] comment posted; [proposal-v4] comment with
      the revised hypothesis posted; gate round 2 dispatched and verdict
      recorded in project.json.

## Comments

_Threaded via add-comment._