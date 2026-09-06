# ISSUE research-loop-report-before-iteration-3: Research-loop activity report (iterations 1-2, cutoff < 2026-09-02T00:00) - extended: token estimation from DSH session logs

## Metadata

- **Epic:** `circulant-krr-climate`
- **Issue id:** `research-loop-report-before-iteration-3`
- **Status:** `resolved` (reopened 2026-09-02 for the token-estimation
  extension, re-resolved 2026-09-02 after the session-log token audit;
  originally resolved 2026-09-02 for the report)
- **Priority:** `P2`
- **Assignee(s):** `issue-manager (reporting task)`
- **Labels:** `report`, `orchestration`, `retrospective`, `token-audit`
- **Workspace:** tracker-only (no project-workspace changes)
- **Created:** `2026-09-02`
- **Updated:** `2026-09-02`

## Description

Reporting task (human request, 2026-09-02; same instruction as the previous
reporting issue `iteration-1-research-loop-report`, new cutoff): gather the
orchestration files that describe the research loop of the
`circulant-krr-climate` project up to **but NOT including** the iteration-3
directive `20260902T0000-directive-iteration-3-novelty-upgrade.md` on the
orchestration-log. That directive is excluded; everything in the gathered
window is strictly earlier (latest included file:
`orchestration-log/comments/20260901T0330-final-validator-clean.md`).
Iteration-3 and iteration-4 material (all 2026-09-02 files) is excluded and
appears only in the out-of-scope boundary note. From the gathered files,
report on:

1. **The research loop** - how the agent iterated across iterations 1 and 2,
   including hypothesis generation (both ideation runs), experimentation,
   and analysis steps, the gate/rework/routing loops, and how long the
   process ran (wall-clock from the first recorded orchestration event to
   the last included comment).
2. **Tool usage** - tokens (cost ledger entries), compute resources (CPU
   envelope, wall-clock, memory of the experiment runs), and Tavily MCP /
   web-research usage as recorded.
3. **Human intervention steps** - any recorded human directives or
   interventions inside the gathered window, with the boundary note that the
   iteration-3 directive (the first ledger entry explicitly marked "human
   directive") is the excluded cutoff.

Reporting artifacts are kept under this issue's directory (`report.md` +
gathered-file inventory appendix). Tracker-only issue; no project-workspace
files are modified.

### 2026-09-02 extension - token estimation from DSH session logs

The human added the DSH session logs of the loop into this issue directory:

`dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/` - **74 session
logs** (1 principal `session.jsonl` + 73 `subagents/*/session.jsonl`,
JSONL event streams, ~171 MB), covering the whole loop session
2026-08-31T12:41:33Z -> 2026-09-01T22:05:35Z (all events timestamped before
the thread's 09-02T00:00 directive comment). Each LLM call is metered:
`inputTokens` (cache-miss fresh input), `outputTokens` (completion), and
`cacheReadTokens` (cache-hit input; total prompt per call =
input+cacheRead). Provider: siliconflow, model
`deepseek-ai/DeepSeek-V4-Flash`.

The original `report.md` Section 2.1 token figures are **manager estimates
only** ("exact session metering unavailable"); dispatched-worker sessions
were unmetered. The added logs close that gap, so this issue is extended to:

1. **Audit the measured token consumption** from the session logs and replace
   the estimates in `report.md` with metered figures (estimates retained,
   flagged as superseded).
2. **Reconcile** measured totals against the ledger estimates (~1,081k window
   total; ~693k iteration-1; ~388k iteration-2) and quantify the gap
   (measured, cache-dominated, is ~2 orders of magnitude larger).
3. **Re-examine the report's boundary and human-intervention conclusions**
   against the in-session record:
   - iteration-3 directive: human `user`-kind message **2026-09-01T02:31:22Z**,
     goal record created 02:34:12Z (principal-side `create_goal`
     bookkeeping), first goal round **03:45:08Z**, in-session iteration-3
     execution 03:45 -> 22:05 (~56 turns, 32 subagents) - all **before** the
     thread's 09-02T00:00 directive comment;
   - iteration-2 directive: human `user`-kind message **2026-08-31T21:22:46Z**
     ("As research manager, iterate ..."), echoed to the thread at 21:24 as
     "[directive: iteration-2] Research manager directive" (label mirrors the
     human's phrasing); additional human messages 23:29:29Z (references /
     4-page limit) and 23:39:51Z (paper review: related works / figures),
     plus a GUI-side goal pause 23:28:44Z - all inside the window;
   - note: goal `create`/`complete` events are **principal-side bookkeeping**
     (the principal called `create_goal`); the `user`-kind messages are the
     authoritative human-intervention record (see `token-audit.md` sections
     3.4-3.5, F4).

## Acceptance Criteria

Original criteria (satisfied 2026-09-02 for the original report; retained):

- [x] Gathered-file inventory strictly scoped to files timestamped
      < 2026-09-02T00:00 (iteration-1 set + iteration-2 set: orchestration-log
      thread, stage issues, epic-root orchestrations); the iteration-3
      directive and all later files excluded and listed only as out-of-scope
      boundary
- [x] `report.md` documents the research loop: iteration-1 recap,
      iteration-2 narrative (ideation r2 cap-stop, hypothesis gate
      FAIL->rework->FAIL->routing, literature rework, ideation r3 re-entry
      + gate PASS, execution, analysis, writeup with gate rework),
      gates/rework/routing, and the run duration
- [x] `report.md` documents tool usage: token ledger (estimates flagged),
      compute resources (hardware envelope, experiment wall-clock/RAM),
      Tavily/web-research usage
- [x] `report.md` documents human intervention steps (ledger record within
      the window; boundary note naming the iteration-3 directive as the
      excluded cutoff)
- [x] Artifacts live under this issue directory; resolution recorded in
      ISSUE.md and thread comments

Extension criteria (new, for the token-estimation work):

- [x] Session-log corpus inventoried: 1 principal + 73 subagent logs, usage
      event semantics documented (per-LLM-call input = cache-miss fresh
      portion, output = completion, cacheRead = cache-hit portion; missing
      cacheRead treated as 0), all events < 2026-09-02T00:00
- [x] Measured aggregation per phase by event timestamp (setup 12:41:33-13:38,
      iteration-1 13:38-17:32, wrap+gap 17:32-21:24, iteration-2
      21:24-03:30, wrap 03:30-03:45, iteration-3-start 03:45-22:05), split
      principal vs subagent sessions; window-attributable total and
      estimate-vs-measured comparison table in `token-audit.md`
- [x] `report.md` Section 2.1 corrected to measured figures (ledger
      estimates retained and flagged as superseded); Section 4 limitations
      updated (metered totals now available; per-issue attribution still
      approximate - phase-bucket, not per-issue); boundary/anomaly noted
- [x] Boundary finding documented: iteration-3 goal creation
      2026-09-01T02:34:12Z, first goal round 03:45:08Z, in-session
      iteration-3-start consumption (~248.2M tokens, 2,110 LLM calls, 32
      subagent sessions) excluded from window totals but disclosed
- [x] Section 3 human-intervention record corrected: `user`-kind messages
      show human interventions inside the window (iteration-2 directive
      2026-08-31T21:22:46Z; references rule 23:29:29Z; paper review
      23:39:51Z; iteration-3 directive 2026-09-01T02:31:22Z; GUI-side goal
      pause 23:28:44Z); goal `create`/`complete` events recognized as
      principal-side bookkeeping, not human evidence; the "research-manager
      directive" ledger label and the "no human intervention inside the
      window" claim corrected with log evidence
- [x] Artifacts under this issue directory (`token-audit.md` new,
      `report.md` corrected); verification re-run; reviewer verdict;
      completion comment; resolution recorded in ISSUE.md

## Repro / Steps

Original steps (for the report; satisfied):

1. List `/workspace/epics/circulant-krr-climate/issues/` and filter every
   comment file whose timestamp is < `20260902T0000` (the iteration-3
   directive is excluded; first excluded-adjacent file after the window is
   `20260902T0010` literature-review-r3 seeding).
2. Read the iteration-2 thread additions (orchestration-log directives
   2124/2150; hypothesis-ideation-r2, hypothesis-rework-r1,
   literature-review-rework-r1, hypothesis-ideation-r3; later comments on
   the r1 stage issues; epic-root orchestration-log 0330) on top of the
   iteration-1 set already inventoried in the sibling report.
3. Cross-reference `/workspace/epics/circulant-krr-climate/project.json`
   (current-state manifest) for cost ledger / verdict history /
   interventions ledger entries attributable to the window.
4. Write the report artifact per the criteria above.

Extension steps (token audit):

5. Inventory `dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/`
   (`session.jsonl` + `subagents/*/session.jsonl`); parse
   `assistant/chunk` events whose `chunk.type == "usage"`.
6. Aggregate input/output/cacheRead per usage event; bucket by event
   timestamp against phase cutoffs (13:38, 17:32, 21:24, 03:30, 03:45 UTC);
   split principal vs subagent sessions; also count subagent sessions per
   creation phase.
7. Extract `goal/change` events (create/pause/complete/block) to date
   principal-side goal bookkeeping and the iteration-2/3 boundary; extract
   `user/message` events with source kind `user` to date the human
   directives/interventions (21:22:46, 23:29:29, 23:39:51, 02:31:22).
8. Compare measured vs ledger estimates (report.md 2.1); write
   `token-audit.md`; correct report.md sections 2.1/3/4; append comment;
   record resolution.

## Proposed Approach

- Original report: gather 84 files (51 iteration-1 + 33 iteration-2), write
  `report.md`, note ledger estimates as estimates. (Done 2026-09-02.)
- Token audit: python3 aggregation over the 74 JSONL logs (~171 MB) - sum
  usage events per phase; two independent implementations for verification;
  measured-vs-estimate table (window estimated ~1,081k; measured on the
  order of ~200M, cache-dominated). Phase boundaries from the report's own
  cutoffs plus goal-event timestamps; iteration-3-start consumption
  disclosed separately (semantically excluded, timestamped in-window).
- Corrections: report.md 2.1 (measured figures, estimates retained),
  section 3 (human `user`-message record dated; goal bookkeeping attributed
  to the principal), section 4 (limitations updated).
- Deliver: `token-audit.md` (methodology + tables), corrected `report.md`,
  reopen comment + completion comment, resolution recorded.

## Files / Modules

- `report.md` (updated - sections 2.1/3/4 corrected, pointer to token-audit)
- `token-audit.md` (new - main audit artifact: methodology, tables,
  boundary/intervention findings)
- `dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/` (evidence -
  DSH session logs added by the human 2026-09-02; read-only input)
- `ISSUE.md` (this file)
- `comments/` (thread via add-comment)

## Comments

_Threaded conversation, chronological, newest last; appended via
add-comment. Author-anonymous (**Agent** tag)._

## Resolution & PRs

- `2026-09-02` -- Original report produced: `report.md` written from 84
  gathered orchestration files (51 iteration-1 + 33 iteration-2, all
  < 2026-09-02T00:00). The iteration-3 directive
  `20260902T0000-directive-iteration-3-novelty-upgrade.md` is **excluded**
  per the request; latest included file is
  `orchestration-log/comments/20260901T0330-final-validator-clean.md`.
  Report covers the research loop (iteration-1 recap + iteration-2:
  ideation r2 cap-stop, hypothesis gate FAIL x2 -> routing to literature
  rework, ideation r3 re-entry + gate PASS, execution verification,
  analysis gate PASS, writeup gate r1 FAIL -> r2 PASS, final validation;
  ~13 h 52 min window, iteration-2 span ~6 h 6 min), tool usage (token
  ledger estimates, window total ~1,081k; compute envelope; Tavily /
  web-verified entries) and human interventions (none attributed to a
  human inside the window; the iteration-3 directive - first ledger entry
  explicitly "human directive:" - is the excluded cutoff). Acceptance
  criteria checked; completion comment appended; issue resolved.
- `2026-09-02` -- Token-estimation extension resolved: the human-added DSH
  session logs (74 sessions: 1 principal + 73 subagents, ~171 MB, all events
  < 2026-09-02T00:00) were audited (see `token-audit.md`; three independent
  aggregation passes + independent reviewer, verdict APPROVE). Measured
  window consumption: **203,334,869 tokens** (5,268,139 in / 1,449,002 out /
  196,617,728 cache-read; 1,625 LLM calls; principal 132,942,733 / 993 calls,
  subagents 70,392,136 / 632 calls) = **~188x** the ~1,081k ledger estimate,
  cache-dominated (96.7%); iteration-1 phase 43,022,717 (~62x), iteration-2
  phase 157,281,952 (~405x). Boundary anomaly (F3): iteration-3 directive
  was a human message 2026-09-01T02:31:22Z; goal record 02:34:12Z
  (principal-side bookkeeping); first goal round 03:45:08Z; in-session
  iteration-3 start 03:45 -> 22:05 (56 turns, 32 subagents, 2,110 calls,
  248,156,771 tokens) disclosed, excluded from window totals. Human
  interventions corrected (report 2.1/2.3/3/4 + Appendix C updated): user
  messages 21:22:46 (iteration-2 directive), 23:28:44 (GUI-side goal pause),
  23:29:29 (references/4-page rule), 23:39:51 (paper review), 02:31:22
  (iteration-3 directive); goal create/complete recognized as principal-side
  bookkeeping. Tavily metered: 94 in-window calls + 6 iteration-3 start.
  Acceptance criteria checked; completion comment appended; issue resolved.
- Resolution type: `fixed`

## Notes

- Cutoff = the orchestration-log comment `20260902T0000-directive-iteration-3-novelty-upgrade.md`
  (iteration-3 human novelty-upgrade directive) - **excluded** per the
  request. Latest included file: `orchestration-log/comments/20260901T0330-final-validator-clean.md`.
- Sibling report for the iteration-1-only window:
  `/workspace/epics/circulant-krr-climate/issues/iteration-1-research-loop-report/report.md`.
- The cost ledger and interventions ledger live in
  `/workspace/epics/circulant-krr-climate/project.json`; token figures were
  documented manager estimates - **superseded on 2026-09-02 by the metered
  session-log audit** (see `token-audit.md` and report.md 2.1).
- Session logs added by the human: `dsh-session-session-8b1c9954-14b0-4216-aaac-516b5b2342a2/`
  (74 logs, 2026-08-31T12:41:33Z -> 2026-09-01T22:05:35Z, all events before
  the 09-02T00:00 thread directive).
- Boundary anomaly (to be documented in the audit): iteration-3 goal created
  2026-09-01T02:34:12Z and in-session iteration-3 execution 03:45 -> 22:05
  both predate the thread's 09-02T00:00 directive comment.
- Human-intervention evidence (authoritative = `user`-kind messages; goal
  `create`/`complete` events are principal-side bookkeeping): iteration-2
  directive message 2026-08-31T21:22:46Z ("As research manager, ..."),
  references/4-page rule 23:29:29Z, paper review (related works / figures)
  23:39:51Z, GUI-side goal pause 23:28:44Z, iteration-3 directive message
  2026-09-01T02:31:22Z ("From human review, the novelty is still a bit
  weak ...").