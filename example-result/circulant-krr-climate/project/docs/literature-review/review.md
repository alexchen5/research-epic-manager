# Literature Review: Exact Kernel Ridge Regression on Regular-Grid Climate
# Fields via Block-Circulant Structure and the FFT

Project: circlant-krr-climate (epic: /workspace/epics/circulant-krr-climate)
Stage: literature_review (anchor issue: literature-review-anchor-r1)

## Executive summary

The primary research question of this project is ALGORITHMIC and
METHODOLOGICAL: can exact kernel ridge regression (KRR) be made tractable on
regular latitude/longitude climate grids under consumer hardware by
exploiting the block-circulant structure of stationary kernels and solving in
the Fourier domain with the FFT -- O(N log N) training and prediction,
O(N) memory, no explicit N-by-N kernel matrix? The climate domain
(sea-surface temperature anomaly fields for masked-field reconstruction and
the Nino3.4 / ENSO index) is the experimental substrate.

The literature is mature on each individual ingredient: (a) spectral and
structured kernel methods show that stationary kernels on grids admit
fast, structured algebra (Gray's Toeplitz/circulant review; Dietrich and
Newsam's circulant embedding; KISS-GP's Kronecker/Toeplitz structure);
(b) randomized approximations (RFF, Nystrom) dominate the "scalable kernel"
story because exact solves are declared infeasible; (c) the climate-ML
literature is benchmark-first (WeatherBench) or GPU-scale (deep ENSO
forecasting), with resource accounting absent. What is MISSING is a
systematic, honest, CPU-only evaluation of *exact* kernel machines on
climate grids under memory constraints, with accuracy-per-flop and
accuracy-per-byte as first-class axes, and with block (leakage-aware)
cross-validation. That missing piece is precisely this project's
contribution.

Provenance note (honest flags): entries below are flagged
`[web-verified]` when the bibliographic record (title/authors/venue/year)
was confirmed by web search during this session, and
`[model-knowledge]` otherwise (from pretrained knowledge, not re-checked
in-session). No entry is invented; flags only state how strongly the
bibliography was confirmed.

Iteration 2 (this session) appended entries 26-40 across three gap topics
(leakage-verified evaluation protocols; ENSO / Nino3.4 forecasting
state of the art; FFT / spectral-kernel KRR evaluation practices). All 15
new entries were web-verified in-session (title/authors/venue/year
confirmed via web search or publisher pages).

Iteration 3 (this session) appended entries 41-69 across the six mandated
clusters (boundary-aware / embedding-corrected fast kernel solves;
spectral-spatial alternating minimization for masked/partial observation;
low-rank + structured-Toeplitz corrections; non-stationary GRF simulation
with controlled boundary conditions; regular-grid infilling benchmark
tasks and metrics; masked / partial-observation kernel methods) plus
exact free-boundary Toeplitz-solve and efficiency-benchmarking
conventions. All 29 new entries were web-verified in-session
(title/authors/venue/year confirmed via web search or publisher pages).

Iteration 4 (rework r2, this session) appended entries 70-74 (four
FAIL-feedback-informed anchors: general-dimension circulant-embedding PSD
conditions [70, Graham et al. 2018]; randomized Nystrom preconditioning
[71, Frangella-Tropp-Udell 2023]; 3D multilevel block-Toeplitz matvec [72,
Barrowes-Teixeira-Kong 2001]; stabilized superfast Toeplitz solve [73,
Stewart 2003]; DCT symmetric-boundary eigenbasis [74, Strang 1999]) plus a
new "Gap Coverage (iteration 4 / rework r2, G9+)" section, three
FAIL-feedback-informed strategy families, and a Nexus note on the 3D WSS-
embedding PSD question. All 5 new entries were web-verified in-session.
The iteration-3 measured artifacts are INVALIDATED HISTORY: they are
referenced in this file ONLY as honest negatives inside the G9+ section
and are never framed as qualifying claims.

## Thematic map

### 1. Spectral / structured kernel methods (the algorithmic core)

- Circulant and Toeplitz matrix structure, FFT convolution theorem, and
  fast matrix-vector products for stationary kernels.
