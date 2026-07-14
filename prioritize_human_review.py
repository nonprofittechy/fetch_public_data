#!/usr/bin/env python3
"""Prioritize the order-insensitive two-label review queue for human input."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from xml.etree import ElementTree as ET

import create_silver_labels as silver
import run_two_label_gpt52_audit as audit_helpers

QUEUE = Path("silver_labels/08_gpt52_two_label_audit/review_queue.json")
FINAL_REVIEW = Path("silver_labels/04_review/final_review.json")
AGREEMENT = Path("silver_labels/06_human_review_workspace/agreement_analysis.json")
STAGE7 = Path("silver_labels/07_multilabel_audit/multilabel_candidate_evidence.json")
SOURCE_WORKBOOK = Path("silver_labels/08_gpt52_two_label_audit/redaction_reviewed_v5_clean_ai_silver_two_label_audit.xlsx")
OUT_DIR = Path("silver_labels/09_internal_priority_review")
OUTPUT_WORKBOOK = OUT_DIR / "redaction_reviewed_v5_clean_ai_silver_prioritized_human_review.xlsx"


# These rows received direct in-context scrutiny in this pass.  The notes name
# the factual or taxonomy decision a human needs to resolve; they do not change
# the labels themselves.
HIGH_PRIORITY_NOTES = {
    4: "Construction-lien, business-contract, and creditor-collection framings all fit; decide whether one or two issues should be retained.",
    17: "The description is only 'administrative law dmv licensure'; there is not enough factual detail to validate the subcategory.",
    27: "The text merely says wrongful termination and/or discrimination, with no facts supporting either theory.",
    28: "The audit rejected Third Party litigation because no third party is identified, but the original passes split on the workers-comp subtype.",
    41: "All three original passes chose Whistleblowers, while the audit chose ADA; clarify whether the user wants protection for reporting ADA violations or an ADA claim personally.",
    46: "The correct bankruptcy perspective is unclear: exposure to an ex-spouse's creditors may fit Creditors, Other, or debtor-side advice depending on the taxonomy intent.",
    56: "The user already holds POA but asks about completing a guardianship/conservatorship process; decide which legal service is actually requested.",
    62: "A dog-bite injury sits directly on the Animal Law versus Personal Injury taxonomy boundary.",
    63: "The row combines disability insurance, medical leave, and return-to-work rights; the audit's Labor General label conflicts with earlier FMLA/Other choices.",
    74: "Police misconduct and Tort Claims Act are overlapping routes for the same government-defendant claim; decide whether both should be labels.",
    96: "SSDI derivative benefits and a divorce agreement are intertwined; earlier models also considered Child Support/Modification.",
    125: "The nonprofit is connected to a Superfund site, but the described request is too vague to choose Environment versus Non-Profit confidently.",
    128: "Foreclosure of business-sale collateral could route as creditor collection, sale-of-business litigation, or real-property foreclosure.",
    136: "Investor churning by an adviser is a securities dispute, but the taxonomy distinction between Securities and General Litigation is unclear here.",
    138: "The audit's Sale of Business label for a partner compensation dispute is questionable; Litigation or General business may be more faithful.",
    139: "A second real-property label is supported, but the text does not say whether the investment property is residential or commercial.",
    140: "Farm transaction, lease, trust, and tax advice span several domains; Personal Income may be the wrong tax subtype.",
    145: "The model marked two labels supported but returned only one unique taxonomy pair, an internal audit inconsistency.",
    152: "Auto-repair negligence can be a consumer-service dispute or a property-damage tort; the intended taxonomy boundary needs adjudication.",
    155: "The audit mapped a defective camper-van build to Real Property/Construction, which may be inapplicable to movable personal property.",
    156: "The dispute concerns both a vehicle transaction and allegedly deceptive financing; choose Automobiles/RVs versus Banking or both.",
    172: "Failure-to-register defense is not the same as seeking relief from registration; the specific registration label may be too narrow.",
    175: "Divorce is context and the user says a divorce lawyer is already retained; decide whether it should be a second label at all.",
    176: "The charge list does not provide enough reliable severity context to choose Major Felony versus Lessor Felony.",
    196: "The narrative says four misdemeanors but mentions strangulation; the actual filed charges are needed to choose felony versus misdemeanor.",
    212: "The immediate problem is a debt demand arising from a crash; Property Damage may describe the origin rather than the legal service sought.",
    213: "Disability-benefit overpayment and collections could fit ERISA/benefits, disability insurance, or debtor/collection categories.",
    232: "The children were already adopted; decide whether Adoption/DHS remains a distinct live issue or only background to custody.",
    252: "The audit omitted the explicit divorce request and substituted Military plus Tenant; the two-label limit likely distorted the result.",
    255: "Over-detention after release implicates both Civil Rights and the more specific Civil Matter for Inmates label.",
    266: "A dog-bite injury sits directly on the Animal Law versus Personal Injury taxonomy boundary.",
    269: "The complaint alleges placement/caseworker misconduct after a stroke; determine whether it is medical malpractice or a general civil claim.",
    279: "Police misconduct and Tort Claims Act are overlapping routes for the same government-defendant claim; decide whether both should be labels.",
    290: "The row expressly raises copyright, harassment, and defamation; the two-label audit necessarily omitted one substantial issue.",
    299: "Patent work is explicit, but the alleged court interference is unspecified; the need for a second litigation label is unclear.",
    307: "The request concerns Canadian immigration, while the detailed Gen. Immigration/Visas description may be U.S.-oriented.",
    325: "The text contains only two possible labels and no supporting facts, so neither can be validated confidently.",
    335: "The row combines FMLA, return-to-work rights, and disability insurance; Labor Other may not be the correct second label.",
    349: "The audit added Third Party litigation without identifying a third party, contradicting its treatment of the duplicate work-injury row.",
    352: "The sparse text mentions both workers' compensation and general workplace rights but gives no injury or claim facts.",
    378: "The residential transaction is clear, but the brief profiling allegation may be too weak for a separate Civil Rights label.",
    384: "Trust/ownership transfer, VA loan, disability-veteran considerations, and tax liability exceed the two-label limit.",
    412: "A deceased-owner property auction and surplus claim may require both probate authority and foreclosure-surplus expertise.",
    418: "No filed charges are identified, so felony severity is uncertain; the county tree removal also raises a separate government tort issue.",
    419: "The row lists divorce, eviction, and a criminal case with no facts; both prioritization and the two-label cap require human input.",
    420: "Work injury, firing, and deportation are all explicit; the two-label audit omitted the employment-termination issue.",
    421: "Guardianship/beneficiary conflict, car injury, and a parking ticket are three separate issues under a two-label cap.",
    424: "Veterans benefits, professional licensing, neighbor nuisance, and a will are four distinct issues under a two-label cap.",
    426: "CareOregon contract termination may be an administrative Medicaid decision, a business contract dispute, or both.",
    428: "The user requests legal malpractice but describes childhood abuse and trauma without a clear attorney-negligence theory.",
    429: "The text does not identify an IEP, accommodation, discipline process, or other facts distinguishing Special Needs Education from Student Rights.",
    430: "The factual description is vague and potentially unreliable; the legal basis for a stalking order cannot be confirmed from the text alone.",
}


# These rows name separate legal matters expressly enough that human review is
# mostly confirmation, not difficult adjudication.
CLEAR_MULTI_ISSUE_ROWS = {
    8, 10, 12, 14, 23, 24, 31, 33, 38, 40, 43, 47, 51, 54, 59, 69, 70, 73,
    83, 94, 108, 109, 110, 120, 129, 134, 151, 165, 166, 178, 186, 193, 225,
    228, 233, 234, 236, 238, 240, 254, 256, 259, 261, 268, 280, 282, 294, 300,
    316, 324, 328, 329, 331, 332, 341, 342, 344, 365, 370, 371, 374, 387, 391,
    397, 399, 404, 411, 422,
}


def pair(match: dict[str, str]) -> tuple[str, str]:
    return match.get("category", ""), match.get("subcategory", "")


def rank1_pattern(row: dict[str, object]) -> str:
    values = [pair(row["models"][model][0]) for model in ["gpt52", "gemini31_pro", "deepseek_v4"]]
    distinct = len(set(values))
    if distinct == 1:
        return "3/3 unanimous"
    if distinct == 2:
        return "2/3 agreement"
    return "all three differ"


def default_reason(item: dict[str, str], pattern: str) -> str:
    if item["primary_assessment"] == "needs_change":
        return "The existing label is absent from the unordered audit set; confirm the proposed replacement against the detailed taxonomy."
    if item["primary_assessment"] == "uncertain":
        return "The audit could not validate the current primary confidently; additional facts or taxonomy judgment are needed."
    if item["multi_label_assessment"] == "two_labels_supported":
        return "The text appears to support two labels; confirm that the second is a distinct issue rather than context or procedure."
    return f"The row remains in review because of {pattern.lower()} or model uncertainty."


def priority_for(
    item: dict[str, str],
    final_row: dict[str, object],
    stage7_rows: set[int],
) -> dict[str, object]:
    row_id = int(item["row_number"])
    pattern = rank1_pattern(final_row)
    score = 0
    signals: list[str] = []
    if item["primary_assessment"] == "needs_change":
        score += 35
        signals.append("existing primary absent from audit set")
    elif item["primary_assessment"] == "uncertain":
        score += 40
        signals.append("primary assessment uncertain")
    if item["multi_label_assessment"] == "uncertain":
        score += 25
        signals.append("multi-label decision uncertain")
    elif item["multi_label_assessment"] == "two_labels_supported":
        score += 8
        signals.append("two labels proposed")
    if pattern == "all three differ":
        score += 20
        signals.append("three-way original disagreement")
    elif pattern == "2/3 agreement":
        score += 10
        signals.append("original rank-1 disagreement")
    if row_id in stage7_rows:
        score += 4
        signals.append("repeated multi-label signal")
    if len(item["problem_description"].strip()) < 80:
        score += 12
        signals.append("very sparse description")
    if item["multi_label_assessment"] == "two_labels_supported" and not item["audit_label_2"]:
        score += 30
        signals.append("audit returned no second unique label")
    if row_id in HIGH_PRIORITY_NOTES:
        score += 40
        tier = "P1 - human decision essential"
        reason = HIGH_PRIORITY_NOTES[row_id]
        action = "Read the full text and relevant detailed-taxonomy entries; record an explicit human decision before using the row as training data."
    elif row_id in CLEAR_MULTI_ISSUE_ROWS and item["primary_assessment"] == "supported":
        score = min(score, 34)
        tier = "P3 - confirmation likely sufficient"
        reason = "The row expressly names separate issues and the existing label remains in the audit set; human review mainly confirms the additional label."
        action = "Quickly confirm the second label and mark accepted or remove it if it is only context/procedure."
    else:
        tier = "P2 - human confirmation recommended"
        reason = default_reason(item, pattern)
        action = "Compare the current label and audit set against the detailed taxonomy; confirm or correct before finalizing."
    return {
        "priority_tier": tier,
        "priority_score": score,
        "internal_priority_reason": reason,
        "recommended_human_action": action,
        "original_rank1_pattern": pattern,
        "priority_signals": "; ".join(signals),
    }


def add_priority_styles(styles_xml: bytes) -> tuple[bytes, dict[str, str]]:
    styles: dict[str, str] = {}
    for tier, color in [
        ("P1", "FFF4CCCC"),
        ("P2", "FFFFE699"),
        ("P3", "FFD9EAD3"),
    ]:
        styles_xml, style = audit_helpers.add_fill_style(styles_xml, color)
        styles[tier] = style
    return styles_xml, styles


def write_workbook(priorities: dict[int, dict[str, object]]) -> None:
    headers = [
        "internal_review_priority",
        "internal_priority_score",
        "internal_priority_reason",
        "recommended_human_action",
        "internal_priority_signals",
        "internal_reviewed_by",
    ]
    with ZipFile(SOURCE_WORKBOOK) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("source workbook has no sheet data")
    start = 73  # BU, after 72 columns in the order-insensitive audit workbook
    cols = [audit_helpers.excel_col(start + index) for index in range(len(headers))]
    files["xl/styles.xml"], priority_styles = add_priority_styles(files["xl/styles.xml"])
    for row in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_number = int(row.get("r", "0"))
        if row_number == 1:
            for col, header in zip(cols, headers):
                audit_helpers.set_cell(row, col, row_number, header, "1")
            continue
        priority = priorities.get(row_number)
        if priority:
            tier_key = str(priority["priority_tier"])[:2]
            values = [
                priority["priority_tier"],
                str(priority["priority_score"]),
                priority["internal_priority_reason"],
                priority["recommended_human_action"],
                priority["priority_signals"],
                "Codex / GPT-5 internal context review (no external API)",
            ]
            for col, value in zip(cols, values):
                audit_helpers.set_cell(row, col, row_number, str(value), priority_styles[tier_key])
        else:
            for col in cols:
                audit_helpers.set_cell(row, col, row_number, "", "2")
    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{cols[-1]}432")
    sheet_cols = root.find(f"{{{silver.NS}}}cols")
    if sheet_cols is None:
        sheet_cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, sheet_cols)
    for index, header in enumerate(headers):
        width = "50" if "reason" in header or "action" in header or "signals" in header else "28"
        ET.SubElement(sheet_cols, f"{{{silver.NS}}}col", {
            "width": width,
            "customWidth": "1",
            "min": str(start + index),
            "max": str(start + index),
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
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    final_review = json.loads(FINAL_REVIEW.read_text(encoding="utf-8"))
    stage7_rows = set(map(int, json.loads(STAGE7.read_text(encoding="utf-8")).keys()))
    priorities: dict[int, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    for item in queue:
        row_id = int(item["row_number"])
        priority = priority_for(item, final_review["rows"][str(row_id)], stage7_rows)
        priorities[row_id] = priority
        records.append({**item, **priority})
    records.sort(key=lambda row: (str(row["priority_tier"]), -int(row["priority_score"]), int(row["row_number"])))
    fields = [
        "priority_tier", "priority_score", "row_number", "problem_description", "current_ai_primary",
        "primary_assessment", "model_primary_assessment", "current_primary_in_label_set", "multi_label_assessment",
        "audit_label_1", "audit_label_2", "internal_priority_reason", "recommended_human_action",
        "original_rank1_pattern", "priority_signals", "audit_justification",
    ]
    with (OUT_DIR / "prioritized_review_queue.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    p1 = [record for record in records if str(record["priority_tier"]).startswith("P1")]
    with (OUT_DIR / "highest_priority_rows.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(p1)
    counts = Counter(str(record["priority_tier"]) for record in records)
    analysis = {
        "scope": "132 rows in the order-insensitive GPT-5.2 review queue",
        "review_method": "Internal Codex/GPT-5 context review using problem text, current and audit labels, original three-model rank-1 pattern, and prior multi-label evidence; no external API or user credentials used.",
        "priority_counts": dict(counts),
        "highest_priority_rows": [int(record["row_number"]) for record in p1],
        "important_caveat": "Priority indicates expected value of human adjudication, not confidence that the current or proposed label is wrong.",
    }
    (OUT_DIR / "priority_analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    write_workbook(priorities)
    print(f"wrote {OUTPUT_WORKBOOK}; priorities: {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
