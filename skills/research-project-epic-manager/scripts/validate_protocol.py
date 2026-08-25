#!/usr/bin/env python3
"""Validate the research-project-epic-manager skill's core algorithms and data contracts.

Stdlib-only.  Run with ``python3 validate_protocol.py``.  Exits 0 on all pass, 1 otherwise.
"""

import json
import os
import re
import sys
import tempfile
sys.path.insert(0, os.path.dirname(__file__))
from review_engine import (parse_verdict, validate_review_scoring, derive_verdict, validate_verdict, fallback_verdict, normalize_review_config, route_for_failure, manager_block, invalidate_and_route, record_reviewer_invocation, writeup_limit, writeup_outcome, PASS_THRESHOLD, stage_for_gate, anchor_issue_ref, validate_stage_issues, stage_issue_violations, stage_issues_insert, stage_issues_anchor, derive_comment_record)
from ideation_controller import (aggregate_reviews, should_stop, token_bucket, initial_bucket, IDEATION_CRITERIA, IDEATION_COMPONENTS)
from concept_store import (build_concept_index, top_k_related, query_papers)
from validate_execution import check_simulation_disclosure

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROTOCOL_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "references",
    "phase-detail.md",
)


def test_dispatch_ordering():
    # type: () -> bool
    """Simulate the Phase-C dispatch algorithm (Steps C1-C3).

    Creates a mock dependency graph:

        A  (no deps)
        B  (depends on A)
        C  (no deps)

    max_concurrent = 2.

    Expected dispatch order:
        * seed pending = [A, C], queue = [B]
        * round 1: dispatch A, C  (slots filled)
        * A completes (resolved) -> release B from queue -> dispatch B
        * final: A, C, then B  (B never dispatched before A resolves)
    """

    # --- mock data ---------------------------------------------------------
    max_concurrent = 2

    issues = [
        {"issue_id": "A", "control": False},
        {"issue_id": "B", "control": False},
        {"issue_id": "C", "control": False},
    ]
    dependencies = {
        "A": [],
        "B": ["A"],
        "C": [],
    }

    # lookup helpers
    issue_map = {i["issue_id"]: i for i in issues}

    # --- C1: initialize ---------------------------------------------------
    dispatched = {}   # issue_id -> subagent_id (simulated)
    pending = []      # issues whose deps are resolved
    queued = []       # issues with unresolved deps
    results = {}      # issue_id -> mock result
    failed_attempts = {}  # issue_id -> count

    # Seed pending
    for issue in issues:
        if issue.get("control"):
            continue
        deps = dependencies.get(issue["issue_id"], [])
        # all deps resolved if none pending/queued/dispatched
        unresolved = [d for d in deps
                      if d in pending or d in queued or d in dispatched]
        if not unresolved:
            pending.append(issue["issue_id"])
        else:
            queued.append(issue["issue_id"])

    # --- initial state check -----------------------------------------------
    # We expect A and C pending, B queued
    if sorted(pending) != ["A", "C"] or queued != ["B"]:
        return False

    # --- C2: dispatch loop ------------------------------------------------
    dispatch_log = []  # ordered record of dispatched issue_ids

    def _fill_slots():
        while len(dispatched) < max_concurrent and pending:
            iid = pending.pop(0)
            dispatched[iid] = "sim-agent-" + iid
            dispatch_log.append(iid)

    _fill_slots()

    # Round 1 must have dispatched A, C (order depends on seed order)
    if sorted(dispatched.keys()) != ["A", "C"]:
        return False

    # Simulate A completing (resolved)
    completed = "A"
    iid = completed
    result = {"status": "resolved"}
    results[iid] = result

    # Release dependents
    for q_id in list(queued):
        deps = dependencies.get(q_id, [])
        if all(d in results and results[d].get("status") == "resolved"
               for d in deps):
            queued.remove(q_id)
            pending.append(q_id)

    del dispatched[iid]
    _fill_slots()

    # After A resolves, B should be released and dispatched
    if "B" not in dispatch_log:
        return False

    # B must come AFTER A in the dispatch log
    a_idx = dispatch_log.index("A")
    b_idx = dispatch_log.index("B")
    if b_idx < a_idx:
        return False

    # Final queue must be empty
    if queued:
        return False

    return True


def test_manifest_schema():
    # type: () -> bool
    """Create and validate a ``project.json`` example matching the
    Project Manifest Contract from Phase A, Step A4."""

    manifest = {
        "control_issue_id": "my-epic-orchestration-log",
        "project": "My Project",
        "epic": "my-epic",
        "status": "plan-ready",
        "config": {
            "dispatch": {
                "max_concurrent": 3,
                "max_retries": 3,
            }
        },
        "issues": [
            {
                "issue_id": "literature-review",
                "title": "Literature Review",
                "control": False,
                "status": "open",
                "issue_path": "issues/literature-review/ISSUE.md",
            },
            {
                "issue_id": "my-epic-orchestration-log",
                "title": "Orchestration Log",
                "control": True,
                "status": "open",
                "issue_path": "issues/my-epic-orchestration-log/ISSUE.md",
            },
        ],
        "dependencies": {
            "literature-review": [],
        },
        "results": {},
    }

    # Top-level required fields
    required_root = ["control_issue_id", "project", "epic",
                     "status", "config", "issues", "dependencies", "results"]
    for k in required_root:
        if k not in manifest:
            return False

    # issues is a non-empty list
    if not isinstance(manifest["issues"], list) or len(manifest["issues"]) < 2:
        return False

    # Each issue must have required fields
    issue_fields = {"issue_id", "title", "control", "status", "issue_path"}
    for iss in manifest["issues"]:
        if not issue_fields.issubset(iss.keys()):
            return False

    # At least one control issue with control: true
    if not any(iss.get("control") for iss in manifest["issues"]):
        return False

    # At least one research issue (control: false)
    if not any(not iss.get("control") for iss in manifest["issues"]):
        return False

    # dependencies maps issue_id -> list
    deps = manifest["dependencies"]
    if not isinstance(deps, dict):
        return False
    for dep_list in deps.values():
        if not isinstance(dep_list, list):
            return False

    # results is a dict (may be empty)
    if not isinstance(manifest["results"], dict):
        return False

    return True


def test_control_issue_filtering():
    # type: () -> bool
    """Verify dispatch seeding (Step C1) correctly skips control issues."""

    issues = [
        {"issue_id": "research-1", "control": False},
        {"issue_id": "orch-log", "control": True},
    ]
    dependencies = {"research-1": [], "orch-log": []}

    pending = []
    queued = []

    for issue in issues:
        if issue.get("control"):
            continue  # must be skipped
        deps = dependencies.get(issue["issue_id"], [])
        unresolved = []
        for d in deps:
            if d in pending or d in queued or d in {}:
                unresolved.append(d)
        if not unresolved:
            pending.append(issue["issue_id"])
        else:
            queued.append(issue["issue_id"])

    # Only research-1 should be pending; orch-log must NOT be in pending/queued
    if pending != ["research-1"]:
        return False
    if queued:
        return False

    return True


