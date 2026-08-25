# Comments - Best practices

Comments are the conversation thread of an issue. They capture *how a ticket
is being solved* - the debate, the decisions, and the updates - rather than
tracker housekeeping. This file is normative: every agent or human that adds
a comment to an issue follows it. In this tracker only the issue manager adds
comments (see the `issue-manager` skill) - sub-agents report to it instead.

## 1. Comments are reserved for debates on solving the ticket

A comment belongs in the thread when it moves the ticket forward:

- A proposed approach or alternative to the one in ISSUE.md.
- A trade-off discussion ("we could X, but Y is cheaper because ...").
- A decision reached while working the ticket, and why.
- A discovered constraint, dead-end, or blocking detail.
- An open question that needs an answer before continuing.
- A status/update tied to the work itself (what changed and why).

A comment does **not** belong when it is tracker chatter that does not help
solve the ticket:

- Meta notes about the tracker ("moving this to blocked", "label added").
- Acknowledgements with no new information ("+1", "noted").
- Duplicates of what the thread or ISSUE.md already records.

When in doubt, ask: "does this help the next reader solve or review the
ticket?" If no, skip it.

## 2. Stay chronological and append-only

- The thread is ordered oldest -> newest, newest last.
- New comments are always appended at the end - never rewrite, reorder, or
  delete an existing comment.
- One comment = one point. Split distinct topics into separate comments so
  the thread stays reviewable and individual items can be referenced.
- Every comment carries a timestamp (`YYYY-MM-DDThh:mm`) so ordering and
  chronology are unambiguous.

## 3. Author-anonymous to reduce user-vs-agent bias

Comments must not reveal *who* wrote them - neither a human handle nor an
agent/model name. All comments share a stable, neutral tag: `**Agent**`.

Why: comments are weighed on their content. When readers can tell a comment
came from a human vs. an agent, they unconsciously weight one more heavily.
Removing authorship reduces that bias and keeps the thread about the work.

Concretely:

- Do **not** write `**@FirstName**:`, `**@agent-name**:`, or any model name in
  the comment author slot.
- Do **not** say "I (as the human)" / "the sub-agent thinks". Write plainly.
- You *may* attribute a decision or a quote where the source matters for the
  record ("per the maintainer, we drop TLS 1.1"), but the comment itself is
  still not signed by you.

## 4. Track status in Metadata, comment the narrative

Status, priority, assignees, and resolution belong in ISSUE.md's Metadata and
in `resolution.md`. Comments capture the *narrative* around those changes
(what was decided and why), not the change itself. When you change a ticket's
status, update Metadata; add a comment only if there is a reason worth
recording.

## 5. Tone

- Plain, direct, factual - the reader is a coworker, human or agent.
- Front-load the point; one comment, one idea.
- Quote or link the specific file / ISSUE.md section you reference.
- Ask the question or state the decision explicitly so the thread is
  actionable, not merely descriptive.

## Template

The `../assets/comment.template.md` template provides a stable format:
timestamp, a one-line summary, the anonymous body, context, and references. See
the `add-comment` skill for the append procedure.