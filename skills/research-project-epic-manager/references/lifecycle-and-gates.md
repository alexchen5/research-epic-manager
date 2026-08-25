# Issue Lifecycle and Gates

This reference defines the just-in-time issue lifecycle mechanics and the
stage-keyed gate mechanics: anchor/split/rework creation, superseded
issues, stage exit, version control, gate evaluation,
FAIL routing with whole-stage downstream invalidation, and the missing
route-target rule.

## Dynamic Issue Lifecycle (Just-in-Time Creation)

Phase B bulk generation is deleted. Issues are opened just-in-time by the
epic manager at each stage entry.

**Issue-id scheme:** `<stage>-<purpose>-r<n>` kebab slugs, where `<stage>`
is the kebab stage name (literature-review, hypothesis, experiment-planning,
experiment-execution, analysis, paper-writeup), `<purpose>` is a kebab slug
describing the work slice (anchor, ideation, arm-a, plan, rework, ...), and
`<n>` increments per issue created for that stage+purpose. Examples:
`literature-review-anchor-r1`, `hypothesis-ideation-r1`,
`experiment-execution-arm-a-r1`, `analysis-rework-r2`.

**Anchor creation (entry/exit).**
- Entry: stage entry reached (prior stage terminal + prior stage artifact
  present; the first stage needs only the approved plan).
- Action: epic manager opens the stage anchor issue with `add-issue --
  status open`, body seeded with (a) the stage goal, (b) the inputs from
  prior stage artifacts (their paths + a summary), and (c) the stage
  acceptance criteria; the issue entry is inserted into
  `project.json["issues"]` and `stage_issues[stage]`, `dependencies` are
  seeded from the canonical stage graph (prior stage's anchor/rework
  issue_ids), and the anchor is flagged `anchor: true`. The epic manager
  appends the `[seeding]` comment (which counts toward Check 9 liveness).
- Exit: issue open on disk and registered in the manifest.

**Splits (parallel work).** When a stage's natural parallelism exceeds one
slice (per idea component, per experiment arm), the epic manager opens
additional issues in the same stage (`<stage>-<purpose>-r<n>`, e.g.
`experiment-execution-arm-a-r1`, `experiment-execution-arm-b-r1`), each with
its own acceptance criteria and artifact contribution, before filling
dispatch slots. Every split issue also gets a `[seeding]` comment.

**Rework openings.** When a gate FAIL routes back to a target stage, the
epic manager reuses an OPEN issue of that stage if one exists; otherwise it
opens `<stage>-rework-r<n>` seeded with a comment containing the FAIL
feedback (`[seeded-fail-feedback]`). See "Gates and Routing" below.

**Superseded issues.** Superseded issues (e.g. an anchor whose stage is
re-entered via rework) stay TERMINAL as history: status `superseded` (a
terminal status), comments preserved, NEVER reopened, never re-dispatched.
No state-owner conflict: new work always lands in NEW issues.

**Stage exit.** A stage exits when ALL of:
1. every issue in `stage_issues[stage]` is TERMINAL (resolved, closed, or
   superseded);
2. the stage artifact exists (`artifacts[stage]` non-empty and files
   present on disk);
3. where a gate is configured for the stage: a gate verdict is recorded
   (PASS or routed; see "Gates and Routing"). With gates disabled, condition
   3 is vacuous.

Stage exit is NOT "the one stage issue resolved": issues resolve
individually against their own acceptance criteria, managed by their issue
managers; the epic manager tracks the stage.

### Version Control

**Project files (the project-scoped workspace repo).** Every issue manager
manages the git branch its coding agents work on when they modify project
files. Normative shape:

- The issue manager creates a branch per coding engagement, named for its
  issue (`<issue-id>` or `<issue-id>-r<n>`), BEFORE dispatching the coding
  agent; the agent works and commits on that branch.
- The issue manager verifies the result and, after its review loop passes,
  merges the branch into the workspace's main line (local-only repo).
  Rejected rounds stay on their branch until fixed.