def test_add_comment_target():
    # type: () -> bool
    """Check that every ``add-comment`` invocation in phase-detail.md
    targeting the orchestration-log uses ``<epic-name>-orchestration-log`` as
    the second positional argument (not the bare literal ``"epic"``)."""

    try:
        with open(_PROTOCOL_FILE, "rt", encoding="ascii") as fh:
            text = fh.read()
    except FileNotFoundError:
        print("  [SKIP] phase-detail.md not found")
        return True
    except UnicodeDecodeError:
        print("  [SKIP] phase-detail.md is not ASCII")
        return True

    # The spec's shell commands span multiple physical lines via a trailing
    # backslash continuation:
    #   python3 ... add-comment.py \
    #       "<epic-name>" "<epic-name>-orchestration-log" \
    #       "..."
    # Join logical lines first so the args are scanned as one unit.

    lines = text.splitlines()
    logical_lines = []  # list of (start_lineno, joined_text)
    current = []
    start = 1
    for lineno, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not current:
            start = lineno
        current.append(stripped.rstrip("\\"))
        if stripped.endswith("\\"):
            continue  # keep joining across the continuation
        logical_lines.append((start, " ".join(current)))
        current = []
    if current:
        logical_lines.append((start, " ".join(current)))

    all_valid = True

    for start_lineno, joined in logical_lines:
        # Only inspect shell invocations of add-comment.py
        if "add-comment.py" not in joined:
            continue

        # Only inspect invocations that target the orchestration-log at all.
        if "orchestration-log" not in joined:
            continue

        # Find what follows the script name.
        idx = joined.find("add-comment.py")
        after_script = joined[idx + len("add-comment.py"):]

        # Extract all double-quoted strings after the script name.
        quoted_args = re.findall(r'"([^"]*)"', after_script)
        if len(quoted_args) < 2:
            continue  # not the "<epic-name>" "<target>" "<body>" shape

        # Per spec: python3 ... add-comment.py "<epic-name>" "<target>" "<body>"
        # quoted_args[0] is the epic name, quoted_args[1] is the second
        # positional argument (the target).
        target = quoted_args[1]
        if target == "epic":
            all_valid = False
            print(f"    FAIL: line {start_lineno}: second positional argument "
                  f"is bare \"epic\" instead of \"<epic-name>-orchestration-log\"")
            print(f"           {joined[:120]}")

    return all_valid



def test_review_engine_scoring_contract_and_routes():
    scoring={"gate":"hypothesis","round":1,"criteria_scores":{"Significance":{"score":2,"justification":"weak"},"Originality":{"score":4,"justification":"novel"}},"revision_feedback":"Significance scores below the bar; the hypothesis must be reframed."}
    derived=derive_verdict(scoring,"hypothesis")
    ok = validate_review_scoring(scoring,"hypothesis")
    ok = ok and derived["verdict"]=="FAIL" and derived["failing_criteria"]==["Significance"] and derived["routing"]=="literature_review"
    ok = ok and validate_verdict(derived,"hypothesis")
    ok = ok and route_for_failure("analysis",["Quality"])=="experiment_planning" and route_for_failure("writeup",["Clarity"])=="paper_writeup"
    return ok and not validate_verdict(dict(derived, routing="blocked"),"hypothesis")

def test_malformed_retry_fallback():
    fw=fallback_verdict("writeup",2)
    return parse_verdict("not-json") is None and fw["verdict"]=="FAIL" and fw["failing_criteria"]==["Clarity"] and fw["routing"]=="paper_writeup" and validate_verdict(fw,"writeup")

def test_config_limits_and_legacy_fallback():
    a=normalize_review_config({"synthesis":{"max_review_rounds":2}}); b=normalize_review_config({"review":{"max_writeup_review_loops":0},"synthesis":{"max_review_rounds":2}})
    return not a["review"]["_writeup_loop_present"] and writeup_limit(a)==2 and b["review"]["_writeup_loop_present"] and writeup_limit(b)==0 and a["review"]["max_total_project_loops"]==10

def test_missing_target_and_invalidation_invariants():
    m={"stage_to_issue_id":{"literature_review":"lr","hypothesis":"h","analysis":"a","paper_writeup":"w"}}; r={"lr":1,"h":1,"a":1}; p=[]; q=[]; d={"a":"agent-a"}; st={}; seen=[]
    t,e=invalidate_and_route(m,"hypothesis",r,p,q,d,st,lambda x:seen.append(x))
    return t=="h" and e is None and set(r)=={"lr"} and p==["h"] and st=={"agent-a":"a"} and invalidate_and_route({},"hypothesis",{},[],[],{}, {})[1] is not None

def test_manager_block_is_not_reviewer_verdict():
    s={"verdict_history":[]}; event=manager_block(s,"analysis","total loop limit")
    return s["current_route"]=="blocked" and event["decision_type"]=="manager_block" and event["current_gate"]=="analysis" and not s["verdict_history"] and not validate_verdict({"gate":"analysis","round":1,"verdict":"FAIL","criteria_scores":{"Quality":{"score":1,"justification":"x"},"Significance":{"score":1,"justification":"x"},"Originality":{"score":1,"justification":"x"}},"failing_criteria":["Quality"],"revision_feedback":"x","routing":"blocked"},"analysis")

def test_extensions_and_all_routes():
    base={"gate":"writeup","round":1,"criteria_scores":{"Clarity":{"score":5,"justification":"clear"}},"revision_feedback":"clear, no weaknesses found beyond minor wording","reviewer_id":"r1"}
    derived=derive_verdict(base,"writeup")
    # reviewer_id is an extra field (allowed and ignored in scoring); a
    # verdict field, if present, is ignored too.
    return validate_review_scoring(base,"writeup") and validate_review_scoring(dict(base, metadata={"source":"test"}),"writeup") and validate_review_scoring(dict(base, verdict="PASS"),"writeup") and derived["verdict"]=="PASS" and derived["failing_criteria"]==[] and derived["routing"]=="complete" and validate_verdict(derived,"writeup") and route_for_failure("hypothesis",["Originality"])=="literature_review" and route_for_failure("hypothesis",[])=="literature_review" and route_for_failure("analysis",["Significance"])=="literature_review"

def test_writeup_limits_and_disabled_flow():
    s,v,b=writeup_outcome({"review":{"max_writeup_review_loops":0,"max_total_project_loops":10},"synthesis":{"max_review_rounds":4}},[])
    return v=="APPROVE" and not b and not s["verdict_history"] and s["loop_counters"]["total_project_loops"]==0

def test_writeup_exhaustion_and_total_boundary():
    bad=["bad","still bad"]
    s,v,b=writeup_outcome({"review":{"max_writeup_review_loops":2,"max_total_project_loops":10}},bad)
    return v=="REJECT" and b and s["loop_counters"]["writeup_gate"]==2 and len(s["block_events"])==1 and s["block_events"][0]["current_route"]=="blocked"

