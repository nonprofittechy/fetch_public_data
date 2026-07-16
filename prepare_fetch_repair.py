#!/usr/bin/env python3
"""Extract GPT-5.2 timeout cases from a run-scoped FETCH log."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path


START_MARKER = "[OpenAIProvider:gpt-5.2] classify start"
LENGTH_PATTERN = re.compile(r"desc_len=(\d+)")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S,%f"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=Path("../app.log"))
    parser.add_argument("--run-start", default="2026-07-16 10:59:27")
    parser.add_argument("--tests", type=Path, default=Path("../promptfoo/followup_questions_only.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("gold_labels_consensus_20260716/fetch_full_runs"))
    return parser.parse_args()


def timestamp(line: str) -> datetime:
    return datetime.strptime(line[:23], TIME_FORMAT)


def main() -> int:
    args = parse_args()
    with args.tests.open(encoding="utf-8-sig", newline="") as stream:
        tests = list(csv.DictReader(stream))
    lines = [
        line for line in args.log.read_text(encoding="utf-8", errors="replace").splitlines()
        if line[:19] >= args.run_start
    ]
    starts = [timestamp(line) for line in lines if START_MARKER in line]
    lengths = [
        int(LENGTH_PATTERN.search(line).group(1))
        for line in lines
        if "[OpenAIProvider:gpt-5.2] prompt_len=" in line
    ]
    expected_lengths = [len(row["problem_description"]) for row in tests]
    if lengths != expected_lengths or len(starts) != len(tests):
        raise ValueError("GPT start order/description lengths do not exactly match the test CSV")

    # The logging stack emits each timeout line twice. Collapse identical
    # timestamp/message events before matching them to starts.
    timeout_events: list[datetime] = []
    for line in lines:
        if "gpt-5.2" not in line or "timed out after 17.0s" not in line:
            continue
        event = timestamp(line)
        if not timeout_events or (event - timeout_events[-1]).total_seconds() > 0.1:
            timeout_events.append(event)

    used: set[int] = set()
    timed_out_indexes: list[int] = []
    match_details: list[dict[str, object]] = []
    for event in timeout_events:
        candidates = sorted(
            (
                abs((event - start).total_seconds() - 17.0),
                index,
                (event - start).total_seconds(),
            )
            for index, start in enumerate(starts)
            if index not in used and 15.0 <= (event - start).total_seconds() <= 22.0
        )
        if not candidates:
            raise ValueError(f"could not match timeout event {event.isoformat()}")
        distance, index, elapsed = candidates[0]
        if distance > 3.1:
            raise ValueError(f"ambiguous timeout match at {event.isoformat()}: {candidates[:3]}")
        used.add(index)
        timed_out_indexes.append(index)
        match_details.append({
            "test_index_zero_based": index,
            "test_number_one_based": index + 1,
            "description_length": expected_lengths[index],
            "start": starts[index].isoformat(),
            "timeout_log_time": event.isoformat(),
            "observed_elapsed_seconds": elapsed,
            "problem_description": tests[index]["problem_description"],
        })

    timed_out_indexes.sort()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    repair_path = args.output_dir / "baseline_gpt52_timeout_repair_cases.csv"
    with repair_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(tests[0]))
        writer.writeheader()
        writer.writerows(tests[index] for index in timed_out_indexes)
    report = {
        "run_start": args.run_start,
        "tests": len(tests),
        "gpt52_starts": len(starts),
        "duplicated_timeout_log_lines": sum(
            "gpt-5.2" in line and "timed out after 17.0s" in line for line in lines
        ),
        "unique_gpt52_timeout_events": len(timeout_events),
        "semantic_merge_timeout_log_lines": sum("semantic_merge timed out" in line for line in lines),
        "matching_validation": "all GPT start description lengths exactly matched CSV order",
        "repair_cases": match_details,
        "repair_csv": str(repair_path),
    }
    (args.output_dir / "baseline_timeout_repair_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
