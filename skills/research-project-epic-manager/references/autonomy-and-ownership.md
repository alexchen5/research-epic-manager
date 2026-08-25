# Autonomy and Ownership

This reference defines role authority in the research-project
protocol: operation modes and the coding/reviewer isolation contract
(with the issue-manager bridge).

## Operation Modes

- **Config knob:** `autonomy.mode`: `"autonomous"` (DEFAULT) | `"gated"`.
  Normalized in Phase A (`autonomy.setdefault("mode", "autonomous")`);
  validators treat `gated` as the non-default path.
- **`autonomous` (default):** the epic manager runs end-to-end WITHOUT
  stopping for human approval at plan approval (Phase A5), stage boundaries,
  review gates, settlement (Phase D5), or synthesis (Phase E entry). It
  decides itself, records the decision plus rationale on the
  orchestration-log (project-level) or on the affected issue (issue-scoped),
  and proceeds. Mandatory human-approval stops are REMOVED from the default
  flow everywhere they appeared.
- **`gated`:** legacy mode preserving the human-approval stops (plan
  approval, proceed/re-dispatch decisions, synthesis entry) for operators
  who want them.
- **Humans stay reachable mid-run in both modes** via the user-input
  front-end channel (see "User input handling" in `references/communication-logging.md`);
  mid-run input is incorporated like any directive, and an override of a
  recorded decision is itself commented where it lands.
- **Escalation narrows to genuine blockers ONLY:** loop-limit blocks
  (`review_state.blocked_reason`), catastrophic failure rates (>= 50%
  blocked), and missing route targets surface as blocked states that await
  input. Routine decision points are NEVER escalation points.
- **E2E runs complete with zero human interaction** (autonomous mode).

## Isolation Contract

Coding and reviewer sub-agents dispatched by an issue-manager sub-agent (or
by the epic manager for gate reviews) receive self-contained briefs with no
tracker vocabulary. They:

- Never read or write tracker files (no epic paths, no issue paths, no
  manifest paths).
- Never call tracker skills (`add-epic`, `add-issue`, `add-comment`). Under
  DISPATCHER-POSTING this extends to reviewers: they return scoring JSON
  only and never append comments.
- Never reference project lifecycle states, verdicts, thresholds, or
  routing (reviewers) and never reference issue concepts (coding agents).
- Communicate findings only to their dispatcher (issue manager or epic
  manager).
- Receive all context (task description, acceptance criteria, inputs,
  evidence preface, findings text) inline in their brief.

The issue-manager sub-agent (dispatched in Phase C) is the bridge: it
translates the tracker context into an isolated brief and converts the
sub-agent's result back into the structured JSON schema defined in
`references/data-contracts.md#per-issue-result`. An issue manager MAY read
its own issue thread (e.g. the ideation issue-manager reads revision
history) and appends comments only to its own issue.
