#!/usr/bin/env python3
"""Analyze five-rater reliability and disagreements on unique reviewed scenarios."""

from __future__ import annotations

import csv
import itertools
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

import build_gold_consensus as gold


RATERS = ("gpt52", "gemini31_pro", "deepseek_v4", "jackie", "qs")
OUT_DIR = gold.OUT_DIR


def icc_absolute(matrix: list[list[float]]) -> dict[str, float | int | None]:
    """Two-way random-effects absolute-agreement ICC(A,1) and ICC(A,k)."""
    n = len(matrix)
    k = len(matrix[0]) if matrix else 0
    if n < 2 or k < 2 or any(len(row) != k for row in matrix):
        raise ValueError("ICC needs a complete n x k matrix with n,k >= 2")
    grand = mean(value for row in matrix for value in row)
    row_means = [mean(row) for row in matrix]
    col_means = [mean(matrix[i][j] for i in range(n)) for j in range(k)]
    ss_rows = k * sum((value - grand) ** 2 for value in row_means)
    ss_cols = n * sum((value - grand) ** 2 for value in col_means)
    ss_total = sum((value - grand) ** 2 for row in matrix for value in row)
    ss_error = max(0.0, ss_total - ss_rows - ss_cols)
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    denom_single = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    denom_average = ms_rows + (ms_cols - ms_error) / n
    return {
        "targets": n,
        "raters": k,
        "icc_a_1": (ms_rows - ms_error) / denom_single if denom_single else None,
        "icc_a_k": (ms_rows - ms_error) / denom_average if denom_average else None,
        "ms_targets": ms_rows,
        "ms_raters": ms_cols,
        "ms_error": ms_error,
    }


def bootstrap_count_icc(matrix: list[list[float]], iterations: int = 2000) -> dict[str, list[float]]:
    rng = random.Random(20260716)
    values: dict[str, list[float]] = {"icc_a_1": [], "icc_a_k": []}
    for _ in range(iterations):
        sample = [matrix[rng.randrange(len(matrix))] for _ in matrix]
        result = icc_absolute(sample)
        for key in values:
            value = result[key]
            if isinstance(value, float) and math.isfinite(value):
                values[key].append(value)
    output: dict[str, list[float]] = {}
    for key, samples in values.items():
        samples.sort()
        output[f"{key}_bootstrap_95_ci"] = [
            samples[int(0.025 * (len(samples) - 1))],
            samples[int(0.975 * (len(samples) - 1))],
        ]
    return output


def set_metrics(left: frozenset[gold.Pair], right: frozenset[gold.Pair]) -> tuple[float, float, bool]:
    union = left | right
    intersection = left & right
    jaccard = len(intersection) / len(union) if union else 1.0
    f1 = 2 * len(intersection) / (len(left) + len(right)) if left or right else 1.0
    return jaccard, f1, left == right


def pair_text(pair: gold.Pair) -> str:
    return f"{pair[0]} > {pair[1]}"


