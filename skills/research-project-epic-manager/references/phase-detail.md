# Phase Detail

This reference is the canonical procedural walk of Phases A-E: entry
conditions, tool chains, numbered steps, and the per-phase completion
checklists. The `SKILL.md` protocol skeletons summarise each phase and
point here.

## Phase A

*Project Scoping (skeleton only)*

### Entry Condition

Human provides research brief + `project-config-template.yaml`.

### Steps

```
Step A1: Parse and capture presence, then normalize config

    config = yaml.safe_load(open("project-config-template.yaml"))
    review_cfg = config.setdefault("review", {})

    # Capture whether max_writeup_review_loops was explicitly present
    # BEFORE applying defaults. Phase E uses this to decide between the
    # new field and the legacy synthesis.max_review_rounds fallback.
    review_cfg["_writeup_loop_present"] = (
        "max_writeup_review_loops" in review_cfg
    )

    review_cfg.setdefault("max_hypothesis_review_loops", 0)
    review_cfg.setdefault("max_experiment_review_loops", 0)
    review_cfg.setdefault("max_writeup_review_loops", 0)
    review_cfg.setdefault("max_total_project_loops", 10)

    # Dynamic just-in-time lifecycle is the default.
    planning = config.setdefault("planning", {})
    planning.setdefault("dynamic_issues", True)
    # Legacy planning.num_issues is tolerated and ignored (schema removal).
    planning.pop("num_issues", None)

    # Ideation block defaults.
    ideation = config.setdefault("ideation", {})
    ideation.setdefault("max_rounds", 3)
    ideation.setdefault("reviewers", 2)
    ideation.setdefault("on_exhaust", "block")

    # Autonomous-by-default.
    autonomy = config.setdefault("autonomy", {})
    autonomy.setdefault("mode", "autonomous")   # | "gated" (legacy stops)

    failure: Invalid YAML -> return error to human.

Step A2: Scoping brief via LLM sub-agent (foreground)

    # The scoping-brief schema stays research-brief + config. Only
    # research.boundaries goes into the prompt, NEVER execution.constraints.
    brief = build_scoping_brief(research_brief, config)
    # Output JSON (NO issue list -- bulk generation is deleted):
    #   { "epic_name": "kebab-case", "project_slug": "kebab-case",
    #     "scope_notes": "one paragraph" }
    plan = subagent(brief, run_in_background=false) -> JSON

    failure: Malformed JSON -> retry once. Second failure -> return error.

Step A3: Create epic, workspace, control issue

    add-epic(plan.epic_name)                      # EPICS_ROOT/<epic>/EPIC.md
    mkdir -p WS_ROOT/<ws>/projects/<slug>/        # project-scoped workspace
    add-issue --body "# Orchestration Log..." --status open \
        "{epic}" "{epic}-orchestration-log"       # control issue
    update EPIC.md "Assigned workspace"

Step A4: Write the manifest SKELETON (control entry + empty maps)

    Manifest skeleton per references/data-contracts.md#issue-manifest, with four Phase-A deltas:
    - issues[] holds the CONTROL entry ONLY;
    - status "scoping-complete";
    - review_state.block_events initialized [] (append-only manager
      decision records; loop-limit synthetics land here);
    - NO stage_to_issue_id, NO num_issues, NO pre-generated issue list.
    Write to project.json.

Step A5: Decide on the plan (autonomous by default)
    # Mandatory human-approval stop REMOVED from the default flow. The epic
    # manager decides plan viability itself, records decision + rationale on
    # the orchestration-log, and proceeds.
    gated mode (autonomy.mode == "gated"): preserve the legacy stop:
        Approved -> "plan-ready", proceed to Phase B.
        Changes  -> "scoping", re-run Step A2.
        Abort    -> "aborted", delete epic.
    autonomous mode:
        viable      -> "plan-ready", proceed to Phase B.
        needs work  -> "scoping", revise the scoping brief, re-run Step A2.
        unviable    -> "aborted", delete epic.
Step A6: Record decision + rationale via add-comment
    command:  python3 WS_ROOT/.dsh/skills/add-comment/scripts/add-comment.py \
              "{epic-name}" "{epic-name}-orchestration-log" \
              "Project scoping complete. Skeleton manifest written (control \
               entry, empty stage_issues/artifacts/interventions). \
               Decision: {approved/changes-requested/aborted} \
               (autonomy.mode: {mode}). Rationale: {...}."
```

