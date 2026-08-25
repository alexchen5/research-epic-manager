# EPICS_ROOT - the issue tracker

This file is the tracker contract for a file-based issue tracker (epics ->
issues -> comments). Treat it as the entry point: read it before adding
epics/issues/comments or working any issue.

## Paths

This repo's skills and scripts are relocatable: absolute machine-local paths
are written as `WS_ROOT` / `EPICS_ROOT` prefixes, never hard-coded values, so
the same files work on any machine.

- `WS_ROOT` - the workspace/harness root (default `/workspace`; user-editable).
  If your layout differs, edit this definition.
- `EPICS_ROOT` - the tracker root where the epics/issues/comments live
  (default `/workspace/epics`; user-editable; expected to sit under WS_ROOT but
  may be anywhere). If your layout differs, edit this definition.

## Layout

```
EPICS_ROOT/
|-- AGENTS.md            # this file - the tracker contract
|-- <epic>/
    |-- EPIC.md          # scope, goals, issues index, auto issue generation
    `-- issues/
        `-- <issue>/
            |-- ISSUE.md     # the issue: metadata, description, acceptance criteria
            `-- comments/    # history - one file per comment, chronological, newest last
```

## Project skills

The tracker's skills live in the shared harness-level discovery root at
`WS_ROOT/.dsh/skills/`, which DSH discovers automatically when the current
working directory is under `EPICS_ROOT/`:

```
WS_ROOT/.dsh/skills/
|-- add-epic/                       # create an epic
|-- add-issue/                      # create an issue (draft-first lifecycle)
|-- add-comment/                    # append an anonymous chronological comment
|-- issue-manager/                  # protocol for working an issue
|-- issue-subagent-orchestration/   # DSH-native sub-agent dispatch mechanics
`-- research-project-epic-manager/  # 5-phase project orchestration (built on these)
```

## Workflow

1. **Epic** - a new body of related work starts with `add-epic`. `EPIC.md`
   describes the scope (Goals, Non-Goals, Scope); its **Auto Issue
   Generation** section will describe how issues for the epic are generated
   automatically. Keep the Issues table in `EPIC.md` current.
2. **Issue** - a unit of work inside an existing epic, via `add-issue`.
   The default is draft-first (author the description, check acceptance
   criteria, remove placeholders, then promote to `open`). For a one-shot
   creation pass `--status open` to skip the draft stage; use `--body` to
   write the full content inline.
3. **Comments** - history only, via `add-comment`. The `## Comments` section
   inside `ISSUE.md` is **reserved** - never write ad-hoc notes there;
   comments are files in `comments/`.
4. **Working an issue** - follow the `issue-manager` skill. Summary:
   - The chat working the issue **is** the issue manager.
   - **Only the issue manager** changes issue state (ISSUE.md) and appends
     comments.
   - **Only the issue manager** dispatches agents.
   - Coding/reviewer sub-agents are **isolated from issue concepts** (no
     tracker paths, no lifecycle vocabulary) and talk only to the issue
     manager - results return to the dispatcher.
   - Dispatch mechanics: the `issue-subagent-orchestration` skill.
5. **Lifecycle** - `draft -> open -> resolved/closed` (with `blocked` as a
   side state that returns to `open`). Status lives in `ISSUE.md` Metadata.

## Conventions

- Comments are **author-anonymous** (shared `**Agent**` tag - no human or
  agent names), chronological with newest last, one comment = one point, and
  reserved for the narrative of solving the work (decisions, trade-offs,
  blockers) - see `.dsh/skills/add-comment/references/comments-best-practices.md`.
- A coder's self-report is a claim: the issue manager re-runs verification
  and gets a reviewer verdict before marking anything `resolved`.
- Git: the top-level git repository of `WS_ROOT` tracks the tracker
  (`EPICS_ROOT`) and the `WS_ROOT/.dsh/` discovery roots. Workspaces (the
  project directories next to `EPICS_ROOT`) are gitignored here: each
  workspace is tracked by its own **local-only** git repository with no
  remote. `EPICS_ROOT` contains no child git repositories. Commit tracker
  changes in the `WS_ROOT` repo; commit workspace work in the workspace's
  own repo.

## Validation batteries

Each tracker skill carries a stdlib-only validation script in its own
`scripts/` directory - `add-epic/scripts/test_add_epic.py`,
`add-issue/scripts/test_add_issue.py`, `add-comment/scripts/test_add_comment.py`,
and `issue-manager/scripts/test_lifecycle.py`. The first three drive the real
skill scripts against a self-deleting scratch epic under `EPICS_ROOT`
(`test-scratch-*` dirs, removed on exit unless `--keep`); `test_lifecycle.py`
additionally enforces cross-cutting invariants (discovery roots, git hygiene,
layout invariants over every epic/issue, and the ASCII-only rule for all .md
files). Run all with exit code 0 as the end-to-end sanity check for the
tracker (the canonical result log is kept on the tracker's own test issue).