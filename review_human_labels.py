#!/usr/bin/env python3
"""Record the human-label corrections explicitly identified in That’s So FETCH."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

import create_silver_labels as silver


SOURCE_PDF = Path("interim_not_to_commit/thats_so_fetch.pdf")
SOURCE_WORKBOOK = Path("redaction_reviewed_v5_clean.xlsx")
INPUT_WORKBOOK = Path("silver_labels/04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx")
OUT_DIR = Path("silver_labels/05_human_label_review")
OUTPUT_WORKBOOK = OUT_DIR / "redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx"


# These are the nine cases in Table 3 (PDF page 199).  The marker protects
# against accidentally applying a row number to a changed input workbook.
CASES = {
    29: ("roofing company to replace my roof", "retained", "The PDF lists Realty > Construction; the existing human label agrees."),
    70: ("bear sprayed through a hole he cut in the fence", "retained", "The PDF lists Realty > Neighbor Disputes; the existing human label agrees."),
    142: ("manage ownership of a dog", "retained", "The PDF lists Consumer; the existing human top-level label agrees."),
    147: ("wedding planner used photos", "retained", "The PDF lists Consumer; the existing human top-level label agrees."),
    149: ("Lost a trial for a driving motor vehicle", "corrected", "The PDF identifies the Consumer human label as an error. An appeal of a traffic trial is Criminal Law; Post Conviction/ Appeals is the closest detailed subcategory."),
    188: ("filing a case in small claims court", "corrected", "The PDF identifies the Criminal human label as an error. Filing a small-claims case is Consumer Law / Small Claims Advice."),
    212: ("car accident in which I was involved and had no car insurance", "retained", "The PDF calls the LLM's personal-injury/property-damage result an LLM error; Debtor/Creditor is the existing human label and matches the payment/debt framing."),
    220: ("received unemployment during the pandemic", "corrected", "The PDF identifies the Debtor/Creditor human label as an error. Pandemic unemployment benefit overpayment/appeal is Administrative Law / Unemployment."),
    339: ("PA ( Physician Associate/Assistant)", "corrected", "The PDF identifies the Labor & Employment human label as an error. The issue is whether a physician assistant may practice under licensing/supervision rules: Administrative Law / Professional Licensing."),
}

CORRECTIONS = {
    149: {"category": "Criminal Law", "subcategory": "Post Conviction/ Appeals"},
    188: {"category": "Consumer Law", "subcategory": "Small Claims Advice"},
    220: {"category": "Administrative Law", "subcategory": "Unemployment"},
    339: {"category": "Administrative Law", "subcategory": "Professional Licensing"},
}


def excel_col(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def set_cell(row: ET.Element, col: str, row_number: int, value: str, style: str | None = None) -> None:
    cell = ET.SubElement(row, f"{{{silver.NS}}}c", {"r": f"{col}{row_number}", "t": "inlineStr"})
    if style is not None:
        cell.set("s", style)
    inline = ET.SubElement(cell, f"{{{silver.NS}}}is")
    text = ET.SubElement(inline, f"{{{silver.NS}}}t")
    text.text = value


def update_styles(styles_xml: bytes) -> bytes:
    root = ET.fromstring(styles_xml)
    fills = root.find(f"{{{silver.NS}}}fills")
    cell_xfs = root.find(f"{{{silver.NS}}}cellXfs")
    if fills is None or cell_xfs is None:
        raise ValueError("styles are missing fills/cellXfs")
    fill = ET.SubElement(fills, f"{{{silver.NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{silver.NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{silver.NS}}}fgColor", {"rgb": "FFFFC7CE"})
    ET.SubElement(pattern, f"{{{silver.NS}}}bgColor", {"indexed": "64"})
    xf = ET.SubElement(cell_xfs, f"{{{silver.NS}}}xf", {
        "numFmtId": "0", "fontId": "0", "fillId": str(len(fills) - 1),
        "borderId": "0", "pivotButton": "0", "quotePrefix": "0", "xfId": "0",
        "applyFill": "1",
    })
    ET.SubElement(xf, f"{{{silver.NS}}}alignment", {"vertical": "top", "wrapText": "1"})
    fills.set("count", str(len(fills)))
    cell_xfs.set("count", str(len(cell_xfs)))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False)


def main() -> int:
    rows = silver.read_workbook_rows(SOURCE_WORKBOOK)
    taxonomy, valid_pairs = silver.read_taxonomy(Path("../app/data/taxonomy_detailed_descriptions.csv"))
    for row_id, (marker, _, _) in CASES.items():
        if marker.lower() not in rows[row_id - 1].get("A", "").lower():
            raise ValueError(f"PDF case marker did not match workbook row {row_id}")
    for row_id, correction in CORRECTIONS.items():
        if (correction["category"], correction["subcategory"]) not in valid_pairs:
            raise ValueError(f"correction for row {row_id} is not in detailed taxonomy")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = {
        "source_pdf": str(SOURCE_PDF),
        "source_pdf_location": "Table 3, PDF page 199",
        "scope": "The nine cases explicitly discussed in the paper's error table; this is not a claim that all 431 rows received an independent human relabeling.",
        "cases": {},
    }
    for row_id, (marker, status, note) in CASES.items():
        original = rows[row_id - 1]
        proposed = CORRECTIONS.get(row_id, {
            "category": original.get("B", ""),
            "subcategory": original.get("C", ""),
        })
        audit["cases"][str(row_id)] = {
            "problem_description": original.get("A", ""),
            "original_human_category": original.get("B", ""),
            "original_human_subcategory": original.get("C", ""),
            "reviewed_category": proposed["category"],
            "reviewed_subcategory": proposed["subcategory"],
            "status": status,
            "justification": note,
        }
    (OUT_DIR / "human_label_review.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# Human-label double-check",
        "",
        f"Source: `{SOURCE_PDF}`; Table 3 on PDF page 199.",
        "",
        "This review checks the nine cases explicitly discussed in the paper. It preserves the original human columns and records proposed checked labels separately.",
        "",
        "Four corrections are supported by the paper's `Human error` classifications:",
        "",
        "- Row 149: `Consumer Law` → `Criminal Law / Post Conviction/ Appeals`.",
        "- Row 188: `Criminal Law` → `Consumer Law / Small Claims Advice`.",
        "- Row 220: `Debtor/Creditor` → `Administrative Law / Unemployment`.",
        "- Row 339: `Labor & Employment` → `Administrative Law / Professional Licensing`.",
        "",
        "The other five table examples agree with the existing human top-level label. Corrected rows are highlighted light red in the checked workbook; all AI-classified rows retain their existing pale-yellow highlight.",
        "",
        "The checked workbook is a derived artifact. `redaction_reviewed_v5_clean.xlsx` remains unchanged.",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    headers = [
        "human_original_category", "human_original_subcategory",
        "human_reviewed_category", "human_reviewed_subcategory",
        "human_review_status", "human_review_justification",
    ]
    with ZipFile(INPUT_WORKBOOK) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("workbook has no sheet data")
    first_extra = 45  # AS, immediately after AR in the reviewed silver workbook
    extra_cols = [excel_col(first_extra + i) for i in range(len(headers))]
    for row in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_number = int(row.get("r", "0"))
        if row_number == 1:
            for col, header in zip(extra_cols, headers):
                set_cell(row, col, row_number, header, "1")
        elif row_number >= 2:
            original = rows[row_number - 1]
            case = CASES.get(row_number)
            if case:
                _, status, note = case
                reviewed = CORRECTIONS.get(row_number, {
                    "category": original.get("B", ""),
                    "subcategory": original.get("C", ""),
                })
                values = [
                    original.get("B", ""), original.get("C", ""),
                    reviewed["category"], reviewed["subcategory"], status, note,
                ]
                style = "3" if status == "corrected" else "2"
            else:
                values = [original.get("B", ""), original.get("C", ""), "", "", "not_in_pdf_scope", ""]
                style = "2"
            for col, value in zip(extra_cols, values):
                set_cell(row, col, row_number, value, style)
    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{extra_cols[-1]}{len(rows)}")
    cols = root.find(f"{{{silver.NS}}}cols")
    if cols is None:
        cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, cols)
    for i, header in enumerate(headers):
        width = 70 if "justification" in header else 30
        ET.SubElement(cols, f"{{{silver.NS}}}col", {"width": str(width), "customWidth": "1", "min": str(first_extra + i), "max": str(first_extra + i)})
    auto_filter = root.find(f"{{{silver.NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{silver.NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{extra_cols[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    files["xl/styles.xml"] = update_styles(files["xl/styles.xml"])
    with ZipFile(OUTPUT_WORKBOOK, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    print(f"wrote {OUTPUT_WORKBOOK}; corrected {len(CORRECTIONS)} human labels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
