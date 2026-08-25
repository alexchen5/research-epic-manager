# Validation

This reference documents the validation batteries, implementation
order, config surface, risks, and the invariants.

## Validation

**`scripts/validate_execution.py`** (stdlib-only; the existing Checks 1-7 are
preserved and adapted to `stage_issues`; old-style manifests are
auto-detected and validated with adapted checks):

### Checks 1-11

| Check | Contract |
|-------|----------|
| 1 | Every resolved issue has `cost` with non-zero tokens |
| 2 | `synthesis.max_review_rounds > 0` -> `review_rounds >= 1`, `final_verdict` set (APPROVE/REJECT only) |
| 3 | paper-writing issue -> `paper_writing_subagent_id` persisted |
| 4 | Project workspace exists and contains the deliverable |
| 5 | All research issues have a terminal status |
| 6 | Control issue entry exists in the manifest |
| 7 | Simulation disclosure in the deliverable |
| 8 | Directive-trail parity: interventions ledger entry <-> `[directive: <digest>]` comment on the affected issue |
| 9 | Thread liveness: every non-control issue has >= 1 comment (seeding comments count) |
| 10 | Reviewer-comment parity: each `verdict_history` entry maps to >= 1 `[review-critique]` on the stage anchor; manager-generated verdicts (fallback, disabled round-0 placeholder) exempt, and loop-limit synthetics (recorded in `block_events`; a `verdict_history` mirror carries routing `"blocked"`) exempt too, covered by `[manager-notice]` |
| 11 | Ideation evidence: active only when `ideation.max_rounds > 0`; >= 2 `[proposal-v<n>]` comments or a recorded stop condition; else manifest records `ideation_disabled` |

**`scripts/validate_protocol.py`** (stdlib-only): all existing tests
preserved; add dynamic-lifecycle helper tests (append-only `stage_issues`
operations -- insert, lookup, terminal-or-not, anchor designation),
ideation controller stop-condition tests (pass / cap / plateau = no
criterion improved AND failing set unchanged), and comment-contract helper
tests (derive_comment_record zero-token rule, digest parity).

**Probe scenarios P8-P11 are delivered as VALIDATOR COVERAGE, not as a
separate demo artifact** (there is no standalone probe script for them):
P8 plateau stop, P9 dynamic issue split within a stage, P10 comment parity,
and P11 just-in-time creation order are covered by `validate_protocol.py`
unit tests (plateau stop, median aggregation, token bucket,
`stage_issues` operations, zero-token critique rendering) and by
`validate_execution.py --self-test` synthetic fixtures (directive parity,
thread liveness, reviewer-comment parity, ideation evidence, JIT issue
style).

**E2E:** run A with gates + ideation enabled (expect dynamic issues,
directive-trail comments, reviewer critique comments, an ideation revision
thread, validators exit 0); run B with everything disabled (linear
passthrough still uses sequential just-in-time issue creation; validators
exit 0). **Both E2E runs complete with ZERO human interaction** in
`autonomous` mode (no plan-approval, decision, or synthesis stops await a
human). Wipe and re-run per iteration, as before.

## Implementation Order, Config Surface, Risks

**Order:** (1) protocol docs (SKILL.md, the eight
`references/*.md` files); (2) scripts
(`ideation_controller.py`, `concept_store.py`,
`review_engine.py` extensions incl. `derive_comment_record`); (3) config
template; (4) validators (incl. the P8-P11 probe coverage: protocol unit
tests + execution-validator self-tests); (5) e2e.

**Config surface:** `planning.dynamic_issues` (default true);
`ideation: {max_rounds: 3, reviewers: 2, on_exhaust: block|proceed}`;
`autonomy.mode` = autonomous (default) | gated;
`planning.num_issues` removed (tolerated + ignored in legacy configs).

**Risks:**
- Token cost of ideation rounds: mitigated by `ideation.max_rounds` and
  `ideation.reviewers` (the cost lever) plus the ideation token bucket.
- Thread noise: one-point-per-comment discipline; per-round history
  comments are mandatory but each is a single comment.
- Validator complexity: keep stdlib-only and table-driven.
- Backward compatibility: linear mode is the degenerate dynamic mode --
  sequential just-in-time creation, one issue at a time; legacy manifests
  (stage_to_issue_id, num_issues, issues-created status) auto-detected.
- Autonomy decision bias: mitigated by the mandate to record every decision
  plus rationale on the orchestration-log / affected issue, and by
  gated mode for operators who want legacy approval stops.

## Invariants

These hold wherever they appear across the protocol:
- Scoring-only reviewer contract: reviewers score 1-5 per rubric with
  one-sentence justifications and non-empty revision_feedback; never emit
  verdict/failing_criteria/routing; never told pass/fail semantics, the
  threshold, or routing.
- Evidence Preface (Block A): derived at brief time from a workspace scan +
  `execution.constraints`, ends with "Score evidence against what actually
  executed, not against what the text claims."
- Calibration preamble (Block B): shared wording copied verbatim for all
  gates, stage-parameterised ONLY in the evidence clause (hypothesis/ideation
  briefs use the expected-significance replacement; analysis/writeup briefs
  keep the evidence caps unchanged), never abbreviated or dropped elsewhere.
- Coding-agent isolation: coding and reviewer child agents never touch
  tracker files or tracker skills and communicate only with their
  dispatcher.
- Cost harvesting: every issue result carries `cost` with non-zero tokens,
  harvested at completion and accumulated in the cost ledger.
- ASCII-only .md rule: every .md file this skill produces or documents must
  contain only ASCII characters.
