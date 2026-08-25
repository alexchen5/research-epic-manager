---
name: add-issue
description: |
  This skill should be used when the user asks to "add an issue", "create an issue",
  "new issue", "open an issue", "file an issue", or references EPICS_ROOT/.
  Adds a single issue scoped to an existing epic. Each issue lives at
  EPICS_ROOT/<epic>/issues/<issue> as a well-organised ISSUE.md template with an
  issue lifecycle: status, priority, assignees, labels, acceptance criteria,
  PRs, comments and resolution.
triggers:
  - add issue
  - create issue
  - new issue
  - open an issue
  - file an issue
  - EPICS_ROOT/
---

# Add Issue

Create a new issue scoped to an already-existing epic. An issue is a single
unit of actionable work inside an epic - the equivalent of a GitHub issue. It has
a lifecycle (draft -> open -> blocked -> resolved/closed), comments, a resolution,
and linked pull requests, mirroring how user queries are tracked on GitHub.

## Layout

Each issue lives at `EPICS_ROOT/<epic>/issues/<issue>`:

```
<issue>/
|-- ISSUE.md          # the issue (from template)
|-- comments/          # chronological thread of comments (append via add-comment skill)
`-- resolution.md      # how/why it was resolved (once closed)
```

## When to use this skill

Use when the user wants to plan individual pieces of work inside an existing epic -
e.g. "add an issue for the login flow", "file an issue for the dashboard",
"create an issue to track the new API". The epic must already exist (see the `add-epic` skill).

## Procedure

1.  Confirm the target epic exists and resolve issues dir:
    ```bash
    issues_parent=EPICS_ROOT/<epic>/issues
    if [ ! -d "EPICS_ROOT/<epic>/issues" ]; then
        echo "error: epic '<epic>' missing or has no issues dir" >&2; exit 1
    fi
    ```

2.  Create the issue (the script lives in this skill's `scripts/` directory -
    the skill loader provides the skill's base path when the skill is loaded):
    ```bash
    python3 <skill-dir>/scripts/add-issue.py \
        "<epic>" "<issue name>" 
    ```
    This writes `EPICS_ROOT/<epic>/issues/<issue>/ISSUE.md` from the
    `ISSUE.template.md` template and returns the created issue dir.

3.  Verify:
    ```bash
    cat EPICS_ROOT/<epic>/issues/<issue>/ISSUE.md
    ls EPICS_ROOT/<epic>/issues
    ```

The `ISSUE.template.md` starts as a well-organised template with Metadata,
Description, Acceptance Criteria, Repro/Steps, Proposed Approach, Files, Comments,
Resolution & PRs, and Notes sections - fill in each as the issue evolves.

Add comments to an issue after it is created with the **`add-comment`** skill,
which appends author-anonymous, chronological comments (see its
`references/comments-best-practices.md`). Comments are never stored with a
human or agent identity.

## Draft-first lifecycle (default)

New issues are created with **status `draft`** by default. A draft is a stub: it
is a skeleton from the template (empty Description, unchecked Acceptance Criteria,
placeholder tokens). It is **not** picked up by the autonomous lifecycle
tracker (which only drives issues with status `open`, `blocked`, `resolved`,
or `closed`).

### Promoting a draft

To move a draft into the autonomous flow, it must first be **authored**
(fill in the Description, check off the acceptance criteria you can verify,
delete the template placeholders) and then promoted:

```bash
python3 <skill-dir>/scripts/add-issue.py --promote \
    "<epic>" "<issue>"
```

The `--promote` flag (or the backward-compat `promote-issue.py`) runs a **final
readiness check** and flips the status from `draft` to `open` only if the issue
is genuinely ready to be worked:

- the Description section has real (non-template) content, and
- at least one Acceptance Criterion is checked (`- [x]`), and
- no template placeholders remain (empty Description filler, unfilled
  criteria, `path/to/file`).

If any of these fail, the issue stays `draft` and the script exits non-zero
and lists what is missing. Use `--force` to promote anyway (not recommended -
you are bypassing the guard that keeps half-written issues out of the
autonomous pipeline).

> **Why?** A sub-agent only gets one shot per assignment. A half-authored
> draft (vague description, no checked criteria) would waste the run and leave
> the issue in an ambiguous state. The draft gate guarantees every issue that
> reaches `open` is actionable.

### One-shot creation with `--status open` and `--body`

If you already have the full issue content ready, pass `--status open` at
creation time to skip the draft stage entirely:

```bash
python3 <skill-dir>/scripts/add-issue.py --status open \
    "<epic>" "<issue name>"
```

The `--status open` flag creates the issue directly in `open` state - no
promotion step needed.

You can also pass the full content inline with `--body` - the argument is
literal markdown text, written verbatim as the issue body. For large content,
pipe from a file or heredoc:

```bash
# From a heredoc:
python3 <skill-dir>/scripts/add-issue.py \
    --body "# My Issue

## Metadata
- **Status:** `open`
...

" \
    "<epic>" "<issue name>"

# From a file:
python3 <skill-dir>/scripts/add-issue.py \
    --body "$(cat /path/to/issue-body.md)" \
    "<epic>" "<issue name>"
```

When `--body` is combined with `--status open`, the issue is fully realised
in one step: ready to be picked up by the issue manager.


## Additional Resources

- **`assets/ISSUE.template.md`** - the ISSUE.template.md skeleton that the
  `add-issue` script fills in (kept here for reference/linking).
- **`scripts/add-issue.py --promote`** - the draft->open readiness gate (see
  "Draft-first lifecycle" above). **`scripts/promote-issue.py`** is a
  backward-compatible wrapper for the same flag.