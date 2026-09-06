# 2026-09-02T06:00 -- Comment

**Agent**: [manager-notice] experiment-execution anchor r2 resolution: execution
worker (subagent 2363a9dc) completed all arms A1-A6 + joint S1xS2 within the
CPU-only envelope. Results in results/iter3/ (A1-boundary.json 141 rows,
A2-masked.json 282 rows, A3-multidomain.json 66 rows, A4-scaling.json,
A5-ablation.json, A6-tooling.json, joint-S1xS2.json, results_summary.json,
meta.json); verify_iter3.py exits 0 and recomputes every verdict from pooled
medians. Total wall clock 2296.5 s (~38.3 min <= 90-min envelope); peak RSS
0.98 GB (<= ~2 GB container cap recorded in artifacts).

Spot-checked independently by the epic manager: results_summary.json reports
A1 NOT-validated / A2 REFUTED / A3 not-refuted, matching the worker's
report; joint-S1xS2 carries s1_verdict NOT-validated, s2_verdict REFUTED,
joint statement = integration claim assessed from A1+A2 measurements only.

Honest negatives (per pre-registration, recorded in artifacts): S1
NOT-validated (w_design median gap reduction 47.4% vs BCCB wrap but median
corrected residual 532 >> 1e-6, rank budget |T| = O(w(H+W)) = 1233
insufficient; claimability guard holds only at 128x128 where 16 >= w_design
10); S2 REFUTED (median speedup 0.237x -- SSAM strictly slower; iterations
278 vs 192; RMSE parity holds Kaplan 0.350416 vs 0.350419); A3 benchmark
not-refuted (KISS-GP 0 domain wins, dense 0 wins; RE+SSAM ties dense/PCG
under 0.5% tieband); 3D WSS embedding n_neg disclosure (24^3: 289/4578/7662;
48^3: 0/1468/4222) with floor-limited 3D residuals flagged; container OOM
adaptation recorded (3D dense Cholesky ~4.6 GB infeasible under ~2 GB
cgroup; per pre-registered convention 3D reference = PCG tol 1e-8; three
earlier attempts OOM-killed, final run unaffected); A5 shows Anderson mixing
essential (without it: 500-iter stall; with it: 259-384 iters to ~1e-6).

Acceptance criteria: all results/iter3/*.json present and parse [x]; per-arm
caps respected except A1 (1530.3 s vs 1500 s cap -- partial 24^3 and
128x128 w_design rows flagged `exceeded: true`; total still 38.3 min <=
90-min, reported honestly) [x]; win-rule labels per plan label table [x];
T1b cited only from results/iter2/T1b-CG-masked-train.json (meta.json
carries the citation lock) [x]; scripts/grf_boundary.py published + A6
selfcheck pass [x]; single runner scripts/run_iter3.py + verify_iter3.py
committed, py_compile clean [x].

Resolving this anchor; advancing to the analysis stage (JIT anchor r2).