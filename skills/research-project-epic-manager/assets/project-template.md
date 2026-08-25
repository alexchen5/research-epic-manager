---
# Project Issue Template (JIT composition)
# Used at JUST-IN-TIME issue creation on the dynamic lifecycle: the issue
# body is composed by the epic manager (or the JIT issue-body sub-agent,
# dispatch.issue_model) from the stage goal, prior-stage artifacts, and the
# stage's acceptance criteria -- at stage entry (anchor), at parallel
# splits, and at gate-routed reworks (reuse or <stage>-rework-r<n>).
# There is NO bulk issue pre-generation in this protocol: no scoping-time
# batch issue creation exists; research issues are composed at stage entry
# only (anchor/split/rework), never in a one-off bulk step.
---

## Metadata

- **Status:** open
- **Assignee:** assigned at Phase C dispatch (issue-manager sub-agent)
- **Labels:** research, <stage>
- **Dependencies:** seeded from the canonical stage graph (prior stage issues)

---

## Description

<!-- Compose from the STAGE GOAL and the PRIOR-ARTIFACT INPUTS:
       anchor = stage goal + stage entry inputs (prior stage artifacts)
       split  = one sub-scope of the stage goal + its slice of the inputs
       rework = the routed FAIL feedback (seeded as [seeded-fail-feedback])
                + the retained goal/inputs of the routed-to stage
     State the context, motivation, and scope of this research issue. -->

*To be composed at JIT creation from the stage goal and prior artifacts.*

---

## Acceptance Criteria

<!-- Compose per issue kind (checked at issue completion and, where the
     stage has a gate, at stage exit):
       anchor/split = the stage exit criteria for this stage
       rework      = the gate FAIL criteria (what the FAIL flagged) plus
                     the retained acceptance criteria of the target stage -->

- [ ] The issue findings are documented clearly and completely.
- [ ] Claims are supported by stage artifacts or citations as applicable.
- [ ] The proposed approach is feasible and clearly described (rework:
      addresses the seeded FAIL feedback).
- [ ] Output artifacts for this issue (if any) are produced and verified.
- [ ] Review criteria (correctness, clarity, coverage) are satisfied where
      a gate evaluates this stage.

---

## Proposed Approach

<!-- The JIT issue-body sub-agent fills this with a 1-2 paragraph
     description of the approach to tackle this issue: methodology,
     expected outputs, and verification steps. -->

*Approach composed at JIT creation from the plan and stage inputs.*

---

## Notes

- Issue ids follow the scheme `<stage>-<purpose>-r<n>` (e.g.
  `literature-review-anchor-r1`, `experiment-execution-arm-a-r1`,
  `analysis-rework-r2`); an anchor is the first issue of a stage and is
  the comment surface for that stage's gate critiques.
- The epic manager composes each body at stage entry / split / rework from
  the stage goal, the prior-stage artifacts, and the acceptance criteria;
  the rework variant embeds the FAIL feedback routed from the gate.
- This issue is worked by an issue-manager sub-agent in Phase C, following
  the standard issue-manager lifecycle (open -> blocked/resolved).
- Comments follow the tracker convention: seeding (`[seeding]`, rework
  `[seeded-fail-feedback]`), directives (`[directive: <digest>]`, routed
  user input `[human-directive: <digest>]`), and dispatcher-posted
  critiques (`[review-critique: <gate>-r<n>]`).
- No issues are pre-generated in bulk at any phase (dynamic, just-in-time
  lifecycle only).