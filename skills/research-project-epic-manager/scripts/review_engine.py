#!/usr/bin/env python3
"""Deterministic stdlib review-gate state engine.

Reviewers return *scoring reviews*: gate, round, criteria_scores (per
criterion: int score 1-5 + one-sentence justification), revision_feedback,
and optional extra fields (e.g. ``integrity_mismatches``).  Reviewers never
emit ``verdict``/``failing_criteria``/``routing`` and are not told pass/fail
semantics.  The manager derives the stored seven-field verdict entry with
``derive_verdict``: verdict = FAIL iff any criterion score < PASS_THRESHOLD
(4), else PASS; failing_criteria = criteria scored < 4; routing = the gate's
pass route on PASS, else ``route_for_failure(gate, failing_criteria)``.
Stored entries keep the seven-field contract; ``validate_verdict`` enforces
derived-consistency (stored verdict/failing/routing must equal the
derivation).  Unknown criterion names and reviewer routing remain invalid.

Dynamic-lifecycle and commenting extensions (all additive; every existing
public function and behaviour is unchanged):

- ``validate_stage_issues(manifest)`` / ``stage_issue_violations(manifest)``
  enforce the append-only ``stage_issues`` map contract: a dict whose keys
  are a subset of the canonical six stages (``LINEAR_STAGES``) and whose
  values are lists of unique non-empty string issue_ids, with no issue_id
  repeated anywhere in the map.
- ``stage_issues_insert`` / ``stage_issues_anchor`` are the pure append-only
  map operations (insert rejects non-canonical stages, malformed ids, and
  global duplicates; anchor returns the first/oldest issue of a stage).
- ``derive_comment_record`` renders the dispatcher-posted human-readable
  critique comment from a SCORING review only (gate, round, criteria_scores,
  revision_feedback): ``{"issue_ref": <anchor issue_id>, "critique": str}``.
  Rendered critiques NEVER carry the derived verdict output and contain ZERO
  standalone PASS/FAIL/THRESHOLD/ROUTING/VERDICT words (case-insensitive
  whole-word matches) -- reviewer-supplied text is scrubbed with
  deterministic neutral substitutes ("clear", "fall short", "bar",
  "direction", "assessment") and NEVER a placeholder, so the invariant holds
  for any input; substring hits inside longer words (e.g. "surpass",
  "compass", "threshold_ledger.json") are left untouched.
- ``invalidate_and_route`` is a deprecated wrapper: legacy manifests
  (``stage_to_issue_id``) keep the legacy convention (the failing gate's
  own stage is the rework target, no per-criterion routing) exactly as
  before; new-style manifests (``stage_issues``) route over the append-only
  map to the ROUTE TARGET stage ``route_to`` (per ``route_for_failure``):
  whole-stage result invalidation at/downstream of route_to, downstream
  pending/queued dropped, downstream dispatched marked stale, and the
  target stage's first/anchor issue requeued -- or a rework-signal when
  the target stage has no issue yet.
"""
import json
import re

LINEAR_STAGES = ("literature_review", "hypothesis", "experiment_planning", "experiment_execution", "analysis", "paper_writeup")
GATES = {
    "hypothesis": {"criteria": ("Significance", "Originality"), "routes": ("literature_review", "experiment_execution"), "limit": "max_hypothesis_review_loops"},
    "analysis": {"criteria": ("Quality", "Significance", "Originality"), "routes": ("literature_review", "experiment_planning", "paper_writeup"), "limit": "max_experiment_review_loops"},
    "writeup": {"criteria": ("Clarity",), "routes": ("paper_writeup", "complete"), "limit": "max_writeup_review_loops"},
}
REQUIRED = ("gate", "round", "verdict", "criteria_scores", "failing_criteria", "revision_feedback", "routing")
SCORING_REQUIRED = ("gate", "round", "criteria_scores", "revision_feedback")
PASS_THRESHOLD = 4
# Pass route per gate: the routing a stored PASS entry must carry
# (used by derive_verdict and by validate_verdict's derived-consistency).
PASS_ROUTES = {
    "hypothesis": "experiment_execution",
    "analysis": "paper_writeup",
    "writeup": "complete",
}

