#!/usr/bin/env python3
"""Build the four-label human-review stage and web-app seed data.

The focused adjudications in this file were performed in the current Codex
context without calling an external model.  They deliberately treat labels as
an unordered set and allow one through four labels when the text supports
separate legal issues.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from xml.etree import ElementTree as ET

import create_silver_labels as silver
import run_two_label_gpt52_audit as workbook


SOURCE_WORKBOOK = Path(
    "silver_labels/09_internal_priority_review/"
    "redaction_reviewed_v5_clean_ai_silver_prioritized_human_review.xlsx"
)
SOURCE_ROWS = Path("redaction_reviewed_v5_clean.xlsx")
QUEUE = Path("silver_labels/08_gpt52_two_label_audit/review_queue.json")
FINAL_REVIEW = Path("silver_labels/04_review/final_review.json")
PRIORITIES = Path("silver_labels/09_internal_priority_review/prioritized_review_queue.csv")
TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")
OUT_DIR = Path("silver_labels/10_four_label_human_review")
OUTPUT_WORKBOOK = OUT_DIR / "redaction_reviewed_v5_clean_four_label_human_review.xlsx"
CASES_JSON = OUT_DIR / "review_cases.json"
FOCUSED_JSON = OUT_DIR / "focused_multilabel_adjudication.json"
FOCUSED_CSV = OUT_DIR / "focused_multilabel_adjudication.csv"


def match(category: str, subcategory: str, rationale: str, confidence: str = "high") -> dict[str, str]:
    return {
        "category": category,
        "subcategory": subcategory,
        "rationale": rationale,
        "confidence": confidence,
    }


# These are review candidates, not silently finalized labels.  Each candidate
# represents a distinct issue visible in the source text.  Lower-confidence
# boundary cases are explicitly identified for the human reviewer.
FOCUSED_ADJUDICATIONS: dict[int, dict[str, object]] = {
    252: {
        "matches": [
            match("Family Law", "General (Divorce/Separation)", "The user expressly asks to process a divorce or annulment."),
            match("Family Law", "Military", "The spouse is in the Navy, making military-family-law rules potentially material."),
            match("International Law", "Gen. Immigration/Visas", "The K-1 visa and conditional green card are explicit and may be affected by ending the marriage.", "medium"),
            match("Real Property", "Tenant (Residential)", "The user asks to remove the spouse from an apartment lease and change the locks."),
        ],
        "justification": "Four distinct requested or legally material issues are visible. Immigration remains medium confidence because the text gives immigration facts but does not expressly request an immigration filing or status determination.",
    },
    290: {
        "matches": [
            match("Intellectual Property", "Trademark/Copyright", "Unauthorized reuse of an original video and a DMCA takedown are explicit copyright issues."),
            match("General Litigation", "Libel/Slander/Defamation", "The user alleges damaging published statements that harmed reputation."),
            match("General Litigation", "Online Harassment/Doxing/Bullying", "The TikTok conduct is described as ongoing online harassment causing distress."),
        ],
        "justification": "Copyright, defamation, and online harassment are separately pleaded theories; the earlier two-label cap necessarily dropped one.",
    },
    384: {
        "matches": [
            match("Wills & Trusts", "General (Wills, Trusts, Estates)", "The user is comparing ownership transfer with placing property in a trust.", "medium"),
            match("Real Property", "General (residential)", "Transfer of ownership/title to non-commercial property is an express part of the request.", "medium"),
            match("Real Property", "Government Loans (VA,FHA,Etc.)", "The user asks about terms of a VA construction loan."),
        ],
        "justification": "Three domains are supported. Property Tax is not added: its detailed taxonomy entry concerns assessment-value disputes, while this row asks only general tax-liability questions. Living Trusts may replace general Wills & Trusts if a revocable living trust is confirmed.",
    },
    419: {
        "matches": [
            match("Family Law", "General (Divorce/Separation)", "The row expressly lists divorce.", "low"),
            match("Real Property", "Tenant (Residential)", "The row expressly lists eviction, provisionally assuming the user is the tenant.", "low"),
            match("Criminal Law", "Other", "The row expressly lists a criminal case but gives no charge or procedural posture.", "low"),
        ],
        "justification": "Three matters are named, but all are low confidence because the text supplies no facts. Human review should verify party role and the criminal charge rather than treating these provisional subcategories as final.",
    },
    420: {
        "matches": [
            match("Workers' Comp", "State", "A workplace injury and resulting foot fracture are explicit."),
            match("Labor & Employment", "Wrongful Discharge", "The user says they were fired after the workplace injury, raising possible retaliatory discharge.", "medium"),
            match("International Law", "Deportation", "The user expressly asks whether they will be deported.", "medium"),
        ],
        "justification": "The row presents three separate service needs. Deportation is more faithful than general visas, although no removal proceeding is described; wrongful discharge also requires human confirmation of the reason for firing.",
    },
    421: {
        "matches": [
            match("Wills & Trusts", "Conservatorship/Guardianship", "The sister's guardianship and control over the parents are an express subject of the dispute.", "medium"),
            match("Wills & Trusts", "Litigation", "The user describes a beneficiary dispute connected to the sister's fiduciary control.", "low"),
            match("General Litigation", "Personal Injury", "The user seeks payment after being struck by the sister's car."),
            match("Criminal Law", "Local Ordinances", "The user contests a parking ticket; this is the nearest municipal-citation entry, but the taxonomy has no exact parking-ticket label.", "low"),
        ],
        "justification": "Four distinct factual matters warrant display for review. The beneficiary and parking-ticket pairs are deliberately low confidence because the detailed taxonomy assumes an erupted will/trust lawsuit and has no exact non-moving parking-citation entry.",
    },
    424: {
        "matches": [
            match("Administrative Law", "Military/Veterans", "The user reports losing veterans benefits."),
            match("Administrative Law", "Professional Licensing", "The user's nursing license is being revoked."),
            match("General Litigation", "Neighbor Disputes/Nuisance", "Repeated loud nighttime music is a classic neighbor-noise nuisance."),
            match("Wills & Trusts", "General (Wills, Trusts, Estates)", "The user expressly wants to write a will."),
        ],
        "justification": "The text expressly identifies four independent legal-service needs, each matching a detailed taxonomy entry.",
    },
}


def split_label(value: str) -> tuple[str, str]:
    if " / " not in value:
        return "", ""
    return tuple(value.split(" / ", 1))  # type: ignore[return-value]


def read_priorities() -> dict[int, dict[str, str]]:
    with PRIORITIES.open(encoding="utf-8", newline="") as stream:
        return {int(row["row_number"]): row for row in csv.DictReader(stream)}


def validate_focused(taxonomy_pairs: dict[tuple[str, str], dict[str, str]]) -> None:
    for row_id, item in FOCUSED_ADJUDICATIONS.items():
        matches = item["matches"]
        if not isinstance(matches, list) or not 1 <= len(matches) <= 4:
            raise ValueError(f"row {row_id} has invalid match count")
        pairs = [(m["category"], m["subcategory"]) for m in matches]
        if len(pairs) != len(set(pairs)):
            raise ValueError(f"row {row_id} has duplicate matches")
        missing = [pair for pair in pairs if pair not in taxonomy_pairs]
        if missing:
            raise ValueError(f"row {row_id} has taxonomy-invalid matches: {missing}")


def default_matches(item: dict[str, str]) -> list[dict[str, str]]:
    result = []
    for slot in (1, 2):
        value = item.get(f"audit_label_{slot}", "")
        if not value:
            continue
        category, subcategory = split_label(value)
        result.append({
            "category": category,
            "subcategory": subcategory,
            "rationale": item.get("audit_justification", ""),
            "confidence": "",
        })
    return result


def build_cases() -> list[dict[str, object]]:
    source_rows = silver.read_workbook_rows(SOURCE_ROWS)
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    final_review = json.loads(FINAL_REVIEW.read_text(encoding="utf-8"))["rows"]
    priorities = read_priorities()
    taxonomy, pairs = silver.read_taxonomy(TAXONOMY)
    validate_focused(pairs)
    descriptions = {(row["category"], row["subcategory"]): row["description"] for row in taxonomy}
    cases: list[dict[str, object]] = []
    for item in queue:
        row_id = int(item["row_number"])
        focused = FOCUSED_ADJUDICATIONS.get(row_id)
        suggested = list(focused["matches"]) if focused else default_matches(item)
        for candidate in suggested:
            candidate["description"] = descriptions[(candidate["category"], candidate["subcategory"])]
        final = final_review[str(row_id)]
        model_outputs = {
            model: final["models"][model]
            for model in ("gpt52", "gemini31_pro", "deepseek_v4")
        }
        priority = priorities[row_id]
        cases.append({
            "row_number": row_id,
            "problem_description": item["problem_description"],
            "original_human_label": {
                "category": source_rows[row_id - 1].get("B", ""),
                "subcategory": source_rows[row_id - 1].get("C", ""),
            },
            "internal_primary_label": final["review"],
            "internal_primary_justification": final["basis"],
            "model_outputs": model_outputs,
            "two_label_audit": item,
            "priority": {
                "tier": priority["priority_tier"],
                "score": int(priority["priority_score"]),
                "reason": priority["internal_priority_reason"],
                "recommended_action": priority["recommended_human_action"],
            },
            "suggested_labels": suggested,
            "suggestion_justification": (
                focused["justification"] if focused else item["audit_justification"]
            ),
            "focused_four_label_review": focused is not None,
        })
    return sorted(cases, key=lambda case: (-int(case["priority"]["score"]), int(case["row_number"])))


def write_focused_outputs(cases: list[dict[str, object]]) -> None:
    focused = [case for case in cases if case["focused_four_label_review"]]
    FOCUSED_JSON.write_text(json.dumps(focused, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "row_number", "problem_description", "label_count", "label_1", "label_2",
        "label_3", "label_4", "confidence_1", "confidence_2", "confidence_3",
        "confidence_4", "consensus_justification",
    ]
    with FOCUSED_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in sorted(focused, key=lambda x: int(x["row_number"])):
            matches = case["suggested_labels"]
            row = {
                "row_number": case["row_number"],
                "problem_description": case["problem_description"],
                "label_count": len(matches),
                "consensus_justification": case["suggestion_justification"],
            }
            for index, candidate in enumerate(matches, 1):
                row[f"label_{index}"] = f"{candidate['category']} / {candidate['subcategory']}"
                row[f"confidence_{index}"] = candidate["confidence"]
            writer.writerow(row)


def write_workbook(cases: list[dict[str, object]]) -> None:
    by_row = {int(case["row_number"]): case for case in cases}
    headers = ["four_label_ai_candidate_count"]
    for slot in range(1, 5):
        headers.extend([
            f"four_label_ai_category_{slot}",
            f"four_label_ai_subcategory_{slot}",
            f"four_label_ai_confidence_{slot}",
            f"four_label_ai_rationale_{slot}",
        ])
    headers.extend(["four_label_ai_consensus_justification", "four_label_ai_focused_review"])
    for slot in range(1, 5):
        headers.extend([f"human_label_{slot}_category", f"human_label_{slot}_subcategory"])
    headers.extend(["human_review_status", "human_review_notes", "human_reviewer", "human_reviewed_at"])

    with ZipFile(SOURCE_WORKBOOK) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("source workbook has no sheet data")
    start = 79  # CA, immediately after BZ in Stage 09.
    cols = [workbook.excel_col(start + index) for index in range(len(headers))]
    files["xl/styles.xml"], ai_style = workbook.add_fill_style(files["xl/styles.xml"], "FFE4DFEC")
    files["xl/styles.xml"], human_style = workbook.add_fill_style(files["xl/styles.xml"], "FFDDEBF7")

    human_start = 19
    for row in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_number = int(row.get("r", "0"))
        if row_number == 1:
            for col, header in zip(cols, headers):
                workbook.set_cell(row, col, row_number, header, "1")
            continue
        case = by_row.get(row_number)
        values = [""] * len(headers)
        if case:
            matches = case["suggested_labels"]
            values[0] = str(len(matches))
            for index, candidate in enumerate(matches):
                offset = 1 + index * 4
                values[offset:offset + 4] = [
                    candidate["category"], candidate["subcategory"],
                    candidate["confidence"], candidate["rationale"],
                ]
            values[17] = str(case["suggestion_justification"])
            values[18] = "yes" if case["focused_four_label_review"] else "no"
        for index, (col, value) in enumerate(zip(cols, values)):
            style = human_style if index >= human_start else (ai_style if case and case["focused_four_label_review"] else "2")
            workbook.set_cell(row, col, row_number, str(value), style)

    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{cols[-1]}432")
    sheet_cols = root.find(f"{{{silver.NS}}}cols")
    if sheet_cols is None:
        sheet_cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, sheet_cols)
    for index, header in enumerate(headers):
        width = "55" if "rationale" in header or "justification" in header or "notes" in header else "27"
        ET.SubElement(sheet_cols, f"{{{silver.NS}}}col", {
            "width": width, "customWidth": "1", "min": str(start + index), "max": str(start + index),
        })
    auto_filter = root.find(f"{{{silver.NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{silver.NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{cols[-1]}432")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    with ZipFile(OUTPUT_WORKBOOK, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    CASES_JSON.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_focused_outputs(cases)
    write_workbook(cases)
    counts = {row_id: len(item["matches"]) for row_id, item in FOCUSED_ADJUDICATIONS.items()}
    print(f"wrote {len(cases)} review cases; focused label counts: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
