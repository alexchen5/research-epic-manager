# 2026-09-02T02:30 -- Comment

**Agent**: [review-critique: ideation-r4-r2] Round-2 ideation aggregate (median;
even count -> lower middle; PASS >= 4):

- Clarity **3** | Relevance 4 | Originality 4 | Feasibility 4 | Significance 4
  -> **median_min 3 < 4 => FAIL (route: proposal revision, round 3).**

Reviewer C (r2, 9ad30de2): Clarity 3 / Relevance 4 / Originality 4 /
Feasibility 4 / Significance 4. Items: (1) reconcile "exact free-boundary" vs
bounded-residual approximate in gaps_closed/win rule end-to-end; (2) pin
SSAM-CAM masked-arm spectral-step kernel operator to the same free-boundary
BTTB objective the PCG reference minimizes (like-with-like speedup/parity);
(3) fix band-width rule 2.5-factor double-use + 3D cost arithmetic (r_3d =
w(HW+HD+WD) at w=3 on 24^3 = 3*1728 = 5184; r^2 ~ 26.9e6 doubles ~ 215 MB);
(4) give the DCT/DST comparator a pre-registered win consequence (S1 must
capture >= 50% of DCT/DST's own gap reduction, else boundary claim reported
as NOT validated against the strongest classical boundary-aware baseline);
(5) pre-register w-sweep {1,2,3,4} fail-fast if residual does not decay
monotonically (guards corpus-reported naive embed-solve plateau ~ 0.18 rel,
EXECUTION_NOTES item 1). Minor: RE vs WSS acronym mapping note; A2 grid
sizes; S1 x S2 joint arm.

Reviewer D (r2, 6ff3c8e5): Clarity 3 / Relevance 4 / Originality 4 /
Feasibility 4 / Significance 4. Items: (a) recompute 3D cost figures as above;
(b) make A1/win-rule text internally consistent with the budget envelope:
dense free-boundary reference = Cholesky at 64x64 and 24^3 only, PCG solve of
the free-boundary BTTB at residual tol 1e-8 (dense-equivalent) at 128x128,
stated in win_rules not just the budget note; (c) reconcile SSAM-CAM with the
masked-Gram system: restrict coefficients to observed-cell support (a =
P_m^T w) so the objective coincides with (P_m K P_m^T + lam I) w = y_m, name
the shared system in A2, replace the unqualified fixed-point sentence with the
KKT-residual stopping + RMSE-parity equivalence criterion; (d) enumerate the
five methods in A3 explicitly + HSS as optional sixth (attempted-if-budget,
honest not-completed report); (e) rename or note RE retained from corpus
nomenclature (WSS expansion = same construction); (f) add "superseded" marker
to EXECUTION_NOTES for the 420-550-iteration / RMSE 0.78-0.83 T1b numbers so
the discrepancy claim matches the file.

Manager revision **proposal-it4-v3.json** (committed 457dcce) folds ALL items
(a)-(f) and C items (1)-(5) — verified on disk: win_rules boundary text now
carries the 128x128 PCG-dense-equivalent reference convention; S2 formulation
restricts coefficients to observed-cell support with the shared masked-Gram
system named in A2 and KKT-residual stopping; A3 enumerates five methods +
HSS-optional; 3D cost arithmetic corrected (r_3d = 5184, r^2 ~ 215 MB);
G5 wording bounded-residual; DCT/DST secondary win consequence; w-sweep
fail-fast guard; RE/WSS acronym mapping note; S1xS2 joint arm noted.

Round-3 ideation reviewers dispatched on proposal-it4-v3.json (final ideation
round; max_rounds = 3).
