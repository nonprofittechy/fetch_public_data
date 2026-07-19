#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FETCH_REPO_ROOT="${FETCH_REPO_ROOT:-$(cd "$HERE/../.." && pwd)}"
REPEATS="${REPEATS:-3}"
FIRST_N="${FIRST_N:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HERE/results/$STAMP"
mkdir -p "$OUT"

source "$FETCH_REPO_ROOT/.venv/bin/activate"
cd "$HERE"

args=(eval --config promptfooconfig.no-cache.yaml --no-cache --no-share --repeat "$REPEATS" --output "$OUT/results.json")
if [[ -n "$FIRST_N" ]]; then
  args+=(--filter-first-n "$FIRST_N")
fi

printf 'Running %s uncached replicate(s); results: %s\n' "$REPEATS" "$OUT/results.json"
FETCH_REPO_ROOT="$FETCH_REPO_ROOT" promptfoo "${args[@]}"

