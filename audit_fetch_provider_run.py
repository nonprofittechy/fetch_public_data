#!/usr/bin/env python3
"""Audit final per-provider outcomes in a run-scoped FETCH application log."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


TIME_FORMAT = "%Y-%m-%d %H:%M:%S,%f"
PROVIDERS = ("gpt-5.2", "gemini", "mistral", "keyword", "spot")
START_MARKER = "[OpenAIProvider:gpt-5.2] classify start"
LENGTH_PATTERN = re.compile(r"desc_len=(\d+)")
SUMMARY_PATTERN = re.compile(r" - (gpt-5\.2|gemini|mistral|keyword|spot): (ok|Exception|error:)")


def timestamp(line: str) -> datetime:
    return datetime.strptime(line[:23], TIME_FORMAT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--tests", type=Path, required=True, help="Input CSV, or completed Promptfoo JSON")
    parser.add_argument("--run-start", required=True, help="Local log time, YYYY-mm-dd HH:MM:SS")
    parser.add_argument("--run-end", help="Exclusive local log time; omit only while no later run exists")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--gpt-repair-csv", type=Path)
    return parser.parse_args()


def load_tests(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        doc = json.loads(path.read_text(encoding="utf-8"))
        records = sorted(doc["results"]["results"], key=lambda row: int(row.get("testIdx", 0)))
        return [dict(record.get("vars") or {}) for record in records]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    tests = load_tests(args.tests)
    lines = []
    for line in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        if len(line) < 23 or line[:4] != "2026":
            continue
        if line[:19] < args.run_start:
            continue
        if args.run_end and line[:19] >= args.run_end:
            continue
        lines.append(line)

    starts = [timestamp(line) for line in lines if START_MARKER in line]
    lengths = [
        int(LENGTH_PATTERN.search(line).group(1))
        for line in lines
        if "[OpenAIProvider:gpt-5.2] prompt_len=" in line and LENGTH_PATTERN.search(line)
    ]
    expected_lengths = [len(row["problem_description"]) for row in tests]
    order_validated = lengths == expected_lengths and len(starts) == len(tests)

    outcomes: Counter[tuple[str, str]] = Counter()
    for line in lines:
        match = SUMMARY_PATTERN.search(line)
        if match:
            outcomes[(match.group(1), match.group(2).rstrip(":"))] += 1

    # Each final Results summary contains exactly one provider-status line.
    # Outer service timeouts are matched at the configured horizon. SDK-level
    # API exceptions are matched to the most recent unclaimed GPT start; with
    # bounded Promptfoo concurrency, that is the request whose SDK call ended.
    exception_events = []
    for line in lines:
        if " - gpt-5.2: Exception" in line:
            exception_events.append((timestamp(line), "timed out after" in line, line.split("Exception -> ", 1)[-1]))
    repair_indexes = []
    repair_details = []
    used = set()
    if order_validated:
        for event, is_outer_timeout, message in exception_events:
            elapsed_candidates = [
                ((event - start).total_seconds(), index)
                for index, start in enumerate(starts)
                if index not in used and 0 <= (event - start).total_seconds() <= args.timeout_seconds + 30
            ]
            if is_outer_timeout:
                candidates = sorted((abs(elapsed - args.timeout_seconds), index, elapsed) for elapsed, index in elapsed_candidates)
            else:
                candidates = sorted((elapsed, index, elapsed) for elapsed, index in elapsed_candidates)
            if not candidates:
                continue
            distance, index, elapsed = candidates[0]
            if is_outer_timeout and distance > 8:
                continue
            used.add(index)
            repair_indexes.append(index)
            repair_details.append({
                "test_index_zero_based": index,
                "scenario_id": tests[index].get("scenario_id", ""),
                "source_row": tests[index].get("source_row", ""),
                "description_length": expected_lengths[index],
                "observed_elapsed_seconds": round(elapsed, 3),
                "match_rule": "configured_timeout_horizon" if is_outer_timeout else "most_recent_unclaimed_start",
                "exception": message,
                "problem_description": tests[index]["problem_description"],
            })

    provider_outcomes = {}
    for provider in PROVIDERS:
        provider_outcomes[provider] = {
            "ok": outcomes[(provider, "ok")],
            "exception": outcomes[(provider, "Exception")],
            "error_result": outcomes[(provider, "error")],
        }
    report = {
        "run_start_local": args.run_start,
        "run_end_local_exclusive": args.run_end,
        "test_rows": len(tests),
        "gpt_start_rows": len(starts),
        "gpt_start_order_validated_against_csv": order_validated,
        "provider_final_outcomes": provider_outcomes,
        "gpt_exception_events": len(exception_events),
        "gpt_exception_rows_matched": len(repair_details),
        "gpt_exception_repair_cases": repair_details,
        "semantic_merge_timeout_log_lines": sum("semantic_merge timed out" in line for line in lines),
        "note": "Transient tracebacks that later succeeded are excluded; counts use final Results summary lines.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.gpt_repair_csv:
        args.gpt_repair_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.gpt_repair_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(tests[0]))
            writer.writeheader()
            writer.writerows(tests[index] for index in sorted(repair_indexes))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