- Circulant embedding of covariance matrices for exact simulation of
  stationary Gaussian fields (the "sample from N x N covariance without
  building it" trick -- same structure we use for KRR solves).
- Structured kernel interpolation (KISS-GP): Kronecker + Toeplitz algebra
  for scalable GPs, and its spectral-mixture siblings.
- SPDE/GMRF approach: continuous covariance approximated by sparse
  Markov structure on a mesh -- an alternative route to structured,
  scalable Gaussian fields.
- Fast exact simulation and grid-based GP methods that exploit regular
  grids (Wood-Chan; circulant embedding literature).

### 2. Randomized kernel approximations

- Random Fourier Features (Bochner/trigonometric Monte Carlo).
- Nystrom method (landmark sampling) and its improved/recursive variants.
- Randomized linear algebra view: these are low-rank approximations with
  probabilistic error guarantees; accuracy/memory trade-off is central.
- Empirical behavior: approximation quality is kernel- and
  spectrum-dependent; no universal winner on low-dimensional smooth
  problems.

### 3. Exact kernel machines and their cost

- Kernel ridge regression (dual-form ridge regression), O(N^2) memory,
  O(N^3) solve; the standard "intractable at scale" claim.
- Gaussian process regression as kernel regression + uncertainty;
  GPML book: O(N^3) inference, sparse and low-rank escape hatches.
- The bias-variance/regularization picture for ridge: the well-posedness
  and conditioning story that structured solvers inherit.

### 4. Kernel and statistical methods in climate / geophysics

- SST field analyses and reconstruction (Kaplan et al. EOF-based
  reconstruction: kernel-PCA-like low-rank subspace fitting -- the exact
  substrate for masked-field reconstruction comparisons).
- ENSO / Nino3.4 index definition (Trenberth) and index regression as an
  off-grid prediction task.
- Deep-learning ENSO forecasting (Ham et al., Nature 2019) and
  benchmark-first forecasting (WeatherBench, Rasp et al. 2020): the
  GPU-scale / benchmark-first contrast this project deliberately avoids.
- Kriging / spatial statistics (Stein; SPDE/GMRF): the statistics-side
  tradition of structured covariance exploitation and of proper spatial
  evaluation (block CV), largely not imported into kernel-ML climate
  studies.

## Annotated bibliography

1. [web-verified] Rahimi, A. and Recht, B. (2007). Random features for
   large-scale kernel machines. Advances in Neural Information Processing
   Systems 20 (NIPS 2007). -- Introduces Random Fourier Features (RFF):
   approximate a stationary kernel by a random trigonometric feature map
   from its spectral density (Bochner's theorem). THE canonical randomized
   kernel approximation; a primary baseline for this project.
2. [web-verified] Williams, C. K. I. and Seeger, M. (2001). Using the
   Nystrom method to speed up kernel machines. NIPS 2000 proceedings,
   MIT Press, 682-688. -- Introduces the Nystrom approximation for kernel
   machines; landmark sampling + low-rank factor. Primary baseline.
3. [web-verified] Drineas, P. and Mahoney, M. W. (2005). On the Nystrom
   method for approximating a Gram matrix for improved kernel-based
   learning. Journal of Machine Learning Research 6:2153-2175. -- Theory
   for Nystrom: sampling-dependent spectral-norm/Frobenius bounds. Anchor
   for the accuracy-vs-sampling trade-off discussion.
4. [web-verified] Gray, R. M. (2006). Toeplitz and circulant matrices: a
   review. Foundations and Trends in Communications and Information
   Theory 2(3):155-239. -- The fundamental reference for circulant
   matrices: circulants are diagonalized by the Fourier matrix, eigenvalues
   from the FFT of the first column; Toeplitz approximated by circulants.
   The mathematical backbone of our algorithm.
5. [web-verified] Dietrich, C. R. and Newsam, G. N. (1997). Fast and exact
   simulation of stationary Gaussian processes through circulant embedding
   of the covariance matrix. SIAM Journal on Scientific Computing
   18(4):1088-1107. -- Circulant embedding: sample exactly from a large
   stationary covariance via one FFT-based square root, O(N log N), O(N)
   memory. Proves the structure is exploitable for *exact* (not
   approximate) computation on grids; our KRR solve uses the same block.
6. [web-verified] Wilson, A. G. and Nickisch, H. (2015). Kernel
   interpolation for scalable structured Gaussian processes (KISS-GP).
   ICML 2015. -- Structured kernel interpolation; combines inducing points
   with Kronecker/Toeplitz structure. Closest prior art to "structure
   exploitation for scalable kernel inference"; our contribution differs in
   being exact (no inducing/interpolation loss) on a regular grid and
   benchmarked on CPU with explicit memory accounting.
7. [web-verified] Rasmussen, C. E. and Williams, C. K. I. (2006). Gaussian
   processes for machine learning. MIT Press. -- GPML standard reference:
   O(N^3) exact inference, kernel design, model selection. Baseline cost
   model for everything "exact".
8. [web-verified] Lindgren, F., Rue, H., and Lindstrom, J. (2011). An
   explicit link between Gaussian fields and Gaussian Markov random
   fields: the stochastic partial differential equation approach. Journal
   of the Royal Statistical Society, Series B 73(4):423-498. -- SPDE/GMRF:
   alternative structured (sparse) route to scalable Gaussian fields on
   meshes; the geostatistics-side precedent for structure-first scaling.
9. [web-verified] Ham, Y.-G., Kim, J.-H., and Luo, J.-J. (2019). Deep
   learning for multi-year ENSO forecasts. Nature 573:568-572. -- GPU-scale
   CNN for ENSO forecasts; the benchmark-first contrast: no CPU budgets,
   no memory accounting. Positioned in our paper as the "heavy baseline as
   context from literature, not to be reproduced".
10. [web-verified] Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A.,
    Mouatadid, S., and Thuerey, N. (2020). WeatherBench: a benchmark data
    set for data-driven weather forecasting. Journal of Advances in
    Modeling Earth Systems 12(11):e2020MS002203. -- Benchmark-first
    weather ML: fixed leaderboard at cluster scale. Contrast for the
    ground-up/CPU honest-resource framing; also a dataset-origin template
    (open, reanalysis-based).
11. [web-verified] Kaplan, A., Cane, M. A., Kushnir, Y., Clement, A. C.,
    Blumenthal, M. B., and Rajagopalan, B. (1998). Analyses of global sea
    surface temperature 1856-1991. Journal of Geophysical Research
    103(C8):18567-18589. -- EOF-based SST field reconstruction over sparse
    observations; the exact experimental family for masked-field
    reconstruction. NOAA PSL distributes the Kaplan SST v2 product
    (psl.noaa.gov/data/gridded/data.kaplan_sst.html) -- candidate primary
    dataset (open; also the source of the widely used Nino3.4 time series).
12. [web-verified] Trenberth, K. E. (1997). The definition of El Nino.
    Bulletin of the American Meteorological Society 78(12):2771-2777. --
    Canonical definition of the Nino3.4 index and ENSO episodes; anchors
    the index-regression task description.
13. [model-knowledge] Scholkopf, B. and Smola, A. J. (2002). Learning with
    kernels. MIT Press. -- Comprehensive kernel-methods monograph; dual
    formulations, representer theorem, kernel design.
14. [model-knowledge] Shawe-Taylor, J. and Cristianini, N. (2004). Kernel
    methods for pattern analysis. Cambridge University Press. -- Kernel
    matrix algebra toolkit: properties, low-rank analysis, algorithmic
    kernel constructions.
15. [model-knowledge] Hoerl, A. E. and Kennard, R. W. (1970). Ridge
    regression: biased estimation for nonorthogonal problems.
    Technometrics 12(1):55-67. -- Ridge regularization origin: the
    bias-variance trade-off that KRR inherits; motivates the ridge-
    conditioning discussion in the methods section.
16. [model-knowledge] Saunders, C., Gammerman, A., and Vovk, V. (1998).
    Ridge regression learning algorithm in dual variables. ICML 1998. --
    KRR dual-form derivation; the exact formulation our algorithm
    solves in the Fourier domain.
17. [model-knowledge] Bach, F. (2017). On the equivalence between kernel
    quadrature rules and random feature expansions. Journal of Machine
    Learning Research 18(21):1-38. -- Connects RFF to quadrature; sharpens
    the theory of randomized kernel approximations (accuracy vs quadrature
    quality). Useful for baseline characterization.
18. [model-knowledge] Halko, N., Martinsson, P.-G., and Tropp, J. A.
    (2011). Finding structure with randomness: probabilistic algorithms
    for approximating matrix decompositions. SIAM Review 53(2):217-288. --
    Randomized linear algebra: the error/memory/resource framing we reuse
    for accuracy-per-flop/byte accounting of the baselines.
19. [model-knowledge] Stein, M. L. (1999). Interpolation of spatial data:
    some theory for kriging. Springer. -- Spatial-statistics theory of
    interpolation and covariance modeling; the geostatistical foundation
    for structured kernel design on climate fields.
20. [model-knowledge] Quinonero-Candela, J. and Rasmussen, C. E. (2005).
    A unifying view of sparse approximate Gaussian process regression.
    Journal of Machine Learning Research 6:1939-1959. -- Unifying framework
    for sparse GP approximations (the family KISS-GP/Nystrom/inducing
    points belong to); catalogues exactly what is thrown away by
    approximation -- the accuracy loss our exact solver avoids.
21. [model-knowledge] Musco, C. and Musco, C. (2017). Recursive sampling
    for the Nystrom method. NIPS 2017. -- Improved Nystrom sampling with
    near-optimal error; modern baseline variant worth comparing.
22. [model-knowledge] Saatci, Y. (2012). Scalable inference for structured
    Gaussian process models. PhD thesis, University of Cambridge. --
    Kronecker/Toeplitz GP inference at scale on grids; the structured-GP
    line that our work extends to exact KRR with resource accounting.
23. [model-knowledge] Flaxman, S., Wilson, A. G., Neill, D. B., Nickisch,
    H., and Smola, A. J. (2015). Fast Kronecker inference in Gaussian
    processes with non-Gaussian likelihoods. ICML 2015. -- Kronecker
    structure for non-Gaussian GP likelihoods; precedent for structured
    solves on grid-shaped data.
24. [model-knowledge] Pedregosa, F. et al. (2011). Scikit-learn: machine
    learning in Python. Journal of Machine Learning Research 12:2825-2830.
    -- scikit-learn (KernelRidge, Nystroem, RFF via
    RBFSampler/FastFood-style APIs): the baseline library AND the
    software substrate constraint (our stack: numpy/scipy/sklearn only).
25. [model-knowledge] Wood, A. T. A. and Chan, G. (1994). Simulation of
    stationary Gaussian processes in [0,1]^d. Journal of Computational and
    Graphical Statistics 3(4):409-432. -- Early circulant-embedding
    simulation on grids (precursor to Dietrich-Newsam); reinforces that
    FFT-based exact structure exploitation on regular grids is established
    in statistics but not in kernel-ML evaluation practice.

### Gap A extension -- leakage-verified evaluation protocols (entries 26-31)

26. [web-verified] Barber, R. F., Candes, E. J., Ramdas, A., and
    Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability.
    Annals of Statistics 51(2):816-845. -- Generalizes split-conformal
    finite-sample coverage guarantees beyond exchangeability: arbitrary
    perturbations of exchangeability yield a coverage gap bounded by a
    total-variation distance between calibration and test distributions.
    -- Supplies the honest caveat for leakage-verified UQ in our protocol:
    temporally dependent climate residuals violate exchangeability, so the
    project pairs split-conformal intervals with temporal-block (not
    random) calibration and reports the dependence caveat rather than
    claiming i.i.d. coverage.

27. [web-verified] Chernozhukov, V., Wuthrich, K., and Zhu, Y. (2018).
    Exact and robust conformal inference methods for predictive machine
    learning with dependent data. Proceedings of the 31st Conference on
    Learning Theory (COLT 2018), PMLR 75:732-749. -- Split-conformal for
    time series: exact finite-sample coverage under exchangeability and
    approximate coverage under weak serial dependence, via a block-based
    construction for dependent data. -- Direct methodological precedent
    for the calendar-month-block / temporal-block conformal calibration
    used in the project's T1a diagnostic-interval arm.

28. [web-verified] Gibbs, I. and Candes, E. (2021). Adaptive conformal
    inference under distribution shift. Advances in Neural Information
    Processing Systems 34 (NeurIPS 2021). -- Adaptive conformal inference
    (ACI): an online update of the miscoverage level driven by empirical
    coverage, provably attaining the target coverage frequency over long
    intervals under arbitrary distribution shift. -- Justifies adaptive
    (rolling) calibration windows in the hindcast protocol: when the
    forecast-error distribution drifts along the rolling origin, a fixed
    calibration split over- or under-covers; ACI re-estimates
    continuously instead.

29. [web-verified] Diebold, F. X. and Mariano, R. S. (1995). Comparing
    predictive accuracy. Journal of Business & Economic Statistics
    13(3):253-263. -- The Diebold-Mariano test: a significance test for
    equal forecast accuracy that accounts for serial correlation in the
    loss differential through a long-run (HAC) variance estimator; the
    standard replacement for naive t-tests over per-period errors. -- The
    pre-registered win rule for the Nino3.4 transfer forecast (T3 arm)
    against persistence / climatology / AR(1) baselines uses a DM
    statistic with block-bootstrap p-values, not a naive monthly t-test.

30. [web-verified] Kunsch, H. R. (1989). The jackknife and the bootstrap
    for general stationary observations. Annals of Statistics 17(3):
    1217-1241. -- Introduces the (moving) block bootstrap for dependent
    sequences: resample contiguous blocks of length l to preserve
    short-range dependence, consistent as l(n) -> inf and l(n)/n -> 0;
    ancestor of year-block / moving-block resampling (stationary variant:
    Politis & Romano 1994). -- Grounds the project's year-block bootstrap
    win rule: naive i.i.d. resampling of monthly residuals breaks
    dependence and overstates the significance of forecast-skill
    differences.

31. [web-verified] Bergmeir, C. and Benitez, J. M. (2012). On the use of
    cross-validation for time series predictor evaluation. Information
    Sciences 191:192-213. -- Argues that blocked / rolling-origin forms of
    cross-validation are the standard, information-efficient evaluation
    protocol for time series predictors, and that random splits leak
    temporal structure. -- Supports the rolling-origin / expanding-window
    hindcast protocol with explicit seam and decay-phase leakage checks
    (no test window overlapping training or early-forecast-phase data).

### Gap B extension -- ENSO / Nino3.4 forecasting state of the art (entries 32-37)

32. [web-verified] Penland, C. and Magorian, T. (1993). Prediction of
    Nino 3 sea surface temperatures using linear inverse modeling.
    Journal of Climate 6(6):1067-1076. -- Linear inverse modeling (LIM):
    fit a linear stochastic Markov model to SST-anomaly EOF coefficients
    and forecast in state space; outperforms persistence at multi-month
    leads, with RMS error at 9-month lead about half a degree Celsius. --
    The canonical statistical ENSO baseline beyond persistence,
    climatology, and AR(p) that the project's Nino3.4 index regression
    must beat (via the pre-registered DM win rule, entries 29-30) to
    claim added value.

33. [web-verified] Barnston, A. G., Tippett, M. K., L'Heureux, M. L., Li,
    S., and DeWitt, D. G. (2012). Skill of real-time seasonal ENSO model
    predictions during 2002-11: Is our capability increasing? Bulletin of
    the American Meteorological Society 93(5):631-651. -- Standard
    real-time ENSO verification across 15 dynamical models: anomaly
    correlation (ACC) and RMSE by lead time and start month on Nino3.4
    anomalies with 3-month running-mean smoothing; the RMSE "useful
    skill"
    threshold (~1 degree) is reached on average only to ~6-month lead
    even for the best models; persistence is the reference benchmark. --
    Defines the field-standard hindcast-evaluation axes (ACC, RMSE by
    start/lead, persistence baseline) that the project's pre-registered
    significance framing adopts (with block-bootstrap significance per
    entry 30).

34. [web-verified] Kirtman, B. P., and Coauthors (2014). The North
    American Multimodel Ensemble: Phase-1 seasonal-to-interannual
    prediction; Phase-2 toward developing intraseasonal prediction.
    Bulletin of the American Meteorological Society 95(4):585-601. --
    NMME: the operational multi-model ensemble infrastructure and its
    verification practice (ACC, RMSE, ROC) for seasonal-to-interannual
    prediction of ENSO. -- Establishes the multi-model / dynamical context
    for honest "skill vs operational systems" claims; a CPU-only exact
    kernel method is positioned as complementary (evaluation practice and
    baseline numbers), not as competing infrastructure.

35. [web-verified] Ham, Y.-G., Kim, J.-H., Kim, E.-S., and On, K.-W.
    (2021). Unified deep learning model for El Nino/Southern Oscillation
    forecasts by incorporating seasonality in climate data. Science
    Bulletin 66(13):1358-1366. -- Follow-up to the Nature 2019 CNN (entry
    9): a unified convolutional network that explicitly encodes
    seasonality, improving Nino3.4 forecast skill across leads. -- A
    concrete post-2019 deep-learning ENSO forecast to cite as GPU-scale
    SOTA context; it reports no CPU or memory accounting anywhere (the
    contrast addressed by this project's G2 resource framing).

36. [web-verified] Zhou, L. and Zhang, R.-H. (2022). A hybrid neural
    network model for ENSO prediction in combination with principal
    oscillation pattern analyses. Advances in Atmospheric Sciences
    39:889-902. -- POP-Net: combines the linear principal-oscillation-
    pattern (POP) modes with a CNN-LSTM; reports skillful Nino3.4
    predictions up to ~17-month lead and alleviation of the spring
    predictability barrier. -- Representative hybrid statistics-DL ENSO
    forecast; with the still-more-recent combined dynamical-deep learning
    hybrid of Chen et al. 2025 (Nat. Commun. 16:3845; see References), it
    defines the hybrid context in which the project's exact-KRR index
    regression must show a clean, pre-registered significance story.

37. [web-verified] Webster, P. J. and Yang, S. (1992). Monsoon and ENSO:
    selectively interactive systems. Quarterly Journal of the Royal
    Meteorological Society 118(505):877-926. -- Canonical statement of the
    spring predictability barrier: forecast skill drops and errors grow
    fastest for predictions initialized across boreal spring in coupled
    models. -- Grounds the practical skill-ceiling claim: the hindcast
    protocol reports skill by start month and expects degraded
    spring-start skill; honest evaluation treats the barrier as a
    measured property, not a bug to hide.

### Gap C extension -- FFT / spectral-kernel KRR evaluation practices (entries 38-40)

38. [web-verified] Lazaro-Gredilla, M., Quinonero-Candela, J., Rasmussen,
    C. E., and Figueiras-Vidal, A. R. (2010). Sparse spectrum Gaussian
    process regression. Journal of Machine Learning Research 11:1865-1881.
    -- Spectral (random Fourier-basis) GP: learns a sparse set of spectral
    frequencies so inference scales with M basis functions instead of N,
    with wall-clock speedups reported against the full GP. -- Precedent
    for "spectral GP methods" in the FFT/spectral-kernel lineage, but it
    trades exactness for M << N; our block-circulant solve keeps the exact
    kernel (same spectral algebra, no basis truncation).

39. [web-verified] Le, Q., Sarlos, T., and Smola, A. (2013). Fastfood --
    computing Hilbert space expansions in loglinear time. ICML 2013, PMLR
    28:244-252. -- Structured random features: replaces dense random
    projection matrices with Hadamard-based constructions so RFF-style
    kernel expansions cost O(n log d) time and O(n) memory on CPU; reports
    ~2 orders of magnitude speedup and ~3 orders lower memory footprint.
    -- Evidence that CPU-only O(N log N)-class structured kernel
    computation is feasible at scale; the resource-accounting contrast
    for our exact FFT solve (same complexity class, no approximation
    error to trade).

40. [web-verified] Gardner, J. R., Pleiss, G., Weinberger, K. Q., Bindel,
    D., and Wilson, A. G. (2018). GPyTorch: blackbox matrix-matrix
    Gaussian process inference with GPU acceleration. NeurIPS 2018. --
    Structured-GP inference library: exact inference expressed as fast
    matrix-matrix operations, benchmarked (wall-clock) against
    approximate methods on standard regression datasets. -- The
    reporting-style precedent for structured kernel methods (exactness
    relative to a dense reference, explicit timing); the project adopts
    the same exactness-vs-approximation resource framing but on CPU with
    memory (peak RSS) and flop/byte accounting (G2).

### Iteration-3 cluster 1 (T1) -- boundary-aware / embedding-corrected fast
### kernel solves (entries 41-45)

41. [web-verified] Davies, R. B. and Harte, D. S. (1987). Tests for Hurst
    effect. Biometrika 74(1):95-101. -- Circulant-embedding origin: simulate
    a stationary Gaussian sequence exactly by embedding its Toeplitz
    covariance into a larger circulant and taking the FFT square root; the
    founding member of the Davies-Harte -> Wood-Chan [25] ->
    Dietrich-Newsam [5] lineage. -- For THIS iteration: proves the "embed
    the structured covariance and exploit the FFT exactly" pattern for
    *simulation*; the free-boundary BTTB *solve* case -- (K + lambda I)
    alpha = y without O(N^2)/O(N^3) -- is precisely the open cousin (G5)
    that RE-ABLRC targets, so the corpus cannot supply an existing exact
    free-boundary fast grid KRR solve.

42. [web-verified] Strang, G. (1986). A proposal for Toeplitz matrix
    calculations. Studies in Applied Mathematics 74(3):171-176. -- The
    founding circulant-preconditioner paper: approximate a Toeplitz matrix
    by the circulant copying its central diagonals so PCG on Toeplitz
    systems costs O(N log N) per iteration via FFT; T. Chan's optimal
    circulant [43] refines the choice. -- For THIS iteration: the
    literature-standard preconditioner family for Toeplitz/BTTB systems
    (G5/G7 baseline positioning): "standard PCG" on our masked Gram is
    conventionally preconditioned by a Strang/Chan-type circulant (or its
    BCCB spectral inverse); RE-ABLRC differs by correcting the boundary
    band of the embedded solve instead of merely approximating the whole
    matrix, and SSAM-CAM's >= 3x-speedup claim is measured against this
    standard.

43. [web-verified] Chan, T. F. (1988). An optimal circulant preconditioner
    for Toeplitz systems. SIAM Journal on Scientific and Statistical
    Computing 9(4):766-771. -- T. Chan's optimal circulant preconditioner
    minimizing ||C - A||_F over circulants; near-optimal PCG clustering for
    Toeplitz families. -- For THIS iteration: the canonical "which
    preconditioner" answer in the Toeplitz literature (G7 positioning):
    our PCG baselines and the iteration-2 FFT-preconditioned CG arm are
    instances of this family; the corpus supports no *exact* free-boundary
    alternative at O(N log N), which is the gap the low-rank boundary
    correction claims.

44. [web-verified] Chan, R. H.-F. and Jin, X.-Q. (2007). An Introduction
    to Iterative Toeplitz Solvers. SIAM. -- The standard monograph on
    iterative Toeplitz solvers: Strang/T. Chan/R. Chan circulant and BTTB
    (level-2) preconditioning, PCG convergence theory, including 2D
    block-Toeplitz cases. -- For THIS iteration: the comprehensive
    reference for the "standard PCG with circulant/BCCB preconditioner"
    baseline convention (G5/G7); it documents mature O(N log N)-per-
    iteration structured PCG but no exact free-boundary KRR solve -- the
    precise territory of RE-ABLRC (reflective embedding + boundary-banded
    low-rank Woodbury correction).

45. [web-verified] Martucci, S. A. (1994). Symmetric convolution and the
    discrete sine and cosine transforms. IEEE Transactions on Signal
    Processing 42(5):1038-1051. -- Symmetric convolution: mirror the
    signal at boundaries (whole-/half-sample symmetries) so DCT/DST
    diagonalize convolution with *non-periodic* (symmetric) boundary
    conditions -- the "boundary-aware spectral" alternative to the
    circulant/FFT torus. -- For THIS iteration: direct prior art for the
    boundary-correction component of RE-ABLRC (G5/G8): symmetric (DCT/DST)
    convolution is the established spectral treatment of reflective
    boundaries on finite grids, and the free-boundary gap reduction (>= 50%
    vs BCCB wrapping) can be cross-checked against the DCT/DST route; the
    DCT route still lacks an exact masked-KRR solve, keeping G5 open.

### Iteration-3 cluster 2 (T2) -- spectral-spatial alternating minimization
### for masked/partial observation (entries 46-52)

> Rework-r2 normalization footnote (honest-framing entry-range nit fix): the
> adopted corpus convention for the ADMM/FISTA family span is "entries
> 46-52" (the meta.json honest_framing convention), with entry 52 (Ng 2004,
> structured Toeplitz iterative methods) as the span-closing member; the
> iteration-3 plan's cluster label "entries 46-51" is superseded by this
> convention. The six-member splitting family proper (ADMM [46], FISTA
> [47], half-quadratic [48], plug-and-play priors [49], POCS [50], gappy
> POD [51]) is unchanged; "46-52" denotes the broader spectral-spatial /
> structured-solve span.

46. [web-verified] Boyd, S., Parikh, N., Chu, E., Peleato, B., and
    Eckstein, J. (2011). Distributed optimization and statistical learning
    via the alternating direction method of multipliers. Foundations and
    Trends in Machine Learning 3(1):1-122. -- ADMM canonical reference:
    operator splitting of composite objectives into separately proximal-
    able blocks (Douglas-Rachford lineage: Gabay 1983; Eckstein-Bertsekas
    1992); global convergence for convex problems; the standard framework
    for large-scale structured optimization. -- For THIS iteration: the
    toolbox anchor for SSAM-CAM (G6): alternating a spectral (FFT-
    accelerated kernel convolution) step and a spatial (masked-fidelity
    projection) step is an ADMM-type splitting; establishes that the
    *speed* of the alternation vs PCG at tol < 1e-6 is an empirical claim
    to pre-register (>= 3x), not a theorem to assert.

47. [web-verified] Beck, A. and Teboulle, M. (2009). A fast iterative
    shrinkage-thresholding algorithm for linear inverse problems. SIAM
    Journal on Imaging Sciences 2(1):183-202. -- FISTA: Nesterov-
    accelerated proximal gradient with O(1/k^2) convergence for composite
    convex problems; the canonical acceleration of ISTA used in
    deconvolution/inpainting. -- For THIS iteration: the acceleration
    family behind SSAM-CAM's "FISTA-type acceleration" (G6): momentum
    acceleration of splitting is established; the claim to make carefully
    is *circulant-accelerated Anderson mixing on the spectral residual* of
    a masked BCCB-KRR solve, which does not appear in this literature --
    the corpus-verified novelty target.

48. [web-verified] Geman, D. and Yang, C. (1995). Nonlinear image recovery
    with half-quadratic regularization. IEEE Transactions on Image
    Processing 4(7):932-946. -- Half-quadratic splitting: auxiliary
    variables convert non-quadratic regularizers into alternating
    quadratic (primal) / pointwise (auxiliary) updates; the classical
    splitting precursor of ADMM in image recovery. -- For THIS iteration:
    the lineage anchor for "half-quadratic splitting" (G6): the
    alternating primal/auxiliary pattern SSAM-CAM instantiates (spectral
    kernel step / masked spatial step); splitting itself is classical, so
    novelty must be claimed on the masked-BCCB-KRR instantiation with
    circulant-accelerated mixing, not on splitting per se.

49. [web-verified] Venkatakrishnan, S. V., Bouman, C. A., and Wohlberg,
    B. (2013). Plug-and-play priors for model based reconstruction. IEEE
    Global Conference on Signal and Information Processing (GlobalSIP
    2013). -- Plug-and-play priors: ADMM where the proximal step is
    replaced by an arbitrary denoiser/prior, decoupling forward model from
    prior. -- For THIS iteration: the "prior decoupled from the forward
    model" precedent (G6): in SSAM-CAM the spectral kernel plays the role
    of the prior and the mask plays the role of the forward model; the
    plug-and-play pattern justifies treating masked-fidelity projection
    and kernel step as interchangeable sub-blocks, positioning SSAM-CAM as
    a structured (exact-kernel, non-approximate) instance of the PnP
    paradigm.

50. [web-verified] Youla, D. C. and Webb, H. (1982). Image restoration by
    the method of convex projections: Part 1 -- theory. IEEE Transactions
    on Medical Imaging 1(2):81-94. -- POCS: alternating projections onto
    convex constraint sets (data-consistency, band/amplitude constraints)
    converge to a feasible point; the canonical projection machinery for
    partial-observation restoration. -- For THIS iteration: the spectral/
    spatial projection precedent for masked reconstruction (G6): POCS
    establishes projection-based alternation on partial observations; the
    honest distinction is that SSAM-CAM converges to the *regularized
    least-squares KRR solution*, not to an arbitrary feasible point -- a
    stronger but unproven-in-literature claim for our method to verify.

51. [web-verified] Everson, R. and Sirovich, L. (1995). Karhunen-Loeve
    procedure for gappy data. Journal of the Optical Society of America A
    12(8):1657-1664. -- Gappy POD: reconstruct missing (gappy) observations
    by alternatingly estimating a Karhunen-Loeve/POD basis from present
    data and filling the gaps from that basis; the canonical spectral-basis
    approach to masked-array reconstruction. -- For THIS iteration: the
    closest "spectral-domain masked reconstruction" relative of SSAM-CAM
    (G6): gappy POD alternates basis fitting and infilling exactly as our
    spectral-spatial alternation does, but on a data-derived POD basis
    rather than the fixed BCCB kernel eigenspace -- a fair prior-art
    comparison arm for the masked-reconstruction benchmarks (T1a/T1b).

### Iteration-3 cluster 3 (T3) -- low-rank + structured-Toeplitz corrections
### (entries 52-54)

52. [web-verified] Ng, M. K. (2004). Iterative Methods for Toeplitz
    Systems. Numerical Mathematics and Scientific Computation, Oxford
    University Press. -- Companion monograph to Chan-Jin [44]: iterative
    methods for Toeplitz and Toeplitz-like systems, circulant and level-2
    (BTTB) preconditioners, including fast solves with banded and low-rank
    modifications. -- For THIS iteration: the "structured Toeplitz +
    low-rank corrections" family anchor (G5/G6): establishes that
    structured solvers with low-rank perturbations are an established
    algorithmic category; what is NOT in the corpus is the *adaptive
    boundary-banded* low-rank correction of a free-boundary KRR solve at
    O(N log N) (RE-ABLRC) -- the proposal's precise claim.

53. [web-verified] Woodbury, M. A. (1950). Inverting modified matrices.
    Memorandum Report 42, Statistical Research Group, Princeton
    University. -- The Sherman-Morrison-Woodbury identity: (A + U C V)^{-1}
    via A^{-1} plus a low-rank correction; the canonical algebraic tool for
    inverting cheap-to-invert matrices under structured perturbations. --
    For THIS iteration: the algebraic backbone of RE-ABLRC (G5): the ridge
    solve (K + lambda I) is written as a circulant/embedding part plus a
    *boundary-banded low-rank correction*, so Woodbury yields the inverse
    in ~O(N log N) + rank-cost instead of O(N^3); the identity itself is
    classical (web-verified via the Google Books record), so the claim is
    the *boundary-band construction that keeps the correction low-rank* on
    regular grids.

54. [web-verified] Ambikasaran, S., Foreman-Mackey, D., Greengard, L.,
    Hogg, D. W., and O'Neil, M. (2016). Fast direct methods for Gaussian
    processes. IEEE Transactions on Pattern Analysis and Machine
    Intelligence 38(2):252-265. -- Hierarchically-semi-separable (HSS) /
    fast-multipole factorization of dense kernel matrices giving
    ~O(N log^2 N) *direct* (non-Krylov) CPU solves. -- For THIS iteration:
    the strongest existing "exact structured solve without iteration"
    alternative (G5 positioning): HSS exploits data-independent low-rank
    off-diagonal blocks of the dense kernel; RE-ABLRC exploits the
    circulant-on-grid structure instead; both are exact, non-randomized,
    CPU-only methods, so the benchmark should compare our method against
    this direct-structured line (and KISS-GP, entry 6) on accuracy and
    wall-clock.

### Iteration-3 cluster 4 (T4) -- non-stationary GRF simulation with
### controlled boundary conditions (entries 55-58)

55. [web-verified] Nychka, D., Furrer, R., Paige, J., and Sain, S. (2017).
    fields: Tools for spatial data. R package (CRAN). -- The standard R
    toolbox for spatial statistics (kriging, covariance estimation, GRF
    simulation); its sim.rf uses circulant embedding for FFT-based exact
    simulation of stationary fields on grids. -- For THIS iteration: the
    reproducibility anchor for the synthetic-field benchmark arm (G8):
    circulant-embedding GRF simulation is *packaged standard practice*
    (lineage entries 41, 25, 5); the added tooling our generator must
    provide -- boundary-value-constrained (Dirichlet/Neumann-type)
    generation and non-stationary range/variance fields -- is beyond what
    fields exposes natively, which is the G8 remainder.

56. [web-verified] Schlather, M., Malinowski, A., Menck, P. J., Oesting,
    M., and Strokorb, K. (2015). Analysis, simulation and prediction of
    multivariate random fields with package RandomFields. Journal of
    Statistical Software 63(8):1-25. -- RandomFields: the comprehensive R
    package for simulation/analysis of (multivariate, non-stationary)
    Gaussian and related fields using spectral/circulant methods; the
    reference tool for reproducible GRF benchmarks. -- For THIS iteration:
    the tooled counterpart of fields (G8): RandomFields is the standard
    sampler for non-stationary Matérn-family fields on grids and the
    natural cross-check for our 2D/3D non-stationary GRF generator; the
    controlled-boundary (free/Dirichlet/mixed) generation remains our
    tooling contribution.

57. [web-verified] Paciorek, C. J. and Schervish, M. J. (2006). Spatial
    modelling using a new class of nonstationary covariance functions.
    Environmetrics 17(5):483-506. -- Nonstationary covariance
    construction: locally-varying (kernel-convolved) Matérn-family
    covariances that preserve positive definiteness. -- For THIS
    iteration: the covariance-design anchor for the non-stationary
    synthetic fields (T4/G8): this is the standard construction for
    non-stationary GRFs with controlled parameters, and the definition of
    "non-stationary Gaussian random field" the benchmark protocol should
    cite.

58. [web-verified] Journel, A. G. and Huijbregts, C. J. (1978). Mining
    Geostatistics. Academic Press. -- The classic geostatistics monograph:
    kriging (BLUP) and *conditional simulation* -- generating fields that
    honor observed values at conditioning points; the statistical
    foundation of spatial interpolation and masked-field reconstruction. --
    For THIS iteration: the conditioning framework behind "controlled
    boundary conditions" (G8) and masked reconstruction (G6): conditional
    simulation on boundary/observed values is standard geostatistical
    practice (formalized by Stein, entry 19); our boundary-value-
    constrained GRF generation is this tradition applied to regular-grid
    kernel methods, and masked-cell prediction can be framed as
    conditioning on observed cells.

### Iteration-3 cluster 5 (T5) -- regular-grid infilling / spatial-regression
### benchmark tasks and metrics (entries 59-62)

59. [web-verified] Gneiting, T. and Raftery, A. E. (2007). Strictly proper
    scoring rules, prediction, and estimation. Journal of the American
    Statistical Association 102(477):359-378. -- CRPS and strictly proper
    scoring rules: CRPS generalizes MAE to probabilistic predictions and
    is strictly proper; standard metric for probabilistic forecasts,
    including coverage/interval-score conventions. -- For THIS iteration:
    the metrics anchor (G7): RMSE/MAE/CRPS/coverage on masked valid cells
    are evaluated per this convention; the iteration-2 conformal-coverage
    diagnostic aligns with the proper-scoring framework for calibrated
    intervals.

60. [web-verified] Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S.,
    Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J.,
    Schroeder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F.,
    and Dormann, C. F. (2017). Cross-validation strategies for data with
    temporal, spatial, hierarchical, or phylogenetic structure. Ecography
    40(8):913-929. -- The canonical leakage-safety reference: random splits
    overestimate skill under spatial/temporal autocorrelation; spatial-
    block / systematic CV protocols are the sound alternative. -- For THIS
    iteration: the direct citation for the benchmark's leakage-safe spatial
    train/test protocol (G7): train-interior / test-boundary-band splits
    and mask-held-out cell evaluation follow this convention (extending the
    iteration-2 temporal-block CV, entry 31, to the spatial axis).

61. [web-verified] Bertalmio, M., Sapiro, G., Caselles, V., and Ballester,
    C. (2000). Image inpainting. Proceedings of ACM SIGGRAPH 2000, 417-424.
    -- PDE-based image inpainting: propagate isophotes from the mask
    boundary into the missing region; the canonical image-infilling
    (masked-reconstruction) task. -- For THIS iteration: the image-
    inpainting analogue of grid infilling (G7): MNIST-784 random/row/band
    mask infilling in the benchmark is the regular-grid analogue of this
    canonical task; establishes that masked-region reconstruction quality
    (RMSE/MAE on valid cells vs ground truth) is the accepted evaluation
    convention in the inpainting literature.

62. [web-verified] Zimmerman, D., Pavlik, C., Ruggles, A., and Armstrong,
    M. P. (1999). An experimental comparison of ordinary and universal
    kriging and inverse distance weighting. Mathematical Geology
    31(4):375-390. -- The classic interpolator-comparison benchmark report:
    controlled simulation experiments comparing kriging variants vs IDW
    under known covariance and sampling design; the template for
    *experimental comparison* of spatial interpolators. -- For THIS
    iteration: benchmark-design precedent (G7): the multi-domain comparison
    (synthetic 2D/3D GRFs, MNIST grid infilling, Kaplan SST v2) follows
    this experimental-comparison convention -- controlled data-generating
    models, multiple domains, pre-registered metrics -- rather than
    leaderboard mining.

### Iteration-3 cluster 6 (T6) -- masked / partial-observation kernel methods
### (entries 63-65)

63. [web-verified] Candes, E. J. and Recht, B. (2009). Exact matrix
    completion via convex optimization. Foundations of Computational
    Mathematics 9(6):717-772. -- Matrix completion: recover a low-rank
    matrix from a subset of observed entries via nuclear-norm minimization;
    the modern theoretical foundation for masked-observation recovery. --
    For THIS iteration: the matrix-completion analog of masked KRR (G6):
    completion theory assumes low-rank structure, whereas masked BCCB-KRR
    keeps the *full-rank kernel* and masks only the training fidelity --
    the corpus contrast the proposal must state to position its novelty.

64. [web-verified] Zhu, X., Ghahramani, Z., and Lafferty, J. (2003).
    Semi-supervised learning using Gaussian fields and harmonic functions.
    Proceedings of the 20th International Conference on Machine Learning
    (ICML 2003), 912-919. -- Semi-supervised Gaussian fields: label
    propagation via harmonic functions on a graph Laplacian; the quadratic,
    closed-form analogue of masked regression on graphs. -- For THIS
    iteration: the semi-supervised-embedding relative of masked-input KRR
    (G6): masked-cell prediction from observed cells is the grid analogue
    of harmonic label propagation; positions our masked-reconstruction arms
    against a canonical semi-supervised method and justifies the "masked-
    inversion problem family" framing.

65. [web-verified] Cai, J.-F., Candes, E. J., and Shen, Z. (2010). A
    singular value thresholding algorithm for matrix completion. SIAM
    Journal on Optimization 20(4):1956-1982. -- SVT: iterative singular-
    value soft-thresholding for the nuclear-norm completion problem; the
    canonical first-order algorithm for masked low-rank recovery. -- For
    THIS iteration: algorithmic precedent for "spectral-domain masked
    inversion at scale" (G6): SVT shows masked recovery via spectral soft-
    thresholding is computationally viable; the contrast for SSAM-CAM is
    that we threshold/alternate in the *kernel eigenspace via FFT*
    (O(N log N)) rather than via SVD (heavy per-iteration cost), keeping
    exactness of the kernel Gram.

### Iteration-3 cluster 7 (extras) -- exact boundary Toeplitz solves and
### efficiency-benchmarking conventions (entries 66-69)

66. [web-verified] Trench, W. F. (1964). An algorithm for the inversion of
    finite Toeplitz matrices. Journal of the Society for Industrial and
    Applied Mathematics 12(3):515-522. -- Trench's O(N^2) exact inversion
    of symmetric Toeplitz matrices from the first column/row; the classical
    exact (non-iterative) Toeplitz solve predating FFT exploitation. -- For
    THIS iteration: the exact-solve reference point for the boundary
    problem (G5): exact free-boundary Toeplitz inversion exists without
    O(N^3) but costs O(N^2); on grids (BTTB) the exact route is not O(N
    log N), so "exact free-boundary fast grid kernel solves" remains open --
    the precise gap RE-ABLRC claims.

67. [web-verified] Gohberg, I. C. and Semencul, A. A. (1972). On the
    inversion of finite Toeplitz matrices and their continuous analogs (in
    Russian). Matematicheskie Issledovaniya 7(2):201-223. -- The
    Gohberg-Semencul formula: any Toeplitz inverse is representable from
    two solving vectors via displacement structure (with Trench 1964 the
    basis of exact fast Toeplitz solves, and of banded/low-rank Toeplitz
    update theory). -- For THIS iteration: with entry 66, establishes that
    the *exact* Toeplitz-solve theory is mature at O(N^2); the open problem
    is the BTTB grid generalization at O(N log N) with boundary control --
    the RE-ABLRC + Woodbury construction; web-verified via Trench's
    Trinity College paper page (URL in References).

68. [web-verified] Golub, G. H. and Van Loan, C. F. (2013). Matrix
    Computations, 4th edition. Johns Hopkins University Press. -- The
    canonical matrix-algorithms reference: flop counting, structured/
    blocked algorithms, Cholesky/LU costs, iterative-solver conditioning --
    the standard source for O(N^3)-vs-structured cost claims and flop/byte
    accounting. -- For THIS iteration: the efficiency-convention anchor
    (G7): all flop/byte estimates and the "no O(N^2) memory / no O(N^3)
    compute" budget follow Golub-Van Loan cost conventions; resource
    accounting (wall-clock / peak RSS / flops-bytes per accuracy point) is
    reported per this standard.

69. [web-verified] Barrett, R., Berry, M., Chan, T. F., Demmel, J., Donato,
    J. M., Dongarra, J., Eijkhout, V., Pozo, R., Romine, C., and van der
    Vorst, H. (1994). Templates for the Solution of Linear Systems:
    Building Blocks for Iterative Methods, 2nd edition. SIAM. -- The
    standard recipe/reporting conventions for iterative solvers: PCG
    variants, preconditioner selection, and the standard stopping criterion
    -- relative residual < tolerance (e.g., 1e-6 or 1e-8), with iteration
    counts and convergence curves as the comparison axes. -- For THIS
    iteration: the tolerance-based effort-comparison convention (G7): the
    pre-registered threshold (>= 3x speedup over standard PCG at equivalent
    residual tolerance < 1e-6) is measured exactly per Templates'
    residual-based stopping criterion; iterations-to-tolerance and
    wall-clock-at-tolerance are the comparison axes per this convention.

### Iteration-4 cluster 8 (rework r2) -- FAIL-feedback-informed structured-
### solve and embedding-PSD anchors (entries 70-74)

70. [web-verified] Graham, I. G., Kuo, F. Y., Nuyens, D., Scheichl, R., and
    Sloan, I. H. (2018). Analysis of circulant embedding methods for
    sampling stationary random fields. SIAM Journal on Numerical Analysis
    56(3):1871-1895. -- General-dimension circulant-embedding theory:
    conditions on the covariance (positive continuous Fourier transform via
    Bochner) that guarantee the extended block-circulant is positive
    semidefinite for a sufficiently large embedding domain, plus an
    a-posteriori bound for the error incurred when negative eigenvalues are
    floored. -- For THIS rework (r2): the PSD-conditions anchor for the
    Nexus note and F1: it supplies the general-d guarantee theory for the
    CIRCULANT-embedding lineage (entries 5, 25), the a-posteriori
    floor-error-control convention used when an embedding is not PSD (A1
    24^3 n_neg {289, 4578, 7662}), and the embedding-size dependence that
    motivates the whole-sample symmetric (DST2-class) exact boundary solve;
    no DCT/DST-class PSD condition is given there, so the 3D
    symmetric-embedding PSD question stays open.

71. [web-verified] Frangella, Z., Tropp, J. A., and Udell, M. (2023).
    Randomized Nystrom preconditioning. SIAM Journal on Matrix Analysis and
    Applications 44(2):553-594 (arXiv 2110.02820). -- Randomized low-rank
    (Nystrom) sketches of an SPD matrix as an algebraic preconditioner for
    PCG: iteration-count reduction with a tunable sketch size, including
    the regularized-system case (A + mu I). -- For THIS rework (r2): the
    masked-Gram preconditioner anchor for F2: the masked system
    (P_m K P_m^T + lambda I) w = y_m is an SPD regularized system, and a
    Nystrom sketch of the low-rank part of the masked Gram is the natural
    replacement for the identity/floored-torus preconditioner class that
    SSAM-CAM used at 0.16-0.24x median speedup; corpus precedent that
    preconditioned-Krylov rate, not masked-Gram equivalence, is where the
    iteration-3 S2 failure sits.

72. [web-verified] Barrowes, B. E., Teixeira, F. L., and Kong, J. A.
    (2001). Fast algorithm for matrix-vector multiply of asymmetric
    multilevel block-Toeplitz matrices in 3-D scattering. Microwave and
    Optical Technology Letters 31(1):28-32. -- Multilevel (3D)
    block-Toeplitz matrix-vector products at O(N log N) via FFT-based
    displacement/embedding structure for asymmetric block Toeplitz matrices
    in 3D electromagnetics. -- For THIS rework (r2): the 3D BTTB-machinery
    anchor for G5/F1: the 3D multilevel-block-Toeplitz matvec is O(N log N)
    (the iteration-2/3 PCG/BTTB matvec convention generalizes to 3D at the
    same cost), so the remaining 3D gap is in the SOLVE (boundary-corrected
    exact/fast solve), not the matvec.

73. [web-verified] Stewart, M. (2003). A superfast Toeplitz solver with
    improved numerical stability. SIAM Journal on Matrix Analysis and
    Applications 25(3):669-693. -- Displacement-rank superfast direct
    solver for positive-definite Toeplitz systems at ~O(n log^3 n) with
    improved stability over the classical superfast line. -- For THIS
    rework (r2): the exact-solve anchor for F1's "exact band solve instead
    of rank-limited Woodbury": between Trench 66 / Gohberg-Semencul 67
    (exact O(N^2) formulas) and the O(w(H+W)) approximate Woodbury
    (measured median corrected-residual plateau 532.2, i.e. ~1e2-1e3), a
    numerically stabilized superfast Toeplitz solve is the intermediate
    exact-1D-operator option for the boundary-band correction; the 2D/3D
    exact generalization remains open, keeping G5 open on grids.

74. [web-verified] Strang, G. (1999). The discrete cosine transform. SIAM
    Review 41(1):135-147. -- The DCT as the eigenbasis of symmetric
    reflection-boundary operators: which DCT/DST variants diagonalize which
    symmetric extension of a signal/filter, with the boundary-condition
    reading of each transform class. -- For THIS rework (r2): the
    symmetric-embedding PSD-condition anchor for the Nexus note: it explains
    why the DCT-I class diagonalizes whole-sample symmetric convolution
    (Martucci 45) and the boundary operators whose spectra are
    non-negative; the 3D non-PSD observation (24^3 n_neg 289-7662) is the
    empirical counterpart of this classical 1D spectral picture -- the
    corpus has no 3D DCT/DST-embedding PSD theorem, keeping the question
    open as an honest secondary finding.

## Identified gaps (motivated, primary for the project)

- G1 (PRIMARY, algorithmic): No consumer-hardware-exact kernel method for
  regular-grid climate fields. The scalable-kernel literature either
  randomizes (RFF/Nystrom/KISS-GP lose exactness) or assumes GPU/HPC
  (deep ENSO, WeatherBench). Circulant structure (Gray; Dietrich-Newsam)
  is proven to give EXACT O(N log N) structured computation, but no
  published CPU-only recipe turns it into exact KRR training + prediction
  on full-resolution climate grids with ridge handling and off-grid
  (index) prediction. This project's algorithm fills exactly this gap.
- G2 (METHODOLOGICAL): Resource accounting is not first-class. Accuracy
  is reported without wall-clock / peak-RSS / flop-and-byte cost per
  accuracy point in both the kernel-scaling and climate-ML literature.
  This project makes accuracy-per-flop and accuracy-per-byte explicit
  axes and benchmarks exact vs randomized baselines under a 7 GB / 12
  core / 90-minute budget.
- G3 (METHODOLOGICAL): Evaluation leakage in field reconstruction. Random
  point-wise splits leak spatial/temporal autocorrelation (standard
  practice in climate ML papers); block / leave-one-field-out CV is the
  statistically sound alternative (Stein; SPDE/GMRF tradition; block CV in
  ecology) but is rarely applied to kernel-method climate reconstruction.
  This project commits to honest block CV + calibration + applicability
  masking.
- G4 (ALGORITHMIC, secondary): Off-grid prediction from grid fields. ENSO
  index regression usually treats the index as a separate time series or
  uses approximation-heavy GPs. Circulant-block KRR with trigonometric
  interpolation provides exact, kernel-consistent off-grid predictions in
  O(N log N) -- an unstated capability this project demonstrates and
  quantifies.

## Gap Coverage (iteration 2)

Iteration 2 appended entries 26-40 (all web-verified in-session) to close
the three gaps routed from the hypothesis gate. How the corpus now
supports each claim:

(a) Leakage-verified evaluation protocol claims. Entries 26-28 supply the
    split-conformal machinery for non-exchangeable (temporally dependent)
    data: Barber et al. 2023 bounds the coverage gap beyond exchangeability;
    Chernozhukov et al. 2018 gives exact/robust conformal for dependent
    data; Gibbs-Candes ACI 2021 provides adaptive (rolling) calibration.
    Entries 29-31 supply the significance and protocol layer: Diebold-
    Mariano 1995 (HAC-based forecast-accuracy testing), Kunsch 1989 (block
    bootstrap; stationary variant Politis-Romano), Bergmeir-Benitez 2012
    (blocked / rolling-origin CV). Together with the existing entry set
    (block CV, leave-one-field-out, leakage, calibration) the corpus now
    supports a complete leakage-verified protocol: temporal-block CV inside
    training, a future-blind test window with seam/decay-phase checks,
    calendar-month-block conformal intervals, and a year-block-bootstrap DM
    win rule instead of naive monthly t-tests -- exactly the T1/T2/T3
    protocol in scripts/run_iters2.py and gap G3.

(b) Honest ENSO-forecast significance framing with pre-registered win
    rules. Entries 32-37 define the target and the baselines: Penland-
    Magorian 1993 (LIM; the canonical statistical baseline beyond
    persistence/climatology/AR(p)), Barnston et al. 2012 and Kirtman et al.
    2014 (field-standard ACC/RMSE-by-start-and-lead verification with
    3-month running-mean smoothing of the index, NMME multi-model
    context), Ham et al. 2021 and Zhou-Zhang 2022 (deep-
    learning and hybrid neural SOTA within 2018-2024, with the hybrid line
    continued by Chen et al. 2025 Nat. Commun.), and Webster-Yang 1992
    (spring predictability barrier). The corpus supports win rules stated
    before seeing test results: fixed leads h in {1,3,6,12}, fixed start
    months, ACC/RMSE vs persistence and climatology by lead, year-block
    bootstrap CIs on the MSE difference per win claim (executed version; a
    DM/HAC statistic was not computed at n=7 test blocks because the block
    count is too small for a HAC estimator -- the bootstrap CI on the
    block-resampled MSE difference is the significance test), DM statistics
    with year-block bootstrap p-values for each win claim, and an explicit
    degraded-skill expectation across the spring barrier -- a significance
    comparison for the T3 transfer forecast, not a leaderboard claim.

(c) FFT resource-accounting + real-data validation framing. Entries 38-40
    document how spectral/structured kernel work reports evaluation:
    Lazaro-Gredilla et al. 2010 (spectral/random-basis GP; exactness traded
    for M << N, wall-clock reported), Le et al. 2013 Fastfood (CPU-only
    O(n log d) structured random features with speedup/memory numbers), and
    Gardner et al. 2018 GPyTorch (structured exact inference benchmarked
    against approximate methods). We also consulted Yin et al. 2019, Sketch
    kernel ridge regression using circulant matrix (IEEE TNNLS 31(9):
    3512-3524; URL in References): the closest circulant-KRR sibling is an
    APPROXIMATE sketch on non-grid data, not an exact CPU solve on climate
    grids -- which sharpens G1 (exact block-circulant KRR on grids remains
    unpublished in our corpus) and G2 (none of the spectral/structured
    papers reports peak RSS or flop/byte cost). The framing our paper
    commits to: exactness vs dense reference, wall-clock (median-of-3),
    peak RSS, flops/bytes, real-data validation on the Kaplan SST v2 grid
    (36x72) plus synthetic O(N log N)/O(N) scaling measurements.

## Gap Coverage (iteration 3)

Iteration 3 appends entries 41-69 (all web-verified in-session) to close four
new gaps routed from iteration-2 review and this iteration's design brief
(ideas/iter3-design-brief.md). How the corpus now supports each claim, and
what remains open:

- G5 (exact free-boundary fast grid kernel solves; no O(N^2)/O(N^3)):
  Partially addressed by entries 41-45 (embedding lineage: Davies-Harte
  [41] -> Wood-Chan [25] -> Dietrich-Newsam [5]; circulant preconditioning
  theory: Strang [42], T. Chan [43], Chan-Jin [44]; symmetric/DCT-DST
  boundary-aware convolution: Martucci [45]), by entries 52-53 (Ng's
  structured Toeplitz iterative methods; Woodbury low-rank correction) and
  by the exact Toeplitz-solve references (Trench [66], Gohberg-Semencul
  [67]). REMAINS OPEN: the corpus supplies exact *embedding* for simulation
  and exact *Toeplitz* solves at O(N^2), and iterative (PCG) solves for
  free-boundary BTTB at O(N log N) per iteration, but no record provides an
  O(N log N), O(N)-memory *exact* solve of (K + lambda I) alpha = y for the
  free-boundary (BTTB) kernel on a regular grid with boundary control. The
  reflective-embedding + boundary-banded low-rank Woodbury correction
  (RE-ABLRC) in the iteration-3 design brief is precisely this missing
  piece; the corpus-supported novelty claim is the *integration* of
  reflective embedding (Martucci-type boundary handling), exact circulant
  spectral solve, and a boundary-banded low-rank correction whose rank is
  O(w x (H+W)) (kernel correlation width w), not the components themselves.

- G6 (masked-input fast solves): Partially addressed by the spectral-spatial
  alternating-minimization cluster (entries 46-51: ADMM/Douglas-Rachford
  [46], FISTA [47], half-quadratic splitting [48], plug-and-play priors
  [49], POCS [50], gappy POD [51]) and by the masked/partial-observation
  kernel-method family (entries 63-65: matrix completion [63], semi-
  supervised Gaussian fields [64], SVT [65]). REMAINS OPEN: all of these are
  *generic* masked-inversion or completion methods -- none applies
  alternating minimization to a grid-KRR problem whose spectral step is an
  exact BCCB (FFT) solve and whose spatial step is a masked-fidelity
  projection, with circulant-accelerated Anderson mixing on the spectral
  residual (SSAM-CAM in the design brief). The 3x-speedup-vs-PCG threshold at
  residual tol < 1e-6 therefore has no corpus precedent to cite as prior art
  -- it is a pre-registered empirical claim the proposal must defend, with
  entries 46-51 supplying the splitting/convergence conventions it builds on
  and entry 69 supplying the tolerance-based comparison convention.

- G7 (multi-domain regular-grid benchmark with pre-registered efficiency and
  boundary thresholds): Partially addressed by the benchmark/metrics cluster
  (entries 59-62: CRPS/proper scoring [59], leakage-safe spatial CV [60],
  image-inpainting analogue [61], interpolator-comparison convention [62])
  and by the efficiency conventions (Golub-Van Loan flop accounting [68],
  Templates residual-tolerance stopping [69]; iteration-2 entries 38-40 for
  spectral-kernel evaluation reporting). REMAINS OPEN: no corpus record
  benchmarks exact BCCB-KRR against dense exact KRR, standard PCG, KISS-GP,
  and RFF on synthetic 2D/3D non-stationary GRFs + a canonical grid-infilling
  task + real Kaplan SST v2 under a single pre-registered protocol with
  (>= 3x PCG speedup at tol < 1e-6) and (>= 50% free-boundary gap reduction
  vs BCCB wrapping) as explicit pass criteria. The benchmark architecture in
  the design brief (arms T1a/T1b/T2/T3, multi-domain table, metrics list) is
  the corpus-positioned novelty: a leakage-safe, resource-accounted exact-
  structured-KRR evaluation with pre-registered thresholds.

- G8 (boundary-controlled GRF simulation tooling for reproducible
  benchmarks): Partially addressed by the non-stationary/controlled GRF
  cluster (entries 55-58: fields [55], RandomFields [56], Paciorek-Schervish
  nonstationary covariance [57], Journel-Huijbregts conditional simulation
  [58]) plus the embedding lineage (entries 41, 25, 5). REMAINS OPEN: the
  corpus tools simulate stationary (or non-stationary) Gaussian fields on
  grids but do NOT expose reproducible *boundary-value-constrained*
  generation (free/Dirichlet/Neumann/mixed boundary conditions on regular
  grids) combined with missing-data masks; the design brief's synthetic-arm
  generators (2D/3D non-stationary GRFs with controlled boundary conditions,
  10/30/50% masks, seeds 0-19/0-9) are tooling this project must build and
  publish -- a methodology contribution, not a rediscovery of packaged
  simulation.

### Benchmark baseline positioning

For the pre-registered benchmark, each required baseline cites its
literature convention:

- Dense exact KRR: exact KRR via the dual solve (K + lambda I) alpha = y
  with dense Cholesky, O(N^3) flops and O(N^2) memory (entries 7, 16; flop
  convention entry 68). Applied at a subsample cap explicitly because the
  O(N^2) memory / O(N^3) solve is the class the project replaces (iteration-2
  execution notes; gap G5 positioning).
- Standard PCG for BTTB/Toeplitz systems: the literature standard is PCG
  preconditioned by a circulant/BCCB (Strang [42], T. Chan [43]) or an
  optimal-circulant/BTTB-level-2 preconditioner (Chan-Jin [44], Ng [52]),
  with relative-residual ~ tol < 1e-6/1e-8 stopping (Templates [69]); the
  iteration-2 masked arm used exactly this convention (spectral-inverse
  preconditioner + residual tolerance 1e-8, EXECUTION_NOTES item 3) and is
  the speed reference for the >= 3x SSAM-CAM claim.
- KISS-GP: structured kernel interpolation with inducing points +
  Kronecker/Toeplitz structure (entry 6); implemented on an inducing grid
  whose structured Gram is solved via the same circulant machinery, per the
  design brief's baseline convention.
- RFF: random Fourier features with Bochner-spectrum sampling (entry 1),
  CPU-accelerated via Fastfood-style structured features (entry 39), and
  quadrature interpretation (entry 17); Ridge on D-dimensional random
  features per Rahimi-Recht conventions, approximating the same kernel as
  the exact solver (honest approximation-error reporting per entries 2, 3,
  20-21).

## Gap Coverage (iteration 4 / rework r2, G9+)

Status banner (honest-framing invariant, non-negotiable): the iteration-3
proposal/experiment cycle (S1 RE-ABLRC + S2 SSAM-CAM; plan
ideas/experiments/experiment-plan-iter3.json; executed results/iter3/*.json)
FAILED its pre-registered win gates at the analysis gate and all its
measured artifacts are INVALIDATED HISTORY. Everything in this section is
therefore (a) an honest negative reported against the pre-registered label
table (win / NOT-validated / REFUTED / tie), never a qualifying claim, and
(b) the evidence base for the next hypothesis. Every numeric statement
below traces to results/iter3/*.json (executed artifacts; pooled blocks and
results/analysis/analysis-iter3.json numbers_pack) or to
results/iter2/*.json (canonical iteration-2 artifacts).

Gap restatements with FAIL-feedback evidence embedded:

- G5 (free-boundary fast grid solves) -- REMAINS OPEN, now with a measured
  boundary-correction plateau. Executed evidence (results/iter3/
  A1-boundary.json, pooled block): median free-boundary gap reduction of
  RE-ABLRC w_design vs BCCB wrapping = 47.3574 % on the 75-row w_design
  pool (< the pre-registered 50 % bar; first win clause FAILS); median
  corrected residual = 532.2245 (>> the 1e-6 acceptance cap; second clause
  FAILS); the correction rank budget |T| = O(w(H+W)) with pooled median
  T_size = 1233 is insufficient -- per-grid corrected-residual medians
  plateau at 546.2021 (64x64) and 415.7885 (128x128), i.e. ~1e2-1e3, never
  ~1e-6; the w-claimable guard (w <= min(H,W)/8, w_design = 10) holds only
  at 128x128 (16 >= 10) and fails at 64x64 (8 < 10) and 24^3 (3 < 10):
  guard {64_8: null, 128_16: true, 24_3: false}; 9 of 141 rows fail-fast
  (non-monotone w-sweep), all at 64x64 (matern32 seeds 7,9,13,14,18;
  matern52 seeds 13,14,18; rbf seed 9). Naive whole-sample symmetric (WSS)
  embedding alone reduces the pooled gap by a median 35.6448 % (pooled median naive residual 896.4332 -> corrected 532.2245) and at 24^3 by 69.7698 %, but the 24^3 cut is floor-limited (median naive residual 28456.9528) because the 3D WSS embedding is NOT PSD (Nexus note). The DST2-class symmetric-convolution comparator is the empirically superior classical boundary-aware class (pooled median gap reduction 61.62 %, 129/141 rows improve; DCT1 median -1872.63 %, 11/141 rows); the DCT/DST-capture consequence HOLDS (capture vs DST2 = 0.7467 on the 70-row positive-DST2 subset / 0.7284 all-75 robustness, both >= 50 %), so RE-ABLRC is NOT additionally disqualified by the consequence rule -- its NOT-validated label rests on the primary gates (gap 47.36 % < 50 %, residual 532.22 >> 1e-6, w-guard fails at 64x64 and 24^3). Corpus
  anchors for the rework: Martucci 45 (DCT/DST symmetric-convolution
  classes), Trench 66 and Gohberg-Semencul 67 (exact O(N)
  Toeplitz/Hankel inverse formulas) as the alternative to the approximate
  Woodbury correction, Ambikasaran HSS 54 as the 2D/3D structured
  re-seeding candidate, plus this-rework entries 70 (CEM PSD conditions,
  general dimension), 72 (3D multilevel block-Toeplitz matvec) and 73
  (stabilized superfast Toeplitz solve). Positive residue within the
  negative (A1 same-config pair at lambda 1e-3): naive -> w_design median
  residual drops 889.6065 -> 546.2021 (64x64) and 646.3849 -> 415.7885
  (128x128) -- the boundary correction helps, just not to <= 1e-6 at
  O(w(H+W)) rank.

- G6 (masked fast solves) -- REFUTED-verified; the gap REMAINS OPEN for a
  masked fast solve at a measured >= 1.5-3x speedup with equivalent
  residual tolerance. Executed evidence (results/iter3/A2-masked.json,
  pooled block + computed pools): median wall-clock speedup of SSAM-CAM vs
  PCG = 0.2374x (synthetic), 0.1560x (kaplan-sst-v2), 0.1624x (222-row
  wall-clock pool) -- strictly SLOWER under every pooling convention (<
  the 1.5x REFUTED bar); median KKT iterations 278.5 (SSAM-CAM) vs 192.0
  (PCG) at the same < 1e-6 convention; SSAM-CAM converged 77.7 % of runs
  vs PCG 100 % (22.3 % hit the 500-iteration ceiling: synthetic 39/150 --
  block 21, random_0.5 10, random_0.3 8; kaplan 24/132 -- polar 12, land
  12). RMSE parity HOLDS (kaplan median 0.3504163 vs 0.3504185; synthetic
  median absolute RMSE diff 1.73e-05) -- parity alone does not rescue the
  speed gate. A5 ablation (results/iter3/A5-ablation.json) makes Anderson
  mixing ESSENTIAL: without it the solver stalls at the 500-iteration
  ceiling with relative residual ~4.1e5-7.4e5; with it, 259-384 iterations
  to ~1e-6; RE-without-correction leaves relative residual 44.81-85.60
  (A5-scoped, lambda 1e-2, 128x128) -- the boundary correction's marginal
  value inside masked solves (not comparable to A1's lambda-1e-3 pool).
  The masked naive-embed solve is far from converged (median
  relative residual 117.43 on the 222-row pool) -- the naive masked
  spectral solve is not a candidate. Corpus anchors: the ADMM/FISTA
  splitting family entries 46-52 (splitting is measured essential but NOT
  sufficient -- Anderson mixing must be kept), entry 71 (randomized
  Nystrom preconditioning, this rework) as the masked-Gram
  preconditioner-class replacement candidate, entries 42-44/52
  (circulant/BTTB preconditioner lineage), entry 69 (tolerance-based
  comparison convention).

- G7 (multi-domain benchmark incl. real Kaplan SST v2) -- the executed
  4-domain x 5-method benchmark (grf-2d / grf-3d / mnist-784 / kaplan-sst-
  v2 x dense-KRR / standard-PCG / KISS-GP / RFF / RE-ABLRC+SSAM-CAM;
  results/iter3/A3-multidomain.json) stands as the first systematic such
  benchmark in the corpus with honest tie-reporting: KISS-GP wins 0
  domains and dense KRR wins 0 domains, so the benchmark is not-refuted
  under the pre-registered rule (REFUTED iff KISS-GP >= 2 or dense >= 1;
  ties reported). RE+SSAM ties dense/PCG within the 0.5 % analysis tieband
  on grf-2d (+0.47 %, at the threshold) and kaplan (~0 %); NOT within it
  on mnist-784 (+14.18 %) and grf-3d (+16.11 %); it converged only 14/66
  rows at the 500-iteration ceiling (grf-2d 3/18, grf-3d 0/2, mnist 0/10,
  kaplan 11/36); median speedup vs PCG per domain is 0.16-0.96x (slower).
  Dense-vs-PCG on grf-2d is classified a TIE under the identical-system
  justification (both solve the SAME masked-Gram system; relative RMSE
  delta 4.85e-07; dense 0.154 s vs PCG 1.714 s), with the disclosed
  sensitivity that a literal no-tieband reading gives dense_wins=1 and
  flips the verdict to REFUTED on grf-2d. Remaining weaknesses to close in
  the next cycle: grf-3d n=2 (plan seeds 0-9) and mnist n=10 (held-out
  digit scope) -- extend toward plan scope (A2 synthetic seeds 0-4 vs plan
  0-19; A3 grf-2d seeds 0-2 vs plan 0-19, grf-3d seeds 0-1 vs plan 0-9);
  the 222-row pooled pool and per-domain breakdowns must be stated in the
  paper text (pool disclosure below); the tieband aggregation convention
  must be written down in the next plan.

- G8 (boundary-controlled GRF tooling) -- CLOSED at the tooling level:
  scripts/grf_boundary.py self-check PASSED (results/iter3/A6-tooling.json
  selfcheck_pass = true; wall_selfcheck 0.0453 s; wall_mixed_boundary_36x
  72_sample 0.0043 s) with free / Dirichlet-zero / Neumann-zero / mixed
  boundary-value sets, whole-sample-symmetric circulant-embedding exact
  sampling, and the Paciorek-Schervish non-stationary covariance path
  (dense small-grid tool scope; no O(N log N) non-stationary claim).
  Documented as a deliverable of the negative-result study (G8 -> A6), not
  a kernel-solve claim.

Pool and convention disclosures (reviewer actionables folded in):

- 222-row pooled pool: A2 wall-clock pool = 222 of 282 rows -- 60
  synthetic block-mask rows (30 at 64x64, 30 at 128x128) carry no
  pcg/ssam wall_s in the artifact (nor re_naive, nor rmse_ssam_vs_pcg);
  every pooling convention is below the 1.5x REFUTED bar, so the verdict
  holds under all pooling choices.
- Tieband aggregation convention: per-domain median-RMSE ratio
  (re_ssam_median / best_median - 1), 0.5 % relative band; the 0.5 % band
  is an analysis operationalization of the plan's "ties reported" term
  (NOT a plan number); sensitivity appendix confines any verdict flip to
  grf-2d.
- Cost-clause parse: win is RMSE-first (tie within band or better RMSE),
  cost is a credibility gate (equal-or-lower cost envelope), ties reported;
  no cherry-picked exclusions.
- T1b citation lock: cite ONLY results/iter2/T1b-CG-masked-train.json
  (rate means 245.1/276.1/280.9 iterations at tol 1e-8, per-field span
  233-291, final relative residual 4.69e-9..9.81e-9, RMSE means
  0.529-0.541); EXECUTION_NOTES pre-fix figures (420-550 iters / RMSE
  0.78-0.83) are SUPERSEDED and never cited (marker added in this rework).
- Honest-framing entry-range nit (fixed): the corpus convention is
  "entries 46-52" for the ADMM/FISTA family span (meta.json
  honest_framing); the iteration-3 plan's "46-51" cluster label is
  superseded by this convention (footnote at cluster 2).
- Resource accounting (executed): total 2296.5 s (~38.3 min) within the
  90-min cap; peak RSS 0.9786 GB; A1 exceeded its 25-min per-arm cap
  (1530.3 s, flagged); three 24^3 dense-Cholesky reference attempts were
  OOM-killed by the ~2 GB container cgroup (A1 ref_attempts_log count 3),
  so the executed 24^3 reference is a CONTAINER-FORCED DEVIATION to
  PCG-tol-1e-8 (disclosed in A1 ref_convention_notes).

## FAIL-feedback-informed strategy families (for the next hypothesis)

Three concrete families, each with a corpus anchor and a falsifiable win
rule consistent with the win-rule-table conventions (boundary: residual <=
1e-6 AND gap >= 50 % AND w <= min(H,W)/8; masked: >= 1.5x speedup at
equivalent tolerance; benchmark: REFUTED iff KISS-GP >= 2 or dense >= 1
domains, ties reported):

- F1 -- DST2-embedding exact/mixed boundary solver (refined S1): replace
  the approximate boundary-banded Woodbury correction of the DCT-I-class
  WSS embedding with an exact DST2-class / Toeplitz-Hankel solve of the
  free-boundary operator's boundary system. Corpus anchors: Martucci 45
  (DST2 is the empirically superior symmetric class: pooled median gap
  reduction 61.62 %, 129/141 rows; 24^3 DST2 median 95.0644 %), Trench 66
  / Gohberg-Semencul 67 (exact O(N) Toeplitz/Hankel inverse formulas),
  Stewart 73 (superfast stabilized O(n log^3 n) Toeplitz solve),
  Ambikasaran HSS 54 (2D/3D structured direct solves as re-seeding
  candidate), Graham 70 (CEM PSD conditions + a-posteriori floor-error
  control, general dimension), Barrowes 72 (3D multilevel block-Toeplitz
  matvec at O(N log N)). Motive (measured): the O(w(H+W)) Woodbury rank
  plateaus the corrected residual at ~1e2-1e3 (pooled median 532.2;
  per-grid 546.2 / 415.8), so a residual <= 1e-6 gate requires an exact
  (or near-exact) band solve rather than a rank-limited low-rank
  correction; the w-claimable guard is then satisfied structurally (exact
  band solves have no rank budget to exhaust). Falsifiable win rule:
  S1' WIN iff median free-boundary gap reduction >= 50 % (2D+3D pooled)
  AND median reported residual bound <= 1e-6 AND w <= min(H,W)/8 AND >=
  50 % capture of the DST2 comparator's own gap reduction; REFUTED iff the
  exact band solve still leaves median residual > 1e-6 or the capture
  consequence fails; else NOT-validated (rank/scope exceeded). The 24^3
  dense-Cholesky reference is re-attempted (cgroup permitting) or the
  container-forced PCG-1e-8 deviation is re-disclosed per A1
  ref_convention_notes.

- F2 -- Masked-Gram acceleration via preconditioned Anderson mixing with a
  measured-tieband benchmark harness (refined S2): keep Anderson mixing
  (A5: ESSENTIAL, ablation-verified), replace the identity/floored-torus
  preconditioner class of the spectral step with a randomized-Nystrom /
  DST2-block / deflation preconditioner of the masked Gram (P_m K P_m^T +
  lambda I). Corpus anchors: Frangella-Tropp-Udell 71 (randomized Nystrom
  preconditioning of SPD/regularized systems -- the masked-Gram low-rank
  preconditioner class), ADMM/FISTA splitting family 46-52 (splitting
  retained as the outer loop), Strang 42 / T. Chan 43 / Chan-Jin 44 / Ng
  52 (circulant/BTTB preconditioner lineage), Templates 69
  (tolerance-based comparison convention). Motive (measured): SSAM-CAM is
  strictly slower under EVERY pooling convention (0.2374x / 0.1560x /
  0.1624x; iters 278.5 vs 192.0; convergence 77.7 % vs 100 %), so the
  failure is in the preconditioning/mixing RATE, not in masked-Gram
  equivalence (RMSE parity holds: 0.3504163 vs 0.3504185). Falsifiable win
  rule: S2' WIN iff median wall-clock speedup vs standard PCG >= 3x at
  equivalent KKT residual < 1e-6 (A2 pooled, RMSE parity on the T1b
  valid-cell domain); REFUTED iff < 1.5x; 1.5-3x reported NOT-validated as
  a tie-band case with the written tieband convention (ratio of per-domain
  medians; 0.5 % analysis band; sensitivity appendix confining verdict
  flips to grf-2d); the 222-row pool and per-domain breakdowns stated in
  the paper; grf-3d / mnist coverage extended toward plan seed scope.

- F3 -- Fallback repositioning: negative-result + tooling contribution: if
  F1/F2 fail their gates again, the deliverable is explicitly a
  negative-result study with tooling. Corpus/plan anchors: the reviewers'
  "defensible but below qualifying-positive bar" note (Significance 3); the
  pre-registered label table continues to govern claims. Headline positive
  outputs: A6 boundary-controlled GRF generator (G8 closed; selfcheck
  pass), A4 O(N log N)/O(N) scaling at N ~ 1e5 (320x320 embedding build
  0.0074 s / naive solve 0.0394 s; 48^3 build 0.0115 s / naive 0.0701 s),
  the Anderson-essential ablation (A5), the benchmark not-refuted with
  sensitivity (A3), and the 20-item honest-negatives list reported
  verbatim. Win rule: no positive win gate -- acceptance = completeness of
  the honest-negative reporting (all 20 negatives verbatim, pools
  disclosed, tieband convention written down, container-forced reference
  deviations disclosed) + tooling deliverables passing self-checks.

## Nexus note -- 3D WSS-embedding PSD question (empirical open problem)

Executed finding (results/iter3/A1-boundary.json
n_negative_eigenvalues_by_grid): the whole-sample symmetric (WSS,
DCT-I-class) embedding is NOT positive semidefinite in 3D on the tested
kernels at the tested ranges: 24^3 n_neg = {matern32: 289, matern52: 4578,
rbf: 7662}; 48^3 n_neg = {matern32: 0, matern52: 1468, rbf: 4222}. In 2D it
is nearly PSD (64x64: rbf 11, 128x128: rbf 3, 320x320: rbf 2; matern
kernels 0). Open question: for which kernel-range / grid-size ratios does
the symmetric (DCT/DST-class) embedding become PSD in d >= 3, and is the
critical ratio kernel- and dimension-dependent? Corpus anchors: Martucci
45 (symmetric-convolution DCT/DST classes), Strang 74 (DCT as eigenbasis
of symmetric-boundary operators), Graham 70 (CEM PSD conditions and
floor-error control in general dimension d), Dietrich-Newsam 5 and
Wood-Chan 25 (circulant-embedding PSD guarantees for simulation). The
corpus provides PSD conditions for the CIRCULANT embedding (entries 5, 25,
70) but no published PSD condition for the symmetric (DCT/DST) embedding
class in 3D -- the 24^3 289-7662-negative-eigenvalue observation is an
honest secondary finding of the negative study and a concrete open
benchmark problem for the next cycle; per entry 70, floored-spectrum
solves with an a-posteriori negative-eigenvalue error bound are the
accepted convention when the embedding is not PSD.

## Concepts (15-30 term index)

- Kernel ridge regression (KRR): ridge-regularized least squares in the
  reproducing-kernel-Hilbert-space dual form.
- Dual solution: KRR coefficients (alpha) solving (K + lambda I)a = y.
- Gram/kernel matrix: pairwise kernel evaluations over training points.
- Stationary kernel: k(x,x') = k(x - x'): translation-invariant.
- Matern kernel: stationary kernel with smoothness parameter nu; flexible
  spatial correlation.
- Squared-exponential / RBF kernel: infinitely smooth stationary kernel
  (Gaussian spectral density).
- Bochner's theorem: stationary kernels are Fourier transforms of
  positive measures (spectral densities).
- Spectral density: Fourier transform of a stationary covariance.
- Random Fourier Features (RFF): randomized trigonometric features
  sampling the spectral density (Monte Carlo kernel approximation).
- Nystrom approximation: low-rank kernel approximation via landmark
  (column) sampling.
- Landmark points: sampled subset spanning the Nystrom low-rank factor.
- Circulant matrix: Toeplitz matrix whose every row is a cyclic shift;
  diagonalized by the DFT matrix.
- Toeplitz matrix: constant-diagonal matrix; circulants are its cyclic
  relatives.
- Block-circulant matrix: 2D-grid stationary kernels yield nearly
  block-circulant Gram matrices on regular lattices.
- FFT / convolution theorem: cyclic convolution becomes pointwise product
  in Fourier domain; circulant solve via FFT is O(N log N).
- Circulant embedding: embedding a Toeplitz covariance into a larger
  circulant for exact FFT-based simulation/solve (Dietrich-Newsam).
- Kronecker structure: separable grid kernels factor into Kronecker
  products; combined with Toeplitz for fast multiplication (KISS-GP).
- KISS-GP: kernel interpolation for scalable structured GPs (inducing
  points + Kronecker/Toeplitz algebra).
- SPDE/GMRF: stochastic-partial-differential-equation link to sparse
  Gaussian Markov random fields for scalable spatial modeling.
- Kriging: best linear unbiased prediction in geostatistics; kernel
  regression's statistical cousin.
- Gaussian process regression: Bayesian kernel regression with
  predictive variance; O(N^3) exact, sparse variants for scale.
- SST anomaly field: sea-surface temperature minus climatology; the
  reconstruction substrate.
- EOF/PCA reconstruction: low-rank subspace (kernel-PCA-like) fitting of
  sparse SST observations (Kaplan et al.).
- ENSO / Nino3.4 index: area-averaged SST anomaly over 5N-5S, 120-170W;
  standard El Nino indicator (Trenberth).
- Block cross-validation: contiguous spatial/temporal block splits;
  leakage-aware evaluation.
- Leave-one-field-out CV: train on all fields but one, test on the held
  field (spatial block CV extreme).
- Leakage / autocorrelation: spatial/temporal correlation that random
  point splits exploit unfairly.
- Calibration: concordance between predictive intervals and empirical
  coverage (e.g., split-conformal).
- Applicability mask: per-input flag for where the model's error is
  trustworthy.
- Resource accounting: wall-clock, peak RSS, flop/byte cost as reported
  evaluation axes.
- Regular grid: uniform-lattice sampling (lat/lon grid cells); the
  structure our algorithm exploits.
- Conformal prediction: distribution-free prediction sets with
  finite-sample coverage under exchangeability; split-conformal is the
  standard construction (used for leakage-verified UQ here).
- Adaptive conformal inference (ACI): online re-estimation of the
  miscoverage level to maintain coverage under distribution shift
  (Gibbs-Candes); motivates rolling calibration windows.
- Diebold-Mariano test: HAC-variance significance test for equal
  forecast accuracy of two methods; the alternative to naive t-tests
  on per-period errors.
- Block bootstrap: resampling contiguous blocks to preserve dependence
  (moving-block, Kunsch; stationary variant, Politis-Romano; year-block
  variant used in this project's win rule).
- Rolling-origin / expanding-window hindcast: evaluation regime where
  training windows advance in time and forecasts verify out-of-sample
  at fixed leads, with seam/decay-phase leakage checks.
- Anomaly correlation coefficient (ACC): correlation between predicted
  and observed anomalies over hindcast cases; the standard ENSO skill
  axis (Barnston et al.).
- Persistence / climatology forecast: baselines predicting the current
  anomaly unchanged, or the monthly mean annual cycle (zero anomaly).
- Linear inverse model (LIM): linear Markov model fit to EOF
  coefficients for ENSO prediction (Penland-Magorian).
- Spring predictability barrier (SPB): ENSO forecast skill drop for
  spring-initialized forecasts (Webster-Yang).
- Spectral GP / sparse spectrum: Gaussian process using M random
  spectral basis functions; approximate with M << N (Lazaro-Gredilla
  et al.).
- Smoothing / running-mean smoothing: 3-month running-mean smoothing of
  the Nino3.4 index is the field convention for hindcast verification
  (Barnston et al. 2012).
- Circulant preconditioner: circulant C approximating a Toeplitz/BTTB
  matrix for PCG acceleration (Strang; T. Chan optimal circulant; Chan-Jin
  BTTB/level-2 theory, entries 42-44, 52).
- Symmetric convolution / DCT-DST boundary handling: mirroring the signal
  at boundaries so DCT/DST diagonalize non-periodic (symmetric) boundary
  convolution -- the reflective boundary analogue of circulant/FFT
  (Martucci, entry 45; central to RE-ABLRC's reflective embedding).
- Alternating direction method of multipliers (ADMM): operator splitting
  into separately proximal-able sub-blocks with a global convergence
  guarantee for convex objectives (Boyd et al., entry 46); the machinery
  behind SSAM-CAM's spectral/spatial alternation.
- FISTA / accelerated proximal gradient: Nesterov-momentum acceleration of
  ISTA with O(1/k^2) convergence for composite convex problems (Beck-
  Teboulle, entry 47).
- Half-quadratic splitting: auxiliary variables split non-quadratic
  regularizers into alternating quadratic/pointwise steps (Geman-Yang,
  entry 48); the classical precursor of ADMM-based image recovery.
- Plug-and-play priors: ADMM with an arbitrary denoiser as the proximal
  step, decoupling the forward model from the prior (Venkatakrishnan et
  al., entry 49).
- POCS / projection onto convex sets: alternating projections onto convex
  constraint sets for partial-observation restoration (Youla-Webb, entry
  50).
- Gappy data / gappy POD: masked-array reconstruction by alternatingly
  estimating a low-dimensional POD/KL basis and filling gaps (Everson-
  Sirovich, entry 51); the spectral-basis masked-reconstruction precedent.
- Woodbury identity: (A + U C V)^{-1} via A^{-1} plus a low-rank
  correction (Sherman-Morrison-Woodbury; entry 53); the algebraic backbone
  of RE-ABLRC's boundary-banded correction.
- Low-rank + structured-Toeplitz corrections: the Woodbury update family
  (entry 53) and HSS direct solves (entry 54); Low-rank corrections of
  circulant/Toeplitz embeddings are an established numerical category (Ng,
  entry 52), but a boundary-banded Low-rank correction targeting the KRR
  free-boundary solve at O(N log N) is not in the corpus (G5).
- HSS / fast direct structured solves: hierarchical-semi-separable
  factorization giving near-linear-time *direct* GP/kernel solves
  (Ambikasaran et al., entry 54); the exact-solve competitor family.
- Conditional simulation: generating fields that honor observed values at
  conditioning (boundary/observed) points (Journel-Huijbregts, entry 58);
  the geostatistical basis of boundary-constrained and masked-field
  generation.
- Non-stationary covariance / GRF: spatially-varying (kernel-convolved)
  Matérn-family covariances for non-stationary Gaussian random fields
  (Paciorek-Schervish, entry 57); the benchmark's non-stationary field
  generator basis.
- CRPS: continuous ranked probability score, a strictly proper scoring
  rule generalizing MAE to predictive distributions (Gneiting-Raftery,
  entry 59); the benchmark's probabilistic reconstruction metric.
- Spatial block cross-validation: spatial/temporal block CV as the
  leakage-safe alternative to random splits for autocorrelated fields
  (Roberts et al., entry 60).
- Image inpainting: propagating isophotes from the mask boundary into
  missing regions (Bertalmio et al., entry 61); the image analogue of grid
  infilling tasks.
- Matrix completion / nuclear norm: recovering a low-rank matrix from a
  subset of observed entries via nuclear-norm minimization (Candes-Recht,
  entry 63); the masked-inversion analog family.
- SVT: singular-value-thresholding algorithm for matrix completion
  (Cai-Candes-Shen, entry 65); spectral soft-thresholding precedent for
  masked inversion.
- Semi-supervised Gaussian fields: harmonic label/field propagation over a
  graph Laplacian with observed values clamped (Zhu-Ghahramani-Lafferty,
  entry 64); the masked-cell prediction analogue.
- Masking / masked-input solves: dropping the missing cells via a
  projection P_m so the training Gram becomes P_m K P_m^T (masking the
  fidelity to observed cells); the operator SSAM-CAM alternates the
  spectral (FFT) step against (entries 46-51, 64).
- Exact boundary Toeplitz solves: Trench (entry 66) and Gohberg-Semencul
  (entry 67) O(N^2) exact Toeplitz inversion via first-column/row or
  displacement structure; the "exact solve exists but is not O(N log N)
  on grids" reference points that RE-ABLRC improves upon.
- Residual-tolerance stopping: relative-residual < tol (e.g., 1e-6/1e-8)
  as the standard iterative-solver stopping and effort-comparison
  convention (Templates, entry 69; flop/byte counting per Golub-Van Loan,
  entry 68).

## Limitations of this review

- 61 of 74 entries are web-verified bibliographic records (title, authors,
  venue, year) confirmed in-session: 12 of the original 25, all 15
  iteration-2 entries (26-40), all 29 iteration-3 entries (41-69), and all
  5 iteration-4 entries (70-74). The remaining 13 (entries 13-25) are
  model-knowledge records not re-checked in-session. Specific
  bibliographic details (page numbers, volume/issue) for
  [model-knowledge] entries should be verified before submission if cited
  with those details. (One borderline flag: entry 67, Gohberg &
  Semencul 1972, was confirmed in-session via Trench's Trinity College
  bibliographic page, which cites the Mat. Issled. 7(2):201-223 record;
  the primary source is Russian-language, so the page-range detail relies
  on that secondary citation. Entry 71's page range (553-594) follows the
  SIMAX 44(2) record and its arXiv 2110.02820 companion.)
- No full-text reading of most entries occurred; annotations summarize
  relevance from knowledge of the literature, not from reading each PDF
  in this session.
- Web access was available and used for verification. Iteration 3 closed
  the boundary/masked-solve and benchmark-methodology gaps: entries 41-45
  (boundary-aware embedding/preconditioning), 46-51 (spectral-spatial
  alternating minimization), 52-54 (low-rank + structured-Toeplitz
  corrections), 55-58 (non-stationary GRF simulation with controlled
  boundaries), 59-62 (grid-infilling benchmarks and metrics), 63-65
  (masked/partial-observation kernel methods), 66-69 (exact boundary
  Toeplitz solves and efficiency conventions). Residual gaps are listed in
  the Gap Coverage (iteration 3) section. The corpus is still not
  exhaustive, and the "no public recipe" (G1) claim remains a claim about
  our corpus, not a universal negative.
- WeatherBench/NOAA data provenance is documented at the source; this
  review did not itself download or license-check the datasets.

## References used (URLs consulted in-session)

- http://www.gatsby.ucl.ac.uk/tea/tea_archive/attached_files/randomFeaturesRahimiRecht.pdf (Rahimi-Recht NIPS 2007 slides)
- https://www.research.ed.ac.uk/en/publications/using-the-nystr%C3%B6m-method-to-speed-up-kernel-machines (Williams-Seeger NIPS 2000)
- https://proceedings.mlr.press/v5/kumar09a/kumar09a.pdf (Drineas-Mahoney JMLR 2005 citation)
- https://www.cs.cmu.edu/~andrewgw (Wilson KISS-GP ICML 2015 listing)
- http://proceedings.mlr.press/v37/wilson15.pdf (KISS-GP ICML 2015 PDF)
- https://link.springer.com/chapter/10.1007/978-3-030-02825-1_8 (Dietrich-Newsam SIAM 1997 citation in Springer chapter)
- https://ee.stanford.edu/~gray/toeplitz.html (Gray Toeplitz/Circulant review)
- https://gaussianprocess.org/gpml (Rasmussen-Williams GPML)
- https://arxiv.org/pdf/2111.01084 (Lindgren-Rue-Lindstrom JRSS-B 2011 citation)
- https://ideas.repec.org/a/nat/nature/v573y2019i7775d10.1038_s41586-019-1559-7.html (Ham et al. Nature 2019)
- https://hero.epa.gov/reference/7713612 (WeatherBench JAMES 2020)
- https://ocp.ldeo.columbia.edu/res/div/ocp/pub/rainbow/paper2.pdf (Kaplan et al. JGR 1998)
- https://psl.noaa.gov/data/gridded/data.kaplan_sst.html (NOAA PSL Kaplan SST v2, dataset page)
- https://journals.ametsoc.org/doi/10.1175/1520-0477(1997)078%3C2771:TDOENO%3E2.0.CO;2 (Trenberth BAMS 1997)
- https://arxiv.org/abs/2202.13415 (Barber et al. 2023, conformal prediction beyond exchangeability; published Annals of Statistics 51(2):816-845)
- https://proceedings.mlr.press/v75/chernozhukov18a.html (Chernozhukov-Wuthrich-Zhu COLT 2018)
- https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html (Gibbs-Candes NeurIPS 2021 ACI)
- https://pkg.robjhyndman.com/forecast/reference/dm.test.html (Diebold-Mariano 1995 citation)
- https://projecteuclid.org/euclid.aos/1176347265 (Kunsch 1989 block bootstrap)
- https://cbergmeir.com/publications/2012-01-01_bergmeir2012use (Bergmeir-Benitez 2012)
- https://journals.ametsoc.org/abstract/journals/clim/6/6/1520-0442_1993_006_1067_ponsst_2_0_co_2.xml (Penland-Magorian 1993 LIM)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6936341 (Barnston et al. 2012 citation)
- https://www.chc.ucsb.edu/monitoring/nmme (Kirtman et al. 2014 NMME citation)
- https://scholar.google.com/citations?user=yLnlEqkAAAAJ&hl=en (Ham et al. 2021 Science Bulletin 66(13):1358-1366 listing)
- https://link.springer.com/article/10.1007/s00376-021-1368-4 (Zhou-Zhang 2022 POP-Net, Adv. Atmos. Sci. 39:889-902)
- https://www.nature.com/articles/s41467-025-59173-8 (Chen et al. 2025 combined dynamical-deep learning ENSO forecasts, Nat. Commun. 16:3845; consulted for Gap Coverage)
- https://www.climate.gov/news-features/blogs/enso/spring-predictability-barrier-we%E2%80%99d-rather-be-spring-break (Webster-Yang 1992 citation)
- https://quinonero.net/publications.html (Lazaro-Gredilla et al. JMLR 11:1865-1881 listing)
- https://proceedings.mlr.press/v28/le13.html (Le et al. Fastfood ICML 2013)
- https://arxiv.org/abs/1809.11165 (Gardner et al. GPyTorch NeurIPS 2018)
- https://pubmed.ncbi.nlm.nih.gov/31675347/ (Yin et al. 2019 sketch KRR via circulant matrix, IEEE TNNLS 31(9):3512-3524; consulted for Gap Coverage)

## References used (iteration-3 URLs consulted in-session)

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12110661/ (Davies-Harte 1987, Tests for Hurst effect, Biometrika 74(1):95-101; web-verified bibliographic record)
- https://onlinelibrary.wiley.com/doi/abs/10.1002/sapm1986742171 (Strang 1986, A proposal for Toeplitz matrix calculations, Studies in Applied Mathematics 74(3):171-176)
- https://epubs.siam.org/doi/10.1137/0909051 (Chan, T. F. 1988, An optimal circulant preconditioner for Toeplitz systems, SIAM J. Sci. Stat. Comput. 9(4):766-771)
- https://epubs.siam.org/doi/book/10.1137/1.9780898718850 (Chan, R. H.-F. and Jin, X.-Q. 2007, An Introduction to Iterative Toeplitz Solvers, SIAM)
- https://ui.adsabs.harvard.edu/abs/1994ITSP...42.1038M/abstract (Martucci 1994, Symmetric convolution and the discrete sine and cosine transforms, IEEE TSP 42(5):1038-1051)
- https://web.stanford.edu/~boyd/papers/admm_distr_stats.html (Boyd-Parikh-Chu-Peleato-Eckstein 2011, ADMM, FnTML 3(1):1-122)
- https://cseweb.ucsd.edu/classes/sp26/cse291C-b/Nesterov/FISTABeck.pdf (Beck-Teboulle 2009, FISTA, SIAM J. Imaging Sci. 2(1):183-202)
- https://pubmed.ncbi.nlm.nih.gov/18290044 (Geman-Yang 1995, Nonlinear image recovery with half-quadratic regularization, IEEE TIP 4(7):932-946)
- https://ieeexplore.ieee.org/document/6737044 (Venkatakrishnan-Bouman-Wohlberg 2013, Plug-and-play priors for model based reconstruction, IEEE GlobalSIP)
- https://www.scitepress.org/Papers/2020/89120/89120.pdf (Youla-Webb 1982, Image restoration by the method of convex projections, IEEE TMI 1(2):81-94; citation consulted)
- https://opg.optica.org/abstract.cfm?uri=josaa-12-8-1657 (Everson-Sirovich 1995, Karhunen-Loeve procedure for gappy data, JOSA A 12(8):1657-1664)
- https://books.google.com/books/about/Iterative_Methods_for_Toeplitz_Systems.html?id=o4I9TTWRE5OC (Ng 2004, Iterative Methods for Toeplitz Systems, Oxford University Press)
- https://books.google.com/books/about/Inverting_Modified_Matrices.html?id=_zAnzgEACAAJ (Woodbury 1950, Inverting modified matrices, Memorandum Report 42, Statistical Research Group, Princeton)
- https://arxiv.org/abs/1403.6015 (Ambikasaran-Foreman-Mackey-Greengard-Hogg-O'Neil 2016, Fast direct methods for Gaussian processes, IEEE TPAMI 38(2):252-265)
- https://cran.r-project.org/package=fields (Nychka-Furrer-Paige-Sain, fields: Tools for spatial data, R package)
- https://cran.r-project.org/package=RandomFields (Schlather et al., RandomFields, R package) — or the JSS companion below
- https://www.jstatsoft.org/v63/i08 (Schlather-Malinowski-Menck-Oesting-Strokorb 2015, Analysis, simulation and prediction of multivariate random fields with package RandomFields, JSS 63(8):1-25)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2157553 (Paciorek-Schervish 2006, Spatial modelling using a new class of nonstationary covariance functions, Environmetrics 17(5):483-506)
- https://books.google.com/books/about/Mining_Geostatistics.html?id=Id1GAAAAYAAJ (Journel-Huijbregts 1978, Mining Geostatistics, Academic Press)
- https://econpapers.repec.org/RePEc:bes:jnlasa:v:102:y:2007:p:359-378 (Gneiting-Raftery 2007, Strictly proper scoring rules, prediction, and estimation, JASA 102(477):359-378)
- https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881 (Roberts et al. 2017, Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure, Ecography 40(8):913-929)
- https://link.springer.com/rwe/10.1007/978-0-387-31439-6_249 (Bertalmio-Sapiro-Caselles-Ballester 2000, Image inpainting, ACM SIGGRAPH, 417-424)
- https://www.publichealth.columbia.edu/research/population-health-methods/kriging-interpolation (Zimmerman-Pavlik-Ruggles-Armstrong 1999, An experimental comparison of ordinary and universal kriging and inverse distance weighting, Math. Geol. 31(4):375-390 citation)
- https://doi.org/10.1007/s10208-009-9045-5 (Candes-Recht 2009, Exact matrix completion via convex optimization, FoCM 9(6):717-772)
- https://mlg.eng.cam.ac.uk/zoubin/ssl.html (Zhu-Ghahramani-Lafferty 2003, Semi-supervised learning using Gaussian fields and harmonic functions, ICML-2003, 912-919)
- https://researchportal.hkust.edu.hk/en/publications/a-singular-value-thresholding-algorithm-for-matrix-completion (Cai-Candes-Shen 2010, A singular value thresholding algorithm for matrix completion, SIAM J. Optim. 20(4):1956-1982)
- https://dl.acm.org/doi/abs/10.1145/321541.321549 (Trench 1964, An algorithm for the inversion of finite Toeplitz matrices, J. SIAM 12(3):515-522 citation)
- http://ramanujan.math.trinity.edu/wtrench/research/papers/TRENCH_GOHBERG_SEMENCUL.PDF (Gohberg-Semencul 1972, On the inversion of finite Toeplitz matrices and their continuous analogs, Mat. Issled. 7(2):201-223; bibliographic citation via Trench's paper)
- https://www.jstor.org/stable/24248458 (Golub-Van Loan 2013, Matrix Computations, 4th ed., Johns Hopkins University Press)
- https://www.cfm.brown.edu/faculty/gk/AM258/Handouts/templates.pdf (Barrett et al. 1994, Templates for the Solution of Linear Systems, SIAM, 2nd edition)
## References used (iteration-4 URLs consulted in-session)

- https://arxiv.org/abs/1710.00751 (Graham-Kuo-Nuyens-Scheichl-Sloan 2018,
  Analysis of circulant embedding methods for sampling stationary random
  fields, SIAM J. Numer. Anal. 56(3):1871-1895)
- https://arxiv.org/abs/2110.02820 (Frangella-Tropp-Udell 2023, Randomized
  Nystrom preconditioning, SIAM J. Matrix Anal. Appl. 44(2):553-594)
- https://tropp.caltech.edu/papers/FTU23-Randomized-Nystrom-SIMAX.pdf
  (publisher-page PDF consulted for the SIMAX 44(2) record of Frangella-
  Tropp-Udell 2023)
- https://www.semanticscholar.org/paper/1a58ecfb6e9a800fda5a9668fd3eac25dd8b68a1
  (Barrowes-Teixeira-Kong 2001, Fast algorithm for matrix-vector multiply
  of asymmetric multilevel block-Toeplitz matrices in 3-D scattering,
  Microwave Opt. Technol. Lett. 31(1):28-32)
- https://dl.acm.org/doi/abs/10.1137/S089547980241791X (Stewart 2003, A
  superfast Toeplitz solver with improved numerical stability, SIAM J.
  Matrix Anal. Appl. 25(3):669-693)
- https://dl.acm.org/doi/10.1137/S0036144598336745 (Strang 1999, The
  discrete cosine transform, SIAM Review 41(1):135-147)
