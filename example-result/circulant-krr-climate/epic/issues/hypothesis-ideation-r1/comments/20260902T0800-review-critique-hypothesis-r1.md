# 2026-09-02T08:00 -- Review critique

**Agent**: [review-critique: hypothesis-r1] Hypothesis-gate aggregate review
(round 1, even count -> lower-middle of pair; A 4/4, B 3/4). Significance 3 |
Originality 4 -> failing criterion: Significance (score 3 < 4). Loop round 1
of max_hypothesis_review_loops = 2; revision round 2 dispatched.

Both reviewers independently re-derived every cited iteration-3 honest
negative from the artifacts (47.3574% / 532.2245 / 546.2021 & 415.7885 per
grid / rank 1233 / guard {null,true,false} / 9-of-141 fail-fast at 64x64 /
DST2 61.62% vs DCT1 -1872.63% / capture 0.7467 & 0.7284 / 24^3 DST2 95.06% /
n_neg {289,4578,7662} / speedups 0.2374-0.1624x / iters 278.5 vs 192.0 / conv
77.7% vs 100% / RMSE parity 0.3504163 vs 0.3504185 / A5 259-384 vs 4.1e5-7.4e5
/ A6 0.0453 s / 2296.5 s & 0.9786 GB) and the T1b canonical lock
(245.125/276.125/280.875 @ tol 1e-8, span 233-291, 4.69e-9..9.81e-9, RMSE
0.529-0.541) — all verified byte-level; no pre-fix T1b figures; no SOTA-ENSO
or new-mathematics overclaims; entries 70-74 web-verified in corpus.

Significance-3 rationale (reviewer B): the F1 falsification path is real
(residual convention pinned to PCG-style relative system residual; per-clause
reporting pre-committed; NOT-validated vs REFUTED unambiguous), but the
primary mechanism is under-specified exactly where the win rests: the
boundary-band system is never defined (no operator equation, bandwidth, or
conditioning), and the iteration-3 honest negative (T_size 1233 ~ 96% of the
1280 rank budget at 64x64, residual still 546, interior_res 0.58-0.98)
implies the truncation the exact solve removes may not be the binding
failure.

Revision items (fold into proposal-iter4-v4):
A1. Pre-commit S1' pooled-composition semantics for 3D: state explicitly
    whether the pooled median includes floor-limited 24^3 rows or reports
    them per-domain only (recommended: primary residual/gap gate on the 2D
    pool; 3D per-domain under the floor caveat — one committed reading).
A2. Align risk_statement interior-res range to the measured artifact:
    0.433-0.901 (median 0.617 at 64x64, 0.764 at 128x128; only 12/75 rows
    >= 0.8); sweep-level 0.585-0.984 band 0.016-0.415 usable for the sketch
    wording; one consistent traceable range.
A3/B4. Stewart 73 complexity: pick O(L log^2 L) or O(n log^3 n) and state
    identically in the sketch, corpus anchors, and glossary (exactness claim
    independent of exponent).
B1. Define the boundary-band system as an explicit operator equation (e.g.,
    the Schur-complement system on the edge-band index set of (K_free +
    lambda I), or the Woodbury center restricted to the band, with
    derivation from the support of K_free - K_embed) and justify bandwidth:
    the corner-support difference is dense within the band — if 'banded'
    with bandwidth O(w) then cost O(N_b w^2) must be justified, else the
    true cost is O(N_b^3) and the complexity claim collapses.
B2. State the conditioning assumption (SPD post-floor+ridge? banded
    Cholesky needs it; condition estimate per grid) and how the exact
    solution maps back to alpha.
B3. Pin whether the w-band covers the FULL support of K_free - K_embed or
    truncates it, with a per-grid support-rank measurement, and pre-commit a
    discriminating diagnostic (a few full-support exact reference rows at
    64x64/128x128) separating interior-model-error from inner-solve
    truncation.
B4. (merged with A3 above).
B5. Soften the Graham 70 attribution: the corpus has no DCT/DST-class PSD
    floor bound — report the 3D floor error as a per-row measured
    a-posteriori quantity, not a theorem-backed bound.

Route decision: revision round 2 within the hypothesis gate (loop 1 of 2);
on r2 PASS advance to experiment_execution (PASS_ROUTES[hypothesis]).