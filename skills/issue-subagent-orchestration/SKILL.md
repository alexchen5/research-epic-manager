---
name: issue-subagent-orchestration
description: |
  Use this skill when the issue manager (see the issue-manager skill) needs to
  dispatch coding and reviewer sub-agents for an issue under EPICS_ROOT/.
  Covers the DeepSeek Harness native delegation tools - subagent,
  subagent_fork, send_message, interrupt_agent, job_output, job_list,
  workflow - with self-contained brief templates that keep coding/reviewer
  agents isolated from issue concepts, a reviewer verdict format,
  manager-side verification, and the review loop before an issue may be
  marked resolved.
triggers:
  - dispatch coding agent
  - dispatch reviewer
  - issue sub-agent
  - sub-agent orchestration
  - work on issue
---

# Issue Sub-Agent Orchestration (DSH-native)

How the issue manager actually spawns and drives sub-agents on the DeepSeek
Harness. The *protocol* (who may do what) is the `issue-manager` skill; this
skill is the *mechanics*.

## Tool map

| Need | Tool |
|---|---|
| New coding agent, fresh context (default) | `subagent` - use `run_in_background: true` for anything beyond a couple of minutes |
| Coding agent that genuinely needs this conversation's context | `subagent_fork` (rare - see anti-patterns) |
| Follow-up round on an existing coder (reviewer findings) | `send_message` to the same sub-agent id |
| Stop a runaway agent's current turn | `interrupt_agent` |
| Collect a background result | `job_output` (use `wait: true` only when genuinely blocked); `job_list` to track |
| Large parallel fan-out (several issues/modules at once) | `workflow` - only for real multi-agent fan-out; for one or two dispatches use plain `subagent` calls |
| One long objective spanning many rounds | goal tools (a single issue normally does not need this) |

## The isolation contract (normative)

Sub-agents are isolated from the tracker by construction: a fresh `subagent`
spawn sees no conversation, so the brief is everything.

**Never in a brief:** paths under `EPICS_ROOT/`, the words "issue", "epic",
"ticket", "status" in the tracker sense, ISSUE.md content as such, the
comment protocol, or any lifecycle vocabulary.

**Always in a brief:** working directory; the task in plain engineering
terms; exact files/modules to touch; the acceptance criteria rephrased as
testable task requirements; explicit done criteria; out-of-scope; and the
report contract (what to say back).

## Coding-agent brief template

```
You are a coding agent. Working directory: WS_ROOT/<project>

Task: <one-paragraph engineering statement, no tracker vocabulary>

Files / modules to touch:
- <path>

Requirements (ALL must hold when you finish):
1. <acceptance criterion, rephrased as a testable requirement>
2. ...

Do not modify: <out-of-scope files/areas>

When done, report:
- what changed (files + one-line rationale each)
- verification you ran (commands + their results)
- open risks / follow-ups
```

## Reviewer-agent brief template

```
You are a code reviewer. Working directory: WS_ROOT/<project>
Review ONLY - do not edit any file.

Changes to review: <files, or a diff summary the manager prepared>

Requirements the change must satisfy:
1. <same testable requirements the coder got>

Check: correctness against the requirements, regressions, obvious
maintainability problems, consistency with surrounding code.

Report:
- Verdict: APPROVE or REJECT
- Findings: numbered list, each with file:line, severity (blocker/major/minor),
  what, why it matters, and a concrete suggested fix
```

A reviewer that edits is a bug in the process - the brief forbids it and the
manager should not dispatch a reviewer with edit intent.

## The loop

1. Dispatch the coder as a **background** subagent (`run_in_background: true`).
   **End your turn** - do NOT busy-sleep. The DSH runtime will notify you
   when the subagent finishes.
2. **Manager-side verification:** re-run the key commands (tests, build,
   lint) yourself. Do not trust the report's claims.
3. Dispatch the reviewer with the changed files + requirements. Collect the
   verdict.
4. `APPROVE` -> issue-manager flow step 7 (record resolution, close).
   `REJECT` -> `send_message` the findings to the same coder (fresh `subagent`
   if the original settled or failed) with the instruction to fix the listed
   findings and re-report. Repeat from step 2. **Cap at 3 rounds**; then
   `Status: blocked` + comment (issue-manager flow step 8).

## Parallelism

- **Independent modules of one issue, no shared files:** dispatch multiple
  coders in parallel (all `run_in_background: true`), collect all results,
  verify, then run ONE review over the combined change.
- **Multiple issues:** sequential dispatches are the norm. Use a
  `workflow` script (pipeline over issue briefs) only when the user asks for
  large-scale orchestration.
- Never dispatch two coders over overlapping files.

## Anti-patterns

- **Sleeping for sub-agents.** `bash sleep`, `time.sleep()`, or any busy-wait
  loop instead of ending your turn. The DSH runtime notifies you when a
  background subagent finishes - use that signal. If you stay in your turn
  and sleep, you waste context window and look unresponsive. Dispatch with
  `run_in_background: true`, then end your turn.
- **Forking by default.** `subagent_fork` seeds the child with the whole
  conversation - which includes the issue discussion, breaking isolation.
  Spawn fresh; fork only when the prior context is genuinely load-bearing
  (e.g. continuing a long debugging thread inside the same project work).
- **Briefs that name the issue.** "Fix the login-flow issue (#42)" in a
  brief is a leak; rephrase as the engineering task.
- **Reviewing on the coder's say-so.** No manager verification + no reviewer
  verdict = no `resolved`.
- **Interrupting to redirect.** `interrupt_agent` stops a turn; it does not
  change the task. Redirect with `send_message` (queued next turn).
- **Letting a sub-agent chase the tracker.** If a coder asks "what's the
  issue?", answer with task context - never with the tracker path.