def test_stale_duplicate_prevention():
    m={"stage_to_issue_id":{"hypothesis":"h"}}; p=["h"]; q=[]; d={}; r={}; stale={}
    invalidate_and_route(m,"hypothesis",r,p,q,d,stale)
    return p==["h"]

def test_final_verdict_compatibility_and_flat_manifest():
    # writeup_outcome now takes SCORING reviews (no verdict/failing/routing).
    s,v,b=writeup_outcome({"review":{"max_writeup_review_loops":1}},[{"gate":"writeup","round":1,"criteria_scores":{"Clarity":{"score":4,"justification":"clear prose, minor wording issues"}},"revision_feedback":"clear; two minor wording notes to fix."}])
    h=s.get("verdict_history",[])
    return v in ("APPROVE","REJECT") and isinstance(h,list) and h and h[-1]["verdict"]=="PASS" and h[-1]["failing_criteria"]==[] and h[-1]["routing"]=="complete"

def test_pass_verdict_requires_nonempty_feedback():
    empty={"gate":"hypothesis","round":1,"verdict":"PASS","criteria_scores":{"Significance":{"score":5,"justification":"strong"},"Originality":{"score":5,"justification":"novel"}},"failing_criteria":[],"revision_feedback":"","routing":"experiment_execution"}
    # An all-5s PASS with empty feedback must be INVALID (malformed -> retry ->
    # fallback), not silently accepted and routed.
    return not validate_verdict(empty,"hypothesis") and not validate_verdict(dict(empty, revision_feedback="   "),"hypothesis") and not validate_verdict(dict(empty, revision_feedback="\n\t"),"hypothesis")

def test_fail_verdict_requires_nonempty_feedback():
    empty={"gate":"hypothesis","round":1,"verdict":"FAIL","criteria_scores":{"Significance":{"score":2,"justification":"weak"},"Originality":{"score":4,"justification":"novel"}},"failing_criteria":["Significance"],"revision_feedback":"","routing":"literature_review"}
    return not validate_verdict(empty,"hypothesis") and not validate_verdict(dict(empty, revision_feedback="   "),"hypothesis")

def test_pass_verdict_with_nonempty_feedback_valid():
    good={"gate":"hypothesis","round":1,"verdict":"PASS","criteria_scores":{"Significance":{"score":4,"justification":"strong"},"Originality":{"score":4,"justification":"novel"}},"failing_criteria":[],"revision_feedback":"Three weaknesses: (1) single-dataset evidence caps Significance at 3 per the preamble; (2) coupling claim untested without ablation; (3) abstract lacks a simulation marker. Fix before routing.","routing":"experiment_execution"}
    return validate_verdict(good,"hypothesis")

def test_validate_review_scoring():
    # A reviewer scoring review has exactly the 4 scoring fields (extras
    # allowed and ignored); the threshold is NEVER applied at validation
    # time -- the reviewer is not asked to decide pass/fail.
    good={"gate":"hypothesis","round":1,"criteria_scores":{
        "Significance":{"score":4,"justification":"well-scoped, material to the field"},
        "Originality":{"score":4,"justification":"novel angle"}},
        "revision_feedback":"Two minor scope notes; one coupling claim is untested."}
    variants=[]
    # missing a required field
    variants.append({k:v for k,v in good.items() if k!="revision_feedback"})
    # gate mismatch
    variants.append(dict(good, gate="analysis"))
    # round 0 / bool round
    variants.append(dict(good, round=0))
    variants.append(dict(good, round=True))
    # unknown criterion name / missing criterion
    variants.append(dict(good, criteria_scores=dict(good["criteria_scores"], Novelty={"score":4,"justification":"j"})))
    variants.append(dict(good, criteria_scores={"Significance":{"score":4,"justification":"j"}}))
    # empty feedback (after strip)
    variants.append(dict(good, revision_feedback="   "))
    # score out of range / non-int / bool
    variants.append(dict(good, criteria_scores={"Significance":{"score":0,"justification":"j"},"Originality":{"score":4,"justification":"j"}}))
    variants.append(dict(good, criteria_scores={"Significance":{"score":6,"justification":"j"},"Originality":{"score":4,"justification":"j"}}))
    variants.append(dict(good, criteria_scores={"Significance":{"score":4.0,"justification":"j"},"Originality":{"score":4,"justification":"j"}}))
    variants.append(dict(good, criteria_scores={"Significance":{"score":True,"justification":"j"},"Originality":{"score":4,"justification":"j"}}))
    # empty justification (after strip)
    variants.append(dict(good, criteria_scores={"Significance":{"score":4,"justification":"  "},"Originality":{"score":4,"justification":"j"}}))
    # extra fields (integrity_mismatches; a stray verdict) are allowed/ignored
    extra=dict(good, integrity_mismatches=["abstract lacks simulation marker"], verdict="PASS")
    return validate_review_scoring(good,"hypothesis") and validate_review_scoring(extra,"hypothesis") and all(not validate_review_scoring(v,"hypothesis") for v in variants)

def test_derive_verdict_and_threshold_boundary():
    # PASS_THRESHOLD is 4: 1-3 fails the round, 4-5 on every criterion passes.
    def scoring(cs):
        return {"gate":"hypothesis","round":1,"criteria_scores":cs,"revision_feedback":"review"}
    # all-3 -> FAIL (below the bar), both criteria failing, literature_review
    d3=derive_verdict(scoring({"Significance":{"score":3,"justification":"j"},"Originality":{"score":3,"justification":"j"}}),"hypothesis")
    ok = PASS_THRESHOLD==4 and d3["verdict"]=="FAIL" and d3["failing_criteria"]==["Significance","Originality"] and d3["routing"]=="literature_review"
    # all-4 -> PASS, no failing criteria, pass route experiment_execution
    d4=derive_verdict(scoring({"Significance":{"score":4,"justification":"j"},"Originality":{"score":4,"justification":"j"}}),"hypothesis")
    ok = ok and d4["verdict"]=="PASS" and d4["failing_criteria"]==[] and d4["routing"]=="experiment_execution"
    # mixed {4,3} -> FAIL (Originality below the bar)
    dm=derive_verdict(scoring({"Significance":{"score":4,"justification":"j"},"Originality":{"score":3,"justification":"j"}}),"hypothesis")
    ok = ok and dm["verdict"]=="FAIL" and dm["failing_criteria"]==["Originality"] and dm["routing"]=="literature_review"
    # all-5 -> PASS, pass route
    d5=derive_verdict(scoring({"Significance":{"score":5,"justification":"j"},"Originality":{"score":5,"justification":"j"}}),"hypothesis")
    ok = ok and d5["verdict"]=="PASS" and d5["routing"]=="experiment_execution"
    return ok

