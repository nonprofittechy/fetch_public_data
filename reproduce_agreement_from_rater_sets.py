#!/usr/bin/env python3
"""Recompute headline agreement statistics from the public normalized input."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from analyze_gold_rater_agreement import BOOTSTRAP_ITERATIONS, PAIR_GROUPS, bootstrap, summarize_group


DEFAULT_INPUT = Path("gold_labels_consensus_20260716/rater_sets.csv")


def parse_label_set(value: str) -> frozenset[tuple[str, str]]:
    if not value:
        return frozenset()
    return frozenset(tuple(item.split(" > ", 1)) for item in value.split(" || "))  # type: ignore[arg-type]


def load_normalized(path: Path) -> list[dict[str, object]]:
    grouped: dict[int, dict[str, object]] = defaultdict(lambda: {"sets": {}})
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            story_index = int(row["story_index"])
            grouped[story_index]["sets"][row["rater"]] = parse_label_set(row["label_set"])  # type: ignore[index]
    return [grouped[index] for index in sorted(grouped)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--bootstrap-iterations", type=int, default=BOOTSTRAP_ITERATIONS)
    args = parser.parse_args()
    cases = load_normalized(args.input)
    results = {group: summarize_group(cases, group) for group in PAIR_GROUPS}
    intervals, _ = bootstrap(cases, args.bootstrap_iterations)
    for group in results:
        results[group].update(intervals[group])
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
