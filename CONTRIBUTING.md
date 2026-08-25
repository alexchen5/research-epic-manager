# Contributing

Thanks for considering a contribution to the epic-manager skills. This file
is deliberately short; the rules below keep the repo coherent.

## License and attribution

- The repo is MIT-licensed (see `LICENSE`); the copyright line reads
  "Copyright (c) 2026 The epic-manager contributors".
- Attribution is collective and field-level: the design is informed by the
  surveyed 2024-2026 autonomous-research field, not by any single project,
  and nothing is vendored from another repository. Do not add per-project
  callouts or copy code verbatim from other projects.
- Tracker comments are author-anonymous: every comment is tagged `**Agent**`,
  with no human or agent names. Do not be surprised if your contribution
  appears that way in tracker threads. Git history, by contrast, is
  attributed normally: your commits keep your name.

## ASCII rule

Agent-facing files (`skills/`, `AGENTS.md`, and the validator scripts) must
stay ASCII-only; the validators enforce this. Human-facing files (such as
this README) may use richer formatting. When you add or edit a file, keep it
ASCII unless it is explicitly a human-facing document.

## How to validate a change

Run the relevant battery before anything is accepted: each skill's
`scripts/test_*.py` (stdlib-only Python, self-deleting scratch epics) and,
for project-manager changes, `skills/research-project-epic-manager/scripts/validate_execution.py`
plus `validate_protocol.py`. Everything must exit 0. Keep the files you touch
ASCII-only.

## What does not belong

- Institution-branded content and credentials. This repo is not affiliated
  with any institution; do not add logos, branding, or credentials.
- Secrets, keys, or personal data of any kind.