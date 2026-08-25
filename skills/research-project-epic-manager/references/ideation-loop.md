# Ideation Loop (Hypothesis Stage)

The hypothesis stage runs an iterative ideation loop
(`scripts/ideation_controller.py` plus the concept store below), replacing
the one-shot hypothesis emission.

**Entry criteria (gate-entry):** the hypothesis stage is entered only when
the `literature_review` stage is terminal AND its artifact
(`docs/literature-review/review.md`) exists. The ideation loop runs only
when `ideation.max_rounds > 0`.

**Inputs:** (a) the literature-review stage outputs (all
`docs/literature-review/*.md`), and (b) a concept index built over that
corpus.

**Concept store CLI contract (`scripts/concept_store.py`, stdlib-only):**

```
python3 scripts/concept_store.py build --corpus <ws>/docs/literature-review \
    --output <ws>/ideas/concept-index.json
    # entity extraction (capitalized noun-phrase candidates, frequency
    # filter) + co-occurrence counts over the corpus documents. Output JSON:
    # { "entities": [{"name", "count", "docs": [doc_ids]}],
    #   "cooccurrences": [["name_a", "name_b", "count"]],
    #   "papers": [{"id", "title", "path"}] }

python3 scripts/concept_store.py query <ws>/ideas/concept-index.json \
    --top-k 5 <seed concept>...
    # returns the top-k CO-MENTION neighbours of the seed concepts and the
    # top-k papers (co-mention adjacency as the citation-graph analog).
```

**Three component prompts (decomposition).** Per round, three
separately-prompted generator calls produce the three proposal components:

- **Problem** -- research question and gap, grounded in the indexed corpus
  and the literature review.
- **Method** -- the approach addressing the problem; prompt context includes
  the current Problem draft.
- **Experiment Design** -- evaluation protocol (experiment arms, datasets
  from `execution.constraints`, metrics, feasibility); prompt context
  includes the current Problem and Method drafts.

Each generator prompt carries: the augmented context (top-k related
concepts/papers retrieved from the concept store via co-mention adjacency)
PLUS the current revision history read from the hypothesis anchor issue
thread (proposal v1 comment -> critique comments -> ...). The thread IS the
revision history.

**Multi-criteria review.** Per round, `ideation.reviewers` (default 2)
reviewers each score ALL THREE components on the ResearchAgent criteria --
Clarity, Relevance, Originality, Feasibility, Significance -- under the
existing scoring-only contract (Concept-Index Preface grounding); all
reviewers for a round are dispatched in parallel.

**Aggregation (majority-vote analog).** Conflicting feedback is aggregated
per component per criterion: MEDIAN score across reviewers (even count: the
conservative lower middle), and MERGED revision_feedback = concat of all
NON-EMPTY reviewer feedback (order-preserving, de-duplicated); all-empty ->
keep the previous round's feedback or a placeholder note.

**Refinement + history.** Each revised triple is posted to the hypothesis
anchor issue thread as a `[proposal-v<n>]` comment, followed by the
dispatcher-posted ideation critique comments (`[review-critique:
ideation-r<round>]`, one per reviewer aggregate); the thread IS the revision
history. Critiques are rendered through `review_engine.derive_comment_record`
exactly like gate critiques -- the zero-placeholder rule scrubs
stop-condition vocabulary (whole-word matches only, deterministic neutral
substitutes). Every proposal revision comment MUST carry the literal marker
`[proposal-v<n>]` matching its round -- no prose substitutes such as
"PROPOSAL TRIPLE (round n)"; Check 11's counting keys off exactly this
marker.

**Stop conditions (iteration controller; evaluated every round):**

- **pass** -- every component, every criterion >= 4;
- **cap** -- round == `ideation.max_rounds`;
- **plateau** -- NO criterion improved vs the previous round AND the failing
  set (criteria scoring < 4) is UNCHANGED. Plateau detection is enabled by
  default (not a config switch).

**on_exhaust behaviour (stop-without-pass):** `ideation.on_exhaust`:

- `block` (default) -- the ideation issue-manager reports a blocker; the
  epic manager blocks the hypothesis stage (`review_state.current_gate =
  "ideation"`, `current_route = "blocked"`, `blocked_reason` concrete),
  records the stop condition, and surfaces a blocked state awaiting input -- a genuine-blocker escalation, not a routine decision stop.
- `proceed` -- continue to `experiment_planning` with the best triple
  (highest aggregate score), flagged `flagged: true` in
  `ideas/proposal-final.json` and in the manifest results; the flag feeds
  the hypothesis gate (if enabled) and the experiment-planning stage.

**Ideation token bucket.** The ideation controller maintains a token bucket
for the loop: tokens are harvested after every generator call and every
reviewer call (standard cost harvesting); the bucket budget is
`ideation.max_rounds x ideation.reviewers x per-round call estimate` (2
calls per reviewer per round: generator aggregation in the issue manager is
free; reviewer calls each cost tokens). Bucket exhaustion ends the loop
early with stop condition `cap` (budget) -- a hard cost-control guarantee;
reviewer count is the cost lever (`ideation.reviewers`), not the round cap
alone.

**Evidence-Preface analog.** The Concept-Index Preface (see
`reviewer-briefs.md#the-ideation-reviewer-brief`) grounds scoring in the
corpus and ends with the fixed sentence: "Score the proposal against the
indexed corpus, not against what the text claims."; an evidence-cap analog
applies (novelty vs the index; feasibility vs `execution.constraints`).

**Output contract (feeds experiment_planning).** On stop, the controller
writes `ideas/proposal-final.json`:

```json
{
  "components": { "problem": "...", "method": "...", "experiment_design": "..." },
  "revision_history": [ { "round": 1, "stop_condition": null,
                          "aggregate_scores": { ... } } ],
  "stop_condition": "pass | cap | plateau | ideation_disabled",
  "flagged": false,
  "aggregate_scores": { "Clarity": 4, "Relevance": 4, "Originality": 3,
                        "Feasibility": 4, "Significance": 4 }
}
```

The epic manager registers the artifact
(`artifacts["hypothesis"] = ["ideas/proposal-final.json"]`) and records a
structured summary in `project.json["results"]["ideation"]` (stop
condition, rounds, aggregate scores, flagged). `experiment_planning` reads
`ideas/proposal-final.json` as its input artifact at stage entry.

**Check 11:** with `ideation.max_rounds > 0`, the hypothesis stage thread
must show >= 2 `[proposal-v<n>]` comments or a recorded stop condition; with
`ideation.max_rounds == 0`, the manifest records `"ideation_disabled"` and
Check 11 is inactive.
