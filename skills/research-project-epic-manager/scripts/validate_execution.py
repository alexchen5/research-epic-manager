#!/usr/bin/env python3
"""Post-execution validation script for research-project-epic-manager.

Reads a ``project.json`` file after Phase E completes (path passed as the
first CLI argument) and validates that the protocol was followed correctly.

Stdlib-only.  Exits 0 if ALL checks pass, 1 if ANY check fails.

Checks 1-7 are the preserved baseline; Check 5 accepts the dynamic-lifecycle
terminal statuses (resolved / blocked / closed / superseded). Checks 8-11
enforce the communication-logging and ideation contracts:

* Check 8 -- directive-trail parity (interventions ledger entry
  <-> [directive: <digest>] / [human-directive: <digest>] comment on the
  affected issue, both directions);
* Check 9 -- thread liveness (every non-control issue has >= 1 comment);
* Check 10 -- reviewer-comment parity (each verdict_history entry maps to
  a [review-critique: <gate>-r<round>] comment on the stage anchor;
  manager-generated entries -- fallback:true, the disabled round-0 writeup
  placeholder, loop-limit synthetics with routing "blocked" -- are exempt
  but require a [manager-notice] comment);
* Check 11 -- ideation evidence (active only when ideation.max_rounds > 0;
  hypothesis thread shows >= 2 [proposal-v<n>] comments OR a recorded stop
  condition; when ideation is absent/disabled the manifest must record an
  "ideation_disabled" stop condition whenever a hypothesis stage exists --
  only a manifest with no hypothesis stage at all is exempt).

Legacy manifests (stage_to_issue_id / planning.num_issues / status
"issues-created") are auto-detected and validated with adapted checks.

Usage::

    python3 validate_execution.py EPICS_ROOT/<epic>/project.json
    python3 validate_execution.py --self-test
"""

import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from review_engine import stage_for_gate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_project(path: str) -> dict:
    """Load and return ``project.json`` from *path*.

    Exits immediately (code 1) if the file does not exist or is not valid
    JSON, printing a helpful message.
    """
    if not os.path.isfile(path):
        print(f"  FAIL  Input file does not exist: {path}")
        sys.exit(1)

    try:
        with open(path, "r") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"  FAIL  project.json is not valid JSON -- {exc}")
        sys.exit(1)


def _manifest_style(project: dict) -> str:
    """Auto-detect the manifest style.

    Returns ``"new"`` when the append-only ``stage_issues`` map is present
    (or neither style marker is), ``"legacy"`` when the manifest still
    carries ``stage_to_issue_id`` and/or ``planning.num_issues`` and/or the
    legacy status ``"issues-created"``.
    """
    if isinstance(project.get("stage_issues"), dict):
        return "new"
    if isinstance(project.get("stage_to_issue_id"), dict):
        return "legacy"
    planning = project.get("planning")
    if isinstance(planning, dict) and "num_issues" in planning:
        return "legacy"
    if project.get("status") == "issues-created":
        return "legacy"
    return "new"


# Documented comment markers from references/communication-logging.md
# "Marker set" (the validator keys off these spellings).
_DOCUMENTED_MARKERS = (
    "[seeding]",
    "[seeded-fail-feedback]",
    "[directive:",
    "[human-directive:",
    "[proposal-v",
    "[review-critique:",
    "[manager-notice",
    "block-linked",
)

_DIRECTIVE_RE = re.compile(
    r"\[(?:directive|human-directive):\s*([^\]]+)\]", re.IGNORECASE)
_PROPOSAL_RE = re.compile(r"\[proposal-v\d+\]", re.IGNORECASE)


def _issue_entries(project: dict) -> list:
    """The ``issues[]`` array (empty list when missing/malformed)."""
    issues = project.get("issues")
    return issues if isinstance(issues, list) else []


def _issue_map(project: dict) -> dict:
    """issue_id -> issue entry dict."""
    return {i.get("issue_id"): i for i in _issue_entries(project)
            if isinstance(i, dict)}


def _stage_issue_ids(project: dict, stage: str) -> list:
    """Issue ids belonging to *stage* (new ``stage_issues[stage]`` list, else
    legacy ``stage_to_issue_id[stage]`` single id, else issue entries with a
    matching ``stage`` field)."""
    stage_issues = project.get("stage_issues")
    if isinstance(stage_issues, dict):
        ids = stage_issues.get(stage)
        if isinstance(ids, list):
            return [i for i in ids if isinstance(i, str) and i.strip()]
        return []
    legacy = project.get("stage_to_issue_id")
    if isinstance(legacy, dict):
        iid = legacy.get(stage)
        return [iid] if isinstance(iid, str) and iid.strip() else []
    return [i.get("issue_id") for i in _issue_entries(project)
            if i.get("stage") == stage and isinstance(i.get("issue_id"), str)]


def _anchor_issue_id(project: dict, stage: str):
    """The anchor issue id of a stage: ``stage_issues[stage][0]`` (new), the
    legacy ``stage_to_issue_id[stage]`` value, else the first issue entry
    flagged ``anchor: true`` (then the first entry) for that stage.
    Returns None when no anchor can be determined (loud failure upstream).
    """
    stage_issues = project.get("stage_issues")
    if isinstance(stage_issues, dict):
        ids = stage_issues.get(stage)
        if isinstance(ids, list) and ids and isinstance(ids[0], str) and ids[0].strip():
            return ids[0]
        return None
    legacy = project.get("stage_to_issue_id")
    if isinstance(legacy, dict):
        iid = legacy.get(stage)
        if isinstance(iid, str) and iid.strip():
            return iid
        return None
    for issue in _issue_entries(project):
        if issue.get("stage") == stage and issue.get("anchor"):
            return issue.get("issue_id")
    for issue in _issue_entries(project):
        if issue.get("stage") == stage:
            return issue.get("issue_id")
    return None


def _issue_comments(project: dict, epics_root: str | None, issue: dict):
    """Read all comment texts of *issue* from its ``comments/`` directory.

    The directory is resolved as ``<epics_root>/<issue_path>/comments``
    (``issue_path`` is relative to the epic root, e.g.
    ``issues/hypothesis-ideation-r1/ISSUE.md``).

    Returns ``(comments, err)``: on success ``err`` is None; a missing
    ``issue_path``, a missing epics root, an unreadable tree, or a missing
    comments directory are reported as a loud error string (never a silent
    skip).
    """
    iid = issue.get("issue_id", "<unknown>")
    issue_path = issue.get("issue_path")
    if not isinstance(issue_path, str) or not issue_path.strip():
        return None, ("Check: issue %r has no 'issue_path' entry -- cannot "
                      "resolve its comments directory" % iid)
    if not epics_root:
        return None, ("Check: no epic root supplied -- cannot resolve "
                      "issue_path %r for issue %r" % (issue_path, iid))
    # ``issue_path`` points at the ISSUE.md file; the comments directory is
    # its sibling (``issues/<issue-id>/comments``).
    issue_dir = os.path.dirname(issue_path)
    if issue_dir:
        comments_dir = os.path.join(epics_root, issue_dir, "comments")
    else:
        comments_dir = os.path.join(epics_root, "comments")
    if not os.path.isdir(comments_dir):
        return [], ("Check: comments directory missing for issue %r: %s"
                    % (iid, comments_dir))
    texts = []
    try:
        for name in sorted(os.listdir(comments_dir)):
            full = os.path.join(comments_dir, name)
            if os.path.isfile(full):
                with open(full, "r", errors="replace") as fh:
                    texts.append(fh.read())
    except OSError as exc:
        return None, ("Check: cannot read comments for issue %r: %s"
                      % (iid, exc))
    return texts, None


# ---------------------------------------------------------------------------
# Individual checks (1-7 preserved baseline)
# ---------------------------------------------------------------------------


