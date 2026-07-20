#!/usr/bin/env bash
# Chained downstream pipeline: waits for generation to complete (all 746 screens
# written), then repairs provider failures, computes deterministic metrics, and
# runs the DeepSeek-V4 LLM-judge metrics. Emits clear stage markers.
set -u
RUN_ID="${1:-main_20260719}"
STUDY="/home/quinten/fetch/publishable-repo/readability_study"
SCREENS="$STUDY/results/generation/$RUN_ID/screens.jsonl"
PY="/home/quinten/fetch/.venv/bin/python"

echo "PIPELINE: waiting for generation to reach 746 screens..."
while true; do
  n=$(wc -l < "$SCREENS" 2>/dev/null || echo 0)
  if [ "$n" -ge 746 ]; then break; fi
  sleep 20
done
echo "PIPELINE: generation complete ($n screens). Starting repair."

cd "$STUDY/harness"
$PY repair_failures.py --run-id "$RUN_ID" --concurrency 6 --rounds 6 2>&1 | tail -40
echo "PIPELINE: repair done."

cd "$STUDY/metrics"
$PY deterministic.py --run-id "$RUN_ID" 2>&1 | grep -viE "warning|loading weights" | tail -10
echo "PIPELINE: deterministic metrics done."

$PY run_llm_metrics.py --run-id "$RUN_ID" --judge-model deepseek-v4 --concurrency 8 2>&1 | tail -25
echo "PIPELINE: llm metrics done. PIPELINE_COMPLETE"
