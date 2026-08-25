# Communication Logging

This reference defines who writes what, when, in the research-project
protocol: the communication logging contract (writers table, directive
dual-write, issue-manager transitions, orchestration-log re-scoping,
no busy-waiting, user input handling), the validator-keyed marker set,
and comment ownership.

## Communication Logging Contract (normative)

**Who writes what, when:**

| Writer | Surface | Writes | When |
|--------|---------|--------|------|
| Epic manager | orchestration-log | Project-level events ONLY: phase transitions, gate invocations (round + derived verdict summary), routing decisions, whole-stage invalidations, blocks, autonomous decisions + rationale, project-level user-input summaries, settlement and synthesis summaries | At each such event; at each autonomous decision; on project-level user input |
| Epic manager | interventions ledger (`project.json["interventions"]`) | `{ts, issue_id, directive_digest}` entry | Whenever it sends a directive (see dual-write rule below) |
| Epic manager | stage anchor issue | Gate critique comments (dispatcher-posted, `[review-critique: <gate>-r<round>]`), manager notices (`[manager-notice]`) for fallback/disabled/loop-limit verdicts | After each gate review; after each manager-generated verdict |
| Issue manager (incl. ideation issue-manager) | its own issue | Seeding comments (`[seeding]`), directive-mirror comments (`[directive: <digest>]`), own transitions (dispatch, completion, blocker), proposal revisions (`[proposal-v<n>]`), dispatcher-posted ideation critiques (`[review-critique: ideation-r<round>]`) | Before acting on a directive; at each transition; after each ideation round |
| Reviewer agents | (none) | Scoring JSON only, returned to their dispatcher | Per review request |
| Coding sub-agents | (none) | Findings to their issue manager only | Per dispatch |

**Directive dual-write rule (mandatory).** The epic-manager -> issue-manager
transport over DSH (subagent briefs, `send_message`) remains the transport,
but every directive that changes scope, adds a requirement, reroutes, or
requests revision is dual-written:

1. The DSH message itself EXPLICITLY instructs the receiving issue manager
   to append an author-anonymous comment to ITS issue BEFORE acting on the
   directive: the comment records the request, QUOTING the directive (the
   decisive sentence, verbatim), LINKING the touched artifacts (their
   workspace-relative paths), and carrying the marker `[directive:
   <digest>]` where `<digest>` matches the ledger entry the epic manager
   appends.
2. The epic manager appends the corresponding `interventions` ledger entry
   `{ts, issue_id, directive_digest}`.

Routine transport messages that do not change scope/requirements/route or
request revision (e.g. "continue", result collection) do not require a
mirror comment, but the epic manager still records significant ones.

**Issue-manager transitions.** Issue managers log own dispatch/completion/
blocker transitions as comments on their issue (anonymous `**Agent**`, one
point per comment); the structured DSH result stays the machine channel.

**Orchestration-log re-scoping.** The orchestration-log is re-scoped to
project-level events only. Per-stage work narrative lives in issue threads,
never on the orchestration-log.

### Marker set (used by the validators)

| Marker | Meaning | Check |
|--------|---------|-------|
| `[seeding]` | Creation seeding comment (anchor: stage goal + inputs + AC; rework: FAIL feedback) | Check 9 (liveness) |
| `[seeded-fail-feedback]` | FAIL feedback embedded in a rework issue's seeding comment | Check 8/9, gate routing |
| `[directive: <digest>]` | Directive-mirror comment quoting the request | Check 8 |
| `[human-directive: <digest>]` | Recording of routed user input on the affected issue (quoted/closely paraphrased, dated, with the epic manager's routing interpretation) appended before acting | Check 8 |
| `[proposal-v<n>]` | Ideation proposal revision comment | Check 11 |
| `[review-critique: <gate>-r<n>]` | Dispatcher-rendered reviewer critique | Check 10 |
| `[manager-notice]` | Manager notice for fallback/disabled/loop-limit verdicts; the block-linked variant `[manager-notice: block-linked to <route_to> FAIL]` records whole-stage invalidation on downstream open issues | Check 10 exemption; gate routing |

**No busy-waiting (normative).** The epic manager is a
idle delegator: it dispatches issue-manager sub-agents in the BACKGROUND,
ends its turn, and reacts to completion notifications and user input as they
arrive. It NEVER polls, sleeps, or busy-waits while agents work. The Phase C
dispatch loop is notification-driven (each iteration reacts to a completion
or interruption notification; late completions are dropped via
`stale_subagent_ids`), never a polling cycle.

**User input handling.** Because the epic manager is
otherwise idle, it IS the receiving FRONT END for user input during a run
and owns routing it into the tracker.

1. On user input mid-run, the epic manager identifies the affected
   issue(s) from the manifest (which issues/stages the input touches).
2. For each affected issue, it messages the owning issue manager over DSH
   (`send_message`) and instructs it to append a comment recording the user
   input BEFORE acting on it: the input is quoted or closely paraphrased,
   marked as a human directive (`[human-directive: <digest>]`) with its
   date, plus the epic manager's routing interpretation (what the input
   changes: scope, requirements, route, or a requested revision).
