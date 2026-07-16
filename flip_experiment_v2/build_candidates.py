#!/usr/bin/env python3
"""Compile the v2 disclosure-flip candidate benchmark from authored family files.

This script makes no API or model calls. Every scenario was individually
authored and vetted by Claude Fable 5 (Anthropic, model id ``claude-fable-5``)
running in Claude Code on 2026-07-16, grounded in:

- the 53-row human disagreement extract
  (``../gold_labels_consensus_20260716/human_disagreements.csv``),
- the four disagreement mechanisms in
  (``../gold_labels_consensus_20260716/FINDINGS.md``),
- FETCH's enriched taxonomy descriptions
  (``$FETCH_REPO_ROOT/app/data/taxonomy_detailed_descriptions.csv``), and
- the paper failure modes carried in the v1 expanded flip audit.

The builder only validates, normalizes, and assembles the authored rows into
one deterministic CSV/JSONL pair. Expected labels are validated against the
FETCH runtime taxonomy (``$FETCH_REPO_ROOT/app/data/taxonomy.csv``) so every
expected label is exactly scorable against FETCH output with no alias table.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHORING = HERE / "authoring"
CANDIDATES = HERE / "candidates"

VALID_MECHANISMS = {
    "M1_core_vs_secondary_issue",
    "M2_specific_vs_general_fallback",
    "M3_missing_procedural_or_institutional_fact",
    "M4_competing_framings_of_one_dispute",
}
VALID_FLIP_TYPES = {"label_change", "routing_disambiguation"}
VALID_DIRECTIONS = {"AtoB", "BtoA"}

FIELDS = [
    "scenario_id",
    "boundary_id",
    "direction",
    "flip_type",
    "mechanism",
    "opening_query",
    "initial_category",
    "initial_subcategory",
    "final_category",
    "final_subcategory",
    "plausible_initial_labels",
    "hidden_fact",
    "fact_as_answer",
    "relevant_question_topic",
    "counterfactual_category",
    "counterfactual_subcategory",
    "counterfactual_hidden_fact",
    "counterfactual_fact_as_answer",
    "grounding_source_rows",
    "grounding_note",
    "safety_sensitive",
    "vetting_note",
    "generator_model",
    "candidate_status",
]

GENERATOR_MODEL = "claude-fable-5 (Claude Fable 5, Anthropic, via Claude Code)"


def load_runtime_taxonomy(fetch_root: Path) -> set[str]:
    path = fetch_root / "app/data/taxonomy.csv"
    pairs: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            cat = (row.get("Category") or "").strip()
            sub = (row.get("Subcategory") or "").strip()
            if cat and sub:
                pairs.add(f"{cat} > {sub}")
    if len(pairs) < 200:
        raise SystemExit(f"Runtime taxonomy at {path} looks wrong: {len(pairs)} pairs")
    return pairs


def split_label(label: str) -> tuple[str, str]:
    parts = [p.strip() for p in label.split(" > ", 1)]
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Label is not 'Category > Subcategory': {label!r}")
    return parts[0], parts[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fetch-root",
        default=os.environ.get("FETCH_REPO_ROOT", str(HERE.parents[1])),
    )
    args = parser.parse_args()
    taxonomy = load_runtime_taxonomy(Path(args.fetch_root))

    family_files = sorted(AUTHORING.glob("family_*.json"))
    if not family_files:
        raise SystemExit("No authored family files found under authoring/")

    rows: list[dict] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()

    for path in family_files:
        family = json.loads(path.read_text(encoding="utf-8"))
        boundary_id = family["boundary_id"]
        mechanism = family["mechanism"]
        flip_type = family["flip_type"]
        if mechanism not in VALID_MECHANISMS:
            errors.append(f"{path.name}: invalid mechanism {mechanism}")
        if flip_type not in VALID_FLIP_TYPES:
            errors.append(f"{path.name}: invalid flip_type {flip_type}")
        grounding_rows = family.get("grounding_source_rows", "")
        grounding_note = family.get("grounding_note", "")
        safety = str(family.get("safety_sensitive", False)).lower()

        for scenario in family["scenarios"]:
            suffix = scenario["suffix"]
            scenario_id = f"v2_{boundary_id}_{suffix}"
            if scenario_id in seen_ids:
                errors.append(f"duplicate scenario_id {scenario_id}")
            seen_ids.add(scenario_id)

            opening = " ".join(scenario["opening_query"].split())
            key = opening.lower()
            if key in seen_queries:
                errors.append(f"{scenario_id}: duplicate opening query")
            seen_queries.add(key)
            n_words = len(opening.split())
            if not 8 <= n_words <= 45:
                errors.append(f"{scenario_id}: opening query {n_words} words (want 8-45)")

            direction = scenario.get("direction", "AtoB")
            if direction not in VALID_DIRECTIONS:
                errors.append(f"{scenario_id}: invalid direction {direction}")

            try:
                init_cat, init_sub = split_label(scenario["initial"])
                fin_cat, fin_sub = split_label(scenario["final"])
                cf_cat, cf_sub = split_label(scenario["counterfactual_final"])
            except (ValueError, KeyError) as exc:
                errors.append(f"{scenario_id}: {exc}")
                continue

            for role, label in (
                ("initial", scenario["initial"]),
                ("final", scenario["final"]),
                ("counterfactual_final", scenario["counterfactual_final"]),
            ):
                if label.strip() not in taxonomy:
                    errors.append(f"{scenario_id}: {role} label not in runtime taxonomy: {label!r}")

            if scenario["initial"].strip() == scenario["final"].strip():
                errors.append(f"{scenario_id}: initial == final; not a flip")
            if scenario["counterfactual_final"].strip() == scenario["final"].strip():
                errors.append(f"{scenario_id}: counterfactual_final == final; no contrast")

            plausible = scenario.get("plausible_initial_labels") or scenario["initial"]
            for label in plausible.split("||"):
                if label.strip() not in taxonomy:
                    errors.append(f"{scenario_id}: plausible label not in taxonomy: {label.strip()!r}")

            for field in ("hidden_fact", "fact_as_answer", "counterfactual_hidden_fact",
                          "counterfactual_fact_as_answer", "relevant_question_topic",
                          "vetting_note"):
                if not str(scenario.get(field, "")).strip():
                    errors.append(f"{scenario_id}: empty {field}")

            rows.append({
                "scenario_id": scenario_id,
                "boundary_id": boundary_id,
                "direction": direction,
                "flip_type": flip_type,
                "mechanism": mechanism,
                "opening_query": opening,
                "initial_category": init_cat,
                "initial_subcategory": init_sub,
                "final_category": fin_cat,
                "final_subcategory": fin_sub,
                "plausible_initial_labels": " || ".join(
                    l.strip() for l in plausible.split("||")),
                "hidden_fact": " ".join(str(scenario["hidden_fact"]).split()),
                "fact_as_answer": " ".join(str(scenario["fact_as_answer"]).split()),
                "relevant_question_topic": scenario["relevant_question_topic"],
                "counterfactual_category": cf_cat,
                "counterfactual_subcategory": cf_sub,
                "counterfactual_hidden_fact": " ".join(
                    str(scenario["counterfactual_hidden_fact"]).split()),
                "counterfactual_fact_as_answer": " ".join(
                    str(scenario["counterfactual_fact_as_answer"]).split()),
                "grounding_source_rows": scenario.get("grounding_source_rows", grounding_rows),
                "grounding_note": grounding_note,
                "safety_sensitive": str(scenario.get("safety_sensitive", safety)).lower(),
                "vetting_note": scenario["vetting_note"],
                "generator_model": GENERATOR_MODEL,
                "candidate_status": "claude_authored_awaiting_human_salience_audit",
            })

    if errors:
        for err in errors:
            print("ERROR:", err)
        raise SystemExit(f"{len(errors)} validation errors; nothing written")

    rows.sort(key=lambda r: r["scenario_id"])
    CANDIDATES.mkdir(exist_ok=True)
    csv_path = CANDIDATES / "flip_candidates_v2.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    jsonl_path = CANDIDATES / "flip_candidates_v2.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_boundary = Counter(r["boundary_id"] for r in rows)
    by_direction = Counter(r["direction"] for r in rows)
    by_flip_type = Counter(r["flip_type"] for r in rows)
    by_mechanism = Counter(r["mechanism"] for r in rows)
    profile = {
        "total_candidates": len(rows),
        "families": len(family_files),
        "by_boundary": dict(sorted(by_boundary.items())),
        "by_direction": dict(by_direction),
        "by_flip_type": dict(by_flip_type),
        "by_mechanism": dict(by_mechanism),
        "safety_sensitive_rows": sum(r["safety_sensitive"] == "true" for r in rows),
        "opening_query_words": {
            "min": min(len(r["opening_query"].split()) for r in rows),
            "max": max(len(r["opening_query"].split()) for r in rows),
            "mean": round(sum(len(r["opening_query"].split()) for r in rows) / len(rows), 2),
        },
        "generator_model": GENERATOR_MODEL,
    }
    (HERE / "analysis/candidate_profile.json").write_text(
        json.dumps(profile, indent=2) + "\n")
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