def test_derive_verdict_routing_cases():
    def derive(gate, cs):
        return derive_verdict({"gate":gate,"round":1,"criteria_scores":cs,"revision_feedback":"review"},gate)
    # analysis Quality-only fail -> experiment_planning
    aq=derive("analysis",{"Quality":{"score":3,"justification":"j"},"Significance":{"score":4,"justification":"j"},"Originality":{"score":4,"justification":"j"}})
    ok = aq["verdict"]=="FAIL" and aq["failing_criteria"]==["Quality"] and aq["routing"]=="experiment_planning"
    # analysis Significance fail -> literature_review
    asg=derive("analysis",{"Quality":{"score":4,"justification":"j"},"Significance":{"score":3,"justification":"j"},"Originality":{"score":4,"justification":"j"}})
    ok = ok and asg["verdict"]=="FAIL" and asg["failing_criteria"]==["Significance"] and asg["routing"]=="literature_review"
    # analysis all-4 -> PASS -> paper_writeup
    ap=derive("analysis",{"Quality":{"score":4,"justification":"j"},"Significance":{"score":4,"justification":"j"},"Originality":{"score":4,"justification":"j"}})
    ok = ok and ap["verdict"]=="PASS" and ap["failing_criteria"]==[] and ap["routing"]=="paper_writeup"
    # writeup Clarity 3 -> FAIL -> paper_writeup; Clarity 4 -> PASS -> complete
    wf=derive("writeup",{"Clarity":{"score":3,"justification":"j"}})
    wp=derive("writeup",{"Clarity":{"score":4,"justification":"j"}})
    ok = ok and wf["verdict"]=="FAIL" and wf["failing_criteria"]==["Clarity"] and wf["routing"]=="paper_writeup" and wp["verdict"]=="PASS" and wp["routing"]=="complete"
    return ok

def test_validate_verdict_rejects_contradictory_stored():
    # Stored entries are manager-derived; validate_verdict enforces
    # derived-consistency (verdict/failing/routing must match the scores).
    base={"gate":"hypothesis","round":1,"criteria_scores":{"Significance":{"score":4,"justification":"j"},"Originality":{"score":4,"justification":"j"}},"revision_feedback":"review"}
    d=derive_verdict(base,"hypothesis")  # PASS, [], experiment_execution
    c1=dict(d, verdict="FAIL", failing_criteria=["Significance"], routing="literature_review")
    low=dict(base, criteria_scores={"Significance":{"score":2,"justification":"j"},"Originality":{"score":4,"justification":"j"}})
    dlow=derive_verdict(low,"hypothesis")  # FAIL, [Significance], literature_review
    c2=dict(dlow, verdict="PASS", failing_criteria=[], routing="experiment_execution")
    c3=dict(dlow, routing="experiment_execution")
    return validate_verdict(d,"hypothesis") and validate_verdict(dlow,"hypothesis") and not validate_verdict(c1,"hypothesis") and not validate_verdict(c2,"hypothesis") and not validate_verdict(c3,"hypothesis")

def test_fallback_derives_fail_and_routing():
    # The fallback is an all-1 scoring review, derived consistently: FAIL on
    # every criterion with derived routing, so validate_verdict accepts it.
    fh=fallback_verdict("hypothesis",1); fa=fallback_verdict("analysis",1); fw=fallback_verdict("writeup",1)
    return (fh["verdict"]=="FAIL" and fh["failing_criteria"]==["Significance","Originality"] and fh["routing"]=="literature_review" and validate_verdict(fh,"hypothesis")
        and fa["verdict"]=="FAIL" and fa["failing_criteria"]==["Quality","Significance","Originality"] and fa["routing"]=="literature_review" and validate_verdict(fa,"analysis")
        and fw["verdict"]=="FAIL" and fw["failing_criteria"]==["Clarity"] and fw["routing"]=="paper_writeup" and validate_verdict(fw,"writeup")
        and fh.get("fallback") is True and fa.get("fallback") is True)

def test_writeup_outcome_with_scoring_responses():
    # PASS scoring (Clarity 4) -> APPROVE; stored entry derived PASS/complete.
    s1,v1,b1=writeup_outcome({"review":{"max_writeup_review_loops":1}}, [{"gate":"writeup","round":1,"criteria_scores":{"Clarity":{"score":4,"justification":"clear"}},"revision_feedback":"minor wording note"}])
    h1=s1.get("verdict_history",[])
    ok = v1=="APPROVE" and not b1 and h1 and h1[-1]["verdict"]=="PASS" and h1[-1]["failing_criteria"]==[] and h1[-1]["routing"]=="complete"
    # FAIL scoring (Clarity 3) -> REJECT after 1 round; stored entry derived
    # FAIL with routing paper_writeup; exhaustion block recorded.
    s2,v2,b2=writeup_outcome({"review":{"max_writeup_review_loops":1}}, [{"gate":"writeup","round":1,"criteria_scores":{"Clarity":{"score":3,"justification":"below the bar"}},"revision_feedback":"three concrete weaknesses listed"}])
    h2=s2.get("verdict_history",[])
    ok = ok and v2=="REJECT" and b2 and s2.get("block_events") and s2["block_events"][0]["current_route"]=="blocked" and h2 and h2[-1]["verdict"]=="FAIL" and h2[-1]["failing_criteria"]==["Clarity"] and h2[-1]["routing"]=="paper_writeup"
    return ok

def test_check7_simulation_disclosure():
    # type: () -> bool
    """Drive check_simulation_disclosure (validate_execution.py Check 7)
    against temp project workspaces:

    * dry-run artifact + deliverable whose abstract lacks a marker -> FAIL
    * dry-run artifact + \"[simulated]\" inside the abstract within the
      first 60 lines -> PASS
    * no simulated-mode artifact -> SKIP (passes silently, even with no
      deliverable file)
    * dry-run artifact + deliverable file missing entirely -> FAIL
    """

    def _write(path, text):
        with open(path, "w") as fh:
            fh.write(text)

    def _dry_run_workspace(tmp):
        os.makedirs(os.path.join(tmp, "archive"))
        _write(os.path.join(tmp, "archive", "results_summary.json"),
               json.dumps({"mode": "dry-run simulated"}))

    # (1) without marker -> fails
    with tempfile.TemporaryDirectory() as tmp1:
        _dry_run_workspace(tmp1)
        deliv1 = os.path.join(tmp1, "deliverable.md")
        _write(deliv1,
               "# Demo\n\n## 1. Abstract\n\nNo simulation marker here.\n\n"
               "## 2. Introduction\n\nBody text.\n")
        fails1 = check_simulation_disclosure(
            {"deliverable_path": deliv1}, workspace_root=tmp1)
        ok1 = bool(fails1) and any("simulation marker" in f for f in fails1)

    # (2) with "[simulated]" in the abstract region (first 60 lines) -> passes
    with tempfile.TemporaryDirectory() as tmp2:
        _dry_run_workspace(tmp2)
        deliv2 = os.path.join(tmp2, "deliverable.md")
        _write(deliv2,
               "# Demo\n\n## 1. Abstract\n\n[simulated] All headline numbers "
               "are dry-run stub estimates.\n\n## 2. Introduction\n\nBody "
               "text.\n")
        fails2 = check_simulation_disclosure(
            {"deliverable_path": deliv2}, workspace_root=tmp2)
        ok2 = not fails2

    # (3) no simulated-mode artifact -> skips (passes silently; the
    #     deliverable may even be absent)
    with tempfile.TemporaryDirectory() as tmp3:
        _write(os.path.join(tmp3, "notes.json"),
               json.dumps({"mode": "real-data"}))
        fails3 = check_simulation_disclosure(
            {"deliverable_path": os.path.join(tmp3, "deliverable.md")},
            workspace_root=tmp3)
        ok3 = not fails3

    # (4) subject but deliverable file missing entirely -> fails
    with tempfile.TemporaryDirectory() as tmp4:
        _dry_run_workspace(tmp4)
        fails4 = check_simulation_disclosure(
            {"deliverable_path": os.path.join(tmp4, "gone.md")},
            workspace_root=tmp4)
        ok4 = bool(fails4) and any("does not exist" in f for f in fails4)

    return ok1 and ok2 and ok3 and ok4