3. The routed input is an `interventions` ledger entry like any directive
   (`{ts, issue_id, directive_digest}`), so Check 8 parity covers it; the
   tracker thread remains the single durable record of why work changed
   course.
4. Scope: PROJECT-LEVEL inputs (e.g. synthesis format, add/drop a stage,
   budget) are ADDITIONALLY summarised on the orchestration-log; per-issue
   inputs land only on their issues. An override of a recorded decision is
   itself commented where it lands.
5. This mirrors the working pattern of the DSH tracker itself: directives
   arrive in chat, and each lands as an anonymous dated comment on the
   affected issue thread.

**Enforcement (forward references):**

- **Check 8 -- Directive-trail parity:** every `interventions` ledger entry
  has at least one matching `[directive: <digest>]` comment (or the
  human-input variant `[human-directive: <digest>]`) on the affected
  issue, and vice versa (digest match). A user-input routing is an
  interventions ledger entry like any directive. Implemented in
  `scripts/validate_execution.py` (new check; existing Checks 1-7 adapted to
  `stage_issues`).
- **Check 9 -- Thread liveness:** every non-control issue has at least one
  comment in its `comments/` directory. Seeding comments count toward
  liveness, so liveness holds by construction for JIT issues; the check
  still validates it.
- **Check 10 -- Reviewer-comment parity:** every `verdict_history` entry
  maps to at least one `[review-critique: <gate>-r<round>]` comment on that
  stage's anchor issue. Manager-generated entries (`fallback: true`, the
  disabled round-0 placeholder) and loop-limit synthetics are EXEMPT (a
  verdict_history mirror carries routing `"blocked"`; see
  `reviewer-briefs.md#reviewer-scoring-review-contract`), with a
  `[manager-notice]` comment instead of a rendered critique.
- **Check 11 -- Ideation evidence:** active ONLY when
  `ideation.max_rounds > 0`; requires >= 2 `[proposal-v<n>]` comments OR a
  recorded stop condition (`"ideation_disabled"` at max_rounds == 0).

---

## Comment Ownership

**Commenting rule:** Only the research-project-epic-manager (the top-level
orchestrator) calls `add-comment` on the orchestration-log, and only for
project-level events (phase transitions, gate invocations, routing decisions,
blocks, autonomous decisions + rationale, project-level user-input summaries). A dispatched issue-manager sub-agent may
append comments only to its assigned work item under the normal
issue-manager protocol (it uses `add-comment` with the work item's issue slug
as the target): seeding comments, directive-mirror comments, its own
transition comments (dispatch, completion, blocker), and -- for the ideation
issue-manager -- proposal revision comments and dispatcher-posted ideation
critiques. **Reviewer agents never append comments** (dispatcher-posting, see
`reviewer-briefs.md#reviewer-commenting-protocol`). Coding and reviewer child agents never touch
tracker files at all. No child agent ever writes to the orchestration-log.

- Every comment is author-anonymous (`**Agent**` tag), chronological,
  one point per comment.

Marker-typed comments ([seeding], [directive:], [human-directive:],
[proposal-v<n>], [review-critique:]) are contract-mandated exceptions to
the tracker's 'no meta notes' convention; they still follow the shared
author-anonymous `**Agent**` convention -- anonymous, chronological, one
point per comment.
