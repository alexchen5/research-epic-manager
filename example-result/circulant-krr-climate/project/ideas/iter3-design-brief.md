# Iteration-3 design brief: novel strategies for boundary + masked grid-KRR

Status: manager draft (ideation input for proposal-it4-*). Every number below
is a pre-registered target; the executed artifacts (results/iter3/) are the
source of truth, not this brief.

## 1. Problem statement

Grid-based kernel ridge regression on HxW (or HxWxD) regular grids using
block-circulant-with-circulant-blocks (BCCB) Gram structure solves
(K + lambda I) alpha = y in O(N log N) via 2D/3D-FFT. Two bottlenecks (from
iteration-2, human review):

1. **Torus boundary gap**: BCCB wrapping imposes periodic boundary
   conditions. On free-boundary kernels (Matérn-3/2, Matérn-5/2, RBF) the
   wrapped solve has ~0.95 (Matérn-3/2) / ~0.12 (RBF) relative error against
   the true free-boundary solution on real fields (P0-pilot-gate-real.json).
2. **Masked-inversion degradation**: under missing-data masks the solve is
   (P_m K P_m^T + lambda I)^{-1}; the BCCB structure is broken and the PCG
   fallback converges slowly (245-281 iterations, RMSE 0.53-0.54 on masked
   reconstruction) (T1b-CG-masked-train.json, iteration-2).

Constraint: no O(N^2) memory, no O(N^3) compute; CPU-only (12 cores / 7 GB /
<= 90-min envelope per run).

## 2. Strategy S1: Reflective Embedding + Adaptive Boundary-Banded Low-Rank Correction (RE-ABLRC)

**Goal**: free-boundary solves at O(N log N) with the modeling gap reduced by
>= 50% vs standard BCCB wrapping.

**Idea**: Embed the free-boundary kernel Gram K (BTTB for stationary kernels
on the grid) into a larger circulant C of size (2H-1 x 2W-1) [resp.
(2H-1)(2W-1)(2D-1) in 3D] via **whole-sample symmetric extension** (DCT-I
class, Martucci entry 45) of the kernel's first column — NOT half-sample
reflective padding (which yields 2H per axis). The embedded circulant matches
K on the interior block while the extra wrap-around ring absorbs the boundary
effect. (Terminology note: this draft's earlier 'reflective (symmetric/
half-sample) padding' wording is superseded by proposal-final's whole-sample
WSS convention per hypothesis-gate reviewer G1 item 1.)
The solve (K + lambda I)a = y is then obtained as a **low-rank correction of
the embedded solve**: K = E^T C E (E = restriction), and

  (K + lambda I)^{-1}
    = (E^T (C + lambda I) E)^{-1}
    = (C+lambda I)^{-1} - Woodbury(E, complementary block),

where the correction is confined to a **boundary band of width w** (the
kernel's effective correlation length on the grid). The correction's rank is
O(w * (H+W)) — not O(N) — so the Woodbury step costs O(N log N + (w(H+W))^2
(H+W)^?) and memory stays O(N). The boundary bandwidth w is chosen
**adaptively** from the kernel's spectral decay (e.g., w = ceil(3 * rho) where
rho is the Matérn range parameter in grid units).

**Verification protocol** (pre-registered): on synthetic GRFs with *controlled
free boundary conditions*, compare (i) dense free-boundary solve (reference;
small grids), (ii) standard BCCB wrapping, (iii) RE-ABLRC, on the *same*
kernel and interpolation/evaluation protocol; report the relative error
gap  g = ||f_approx - f_free|| / ||f_free||  and its % reduction relative to
the BCCB-wrapping gap. Threshold: gap reduction >= 50%.

## 3. Strategy S2: Spectral-Spatial Alternating Minimization with Circulant-Accelerated Anderson Mixing (SSAM-CAM)

**Goal**: masked-input solves at >= 3x the speed of standard PCG at
equivalent residual tolerance < 1e-6, without forming (P_m K P_m^T + lambda I).

**Idea**: Solve the masked KRR problem in coefficient space,

  min_a  || P_m (K a - y) ||^2 + lambda a^T K a,

by **alternating minimization** that never forms the masked Gram:
- **Spectral step**: K a is a convolution -> computed by FFT in O(N log N)
  (K a = IFFT(FFT(c) .* FFT(a))); the ridge term lambda a^T K a likewise.
