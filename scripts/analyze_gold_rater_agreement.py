#!/usr/bin/env python3
"""Analyze multi-label set agreement on the five-rater review subset.

The independent unit is one unique problem description.  Each annotation is an
unordered set of exact (category, subcategory) taxonomy pairs.  The primary
statistics are Jaccard distance and Krippendorff's alpha using Jaccard distance.
Only the Python standard library is required.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import platform
import random
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Callable, Hashable, Iterable, Sequence, TypeVar

import build_gold_consensus as gold


RATERS = ("gpt52", "gemini31_pro", "deepseek_v4", "jackie", "qs")
LLM_RATERS = RATERS[:3]
HUMAN_RATERS = RATERS[3:]
BOOTSTRAP_ITERATIONS = 2000
BOOTSTRAP_SEED = 20260716
OUT_DIR = gold.OUT_DIR

PAIR_GROUPS = {
    "humans": tuple(itertools.combinations(HUMAN_RATERS, 2)),
    "llms": tuple(itertools.combinations(LLM_RATERS, 2)),
    "human_llm": tuple((human, llm) for human in HUMAN_RATERS for llm in LLM_RATERS),
    "all_five": tuple(itertools.combinations(RATERS, 2)),
}
GROUP_RATERS = {
    "humans": HUMAN_RATERS,
    "llms": LLM_RATERS,
    "all_five": RATERS,
}

Pair = gold.Pair
SetRating = frozenset[Pair]
T = TypeVar("T", bound=Hashable)


@lru_cache(maxsize=None)
def jaccard_distance(left: frozenset[T], right: frozenset[T]) -> float:
    """Return 1 - |intersection| / |union|; two empty sets have distance zero."""
    union = left | right
    return 1.0 - len(left & right) / len(union) if union else 0.0


def percentile(sorted_values: Sequence[float], probability: float) -> float:
    """Linearly interpolated percentile (the common type-7 quantile)."""
    if not sorted_values:
        raise ValueError("cannot take a percentile of no values")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def confidence_interval(values: Iterable[float]) -> list[float] | None:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return None
    return [percentile(finite, 0.025), percentile(finite, 0.975)]


def expected_disagreement(
    ratings: Sequence[T], distance: Callable[[T, T], float]
) -> float:
    """Expected distance between two distinct ratings drawn from the pooled ratings."""
    if len(ratings) < 2:
        return math.nan
    counts = Counter(ratings)
    total = sum(
        left_count * right_count * distance(left, right)
        for (left, left_count), (right, right_count) in itertools.combinations(counts.items(), 2)
    )
    return total / math.comb(len(ratings), 2)


def krippendorff_alpha(
    units: Sequence[dict[str, T]],
    raters: Sequence[str],
    distance: Callable[[T, T], float],
) -> dict[str, float | int | None]:
    """Krippendorff alpha for complete, interchangeable-rater units."""
    pairs = tuple(itertools.combinations(raters, 2))
    observed = mean(
        distance(unit[left], unit[right])
        for unit in units
        for left, right in pairs
    )
    pooled = [unit[rater] for unit in units for rater in raters]
    expected = expected_disagreement(pooled, distance)
    alpha = None if not math.isfinite(expected) or expected == 0.0 else 1.0 - observed / expected
    return {
        "alpha": alpha,
        "observed_disagreement": observed,
        "expected_disagreement": expected if math.isfinite(expected) else None,
        "units": len(units),
        "raters": len(raters),
    }


def cross_group_alpha(
    units: Sequence[dict[str, T]],
    left_raters: Sequence[str],
    right_raters: Sequence[str],
    distance: Callable[[T, T], float],
) -> dict[str, float | int | str | None]:
    """Cross-group alpha analogue using separate left/right expected marginals.

    This is used for human--LLM comparison.  It has alpha's 1 - Do/De form,
    but is named explicitly because the two rater types are not interchangeable.
    """
    observed = mean(
        distance(unit[left], unit[right])
        for unit in units
        for left in left_raters
        for right in right_raters
    )
    left_pool = [unit[rater] for unit in units for rater in left_raters]
    right_pool = [unit[rater] for unit in units for rater in right_raters]
    left_counts = Counter(left_pool)
    right_counts = Counter(right_pool)
    expected = sum(
        left_count * right_count * distance(left, right)
        for left, left_count in left_counts.items()
        for right, right_count in right_counts.items()
    ) / (len(left_pool) * len(right_pool))
    alpha = None if expected == 0.0 else 1.0 - observed / expected
    return {
        "alpha": alpha,
        "observed_disagreement": observed,
        "expected_disagreement": expected,
        "units": len(units),
        "left_raters": len(left_raters),
        "right_raters": len(right_raters),
        "method": "cross_group_1_minus_Do_over_De",
    }


def pair_text(pair: Pair) -> str:
    return f"{pair[0]} > {pair[1]}"


def serialize_set(labels: SetRating) -> str:
    return " || ".join(sorted(map(pair_text, labels)))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_cases() -> tuple[list[dict[str, object]], list[dict[str, str]], list[Pair]]:
    _, taxonomy = gold.silver.read_taxonomy(gold.TAXONOMY)
    raw_reviews, human_by_text = gold.load_human_decisions(set(taxonomy))
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
        sets: dict[str, SetRating] = {
            name: frozenset(gold.ordered_model_pairs(results[str(canonical)]))
            for name, results in models.items()
        }
        sets.update({name: decision.labels for name, decision in humans.items()})
        cases.append({"text": text, "source_rows": source_by_text[text], "sets": sets})
    cases.sort(key=lambda item: item["source_rows"][0])  # type: ignore[index]
    return cases, raw_reviews, taxonomy


def set_units(cases: Sequence[dict[str, object]]) -> list[dict[str, SetRating]]:
    return [case["sets"] for case in cases]  # type: ignore[misc]


def alpha_for_group(
    units: Sequence[dict[str, T]], group: str, distance: Callable[[T, T], float]
) -> dict[str, float | int | str | None]:
    if group == "human_llm":
        return cross_group_alpha(units, HUMAN_RATERS, LLM_RATERS, distance)
    return krippendorff_alpha(units, GROUP_RATERS[group], distance)


def summarize_group(cases: Sequence[dict[str, object]], group: str) -> dict[str, object]:
    pairs = PAIR_GROUPS[group]
    units = set_units(cases)
    distances = [
        jaccard_distance(unit[left], unit[right])
        for unit in units
        for left, right in pairs
    ]
    exact = [
        unit[left] == unit[right]
        for unit in units
        for left, right in pairs
    ]
    count_differences = [
        abs(len(unit[left]) - len(unit[right]))
        for unit in units
        for left, right in pairs
    ]
    alpha = alpha_for_group(units, group, jaccard_distance)
    raters = tuple(dict.fromkeys(rater for pair in pairs for rater in pair))
    summary: dict[str, object] = {
        "stories": len(cases),
        "rater_pairs_per_story": len(pairs),
        "pair_observations": len(distances),
        "mean_jaccard_distance": mean(distances),
        "alpha_jaccard": alpha["alpha"],
        "observed_disagreement": alpha["observed_disagreement"],
        "expected_disagreement": alpha["expected_disagreement"],
        "exact_set_agreements": sum(exact),
        "exact_set_agreement_rate": mean(map(float, exact)),
        "mean_absolute_label_count_difference": mean(count_differences),
        "mean_labels_per_rating": mean(len(unit[rater]) for unit in units for rater in raters),
    }
    if group == "human_llm":
        summary["alpha_interpretation"] = "cross-group alpha analogue; separate human and LLM marginals"
        summary["mean_labels_per_human_rating"] = mean(
            len(unit[rater]) for unit in units for rater in HUMAN_RATERS
        )
        summary["mean_labels_per_llm_rating"] = mean(
            len(unit[rater]) for unit in units for rater in LLM_RATERS
        )
    return summary


def bootstrap(
    cases: Sequence[dict[str, object]], iterations: int = BOOTSTRAP_ITERATIONS
) -> tuple[dict[str, dict[str, list[float] | int]], list[dict[str, object]]]:
    rng = random.Random(BOOTSTRAP_SEED)
    draws: list[dict[str, object]] = []
    values = {
        group: {"mean_jaccard_distance": [], "alpha_jaccard": []}
        for group in PAIR_GROUPS
    }
    for iteration in range(1, iterations + 1):
        sample = [cases[rng.randrange(len(cases))] for _ in cases]
        for group in PAIR_GROUPS:
            result = summarize_group(sample, group)
            row = {
                "iteration": iteration,
                "group": group,
                "mean_jaccard_distance": result["mean_jaccard_distance"],
                "alpha_jaccard": result["alpha_jaccard"],
            }
            draws.append(row)
            values[group]["mean_jaccard_distance"].append(float(row["mean_jaccard_distance"]))
            if row["alpha_jaccard"] is not None:
                values[group]["alpha_jaccard"].append(float(row["alpha_jaccard"]))

    intervals: dict[str, dict[str, list[float] | int]] = {}
    for group, metrics in values.items():
        intervals[group] = {
            "iterations": iterations,
            "finite_alpha_iterations": len(metrics["alpha_jaccard"]),
            "mean_jaccard_distance_95_ci": confidence_interval(metrics["mean_jaccard_distance"]),
            "alpha_jaccard_95_ci": confidence_interval(metrics["alpha_jaccard"]),
        }
    return intervals, draws


def nominal_distance(left: bool, right: bool) -> float:
    return float(left != right)


def label_level_rows(
    cases: Sequence[dict[str, object]], taxonomy: Sequence[Pair]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    units = set_units(cases)
    summaries: list[dict[str, object]] = []
    pairwise: list[dict[str, object]] = []
    for category, subcategory in taxonomy:
        label = (category, subcategory)
        binary_units = [
            {rater: label in unit[rater] for rater in RATERS}
            for unit in units
        ]
        alpha = krippendorff_alpha(binary_units, RATERS, nominal_distance)
        selected_by_any = sum(any(unit.values()) for unit in binary_units)
        summary: dict[str, object] = {
            "category": category,
            "subcategory": subcategory,
            "stories_selected_by_any_rater": selected_by_any,
            "nominal_alpha_all_five": alpha["alpha"],
            "observed_nominal_disagreement": alpha["observed_disagreement"],
            "expected_nominal_disagreement": alpha["expected_disagreement"],
        }
        for rater in RATERS:
            selected = sum(unit[rater] for unit in binary_units)
            summary[f"{rater}_selected"] = selected
            summary[f"{rater}_prevalence"] = selected / len(binary_units)
        summaries.append(summary)

        for left, right in itertools.combinations(RATERS, 2):
            left_positive = {index for index, unit in enumerate(binary_units) if unit[left]}
            right_positive = {index for index, unit in enumerate(binary_units) if unit[right]}
            intersection = len(left_positive & right_positive)
            union = len(left_positive | right_positive)
            denominator = len(left_positive) + len(right_positive)
            pairwise.append({
                "category": category,
                "subcategory": subcategory,
                "left_rater": left,
                "right_rater": right,
                "left_selected": len(left_positive),
                "right_selected": len(right_positive),
                "both_selected": intersection,
                "positive_jaccard": intersection / union if union else None,
                "positive_dice_f1": 2 * intersection / denominator if denominator else None,
            })
    return summaries, pairwise


def write_csv(path: Path, rows: Sequence[dict[str, object]], fieldnames: Sequence[str] | None = None) -> None:
    if not rows and not fieldnames:
        raise ValueError(f"cannot infer fields for empty CSV {path}")
    fields = list(fieldnames or rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    cases, raw_reviews, taxonomy = load_cases()
    units = set_units(cases)
    summaries = {group: summarize_group(cases, group) for group in PAIR_GROUPS}
    intervals, bootstrap_draws = bootstrap(cases)
    for group in summaries:
        summaries[group].update(intervals[group])

    rater_summary = {
        rater: {
            "mean_label_count": mean(len(unit[rater]) for unit in units),
            "label_count_distribution": dict(sorted(Counter(len(unit[rater]) for unit in units).items())),
        }
        for rater in RATERS
    }

    rater_rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []
    disagreement_rows: list[dict[str, object]] = []
    for story_index, case in enumerate(cases, start=1):
        sets: dict[str, SetRating] = case["sets"]  # type: ignore[assignment]
        source_rows: list[int] = case["source_rows"]  # type: ignore[assignment]
        for rater in RATERS:
            rater_rows.append({
                "story_index": story_index,
                "canonical_source_row": source_rows[0],
                "source_row_aliases": ";".join(map(str, source_rows)),
                "rater": rater,
                "rater_type": "human" if rater in HUMAN_RATERS else "llm",
                "label_count": len(sets[rater]),
                "label_set": serialize_set(sets[rater]),
            })
        for left, right in itertools.combinations(RATERS, 2):
            pair_rows.append({
                "story_index": story_index,
                "canonical_source_row": source_rows[0],
                "left_rater": left,
                "right_rater": right,
                "pair_type": "human_human" if left in HUMAN_RATERS and right in HUMAN_RATERS else (
                    "llm_llm" if left in LLM_RATERS and right in LLM_RATERS else "human_llm"
                ),
                "jaccard_distance": jaccard_distance(sets[left], sets[right]),
                "exact_set_match": int(sets[left] == sets[right]),
                "absolute_label_count_difference": abs(len(sets[left]) - len(sets[right])),
            })
        if sets["jackie"] != sets["qs"]:
            votes: Counter[Pair] = Counter()
            for rater in RATERS:
                votes.update(sets[rater])
            disagreement_rows.append({
                "canonical_source_row": source_rows[0],
                "source_row_aliases": ";".join(map(str, source_rows)),
                "problem_description": case["text"],
                "human_jaccard_distance": jaccard_distance(sets["jackie"], sets["qs"]),
                "jackie_labels": serialize_set(sets["jackie"]),
                "qs_labels": serialize_set(sets["qs"]),
                "gpt52_labels": serialize_set(sets["gpt52"]),
                "gemini31_pro_labels": serialize_set(sets["gemini31_pro"]),
                "deepseek_v4_labels": serialize_set(sets["deepseek_v4"]),
                "five_rater_votes": " || ".join(
                    f"{pair_text(pair)} [{count}/5]" for pair, count in votes.most_common()
                ),
            })
    disagreement_rows.sort(key=lambda row: (row["human_jaccard_distance"], row["canonical_source_row"]), reverse=True)

    duplicate_groups: dict[tuple[str, str], list[SetRating]] = defaultdict(list)
    for row in raw_reviews:
        reviewer = row["reviewer_key"].strip().lower()
        if reviewer in gold.HUMAN_REVIEWERS and row["status"] in gold.ELIGIBLE_STATUSES:
            duplicate_groups[(row["problem_description"], reviewer)].append(gold.label_set(row))
    repeated = [sets for sets in duplicate_groups.values() if len(sets) > 1]

    label_summaries, label_pairwise = label_level_rows(cases, taxonomy)
    inputs = [gold.SOURCE, gold.TAXONOMY, gold.REVIEWS, *gold.MODEL_FILES.values()]
    report = {
        "method": {
            "annotation_unit": "unordered set of exact category/subcategory pairs",
            "independent_sampling_unit": "unique problem description",
            "jaccard_distance": "1 - |intersection| / |union|; distance(empty, empty) = 0",
            "alpha_jaccard": "1 - observed mean Jaccard distance / expected pooled Jaccard distance",
            "human_llm_alpha": "cross-group analogue with expected distance from separate pooled human and LLM marginals",
            "bootstrap": {
                "unit": "story",
                "iterations": BOOTSTRAP_ITERATIONS,
                "seed": BOOTSTRAP_SEED,
                "interval": "2.5th and 97.5th percentiles with linear interpolation",
            },
        },
        "scope": {
            "raw_review_records": len(raw_reviews),
            "unique_reviewed_stories": len(cases),
            "raters": list(RATERS),
            "taxonomy_labels": len(taxonomy),
            "duplicate_source_descriptions_excluded_from_story_count": sum(len(case["source_rows"]) - 1 for case in cases),  # type: ignore[arg-type]
        },
        "comparison_summary": summaries,
        "rater_summary": rater_summary,
        "duplicate_review_stability": {
            "repeated_story_reviewer_pairs": len(repeated),
            "exactly_repeated_label_sets": sum(len(set(sets)) == 1 for sets in repeated),
            "resolution": "latest eligible saved decision per reviewer used for each unique story",
        },
        "reproducibility": {
            "script": Path(__file__).name,
            "python": platform.python_version(),
            "input_sha256": {str(path): file_sha256(path) for path in inputs},
            "intermediate_files": [
                "rater_sets.csv",
                "story_pairwise_set_distances.csv",
                "comparison_summary.csv",
                "comparison_bootstrap.csv",
                "label_level_summary.csv",
                "label_level_pairwise_positive_agreement.csv",
                "human_disagreements.csv",
            ],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "rater_agreement_analysis.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(OUT_DIR / "rater_sets.csv", rater_rows)
    write_csv(OUT_DIR / "story_pairwise_set_distances.csv", pair_rows)
    comparison_rows = []
    for group, summary in summaries.items():
        row = {"group": group, **summary}
        for key, value in list(row.items()):
            if isinstance(value, list):
                row[key] = "" if value is None else ";".join(f"{number:.12g}" for number in value)
        comparison_rows.append(row)
    write_csv(
        OUT_DIR / "comparison_summary.csv",
        comparison_rows,
        fieldnames=list(dict.fromkeys(key for row in comparison_rows for key in row)),
    )
    write_csv(OUT_DIR / "comparison_bootstrap.csv", bootstrap_draws)
    write_csv(OUT_DIR / "label_level_summary.csv", label_summaries)
    write_csv(OUT_DIR / "label_level_pairwise_positive_agreement.csv", label_pairwise)
    write_csv(OUT_DIR / "human_disagreements.csv", disagreement_rows)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
