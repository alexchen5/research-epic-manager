#!/usr/bin/env bash
# End-to-end experiment driver (CPU-only; cumulative wall-clock; abort at 85 min).
set -euo pipefail
cd "$(dirname "$0")/.."
T0=$(date +%s)
echo "[$(date +%H:%M:%S)] pipeline start (T0=$T0)" | tee -a results/run_log.txt
python3 scripts/run_pipeline.py 2>&1 | tee -a results/run_log.txt
T1=$(date +%s)
echo "[$(date +%H:%M:%S)] pipeline end; wall=$((T1 - T0))s" | tee -a results/run_log.txt