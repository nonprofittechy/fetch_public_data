#!/usr/bin/env python3
"""Create per-run and cross-run evidence artifacts from PromptFoo JSON."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
ANALYSIS_RUNS = HERE / "analysis/runs"

DETAIL_FIELDS = [
    "run", "scenario_id", "condition", "swap_pair", "direction", "source_stratum",
    "paper_failure_mode", "multi_label_grounded", "domestic_violence_hidden_fact",
    "domestic_violence_explicit_probe",
    "opening_query", "hidden_fact", "expected_initial_label", "expected_initial_label_canonical",
    "expected_final_label", "expected_final_label_canonical",
    "initial_top_label", "initial_labels", "initial_top_category_is_expected", "initial_top_is_expected", "initial_category_correct", "initial_subcategory_correct",
    "initial_exact_scorable", "provider_initial_category_flag", "provider_initial_exact_flag",
    "follow_up_question_count", "follow_up_questions", "question_matched",
    "matched_question", "final_top_label", "final_labels", "final_top_category_is_expected", "final_top_is_expected", "final_category_correct",
    "final_subcategory_correct", "final_exact_scorable", "provider_final_category_flag", "provider_final_exact_flag",
    "expected_final_category_present_initially", "expected_final_exact_present_initially",
    "expected_final_category_added", "expected_final_exact_added",
    "classification_changed", "top_category_changed", "provider_error",
    "latency_ms", "promptfoo_success",
]


CANONICAL_LABEL_ALIASES = {
    "Business & Corporate > General (Contracts, Business, Organization)": "Business and Corporate > General (contracts, entities)",
    "Business & Corporate > Sale of Business": "Business and Corporate > Sale Of Business",
    "Debtor/Creditor > Judgement Collection": "Debtor/Creditor > Judgment Collection",
    "Family Law > General (Divorce/Separation)": "Family Law > General (Divorce/Separation etc.)",
    "General Litigation > Malpractice-Medical": "General Litigation > Malpractice (Medical)",
    "General Litigation > Online Harassment/Doxing/Bullying": "General Litigation > Online Harrassment/Doxing/Bullying",
    "Real Property > Government Loans (VA,FHA,Etc.)": "Real Property > Government Loans (VA, FHA, etc.)",
    "Workers' Comp > Third Party litigation": "Workers' Comp > Third Party Litigation",
}

# These source labels collapse or branch in the current FETCH taxonomy. Calling
# them an exact current-taxonomy target would manufacture precision.
UNSCORABLE_EXACT_LABELS = {
    "Administrative Law > SSD (Social Security Disability)",
    "Labor & Employment > Discrimination",
    "Labor & Employment > Wage and Hour Claims",
    "Labor & Employment > Wrongful Discharge",
}


def canonical_label(label: str) -> str:
    return CANONICAL_LABEL_ALIASES.get(label, label).strip()


def category(label: str) -> str:
    cat = canonical_label(label).split(" > ", 1)[0].strip()
    return "Business and Corporate" if cat == "Business & Corporate" else cat


def category_present(labels: list[str], expected: str) -> bool:
    return any(category(label) == category(expected) for label in labels)


def exact_present(labels: list[str], expected: str) -> bool:
    target = canonical_label(expected).lower()
    return any(canonical_label(label).lower() == target for label in labels)


def exact_scorable(expected: str) -> bool:
    return expected not in UNSCORABLE_EXACT_LABELS


def pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 2) if d else None


def b(value) -> bool:
    return value is True or str(value).lower() == "true"


def parse_run(run_dir: Path) -> list[dict]:
    doc = json.loads((run_dir / "results.json").read_text())
    if doc.get("schema") == "direct_fetch_v1":
        result_items = doc.get("results", [])
    else:
        result_items = doc.get("results", {}).get("results", [])
    rows = []
    for item in result_items:
        variables = item.get("vars") or item.get("testCase", {}).get("vars", {})
        condition = item.get("provider", {}).get("label", "").replace("-hidden-fact", "")
        raw = (item.get("response") or {}).get("output")
        try:
            result = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            result = {}
        if condition == "counterfactual":
            expected_final = f"{variables.get('counterfactual_category', '')} > {variables.get('counterfactual_subcategory', '')}"
            fact = variables.get("counterfactual_hidden_fact", "")
        else:
            expected_final = f"{variables.get('final_category', '')} > {variables.get('final_subcategory', '')}"
            fact = variables.get("hidden_fact", "")
        initial = f"{variables.get('initial_category', '')} > {variables.get('initial_subcategory', '')}"
        questions = result.get("follow_up_questions") or []
        question_text = " || ".join(q.get("question", "") for q in questions)
        dv_probe = bool(re.search(
            r"\b(?:abus\w*|violen\w*|threat\w*|hurt|harm\w*|safe\w*|stalk\w*|hit|hitting|"
            r"control\w*|restraining|protective|protection|danger\w*)\b|stay away",
            question_text, re.I,
        ))
        initial_labels = [item.get("label", "") for item in (result.get("initial_labels") or [])]
        final_labels = [item.get("label", "") for item in (result.get("final_labels") or [])]
        initial_top = result.get("initial_top_label") or ""
        final_top = result.get("final_top_label") or ""
        initial_can = canonical_label(initial)
        final_can = canonical_label(expected_final)
        initial_scorable = exact_scorable(initial)
        final_scorable = exact_scorable(expected_final)
        final_category_initially = category_present(initial_labels, expected_final)
        final_exact_initially = exact_present(initial_labels, expected_final) if final_scorable else None
        final_category_after = category_present(final_labels, expected_final)
        final_exact_after = exact_present(final_labels, expected_final) if final_scorable else None
        rows.append({
            "run": run_dir.name,
            "scenario_id": variables.get("scenario_id", ""),
            "condition": condition,
            "swap_pair": variables.get("swap_pair", ""),
            "direction": variables.get("direction", ""),
            "source_stratum": variables.get("source_stratum", ""),
            "paper_failure_mode": variables.get("paper_failure_mode", ""),
            "multi_label_grounded": b(variables.get("multi_label_grounded")),
            "domestic_violence_hidden_fact": b(variables.get("domestic_violence_hidden_fact")),
            "domestic_violence_explicit_probe": dv_probe,
            "opening_query": variables.get("opening_query", ""),
            "hidden_fact": fact,
            "expected_initial_label": initial,
            "expected_initial_label_canonical": initial_can,
            "expected_final_label": expected_final,
            "expected_final_label_canonical": final_can,
            "initial_top_label": initial_top,
            "initial_labels": " || ".join(initial_labels),
            "initial_top_category_is_expected": category(initial_top) == category(initial),
            "initial_top_is_expected": initial_scorable and canonical_label(initial_top).lower() == initial_can.lower(),
            "initial_category_correct": category_present(initial_labels, initial),
            "initial_subcategory_correct": exact_present(initial_labels, initial) if initial_scorable else None,
            "initial_exact_scorable": initial_scorable,
            "provider_initial_category_flag": result.get("initial_category_correct"),
            "provider_initial_exact_flag": result.get("initial_subcategory_correct"),
            "follow_up_question_count": len(questions),
            "follow_up_questions": question_text,
            "question_matched": b(result.get("question_matched")),
            "matched_question": result.get("matched_question") or "",
            "final_top_label": final_top,
            "final_labels": " || ".join(final_labels),
            "final_top_category_is_expected": category(final_top) == category(expected_final),
            "final_top_is_expected": final_scorable and canonical_label(final_top).lower() == final_can.lower(),
            "final_category_correct": final_category_after,
            "final_subcategory_correct": final_exact_after,
            "final_exact_scorable": final_scorable,
            "provider_final_category_flag": result.get("final_category_correct"),
            "provider_final_exact_flag": result.get("final_subcategory_correct"),
            "expected_final_category_present_initially": final_category_initially,
            "expected_final_exact_present_initially": final_exact_initially,
            "expected_final_category_added": bool(final_category_after and not final_category_initially),
            "expected_final_exact_added": bool(final_exact_after and not final_exact_initially) if final_scorable else None,
            "classification_changed": bool(final_top and initial_top and final_top != initial_top),
            "top_category_changed": bool(final_top and initial_top and category(final_top) != category(initial_top)),
            "provider_error": item.get("orchestrator_error") or result.get("error") or ("missing/unparseable provider output" if not result else ""),
            "latency_ms": item.get("latencyMs") or 0,
            "promptfoo_success": b(item.get("success")),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    usable = [r for r in rows if not r["provider_error"]]
    matched = [r for r in usable if r["question_matched"]]
    initial_exact = [r for r in usable if r["initial_exact_scorable"]]
    matched_exact = [r for r in matched if r["final_exact_scorable"]]
    intended = [r for r in usable if r["condition"] == "intended"]
    intended_matched = [r for r in intended if r["question_matched"]]
    intended_matched_exact = [r for r in intended_matched if r["final_exact_scorable"]]
    counter = [r for r in usable if r["condition"] == "counterfactual"]
    counter_matched = [r for r in counter if r["question_matched"]]
    counter_matched_exact = [r for r in counter_matched if r["final_exact_scorable"]]
    dv = [r for r in usable if r["domestic_violence_hidden_fact"]]
    dv_matched = [r for r in dv if r["question_matched"]]
    dv_matched_exact = [r for r in dv_matched if r["final_exact_scorable"]]
    initially_wrong_matched = [r for r in matched if not r["initial_category_correct"]]
    transition_matrix = {
        "initial_present_final_present": sum(r["initial_category_correct"] and r["final_category_correct"] for r in matched),
        "initial_present_final_absent": sum(r["initial_category_correct"] and not r["final_category_correct"] for r in matched),
        "initial_absent_final_present": sum(not r["initial_category_correct"] and r["final_category_correct"] for r in matched),
        "initial_absent_final_absent": sum(not r["initial_category_correct"] and not r["final_category_correct"] for r in matched),
    }
    top_category_transition_matrix = {
        "initial_expected_top_category_final_expected_top_category": sum(r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] for r in matched),
        "initial_expected_top_category_final_other_top_category": sum(r["initial_top_category_is_expected"] and not r["final_top_category_is_expected"] for r in matched),
        "initial_other_top_category_final_expected_top_category": sum(not r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] for r in matched),
        "initial_other_top_category_final_other_top_category": sum(not r["initial_top_category_is_expected"] and not r["final_top_category_is_expected"] for r in matched),
    }
    paper_style_top_outcomes = {
        "initial_expected_final_expected_top_changed": sum(r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] and r["top_category_changed"] for r in matched),
        "initial_expected_final_expected_top_unchanged": sum(r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] and not r["top_category_changed"] for r in matched),
        "initial_expected_final_other_top_changed": sum(r["initial_top_category_is_expected"] and not r["final_top_category_is_expected"] and r["top_category_changed"] for r in matched),
        "initial_expected_final_other_top_unchanged": sum(r["initial_top_category_is_expected"] and not r["final_top_category_is_expected"] and not r["top_category_changed"] for r in matched),
        "initial_other_final_expected_top_changed": sum(not r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] and r["top_category_changed"] for r in matched),
        "initial_other_final_expected_top_unchanged": sum(not r["initial_top_category_is_expected"] and r["final_top_category_is_expected"] and not r["top_category_changed"] for r in matched),
        "initial_other_final_other": sum(not r["initial_top_category_is_expected"] and not r["final_top_category_is_expected"] for r in matched),
    }
    historical_paper_outcome_matrix = {
        "initial_correct_final_correct": sum(r["initial_category_correct"] and r["final_category_correct"] for r in matched),
        "neutral_failure_to_flip": sum(r["initial_category_correct"] and not r["final_category_correct"] and not r["top_category_changed"] for r in matched),
        "harmed_degraded": sum(r["initial_category_correct"] and not r["final_category_correct"] and r["top_category_changed"] for r in matched),
        "rescued": sum(not r["initial_category_correct"] and r["final_category_correct"] for r in matched),
        "initially_wrong_still_wrong": sum(not r["initial_category_correct"] and not r["final_category_correct"] for r in matched),
    }
    expected_final_set_transition = {
        "absent_initially_present_after": sum(not r["expected_final_category_present_initially"] and r["final_category_correct"] for r in matched),
        "present_initially_present_after": sum(r["expected_final_category_present_initially"] and r["final_category_correct"] for r in matched),
        "present_initially_absent_after": sum(r["expected_final_category_present_initially"] and not r["final_category_correct"] for r in matched),
        "absent_initially_absent_after": sum(not r["expected_final_category_present_initially"] and not r["final_category_correct"] for r in matched),
    }
    expected_final_exact_set_transition = {
        "absent_initially_present_after": sum(not r["expected_final_exact_present_initially"] and r["final_subcategory_correct"] for r in matched_exact),
        "present_initially_present_after": sum(r["expected_final_exact_present_initially"] and r["final_subcategory_correct"] for r in matched_exact),
        "present_initially_absent_after": sum(r["expected_final_exact_present_initially"] and not r["final_subcategory_correct"] for r in matched_exact),
        "absent_initially_absent_after": sum(not r["expected_final_exact_present_initially"] and not r["final_subcategory_correct"] for r in matched_exact),
    }
    return {
        "total_cases": len(rows),
        "usable_cases": len(usable),
        "provider_errors": len(rows) - len(usable),
        "initial_category_accuracy_pct": pct(sum(r["initial_category_correct"] for r in usable), len(usable)),
        "initial_exact_scorable_cases": len(initial_exact),
        "initial_exact_accuracy_pct": pct(sum(r["initial_subcategory_correct"] for r in initial_exact), len(initial_exact)),
        "initial_expected_category_is_top_pct": pct(sum(r["initial_top_category_is_expected"] for r in usable), len(usable)),
        "initial_expected_exact_is_top_pct": pct(sum(r["initial_top_is_expected"] for r in initial_exact), len(initial_exact)),
        "question_coverage_pct": pct(len(matched), len(usable)),
        "final_category_accuracy_when_matched_pct": pct(sum(r["final_category_correct"] for r in matched), len(matched)),
        "expected_final_category_added_when_matched_pct": pct(sum(r["expected_final_category_added"] for r in matched), len(matched)),
        "final_exact_scorable_matched_cases": len(matched_exact),
        "final_exact_accuracy_when_matched_pct": pct(sum(r["final_subcategory_correct"] for r in matched_exact), len(matched_exact)),
        "expected_final_exact_added_when_matched_pct": pct(sum(r["expected_final_exact_added"] for r in matched_exact), len(matched_exact)),
        "final_expected_category_is_top_when_matched_pct": pct(sum(r["final_top_category_is_expected"] for r in matched), len(matched)),
        "final_expected_exact_is_top_when_matched_pct": pct(sum(r["final_top_is_expected"] for r in matched_exact), len(matched_exact)),
        "classification_changed_when_matched_pct": pct(sum(r["classification_changed"] for r in matched), len(matched)),
        "top_category_changed_when_matched_pct": pct(sum(r["top_category_changed"] for r in matched), len(matched)),
        "initially_wrong_matched_count": len(initially_wrong_matched),
        "rescued_to_expected_category_count": sum(r["final_category_correct"] for r in initially_wrong_matched),
        "expected_category_transition_matrix_when_matched": transition_matrix,
        "top_category_transition_matrix_when_matched": top_category_transition_matrix,
        "paper_style_top_category_outcomes_when_matched": paper_style_top_outcomes,
        "historical_paper_outcome_matrix_when_matched": historical_paper_outcome_matrix,
        "expected_final_category_set_transition_when_matched": expected_final_set_transition,
        "expected_final_exact_set_transition_when_matched": expected_final_exact_set_transition,
        "intended": {
            "cases": len(intended),
            "question_coverage_pct": pct(len(intended_matched), len(intended)),
            "final_category_accuracy_when_matched_pct": pct(sum(r["final_category_correct"] for r in intended_matched), len(intended_matched)),
            "final_exact_scorable_matched_cases": len(intended_matched_exact),
            "final_exact_accuracy_when_matched_pct": pct(sum(r["final_subcategory_correct"] for r in intended_matched_exact), len(intended_matched_exact)),
        },
        "counterfactual": {
            "cases": len(counter),
            "question_coverage_pct": pct(len(counter_matched), len(counter)),
            "final_category_accuracy_when_matched_pct": pct(sum(r["final_category_correct"] for r in counter_matched), len(counter_matched)),
            "final_exact_scorable_matched_cases": len(counter_matched_exact),
            "final_exact_accuracy_when_matched_pct": pct(sum(r["final_subcategory_correct"] for r in counter_matched_exact), len(counter_matched_exact)),
        },
        "domestic_violence_hidden_fact": {
            "cases": len(dv),
            "question_coverage_pct": pct(len(dv_matched), len(dv)),
            "explicit_safety_or_abuse_probe_pct": pct(sum(r["domestic_violence_explicit_probe"] for r in dv), len(dv)),
            "matcher_coverage_among_explicit_probes_pct": pct(sum(r["question_matched"] for r in dv if r["domestic_violence_explicit_probe"]), sum(r["domestic_violence_explicit_probe"] for r in dv)),
            "final_category_accuracy_when_matched_pct": pct(sum(r["final_category_correct"] for r in dv_matched), len(dv_matched)),
            "final_exact_scorable_matched_cases": len(dv_matched_exact),
            "final_exact_accuracy_when_matched_pct": pct(sum(r["final_subcategory_correct"] for r in dv_matched_exact), len(dv_matched_exact)),
            "top_label_changed_when_matched_pct": pct(sum(r["classification_changed"] for r in dv_matched), len(dv_matched)),
        },
    }


def group_summary(rows: list[dict], field: str) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[str(row[field])].append(row)
    output = []
    for key, group in sorted(groups.items()):
        usable = [r for r in group if not r["provider_error"]]
        matched = [r for r in usable if r["question_matched"]]
        initial_exact = [r for r in usable if r["initial_exact_scorable"]]
        matched_exact = [r for r in matched if r["final_exact_scorable"]]
        output.append({
            field: key,
            "cases": len(group),
            "usable": len(usable),
            "initial_category_accuracy_pct": pct(sum(r["initial_category_correct"] for r in usable), len(usable)),
            "initial_expected_category_is_top_pct": pct(sum(r["initial_top_category_is_expected"] for r in usable), len(usable)),
            "initial_exact_scorable": len(initial_exact),
            "initial_expected_exact_is_top_pct": pct(sum(r["initial_top_is_expected"] for r in initial_exact), len(initial_exact)),
            "question_coverage_pct": pct(len(matched), len(usable)),
            "final_category_accuracy_when_matched_pct": pct(sum(r["final_category_correct"] for r in matched), len(matched)),
            "expected_final_category_added_when_matched_pct": pct(sum(r["expected_final_category_added"] for r in matched), len(matched)),
            "final_expected_category_is_top_when_matched_pct": pct(sum(r["final_top_category_is_expected"] for r in matched), len(matched)),
            "final_exact_scorable_matched": len(matched_exact),
            "final_exact_accuracy_when_matched_pct": pct(sum(r["final_subcategory_correct"] for r in matched_exact), len(matched_exact)),
            "expected_final_exact_added_when_matched_pct": pct(sum(r["expected_final_exact_added"] for r in matched_exact), len(matched_exact)),
            "final_expected_exact_is_top_when_matched_pct": pct(sum(r["final_top_is_expected"] for r in matched_exact), len(matched_exact)),
        })
    return output


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def quote_block(row: dict) -> str:
    questions = row["follow_up_questions"] or "[no follow-up question generated]"
    matched = row["matched_question"] or "[none]"
    final = row["final_top_label"] or "[no final classification because the fact was not elicited]"
    return (
        f"### {row['scenario_id']} — {row['condition']} — `{row['swap_pair']}`\n\n"
        f"> Opening query: “{row['opening_query']}”\n>\n"
        f"> Generated question(s): “{questions}”\n>\n"
        f"> Hidden-fact answer: “{row['hidden_fact']}”\n>\n"
        f"> Matcher-selected question: “{matched}”\n>\n"
        f"> Initial returned label set: “{row['initial_labels'] or row['initial_top_label']}”\n>\n"
        f"> Final returned label set: “{row['final_labels'] or final}”\n\n"
        f"Expected final: `{row['expected_final_label']}`; matched={row['question_matched']}; "
        f"expected category present={row['final_category_correct']}; expected exact label present={row['final_subcategory_correct']}.\n\n"
    )


def select_quotes(rows: list[dict]) -> list[dict]:
    usable = [r for r in rows if not r["provider_error"]]
    chosen, seen = [], set()
    predicates = [
        lambda r: r["domestic_violence_hidden_fact"] and r["condition"] == "intended" and not r["question_matched"],
        lambda r: r["domestic_violence_hidden_fact"] and r["condition"] == "intended" and r["final_subcategory_correct"],
        lambda r: r["paper_failure_mode"] and r["question_matched"] and not r["final_category_correct"],
        lambda r: r["paper_failure_mode"] and r["final_subcategory_correct"],
        lambda r: r["condition"] == "intended" and r["question_matched"] and r["final_subcategory_correct"],
        lambda r: r["condition"] == "counterfactual" and r["question_matched"] and r["final_subcategory_correct"],
        lambda r: r["condition"] == "intended" and not r["question_matched"],
        lambda r: r["condition"] == "intended" and r["question_matched"] and r["final_exact_scorable"] and r["final_subcategory_correct"] is False,
    ]
    for predicate in predicates:
        for row in usable:
            key = (row["scenario_id"], row["condition"])
            if key not in seen and predicate(row):
                chosen.append(row); seen.add(key); break
    return chosen


def analyze_one(run_dir: Path) -> tuple[list[dict], dict]:
    rows = parse_run(run_dir)
    out = ANALYSIS_RUNS / run_dir.name
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    console = (run_dir / "console.log").read_text(errors="replace") if (run_dir / "console.log").exists() else ""
    summary["operational_log_counts"] = {
        "gpt5_failures": len(re.findall(r"Classifier provider 'gpt-5' failed", console)),
        # Count the service's single summary line, not both that line and the
        # immediately preceding exception detail for the same timeout.
        "gpt5_timeouts": len(re.findall(r"Classifier provider 'gpt-5' failed:.*timed out", console)),
        "gemini_failures": len(re.findall(r"(?:gemini: error|Gemini: Error)", console, re.I)),
        "mistral_rate_limits": len(re.findall(r"mistral-small-2503.*rate limit", console, re.I)),
        "spot_errors": len(re.findall(r"Error with SPOT API", console)),
        "semantic_merge_timeouts": len(re.findall(r"semantic_merge timed out", console)),
    }
    write_csv(out / "scenario_details.csv", rows, DETAIL_FIELDS)
    for field in ("swap_pair", "paper_failure_mode", "source_stratum", "direction", "condition",
                  "domestic_violence_hidden_fact", "multi_label_grounded"):
        write_csv(out / f"by_{field}.csv", group_summary(rows, field))
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    quotes = select_quotes(rows)
    (out / "quote_candidates.md").write_text(
        "# Quote candidates\n\nDirect excerpts from this run's provider results.\n\n" + "".join(quote_block(r) for r in quotes)
    )
    return rows, summary


def main() -> None:
    run_dirs = []
    for path in sorted(RESULTS.glob("final_run_*")):
        if (path / "results.json").exists():
            run_dirs.append(path)
    all_rows, run_summaries = [], {}
    for run_dir in run_dirs:
        rows, summary = analyze_one(run_dir)
        all_rows.extend(rows); run_summaries[run_dir.name] = summary
    ANALYSIS_RUNS.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_RUNS / "run_summaries.json").write_text(json.dumps(run_summaries, indent=2) + "\n")
    if not run_dirs:
        print("No completed full-run result JSON files found")
        return
    metric_names = [
        "initial_category_accuracy_pct", "initial_exact_accuracy_pct", "question_coverage_pct",
        "final_category_accuracy_when_matched_pct", "final_exact_accuracy_when_matched_pct",
        "expected_final_category_added_when_matched_pct", "expected_final_exact_added_when_matched_pct",
    ]
    cross = {
        "run_count": len(run_dirs),
        "runs": list(run_summaries),
        "metrics": {},
        "pooled": summarize(all_rows),
        "operational_log_counts_across_saved_logs": {
            key: sum(s.get("operational_log_counts", {}).get(key, 0) for s in run_summaries.values())
            for key in ("gpt5_failures", "gpt5_timeouts", "gemini_failures", "mistral_rate_limits",
                        "spot_errors", "semantic_merge_timeouts")
        },
    }
    for metric in metric_names:
        values = [s[metric] for s in run_summaries.values() if s[metric] is not None]
        cross["metrics"][metric] = {
            "values": values, "mean": round(mean(values), 2),
            "population_sd": round(pstdev(values), 2) if len(values) > 1 else 0,
            "min": min(values), "max": max(values),
        }
    (ANALYSIS_RUNS / "cross_run_summary.json").write_text(json.dumps(cross, indent=2) + "\n")
    write_csv(ANALYSIS_RUNS / "all_scenario_details.csv", all_rows, DETAIL_FIELDS)
    for field in ("swap_pair", "paper_failure_mode", "source_stratum", "direction",
                  "domestic_violence_hidden_fact", "multi_label_grounded"):
        write_csv(ANALYSIS_RUNS / f"pooled_by_{field}.csv", group_summary(all_rows, field))

    by_scenario = defaultdict(list)
    for row in all_rows:
        by_scenario[row["scenario_id"]].append(row)
    stability = []
    for scenario_id, group in sorted(by_scenario.items()):
        usable = [r for r in group if not r["provider_error"]]
        label_sets = [r["final_labels"] for r in usable if r["question_matched"]]
        questions = [r["follow_up_questions"] for r in usable]
        stability.append({
            "scenario_id": scenario_id,
            "runs_observed": len(group),
            "usable_runs": len(usable),
            "question_matched_runs": sum(r["question_matched"] for r in usable),
            "domestic_violence_explicit_probe_runs": sum(r["domestic_violence_explicit_probe"] for r in usable),
            "expected_category_present_initial_runs": sum(r["initial_category_correct"] for r in usable),
            "expected_category_is_initial_top_runs": sum(r["initial_top_category_is_expected"] for r in usable),
            "expected_category_present_final_runs": sum(r["final_category_correct"] for r in usable if r["question_matched"]),
            "expected_category_is_final_top_runs": sum(r["final_top_category_is_expected"] for r in usable if r["question_matched"]),
            "final_exact_scorable_matched_runs": sum(r["final_exact_scorable"] for r in usable if r["question_matched"]),
            "expected_exact_label_present_final_runs": sum(r["final_subcategory_correct"] is True for r in usable if r["question_matched"]),
            "distinct_question_sets": len(set(questions)),
            "distinct_final_label_sets": len(set(label_sets)),
            "swap_pair": group[0]["swap_pair"],
            "domestic_violence_hidden_fact": group[0]["domestic_violence_hidden_fact"],
            "paper_failure_mode": group[0]["paper_failure_mode"],
        })
    write_csv(ANALYSIS_RUNS / "scenario_stability.csv", stability)
    cross["scenario_stability"] = {
        "question_matched_run_count_distribution": {
            str(n): sum(r["question_matched_runs"] == n for r in stability)
            for n in range(len(run_dirs) + 1)
        },
        "expected_exact_label_present_final_run_count_distribution": {
            str(n): sum(r["expected_exact_label_present_final_runs"] == n for r in stability)
            for n in range(len(run_dirs) + 1)
        },
        "expected_category_is_final_top_run_count_distribution": {
            str(n): sum(r["expected_category_is_final_top_runs"] == n for r in stability)
            for n in range(len(run_dirs) + 1)
        },
        "scenarios_with_different_question_sets_across_runs": sum(
            r["distinct_question_sets"] > 1 for r in stability
        ),
        "scenarios_with_different_final_label_sets_across_matched_runs": sum(
            r["distinct_final_label_sets"] > 1 for r in stability
        ),
    }
    (ANALYSIS_RUNS / "cross_run_summary.json").write_text(json.dumps(cross, indent=2) + "\n")
    print(json.dumps(cross, indent=2))


if __name__ == "__main__":
    main()