def check_resolved_issues_have_cost(project: dict) -> list:
    """**Check 1** -- Every resolved issue has ``cost`` with non-zero tokens.

    Looks for ``cost`` on the issue entry itself first, then falls back to
    ``project.json["results"][issue_id]["cost"]``, then to the documented
    accumulation ledger ``project.json["results"]["costs"][issue_id]``.

    Returns a list of human-readable failure messages (empty = pass).
    """
    issues = project.get("issues", [])
    results = project.get("results", {})
    failures: list[str] = []

    for issue in issues:
        if issue.get("control"):
            continue
        if issue.get("status") != "resolved":
            continue

        iid = issue.get("issue_id", "<unknown>")

        # Look for cost on the issue entry first, then in the per-issue
        # result, then in the documented accumulation ledger
        # results["costs"][issue_id].
        cost = issue.get("cost")
        if not cost or not isinstance(cost, dict):
            cost = results.get(iid, {}).get("cost")
        if not cost or not isinstance(cost, dict):
            costs_ledger = results.get("costs")
            if isinstance(costs_ledger, dict):
                cost = costs_ledger.get(iid)

        if not cost or not isinstance(cost, dict):
            failures.append(
                f"    FAIL  Issue '{iid}' is resolved but has no 'cost' field "
                f"(checked issue entry, results[{iid}].cost, and "
                f"results['costs'][{iid}])"
            )
            continue

        def _check_token(field: str, label: str) -> None:
            val = cost.get(field, 0)
            if not isinstance(val, (int, float)) or val <= 0:
                failures.append(
                    f"    FAIL  Issue '{iid}': {label} is {val} "
                    f"(must be a positive integer > 0)"
                )

        _check_token("input_tokens", "input_tokens")
        _check_token("output_tokens", "output_tokens")
        _check_token("cache_read_tokens", "cache_read_tokens")

    return failures


def _writeup_gate_engaged(project: dict) -> bool:
    """True when a writeup gate is engaged (Check 2 activation).

    Engaged when any of the following holds:

    * ``config.synthesis.max_review_rounds > 0`` -- the legacy active
      writeup path (after normalization);
    * ``config.review.max_writeup_review_loops > 0`` -- the new-style
      active writeup path (after normalization; new-style runs force
      ``max_review_rounds`` to 0, so this surface keeps the external
      contract live);
    * the manifest records any writeup-gate activity in ``review_state``:
      a ``verdict_history`` entry with ``gate == "writeup"`` (including the
      manager-generated disabled round-0 placeholder) or a
      ``block_events`` / ``decision_events`` entry with
      ``gate == "writeup"`` (e.g. a loop-limit block).
    """
    config = project.get("config")
    if not isinstance(config, dict):
        config = {}
    synthesis = config.get("synthesis")
    if not isinstance(synthesis, dict):
        synthesis = {}
    review = config.get("review")
    if not isinstance(review, dict):
        review = {}
    for value in (synthesis.get("max_review_rounds", 0),
                  review.get("max_writeup_review_loops", 0)):
        if isinstance(value, (int, float)) and value > 0:
            return True
    review_state = project.get("review_state")
    if isinstance(review_state, dict):
        for key in ("verdict_history", "block_events", "decision_events"):
            entries = review_state.get(key)
            if isinstance(entries, list) and any(
                    isinstance(e, dict) and e.get("gate") == "writeup"
                    for e in entries):
                return True
    return False


def check_review_evidence(project: dict) -> list:
    """**Check 2** -- Writeup review evidence plus the external
    ``final_verdict`` contract.

    When ``config.synthesis.max_review_rounds > 0`` (the legacy active
    writeup path) the deliverable must carry review evidence:
    ``review_rounds >= 1`` (unchanged legacy rule).

    The external contract -- ``final_verdict`` MUST be ``"APPROVE"`` or
    ``"REJECT"``, never ``"UNKNOWN"``/``"SKIPPED"``/``"BLOCKED"`` --
    activates whenever a writeup gate is engaged (see
    ``_writeup_gate_engaged``): ``synthesis.max_review_rounds > 0`` OR
    ``review.max_writeup_review_loops > 0`` (after normalization) OR any
    writeup ``verdict_history`` / ``block_events`` / ``decision_events``
    entry in the manifest.  A new-style run (normalization forces
    ``max_review_rounds`` to 0) therefore still fails loudly on a bad
    ``final_verdict`` when the writeup gate is engaged.

    Returns a list of human-readable failure messages (empty = pass).
    """
    config = project.get("config", {})
    synthesis = config.get("synthesis", {})
    max_rounds = synthesis.get("max_review_rounds", 0)

    failures: list[str] = []

    if max_rounds > 0:
        review_rounds = project.get("review_rounds")
        if review_rounds is None:
            failures.append(
                "    FAIL  synthesis.max_review_rounds > 0 but 'review_rounds' "
                "is missing from project.json (expected >= 1)"
            )
        elif not isinstance(review_rounds, (int, float)) or review_rounds < 1:
            failures.append(
                f"    FAIL  synthesis.max_review_rounds > 0 but 'review_rounds' "
                f"is {review_rounds} (must be >= 1)"
            )

    if _writeup_gate_engaged(project):
        final_verdict = project.get("final_verdict")
        if not final_verdict:
            failures.append(
                "    FAIL  A writeup gate is engaged but 'final_verdict' "
                "is missing from project.json (expected 'APPROVE' or 'REJECT')"
            )
        elif final_verdict not in ("APPROVE", "REJECT"):
            failures.append(
                f"    FAIL  'final_verdict' is '{final_verdict}' "
                f"but must be 'APPROVE' or 'REJECT'"
            )

    return failures


def check_paper_writing_subagent(project: dict) -> list:
    """**Check 3** -- If a paper-writing issue exists,
    ``paper_writing_subagent_id`` must be persisted in ``project.json``.

    Returns a list of human-readable failure messages (empty = pass).
    """
    issues = project.get("issues", [])
    has_paper_writing = any(
        i.get("issue_type") == "paper-writing" for i in issues
    )

    if not has_paper_writing:
        return []

    failures: list[str] = []

    subagent_id = project.get("paper_writing_subagent_id")
    if not subagent_id:
        failures.append(
            "    FAIL  Paper-writing issue exists but "
            "'paper_writing_subagent_id' is missing or empty in project.json"
        )

    return failures


def check_workspace_and_deliverable(project: dict) -> list:
    """**Check 4** -- The project workspace directory exists and contains the
    deliverable file.

    Uses ``project_workspace`` (if present) to verify the directory, and
    ``deliverable_path`` to verify the file.  When ``project_workspace`` is
    missing the parent directory of ``deliverable_path`` is used as a
    fallback so the check remains meaningful.

    Returns a list of human-readable failure messages (empty = pass).
    """
    failures: list[str] = []

    # --- workspace directory ---
    workspace = project.get("project_workspace")
    deliverable_path = project.get("deliverable_path")

    if workspace:
        if not os.path.isdir(workspace):
            failures.append(
                f"    FAIL  Project workspace directory does not exist: "
                f"{workspace}"
            )
    else:
        # Fallback: derive from deliverable_path
        if deliverable_path:
            workspace = os.path.dirname(deliverable_path)
            if not os.path.isdir(workspace):
                failures.append(
                    f"    FAIL  deliverable_path's parent directory does "
                    f"not exist: {workspace} (project_workspace was not set "
                    f"in project.json)"
                )
        else:
            failures.append(
                "    FAIL  Neither 'project_workspace' nor 'deliverable_path' "
                "is set in project.json -- cannot verify workspace"
            )

    # --- deliverable file ---
    if deliverable_path:
        if not os.path.isfile(deliverable_path):
            failures.append(
                f"    FAIL  Deliverable file does not exist: "
                f"{deliverable_path}"
            )
    else:
        failures.append(
            "    FAIL  'deliverable_path' is missing from project.json"
        )

    return failures


def check_terminal_status(project: dict) -> list:
    """**Check 5** -- All *research* issues have a terminal status.

    Terminal statuses under the dynamic just-in-time lifecycle are
    ``resolved``, ``blocked``, ``closed``, and ``superseded`` (superseded
    issues stay terminal as history; they are never reopened).  Legacy
    manifests use ``resolved``/``blocked``, which remain valid.

    The control issue (``control: true``) is excluded since it is never
    dispatched.

    Returns a list of human-readable failure messages (empty = pass).
    """
    issues = project.get("issues", [])
    failures: list[str] = []
    terminal = ("resolved", "blocked", "closed", "superseded")

    for issue in issues:
        if issue.get("control"):
            continue
        iid = issue.get("issue_id", "<unknown>")
        status = issue.get("status")
        if status not in terminal:
            failures.append(
                f"    FAIL  Issue '{iid}' has status '{status}' -- "
                f"expected a terminal status: resolved, blocked, closed, "
                f"or superseded"
            )

    return failures


