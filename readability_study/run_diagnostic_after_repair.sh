#!/usr/bin/env bash
set -u
PLOG="/home/quinten/fetch/publishable-repo/readability_study/results/pipeline.log"
PY="/home/quinten/fetch/.venv/bin/python"
DIAG="/home/quinten/fetch/publishable-repo/readability_study/metrics/diagnostics"
echo "DIAG: waiting for repair stage to finish..."
until grep -q "PIPELINE: repair done" "$PLOG" 2>/dev/null; do sleep 15; done
echo "DIAG: repair done; generation models free. Running provider-question-rate diagnostic."
cd "$DIAG"
$PY provider_question_rates.py --run-id main_20260719 --mode empty-nano --concurrency 3 2>&1 | grep -vE "warning|Warning|resolution|Retrying|telemetry" | tail -30
echo "DIAG: empty-nano done. Running random sample."
$PY provider_question_rates.py --run-id main_20260719 --mode sample --n 30 --concurrency 3 2>&1 | grep -vE "warning|Warning|resolution|Retrying|telemetry" | tail -40
echo "DIAG: DIAGNOSTIC_COMPLETE"
