# Data Contracts

This reference documents the manifest/data side of the protocol: the
project config schema (doc-side description; the authoritative template is
`assets/project-config-template.yaml`), the per-issue result shape, the
issue manifest (`project.json`), review state, and the interventions ledger.

## Project Config (`project-config-template.yaml`)

The YAML config the human provides alongside the research brief. The
`planning` block defaults to a dynamic just-in-time issue lifecycle
(`planning.dynamic_issues: true`); `planning.num_issues` is REMOVED from the
schema and, if present in a legacy config, is tolerated and ignored. The
`ideation` block configures the hypothesis-stage ideation loop. The `review`
block is unchanged.

The authoritative configuration template is `assets/project-config-template.yaml`
(referenced, not re-embedded here). The doc-side schema description follows;
missing per-gate max-loop fields normalize to 0 (disabled) on load.

Per-gate `review.max_*_review_loops` fields missing from the config
normalize to 0 (disabled) on load; `max_total_project_loops` defaults to
10. `_writeup_loop_present` records whether `max_writeup_review_loops`
was explicitly present, taking precedence over the legacy
`synthesis.max_review_rounds` fallback (used only when absent);
`review.pass_threshold` is legacy informational. `autonomy.mode` defaults
to `"autonomous"` (`autonomy.setdefault("mode", "autonomous")`); `"gated"`
keeps the legacy approval stops. Ideation defaults: `max_rounds: 3`,
`reviewers: 2`, `on_exhaust: block`; stop conditions: pass (all criteria
>= 4), cap (round == max_rounds), plateau (no criterion improved AND
failing set unchanged, detection on by default). Legacy `planning.num_issues`
is tolerated and ignored (see the intro above).

---

## Per-Issue Result (sub-agent final message)

The issue-manager sub-agent returns a structured result to its dispatcher
(the epic manager). Key fields:

- `issue_id` (string, required)
- `status` ("resolved" | "blocked", required)
- `findings` (string, required)
- `outputs` (string[], optional)
- `cost.input_tokens` / `cost.output_tokens` / `cost.cache_read_tokens`
  (integers, optional but MANDATORY in practice; see Phase B cost ledger)
- `blocker_reason` (string, required when blocked)
- `verifier_result` (object: `{passed, evidence, verifier_name}`, optional)
- `review_scores` (map of criterion -> `{score, justification, severity}`,
  optional)
- `score_trajectory` (array of per-round score maps, optional)
- `perspective` (string, optional)

---

## Issue Manifest (`project.json`)

Skeleton written in Phase A; extended just-in-time throughout the run
(issues, stage_issues, artifacts, interventions, results). `stage_issues`,
`artifacts`, and `interventions` are all append-only: existing entries are
never edited, deleted, or re-opened; new work always lands in NEW entries.

```json
{
  "project": "<project.name>",
  "epic": "<epic-name>",
  "status": "scoping-complete | plan-ready | control-validated | dispatching | all-settled | completed | partial | synthesised | aborted | blocked",
  "project_workspace": "WS_ROOT/<ws>/projects/<project-name>/",
  "control_issue_id": "<epic-name>-orchestration-log",
  "config": { /* normalized, includes _writeup_loop_present */ },
  "planning": { "dynamic_issues": true },
  "issues": [ /* JIT-created issue entries; starts with only the control entry */ ],
  "dependencies": { /* seeded from the canonical stage graph at each JIT creation */ },
  "stage_issues": { "literature_review": ["literature-review-anchor-r1"], "hypothesis": ["hypothesis-ideation-r1"] },
  "artifacts": { "literature_review": ["docs/literature-review/review.md"], "hypothesis": ["ideas/proposal-final.json"] },
  "interventions": [ { "ts": "2026-08-22T0300Z", "issue_id": "analysis-rework-r2", "directive_digest": "d-41a3" } ],
  "review_state": { /* as defined below */ },
  "results": { /* per-issue results + costs + ideation stop summary */ },
  "paper_writing_subagent_id": null,
  "deliverable_path": null,
  "review_rounds": 0,
  "final_verdict": null
}
```

Issue entry shape (appended to `issues[]` at JIT creation):

```json
{
  "issue_id": "hypothesis-ideation-r1",
  "title": "Hypothesis ideation (proposal search and refinement)",
  "stage": "hypothesis",
  "dependencies": ["literature-review-anchor-r1"],
  "issue_type": "ideation",
  "status": "open",
  "issue_path": "issues/hypothesis-ideation-r1/ISSUE.md",
  "anchor": true,
  "acceptance_criteria": [ "..." ],
  "seeded_from": null
}
```

- `stage` (required): the canonical stage this issue belongs to; many issues
  may share one stage (splits, reworks).
- `anchor` (true on the FIRST issue created in a stage): the stage anchor is
  the stage's comment surface -- seeding comments, gate critique comments,
  manager notices, and directive-mirror comments target it. It stays the
  comment surface even after it becomes terminal (comments are never
  deleted). A superseded anchor is never reopened; rework lands in NEW
  issues.
- `seeded_from`: provenance string describing why the issue was opened
  (e.g. `"gate-FAIL literature_review"` on a rework issue).

### Back-compat note (old manifests)

Legacy manifests carry
`stage_to_issue_id` (a 1:1 stage -> issue_id map) and
`planning.num_issues`, and may carry status `issues-created`. Such manifests
are auto-detected by the validators, which run adapted checks over them.
New manifests MUST NOT write `stage_to_issue_id`; the map role is replaced
by the append-only `stage_issues` map. In `review_engine.py` the stage-map
helpers (e.g. `invalidate_and_route`) become deprecated wrappers whose
tests are preserved.

---

## Review State (in project.json)

Initialized in Phase A; updated in Phase C (review gates) and Phase E
(writeup). Shape (unchanged fields plus the append-only `block_events`
manager decision record):

```json
{
  "review_state": {
    "loop_counters": {
      "hypothesis_gate": 0,
      "analysis_gate": 0,
      "writeup_gate": 0,
      "total_project_loops": 0
    },
    "verdict_history": [
      {
        "gate": "hypothesis",
        "round": 1,
        "verdict": "PASS",
        "criteria_scores": {"Significance": {"score": 4, "justification": "..."}},
        "failing_criteria": [],
        "revision_feedback": "Three weaknesses: single-dataset evidence caps Significance; coupling claim untested without ablation; abstract lacks a simulation marker.",
        "routing": "experiment_execution",
        "timestamp": "2026-08-21T0200"
      }
    ],
    "block_events": [],  # append-only manager decision records; exhaustion/
                         # loop-limit synthetics land here, NOT in
                         # verdict_history (see text below)
    "current_gate": null,
    "current_route": null,
    "blocked_reason": null
  }
}
```

`block_events` is the append-only home of MANAGER decision records.
Exhaustion/loop-limit synthetics are recorded here (e.g.
`{decision_type: "manager_block", current_route: "blocked", ...}`), NOT
appended to `verdict_history`; see "Manager-generated blocked route" below.

---

## Interventions Ledger

Append-only `project.json["interventions"]`, the source of truth for
epic-manager directives:

`[ { "ts": "2026-08-22T0300Z", "issue_id": "analysis-rework-r2",
     "directive_digest": "d-41a3" } ]`

The epic manager appends one entry whenever it sends a directive (a
cross-role message that changes scope, adds a requirement, reroutes, or
requests revision). `directive_digest` is a short stable identifier derived
from the directive text (e.g. hash prefix) that is ALSO embedded in the
mirror comment the receiving issue manager appends (`[directive:
<digest>]`), making Check 8 parity provable by construction.

