#!/usr/bin/env bash
set -u
PLOG="/home/quinten/fetch/publishable-repo/readability_study/results/pipeline.log"
PY="/home/quinten/fetch/.venv/bin/python"
STUDY="/home/quinten/fetch/publishable-repo/readability_study"
echo "ANALYSIS: waiting for PIPELINE_COMPLETE..."
until grep -q "PIPELINE_COMPLETE" "$PLOG" 2>/dev/null; do sleep 20; done
echo "ANALYSIS: metrics done. Building blind subset + running paired analysis."
cd "$STUDY/metrics/claude_subset" && $PY build_blind_subset.py --run-id main_20260719 --n-scenarios 30 2>&1 | tail -3
cd "$STUDY/analysis" && $PY analyze.py --run-id main_20260719 --judge deepseek-v4 2>&1 | tail -60
echo "ANALYSIS: ANALYSIS_COMPLETE"
