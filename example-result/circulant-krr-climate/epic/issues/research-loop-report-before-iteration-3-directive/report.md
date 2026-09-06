# Research-loop activity report - circulant-krr-climate, iterations 1-2 (before the iteration-3 directive)

**Scope.** Gathered orchestration files describing the research loop of the
`circulant-krr-climate` project from project start through the last recorded
event **strictly before** the iteration-3 directive comment
`20260902T0000-directive-iteration-3-novelty-upgrade.md` on the
orchestration-log. Per the request, that directive is **NOT included**; the
latest included file is
`orchestration-log/comments/20260901T0330-final-validator-clean.md`.
Everything dated 2026-09-02 or later (iteration 3 and iteration 4 material)
is excluded and appears only in the out-of-scope boundary note (Appendix B).

**Report date.** 2026-09-02 (UTC). **Prepared by:** issue manager of
`research-loop-report-before-iteration-3-directive` (tracker-only reporting
task; same instruction as sibling issue `iteration-1-research-loop-report`,
new cutoff).

**Correction stamp (2026-09-02, later same day).** The human added the loop's
DSH session logs to the issue directory; this report was then corrected to
metered token figures and revised human-intervention/boundary records
(sections 2.1, 2.3, 3, 4, Appendix C; full audit in `token-audit.md`).
The gathered-file inventory (Appendix A) is unchanged.

**Source corpus.** **84 thread files**, all timestamped < 2026-09-02T00:00:
the 51 iteration-1 files (identical set to the sibling report's Appendix A,
all <= 2026-08-31T17:32) plus 33 iteration-2 files (Appendix A here). The
manifest `project.json` and `EPIC.md` are living documents modified after
the cutoff; they are cited **only** for window-attributable entries (cost
ledger, interventions ledger, verdicts, iteration labels), flagged in
section 4.

---

## 1. The research loop - how the agent iterated

### 1.1 Iteration 1 recap (2026-08-31 13:38 - 17:32, ~3 h 54 min)

The first loop ran the 5-phase protocol end to end (scoping, control
validation, JIT stage dispatch, staging, synthesis) over the stage spine
literature_review -> hypothesis (3-round ideation loop, stop=pass) ->
experiment_planning -> experiment_execution (6 arms, 57.0 s, synthetic
[simulated] data) -> analysis (gate r1 FAIL 4/3/3 -> rework -> r2 PASS
4/4/4) -> paper_writeup (clarity gate PASS 4/4), finishing with
`validate_execution.py` Checks 1-11 ALL PASS, `final_verdict` APPROVE,
`project.json` status `synthesised`. Recurring pattern: dispatched-worker
stalls -> manager-executed inline fallback (literature, planning, execution
x2, analysis). Full narrative, token ledger and inventory: sibling report
`/workspace/epics/circulant-krr-climate/issues/iteration-1-research-loop-report/report.md`.
Iteration-1 [simulated] results remain as the iteration-2 benchmark.

### 1.2 Iteration-2 directive and kickoff (21:24 - 21:25)

- **21:24** orchestration-log `[directive: iteration-2]` (thread record;
  EPIC.md labels it "Iteration 2 (research-manager directive, 2026-08-31)" -
  session logs show the directive was a human message at 21:22:46Z phrased
  "As research manager, ..."; see section 3): iterate the project **back to the HYPOTHESIS IDEATION
  step**, targeting a **HIGHER-SIGNIFICANCE** result. Sanctioned constraint
  modification: REAL climate data now permitted - the Python-stack
  limitation is lifted for **data reading only** (h5py added via apt for
  netCDF-4/HDF5; CPU-only 12-core / ~7 GB / <= 90-min envelope unchanged).
  Real-data target: NOAA PSL Kaplan SST v2 monthly anomalies (5-deg 72x36).
- **21:25** ideation seeded (hypothesis-ideation-r2): 3-component loop
  (Problem/Method/Experiment Design), 2 reviewers per round, median
  aggregation, stop conditions pass/cap/plateau, max 3 rounds. Real data
  live at `results/raw/real/` (2005 months; Nino3.4 index validated vs
  1982/83-2015/16 ENSO events).

### 1.3 Iteration-2 ideation r2 (21:25 - 21:34, ~9 min): cap-stop

Proposal triple -> critique -> revision rounds; stop on **cap** (round 3 of
3), not pass:

- **v1 (21:27).** Problem: does exact torus spectral KRR on REAL Kaplan SST
  v2 (a) reconstruct masked real fields with calibrated conformal intervals
  and (b) forecast the real Nino3.4 index at h=1..12 vs
  persistence/climatology/AR(1) under future-blind holdout. Method: torus
  spectral KRR unchanged (exact BCCB closed-form solve, spectral floor,
  exact free-boundary PCG matvec) + kernel-consistent box functional + NEW
  honestly-scoped frequency-domain transfer forecast arm. Design: P0/T1a/
  T1b/T2 + new T3 + B on real pool + S; future-blind holdout
  (train <= 2015-12, test 2016-2022) + temporal-block CV.
