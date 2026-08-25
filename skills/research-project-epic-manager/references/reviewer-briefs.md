# Reviewer Briefs

This reference defines the reviewer side of the research-project protocol:
the reviewer scoring review contract, the reviewer brief
construction (Blocks A-E, plus the ideation reviewer brief), and
the reviewer commenting protocol (DISPATCHER-POSTING).

For research-project gate reviews the scoring contract supersedes the
tracker's APPROVE/REJECT reviewer template: a reviewer returns a scoring
review only and is never told pass/fail semantics.

## Reviewer Scoring Review Contract

Both Phase C (hypothesis/analysis) and Phase E (writeup) use the identical
contract. A reviewer sub-agent returns a *scoring review* -- it scores
quality per criterion and NEVER decides pass/fail:

Scoring JSON shape: `{gate, round, criteria_scores, revision_feedback,
integrity_mismatches}` -- canonical example in Block E below; the reviewer
never emits verdict/failing_criteria/routing.

**The reviewer is never told pass/fail semantics.** The scoring review has
no `verdict`, no `failing_criteria`, no `routing` -- the reviewer scores
only. If a response happens to carry a `verdict` field anyway, it is
ignored. Extra fields (e.g. `integrity_mismatches`) are allowed and ignored.

**Validation:** `parse_verdict()` decodes JSON; returns None on failure.
`validate_review_scoring()` checks all 4 scoring fields (gate, round,
criteria_scores, revision_feedback), gate match, int round >= 1 (not bool),
criteria_scores covering EXACTLY the gate's criteria (each item an int score
1-5, not bool, with a non-empty one-sentence `justification`; unknown
criteria invalid), and a non-empty `revision_feedback` (after strip). Retry
once on failure. Second failure -> fallback: an all-1 scoring review whose
stored entry is derived via `derive_verdict()` (FAIL with every criterion
failing, derived routing).

**Stored verdict entries (manager-derived):** The manager composes the
stored seven-field entry via `derive_verdict(scoring, gate)`:

- `verdict` = "FAIL" iff ANY criterion score < PASS_THRESHOLD (4), else
  "PASS"
- `failing_criteria` = criteria scored < 4
- `routing` = the gate's pass route on PASS (hypothesis ->
  experiment_execution, analysis -> paper_writeup, writeup -> complete),
  else `route_for_failure(gate, failing_criteria)`
- `criteria_scores` and `revision_feedback` carried through unchanged

Stored entries keep the seven-field contract and `validate_verdict()`
enforces derived-consistency: the stored verdict/failing_criteria/routing
must equal the derivation from the criteria_scores (a stored entry whose
fields contradict its scores is INVALID).

```json
{
  "gate": "hypothesis | analysis | writeup",
  "round": 1,
  "verdict": "PASS | FAIL",
  "criteria_scores": {
    "CriterionName": {"score": 1-5, "justification": "string"}
  },
  "failing_criteria": ["CriterionName", ...],
  "revision_feedback": "string (non-empty, concrete, actionable)",
  "routing": "literature_review | experiment_planning | paper_writeup | complete"
}
```

**Manager-generated "blocked" route:** When loop limits are exhausted, the
manager sets `routing: "blocked"` directly. This is NOT a reviewer-allowed
value and NOT a derived routing; it signifies a procedural block.
`validate_verdict()` does NOT accept "blocked" as valid routing -- it is
only set by the manager outside the reviewer validation path. The manager
records such exhaustion/loop-limit decisions in `block_events` (append-only
manager decision records) and does NOT append them to `verdict_history` as
a normal flow. IF a flow mirrors a synthetic into `verdict_history`, the
mirror must keep `routing: "blocked"` so that Check 10 exempts it from
reviewer-comment parity; the associated `[manager-notice]` comment is
required either way.