def test_concept_index_determinism_and_ranking():
    # type: () -> bool
    """Concept store contract: build_concept_index is deterministic (same
    corpus, any input order, byte-identical JSON), entities/cooccurrences/
    papers are deterministically sorted, and top_k_related / query_papers
    rank by co-mention adjacency with sane degenerate inputs."""

    with tempfile.TemporaryDirectory() as tmp:
        corpus = {
            "a.md": "# Paper A\n\nAlpha framework and Beta toolkit appear "
                    "together. Alpha matters most.\n",
            "b.md": "# Paper B\n\nBeta toolkit and Gamma library co-occur. "
                    "Gamma is a fresh angle.\n",
        }
        paths = []
        for name, text in corpus.items():
            path = os.path.join(tmp, name)
            with open(path, "w") as fh:
                fh.write(text)
            paths.append(path)

        idx1 = build_concept_index(paths)
        idx2 = build_concept_index(list(reversed(paths)))

        # (1) determinism: input order-insensitive, byte-identical JSON
        ok = json.dumps(idx1, sort_keys=True) == json.dumps(idx2, sort_keys=True)

        # (2) entities sorted by (count desc, name asc)
        names = [e["name"] for e in idx1["entities"]]
        ok = ok and all(
            (idx1["entities"][i]["count"] > idx1["entities"][i + 1]["count"])
            or (idx1["entities"][i]["count"] == idx1["entities"][i + 1]["count"]
                and names[i] < names[i + 1])
            for i in range(len(names) - 1))

        # (3) cooccurrences sorted by (count desc, name_a asc, name_b asc)
        cooc = idx1["cooccurrences"]
        ok = ok and all(
            (cooc[i][2] > cooc[i + 1][2])
            or (cooc[i][2] == cooc[i + 1][2] and cooc[i][0] < cooc[i + 1][0])
            or (cooc[i][2] == cooc[i + 1][2] and cooc[i][0] == cooc[i + 1][0]
                and cooc[i][1] < cooc[i + 1][1])
            for i in range(len(cooc) - 1))

        # (4) papers sorted by id
        ok = ok and [p["id"] for p in idx1["papers"]] == sorted(
            p["id"] for p in idx1["papers"])

        # (5) ranking sanity: "Alpha" co-mentions Beta in paper a; Beta is
        #     the top related concept; k caps the result and the ranking is
        #     prefix-consistent.
        related = top_k_related(idx1, "Alpha", 2)
        ok = ok and bool(related) and related[0] == "Beta" and len(related) <= 2
        broader = top_k_related(idx1, "Alpha", 5)
        ok = ok and related == broader[:len(related)]

        # (6) papers ranking: the Alpha seed appears only in paper a
        papers = query_papers(idx1, "Alpha", 5)
        ok = ok and bool(papers) and papers[0]["id"] == "a" and len(papers) <= 5

        # (7) degenerate queries: k <= 0 and unknown seeds return []
        ok = ok and top_k_related(idx1, "Alpha", 0) == []
        ok = ok and top_k_related(idx1, "Alpha", -1) == []
        ok = ok and top_k_related(idx1, "TotallyUnnamedConceptXYZ", 5) == []
        ok = ok and query_papers(idx1, "TotallyUnnamedConceptXYZ", 5) == []
        ok = ok and query_papers(idx1, "Alpha", 0) == []

    return ok


def test_aggregate_reviews_median_and_merging():
    # type: () -> bool
    """aggregate_reviews: per-criterion MEDIAN per component (even reviewer
    counts -> conservative lower of the two middle scores); non-empty
    revision feedback merged, order-preserving and de-duplicated; malformed
    reviews skipped; empty input -> round 0 with empty payloads."""

    def review(components, round_no=1):
        return {"gate": "ideation", "round": round_no, "components": components}

    r1 = review({
        "problem": {"criteria_scores": {
            "Clarity": {"score": 4, "justification": "clear framing"},
            "Relevance": {"score": 3, "justification": "weak match"}},
            "revision_feedback": "Make the research gap explicit."},
        "method": {"criteria_scores": {
            "Clarity": {"score": 2, "justification": "dense"}},
            "revision_feedback": ""},
    })
    r2 = review({
        "problem": {"criteria_scores": {
            "Clarity": {"score": 2, "justification": "vague"},
            "Relevance": {"score": 5, "justification": "strong match"}},
            "revision_feedback": "Make the research gap explicit."},
        "method": {"criteria_scores": {
            "Clarity": {"score": 5, "justification": "clear now"}},
            "revision_feedback": "Tighten the evaluation section."},
    })

    agg = aggregate_reviews([r1, r2])
    # even counts: Clarity [4,2] -> lower middle 2; Relevance [3,5] -> lower
    # middle 3; method Clarity [2,5] -> 2.
    ok = agg["round"] == 1
    ok = ok and agg["aggregate_scores"]["problem"]["Clarity"] == 2
    ok = ok and agg["aggregate_scores"]["problem"]["Relevance"] == 3
    ok = ok and agg["aggregate_scores"]["method"]["Clarity"] == 2
    # feedback: identical string de-duplicated (first occurrence wins);
    # method's empty feedback skipped, so only r2's survives.
    ok = ok and agg["revision_feedback"]["problem"] == \
        "Make the research gap explicit."
    ok = ok and agg["revision_feedback"]["method"] == \
        "Tighten the evaluation section."

    # odd count: Clarity [2,4,5] -> median 4; feedback merged order-preserving
    r3 = review({
        "problem": {"criteria_scores": {
            "Clarity": {"score": 5, "justification": "very clear"},
            "Relevance": {"score": 2, "justification": "off-topic"}},
            "revision_feedback": "Second reviewer note."},
    })
    agg3 = aggregate_reviews([r1, r2, r3])
    ok = ok and agg3["aggregate_scores"]["problem"]["Clarity"] == 4
    ok = ok and agg3["aggregate_scores"]["problem"]["Relevance"] == 3
    ok = ok and agg3["revision_feedback"]["problem"] == \
        "Make the research gap explicit. Second reviewer note."

    # empty input -> round 0 with empty payloads
    empty = aggregate_reviews([])
    ok = ok and empty["round"] == 0 and empty["aggregate_scores"] == {}
    ok = ok and empty["revision_feedback"] == {}

    # malformed reviews are skipped, not fatal
    agg4 = aggregate_reviews([{"gate": "ideation", "round": 1,
                               "components": "nope"}, r2])
    ok = ok and agg4["aggregate_scores"]["method"]["Clarity"] == 5
    return ok


