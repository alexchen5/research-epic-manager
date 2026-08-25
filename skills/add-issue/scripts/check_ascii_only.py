#!/usr/bin/env python3
"""check_ascii_only.py -- Check whether text files contain only ASCII characters.

This script can be used both as a CLI tool and as a Python library.

Usage (CLI):
    python3 check_ascii_only.py file1.md file2.md ...
    python3 check_ascii_only.py --dir <directory>   # recursively scan *.md files

Usage (library):
    from check_ascii_only import check_file, check_files, check_directory
    violations = check_file("path/to/file.md")
    results = check_files(["file1.md", "file2.md"])
    results = check_directory("path/to/dir")
"""

import argparse
import os
import sys


def check_file(path: str) -> list[tuple[int, str]]:
    """Check a single file for lines containing non-ASCII characters.

    Args:
        path: Path to the file to check.

    Returns:
        List of (line_number, line_content) tuples for lines that contain
        at least one non-ASCII character (ord(c) > 127). Returns an empty
        list if the file is clean.

    The line_number is 1-based. The line_content is the raw line as read
    from the file (including any trailing newline).
    """
    violations: list[tuple[int, str]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                for ch in line:
                    if ord(ch) > 127:
                        violations.append((line_no, line.rstrip("\n")))
                        break
    except FileNotFoundError:
        print(f"Warning: file not found -- {path}", file=sys.stderr)
        return violations
    except PermissionError:
        print(f"Warning: permission denied -- {path}", file=sys.stderr)
        return violations
    except UnicodeDecodeError:
        print(f"Warning: cannot decode as UTF-8 (binary?) -- {path}", file=sys.stderr)
        return violations
    except IsADirectoryError:
        print(f"Warning: expected a file, got a directory -- {path}", file=sys.stderr)
        return violations
    except OSError as exc:
        print(f"Warning: cannot read file -- {path} ({exc})", file=sys.stderr)
        return violations
    return violations


def check_files(paths: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Check multiple files for non-ASCII characters.

    Args:
        paths: List of paths to files to check.

    Returns:
        Dictionary mapping each file path to its list of (line_number, line_content)
        violations. Files that cannot be read produce an empty list entry and a
        warning on stderr.
    """
    results: dict[str, list[tuple[int, str]]] = {}
    for path in paths:
        results[path] = check_file(path)
    return results


def check_directory(dir_path: str) -> dict[str, list[tuple[int, str]]]:
    """Recursively scan a directory for *.md files and check each for non-ASCII.

    Hidden directories (names starting with '.') are skipped.

    Args:
        dir_path: Root directory path to scan.

    Returns:
        Dictionary mapping each discovered *.md file path to its list of
        (line_number, line_content) violations.
    """
    results: dict[str, list[tuple[int, str]]] = {}
    # os.walk respects the topdown flag; we prune hidden dirs in-place
    for root, dirs, files in os.walk(dir_path):
        # Skip hidden directories by pruning them from the walk
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if name.endswith(".md"):
                path = os.path.join(root, name)
                results[path] = check_file(path)
    return results


def format_violations(
    results: dict[str, list[tuple[int, str]]],
) -> list[str]:
    """Format check results into human-readable strings.

    Each violation is rendered as:
        FILE:LINE:CHAR  content_snippet

    where CHAR is the non-ASCII character found (shown verbatim; may display
    oddly for control/wide characters).

    Args:
        results: Dictionary mapping file path to list of (line_number, line_content).

    Returns:
        List of formatted strings, empty if no violations exist.
    """
    lines: list[str] = []
    for filepath, violations in sorted(results.items()):
        for line_no, content in violations:
            # Find the non-ASCII character for the snippet
            nonascii_char = ""
            for ch in content:
                if ord(ch) > 127:
                    nonascii_char = ch
                    break
            lines.append(f"{filepath}:{line_no}:{nonascii_char}  {content}")
    return lines


def main() -> None:
    """Main entry point for CLI usage. Parses arguments, runs checks, prints results."""
    parser = argparse.ArgumentParser(
        description="Check text files for non-ASCII characters."
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="One or more file paths to check.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        metavar="PATH",
        default=None,
        help="Recursively scan a directory for *.md files.",
    )
    args = parser.parse_args()

    results: dict[str, list[tuple[int, str]]] = {}

    if args.directory:
        results.update(check_directory(args.directory))

    if args.files:
        results.update(check_files(args.files))

    if not args.files and not args.directory:
        parser.print_usage()
        sys.exit(1)

    # Print all violations
    for line in format_violations(results):
        print(line)

    # Determine exit code
    any_violations = any(violations for violations in results.values())
    sys.exit(1 if any_violations else 0)


if __name__ == "__main__":
    main()