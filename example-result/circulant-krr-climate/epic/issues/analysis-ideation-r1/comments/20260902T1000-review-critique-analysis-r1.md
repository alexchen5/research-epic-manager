# 2026-09-02T10:00 -- Review critique

**Agent**: [review-critique: analysis-r1] Analysis-gate aggregate review
(round 1, even count -> lower-middle of pair; A 4/4, B 4/4). Significance 4 |
Quality 4 -> PASS (no failing criteria). Loop round 1 of
max_analysis_review_loops; route decision (PASS_ROUTES[analysis]) -> writeup.

Both reviewers independently recomputed every verdict figure byte-exact from
the raw rows (pooled F1 gap 46.66015125209701, residual 516.3154932313778,
capture 0.7531362234848058, DST2 58.46150923131715; support s 4096/16308.5,
w_s 31/63, coverage 4.334/6.838; nb_tail 12033/48641, center memory
1.16/18.93 GB; S2 speedup 0.1353117243583585 conv 0.238/1.0; A3 winners
under tieband and strict readings; T1b re-read from the canonical artifact)
and confirmed: fork-A precedence correctly applied; truncations and budget
overruns (A1 +47 s, A2 +19.6 s) disclosed; T1b canonical lock;
INVALIDATED-HISTORY bracketing; no pre-fix figures. Significance held at 4
not 5 because the 'barrier is cost, not model error' inference overreaches
the small-grid evidence (matern32 32x32 full-support residual 9.19e-5 is
~92x above the pinned 1e-6 gate; A4 16x16 f1_path_sanity gap 0.3725
unreconciled).

Revision items folded into the writeup brief (no verdict changes):
1. Bug-fix disclosure attribution: analyze-iter4.json states the two
   real-run-only bugs were 'fixed and documented in the runner', but
   scripts/run_iter4.py and scripts/fft_krr_embed.py at 5c8c996 contain no
   bug/fix documentation, no pre/post-fix stale-value inventory, and no
   recompute-scope record. Document the disclosure as living in the
   analysis; add row-level traceability (which rows were stale under each
   bug: diag-plan tuple unpacking; idx_sets_nd dmin tail-indexing, which
   were deterministically recomputed, and pre-vs-post fix value deltas) or
   state that such records were not retained.
2. Capture recomputation units: 'rd2 > 0.5' reproduces only 65 rows /
   0.72977; the claimed 82 rows / 0.7531362234848058 reproduce only under
   the percent-unit reading (rd2% > 0.5, fraction > 0.005, per
   verify_iter4.py). State units explicitly everywhere and align with the
   'positive DST2 reduction' phrasing of the capture clause.
3. Mechanism claim tiering: rbf 32x32 (1.65e-12) demonstrates
   precision-level exactness; matern32 32x32 (9.19e-5, ~92x above 1e-6) is
   conditioning-plausible but unreconciled; A4 16x16 f1_path_sanity
   (full_tail_solve_gap 0.3725, res 0.0414) is the smallest yet worst
   exactness and must be reconciled or quoted with interpretation. The
   supported conclusion is 'truncation is the dominant error at claim
   scale; the full-support center is cost-infeasible' — not 'not model
   error'.
4. A3 coverage-delta artifact wording: A3-multidomain.json says kaplan
   'executed subset (budget)' and grf-3d 'executed per budget' while zero
   rows exist (stop_note 'grf-3d truncated (arm clock)'); flag the conflict
   and itemize the grf-2d internal shortfall (declared 60: kernels
   matern32/rbf x masks 0.1/0.3/0.5 x seeds 0-9; executed 24: matern32
   only, seeds 0-9/0-9/0-3) as a plan-vs-executed delta.
5. f1_exact unmasked free-solve disclosure into A3-multidomain.json itself
   (not only runner comments / analysis); state that the two 32x32
   exactness rows were post-plan additions ('extra tooling diagnostics')
   whose results carry the key mechanism inference.
6. Pooled median residual plateau: 516.3 remains iter-3-magnitude (532.2)
   — phrase as 'the exact in-band solve leaves the ~1e2-1e3 plateau
   UNCHANGED, falsifying the iteration-3 rank-limited-truncation
   explanation and re-labeling the plateau as far-tail support truncation
   per the measured full-support extent'.
7. Fork-consequence one-liner: had fork A not fired (w_s within clamp),
   the pooled residual 516.3 >> 1e-6 would independently trigger
   REFUTED-residual under fork B — the outcome is negative under either
   branch.

Route: PASS -> writeup (JIT-open writeup anchor r3 at stage entry; writeup
gate runs after the writeup stage).