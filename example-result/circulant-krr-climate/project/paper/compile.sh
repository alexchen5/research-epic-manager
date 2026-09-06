#!/bin/bash
# Compile the CTIM workshop paper (main.tex) with tectonic (CPU-only host).
set -e
cd "$(dirname "$0")"
rm -f main.pdf
tectonic main.tex > compile.out 2>&1 || { echo "COMPILE FAILED"; tail -20 compile.out; exit 1; }
echo "COMPILE OK: $(ls -la main.pdf | awk '{print $5}') bytes, $(pdfinfo main.pdf 2>/dev/null | grep Pages || true)"