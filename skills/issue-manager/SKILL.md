---
name: issue-manager
description: |
  Use this skill when a chat is asked to work on, execute, progress, resolve,
  or close an issue under EPICS_ROOT/. - "work on issue X", "execute this
  issue", "pick up issue", "close issue", "issue manager". Defines the
  issue-manager protocol: the parent chat working an issue is the issue
  manager - the only role allowed to change issue state, append issue
  comments, and dispatch sub-agents. Coding and reviewer sub-agents are
  isolated from issue concepts and interact only with the issue manager.
triggers:
  - work on issue
  - execute issue
  - pick up issue
  - close issue
  - resolve issue
  - issue manager
---

# Issue Manager

Protocol for working an issue in the `EPICS_ROOT/` tracker. When a chat is
asked to work on an issue, **that chat is the issue manager** for the duration
of the work. This skill is normative for the parent chat; the mechanics of
dispatching the sub-agents live in the `issue-subagent-orchestration` skill.

## Roles

| Role | What it is | May do |
|---|---|---|
| **Issue manager** | The parent chat working the issue (you) | Read/write the issue (status, metadata, resolution), append comments via the `add-comment` skill, dispatch sub-agents, verify results, close the issue |
| **Coding agent** | A dispatched sub-agent (fresh context) | Edit project code/files and report results **to the issue manager only** |
| **Reviewer agent** | A dispatched sub-agent (fresh context) | Read code + requirements and report a verdict **to the issue manager only** |

## Hard rules

1. **Only the issue manager mutates issue state.** Status, metadata, and
   resolution are written to `ISSUE.md` by the issue manager alone.
2. **Only the issue manager appends issue comments** (via the `add-comment`
   skill). Coding/reviewer agents never write to the tracker.
3. **Only the issue manager dispatches agents.** No agent-to-agent
   communication exists in this protocol - every sub-agent's results return
   to its dispatcher (the issue manager), which is how the harness works
   natively.
4. **Coding/reviewer agents have no idea about the concept of issues.** Their
   briefs contain no paths under `EPICS_ROOT/`, no `ISSUE.md` content, no
   lifecycle vocabulary (open/blocked/resolved/closed/...), and no comment
   protocol. They receive a self-contained engineering task: files,
   requirements (the acceptance criteria rephrased as task requirements),
   done criteria, out-of-scope. If a sub-agent needs information that lives
   in the issue thread, the issue manager retrieves it and passes it in a
   follow-up brief - the sub-agent never reads the tracker itself.
5. **The manager orchestrates; agents implement.** The issue manager does not
   write code itself, except when the user explicitly asks the manager to
   make a change directly.

## Working an issue - standard flow

1. **Read the issue.**
   `cat EPICS_ROOT/<epic>/issues/<issue>/ISSUE.md` and skim the thread in
   `comments/`. If the status is `draft`, author and promote it first (via
   `add-issue --promote` or the `promote-issue.py` wrapper).
2. **Claim it.** Set `Status: open` in ISSUE.md Metadata if it is not already
   `open` (update the `Updated` date).
3. **Plan the dispatch.** Decide how to split the work (single coder vs.
   parallel modules) - see `issue-subagent-orchestration`.
4. **Dispatch coding agent(s)** with self-contained briefs (templates in
   `issue-subagent-orchestration`).
5. **Verify before believing.** When a coder reports, the issue manager
   re-runs the key verification (tests/build/lint) itself. A coder's
   self-report is a claim, not evidence.
6. **Dispatch a reviewer** with the changed files + the requirements.
7. **Act on the verdict.**
   - `APPROVE` -> record the resolution in ISSUE.md (`Resolution & PRs`), set
     `Status: resolved` (or `closed`), and append one summary comment via
     `add-comment` if there is narrative worth recording.
   - `REJECT` -> send the findings back to the coder (`send_message` to the
     same sub-agent, or a fresh dispatch) and repeat. After 3 rejected
     rounds, stop and escalate: set `Status: blocked` with a comment
     explaining the loop.
8. **Blocked?** Set `Status: blocked` and append a comment recording the
   blocker (what is missing, what unblocks it).

## State machine

```
draft -> open -> resolved
         \
          blocked -> open -> closed
```

- Status lives in `ISSUE.md` Metadata and is written only by the issue
  manager.
- The `## Comments` section of `ISSUE.md` is **reserved** - actual comments
  live as files in `comments/` (one file per comment, via `add-comment`);
  never write ad-hoc notes into the ISSUE.md section.
- Every non-trivial state transition gets a comment **only when there is
  narrative worth recording** (decision, blocker, resolution) - see
  `add-comment/references/comments-best-practices.md`. Status changes
  themselves are not commented.

## What the issue manager never does

- Lets a sub-agent touch `EPICS_ROOT/` (no issue paths in briefs).
- Marks an issue resolved on a coder's self-report without manager-side
  verification and a reviewer verdict.
- Dispatches agents "to read the issue" - briefs are the contract.
- Edits historical comments (append-only thread).

## Related skills

- **`issue-subagent-orchestration`** - the DSH-native dispatch mechanics
  (tools, brief templates, review loop, parallelism).
- **`add-issue`** - creates issues; owns the draft -> open readiness gate.
- **`add-comment`** - appends comments to the thread.
- **`add-epic`** - creates the epic that scopes the issue.