def check_control_issue_entry(project: dict) -> list:
    """**Check 6** -- The control issue entry exists in ``project.json``.

    Verifies that there is an issue in the ``issues`` array with
    ``control: true`` and that its ``issue_id`` matches
    ``control_issue_id``.

    Returns a list of human-readable failure messages (empty = pass).
    """
    issues = project.get("issues", [])
    control_issue_id = project.get("control_issue_id")
    failures: list[str] = []

    if not control_issue_id:
        failures.append(
            "    FAIL  'control_issue_id' is missing from project.json"
        )
        return failures

    found = any(
        i.get("control") and i.get("issue_id") == control_issue_id
        for i in issues
    )

    if not found:
        any_control = any(i.get("control") for i in issues)
        if any_control:
            failures.append(
                f"    FAIL  No control issue with issue_id "
                f"'{control_issue_id}' found in issues array "
                f"(other control issues exist but ids do not match)"
            )
        else:
            failures.append(
                f"    FAIL  No control issue entry (control: true) found "
                f"in issues array -- expected one with "
                f"issue_id = '{control_issue_id}'"
            )

    return failures


def check_simulation_disclosure(project: dict, workspace_root: str | None = None) -> list:
    """**Check 7** -- Simulation disclosure in the deliverable.

    When the project workspace contains simulated/dry-run mode artifacts, the
    deliverable's abstract (opening) region must carry a simulation marker
    within its first 60 lines.  The marker check targets the abstract/opening
    region rather than the whole 60-line window so that a single buried body
    note (e.g. a "dry-run mode" remark at line ~59) does not satisfy the
    disclosure requirement: headline claims live in the abstract, so the
    disclosure must live there too.

    Subject determination:
      * any JSON file under the workspace that parses and has a ``"mode"``
        value (stringified) containing "dry" or "simul" (case-insensitive), OR
      * any file under a path segment named ``simulated`` / ``dry-run``.

    When subject: the deliverable file's first 60 lines must contain,
    case-insensitively, at least one of: "simulated", "dry-run",
    "[simulated]", "[ESTIMATE".  If the deliverable file is missing entirely
    the check reports the missing-file failure (like other checks) rather
    than skipping.  If no simulated-mode artifact is found, the check passes
    silently (skip).

    ``workspace_root`` overrides the workspace used for the scan (used by the
    protocol validator tests); default is ``project["project_workspace"]``,
    falling back to the directory of ``deliverable_path``.

    Returns a list of human-readable failure messages (empty = pass).
    """
    failures: list[str] = []

    if workspace_root is None:
        workspace_root = project.get("project_workspace")
        if not workspace_root:
            deliverable_path = project.get("deliverable_path")
            if deliverable_path:
                workspace_root = os.path.dirname(deliverable_path)

    if not workspace_root or not os.path.isdir(workspace_root):
        # Nothing scannable -> no simulated-mode artifact found -> skip.
        return []

    # --- subject determination ---------------------------------------------
    subject = False
    root_lower = os.path.basename(workspace_root).lower()
    for dirpath, _dirnames, filenames in os.walk(workspace_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, workspace_root)
            parts = rel.split(os.sep)
            if root_lower in ("simulated", "dry-run") or any(
                p.lower() in ("simulated", "dry-run") for p in parts
            ):
                subject = True
                break
            if name.lower().endswith(".json"):
                try:
                    with open(full, "r", errors="replace") as fh:
                        data = json.load(fh)
                except (ValueError, OSError):
                    continue
                if isinstance(data, dict) and "mode" in data:
                    mode = str(data["mode"]).lower()
                    if "dry" in mode or "simul" in mode:
                        subject = True
                        break
        if subject:
            break

    if not subject:
        return []  # no simulated-mode artifact -> pass silently

    # --- deliverable file presence -----------------------------------------
    deliverable_path = project.get("deliverable_path")
    if not deliverable_path:
        failures.append(
            "    FAIL  Simulated/dry-run mode artifacts exist in the project "
            "workspace but 'deliverable_path' is missing from project.json -- "
            "cannot verify simulation disclosure in the deliverable"
        )
        return failures
    if not os.path.isfile(deliverable_path):
        failures.append(
            f"    FAIL  Deliverable file does not exist: {deliverable_path} "
            f"(simulated/dry-run mode artifacts present in the project "
            f"workspace -- disclosure cannot be verified)"
        )
        return failures

    # --- first-60-lines window ---------------------------------------------
    head_lines: list[str] = []
    try:
        with open(deliverable_path, "r", errors="replace") as fh:
            for _i, line in enumerate(fh):
                if _i >= 60:
                    break
                head_lines.append(line)
    except OSError as exc:
        failures.append(
            f"    FAIL  Cannot read deliverable file: {deliverable_path} "
            f"({exc})"
        )
        return failures

    markers = ("simulated", "dry-run", "[simulated]", "[estimate")

    # --- abstract / opening region within the window -----------------------
    # If a heading whose text contains "abstract" appears in the window, the
    # disclosure region runs from that heading to the next heading (or the
    # end of the window).  Otherwise the region is the opening block before
    # the first heading; if there is no heading at all, it is the whole
    # window.  A marker buried in a later body section does not count.
    region_lines: list[str] = head_lines
    first_heading_idx = None
    abstract_idx = None
    for i, line in enumerate(head_lines):
        if line.lstrip().startswith("#"):
            if first_heading_idx is None:
                first_heading_idx = i
            if "abstract" in line.lower():
                abstract_idx = i
                break
    if abstract_idx is not None:
        end = len(head_lines)
        for i in range(abstract_idx + 1, len(head_lines)):
            if head_lines[i].lstrip().startswith("#"):
                end = i
                break
        region_lines = head_lines[abstract_idx:end]
    elif first_heading_idx is not None:
        region_lines = head_lines[:first_heading_idx]

    region_text = "".join(region_lines).lower()
    if not any(m in region_text for m in markers):
        failures.append(
            f"    FAIL  Deliverable abstract/opening region omits a "
            f"simulation marker: {deliverable_path} (simulated/dry-run mode "
            f"artifacts exist in the project workspace; the abstract and "
            f"every results table/prose cell must carry a marker such as "
            f"'simulated', 'dry-run', '[simulated]', or '[ESTIMATE' within "
            f"the deliverable's first 60 lines)"
        )

    return failures


# ---------------------------------------------------------------------------
# Individual checks (8-11 dynamic-lifecycle / communication contracts)
# ---------------------------------------------------------------------------