**Criteria restrictions by gate** (reviewers never emit routing; stored
entries may carry any of the gate's routes):

| Gate | Allowed Criteria | Valid Routing (stored entries) |
|------|-----------------|-------------------------------|
| hypothesis | Significance, Originality | literature_review, experiment_execution |
| analysis | Quality, Significance, Originality | literature_review, experiment_planning, paper_writeup |
| writeup | Clarity | paper_writeup, complete |

**Score Rubric (1-5):**

| Score | Meaning |
|-------|---------|
| 5 | Exceptional -- direct evidence of the claimed quality |
| 4 | Sound -- minor issues only, meets the bar |
| 3 | Borderline -- defensible with caveats, below the acceptance bar |
| 2 | Weak -- material flaws that block the claim |
| 1 | Reject-worthy or materially misleading |

The system derives the round outcome from the scores: a criterion scored
1-3 fails the round; 4-5 on every criterion passes. The reviewer scores
only; it never states a pass/fail outcome.

**Failure Modes:**

| Condition | Handling |
|-----------|----------|
| Reviewer returns malformed scoring review | Retry once with strict instructions. Second failure -> fallback all-1 scoring, derived FAIL via `derive_verdict()`; the stored entry is marked `fallback: true` and is EXEMPT from Check 10 (manager posts a `[manager-notice]` comment instead of a rendered critique) |
| Reviewer crashes | Retry once. Second failure -> fallback scoring |
| Per-gate loop limit exceeded | Manager blocks: `current_route=blocked`, `blocked_reason` set, no reviewer dispatched; the loop-limit synthetic is recorded in `block_events` (a manager decision record, distinct from `verdict_history`); a `verdict_history` mirror carries routing `"blocked"` and is EXEMPT from Check 10 (manager posts a `[manager-notice]` comment either way) |
| Total project loop limit exceeded | Same as above |
| All gates disabled (max_loops=0) | Linear passthrough with sequential just-in-time issue creation. Backward compatible. |

---

## Reviewer Brief Construction (authoritative -- must be followed verbatim by the runner)

This section defines the reviewer brief builders referenced by
`SKILL.md` Phases A-E "Key references"
(`build_reviewer_brief` for the Phase C hypothesis and analysis gates,
`build_writeup_reviewer_brief` for the Phase E writeup Clarity
gate, and the ideation reviewer brief for the Phase C ideation loop). The
runner MUST construct every gate reviewer brief from the templates below, IN
FULL -- never abbreviate or drop the calibration preamble. A brief that omits
the calibration preamble, the Evidence Preface, or the reporting-integrity
obligations is NOT a valid reviewer brief; treat this as a protocol
violation, not a style choice.

The two gate builders share one construction:

```
build_reviewer_brief(stage, criteria, valid_routing, evidence_preface,
                     findings_text) -> brief
build_writeup_reviewer_brief(deliverable_path, round_number,
                             evidence_preface) -> brief

    brief = join("\n\n", [
        evidence_preface(stage),          # block A
        calibration_preamble(stage),      # block B -- shared preamble,
                                          #   evidence clause stage-parameterised
        reporting_integrity_obligations(stage),  # block C
        gate_specific_criteria(stage, criteria, valid_routing),  # block D
        scoring_review_contract(stage),          # block E
    ])
```

### Block A -- Evidence Preface (2-4 sentences derived at brief time)

The runner derives the preface from the project workspace and project config
AT BRIEF TIME (not written once and reused). Steps:

1. Scan the project workspace for `**/results_summary.json`,
   `archive/**/*.json`, and `**/*_metrics.json`.
2. Extract any `mode`, `dataset.origin`, `model.class` (or `model`),
   `n_records`, and count fields found in those artifacts.
3. If a mode says dry-run/simulated, OR no mode artifact exists yet, state
   that explicitly and instruct the reviewer to assume simulated internals.
4. Also derive from project config `execution.constraints` (e.g. CPU-only,
   no GPU) and include them.
5. The preface ends with the fixed sentence:
   "Score evidence against what actually executed, not against what the text
   claims."

For gate reviewers the findings text passed to the brief MUST be the
concatenation of the stage issues' finding summaries (`gate findings_text
= concatenation of the stage issues' finding summaries`).

### Block B -- Calibration Preamble (stage-parameterised in the evidence clause only, mandatory)

The preamble is SHARED verbatim across every gate and round, with exactly
ONE stage-parameterised clause: the evidence clause. Hypothesis-gate and
ideation briefs replace the evidence-cap sentences with the replacement
below; analysis/writeup briefs keep the existing evidence-cap sentences
unchanged. All other preamble wording stays byte-identical everywhere.

```
You are a strict, adversarial peer reviewer. Assume this submission is
borderline-reject until it survives scrutiny. You do NOT decide pass or
fail; the system derives the round outcome from your scores. Score quality
only. Score rubric: 1 = reject-worthy or materially misleading; 2 = weak,
material flaws that block the claim; 3 = borderline, defensible with
caveats, below the acceptance bar; 4 = sound, minor issues only, meets the
bar; 5 = exceptional, direct evidence of the claimed quality.
[EVIDENCE CLAUSE -- stage-parameterised]

Evidence clause for HYPOTHESIS-gate and IDEATION briefs (replaces the caps
sentences verbatim):

No executed experimental evidence exists at this stage BY DESIGN. Judge
expected significance against the cited literature / indexed corpus; do
not score below the bar merely because results do not exist yet.

Evidence clause for ANALYSIS-gate and WRITEUP briefs (kept unchanged):

Evidence-based caps: if the Evidence Preface indicates simulated/dry-run
internals, Quality can never exceed 3; if the evidence covers a single
dataset or domain, Significance can never exceed 3.

revision_feedback MUST be non-empty, concrete, and actionable.
```

### Block C -- Reporting-Integrity Obligations (all gates)

Every gate brief MUST instruct the reviewer to:

- Verify that the text under review does not claim real data/models/containers
  that the Evidence Preface contradicts -- e.g. "real dataset", "real model",
  "containerised", "Docker build" vs a generator/surrogate/subprocess
  artifact. ANY such mismatch forces the affected criterion to score 2 or
  below and must be recorded in `revision_feedback` with the literal word
  "blocker" (spell it out; do not bury it). Reviewers never emit
  `failing_criteria`; the forced low score drives the derived round outcome.
- Treat the Evidence Preface as ground truth for what actually executed; the
  text under review may not assert more than the preface supports.

For the WRITEUP gate (and Phase E deliverables only), Block C additionally
MUST instruct the reviewer to:

- Require a simulation marker in the abstract AND on every results
  table/prose cell when the preface indicates simulated internals (markers:
  "simulated", "dry-run", "[simulated]", "[ESTIMATE"). A single marker buried
  in the body does NOT satisfy this obligation.
- Cross-check every reported count and ledger row against the artifact JSON
  values given in the Evidence Preface; any mismatch is a blocker: score the
  affected criterion 2 or below and record "blocker" in `revision_feedback`.
- Reject threshold rows that were pre-registered as descriptive-only being
  promoted post hoc into formal PASS rows; rows pre-registered as descriptive
  must stay descriptive.

### Block D -- Gate-Specific Criteria

Keep the stage-specific criterion text and allowed routing from the
"Criteria restrictions by gate" table + shared 1-5 rubric above; the
reviewer scores quality only and never states pass/fail; routes are
manager-derived. Stage-keyed criterion definitions follow.

#### Stage-keyed criterion definitions

What each criterion
MEANS is stage-conditional and the brief must define it for its stage:

- Hypothesis gate + ideation reviews: "Significance" means EXPECTED
  significance -- judged on literature-grounded motivation, the importance
  of the problem, and the plausible impact if executed, assessed AGAINST
  THE INDEXED CORPUS / cited literature. Absence of primary experimental
  evidence is inherent to the stage and MUST NOT reduce any score. What
  legitimately lowers Significance: weak or missing literature grounding,
  a marginal problem, no plausible impact path. "Originality" is judged as
  novelty against the indexed corpus.
- Analysis gate (and writeup where applicable): executed-evidence
  standards stand -- Significance and Quality are judged against what
  actually ran, and the existing evidence-based caps (simulated internals
  cap Quality at 3; single-dataset/domain caps Significance at 3) APPLY
  here.

### Block E -- Scoring Review JSON Contract

The reviewer MUST return the shared SCORING review (no verdict, no
failing_criteria, no routing):

The `round` field in the example below is a PLACEHOLDER: every brief must
stamp the ACTUAL round number of the brief being built -- a round-2 brief
must show `"round": 2`, never a stale example value.

```json
{
  "gate": "hypothesis | analysis | writeup",
  "round": 1,
  "criteria_scores": {
    "CriterionName": {"score": 1-5, "justification": "one sentence"}
  },
  "revision_feedback": "string (MUST be non-empty, concrete, actionable)",
  "integrity_mismatches": [ "..." ]   // OPTIONAL
}
```

The manager derives the stored seven-field entry from this scoring review
via `derive_verdict()` (verdict = FAIL iff any score < 4; failing_criteria
= scores < 4; routing = pass route or `route_for_failure`), and
`validate_verdict()` enforces derived-consistency on the stored entries.

### The Ideation Reviewer Brief (hypothesis stage)

The ideation loop uses its own reviewer brief with the SAME scoring-only
contract and calibration discipline, grounded in the concept-index corpus
(an Evidence-Preface analog; see "Ideation Loop" below). Construction:

```
build_ideation_reviewer_brief(round_number, proposal_text, concept_preface)
    brief = join("\n\n", [
        concept_index_preface(corpus_stats),   # Evidence-Preface analog
        calibration_preamble("hypothesis"),    # block B -- shared preamble,
                                                 #   evidence clause = hypothesis/ideation variant
        ideation_criteria(),                   # Clarity, Relevance, Originality,
                                               #   Feasibility, Significance
        ideation_scoring_contract(round_number),
    ])
```

`concept_index_preface` states the corpus statistics from
`ideas/concept-index.json` (document count, entity count, top co-mentions)
and ends with the fixed sentence: "Score the proposal against the indexed
corpus, not against what the text claims." It additionally frames
Significance as EXPECTED significance anchored to the indexed corpus:
proposals are judged on literature-grounded motivation,
problem importance, and plausible impact if executed against the
corpus/cited literature; the absence of executed evidence is inherent to
ideation and must not lower scores. Ideation reviewers are never told about
stop conditions, prior scores, other reviewers, pass/fail semantics, or
routing.

---

## Reviewer Commenting Protocol (DISPATCHER-POSTING)

**Reviewers never append comments.** Reviewers return scoring JSON only and
never see tracker surfaces or prior scores;
their DISPATCHER renders the human-readable critique and appends it via the
`add-comment` script under the anonymous `**Agent**` tag. This preserves the
isolation contract exactly, makes Check 10 parity provable by construction,
and matches the tracker-wide rule that issue managers are the comment
writers.

**Contract:**

1. After each gate review, the dispatcher (epic manager for the
   hypothesis/analysis/writeup gates; the ideation issue-manager for
   ideation rounds) renders a human-readable critique comment from the
   scoring review via the `review_engine.derive_comment_record` engine
   helper, and appends it to the stage's anchor issue:
   - per-criterion score with its one-sentence justification,
   - the non-empty `revision_feedback`,
   - marker `[review-critique: <gate>-r<round>]`.
2. Anti-anchoring is preserved: the critique is rendered ONLY from the
   scoring review (gate, round, criteria_scores, revision_feedback). The
   reviewer still never learns pass/fail semantics, the threshold, or
   routing -- and neither the reviewer NOR the rendered critique carries
   those.
3. **Zero-token rule:** a rendered critique contains ZERO standalone
   occurrences of PASS, FAIL, THRESHOLD, ROUTING, or VERDICT
   (case-insensitive whole-word matches; substring hits inside longer words
   such as "surpass" are not banned).
   `derive_comment_record` never includes `derive_verdict` output
   (verdict/failing_criteria/routing) and never states the threshold; it
   uses scores and qualitative wording ("score 3", "below the bar", "needs
   revision", "meets the bar"). The gate name in the marker (e.g.
   "hypothesis") is fine; the banned tokens are not.
4. One point per comment: a single critique comment per review (critiques
   are one point: the review outcome narrative). Manager notices are one
   comment each.
5. Manager-generated entries (fallback, disabled round-0 writeup
   placeholder) get a `[manager-notice]` comment instead of a rendered
   critique; loop-limit synthetics follow the "Manager-generated 'blocked'
   route" passage above (block_events + verdict_history mirror + Check-10
   exemption).