- **v2 (21:28).** Folded round-1 feedback: explicit no-SOTA-ENSO-skill
  ceiling; one consistent spectral functional operator (box mean = spectral
  inner product, Parseval/linearity); leak control normative (all fits on
  train, rolling-origin evaluation, spatial-only circulant wrap, no temporal
  seam crossing; 2015/16 El Nino confined to test verified); conformal
  acknowledged as non-exchangeable (rolling-origin calibration, coverage
  DIAGNOSTIC); Kaplan mask regime mirrored train/test; metrics incl.
  Diebold-Mariano year-block bootstrap; per-arm worst-case budgets (< 90
  min; T3 ~0.1 s FFT-only; B ~6 s n=10k).
- **v3 (21:31, cap round).** Folded round-2 feedback with six deltas:
  h in {1,3,6,12} = T3 set ONLY; calendar-month-block conformal with
  calibration blocks strictly after and non-overlapping with H_h training
  blocks (calibration-leak independence explicit), coverage per mask/fold +
  mean width; **factual correction**: 2015/16 El Nino PEAK (Dec 2015) is
  INSIDE the train window - only the decaying phase is test-side; added
  decay-phase confound sensitivity (2016 exclusion); mirrored-mask
  construction concretized (ocean cells only, defined once for the whole
  run); seam-leakage sensitivity (h=1 under 2015-excluded vs retained);
  wall-clock protocol (median of 3 after warm-up; worst-case max for budget;
  total < 90 s CPU, peak RSS << 7 GB).
- **Critique (21:33), ideation r3:** Clarity 4, Relevance 4, Originality 3
  (conservative lower-middle), Feasibility 4, Significance 4 - **not pass**
  (Originality below bar); revision feedback adopted at plan level.
- **Manager notice (21:34):** loop terminated on the round cap (3/3); the
  failing criterion set narrowed to Originality (3) in the last round, so no
  plateau; **cap** stop recorded; best proposal = v3;
  `ideas/proposal-final.json` (iteration 2) written from v3; iteration-1
  final archived under `ideas/archive/`. Hypothesis gate next.

### 1.4 Hypothesis gate: FAIL x2 -> routing (21:37 - 21:50)

- **Gate r1 (21:37):** aggregate Significance **3**, Originality **2**
  (median, two reviewers) -> **FAIL**, below threshold. Seven revision items
  (pre-registered forecast win criteria with bootstrap CI; conformal adapted
  to non-exchangeable seasonal/autocorrelated residuals with explicit
  tolerances; non-spectral Cholesky control arm on the same data;
  grid-resolution sensitivity + ENSO floor; data pinning + rerunnability;
  real-data threat plan; numeric seam checks with truncation sweep).
- **Rework (21:38 - 21:39, hypothesis-rework-r1):** seeded-fail-feedback
  posted; proposal-v4 closed all seven items: pre-registered support
  semantics (supported iff beats persistence AND climatology AND AR(1) in
  RMSE AND skill AND margin > year-block bootstrap 95% CI; refuted if fails
  on > half the horizons; no post-hoc reinterpretation); calendar-month-
  block conformal with 0.90 +/- 0.06 tolerance bands per seam/decay subset;
  Cholesky control (n in {2k,5k}) with accuracy-per-flop/per-byte ratios;
  5-deg scope + ENSO floor as discussion; data pinned (Kaplan v2, Sep-2014
  conversion attr, h5py path) + seeds + per-arm resources; threats
  (Kaplan smoothing, ocean-only masks, PCG failure-mode plan - stall > 10x
  tol -> relaxed-tol marker, never silent drop); numeric seam checks
  (Dec-Jan boundary split; truncation cutoffs 2014-12/2013-12/2012-12;
  2015-excluded vs retained with fixed test window). Artifact
  `ideas/proposal-it2-v4.json`; `proposal-final.json` re-pointed to v4.
- **Gate r2 (21:50):** aggregate Significance **3**, Originality **3**
  (lower-middle) -> **FAIL**; the hypothesis gate loop budget (2 configured
  loops = 2/2) is **exhausted**.
- **Routing (21:50):** `[directive: iteration-2-routing]` +
  `[manager-notice: gate-routing]` - manager-authoritative route_for_failure:
  hypothesis FAIL -> **literature_review** for corpus strengthening
  (leakage-verified evaluation protocols, ENSO forecast baselines/SOTA,
  FFT-kernel evaluation practices), then hypothesis re-entry. Whole-stage
  invalidation vacuous (no downstream stage issues exist; JIT). Verdict
  history and ideation records preserved as audit; **no block raised**
  (route target exists, feedback actionable). `literature-review-rework-r1`
  opened + seeded.

### 1.5 Literature grounding rework (21:50 - 22:32, ~42 min)

Three corpus gaps seeded: (1) leakage-verified evaluation protocols
(non-exchangeable split-conformal, temporal-block/rolling-origin
calibration, year-block/moving-block bootstrap, seam/decay checks); (2)
ENSO (Nino3.4) forecasting SOTA and standard hindcast evaluation; (3)
FFT/spectral kernel KRR evaluation practices. Also seeded with the gate r2
critique items (a)-(f).