def test_should_stop_branches_and_boundaries():
    # type: () -> bool
    """should_stop: pass / cap / plateau with precedence pass > cap >
    plateau; exactly-4 passes; cap at the boundary (round_no >= max_rounds,
    max_rounds <= 0 disables immediately); plateau requires BOTH no
    criterion improved AND an unchanged failing set."""

    def with_criteria(c, r, o, f, s):
        return {"Clarity": c, "Relevance": r, "Originality": o,
                "Feasibility": f, "Significance": s}

    def scores(problem=None, method=None, experiment_design=None):
        out = {}
        if problem is not None:
            out["problem"] = problem
        if method is not None:
            out["method"] = method
        if experiment_design is not None:
            out["experiment_design"] = experiment_design
        return out

    ok = True

    def expect(name, this, prev, round_no, max_rounds, stop, reason):
        nonlocal ok
        got_stop, got_reason = should_stop(this, prev, round_no, max_rounds)
        if (got_stop, got_reason) != (stop, reason):
            print("    FAIL  should_stop subcase %r: expected (%r, %r) got "
                  "(%r, %r)" % (name, stop, reason, got_stop, got_reason))
            ok = False

    all4 = with_criteria(4, 4, 4, 4, 4)
    all3 = with_criteria(3, 3, 3, 3, 3)
    mixed = with_criteria(4, 3, 4, 4, 4)   # Relevance below the bar

    # -- pass branch + the exactly-4 boundary -----------------------------
    expect("pass mid-loop", scores(problem=all4), None, 1, 3, True, "pass")
    expect("pass exactly at 4", scores(problem=all4, method=all4), None,
           2, 3, True, "pass")
    expect("pass beats cap", scores(problem=all4), None, 3, 3, True, "pass")
    expect("all-3 not pass", scores(problem=all3), None, 1, 3, False, "")

    # -- cap branch + boundary -------------------------------------------
    expect("cap at exact boundary", scores(problem=mixed), None, 3, 3,
           True, "cap")
    expect("cap below boundary", scores(problem=mixed), None, 2, 3,
           False, "")
    expect("cap max_rounds 0", scores(problem=mixed), None, 1, 0, True, "cap")
    expect("cap disabled loop", scores(problem=mixed), None, 0, 0, True, "cap")
    # precedence: when plateau conditions hold but the cap is hit, cap wins
    expect("plateau collides with cap", scores(problem=all3),
           scores(problem=all3), 3, 3, True, "cap")

    # -- plateau: BOTH no improvement AND unchanged failing set -----------
    expect("plateau identical rounds", scores(problem=all3),
           scores(problem=all3), 2, 3, True, "plateau")
    # an improved criterion (even one still failing) voids the plateau
    expect("improved voids plateau",
           scores(problem=with_criteria(4, 3, 3, 3, 3)),
           scores(problem=with_criteria(3, 3, 3, 3, 3)), 2, 3, False, "")
    # a NEW failing criterion changes the failing set -> no plateau
    expect("new failing criterion voids plateau",
           scores(problem=with_criteria(3, 4, 4, 4, 4),
                  method=with_criteria(3, 4, 4, 4, 4)),
           scores(problem=with_criteria(3, 4, 4, 4, 4)), 2, 3, False, "")
    # a FIXED failing criterion changes the failing set -> no plateau
    expect("fixed failing criterion voids plateau",
           scores(problem=with_criteria(3, 4, 4, 4, 4)),
           scores(problem=with_criteria(3, 4, 4, 4, 4),
                  method=with_criteria(3, 4, 4, 4, 4)), 2, 3, False, "")
    # round 1 with no previous round can never plateau
    expect("no prev never plateau", scores(problem=all3), None, 1, 3,
           False, "")
    # empty this-round scores: no pass, no plateau (cap still applies)
    expect("empty scores not pass/plateau", {}, None, 2, 3, False, "")
    expect("empty scores cap", {}, None, 3, 3, True, "cap")

    return ok


def test_token_bucket_boundaries():
    # type: () -> bool
    """token_bucket / initial_bucket: exact-fit allowance, denial over the
    budget, non-positive/non-numeric cost handling, non-mutating input
    state, and the initial budget formula max_rounds * reviewers *
    per_round_call_estimate (all clamped >= 0)."""

    ok = True

    def expect(name, state, cost, allowed, spent):
        nonlocal ok
        got_allowed, new_state = token_bucket(state, cost)
        if got_allowed != allowed or new_state.get("spent") != spent:
            print("    FAIL  token_bucket subcase %r: expected allowed=%r "
                  "spent=%r got allowed=%r spent=%r"
                  % (name, allowed, spent, got_allowed, new_state.get("spent")))
            ok = False

    bucket = {"budget": 6000, "spent": 5000}
    expect("exact fit", bucket, 1000, True, 6000)
    expect("over budget denied", bucket, 1001, False, 5000)
    expect("zero cost always allowed", bucket, 0, True, 5000)
    expect("negative cost clamped to 0", bucket, -5, True, 5000)
    expect("non-numeric cost treated as 0", bucket, "abc", True, 5000)
    expect("zero budget denied", {"budget": 0, "spent": 0}, 1, False, 0)
    expect("exhausted bucket denied",
           {"budget": 6000, "spent": 6000}, 1, False, 6000)
    expect("missing keys default 0", {}, 0, True, 0)

    # input state is never mutated
    original = {"budget": 6000, "spent": 5000}
    token_bucket(original, 1000)
    ok = ok and original == {"budget": 6000, "spent": 5000}

    # initial bucket: max_rounds * reviewers * per_round_call_estimate
    ok = ok and initial_bucket(3, 2, 1000) == {"budget": 6000, "spent": 0}
    ok = ok and initial_bucket(0, 2, 1000) == {"budget": 0, "spent": 0}
    ok = ok and initial_bucket(-1, 2, 1000) == {"budget": 0, "spent": 0}
    ok = ok and initial_bucket(3, "x", 1000) == {"budget": 0, "spent": 0}

    return ok


