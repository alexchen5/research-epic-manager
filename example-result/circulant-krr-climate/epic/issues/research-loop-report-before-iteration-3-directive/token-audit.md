# Token audit - DSH session logs (iterations 1-2 window + in-session iteration-3 start)

**Issue:** `research-loop-report-before-iteration-3-directive` (token-estimation
extension, 2026-09-02). **Prepared by:** issue manager (reporting task).

## 1. Scope and corpus

Evidence added by the human into this issue directory:

- `dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/session.jsonl` -
  the principal (manager) session log.
- `dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/subagents/*/session.jsonl` -
  **73** subagent session logs.

Total ~171 MB of JSONL; **74 sessions**. Session lifetime
`2026-08-31T12:41:33Z -> 2026-09-01T22:05:35Z`; **every event is timestamped
before** the thread's iteration-3 directive comment `2026-09-02T00:00` (the
human-defined cutoff of the original report request). Provider:
`siliconflow`, model `deepseek-ai/DeepSeek-V4-Flash`.

## 2. Methodology

- **Usage events.** Each metered LLM call emits an `assistant/chunk` event
  whose `chunk.type == "usage"` and `chunk.usage = {inputTokens,
  outputTokens[, cacheReadTokens]}`. Inspection of consecutive calls shows
  `inputTokens` is the **cache-miss (fresh)** portion of the prompt,
  `cacheReadTokens` the **cache-hit** portion (the cache value grows with the
  accumulated context while the fresh value stays small), and `outputTokens`
  the completion. **Total prompt per call = inputTokens + cacheReadTokens**;
  missing `cacheReadTokens` treated as 0. Totals reported are
  in / out / cache / total (= in + out + cache).
- **Aggregation.** All usage events summed per file, then bucketed by event
  timestamp against phase cutoffs (UTC):
  - `setup` 12:41:33 -> 13:38 (session inception, brief, scoping - before the
    first orchestration event),
  - `it1` 13:38 -> 17:32 (iteration 1; report window start = first recorded
    orchestration event 13:38),
  - `it1wrapgap` 17:32 -> 21:24 (iteration-1 finalization tail + idle gap),
  - `it2` 21:24 -> 03:30 (iteration 2; human iteration-2 message 21:22:46Z,
    goal created 21:24:05Z, final validator clean 03:30),
  - `it2wrap` 03:30 -> 03:45 (finalization/wrap-up steps),
  - `it3start` 03:45 -> 22:05 (in-session iteration-3 goal rounds - semantic
    iteration-3 content, disclosed separately, excluded from window totals).
- **Verification.** Three independent passes agree on every figure:
  1. JSON-parsed aggregation (phase bucketing);
  2. JSON-parsed aggregation with different cutoff handling;
  3. regex-only extraction of raw token fields (no JSON parser) - identical
     combined table and per-class splits (Appendix C).

## 3. Results

### 3.1 Metered tokens - combined (principal + 73 subagent sessions)

| phase | span (UTC) | LLM calls | input (fresh) | output | cache-read | total |
|---|---|---|---|---|---|---|
| setup | 08-31 12:41:33-13:38 | 31 | 122,367 | 22,538 | 1,223,168 | 1,368,073 |
| it1 | 08-31 13:38-17:32 | 360 | 1,160,184 | 344,709 | 41,517,824 | 43,022,717 |
| it1wrapgap | 08-31 17:32-21:24 | 11 | 167,926 | 8,633 | 1,485,568 | 1,662,127 |
| it2 | 08-31 21:24 - 09-01 03:30 | 1,218 | 3,811,868 | 1,067,635 | 152,017,664 | 156,897,167 |
| it2wrap | 09-01 03:30-03:45 | 5 | 5,794 | 5,487 | 373,504 | 384,785 |
| **window total** | | **1,625** | **5,268,139** | **1,449,002** | **196,617,728** | **203,334,869** |
| it3start | 09-01 03:45-22:05 | 2,110 | 9,800,874 | 2,627,513 | 235,728,384 | 248,156,771 |
| **session total** | | **3,735** | **15,069,013** | **4,076,515** | **432,346,112** | **451,491,640** |

### 3.2 Split - principal vs subagents (window)

| class | LLM calls | input | output | cache-read | total |
|---|---|---|---|---|---|
| principal (manager) | 993 | 2,478,573 | 624,032 | 129,840,128 | 132,942,733 |
| subagents (73) | 632 | 2,789,566 | 824,970 | 66,777,600 | 70,392,136 |
| window total | 1,625 | 5,268,139 | 1,449,002 | 196,617,728 | 203,334,869 |

### 3.3 Subagent sessions by creation phase

| creation phase | sessions |
|---|---|
| setup + it1 (before 08-31 17:32) | 18 |
| it2 (08-31 21:24 -> 09-01 03:30) | 23 |
| it3start (09-01 03:45 -> 21:53:59) | 32 |
| total | 73 |

