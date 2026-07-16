#!/usr/bin/env python3
"""Build row-compatible and deduplicated consensus labels from Stage 10 review.

The source workbook contains exact and whitespace-only duplicate problem
descriptions. Consensus is therefore computed once per normalized description
and then mapped back to every source row so aliases cannot receive inconsistent
gold labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import create_silver_labels as silver


Pair = tuple[str, str]
SOURCE = Path("redaction_reviewed_v5_clean.xlsx")
TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")
REVIEWS = Path("silver_labels/10_four_label_human_review/human_label_reviews (4).csv")
MODEL_FILES = {
    "gpt52": Path("silver_labels/01_gpt52/checkpoint.json"),
    "gemini31_pro": Path("silver_labels/02_gemini31_pro/checkpoint.json"),
    "deepseek_v4": Path("silver_labels/03_deepseek_v4/checkpoint.json"),
}
INTERNAL_REVIEW = Path("silver_labels/04_review/final_review.json")
OUT_DIR = Path("gold_labels_consensus_20260716")
ELIGIBLE_STATUSES = {"accepted", "corrected"}
HUMAN_REVIEWERS = ("jackie", "qs")


@dataclass(frozen=True)
class HumanDecision:
    reviewer: str
    source_row: int
    labels: frozenset[Pair]
    status: str
    updated_at: str


def normalize_description(value: str) -> str:
    """Collapse formatting-only whitespace differences without changing words."""
    return re.sub(r"\s+", " ", value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def label_set(row: dict[str, str], prefix: str = "human") -> frozenset[Pair]:
    labels = {
        (row.get(f"{prefix}_category_{slot}", ""), row.get(f"{prefix}_subcategory_{slot}", ""))
        for slot in range(1, 5)
        if row.get(f"{prefix}_category_{slot}", "") and row.get(f"{prefix}_subcategory_{slot}", "")
    }
    return frozenset(labels)


def load_human_decisions(valid_pairs: set[Pair]) -> tuple[list[dict[str, str]], dict[str, dict[str, HumanDecision]]]:
    with REVIEWS.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    seen_keys: set[tuple[int, str]] = set()
    candidates: dict[tuple[str, str], list[HumanDecision]] = defaultdict(list)
    for row in rows:
        source_row = int(row["row_number"])
        reviewer = row["reviewer_key"].strip().lower()
        key = (source_row, reviewer)
        if key in seen_keys:
            raise ValueError(f"duplicate raw review key {key}")
        seen_keys.add(key)
        labels = label_set(row)
        unknown = labels - valid_pairs
        if unknown:
            raise ValueError(f"review row {source_row} contains invalid pairs: {sorted(unknown)}")
        if reviewer in HUMAN_REVIEWERS and row["status"] in ELIGIBLE_STATUSES and labels:
            candidates[(normalize_description(row["problem_description"]), reviewer)].append(
                HumanDecision(reviewer, source_row, labels, row["status"], row["updated_at"])
            )

    # Repeated source descriptions caused genuine repeat reviews. The latest
    # saved decision is the reviewer's final decision for that scenario.
    collapsed: dict[str, dict[str, HumanDecision]] = defaultdict(dict)
    for (text, reviewer), decisions in candidates.items():
        collapsed[text][reviewer] = max(
            decisions,
            key=lambda item: (datetime.fromisoformat(item.updated_at), item.source_row),
        )
    return rows, collapsed


def ordered_model_pairs(items: Iterable[dict[str, str]]) -> list[Pair]:
    return [(item["category"], item["subcategory"]) for item in items]


def select_consensus(
    model_sets: dict[str, list[Pair]],
    internal_primary: Pair,
    humans: dict[str, HumanDecision],
) -> tuple[list[Pair], str, dict[Pair, dict[str, object]]]:
    model_votes: Counter[Pair] = Counter()
    ranks: dict[Pair, list[int]] = defaultdict(list)
    for pairs in model_sets.values():
        for rank, pair in enumerate(pairs, start=1):
            model_votes[pair] += 1
            ranks[pair].append(rank)
    human_votes: Counter[Pair] = Counter()
    for decision in humans.values():
        human_votes.update(decision.labels)

    support: dict[Pair, dict[str, object]] = {}
    for pair in set(model_votes) | set(human_votes) | {internal_primary}:
        support[pair] = {
            "human_votes": human_votes[pair],
            "model_votes": model_votes[pair],
            "mean_model_rank": sum(ranks[pair]) / len(ranks[pair]) if ranks[pair] else None,
            "internal_primary": pair == internal_primary,
        }

    if len(humans) == 2:
        # Human omissions matter. Keep a label when both humans selected it, or
        # when one human selected it and at least two independent models
        # corroborated it. The latter threshold favors precision for gold data.
        candidates = [
            pair for pair in support
            if human_votes[pair] == 2 or (human_votes[pair] == 1 and model_votes[pair] >= 2)
        ]
        if not candidates:
            # No shared or strongly corroborated human label: retain the most
            # supported human-selected pair, using the internal primary only as
            # a deterministic tie-breaker.
            human_candidates = [pair for pair in support if human_votes[pair]]
            candidates = [max(
                human_candidates,
                key=lambda pair: (
                    human_votes[pair] + model_votes[pair],
                    model_votes[pair],
                    pair == internal_primary,
                    pair[0],
                    pair[1],
                ),
            )] if human_candidates else [internal_primary]

        # These criminal charge-severity routes are alternative classifications
        # of one charge, not separate legal issues. Retain the strongest one.
        severity = {
            ("Criminal Law", "Misdemeanor"),
            ("Criminal Law", "Lessor Felony"),
            ("Criminal Law", "Major Felony"),
        }
        selected_severity = severity.intersection(candidates)
        if len(selected_severity) > 1:
            winner = max(
                selected_severity,
                key=lambda pair: (
                    human_votes[pair] + model_votes[pair],
                    human_votes[pair],
                    model_votes[pair],
                    pair == internal_primary,
                ),
            )
            candidates = [pair for pair in candidates if pair not in severity or pair == winner]
        exact = len({decision.labels for decision in humans.values()}) == 1
        provenance = "two_human_exact_consensus" if exact else "two_human_model_corroborated_consensus"
    else:
        # For scenarios outside the human queue, retain the internally reviewed
        # primary and any pair independently proposed by at least two models.
        candidates = [pair for pair in support if model_votes[pair] >= 2 or pair == internal_primary]
        provenance = "three_model_plus_internal_consensus"

    def sort_key(pair: Pair) -> tuple[float, ...] | tuple[float, float, float, str, str]:
        info = support[pair]
        mean_rank = info["mean_model_rank"] if info["mean_model_rank"] is not None else 99.0
        return (
            -float(info["human_votes"]),
            -float(info["model_votes"]),
            -float(bool(info["internal_primary"])),
            float(mean_rank),
            pair[0],
            pair[1],
        )

    selected = sorted(set(candidates), key=sort_key)[:4]
    return selected, provenance, support


def output_fields() -> list[str]:
    fields = [
        "source_row", "scenario_id", "canonical_source_row", "source_row_aliases",
        "problem_description", "gold_label_count",
    ]
    for slot in range(1, 5):
        fields.extend([f"gold_category_{slot}", f"gold_subcategory_{slot}"])
    fields.extend([
        "consensus_provenance", "human_reviewers_used", "duplicate_source_description",
        "support_summary_json",
    ])
    return fields


def serialize_row(record: dict[str, object], source_row: int) -> dict[str, object]:
    labels: list[Pair] = record["labels"]  # type: ignore[assignment]
    output: dict[str, object] = {
        "source_row": source_row,
        "scenario_id": record["scenario_id"],
        "canonical_source_row": record["canonical_source_row"],
        "source_row_aliases": ";".join(map(str, record["source_rows"])),
        "problem_description": record["problem_description"],
        "gold_label_count": len(labels),
        "consensus_provenance": record["provenance"],
        "human_reviewers_used": ";".join(record["human_reviewers"]),
        "duplicate_source_description": "yes" if len(record["source_rows"]) > 1 else "no",
        "support_summary_json": json.dumps(record["support"], ensure_ascii=False, sort_keys=True),
    }
    for slot in range(1, 5):
        pair = labels[slot - 1] if slot <= len(labels) else ("", "")
        output[f"gold_category_{slot}"] = pair[0]
        output[f"gold_subcategory_{slot}"] = pair[1]
    return output


def main() -> int:
    args = parse_args()
    source_rows = silver.read_workbook_rows(SOURCE)
    _, taxonomy_pairs = silver.read_taxonomy(TAXONOMY)
    valid_pairs = set(taxonomy_pairs)
    raw_reviews, human_by_text = load_human_decisions(valid_pairs)
    models = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in MODEL_FILES.items()
    }
    internal = json.loads(INTERNAL_REVIEW.read_text(encoding="utf-8"))["rows"]

    source_by_text: dict[str, list[int]] = defaultdict(list)
    for source_row in range(2, len(source_rows) + 1):
        source_by_text[normalize_description(source_rows[source_row - 1]["A"])].append(source_row)

    records: list[dict[str, object]] = []
    truncated = 0
    for index, (text, aliases) in enumerate(source_by_text.items(), start=1):
        canonical = aliases[0]
        model_sets = {
            name: ordered_model_pairs(results[str(canonical)])
            for name, results in models.items()
        }
        review = internal[str(canonical)]["review"]
        primary = (review["category"], review["subcategory"])
        human_decisions = human_by_text.get(text, {})
        labels, provenance, support = select_consensus(model_sets, primary, human_decisions)
        eligible_before_cap = sum(
            1 for info in support.values()
            if (
                (len(human_decisions) == 2 and (info["human_votes"] == 2 or (info["human_votes"] == 1 and info["model_votes"] >= 2)))
                or (len(human_decisions) != 2 and (info["model_votes"] >= 2 or info["internal_primary"]))
            )
        )
        truncated += eligible_before_cap > 4
        compact_support = {
            f"{pair[0]} > {pair[1]}": info
            for pair, info in support.items()
            if pair in labels
        }
        records.append({
            "scenario_id": f"gold-{index:04d}",
            "canonical_source_row": canonical,
            "source_rows": aliases,
            "problem_description": normalize_description(source_rows[canonical - 1]["A"]),
            "labels": labels,
            "provenance": provenance,
            "human_reviewers": sorted(human_decisions),
            "support": compact_support,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    unique_path = args.output_dir / "gold_labels_consensus_unique.csv"
    full_path = args.output_dir / "gold_labels_consensus_full_431.csv"
    with unique_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_fields())
        writer.writeheader()
        for record in records:
            writer.writerow(serialize_row(record, int(record["canonical_source_row"])))
    with full_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_fields())
        writer.writeheader()
        for record in records:
            for source_row in record["source_rows"]:  # type: ignore[union-attr]
                writer.writerow(serialize_row(record, int(source_row)))

    report = {
        "source_rows": len(source_rows) - 1,
        "unique_problem_descriptions": len(records),
        "duplicate_description_groups": sum(len(v) > 1 for v in source_by_text.values()),
        "duplicate_description_excess_rows": sum(len(v) - 1 for v in source_by_text.values()),
        "raw_human_review_records": len(raw_reviews),
        "raw_duplicate_row_reviewer_keys": 0,
        "unique_human_reviewed_scenarios": len(human_by_text),
        "human_reviewed_scenarios_with_two_eligible_reviewers": sum(len(v) == 2 for v in human_by_text.values()),
        "source_duplicate_groups_touched_by_human_review": sum(
            text in human_by_text and len(aliases) > 1 for text, aliases in source_by_text.items()
        ),
        "duplicate_descriptions_actually_reviewed_more_than_once": sum(
            len({int(row["row_number"]) for row in raw_reviews
                 if normalize_description(row["problem_description"]) == text and row["reviewer_key"].lower() in HUMAN_REVIEWERS}) > 1
            for text in human_by_text
        ),
        "consensus_sets_truncated_to_four": truncated,
        "label_count_distribution_unique": dict(sorted(Counter(len(r["labels"]) for r in records).items())),
        "provenance_distribution_unique": dict(sorted(Counter(r["provenance"] for r in records).items())),
        "outputs": {"row_compatible": str(full_path), "deduplicated": str(unique_path)},
    }
    (args.output_dir / "build_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
