#!/usr/bin/env python3
"""Run a fresh Azure GPT-5.2 audit allowing at most two labels per row."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from xml.etree import ElementTree as ET

import create_silver_labels as silver

NS = silver.NS
INPUT_ROWS = Path("redaction_reviewed_v5_clean.xlsx")
FINAL_AI_WORKBOOK = Path("silver_labels/05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx")
FINAL_REVIEW = Path("silver_labels/04_review/final_review.json")
TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")
OUT_DIR = Path("silver_labels/08_gpt52_two_label_audit")
MODEL = "gpt-5.2"
BATCH_SIZE = 10
MODE = "two-label-audit"


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


def build_prompt(taxonomy_text: str, batch: list[tuple[int, str, str]]) -> str:
    records = "\n\n".join(
        f"ROW {row_id}\nCURRENT FINAL AI PRIMARY LABEL: {current_label}\nPROBLEM DESCRIPTION: {description}"
        for row_id, description, current_label in batch
    )
    return f"""You are auditing a completed legal-help routing dataset.

Independently classify each user problem below using ONLY the canonical taxonomy
entries and their detailed descriptions. The CURRENT FINAL AI PRIMARY LABEL is
provided for audit comparison, but do not accept it automatically and do not
use the existing human labels as a shortcut. Do not use a keyword classifier,
SPOT, or any external taxonomy.

Return exactly one or two possible category/subcategory matches per row, in
descending order of fit. Return a second match ONLY when the problem text
supports a distinct additional legal issue or an explicitly requested legal
service. Do not add a second match merely because it is a neighboring category,
a generic fallback, or another procedural framing of the same issue. If the
current primary is not supported, replace it with the best supported label.

Use exact category and subcategory strings from the taxonomy. Do not invent a
label. For every match, provide a concise justification grounded in the text.
Also state whether the current primary is supported and whether one or two
labels are supported.

Allowed values:
- primary_assessment: supported | needs_change | uncertain
- multi_label_assessment: one_label_sufficient | two_labels_supported | uncertain
- confidence: high | medium | low

Return ONLY valid JSON in this shape:
{{
  "classifications": [
    {{
      "row_id": 1,
      "primary_assessment": "supported|needs_change|uncertain",
      "multi_label_assessment": "one_label_sufficient|two_labels_supported|uncertain",
      "matches": [
        {{"category": "...", "subcategory": "...", "justification": "...", "confidence": "high|medium|low"}}
      ],
      "audit_justification": "..."
    }}
  ]
}}

CANONICAL DETAILED TAXONOMY:
{taxonomy_text}

