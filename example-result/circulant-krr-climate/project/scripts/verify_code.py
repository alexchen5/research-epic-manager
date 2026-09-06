#!/usr/bin/env python3
"""Verifier stub: checks that committed analysis scripts are importable/syntactically valid."""
import ast, pathlib, sys
bad = []
for p in sorted(pathlib.Path("scripts").glob("*.py")):
    if p.name in ("verify_code.py", "verify_data.py"):
        continue
    try:
        ast.parse(p.read_text())
    except SyntaxError as e:
        bad.append(f"{p}: {e}")
if bad:
    print("VERIFY_CODE FAIL\n" + "\n".join(bad)); sys.exit(1)
print("VERIFY_CODE OK")
