#!/usr/bin/env python3
"""Validation battery for the `add-issue` skill (I-tests).

Runs the real `add-issue.py` / `promote-issue.py` against a self-deleting
scratch epic under EPICS_ROOT and asserts the documented behaviour:

  I1  rejects an issue under a non-existent epic (exit 1)
  I2  creates the issue dir + ISSUE.md as status `draft`, with the
      {issue-id}/{epic-name} placeholders filled
  I3  rejects a duplicate issue name (exit 1)
  I4  promote-issue.py refuses an unauthored draft (exit 1) and lists
      what is missing (placeholder description, no checked AC,
      Criterion-1 placeholder, path/to/file)
  I5  an authored draft (real description, a checked AC, no placeholders)
      promotes to `open`
  I6  a freshly created issue has today's date in the Created/Updated
      metadata (no literal {YYYY-MM-DD} left)
  I7  --force promotes an unauthored draft (escape hatch documented)
  I8  --body writes the literal text verbatim, defaults to status `open`
      (no template stubs or placeholders)
  I9  --status open creates an issue directly as `open` (from template)

Usage: python3 test_add_issue.py [--keep]
Exit code: 0 = all pass, 1 = at least one failure.
Stdlib only. The scratch epic is removed unless --keep.
"""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ADD_ISSUE = SCRIPTS / "add-issue.py"
PROMOTE = SCRIPTS / "promote-issue.py"
ADD_EPIC = SCRIPTS.parent.parent / "add-epic" / "scripts" / "add-epic.py"
EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))

SCRATCH_EPIC = "test-scratch-add-issue"

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    line = f"  {'PASS' if ok else 'FAIL'}  {name}"
    if detail and not ok:
        line += f"  -- {detail}"
    print(line)


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )


def issue_md(slug: str) -> Path:
    return EPICS_ROOT / SCRATCH_EPIC / "issues" / slug / "ISSUE.md"


