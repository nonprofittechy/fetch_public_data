#!/usr/bin/env python3
"""Build a review workbook for rows with multiple model-supported labels."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

import create_silver_labels as silver

SOURCE = Path("silver_labels/06_human_review_workspace/redaction_reviewed_v5_clean_human_review_workspace.xlsx")
ROWS = Path("redaction_reviewed_v5_clean.xlsx")
EVIDENCE = Path("silver_labels/07_multilabel_audit/multilabel_candidate_evidence.json")
OUT = Path("silver_labels/07_multilabel_audit/redaction_reviewed_v5_clean_multilabel_review_workspace.xlsx")


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
    text.text = str(value)


def add_fill_style(styles_xml: bytes, color: str) -> tuple[bytes, str]:
    root = ET.fromstring(styles_xml)
    fills = root.find(f"{{{silver.NS}}}fills")
    xfs = root.find(f"{{{silver.NS}}}cellXfs")
    if fills is None or xfs is None:
        raise ValueError("styles are missing fills/cellXfs")
    fill = ET.SubElement(fills, f"{{{silver.NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{silver.NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{silver.NS}}}fgColor", {"rgb": color})
    ET.SubElement(pattern, f"{{{silver.NS}}}bgColor", {"indexed": "64"})
    xf = ET.SubElement(
        xfs,
        f"{{{silver.NS}}}xf",
        {
            "numFmtId": "0",
            "fontId": "0",
            "fillId": str(len(fills) - 1),
            "borderId": "0",
            "pivotButton": "0",
            "quotePrefix": "0",
            "xfId": "0",
            "applyFill": "1",
        },
    )
    ET.SubElement(xf, f"{{{silver.NS}}}alignment", {"vertical": "top", "wrapText": "1"})
    fills.set("count", str(len(fills)))
    xfs.set("count", str(len(xfs)))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False), str(len(xfs) - 1)


def candidate_values(item: dict[str, object]) -> list[str]:
    values: list[str] = []
    for index in range(3):
        if index < len(item.get("supported_candidates", [])):
            candidate = item["supported_candidates"][index]
            values.extend(
                [
                    candidate.get("category", ""),
                    candidate.get("subcategory", ""),
                    candidate.get("model_support", ""),
                    candidate.get("rank1_support", ""),
                    ", ".join(candidate.get("models", [])),
                    " / ".join(
                        f"{model}: {candidate.get('justifications', {}).get(model, '')}"
                        for model in candidate.get("models", [])
                    ),
                ]
            )
        else:
            values.extend(["", "", "", "", "", ""])
    return values


def main() -> int:
    rows = silver.read_workbook_rows(ROWS)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    headers = [
        "multilabel_ai_assessment",
        "multilabel_supported_candidate_count",
    ]
    for index in range(1, 4):
        headers.extend(
            [
                f"multilabel_candidate_{index}_category",
                f"multilabel_candidate_{index}_subcategory",
                f"multilabel_candidate_{index}_model_support",
                f"multilabel_candidate_{index}_rank1_support",
                f"multilabel_candidate_{index}_models",
                f"multilabel_candidate_{index}_justification",
            ]
        )
    headers.extend(
        [
            "your_multilabel_label_1_category",
            "your_multilabel_label_1_subcategory",
            "your_multilabel_label_2_category",
            "your_multilabel_label_2_subcategory",
            "your_multilabel_label_3_category",
            "your_multilabel_label_3_subcategory",
            "your_multilabel_review_status",
            "your_multilabel_notes",
        ]
    )
    with ZipFile(SOURCE) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("workbook has no sheet data")
    start = 63  # BK, immediately after the 62 columns in the one-label workspace
    cols = [excel_col(start + i) for i in range(len(headers))]
    ai_style = human_style = None
    files["xl/styles.xml"], ai_style = add_fill_style(files["xl/styles.xml"], "FFFFE699")
    files["xl/styles.xml"], human_style = add_fill_style(files["xl/styles.xml"], "FFDDEBF7")
    for row in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_number = int(row.get("r", "0"))
        if row_number == 1:
            for col, header in zip(cols, headers):
                set_cell(row, col, row_number, header, "1")
            continue
        if row_number < 2 or row_number > len(rows):
            continue
        item = evidence.get(str(row_number))
        if item:
            values = [item["assessment"], str(len(item["supported_candidates"]))] + candidate_values(item)
            ai_values = values
        else:
            ai_values = ["", ""] + ["" for _ in range(18)]
        values = ai_values + ["" for _ in range(8)]
        for col, value in zip(cols, values):
            style = human_style if col in cols[-8:] else (ai_style if item else "2")
            set_cell(row, col, row_number, value, style)
    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{cols[-1]}{len(rows)}")
    sheet_cols = root.find(f"{{{silver.NS}}}cols")
    if sheet_cols is None:
        sheet_cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, sheet_cols)
    for index, header in enumerate(headers):
        width = "42" if "justification" in header or "notes" in header else "26"
        ET.SubElement(
            sheet_cols,
            f"{{{silver.NS}}}col",
            {"width": width, "customWidth": "1", "min": str(start + index), "max": str(start + index)},
        )
    auto_filter = root.find(f"{{{silver.NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{silver.NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{cols[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    print(f"wrote {OUT}; candidate rows: {len(evidence)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
