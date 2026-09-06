# ISSUE writeup-anchor-r3: Writeup of iteration-4 findings

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `writeup-anchor-r3`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `writeup`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Produce the iteration-4 writeup (paper draft) from the gated analysis.
Analysis gate r1 PASS (Significance 4 / Quality 4 aggregate; loop round 1 of
max_analysis_review_loops) with 7 fold-in items. Gated analysis input:
results/analyze-iter4.json (commit de08484; verify_analyze_iter4.py 120
checks pass) -> execution artifacts results/iter4/ (commit 5c8c996;
verify_iter4.py 248/0/2).

Executed outcome (honest pre-registered negative): S1' (F1 primary)
NOT-validated-guard — fork A fires (measured support distance w_s 31.0 at
64x64 > clamp 8; 63.0 at 128x128 > clamp 16; support of K_free - K_embed
covers ALL cells at 64x64 s=4096, median 16308.5 at 128x128; coverage
4.334/6.838). Fork B not reached but would also fail (pooled residual
516.3 >> 1e-6 -> REFUTED-residual) — negative under either branch. Pooled
2D claim (90 rows): gap 46.66% (< 50%), residual 516.3, w_guard True
(structural), capture 0.7531 (ratio = 75.3%, holds under the iter-3
convention). S2' (F2) REFUTED (0.1353x < 1.5x; ssam-nystrom stalls at
1.385e-4 flat across k=64-256, 23.8% converged vs PCG 100%). Benchmark
REFUTED (dense_wins=1, unique grf-2d winner under both tieband and strict
readings; kiss_wins=0). A4 pass. Cross-arm: 42.9 min <= 45-min hard stop;
peak RSS 1.048 GB; A1 (+47 s) / A2 (+19.6 s) budget-exceeded flags
disclosed; 3D rows per-domain under the floor caveat (n_neg 289/4578/7662);
24^3 never pooled (M5); A3 truncated to grf-2d (coverage deltas itemized);
two real-run-only bugs fixed (deterministically recomputed) and disclosed.

Falsified mechanism-level story the writeup must carry: the exact dense
Woodbury-center solve removes in-band truncation, but the pooled residual
plateau (516.3) is unchanged vs iter-3 (532.2; 546.205 vs 546.2021 at
64x64) — falsifying the iteration-3 rank-limited-truncation explanation.
The plateau is far-tail support truncation: the boundary/mirror coupling
of the DST2 whole-sample-symmetric embedding is FULL-SUPPORT-sized, not
band-sized, so the w-clamp family is structurally closed; the full-support
exact center is cost-infeasible at claim scale (nb_tail 12033/48641;
1.16/18.93 GB dense center). F2: the Nystrom preconditioner complement
stalls the masked system (mechanism-level finding). Strategy implication
rankings (F3 repositioning; explicit boundary-value formulations;
inducing-point/DD reformulations) with corpus anchors; the F3 fallback
(negative-result + tooling repositioning) is the pre-registered fallback
strategy of proposal-iter4-v4.

## Acceptance Criteria

- [ ] docs/writeup-iter4.md (+ committed) — title, abstract, honest
      negative-result framing, methods (F1 dense Woodbury-center exact
      solve per proposal-iter4-v4 operator equation WTT u_T = z0[T];
      support measurement; A2 Nystrom-Anderson; A3 benchmark; A4 tooling),
      results (S1' NOT-validated-guard with per-clause attribution; S2'
      REFUTED; benchmark REFUTED), mechanism findings (full-support
      mirror-coupling; plateau unchanged vs rank-limited explanation
      falsified; Nystrom-complement stall), discussion (F3 framework,
      boundary-value formulations, inducing/DD reformulations — honest,
      no overclaim), limitations (3D floor caveat, truncations, budget
      overruns, bug-fix traceability), future work, consistency with the
      literature review corpus.
- [ ] All 7 fold-in items from the analysis-gate critique applied (bug-fix
      disclosure attribution + row-level traceability; capture units
      explicit everywhere; mechanism-claim tiering (rbf 1.65e-12 vs
      matern32 9.19e-5 vs A4 16x16 gap 0.3725 reconciled); A3
      coverage-delta artifact wording flagged + grf-2d internal shortfall
      itemized; f1_exact unmasked disclosure also in A3 artifact; plateau
      re-label ('unchanged', falsifies rank-limited explanation); fork
      consequence one-liner).
- [ ] Honest framing: T1b canonical lock only (results/iter2/T1b-CG-
      masked-train.json 245.125/276.125/280.875 @ tol 1e-8, span 233-291,
      4.69e-9..9.81e-9, RMSE 0.529-0.541); EXECUTION_NOTES/analysis.json
      SUPERSEDED markers (pre-fix 420-550/0.78-0.83 absent); iter-3
      numbers only as INVALIDATED-HISTORY negatives; iter-4 numbers from
      results/iter4 artifacts only; no new-mathematics claims; no
      SOTA-ENSO claim; no O(N^2)-free claim outside stationary
      BCCB/BTTB class; 3D WSS-embedding PSD caveat; 24^3 never pooled
      (M5); 0.1 s rounding; ~2 GB cgroup disclosure; ASCII-only.
- [ ] Cross-references: corpus anchors (Martucci 45, Trench 66,
      Gohberg-Semencul 67, Stewart 73, HSS 54, Graham 70 soft, Barrowes
      72, Strang 74, Frangella-Tropp-Udell 71, Wilson-Nickisch 6) —
      consistent with docs/literature-review/review.md.
- [ ] Committed with message "iter4: writeup draft + verify".

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: results/analyze-iter4.json + results/iter4/* (gated
  analysis + execution), ideas/proposal-iter4-v4.json (hypothesis),
  ideas/experiments/experiment-plan-iter4.json (plan),
  docs/literature-review/review.md (corpus), results/iter2 (canonical),
  results/iter3 (invalidated history), EXECUTION_NOTES.md +
  results/analysis.json (superseded). JIT-opened at analysis resolution;
  writeup worker dispatched on seeding.
- The writeup gate (Quality + Honesty + Clarity) runs after this stage;
  the writeup draft is its evidence input.