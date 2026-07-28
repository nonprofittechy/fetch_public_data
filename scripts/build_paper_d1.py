#!/usr/bin/env python3
"""Build the 355-narrative D1 file used by the paper.

The 373-row consensus file is unique after exact, redacted-text
normalization. Eighteen repeats remain because separately redacted deliveries
of the same narrative differ in synthetic names, ages, dates, vehicles, or
dollar amounts, and because one imported narrative was split into fragments.

Retention rule: for containment matches, keep the more complete narrative;
otherwise keep the lower scenario ID. The 0.80 Jaccard threshold sits in the
observed gap between re-send twins (at least 0.83) and distinct queries (at
most 0.56).
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from repo_paths import D1_CONSENSUS_DIR, D1_DIR


JACCARD_DUPLICATE = 0.80
DEFAULT_INPUT = D1_CONSENSUS_DIR / "gold_labels_consensus_unique.csv"
DEFAULT_OUTPUT = D1_DIR / "d1_paper_dataset_355.csv"


def normalize(text: str) -> str:
    """Lowercase and remove punctuation/extra whitespace for comparison."""
    return re.sub(
        r"\s+",
        " ",
        re.sub(r"[^a-z0-9 ]", "", (text or "").lower()),
    ).strip()


def find_repeats(
    rows: list[dict[str, str]],
) -> tuple[set[str], list[tuple[str, str, str]]]:
    """Return dropped IDs and ``(kept, dropped, reason)`` audit records."""
    texts = [(row["scenario_id"], normalize(row["problem_description"])) for row in rows]
    pairs: list[tuple[str, str, str]] = []

    for index, (scenario_a, text_a) in enumerate(texts):
        for scenario_b, text_b in texts[index + 1 :]:
            if not text_a or not text_b:
                continue

            if text_a in text_b or text_b in text_a:
                short, long_ = (
                    (scenario_a, scenario_b)
                    if len(text_a) < len(text_b)
                    else (scenario_b, scenario_a)
                )
                short_words = min(len(text_a.split()), len(text_b.split()))
                long_words = max(len(text_a.split()), len(text_b.split()))
                reason = "fragment" if short_words * 2 < long_words else "truncated re-send"
                pairs.append((long_, short, reason))
                continue

            words_a, words_b = set(text_a.split()), set(text_b.split())
            score = len(words_a & words_b) / len(words_a | words_b)
            if score >= JACCARD_DUPLICATE:
                keep, drop = sorted(
                    (scenario_a, scenario_b),
                    key=lambda scenario: int(scenario.split("-")[1]),
                )
                pairs.append((keep, drop, f"re-send twin (J={score:.2f})"))

    return {drop for _, drop, _ in pairs}, pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    if fields is None:
        raise ValueError(f"{args.input} has no CSV header")

    drop_ids, pairs = find_repeats(rows)
    kept = [row for row in rows if row["scenario_id"] not in drop_ids]
    if len(rows) != 373 or len(drop_ids) != 18 or len(kept) != 355:
        raise ValueError(
            f"unexpected D1 counts: {len(rows)} input, "
            f"{len(drop_ids)} dropped, {len(kept)} output"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)

    for keep, drop, reason in sorted(pairs, key=lambda pair: pair[2]):
        print(f"drop {drop} (repeat of {keep}): {reason}")
    print(f"wrote {len(kept)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
