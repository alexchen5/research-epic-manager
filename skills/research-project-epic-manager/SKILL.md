---
name: research-project-epic-manager
description: |
  This skill orchestrates multi-issue research projects using the DSH tracker
  (epics, issues, sub-agents). Given a research brief and a project config, it
  runs a 5-phase protocol: scoping the project plan, generating issues,
  dispatching sub-agents to work each issue, collecting results, and
  synthesising a deliverable (report, presentation slides, or paper draft).
  The always-used 5-phase protocol summary, the reading guide, and the pointer
  index live in SKILL.md itself; detailed implementation is in `references/`.
  Use this skill when the task is to "manage a research project", "run a
  research workflow", "create a research paper", "produce a research report",
  or "orchestrate a multi-issue research epic".
triggers:
  - manage a research project
  - run a research workflow
  - create a research paper
  - produce a research report
  - orchestrate a multi-issue research epic
  - start a research project
  - kick off a research study
---

# Research Project Epic Manager

This skill orchestrates a research project from brief to deliverable using
the DSH tracker under a DYNAMIC, just-in-time issue lifecycle (issues
opened per stage, never pre-generated in bulk). This file is the entry
point: it holds the always-used 5-phase protocol summary, the reading
guide, and the pointer index into the eight reference files.

## Section-addressing convention

`references/<file>.md#<section-slug>` where the slug is the heading text
lowercased, parentheticals removed, and punctuation replaced by hyphens
(e.g. `## Phase A` -> `phase-detail.md#phase-a`, `## Invariants` ->
`validation.md#invariants`).

## Reference files

Read reference files selectively; most are stage- or situation-gated.

| File | What it holds | When to read | Key sections |
|------|---------------|--------------|--------------|
| `references/data-contracts.md` | manifest/data contracts: config schema (authoritative template `assets/project-config-template.yaml`), per-issue result, issue manifest, review state + `block_events`, interventions ledger | before Phase A and whenever writing project.json | `#project-config` (+ `assets/project-config-template.yaml`), `#per-issue-result`, `#issue-manifest`, `#back-compat-note`, `#review-state`, `#interventions-ledger` |
| `references/reviewer-briefs.md` | reviewer side: scoring review contract, brief construction (Blocks A-E), ideation brief, DISPATCHER-POSTING protocol | ONLY when dispatching a reviewer (gate review or ideation review); skippable otherwise | `#reviewer-scoring-review-contract`, `#reviewer-brief-construction`, `#block-a-evidence-preface`, `#block-b-calibration-preamble`, `#block-c-reporting-integrity-obligations`, `#block-d-gate-specific-criteria`, `#block-e-scoring-review-json-contract`, `#the-ideation-reviewer-brief`, `#reviewer-commenting-protocol` |
| `references/ideation-loop.md` | hypothesis-stage ideation loop (concept store CLI, three-component generation, review, aggregation, stop conditions, token bucket) | ONLY for hypothesis-stage ideation; skippable when ideation is disabled (`ideation.max_rounds == 0`) | `references/ideation-loop.md` |
| `references/lifecycle-and-gates.md` | just-in-time issue lifecycle, version control, stage-keyed gates and routing | before phase issue creation | `#dynamic-issue-lifecycle`, `#version-control`, `#gates-and-routing` |
| `references/phase-detail.md` | canonical procedural walk of Phases A-E (entry conditions, tool chains, numbered steps) + the five completion checklists | during each phase (procedural walk + completion checklists) | `#phase-a` .. `#phase-e`, `#phase-a-completion-checklist` .. `#phase-e-completion-checklist` (phase steps + completion checklists) |
| `references/communication-logging.md` | communication logging contract (writers table, directive dual-write, marker set, comment ownership) | whenever comments/directives/markers are recorded (writers table + marker set are normative) | `#communication-logging-contract`, `#marker-set`, `#comment-ownership` |
| `references/autonomy-and-ownership.md` | operation modes and the isolation contract | when operation-mode or isolation-boundary questions arise (circumstantial) | `#operation-modes`, `#isolation-contract` |
| `references/validation.md` | validation batteries (Checks 1-11), implementation order, config surface, risks, invariants | when running/debugging the validator suites and for the invariants (circumstantial) | `#validation`, `#checks-1-11`, `#implementation-order-config-surface-risks`, `#invariants` |

## 5-Phase Protocol

### Phase A -- Project Scoping (skeleton only)

**Entry condition:** The human invoker provides a research brief (1-3
paragraphs) and a `project-config-template.yaml` (may be default or
customised).