def route_for_failure(gate, failing_criteria):
    """Manager routing for a FAIL: hypothesis always literature_review;
    analysis rewinds to literature_review on Significance/Originality, else
    experiment_planning on Quality-only; writeup always paper_writeup."""
    fc = set(failing_criteria or [])
    if gate == "analysis":
        if "Significance" in fc or "Originality" in fc:
            return "literature_review"
        if "Quality" in fc:
            return "experiment_planning"
        return "literature_review"
    if gate == "writeup":
        return "paper_writeup"
    return "literature_review"  # hypothesis and default fallback

def parse_verdict(raw):
    """Generic JSON-dict parser; also parses scoring reviews."""
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except (ValueError, TypeError): return None
    return raw if isinstance(raw, dict) else None

def validate_review_scoring(scoring, gate):
    """Validate a reviewer *scoring review* (what reviewers actually emit).

    All of SCORING_REQUIRED must be present; gate must match; round is an
    int >= 1 (not bool); criteria_scores must cover EXACTLY the gate's
    criteria, each item a dict with an int score 1-5 (not bool) and a
    non-empty ``justification`` string; revision_feedback must be a
    non-empty string after .strip().  Extra fields (e.g.
    ``integrity_mismatches``) are allowed and ignored; a ``verdict`` field,
    if one happens to be present, is ignored too -- reviewers are not asked
    to emit pass/fail semantics.
    """
    if gate not in GATES or not isinstance(scoring, dict): return False
    if any(k not in scoring for k in SCORING_REQUIRED): return False
    if scoring["gate"] != gate: return False
    if not isinstance(scoring["round"], int) or isinstance(scoring["round"], bool) or scoring["round"] < 1: return False
    if not isinstance(scoring["revision_feedback"], str) or not scoring["revision_feedback"].strip(): return False
    scores = scoring["criteria_scores"]
    spec = GATES[gate]
    if not isinstance(scores, dict) or set(scores) != set(spec["criteria"]): return False
    for criterion in spec["criteria"]:
        item = scores[criterion]
        if not isinstance(item, dict) or "score" not in item or "justification" not in item: return False
        if not isinstance(item["score"], int) or isinstance(item["score"], bool) or not 1 <= item["score"] <= 5: return False
        if not isinstance(item["justification"], str) or not item["justification"].strip(): return False
    return True

def derive_verdict(scoring, gate):
    """Manager-compose the stored seven-field verdict entry from a scoring
    review.  verdict = FAIL iff any criterion score < PASS_THRESHOLD (4),
    else PASS; failing_criteria = criteria scored < 4; routing = the gate's
    pass route on PASS else ``route_for_failure(gate, failing_criteria)``.
    Criterion scores and revision_feedback are carried through.
    """
    spec = GATES[gate]
    scores = scoring["criteria_scores"]
    failing = [c for c in spec["criteria"] if scores[c]["score"] < PASS_THRESHOLD]
    verdict = "FAIL" if failing else "PASS"
    routing = PASS_ROUTES[gate] if not failing else route_for_failure(gate, failing)
    return {
        "gate": gate,
        "round": scoring["round"],
        "verdict": verdict,
        "criteria_scores": dict(scores),
        "failing_criteria": failing,
        "revision_feedback": scoring["revision_feedback"],
        "routing": routing,
    }

