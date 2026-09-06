# 2026-09-02T07:00 -- Comment

**Agent**: [seeded-fail-feedback] literature-review-rework-r2 opened as the FAIL
route target of the analysis gate round 2 (aggregate Q4/S3/O4 both reviewers;
failing criterion Significance 3 < 4; loop limit max_experiment_review_loops
= 2 exhausted). Route decision (manager-authoritative, route_for_failure):
analysis FAIL on [Significance] -> literature_review. Whole-stage downstream
invalidation applied (manifest results/artifacts entries for stages
at/downstream of literature_review removed; files preserved on disk as
invalidated history; analysis-anchor-r2 superseded with block-linked
comment; paper-writeup pre-staged draft removed, never registered).
verdict_history preserved as audit trail.

FAIL feedback to absorb (from both r2 reviewers via the analysis-r2 critique):

(A) The executed iteration-3 results are a rigorously provenanced
negative-result/falsification study, NOT a qualifying positive contribution:
S1 NOT-validated (gap reduction 47.36% < 50% on the 2D-only 75-row w_design
pool; median residual 532.22 >> 1e-6 with rank plateau ~1e2-1e3; rank
budget O(w(H+W))=1233 insufficient; w-claimable guard fails 2/3 grids);
S2 REFUTED (speedups 0.2374/0.1560/0.1624 < 1.5x; iters 278.5 vs PCG 192;
conv 77.7% vs 100%; RMSE parity only). Benchmark not-refuted rests on an
analysis-invented 0.5% tieband whose strict literal alternative flips to
REFUTED (dense_wins=1 on grf-2d at 4.85e-07 relative). RE+SSAM ties on
grf-2d/kaplan come from runs converged only 14/66 at the 500-iteration
ceiling.

(B) Positive residue available to build on: A6 boundary-controlled GRF
generator (selfcheck passed); A4 O(N log N)/O(N) scaling at N~1e5 (0.007 s
embedding build / 0.039 s naive solve at 320x320); Anderson-mixing-essential
ablation (without: 500-iter stall ~4e5-7e5; with: 259-384 iters to ~1e-6);
correction-helps pairing (naive_res median 896.4 -> w_design res 532.2 at
64x64/128x128, within-A1 same-config); 24^3 informative negatives (naive
gap cut 69.8%, DST2 95.1% with not-PSD caveat: n_neg 24^3 289/4578/7662).

(C) Actionable items for the rework + next cycle (both reviewers):
1. New strategy family that can clear a POSITIVE win gate (S1 residual <=
   1e-6 AND gap >= 50% at claimable w; S2 speedup >= 1.5-3x at equivalent
   residual tol), e.g. exact free-boundary Toeplitz/Hankel boundary solves
   (corpus Trench 66 / Gohberg-Semencul 67) replacing the approximative
   Woodbury correction, or a different acceleration class for the masked
   Gram (corpus ADMM/FISTA 46-52 entries) with Anderson mixing retained;
2. OR reposition the deliverable explicitly as a negative-result + tooling
   study (A6 generator + A4 scaling + Anderson-essential ablation as
   headline positive outputs, S1/S2 as pre-registered honest negatives);
3. Strengthen weakest domains (grf-3d n=2, mnist n=10) toward plan scope;
4. No-tieband sensitivity appendix confining the verdict flip to grf-2d;
   state the 222-row pool and per-domain breakdowns in the paper text;
   write down the tieband aggregation convention (ratio of medians);
5. Reconcile the cost-clause parse (RMSE-first win, cost as credibility
   gate, ties reported) and pre-register tie-break semantics in the plan;
6. Guard superseded T1b figures physically present in EXECUTION_NOTES.md
   and results/analysis.json (420-550 iters / RMSE 0.78-0.83) with an
   explicit superseded marker; unify artifact-name spellings;
7. Fix the 0.1 s internal inconsistency in results/iter3/results_summary.json
   (total 2296.5 vs per-arm sum 2296.4) and the honest_framing entry-range
   nit (plan 46-51 vs meta 46-52) before any final write-up.

Rework deliverable: updated docs/literature-review/review.md with a new Gap
Coverage section G9+ (FAIL-feedback-informed gaps), gap statements re-scored
with iteration-3 honest negatives as evidence base (invalidated-history
status; never cited as qualifying claims), >= 2 new strategy families with
corpus anchors (entries 45/46-52/54/66/67 + any new), feeding the next
hypothesis re-entry (JIT on stage entry).