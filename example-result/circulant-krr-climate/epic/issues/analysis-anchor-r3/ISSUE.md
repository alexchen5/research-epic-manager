# ISSUE analysis-anchor-r3: Analysis of iteration-4 results

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `analysis-anchor-r3`
- **Status:** `resolved`
- **Priority:** `P1`
- **Assignee(s):** `issue-manager (dispatched)`
- **Labels:** `stage`, `analysis`
- **Workspace:** `/workspace/research-project-manager/projects/circulant-krr-climate/`
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Synthesize and critically analyze the iteration-4 execution results
(results/iter4/, committed 5c8c996; verify_iter4.py 248 checks / 0 failures /
2 honest warnings). Iteration-4 gated hypothesis was F1 (DST2-embedding
exact/mixed boundary solver; dense Woodbury-center exact solve WTT u_T =
z0[T]; structural w-clamp w_design = min(ceil(2.5*rho), min(H,W)/8);
pre-committed precedence fork). Executed verdicts:

- S1' (F1): **NOT-validated-guard** — fork A fires: measured support
  distance w_s median 31.0 (64x64) / 63.0 (128x128) exceeds the clamp
  8 / 16; fork B (residual) not reached. Pooled 2D claim (90 rows): gap
  reduction 46.66%, relative system residual 516.32, capture 0.75%
  (DST2 comparator 58.46%), w_guard True (structural). Per-grid:
  64x64 47.87% / 546.2 / capture 0.737 (9 fail-fast), 128x128 45.81% /
  462.3 / capture 0.881. 3D rows per-domain only under the floor caveat
  (n_neg 289/4578/7662; floor error 1.087; min spec0 -3.34/-30.69; refs
  PCG-1e-8 rel 9.98e-9). Support: s=4096 (all cells) 64x64 / median
  16308.5 128x128, coverage 4.33 / 6.84, threshold 1e-6-scaled; cond(WTT)
  1729.7/442.5/486.1 (64x64) and 4358.3/1421.0/2857.7 (128x128); full-tail
  diagnostics capped nb=4000 with honest not-completed notes
  (nb_tail 12033/48641); 32x32 exact refs matern32 res ~1e-4, rbf ~0.
- S2' (F2): **REFUTED** — median speedup 0.135x < 1.5x (147-row pool:
  120 grf-2d + 27 grf-3d); PCG 290 iters median, 100% converged, rel
  9.0e-7 vs ssam-nystrom 500-iter ceiling median, 23.8% converged, rel
  1.39e-4; k-sweep {64,128,256} flat at 1.4e-4; matched 1e-8 subset never
  converges (1.1e-4..3.1e-4); DST2-block/spectral Anderson variant
  converged 384 iters on probe (honest variant data); deflation
  not-completed; kaplan parity 0 rows truncated (disclosed).
- Benchmark (A3): **REFUTED** — dense KRR wins 1 domain (grf-2d
  0.0613476449 vs PCG 0.0613476783: tied under 0.5% band, cost gate ->
  dense unique winner 0.68 s vs 1.64 s; literal no-tieband strict row
  agrees), kiss_wins=0; A3 truncated to grf-2d 24 rows under the hard
  stop (coverage deltas disclosed); f1-exact disclosed as unmasked.
- A4 tooling pass; total 2571.3 s = 42.9 min; peak RSS 1.048 GB.

The analysis must interpret the NOT-validated-guard outcome honestly: the
w-guard structural clamp holds, but the measured far-tail support (w_s up to
63 at 128x128 — support covers ALL cells at 64x64) exceeds the clamp, so the
pre-committed fork A fires; the residual plateau (~516-546) persists. The
exact-solve mechanism removed truncation error within the band but the
far-tail support outside the clamp dominates — the "boundary effect" is not
band-sized. DST2 comparator achieves 58.46% reduction (honest negative is
that the F1 pipeline must beat/complement that). Iteration-4 verdict:
hypothesis NOT validated (primary and fallback arms REFUTED on their own
rules); this is a legitimate negative result that closes the exact-solve
strategy family and motivates the next-iteration strategy decision.

## Acceptance Criteria

- [ ] results/analyze-iter4.json with verdict-by-arm synthesis (S1'
      NOT-validated-guard with fork A evidence; S2' REFUTED; benchmark
      REFUTED; honest-negative framing), per-clause attribution,
      iteration-4 cross-arm summary, strategy implications (F1 family
      closed by support measurement; F2 family REFUTED; candidate
      next-iteration directions ranked with corpus anchors), and
      future-blind consistency notes.
- [ ] Honest framing: T1b canonical lock only
      (results/iter2/T1b-CG-masked-train.json 245.125/276.125/280.875 @
      tol 1e-8, span 233-291, 4.69e-9..9.81e-9, RMSE 0.529-0.541);
      EXECUTION_NOTES/analysis.json SUPERSEDED markers; iter-3 numbers
      only as INVALIDATED-HISTORY negatives; iter-4 numbers from
      results/iter4 artifacts only; no new-mathematics/SOTA claims; 0.1 s
      rounding; ~2 GB cgroup disclosure; 3D floor caveat.
- [ ] All numbers artifact-traced (results/iter4/A1-F1.json,
      A2-F2.json, A3-multidomain.json, A4-tooling.json,
      results_summary.json, meta.json); no pre-fix figures; ASCII-only.
- [ ] Committed to the workspace repo with the message
      "iter4: analysis artifact + verify".

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

_Resolution recorded on stage completion._

## Notes

- Input at seeding: results/iter4/* (execution artifacts),
  ideas/experiments/experiment-plan-iter4.json (approved plan + label
  table), ideas/proposal-iter4-v4.json (gated hypothesis),
  docs/literature-review/review.md (74-entry corpus), results/iter2
  (canonical), results/iter3 (invalidated history), EXECUTION_NOTES.md +
  results/analysis.json (superseded). JIT-opened at execution resolution;
  analysis worker dispatched on seeding.
- The analysis gate (Significance + Quality) runs after this stage; the
  analysis artifact is its evidence input (like earlier iterations).