def validate_verdict(verdict, gate):
    """Validate *stored* (manager-derived) seven-field verdict entries.

    All existing field/routing checks apply, plus derived-consistency: the
    stored verdict/failing_criteria/routing must equal what derive_verdict
    would produce from the criterion scores.  Manager records (decision_type
    manager_block/gate_disabled or manager_generated) are a separate schema
    and never reviewer verdicts; routing \"blocked\" is manager-only.
    """
    if gate not in GATES or not isinstance(verdict, dict) or any(k not in verdict for k in REQUIRED): return False
    # Manager records are a separate schema and never reviewer verdicts.
    if verdict.get("decision_type") in ("manager_block", "gate_disabled") or verdict.get("manager_generated"): return False
    spec = GATES[gate]
    if verdict["gate"] != gate or not isinstance(verdict["round"], int) or isinstance(verdict["round"], bool) or verdict["round"] < 1: return False
    if verdict["verdict"] not in ("PASS", "FAIL") or not isinstance(verdict["revision_feedback"], str): return False
    # Reporting-integrity: revision_feedback MUST be non-empty (after strip)
    # on stored entries, PASS and FAIL alike.  A PASS with empty feedback is
    # INVALID (not auto-FAIL) -- the caller treats it as malformed.
    if not verdict["revision_feedback"].strip(): return False
    scores = verdict["criteria_scores"]
    if not isinstance(scores, dict) or any(c not in scores for c in spec["criteria"]): return False
    if any(c not in spec["criteria"] for c in verdict["failing_criteria"] if isinstance(verdict["failing_criteria"], list)): return False
    for criterion in spec["criteria"]:
        item = scores[criterion]
        if not isinstance(item, dict) or "score" not in item or "justification" not in item or not isinstance(item["score"], int) or isinstance(item["score"], bool) or not 1 <= item["score"] <= 5 or not isinstance(item["justification"], str): return False
    failing = verdict["failing_criteria"]
    if not isinstance(failing, list) or len(set(failing)) != len(failing) or not all(c in spec["criteria"] for c in failing): return False
    if verdict["routing"] not in spec["routes"]: return False
    # Derived-consistency: the stored entry must equal the derivation.
    failing_derived = [c for c in spec["criteria"] if scores[c]["score"] < PASS_THRESHOLD]
    verdict_derived = "FAIL" if failing_derived else "PASS"
    routing_derived = PASS_ROUTES[gate] if not failing_derived else route_for_failure(gate, failing_derived)
    if verdict["verdict"] != verdict_derived or failing != failing_derived or verdict["routing"] != routing_derived: return False
    return True

def fallback_verdict(gate, round_number):
    """Fallback after one malformed retry: build a scoring review with every
    criterion at score 1 and derive the stored entry from it (consistent
    derived routing, e.g. analysis FAIL on Quality -> experiment_planning,
    FAIL on Significance -> literature_review)."""
    spec = GATES[gate]
    scoring = {
        "gate": gate,
        "round": round_number,
        "criteria_scores": {c: {"score": 1, "justification": "Reviewer response malformed after retry."} for c in spec["criteria"]},
        "revision_feedback": "Malformed reviewer response after one retry; manual inspection required.",
    }
    verdict = derive_verdict(scoring, gate)
    verdict["fallback"] = True
    return verdict

def normalize_review_config(config):
    config = dict(config or {})
    review = dict(config.get("review") or {})
    present = "max_writeup_review_loops" in review
    review["_writeup_loop_present"] = present
    for key in ("max_hypothesis_review_loops", "max_experiment_review_loops", "max_writeup_review_loops"):
        review.setdefault(key, 0)
    review.setdefault("max_total_project_loops", 10)
    config["review"] = review
    synthesis = dict(config.get("synthesis") or {})
    if present:
        synthesis["max_review_rounds"] = 0
    config["synthesis"] = synthesis
    return config

def manager_block(state, gate, reason, block_type="exhaustion"):
    """Record a manager-generated blocked routing decision.  routing
    \"blocked\" is NOT a reviewer-allowed route; such records never pass
    validate_verdict."""
    event = {"decision_type": "manager_block", "block_type": block_type,
             "gate": gate, "current_gate": gate, "current_route": "blocked",
             "reason": reason}
    state["current_route"] = "blocked"
    state["current_gate"] = gate
    state["current_reason"] = reason
    state.setdefault("block_events", []).append(event)
    state.setdefault("decision_events", []).append(event)
    return event

def invalidate_and_route(manifest, gate, results, pending, queued, dispatched, stale, notify=None, route_to=None):
    """Backward invalidate on FAIL (DEPRECATED wrapper).

    Route-target semantics by manifest style:

    - Legacy manifests (``stage_to_issue_id``) take the historical path
      exactly as before (legacy convention: the failing gate's own stage is
      the rework target).  ``route_to`` is ignored.
    - New-style manifests (``stage_issues``) route to the ROUTE TARGET stage
      ``route_to`` (per ``route_for_failure``; must be passed): whole-stage
      result invalidation at/downstream of route_to, downstream
      pending/queued issue_ids dropped, downstream dispatched subagents
      marked stale in ``stale`` (subagent_id -> issue_id), and the target
      stage's FIRST (anchor) issue requeued (duplicate-prevented).  When
      ``stage_issues[route_to]`` has no issue, returns (None, None)
      signalling that the caller must open a rework issue
      ``<route_to>-rework-r<n>`` seeded with the FAIL feedback.

    Returns (target_issue_id, error); error is not None when the route
    target is missing/invalid.
    """
    if isinstance(manifest.get("stage_issues"), dict):
        return _invalidate_and_route_stage_issues(
            manifest, gate, results, pending, queued, dispatched, stale, notify, route_to)
    return _invalidate_and_route_legacy(
        manifest, gate, results, pending, queued, dispatched, stale, notify)


