#!/usr/bin/env python3
"""Wrapper for add-issue.py --promote (backward compatibility).

Kept so existing callers and the test suite continue to work unchanged.

Usage:
    promote-issue.py <epic> <issue> [--force] [--workspace <ws>]

This forwards the call to add-issue.py with --promote (and --force / --workspace
if given). See add-issue.py for the full description.
"""
import sys
from pathlib import Path

# Resolve add-issue.py alongside this wrapper
SCRIPTS_DIR = Path(__file__).resolve().parent
ADD_ISSUE = SCRIPTS_DIR / "add-issue.py"


def main() -> int:
    # Forward all args to add-issue.py, injecting --promote
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    if "--promote" not in args:
        args.append("--promote")
    # Re-invoke via subprocess (clean separation, keeps exact behaviour)
    import subprocess
    cmd = [sys.executable, str(ADD_ISSUE)] + args
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