ROWS TO AUDIT:
{records}
"""


def normalize_audit(
    response: dict[str, object],
    requested_ids: set[int],
    valid_pairs: dict[tuple[str, str], dict[str, str]],
) -> dict[int, dict[str, object]]:
    raw_items = response.get("classifications", [])
    if not isinstance(raw_items, list):
        raise ValueError("classifications is not a list")
    normalized: dict[int, dict[str, object]] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            row_id = int(item.get("row_id"))
        except (TypeError, ValueError):
            continue
        if row_id not in requested_ids:
            continue
        raw_matches = item.get("matches", [])
        if not isinstance(raw_matches, list):
            continue
        matches: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for raw_match in raw_matches[:2]:
            if not isinstance(raw_match, dict):
                continue
            category = silver.CATEGORY_ALIASES.get(
                str(raw_match.get("category", "")).strip(),
                str(raw_match.get("category", "")).strip(),
            )
            subcategory = str(raw_match.get("subcategory", "")).strip()
            value = (category, subcategory)
            if value not in valid_pairs or value in seen:
                continue
            seen.add(value)
            confidence = str(raw_match.get("confidence", "medium")).strip().lower()
            if confidence not in {"high", "medium", "low"}:
                confidence = "medium"
            matches.append(
                {
                    "category": category,
                    "subcategory": subcategory,
                    "justification": " ".join(str(raw_match.get("justification", "")).split())
                    or "Best fit based on the facts provided.",
                    "confidence": confidence,
                }
            )
        if not matches:
            continue
        primary_assessment = str(item.get("primary_assessment", "uncertain")).strip().lower()
        if primary_assessment not in {"supported", "needs_change", "uncertain"}:
            primary_assessment = "uncertain"
        multi_label_assessment = str(item.get("multi_label_assessment", "uncertain")).strip().lower()
        if multi_label_assessment not in {"one_label_sufficient", "two_labels_supported", "uncertain"}:
            multi_label_assessment = "uncertain"
        normalized[row_id] = {
            "primary_assessment": primary_assessment,
            "multi_label_assessment": multi_label_assessment,
            "matches": matches,
            "audit_justification": " ".join(str(item.get("audit_justification", "")).split())
            or "Audit decision based on the problem text and detailed taxonomy.",
        }
    missing = requested_ids - normalized.keys()
    if missing:
        raise ValueError(f"model omitted or invalidated rows: {sorted(missing)}")
    return normalized


def load_checkpoint(path: Path) -> dict[int, dict[str, object]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(key): value for key, value in raw.items()}


def save_checkpoint(path: Path, results: dict[int, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_metadata(
    run_dir: Path,
    input_path: Path,
    final_review_path: Path,
    taxonomy_path: Path,
    taxonomy: list[dict[str, str]],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    (run_dir / "responses").mkdir(exist_ok=True)
    (run_dir / "taxonomy_snapshot.csv").write_text(
        taxonomy_path.read_text(encoding="utf-8-sig"), encoding="utf-8"
    )
    metadata = {
        "provider": "azure",
        "model": MODEL,
        "mode": MODE,
        "input_rows_file": str(input_path),
        "input_rows_sha256": sha256(input_path),
        "final_ai_silver_workbook": str(FINAL_AI_WORKBOOK),
        "final_ai_silver_workbook_sha256": sha256(FINAL_AI_WORKBOOK),
        "final_review_json": str(final_review_path),
        "final_review_json_sha256": sha256(final_review_path),
        "taxonomy_file": str(taxonomy_path),
        "taxonomy_snapshot": "taxonomy_snapshot.csv",
        "taxonomy_sha256": sha256(run_dir / "taxonomy_snapshot.csv"),
        "taxonomy_rows": len(taxonomy),
        "prompt_builder": "run_two_label_gpt52_audit.py:build_prompt",
        "max_matches_per_row": 2,
        "batch_size": BATCH_SIZE,
        "resume_note": "The run was resumed after a provider timeout using 10-row batches; earlier checkpointed rows and their original 20-row prompts/responses are retained in this folder.",
        "keyword_classifier": False,
        "spot_classifier": False,
        "credentials": "OPENAI_API_KEY and OPENAI_BASE_URL loaded at runtime; not written to artifacts",
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "prompt_template.txt").write_text(
        "The rendered prompt for each batch is saved under prompts/.\n"
        "The template is build_prompt() in run_two_label_gpt52_audit.py.\n",
        encoding="utf-8",
    )


def write_prompts(run_dir: Path, taxonomy: list[dict[str, str]], rows: list[dict[str, str]], final_review: dict[str, object]) -> None:
    taxonomy_text = silver.taxonomy_block(taxonomy)
    for start in range(0, len(rows) - 1, BATCH_SIZE):
        batch = []
        for row_id, row in enumerate(rows[1:], start=2):
            if start <= row_id - 2 < start + BATCH_SIZE:
                review = final_review["rows"][str(row_id)]["review"]
                batch.append((row_id, row["A"], label(pair(review))))
        (run_dir / "prompts" / f"batch10_{start // BATCH_SIZE + 1:03d}.txt").write_text(
            build_prompt(taxonomy_text, batch), encoding="utf-8"
        )


def run_audit(
    rows: list[dict[str, str]],
    taxonomy: list[dict[str, str]],
    valid_pairs: dict[tuple[str, str], dict[str, str]],
    final_review: dict[str, object],
    checkpoint: Path,
    run_dir: Path,
) -> dict[int, dict[str, object]]:
    silver.load_dotenv_if_needed(Path("../.env"))
    results = load_checkpoint(checkpoint)
    write_metadata(run_dir, INPUT_ROWS, FINAL_REVIEW, TAXONOMY, taxonomy)
    write_prompts(run_dir, taxonomy, rows, final_review)
    taxonomy_text = silver.taxonomy_block(taxonomy)
    pending = [
        (row_id, row["A"], label(pair(final_review["rows"][str(row_id)]["review"])))
        for row_id, row in enumerate(rows[1:], start=2)
        if row_id not in results
    ]
    total = len(rows) - 1
    for offset in range(0, len(pending), BATCH_SIZE):
        batch = pending[offset : offset + BATCH_SIZE]
        requested = {row_id for row_id, _, _ in batch}
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                prompt = build_prompt(taxonomy_text, batch)
                response, raw_response = silver.call_model("azure", prompt, MODEL, 16000)
                parsed = normalize_audit(response, requested, valid_pairs)
                results.update(parsed)
                save_checkpoint(checkpoint, results)
                batch_number = offset // BATCH_SIZE + 1
                (run_dir / "responses" / f"batch10_{batch_number:03d}.json").write_text(raw_response, encoding="utf-8")
                print(f"audited {len(results)}/{total} rows", flush=True)
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001 - retry provider/validation failures
                last_error = exc
                if attempt < 3:
                    time.sleep(2 * attempt)
        if last_error is not None:
            raise RuntimeError(f"batch starting at row {batch[0][0]} failed: {last_error}")
    return results


def set_cell(row: ET.Element, col: str, row_number: int, value: str, style: str | None = None) -> None:
    cell = ET.SubElement(row, f"{{{NS}}}c", {"r": f"{col}{row_number}", "t": "inlineStr"})
    if style is not None:
        cell.set("s", style)
    inline = ET.SubElement(cell, f"{{{NS}}}is")
    text = ET.SubElement(inline, f"{{{NS}}}t")
    text.text = str(value)


def add_fill_style(styles_xml: bytes, color: str) -> tuple[bytes, str]:
    root = ET.fromstring(styles_xml)
    fills = root.find(f"{{{NS}}}fills")
    xfs = root.find(f"{{{NS}}}cellXfs")
    if fills is None or xfs is None:
        raise ValueError("styles are missing fills/cellXfs")
    fill = ET.SubElement(fills, f"{{{NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{NS}}}fgColor", {"rgb": color})
    ET.SubElement(pattern, f"{{{NS}}}bgColor", {"indexed": "64"})
    xf = ET.SubElement(xfs, f"{{{NS}}}xf", {
        "numFmtId": "0", "fontId": "0", "fillId": str(len(fills) - 1),
        "borderId": "0", "pivotButton": "0", "quotePrefix": "0", "xfId": "0", "applyFill": "1",
    })
    ET.SubElement(xf, f"{{{NS}}}alignment", {"vertical": "top", "wrapText": "1"})
    fills.set("count", str(len(fills)))
    xfs.set("count", str(len(xfs)))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False), str(len(xfs) - 1)


def write_workbook(source: Path, output: Path, rows: list[dict[str, str]], final_review: dict[str, object], results: dict[int, dict[str, object]]) -> None:
    headers = [
        "two_label_audit_status", "two_label_audit_primary_assessment", "two_label_audit_multi_label_assessment",
        "two_label_audit_current_ai_primary",
        "two_label_audit_category_1", "two_label_audit_subcategory_1", "two_label_audit_justification_1", "two_label_audit_confidence_1",
        "two_label_audit_category_2", "two_label_audit_subcategory_2", "two_label_audit_justification_2", "two_label_audit_confidence_2",
        "two_label_audit_justification", "two_label_audit_model",
        "your_two_label_review_category_1", "your_two_label_review_subcategory_1",
        "your_two_label_review_category_2", "your_two_label_review_subcategory_2",
        "your_two_label_review_status", "your_two_label_review_notes",
    ]
    with ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("source workbook has no sheet data")
    start = 51  # AY, immediately after AX in the human-checked final AI workbook
    cols = [excel_col(start + i) for i in range(len(headers))]
    files["xl/styles.xml"], ai_style = add_fill_style(files["xl/styles.xml"], "FFFFE699")
    files["xl/styles.xml"], human_style = add_fill_style(files["xl/styles.xml"], "FFDDEBF7")
    for row_el in sheet_data.findall(f"{{{NS}}}row"):
        row_number = int(row_el.get("r", "0"))
        if row_number == 1:
            for col, header in zip(cols, headers):
                set_cell(row_el, col, row_number, header, "1")
            continue
        if row_number < 2 or row_number > len(rows):
            continue
        result = results[row_number]
        review = final_review["rows"][str(row_number)]["review"]
        matches = result["matches"]
        values = [
            "two labels" if result["multi_label_assessment"] == "two_labels_supported" else "one label / uncertain",
            result["primary_assessment"], result["multi_label_assessment"], label(pair(review)),
        ]
        for index in range(2):
            match = matches[index] if index < len(matches) else {}
            values.extend([match.get("category", ""), match.get("subcategory", ""), match.get("justification", ""), match.get("confidence", "")])
        values.extend([result["audit_justification"], MODEL, "", "", "", "", "", ""])
        for col, value in zip(cols, values):
            set_cell(row_el, col, row_number, value, human_style if col in cols[-6:] else ai_style)
    dimension = root.find(f"{{{NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{cols[-1]}{len(rows)}")
    sheet_cols = root.find(f"{{{NS}}}cols")
    if sheet_cols is None:
        sheet_cols = ET.Element(f"{{{NS}}}cols")
        root.insert(2, sheet_cols)
    for index, header in enumerate(headers):
        width = "42" if "justification" in header or "notes" in header else "26"
        ET.SubElement(sheet_cols, f"{{{NS}}}col", {"width": width, "customWidth": "1", "min": str(start + index), "max": str(start + index)})
    auto_filter = root.find(f"{{{NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{cols[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)


def write_analysis(rows: list[dict[str, str]], final_review: dict[str, object], results: dict[int, dict[str, object]]) -> None:
    summary_fields = [
        "row_number", "problem_description", "current_ai_primary", "audit_status", "primary_assessment",
        "multi_label_assessment", "audit_label_1", "audit_label_2", "audit_justification",
    ]
    counts = Counter()
    queue_rows: list[dict[str, str]] = []
    with (OUT_DIR / "audit_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_fields)
        writer.writeheader()
        for row_id, row in enumerate(rows[1:], start=2):
            result = results[row_id]
            review = final_review["rows"][str(row_id)]["review"]
            matches = result["matches"]
            current = label(pair(review))
            audit_labels = [label(pair(match)) for match in matches]
            status = "two labels supported" if result["multi_label_assessment"] == "two_labels_supported" else "primary audit" 
            audit_row = {
                "row_number": str(row_id),
                "problem_description": row["A"],
                "current_ai_primary": current,
                "audit_status": status,
                "primary_assessment": result["primary_assessment"],
                "multi_label_assessment": result["multi_label_assessment"],
                "audit_label_1": audit_labels[0] if audit_labels else "",
                "audit_label_2": audit_labels[1] if len(audit_labels) > 1 else "",
                "audit_justification": result["audit_justification"],
            }
            writer.writerow(audit_row)
            counts[(result["primary_assessment"], result["multi_label_assessment"])] += 1
            if result["primary_assessment"] != "supported" or result["multi_label_assessment"] == "two_labels_supported":
                queue_rows.append(audit_row)
    full = {str(row_id): {
        "row_number": row_id,
        "problem_description": rows[row_id - 1]["A"],
        "current_ai_primary": final_review["rows"][str(row_id)]["review"],
        "audit": result,
    } for row_id, result in sorted(results.items())}
    (OUT_DIR / "audit_results.json").write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "review_queue.json").write_text(json.dumps(queue_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    analysis = {
        "scope": "431 rows from the final AI silver-label dataset",
        "provider": "azure",
        "model": MODEL,
        "audit_prompt_allows_maximum_labels": 2,
        "counts_by_primary_and_multi_label_assessment": {
            f"{primary} + {multi}": count for (primary, multi), count in sorted(counts.items())
        },
        "rows_with_two_labels_supported": sum(count for (primary, multi), count in counts.items() if multi == "two_labels_supported"),
        "rows_where_current_primary_needs_change": sum(count for (primary, multi), count in counts.items() if primary == "needs_change"),
        "rows_with_uncertain_primary_assessment": sum(count for (primary, multi), count in counts.items() if primary == "uncertain"),
        "review_queue_rows": len(queue_rows),
        "interpretation": "This is a fresh single-model audit, not independent inter-rater agreement. It reports the model's two-label assessment against the existing final AI primary label; human review remains appropriate for needs_change, uncertain, and two-label rows.",
        "files": {
            "audit_results": "audit_results.json",
            "audit_summary": "audit_summary.csv",
            "review_queue": "review_queue.json",
        },
    }
    (OUT_DIR / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=OUT_DIR / "checkpoint.json")
    parser.add_argument("--run-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--output", type=Path, default=OUT_DIR / "redaction_reviewed_v5_clean_ai_silver_two_label_audit.xlsx")
    args = parser.parse_args()
    silver.load_dotenv_if_needed(Path("../.env"))
    taxonomy, valid_pairs = silver.read_taxonomy(TAXONOMY)
    rows = silver.read_workbook_rows(INPUT_ROWS)
    final_review = json.loads(FINAL_REVIEW.read_text(encoding="utf-8"))
    results = run_audit(rows, taxonomy, valid_pairs, final_review, args.checkpoint, args.run_dir)
    write_analysis(rows, final_review, results)
    write_workbook(FINAL_AI_WORKBOOK, args.output, rows, final_review, results)
    print(f"wrote {args.output}; audited {len(results)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