def check_directive_trail_parity(project: dict, epics_root: str | None = None) -> list:
    """**Check 8** -- Directive-trail parity.

    The source of truth is the append-only ``project.json["interventions"]``
    ledger (entries ``{ts, issue_id, directive_digest}``).  Every ledger
    entry must have a matching directive-mirror comment on the affected
    issue -- ``[directive: <digest>]`` or ``[human-directive: <digest>]``
    with a case-insensitive digest match (the documented spellings from the
    Communication Logging Contract).  The reverse direction also holds:
    every directive/human-directive comment must have a matching ledger
    entry (dual-write parity).

    The comment scan keys off the documented marker vocabulary (directive,
    proposal-v<n>, review-critique, manager-notice, block-linked,
    seeded-fail-feedback, seeding); a ledger entry whose affected issue
    carries no comment with any documented marker is additionally reported
    as an untrailed issue.

    Missing optional sections (no interventions ledger, no issue_path, no
    epics root, missing comments directory) fail LOUDLY, never silently
    skip.  Returns a list of human-readable failure messages (empty = pass).
    """
    failures: list[str] = []

    interventions = project.get("interventions")
    if interventions is None:
        failures.append(
            "    FAIL  Check 8: 'interventions' ledger is missing from "
            "project.json (it is the source of truth for epic-manager "
            "directives)"
        )
        return failures
    if not isinstance(interventions, list):
        failures.append(
            "    FAIL  Check 8: 'interventions' is not a list -- expected "
            "the append-only ledger of {ts, issue_id, directive_digest} "
            "entries"
        )
        return failures

    issue_map = _issue_map(project)
    comment_digests = {}   # issue_id -> set of digests seen in directive comments
    untrailed = {}         # issue_id -> True when no documented-marker comment

    for issue in _issue_entries(project):
        if issue.get("control"):
            continue  # the control issue is never a directive surface
        iid = issue.get("issue_id")
        comments, err = _issue_comments(project, epics_root, issue)
        if err is not None:
            failures.append("    FAIL  Check 8: %s" % err)
            continue
        digests = set()
        has_marker = False
        for text in comments:
            lower = text.lower()
            if any(m in lower for m in _DOCUMENTED_MARKERS):
                has_marker = True
            for m in _DIRECTIVE_RE.finditer(text):
                digests.add(m.group(1).strip().lower())
        if digests:
            comment_digests[iid] = digests
        if iid is not None and not has_marker:
            untrailed[iid] = True

    for entry in interventions:
        if not isinstance(entry, dict):
            failures.append(
                "    FAIL  Check 8: interventions entry is not a dict: %r"
                % (entry,))
            continue
        iid = entry.get("issue_id")
        digest = entry.get("directive_digest")
        if not isinstance(iid, str) or not iid.strip():
            failures.append(
                "    FAIL  Check 8: interventions entry missing a valid "
                "'issue_id': %r" % (entry,))
            continue
        if not isinstance(digest, str) or not digest.strip():
            failures.append(
                "    FAIL  Check 8: interventions entry for issue %r is "
                "missing a valid 'directive_digest': %r" % (iid, entry))
            continue
        if iid not in issue_map:
            failures.append(
                "    FAIL  Check 8: ledger entry references unknown issue %r"
                % iid)
            continue
        issue = issue_map[iid]
        comments, err = _issue_comments(project, epics_root, issue)
        if err is not None:
            failures.append("    FAIL  Check 8: %s" % err)
            continue
        matched = any(
            m.group(1).strip().lower() == digest.strip().lower()
            for text in comments
            for m in _DIRECTIVE_RE.finditer(text))
        if not matched:
            failures.append(
                "    FAIL  Check 8: interventions entry for issue %r "
                "(directive_digest %r) has no matching [directive: %s] or "
                "[human-directive: %s] comment on that issue "
                "(directive-trail parity)" % (iid, digest, digest, digest))
            if untrailed.get(iid):
                failures.append(
                    "    FAIL  Check 8: affected issue %r carries no comment "
                    "with any documented marker (directive, proposal-v<n>, "
                    "review-critique, manager-notice, block-linked, "
                    "seeded-fail-feedback, seeding) -- untrailed thread" % iid)

    # Reverse direction: every directive comment digest needs a ledger entry.
    for iid, digests in comment_digests.items():
        for digest in digests:
            matched_entry = any(
                isinstance(e, dict)
                and e.get("issue_id") == iid
                and isinstance(e.get("directive_digest"), str)
                and e["directive_digest"].strip().lower() == digest
                for e in interventions)
            if not matched_entry:
                failures.append(
                    "    FAIL  Check 8: [directive] comment on issue %r "
                    "(digest %r) has no matching interventions ledger entry "
                    "(dual-write parity)" % (iid, digest))

    return failures


def check_thread_liveness(project: dict, epics_root: str | None = None) -> list:
    """**Check 9** -- Thread liveness.

    Every non-control issue has at least one comment in its ``comments/``
    directory (seeding comments count toward liveness).  Missing optional
    sections (no issue_path, no epics root, missing comments directory)
    fail LOUDLY.  Returns a list of human-readable failure messages
    (empty = pass).
    """
    failures: list[str] = []

    for issue in _issue_entries(project):
        if issue.get("control"):
            continue
        iid = issue.get("issue_id", "<unknown>")
        comments, err = _issue_comments(project, epics_root, issue)
        if err is not None:
            failures.append("    FAIL  Check 9: %s" % err)
            continue
        if not comments:
            failures.append(
                "    FAIL  Check 9: non-control issue %r has no comments "
                "(thread liveness requires >= 1 comment; seeding comments "
                "count)" % iid)

    return failures


def _manager_generated(entry: dict) -> bool:
    """True for manager-generated verdict entries (exempt from reviewer-
    comment parity): ``fallback: true``, the disabled round-0 writeup
    placeholder (``round == 0``), and loop-limit synthetics
    (``routing == "blocked"``, a manager-only route)."""
    return (entry.get("fallback") is True
            or entry.get("round") == 0
            or entry.get("routing") == "blocked")


def check_reviewer_comment_parity(project: dict, epics_root: str | None = None) -> list:
    """**Check 10** -- Reviewer-comment parity.

    Every ``review_state.verdict_history`` entry maps to at least one
    ``[review-critique: <gate>-r<round>]`` comment on the stage anchor issue
    of the gate's stage (``review_engine.stage_for_gate``: ideation ->
    hypothesis, writeup -> paper_writeup).

    Manager-generated entries (``fallback: true``, disabled round-0 writeup
    placeholder, loop-limit synthetics with ``routing`` \"blocked\") are
    EXEMPT from the critique requirement but must have at least one
    ``[manager-notice]`` comment on the anchor issue.

    A missing ``review_state.verdict_history`` fails LOUDLY (named check,
    never a silent skip).  Returns a list of human-readable failure messages
    (empty = pass).
    """
    failures: list[str] = []

    review_state = project.get("review_state")
    if not isinstance(review_state, dict):
        review_state = {}
    verdict_history = review_state.get("verdict_history")
    if verdict_history is None:
        failures.append(
            "    FAIL  Check 10: 'review_state.verdict_history' is missing "
            "from project.json -- reviewer-comment parity cannot be "
            "verified"
        )
        return failures
    if not isinstance(verdict_history, list):
        failures.append(
            "    FAIL  Check 10: 'review_state.verdict_history' is not a "
            "list"
        )
        return failures

    for entry in verdict_history:
        if not isinstance(entry, dict):
            failures.append(
                "    FAIL  Check 10: verdict_history entry is not a dict: %r"
                % (entry,))
            continue
        gate = entry.get("gate")
        round_no = entry.get("round")
        if not isinstance(gate, str) or not gate.strip():
            failures.append(
                "    FAIL  Check 10: verdict_history entry missing a valid "
                "'gate': %r" % (entry,))
            continue
        manager_generated = _manager_generated(entry)
        if not manager_generated:
            if not isinstance(round_no, int) or isinstance(round_no, bool) or round_no < 1:
                failures.append(
                    "    FAIL  Check 10: verdict_history entry for gate %r "
                    "has an invalid 'round' (%r); round must be an int >= 1 "
                    "for reviewer-derived entries" % (gate, round_no))
                continue

        stage = stage_for_gate(gate)
        anchor = _anchor_issue_id(project, stage)
        if not anchor:
            failures.append(
                "    FAIL  Check 10: no anchor issue found for stage %r "
                "(gate %r) -- cannot verify critique parity" % (stage, gate))
            continue
        issue = _issue_map(project).get(anchor)
        if not isinstance(issue, dict):
            failures.append(
                "    FAIL  Check 10: anchor issue %r for stage %r is not "
                "present in issues[]" % (anchor, stage))
            continue
        comments, err = _issue_comments(project, epics_root, issue)
        if err is not None:
            failures.append("    FAIL  Check 10: %s" % err)
            continue

        if manager_generated:
            if not any("[manager-notice" in text.lower() for text in comments):
                failures.append(
                    "    FAIL  Check 10: manager-generated verdict entry "
                    "(%s gate, round %s) has no [manager-notice] comment on "
                    "anchor issue %r (exemption requires a notice)"
                    % (gate, round_no, anchor))
        else:
            marker = "[review-critique: %s-r%d]" % (gate, round_no)
            if not any(marker.lower() in text.lower() for text in comments):
                failures.append(
                    "    FAIL  Check 10: verdict entry (%s gate, round %d) "
                    "has no [review-critique: %s-r%d] comment on anchor "
                    "issue %r (reviewer-comment parity)"
                    % (gate, round_no, gate, round_no, anchor))

    return failures


