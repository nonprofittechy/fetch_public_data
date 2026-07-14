#!/usr/bin/env python3
"""Reproduce the expanded-vs-On-Wednesdays comparison artifacts.

The current-run input is the committed order-independent scenario-details CSV.
Published paper values are constants transcribed from Tables 4 and 5. When the
original FETCH checkout is available, the script also verifies that all 200
legacy opening queries and hidden facts were copied without textual changes.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


HERE = Path(__file__).resolve().parent
DETAILS = HERE / "analysis/runs/all_scenario_details.csv"
CANDIDATES = HERE / "candidates/expanded_flip_candidates_1000.csv"
OUT_JSON = HERE / "analysis/on_wednesdays_difference_summary.json"
OUT_CSV = HERE / "analysis/on_wednesdays_pair_comparison.csv"
ORIGINAL_LEGACY = Path("/home/quinten/fetch/promptfoo/individual_facts/classification_flip_scenarios.csv")
ORIGINAL_RESULTS = Path("/home/quinten/fetch/results/followup_fact_results.json")

PAPER_PAIRS = {
    "custody_vs_support": (100.0, 85.0, 100.0),
    "domestic_violence": (100.0, 10.0, 100.0),
    "dui_vs_dmv": (100.0, 100.0, 90.0),
    "tenant_vs_landlord": (95.0, 95.0, 94.7),
    "debtor_vs_creditor": (80.0, 55.0, 72.7),
    "employee_vs_employer": (80.0, 90.0, 61.1),
    "employment_admin": (65.0, 20.0, 0.0),
    "bankruptcy_vs_collections": (50.0, 45.0, 88.9),
    "injury_location": (100.0, 95.0, 26.3),
    "criminal_vs_restraining": (0.0, 95.0, 15.8),
}


def yes(row: dict, field: str) -> bool:
    return row[field].lower() == "true"


def pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 2) if d else None


def metrics(rows: list[dict]) -> dict:
    matched = [r for r in rows if yes(r, "question_matched")]
    rescue = sum(not yes(r, "initial_category_correct") and yes(r, "final_category_correct") for r in matched)
    # This exactly mirrors the paper analysis code: "harm" requires an
    # initially correct case, a wrong final target, and a changed serialized
    # first category. It is retained only for historical comparison.
    paper_harm = sum(
        yes(r, "initial_category_correct")
        and not yes(r, "final_category_correct")
        and yes(r, "top_category_changed")
        for r in matched
    )
    neutral_failure = sum(
        yes(r, "initial_category_correct")
        and not yes(r, "final_category_correct")
        and not yes(r, "top_category_changed")
        for r in matched
    )
    return {
        "cases": len(rows),
        "initial_category_present_pct": pct(sum(yes(r, "initial_category_correct") for r in rows), len(rows)),
        "question_coverage_pct": pct(len(matched), len(rows)),
        "matched_cases": len(matched),
        "final_category_present_when_matched_pct": pct(sum(yes(r, "final_category_correct") for r in matched), len(matched)),
        "paper_style_rescued": rescue,
        "paper_style_harmed": paper_harm,
        "paper_style_neutral_failure_to_flip": neutral_failure,
        "paper_style_rescue_to_harm_ratio": round(rescue / paper_harm, 2) if paper_harm else None,
        "expected_final_category_added": sum(yes(r, "expected_final_category_added") for r in matched),
        "expected_final_category_lost": sum(
            yes(r, "expected_final_category_present_initially") and not yes(r, "final_category_correct") for r in matched
        ),
        "expected_final_exact_added": sum(
            yes(r, "expected_final_exact_added") for r in matched if yes(r, "final_exact_scorable")
        ),
        "expected_final_exact_lost": sum(
            yes(r, "expected_final_exact_present_initially") and not yes(r, "final_subcategory_correct")
            for r in matched if yes(r, "final_exact_scorable")
        ),
    }


def main() -> None:
    with DETAILS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    by_source = {
        source: metrics([r for r in rows if r["source_stratum"] == source])
        for source in ("legacy_200_snapshot", "expanded_workbook_grounded")
    }
    by_run_legacy = {
        run: metrics([r for r in rows if r["run"] == run and r["source_stratum"] == "legacy_200_snapshot"])
        for run in sorted({r["run"] for r in rows})
    }

    pair_rows = []
    for pair, (paper_initial, paper_coverage, paper_final) in PAPER_PAIRS.items():
        current = [r for r in rows if r["source_stratum"] == "legacy_200_snapshot" and r["swap_pair"] == pair]
        current_metrics = metrics(current)
        pair_rows.append({
            "swap_pair": pair,
            "paper_initial_pct": paper_initial,
            "current_initial_pct": current_metrics["initial_category_present_pct"],
            "initial_delta_points": round(current_metrics["initial_category_present_pct"] - paper_initial, 2),
            "paper_coverage_pct": paper_coverage,
            "current_coverage_pct": current_metrics["question_coverage_pct"],
            "coverage_delta_points": round(current_metrics["question_coverage_pct"] - paper_coverage, 2),
            "paper_final_pct_when_matched": paper_final,
            "current_final_pct_when_matched": current_metrics["final_category_present_when_matched_pct"],
            "final_delta_points": round(current_metrics["final_category_present_when_matched_pct"] - paper_final, 2),
            "current_pooled_cases": len(current),
            "current_matched_cases": current_metrics["matched_cases"],
        })

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    copy_check = {"performed": False}
    copied_id_by_current = {}
    if ORIGINAL_LEGACY.exists():
        with ORIGINAL_LEGACY.open(newline="", encoding="utf-8-sig") as handle:
            original = {r["scenario_id"]: r for r in csv.DictReader(handle)}
        with CANDIDATES.open(newline="", encoding="utf-8") as handle:
            copied = {
                r["source_legacy_scenario_id"]: r
                for r in csv.DictReader(handle) if r["source_stratum"] == "legacy_200_snapshot"
            }
        copied_id_by_current = {row["scenario_id"]: original_id for original_id, row in copied.items()}
        fields = ("opening_query", "hidden_fact", "fact_as_answer", "relevant_question_topic")
        copy_check = {
            "performed": True,
            "original_rows": len(original),
            "copied_rows": len(copied),
            "text_mismatches": {field: sum(original[k][field] != copied[k][field] for k in original) for field in fields},
        }

    paired_check = {"performed": False}
    if ORIGINAL_RESULTS.exists() and copied_id_by_current:
        raw_doc = json.loads(ORIGINAL_RESULTS.read_text())
        original_outcomes = {}
        for item in raw_doc.get("results", {}).get("results", []):
            response = item.get("response") or {}
            raw = (response.get("metadata") or {}).get("raw_json") or response.get("output") or "{}"
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                continue
            original_outcomes[(item.get("vars") or {}).get("scenario_id", "")] = result
        paired_runs = {}
        for run in sorted({r["run"] for r in rows}):
            current = {
                copied_id_by_current[r["scenario_id"]]: r
                for r in rows if r["run"] == run and r["source_stratum"] == "legacy_200_snapshot"
            }
            match = defaultdict(int)
            initial = defaultdict(int)
            final_both_matched = defaultdict(int)
            for scenario_id, original in original_outcomes.items():
                row = current[scenario_id]
                old_match = bool(original.get("question_matched"))
                new_match = yes(row, "question_matched")
                match[f"paper_{old_match}_current_{new_match}"] += 1
                initial[f"paper_{bool(original.get('initial_category_correct'))}_current_{yes(row, 'initial_category_correct')}"] += 1
                if old_match and new_match:
                    final_both_matched[
                        f"paper_{bool(original.get('final_category_correct'))}_current_{yes(row, 'final_category_correct')}"
                    ] += 1
            paired_runs[run] = {
                "question_match_transition": dict(match),
                "initial_category_transition": dict(initial),
                "final_category_transition_among_cases_matched_in_both": dict(final_both_matched),
            }
        paired_check = {
            "performed": True,
            "paper_result_rows": len(original_outcomes),
            "by_current_run": paired_runs,
        }

    composition = {}
    for source in by_source:
        group = [r for r in rows if r["source_stratum"] == source]
        same = [r for r in group if r["expected_initial_label_canonical"].split(" > ")[0] == r["expected_final_label_canonical"].split(" > ")[0]]
        cross = [r for r in group if r not in same]
        composition[source] = {
            "same_top_category_pct": pct(len(same), len(group)),
            "same_category_question_coverage_pct": pct(sum(yes(r, "question_matched") for r in same), len(same)),
            "cross_category_question_coverage_pct": pct(sum(yes(r, "question_matched") for r in cross), len(cross)),
            "opening_query_mean_words": round(mean(len(r["opening_query"].split()) for r in group), 2),
            "hidden_fact_mean_words": round(mean(len(r["hidden_fact"].split()) for r in group), 2),
        }

    output = {
        "paper_overall": {
            "cases": 200,
            "initial_category_present_pct": 77.0,
            "question_coverage_pct": 69.0,
            "matched_cases": 138,
            "final_category_present_when_matched_pct": 65.2,
            "rescued": 18,
            "harmed": 4,
            "rescue_to_harm_ratio": 4.5,
        },
        "current_by_source": by_source,
        "current_legacy_by_run": by_run_legacy,
        "composition": composition,
        "legacy_text_copy_check": copy_check,
        "paired_same_scenario_check": paired_check,
        "notes": [
            "Current legacy metrics pool the same 200 scenarios across three uncached runs (600 observations).",
            "The historical harm metric depends on a changed serialized first category; it is not an order-independent criterion.",
            "Expected-final additions/losses are the symmetric order-independent diagnostic.",
        ],
    }
    OUT_JSON.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} and {OUT_CSV}")


if __name__ == "__main__":
    main()
