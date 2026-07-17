#!/usr/bin/env python3
"""Render paper-facing Markdown from FETCH multi-label accuracy artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def fmt(value) -> str:
    return "—" if value is None or value == "" else f"{float(value):.1f}%"


def short(text: str, limit: int = 360) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.artifact_dir / "FETCH_GOLD_ACCURACY_FINDINGS.md"
    report = json.loads((args.artifact_dir / "accuracy_summary.json").read_text())
    scenarios = read_csv(args.artifact_dir / "scenario_results.csv")
    by_count = read_csv(args.artifact_dir / "metrics_by_gold_label_count.csv")
    by_category = read_csv(args.artifact_dir / "metrics_by_top_level_category.csv")

    lines = [
        "# FETCH multi-label consensus-gold findings",
        "",
        "## Headline results",
        "",
        f"The primary benchmark contains **{report['gold_scenarios']} unique, whitespace-normalized scenarios**. "
        "Each uncached replicate used the full five-classifier FETCH vote ensemble (GPT-5.2, Gemini, Mistral, keyword, and SPOT). "
        "Exact sublabel comparisons apply the audited legacy/current taxonomy compatibility map described in "
        "[`FETCH_GOLD_ACCURACY_METHODS.md`](FETCH_GOLD_ACCURACY_METHODS.md).",
        "",
        "| Run | N | All exact sublabels | Some exact sublabels | Top-level only | No correct category | Any exact sublabel | Any correct top-level | Graded score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    summaries = dict(report["run_summaries"])
    summaries["pooled"] = report["pooled_summary"]
    for name, summary in summaries.items():
        tiers = summary["outcome_tiers"]
        lines.append(
            f"| {name} | {summary['scenarios']} | {fmt(tiers['all_exact_sublabels']['pct'])} "
            f"| {fmt(tiers['some_exact_sublabels']['pct'])} | {fmt(tiers['top_level_only']['pct'])} "
            f"| {fmt(tiers['no_correct_category']['pct'])} | {fmt(summary['any_exact_sublabel_pct'])} "
            f"| {fmt(summary['any_correct_top_level_pct'])} | {fmt(summary['mean_graded_retrieval_score_pct'])} |"
        )

    pooled = report["pooled_summary"]
    lines.extend([
        "",
        f"Across the two run-observations per scenario, FETCH retrieved at least one exact sublabel in "
        f"**{fmt(pooled['any_exact_sublabel_pct'])}** and at least one correct top-level category in "
        f"**{fmt(pooled['any_correct_top_level_pct'])}**. It retrieved every gold sublabel in "
        f"**{fmt(pooled['all_exact_sublabels_pct'])}**. The lower strict-set result "
        f"(**{fmt(pooled['strict_exact_set_pct'])}**) shows that the ensemble commonly adds plausible labels beyond the conservative gold set; "
        "it should not be confused with failure to retrieve the needed route.",
        "",
        "## Rank-aware retrieval",
        "",
        "| Run | Hits@1: any exact | Hits@2: any exact | All gold within top 2 | Gold-instance recall@1 | Gold-instance recall@2 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for name, summary in summaries.items():
        lines.append(
            f"| {name} | {fmt(summary['scenario_hits_at_1_pct'])} | {fmt(summary['scenario_hits_at_2_pct'])} "
            f"| {fmt(summary['all_gold_within_top_2_pct'])} | {fmt(summary['gold_instance_recall_at_1_pct'])} "
            f"| {fmt(summary['gold_instance_recall_at_2_pct'])} |"
        )
    lines.extend([
        "",
        "Hits@2 asks whether at least one exact gold sublabel appears among the first two ordered FETCH labels. "
        "The all-gold-within-top-2 measure is stricter for multi-label scenarios, while gold-instance recall@2 pools every expected label instance.",
        "",
        f"At the label-instance level, exact micro precision / recall / F1 were "
        f"**{fmt(pooled['micro_exact_precision_pct'])} / {fmt(pooled['micro_exact_recall_pct'])} / {fmt(pooled['micro_exact_f1_pct'])}**. "
        "For referral utility, recall and the outcome tiers are the more direct measures: one correct route may be useful even when extra routes are offered.",
        "",
        "## Performance by number of gold issues",
        "",
        "| Gold sublabels | Scenario-run observations | All exact | Some exact | Top-level only | No correct category | Mean exact coverage | Graded score |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in sorted((row for row in by_count if row["run"] == "pooled"), key=lambda row: int(row["group"])):
        tiers = json.loads(row["outcome_tiers"].replace("'", '"'))
        lines.append(
            f"| {row['group']} | {row['scenarios']} | {fmt(tiers['all_exact_sublabels']['pct'])} "
            f"| {fmt(tiers['some_exact_sublabels']['pct'])} | {fmt(tiers['top_level_only']['pct'])} "
            f"| {fmt(tiers['no_correct_category']['pct'])} | {fmt(row['mean_exact_gold_coverage_pct'])} "
            f"| {fmt(row['mean_graded_retrieval_score_pct'])} |"
        )

    lines.extend([
        "",
        "Multi-label rows make the distinction between *some* and *all* retrieval visible. A system can successfully expose one attorney-relevant route while still omitting a secondary issue; the graded score gives partial credit without calling that result complete.",
        "",
        "## Performance by top-level legal category",
        "",
        "A scenario with gold labels in more than one top-level category contributes to each applicable row.",
        "",
        "| Gold top-level category | Scenario-run observations | Any exact sublabel | All exact sublabels | Any correct top-level | Exact coverage | Graded score |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    category_rows = sorted(
        (row for row in by_category if row["run"] == "pooled"),
        key=lambda row: (-int(row["scenarios"]), row["group"]),
    )
    for row in category_rows:
        lines.append(
            f"| {row['group']} | {row['scenarios']} | {fmt(row['any_exact_sublabel_pct'])} "
            f"| {fmt(row['all_exact_sublabels_pct'])} | {fmt(row['any_correct_top_level_pct'])} "
            f"| {fmt(row['mean_exact_gold_coverage_pct'])} | {fmt(row['mean_graded_retrieval_score_pct'])} |"
        )

    cross = report["cross_run"]
    lines.extend([
        "",
        "## Replicate stability",
        "",
        f"Both runs contain {cross.get('complete_scenarios', 0)} common scenarios. The exact/none success status was stable for "
        f"**{fmt(cross.get('any_exact_status_stable_pct'))}** of scenarios, while the full four-tier outcome was stable for "
        f"**{fmt(cross.get('outcome_tier_stable_pct'))}**. The returned label set was identical in "
        f"**{fmt(cross.get('identical_predicted_set_pct'))}** and had mean cross-run Jaccard similarity "
        f"**{fmt(cross.get('mean_predicted_set_jaccard_pct'))}**. "
        f"At least one exact sublabel appeared in every run for **{fmt(cross.get('any_exact_in_every_run_pct'))}**, "
        f"and all gold sublabels appeared in every run for **{fmt(cross.get('all_exact_in_every_run_pct'))}**.",
        "",
        "## Qualitative error patterns",
        "",
        "The most informative misses fall into three groups:",
        "",
        "1. **Partial multi-issue retrieval.** FETCH finds the dominant dispute but omits a secondary legal route, often when the narrative gives much more detail to one issue.",
        "2. **Right domain, wrong specialist route.** The ensemble reaches the correct top-level area but chooses a neighboring subcategory. These cases are often genuinely ambiguous because procedural posture, party side, requested relief, or whether an issue is primary versus contextual is not explicit.",
        "3. **Broad overprediction.** Exact recall is high relative to precision because the vote/merge ensemble commonly retains additional plausible routes. This may increase the chance of reaching a helpful attorney, but it also creates triage burden and explains the gap between all-label retrieval and strict exact-set matching.",
        "",
        "### Illustrative partial or category-only cases",
        "",
    ])
    candidates = [row for row in scenarios if row["outcome_tier"] in {"some_exact_sublabels", "top_level_only", "no_correct_category"}]
    candidates.sort(key=lambda row: (float(row["graded_retrieval_score"]), -int(row["gold_label_count"]), row["scenario_id"], row["run"]))
    used = set()
    selected = []
    for row in candidates:
        if row["scenario_id"] in used:
            continue
        used.add(row["scenario_id"])
        selected.append(row)
        if len(selected) == 8:
            break
    for row in selected:
        lines.extend([
            f"- **{row['scenario_id']} ({row['run']}; {row['outcome_tier'].replace('_', ' ')})** — “{short(row['problem_description'])}”",
            f"  - Gold: `{row['gold_labels']}`",
            f"  - FETCH: `{row['predicted_labels'] or '[no parsed labels]'}`",
        ])

    lines.extend([
        "",
        "These examples are diagnostic, not a random sample. Row-level outcomes for every scenario and run are in [`scenario_results.csv`](scenario_results.csv).",
        "",
        "## Scope and limitations",
        "",
        "The gold set is a conservative consensus derived from two human raters, three independent LLM passes, and the internally reviewed primary label; it is not de novo adjudication by multiple specialist attorneys for every row. Some additional FETCH labels may be reasonable even when absent from gold. The metrics therefore report both retrieval-oriented recall and strict-set precision, preserve all raw predictions, and avoid treating top-level-only routing as equivalent to an exact specialist match.",
        "",
        "The independent run/provider audit records final provider timeouts or errors. A transient provider traceback that succeeded on retry is not counted as a final provider failure. Any targeted GPT-5.2 repair is saved separately and integrated before the final tables.",
    ])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
