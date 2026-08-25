#!/usr/bin/env python3
"""Validation battery for the issue lifecycle + tracker invariants (L-tests).

Runs the real skill scripts end-to-end against a self-deleting scratch epic
and additionally checks cross-cutting invariants of the tracker:

  L1  happy path: draft -> open (readiness gate) -> resolved
  L2  side state: open -> blocked -> open -> closed
  L10 lint-issue.py validation: linter passes on proper issues and fails on
      broken ones
  L3  status lines keep the `- **Status:** `<state>`` format, state in the
      allowed set
  L4  comment thread files are timestamp-named and chronologically ordered
  L5  (removed - no longer applicable after skills reorganisation)
  L6  discovery root resolves: .dsh/skills is a real directory under
      the workspace root (WS_ROOT) - single-root architecture after
      merging the tracker's .dsh into WS_ROOT/.dsh
  L7  git hygiene: the hosting repository at WS_ROOT tracks the tracker
      root (EPICS_ROOT); no child .git under EPICS_ROOT (untracked files
      under EPICS_ROOT are reported, not failed - mid-work is expected)
  L8  layout invariants: every issue dir has an ISSUE.md with exactly one
      Status line and a reserved `## Comments` section (checked over all
      epics, including the real ones)
  L9  ASCII-only rule: every .md file under every epic is free of non-ASCII
      characters (checked via check_ascii_only.py)

Usage: python3 test_lifecycle.py [--keep]
Exit code: 0 = all pass, 1 = at least one failure.
Stdlib only. The scratch epic is removed unless --keep.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPTS.parent.parent
ADD_EPIC = SKILLS_ROOT / "add-epic" / "scripts" / "add-epic.py"
ADD_ISSUE = SKILLS_ROOT / "add-issue" / "scripts" / "add-issue.py"
PROMOTE = SKILLS_ROOT / "add-issue" / "scripts" / "promote-issue.py"
ADD_COMMENT = SKILLS_ROOT / "add-comment" / "scripts" / "add-comment.py"
LINT_ISSUE = SKILLS_ROOT / "add-issue" / "scripts" / "lint-issue.py"

EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))
WS_ROOT = Path(os.environ.get("WS_ROOT", "/workspace"))
SCRATCH_EPIC = "test-scratch-lifecycle"
ALLOWED = {"draft", "open", "blocked", "resolved", "closed"}

# ASCII-only check utility (shared from the add-issue skill)
_CHECK_ASCII_DIR = SKILLS_ROOT / "add-issue" / "scripts"
sys.path.insert(0, str(_CHECK_ASCII_DIR))
from check_ascii_only import check_directory as _check_dir_ascii  # noqa: E402

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


def set_status(slug: str, status: str) -> None:
    p = issue_md(slug)
    lines = p.read_text().splitlines()
    today = date.today().isoformat()
    for i, line in enumerate(lines):
        if line.strip().startswith("- **Status:**"):
            lines[i] = f"- **Status:** `{status}`"
        elif line.startswith("- **Updated:**"):
            lines[i] = f"- **Updated:** `{today}`"
    p.write_text("\n".join(lines) + "\n")


def author(text: str, slug: str, title: str) -> str:
    today = date.today().isoformat()
    t = text
    t = t.replace(f"# ISSUE {slug}: {{short title}}",
                  f"# ISSUE {slug}: {title}")
    t = t.replace(
        "> What is the problem or the ask? Background, motivation, expected outcome.\n"
        "> Enough detail for any agent to pick it up.",
        "Validation fixture for the lifecycle battery.",
    )
    t = t.replace(
        "- [ ] Criterion 1\n- [ ] Criterion 2\n- [ ] Criterion 3",
        "- [x] Draft passes the readiness gate\n"
        "- [x] Lifecycle transitions are scriptable\n"
        "- [ ] Reserved for future use",
    )
    t = t.replace("- `path/to/file`", "- `scripts/lifecycle.py`")
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
        r = run(ADD_EPIC, "Test Scratch Lifecycle")
        if r.returncode != 0:
            print(f"setup failed: {r.stderr.strip()}")
            return 1

        # L1: happy path
        run(ADD_ISSUE, SCRATCH_EPIC, "Happy Path")
        p = issue_md("happy-path")
        assert status_of(p.read_text()) == "draft"
        p.write_text(author(p.read_text(), "happy-path", "Happy path"))
        r = run(PROMOTE, SCRATCH_EPIC, "happy-path")
        ok = r.returncode == 0 and status_of(p.read_text()) == "open"
        set_status("happy-path", "resolved")
        end_ok = status_of(p.read_text()) == "resolved"
        check("L1 draft -> open -> resolved",
              ok and end_ok, f"promote rc={r.returncode} "
              f"final={status_of(p.read_text())}")

        # L2: blocked side state
        run(ADD_ISSUE, SCRATCH_EPIC, "Blocked Path")
        p = issue_md("blocked-path")
        p.write_text(author(p.read_text(), "blocked-path", "Blocked path"))
        r = run(PROMOTE, SCRATCH_EPIC, "blocked-path")
        set_status("blocked-path", "blocked")
        mid_ok = status_of(p.read_text()) == "blocked"
        set_status("blocked-path", "open")
        set_status("blocked-path", "closed")
        end_ok = status_of(p.read_text()) == "closed"
        check("L2 open -> blocked -> open -> closed",
              r.returncode == 0 and mid_ok and end_ok,
              f"final={status_of(p.read_text())}")

        # L3: status line format
        bad = []
        for slug in ("happy-path", "blocked-path"):
            text = issue_md(slug).read_text()
            lines = [l for l in text.splitlines()
                     if l.strip().startswith("- **Status:**")]
            if len(lines) != 1:
                bad.append(f"{slug}: {len(lines)} status lines")
                continue
            m = re.fullmatch(r"- \*\*Status:\*\* `([a-z_]+)`", lines[0].strip())
            if not m or m.group(1) not in ALLOWED:
                bad.append(f"{slug}: {lines[0]!r}")
        check("L3 status line format + allowed state set", not bad, "; ".join(bad))

        # L4: comment thread naming + chronology
        run(ADD_COMMENT, SCRATCH_EPIC, "happy-path",
            "Lifecycle battery first comment", "--ts", "2026-08-16T08:00")
        run(ADD_COMMENT, SCRATCH_EPIC, "happy-path",
            "Lifecycle battery second comment", "--ts", "2026-08-16T08:05")
        cd = issue_md("happy-path").parent / "comments"
        files = sorted(cd.glob("*.md"))
        prefixes = [f.name[:13] for f in files]
        ok = (
            len(files) == 2
            and prefixes == ["20260816T0800", "20260816T0805"]
            and all(re.search(r"# \d{4}-\d{2}-\d{2}T\d{2}:\d{2} -- ",
                             f.read_text()) for f in files)
        )
        check("L4 comment files timestamp-named and chronological", ok,
              f"prefixes={prefixes}")

        # L10: lint-issue.py validation
        lint_failed = False
        lint_detail = []
        # (a) Create a scratch issue for lint testing
        run(ADD_ISSUE, SCRATCH_EPIC, "Lint Test")
        lp = issue_md("lint-test")
        text = author(lp.read_text(), "lint-test", "Lint test")
        # Remove remaining placeholder tokens the linter checks. Placeholder
        # comment/resolution dated lines are removed (no real comments/PRs on
        # the scratch issue) rather than given a date, so the linter does not
        # require a matching comments/ file.
        text = "\n".join(
            l for l in text.splitlines()
            if "{YYYY-MM-DD}" not in l
        )
        for token in ("{P0 | P1 | P2 | P3}", "{epic-name}", "{issue-id}",
                      "{resolution}", "{@handle}", "{optional}",
                      "{workspace-or-none}",
                      "{fixed | wontfix | duplicate | by-design | superseded}"):
            text = text.replace(token, "")
        lp.write_text(text)
        r = run(PROMOTE, SCRATCH_EPIC, "lint-test")
        if r.returncode != 0:
            lint_failed = True
            lint_detail.append(f"promote rc={r.returncode}")
        # (b) Run linter - a proper issue should pass
        if not lint_failed:
            r = run(LINT_ISSUE, SCRATCH_EPIC, "lint-test")
            if r.returncode != 0:
                lint_failed = True
                lint_detail.append(f"lint on clean issue rc={r.returncode} "
                                   f"stderr={r.stderr.strip()}")
        # (c) Deliberately break the status line
        if not lint_failed:
            text = lp.read_text()
            text = text.replace("- **Status:** `open`", "- **Status:** `invalid`")
            lp.write_text(text)
            r = run(LINT_ISSUE, SCRATCH_EPIC, "lint-test")
            if r.returncode != 1:
                lint_failed = True
                lint_detail.append(f"lint on broken issue: expected rc=1, got rc={r.returncode}")
            # (d) Verify the linter reported the invalid status
            if "invalid" not in r.stderr and "invalid" not in r.stdout:
                lint_failed = True
                lint_detail.append("lint did not flag 'invalid' status")
        # (e) Restore the issue
        if not lint_failed:
            text = lp.read_text()
            text = text.replace("- **Status:** `invalid`", "- **Status:** `open`")
            lp.write_text(text)
        check("L10 lint-issue.py validation", not lint_failed, "; ".join(lint_detail))

        # L6: discovery root exists (single root at WS_ROOT/.dsh/skills)
        ok = (WS_ROOT / ".dsh" / "skills").is_dir()
        check("L6 .dsh/skills discovery root exists under WS_ROOT",
              ok,
              f"ws.dsh={(WS_ROOT / '.dsh' / 'skills').exists()}")

        # L7: git hygiene (hosting repository at WS_ROOT tracks EPICS_ROOT)
        child_gits = [str(p) for p in EPICS_ROOT.rglob(".git")]
        try:
            epics_rel = EPICS_ROOT.relative_to(WS_ROOT)
        except ValueError:
            epics_rel = None
        repo = subprocess.run(
            ["git", "-C", str(WS_ROOT), "rev-parse", "--git-dir"],
            capture_output=True, text=True)
        tracked = subprocess.run(
            ["git", "-C", str(WS_ROOT), "ls-files", "--",
             str(epics_rel / "AGENTS.md") if epics_rel is not None else ""],
            capture_output=True, text=True)
        dirty = subprocess.run(
            ["git", "-C", str(WS_ROOT), "status", "--porcelain", "--",
             str(epics_rel) if epics_rel is not None else ""],
            capture_output=True, text=True)
        untracked_n = sum(1 for l in dirty.stdout.splitlines() if l.startswith("??"))
        ok = (
            not child_gits
            and epics_rel is not None
            and repo.returncode == 0
            and tracked.stdout.strip() == str(epics_rel / "AGENTS.md")
        )
        detail = f"child_gits={child_gits} repo_rc={repo.returncode} " \
                 f"untracked_under_epics={untracked_n}"
        check("L7 git hygiene (hosting repo at WS_ROOT tracks the tracker "
              "root; no child .git under EPICS_ROOT)",
              ok, detail)
        if untracked_n:
            print(f"        (note: {untracked_n} untracked path(s) under "
                  f"{epics_rel}/ - expected mid-work, not a failure)")

        # L8: layout invariants over ALL epics
        bad = []
        for epic_dir in sorted(EPICS_ROOT.iterdir()):
            if not epic_dir.is_dir() or epic_dir.name == "skills":
                continue
            issues_dir = epic_dir / "issues"
            if not issues_dir.is_dir():
                bad.append(f"{epic_dir.name}: no issues/ dir")
                continue
            for issue_dir in sorted(issues_dir.iterdir()):
                imd = issue_dir / "ISSUE.md"
                if not imd.is_file():
                    bad.append(f"{epic_dir.name}/{issue_dir.name}: no ISSUE.md")
                    continue
                text = imd.read_text()
                n_status = sum(1 for l in text.splitlines()
                               if l.strip().startswith("- **Status:**"))
                if n_status != 1:
                    bad.append(f"{epic_dir.name}/{issue_dir.name}: "
                               f"{n_status} status lines")
                if "## Comments" not in text:
                    bad.append(f"{epic_dir.name}/{issue_dir.name}: "
                               f"missing reserved ## Comments section")
        check("L8 layout invariants hold for every epic/issue", not bad,
              "; ".join(bad[:5]))

        # L9: ASCII-only rule over ALL epics
        ascii_bad = []
        for epic_dir in sorted(EPICS_ROOT.iterdir()):
            if not epic_dir.is_dir() or epic_dir.name == "skills":
                continue
            violations = _check_dir_ascii(str(epic_dir))
            for filepath, file_violations in sorted(violations.items()):
                rel = Path(filepath).relative_to(EPICS_ROOT)
                for line_no, _ in file_violations[:3]:  # report up to 3 lines per file
                    ascii_bad.append(f"{rel}:{line_no}")
        check("L9 all .md files under every epic are ASCII-only",
              not ascii_bad, "; ".join(ascii_bad[:10]))
    finally:
        cleanup(args.keep)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\ntest_lifecycle: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
