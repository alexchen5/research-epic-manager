# Verification report: no method-code divergence, no unreproducible empirical claims

Date: 2026-09-04
Scope under audit: the synthesised report
`/workspace/research-project-manager/projects/automlr-workshop-paper/latex/part1.tex`
(and the companion `part2.tex` / `part3.tex` / `main.tex` bundle, where cited
numbers appear).
Evidence base: committed source under `scripts/` and committed result artifacts
under `results/` (for this report, primarily `results/iter2/*.json`).

Three checks were performed, mirroring the issue acceptance criteria:

- A. Method-code traceability (report method statements -> implementing code).
- B. Empirical-claim reproducibility (every report number -> committed artifact
  at matching value).
- C. Superseded-number leakage (no pre-fix / pre-iteration figure republished).

---

## Check A - Method-code traceability: PASS

The report's "Method: exact torus spectral KRR" section and protocol arms map to
committed code with no contradiction. Mapping:

| Report method statement | Implementing code (scripts/) |
|---|---|
| BCCB Gram of the periodised (torus) kernel via circular row/col distances | `fft_krr.torus_first_column` (dy=min(iy,ny-iy), dx=min(ix,nx-ix)) |
| Spectral solve `alpha = irfft2(rfft2(y) / (c_hat + lambda))`, O(N log N) / O(N) memory | `fft_krr.fit_torus` + `fft_krr.torus_spectrum` |
| Spectral floor / PSD projection for negative BCCB eigenvalues (e.g. RBF), then ridge | `fft_krr.torus_spectrum` (`np.maximum(spec_raw,0)` when n_neg>0, then `spec+lam`) |
| Free-boundary masked solve: PCG, exact BTTB matvec via the (2N-1)-mirror circulant, floored-torus spectral preconditioner, tol 1e-8 | `fft_krr.embed_first_column` (mirror embedding) + `fft_krr.cg_masked_solve` (used by run_iters2.py T1b); documented in `fft_krr.py` module docstring |
| Kernel-consistent box functional for the Nino3.4 index | `fft_krr.predict_box_functional` (area-weighted box mean of the spectral prediction) |
| Protocol arms P0 / T1a / T1b / T2 / T3 / B / S | `scripts/run_iters2.py` (module docstring enumerates each arm and its artifact) |
| Baselines exact / Nystrom / RFF | `scripts/baselines.py` |
| T3 transfer h in {1,3,6,12} vs persistence / train-only climatology / AR(1), year-block bootstrap win rule | `scripts/run_iters2.py` (T3 arm) + win-rule wording recorded verbatim in `results/iter2/T3-forecast-transfer.json` |

No method statement in the report contradicts the code. The report's framing
("exact FOR THE EMBEDDED-TORUS KERNEL only; free-boundary is the modeling gap")
matches the honest qualification in `fft_krr.py`'s module docstring and the
pre-committed proposal.

## Check B - Empirical-claim reproducibility: PASS

Every quantitative figure checked in the report traces to a committed artifact at
a matching value (report value vs artifact value).

### P0 torus exactness (report Section P0)
- spectral-vs-dense relative ell-inf: matern32 2.62e-12, rbf 1.12e-12 ->
  `results/iter2/P0-pilot-gate-real.json` `matern32.spectral_vs_dense_torus_rel`
  = 2.61798e-12, `rbf...` = 1.11696e-12.
- free-boundary gap 0.95 (matern32) / 0.12 (rbf) ->
  `torus_vs_free_gap_rel` = 0.94962 / 0.11592.

### T1a masked reconstruction (report Table tab:t1a)
Source: `results/iter2/T1a-spectral-reconstruction.json` `per_mask_metrics`.
- matern32 RMSE: random 10% 0.0843 (0.08435); 30% 0.0856 (0.08560); 50% 0.0872
  (0.08723); halo w1 0.0827 (0.08270); w2 0.0816 (0.08156); w4 0.0880 (0.08796).
- matern32 coverage: 0.898 / 0.892 / 0.886 / 0.896 / 0.897 / 0.877 (artifact
  0.89778 / 0.89158 / 0.88605 / 0.89583 / 0.89708 / 0.87667).
- rbf RMSE: 0.2525 / 0.2411 / 0.2356 / 0.2789 / 0.2839 / 0.3155 (artifact
  0.2525 / 0.2411 / 0.2356 / 0.2789 / 0.2839 / 0.3155).
- rbf coverage: 0.873 / 0.893 / 0.892 / 0.856 / 0.816 / 0.824.
- random-vs-halo gap +0.0040 = 0.0856 (random 30%) - 0.0816 (halo w2).
- Localised violations cited: matern32 halo w2 decay 0.747 (0.74731); halo w4
  seam/decay 0.836 / 0.739 (0.83594 / 0.73893); rbf halo w2 global 0.816.

### T1b genuinely masked training (report Section T1b)
Source: `results/iter2/T1b-CG-masked-train.json`.
- mean iterations 245-281 (rate means 280.875 / 276.125 / 245.125; span 233-291).
- final relative residual 4.69e-9..9.81e-9 (4.6935e-9 .. 9.8070e-9).
- masked RMSE 0.529-0.541 (0.54116 / 0.52932 / 0.53124).
These match the CANONICAL lock directive in `EXECUTION_NOTES.md`, not the
superseded pre-fix figures.

