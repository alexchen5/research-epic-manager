---
name: add-epic
description: |
  This skill should be used when the user asks to "add an epic", "create an epic",
  "start a new epic", "make an epic", "open an epic", "file an issue epic",
  "set up an epic", or references EPICS_ROOT/.
  Creates a new epic - a GitHub-style container for organising related
  queries and work - under EPICS_ROOT/<epic>, with an EPIC.md template and an
  issues/<issue> directory to hold the issue work scoped to that epic.
triggers:
  - add epic
  - create epic
  - new epic
  - start epic
  - make an epic
  - EPICS_ROOT/
---

# Add Epic

Create a new epic under `EPICS_ROOT/`. An epic is a directory that
groups a body of related work (issues, PRs, decisions) around a shared goal,
mirroring how a GitHub project/repo organises user queries.

## Layout

Each epic lives at `EPICS_ROOT/<epic>` and contains:

```
<epic>/
|-- EPIC.md          # describes the epic (from template)
`-- issues/          # container for issue dirs scoped to this epic
```

## When to use this skill

Use when the user wants to start tracking a discrete body of related work -
for example "add a new feature", "build a dashboard", "fix the auth flow",
"set up an epic for the reports work". Use the `add-issue` skill when the
user then wants to plan individual pieces of work inside the epic.

## Procedure

1.  Slugify the epic name:
    ```bash
    epic=$(echo "<epic name>" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')
    ```

2.  Run the creation script (it lives in this skill's `scripts/` directory -
    the skill loader provides the skill's base path when the skill is loaded):
    ```bash
    python3 <skill-dir>/scripts/add-epic.py "<epic name>"
    ```
    The script creates `EPICS_ROOT/<epic>/EPIC.md` from the `assets/EPIC.template.md`
    template and an empty `issues/` directory.

3.  Verify:
    ```bash
    ls EPICS_ROOT/<epic>/{EPIC.md,issues/}
    cat EPICS_ROOT/<epic>/EPIC.md
    ```

The `EPIC.md` starts as a well-organised template with Status, Goals,
Non-Goals, Scope, Auto Issue Generation, Issues, Milestones, Decisions, Risks,
and cross-links - fill in each section as the epic evolves.

## Additional Resources

- **`assets/ISSUE.template.md`** - the issue template used by the
  `add-issue` skill (kept here for reference/linking).

## Reference Files

- **`assets/EPIC.template.md`** - the EPIC.md skeleton filled in by the script.