## Phase A Completion Checklist

Before proceeding to Phase B, verify ALL of the following:
- [ ] project.json skeleton written with status "plan-ready"
- [ ] Project workspace directory created; EPIC.md "Assigned workspace" updated
- [ ] Orchestration-log control issue created and registered as the only
      entry in project.json["issues"] (control=true)
- [ ] Plan decision made by the epic manager and recorded with rationale via
      add-comment (autonomous mode); gated mode keeps the legacy human
      approval stop
- [ ] review_state initialized (loop_counters all zero, verdict_history and
      block_events empty, current_gate/current_route/blocked_reason null)
- [ ] stage_issues, artifacts, interventions all present and EMPTY (append-only)
- [ ] planning.dynamic_issues captured (default true); planning.num_issues
      REMOVED (tolerated and ignored if present in a legacy config)
- [ ] Ideation config normalized (max_rounds 3, reviewers 2, on_exhaust block)
- [ ] review_config_presence captured: _writeup_loop_present in config.review
- [ ] NO issues generated in Phase A (bulk generation deleted)

## Phase B

*Control Validation / Cost Placeholder*

### Entry Condition

`project.json` exists with `status: "plan-ready"`.

### Steps

```
Step B1: Validate the orchestration-log control issue (created in Phase A)
    control_path = issues/{control_id}/ISSUE.md under the epic
    assert os.path.exists(control_path)
    failure: not found -> abort with state-mismatch error.

Step B2: Initialize the cost ledger placeholder
    project.json["results"]["costs"] = {}
    # MANDATORY cost-harvesting contract: non-zero cost tokens per result
    # (validation.md Check 1); ideation bucket under results["ideation"]["costs"].

Step B3: project.json["status"] = "control-validated"; save.

Step B4: add-comment summary on orchestration-log
    "Control validated; cost ledger initialized; JIT issue lifecycle armed
     (dynamic_issues: <value>)."
```

## Phase B Completion Checklist

Before proceeding to Phase C, verify ALL of the following:
- [ ] Control issue exists on disk and is registered in the manifest
- [ ] project.json["status"] = "control-validated"
- [ ] MANDATORY: cost ledger initialized at project.json["results"]["costs"]
- [ ] NO issue creation performed in Phase B (deferred to Phase C)
- [ ] Phase B summary recorded via add-comment on orchestration-log

## Phase C

*Stage-Driven Sub-Agent Dispatch (JIT)*

### Entry Condition

`project.json` with `status: "control-validated"`.

### DSH Primitives

`subagent(background)`, `job_output`, `send_message`, `interrupt_agent`.

### Shared Helpers

```
find_issue_by_id(issues, issue_id):            # FRESH lookup every use
parse_verdict(raw)                             # JSON decode or None
validate_review_scoring(s, stage, gc)          # scoring-only contract
derive_verdict(s, stage, gc)                   # manager-derived stored entry
fallback_verdict(stage, round_number)          # all-1 scoring, fallback:True
derive_comment_record(scoring, stage):         # renders critique text from
    # the SCORING review only; ZERO PASS/FAIL/THRESHOLD/ROUTING/VERDICT
    # (case-insensitive) -- references/reviewer-briefs.md#reviewer-commenting-protocol.
```

### Steps

