#!/usr/bin/env python3
"""Deterministic stdlib ideation loop control for the hypothesis stage.

Pure, order-independent helpers that drive the generate -> multi-criteria
review -> revise loop (the ResearchAgent-inspired ideation subroutine).  All
functions are deterministic, JSON-serialisable in their inputs and outputs,
and never mutate their arguments.

Contracts:

- ``IDEATION_CRITERIA`` -- the ResearchAgent criteria every ideation
  reviewer scores every component on: Clarity, Relevance, Originality,
  Feasibility, Significance.

- ``IDEATION_COMPONENTS`` -- the three proposal components in canonical
  order: problem, method, experiment_design.

- ``aggregate_reviews(list_of_scoring_dicts) -> dict``
  Aggregates one round's reviewer scoring reviews (majority-vote analog).
  Input: a list of ideation scoring reviews, each:::

      {
        "gate": "ideation",
        "round": 1,
        "components": {
          "problem":         {"criteria_scores": {criterion: {"score": 1-5,
                                                              "justification": str}},
                              "revision_feedback": str},
          "method":          {...},
          "experiment_design": {...},
        },
      }

  Output:::

      {
        "gate": "ideation",
        "round": <max round seen> or 0,
        "aggregate_scores": {component: {criterion: median_score}},
        "revision_feedback": {component: "merged non-empty feedback"},
      }

  Per component per criterion the aggregate score is the MEDIAN across
  reviewers; for an even reviewer count the conservative LOWER of the two
  middle scores is used (e.g. [3, 4] -> 3).  revision_feedback per component
  is the concatenation (single-space joined) of all NON-EMPTY reviewer
  feedback strings, order-preserving and de-duplicated (first occurrence
  wins).  Components are emitted in canonical order; criteria within a
  component are emitted sorted by name.  Non-dict reviews and malformed
  payloads are skipped; a component with no scores is omitted.

- ``should_stop(scores_this_round, scores_prev_round, round_no, max_rounds)
  -> (stop: bool, reason: str)``
  Evaluates the three stop conditions every round, in precedence order
  pass > cap > plateau; ``reason`` is the empty string when not stopping::

      - "pass"    iff EVERY criterion of EVERY component scores >= 4
                  (a passed round is a success even when the cap is reached);
      - "cap"     iff round_no >= max_rounds (a hard round budget; a
                  max_rounds <= 0 configuration stops immediately, which is
                  the loop-disabled behaviour);
      - "plateau" iff scores_prev_round is provided AND no criterion improved
                  vs the previous round AND the failing set (component,
                  criterion pairs scoring < 4) is UNCHANGED -- the
                  LLM-saturation guard.  A brand-new failing criterion or any
                  score increase voids the plateau.

  ``scores_this_round`` / ``scores_prev_round`` share the shape
  {component: {criterion: int score}} (the ``aggregate_scores`` payload of
  ``aggregate_reviews``).  A missing previous round (round 1) can never be a
  plateau.

- ``token_bucket(state, estimated_cost) -> (allowed: bool, new_state: dict)``
  Simple budget guard.  ``state`` is ``{"budget": int, "spent": int}`` (both
  >= 0, missing keys default to 0); ``estimated_cost`` is clamped to >= 0.
  ``allowed`` iff ``spent + estimated_cost <= budget``; ``new_state`` is a
  FRESH dict with ``spent`` incremented when allowed (``estimated_cost <= 0``
  is always allowed and spends nothing).  The input state is never mutated.

- ``initial_bucket(max_rounds, reviewers, per_round_call_estimate) -> dict``
  ``{"budget": max_rounds * reviewers * per_round_call_estimate, "spent": 0}``
  per the documented bucket formula (bucket exhaustion ends the loop early
  with stop condition "cap" in the caller).  All factors are clamped to >= 0.

The pass bar is the single sourced ``review_engine.PASS_THRESHOLD`` (4).
This module imports only the standard library plus ``review_engine``.
"""

from review_engine import PASS_THRESHOLD

IDEATION_CRITERIA = ("Clarity", "Relevance", "Originality", "Feasibility", "Significance")
IDEATION_COMPONENTS = ("problem", "method", "experiment_design")
IDEATION_GATE = "ideation"


