#!/usr/bin/env python3
"""Validate formatting invariants of ISSUE.md files created by add-issue.py.

Usage:
    lint-issue.py <epic> <issue>              # check one issue
    lint-issue.py --all                       # check every issue under EPICS_ROOT
    lint-issue.py <epic> <issue> --fix        # attempt auto-fix of violations
    lint-issue.py --all --fix                 # fix all issues

Exits 0 if clean, 1 with diagnostics otherwise.

Checks:
  - status: exactly one status line, value in {draft,open,blocked,resolved,closed}
  - sections: must contain ## Description, ## Acceptance Criteria, ## Comments, ## Resolution & PRs
  - no placeholders: certain template literal strings must be absent
  - dates: - **Created:** and - **Updated:** have valid YYYY-MM-DD
  - comments: each `- YYYY-MM-DD` line under ## Comments has a matching file in comments/
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))

ALLOWED_STATUSES = {"draft", "open", "blocked", "resolved", "closed"}

REQUIRED_SECTIONS = [
    "## Description",
    "## Acceptance Criteria",
    "## Comments",
    "## Resolution & PRs",
]

PLACEHOLDER_TOKENS = [
    "{YYYY-MM-DD}",
    "{epic-name}",
    "{issue-id}",
    "path/to/file",
    "{short title}",
    "P0 | P1 | P2 | P3",
]

DATE_LINE_PREFIXES = ["- **Created:**", "- **Updated:**"]

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def _find_issues() -> list[Path]:
    """Return list of ISSUE.md paths under EPICS_ROOT."""
    return sorted(EPICS_ROOT.glob("*/issues/*/ISSUE.md"))


def _rel_path(p: Path) -> str:
    """Return a path relative to EPICS_ROOT for display."""
    try:
        return str(p.relative_to(EPICS_ROOT))
    except ValueError:
        return str(p)


def _epic_issue_from_path(p: Path) -> tuple[str, str]:
    """Given an ISSUE.md path, return (epic, issue)."""
    parts = p.relative_to(EPICS_ROOT).parts
    return parts[0], parts[2]  # epic/issues/issue/ISSUE.md -> parts[0], parts[2]


def _is_comment_date_line(line: str) -> bool:
    """Check if a line looks like a comment entry: `- YYYY-MM-DD ...`."""
    stripped = line.strip()
    return bool(re.match(r"^- `\d{4}-\d{2}-\d{2}`", stripped))


def _fenced_code_lines(lines: list[str]) -> set[int]:
    """Return the set of 0-based line numbers that fall inside fenced code blocks.

    A fenced code block starts with a line whose first non-space chars are
    ``` (three or more backticks) or ~~~ (three or more tildes) and ends
    at the next matching fence. Nested fences are not valid Markdown, so
    a simple toggle works.
    """
    inside = False
    fenced: set[int] = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside = not inside
            continue
        if inside:
            fenced.add(i)
    return fenced


def check_issue(p: Path) -> list[str]:
    """Return a list of violation strings for a single ISSUE.md file.

    Each violation is formatted as:
        <epic>/issues/<issue>/ISSUE.md: <check-name>: <detail>
    """
    violations: list[str] = []
    epic, issue = _epic_issue_from_path(p)
    prefix = f"{epic}/issues/{issue}/ISSUE.md"
    text = p.read_text()
    lines = text.splitlines()
    fenced_lines = _fenced_code_lines(lines)

    # --- 1. Status check ------------------------------------------------
    status_lines = [l for l in lines if l.strip().startswith("- **Status:**")]
    if len(status_lines) == 0:
        violations.append(f"{prefix}: status: no status line found")
    elif len(status_lines) > 1:
        violations.append(f"{prefix}: status: multiple status lines found ({len(status_lines)})")
    else:
        # Extract the status value: "- **Status:** `draft`"
        m = re.search(r"`([^`]+)`", status_lines[0])
        status_val = m.group(1) if m else ""
        if status_val not in ALLOWED_STATUSES:
            violations.append(
                f"{prefix}: status: invalid status '{status_val}' "
                f"(allowed: {', '.join(sorted(ALLOWED_STATUSES))})"
            )

    # --- 2. Sections check ----------------------------------------------
    for section in REQUIRED_SECTIONS:
        if section not in text:
            violations.append(f"{prefix}: sections: missing '{section}' heading")

    # -- 3. Placeholder check (skip fenced code blocks) -----------------
    for token in PLACEHOLDER_TOKENS:
        # Check each line individually; flag tokens on every non-fenced line
        for i, line in enumerate(lines):
            if i in fenced_lines:
                continue
            if token in line:
                violations.append(
                    f"{prefix}: placeholders: unresolved token '{token}' still present"
                )

    # -- 4. Date validity ----------------------------------------------
    for prefix_line in DATE_LINE_PREFIXES:
        matching = [l for l in lines if l.strip().startswith(prefix_line)]
        if not matching:
            violations.append(f"{prefix}: dates: missing '{prefix_line}' line")
        elif ISO_DATE_RE.search(matching[0]) is None:
            violations.append(f"{prefix}: dates: '{prefix_line}' has no valid ISO date")

    # -- 5. Comment references ------------------------------------------
    # Find lines in ## Comments section that reference a date
    comments_section = False
    comment_dates: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "## Comments":
            comments_section = True
            continue
        if comments_section:
            if stripped.startswith("## "):
                break
            if _is_comment_date_line(stripped):
                m = ISO_DATE_RE.search(stripped)
                if m:
                    comment_dates.append(m.group(1))

    if comment_dates:
        issue_dir = p.parent
        comments_dir = issue_dir / "comments"
        if not comments_dir.is_dir():
            violations.append(
                f"{prefix}: comments: comments/ directory missing "
                f"(referenced by {len(comment_dates)} comment(s))"
            )
        else:
            for cd in comment_dates:
                # Accept any .md file in comments/ that matches the date
                matched = list(comments_dir.glob(f"{cd}.md"))
                if not matched:
                    violations.append(
                        f"{prefix}: comments: no comment file for `{cd}` in comments/"
                    )

    return violations


def fix_issue(p: Path) -> list[str]:
    """Attempt auto-fix of violations in an ISSUE.md file.

    Returns a list of fix descriptions applied. Only applies safe fixes:
    - Removes placeholder lines
    - Normalises dates to today

    Returns empty list if no fix was needed/applied.  Placeholder tokens
    inside fenced code blocks are left untouched.
    """
    fixes: list[str] = []
    text = p.read_text()
    original = text
    lines = text.splitlines()
    fenced_lines = _fenced_code_lines(lines)

    # Remove placeholder tokens (only from non-fenced lines)
    for token in PLACEHOLDER_TOKENS:
        for i, line in enumerate(lines):
            if i in fenced_lines:
                continue
            if token in line:
                lines[i] = line.replace(token, "")
                fixes.append(f"removed placeholder token '{token}'")

    text = "\n".join(lines)

    # Fix dates
    today = date.today().isoformat()
    for prefix_line in DATE_LINE_PREFIXES:
        pattern = re.escape(prefix_line) + r"\s*`\d{4}-\d{2}-\d{2}`"
        replacement = f"{prefix_line} `{today}`"
        if re.search(pattern, text):
            text = re.sub(pattern, replacement, text)

    if text != original:
        p.write_text(text)
        fixes.append("normalised dates to today")

    return fixes


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint ISSUE.md formatting invariants.")
    parser.add_argument("epic", nargs="?", help="Epic name")
    parser.add_argument("issue", nargs="?", help="Issue name")
    parser.add_argument("--all", action="store_true", help="Check every issue in every epic")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-fix of violations")
    args = parser.parse_args()

    if args.all:
        issue_paths = _find_issues()
        if not issue_paths:
            print(f"No issues found under {EPICS_ROOT}.", file=sys.stderr)
            return 0
    elif args.epic and args.issue:
        issue_path = EPICS_ROOT / args.epic / "issues" / args.issue / "ISSUE.md"
        if not issue_path.exists():
            print(f"error: {issue_path} not found", file=sys.stderr)
            return 1
        issue_paths = [issue_path]
    else:
        parser.print_usage()
        print("error: specify <epic> <issue> or --all", file=sys.stderr)
        return 1

    any_violations = False
    for p in issue_paths:
        # Auto-fix first if requested
        if args.fix:
            applied = fix_issue(p)
            if applied:
                for fix in applied:
                    print(f"{_rel_path(p)}: fix: {fix}")

        violations = check_issue(p)
        if violations:
            any_violations = True
            for v in violations:
                print(v, file=sys.stderr)

    return 1 if any_violations else 0


if __name__ == "__main__":
    sys.exit(main())