```
Step C1: Initialize dispatch state

    dispatched = {}         # issue_id -> subagent_id
    pending = []            # issue_ids with resolved deps
    queued = []             # issue_ids with unresolved deps
    results = {}            # issue_id -> result
    failed_attempts = {}    # issue_id -> count
    stale_subagent_ids = {} # subagent_id -> issue_id (late completions ignored)

    stage_spine = ["literature_review", "hypothesis", "experiment_planning",
                   "experiment_execution", "analysis", "paper_writeup"]

    gate_config_map = {     # explicit, never derived from stage name
        "hypothesis": {"enabled": review.max_hypothesis_review_loops > 0,
                       "max_loops": ..., "criteria": ["Significance","Originality"],
                       "valid_routing": ["literature_review","experiment_execution"]},
        "analysis":   {"enabled": review.max_experiment_review_loops > 0,
                       "max_loops": ..., "criteria": ["Quality","Significance","Originality"],
                       "valid_routing": ["literature_review","experiment_planning","paper_writeup"]}
    }

Step C2: Stage loop over stage_spine

    for stage in stage_spine:

        C2a: Stage entry criteria
            prior stage (if any) is terminal-in-manifest AND its stage
            artifact exists on disk -> else this stage waits / is skipped
            (never-yet-started stages simply get no issues; see routing).

        C2b: JIT issue creation (BEFORE filling dispatch slots)
            open the stage anchor issue (and any splits) via add-issue,
            seed the [seeding] comment(s), insert into issues[] and
            stage_issues[stage], seed dependencies from the canonical
            stage graph, and add the new issue_ids to pending.

        C2c: Dispatch loop WITHIN the stage
            while pending or dispatched or queued (stage-scoped):

                # --- Stale cleanup at loop top (persisting
                #     stale_subagent_ids, as today) ---
                stale_ids = set(stale_subagent_ids.values())
                pending = [pid for pid in pending if pid not in stale_ids]

                # Fill slots up to max_concurrent: pop pending, FRESH
                # find_issue_by_id, build issue-manager brief, subagent
                # (background); if paper-writing issue: persist
                # paper_writing_subagent_id immediately.
                #
                # Directive dual-write (mandatory): scope/routing/revision
                # briefs MUST mirror a [directive: <digest>] comment BEFORE
                # acting + ledger entry (communication-logging.md).

                # On completion notification (see today's logic): reverse
                # lookup, ignore stale completions, FRESH issue_data lookup,
                # job_output, MANDATORY cost harvest, retries, transitive
                # blocks, unconditional dispatched cleanup, dependents
                # release (only when review_state.current_route != "blocked").

        C2d: Stage exit + gate
            require: every issue in stage_issues[stage] TERMINAL,
                     artifacts[stage] present.
            if stage in gate_config_map and gate enabled:
                run the gate (reviewers scoring-only, derive_verdict,
                dispatcher-posted [review-critique] on the anchor, or
                [manager-notice] for manager-generated verdicts; record on
                orchestration-log). PASS -> next stage. FAIL -> backward
                routing (see "Gates and Routing"): reuse open issue in the
                target stage or open <target>-rework-r<n> seeded with the
                FAIL feedback; whole-stage invalidation at/downstream of the
                target; mark non-terminal issues superseded; re-enter the
                target stage (goto C2b for the target).
            else: PASS-equivalent, next stage.

Step C3: Health check and settle -> project.json["status"] = "all-settled"
```

**Hypothesis stage internal order (ideation + gate):** C2b opens
`hypothesis-ideation-r1` (anchor); it runs the ideation loop
(references/ideation-loop.md), producing `ideas/proposal-final.json` with
`[proposal-v<n>]` / dispatcher-posted `[review-critique: ideation-r<round>]`
comments; stage exit requires the recorded stop condition
(`ideation_disabled` at max_rounds == 0); the GATE then evaluates the
proposal (Significance / Originality).

## Phase C Completion Checklist

Before proceeding to Phase D, verify ALL of the following:
- [ ] Every stage's issues were opened just-in-time at stage entry (anchor
      first, then splits; issue ids follow `<stage>-<purpose>-r<n>`)
