#!/usr/bin/env python3
"""Validation battery for the `add-comment` skill (C-tests).

Runs the real `add-comment.py` against a self-deleting scratch epic/issue
under EPICS_ROOT and asserts the documented behaviour:

  C1  rejects a comment for a non-existent issue (exit 1)
  C2  appends a comment file named <YYYYMMDDTHHMM>-<slug>.md, with the
      anonymous `**Agent**` tag, the --kind heading, and no human/agent
      identity leaked into the file
  C3  the thread stays chronological (newer timestamp sorts later)
  C4  re-adding the same comment in the same minute is rejected (exit 1)
  C5  generated comments contain no unfilled template boilerplate
  C6  the default kind is "Comment" when --kind is omitted

Usage: python3 test_add_comment.py [--keep]
Exit code: 0 = all pass, 1 = at least one failure.
Stdlib only. The scratch epic is removed unless --keep.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ADD_COMMENT = SCRIPTS / "add-comment.py"
ADD_EPIC = SCRIPTS.parent.parent / "add-epic" / "scripts" / "add-epic.py"
ADD_ISSUE = SCRIPTS.parent.parent / "add-issue" / "scripts" / "add-issue.py"
EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))

SCRATCH_EPIC = "test-scratch-add-comment"
ISSUE = "comment-target"

BOILERPLATE = (
    "Short, one-line summary of this comment",
    "What prompted this comment?",
    "Link or note relevant files",
)

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


def comments_dir() -> Path:
    return EPICS_ROOT / SCRATCH_EPIC / "issues" / ISSUE / "comments"


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
        r = run(ADD_EPIC, "Test Scratch Add Comment")
        if r.returncode != 0:
            print(f"setup failed: {r.stderr.strip()}")
            return 1
        r = run(ADD_ISSUE, SCRATCH_EPIC, "Comment Target")
        if r.returncode != 0:
            print(f"setup failed: {r.stderr.strip()}")
            return 1

        # C1: missing issue
        r = run(ADD_COMMENT, SCRATCH_EPIC, "no-such-issue", "Body text")
        check("C1 rejects comment for non-existent issue (exit 1)",
              r.returncode == 1 and "not found" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # C2: basic append (fixed timestamp sorts before C3 09:30 and C6 10:00)
        r = run(ADD_COMMENT, SCRATCH_EPIC, ISSUE,
                "First validation comment about the tracker",
                "--kind", "Update",
                "--ts", "2026-08-16T08:00")
        cd = comments_dir()
        files = sorted(cd.glob("*.md")) if cd.is_dir() else []
        f = files[0] if files else None
        text = f.read_text() if f else ""
        ok = (
            r.returncode == 0
            and f is not None
            and re.fullmatch(r"\d{8}T\d{4}-[a-z0-9-]+\.md", f.name) is not None
            and "First validation comment about the tracker" in text
            and "**Agent**" in text
            and "-- Update" in text
            and "**@" not in text
            and "openhands" not in text.lower()
            and "deepseek" not in text.lower()
        )
        check("C2 appends <ts>-<slug>.md with **Agent** tag, --kind, no identity",
              ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]} files={[x.name for x in files]}")

        # C3: chronology with an explicit later timestamp
        r = run(ADD_COMMENT, SCRATCH_EPIC, ISSUE,
                "Second validation comment later in the day",
                "--ts", "2026-08-16T09:30")
        files = sorted(cd.glob("*.md")) if cd.is_dir() else []
        ts_prefixes = [p.name[:13] for p in files]
        ok = (
            r.returncode == 0
            and len(files) == 2
            and ts_prefixes == sorted(ts_prefixes)
            and ts_prefixes[-1] == "20260816T0930"
        )
        check("C3 thread stays chronological (newer timestamp sorts last)",
              ok, f"rc={r.returncode} prefixes={ts_prefixes}")

        # C4: same minute + same body rejected
        r = run(ADD_COMMENT, SCRATCH_EPIC, ISSUE,
                "Second validation comment later in the day",
                "--ts", "2026-08-16T09:30")
        check("C4 duplicate comment (same minute, same body) rejected (exit 1)",
              r.returncode == 1 and "already exists" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # C5: no template boilerplate leaks into generated comments
        bad = []
        for p in sorted(cd.glob("*.md")):
            text = p.read_text()
            leaked = [b for b in BOILERPLATE if b in text]
            if leaked:
                bad.append(f"{p.name}: {leaked}")
        check("C5 generated comments contain no template boilerplate",
              not bad, "; ".join(bad))

        # C6: default kind
        r = run(ADD_COMMENT, SCRATCH_EPIC, ISSUE,
                "Third validation comment default kind",
                "--ts", "2026-08-16T10:00")
        files = sorted(cd.glob("*.md"))
        newest = files[-1] if files else None
        text = newest.read_text() if newest else ""
        ok = r.returncode == 0 and "-- Comment" in text
        check("C6 default kind is 'Comment'", ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")
    finally:
        cleanup(args.keep)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\ntest_add_comment: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("failed: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