**Summary:** Parse the config with `yaml.safe_load`, derive epic metadata
(epic name, project slug) via a scoping LLM sub-agent, create the epic
directory with `add-epic`, allocate the project-scoped workspace, create the
orchestration-log control issue with `add-issue`, and write a `project.json`
manifest SKELETON (control entry + empty maps, per
references/data-contracts.md#issue-manifest). NO issues are generated. The
epic manager then DECIDES on the plan itself (autonomous)
and records the decision + rationale on the orchestration-log; `gated` keeps
the legacy human-approval stop.

**Exit artifacts:** `EPICS_ROOT/<epic-name>/project.json` (status
`plan-ready`; skeleton only), the epic directory (EPIC.md +
orchestration-log control issue), and the project-scoped workspace.

**Tool chain:** `yaml.safe_load` -> `subagent`(foreground, scoping brief) ->
`add-epic` -> `mkdir -p` -> `add-issue` -> filesystem write -> plan decision
gate (`autonomous` decides + records rationale; `gated` keeps the legacy
human-approval stop).

**Key references:** `references/phase-detail.md#phase-a`;
`references/data-contracts.md#issue-manifest`;
`references/lifecycle-and-gates.md#dynamic-issue-lifecycle`.

**Completion checklist:** `references/phase-detail.md#phase-a-completion-checklist`.

### Phase B -- Control Validation / Cost Placeholder

**Entry condition:** `project.json` exists with `status: "plan-ready"`.

**Summary:** Validate the orchestration-log control issue exists on disk
(the only issue that exists at this point), initialize the cost ledger
placeholder, and set `project.json["status"] = "control-validated"`. Phase B
bulk issue generation is DELETED; issue creation is deferred to Phase C.

**Exit artifact:** `project.json` with status `control-validated` and an
initialized cost ledger.

**Key references:** `references/phase-detail.md#phase-b`;
`references/data-contracts.md#issue-manifest` (cost ledger under
`project.json["results"]["costs"]`); `references/validation.md#validation`
(cost-harvesting contract).

**Completion checklist:** `references/phase-detail.md#phase-b-completion-checklist`.

### Phase C -- Stage-Driven Sub-Agent Dispatch (JIT)

**Entry condition:** `project.json` exists with `status: "control-validated"`.

**Summary:** Walk the canonical stage spine in order. At each stage entry,
the epic manager OPENS the stage issues just-in-time (anchor first, then
splits, then reworks on gate routing), seeds dispatch, and runs
issue-manager sub-agents. At stage exit (all issues terminal + artifact
present), a configured gate is evaluated (see
`references/lifecycle-and-gates.md#gates-and-routing`): PASS advances,
FAIL routes to a target stage with whole-stage downstream invalidation.
The hypothesis stage embeds the iterative ideation loop. The epic manager
is the idle delegator: BACKGROUND dispatch, ends its
turn, reacts to notifications and user input -- never busy-waits.

**Exit artifact:** Per-issue results collected, `project.json` `status: "all-settled"` (or `"dispatching"` during).

**Tool chain:** `subagent`(background) -> `job_output` -> `send_message` ->
`add-issue` -> `add-comment` -> filesystem update.

**Key references:** `references/phase-detail.md#phase-c`;
`references/lifecycle-and-gates.md#gates-and-routing`;
`references/ideation-loop.md`;
`references/reviewer-briefs.md#reviewer-commenting-protocol`.

**Completion checklist:** `references/phase-detail.md#phase-c-completion-checklist`.

### Phase D -- Staging / Collection

**Entry condition:** `project.json` `status: "all-settled"` with all results collected.

**Summary:** Runs inline with Phase C (continuous). At finalisation:
validate results/review_state, compute the project status from research
issues only (excluding the control issue), write the final `project.json`,
settlement summary, and the next-action decision (autonomous);
gated presents the summary for human review instead.

**Exit artifact:** `project.json` with final status (`completed`, `partial`,
or `all-settled`).

**Key references:** `references/phase-detail.md#phase-d`.

**Completion checklist:** `references/phase-detail.md#phase-d-completion-checklist`.

### Phase E -- Synthesis (with Writeup Clarity Gate)

**Entry condition:** `project.json` status `"completed"`, `"partial"`, or
`"blocked"` (`blocked_reason` set; loop-limit blocks still permit a partial
draft). NO human approval required (autonomous); `gated`
keeps the legacy approval stop. Upstream hypothesis + analysis gates passed
(last verdict PASS) or `blocked_reason` set -- the executable upstream gate
check (unresolved-gate abort is a defensive blocked state).

**Summary:** Collect resolved findings + blocked reasons from
`project.json`; build a synthesis prompt and generate a deliverable via an
LLM sub-agent. The deliverable enters the Writeup Clarity gate loop
(scoring-only; critiques/notices dispatcher-posted on the paper-writeup
anchor). On PASS finalise; on exhaustion block (never a silent approval).
Write to the project-scoped workspace; update project.json.

**IMPORTANT: Constraint filtering.** The synthesis prompt must include ONLY
`research.boundaries` from the config, NOT `execution.constraints`.

**Exit artifact:** Deliverable file at
`WS_ROOT/<skill-ws>/projects/<project-name>/deliverable.{md,html}`.
project.json updated.

**Key references:** `references/phase-detail.md#phase-e`;
`references/reviewer-briefs.md#block-e-scoring-review-json-contract`;
`references/validation.md#invariants`.

**Completion checklist:** `references/phase-detail.md#phase-e-completion-checklist`.

Detail lives in `references/`; follow the reading guide above.