- [ ] Issue entries inserted into issues[] and stage_issues[stage]
      (append-only); dependencies seeded from the canonical stage graph
- [ ] Every JIT issue received a [seeding] comment (Check 9 satisfiable)
- [ ] Every dispatched issue has a result in project.json["results"]
- [ ] MANDATORY: Each resolved issue has cost with non-zero tokens
      (harvested into results["costs"])
- [ ] Paper-writing issue (if any) has paper_writing_subagent_id persisted
- [ ] Anchor-thread marker contract: [directive: <digest>] mirrors + ledger
      match (Check 8); ideation evidence >= 2 [proposal-v<n>] comments or a
      recorded stop condition (Check 11)
- [ ] Gate critiques dispatcher-posted on stage anchors
      ([review-critique: <gate>-r<round>]); manager-generated verdicts
      covered by [manager-notice] (Check 10)
- [ ] Review gate verdict history captured in review_state for every
      hypothesis/analysis gate invocation
- [ ] On gate FAIL: whole-stage invalidation at/downstream of the target
      (results + artifacts wiped, subagents interrupted/stale, downstream
      OPEN issues receive block-linked comments, non-terminal issues
      superseded); verdict history preserved; FAIL feedback lands on the
      reused/rework issue
- [ ] Blocked-on-loop-limit cases recorded with blocked_reason, a
      block_events entry, and an orchestration-log comment
- [ ] Stale subagent completions ignored via stale_subagent_ids
- [ ] project.json["status"] = "all-settled"
- [ ] Dispatch summary recorded via add-comment with cost breakdown

## Phase D

*Staging / Collection*

### Entry Condition

`project.json` with `status: "all-settled"`.

**Continuity note:** Phase D finalisation runs continuously with the Phase C loop; its FORMAL entry gate remains `status: "all-settled"`.

### Steps

```
Step D1: Validate each result (copy cost, findings, outputs to issue entries)
    for each NON-control issue in project.json["issues"]:
        result = results.get(issue_id)
        issue["status"] = result.status (or "blocked" if missing)
        issue["findings"] / ["outputs"] / ["cost"] / ["blocker_reason"]
        issue["review_scores"] / ["verifier_result"] / ["perspective"]

Step D1.5: Validate review_state; log blocked_reason; attach verdict
    summaries (gate, rounds, last verdict/routing) to hypothesis/analysis
    stages (on their anchor issues).

Step D2: Compute project status from research issues only (exclude control)
    # PRECEDENCE unchanged: review_state.blocked_reason (loop-limit block)
    # -> "blocked" (OVERRIDES all-resolved; never "completed" merely because
    # all issues resolved); else all-resolved -> "completed"; else any
    # issue blocked -> "partial"; else -> "all-settled".

Step D3: Save final project.json
Step D4: add-comment settlement with cost + review_state summary
Step D5: Decide next action (autonomous by default)
    # Epic manager decides + records rationale (see `references/autonomy-and-ownership.md#operation-modes`).
```
```

**Executable upstream gate check:** Phase E requires hypothesis AND analysis
gates passed (last verdict PASS), OR `blocked_reason` set. Otherwise abort
with status `"blocked"` and `final_verdict = "REJECT"` (external contract:
APPROVE/REJECT only).

## Phase D Completion Checklist

Before proceeding to Phase E, verify ALL of the following:
- [ ] MANDATORY: Every resolved issue has cost with non-zero tokens
- [ ] MANDATORY: Status precedence applied -- review_state.blocked_reason
      (loop-limit block) sets status "blocked" OVERRIDING all-resolved; only
      then all-resolved -> "completed", any issue blocked -> "partial",
      else -> "all-settled". A project with a loop-limit block is NEVER
      marked "completed" merely because all issues resolved.
- [ ] Project status computed from research issues only; superseded issues
      are terminal and never counted as resolved
- [ ] Final project.json saved with status (completed/partial/all-settled/
      blocked)