def _median(scores):
    """-> int median; even count -> the conservative lower of the two middle
    values (e.g. [3, 4] -> 3, [2, 5] -> 2)."""
    ordered = sorted(scores)
    n = len(ordered)
    if n % 2 == 1:
        return ordered[n // 2]
    return ordered[n // 2 - 1]


def aggregate_reviews(reviews):
    """Aggregate one ideation round's scoring reviews (see module docstring)."""
    reviews = [r for r in (reviews or []) if isinstance(r, dict)]
    rounds = [r["round"] for r in reviews
              if isinstance(r.get("round"), int) and not isinstance(r.get("round"), bool)]
    max_round = max(rounds) if rounds else 0
    if not reviews:
        return {"gate": IDEATION_GATE, "round": 0,
                "aggregate_scores": {}, "revision_feedback": {}}

    scores_by_cell = {}   # (component, criterion) -> [scores]
    feedback_seen = {}    # component -> [deduped feedback strings]
    for review in reviews:
        components = review.get("components")
        if not isinstance(components, dict):
            continue
        for component, payload in components.items():
            if not isinstance(payload, dict):
                continue
            criteria = payload.get("criteria_scores")
            if isinstance(criteria, dict):
                for criterion, item in criteria.items():
                    if not isinstance(item, dict):
                        continue
                    score = item.get("score")
                    if isinstance(score, int) and not isinstance(score, bool):
                        scores_by_cell.setdefault((component, criterion), []).append(score)
            feedback = payload.get("revision_feedback")
            if isinstance(feedback, str) and feedback.strip():
                feedback = feedback.strip()
                seen = feedback_seen.setdefault(component, [])
                if feedback not in seen:
                    seen.append(feedback)

    components_with_data = set(scores_by_cell) | set(feedback_seen)
    ordered_components = [c for c in IDEATION_COMPONENTS if c in components_with_data]
    ordered_components += sorted(components_with_data - set(IDEATION_COMPONENTS))

    aggregate_scores = {}
    for component in ordered_components:
        cells = {criterion: _median(vals)
                 for (comp, criterion), vals in sorted(scores_by_cell.items())
                 if comp == component}
        if cells:
            aggregate_scores[component] = cells

    merged_feedback = {}
    for component in ordered_components:
        strings = feedback_seen.get(component)
        if strings:
            merged_feedback[component] = " ".join(strings)

    return {"gate": IDEATION_GATE, "round": max_round,
            "aggregate_scores": aggregate_scores,
            "revision_feedback": merged_feedback}


def _score_cells(scores):
    """-> dict {(component, criterion): int score} from an aggregate_scores
    payload; malformed entries are skipped."""
    cells = {}
    if not isinstance(scores, dict):
        return cells
    for component, criteria in scores.items():
        if not isinstance(criteria, dict):
            continue
        for criterion, score in criteria.items():
            if isinstance(score, int) and not isinstance(score, bool):
                cells[(component, criterion)] = score
    return cells


def _failing_set(cells):
    """-> frozenset of (component, criterion) pairs scoring below the bar."""
    return frozenset(k for k, v in cells.items() if v < PASS_THRESHOLD)


def should_stop(scores_this_round, scores_prev_round, round_no, max_rounds):
    """Evaluate the ideation stop conditions (see module docstring)."""
    cells = _score_cells(scores_this_round)
    if cells and all(v >= PASS_THRESHOLD for v in cells.values()):
        return True, "pass"
    if round_no >= max_rounds:
        return True, "cap"
    if cells and scores_prev_round is not None:
        prev_cells = _score_cells(scores_prev_round)
        improved = any(cells[(comp, criterion)] > prev_cells.get((comp, criterion), cells[(comp, criterion)])
                       for comp, criterion in cells)
        if not improved and _failing_set(cells) == _failing_set(prev_cells):
            return True, "plateau"
    return False, ""


def token_bucket(state, estimated_cost):
    """Budget guard: ``(allowed, new_state)`` without mutating ``state``."""
    state = dict(state or {})
    budget = int(state.get("budget", 0) or 0)
    spent = int(state.get("spent", 0) or 0)
    try:
        cost = max(0, int(estimated_cost))
    except (TypeError, ValueError):
        cost = 0
    if cost == 0:
        return True, {"budget": budget, "spent": spent}
    if spent + cost <= budget:
        return True, {"budget": budget, "spent": spent + cost}
    return False, {"budget": budget, "spent": spent}


def initial_bucket(max_rounds, reviewers, per_round_call_estimate):
    """-> fresh bucket state per the documented formula
    ``max_rounds * reviewers * per_round_call_estimate`` (all clamped >= 0)."""
    def _nonneg(value):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0
    budget = _nonneg(max_rounds) * _nonneg(reviewers) * _nonneg(per_round_call_estimate)
    return {"budget": budget, "spent": 0}