def check_ideation_evidence(project: dict, epics_root: str | None = None) -> list:
    """**Check 11** -- Ideation evidence.

    Active ONLY when ``config.ideation.max_rounds > 0``: the hypothesis
    stage must exist, and its thread must show >= 2 ``[proposal-v<n>]``
    comments OR a recorded stop condition (``results["ideation"]
    ["stop_condition"]`` in pass/cap/plateau).

    When ideation is absent/disabled (max_rounds <= 0 or no ideation block),
    the manifest must record the stop condition ``"ideation_disabled"`` in
    ``results["ideation"]`` whenever a hypothesis stage exists; only a
    manifest with NO hypothesis stage at all (linear passthrough, run B
    style) is accepted without the record.

    Missing required sections fail LOUDLY (named check, never a silent
    skip).  Returns a list of human-readable failure messages (empty =
    pass).
    """
    failures: list[str] = []

    config = project.get("config")
    if not isinstance(config, dict):
        config = {}
    ideation = config.get("ideation")
    max_rounds = 0
    if isinstance(ideation, dict):
        mr = ideation.get("max_rounds")
        if isinstance(mr, int) and not isinstance(mr, bool):
            max_rounds = mr

    results = project.get("results")
    ideation_result = results.get("ideation") if isinstance(results, dict) else None
    stop = None
    if isinstance(ideation_result, dict):
        stop = ideation_result.get("stop_condition")
    elif isinstance(ideation_result, str) and ideation_result.strip():
        stop = ideation_result

    hypothesis_ids = _stage_issue_ids(project, "hypothesis")

    if max_rounds > 0:
        # --- ideation active: evidence required ---------------------------
        if not hypothesis_ids:
            failures.append(
                "    FAIL  Check 11: ideation is active "
                "(ideation.max_rounds=%d) but the manifest has no "
                "hypothesis-stage issues" % max_rounds)
            return failures
        if stop in ("pass", "cap", "plateau"):
            return failures  # recorded stop condition satisfies the check
        proposal_count = 0
        for iid in hypothesis_ids:
            issue = _issue_map(project).get(iid)
            if not isinstance(issue, dict):
                failures.append(
                    "    FAIL  Check 11: hypothesis issue %r is not present "
                    "in issues[]" % iid)
                continue
            comments, err = _issue_comments(project, epics_root, issue)
            if err is not None:
                failures.append("    FAIL  Check 11: %s" % err)
                continue
            proposal_count += sum(
                1 for text in comments if _PROPOSAL_RE.search(text))
        if proposal_count < 2:
            failures.append(
                "    FAIL  Check 11: ideation is active (max_rounds=%d) but "
                "the hypothesis thread shows %d [proposal-v<n>] comment(s) "
                "and no recorded stop condition -- need >= 2 proposal "
                "revision comments or a stop record" % (max_rounds, proposal_count))
        return failures

    # --- ideation disabled / absent ----------------------------------------
    if stop == "ideation_disabled":
        return failures
    if not hypothesis_ids:
        return failures  # no hypothesis stage at all (linear passthrough)
    failures.append(
        "    FAIL  Check 11: ideation is disabled/absent "
        "(ideation.max_rounds=%d) with a hypothesis stage in the manifest, "
        "but results['ideation']['stop_condition'] is not "
        "'ideation_disabled'" % max_rounds)
    return failures


# ---------------------------------------------------------------------------
# Battery runner
# ---------------------------------------------------------------------------

CHECKS = [
    (
        "Check 1: Every resolved issue has a cost field "
        "with non-zero tokens",
        check_resolved_issues_have_cost,
    ),
    (
        "Check 2: Review evidence + external final_verdict contract "
        "(engaged when a writeup gate is active)",
        check_review_evidence,
    ),
    (
        "Check 3: Paper-writing subagent_id persisted "
        "(if paper-writing issue exists)",
        check_paper_writing_subagent,
    ),
    (
        "Check 4: Project workspace directory exists "
        "and contains the deliverable",
        check_workspace_and_deliverable,
    ),
    (
        "Check 5: All research issues have a terminal status "
        "(resolved, blocked, closed, superseded)",
        check_terminal_status,
    ),
    (
        "Check 6: Control issue entry exists",
        check_control_issue_entry,
    ),
    (
        "Check 7: Simulation disclosure in deliverable "
        "(marker present when simulated/dry-run mode artifacts exist)",
        check_simulation_disclosure,
    ),
    (
        "Check 8: Directive-trail parity (interventions ledger entry "
        "<-> [directive: <digest>] comment on the affected issue)",
        check_directive_trail_parity,
    ),
    (
        "Check 9: Thread liveness (every non-control issue has >= 1 "
        "comment; seeding comments count)",
        check_thread_liveness,
    ),
    (
        "Check 10: Reviewer-comment parity (verdict_history <-> "
        "[review-critique: <gate>-r<round>]; manager-generated entries -> "
        "[manager-notice])",
        check_reviewer_comment_parity,
    ),
    (
        "Check 11: Ideation evidence (active when ideation.max_rounds > 0; "
        ">= 2 [proposal-v<n>] comments or a recorded stop condition; "
        "disabled -> 'ideation_disabled' when a hypothesis stage exists)",
        check_ideation_evidence,
    ),
]

_COMMENT_CHECKS = frozenset({
    check_directive_trail_parity,
    check_thread_liveness,
    check_reviewer_comment_parity,
    check_ideation_evidence,
})


def run_battery(project: dict, epics_root: str | None = None) -> list:
    """Run every check against *project*.

    Returns a list of ``(title, failures, ok)`` tuples; *epics_root* is the
    epic directory that ``issue_path`` values resolve against (required by
    Checks 8-11; the CLI passes the directory of the project.json path).
    """
    results = []
    for title, fn in CHECKS:
        try:
            if fn in _COMMENT_CHECKS:
                failures = fn(project, epics_root)
            else:
                failures = fn(project)
        except Exception as exc:  # noqa: BLE001 -- report, never crash
            failures = [
                "    FAIL  %s raised an unexpected exception: %s"
                % (title, exc)]
        if not isinstance(failures, list):
            failures = ["    FAIL  %s returned a malformed result" % title]
        results.append((title, failures, not failures))
    return results


# ---------------------------------------------------------------------------
# Self-test (inline synthetic fixtures; stdlib only)
# ---------------------------------------------------------------------------


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def _build_workspace(workspace: str) -> None:
    """Shared project workspace: a simulated-mode artifact plus a deliverable
    whose abstract carries a simulation marker (satisfies Check 7)."""
    _write(os.path.join(workspace, "archive", "results_summary.json"),
           json.dumps({"mode": "dry-run simulated"}))
    _write(os.path.join(workspace, "deliverable.md"),
           "# Demo\n\n## 1. Abstract\n\n[simulated] All headline numbers "
           "are dry-run stub estimates.\n\n## 2. Introduction\n\nBody text.\n")


def _comment(epics_root: str, issue_id: str, name: str, text: str) -> None:
    _write(os.path.join(epics_root, "issues", issue_id, "comments", name),
           text)


def _issue_entry(issue_id: str, title: str, stage: str, control: bool = False,
                 anchor: bool = False) -> dict:
    entry = {
        "issue_id": issue_id,
        "title": title,
        "stage": stage,
        "control": control,
        "anchor": anchor,
        "status": "resolved" if not control else "open",
        "issue_path": "issues/%s/ISSUE.md" % issue_id,
    }
    if control:
        entry["status"] = "open"
    return entry


def _build_new_style_tree(epics_root: str) -> None:
    """Write the on-disk issue tree (comments) for the new-style fixture."""
    _comment(epics_root, "literature-review-anchor-r1", "c-01-seeding.md",
             "[seeding] Literature review anchor opened with the stage goal, "
             "inputs, and acceptance criteria.")
    # hypothesis ideation anchor: revision-history thread
    _comment(epics_root, "hypothesis-ideation-r1", "c-01-seeding.md",
             "[seeding] Hypothesis ideation anchor opened; ideation loop "
             "follows (generate -> multi-criteria review -> revise).")
    _comment(epics_root, "hypothesis-ideation-r1", "c-02-proposal-v1.md",
             "[proposal-v1] Problem/Method/Experiment-design triple v1 "
             "posted to the thread.")
    _comment(epics_root, "hypothesis-ideation-r1", "c-03-critique-ideation-r1.md",
             "[review-critique: ideation-r1] Clarity 4 (meets the bar); "
             "Relevance 4 (meets the bar); Originality 3 (below the bar): "
             "sharpen the novelty claim.")
    _comment(epics_root, "hypothesis-ideation-r1", "c-04-critique-hypothesis-r1.md",
             "[review-critique: hypothesis-r1] Significance 4 (meets the "
             "bar) -- well-scoped; Originality 4 (meets the bar) -- novel "
             "angle.")
    _comment(epics_root, "hypothesis-ideation-r1", "c-05-proposal-v2.md",
             "[proposal-v2] Triple v2 posted with the revisions merged from "
             "the round-1 critiques.")
    _comment(epics_root, "experiment-planning-anchor-r1", "c-01-seeding.md",
             "[seeding] Experiment planning anchor opened with the final "
             "proposal as input.")
    _comment(epics_root, "experiment-execution-arm-a-r1", "c-01-seeding.md",
             "[seeding] Execution arm-a opened (parallel split).")
    _comment(epics_root, "experiment-execution-arm-b-r1", "c-01-seeding.md",
             "[seeding] Execution arm-b opened (parallel split).")
    _comment(epics_root, "experiment-execution-arm-b-r1", "c-02-directive-d7b2c.md",
             "[directive: d-7b2c] Epic manager directive: add the arm-b "
             "ablation before proceeding; recorded before acting.")
    _comment(epics_root, "analysis-anchor-r1", "c-01-seeding.md",
             "[seeding] Analysis anchor opened with the execution outputs.")
    _comment(epics_root, "analysis-anchor-r1", "c-02-critique-analysis-r1.md",
             "[review-critique: analysis-r1] Quality 4 (meets the bar); "
             "Significance 4 (meets the bar); Originality 4 (meets the bar).")
    _comment(epics_root, "paper-writeup-anchor-r1", "c-01-seeding.md",
             "[seeding] Paper writeup anchor opened with the synthesis "
             "inputs.")
    _comment(epics_root, "paper-writeup-anchor-r1", "c-02-manager-notice.md",
             "[manager-notice] Writeup Clarity gate disabled; no review was "
             "performed (disabled round-0 placeholder recorded).")


