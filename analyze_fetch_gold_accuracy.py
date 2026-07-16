#!/usr/bin/env python3
"""Score FETCH Promptfoo outputs against the multi-label consensus gold set.

The report distinguishes exact sublabel retrieval, partial exact retrieval, and
top-level-category-only routing.  It also makes legacy/current OSB taxonomy
compatibility explicit so punctuation changes are not counted as model errors.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


# One-to-one legacy/current taxonomy identifier changes. Values are the current
# FETCH identifiers. Keys not listed here are normalized mechanically only.
LABEL_ALIASES = {
    "Administrative Law > SSD (Social Security Disability)": "Administrative Law > Social Security/SSI",
    "Administrative Law > Schools - Special Needs Edu.": "Administrative Law > Schools — Special Needs Education",
    "Business & Corporate > Agriculture/Farm": "Business and Corporate > Agriculture/Farm",
    "Business & Corporate > Entertainment": "Business and Corporate > Entertainment",
    "Business & Corporate > Environment": "Business and Corporate > Environmental",
    "Business & Corporate > General (Contracts, Business, Organization)": "Business and Corporate > General (contracts, entities)",
    "Business & Corporate > Litigation": "Business and Corporate > Litigation",
    "Business & Corporate > Marijuana Business": "Business and Corporate > Marijuana Business",
    "Business & Corporate > Non-Profit": "Business and Corporate > Non-Profit",
    "Business & Corporate > Restaurant/OLCC": "Business and Corporate > Restaurants/OLCC",
    "Business & Corporate > Sale of Business": "Business and Corporate > Sale Of Business",
    "Business & Corporate > Securities": "Business and Corporate > Securities",
    "Criminal Law > Lessor Felony": "Criminal Law > Lesser Felony",
    "Criminal Law > Post Conviction/ Appeals": "Criminal Law > Post Conviction/Appeals",
    "Consumer Law > Automobiles/RVs/Mobile Homes": "Consumer Law > Automobiles/RV's/Mobile Homes",
    "Debtor/Creditor > Judgement Collection": "Debtor/Creditor > Judgment Collection",
    "Family Law > Birth Certificate/Name Changes": "Family Law > Birth Certificate/Name Change",
    "Family Law > General (Divorce/Separation)": "Family Law > General (Divorce/Separation etc.)",
    "Family Law > Guardianship(minor)": "Family Law > Guardianship",
    "Family Law > Juvenile/DHS Issue - SCF (CSD) related": "Family Law > Juvenile/DHS Issues",
    "General Litigation > Malpractice-Dental": "General Litigation > Malpractice (Dental)",
    "General Litigation > Malpractice-Legal": "General Litigation > Malpractice (Legal)",
    "General Litigation > Malpractice-Medical": "General Litigation > Malpractice (Medical)",
    "General Litigation > Online Harassment/Doxing/Bullying": "General Litigation > Online Harrassment/Doxing/Bullying",
    "International Law > Business and Corporate": "International Law > Business And Corporate",
    "International Law > Gen. Immigration/Visas": "International Law > General Immigration/Visas",
    "Real Property > Government Loans (VA,FHA,Etc.)": "Real Property > Government Loans (VA, FHA, etc.)",
    "Workers' Comp > Third Party litigation": "Workers' Comp > Third Party Litigation",
    "Wills & Trusts > General (Wills, Trusts, Estates)": "Wills & Trusts > General (Wills/Trusts/Estates)",
}

# The old taxonomy did not encode which side of an employment dispute was
# represented. A current side-specific child is compatible with the old gold
# concept; this is reported as a compatibility match, not a literal string match.
LABEL_EXPANSIONS = {
    "Labor & Employment > ADA (Disability) Act Issues": {
        "Labor & Employment > ADA (Disability) Act Issues - Employee",
        "Labor & Employment > ADA (Disability) Act Issues - Employer",
    },
    "Labor & Employment > Discrimination": {
        "Labor & Employment > Discrimination - Employee",
        "Labor & Employment > Discrimination - Employer",
    },
    "Labor & Employment > Document Review/Severance Packages.": {
        "Labor & Employment > Document Review/Severance Packages - Employee",
        "Labor & Employment > Document Review/Severance Packages - Employer",
    },
    "Labor & Employment > FMLA": {
        "Labor & Employment > FMLA - Employee",
        "Labor & Employment > FMLA - Employer",
    },
    "Labor & Employment > General": {
        "Labor & Employment > General - Employee",
        "Labor & Employment > General - Employer",
    },
    "Labor & Employment > Sexual Harrasment": {
        "Labor & Employment > Sexual Harassment - Employee",
        "Labor & Employment > Sexual Harassment - Employer",
    },
    "Labor & Employment > Union Issues": {
        "Labor & Employment > Union Issues - Employee",
        "Labor & Employment > Union Issues - Employer",
    },
    "Labor & Employment > Wage and Hour Claims": {
        "Labor & Employment > Wage and Hour Claims - Employee",
        "Labor & Employment > Wage and Hour Claims - Employer",
    },
    "Labor & Employment > Whistleblowers": {
        "Labor & Employment > Whistleblowers - Employee",
        "Labor & Employment > Whistleblowers - Employer",
    },
    "Labor & Employment > Wrongful Discharge": {
        "Labor & Employment > Wrongful Discharge - Employee",
        "Labor & Employment > Wrongful Discharge - Employer",
    },
}


def norm_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def canonical_label(label: str) -> str:
    label = norm_text(label)
    label = LABEL_ALIASES.get(label, label)
    if label.startswith("Business & Corporate >"):
        label = "Business and Corporate >" + label.split(">", 1)[1]
    return label.casefold()


def accepted_labels(gold_label: str) -> set[str]:
    expanded = LABEL_EXPANSIONS.get(norm_text(gold_label))
    values = expanded if expanded else {LABEL_ALIASES.get(norm_text(gold_label), norm_text(gold_label))}
    return {canonical_label(value) for value in values}


def category(label: str) -> str:
    value = norm_text(label).split(" > ", 1)[0]
    if value == "Business & Corporate":
        value = "Business and Corporate"
    return value.casefold()


def display_category(label: str) -> str:
    value = norm_text(label).split(" > ", 1)[0]
    return "Business and Corporate" if value == "Business & Corporate" else value


def load_gold(path: Path) -> tuple[dict[str, dict], list[str]]:
    rows: dict[str, dict] = {}
    fieldnames: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            description = norm_text(row["problem_description"])
            if description in rows:
                raise ValueError(f"Duplicate gold description: {description[:100]}")
            rows[description] = row
    return rows, fieldnames


def gold_labels(row: dict) -> list[str]:
    labels = []
    for idx in range(1, 5):
        cat = norm_text(row.get(f"gold_category_{idx}", ""))
        sub = norm_text(row.get(f"gold_subcategory_{idx}", ""))
        if cat and sub:
            labels.append(f"{cat} > {sub}")
    return labels


def parse_raw_json(record: dict) -> tuple[list[str], str]:
    response = record.get("response") or {}
    raw = (response.get("metadata") or {}).get("raw_json")
    if not raw:
        raw = response.get("output") or ""
        match = re.search(r"<!-- RAW_JSON:(.+?)-->", raw, flags=re.S)
        if match:
            raw = match.group(1)
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        labels = [norm_text(item.get("label", "")) for item in parsed.get("labels", [])]
        return [item for item in labels if item], norm_text(parsed.get("error", ""))
    except Exception as exc:
        return [], norm_text(record.get("error") or f"unparseable output: {exc}")


def load_promptfoo(path: Path) -> tuple[str, list[dict]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    results = doc.get("results", {}).get("results", [])
    return str(doc.get("evalId", path.stem)), results


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def pct(value: float | None) -> float | None:
    return round(100 * value, 2) if value is not None else None


def score_record(run: str, record: dict, gold: dict) -> dict:
    expected = gold_labels(gold)
    predicted, error = parse_raw_json(record)
    pred_can = {canonical_label(label) for label in predicted}
    gold_accept = [accepted_labels(label) for label in expected]
    exact_flags = [bool(options & pred_can) for options in gold_accept]
    compatible_pred_flags = [any(canonical_label(label) in options for options in gold_accept) for label in predicted]

    gold_categories = {category(label) for label in expected}
    predicted_categories = {category(label) for label in predicted}
    exact_hits = sum(exact_flags)
    category_hits = len(gold_categories & predicted_categories)
    gold_label_category_flags = [category(label) in predicted_categories for label in expected]
    category_supported_labels = sum(gold_label_category_flags)
    category_only_labels = sum(cat_ok and not exact for cat_ok, exact in zip(gold_label_category_flags, exact_flags))

    if exact_hits == len(expected):
        tier = "all_exact_sublabels"
    elif exact_hits:
        tier = "some_exact_sublabels"
    elif category_hits:
        tier = "top_level_only"
    else:
        tier = "no_correct_category"

    all_predictions_compatible = bool(predicted) and all(compatible_pred_flags)
    return {
        "run": run,
        "scenario_id": gold.get("scenario_id", ""),
        "source_row": gold.get("source_row", ""),
        "problem_description": norm_text(gold["problem_description"]),
        "gold_labels": " || ".join(expected),
        "predicted_labels": " || ".join(predicted),
        "gold_label_count": len(expected),
        "predicted_label_count": len(predicted),
        "exact_hits": exact_hits,
        "exact_recall": round(safe_div(exact_hits, len(expected)) or 0, 6),
        "compatible_predicted_hits": sum(compatible_pred_flags),
        "exact_precision": round(safe_div(sum(compatible_pred_flags), len(predicted)) or 0, 6),
        "any_exact_sublabel": exact_hits > 0,
        "all_exact_sublabels": exact_hits == len(expected),
        "strict_exact_set": exact_hits == len(expected) and all_predictions_compatible,
        "gold_category_count": len(gold_categories),
        "predicted_category_count": len(predicted_categories),
        "category_hits": category_hits,
        "category_recall": round(safe_div(category_hits, len(gold_categories)) or 0, 6),
        "any_correct_top_level": category_hits > 0,
        "all_correct_top_levels": category_hits == len(gold_categories),
        "category_supported_gold_labels": category_supported_labels,
        "category_only_gold_labels": category_only_labels,
        "graded_retrieval_score": round(safe_div(exact_hits + 0.5 * category_only_labels, len(expected)) or 0, 6),
        "outcome_tier": tier,
        "provider_error": error,
        "promptfoo_success": record.get("success", ""),
        "latency_ms": record.get("latencyMs", ""),
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    tiers = Counter(row["outcome_tier"] for row in rows)
    gold_total = sum(int(row["gold_label_count"]) for row in rows)
    pred_total = sum(int(row["predicted_label_count"]) for row in rows)
    exact_hits = sum(int(row["exact_hits"]) for row in rows)
    pred_hits = sum(int(row["compatible_predicted_hits"]) for row in rows)
    category_only = sum(int(row["category_only_gold_labels"]) for row in rows)
    precision = safe_div(pred_hits, pred_total)
    recall = safe_div(exact_hits, gold_total)
    f1 = safe_div(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
    return {
        "scenarios": n,
        "provider_error_scenarios": sum(bool(row["provider_error"]) for row in rows),
        "outcome_tiers": {key: {"n": tiers[key], "pct": pct(safe_div(tiers[key], n))} for key in [
            "all_exact_sublabels", "some_exact_sublabels", "top_level_only", "no_correct_category"
        ]},
        "any_exact_sublabel_pct": pct(safe_div(sum(bool(row["any_exact_sublabel"]) for row in rows), n)),
        "all_exact_sublabels_pct": pct(safe_div(sum(bool(row["all_exact_sublabels"]) for row in rows), n)),
        "strict_exact_set_pct": pct(safe_div(sum(bool(row["strict_exact_set"]) for row in rows), n)),
        "any_correct_top_level_pct": pct(safe_div(sum(bool(row["any_correct_top_level"]) for row in rows), n)),
        "all_correct_top_levels_pct": pct(safe_div(sum(bool(row["all_correct_top_levels"]) for row in rows), n)),
        "mean_exact_gold_coverage_pct": pct(mean(float(row["exact_recall"]) for row in rows)) if rows else None,
        "mean_graded_retrieval_score_pct": pct(mean(float(row["graded_retrieval_score"]) for row in rows)) if rows else None,
        "micro_exact_precision_pct": pct(precision),
        "micro_exact_recall_pct": pct(recall),
        "micro_exact_f1_pct": pct(f1),
        "gold_label_instances": gold_total,
        "exact_gold_label_hits": exact_hits,
        "category_only_gold_label_hits": category_only,
    }


def grouped(rows: list[dict], key_fn) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        for key in key_fn(row):
            groups[str(key)].append(row)
    output = []
    for key in sorted(groups):
        item = {"group": key}
        item.update(summarize(groups[key]))
        output.append(item)
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cross_run(rows_by_run: dict[str, list[dict]]) -> dict:
    by_scenario: dict[str, dict[str, dict]] = defaultdict(dict)
    for run, rows in rows_by_run.items():
        for row in rows:
            by_scenario[row["scenario_id"]][run] = row
    complete = [values for values in by_scenario.values() if len(values) == len(rows_by_run)]
    if len(rows_by_run) < 2 or not complete:
        return {"complete_scenarios": len(complete)}
    tier_stable = sum(len({row["outcome_tier"] for row in values.values()}) == 1 for values in complete)
    exact_any_stable = sum(len({bool(row["any_exact_sublabel"]) for row in values.values()}) == 1 for values in complete)
    all_exact_every_run = sum(all(row["all_exact_sublabels"] for row in values.values()) for values in complete)
    any_exact_every_run = sum(all(row["any_exact_sublabel"] for row in values.values()) for values in complete)
    prediction_jaccards = []
    identical_predictions = 0
    for values in complete:
        prediction_sets = [
            {canonical_label(label) for label in row["predicted_labels"].split(" || ") if label}
            for row in values.values()
        ]
        pair_scores = []
        for left_index in range(len(prediction_sets)):
            for right_index in range(left_index + 1, len(prediction_sets)):
                left, right = prediction_sets[left_index], prediction_sets[right_index]
                pair_scores.append(len(left & right) / len(left | right) if left | right else 1.0)
        prediction_jaccards.append(mean(pair_scores))
        identical_predictions += len({frozenset(labels) for labels in prediction_sets}) == 1
    return {
        "complete_scenarios": len(complete),
        "outcome_tier_stable_pct": pct(safe_div(tier_stable, len(complete))),
        "any_exact_status_stable_pct": pct(safe_div(exact_any_stable, len(complete))),
        "all_exact_in_every_run_pct": pct(safe_div(all_exact_every_run, len(complete))),
        "any_exact_in_every_run_pct": pct(safe_div(any_exact_every_run, len(complete))),
        "identical_predicted_set_pct": pct(safe_div(identical_predictions, len(complete))),
        "mean_predicted_set_jaccard_pct": pct(mean(prediction_jaccards)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--run", action="append", required=True, help="NAME=promptfoo.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    gold, _ = load_gold(args.gold)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows_by_run: dict[str, list[dict]] = {}
    run_metadata = {}
    unmatched_by_run = {}
    all_rows = []

    for spec in args.run:
        name, raw_path = spec.split("=", 1)
        eval_id, records = load_promptfoo(Path(raw_path))
        scored = []
        unmatched = []
        duplicate_records = []
        seen = set()
        for record in records:
            description = norm_text((record.get("vars") or {}).get("problem_description", ""))
            if description not in gold:
                unmatched.append(description)
                continue
            scenario_id = gold[description].get("scenario_id", description)
            if scenario_id in seen:
                # A run launched from an older exact-string-deduplicated CSV can
                # contain the one whitespace-only alias. Keep the canonical
                # first occurrence and disclose the collapsed result.
                duplicate_records.append(scenario_id)
                continue
            seen.add(scenario_id)
            scored.append(score_record(name, record, gold[description]))
        rows_by_run[name] = scored
        all_rows.extend(scored)
        run_metadata[name] = {
            "eval_id": eval_id,
            "raw_records": len(records),
            "matched_gold_records": len(scored),
            "unmatched_run_records": len(unmatched),
            "collapsed_duplicate_run_records": len(duplicate_records),
            "collapsed_duplicate_scenario_ids": duplicate_records,
            "missing_gold_records": len(gold) - len(scored),
        }
        unmatched_by_run[name] = unmatched

    summaries = {name: summarize(rows) for name, rows in rows_by_run.items()}
    report = {
        "schema": "fetch_gold_accuracy_v1",
        "gold_scenarios": len(gold),
        "run_metadata": run_metadata,
        "run_summaries": summaries,
        "pooled_summary": summarize(all_rows),
        "cross_run": cross_run(rows_by_run),
        "taxonomy_compatibility": {
            "one_to_one_aliases": LABEL_ALIASES,
            "legacy_to_current_expansions": {key: sorted(value) for key, value in LABEL_EXPANSIONS.items()},
        },
        "unmatched_run_descriptions": unmatched_by_run,
    }
    (args.output_dir / "accuracy_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_csv(args.output_dir / "scenario_results.csv", all_rows)

    gold_count_rows = []
    category_rows = []
    for name, rows in rows_by_run.items():
        for item in grouped(rows, lambda row: [row["gold_label_count"]]):
            gold_count_rows.append({"run": name, **item})
        # A scenario can contribute to multiple categories; this is intentional.
        for item in grouped(rows, lambda row: sorted({display_category(label) for label in row["gold_labels"].split(" || ")})):
            category_rows.append({"run": name, **item})
    for item in grouped(all_rows, lambda row: [row["gold_label_count"]]):
        gold_count_rows.append({"run": "pooled", **item})
    for item in grouped(all_rows, lambda row: sorted({display_category(label) for label in row["gold_labels"].split(" || ")})):
        category_rows.append({"run": "pooled", **item})
    write_csv(args.output_dir / "metrics_by_gold_label_count.csv", gold_count_rows)
    write_csv(args.output_dir / "metrics_by_top_level_category.csv", category_rows)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
