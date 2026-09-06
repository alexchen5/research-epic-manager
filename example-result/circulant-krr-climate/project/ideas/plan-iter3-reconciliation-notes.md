# Iteration-3 plan reconciliation notes (hypothesis-gate round 1)

Status: pre-planning notes; fold into the experiment-planning stage issue on
gate settlement. Only the planning stage issue (or this file's successors)
records the approved plan.

Source of truth for execution: ideas/proposal-final.json (hypothesis artifact,
ideation stop_condition=pass) + results/iter2 canonical artifacts.

## T1b citation convention (locked)

- results/iter2/T1b-CG-masked-train.json (canonical): rate means
  245.1/276.1/280.9 iterations at tol 1e-8; per-field span 233-291;
  final relative residual per-field 4.69e-9..9.81e-9 (rate means
  7.57e-9 / 7.89e-9 / 8.98e-9); RMSE means 0.529-0.541.
- EXECUTION_NOTES pre-fix figures (420-550 iters / RMSE 0.78-0.83) are
  SUPERSEDED (in-file marker); never cited.
- Exact residual range (4.69e-9..9.81e-9) is cited wherever "identical
  relative convention with the PCG reference" is claimed (G2 item 1).

## Hypothesis-gate G1 items (fold as pre-registration strengtheners)

1. Terminology reconciliation: iter3-design-brief.md amended to whole-sample
   WSS (DCT-I, Martucci 45), superseding its earlier "half-sample reflective
   padding" wording; proposal-final terminology governs.
2. S1 rank-assumption falsification guard (make it a scored fail criterion,
   not just a fail-fast heuristic): in A1, measure the relative
   interior-vs-band residual norm across the w-sweep {1,2,3,4}; pre-state
   failure threshold: if the correction rank needed for median residual
   <= 1e-6 exceeds the w(H+W) budget, RE-ABLRC is reported NOT validated.
3. Carry SSAM-CAM iteration-count expectation into the executed plan:
   target < 60-90 equivalent iterations (design brief §3); per-iteration
   cost O(N log N + n); Anderson window m=5 rationale recorded; the
   >= 3x speedup-at-tol<1e-6 win stays falsifiable pre-run.
4. MNIST-784 arm pre-registration: kernel = RBF on pixel coordinates;
   "grid KRR" on 28x28 = stationary BCCB on flattened raster (per-image
   solves); held-out-digit classes + patch-mask splits locked; no post-hoc
   kernel/split selection.
5. Non-blocking: A2 RMSE-parity judged on the SAME valid-cell evaluation
   domain as T1b (mask-excluded valid cells), so parity is interpretable.

## Hypothesis-gate G2 items (fold as pre-registration strengtheners)

6. Unify the method acronym: RE-ABLRC everywhere (problem/method/experiment
   components; no RE-ABLRC/RE-ABRLC variants), with a glossary line mapping
   the corpus G5 "RE (Reflective Embedding)" to the whole-sample symmetric
   (2H-1)x(2W-1) DCT-I-class construction (Martucci entry 45).
7. Small-w regime guard (win-rule precondition): S1 boundary win is claimed
   ONLY for w <= min(H,W)/8; w = ceil(2.5*rho) ~ O(H) as the kernel range
   approaches the grid dimension makes the correction rank ~O(N)
   (effectively dense), silently exiting the O(N log N) + low-rank cost
   regime; the w-sweep fail-fast and 128x128 PCG-dense-equivalent reference
   partially guard this, but the regime condition must be explicit in the
   win rule table.
8. Single win-rule label table (one pre-registration location):
   - S1 boundary win iff median relative gap reduction >= 50% (2D+3D
     pooled) AND median reported residual bound <= 1e-6 AND w <= min(H,W)/8;
     else NOT-validated (if rank budget exceeded) or REFUTED (if the
     DCT/DST 50%-capture consequence fails).
   - S2 speed win iff median wall-clock speedup vs PCG >= 3x at equivalent
     KKT residual < 1e-6 (A2 pooled, RMSE parity); REFUTED iff < 1.5x
     (design-brief §5 semantics).
   - Benchmark: REFUTED iff KISS-GP wins >= 2 domains or dense KRR >= 1
     domain; ties reported, no cherry-picked exclusions.
   - DCT/DST comparator: S1 must capture >= 50% of DCT/DST's own gap
     reduction, else the boundary claim is reported NOT validated against
     the strongest classical boundary-aware baseline.

## Baseline implementations (published conventions)

- dense KRR: exact Cholesky on subsample <= 4000 rows (CPU-only)
- standard PCG: masked Gram (P_m K P_m^T + lam I), BTTB matvec,
  identity + floored-torus preconditioner (iter-2 T1b convention)
- KISS-GP: inducing regular grid + local (bi/tri)linear interpolation,
  Toeplitz-BTTB inducing Gram solved via circulant machinery
- RFF: sklearn Ridge on RFF features (iter-2 B arm)
- optional HSS (Ambikasaran 54): attempted-if-budget, honest
  not-completed report if over-envelope

## Budget envelope (pre-registered)

CPU-only, 12 cores, ~7 GB, <= 90 min total; per-arm caps A1<=25, A2<=30,
A3<=20, A4<=5, A5<=5, A6<=5 (sum 90); measurements amortized as iter-2;
results written to results/iter3/*.json.