**Resolved 22:32** (manager-verified): `docs/literature-review/review.md`
extended with **15 new annotated entries 26-40, all web-verified in-session**
(Gap A: Barber 2023, Chernozhukov 2018, Gibbs-Candes ACI 2021,
Diebold-Mariano 1995, Kunsch 1989 block bootstrap, Bergmeir-Benitez 2012
rolling-origin; Gap B: Penland-Magorian LIM 1993, Barnston 2012 + Kirtman
2014 NMME verification standards, Ham 2021 + Zhou-Zhang 2022 + Chen 2025 ML
ENSO, Webster-Yang 1992 spring barrier; Gap C: Lazaro-Gredida 2010, Le 2013
Fastfood, Gardner 2018 GPyTorch, Yin et al. 2019 circulant-KRR sketch -
sharpens G1 as exact-CPU-on-grids-unpublished). `ideas/concept-index.json`
rebuilt: **492 entities (was 281), 120,786 co-occurrences (was 39,340)**,
ENSO now top-2 term. "Gap Coverage (iteration 2)" section added (LIM ~0.5 C
RMS @ 9-month lead as baseline bar; ~6-month useful skill ceiling;
spring-barrier expectation). Workspace commit 53b1e8b.

### 1.6 Ideation r3 re-entry + hypothesis gate PASS (22:40 - 00:05, ~1 h 25 min)

- **22:40** seeded (enriched corpus + critique items a-f + executed
  real-data results `results/iter2/*`). **22:42** v1 grounded in executed
  data (T2 functional 3.2x better than direct head; T1a RMSE 0.082-0.088;
  T3 no-overclaim negatives; 108 s / 1.55 GB).
- **23:10** ideation critique r1: Clarity 4 / Relevance 4 / Originality 4 /
  Feasibility 5 / Significance 4 -> **ideation PASS**; seven revision items
  folded into the gate revision, including a **reviewer-found bug**: the T3
  year-block bootstrap was **VACUOUS in the executed artifact** (every CI
  half-width 0.0 - calendar-year mapping bug collapsed all test months to
  one block/year 1805); fixed in the runner (true calendar years 2016-2022,
  7 blocks, 2000 draws) and re-executed. Also: exactness re-scoped
  (EXACT = torus-embedded kernel only; free gap 0.95 matern32 / 0.12 rbf
  disclosed); coverage acceptance per-mask with violation disclosure
  (matern32 halo_w4 decay 0.739 / seam 0.836; rbf halo_w2 global 0.816);
  spring-barrier evidence arm (origin-month-9 h12 skill -0.96, origin-5 h6
  -0.44 vs origin-3 h3 +0.84 - boreal-spring-cross degradation evidenced);
  S-scaling contradiction fixed (~0.04 GB single 0.25-deg field); budget
  amortization (Nystrom-5000 ~46 s dominates B).
- **23:25** proposal-it3-v2 (gate revision) executed the fixes: title
  re-scoped to torus-embedded exact spectral KRR with gap disclosure;
  bootstrap fixed (se 0.007-0.333, real CIs, n_blocks/n_resamples
  reported); **resolution sensitivity executed** (native 5-deg recon 0.0853
  / functional 0.0856 corr 0.997 vs 10-deg coarsened 0.1667 / 0.3825 corr
  0.950); **apples-to-apples flop/byte ratio executed** (spectral pooled
  RMSE 0.0828 on the same 2000 valid test cells vs ridge 1.25-1.34 / Nystrom
  1.24 / RFF 1.73; 5e4-1.6e6x fewer flops; ~5 orders of magnitude better
  accuracy-per-flop); full pipeline re-run: 77.8 s / 1.55 GB.
- **23:45** hypothesis gate r1 critique: both reviewers Significance 4 /
  Originality 4 -> **PASS**; nine folded items, including: T3 verdict
  **REFUTED (0/4 supported)** under the pre-registered semantics, stated as
  an aggregate; h=6 qualified (RMSE 0.796 vs persistence 0.907 but year-block
  bootstrap p=0.234, CI crosses 0; transfer loses to AR(1) at every horizon
  and to climatology at h>=6); bootstrap_meta {n_blocks 7, n_resamples
  2000, seed 7}; win rule relabeled bootstrap-CI (no DM statistic);
  T2 scope note (CV method comparison over all 2005 months, NOT a
  future-blind forecast claim); test-window field std 0.6001 + per-kernel
  RMSE ranges; 10-deg coarsening foregrounded as honest negative; resources
  reconciled (77.8 s, not 108 s); spring-barrier claim reworded to
  evidence-based origin-dependence; **B-arm pooled-cell decode bug found and
  fixed** (position-in-valid-list used as flat cell index, biasing ~53% of
  test cells to missing cells; re-executed; trivial parity baselines added).