### T2 Nino3.4 functional index (report Section T2)
Source: `results/iter2/T2-ENSO-index.json`.
- functional RMSE 0.0856 (0.08561); direct ridge head 0.2696 (0.26959), ~3.2x;
  zero baseline 0.7955 (0.79546); corr 0.997 (0.99712).

### T3 transfer forecast (report Table tab:t3 and Section T3)
Source: `results/iter2/T3-forecast-transfer.json`.
- h=1 transfer 0.268 / pers 0.251 / climat 0.773 / AR(1) 0.241 / skill 0.880
  (0.26791 / 0.25087 / 0.77287 / 0.24089 / 0.87984).
- h=3: 0.565 / 0.562 / 0.773 / 0.508 / 0.466 (0.5650 / 0.5616 / 0.7729 /
  0.5076 / 0.4656).
- h=6: 0.796 / 0.907 / 0.773 / 0.766 / -0.061 (0.7963 / 0.9073 / 0.7729 /
  0.7656 / -0.061).
- h=12: 0.923 / 1.154 / 0.773 / 0.879 / -0.427 (0.9232 / 1.1538 / 0.7729 /
  0.8785 / -0.427).
- aggregate REFUTED (0/4 supported): each horizon's `win.supported` = false.
- h=1 margin vs best = -0.0137 (`margin_vs_best` = -0.013748), matching the
  reported tailing-AR(1) margin.
- bootstrap CI half-widths 0.0056..0.333 (`bootstrap_se_range_all_comparisons`).
- truncation sweeps (2012/13/14 cutoffs) keep h=1 skill 0.8795..0.8797
  (`truncation_sweep_h1` 0.87958 / 0.87962 / 0.87973).
- seasonality: January h=1 skill 0.954; April strongest at h>=3; October drives
  across h in {1,3,6,12} to 0.62 / -0.00 / -0.88 / -0.96
  (`start_month_skill` origin-month-9 0.6205 / -0.00 / -0.88 / -0.96).

### B pooled-cell baselines (report Section B)
Source: `results/iter2/RESOLUTION-AND-RATIOS.json` + `B-baselines.json`.
- spectral reconstruction RMSE 0.0999 (`spectral_2592.rmse` = 0.09991) on the
  SAME 2000 valid test cells.
- coordinate-only exact/Nystrom/RFF RMSE 0.820..0.824 (0.82031..0.82438).
- relative FLOPs 4.8e2 .. 1.6e6 (`flop_ratio_vs_spectral`: rff_4828 480.07,
  ridge_2000 53031.95, ridge_4828 746018.16, nystrom_4828 1628743.78).
- trivial baselines zero 0.801 / mean 0.605 / climatology 0.813
  (`trivial_baselines` 0.80115 / 0.60454 / 0.81258).

### R resolution sensitivity (report Section R)
Source: `results/iter2/RESOLUTION-AND-RATIOS.json`.
- reconstruction 0.0853 -> 0.1667 (0.08527 -> 0.16668).
- functional RMSE 0.0856 -> 0.3825 (0.08561 -> 0.38249), corr 0.997 -> 0.950
  (0.99712 -> 0.94978).

### S scaling and footprint (report Section S)
Source: `results/iter2/S-scaling.json` + `results/iter2/results_summary.json`.
- sub-millisecond fits 0.2..0.5 ms to N=10,368 (wall_clock_s 0.0002 / 0.0002 /
  0.0005).
- five working arrays, ~0.04 GB for ~1e6 cells (`extrapolation.est_bytes`
  41.47 MB at 1,036,800 cells).
- footprint 78.7 s / 1.57 GB (`results_summary.json` total_wall_clock_s 78.74,
  peak_rss_gb 1.573).

## Check C - Superseded-number leakage: PASS

- The report cites T1b as mean iterations 245-281, residual 4.69e-9..9.81e-9,
  RMSE 0.529-0.541, which are exactly the CANONICAL values from
  `results/iter2/T1b-CG-masked-train.json`. It does NOT republish the pre-fix
  figures (420-550 iters / RMSE 0.78-0.83) that `EXECUTION_NOTES.md` marks as
  never-to-cite. It also states full-field spectral T1a remains more accurate,
  consistent with the locked narrative.
- Data mode: the report states real NOAA Kaplan SST v2 (2005 fields). All cited
  numbers come from `results/iter2/` artifacts whose `dataset.origin` =
  "real-kaplan-sst-v2" and `simulation_marker` = null. No iteration-1
  [simulated] figure from `results/claims.json` (e.g. T1a RMSE 0.071, T2 0.0628,
  footprint 70.8 s / 5.06 GB) is republished as a real-data result.

## Verdict

- Check A (method-code): PASS - no method-code divergence.
- Check B (empirical-claim reproducibility): PASS - all checked report numbers
  trace to committed artifacts at matching value.
- Check C (superseded-number leakage): PASS - no unlawful superseded figure.

Overall: the synthesised report `part1.tex` is free of method-code divergence
and contains no unreproducible or superseded empirical claims under the stated
evidence base. Minor observational note (not a divergence): the report's
conformal protocol description ("conformity scores = |y - y_hat| on valid cells
of terminal in-train fields 1860-1919") aligns with the artifact's
`conformal_protocol` ("60 terminal in-train years' same-calendar-month
scores"); the specific field-range wording is a prose paraphrase of the
artifact field, not a contradiction.
