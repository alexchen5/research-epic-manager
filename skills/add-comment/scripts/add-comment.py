#!/usr/bin/env python3
"""Append a single anonymous, chronological comment to an existing issue.

Usage:
    add-comment.py <epic> <issue> "<comment body>" [--ts 'YYYY-MM-DDThh:mm']
                  [--kind <kind>] [--summary <text>] [--context <text>]
                  [--references <text>]

Creates a new comment file under:
    EPICS_ROOT/<epic>/issues/<issue>/comments/<TS>-<slug>.md

The comment is author-anonymous (uses a stable **Agent** tag, never a human
or agent name) and appended to the end of the thread (newest last). Requires
the issue to already exist (see the add-issue skill).

The generated file contains only real content. It always has the
`# <timestamp> -- <kind>` heading and the `**Agent**: <body>` line. The
optional pieces appear only when their flag is given, and are omitted
entirely (no empty header, no instructional prose) otherwise:
  --summary      rendered as a `> <summary>` blockquote under the heading
  --context      rendered as a `## Context` section
  --references   rendered as a `## References` section
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ASCII-only check utility (shared from the add-issue skill scripts)
_CHECK_ASCII_DIR = Path(__file__).resolve().parent.parent.parent / "add-issue" / "scripts"
sys.path.insert(0, str(_CHECK_ASCII_DIR))
from check_ascii_only import check_file

EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))
SKILL_ASSETS = Path(__file__).resolve().parent.parent / "assets"

TEMPLATE = SKILL_ASSETS / "comment.template.md"


def slugify(text: str) -> str:
    """Turn a short body snippet into a kebab-case filename slug."""
    out = []
    for ch in text.lower().strip():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "_", "-"):
            out.append("-")
    return "".join(out).strip("-")[:60] or "comment"


def ts_id(ts: str) -> str:
    """Returns the machine-safe 'YYYYMMDDTHHMM' portion used in filenames."""
    # Accept 'YYYY-MM-DDTHH:mm' or plain ISO; strip to safe filename chars.
    cleaned = re.sub(r"[^0-9A-Za-z]", "", ts)
    return cleaned[:13]  # YYYYMMDDTHHMM


def resolve_issue_dir(epic: str, issue: str) -> Path:
    epic_dir = EPICS_ROOT / epic
    if not epic_dir.is_dir():
        print(f"error: epic '{epic}' not found at {epic_dir}", file=sys.stderr)
        sys.exit(1)

    issue_dir = epic_dir / "issues" / issue
    if not (issue_dir / "ISSUE.md").exists():
        print(
            f"error: issue '{issue}' not found at {issue_dir} "
            f"(run the add-issue skill first)",
            file=sys.stderr,
        )
        sys.exit(1)
    return issue_dir


def _replace_once(text: str, old: str, new: str) -> str:
    """Replace `old` with `new`, requiring exactly one occurrence.

    The template is a fixed skeleton; if a pattern is missing or duplicated
    the asset has drifted from this script, so fail loudly instead of
    writing a malformed comment.
    """
    if text.count(old) != 1:
        print(
            "error: internal error: comment template changed; expected "
            f"exactly one occurrence of {old[:40]!r} "
            f"(found {text.count(old)})",
            file=sys.stderr,
        )
        sys.exit(1)
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a comment to an issue.")
    parser.add_argument("epic", help="Epic name (the issue must already exist)")
    parser.add_argument("issue", help="Issue name (kebab-case slug)")
    parser.add_argument("body", help="Comment body text")
    parser.add_argument(
        "--ts",
        help="ISO timestamp, e.g. '2026-07-23T09:30'. Defaults to now.",
    )
    parser.add_argument(
        "--kind",
        help="Optional comment kind heading, e.g. 'Decision', 'Update', 'Question'.",
    )
    parser.add_argument(
        "--summary",
        help="Optional one-line summary; rendered as a '> ' blockquote under the heading.",
    )
    parser.add_argument(
        "--context",
        help="Optional context text; rendered as a '## Context' section.",
    )
    parser.add_argument(
        "--references",
        help="Optional references text; rendered as a '## References' section.",
    )
    argv = parser.parse_args()

    now = datetime.now().replace(microsecond=0)
    ts_value = argv.ts or now.strftime("%Y-%m-%dT%H:%M")
    comments_dir = resolve_issue_dir(argv.epic, argv.issue) / "comments"
    comments_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{ts_id(ts_value)}-{slugify(argv.body)}.md"
    dest = comments_dir / fname
    if dest.exists():
        print(f"error: comment already exists at {dest}", file=sys.stderr)
        sys.exit(1)

    content = TEMPLATE.read_text()
    content = _replace_once(content, "{timestamp}", ts_value)
    content = _replace_once(content, "{kind}", argv.kind or "Comment")
    content = _replace_once(content, "{body}", argv.body.strip())

    # Optional sections: fill in when the flag is given, otherwise strip the
    # whole section (header, placeholder, and its surrounding blank line) so
    # the generated file contains only real content - no empty headers and
    # no instructional prose.
    summary = " ".join(argv.summary.split()) if argv.summary else ""
    if summary:
        content = _replace_once(content, "> {summary}", f"> {summary}")
    else:
        content = _replace_once(content, "\n> {summary}\n", "")

    context = (argv.context or "").strip()
    if context:
        content = _replace_once(content, "{context}", context)
    else:
        content = _replace_once(content, "\n## Context\n\n{context}\n", "")

    references = (argv.references or "").strip()
    if references:
        content = _replace_once(content, "{references}", references)
    else:
        content = _replace_once(content, "\n## References\n\n{references}\n", "")

    dest.write_text(content)

    # ASCII-only check: reject content with non-ASCII characters
    violations = check_file(str(dest))
    if violations:
        dest.unlink()  # remove the file - don't leave a corrupt comment
        for line_no, line_text in violations:
            print(f"error: non-ASCII at line {line_no}: {line_text}", file=sys.stderr)
        print("error: content contains non-ASCII characters (see above)", file=sys.stderr)
        sys.exit(1)

    print(f"Appended comment: {dest}")
    print(f"  issue: {comments_dir.parent}")
    return 0


if __name__ == "__main__":
    main()