def test_stage_issues_operations_and_validation():
    # type: () -> bool
    """Append-only stage_issues operations: validate_stage_issues accept /
    reject (duplicate ids within and across stages, unknown stage keys,
    non-list values, malformed ids), stage_issues_insert / anchor, and the
    JIT anchor naming + gate -> stage mapping."""

    ok = True

    def expect(name, cond):
        nonlocal ok
        if not cond:
            print("    FAIL  stage_issues subcase %r" % name)
            ok = False

    # -- validate_stage_issues / stage_issue_violations -------------------
    good = {"stage_issues": {
        "literature_review": ["literature-review-anchor-r1"],
        "hypothesis": ["hypothesis-ideation-r1"],
        "analysis": ["analysis-anchor-r1", "analysis-rework-r2"],
    }}
    expect("valid map accepted", validate_stage_issues(good))
    expect("valid map no violations", stage_issue_violations(good) == [])
    expect("empty map accepted", validate_stage_issues({"stage_issues": {}}))

    dup_within = {"stage_issues": {"hypothesis": ["h1", "h1"]}}
    expect("duplicate within a stage rejected",
           not validate_stage_issues(dup_within))
    expect("duplicate violation named",
           any("duplicate issue_id 'h1'" in v
               for v in stage_issue_violations(dup_within)))

    dup_across = {"stage_issues": {"literature_review": ["x"],
                                   "hypothesis": ["x"]}}
    expect("duplicate across stages rejected",
           not validate_stage_issues(dup_across))

    unknown_stage = {"stage_issues": {"bogus": ["x"]}}
    expect("unknown stage key rejected",
           not validate_stage_issues(unknown_stage))
    expect("unknown stage violation named",
           any("not a canonical stage" in v
               for v in stage_issue_violations(unknown_stage)))

    non_list = {"stage_issues": {"hypothesis": "h1"}}
    expect("non-list value rejected", not validate_stage_issues(non_list))
    expect("non-list violation named",
           any("value is not a list" in v
               for v in stage_issue_violations(non_list)))

    expect("empty issue id rejected",
           not validate_stage_issues({"stage_issues": {"hypothesis": [""]}}))
    expect("non-string issue id rejected",
           not validate_stage_issues({"stage_issues": {"hypothesis": [1]}}))
    expect("missing map rejected",
           not validate_stage_issues({"stage_issues": "nope"}))
    expect("manifest not dict rejected", not validate_stage_issues(42))

    # -- stage_issues_insert (append-only semantics) ----------------------
    base = {}
    inserted = stage_issues_insert(base, "hypothesis", "hypothesis-ideation-r1")
    expect("insert creates the key",
           inserted == {"hypothesis": ["hypothesis-ideation-r1"]})
    expect("insert does not mutate input", base == {})
    again = stage_issues_insert(inserted, "hypothesis", "hypothesis-ideation-r2")
    expect("insert appends",
           again["hypothesis"] == ["hypothesis-ideation-r1",
                                   "hypothesis-ideation-r2"])
    expect("global duplicate rejected",
           stage_issues_insert(again, "hypothesis", "hypothesis-ideation-r1")
           == again)
    expect("cross-stage duplicate rejected",
           stage_issues_insert(
               {"literature_review": ["hypothesis-ideation-r1"]},
               "hypothesis", "hypothesis-ideation-r1")
           == {"literature_review": ["hypothesis-ideation-r1"]})
    expect("non-canonical stage rejected",
           stage_issues_insert({"hypothesis": ["h"]}, "bogus", "x")
           == {"hypothesis": ["h"]})
    expect("non-string id rejected",
           stage_issues_insert({"hypothesis": ["h"]}, "hypothesis", 7)
           == {"hypothesis": ["h"]})
    expect("non-list current value rejected",
           stage_issues_insert({"hypothesis": "h"}, "hypothesis", "x")
           == {"hypothesis": "h"})

    # -- stage_issues_anchor ----------------------------------------------
    expect("anchor is first/oldest",
           stage_issues_anchor({"hypothesis": ["hypothesis-ideation-r1",
                                               "hypothesis-ideation-r2"]},
                               "hypothesis") == "hypothesis-ideation-r1")
    expect("absent stage anchor is None",
           stage_issues_anchor({"hypothesis": ["h"]}, "literature_review")
           is None)
    expect("non-dict map anchor is None",
           stage_issues_anchor("nope", "hypothesis") is None)

    # -- JIT anchor naming + gate -> stage mapping ------------------------
    expect("hypothesis anchor is ideation",
           anchor_issue_ref("hypothesis") == "hypothesis-ideation-r1")
    expect("literature anchor",
           anchor_issue_ref("literature_review") == "literature-review-anchor-r1")
    expect("analysis anchor",
           anchor_issue_ref("analysis") == "analysis-anchor-r1")
    expect("paper writeup anchor",
           anchor_issue_ref("paper_writeup") == "paper-writeup-anchor-r1")
    expect("experiment planning anchor",
           anchor_issue_ref("experiment_planning")
           == "experiment-planning-anchor-r1")
    expect("experiment execution anchor",
           anchor_issue_ref("experiment_execution")
           == "experiment-execution-anchor-r1")
    expect("ideation gate serves hypothesis",
           stage_for_gate("ideation") == "hypothesis")
    expect("writeup gate serves paper_writeup",
           stage_for_gate("writeup") == "paper_writeup")
    expect("gate named like its stage",
           stage_for_gate("analysis") == "analysis")

    return ok


