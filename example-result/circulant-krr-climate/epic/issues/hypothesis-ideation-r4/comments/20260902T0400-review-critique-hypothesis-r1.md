# 2026-09-02T04:00 -- Review critique

**Agent**: [review-critique: hypothesis-r1] Hypothathesis-gate aggregate review
(round 1, median of two reviewers; lower-middle for ties). Significance 4
(G1 4, G2 4) | Originality 4 (G1 4, G2 4) -> both criteria meet the bar
(score >= 4). No material integrity mismatches on either card.

Revision feedback (aggregated, all pre-registration strengtheners to fold
into the executed plan, not changes to the proposal's substance):
(1) T1b PCG residual exact re-citation: canonical artifact records per-field
final relative residuals 4.69e-9..9.81e-9 (rate means 7.57e-9/7.89e-9/8.98e-9),
so state that exact range wherever the "identical relative convention with
the PCG reference" claim is made.
(2) Unify the method acronym (RE-ABLRC) across problem/method/experiment
components and add a one-line glossary mapping the corpus G5 "RE
(Reflective Embedding)" to the proposal's whole-sample symmetric (2H-1)x(2W-1)
DCT-I-class construction.
(3) Pre-register a small-w regime guard: the S1 win rule (>= 50% gap
reduction with residual bound <= 1e-6) is claimed only for w <= min(H,W)/8;
w = ceil(2.5*rho) ~ O(H) when the kernel range approaches the grid dimension
makes the correction rank ~O(N) (effectively dense), which would silently
exit the O(N log N) + low-rank cost regime.
(4) Restate the complete win-rule label set in ONE pre-registration table:
S1 win iff median gap reduction >= 50% with residual cap; S2 win iff median
speedup >= 3x, refuted iff < 1.5x (brief semantics); benchmark negative if
KISS-GP wins >= 2 domains or dense KRR >= 1; DCT/DST <= 50%-capture labeled
NOT validated; else refuted-by-design.
(5) Non-blocking nit (G2): A2 RMSE-parity judged on the SAME valid-cell
evaluation domain as T1b.
Minor citation precision (G2): proposal cites "PCG final relative residual
5e-9..8e-9"; canonical is 4.69e-9..9.81e-9 per-field — corrected per item (1).

Route decision: advance to the experiment-planning stage (planning anchor to
be opened, seeded with these items + ideas/plan-iter3-reconciliation-notes.md).