def main() -> int:
    _, taxonomy = gold.silver.read_taxonomy(gold.TAXONOMY)
    valid_pairs = set(taxonomy)
    raw_reviews, human_by_text = gold.load_human_decisions(valid_pairs)
    models = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in gold.MODEL_FILES.items()
    }
    source_rows = gold.silver.read_workbook_rows(gold.SOURCE)
    source_by_text: dict[str, list[int]] = defaultdict(list)
    for source_row in range(2, len(source_rows) + 1):
        source_by_text[source_rows[source_row - 1]["A"]].append(source_row)

    cases: list[dict[str, object]] = []
    for text, humans in human_by_text.items():
        if set(humans) != set(gold.HUMAN_REVIEWERS):
            continue
        canonical = source_by_text[text][0]
        sets: dict[str, frozenset[gold.Pair]] = {
            name: frozenset(gold.ordered_model_pairs(results[str(canonical)]))
            for name, results in models.items()
        }
        sets.update({name: decision.labels for name, decision in humans.items()})
        cases.append({"text": text, "source_rows": source_by_text[text], "sets": sets})
    cases.sort(key=lambda item: item["source_rows"][0])  # type: ignore[index]

    count_matrix = [[float(len(case["sets"][rater])) for rater in RATERS] for case in cases]  # type: ignore[index]
    count_icc = icc_absolute(count_matrix)
    count_icc.update(bootstrap_count_icc(count_matrix))
    human_count_icc = icc_absolute([[row[3], row[4]] for row in count_matrix])
    llm_count_icc = icc_absolute([row[:3] for row in count_matrix])

    conditional_pair_matrix: list[list[float]] = []
    conditional_top_matrix: list[list[float]] = []
    full_pair_matrix: list[list[float]] = []
    for case in cases:
        sets = case["sets"]  # type: ignore[assignment]
        union_pairs = set().union(*(sets[rater] for rater in RATERS))
        for pair in sorted(union_pairs):
            conditional_pair_matrix.append([float(pair in sets[rater]) for rater in RATERS])
        top_sets = {rater: {pair[0] for pair in sets[rater]} for rater in RATERS}
        for category in sorted(set().union(*top_sets.values())):
            conditional_top_matrix.append([float(category in top_sets[rater]) for rater in RATERS])
        for pair in taxonomy:
            full_pair_matrix.append([float(pair in sets[rater]) for rater in RATERS])

    pairwise: dict[str, dict[str, float | int]] = {}
    for left, right in itertools.combinations(RATERS, 2):
        metrics = [set_metrics(case["sets"][left], case["sets"][right]) for case in cases]  # type: ignore[index]
        pairwise[f"{left}__{right}"] = {
            "mean_jaccard": mean(item[0] for item in metrics),
            "mean_label_f1": mean(item[1] for item in metrics),
            "exact_set_agreements": sum(item[2] for item in metrics),
            "exact_set_agreement_rate": mean(float(item[2]) for item in metrics),
        }

    duplicate_groups: dict[tuple[str, str], list[frozenset[gold.Pair]]] = defaultdict(list)
    for row in raw_reviews:
        reviewer = row["reviewer_key"].strip().lower()
        if reviewer in gold.HUMAN_REVIEWERS and row["status"] in gold.ELIGIBLE_STATUSES:
            duplicate_groups[(row["problem_description"], reviewer)].append(gold.label_set(row))
    repeated = [sets for sets in duplicate_groups.values() if len(sets) > 1]
    repeat_exact = sum(len(set(sets)) == 1 for sets in repeated)

    disagreement_rows: list[dict[str, object]] = []
    for case in cases:
        sets = case["sets"]  # type: ignore[assignment]
        jaccard, f1, exact = set_metrics(sets["jackie"], sets["qs"])
        if exact:
            continue
        votes: Counter[gold.Pair] = Counter()
        for rater in RATERS:
            votes.update(sets[rater])
        disagreement_rows.append({
            "canonical_source_row": case["source_rows"][0],  # type: ignore[index]
            "source_row_aliases": ";".join(map(str, case["source_rows"])),
            "problem_description": case["text"],
            "human_jaccard": jaccard,
            "human_label_f1": f1,
            "jackie_labels": " || ".join(sorted(map(pair_text, sets["jackie"]))),
            "qs_labels": " || ".join(sorted(map(pair_text, sets["qs"]))),
            "gpt52_labels": " || ".join(sorted(map(pair_text, sets["gpt52"]))),
            "gemini31_pro_labels": " || ".join(sorted(map(pair_text, sets["gemini31_pro"]))),
            "deepseek_v4_labels": " || ".join(sorted(map(pair_text, sets["deepseek_v4"]))),
            "five_rater_votes": " || ".join(
                f"{pair_text(pair)} [{count}/5]" for pair, count in votes.most_common()
            ),
        })
    disagreement_rows.sort(key=lambda row: (row["human_jaccard"], row["canonical_source_row"]))

    rater_summary = {
        rater: {
            "mean_label_count": mean(len(case["sets"][rater]) for case in cases),  # type: ignore[index]
            "label_count_distribution": dict(sorted(Counter(len(case["sets"][rater]) for case in cases).items())),  # type: ignore[index]
        }
        for rater in RATERS
    }
    report = {
        "scope": {
            "raw_review_records": len(raw_reviews),
            "unique_reviewed_scenarios": len(cases),
            "raters": list(RATERS),
            "duplicate_source_descriptions_excluded_from_target_count": sum(
                len(case["source_rows"]) - 1 for case in cases  # type: ignore[arg-type]
            ),
        },
        "icc": {
            "label_count_all_five_raters": count_icc,
            "label_count_humans_only": human_count_icc,
            "label_count_llms_only": llm_count_icc,
            "conditional_exact_pair_incidence_all_five": icc_absolute(conditional_pair_matrix),
            "conditional_top_level_incidence_all_five": icc_absolute(conditional_top_matrix),
            "all_209_pair_incidence_sensitivity": icc_absolute(full_pair_matrix),
        },
        "rater_summary": rater_summary,
        "pairwise_set_agreement": pairwise,
        "human_exact_set_agreements": pairwise["jackie__qs"]["exact_set_agreements"],
        "human_exact_set_agreement_rate": pairwise["jackie__qs"]["exact_set_agreement_rate"],
        "human_disagreement_scenarios": len(disagreement_rows),
        "duplicate_review_stability": {
            "repeated_scenario_reviewer_pairs": len(repeated),
            "exactly_repeated_label_sets": repeat_exact,
            "exact_repeat_rate": repeat_exact / len(repeated) if repeated else None,
            "resolution": "latest eligible saved decision per reviewer used for each unique scenario",
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "rater_agreement_analysis.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    with (OUT_DIR / "human_disagreements.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(disagreement_rows[0]))
        writer.writeheader()
        writer.writerows(disagreement_rows)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
