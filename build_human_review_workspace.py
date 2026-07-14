#!/usr/bin/env python3
"""Build the workbook and extracts for the next human review."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

import create_silver_labels as silver

INPUT_WORKBOOK = Path("silver_labels/05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx")
INPUT_ROWS = Path("redaction_reviewed_v5_clean.xlsx")
AUDIT = Path("silver_labels/04_review/final_review.json")
OUT_DIR = Path("silver_labels/06_human_review_workspace")
OUTPUT_WORKBOOK = OUT_DIR / "redaction_reviewed_v5_clean_human_review_workspace.xlsx"
DISAGREEMENT_CSV = OUT_DIR / "disagreement_rows.csv"
ANALYSIS_JSON = OUT_DIR / "agreement_analysis.json"
MODELS = ["gpt52", "gemini31_pro", "deepseek_v4"]


def excel_col(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def pair(match: dict[str, str]) -> tuple[str, str]:
    return match.get("category", ""), match.get("subcategory", "")


def label(value: tuple[str, str]) -> str:
    return f"{value[0]} / {value[1]}".strip(" /")


def four_pass_info(row: dict[str, object]) -> tuple[str, int, int, bool]:
    model_pairs = [pair(row["models"][model][0]) for model in MODELS]
    all_pairs = model_pairs + [pair(row["review"])]
    counts = Counter(all_pairs)
    maximum = max(counts.values())
    distinct = len(counts)
    if distinct == 1:
        pattern = "4/4 unanimous"
    elif maximum == 3:
        pattern = "3/4 agreement"
    else:
        pattern = "2/4 agreement"
    return pattern, maximum, distinct, distinct > 1


def analyze(rows: list[dict[str, str]], audit: dict[str, object]) -> list[int]:
    three: Counter[tuple[int, int]] = Counter()
    four: Counter[tuple[int, int]] = Counter()
    internal_matches: Counter[int] = Counter()
    disagreement_ids: list[int] = []
    for row_id_text, row in audit["rows"].items():
        row_id = int(row_id_text)
        model_pairs = [pair(row["models"][model][0]) for model in MODELS]
        counts = Counter(model_pairs)
        three[(len(counts), max(counts.values()))] += 1
        pattern, maximum, distinct, disagreement = four_pass_info(row)
        four[(distinct, maximum)] += 1
        internal_matches[sum(pair(row["review"]) == value for value in model_pairs)] += 1
        if disagreement:
            disagreement_ids.append(row_id)
    analysis = {
        "scope": "431 rows in redaction_reviewed_v5_clean.xlsx",
        "four_pass_definition": ["GPT-5.2", "Gemini 3.1 Pro Preview", "DeepSeek v4", "internal reviewed label"],
        "important_caveat": "The internal reviewed label is derived from the three model outputs plus in-context review, so four-pass agreement is descriptive rather than independent-rater reliability.",
        "three_independent_models": {
            "unanimous_3_of_3": three[(1, 3)],
            "two_agree_2_of_3": three[(2, 2)],
            "all_distinct_1_of_3": three[(3, 1)],
            "any_rank1_disagreement": sum(v for (distinct, _), v in three.items() if distinct > 1),
        },
        "four_pass_comparison": {
            "unanimous_4_of_4": four[(1, 4)],
            "three_agree_3_of_4": four[(2, 3)],
            "two_agree_2_of_4": sum(v for (distinct, maximum), v in four.items() if maximum == 2),
            "four_pass_disagreement": sum(v for (distinct, _), v in four.items() if distinct > 1),
        },
        "internal_label_matches_how_many_independent_models": dict(sorted(internal_matches.items())),
        "disagreement_row_numbers": sorted(disagreement_ids),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return sorted(disagreement_ids)


def write_disagreements(rows: list[dict[str, str]], audit: dict[str, object], row_ids: list[int]) -> None:
    fields = ["row_number", "problem_description", "original_human_category", "original_human_subcategory", "gpt52_rank1", "gemini31_pro_rank1", "deepseek_v4_rank1", "internal_review", "four_pass_pattern", "four_pass_max_agreement", "four_pass_distinct_labels", "review_basis", "gpt52_all_candidates", "gemini31_pro_all_candidates", "deepseek_v4_all_candidates"]
    with DISAGREEMENT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row_id in row_ids:
            item = audit["rows"][str(row_id)]
            pattern, maximum, distinct, _ = four_pass_info(item)
            out = {
                "row_number": str(row_id),
                "problem_description": item["problem_description"],
                "original_human_category": rows[row_id - 1].get("B", ""),
                "original_human_subcategory": rows[row_id - 1].get("C", ""),
                "internal_review": label(pair(item["review"])),
                "four_pass_pattern": pattern,
                "four_pass_max_agreement": str(maximum),
                "four_pass_distinct_labels": str(distinct),
                "review_basis": item["basis"],
            }
            for model in MODELS:
                out[f"{model}_rank1"] = label(pair(item["models"][model][0]))
                out[f"{model}_all_candidates"] = json.dumps(item["models"][model], ensure_ascii=False)
            writer.writerow(out)


def set_cell(row: ET.Element, col: str, row_number: int, value: str, style: str | None = None) -> None:
    cell = ET.SubElement(row, f"{{{silver.NS}}}c", {"r": f"{col}{row_number}", "t": "inlineStr"})
    if style is not None:
        cell.set("s", style)
    inline = ET.SubElement(cell, f"{{{silver.NS}}}is")
    text = ET.SubElement(inline, f"{{{silver.NS}}}t")
    text.text = value


def add_blue_style(styles_xml: bytes) -> bytes:
    root = ET.fromstring(styles_xml)
    fills = root.find(f"{{{silver.NS}}}fills")
    xfs = root.find(f"{{{silver.NS}}}cellXfs")
    if fills is None or xfs is None:
        raise ValueError("styles are missing fills/cellXfs")
    fill = ET.SubElement(fills, f"{{{silver.NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{silver.NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{silver.NS}}}fgColor", {"rgb": "FFDDEBF7"})
    ET.SubElement(pattern, f"{{{silver.NS}}}bgColor", {"indexed": "64"})
    xf = ET.SubElement(xfs, f"{{{silver.NS}}}xf", {"numFmtId": "0", "fontId": "0", "fillId": str(len(fills) - 1), "borderId": "0", "pivotButton": "0", "quotePrefix": "0", "xfId": "0", "applyFill": "1"})
    ET.SubElement(xf, f"{{{silver.NS}}}alignment", {"vertical": "top", "wrapText": "1"})
    fills.set("count", str(len(fills)))
    xfs.set("count", str(len(xfs)))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False)


def write_workspace(rows: list[dict[str, str]], audit: dict[str, object]) -> None:
    headers = ["workspace_original_human_category", "workspace_original_human_subcategory", "workspace_internal_category", "workspace_internal_subcategory", "four_pass_pattern", "four_pass_max_agreement", "four_pass_distinct_labels", "disagreement_flag", "your_review_category", "your_review_subcategory", "your_review_status", "your_review_notes"]
    with ZipFile(INPUT_WORKBOOK) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("workbook has no sheet data")
    first_extra = 51  # AY, immediately after AX
    cols = [excel_col(first_extra + i) for i in range(len(headers))]
    for row in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_number = int(row.get("r", "0"))
        if row_number == 1:
            for col, header in zip(cols, headers):
                set_cell(row, col, row_number, header, "1")
        elif row_number >= 2:
            item = audit["rows"][str(row_number)]
            pattern, maximum, distinct, disagreement = four_pass_info(item)
            values = [rows[row_number - 1].get("B", ""), rows[row_number - 1].get("C", ""), item["review"].get("category", ""), item["review"].get("subcategory", ""), pattern, str(maximum), str(distinct), "yes" if disagreement else "no", "", "", "", ""]
            for col, value in zip(cols, values):
                set_cell(row, col, row_number, value, "4" if col in cols[-4:] else "2")
    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{cols[-1]}{len(rows)}")
    sheet_cols = root.find(f"{{{silver.NS}}}cols")
    if sheet_cols is None:
        sheet_cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, sheet_cols)
    for i, header in enumerate(headers):
        ET.SubElement(sheet_cols, f"{{{silver.NS}}}col", {"width": "34" if "notes" in header else "26", "customWidth": "1", "min": str(first_extra + i), "max": str(first_extra + i)})
    auto_filter = root.find(f"{{{silver.NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{silver.NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{cols[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    files["xl/styles.xml"] = add_blue_style(files["xl/styles.xml"])
    with ZipFile(OUTPUT_WORKBOOK, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def write_readme(analysis: dict[str, object]) -> None:
    independent = analysis["three_independent_models"]
    four = analysis["four_pass_comparison"]
    lines = [
        "# Human-review workspace", "",
        "Use `redaction_reviewed_v5_clean_human_review_workspace.xlsx` for the next review.", "",
        "The workbook includes the original human label, all ranked outputs from GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4, the internal reviewed label, and blue blank cells for `your_review_category`, `your_review_subcategory`, `your_review_status`, and `your_review_notes`.", "",
        "The disagreement-only extract is `disagreement_rows.csv`; it includes all ranked candidates and justifications. Machine-readable counts are in `agreement_analysis.json`.", "",
        "## Agreement", "",
        f"Three independent models: {independent['unanimous_3_of_3']} unanimous 3/3 ({independent['unanimous_3_of_3'] / 431:.1%}), {independent['two_agree_2_of_3']} with 2/3 agreement ({independent['two_agree_2_of_3'] / 431:.1%}), and {independent['all_distinct_1_of_3']} all-distinct rows ({independent['all_distinct_1_of_3'] / 431:.1%}). Any rank-1 disagreement: {independent['any_rank1_disagreement']} rows.", "",
        f"Four displayed passes (three models plus the internal reviewed label): {four['unanimous_4_of_4']} unanimous 4/4 ({four['unanimous_4_of_4'] / 431:.1%}), {four['three_agree_3_of_4']} with 3/4 agreement ({four['three_agree_3_of_4'] / 431:.1%}), and {four['two_agree_2_of_4']} with 2/4 agreement ({four['two_agree_2_of_4'] / 431:.1%}). Any four-pass disagreement: {four['four_pass_disagreement']} rows.", "",
        "Caveat: the internal reviewed label is derived from the three model outputs plus in-context review, so four-pass agreement is descriptive, not independent-rater reliability.", "",
        "The original workbook and original human-label columns remain unchanged. The blank human fields are intentionally not prefilled.",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = silver.read_workbook_rows(INPUT_ROWS)
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    disagreement_ids = analyze(rows, audit)
    write_disagreements(rows, audit, disagreement_ids)
    write_workspace(rows, audit)
    write_readme(json.loads(ANALYSIS_JSON.read_text(encoding="utf-8")))
    print(f"wrote {OUTPUT_WORKBOOK}; disagreement rows: {len(disagreement_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
