# 2026-09-02T06:30 -- Review critique

**Agent**: [review-critique: analysis-r1] Analysis-gate aggregate review (round
1, median of two reviewers; lower-middle for ties). Quality 4 (both 4) |
Significance 3 (both 3) | Originality 4 (both 4) -> failing criterion:
Significance (score 3 < 4). The 17 honest negatives are present and truthful;
every headline verdict was independently recomputed from the raw artifacts
and matched byte-exact; T1b cited only from canonical
results/iter2/T1b-CG-masked-train.json; superseded figures never cited. The
Significance-3 rationale: the primary pre-registered gates are unmet (S1
NOT-validated on the 1e-6 residual cap; S2 REFUTED at 0.237x), so the residue
is a defensible-but-modest negative-result + tooling + benchmark contribution
rather than a strong positive novel result.

Revision feedback (artifact-fidelity fixes; none change any verdict):
(1) Fix the honest-negatives count in the paper checklist (says 16, array has
17). (2) Restate the DST2 capture-ratio subset precisely: 0.7467 is the
median over the 70 w_design rows with positive DST2 reduction (75 rows carry
both fields; all-75 median 0.7284 also > 50% -- robustness figure added).
(3) Relabel the 24^3 PCG-1e-8 reference: the plan pre-registered dense
Cholesky at 24^3 (PCG-1e-8 was pre-registered for 128x128 only), so the 24^3
substitution is a container-forced deviation (disclosed), not a
"pre-registered convention". (4) Trace or reclassify "three earlier OOM
attempts": A1 ref_convention_notes records only 24^3 dense-Cholesky
infeasibility under the ~2 GB cgroup; move the attempt count to an execution
log note without artifact-provenance implication. (5) Mark the 0.5% tieband
explicitly as an analysis operationalization (absent from the plan's label
table; grf-2d +0.47% sits at the threshold) with a sensitivity note; the
benchmark verdict is unaffected (kiss_wins/dense_wins = 0). (6) Fix
paper_numbers_checklist item 15: its value (Martucci DCT/DST; ADMM/FISTA;
Ambikasaran HSS; Trench/Gohberg-Semencul) is not verbatim in
meta.json.honest_framing -- extend meta.json or re-point the trace to the
plan's honest_framing. (7) Tighten A5's cross-comparison: "RE without
correction leaves rel res 44.8-85.6 (vs corrected median 532)" mixes A5
(lambda 1e-2, 128x128) with A1 (lambda 1e-3 pool) -- cite A1's same-config
pairing (naive_res median 896.4 -> w_design res 532.2 at 64x64/128x128)
directly for the "correction helps" claim.

Route decision: revision round 2 within the analysis gate (max
experiment_review_loops = 2; writeup-gate precedent r1 FAIL -> revision),
same stage; on revision completion dispatch fresh round-2 reviewers.