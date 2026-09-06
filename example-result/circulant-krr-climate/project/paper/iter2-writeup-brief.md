# Iteration-2 paper rewrite brief (writeup worker input)

Rewrite `paper/main.tex` (4 pages, NeurIPS 2026 workshop template,
`compile.sh` + `pdflatex`-based, working in this dir) so it reports the
REAL-DATA iteration-2 study. Replace every `[simulated]` framing; the
abstract MUST state real-data validation on Kaplan SST v2.

## Honest-framing invariants (non-negotiable)
- No FFT-kernel newness, no spectral-regression newness, no SOTA-ENSO-skill
  claims. Contribution = concrete CPU-only circulant-block implementation +
  real-data reconstruction/index benchmark + leakage-verified evaluation
  protocol + resource accounting.
- EXACT = torus-embedded kernel only. Report the free-boundary gap per
  kernel on the real test field (relative 0.95 matern32 / 0.12 rbf) in the
  method + limitations; never claim free-boundary exactness.
- Every number below must match the artifacts in results/iter2/ (read the
  JSONs; paper_content.json is the digest). No new numbers invented.
- T3 transfer superiority is REFUTED under the pre-registered semantics
  (0/4 horizons supported) — state it as an explicit honest negative, with
  the per-horizon table, bootstrap CIs, and the h=12 floor.
- The T2 functional gain is a 5-fold temporal-block CV method comparison
  (leakage-safe), NOT a future-blind forecast claim — say so in-text.
- Coverage diagnostics: target 0.90; report per-mask coverage and list
  violations (matern32 halo_w4 decay 0.739, seam 0.836; rbf halo_w2 global
  0.816) — no averaging away.
- Missing data: 53.4% of cells (100% polar caps; land columns); sentinel
  -9.96921e36 treated as missing, imputed by valid-cell monthly mean,
  excluded from every evaluation target (valid-only evaluation).
- Resolution sensitivity is an honest negative (10-deg coarsening
  degrades: recon RMSE 0.0853->0.1667; functional RMSE 0.0856->0.3825,
  corr 0.997->0.950).
- Resource axes: 78.7 s wall, 1.57 GB peak, CPU-only (NumPy/SciPy/sklearn;
  h5py only for data reading), O(N log N)/O(N).
- Keep the iter-1 title/contribution positioning but update the dataset
  sentence: real Kaplan SST v2 (results/raw/real/, h5py conversion).
- Remove iter-1 claims that no longer apply (simulated pilot numbers like
  free-gap 1.74->0.31; 70.8 s; 0.071 RMSE; etc.) or replace with the
  real-data equivalents.

## Headline numbers (verify each against artifacts)
- P0: torus-exact 2.62e-12 rel (matern32) / 1.12e-12 (rbf) vs dense
  floored-torus on a real test-window field; free-gap 0.95 / 0.12.
- T1a (test window 2016-01..2022-12, 84 months): matern32 masked RMSE
  0.0816-0.0880 across random 10/30/50% and halo w1/w2/w4 masks; rbf
  0.2356-0.3155. Field anomaly std on the test window 0.6001 -> RMSE ~14%
  of std. Per-kernel calendar-month conformal coverage global 0.877-0.899
  (matern32) / 0.816-0.893 (rbf); target 0.90; violations listed.
  Optimism gap (random vs halo) +0.0040.
- T1b masked-input PCG: per-rate mean iterations 245-281 (per-field span 233-291) to tol 1e-8, converged all runs, RMSE on masked ~0.53; rel residual 5e-9..8e-9.
- T2 Nino3.4 functional (5-fold temporal-block CV over 2005 months):
  RMSE 0.0856 (corr 0.997; r2 0.994) vs direct ridge head 0.270 (3.2x)
  vs zero-model 0.795. Scope note mandatory.
- T3 transfer forecast: h=1 {0.268 vs pers 0.251 / clim 0.773 / AR1 0.241,
  skill 0.880}; h=3 {0.565 vs 0.562/0.773/0.508}; h=6 {0.796 vs 0.907/
  0.773/0.766, skill -0.061, beats persistence only, p=0.234}; h=12 {0.923
  vs 1.154/0.773/0.879, skill -0.427}. VERDICT: REFUTED (0/4). Bootstrap
  se 0.0056-0.333 across all comparisons (vs-persistence subset 0.007-0.333; n_blocks 7, n_resamples 2000, seed 7). Start-month x
  lead skill tables (January-origin best at h=1 skill 0.954; April-origin strongest at h>=3 (0.84/0.70/0.06); October-origin worst at h=6 -0.88 / h=12 -0.96) — origin dependence, h=12 floor. Truncation sweep
  cutoffs 2012/2013/2014-12: skill 0.8795-0.8797 stable.
- B (same 2000 valid test cells): ridge subsample 0.820-0.824, Nystrom
  0.820, RFF 0.822; spectral 0.0999; flop ratios PER METHOD: ridge 5.3e4-7.5e5x (5.6-6.8 orders acc/flop), Nystrom 1.6e6x (~7.1 orders), RFF 4.8e2x (~3.6 orders); trivial parity baselines zero 0.801 /
  global-mean 0.605 / per-cell climatology 0.813 (task is near-signal-free
  for coordinate-only regression).
- Resolution: 5-deg native vs 2x2-coarsened 10-deg (see honest negative).
- Scaling: sub-ms fits through N=10,368; single 0.25-deg field est ~0.04 GB
  (batch memory grows linearly).

## main.bib update
Add (verify key names against existing bib): Barber, Candes, Ramdas,
Samworth 2023 (non-exchangeable conformal); Chernozhukov, Wuthrich, Zhu
2018 (exact/conformal for dependent data) if web-verified; Gibbs & Candes
2021 ACI; Diebold & Mariano 1995; Kunsch 1989 block bootstrap; Bergmeir &
Benitez 2012; Penland & Magorian 1993 LIM; Barnston, Tippett, L'Heureux,
Li, DeWitt 2012 (ENSO skill/verification); Kirtman et al. 2014 (NMME);
Webster & Yang 1992 (spring barrier); Ham, Kim, Luo 2019 Nature / 2021
(deep-learning ENSO) or Zhou & Zhang 2022; Chen et al. 2025 Nat. Commun.
if available; Yin et al. 2019 (sketch KRR via circulant, IEEE TNNLS
31(9):3512-3524); Le, Sarlos, Smola 2013 Fastfood; Gardner et al. 2018
GPyTorch; Lazaro-Gredilla et al. 2010. Keep existing entries that are
still cited. Reference URLs live in docs/literature-review/review.md
(References section) for web-verified entries.

## Template/existing structure to keep
Sections: Introduction, Method (BCCB solve eq, torus exactness scoping,
masked PCG), Data (real Kaplan SST v2 + missing handling + splits windows),
Experiments+Results (tables T1a/T1b/T2/T3/B/S/R + ratio control),
Limitations + Discussion (honest negatives incl. REFUTED T3, coverage
violations, resolution degradation, Kaplan smoothing caveat), Conclusion.
Compile with compile.sh (pdflatex chain); verify main.pdf is 4 pages.
Commit the workspace changes (git in the project root).