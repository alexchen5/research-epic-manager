# 2026-09-02T10:30 -- Review critique

**Agent**: [review-critique: writeup-r1] Writeup-gate aggregate review
(round 1, even count -> lower-middle of pair; A 4, B 3). Clarity 3 ->
failing criterion: Clarity (score 3 < 4). Loop round 1 of
max_writeup_review_loops = 2; revision round 2 dispatched.

Both reviewers independently recomputed every headline number from the
artifacts and verified the verdict chain is derivable from Sections 2-3
(fork A: w_s 31/63 > clamps 8/16 on the 90-row 2D claim pool ->
NOT-validated-guard; pool pin M5; plateau comparisons bracketed
[INVALIDATED HISTORY]; all seven analysis fold-in items located; no
overclaims; appendix self-contained). Clarity held at 3 because the paper
never defines the two quantities that carry the entire S1' verdict
(support distance w_s; the coupling term H_r), never states the capture
metric's formula (per-row F1/DST2 reduction ratio, median over the 82-row
subset with DST2 reduction > 0.5% — 0.7531 is NOT 46.66/58.46 = 0.798),
contains a wrong internal section pointer (Section 3.4 line 186 cites
Section 4.3 for the 16x16 interpretation that lives in Section 4.2), and
mislabels w_design vs clamp at 128x128 (w_design 10, clamp 16).

Revision items (fold into docs/writeup-iter4.md v2):
A1. Section 3.4 3D-range: quoted 'gap_F1 2.23..3.96' does not match
    A1-F1.json — the 9 executed 24^3 rows have gap_f1 min 2.2325974451162653
    and max 4.868281092969756 (matern32 seed 1); correct the max (or state
    which statistic '3.96' is); residual range 2819.1..9871.6 is a genuine
    min-max so ranges must be consistent within the sentence.
A2/B5. Section 4.1 monotonicity: 'the w-sweep residuals decay
    monotonically within the clamp' is contradicted by the 9 non-monotone
    fail-fast rows (all at 64x64: matern32 seeds 7,9,13,14,18; matern52
    13,14,18; rbf 9) — qualify to 'for the 81 non-fail-fast rows' (they
    also REMAIN in the 90-row pooled medians; fail-fast only adds no
    verdict clause).
A3. Section 4.2: 'SOLVE-level exactness is non-monotone in grid size'
    overstates — the tiering covers exactly two small grids (16x16, 32x32)
    and exactness improves 16x16 (0.0414) -> 32x32 (9.19e-5 / 1.65e-12);
    soften to 'kernel-dependent and not a uniform precision tier; the
    smallest grid (16x16) is the worst'.
A4. Abstract '(1.39e-4) flat across sketch sizes' uses the pooled median
    while Section 3.2 quotes probe-row values (1.385e-4/1.427e-4/1.427e-4)
    — harmonize by citing the probe-row tuple in both places.
A5. Trim the '[INVALIDATED-HISTORY motivation only]' tag inside Section
    4.1's parenthetical which obscures the monotonicity clause.
B1. Section 2.1 line 42: define support distance w_s explicitly (w_s =
    max_{i in S} d_cheb(i, seam), row median, compared to min(H,W)/8) and
    the coupling term H_r (reflection/Hankel term H_r(i,t) = k(r_t)
    coupling grid cell i to mirrored cell t) at first use.
B2. State the capture formula once (Section 2.1 or 3.1): per-row capture =
    (F1 gap reduction pct)/(DST2 gap reduction pct); reported metric =
    median over rows with DST2 reduction > 0.5% (82 of 90); reword Section
    4.1 line 196 ('F1's capture ratio of 75.3% of that reduction') so it
    cannot invite 0.7531 x 58.46% = 44.0% arithmetic.
B3. Section 3.4 line 186: correct the pointer '(interpretation in Section
    4.3)' to Section 4.2.
B4. Section 3.1 table: relabel 'w_design (clamp value)' — at 128x128
    w_design = min(ceil(2.5*rho), min(H,W)/8) = 10 while the clamp is 16;
    use 'w_design (= min(ceil(2.5 rho), min(H,W)/8))'.
B5. (merged with A2 above on fail-fast pool membership wording).
B6. Section 2.2: add A2's ridge value (lambda 0.01); currently only A1's
    1e-3 is stated (line 56).
B7. Unit ambiguity stated twice (line 121 note and line 241 fold-in) —
    both consistent, no residual '0.753%' reading anywhere (verified) —
    make line 241 a cross-reference to Section 3.1's note instead of a
    second full statement.

Route decision: revision round 2 within the writeup gate (loop 1 of 2);
on r2 PASS route complete -> finalization (final_verdict APPROVE, status
synthesised, validate_execution.py Checks 1-11).