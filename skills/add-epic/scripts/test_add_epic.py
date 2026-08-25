#!/usr/bin/env python3
"""Validation battery for the `add-epic` skill (E-tests).

Runs the real `add-epic.py` against a self-deleting scratch epic under
EPICS_ROOT and asserts the documented behaviour:

  E1  creates <epic>/EPIC.md from the template + an empty issues/ dir,
      with the Created/Last-updated dates filled in
  E2  rejects a duplicate epic name (exit 1)
  E3  slugifies the epic name to kebab-case (E3b documents a known
      deviation: consecutive separators are not collapsed, finding F4)
  E4  --workspace symlinks the epic's issues dir into an existing
      workspace; a missing workspace warns but still exits 0

Usage: python3 test_add_epic.py [--keep]
Exit code: 0 = all pass, 1 = at least one failure.
Stdlib only. The scratch epic and temp workspace are removed unless --keep.
"""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ADD_EPIC = SCRIPTS / "add-epic.py"
EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))
WS_ROOT = Path(os.environ.get("WS_ROOT", "/workspace"))

SCRATCH_EPIC = "test-scratch-add-epic"
SLUG_EPIC = "test-scratch-slug-epic"
WS_EPIC = "test-scratch-ws-epic"
WS_EPIC2 = "test-scratch-ws2-epic"
SCRATCH_WS = "tmp-test-ws-add-epic"

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


def cleanup(keep: bool) -> None:
    for name in (SCRATCH_EPIC, SLUG_EPIC, "test--scratch--slug-epic",
                 WS_EPIC, WS_EPIC2):
        d = EPICS_ROOT / name
        if not keep and d.exists():
            shutil.rmtree(d)
    ws = WS_ROOT / SCRATCH_WS
    if not keep and ws.exists():
        link = ws / "issues"
        if link.is_symlink() or link.exists():
            link.unlink()
        shutil.rmtree(ws, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true",
                    help="leave scratch artifacts for debugging")
    args = ap.parse_args()

    cleanup(False)  # clear stale state from an interrupted previous run

    try:
        # E1: creation from template
        r = run(ADD_EPIC, "Test Scratch Add Epic")
        epic_dir = EPICS_ROOT / SCRATCH_EPIC
        epic_md = epic_dir / "EPIC.md"
        issues_dir = epic_dir / "issues"
        today = date.today().isoformat()
        text = epic_md.read_text() if epic_md.is_file() else ""
        ok = (
            r.returncode == 0
            and epic_md.is_file()
            and issues_dir.is_dir()
            and not list(issues_dir.iterdir())
            and f"# EPIC: {SCRATCH_EPIC}" in text
            and "{YYYY-MM-DD}" not in text
            and today in text
        )
        check("E1 creates EPIC.md + empty issues/ from template (dates filled)", ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # E2: duplicate rejected
        r = run(ADD_EPIC, "Test Scratch Add Epic")
        check("E2 rejects duplicate epic name (exit 1)",
              r.returncode == 1 and "already exists" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # E3a: slugification with single separators
        r = run(ADD_EPIC, "Test Scratch Slug Epic")
        ok = r.returncode == 0 and (EPICS_ROOT / SLUG_EPIC).is_dir()
        check("E3a slugifies single-separator name to kebab-case dir", ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # E3b: consecutive separators. The script's slugify maps every
        # space/underscore/dash to '-' but does NOT collapse runs, so
        # "Test  Scratch--Slug_Epic!" becomes "test--scratch--slug-epic".
        # This deviates from the skill's documented `tr -cs 'a-z0-9' '-'`
        # (which collapses); recorded as finding F4 in the validation
        # report, asserted here as current behaviour.
        r = run(ADD_EPIC, "Test  Scratch--Slug_Epic!")
        ok = r.returncode == 0 and (EPICS_ROOT / "test--scratch--slug-epic").is_dir()
        check("E3b consecutive separators preserved (known deviation, F4)", ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")

        # E4a: --workspace symlink into an existing workspace
        ws = WS_ROOT / SCRATCH_WS
        ws.mkdir(parents=True, exist_ok=True)
        r = run(ADD_EPIC, "Test Scratch Ws Epic", "--workspace", SCRATCH_WS)
        link = ws / "issues"
        target_ok = (
            link.is_symlink()
            and link.resolve() == (EPICS_ROOT / WS_EPIC / "issues").resolve()
        )
        check("E4a --workspace symlinks issues into existing workspace",
              r.returncode == 0 and target_ok,
              f"rc={r.returncode} err={r.stderr.strip()[:200]} symlink={link.is_symlink()}")

        # E4b: missing workspace -> warning, no link, still exit 0
        r = run(ADD_EPIC, "Test Scratch Ws2 Epic", "--workspace", "no-such-ws-xyz")
        check("E4b missing workspace warns but exits 0 (no link)",
              r.returncode == 0 and "not found" in r.stderr,
              f"rc={r.returncode} err={r.stderr.strip()[:200]}")
    finally:
        cleanup(args.keep)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\ntest_add_epic: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("failed: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
