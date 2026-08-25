#!/usr/bin/env python3
"""Create a new issue directory under an epic's issues/ dir.

Usage:
    add-issue.py <epic> <issue-name>                              (template-based, draft)
    add-issue.py <epic> <issue-name> --body <text>                (one-shot, from literal text)
    add-issue.py <epic> <issue-name> --status open                (create directly as open)
    add-issue.py <epic> <issue-name> --promote                    (create draft then promote)
    add-issue.py <epic> <issue-name> --body <text> --status open  (one-shot as open)

Also supports operating on an *existing* issue:
    add-issue.py <epic> <issue-name> --promote                    (readiness check + status flip)

Creates:
    EPICS_ROOT/<epic>/issues/<issue>/ISSUE.md   (from the template or --body)
    and returns the issue id (kebab-case slug).

Requires the epic to already exist (see the add-epic skill).
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

# ASCII-only check utility (ships in this same scripts/ directory)
from check_ascii_only import check_file

EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))
SKILL_ASSETS = Path(__file__).resolve().parent.parent / "assets"

TEMPLATE = SKILL_ASSETS / "ISSUE.template.md"

PLACEHOLDER_TOKENS = [
    "What is the problem or the ask?",
    "- [ ] Criterion 1",
    "path/to/file",
]


def slugify(name: str) -> str:
    """Convert a human-friendly name to a kebab-case slug."""
    out = []
    for ch in name.lower().strip():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "_", "-"):
            out.append("-")
    return "".join(out).strip("-")


def _readiness_failures(text: str) -> list[str]:
    """Return reasons the issue is not ready to be opened (same logic as promote-issue.py)."""
    failures: list[str] = []

    desc_match = re.search(r"##\s*Description\s*(.*?)(?=\n##\s|\Z)", text, re.S | re.I)
    desc = desc_match.group(1).strip() if desc_match else ""
    if not desc:
        failures.append("Description section is empty")
    elif "what is the problem or the ask?" in desc.casefold():
        failures.append("Description still holds template placeholder text")

    if not re.findall(r"-\s*\[x\]", text, re.I):
        failures.append("no checked Acceptance Criteria ([x]) found")

    for token in PLACEHOLDER_TOKENS:
        if token in text:
            failures.append(f"unresolved placeholder '{token}' still present")

    return failures


def _set_status(p: Path, status: str) -> None:
    """Replace the status line in an ISSUE.md file."""
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("- **Status:**"):
            lines[i] = f"- **Status:** `{status}`"
            break
    p.write_text("\n".join(lines) + "\n")


def _get_current_status(p: Path) -> str | None:
    """Read the current status value from an ISSUE.md file."""
    text = p.read_text()
    for line in text.splitlines():
        if line.strip().startswith("- **Status:**"):
            m = re.search(r"`([^`]+)`", line)
            return m.group(1) if m else None
    return None


def _run_linter(issue_dir: Path, epic: str, issue: str) -> None:
    """If lint-issue.py exists alongside add-issue.py, run it on the target issue.

    Prints a warning if the linter exits non-zero but does NOT abort.
    """
    linter_path = Path(__file__).resolve().parent / "lint-issue.py"
    if not linter_path.exists():
        return

    import subprocess
    result = subprocess.run(
        [sys.executable, str(linter_path), epic, issue],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(
            f"  warning: lint-issue.py reported violations "
            f"(exit {result.returncode})",
            file=sys.stderr,
        )
        stderr_clean = result.stderr.strip()
        if stderr_clean:
            for line in stderr_clean.splitlines():
                print(f"    lint: {line}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or promote an issue.")

    # Positional args
    parser.add_argument("epic", help="Epic name (must already exist)")
    parser.add_argument("name", help="Issue name (auto-slugified)")

    # New flags
    parser.add_argument("--body", help="Write ISSUE.md directly from this text (skip template)")
    parser.add_argument(
        "--status", choices=["draft", "open"], default=None,
        help="Initial status (default: draft when creating from template, "
             "or open when --body is given)",
    )
    parser.add_argument(
        "--promote", action="store_true",
        help="Run readiness check and flip status from draft to open",
    )

    # Kept for backward compat (promote-issue.py forwarded these; ignored but accepted)
    parser.add_argument("--workspace", help=argparse.SUPPRESS)
    parser.add_argument(
        "--force", action="store_true",
        help="Force creation even if issue already exists (ignored for new issues)",
    )

    argv = parser.parse_args()

    # --body and --promote are mutually exclusive: body content is authored
    # by definition, so there is nothing for --promote to check.
    if argv.body and argv.promote:
        print(
            "error: --body and --promote are mutually exclusive "
            "(body content is already authored; use --status open instead)",
            file=sys.stderr,
        )
        sys.exit(1)

    epic = slugify(argv.epic)
    epic_dir = EPICS_ROOT / epic
    if not epic_dir.is_dir():
        print(f"error: epic '{argv.epic}' not found at {epic_dir}", file=sys.stderr)
        sys.exit(1)

    issue = slugify(argv.name)
    if not issue:
        print("error: issue name could not be slugified", file=sys.stderr)
        sys.exit(1)

    issues_dir = epic_dir / "issues"
    issue_dir = issues_dir / issue
    dest = issue_dir / "ISSUE.md"
    is_new = not issue_dir.exists()

    # --- Determine status ------------------------------------------------
    # If --status was explicitly given, use it; otherwise default to draft
    # for template-based creation and open for --body creation.
    if argv.status is not None:
        status = argv.status
    elif argv.body is not None:
        status = "open"
    else:
        status = "draft"

    # --- Mode: create a new issue ----------------------------------------
    if is_new:
        issue_dir.mkdir(parents=True)

        if argv.body is not None:
            # One-shot: write the literal body directly
            content = argv.body
        else:
            # Template-based: load the template and fill placeholders
            today = date.today().isoformat()
            content = (
                TEMPLATE.read_text()
                .replace("{issue-id}", issue)
                .replace("{epic-name}", epic)
                .replace("- **Created:** `{YYYY-MM-DD}`", f"- **Created:** `{today}`")
                .replace("- **Updated:** `{YYYY-MM-DD}`", f"- **Updated:** `{today}`")
            )

        # If status != draft, fix the template status line
        # The template has "draft" as default; if we want "open", replace it.
        if status != "draft" and argv.body is None:
            # Template has `- **Status:** `draft`` - only replace in template output
            content = content.replace(
                "- **Status:** `draft`",
                f"- **Status:** `{status}`",
            )

        dest.write_text(content)

        # ASCII-only check: reject content with non-ASCII characters
        violations = check_file(str(dest))
        if violations:
            dest.unlink()  # remove the file - don't leave a corrupt issue
            for line_no, line_text in violations:
                print(f"error: non-ASCII at line {line_no}: {line_text}", file=sys.stderr)
            print("error: content contains non-ASCII characters (see above)", file=sys.stderr)
            sys.exit(1)

        print(f"Created issue: {issue_dir}")
        print(f"  ISSUE.md: {dest}")
        if status == "open":
            print(f"  status:   open")
        else:
            print(f"  status:   draft (use --status open to create directly as open, or --promote to promote)")
        print(f"  epic:     {issue_dir.parent.parent}")

        # If --promote was also given, run the readiness check on the just-written issue
        if argv.promote:
            print()
            # Delegate to the promote logic below
            pass  # handled by the --promote block below
        else:
            # Lint after write
            _run_linter(issue_dir, epic, issue)
            return 0

    # --- Mode: handle --promote (either after creation above, or on existing issue) ----
    if argv.promote:
        if not dest.exists():
            print(f"error: ISSUE.md not found at {dest}", file=sys.stderr)
            sys.exit(1)

        text = dest.read_text()

        if argv.force:
            _set_status(dest, "open")
            print(f"Promoted {issue} -> open (forced)")
            _run_linter(issue_dir, epic, issue)
            return 0

        # Only allow promotion from draft
        current_status = _get_current_status(dest)
        if current_status is not None and current_status != "draft" and not is_new:
            if current_status == "open":
                print(f"issue '{issue}' is already open (no change needed)", file=sys.stderr)
                return 0
            else:
                print(
                    f"error: issue '{issue}' has status '{current_status}', "
                    f"can only promote from 'draft'",
                    file=sys.stderr,
                )
                sys.exit(1)

        failures = _readiness_failures(text)
        if failures:
            print(f"issue '{issue}' NOT ready:", file=sys.stderr)
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
            print("fix these, then re-run with --promote (or pass --force).",
                  file=sys.stderr)
            sys.exit(1)

        # Ensure the status line is set to 'open' even if it was already draft
        _set_status(dest, "open")
        if is_new:
            print(f"Created and promoted {issue} -> open")
        else:
            print(f"Promoted {issue} -> open")

        _run_linter(issue_dir, epic, issue)
        return 0

    # --- Existing issue but no --promote: nothing to do -----------------
    if not is_new:
        print(f"error: issue already exists at {issue_dir}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    main()