- [ ] Settlement summary recorded via add-comment with resolved/blocked
      counts, total tokens, per-issue breakdown, review_state summary
- [ ] Next-action decision recorded with rationale by the epic manager
      (autonomous: proceed-to-synthesis / re-dispatch / partial-flag; gated
      mode keeps the legacy human stop)
- [ ] MANDATORY: paper_writing_subagent_id set if paper-writing issue exists
- [ ] Verdict history summaries attached to hypothesis/analysis stage anchors
- [ ] EXECUTABLE UPSTREAM GATE CHECK: hypothesis + analysis last verdict PASS, OR `blocked_reason` set (see the executable check above)

## Phase E

*Synthesis (with Writeup Clarity Gate)*

### Entry Condition

`project.json` with `status: "completed"`, `"partial"`, or `"blocked"` --
the `"blocked"` case ONLY when `review_state.blocked_reason` is set (a
loop-limit block still permits synthesising a partial draft). NO human
approval is required (autonomous by default); in
`autonomy.mode: gated` the legacy approval stop applies before entering
Phase E. Executable upstream gate check per Phase D (an unresolved-gate
abort is a defensive blocked state).

### Exit Artifact

Deliverable in project-scoped workspace. `project.json` with status
`synthesised` (on PASS/disabled) or `blocked` (on writeup exhaustion).

### Steps

```
Step E1: Executable upstream gate check (as today; abort path -> status
    "blocked", final_verdict "REJECT").

Step E1.5: Build the artifact evidence summary (same workspace scan as the
    Evidence Preface: **/results_summary.json, archive/**/*.json,
    **/*_metrics.json -> mode, dataset origin, model class, n_records,
    container simulation, key JSON counts)

Step E2: Build synthesis prompt (ONLY research.boundaries; NEVER
    execution.constraints) with the evidence summary verbatim and the
    reporting-integrity requirement set (counts == artifact values; no
    "real"/"containerised" claims beyond the summary; simulation markers in
    the abstract and every results cell when simulated; threshold ledger
    reproduced verbatim with pre-registered statuses preserved; no pillar-
    ablation run -> joint-necessity/coupling claims worded as predictions).

Step E3: Generate initial draft via sub-agent; write to project workspace.

Step E3.5: Writeup Clarity gate review loop

    # Resolve max rounds: _writeup_loop_present True ->
    # review.max_writeup_review_loops (incl. explicit 0 = disabled); absent
    # -> legacy synthesis.max_review_rounds fallback. (Compatibility
    # translation for validate_execution.py Check 2 unchanged.)

    round_count = 0

    if max_rounds <= 0:
        # Disabled gate: manager placeholder verdict (round 0, Clarity
        # score 3, verdict PASS, routing "complete"). Round 0 is BELOW the
        # valid reviewer range: this is a MANAGER-GENERATED placeholder,
        # exempt from Check 10; the manager posts a [manager-notice]
        # comment documenting no review was performed.
    else:
        while round_count < max_rounds:
            round_count += 1
            # Total-loop-limit check BEFORE dispatch; if exceeded: synthetic
            # verdict (score 1, routing "blocked", manager-generated) in
            # block_events; verdict_history mirror keeps routing "blocked"
            # so Check 10 exempts it; [manager-notice]; break.
            # Else dispatch the writeup reviewer (build_writeup_reviewer_brief
            # IN FULL: Evidence Preface from E1.5 + calibration preamble +
            # writeup reporting-integrity obligations + Clarity criteria +
            # scoring contract); validate (retry once, fallback);
            # derive_verdict; increment writeup_gate/total_project_loops;
            # append stored entry; DISPATCHER-POST a rendered critique
            # [review-critique: writeup-r<round>] on the paper-writeup anchor
            # issue (or [manager-notice] for fallback).
            # PASS -> break. FAIL -> add-comment on orchestration-log, send
            # revision to paper_writing_subagent_id (or regenerate with a
            # fresh foreground subagent), rewrite deliverable.

    # Post-loop: PASS/disabled -> status "synthesised", final_verdict
    # "APPROVE"; FAIL/exhaustion -> status "blocked", final_verdict "REJECT".
    # External contract (Check 2): final_verdict is ALWAYS APPROVE/REJECT;
    # never UNKNOWN/SKIPPED/BLOCKED. deliverable_path, review_rounds saved.

Step E5: add-comment completion summary (deliverable path, writeup rounds,
    final verdict, project status).
```