def _new_style_manifest(workspace: str, with_ideation_stop: bool) -> dict:
    """New-style manifest JSON for the synthetic passing fixture."""
    issues = [
        _issue_entry("my-epic-orchestration-log", "Orchestration Log",
                     "paper_writeup", control=True),
        _issue_entry("literature-review-anchor-r1", "Literature Review",
                     "literature_review", anchor=True),
        _issue_entry("hypothesis-ideation-r1", "Hypothesis Ideation",
                     "hypothesis", anchor=True),
        _issue_entry("experiment-planning-anchor-r1", "Experiment Planning",
                     "experiment_planning", anchor=True),
        _issue_entry("experiment-execution-arm-a-r1", "Execution Arm A",
                     "experiment_execution"),
        _issue_entry("experiment-execution-arm-b-r1", "Execution Arm B",
                     "experiment_execution"),
        _issue_entry("analysis-anchor-r1", "Analysis",
                     "analysis", anchor=True),
        _issue_entry("paper-writeup-anchor-r1", "Paper Writeup",
                     "paper_writeup", anchor=True),
    ]
    results = {}
    for issue in issues:
        if issue.get("control"):
            continue
        results[issue["issue_id"]] = {
            "status": "resolved",
            "cost": {"input_tokens": 1000, "output_tokens": 500,
                     "cache_read_tokens": 100},
        }
    if with_ideation_stop:
        results["ideation"] = {
            "stop_condition": "pass",
            "rounds": 2,
            "flagged": False,
            "aggregate_scores": {"Clarity": 4, "Relevance": 4,
                                 "Originality": 4, "Feasibility": 4,
                                 "Significance": 4},
        }
    return {
        "project": "Synthetic Passing Project",
        "epic": "synthetic-passing-epic",
        "status": "completed",
        "project_workspace": workspace,
        "control_issue_id": "my-epic-orchestration-log",
        "planning": {"dynamic_issues": True},
        "config": {
            "dispatch": {"max_concurrent": 2, "max_retries": 2},
            "review": {"max_hypothesis_review_loops": 1,
                       "max_experiment_review_loops": 1,
                       "max_writeup_review_loops": 0,
                       "max_total_project_loops": 10,
                       "_writeup_loop_present": True},
            "synthesis": {"max_review_rounds": 0},
            "ideation": {"max_rounds": 2, "reviewers": 2,
                         "on_exhaust": "proceed"},
        },
        "issues": issues,
        "dependencies": {
            "literature-review-anchor-r1": [],
            "hypothesis-ideation-r1": ["literature-review-anchor-r1"],
            "experiment-planning-anchor-r1": ["hypothesis-ideation-r1"],
            "experiment-execution-arm-a-r1": ["experiment-planning-anchor-r1"],
            "experiment-execution-arm-b-r1": ["experiment-planning-anchor-r1"],
            "analysis-anchor-r1": ["experiment-execution-arm-a-r1",
                                   "experiment-execution-arm-b-r1"],
            "paper-writeup-anchor-r1": ["analysis-anchor-r1"],
        },
        "stage_issues": {
            "literature_review": ["literature-review-anchor-r1"],
            "hypothesis": ["hypothesis-ideation-r1"],
            "experiment_planning": ["experiment-planning-anchor-r1"],
            "experiment_execution": ["experiment-execution-arm-a-r1",
                                     "experiment-execution-arm-b-r1"],
            "analysis": ["analysis-anchor-r1"],
            "paper_writeup": ["paper-writeup-anchor-r1"],
        },
        "artifacts": {
            "literature_review": ["docs/literature-review/review.md"],
            "hypothesis": ["ideas/proposal-final.json"],
            "experiment_planning": ["docs/experiment-planning/plan.md"],
            "experiment_execution": ["docs/experiment-execution/results.md"],
            "analysis": ["docs/analysis/findings.md"],
            "paper_writeup": ["docs/paper-writeup/deliverable.md"],
        },
        "interventions": [
            {"ts": "2026-08-22T0300Z",
             "issue_id": "experiment-execution-arm-b-r1",
             "directive_digest": "d-7b2c"},
        ],
        "review_state": {
            "loop_counters": {"hypothesis_gate": 1, "analysis_gate": 1,
                              "writeup_gate": 0, "total_project_loops": 2},
            "verdict_history": [
                {"gate": "hypothesis", "round": 1, "verdict": "PASS",
                 "criteria_scores": {
                     "Significance": {"score": 4, "justification": "well-scoped"},
                     "Originality": {"score": 4, "justification": "novel"}},
                 "failing_criteria": [],
                 "revision_feedback": "Tighten the novelty claim wording.",
                 "routing": "experiment_execution"},
                {"gate": "analysis", "round": 1, "verdict": "PASS",
                 "criteria_scores": {
                     "Quality": {"score": 4, "justification": "sound"},
                     "Significance": {"score": 4, "justification": "material"},
                     "Originality": {"score": 4, "justification": "novel"}},
                 "failing_criteria": [],
                 "revision_feedback": "Add a robustness paragraph.",
                 "routing": "paper_writeup"},
                {"gate": "writeup", "round": 0, "verdict": "PASS",
                 "criteria_scores": {
                     "Clarity": {"score": 3, "justification":
                                 "disabled gate placeholder"}},
                 "failing_criteria": [],
                 "revision_feedback": "Gate disabled; no review performed.",
                 "routing": "complete"},
            ],
            "current_gate": None,
            "current_route": None,
            "blocked_reason": None,
        },
        "results": results,
        "paper_writing_subagent_id": None,
        "deliverable_path": os.path.join(workspace, "deliverable.md"),
        "review_rounds": 1,
        "final_verdict": "APPROVE",
    }


def _mutate_disk(epics_root: str) -> None:
    """Delete the comment files that the mutated fixture violates."""
    os.remove(os.path.join(epics_root, "issues",
                           "experiment-execution-arm-a-r1", "comments",
                           "c-01-seeding.md"))                      # Check 9
    os.remove(os.path.join(epics_root, "issues",
                           "analysis-anchor-r1", "comments",
                           "c-02-critique-analysis-r1.md"))          # Check 10
    os.remove(os.path.join(epics_root, "issues",
                           "experiment-execution-arm-b-r1", "comments",
                           "c-02-directive-d7b2c.md"))               # Check 8
    os.remove(os.path.join(epics_root, "issues",
                           "hypothesis-ideation-r1", "comments",
                           "c-02-proposal-v1.md"))                   # Check 11
    os.remove(os.path.join(epics_root, "issues",
                           "hypothesis-ideation-r1", "comments",
                           "c-05-proposal-v2.md"))                   # Check 11