- **Spatial step**: the fidelity term ||P_m(...)||^2 only touches the observed
  cells -> a cheap O(n) projection/soft-threshold on the mask.
- Alternating the gradient/proximal steps (half-quadratic splitting / FISTA
  family) converges to the same solution as the masked Gram solve; the
  per-iteration cost is O(N log N + n), memory O(N).
- **Circulant-accelerated Anderson mixing**: the fixed-point map of the
  alternating scheme is contractive with a circulant (BCCB) linear part; apply
  Anderson extrapolation on the spectral residual to reach tol < 1e-6 in a
  fraction of PCG iterations (classical PCG on the masked Gram needs
  245-281 iters; target: < ~60-90 equivalent iterations -> >= 3x wall-clock
  speedup at equal final residual).

**Verification protocol** (pre-registered): same masked-reconstruction tasks
as iteration-2 T1b (Kaplan masks + synthetic masks), same evaluation cells,
PCG reference at tol < 1e-6; report iterations, wall-clock, and the speedup
factor. Threshold: speedup >= 3x (median over tasks/seeds).

## 4. Multi-domain benchmark (arm B-iter3)

| Domain | Description | Splits / leakage rules |
|---|---|---|
| Synthetic 2D non-stationary GRF | Matérn-family fields with controlled boundary conditions (free, Dirichlet, mixed), non-stationary range/length fields, missing-data masks 10/30/50% | train interior / test boundary band + masked cells; seeds 0-19 |
| Synthetic 3D non-stationary GRF | 32x32x32 blocks, Matérn 3/2 + non-stationary variance | same protocol, seeds 0-9 |
| Standard regular-grid ML benchmark | MNIST-784 (28x28) grid infilling (random-mask reconstruction + row/band masks) as the canonical regular-grid infilling task | held-out digit classes + held-out patch masks; no overlap |
| Real Kaplan SST v2 | 36x72 fields, sentinel-aware, masks (polar caps, land, random 10/30/50%) | future-blind train 1856-01..2015-12 / test 2016-01..2022-12 (iteration-2 windows) |

**Baselines** (each implemented CPU-only, honest configuration published):
exact dense KRR (subsample cap <= 4000 points), standard PCG on the masked
Gram, KISS-GP (structured grid inducing points with local interpolation;
Toeplitz-BTTB Gram on the inducing grid -> solves via our circulant
machinery), Random Fourier Features (RFF; sklearn Ridge on RFF features).

**Metrics**: RMSE / MAE on valid cells (mask-excluded), CRPS-style coverage
(conformal 0.90 target, per-mask), wall-clock, peak RSS, flops/bytes estimates
(est_spectral_fit_flops / est_spectral_bytes), accuracy-per-flop and
accuracy-per-byte ratios (solve-cost control framing), iterations to
tol < 1e-6 and the PCG-speeedup factor, boundary-gap reduction %.

## 5. Success / failure semantics (pre-registered, aggregate)

- S1 PASS iff median gap reduction >= 50% vs BCCB wrapping across (2D, 3D)
  free-boundary tasks; partial credit reported honestly per task.
- S2 PASS iff median speedup vs standard PCG at tol < 1e-6 >= 3x; fail if
  < 1.5x (then report the honest negative).
- Benchmark PASS iff proposal beats at least the two structured baselines
  (PCG and BCCB-wrapping) on >= 3 of the 4 domains in RMSE at equal-or-lower
  cost envelope; ties reported.

## 6. Honest framing (invariants, same as iteration-2, extended)

- No claim that Woodbury / Anderson mixing / FISTA are new: the novelty is the
  *grid-KRR-targeted integration*: reflective-embedding + adaptive
  boundary-banded correction for free-boundary BCCB solves, and spectral-
  spatial AM with circulant-accelerated mixing for masked grids — each
  corpus-positioned against the iteration-3 literature review (G5-G8).
- Every number in the paper traces to results/iter3/*.json; no
  [simulated]-framing (real fields carry dataset.origin real-kaplan-sst-v2);
  synthetic-GRF domains are explicitly labeled synthetic with a full
  generator description (reproducible sampling, seeds) — disclosed as such.
- Baselines implemented with published conventions (KISS-GP: Wilson &
  Nickisch 2015; RFF: Rahimi & Recht 2007; PCG: standard practice; dense
  KRR: exact Cholesky on the subsample).