## Phase E Completion Checklist

Before marking the project complete, verify ALL of the following:
- [ ] MANDATORY: Executable upstream gate check performed (hypothesis PASS
      and analysis PASS, or blocked_reason allows partial)
- [ ] MANDATORY: Phase E entry accepts status "blocked" ONLY when
      review_state.blocked_reason is set; a loop-limit block yields a
      partial draft with final_verdict "REJECT", never "completed"
- [ ] MANDATORY: Writeup Clarity gate used max_writeup_review_loops when
      _writeup_loop_present=True; legacy synthesis.max_review_rounds only
      when absent
- [ ] MANDATORY: Reviewer responses are SCORING reviews (gate, round,
      criteria_scores with Clarity score 1-5 + justification, non-empty
      revision_feedback; no verdict/failing_criteria/routing) and stored
      verdict entries are manager-derived via derive_verdict (FAIL iff
      Clarity < 4) and pass validate_verdict (gate: writeup, criteria:
      Clarity only)
- [ ] MANDATORY: Writeup critiques are DISPATCHER-POSTED on the
      paper-writeup anchor issue ([review-critique: writeup-r<round>]); the
      disabled round-0 placeholder gets a [manager-notice] (Check 10
      exemption). Loop-limit synthetics: score 1 (not 0), routing "blocked",
      recorded in block_events; a verdict_history mirror keeps "blocked" so
      Check 10 exempts it; status "blocked", NEVER "synthesised";
      [manager-notice] required
- [ ] MANDATORY: Revision instructions sent to paper_writing_subagent_id
      (if paper-writing issue exists)
- [ ] MANDATORY: Step E1.5 artifact evidence summary built and used
      verbatim in BOTH the synthesis prompt and the writeup reviewer brief
      Evidence Preface
- [ ] MANDATORY: Every reported count equals the artifact JSON values in the
      evidence summary; data/model/container claims match exactly
- [ ] MANDATORY: When mode indicates simulated internals, the ABSTRACT and
      every results table/prose cell carry a simulation marker, and the
      abstract states "no real model was fitted and no real SHAP was
      computed" when applicable
- [ ] MANDATORY: Threshold ledger reproduced verbatim with pre-registered
      statuses preserved and NO post-hoc promotion
- [ ] MANDATORY: Without a pillar-ablation run, the joint-necessity thesis
      and coupling claims are worded as predictions
- [ ] Loop counters incremented (writeup_gate, total_project_loops) after
      each writeup round; verdict history appended for each writeup round
- [ ] MANDATORY: Writeup reviewer brief built from the authoritative
      templates (`references/reviewer-briefs.md#reviewer-brief-construction`) IN FULL, including the Evidence Preface (ending with
      "Score evidence against what actually executed, not against what the
      text claims."), the calibration preamble ("Assume this submission is
      borderline-reject"), the rubric, and the writeup reporting-integrity
      obligations -- never abbreviated; the brief asks for a SCORING review
      only and never tells the reviewer the threshold or pass/fail semantics
- [ ] On writeup gate PASS or disabled: status = "synthesised",
      final_verdict = "APPROVE"
- [ ] EXTERNAL CONTRACT (scripts/validate_execution.py Check 2): project
      final_verdict is ALWAYS "APPROVE" or "REJECT" -- never
      UNKNOWN/SKIPPED/BLOCKED
- [ ] Deliverable written to project-scoped workspace; deliverable_path set
- [ ] Constraint filtering verified: no execution.constraints in deliverable