def _invalidate_and_route_legacy(manifest, gate, results, pending, queued, dispatched, stale, notify=None):
    """Legacy 1:1 ``stage_to_issue_id`` path (historical behaviour verbatim).

    Legacy convention: the failing gate's own stage is the rework target (no
    per-criterion routing), so invalidation starts at the gate's own stage
    and the gate's own issue is requeued."""
    stages = manifest.get("stage_to_issue_id") or {}
    target = stages.get(gate)
    if not target:
        return None, "No route target for gate %r" % gate
    try:
        idx = LINEAR_STAGES.index(gate)
    except ValueError:
        return None, "Gate %r not in linear stages" % gate
    for stage in LINEAR_STAGES[idx:]:
        issue_id = stages.get(stage)
        if issue_id:
            results.pop(issue_id, None)
    for stage in LINEAR_STAGES[idx + 1:]:
        issue_id = stages.get(stage)
        if not issue_id:
            continue
        if issue_id in pending:
            pending.remove(issue_id)
        if issue_id in queued:
            queued.remove(issue_id)
        if issue_id in dispatched:
            stale[dispatched[issue_id]] = issue_id
    if target not in pending and target not in queued:
        pending.append(target)
    if notify is not None:
        notify(target)
    return target, None


def _invalidate_and_route_stage_issues(manifest, gate, results, pending, queued, dispatched, stale, notify=None, route_to=None):
    """New-style ``stage_issues`` path: whole-stage invalidation at/downstream
    of the ROUTE TARGET stage ``route_to``, then requeue/signal for
    ``stage_issues[route_to]``.

    ``gate`` is the failing gate (diagnostics only); ``route_to`` is the
    stage the FAIL routes back to (per ``route_for_failure``).  Results of
    every issue at/downstream of route_to (including route_to itself) are
    wiped whole-stage; pending/queued issue_ids strictly downstream of
    route_to are dropped; downstream dispatched subagents are marked stale
    (subagent_id -> issue_id).

    Returns ``(target_issue_id, error)``:
    - ``route_to`` missing or not a canonical stage -> ``(None, error)``,
      nothing changed.
    - ``stage_issues[route_to]`` has an anchor -> the anchor (first issue)
      is requeued (duplicate-prevented; ``notify`` called with it) and
      ``(anchor, None)`` is returned.
    - ``stage_issues[route_to]`` is absent or empty -> ``(None, None)``:
      no existing issue to requeue, signalling that the caller must open a
      rework issue ``<route_to>-rework-r<n>`` seeded with the FAIL feedback
      (rework lands in the target stage's entry).
    """
    if route_to is None:
        return None, "No route target for stage %r" % gate
    stage_issues = manifest.get("stage_issues") or {}
    try:
        idx = LINEAR_STAGES.index(route_to)
    except ValueError:
        return None, "Route target %r not in linear stages" % route_to
    # Whole-stage invalidation at/downstream of the ROUTE TARGET (including
    # route_to itself), unconditional on FAIL per the binding spec.
    for stage in LINEAR_STAGES[idx:]:
        for issue_id in stage_issues.get(stage, ()):
            results.pop(issue_id, None)
    # Drop pending/queued and stale-mark dispatched issues strictly
    # downstream of the route target (the target's own stage is the
    # requeue/rework site).
    for stage in LINEAR_STAGES[idx + 1:]:
        for issue_id in stage_issues.get(stage, ()):
            if issue_id in pending:
                pending.remove(issue_id)
            if issue_id in queued:
                queued.remove(issue_id)
            if issue_id in dispatched:
                stale[dispatched[issue_id]] = issue_id
    target_ids = stage_issues.get(route_to)
    if not isinstance(target_ids, list) or not target_ids:
        # Target stage has no issue yet: nothing to requeue; signal that the
        # caller must open <route_to>-rework-r<n> with the FAIL feedback.
        return None, None
    target = target_ids[0]
    if target not in pending and target not in queued:
        pending.append(target)
    if notify is not None:
        notify(target)
    return target, None