77 `subagent` dispatch calls appear in the principal log; 73 sessions have
log files (4 dispatches left no session log).

### 3.4 Goal operations (principal log)

| time (UTC) | event | goal |
|---|---|---|
| 08-31 13:12:30 | `create_goal` (principal call) | iteration-1 run (after human brief 13:04:46) |
| 08-31 17:33:07 | `update_goal` complete (principal) | iteration-1 |
| 08-31 21:24:05 | `create_goal` (principal call) | iteration-2 (after human message 21:22:46) |
| 08-31 23:28:44 | `goal/change` pause - no principal pause call logged; consistent with a human GUI-side pause | iteration-2 |
| 09-01 01:14:42 / 01:15:01 | `update_goal` complete (principal) | iteration-2 |
| 09-01 02:34:12 | `create_goal` (principal call) | iteration-3 (after human message 02:31:22) |
| 09-01 07:17:14 | `goal/change` block (principal, during goal continuation) | iteration-3 |

The goal/change `create` events are **principal-side bookkeeping** (the
principal called `create_goal`); they are not evidence of human authority.
The authoritative human-intervention record is the `user`-kind messages
(section 3.5).

### 3.5 Human user messages (source kind `user`) - the recorded human interventions

| time (UTC) | message (lead) | note |
|---|---|---|
| 08-31 13:04:46 | research brief (project brief) | pre-loop; already noted in report section 3 |
| 08-31 21:22:46 | "As research manager, iterate upon this project by moving the pipeline back to the ideation step, looking for a higher significance re..." | **iteration-2 directive**, in-window; echoed to thread 21:24 as "[directive: iteration-2] Research manager directive" - the label mirrors the human's own "As research manager" phrasing |
| 08-31 23:29:29 | "references do not count towards 4 page limit (the writeup worker has been notified of this change)" | editorial constraint for the paper writeup; in-window; **not echoed in the thread** |
| 08-31 23:39:51 | "From a quick human review - the paper writeup is missing related works and contains no figures" | human paper-review feedback; in-window; **not echoed in the thread** |
| 09-01 02:31:22 | "From human review, the novelty is still a bit weak. As research project manager, you are to run another iteration to this project. Up..." | **iteration-3 directive**; in-window by timestamp; thread record `2026-09-02T00:00` posted ~21.5 h later (ledger record) |

No `user`-kind messages occur after 09-01 03:45 **in the principal log**;
post-03:45 turns there are driven by goal rounds (24) and platform notices
(subagent reports/settled, plugin jobs). (Subagent logs each carry one
injected dispatch-prompt `user` event - principal bookkeeping, not a human
message; 32 such events exist at >= 03:45, one per subagent created then.)

## 4. Findings

### F1. Ledger estimates understate measured consumption by orders of magnitude

| scope | ledger estimate | measured | ratio |
|---|---|---|---|
| window total (it1+it2) | ~1,081,000 | 203,334,869 | ~188x |
| iteration 1 (13:38-17:32) | ~693,000 | 43,022,717 | ~62x |
| iteration 2 (21:24-03:30 + wrap) | ~388,000 | 157,281,952 | ~405x |

Cache-read tokens dominate: **96.7%** of the window total is cache-hit input
re-read on every LLM call (196.6M of 203.3M). Fresh input is 2.6%,
output 0.7%. Cache-hit tokens price far below fresh tokens, so measured
**token** ratios do not map linearly to cost; the logs record no prices and
this audit reports token counts only.

### F2. Dispatched-worker sessions were not unmetered after all

The original report flagged dispatched-worker sessions as unmetered. The
logs meter them: subagent sessions contribute 70.4M window tokens (34.6% of
the window total; 632 LLM calls). The principal contributes 132.9M (65.4%).

### F3. Boundary anomaly: iteration 3 began in-session ~21.5 h before its thread record

The thread's iteration-3 directive comment is `2026-09-02T00:00` (the
human-defined cutoff). In-session evidence:

- human iteration-3 message: **09-01 T02:31:22Z**,
- iteration-3 goal created: **09-01 T02:34:12Z** (principal `create_goal`),
- first iteration-3 goal round: **09-01 T03:45:08Z** (turn 30),
- in-session iteration-3 execution: **03:45 -> 22:05Z** (56 turns, 32
  subagent sessions, 2,110 LLM calls, 248.2M tokens).

All of it is timestamped **before** the 09-02T00:00 thread comment. The
original report's gathered *thread* window is unaffected (the human defined
the cutoff by thread files), but any token accounting that used the thread
cutoff alone would silently include 248.2M tokens of iteration-3 content.
This audit therefore **excludes** `it3start` from window totals and
discloses it separately.

### F4. Human interventions did occur inside the window (report section 3 correction)

