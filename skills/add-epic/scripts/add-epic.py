#!/usr/bin/env python3
"""Create a new epic directory under EPICS_ROOT/.

Usage:
    add-epic.py <epic-name>

Creates:
    EPICS_ROOT/<epic>/EPIC.md              (from the template)
    EPICS_ROOT/<epic>/issues/              (empty dir holding scoped issues)
"""
import argparse
import os
import sys
from pathlib import Path

# ASCII-only check utility (shared from the add-issue skill scripts)
_CHECK_ASCII_DIR = Path(__file__).resolve().parent.parent.parent / "add-issue" / "scripts"
sys.path.insert(0, str(_CHECK_ASCII_DIR))
from check_ascii_only import check_file

EPICS_ROOT = Path(os.environ.get("EPICS_ROOT", "/workspace/epics"))
SKILL_ASSETS = Path(__file__).resolve().parent.parent / "assets"

TEMPLATE = SKILL_ASSETS / "EPIC.template.md"


def slugify(name: str) -> str:
    """Convert a human-friendly name to a kebab-case slug."""
    out = []
    for ch in name.lower().strip():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "_", "-"):
            out.append("-")
    return "".join(out).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new epic.")
    parser.add_argument("name", help="Epic name (auto slugified)")
    args = parser.parse_args()

    epic = slugify(args.name)
    if not epic:
        print("error: epic name could not be slugified", file=sys.stderr)
        sys.exit(1)

    epic_dir = EPICS_ROOT / epic
    issues_dir = epic_dir / "issues"

    if epic_dir.exists():
        print(f"error: epic already exists at {epic_dir}", file=sys.stderr)
        sys.exit(1)

    epic_dir.mkdir(parents=True)
    issues_dir.mkdir(parents=True, exist_ok=True)

    # Write EPIC.md from template
    dest = epic_dir / "EPIC.md"
    template_text = TEMPLATE.read_text()
    today = __import__("datetime").date.today().isoformat()
    content = template_text.replace("{epic-name}", epic).replace("{YYYY-MM-DD}", today)
    dest.write_text(content)

    # ASCII-only check: reject content with non-ASCII characters
    violations = check_file(str(dest))
    if violations:
        dest.unlink()  # remove the file - don't leave a corrupt epic
        for line_no, line_text in violations:
            print(f"error: non-ASCII at line {line_no}: {line_text}", file=sys.stderr)
        print("error: content contains non-ASCII characters (see above)", file=sys.stderr)
        sys.exit(1)

    print(f"Created epic: {epic_dir}")
    print(f"  EPIC.md:   {dest}")
    print(f"  issues:    {issues_dir}")

    return 0


if __name__ == "__main__":
    main()