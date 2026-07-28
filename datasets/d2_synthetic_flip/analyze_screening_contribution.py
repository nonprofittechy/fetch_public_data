#!/usr/bin/env python3
"""Isolate the screening protocol's own marginal contribution within a
single condition-C run, by comparing per-case ``effective_categories``
(screening-aware union) against ``labels`` (raw model vote) on the exact
same case and the exact same underlying model outputs.

This is a paired, within-run comparison (not a between-run condition-B-vs-C
comparison), so it isolates just the deterministic union step and is not
confounded by run-to-run LLM sampling variance. A "rescue" is a case where
the union added the expected exact label that the raw model vote alone
missed; a "regression" would be the union somehow losing a label the raw
vote had (should not happen, since effective_categories is a superset by
construction — reported as a sanity check).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def exact_present(labels, expected_cat: str, expected_sub: str) -> bool:
    want = norm(f"{expected_cat} > {expected_sub}")
    return any(norm(l["label"]) == want for l in labels)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="condition-C results/ run directory")
    parser.add_argument(
        "--candidates", default="candidates/flip_candidates_v2.csv"
    )
    parser.add_argument("--out", required=True, help="output JSON path")
    args = parser.parse_args()

    with open(args.candidates, newline="", encoding="utf-8") as handle:
        candidates = {row["scenario_id"]: row for row in csv.DictReader(handle)}

    results = json.loads((Path(args.run) / "results.json").read_text())["results"]

    matched = 0
    effective_correct = 0
    model_only_correct = 0
    rescues = []
    regressions = []

    for row in results:
        output = (row.get("response") or {}).get("output")
        if not output:
            continue
        parsed = json.loads(output)
        if not parsed.get("question_matched") or not parsed.get("final_labels"):
            continue
        scenario_id = row["vars"].get("scenario_id")
        candidate = candidates.get(scenario_id)
        if not candidate:
            continue
        final_cat = candidate["final_category"]
        final_sub = candidate["final_subcategory"]

        matched += 1
        effective = parsed["final_labels"]
        model_only = parsed.get("final_labels_model_only") or []
        eff_ok = exact_present(effective, final_cat, final_sub)
        mo_ok = exact_present(model_only, final_cat, final_sub)
        if eff_ok:
            effective_correct += 1
        if mo_ok:
            model_only_correct += 1
        if eff_ok and not mo_ok:
            rescues.append(
                {
                    "scenario_id": scenario_id,
                    "expected": f"{final_cat} > {final_sub}",
                    "mandatory_categories_final": parsed.get("mandatory_categories_final"),
                }
            )
        if mo_ok and not eff_ok:
            regressions.append(scenario_id)

    summary = {
        "run": args.run,
        "matched_cases_with_final_answer": matched,
        "effective_categories_exact_correct": effective_correct,
        "model_only_exact_correct": model_only_correct,
        "screening_rescues": len(rescues),
        "screening_regressions_sanity_check": len(regressions),
        "rescue_detail": rescues,
        "regression_detail_should_be_empty": regressions,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, list)}, indent=2))


if __name__ == "__main__":
    main()