def status_of(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("- **Status:**"):
            return line.split("**Status:**", 1)[1].strip().strip("`")
    return "<no status line>"


def author(text: str, slug: str, title: str) -> str:
    """Turn the raw template into an authored draft (as a manager would)."""
    today = date.today().isoformat()
    t = text
    t = t.replace(f"# ISSUE {slug}: {{short title}}",
                  f"# ISSUE {slug}: {title}")
    t = t.replace(
        "> What is the problem or the ask? Background, motivation, expected outcome.\n"
        "> Enough detail for any agent to pick it up.",
        "Validation fixture: this draft must pass the promote-issue.py "
        "readiness gate once authored (real description, a checked "
        "acceptance criterion, no template placeholders).",
    )
    t = t.replace(
        "- [ ] Criterion 1\n- [ ] Criterion 2\n- [ ] Criterion 3",
        "- [x] Description is real text, not template filler\n"
        "- [x] At least one acceptance criterion is checked\n"
        "- [ ] Third criterion stays unchecked (allowed)",
    )
    t = t.replace("- `path/to/file`", "- `scripts/gate-check.py`")
    t = t.replace("- `{YYYY-MM-DD}` - comment", "")
    t = t.replace("- **Created:** `{YYYY-MM-DD}`",
                  f"- **Created:** `{today}`")
    t = t.replace("- **Updated:** `{YYYY-MM-DD}`",
                  f"- **Updated:** `{today}`")
    return t


def cleanup(keep: bool) -> None:
    d = EPICS_ROOT / SCRATCH_EPIC
    if not keep and d.exists():
        shutil.rmtree(d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true",
                    help="leave scratch artifacts for debugging")
    args = ap.parse_args()

    cleanup(False)  # clear stale state from an interrupted previous run

    try:
        r = run(ADD_EPIC, "Test Scratch Add Issue")
        if r.returncode != 0:
            print(f"setup failed: {r.stderr.strip()}")
            return 1

        # I1: missing epic
        r = run(ADD_ISSUE, "no-such-epic-xyz", "Whatever")
        check("I1 rejects issue under non-existent epic (exit 1)",
              r.returncode == 1 and "not found" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # I2: creation as draft
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Gate Check Issue")
        p = issue_md("gate-check-issue")
        text = p.read_text() if p.is_file() else ""
        ok = (
            r.returncode == 0
            and p.is_file()
            and status_of(text) == "draft"
            and "{issue-id}" not in text
            and "{epic-name}" not in text
            and f"- **Epic:** `{SCRATCH_EPIC}`" in text
        )
        check("I2 creates issue as `draft` with id/epic placeholders filled",
              ok, f"rc={r.returncode} err={r.stderr.strip()[:200]} status={status_of(text)}")

        # I3: duplicate
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Gate Check Issue")
        check("I3 rejects duplicate issue name (exit 1)",
              r.returncode == 1 and "already exists" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # I4: readiness gate refuses raw draft
        r = run(PROMOTE, SCRATCH_EPIC, "gate-check-issue")
        err = r.stderr
        ok = (
            r.returncode == 1
            and "Description" in err
            and "checked" in err
            and "Criterion 1" in err
            and "path/to/file" in err
        )
        check("I4 promote refuses unauthored draft and lists gaps", ok,
              f"rc={r.returncode} err={err.strip()[:300]}")

        # I5: authored draft promotes
        p.write_text(author(text, "gate-check-issue", "Gate check issue"))
        authored = p.read_text()
        leftover = [tok for tok in
                    ("What is the problem or the ask?", "Criterion 1",
                     "path/to/file") if tok in authored]
        r = run(PROMOTE, SCRATCH_EPIC, "gate-check-issue")
        ok = (
            not leftover
            and r.returncode == 0
            and status_of(p.read_text()) == "open"
        )
        check("I5 authored draft promotes to `open`", ok,
              f"rc={r.returncode} leftover={leftover} err={r.stderr.strip()[:200]}")

        # I6: fresh issue has real Created/Updated dates
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Fresh Date Check")
        p = issue_md("fresh-date-check")
        text = p.read_text() if p.is_file() else ""
        created = [l for l in text.splitlines() if l.startswith("- **Created:**")]
        updated = [l for l in text.splitlines() if l.startswith("- **Updated:**")]
        today = date.today().isoformat()
        ok = bool(created) and bool(updated) \
            and today in created[0] and today in updated[0]
        check("I6 fresh issue has today's date in Created/Updated metadata",
              ok,
              f"rc={r.returncode} created={created} updated={updated}")

        # I7: --force escape hatch
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Force Check")
        r = run(PROMOTE, SCRATCH_EPIC, "force-check", "--force")
        p = issue_md("force-check")
        ok = r.returncode == 0 and p.is_file() and status_of(p.read_text()) == "open"
        check("I7 --force promotes unauthored draft (escape hatch)", ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # I8: --body with literal markdown content
        slug = "body-test"
        body_content = (
            "# ISSUE body-test: Body Test\n\n"
            "## Metadata\n\n"
            "- **Status:** `open`\n"
            "- **Epic:** `test-scratch-add-issue`\n"
            "\n"
            "## Description\n\n"
            "This issue was created with --body, bypassing the template."
        )
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Body Test", "--body", body_content)
        p = issue_md(slug)
        text = p.read_text() if p.is_file() else ""
        # Check no template placeholder tokens leaked through
        template_leaks = [tok for tok in
                          ("What is the problem or the ask?", "Criterion 1",
                           "Criterion 2", "Criterion 3", "path/to/file",
                           "{YYYY-MM-DD}", "{issue-id}", "{epic-name}")
                          if tok in text]
        ok = (
            r.returncode == 0
            and p.is_file()
            and status_of(text) == "open"
            and not template_leaks
            and "Body Test" in text
            and "This issue was created with --body" in text
        )
        check("I8 --body writes verbatim content with default status `open`",
              ok,
              f"rc={r.returncode} status={status_of(text)} "
              f"template_leaks={template_leaks}")

        # I9: --status open (using template)
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Status Open Test", "--status", "open")
        p = issue_md("status-open-test")
        text = p.read_text() if p.is_file() else ""
        ok = (
            r.returncode == 0
            and p.is_file()
            and status_of(text) == "open"
            and "{issue-id}" not in text
            and "{epic-name}" not in text
        )
        check("I9 --status open creates issue directly as `open`",
              ok,
              f"rc={r.returncode} status={status_of(text)} "
              f"err={r.stderr.strip()[:200]}")
    finally:
        cleanup(args.keep)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\ntest_add_issue: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("failed: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
