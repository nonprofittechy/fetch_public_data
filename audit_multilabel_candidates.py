#!/usr/bin/env python3
"""Audit whether ranked model alternatives support multiple labels per row.

This is a post-hoc audit of the already completed LLM passes.  It does not call
an API and does not use keyword/SPOT classification.  A pair is model-supported
when that exact detailed-taxonomy pair appears in at least two of the three
models' top-three ranked matches.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import create_silver_labels as silver

AUDIT = Path("silver_labels/04_review/final_review.json")
INPUT_ROWS = Path("redaction_reviewed_v5_clean.xlsx")
OUT_DIR = Path("silver_labels/07_multilabel_audit")
SUMMARY_CSV = OUT_DIR / "multilabel_candidate_rows.csv"
EVIDENCE_JSON = OUT_DIR / "multilabel_candidate_evidence.json"
ANALYSIS_JSON = OUT_DIR / "multilabel_analysis.json"
README = OUT_DIR / "README.md"
MODELS = ["gpt52", "gemini31_pro", "deepseek_v4"]
MODEL_NAMES = {
    "gpt52": "GPT-5.2",
    "gemini31_pro": "Gemini 3.1 Pro Preview",
    "deepseek_v4": "DeepSeek v4",
}


def pair(match: dict[str, str]) -> tuple[str, str]:
    return match.get("category", ""), match.get("subcategory", "")


def label(value: tuple[str, str]) -> str:
    return f"{value[0]} / {value[1]}".strip(" /")


def aggregate(row: dict[str, object]) -> list[dict[str, object]]:
    by_pair: dict[tuple[str, str], dict[str, object]] = {}
    for model in MODELS:
        for rank, match in enumerate(row["models"][model][:3], start=1):
            value = pair(match)
            item = by_pair.setdefault(
                value,
                {
                    "category": value[0],
                    "subcategory": value[1],
                    "label": label(value),
                    "model_support": 0,
                    "rank1_support": 0,
                    "occurrences": 0,
                    "models": [],
                    "ranks": {},
                    "confidences": {},
                    "justifications": {},
                },
            )
            item["occurrences"] += 1
            item["models"].append(model)
            item["ranks"].setdefault(model, rank)
            item["confidences"][model] = match.get("confidence", "")
            item["justifications"][model] = match.get("justification", "")
    for item in by_pair.values():
        item["models"] = sorted(set(item["models"]))
        item["model_support"] = len(item["models"])
        item["rank1_support"] = sum(item["ranks"].get(model) == 1 for model in MODELS)
    return sorted(
        by_pair.values(),
        key=lambda item: (
            -int(item["model_support"]),
            -int(item["rank1_support"]),
            min(item["ranks"].values()),
            str(item["label"]),
        ),
    )


def assessment(candidates: list[dict[str, object]]) -> str:
    supported = [item for item in candidates if int(item["model_support"]) >= 2]
    if len(supported) >= 3:
        return "three-label candidate"
    if len(supported) == 2:
        # 2/3 support for both exact pairs is strong evidence, but still needs
        # a human determination that the two labels describe separate issues.
        if all(int(item["rank1_support"]) >= 1 for item in supported):
            return "two-label candidate"
        return "possible two-label candidate"
    return "single-label / weak alternative"


def write_outputs() -> dict[str, object]:
    rows = silver.read_workbook_rows(INPUT_ROWS)
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, object] = {}
    csv_fields = [
        "row_number",
        "problem_description",
        "original_human_category",
        "original_human_subcategory",
        "internal_review_label",
        "ai_multilabel_assessment",
        "supported_candidate_count",
        "candidate_labels",
        "candidate_support",
        "candidate_rank1_support",
        "candidate_models",
        "candidate_justifications",
    ]
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=csv_fields)
        writer.writeheader()
        counts: Counter[str] = Counter()
        supported_count_histogram: Counter[int] = Counter()
        for row_id_text, row in audit["rows"].items():
            row_id = int(row_id_text)
            candidates = aggregate(row)
            supported = [item for item in candidates if int(item["model_support"]) >= 2]
            # Only rows with at least two independently repeated exact pairs
            # are pulled into the candidate extract.
            if len(supported) < 2:
                continue
            kind = assessment(candidates)
            counts[kind] += 1
            supported_count_histogram[len(supported)] += 1
            evidence[row_id_text] = {
                "row_number": row_id,
                "problem_description": row["problem_description"],
                "original_human_category": rows[row_id - 1].get("B", ""),
                "original_human_subcategory": rows[row_id - 1].get("C", ""),
                "internal_review": row["review"],
                "assessment": kind,
                "supported_candidates": supported,
                "all_model_candidates": {model: row["models"][model] for model in MODELS},
            }
            writer.writerow(
                {
                    "row_number": row_id,
                    "problem_description": row["problem_description"],
                    "original_human_category": rows[row_id - 1].get("B", ""),
                    "original_human_subcategory": rows[row_id - 1].get("C", ""),
                    "internal_review_label": label(pair(row["review"])),
                    "ai_multilabel_assessment": kind,
                    "supported_candidate_count": len(supported),
                    "candidate_labels": " || ".join(str(item["label"]) for item in supported),
                    "candidate_support": " || ".join(str(item["model_support"]) for item in supported),
                    "candidate_rank1_support": " || ".join(str(item["rank1_support"]) for item in supported),
                    "candidate_models": " || ".join(
                        f"{item['label']}: {', '.join(MODEL_NAMES[m] for m in item['models'])}" for item in supported
                    ),
                    "candidate_justifications": " || ".join(
                        f"{item['label']}: " + " / ".join(
                            f"{MODEL_NAMES[m]}: {item['justifications'][m]}" for m in item["models"]
                        )
                        for item in supported
                    ),
                }
            )
    EVIDENCE_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    analysis = {
        "scope": "431 rows from redaction_reviewed_v5_clean.xlsx",
        "method": "Post-hoc comparison of the three completed independent model passes; no API call, keyword classifier, or SPOT step.",
        "candidate_definition": "An exact category/subcategory pair is model-supported when it appears in at least two of GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4 top-three candidate lists.",
        "interpretation_caveat": "Model support identifies rows for human review. It does not by itself prove that alternatives are independently correct: some are neighboring framings of one issue, and some are lower-ranked possibilities. The final multi-label decision should consider whether each label names a separate legal issue supported by the text and detailed taxonomy.",
        "rows_with_two_or_more_supported_pairs": sum(counts.values()),
        "assessment_counts": dict(counts),
        "supported_pair_count_histogram": {str(k): v for k, v in sorted(supported_count_histogram.items())},
        "candidate_rows_csv": SUMMARY_CSV.name,
        "full_evidence_json": EVIDENCE_JSON.name,
        "model_versions": MODEL_NAMES,
    }
    ANALYSIS_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return analysis


def write_readme(analysis: dict[str, object]) -> None:
    total = 431
    n = analysis["rows_with_two_or_more_supported_pairs"]
    counts = analysis["assessment_counts"]
    lines = [
        "# Multi-label audit", "",
        "This stage checks whether a row may legitimately have two or three labels. It is a post-hoc audit of the three completed LLM passes; it does not call an API and does not use keyword or SPOT classification.", "",
        "Use [`redaction_reviewed_v5_clean_multilabel_review_workspace.xlsx`](redaction_reviewed_v5_clean_multilabel_review_workspace.xlsx) for human review. It carries forward the one-label review workspace, highlights the AI candidate evidence, and adds three blank human label slots plus status and notes.", "",
        "## Method", "",
        "For each row, I collected every exact category/subcategory pair appearing in each model's top-three ranked list. A pair counts as **model-supported** when at least two of the three independent passes included that exact pair. A row enters the candidate extract when at least two distinct pairs meet that threshold.", "",
        "This is intentionally a generous review queue. Repeated model support is evidence that a second label deserves attention, not a final determination that it is correct. Some alternatives are different descriptions of the same issue; others reflect separate legal problems. The human reviewer should use the problem text and the canonical detailed taxonomy to make that distinction.", "",
        "## Results", "",
        f"Of {total} rows, {n} ({n / total:.1%}) have at least two distinct exact pairs supported by at least two models.", "",
        f"- Three-label candidates: {counts.get('three-label candidate', 0)}.",
        f"- Two-label candidates: {counts.get('two-label candidate', 0)}.",
        f"- Possible two-label candidates: {counts.get('possible two-label candidate', 0)}.", "",
        "The extract includes all model-supported alternatives, support counts, rank-1 support, every model that proposed each pair, and the original model justifications. The full JSON also preserves all top-three model candidates and the internal reviewed primary label.", "",
        "For an interpretation of the result, including clear two- and three-issue examples and cautionary false-multi-label patterns, see [`MULTILABEL_FINDINGS.md`](MULTILABEL_FINDINGS.md).", "",
        "## Files", "",
        f"- [`multilabel_candidate_rows.csv`]({SUMMARY_CSV.name}) — review queue, one row per candidate row.",
        f"- [`multilabel_candidate_evidence.json`]({EVIDENCE_JSON.name}) — complete structured evidence for every candidate row.",
        f"- [`multilabel_analysis.json`]({ANALYSIS_JSON.name}) — machine-readable counts and definitions.",
        f"- [`redaction_reviewed_v5_clean_multilabel_review_workspace.xlsx`](redaction_reviewed_v5_clean_multilabel_review_workspace.xlsx) — review-ready workbook with up to three AI-supported candidates and three blank human label slots.",
        "- The prior [`../06_human_review_workspace/`](../06_human_review_workspace/) workbook remains the one-label human review workspace; this stage does not overwrite it.", "",
        "## Reproduction", "",
        "Run `python audit_multilabel_candidates.py` from the repository root after the completed model outputs and `silver_labels/04_review/final_review.json` are present.", "",
        "## Model passes", "",
        "The evidence combines GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4. The internal reviewed primary label is shown for context but is not counted as an independent model in the candidate definition.", "",
    ]
    README.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    analysis = write_outputs()
    write_readme(analysis)
    print(json.dumps(analysis, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
