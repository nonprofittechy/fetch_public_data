#!/usr/bin/env python3
"""Validate and merge a review-app gold export with the public source data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import create_silver_labels as silver


SOURCE = Path("redaction_reviewed_v5_clean.xlsx")
TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-export", type=Path, required=True, help="CSV downloaded from /export/gold.csv")
    parser.add_argument("--output", type=Path, default=Path("human_validated_gold.csv"))
    parser.add_argument("--report", type=Path, default=Path("human_validated_gold_report.json"))
    parser.add_argument(
        "--mode", choices=("reviewed-only", "full"), default="reviewed-only",
        help="Emit only validated rows or all 431 source rows with blank gold fields where unreviewed.",
    )
    parser.add_argument("--min-reviewers", type=int, choices=(1, 2), default=1)
    return parser.parse_args()


def read_gold(path: Path, valid_pairs: set[tuple[str, str]], source_rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                row_number = int(row["row_number"])
                count = int(row["gold_label_count"])
                reviewers = int(row["reviewer_count"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid gold export row: {row}") from exc
            if row_number in result:
                raise ValueError(f"Duplicate gold row {row_number}")
            if not 2 <= row_number <= len(source_rows):
                raise ValueError(f"Gold row {row_number} is outside the source workbook")
            if row.get("problem_description", "") != source_rows[row_number - 1].get("A", ""):
                raise ValueError(f"Problem text mismatch for row {row_number}")
            if not 1 <= count <= 4:
                raise ValueError(f"Gold row {row_number} has invalid label count {count}")
            if reviewers < 1:
                raise ValueError(f"Gold row {row_number} has no validating reviewer")
            labels = []
            for slot in range(1, count + 1):
                pair = (row.get(f"gold_category_{slot}", ""), row.get(f"gold_subcategory_{slot}", ""))
                if pair not in valid_pairs:
                    raise ValueError(f"Gold row {row_number} has invalid taxonomy pair {pair}")
                labels.append(pair)
            if len(labels) != len(set(labels)):
                raise ValueError(f"Gold row {row_number} contains duplicate labels")
            result[row_number] = row
    return result


def output_fields() -> list[str]:
    fields = [
        "row_number", "problem_description", "original_human_category",
        "original_human_subcategory", "gold_label_count",
    ]
    for slot in range(1, 5):
        fields.extend([f"gold_category_{slot}", f"gold_subcategory_{slot}"])
    fields.extend([
        "reviewer_count", "human_reviewers", "validation_basis", "validated_at",
        "gold_source",
    ])
    return fields


def main() -> int:
    args = parse_args()
    source_rows = silver.read_workbook_rows(SOURCE)
    taxonomy, pairs = silver.read_taxonomy(TAXONOMY)
    gold = read_gold(args.gold_export, set(pairs), source_rows)
    selected = {
        row_number: row for row_number, row in gold.items()
        if int(row["reviewer_count"]) >= args.min_reviewers
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_fields())
        writer.writeheader()
        row_numbers = range(2, len(source_rows) + 1) if args.mode == "full" else sorted(selected)
        for row_number in row_numbers:
            source = source_rows[row_number - 1]
            review = selected.get(row_number, {})
            output = {
                "row_number": row_number,
                "problem_description": source.get("A", ""),
                "original_human_category": source.get("B", ""),
                "original_human_subcategory": source.get("C", ""),
                "gold_source": "FETCH human review app" if review else "unreviewed",
                **review,
            }
            writer.writerow(output)
    report = {
        "source_rows": len(source_rows) - 1,
        "canonical_taxonomy_pairs": len(taxonomy),
        "gold_export_rows": len(gold),
        "rows_meeting_min_reviewers": len(selected),
        "minimum_reviewers": args.min_reviewers,
        "mode": args.mode,
        "output": str(args.output),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