def _legacy_manifest(workspace: str) -> dict:
    """Legacy-style manifest (stage_to_issue_id + ideation disabled) for the
    auto-detection fixture."""
    issues = [
        _issue_entry("my-epic-orchestration-log", "Orchestration Log",
                     "paper_writeup", control=True),
        _issue_entry("lr", "Literature Review", "literature_review"),
        _issue_entry("h", "Hypothesis", "hypothesis"),
        _issue_entry("ep", "Experiment Planning", "experiment_planning"),
        _issue_entry("ee", "Experiment Execution", "experiment_execution"),
        _issue_entry("a", "Analysis", "analysis"),
        _issue_entry("w", "Paper Writeup", "paper_writeup"),
    ]
    results = {}
    for issue in issues:
        if issue.get("control"):
            continue
        results[issue["issue_id"]] = {
            "status": "resolved",
            "cost": {"input_tokens": 800, "output_tokens": 400,
                     "cache_read_tokens": 50},
        }
    results["ideation"] = {"stop_condition": "ideation_disabled"}
    return {
        "project": "Synthetic Legacy Project",
        "epic": "synthetic-legacy-epic",
        "status": "completed",
        "project_workspace": workspace,
        "control_issue_id": "my-epic-orchestration-log",
        "planning": {"num_issues": 6},   # legacy marker (tolerated)
        "config": {
            "dispatch": {"max_concurrent": 2, "max_retries": 2},
            "synthesis": {"max_review_rounds": 0},
        },
        "issues": issues,
        "dependencies": {"lr": [], "h": ["lr"], "ep": ["h"], "ee": ["ep"],
                         "a": ["ee"], "w": ["a"]},
        "stage_to_issue_id": {
            "literature_review": "lr",
            "hypothesis": "h",
            "experiment_planning": "ep",
            "experiment_execution": "ee",
            "analysis": "a",
            "paper_writeup": "w",
        },
        "interventions": [
            {"ts": "2026-08-21T1200Z", "issue_id": "a",
             "directive_digest": "d-l1"},
        ],
        "review_state": {
            "loop_counters": {"hypothesis_gate": 1, "analysis_gate": 1,
                              "writeup_gate": 0, "total_project_loops": 2},
            "verdict_history": [
                {"gate": "hypothesis", "round": 1, "verdict": "PASS",
                 "criteria_scores": {
                     "Significance": {"score": 4, "justification": "ok"},
                     "Originality": {"score": 4, "justification": "ok"}},
                 "failing_criteria": [],
                 "revision_feedback": "Minor wording note.",
                 "routing": "experiment_execution"},
                {"gate": "analysis", "round": 1, "verdict": "PASS",
                 "criteria_scores": {
                     "Quality": {"score": 4, "justification": "ok"},
                     "Significance": {"score": 4, "justification": "ok"},
                     "Originality": {"score": 4, "justification": "ok"}},
                 "failing_criteria": [],
                 "revision_feedback": "Add a robustness paragraph.",
                 "routing": "paper_writeup"},
                {"gate": "writeup", "round": 0, "verdict": "PASS",
                 "criteria_scores": {
                     "Clarity": {"score": 3, "justification":
                                 "disabled gate placeholder"}},
                 "failing_criteria": [],
                 "revision_feedback": "Gate disabled; no review performed.",
                 "routing": "complete"},
            ],
            "current_gate": None,
            "current_route": None,
            "blocked_reason": None,
        },
        "results": results,
        "paper_writing_subagent_id": None,
        "deliverable_path": os.path.join(workspace, "deliverable.md"),
        "review_rounds": 0,
        "final_verdict": "APPROVE",
    }


def _build_legacy_tree(epics_root: str) -> None:
    """Write the on-disk issue tree (comments) for the legacy fixture."""
    for iid in ("lr", "h", "ep", "ee", "w"):
        _comment(epics_root, iid, "c-01-seeding.md",
                 "[seeding] %s opened with the stage goal, inputs, and "
                 "acceptance criteria." % iid)
    _comment(epics_root, "a", "c-01-seeding.md",
             "[seeding] Analysis anchor opened with the execution outputs.")
    _comment(epics_root, "a", "c-02-directive-d-l1.md",
             "[directive: d-l1] Epic manager directive: rerun the robustness "
             "checks before analysis completes.")
    _comment(epics_root, "h", "c-02-critique-hypothesis-r1.md",
             "[review-critique: hypothesis-r1] Significance 4 (meets the "
             "bar); Originality 4 (meets the bar).")
    _comment(epics_root, "a", "c-03-critique-analysis-r1.md",
             "[review-critique: analysis-r1] Quality 4 (meets the bar); "
             "Significance 4 (meets the bar); Originality 4 (meets the bar).")
    _comment(epics_root, "w", "c-02-manager-notice.md",
             "[manager-notice] Writeup Clarity gate disabled; no review was "
             "performed.")


