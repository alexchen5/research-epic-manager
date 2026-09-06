# Boundary-aware spectral kernel ridge regression on regular grids: a pre-registered negative-result study of exact DST2-embedding boundary solves and randomized-Nystrom-preconditioned masked solves (iteration-4)

Project: circulant-krr-climate -- Iteration-4 writeup draft (paper draft, Markdown).
Pre-registration: ideas/proposal-iter4-v4.json (gated hypothesis) and ideas/experiments/experiment-plan-iter4.json (approved plan).
Execution: results/iter4/*.json (commit 5c8c996); gated analysis: results/analyze-iter4.json (commit de08484).
Status: honest negative-result study (pre-registered fallback F3). All iteration-3 measured values cited below are INVALIDATED HISTORY and appear only as honest negatives.
Writeup revision: v2 (revision_of v1; writeup-gate r1 FAIL on Clarity, A4/B3 lower-middle; loop 1 of 2). revision_delta: A1 (3D informational gap range corrected to the genuine min..max 2.23..4.87, stated consistently with the residual min..max in the same sentence); A2/B5 (w-sweep monotonicity qualified: 81 non-fail-fast rows decay within the clamp to the ~500 plateau; 9 fail-fast rows disclosed, non-monotone, and remain INSIDE the 90-row claim-pool medians); A3 (exactness-tier wording: kernel-dependent, not a uniform precision tier, no grid-size non-monotonicity claim; claim-scale confounded by the nb=4000 cap); A4 (abstract F2 stall figure harmonized with Section 3.2: probe-row k-sweep tuple 1.385e-4 / 1.427e-4 / 1.427e-4 across k = 64/128/256); B1 (support distance w_s and the coupling term H_r defined at first use in Section 2.1); B2 (per-row capture formula stated once and disambiguated from ratios of pooled medians); B3 (internal pointer fixed: the A4 small-grid interpretation reference now points to Section 4.2, the exactness-tiering subsection); B4 (Section 3.1 table relabeled with the w_design formula, so no reader infers w_design IS the clamp); B6 (A2 ridge lambda = 0.01 stated in Section 2.2); B7 (Section 6 capture-unit mention reduced to a cross-reference to the Section 3.1 note). All other numbers (beyond the A1/A4 corrections above), INVALIDATED-HISTORY brackets, appendix, and references byte-stable from v1.

## Abstract

This paper reports a pre-registered, falsifiable evaluation of two strategy families for boundary-aware spectral kernel ridge regression (KRR) on regular grids. Family F1 (primary) replaces the rank-limited Woodbury boundary correction of a whole-sample-symmetric DST2 embedding with an EXACT dense solve of the Woodbury-center reduced system, under the structural clamp w <= min(H,W)/8. F1 is NOT-validated at the guard: the measured numerical support of the mirror/boundary coupling of the DST2 embedding of the free operator has FULL-SUPPORT extent (support set = all 4096 cells at 64x64; median support distance w_s 31/63 vs clamps 8/16), so fork A of the pre-committed precedence mapping fires and no w-clamp regime can contain the boundary effect; fork B (pooled residual 516.3 >> 1e-6) would independently trigger REFUTED-residual, making the outcome a measured NEGATIVE under either branch. Family F2 (contingent, randomized-Nystrom-preconditioned Anderson mixing for masked Gram systems) is REFUTED at 0.1353x median speedup vs PCG (< 1.5x bar); the Nystrom preconditioner stalls on its complement (~1.4e-4 flat across k: probe-row residuals 1.385e-4 / 1.427e-4 / 1.427e-4 over the k-sweep {64, 128, 256}; matched-1e-8 subset never converges). The four-domain benchmark is REFUTED (dense KRR uniquely wins grf-2d under both the 0.5% tieband + cost gate and the literal no-tieband reading; KISS-GP wins 0 domains). Two mechanism findings shape the negative: (i) the exact center solve removes in-band truncation but leaves the pooled residual plateau UNCHANGED vs iteration-3 (516.3 vs 532.2 pooled; 546.205 vs 546.2021 at 64x64, the iteration-3 values being [INVALIDATED HISTORY]), falsifying the iteration-3 rank-limited-truncation explanation -- the plateau is far-tail support truncation of a full-support-sized coupling, and the exact full-support center is cost-infeasible at claim scale (nb_tail 12033/48641; center memory ~1.16/18.93 GB; O(nb^3) solve); and (ii) the DST2 comparator itself (58.46% pooled median gap reduction) remains the empirically best classical boundary-aware class on this regime. Per the pre-registered fallback F3, the deliverable is a complete honest-negative + tooling study: the boundary-controlled GRF generator and F1 spectral tooling pass their self-checks (A4).

## 1 Introduction / motivation

Kernel ridge regression with stationary kernels on regular grids admits fast structured algebra: the kernel matrix of a stationary kernel on a rectangular grid is block-Toeplitz with Toeplitz blocks (BTTB), and the block-circulant (BCCB) wrap-around approximation of it is diagonalized by the FFT, giving O(N log N) solves on the torus. The climate-field problem of interest (masked SST-field reconstruction on the Kaplan SST v2 grid, and free-boundary grid fields in general) is NOT a torus problem: the free boundary (the finite domain boundary of the observed grid) couples the solution to the domain edge, and a plain BCCB (toroidal wrap) solve produces visible boundary artifacts relative to the exact free-boundary solve. The measured gap between the BCCB-wrap approximation and the free-boundary reference is the target quantity of the boundary arm of this project (results/iter2 canonical artifacts; P0 pilot: torus-vs-free gap 0.9496 for matern32 at 36x72 [canonical iteration-2 artifact]).

The project's boundary line of attack compares three classical spectral boundary classes on the regular grid:

- BCCB: the torus/circulant wrap (baseline whose gap is reduced).
- DCT1 (whole-sample symmetric, DCT-I-class embedding): the whole-sample symmetric mirror embedding diagonalized by the DCT-I class (Martucci 45).
- DST2 (whole-sample symmetric, DST-II-class embedding): the empirically superior classical boundary-aware class on the measured regime (iter-3 measured DST2 pooled median gap reduction 61.62% vs DCT1 -1872.63% [INVALIDATED HISTORY - honest negative]; iteration-4 measured DST2 pooled median gap reduction 58.46%, still ahead of the F1 solver's 46.66%).

The gap G5 of the project corpus (exact free-boundary fast grid kernel solves) remains open from the iteration-3 cycle. The iteration-3 execution FAILED its pre-registered gates (S1 NOT-validated, S2 REFUTED, benchmark not-refuted) at the analysis gate; all iteration-3 measured artifacts are INVALIDATED HISTORY and are cited here only as honest negatives: the iteration-3 F1-predecessor (RE-ABLRC, a rank-limited Woodbury correction of rank |T| = O(w(H+W))) reached a median free-boundary gap reduction of 47.3574% (< the 50% bar) with a pooled median corrected residual of 532.2245 (>> 1e-6) and per-grid residual plateaus 546.2021 (64x64) / 415.7885 (128x128) at a median rank budget |T| = 1233 [INVALIDATED HISTORY]. The iteration-3 numbers never appear in this paper as qualifying claims.

Iteration-4 re-enters the hypothesis stage (gated proposal v4; approved plan; rework-r2 literature review with entries 70-74) with three pre-registered strategy families: F1 (primary) -- EXACT band/center solves on the DST2 whole-sample-symmetric embedding, with the w regime made structural via the clamp w_design = min(ceil(2.5*rho), min(H,W)/8); F2 (contingent secondary) -- randomized-Nystrom-preconditioned Anderson mixing for the masked Gram system; F3 (fallback) -- if the gates fail again, the deliverable is explicitly a negative-result + tooling study under the same pre-registered label table. The present paper is the F3 deliverable: iteration-4 is a measured NEGATIVE for both pre-registered strategy families (F1 NOT-validated-guard; F2 REFUTED; benchmark REFUTED), with a tooling deliverable that passes its self-checks.

## 2 Methods

### 2.1 F1 (primary): exact dense Woodbury-center solves on the DST2 whole-sample-symmetric embedding

Operator setup (per the gated proposal's pinned operator equation, F1_operator_equation):

- N = H*W (3D: H*W*D). K_free is the free-boundary BTTB Gram of a stationary kernel (matern32, matern52, rbf; ell = 4.0 grid units, rho = 4.0), SPD for the matern kernels, PSD-floored + ridge for rbf with n_neg disclosed per grid.
- M = K_emb + lambda I, where K_emb is the whole-sample-symmetric circulant embedding of the (2d-1)-per-axis mirror of the kernel, whose leading (principal) block is matvec-EXACT for the free operator K_free (code selfcheck; A4 16x16 matvec exactness 2.34e-16; also 32x32/64x64 rows confirm).
- a0 = (M^{-1} Y)|prin with Y the zero-padded right-hand side -- the "naive" embedded solve restricted to the grid (the DST2 comparator is this naive solve; the BCCB comparator is the torus solve).

Boundary system (the F1 replacement for the iteration-3 rank-limited Woodbury [INVALIDATED-HISTORY provenance]): by principal-block exactness, the solve discrepancy of a0 is exactly the uncorrected coupling of principal rows with mirror (tail) cells. F1 assembles the Woodbury-center reduced system on the band index set T (tail cells within Chebyshev distance < w of the seam):

    WTT u_T = z0[T],   WTT = M^{-1}[T, T],

and solves the center DIRECTLY and exactly (dense symmetric SPD factor, no rank truncation; per-grid cond(WTT) measured, e.g. median condition 1729.7 (matern32, 64x64) / 4358.3 (matern32, 128x128)). The map-back is alpha = a0 - M^{-1}u with u = u_T on T and zero elsewhere, via the spectral inverse (O(N log N)). The center is DENSE (no O(w)-bandwidth sparsity exists; the "banded O(N_b w^2)" reading of earlier proposal drafts is retracted per the gated proposal): true cost O(nb^3) time / O(N + nb^2) memory with nb = |T| support-rank-measured. Structured speed paths (1D Trench/Gohberg-Semencul exact solves, Stewart superfast solve, HSS re-seeding) were pre-committed attempted-if-budget.

Support measurement (pre-committed, B3 pin): the reflection/Hankel coupling term H_r(i, t) = k(r_t) is the term coupling grid cell i to its mirrored cell t in the DST2 whole-sample-symmetric embedding (r_t the reflected distance); support set S = {cells: |H_r| > 1e-6 * max|H_r|}, threshold tied to the 1e-6 relative-residual convention (row example 64x64 matern32 seed 0: threshold 7.1e-4); support rank s = |S|; support distance w_s = max_{i in S} d_cheb(i, seam), the Chebyshev distance from the embedding seam (the boundary between the principal grid and the mirrored tail) to the farthest cell of the support S; coverage ratio s/|T_w| -- all reported per grid, with w_s reported as the row median and compared to the clamp min(H,W)/8.

Precedence fork (ONE pre-committed mapping, no ambiguity): (fork A) w_s > min(H,W)/8 on ANY 2D claim grid -> NOT-validated-guard, with w_s/s/coverage reported per grid; (fork B) w_s <= min(H,W)/8 but the 2D claim-pool median relative system residual > 1e-6 -> REFUTED-residual (reference-independent).

Win rules (verbatim label table, plan-iter3-reconciliation-notes.md item 8, with iteration-4 modifications M1/M2/M5): S1' WIN iff median free-boundary gap reduction >= 50% (2D claim pool) AND median reported relative system residual <= 1e-6 (pinned convention ||(K + lambda I) alpha_hat - y|| / ||y||) AND w <= min(H,W)/8 on every pool grid (structural clamp) AND capture >= 50% of the DST2 comparator's own gap reduction; REFUTED iff the exact band solve still leaves median residual > 1e-6 on the 2D claim pool or the capture consequence fails; else NOT-validated with per-clause reporting (clause/grid named).

M5 pool pin: the S1' gap and residual gates apply to the 2D CLAIM POOL ONLY -- all 64x64 and 128x128 w_design rows under the clamp (64x64: seeds 0-19, 60 rows, w_design 8; 128x128: seeds 0-9, 30 rows, w_design 10; total 90 rows). The 24^3 rows are reported per-domain ONLY under the 3D floor caveat and NEVER enter the pooled medians; REFUTED can be triggered only by a 2D claim-pool failure.

w-sweep fail-fast (iteration-3 convention, pre-registered): monotonic residual decay over the sweep w in {1,2,3,4} (the w_design point is the clamped operating width, excluded from the sweep-only monotonicity check; a small increase at the w_design step is not fail-fast); non-monotonic sweep rows fail-fast and are recorded.

References: 64x64 = dense Cholesky of the free BTTB Gram (pre-registered); 128x128 = PCG tol 1e-8 dense-equivalent (identical relative convention to T1b); 24^3 = dense Cholesky NOT pre-registered (estimated ~3.1 GB peak > ~2 GB cgroup; iteration-3 precedent: three OOM-killed attempts [INVALIDATED HISTORY - disclosure template]) -- executed 24^3 reference = container-forced PCG tol 1e-8 deviation, disclosed.

Diagnostic rows (pre-committed): 9 budgeted full-tail exact reference rows (64x64: 3 kernels x seeds 0,1 = 6; 128x128: 3 kernels x seed 0 = 3), center = FULL support, support capped at the cgroup-permitted center size with honest not-completed wording otherwise; plus two small-grid exactness references at 32x32 (post-plan diagnostics; see Section 6).

Lambda = 1e-3 (A1). Grids 64x64 and 128x128 (2D claim pool) and 24^3 (3D, per-domain only).

### 2.2 F2 (contingent): A2 masked arm -- randomized-Nystrom-preconditioned Anderson mixing

Shared masked-Gram system, identical for both solvers: (P_m K P_m^T + lambda I) w = y_m (P_m the observation mask; coefficients restricted to the observed-cell support a = P_m^T w; the same system standard PCG solves, iteration-2 T1b convention [canonical reference: per-field relative residuals 4.69e-9..9.81e-9 at tol 1e-8]). Ridge: lambda = 0.01 (A2 pre-registration; the A1 boundary arm uses lambda = 1e-3, see Section 2.1). Solvers:

- ssam-nystrom: Anderson mixing window m = 5 (iteration-3 A5 ablation: Anderson ESSENTIAL -- without it the solver stalls at the 500-iteration ceiling at relative residual ~4.1e5-7.4e5; with it 259-384 iterations to ~1e-6 [INVALIDATED HISTORY - honest negative]) + randomized-Nystrom preconditioner of the masked Gram (Frangella-Tropp-Udell 71), sketch sizes k in {64,128,256} disclosed per row, small-k sweep on a probe row; spectral step O(N log N).
- pcg reference: standard PCG, BTTB matvec + identity/floored-torus preconditioner (iteration-2 T1b convention).

Termination: KKT residual r_t := (P_m K P_m^T + lambda I) w - y_m, relative to ||y_m||, IDENTICAL convention for both solvers; primary gate < 1e-6, matched secondary 1e-8; iteration ceiling 500. Win rule S2': >= 3x median wall-clock speedup at equivalent KKT < 1e-6 with RMSE parity on the T1b valid-cell domain; REFUTED iff < 1.5x; 1.5-3x = NOT-validated tie-band case. Pool composition PRE-DISCLOSED: grf-2d (2 grids x 3 kernels x 4 masks x seeds 0-19 = 480 declared; budgeted subset seeds 0-4 = 120 rows), grf-3d (24^3 x 3 kernels x 4 masks x seeds 0-9 = 120 declared; budgeted subset seeds 0-2 = 36 rows), mnist-784 (n >= 10), kaplan-sst-v2 (44 fields x 3 masks = 132 rows template). Truncation priority: synthetic 2D first, synthetic 3D second, kaplan last (real-data rows preserved last under the future-blind lock). Variant candidates (attempted-if-budget, honest not-completed if over-envelope): DST2/block-structure preconditioner; dominant-eigenspace deflation.

Future-blind kaplan conventions (locked): mask seed 7; train idx 0..1919 (1856-01..2015-12), test idx 1920..2003 (2016-01..2022-12), idx 2004 (2023-01) EXCLUDED from both splits; missing-cell sentinel |x| > 1e30 (53.4% missing); h5py route.

### 2.3 A3 benchmark: 4 domains x 5 methods

Domains: grf-2d (declared seeds 0-9), grf-3d (declared seeds 0-3 or budgeted subset with disclosure), mnist-784 (28x28 grid KRR, RBF on pixel coordinates, held-out digit classes + patch masks locked before runs, n >= 10), kaplan-sst-v2 (real, future-blind as iteration-2/3). Methods: f1_exact (the iteration-4 boundary solver; NOTE: unmasked full-field solve -- see Section 3.3 disclosure), standard_pcg, dense_krr (exact Cholesky on subsample <= 4000 rows), kiss_gp (inducing grid + local interpolation; Wilson-Nickisch 6), rff (sklearn Ridge on RFF features). Metrics: rmse_valid_only (mask-excluded cells), wall_clock_s, peak RSS, est flops/bytes, accuracy-per-flop/byte, iterations_to_tol, speedup_vs_pcg, boundary_gap_reduction_pct.

Tieband convention (reviewer-fixed, uniform): per-domain median-RMSE ratio (method_median / best_median - 1), 0.5% relative band, applied uniformly; a LITERAL no-tieband sensitivity row (0.0% band -> strict winner counts) REQUIRED. Cost-clause parse: win is RMSE-first (best or within tie band); cost (wall clock) is a credibility gate (win requires median wall <= best-RMSE-method wall + 0.1 s rounding tolerance); ties reported; no cherry-picked exclusions. Benchmark verdict rule: REFUTED iff KISS-GP wins >= 2 of 4 domains OR dense KRR wins >= 1 of 4 domains in RMSE at equal-or-lower cost envelope. Plan-vs-executed coverage deltas are itemized as honest negatives (A3 coverage_delta_registration).

### 2.4 A4 tooling

scripts/grf_boundary.py selfcheck (free / Dirichlet-zero / Neumann-zero / mixed boundary-value sets; whole-sample-symmetric circulant-embedding exact sampling; Paciorek-Schervish non-stationary covariance path; seeds 0-19) + F1 path sanity at 16x16 (build-vs-direct residual of the exact full-tail solve; matvec exactness of the embedded operator vs the dense free Gram).

### 2.5 Seeds and budget conventions

Seeds: synthetic 2D 0-19 (claim pool 64x64 seeds 0-19; 128x128 seeds 0-9), synthetic 3D 0-9, kaplan split as above with mask seed 7, bootstrap 7 (iteration-2/3 convention, preserved; per-domain random-mask draws seeded from it); every truncation is a disclosed execution-truncation, never a seed/split change. Budget: CPU-only, 12 cores, ~2 GB cgroup ACTUAL cap (the project envelope claim <= 7 GB is superseded by container reality), 45-min total hard stop; per-arm caps A1 20 / A2 18 / A3 7 / A4 2; 0.1 s rounding convention for arm clocks; any arm exceeding its cap is flagged (budget_exceeded) per the iteration-3 disclosure template; truncation priority: claim rows first, diagnostic rows second, seeded subset (3D) last.

## 3 Results

### 3.1 S1' (F1 primary): NOT-validated-guard -- fork A fires on both 2D claim grids

Fork A evidence (support measurement, per-grid, from the 90-row 2D claim pool; results/iter4/A1-F1.json per_grid.support blocks, recomputed from rows in the analysis and in the verifier):

| Quantity | 64x64 | 128x128 |
|---|---|---|
| claim rows n | 60 | 30 |
| clamp min(H,W)/8 | 8 | 16 |
| w_design (= min(ceil(2.5 rho), min(H,W)/8)) | 8 | 10 |
| w_guard (w <= clamp, by construction) | True | True |
| median support distance w_s | 31.0 (max 31.0) | 63.0 (max 63.0) |
| median support rank s | 4096.0 (= ALL 64x64 cells) | 16308.5 (~99.5% of 16384 cells) |
| median coverage s/|T_w| | 4.334 | 6.838 |
| median gap reduction vs BCCB | 47.874% | 45.808% |
| median relative system residual | 546.205 | 462.259 |
| median capture ratio vs DST2 | 0.7374 | 0.8812 |
| median DST2 comparator reduction | 61.044% | 45.263% |
| median gap BCCB (wrap baseline) | 2.630 | 6.627 |
| fail-fast rows (non-monotone w-sweep) | 9 | 0 |
| cond(WTT): matern32 / matern52 / rbf | 1729.7 / 442.5 / 486.1 | 4358.3 / 1421.0 / 2857.7 |

*Per-grid capture columns apply the same subset convention as the pooled metric: rows with
DST2 reduction > 0.5% within the grid -- 60 of 60 at 64x64 and 22 of 30 at 128x128, summing
to the 82 of 90 pooled capture subset.*

The support set S covers ALL 4096 cells at 64x64 (s = 4096; the mirror coupling spans the entire finite grid) and ~99.5% of cells at 128x128 (median s = 16308.5); the w-clamped band T_w (size |T_w| ~ 945 cells at 64x64 w=8) is far SMALLER than the measured support (coverage 4.334 / 6.838 -- full-support-sized, not a truncation remnant of the band). The support distance exceeds the clamp on both claim grids (31.0 > 8; 63.0 > 16): fork A fires -> NOT-validated-guard (s1_verdict_clause: "fork A: measured support distance w_s exceeds the clamp min(H,W)/8 on a 2D claim grid; w_s/s/coverage reported per grid"). Fork B was NOT reached (null in the artifact).

Fork-consequence one-liner (the pre-committed reading of the outcome): S1' = NOT-validated-guard: the exact center solve works in-band but the DST2-embedding boundary effect has full-support extent (w_s 31/63 > clamps 8/16; s = all cells at 64x64), so no w-clamp regime can contain it -- fork A fires, fork B not reached. Importantly, the outcome is a NEGATIVE UNDER EITHER BRANCH: had the support distance stayed within the clamp, fork B would independently have triggered REFUTED-residual, because the pooled median relative system residual is 516.3 >> the pinned 1e-6 gate.

Pooled 2D claim block (n = 90; independently recomputed from the rows: median(100*(1 - gap_f1/gap_bccb)) = 46.66015125209701; median(res_f1) = 516.3154932313778; median(gap_bccb) = 2.79907229881912; median DST2 reduction = 58.46150923131715).

Capture formula (stated once here): per-row capture = (F1 gap reduction pct) / (DST2 gap reduction pct); the reported metric is the MEDIAN over the 82 rows with DST2 reduction > 0.5% (82 of 90; the threshold unit follows the verify_iter4.py percent convention, i.e. DST2 reduction strictly above 0.5 percentage points). The pooled value is capture = 0.7531362234848058, hence 0.7531 (75.3%) is NOT 46.66/58.46 = 0.798 (the ratio of the pooled medians would be a different quantity).

| Pooled clause (2D claim pool, n=90) | Value | Pre-registered bar | Clause reading |
|---|---|---|---|
| median gap reduction vs BCCB | 46.66% | >= 50% | FAILS (by 3.34 pp) |
| median relative system residual | 516.3 | <= 1e-6 | FAILS (>> bar; fork B would fire) |
| w_guard (w <= min(H,W)/8, structural clamp) | True | required | HOLDS BY CONSTRUCTION (clamp); the fork-A failure is the SUPPORT distance w_s, not w_design |
| capture ratio vs DST2 comparator | 0.7531 = 75.3% | >= 50% (capture consequence) | HOLDS (75.3% >= 50%) |
| median DST2 comparator reduction | 58.46% | comparator only | DST2 is AHEAD of F1 (58.46% > 46.66%) |
| median gap BCCB (wrap baseline) | 2.799 | - | baseline whose gap is reduced |

Unit-ambiguity note (required, per the analysis-gate critique): the artifact field name median_capture_vs_dst2_pct stores the RATIO (0.7531, i.e. 75.3%) -- not a literal percent string of 0.753%. The ratio reading is the one consistent with the measured reductions and with the iteration-3 analysis convention (capture 0.7467 / 0.7284 [INVALIDATED HISTORY - honest-negative provenance]); the verdict does not depend on this clause (fork A preempts it). Whenever this paper reports capture it uses the explicit "ratio = percent" reading.

Per-clause attribution (pre-registered): the pool-semantics pin (M5) applies the gates to the 2D claim pool; the fail-fast rows (9, all at 64x64: matern32 seeds 7,9,13,14,18; matern52 seeds 13,14,18; rbf seed 9) are recorded and do not enter the verdict; per-grid n_neg and cond(WTT) are recorded (see below). The 24^3 rows are per-domain only (Section 3.4).

n_neg (negative eigenvalues of the embedded spectrum, per grid/kernel; floored at 0 with ridge 1e-3):

| Grid | matern32 | matern52 | rbf |
|---|---|---|---|
| 64x64 | 0 | 0 | 11 |
| 128x128 | 0 | 0 | 3 |
| 320x320 | 0 | 0 | 2 |
| 24^3 | 289 | 4578 | 7662 |
| 48^3 | 0 | 1468 | 4222 |

### 3.2 S2' (F2 contingent): REFUTED -- 0.1353x median speedup vs PCG

Pool: 147 rows (120 grf-2d + 27 grf-3d). kaplan-sst-v2 rows executed: 0; mnist rows executed: 0 -- both declared row classes were truncated last under the arm clock and disclosed (pooled.n_kaplan_rows 0, pooled.n_mnist_rows 0). Summary (all recomputed from the 147 rows; results/iter4/A2-F2.json pooled block):

| Quantity | Pooled (n=147) | synthetic-2d (n=120) | synthetic-3d (n=27) |
|---|---|---|---|
| median speedup vs PCG | 0.1353x | 0.1297x | 0.3739x |
| ssam converged fraction | 23.8% | 29.2% | 0.0% |
| pcg converged fraction | 100% | 100% | 100% |
| ssam median iterations | 500 (ceiling) | 500 | 500 |
| pcg median iterations | 290 | 283 | 481 |
| ssam median relative KKT residual | 1.385e-4 | 4.78e-5 | 0.0586 |
| pcg median relative KKT residual | 9.01e-7 | 9.18e-7 | 8.37e-7 |

Verdict: S2' = REFUTED (median speedup 0.1353x < 1.5x REFUTED bar; s2_verdict_clause "median speedup < 1.5x"). Supporting evidence:

- k-sweep on a probe row (64x64 matern32 random_0.3 seed 0), k in {64,128,256}: ssam relative residuals 1.385e-4 / 1.427e-4 / 1.427e-4 -- FLAT at ~1.4e-4: increasing the sketch size does not move the plateau.
- Matched-1e-8 subset (4 rows): never converges at the 500-iteration ceiling; ssam relative residuals 3.13e-4, 2.74e-4, 1.39e-4, 1.10e-4 (1.1e-4..3.1e-4), conv false on all matched rows while PCG converges at 6.9e-9..9.1e-9 (genuine min..max over the 4 matched rows).
- Variant data (attempted-if-budget, single-row, NOT a claim): the spectral DST2-block Anderson variant converged on the probe row (384 iterations, rel 9.82e-7) vs Nystrom-k64 same-row 500 iterations / not converged / 1.385e-4 -- one honest variant observation.
- Deflation: not-completed (budget; attempted-if-budget clause disclosed).
- kaplan RMSE parity: NOT re-measured in iteration-4 (0 kaplan rows); the iteration-3 parity figures (0.3504163 / 0.3504185) are INVALIDATED HISTORY and are not used.

### 3.3 Benchmark (A3): REFUTED -- dense KRR uniquely wins grf-2d; KISS wins 0 domains

Executed scope: 24 grf-2d rows ONLY (see Section 6 for the coverage-truncation itemization). Per-domain medians (grf-2d, n=24; recomputed from rows):

| Method | median RMSE (valid cells) | median wall (s) |
|---|---|---|
| f1_exact (UNMASKED; see disclosure) | 184.6969 | 2.69 |
| standard PCG | 0.06134768 | 1.64 |
| dense KRR | 0.06134764 | 0.68 |
| KISS-GP | 1.6073 | 0.32 |
| RFF | 0.2020 | 0.10 |

Disclosure (required): f1_exact ran as the boundary solver on the FREE operator -- an UNMASKED full-field solve, disclosed as NOT a masked-train method (runner disclosure; now also recorded in the artifact itself, A3 f1_exact_disclosure); its RMSE is not comparable to the masked-train methods and it is reported for completeness of the method set only.

Winner logic: best RMSE = dense (0.0613476449); 0.5% tieband tied = {dense, pcg} (relative delta 5.4e-7 -- the identical masked-Gram system both solvers solve); cost gate (median wall <= best wall + 0.1 s) -> dense unique winner (0.68 s vs PCG 1.64 s); LITERAL no-tieband sensitivity row (0.0% band) -> strict winner dense (dense_wins_strict 1, kiss_wins_strict 0). kiss_wins = 0, dense_wins = 1 -> benchmark_verdict REFUTED ("REFUTED iff KISS-GP wins >= 2 of 4 domains OR dense KRR wins >= 1 of 4 domains in RMSE at equal-or-lower cost envelope; ties reported; no cherry-picked exclusions"). The verdict holds under both the tieband+cost reading and the strict reading (no band-dependent flip).

### 3.4 Envelope, budget, and honesty (cross-arm)

| Arm | rows | elapsed (s) | cap (min) | status |
|---|---|---|---|---|
| A1-F1 | 110 | 1247.0 | 20 | exceeded by 47 s (flagged budget_exceeded) |
| A2-F2 | 147 | 1099.6 | 18 | exceeded by 19.6 s (flagged budget_exceeded) |
| A3-multidomain | 24 | 224.3 | 7 | re-capped under the 45-min hard stop (budget_adjustment_note: executed budget min(7, total_left - 140 s)/60 min; stop_note "grf-3d truncated (arm clock)") |
| A4-tooling | - | 0.1 | 2 | within cap |

- Total wall clock 2571.3 s = 42.9 min <= the 45-min hard stop. Per-arm sum 2571.0 s vs measured total 2571.3 s is a 0.1 s-rounding artifact, not a timing error (documented rounding convention).
- Peak RSS 1.048 GB (measured) < the ~2 GB cgroup cap (the project envelope claim <= 7 GB is superseded by the container reality; all sizing was done under ~2 GB).
- 3D rows: 24^3 rows executed = 9 rows, all matern32 seeds 0-8 (stop_note "3d rows truncated (arm clock)"); the pre-committed budgeted subset was seeds 0-2 PER KERNEL (9 rows); the executed subset is matern32 0-8 -- truncation disclosure: the arm clock stopped the 3D block mid-kernel; matern52/rbf 24^3 rows were NOT executed. Every 24^3 row carries floor_caveat true, n_neg 289 (matern32), and the per-row MEASURED a-posteriori floor error 1.087 (no theorem-backed floor bound claimed; Graham 70 a-posteriori convention). 24^3 rows NEVER enter pooled medians (M5 pin). Executed 24^3 references = container-forced PCG tol 1e-8 (relative residuals 7.29e-9..9.98e-9). Per-domain 3D S1' clauses (informational only): F1 residual min..max 2819.1..9871.6, gap_F1 min..max 2.23..4.87 vs BCCB (both ranges are the genuine min..max over the 9 executed 24^3 rows), support s = 13824 (all cells) and w_s = 11 > clamp 3 (per-domain observation; fork A is defined on the 2D claim grids only).
- Execution integrity: crash-rescue checkpoint mechanism used during the run (resume path reads rescue artifacts; final artifact records resumed_from_crash null); two real-run-only bugs fixed during the run with claims deterministically recomputed (traceability limitation, Section 6); every truncation disclosed (budget_exceeded / stop_note / not-completed wording).
- A4 tooling: pass. grf_boundary selfcheck 0.0456 s; mixed-boundary 36x72 sample 0.0044 s; F1 16x16 path sanity: matvec exactness error 2.34e-16, full-tail solve gap 0.372507308964934, residual 0.04143830659996375, nb 705 (interpretation in Section 4.2).

## 4 Mechanism findings

### 4.1 The plateau is far-tail support truncation, and it is UNCHANGED by the exact center solve

The headline mechanism finding of the iteration-4 boundary arm is a falsification. The iteration-3 explanation of the S1 residual plateau attributed it to the RANK-LIMITED truncation of the approximate Woodbury correction (rank budget |T| median 1233, O(w(H+W)); corrected-residual plateau 532.2245 pooled / 546.2021 at 64x64 [INVALIDATED HISTORY]). Iteration-4 removes that mechanism: the F1 center solve is an EXACT dense solve of the Woodbury-center system with NO rank truncation; for the 81 non-fail-fast rows the sweep residuals decay monotonically over w in {1,2,3,4} and settle within the clamp to the ~500 plateau (14 of the 81 rows show a small increase at the w_design step, max ~0.13%), while the 9 fail-fast rows (all at 64x64: matern32 seeds 7,9,13,14,18; matern52 seeds 13,14,18; rbf seed 9) are non-monotone and are disclosed (the iteration-3 rank-limited plateau class is gone [INVALIDATED-HISTORY motivation only]). The fail-fast rows remain INSIDE the 90-row claim-pool medians: fail-fast adds no verdict clause and does not remove rows from the pool. Yet the pooled residual plateau is UNCHANGED: the iteration-4 pooled median relative system residual is 516.3 (516.3154932313778) vs the iteration-3 pooled median 532.2 (532.2245) [INVALIDATED HISTORY], and at 64x64 the iteration-4 median is 546.205 (546.2050329278138) vs the iteration-3 plateau 546.2021 [INVALIDATED HISTORY]. The exact comparisons used for this claim are EXACTLY: pooled 516.3 (iter-4) vs 532.2 (iter-3 [INVALIDATED HISTORY]), and per-grid 64x64 546.205 (iter-4) vs 546.2021 (iter-3 [INVALIDATED HISTORY]). The iteration-3 rank-limited-truncation explanation is therefore FALSIFIED.

The surviving explanation is far-tail SUPPORT truncation: the mirror/boundary coupling H_r of the whole-sample-symmetric DST2 embedding of the FREE operator is FULL-SUPPORT-sized, not band-sized. The measured support set S covers all 4096 cells at 64x64 and ~99.5% of cells at 128x128 (s median 16308.5) at the 1e-6-scaled threshold; support distance w_s = 31/63 far exceeds any clamp the F1 regime allows (8/16). The w-clamp family T_w is therefore structurally INCAPABLE of containing the boundary effect at claim scale: no w <= min(H,W)/8 band can cover a full-support coupling. The F1 w-clamp hypothesis is CLOSED by fork A for this embedding class, and the exact full-support center is cost-infeasible at claim scale: nb_tail = 12033 (64x64) / 48641 (128x128); dense center memory estimates ~1.16 GB (64x64) / ~18.93 GB (128x128) exceed the ~2 GB cgroup; center solve O(nb^3). The executed nearest-tail full-support diagnostic rows were capped at nb = 4000 with honest not-completed wording (full_support_completed false; nb_cap 4000; nb_tail recorded).

The honest boundary-class positive residue within this negative is the DST2 comparator itself: the naive DST2 spectral solve (no band correction) reaches a pooled median gap reduction of 58.46% -- AHEAD of F1's 46.66% on the same 90-row 2D claim pool -- and F1's capture consequence HOLDS: the median per-row capture ratio is 0.7531 (75.3%) >= 50% (per-row capture defined in Section 3.1; the ratio is a median of per-row ratios -- NOT a share of the 58.46% pooled DST2 reduction and NOT the quotient of pooled medians 46.66/58.46 = 0.798).

### 4.2 The exactness tiering (three-tier statement, per the analysis-gate critique)

The small-grid full-tail exactness references give a MIXED picture that must be quoted with interpretation (results/iter4/A1-F1.json kind small-grid-exactness-reference rows at 32x32; A4-tooling f1_path_sanity_16x16):

- rbf 32x32 full-tail exact solve reaches relative residual 1.6513127301794495e-12 (1.65e-12, precision-level);
- matern32 32x32 full-tail exact solve reaches 9.190727049870518e-05 (9.19e-5) -- ~92x ABOVE the 1e-6 gate (conditioning-plausible, cond(WTT) = 172878 at 32x32 matern32, but UNRECONCILED);
- A4 16x16 f1_path_sanity (full_tail_solve_gap 0.372507308964934, res 0.04143830659996375, nb 705) is the SMALLEST yet WORST exactness of the three -- a 16x16 grid (rho/grid ratio largest) leaves a 0.0414 relative residual despite an exactly-correct matvec (2.34e-16).

Interpretation: the exact full-tail formulation is correct at the matvec level on all tested grids, but its SOLVE-level exactness is kernel-dependent and not a uniform precision tier: the smallest grid (16x16) is the worst (res 0.0414) and 32x32 improves (matern32 9.19e-5, rbf 1.65e-12); claim-scale comparisons are confounded by the nb=4000 cap. The supported conclusion is therefore limited and precise: "truncation is the dominant error at claim scale; the full-support center is cost-infeasible" -- NOT "not model error". Solve-level residual behavior beyond the claim-scale truncation is conditioning-plausible but unreconciled on the small grids (matern32 32x32; 16x16 sanity), and the writeup makes no claim that the residual plateau is free of conditioning contributions.

### 4.3 The Nystrom-preconditioner complement stall

The F2 negative has a clean mechanism reading: the randomized-Nystrom preconditioner of the masked Gram removes a low-rank dominant part of the spectrum, but the Anderson-plus-preconditioned iteration then stalls on the PRECONDITIONER COMPLEMENT -- a slowly-converging remainder of the spectrum that increasing sketch sizes k in {64,128,256} do not move (probe-row plateaus 1.385e-4 / 1.427e-4 / 1.427e-4, FLAT; matched-1e-8 subset 1.1e-4..3.1e-4 at the 500-iteration ceiling, never converging). PCG converges 100% of rows at median 290 iterations vs 23.8% / 500 for ssam-nystrom. The single-row spectral DST2-block variant (384 iterations, 9.82e-7 on the probe row) indicates the stall is specific to the Nystrom complement rather than to Anderson mixing per se -- but it is one honest variant observation (attempted-if-budget), not a claim.

## 5 Discussion

### 5.1 The pre-registered fallback F3 is now the deliverable

Iteration-4 is a measured NEGATIVE for both pre-registered strategy families: F1 NOT-validated-guard (fork A), F2 REFUTED (< 1.5x), benchmark REFUTED (dense KRR wins grf-2d under both tieband readings). The declared F3 fallback (proposal-iter4-v4 fallback_strategy: "negative-result + tooling contribution"; acceptance = completeness of the honest-negative reporting + tooling deliverables passing self-checks, with no positive win gate) is therefore the honest default deliverable of the cycle. The reviewers' "defensible but below qualifying-positive bar" note (Significance 3) applies: the F1 mechanism spec was correctly falsified by pre-committed measurements -- the support measurement and the precedence fork did their designed job -- and the tooling (boundary-controlled GRF generator, F1 spectral embedding/exact-solve tooling) passes its self-checks (A4; G8 CLOSED at the tooling level, per the corpus review).

### 5.2 G5 remains open; boundary-value formulations are the honest next step

G5 (an exact free-boundary fast grid kernel solve) REMAINS OPEN: the corpus supplies exact circulant-embedding simulation, exact Toeplitz solves at O(N^2) (Trench 66, Gohberg-Semencul 67), a stabilized superfast Toeplitz solve at O(n log^3 n) (Stewart 73), and HSS structured directs (Ambikasaran 54), but no exact O(N log N) free-boundary grid solve (review.md G5 restatement). The iteration-4 measurement sharpens why: within the whole-sample-symmetric (DST2-class) embedding of the FREE operator, the boundary coupling is full-support-sized, so correcting the embedding while keeping a banded regime cannot work (fork A). The honest alternative is a boundary-MODEL change rather than an embedding correction: explicit Dirichlet-zero / Neumann-zero / finite-domain boundary conditioning is already tooled in scripts/grf_boundary.py (G8), and the correct spectral object for symmetric-boundary operators is the symmetric-boundary operator itself, diagonalized by the DCT/DST class (Strang 74: DCT/DST as eigenbasis of symmetric-boundary operators), not a corrected embedding of the free operator. This is stated as a new hypothesis for the next cycle, not a guaranteed fix; no optimistic claim is made (ranked direction 2 of the analysis).

### 5.3 Reformulations are weakly motivated by the benchmark

KISS-GP-style inducing points (Wilson-Nickisch 6) and nested/domain-decomposition boundary corrections (HSS 54; Barrowes 72 3D multilevel block-Toeplitz matvec at O(N log N)) remain the corpus-anchored reformulation candidates, with an HONEST CAVEAT that the iteration-4 benchmark just REFUTED the inducing-points-as-winner motivation on the tested regime: KISS-GP's median grf-2d RMSE is 1.61 vs dense KRR's 0.0613 (RFF 0.20; PCG/dense tied on the identical masked system). An inducing-points-as-benchmark-winner claim would therefore need a fresh pre-registration, and no domain-decomposition entry exists in the corpus (that anchor is an extension, stated as such). G6 (masked fast solves) remains open for a masked fast solve at a measured >= 1.5-3x speedup with equivalent residual tolerance (iteration-3: REFUTED-verified at 0.2374x-0.1624x [INVALIDATED HISTORY]).

### 5.4 What NOT to continue (per the analysis prescription)

- No re-run of the F1 w-clamp inside the same DST2-free-operator embedding: fork A closes it (measured w_s 31/63 far exceeds any clamp the regime allows).
- No bandwidth-retuning or threshold-relaxation variants: the support is full-width by construction of the embedding at the 1e-6-scaled threshold, not by the kernel tail alone.
- No F2-family claim from the iteration-4 evidence: the pre-registered Nystrom-preconditioned Anderson is REFUTED; the spectral DST2-block variant converged on one probe row and deflation/kaplan parity were not-completed; any F2 continuation needs a fresh pre-registered arm with budget for deflation and kaplan parity before a claim is possible.
- No 3D pooled claims: 24^3 rows stay per-domain under the floor caveat on every path (M5 pin).

## 6 Limitations

- 3D floor caveat. The 3D whole-sample-symmetric embedding is empirically non-PSD on the tested kernels/grids (n_neg 24^3 {289, 4578, 7662}; 48^3 {0, 1468, 4222}); floored solve != free solve; floor error is reported per-row as a MEASURED a-posteriori quantity (1.087 at 24^3 matern32; Graham 70 a-posteriori convention) with NO theorem-backed floor bound (no DCT/DST-class PSD floor theorem in the corpus; Nexus note). No 3D exactness claim is made. 24^3 rows are per-domain only and NEVER pooled.
- 3D row truncation. The executed 24^3 rows are matern32 seeds 0-8 (9 rows), NOT the pre-committed seeds 0-2 PER KERNEL (arm-clock truncation: the A1 stop_note records "3d rows truncated (arm clock)"); matern52/rbf 24^3 rows were not executed; the 24^3 reference is the container-forced PCG-1e-8 deviation (dense Cholesky not pre-registered, ~3.1 GB estimate > ~2 GB cgroup).
- A3 coverage itemization (honest negatives, itemized). A3 was truncated to 24 grf-2d rows ONLY under the 45-min hard stop (clock 224.3 s; budget_adjustment_note min(7, total_left - 140 s)/60 min; stop_note "grf-3d truncated (arm clock)"). Wording conflict FLAGGED: the artifact's coverage_delta_registration says kaplan-sst-v2 was "executed subset (budget)" and grf-3d was "executed per budget", but ZERO kaplan-sst-v2 rows and ZERO grf-3d rows exist in results/iter4/A3-multidomain.json (rows n = 24, all grf-2d) -- the registration wording overstates the executed scope and is corrected here. grf-2d internal shortfall: declared 60 rows (matern32/rbf x masks 0.1/0.3/0.5 x seeds 0-9); executed 24 rows (matern32 ONLY, masks 0.1/0.3 seeds 0-9, mask 0.5 seeds 0-3). mnist-784 was not executed. These are plan-vs-executed deltas itemized as honest negatives, never qualifying claims.
- A2 truncations. kaplan rows = 0 (declared row class truncated last under the arm clock, disclosed; parity clause NOT re-measured; iteration-3 parity figures INVALIDATED HISTORY); deflation not-completed; matched-1e-8 subset = 4 rows; 3D rbf mask-completion truncated to 3 rows (27 of 36 budgeted 3D rows executed).
- Budget overruns (flagged, disclosed). A1 exceeded its 20-min cap by 47 s (1247.0 s); A2 exceeded its 18-min cap by 19.6 s (1099.6 s). Both carry budget_exceeded true per the pre-registered disclosure protocol. Total 2571.3 s = 42.9 min stayed within the 45-min hard stop. Per-arm clocks are 0.1 s-rounded (sum 2571.0 vs total 2571.3 -- rounding artifact, not a timing error).
- Bug-fix traceability (analysis-gate item 1). Two real-run-only bugs were fixed during the run -- the diag-plan tuple unpacking and the idx_sets_nd dmin tail-indexing -- and all claims were deterministically recomputed after the fixes, with a crash-rescue/resume mechanism added (final artifact records resumed_from_crash null). The disclosure of these fixes lives in the analysis artifact; the runner at commit 5c8c996 contains NO in-repo bug documentation, NO stale-value inventory, and NO recompute-scope record. No row-level traceability or state records beyond the final artifacts were retained. The writeup makes no claim that the fixes are documented in the runner itself.
- Capture unit ambiguity (analysis-gate item 2). Cross-reference: the unit-ambiguity note in Section 3.1 is the single full statement (the artifact field median_capture_vs_dst2_pct stores the RATIO 0.7531 = 75.3%, never a literal 0.753% reading); this limitation bullet only records the consequence: the writeup reports capture exclusively in that explicit reading, and the verdict does not depend on the capture clause (fork A preempts).
- f1_exact unmasked and post-plan diagnostics (analysis-gate item 5). f1_exact is an UNMASKED full-field solve -- NOT a masked-train method; its RMSE (184.7) is incomparable to the masked-train methods and is disclosed in the artifact itself as well as here. The two 32x32 small-grid exactness rows are POST-PLAN diagnostics (not part of the approved plan's 9-row full-support diagnostic composition); they are reported with that provenance, and the exactness tiering they reveal is mixed (Section 4.2) -- no claim of uniform solve-level exactness is made. The A4 16x16 f1_path_sanity is likewise an additional in-run tooling sanity row.
- Support-threshold and band conventions. The support set uses the 1e-6-scaled threshold (|H_r| > 1e-6 * max|H_r|); T_w is the Chebyshev-distance w-band; support quantities are per-diagnostic-row measurements reported as medians over rows. Residual conventions for the comparators (DST2/DCT1/BCCB gaps) follow the iteration-2/3 measured gap norm (gap norm ||f_approx - f_free|| / ||f_free||, pinned in this cycle's methods).
- Kaplan real-data coverage. Zero kaplan rows executed in A2 and A3 (truncated); the future-blind lock itself (seed 7; train idx 0..1919 / test idx 1920..2003 / idx 2004 excluded) was not violated, and the 44-field declared slice was recorded (kaplan_split.fields_executed), but all real-data RATE/parity measurements of iteration-4 are absent by truncation.

## 7 Future work and conclusion

Future work, in ranked order (analysis strategy_implications):

1. F3 fallback deliverable: complete the negative-result + tooling study under the pre-registered label table (this paper), with the tooling deliverables (grf_boundary.py; fft_krr_embed.py dst2_exact_band_nd / full_support_diag_nd / ssam_nystrom_nd) passing their self-checks (A4; G8 CLOSED at the tooling level).
2. Boundary-model change: explicit boundary-value / finite-domain formulations (Dirichlet-zero / Neumann-zero already tooled) treating the symmetric-boundary operator itself as the spectral object (Strang 74), with the 3D WSS-embedding PSD question (24^3 n_neg 289-7662) kept as an honest secondary open problem (Nexus note; Graham 70 a-posteriori floor-error conventions). New hypothesis, pre-registered before execution, no guaranteed-fix framing.
3. Masked-arm continuation only via a fresh pre-registration: budgeted deflation and kaplan parity re-measurement, or a spectral DST2-block preconditioner variant (single-row evidence: 384 iterations / 9.82e-7 vs Nystrom stall) -- with the honest caveat that G6 remains open for a masked fast solve at >= 1.5-3x with equivalent tolerance.
4. Reformulations (inducing points / domain decomposition) only with fresh pre-registration and the KISS-loses caveat from this benchmark stated (KISS 1.61 vs dense 0.0613 on grf-2d).

Conclusion. Iteration-4 is a complete, pre-registered honest NEGATIVE for both strategy families: F1 NOT-validated-guard because the DST2-embedding boundary coupling is full-support-sized (fork A; fork B would independently REFUTED-residual), F2 REFUTED because the Nystrom-preconditioned Anderson stalls on the preconditioner complement, and the benchmark REFUTED with dense KRR the unique grf-2d winner under both tieband readings. The mechanism finding -- plateau UNCHANGED (516.3 vs 532.2 pooled; 546.205 vs 546.2021 at 64x64, iteration-3 values [INVALIDATED HISTORY]) despite the removal of rank-limited truncation -- falsifies the iteration-3 explanation and relocates the barrier to far-tail support truncation of a full-support coupling that is cost-infeasible to solve exactly at claim scale. Within the tested regime, the DST2 comparator (58.46%) remains the empirically best classical boundary-aware class. Per the pre-registered fallback F3, the deliverable is the negative-result + tooling study itself, with no positive win gate claimed.

## References

Numbered to the corpus entries of docs/literature-review/review.md (74 entries); all bibliographic records web-verified in-session per the review's provenance flags.

1. (corpus 45) Martucci, S. A. (1994). Symmetric convolution and the discrete sine and cosine transforms. IEEE Transactions on Signal Processing 42(5):1038-1051. -- DCT/DST diagonalize symmetric-boundary convolution; the DST2 whole-sample-symmetric embedding class used by F1 and the comparator.
2. (corpus 66) Trench, W. F. (1964). An algorithm for the inversion of finite Toeplitz matrices. Journal of the Society for Industrial and Applied Mathematics 12(3):515-522. -- Exact O(N^2) Toeplitz inversion; the exact-solve class F1 was designed to use (attempted-if-budget speed path).
3. (corpus 67) Gohberg, I. C. and Semencul, A. A. (1972). On the inversion of finite Toeplitz matrices and their continuous analogs (in Russian). Matematicheskie Issledovaniya 7(2):201-223. -- Gohberg-Semencul displacement formula; basis of exact Toeplitz solves alongside Trench.
4. (corpus 73) Stewart, M. (2003). A superfast Toeplitz solver with improved numerical stability. SIAM Journal on Matrix Analysis and Applications 25(3):669-693. -- Stabilized superfast Toeplitz solve, O(n log^3 n); the exact-solve anchor between O(N^2) formulas and the rank-limited Woodbury line.
5. (corpus 54) Ambikasaran, S., Foreman-Mackey, D., Greengard, L., Hogg, D. W., and O'Neil, M. (2016). Fast direct methods for Gaussian processes. IEEE Transactions on Pattern Analysis and Machine Intelligence 38(2):252-265. -- HSS structured direct solves; pre-committed re-seeding candidate for the F1 center (attempted-if-budget).
6. (corpus 70) Graham, I. G., Kuo, F. Y., Nuyens, D., Scheichl, R., and Sloan, I. H. (2018). Analysis of circulant embedding methods for sampling stationary random fields. SIAM Journal on Numerical Analysis 56(3):1871-1895. -- General-dimension circulant-embedding PSD conditions and a-posteriori floor-error control; cited SOFTENED: CIRCULANT-class floor-error conventions only, no DCT/DST-class PSD floor theorem claimed.
7. (corpus 72) Barrowes, B. E., Teixeira, F. L., and Kong, J. A. (2001). Fast algorithm for matrix-vector multiply of asymmetric multilevel block-Toeplitz matrices in 3-D scattering. Microwave and Optical Technology Letters 31(1):28-32. -- 3D multilevel block-Toeplitz matvec at O(N log N); the 3D matvec-cost anchor (the 3D gap is in the SOLVE, not the matvec).
8. (corpus 74) Strang, G. (1999). The discrete cosine transform. SIAM Review 41(1):135-147. -- DCT/DST as eigenbasis of symmetric-boundary operators; the boundary-model-change direction's spectral anchor.
9. (corpus 71) Frangella, Z., Tropp, J. A., and Udell, M. (2023). Randomized Nystrom preconditioning. SIAM Journal on Matrix Analysis and Applications 44(2):553-594 (arXiv 2110.02820). -- Randomized low-rank Nystrom preconditioning of SPD regularized systems; the F2 preconditioner class whose complement-stall was measured.
10. (corpus 6) Wilson, A. G. and Nickisch, H. (2015). Kernel interpolation for scalable structured Gaussian processes (KISS-GP). ICML 2015. -- Inducing-point structured GP interpolation; the benchmark's KISS-GP baseline (wins 0 domains in iteration-4).

## Appendix A: honest-framing checklist (self-contained)

- T1b canonical lock. The only permitted T1b citation is results/iter2/T1b-CG-masked-train.json (CANONICAL): masked-train PCG rate means 245.125 / 276.125 / 280.875 iterations at tol 1e-8 (masking rates 50%/30%/10%); per-field iteration span 233-291; final per-field relative residuals 4.6935e-09..9.8070e-09 (4.69e-9..9.81e-9); RMSE means 0.529323 / 0.531244 / 0.541160 (0.529-0.541); wall_clock_s 4.63; peak_rss_gb 0.907. These were re-read from the canonical artifact in the analysis and are re-cited here from it only.
- SUPERSEDED markers never cited. EXECUTION_NOTES.md and results/analysis.json carry explicit SUPERSEDED markers for the pre-fix T1b iteration-count / RMSE figures; those figures NEVER appear in this paper -- not even inside a never-cited statement (byte-level convention honored in the analysis; the same convention is honored here: zero hits of the pre-fix literals).
- Iteration-3 INVALIDATED HISTORY statuses (honest negatives only, never qualifying): G5 REMAINS OPEN -- iteration-3 S1 median gap reduction 47.3574% < 50% bar, pooled residual 532.2245, per-grid plateaus 546.2021 / 415.7885, rank budget median |T| 1233, DST2 61.62% vs DCT1 -1872.63%, capture 0.7467 / 0.7284 [INVALIDATED HISTORY]; G6 REFUTED-verified -- iteration-3 median speedups 0.2374x (synthetic) / 0.1560x (kaplan) / 0.1624x (pool), iterations 278.5 vs 192.0, convergence 77.7% vs 100% [INVALIDATED HISTORY]; G7 not-refuted -- iteration-3 kiss_wins 0 / dense_wins 0 with the disclosed tieband sensitivity [INVALIDATED HISTORY]; G8 CLOSED at the tooling level -- iteration-3 A6 selfcheck 0.0453 s [INVALIDATED-HISTORY provenance template; iteration-4 A4 selfcheck 0.0456 s is the current measurement].
- No new-mathematics claims. Every component is cited to the corpus (entries above plus the embedding/preconditioner lineage): the claim is the grid-KRR-targeted integration plus its pre-registered measurement; "exact" appears ONLY as "exact band/center solves" -- never as an exactness claim for the overall free-boundary solve, whose residual is measured and gated at <= 1e-6.
- No SOTA-ENSO claim. No real-SST skill / ENSO-forecast-skill claim appears anywhere; every empirical number on real data is a reconstruction/efficiency measurement, not a forecast-skill claim (and zero real-data rows executed this iteration by truncation).
- No O(N^2)-free claim outside the stationary BCCB/BTTB class. All O(N log N)/O(N)-memory scoping is to the stationary BCCB/BTTB class on regular grids; the F1 center is O(nb^3) time / O(N + nb^2) memory with nb support-rank-measured (12033/48641 at full tail) -- dense, disclosed, never hidden.
- 3D WSS-embedding PSD caveat. 3D symmetric embeddings are empirically non-PSD on the tested kernels/grids; floored solve != free solve; floor error is a per-row MEASURED a-posteriori quantity (B5, Graham 70 convention); no theorem-backed floor bound; no 3D exactness claim.
- 24^3 never pooled. The 2D claim pool pin (M5) is honored on every path; the REFUTED/guard gates are 2D-claim-pool clauses only.
- 0.1 s rounding disclosure honored. Per-arm sum 2571.0 s vs measured total 2571.3 s is a rounding artifact (iteration-3 template: 2296.4 vs 2296.5 s [INVALIDATED-HISTORY disclosure template]).
- Container cgroup disclosure. Actual container cgroup ~2 GB; peak RSS 1.048 GB measured vs that cap; the project envelope claim <= 7 GB is superseded by the container reality; 24^3 dense Cholesky NOT pre-registered (est. ~3.1 GB > cgroup) and NOT re-attempted; executed 24^3 reference = container-forced PCG tol 1e-8, disclosed.
- Exact-value traceability. Every median in the tables above was re-derived from the row-level artifacts by scripts/verify_iter4.py (248 checks / 0 failures / 2 honest warnings -- the two flagged budget exceedances) and by the gated analysis (verify_analyze_iter4.py, 120 checks), and re-verified in this writeup pass: pooled 2D claim medians 46.66015125209701 (gap pct) / 516.3154932313778 (residual) / 0.7531362234848058 (capture ratio) / 58.46150923131715 (DST2 pct) / 2.79907229881912 (BCCB gap); per-grid 64x64 47.874221947416 / 546.2050329278138 / 0.7374352825724045 and 128x128 45.808031510740975 / 462.25912378446515 / 0.8812013692551097 (gap / residual / capture); A2 pooled median speedup 0.1353117243583585, ssam convergence 0.23809523809523808, median iterations 500/290, median residuals 1.385462487279592e-04 / 9.012804174494269e-07; A3 grf-2d method medians f1_exact 184.6968818113341 / pcg 0.061347678258299274 / dense 0.061347644923299575 / kiss 1.6073410798202419 / rff 0.20202991779793944; envelope total 2571.3 s, peak RSS 1.0479583740234375 GB.