def record_reviewer_invocation(state, verdict):
    """Record a *stored* (derived) verdict entry in verdict_history."""
    entry = {k: verdict[k] for k in REQUIRED if k in verdict}
    state.setdefault("verdict_history", []).append(entry)
    return state

def record_fallback(state, gate, round_number):
    """Record the fallback stored entry (derived from an all-1 scoring
    review) after one malformed retry; returns the fallback verdict."""
    verdict = fallback_verdict(gate, round_number)
    record_reviewer_invocation(state, verdict)
    state.setdefault("fallbacks", []).append({"gate": gate, "round": round_number})
    return verdict

def writeup_limit(config):
    """Max writeup rounds: new field when explicitly present, else legacy
    synthesis.max_review_rounds.  Reads the (already normalized) config
    directly -- do NOT re-normalize here, because normalization's setdefault
    would re-insert ``max_writeup_review_loops`` and flip
    ``_writeup_loop_present`` on a second pass."""
    review = config.get("review", {})
    if review.get("_writeup_loop_present"):
        return review.get("max_writeup_review_loops", 0)
    return config.get("synthesis", {}).get("max_review_rounds", 0)

def writeup_outcome(config, reviewer_responses):
    """Model the writeup Clarity gate.  ``reviewer_responses`` are SCORING
    reviews (not completed verdicts).  Per round: parse -> validate scoring
    (malformed/empty feedback -> one retry -> fallback) -> derive_verdict ->
    record; increment counters; PASS iff the derived verdict is PASS.
    Loop-exhaustion/total-limit manager_block paths are unchanged.

    Returns (state, final_verdict, blocked) where final_verdict is
    \"APPROVE\"/\"REJECT\" (legacy-compatible names).
    """
    config = normalize_review_config(config)
    limit = writeup_limit(config)
    state = {"loop_counters": {"writeup_gate": 0, "total_project_loops": 0}, "verdict_history": [], "block_events": []}
    if limit <= 0:
        state.setdefault("decision_events", []).append({"decision_type": "gate_disabled", "gate": "writeup", "max_rounds": 0})
        return state, "APPROVE", False
    for number in range(1, limit + 1):
        if state["loop_counters"]["total_project_loops"] >= config["review"]["max_total_project_loops"]:
            state["loop_counters"]["writeup_gate"] += 1; state["loop_counters"]["total_project_loops"] += 1
            manager_block(state, "writeup", "Total project loop limit exhausted during writeup")
            return state, "REJECT", True
        raw = reviewer_responses.pop(0) if reviewer_responses else None
        scoring = parse_verdict(raw)
        if not scoring or not validate_review_scoring(scoring, "writeup"):
            raw = reviewer_responses.pop(0) if reviewer_responses else None
            scoring = parse_verdict(raw)
        if not scoring or not validate_review_scoring(scoring, "writeup"):
            verdict = record_fallback(state, "writeup", number)
        else:
            verdict = derive_verdict(scoring, "writeup")
            record_reviewer_invocation(state, verdict)
        state["loop_counters"]["writeup_gate"] += 1; state["loop_counters"]["total_project_loops"] += 1
        if verdict["verdict"] == "PASS": return state, "APPROVE", False
    manager_block(state, "writeup", "Writeup Clarity gate exhausted after %d rounds" % limit, "writeup_exhausted")
    return state, "REJECT", True


# ---------------------------------------------------------------------------
# Dynamic-lifecycle + commenting extensions (additive; see module docstring)
# ---------------------------------------------------------------------------

