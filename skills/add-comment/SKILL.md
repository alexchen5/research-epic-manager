---
name: add-comment
description: |
  This skill should be used when the user or the issue manager asks to
  "add a comment", "post a comment", "comment on the issue", "leave a
  comment", "append a comment", or "update the thread", or references
  EPICS_ROOT/ comments. Appends a single chronological comment to an
  existing issue's comments thread at
  EPICS_ROOT/<epic>/issues/<issue>/comments/. Per the issue-manager
  protocol, only the issue manager may add comments - coding and reviewer
  sub-agents report to the issue manager instead. Enforces comment best
  practices - comments are reserved for debate and updates on how the ticket
  is being solved, are logged chronologically (newest last), and are kept
  author-anonymous so humans and agents are not treated differently.
triggers:
  - add comment
  - post comment
  - comment on the issue
  - leave a comment
  - append comment
  - update issue comments
---

# Add Comment

Append a single comment to an existing issue's chronological thread of
discussion. A comment is a dated, threaded note on how a ticket is being (or
was) solved - the equivalent of a comment on a GitHub issue. Comments live as
individual files in the issue's `comments/` directory and mirror the thread
conventions users already expect on issue trackers.

## Layout

Comments live alongside the issue, under the issue's `comments/` dir:

```
<issue>/
|-- ISSUE.md          # the issue (from the add-issue template)
|-- comments/         # chronological thread of comments (newest last)
|   |-- 2026-07-23T0200-3rd-party-lib.md
|   |-- 2026-07-23T0930-auth-retry-loop.md
|   `-- ...
`-- resolution.md     # how/why it was resolved (once closed)
```

## When to use this skill

Use whenever a comment should be added to an **existing** issue - the request
comes from the user or from the issue manager (the parent chat working the
issue). Examples: "note an alternative approach", "flag a discovered
constraint", "log a decision reached while working the ticket",
"record why an approach was abandoned", "tag a follow-up".

Do **not** use this skill to edit the issue body (ISSUE.md), resolve the
issue (`resolution.md`), or change its status - those live in the
`add-issue` skill's flow.

## Only the issue manager adds comments

Per the tracker's issue-manager protocol (see the `issue-manager` skill), the
issue manager - the parent chat working the issue - is the only role that
appends to an issue's thread. Coding and reviewer sub-agents never write
comments themselves; they report their findings to the issue manager, which
records them with this skill. This keeps the thread consistent, unbiased,
and owned by the same role that owns the issue state.

## Best practices (must read)

Read `references/comments-best-practices.md` before writing a comment. The
non-negotiable rules:

1. **Comments are for debating how to solve the ticket** - progress reports,
   decisions, trade-off discussions, open questions, dead-ends. They are
   **not** a log of task chatter about the issue tracker itself. If the
   comment is not about solving the ticket, don't post it.
2. **Anonymous - never sign as a user or agent.** Comments use a stable,
   shared directory-ish tag (`**Agent**`) rather than any human handle,
   agent name, or model. This removes bias between who (human vs agent)
   commented. Never write `@firstName`-style human names in the `**@author**`
   field; see step 4.
3. **Chronological, append-only.** New comments are appended at the end of
   the thread (newest last). Never rewrite or reorder historical comments.
4. **Status is tracked in Metadata, not in comments.** Status changes and
   resolution happen in ISSUE.md / resolution.md. Comments capture the
   narrative around those changes, not the change itself.
5. **One comment = one point.** Split distinct topics into separate comments
   so threads stay reviewable.
6. **Dated.** Every comment gets a timestamp (ISO `YYYY-MM-DDThhmm`). This
   keeps the thread ordered and unambiguous.

## Procedure

1.  Resolve the issue dir and confirm it has a `comments/` directory:
    ```bash
    issue_dir=EPICS_ROOT/<epic>/issues/<issue>
    if [ ! -f "$issue_dir/ISSUE.md" ]; then
        echo "error: issue '<issue>' not found under epic '<epic>'" >&2; exit 1
    fi
    mkdir -p "$issue_dir/comments"
    ```
    The issue must already exist (see the `add-issue` skill).

2.  Read the existing thread so you don't repeat or contradict it, and follow
    the best-practices file (it lives in this skill's `references/` directory -
    the skill loader provides the skill's base path when the skill is loaded):
    ```bash
    cat <skill-dir>/references/comments-best-practices.md
    ls "$issue_dir/comments"
    ```

3.  Write the comment as a new markdown file in `comments/` (the script lives
    in this skill's `scripts/` directory):
    ```bash
    python3 <skill-dir>/scripts/add-comment.py \
        "<epic>" "<issue>" "<Comment body text>" \
        [--ts 'YYYY-MM-DDThh:mm'] [--kind <kind>] \
        [--summary "<one-line summary>"] \
        [--context "<context text>"] \
        [--references "<references text>"]
    ```
    The script slugifies the body into a `YYYY-MM-DDTHHMM-<slug>.md` filename,
    stamps it with the timestamp, writes the comment file, and returns its
    path. The generated file contains **only real content**: it always has the
    `# <timestamp> -- <kind>` heading and the anonymous `**Agent**: <body>`
    line, and each optional piece appears **only when its flag is given** -
    omitted flags leave no empty header and no instructional prose behind:

    - `--summary` - rendered as a `> <summary>` blockquote directly under the
      heading.
    - `--context` - rendered as a `## Context` section after the `**Agent**`
      line.
    - `--references` - rendered as a `## References` section at the end.

    The content follows the `assets/comment.template.md` skeleton and the
    anonymity rules in the best practices file.

    The script resolves the issue directory from EPICS_ROOT/<epic>:
    ```bash
    python3 <skill-dir>/scripts/add-comment.py \
        "<epic>" "<issue>" "<Comment body text>"
    ```

4.  Verify:
    ```bash
    cat EPICS_ROOT/<epic>/issues/<issue>/comments/<newest-comment>.md
    ls -1 EPICS_ROOT/<epic>/issues/<issue>/comments
    ```

## Comment identity

Comments are **anonymous** - they use a stable, shared tag (`**Agent**`)
instead of any human or agent identity. Do **not** include the name of the
person, the agent, the model, or the tool that wrote the comment. This is
deliberate: when readers see a comment, they should focus on the content, not
on whether it came from a human or an agent, which removes bias in how the
comment is weighed.

Do still attribute *decisions and quoted statements* where the source matters
for the record (e.g. "per the maintainer, we will drop TLS 1.1") - you may
refer to who made a decision, just do not tag the comment as authored by them.


## Additional Resources

- **`references/comments-best-practices.md`** - the comment guidelines
  (when to comment, what to include, tone, anonymity, threading).
- **`assets/comment.template.md`** - the comment skeleton the `add-comment`
  script fills in. The heading and the `**Agent**` line are always rendered;
  the `> {summary}` blockquote, the `## Context` section, and the
  `## References` section are rendered only when the matching
  `--summary` / `--context` / `--references` flag is given (otherwise the
  whole section, header included, is stripped from the output).
- **`scripts/add-comment.py`** - helper that appends the comment file with a
  timestamp and returns its path.

## Related skills

- **`add-issue`** - creates the issue (and its `comments/` dir).
- **`add-epic`** - creates the epic that scopes issues.