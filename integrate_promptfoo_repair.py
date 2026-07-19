#!/usr/bin/env python3
"""Replace timeout-affected PromptFoo records and recompute aggregate metrics."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_DIR = Path("gold_labels_consensus_20260716/fetch_full_runs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=RUN_DIR / "baseline_raw.json")
    parser.add_argument("--repair", type=Path, default=RUN_DIR / "baseline_gpt52_repair.json")
    parser.add_argument("--repair-cases", type=Path, default=RUN_DIR / "baseline_gpt52_timeout_repair_cases.csv")
    parser.add_argument("--output", type=Path, default=RUN_DIR / "baseline_repaired_integrated.json")
    parser.add_argument("--report", type=Path, default=RUN_DIR / "baseline_repair_integration_report.json")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(record: dict[str, Any]) -> str:
    return str(record.get("vars", {}).get("problem_description", ""))


def numeric_sum(records: list[dict[str, Any]], field: str) -> float:
    return sum(float(record.get(field) or 0) for record in records)


def recompute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    named_scores: dict[str, float] = {}
    named_counts: dict[str, int] = {}
    assert_pass = assert_fail = 0
    token_keys = ("total", "prompt", "completion", "cached", "numRequests")
    assertion_tokens = {key: 0 for key in token_keys}
    for record in records:
        for name, value in (record.get("namedScores") or {}).items():
            if isinstance(value, (int, float)):
                named_scores[name] = named_scores.get(name, 0.0) + float(value)
                named_counts[name] = named_counts.get(name, 0) + 1
        components = record.get("gradingResult", {}).get("componentResults", [])
        assert_pass += sum(bool(item.get("pass")) for item in components)
        assert_fail += sum(not bool(item.get("pass")) for item in components)
        tokens = record.get("gradingResult", {}).get("tokensUsed", {})
        for key in token_keys:
            assertion_tokens[key] += int(tokens.get(key) or 0)
    passes = sum(bool(record.get("success")) for record in records)
    failures = len(records) - passes
    return {
        "score": numeric_sum(records, "score"),
        "testPassCount": passes,
        "testFailCount": failures,
        "testErrorCount": 0,
        "assertPassCount": assert_pass,
        "assertFailCount": assert_fail,
        "totalLatencyMs": int(numeric_sum(records, "latencyMs")),
        "tokenUsage": {
            "prompt": 0,
            "completion": 0,
            "cached": 0,
            "total": 0,
            "numRequests": len(records),
            "completionDetails": {"reasoning": 0, "acceptedPrediction": 0, "rejectedPrediction": 0},
            "assertions": {
                **assertion_tokens,
                "completionDetails": {"reasoning": 0, "acceptedPrediction": 0, "rejectedPrediction": 0},
            },
        },
        "namedScores": named_scores,
        "namedScoresCount": named_counts,
        "cost": numeric_sum(records, "cost"),
    }


def main() -> int:
    args = parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    repair = json.loads(args.repair.read_text(encoding="utf-8"))
    baseline_records = baseline["results"]["results"]
    repair_records = repair["results"]["results"]
    with args.repair_cases.open(encoding="utf-8-sig", newline="") as stream:
        expected = {row["problem_description"] for row in csv.DictReader(stream)}
    replacement_by_text = {text(record): record for record in repair_records}
    if len(expected) != len(repair_records) or set(replacement_by_text) != expected:
        raise ValueError("repair JSON descriptions do not exactly match the repair CSV")
    baseline_by_text = {text(record): record for record in baseline_records}
    if len(baseline_by_text) != len(baseline_records):
        raise ValueError("baseline descriptions are not unique")
    if not expected <= set(baseline_by_text):
        raise ValueError("repair descriptions are missing from baseline")

    old_success = {description: bool(baseline_by_text[description].get("success")) for description in expected}
    integrated_records: list[dict[str, Any]] = []
    for old in baseline_records:
        description = text(old)
        if description not in replacement_by_text:
            integrated_records.append(old)
            continue
        replacement = copy.deepcopy(replacement_by_text[description])
        replacement["testIdx"] = old.get("testIdx")
        replacement["promptIdx"] = old.get("promptIdx")
        replacement["promptId"] = old.get("promptId")
        integrated_records.append(replacement)

    integrated = copy.deepcopy(baseline)
    integrated["results"]["results"] = integrated_records
    integrated["results"]["prompts"][0]["metrics"] = recompute_metrics(integrated_records)
    integrated.setdefault("metadata", {})["gpt52TimeoutRepair"] = {
        "sourceEvalId": baseline.get("evalId"),
        "repairEvalId": repair.get("evalId"),
        "replacementCount": len(expected),
        "integrationKey": "vars.problem_description",
        "classifierTimeoutSeconds": 60,
        "semanticMergeTimeoutSeconds": 60,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(integrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_success = {description: bool(replacement_by_text[description].get("success")) for description in expected}
    metrics = integrated["results"]["prompts"][0]["metrics"]
    report = {
        "baseline_eval_id": baseline.get("evalId"),
        "repair_eval_id": repair.get("evalId"),
        "records": len(integrated_records),
        "replaced_records": len(expected),
        "repaired_rows_pass_before": sum(old_success.values()),
        "repaired_rows_pass_after": sum(new_success.values()),
        "pass_flips": {
            "fail_to_pass": sum(not old_success[x] and new_success[x] for x in expected),
            "pass_to_fail": sum(old_success[x] and not new_success[x] for x in expected),
        },
        "integrated_pass_count": metrics["testPassCount"],
        "integrated_fail_count": metrics["testFailCount"],
        "integrated_pass_rate": metrics["testPassCount"] / len(integrated_records),
        "sha256": {
            "baseline_raw": sha256(args.baseline),
            "repair": sha256(args.repair),
            "integrated": sha256(args.output),
        },
        "output": str(args.output),
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