# Anchor purposes per stage: the first issue opened in a stage is its anchor;
# the hypothesis stage's anchor purpose is "ideation" (hypothesis-ideation-r1).
_ANCHOR_PURPOSES = {"hypothesis": "ideation"}
# Gate names that do not equal their stage name (ideation reviews serve the
# hypothesis stage; the writeup gate serves paper_writeup).
_STAGE_FOR_GATE = {"ideation": "hypothesis", "writeup": "paper_writeup"}
# Tokens forbidden in rendered critique text as STANDALONE words only
# (case-insensitive whole-word matches; substring hits inside longer words
# such as "surpass"/"compass"/"threshold_ledger.json" are not banned).
_BANNED_TOKENS = ("pass", "fail", "threshold", "routing", "verdict")
# Deterministic neutral substitutes for banned words, each outside the
# banned vocabulary; rendered critiques NEVER emit placeholders like
# "<redacted>".
_SCRUB_SUBSTITUTES = {
    "pass": "clear",
    "fail": "fall short",
    "threshold": "bar",
    "routing": "direction",
    "verdict": "assessment",
}


def stage_for_gate(gate):
    """Stage a gate serves: ``ideation`` -> ``hypothesis``, ``writeup`` ->
    ``paper_writeup``, otherwise the gate name itself."""
    return _STAGE_FOR_GATE.get(gate, gate)


def _stage_kebab(stage):
    """``literature_review`` -> ``literature-review`` (kebab slug)."""
    return str(stage).replace("_", "-")


def anchor_issue_ref(stage):
    """Anchor issue_id a stage would carry by the JIT convention:
    ``<stage-kebab>-<purpose>-r1`` (hypothesis anchor purpose "ideation",
    all other stages "anchor").  Examples: ``literature-review-anchor-r1``,
    ``hypothesis-ideation-r1``, ``analysis-anchor-r1``."""
    stage = stage_for_gate(stage)
    purpose = _ANCHOR_PURPOSES.get(stage, "anchor")
    return "%s-%s-r1" % (_stage_kebab(stage), purpose)


def stage_issue_violations(manifest):
    """-> list[str] of human-readable violations of the append-only
    ``stage_issues`` map contract (empty list == valid).  Contract:
    ``stage_issues`` is a dict; every key is a canonical stage (a subset of
    ``LINEAR_STAGES``); every value is a list of non-empty string issue_ids;
    no issue_id is repeated within a stage list or anywhere across stages.
    A missing or non-dict ``stage_issues`` is reported as one violation.
    """
    if not isinstance(manifest, dict):
        return ["manifest is not a dict"]
    stage_issues = manifest.get("stage_issues")
    if not isinstance(stage_issues, dict):
        return ["stage_issues is missing or not a dict"]
    violations = []
    seen = set()
    for stage in sorted(stage_issues):
        if stage not in LINEAR_STAGES:
            violations.append("stage %r is not a canonical stage" % stage)
        issue_ids = stage_issues[stage]
        if not isinstance(issue_ids, list):
            violations.append("stage %r: value is not a list" % stage)
            continue
        for issue_id in issue_ids:
            if not isinstance(issue_id, str) or not issue_id.strip():
                violations.append("stage %r: non-string or empty issue id %r" % (stage, issue_id))
            elif issue_id in seen:
                violations.append("duplicate issue_id %r (stage %r)" % (issue_id, stage))
            else:
                seen.add(issue_id)
    return violations


def validate_stage_issues(manifest):
    """True iff the append-only ``stage_issues`` map satisfies the contract
    enforced by ``stage_issue_violations`` (no violations)."""
    return not stage_issue_violations(manifest)


def stage_issues_insert(stage_issues, stage, issue_id):
    """Append-only insert: returns a NEW stage_issues dict with ``issue_id``
    appended to ``stage_issues[stage]``.

    Rejects (returns the input unchanged, never mutating it) when the stage
    is not canonical, the issue_id is not a non-empty string, the stage's
    current value is not a list, or the issue_id already exists anywhere in
    the map (global uniqueness).  A stage key absent from the map is created
    with its first element.
    """
    if not isinstance(stage_issues, dict) or stage not in LINEAR_STAGES:
        return stage_issues
    if not isinstance(issue_id, str) or not issue_id.strip():
        return stage_issues
    current = stage_issues.get(stage)
    if current is not None and not isinstance(current, list):
        return stage_issues
    if any(issue_id in (lst or []) for lst in stage_issues.values()):
        return stage_issues
    new = {s: list(v) for s, v in stage_issues.items()}
    new[stage] = (list(current) if current else []) + [issue_id]
    return new