def self_test() -> int:
    """Inline synthetic-fixture self-test: builds a passing new-style
    fixture, a mutated fixture with deliberate violations, and a legacy-style
    fixture; confirms the passing fixtures exit all-green and the mutated
    fixture fails Checks 8-11.  Also exercises the Check 2 active-path
    (writeup gate engaged: bad final_verdict fails loudly, APPROVE/REJECT
    pass), the Check 2 manifest triggers (writeup verdict_history /
    block_events), and the Check 1 cost-ledger fallback
    (results["costs"][issue_id]).  Returns 0 only when every fixture and
    probe behaves as expected."""
    print("validate_execution.py self-test")
    print("===============================")
    all_ok = True

    with tempfile.TemporaryDirectory() as tmp:
        epics_root = os.path.join(tmp, "epic")
        os.makedirs(epics_root)
        workspace = os.path.join(tmp, "ws")
        _build_workspace(workspace)

        # -- [1] passing new-style fixture ---------------------------------
        _build_new_style_tree(epics_root)
        passing = _new_style_manifest(workspace, with_ideation_stop=True)
        results = run_battery(passing, epics_root)
        failures = [msg for _t, ff, _ok in results for msg in ff]
        print("\n[1] synthetic passing new-style fixture"
              " (stage_issues map):")
        for title, ff, ok in results:
            print("    %s  %s" % ("PASS" if ok else "FAIL", title))
        print("    manifest style: %s (auto-detected)" % _manifest_style(passing))
        if failures:
            all_ok = False
            for msg in failures:
                print("    " + msg)

        # -- [2] mutated fixture -------------------------------------------
        _mutate_disk(epics_root)
        mutated = _new_style_manifest(workspace, with_ideation_stop=False)
        mresults = run_battery(mutated, epics_root)
        mfailures = [msg for _t, ff, _ok in mresults for msg in ff]
        print("\n[2] synthetic mutated fixture (deliberate violations):")
        failed_names = [t.split(":")[0] for t, ff, ok in mresults if not ok]
        for title, ff, ok in mresults:
            print("    %s  %s" % ("PASS" if ok else "FAIL", title))
        expected = ("Check 8", "Check 9", "Check 10", "Check 11")
        missing = [e for e in expected if e not in failed_names]
        extra = [t for t, ff, ok in mresults
                 if not ok and t.split(":")[0] not in expected]
        if mfailures and not missing and not extra:
            print("    as expected: %s failed on the mutated fixture"
                  % ", ".join(expected))
            for msg in mfailures:
                print("    " + msg)
        else:
            all_ok = False
            if not mfailures:
                print("    FAIL  mutated fixture produced NO failures "
                      "(Checks 8-11 not exercised)")
            if missing:
                print("    FAIL  mutated fixture did not fail the expected "
                      "checks: missing %s" % ", ".join(missing))
            if extra:
                print("    FAIL  mutated fixture also failed unexpected "
                      "checks: %s" % "; ".join(extra))

        # -- [3] legacy-style fixture --------------------------------------
        _build_legacy_tree(epics_root)
        legacy = _legacy_manifest(workspace)
        lresults = run_battery(legacy, epics_root)
        lfailures = [msg for _t, ff, _ok in lresults for msg in ff]
        print("\n[3] synthetic legacy fixture (stage_to_issue_id, "
              "num_issues, ideation disabled):")
        for title, ff, ok in lresults:
            print("    %s  %s" % ("PASS" if ok else "FAIL", title))
        print("    manifest style: %s (auto-detected)" % _manifest_style(legacy))
        if lfailures:
            all_ok = False
            for msg in lfailures:
                print("    " + msg)

        # -- [4] Check 2 active-path fixture (writeup gate engaged) ---------
        # A writeup gate is engaged via review.max_writeup_review_loops > 0
        # (new-style; normalization forces synthesis.max_review_rounds to 0).
        # The external final_verdict contract must activate: a bad value
        # fails Check 2 LOUDLY, and APPROVE passes the whole battery.
        _build_new_style_tree(epics_root)       # rebuild pristine tree
        c2_bad = _new_style_manifest(workspace, with_ideation_stop=True)
        c2_bad["config"]["review"]["max_writeup_review_loops"] = 1
        c2_bad["final_verdict"] = "UNKNOWN"
        c2r = run_battery(c2_bad, epics_root)
        c2_failures = [msg for _t, ff, _ok in c2r for msg in ff]
        print("\n[4] Check 2 active-path (writeup gate engaged via "
              "max_writeup_review_loops=1, final_verdict UNKNOWN):")
        for title, ff, ok in c2r:
            print("    %s  %s" % ("PASS" if ok else "FAIL", title))
        c2_failed = [t.split(":")[0] for t, ff, ok in c2r if not ok]
        c2_extra = [t for t, ff, ok in c2r
                    if not ok and t.split(":")[0] != "Check 2"]
        if (c2_failures and c2_failed == ["Check 2"] and not c2_extra):
            print("    as expected: Check 2 failed loudly on final_verdict "
                  "'UNKNOWN' (all other checks passed)")
            for msg in c2_failures:
                print("    " + msg)
        else:
            all_ok = False
            if not c2_failures:
                print("    FAIL  Check 2 did NOT engage on the active writeup "
                      "path (final_verdict 'UNKNOWN' accepted)")
            if c2_failed != ["Check 2"]:
                print("    FAIL  unexpected fails on the Check 2 active-path "
                      "fixture: %s" % ", ".join(c2_failed))
            if c2_extra:
                print("    FAIL  other checks also failed on the Check 2 "
                      "active-path fixture: %s" % "; ".join(c2_extra))

        c2_ok = _new_style_manifest(workspace, with_ideation_stop=True)
        c2_ok["config"]["review"]["max_writeup_review_loops"] = 1
        ok_results = run_battery(c2_ok, epics_root)  # final_verdict APPROVE
        ok_failures = [msg for _t, ff, _ok in ok_results for msg in ff]
        if ok_failures:
            all_ok = False
            print("    FAIL  Check 2 active-path with final_verdict 'APPROVE' "
                  "produced failures:")
            for msg in ok_failures:
                print("    " + msg)
        else:
            print("    as expected: Check 2 active-path with final_verdict "
                  "'APPROVE' passed the whole battery")

        # -- [5] unit probes (targeted direct calls, no disk tree needed) ---
        # Check 2 manifest triggers (verdict_history / block_events) and
        # the Check 1 cost-ledger fallback (results["costs"][issue_id]).
        print("\n[5] unit probes -- Check 2 manifest triggers + Check 1 "
              "cost-ledger fallback:")
        unit_ok = True

        # 5a: writeup verdict_history entries engage Check 2 even with the
        # config zeroed (normalization forces max_review_rounds to 0).
        p5a = _new_style_manifest(workspace, with_ideation_stop=True)
        p5a["config"]["synthesis"] = {"max_review_rounds": 0}
        p5a["config"]["review"] = {"max_writeup_review_loops": 0}
        p5a["final_verdict"] = "UNKNOWN"
        ff5a = check_review_evidence(p5a)
        if any("'final_verdict' is 'UNKNOWN'" in m for m in ff5a):
            print("    5a PASS  writeup verdict_history entry engages Check 2 "
                  "(config zeroed; 'UNKNOWN' rejected)")
        else:
            unit_ok = False
            print("    5a FAIL  writeup verdict_history trigger produced %r"
                  % ff5a)

        # 5b: writeup block_events entries engage Check 2 (loop-limit block).
        p5b = _new_style_manifest(workspace, with_ideation_stop=True)
        p5b["config"]["synthesis"] = {"max_review_rounds": 0}
        p5b["config"]["review"] = {"max_writeup_review_loops": 0}
        p5b["review_state"]["verdict_history"] = [
            e for e in p5b["review_state"]["verdict_history"]
            if e.get("gate") != "writeup"]
        p5b["review_state"]["block_events"] = [
            {"decision_type": "manager_block", "gate": "writeup",
             "current_gate": "writeup", "current_route": "blocked",
             "reason": "Writeup Clarity gate exhausted"}]
        p5b["final_verdict"] = "UNKNOWN"
        ff5b = check_review_evidence(p5b)
        if any("'final_verdict' is 'UNKNOWN'" in m for m in ff5b):
            print("    5b PASS  writeup block_events entry engages Check 2 "
                  "('UNKNOWN' rejected)")
        else:
            unit_ok = False
            print("    5b FAIL  writeup block_events trigger produced %r"
                  % ff5b)

        # 5c: no writeup gate engaged at all -> Check 2 stays inactive
        # (bad final_verdict tolerated exactly as before: no weakening).
        p5c = _new_style_manifest(workspace, with_ideation_stop=True)
        p5c["config"]["synthesis"] = {"max_review_rounds": 0}
        p5c["config"]["review"] = {"max_writeup_review_loops": 0}
        p5c["review_state"]["verdict_history"] = [
            e for e in p5c["review_state"]["verdict_history"]
            if e.get("gate") != "writeup"]
        p5c["review_state"]["block_events"] = []
        p5c["final_verdict"] = "UNKNOWN"
        ff5c = check_review_evidence(p5c)
        if not ff5c:
            print("    5c PASS  no writeup gate engaged -> Check 2 inactive "
                  "('UNKNOWN' not checked)")
        else:
            unit_ok = False
            print("    5c FAIL  Check 2 engaged without a writeup gate: %r"
                  % ff5c)

        # 5d: Check 1 accepts costs recorded ONLY in the documented
        # accumulation ledger results["costs"][issue_id].
        p5d = {
            "issues": [{"issue_id": "only-ledger-i1", "status": "resolved"}],
            "results": {"costs": {"only-ledger-i1": {
                "input_tokens": 1200, "output_tokens": 600,
                "cache_read_tokens": 90}}},
        }
        ff5d = check_resolved_issues_have_cost(p5d)
        if not ff5d:
            print("    5d PASS  Check 1 accepts results['costs'][issue_id] "
                  "only (per-issue cost absent)")
        else:
            unit_ok = False
            print("    5d FAIL  Check 1 rejected the costs-ledger fixture: %r"
                  % ff5d)

        # 5e: Check 1 still fails when cost is absent everywhere.
        p5e = {
            "issues": [{"issue_id": "no-cost-i1", "status": "resolved"}],
            "results": {},
        }
        ff5e = check_resolved_issues_have_cost(p5e)
        if ff5e:
            print("    5e PASS  Check 1 still fails when no cost exists "
                  "anywhere")
        else:
            unit_ok = False
            print("    5e FAIL  Check 1 accepted a resolved issue with no "
                  "cost at all")

        # 5f: 'REJECT' is also a valid final_verdict on the engaged path.
        p5f = _new_style_manifest(workspace, with_ideation_stop=True)
        p5f["config"]["review"]["max_writeup_review_loops"] = 1
        p5f["final_verdict"] = "REJECT"
        ff5f = check_review_evidence(p5f)
        if not ff5f:
            print("    5f PASS  Check 2 accepts final_verdict 'REJECT' on the "
                  "engaged writeup path")
        else:
            unit_ok = False
            print("    5f FAIL  Check 2 rejected final_verdict 'REJECT': %r"
                  % ff5f)

        if not unit_ok:
            all_ok = False

    print()
    if all_ok:
        print("Result: SELF-TEST PASS")
        return 0
    print("Result: SELF-TEST FAILED")
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 validate_execution.py <path-to-project.json>")
        print("       python3 validate_execution.py --self-test")
        return 1

    if sys.argv[1] == "--self-test":
        return self_test()

    path = sys.argv[1]
    project = _load_project(path)
    epics_root = os.path.dirname(os.path.abspath(path))

    print("  Manifest style: %s (auto-detected)" % _manifest_style(project))

    results = run_battery(project, epics_root)
    all_failures: list[str] = []

    for title, failures, _ok in results:
        if failures:
            print(f"  FAIL  {title}")
            for msg in failures:
                print(msg)
            all_failures.extend(failures)
        else:
            print(f"  PASS  {title}")

    print()
    if all_failures:
        n = len(all_failures)
        print(f"Result: FAILED ({n} sub-check{'s' if n != 1 else ''} failed)")
        return 1
    else:
        print("Result: ALL PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())