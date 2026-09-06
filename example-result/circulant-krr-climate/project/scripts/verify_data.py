#!/usr/bin/env python3
"""Verifier stub: checks artifact JSON files exist and parse."""
import json, pathlib, sys
bad = []
for p in sorted(pathlib.Path("results").rglob("*.json")):
    try:
        json.loads(p.read_text())
    except Exception as e:
        bad.append(f"{p}: {e}")
if bad:
    print("VERIFY_DATA FAIL\n" + "\n".join(bad)); sys.exit(1)
print("VERIFY_DATA OK")