def stage_issues_anchor(stage_issues, stage):
    """-> the first (oldest) issue_id of ``stage_issues[stage]`` (the anchor
    by creation order), or None when the stage has no entry."""
    issue_ids = stage_issues.get(stage) if isinstance(stage_issues, dict) else None
    return issue_ids[0] if isinstance(issue_ids, list) and issue_ids else None


def _scrub_banned(text):
    """Replace every case-insensitive STANDALONE banned word in
    reviewer-supplied text with its deterministic neutral substitute
    (``_SCRUB_SUBSTITUTES``) so rendered critiques can never leak a banned
    token.  Whole-word matching only: substring hits inside longer words
    (e.g. "passing", "surpass", "compass", "threshold_ledger.json") are
    left untouched.  Never emits a placeholder."""
    for token, substitute in _SCRUB_SUBSTITUTES.items():
        text = re.sub(
            r"\b" + re.escape(token) + r"\b",
            substitute,
            text,
            flags=re.IGNORECASE,
        )
    return text


def _contains_banned(text):
    """True iff any STANDALONE banned word occurs in ``text``
    (case-insensitive whole-word match)."""
    return any(
        re.search(r"\b" + re.escape(token) + r"\b", text, flags=re.IGNORECASE)
        for token in _BANNED_TOKENS
    )


def derive_comment_record(scoring, stage=None):
    """Render the dispatcher-posted critique comment from a SCORING review.

    Input: the reviewer's scoring dict (``gate``, ``round``,
    ``criteria_scores`` {criterion: {score 1-5, justification}}, non-empty
    ``revision_feedback``) -- never the derived verdict entry.  ``stage``
    optionally overrides the stage used to compute ``issue_ref``; when None
    it is derived from the gate via ``stage_for_gate``.

    Returns None on malformed input (non-dict, missing gate/round/
    criteria_scores, empty criteria_scores, empty revision_feedback after
    .strip(), or a non-int round < 1).  Otherwise returns::

        {"issue_ref": <anchor issue_id of the gate's stage>,
         "critique": <rendered critique text>}

    The rendered critique carries the marker
    ``[review-critique: <gate>-r<round>]``, lists every criterion with its
    score and one-sentence justification, and ends with the non-empty
    ``revision_feedback``.  It contains ZERO standalone PASS/FAIL/THRESHOLD/
    ROUTING/VERDICT words (case-insensitive whole-word matches);
    reviewer-supplied text is scrubbed with deterministic neutral
    substitutes (never placeholders) so the invariant holds for any input,
    and a hard guard raises AssertionError if a banned word would still leak.
    """
    if not isinstance(scoring, dict):
        return None
    gate = scoring.get("gate")
    round_no = scoring.get("round")
    criteria = scoring.get("criteria_scores")
    feedback = scoring.get("revision_feedback")
    if not isinstance(gate, str) or not gate.strip():
        return None
    if not isinstance(round_no, int) or isinstance(round_no, bool) or round_no < 1:
        return None
    if not isinstance(criteria, dict) or not criteria:
        return None
    if not isinstance(feedback, str) or not feedback.strip():
        return None
    if stage is None:
        stage = stage_for_gate(gate)

    lines = ["[review-critique: %s-r%d]" % (gate, round_no), ""]
    lines.append("Review round %d for %s:" % (round_no, _stage_kebab(stage)))
    lines.append("")
    for criterion in sorted(criteria):
        item = criteria[criterion]
        if not isinstance(item, dict):
            continue
        score = item.get("score")
        justification = item.get("justification")
        if isinstance(score, int) and not isinstance(score, bool) and 1 <= score <= 5:
            qualifier = ("meets the bar" if score >= PASS_THRESHOLD
                         else "below the bar")
            justification = _scrub_banned(str(justification)) if isinstance(justification, str) else ""
            lines.append("- %s: score %d (%s) -- %s" % (criterion, score, qualifier, justification))
    lines.append("")
    lines.append("Revision feedback: %s" % _scrub_banned(feedback.strip()))

    critique = "\n".join(lines)
    if _contains_banned(critique):
        raise AssertionError("banned token leaked into rendered critique")
    return {"issue_ref": anchor_issue_ref(stage), "critique": critique}