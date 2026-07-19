#!/usr/bin/env bash
set -u
PY=/home/quinten/fetch/.venv/bin/python
D=/home/quinten/fetch/publishable-repo/readability_study
cd $D/metrics && $PY deterministic.py --run-id main_20260719 2>&1 | tail -1
cd $D/metrics && $PY run_llm_metrics.py --run-id main_20260719 --judge-model deepseek-v4 --concurrency 6 2>&1 | tail -1
cd $D/analysis && $PY analyze.py --run-id main_20260719 --judge deepseek-v4 2>&1 | tail -32
echo "FINALIZE_COMPLETE"