- Abandoned branches are left in place as history, never force-pushed away.
- Because each issue manager owns disjoint branches, concurrent issue
  managers never contend on project files; where artifacts feed downstream
  stages, merge order follows stage dependency order.

**Tracker files (epics/issues/comments).** NO branch management required:
exactly one epic manager exists per run, and each issue manager writes only
its own issue's state and comments. The epic manager remains the single
committer of tracker changes to the top-level repository.

Implementation impact: documentation only; branch hygiene is delegated
practice (validators unchanged; do not add checks).

## Gates and Routing (stage-keyed)

Gates remain stage-keyed control points, evaluated at STAGE exit against
stage artifacts and threads -- NOT against one specific issue.

**Stage-conditioned evidence semantics:** see
`reviewer-briefs.md#block-d-gate-specific-criteria` -- the stage-keyed criterion
definitions are normative there.

**Gate evaluation (at stage exit):**

1. Stage exit conditions 1-2 hold (all `stage_issues[stage]` issues
   terminal; stage artifact present).
2. If the gate is enabled (`max_*_review_loops > 0`), the epic manager
   computes `findings_text` = the concatenation of the stage issues' finding
   summaries, builds the reviewer brief (Evidence Preface + calibration
   preamble + reporting-integrity + gate criteria + scoring contract, IN
   FULL), and dispatches the reviewer sub-agents (scoring-only contract).
3. Reviewer responses are validated (retry once, then fallback); the epic
   manager derives the stored verdict via `derive_verdict`, appends it to
   `verdict_history`, and records the gate invocation on the
   orchestration-log (project-level event).
4. The epic manager renders the critique via
   `review_engine.derive_comment_record` and appends it to the stage anchor
   issue (`[review-critique: <gate>-r<round>]`); manager-generated verdicts
   (fallback / loop-limit) get `[manager-notice]` comments instead.
5. PASS -> advance to the next stage (JIT-open its anchor at entry).
   FAIL -> backward routing (below).

**FAIL routing to a target STAGE.** The routing decision is
manager-authoritative, derived via `route_for_failure` (hypothesis FAIL ->
`literature_review`; analysis FAIL: `literature_review` on
Significance/Originality, `experiment_planning` on Quality-only, else
`literature_review`; writeup FAIL -> `paper_writeup` revision loop in Phase
E, not stage routing). On FAIL:

1. Record the routing decision on the orchestration-log.
2. Find an OPEN (non-terminal) issue in `stage_issues[target]`; if found,
   append a comment to it containing the FAIL feedback and re-dispatch it.
   Otherwise open `<target>-rework-r<n>` seeded with a comment containing
   the FAIL feedback (`[seeded-fail-feedback]`).
3. **Whole-stage downstream invalidation (preserved verbatim):** results
   AND artifacts at/downstream of the target stage are wiped WHOLE-STAGE
   (not per issue): remove their `results` entries and `artifacts` stage
   entries; remove downstream pending/queued issue_ids; `interrupt_agent`
   on downstream in-flight subagents and mark those subagent_ids stale in
   `stale_subagent_ids` (late completions ignored); downstream OPEN issues
   each receive a blocked-linked comment ("blocked-linked comments" per plan
   section 5), marker form `[manager-notice: block-linked to <route_to>
   FAIL]`, recording the invalidation, then non-terminal issues in affected
   stages are marked `superseded` (terminal). `verdict_history` is PRESERVED
   as the audit trail. Comments are NEVER deleted.
4. Downstream not-yet-started stages simply never get issues created -- a
   benefit of just-in-time creation.
5. Re-enter the target stage: dispatch its (reused or rework) issue(s);
   the stage re-exits when its issues are terminal + artifact present
   (+ gate PASS where configured).

**Superseded issues stay terminal (never reopened)** -- no reopen, no
state-owner conflict; the rework issue owns the new work.

**Missing route target:** with the new manifest a route's target stage
always exists (stage_issues is appended per stage); if `stage_issues[target]`
is somehow absent (never visited), treat as a procedural block with a
concrete `blocked_reason` rather than a silent no-op.