- **00:05** manager notice: hypothesis gate **PASS** (median 4/4) on
  proposal-it3-v3; ideation issue resolved; route: experiment_planning
  (plan approved and reconciled) -> experiment_execution
  (artifacts results/iter2/*, re-verified) -> analysis -> writeup.

### 1.7 Experiment execution verification (00:20)

Manager verified the iteration-2 REAL-data execution against the approved
plan: `results/iter2/{P0-pilot-gate-real, T1a-spectral-reconstruction,
T1b-CG-masked-train, T2-ENSO-index, T3-forecast-transfer, B-baselines,
S-scaling, RESOLUTION-AND-RATIOS, TRIVIAL-BASELINES, missing_mask,
paper_content, results_summary}.json`; `dataset.origin
real-kaplan-sst-v2` with **no simulation marker** in every artifact;
future-blind train 1856-01..2015-12 / test 2016-01..2022-12 (84 months;
2023-01 excluded from both); sentinel-aware loader (NCAR -9.96921e36;
53.4% missing incl. 100% polar caps; valid-only evaluation); torus-exactness
gate 2.62e-12 rel with free-gap disclosed (0.95 matern32 / 0.12 rbf);
per-kernel calendar-month conformal with disclosed violations (acceptance
per mask); T3 year-block bootstrap non-degenerate (se 0.007-0.333, n_blocks
7, n_resamples 2000, seed 7) with aggregate verdict **REFUTED (0/4)**
stated honestly; start-month x lead skill tables; truncation sweep stable
(skill 0.8795-0.8797); resolution sensitivity as honest negative;
apples-to-apples flop/byte ratio on the same 2000 valid cells (spectral
0.0999 vs ridge/Nystrom/RFF 0.82; 5e4-1.6e6x fewer flops) with trivial
parity baselines; resources **77.8 s wall, 1.57 GB peak, CPU-only**. Full
pipeline re-executed after the reviewer-found B-arm decode fix. Workspace
commits 53b1e8b..cf2b47a.

### 1.8 Analysis gate (00:45): PASS

Aggregated critique r1: reviewer A {Quality 4, Significance 5, Originality
5}, reviewer B {4, 4, 4} -> median **4/4/4 PASS**; both reviewers verified
headline-claim traceability and leakage safety (future-blind splits,
temporal-block CV, train-only conformal calibration, year-block bootstrap).
Folded fixes: resources to artifact values (**78.7 s / 1.57 GB** -
reconciled figure); per-method flop/accuracy-per-flop ratios (ridge
5.3e4-7.5e5x / 5.6-6.8 orders, Nystrom 1.6e6x / ~7.1 orders, RFF 4.8e2x /
~3.6 orders) with solve-cost-control scoping; T3 bootstrap se range full
(0.0056-0.333); per-horizon `not_supported` tags + aggregate REFUTED
semantics; month accounting explicit (2005 = 1920+84+1; 2023-01 excluded);
P0 free-boundary caveat (torus-exact solve is NOT the free-boundary result);
per-lead origin-dependence (Jan best h=1; Apr strongest h>=3; Oct worst);
review.md Gap Coverage (b) aligned with the executed bootstrap-CI win rule
(no DM/HAC at n=7 blocks). Writeup stage opens.

### 1.9 Writeup with gate rework (01:00 - 02:00)

- **01:00** writeup stage entry (iteration 2): the rewrite REPLACES the
  iteration-1 simulated paper with the real-data study; brief
  `paper/iter2-writeup-brief.md`, digest `results/iter2/paper_content.json`;
  **worker dispatched** (`paper_writing_subagent_id` recorded). Acceptance:
  4-page PDF, real-data abstract, honest negatives (T3 REFUTED 0/4,
  per-mask coverage violations, 10-deg degradation, torus-vs-free gap
  0.95/0.12), resource axes (78.7 s / 1.57 GB), main.bib extended with
  web-verified corpus references; writeup gate (2 reviewers, Clarity) then
  finalization.
- **01:50** gate r1: Clarity 3/3 -> **FAIL**; both reviewers verified number
  traceability and honest framing; twelve revision items: (1) MATERIAL:
  "every origin negative at h=12" contradicted by the paper's own table and
  artifact (April h=12 skill +0.059) - reword; (2) pseudo-numbered Eq. (3);
  (3) Table 4 overfull by 52.7 pt; (4) underfull vbox (main.tex:207);
  (5) define halo mask + seam/decay subsets; (6) spell out BCCB/BTTB/PCG/
  HAC/ACI/U at first use; (7) define acc/flop column direction/base; (8)
  month-index accounting explicit (index 0 = 1856-01); (9) Fig 2 caption
  scope; (10) T1b residual range precise (4.69e-9..9.78e-9); (11) halo
  coverage phrasing (0.739-0.852 all-halo span); (12) ~0.04 GB = ~5 working
  arrays (one field = 8.3 MB).
- **02:00** gate r2: two FRESH reviewers, Clarity 4/4 -> **PASS**; all 12
  fixes verified; 0 Overfull/Underfull in full-verbosity rebuild; body
  exactly 4 pages + References on p5; all 30 references render; cosmetic
  nits folded by the manager directly (commit 34bc2cb). Finalization next.

### 1.10 Finalization (03:30)

`orchestration-log/comments/20260901T0330-final-validator-clean.md`:
`validate_execution.py` Checks 1-11 ALL PASS on the iteration-2 manifest
(status synthesised; `final_verdict` APPROVE; deliverable_path absolute;
all research issues terminal; writeup gate r1 FAIL + r2 PASS recorded with
matching [review-critique] comments; hypothesis/analysis gates recorded;
costs ledged for every resolved issue incl. the "iteration-3 ideation"
label; interventions ledger mirrors the [directive: ...] comments; ideation
stop condition recorded). This is the last included file; the iteration-3
directive follows next morning at 2026-09-02T00:00 (excluded).

### 1.11 Iteration pattern + duration

**Pattern:** the loop is manager-orchestrated and fully autonomous within
this window (see section 3). A research-manager directive re-entered the
spine at hypothesis ideation for a higher-significance real-data result;
the ideation loop stopped on **cap** (failing criterion narrowed, no
plateau) and the best proposal was gated; the hypothesis gate FAILED twice
(loop budget 2/2) and was **routed upstream to literature_review** for
corpus strengthening, then re-entered with a fresh budget and PASSED;
reviewers repeatedly found real bugs in executed artifacts (vacuous
bootstrap via calendar-year mapping; B-arm pooled decode bias) which were
fixed in the runner and re-executed before gating; the writeup gate failed
r1 on Clarity 3/3 and passed r2 4/4 after 12 fixes with fresh reviewers.
Risks were surfaced as honest negatives (T3 REFUTED 0/4 under
pre-registered rules, coverage violations, 10-deg degradation, torus-vs-free
gap) and every claim traced to artifact keys.

**Duration:** window starts at the first recorded orchestration event
13:38 on 2026-08-31 (iteration 1) and ends at the last included comment
03:30 on 2026-09-01 = **13 h 52 min** total. Iteration 2 alone: directive
21:24 (08-31) -> finalizer 03:30 (09-01) = **~6 h 6 min**, with sub-spans:
ideation r2 ~9 min (21:25-21:34); gate r1 + rework + gate r2 ~13 min
(21:37-21:50); literature rework ~42 min (21:50-22:32); ideation r3 +
hypothesis gate ~1 h 25 min (22:40-00:05); execution verification 00:20;
analysis gate 00:45; writeup stage ~2 h incl. gate rework (01:00-02:00);
finalization at 03:30 (after a ~1.5 h gap without thread events).

**Session-level note (added session logs, 2026-09-02):** the loop's DSH
session (12:41:33 on 08-31 -> 22:05:35 on 09-01) continued after the 03:30
thread event with in-session iteration-3-start activity: human iteration-3
message 02:31:22Z, goal record 02:34:12Z, first goal round 03:45:08Z, and 56
turns through 22:05 (32 subagent sessions, 248.2M metered tokens). This is
outside the gathered *thread* window (the human-defined cutoff is the
09-02T00:00 directive comment) and appears only in `token-audit.md` (F3).

---

## 2. Tool usage

### 2.1 Tokens (cost ledger, `project.json` -> `results.costs`)

**Correction (2026-09-02):** the human added the loop's DSH session logs to
this issue directory (`dsh-session-session-8b1c9954-.../`, 74 session logs:
principal + 73 subagents, ~171 MB, all events < 2026-09-02T00:00). They carry
per-LLM-call metered usage (inputTokens = cache-miss fresh input,
outputTokens = completion, cacheReadTokens = cache-hit input; total prompt
per call = input + cacheRead). Section 2.1 below is corrected to **measured**
figures; the ledger estimates are retained as superseded history. Full
methodology and tables: `token-audit.md` (this issue directory).

**Measured window consumption** (iterations 1-2 semantics, per phase cutoff
13:38 / 17:32 / 21:24 / 03:30 on the session timeline; 1,625 LLM calls):

| phase | LLM calls | input (fresh) | output | cache-read | total |
|---|---|---|---|---|---|
| setup (12:41:33-13:38) | 31 | 122,367 | 22,538 | 1,223,168 | 1,368,073 |
| iteration 1 (13:38-17:32) | 360 | 1,160,184 | 344,709 | 41,517,824 | 43,022,717 |
| it1 wrap/gap (17:32-21:24) | 11 | 167,926 | 8,633 | 1,485,568 | 1,662,127 |
| iteration 2 (21:24-03:30) | 1,218 | 3,811,868 | 1,067,635 | 152,017,664 | 156,897,167 |
| it2 wrap (03:30-03:45) | 5 | 5,794 | 5,487 | 373,504 | 384,785 |
| **window total** | **1,625** | **5,268,139** | **1,449,002** | **196,617,728** | **203,334,869** |

Measured window consumption is **~188x the ledger estimate** (~1,081k),
cache-dominated (96.7%; cache-hit input prices far below fresh input, so the
token ratio does not map linearly to cost). Of the window total, the
principal (manager) sessions account for 132,942,733 (993 calls) and the 73
subagent sessions - previously "unmetered" - for 70,392,136 (632 calls).
Iteration-1 phase: 43,022,717 vs ~693k estimate (~62x). Iteration-2 phase
(with wrap): 157,281,952 vs ~388k estimate (~405x).

**Disclosed, excluded from window totals:** in-session iteration-3-start
activity (first goal round 09-01T03:45, after the human's iteration-3 message
02:31:22Z; 56 turns, 32 subagent sessions) consumed 248,156,771 tokens
(2,110 calls) before the session ended 09-01T22:05 - all timestamped before
the thread's 09-02T00:00 directive comment; see Findings F3 in
`token-audit.md`.

**Superseded ledger estimates** (kept for the record): iteration-1 entries
(six issues) totaled ~693k (370k in / 178k out / 145k cache-read) - see
sibling report; iteration-2 entries (four issues):

| Issue | input | output | cache_read | total | note |
|---|---|---|---|---|---|
| hypothesis-ideation-r2 | 45,000 | 22,000 | 30,000 | 97,000 | gate-r2 re-entry ideation; estimated |
| hypothesis-rework-r1 | 45,000 | 22,000 | 30,000 | 97,000 | proposal-v4 folding reviewer items 1-7; estimated |
| literature-review-rework-r1 | 45,000 | 22,000 | 30,000 | 97,000 | corpus enriched (492 entities, 120,786 co-occurrences; web research + indexing); estimated |
| hypothesis-ideation-r3 | 45,000 | 22,000 | 30,000 | 97,000 | labeled "iteration-3 ideation" in ledger (naming inconsistency, see 4.2); estimated |
| **Iteration-2 total** | **180,000** | **88,000** | **120,000** | **388,000** | all estimates |

Former window total: ~1,081,000 tokens (550k in / 266k out / 265k
cache-read), estimated, manager-visible work only - **superseded by the
measured figures above (2026-09-02)**.

### 2.2 Compute resources

- **Envelope:** consumer hardware, CPU-only - 12 cores, ~7 GB RAM; NumPy
  1.24.2, SciPy 1.10.1, scikit-learn 1.2.1, tectonic 0.17.0, h5py (added at
  iteration 2 for netCDF-4/HDF5 data reading). No GPU.
- **Iteration-2 pipeline (real data):** full pipeline **77.8 s** wall (also
  quoted 108 s in an early draft and 78.7 s in the analysis-gate fold;
  artifact-reconciled values 77.8-78.7 s), **1.55-1.57 GB peak RSS**,
  CPU-only, well under the 90-min / 7 GB cap. Key
  results: P0 torus-exactness 2.62e-12 rel (free gap 0.95/0.12 disclosed);
  T1a masked reconstruction RMSE 0.0816-0.0880 (matern32; rbf 0.24-0.32)
  with calendar-month conformal diagnostics; T1b PCG 245-281 iterations at
  tol 1e-8 (RMSE ~0.53); T2 functional RMSE 0.0856 (corr 0.997) vs
  zero-model 0.795 vs direct ridge head 0.270 (3.2x); T3 transfer forecast
  REFUTED 0/4 under pre-registered win rules (h=6 raw 0.796 vs persistence
  0.907, bootstrap p=0.234); B baselines 1.24-1.73 on pooled real cells,
  same-2000-cells spectral 0.0999 vs 0.82 with 5e4-1.6e6x fewer flops; S
  sub-ms O(N log N) scaling, single 0.25-deg field ~0.04 GB (8.3 MB per
  float64 field, ~5 working arrays), Nystrom-5000 ~46 s dominates B budget.
- **PDF:** tectonic compile, 4 body pages + References p5, 30 references,
  warning-free (0 Overfull/Underfull after fixes).

### 2.3 Tavily MCP / web research

- **Literature grounding rework:** 15 new annotated entries (26-40) "all
  web-verified in-session" (22:32 notice); cost-ledger note for
  literature-review-rework-r1 mentions "web research + indexing". This
  continues iteration-1's in-session tavily use (12 web-verified entries
  after the 15:00 correction).
- **Correction (2026-09-02, session logs):** per-call counts are now metered:
  **94 Tavily MCP calls in-window** (12 principal-side `tavily_search` + 82
  worker-side, including 4 `tavily_extract`), plus 6 worker-side during the
  in-session iteration-3 start (disclosed, outside window totals).
- **Execution:** scientific compute is no-web; data reading via h5py from
  bundled real files (no live fetch in the executed runs recorded).
- Later iterations' heavier web-research usage (iteration 3 rework) is
  outside the window.

---

## 3. Human intervention steps

**Correction (2026-09-02, session logs):** the gathered *thread* ledger alone
shows no explicitly human-attributed entry inside the window, but the added
DSH session logs record **four human (`user`-kind) messages inside the
window by timestamp** plus a human GUI-side goal pause. The thread only
echoed the two directives; the editorial/review messages were never recorded
in the thread. Full table: `token-audit.md` section 3.5.

- **Pre-loop human input (not in-window):** `2026-08-31T13:04:46Z` - the
  original research brief + project config (Phase A entry, before the first
  thread event 13:38).
- **Iteration-2 directive (in-window):** `2026-08-31T21:22:46Z` - human
  message: "As research manager, iterate upon this project by moving the
  pipeline back to the ideation step, looking for a higher significance
  re...". Echoed to the thread at 21:24 as `[directive: iteration-2]
  Research manager directive` (the label mirrors the human's own "As
  research manager" phrasing); goal record created 21:24:05Z (principal-side
  `create_goal` bookkeeping). The "sanctioned" h5py constraint lift is part
  of this directive.
- **Editorial/review feedback (in-window, unrecorded in the thread):**
  - `2026-08-31T23:29:29Z` - "references do not count towards 4 page limit
    (the writeup worker has been notified of this change)";
  - `2026-08-31T23:39:51Z` - "From a quick human review - the paper writeup
    is missing related works and contains no figures".
  Both messages precede the iteration-2 writeup stage (01:00 on 09-01) and
  are consistent with the writeup brief's richer `main.bib` and figures.
- **Iteration-2 goal pause:** `2026-08-31T23:28:44Z` - `goal/change` pause
  with no principal `update_goal` pause call logged; consistent with a human
  GUI-side pause, immediately before the 23:29:29 message.
- **Iteration-3 directive (in-window by timestamp, semantically the excluded
  cutoff):** `2026-09-01T02:31:22Z` - human message: "From human review, the
  novelty is still a bit weak. As research project manager, you are to run
  another iteration to this project. Up...". Goal record created 02:34:12Z
  (principal-side); **first iteration-3 goal round 03:45:08Z**; in-session
  iteration-3 execution ran 03:45 -> 22:05 on 09-01. The thread record of
  the directive (`2026-09-02T00:00Z`, "Human directive:") was posted ~21.5 h
  after the actual human message - this is the ledger-based cutoff the user
  defined for this report, retained as the boundary (see token-audit.md F3).
- **Manager-side, not human:** the `interventions` ledger entry
  `2026-08-31T21:50Z` (iteration-2-routing) is the manager's
  route_for_failure decision (hypothesis FAIL -> literature rework ->
  re-entry).

---

## 4. Ledger limitations (honesty notes)

1. **Token figures: estimates superseded by metered audit (2026-09-02).**
   The ledger figures in section 2.1 (and the sibling report) were manager
   estimates; the added DSH session logs now provide measured per-LLM-call
   usage (section 2.1 + `token-audit.md`). Measured window total
   203,334,869 tokens (~188x the ~1,081k estimate), cache-dominated.
   Per-issue attribution is still not possible (usage events are not tagged
   per stage issue); phase bucketing is the honest granularity.
2. **Naming inconsistency in the ledger:** the cost entry for
   `hypothesis-ideation-r3` is labeled "iteration-3 ideation" and the 03:30
   validator comment likewise says "costs ledged ... incl. iteration-3
   ideation", while the issue's own title is "Hypothesis ideation r3
   (iteration 2, re-entry...)" and EPIC.md reserves "iteration 3" for the
   post-directive phase. Reports the loop as: iteration 2 = real-data phase
   (r3 ideation is its hypothesis re-entry).
3. **Wall-clock figures vary across comments:** 108 s (early draft) ->
   77.8 s / 1.55 GB (execution notice, v2) and 78.7 s / 1.57 GB (analysis
   gate, writeup brief); the thread reconciled to artifact values
   (77.8 / 78.7 s; 1.55-1.57 GB). Both reconciled figures are quoted above.
4. `project.json` is a living manifest (updated 2026-09-02T00:45Z) and
   `EPIC.md` now carries iteration-3/4 sections; only window-attributable
   entries (cost ledger keys, interventions ledger, verdict fragments) were
   cited.
5. Tavily call counts were not recorded in the tracker during the window,
   but are metered in the session logs: 94 in-window calls (12
   principal-side + 82 worker-side) plus 6 worker-side during the in-session
   iteration-3 start (section 2.3; `token-audit.md` section 5).
6. One critique comment (23:45) is truncated in the file at 2000 chars; its
   continuation is covered by the aggregating manager notice (00:05), which
   is included.

---

## Appendix A - Gathered file inventory (84 files, all < 2026-09-02T00:00)

### A.1 Iteration-1 set - 51 files

Identical set to sibling report `iteration-1-research-loop-report`,
Appendix A (orchestration-log ISSUE.md + 18 comments; six r1 stage issues
with ISSUE.md + comments; all timestamped <= 2026-08-31T17:32). All are
within this window as well.

### A.2 Iteration-2 additions - 33 files

**Orchestration log (control issue), comments (2):**
`20260831T2124-manager-directive-iteration-2-research-manager-directive-ite.md`,
`20260831T2150-manager-directive-iteration-2-routing-hypothesis-gate-r2-exh.md`

**hypothesis-ideation-r2 (10):** `ISSUE.md`; comments
`20260831T2125-seeding-iteration-2-ideation-...`,
`20260831T2127-proposal-v1-iteration-2-...`,
`20260831T2128-proposal-v2-iteration-2-...`,
`20260831T2131-proposal-v3-iteration-2-...`,
`20260831T2133-review-critique-ideation-r3-...`,
`20260831T2134-manager-notice-ideation-loop-...`,
`20260831T2137-review-critique-hypothesis-r1-...`,
`20260831T2150-review-critique-hypothesis-r2-...`,
`20260831T2150-manager-notice-gate-routing-...`

**hypothesis-rework-r1 (4):** `ISSUE.md`; comments
`20260831T2138-seeded-fail-feedback-...`,
`20260831T2139-proposal-v4-...`, `20260831T2139-manager-notice-rework-complete-...`

**literature-review-rework-r1 (4):** `ISSUE.md`; comments
`20260831T2150-seeding-literature-grounding-rework-...`,
`20260831T2150-seeded-fail-feedback-...`,
`20260831T2232-manager-notice-rework-resolved.md`

**hypothesis-ideation-r3 (7):** `ISSUE.md`; comments
`20260831T2240-seeding-hypothesis-ideation-r3.md`,
`20260831T2242-proposal-it3-v1.md`,
`20260831T2310-review-critique-ideation-r3-r1.md`,
`20260831T2325-proposal-it3-v2-gate-revision.md`,
`20260831T2345-review-critique-hypothesis-r1.md`,
`20260901T0005-manager-notice-gate-pass.md`

**Later comments on r1 stage issues (5):** `experiment-execution-anchor-r1/
comments/20260901T0020-manager-notice-execution-iter2-verified.md`;
`analysis-anchor-r1/comments/20260901T0045-review-critique-analysis-r1.md`;
`paper-writeup-anchor-r1/comments/20260901T0100-manager-notice-writeup-stage-entry-iter2.md`,
`20260901T0150-review-critique-writeup-r1.md`,
`20260901T0200-review-critique-writeup-r2.md`

**Epic-root orchestration-log (1):**
`orchestration-log/comments/20260901T0330-final-validator-clean.md` (last
included file)

Auxiliary living documents (cited selectively): `EPIC.md`, `project.json`.

## Appendix B - Out-of-scope boundary (excluded)

- **`20260902T0000-directive-iteration-3-novelty-upgrade.md`** - the
  iteration-3 directive itself; **excluded per the request** (first ledger
  entry explicitly marked "human directive:").
- All 2026-09-02 material: literature-review-r3 seeding/notices,
  hypothesis-ideation-r4 (proposal + critique rounds + gate rework),
  experiment-planning-anchor-r2 / experiment-execution-anchor-r2 /
  analysis-anchor-r2 (+ block), hypothesis-ideation-r5,
  literature-review-rework-r2, writeup-anchor-r3,
  `20260902T1115-project-finalization-iteration-4` (iteration 4), and later
  comments on r1-stage issues (analysis/paper critique rounds at 09-02).
- None of the excluded files were read into this report; EPIC.md sections
  for iterations 3-4 and the 2026-09-02T00:45Z manifest update were only
  used to attribute the window boundary.
- **Session-log evidence (added 2026-09-02):** in-session iteration-3
  activity (human message 09-01T02:31:22Z, goal record 02:34:12Z, goal
  rounds 03:45-22:05, 248.2M metered tokens) is disclosed in `token-audit.md`
  (F3) - timestamped before the 09-02T00:00 cutoff, semantically excluded
  from this window. The thread files gathered here are unaffected.

## Appendix C - Session-log evidence (token audit, added by the human 2026-09-02)

The human added the loop's DSH session logs to this issue directory
(`dsh-session-session-8b1c9954-.../`, 74 sessions: principal + 73
subagents, ~171 MB, all events < 2026-09-02T00:00). The full token audit
(methodology, tables, boundary and human-intervention findings) lives in
`token-audit.md`. Headline corrections applied to sections 2.1, 2.3, 3, 4:

- Measured window consumption: **203,334,869 tokens** (5,268,139 fresh in /
  1,449,002 out / 196,617,728 cache-read; 1,625 LLM calls) - ~188x the
  ~1,081k ledger estimate, cache-dominated (96.7%).
- Principal 132,942,733 (993 calls); subagents (previously "unmetered")
  70,392,136 (632 calls). Tavily: 94 in-window calls (12 + 82) + 6
  worker-side during the in-session iteration-3 start.
- Human interventions in-window: 21:22:46 (iteration-2 directive),
  23:29:29 (references rule), 23:39:51 (paper review), 02:31:22
  (iteration-3 directive by timestamp), plus a GUI-side goal pause
  23:28:44 - report section 3 corrected.
- Iteration-3 boundary anomaly: the in-session directive/goal/execution all
  predate the thread's 09-02T00:00 record (F3).