def test_derive_comment_record_zero_tokens():
    # type: () -> bool
    """derive_comment_record: rendered critiques carry ZERO STANDALONE
    PASS / FAIL / THRESHOLD / ROUTING / VERDICT words (case-insensitive
    whole-word matches) even under adversarial reviewer text (\"FAIL the
    threshold\", \"VERDICT\", \"surpass\", \"compass\").  Whole-word
    matching is the invariant: \"surpass\"/\"compass\"/\"passes\" pass
    through UNCHANGED (substring hits inside longer words are never
    substituted or flagged); the issue_ref follows the JIT anchor
    convention; malformed inputs return None."""

    banned = ("pass", "fail", "threshold", "routing", "verdict")

    def record(justification, feedback):
        return derive_comment_record({
            "gate": "hypothesis",
            "round": 1,
            "criteria_scores": {
                "Significance": {"score": 4, "justification": justification},
                "Originality": {"score": 3, "justification": "novel framing"},
            },
            "revision_feedback": feedback,
        })

    adversarial = [
        ("FAIL the threshold", "These results FAIL the threshold."),
        ("VERDICT", "The VERDICT rests on weak evidence."),
        ("surpass", "The method may surpass single-dataset baselines."),
        ("compass", "The compass of the study is narrow."),
        ("Routing", "If it passes, routing decides the next step."),
        ("threshold ROUTING verdict PASS FAIL",
         "PASS and FAIL are forbidden tokens; THRESHOLD too."),
    ]
    ok = True
    for justification, feedback in adversarial:
        rec = record(justification, feedback)
        if rec is None:
            print("    FAIL  derive_comment_record returned None for %r"
                  % justification)
            ok = False
            continue
        if rec["issue_ref"] != "hypothesis-ideation-r1":
            print("    FAIL  issue_ref %r != hypothesis-ideation-r1"
                  % rec["issue_ref"])
            ok = False
        if not rec["critique"].startswith("[review-critique: hypothesis-r1]"):
            print("    FAIL  critique marker missing in %r" % rec["critique"])
            ok = False
        lowered = rec["critique"].lower()
        # Whole-word invariant: banned tokens are STANDALONE words
        # (case-insensitive \b...\b matching, mirroring review_engine), so
        # inputs like "surpass"/"compass"/"passes" pass through UNCHANGED
        # and must NOT be flagged.  A substring check would false-positive
        # on those non-banned words; the leak test uses the same
        # word-boundary rule the engine enforces (invariant unchanged --
        # zero standalone banned words is still required).
        for token in banned:
            if re.search(r"\b" + re.escape(token) + r"\b",
                         rec["critique"], flags=re.IGNORECASE):
                print("    FAIL  banned token %r leaked into critique: %r"
                      % (token, rec["critique"]))
                ok = False
        if "revision feedback:" not in lowered:
            print("    FAIL  critique lacks the revision feedback line")
            ok = False

    # a non-hypothesis gate maps to its own stage anchor
    marker = derive_comment_record({
        "gate": "analysis", "round": 2,
        "criteria_scores": {"Quality": {"score": 4, "justification": "sound"}},
        "revision_feedback": "Add a robustness paragraph.",
    })
    ok = ok and marker is not None and marker["issue_ref"] == "analysis-anchor-r1"
    ok = ok and "[review-critique: analysis-r2]" in marker["critique"]

    # malformed inputs -> None (never a silent rendered critique)
    malformed = [
        None, 42, {},
        {"gate": "hypothesis", "round": 1, "criteria_scores": {},
         "revision_feedback": "x"},
        {"gate": "hypothesis", "round": 0,
         "criteria_scores": {"Significance": {"score": 4,
                                              "justification": "j"}},
         "revision_feedback": "x"},
        {"gate": "hypothesis", "round": 1,
         "criteria_scores": {"Significance": {"score": 4,
                                              "justification": "j"}},
         "revision_feedback": "   "},
        {"gate": "hypothesis", "round": True,
         "criteria_scores": {"Significance": {"score": 4,
                                              "justification": "j"}},
         "revision_feedback": "x"},
    ]
    for bad in malformed:
        if derive_comment_record(bad) is not None:
            print("    FAIL  malformed input %r produced a critique" % (bad,))
            ok = False

    return ok


def test_manifest_terminal_states():
    # type: () -> bool
    """Terminal-or-not for the dynamic lifecycle: resolved / closed /
    superseded / blocked are terminal; draft / open are not. Superseded
    issues stay terminal as history (never reopened); a stage may exit when
    every issue in stage_issues[stage] is terminal and the stage artifact
    exists."""

    terminal = ("resolved", "closed", "superseded", "blocked")
    non_terminal = ("draft", "open")
    ok = all(s in terminal for s in terminal)
    ok = ok and all(s not in terminal for s in non_terminal)
    if not ok:
        print("    FAIL  terminal status classification")

    manifest = {
        "stage_issues": {"hypothesis": ["h1", "h2"]},
        "artifacts": {"hypothesis": ["ideas/proposal-final.json"]},
    }
    statuses = {"h1": "superseded", "h2": "resolved"}
    all_terminal = all(statuses[iid] in terminal
                       for iid in manifest["stage_issues"]["hypothesis"])
    artifact_present = bool(manifest["artifacts"]["hypothesis"])
    ok = ok and all_terminal and artifact_present
    return ok


def main():
    # type: () -> int
    tests = [
        ("test_dispatch_ordering",    test_dispatch_ordering),
        ("test_manifest_schema",      test_manifest_schema),
        ("test_control_issue_filtering", test_control_issue_filtering),
        ("test_add_comment_target",   test_add_comment_target),
        ("test_review_engine_scoring_contract_and_routes",test_review_engine_scoring_contract_and_routes),
        ("test_malformed_retry_fallback",test_malformed_retry_fallback),
        ("test_config_limits_and_legacy_fallback",test_config_limits_and_legacy_fallback),
        ("test_missing_target_and_invalidation_invariants",test_missing_target_and_invalidation_invariants),
        ("test_manager_block_is_not_reviewer_verdict",test_manager_block_is_not_reviewer_verdict),
        ("test_extensions_and_all_routes",test_extensions_and_all_routes),
        ("test_writeup_limits_and_disabled_flow",test_writeup_limits_and_disabled_flow),
        ("test_writeup_exhaustion_and_total_boundary",test_writeup_exhaustion_and_total_boundary),
        ("test_stale_duplicate_prevention",test_stale_duplicate_prevention),
        ("test_final_verdict_compatibility_and_flat_manifest",test_final_verdict_compatibility_and_flat_manifest),
        ("test_pass_verdict_requires_nonempty_feedback",test_pass_verdict_requires_nonempty_feedback),
        ("test_fail_verdict_requires_nonempty_feedback",test_fail_verdict_requires_nonempty_feedback),
        ("test_pass_verdict_with_nonempty_feedback_valid",test_pass_verdict_with_nonempty_feedback_valid),
        ("test_validate_review_scoring",test_validate_review_scoring),
        ("test_derive_verdict_and_threshold_boundary",test_derive_verdict_and_threshold_boundary),
        ("test_derive_verdict_routing_cases",test_derive_verdict_routing_cases),
        ("test_validate_verdict_rejects_contradictory_stored",test_validate_verdict_rejects_contradictory_stored),
        ("test_fallback_derives_fail_and_routing",test_fallback_derives_fail_and_routing),
        ("test_writeup_outcome_with_scoring_responses",test_writeup_outcome_with_scoring_responses),
        ("test_check7_simulation_disclosure",test_check7_simulation_disclosure),
        ("test_concept_index_determinism_and_ranking",test_concept_index_determinism_and_ranking),
        ("test_aggregate_reviews_median_and_merging",test_aggregate_reviews_median_and_merging),
        ("test_should_stop_branches_and_boundaries",test_should_stop_branches_and_boundaries),
        ("test_token_bucket_boundaries",test_token_bucket_boundaries),
        ("test_stage_issues_operations_and_validation",test_stage_issues_operations_and_validation),
        ("test_derive_comment_record_zero_tokens",test_derive_comment_record_zero_tokens),
        ("test_manifest_terminal_states",test_manifest_terminal_states),
    ]

    failures = []
    for name, fn in tests:
        try:
            result = fn()
        except Exception as exc:
            print(f"  FAIL  {name}  (exception: {exc})")
            failures.append(name)
            continue

        if result:
            print(f"  PASS  {name}")
        else:
            print(f"  FAIL  {name}")
            failures.append(name)

    print()
    if failures:
        print(f"Result: FAILED ({len(failures)}/{len(tests)} tests failed)")
        return 1
    else:
        print("Result: ALL PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())