The report's Sec.3 conclusion ("no ledger entry explicitly attributed to a
human inside the window") is superseded by the session logs: four
`user`-kind messages fall inside the window by timestamp (21:22:46
iteration-2 directive; 23:29:29 references rule; 23:39:51 paper review;
02:31:22 iteration-3 directive), plus a human GUI-side goal pause
(23:28:44Z). The thread only echoed the two directives ("Research manager
directive" at 21:24 - the human's own "As research manager" phrasing - and
"Human directive:" at 09-02T00:00); the two editorial/review messages
(23:29, 23:39) were never recorded in the thread. The goal/change `create`
events are principal-side bookkeeping, so they are **not** evidence of human
authority; the `user` messages are the authoritative record.

## 5. Tool-usage additions (report section 2.3 update)

Metered tool calls (window = before 09-01 03:30):

- Tavily MCP: **94 calls in-window** (12 principal-side `tavily_search` +
  82 worker-side, incl. 4 `tavily_extract`) and **6 worker-side** during
  `it3start` - the report's "per-call counts were not metered" limitation is
  resolved.
- Principal session calls (1,498 total): bash 930, read 139, write 131,
  subagent 77, edit 60, job_output 54, list_agents 35, grep 17,
  tavily_search 12, todo_write 11, send_message 8, interrupt_agent 5,
  glob 4, skill 3, create_goal 3, job_list 3, update_goal 3, get_goal 2,
  job_kill 1.
- Subagent calls (2,867 total): bash 1,608, read 498, edit 387, grep 92,
  tavily_search 84, write 64, job_output 61, report 33, todo_write 17,
  glob 10, read_image 5, tavily_extract 4, skill 3, job_kill 1.

## 6. Limitations

1. **Per-issue attribution is not possible.** Usage events are not tagged
   per stage issue; the ledger's per-issue rows (e.g., 45k/22k/30k) cannot
   be validated row-by-row. Phase bucketing is the honest granularity.
2. **No prices in the logs.** Token ratios overstate relative cost because
   cache-hit tokens price far below fresh tokens; costs were not part of the
   original report either.
3. The session logs themselves are the metering record (asserted by the
   harness); no independent metering exists to cross-check provider-side
   accounting.
4. Compaction/title/retry LLM calls are included in the sums where they emit
   usage events (title request 13:04:46; 2 retries; compaction summaries);
   their individual contribution is small relative to totals.
5. The `it3start` disclosure covers only this session's iteration-3 start;
   the thread's 09-02 iteration-3/4 run happened after this session ended
   and is outside all totals here (its tokens are not recorded in these
   logs).

## Appendix A - Phase attribution rule

Cutoffs (UTC): 13:38 (first orchestration event; report window start),
17:32 (iteration-1 end), 21:24 (iteration-2 goal/message), 03:30 (last
included thread file), 03:45 (first iteration-3 goal round). Event time =
the usage event's `time` field. Missing `cacheReadTokens` = 0.

## Appendix B - Window-attributable totals by class

| class | calls | in | out | cache | total |
|---|---|---|---|---|---|
| principal (window) | 993 | 2,478,573 | 624,032 | 129,840,128 | 132,942,733 |
| subagents (window) | 632 | 2,789,566 | 824,970 | 66,777,600 | 70,392,136 |
| combined | 1,625 | 5,268,139 | 1,449,002 | 196,617,728 | 203,334,869 |

## Appendix C - Cross-check note

Aggregation was run three times with independent implementations: (1) JSON
parsing with phase bucketing, (2) JSON parsing with different cutoff
handling, (3) regex-only extraction of raw token fields with no JSON parser.
All three agree on the combined phase table, the window total
(203,334,869), the session total (451,491,640), and the per-class splits
(993 principal / 632 subagent window calls).

An independent reviewer re-derived every figure from scratch on a copy of
the raw logs (own scripts, JSON-parse and pure-regex approaches; 0
unparseable lines of 345,322; no double counting) and returned **APPROVE**
on 2026-09-02, with two wording corrections now folded in: (d) the tool-call
enumeration omitted 5 tool names (update_goal/get_goal/job_kill principal;
skill/job_kill subagent - totals unaffected) and (g) the "no user-kind
messages after 03:45" statement holds for the principal log only (subagent
logs carry injected dispatch-prompt user events, 32 at >= 03:45).

---

**Bottom line:** the ledger's "~1,081k window total, manager-visible work
only, estimates" is superseded: **measured window consumption is
203,334,869 tokens** (5,268,139 fresh input / 1,449,002 output / 196,617,728
cache-read) across 1,625 LLM calls (993 principal + 632 subagent), ~188x the
estimate, cache-dominated. Iteration-3-start consumption (248,156,771
tokens, 2,110 calls) is excluded from window totals and disclosed separately;
human interventions inside the window are documented in section 3.5 / F4.