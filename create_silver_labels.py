#!/usr/bin/env python3
"""Create LLM-only silver labels for the public redaction-review workbook.

The script deliberately does not invoke FETCH's keyword or SPOT classifiers.
It sends the detailed taxonomy descriptions to an Azure OpenAI-compatible model,
asks for up to three ranked category/subcategory matches per row, validates the
returned labels against the taxonomy, and adds the results to a highlighted
copy of the input workbook.

The default paths assume this script is run from this repository.  It reads
credentials from the process environment or, when absent, from ../.env.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET


NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", NS)

# The detailed file has one capitalization typo.  This is the only label
# normalization performed; descriptions and subcategory names are unchanged.
CATEGORY_ALIASES = {"General litigation": "General Litigation"}

DEFAULT_INPUT = Path("redaction_reviewed_v5_clean.xlsx")
DEFAULT_TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")
DEFAULT_OUTPUT = Path("redaction_reviewed_v5_clean_ai_silver.xlsx")
DEFAULT_CHECKPOINT = Path(".silver_classification_checkpoint.json")
DEFAULT_RUN_DIR = Path("silver_labels/01_gpt52")


def load_dotenv_if_needed(path: Path) -> None:
    """Load simple KEY=VALUE entries without overwriting exported variables."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_taxonomy(path: Path) -> tuple[list[dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw_category = (row.get("Category") or "").strip()
            subcategory = (row.get("Subcategory") or "").strip()
            description = (row.get("Enriched Description") or "").strip()
            if not raw_category or not subcategory:
                continue
            category = CATEGORY_ALIASES.get(raw_category, raw_category)
            item = {
                "category": category,
                "subcategory": subcategory,
                "description": description,
            }
            rows.append(item)

    # Keep the exact pair set used for validation.  Duplicates are not
    # expected, but preserving the first description makes behavior stable.
    pairs = {(r["category"], r["subcategory"]): r for r in rows}
    return rows, pairs


def cell_text(cell: ET.Element) -> str:
    inline = cell.find(f"{{{NS}}}is")
    if inline is not None:
        return "".join(t.text or "" for t in inline.iter(f"{{{NS}}}t"))
    value = cell.find(f"{{{NS}}}v")
    return value.text if value is not None and value.text else ""


def column_name(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def read_workbook_rows(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    result: list[dict[str, str]] = []
    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
        values: dict[str, str] = {}
        for cell in row.findall(f"{{{NS}}}c"):
            values[column_name(cell.get("r", ""))] = cell_text(cell)
        result.append(values)
    if not result or result[0].get("A") != "problem_description":
        raise ValueError("Expected problem_description header in column A")
    return result


def taxonomy_block(taxonomy: Iterable[dict[str, str]]) -> str:
    return "\n".join(
        f"{r['category']} | {r['subcategory']} | {r['description']}" for r in taxonomy
    )


def build_prompt(taxonomy_text: str, batch: list[tuple[int, str]]) -> str:
    records = "\n".join(
        f"ROW {row_id}: {description}" for row_id, description in batch
    )
    return f"""You are the final LLM classifier in a legal-help routing pipeline.

Classify each user problem below using ONLY the canonical taxonomy entries and
their detailed descriptions.  Do not use a keyword classifier, SPOT, or the
existing expected labels as a shortcut.  Reason about the user's role, the
legal issue, and the distinction between neighboring subcategories.

Return up to three possible matches for each row, in descending order of fit.
Use exact category and subcategory strings from the taxonomy.  Do not invent a
label.  Usually return one match; return two or three only when the text really
leaves a meaningful ambiguity.  Each justification must be concise (one or two
sentences), identify the facts that support the match, and explain the most
important distinction when a lower-ranked match is included.  Always provide a
best effort match, even when the description is sparse.

Return ONLY valid JSON in this shape:
{{
  "classifications": [
    {{
      "row_id": 1,
      "matches": [
        {{"category": "...", "subcategory": "...", "justification": "...", "confidence": "high|medium|low"}}
      ]
    }}
  ]
}}

CANONICAL DETAILED TAXONOMY:
{taxonomy_text}

ROWS TO CLASSIFY:
{records}
"""


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response was not a JSON object")
    return value


def azure_chat(prompt: str, model: str, max_completion_tokens: int) -> tuple[dict[str, Any], str]:
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip().rstrip("/")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not base_url or not api_key:
        raise RuntimeError("OPENAI_BASE_URL and OPENAI_API_KEY are required")
    url = base_url + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only the requested JSON object."},
            {"role": "user", "content": prompt},
        ],
        "max_completion_tokens": max_completion_tokens,
        "response_format": {"type": "json_object"},
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": api_key},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"].get("content")
    if not content:
        raise ValueError("Azure response did not contain message content")
    return extract_json(content), json.dumps(body, ensure_ascii=False, indent=2)


def gemini_chat(prompt: str, model: str, max_completion_tokens: int) -> tuple[dict[str, Any], str]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": max_completion_tokens,
        },
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    content = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
    if not content:
        raise ValueError("Gemini response did not contain text content")
    return extract_json(content), json.dumps(body, ensure_ascii=False, indent=2)


def call_model(provider: str, prompt: str, model: str, max_completion_tokens: int) -> tuple[dict[str, Any], str]:
    if provider == "gemini":
        return gemini_chat(prompt, model, max_completion_tokens)
    if provider == "azure":
        return azure_chat(prompt, model, max_completion_tokens)
    raise ValueError(f"unsupported provider: {provider}")


def normalize_matches(
    response: dict[str, Any],
    requested_ids: set[int],
    valid_pairs: dict[tuple[str, str], dict[str, str]],
) -> dict[int, list[dict[str, str]]]:
    normalized: dict[int, list[dict[str, str]]] = {}
    raw_items = response.get("classifications", [])
    if not isinstance(raw_items, list):
        raise ValueError("classifications is not a list")
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            row_id = int(item.get("row_id"))
        except (TypeError, ValueError):
            continue
        if row_id not in requested_ids:
            continue
        matches = item.get("matches", [])
        if not isinstance(matches, list):
            continue
        clean: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for match in matches[:3]:
            if not isinstance(match, dict):
                continue
            category = CATEGORY_ALIASES.get(str(match.get("category", "")).strip(), str(match.get("category", "")).strip())
            subcategory = str(match.get("subcategory", "")).strip()
            pair = (category, subcategory)
            if pair not in valid_pairs or pair in seen:
                continue
            seen.add(pair)
            justification = " ".join(str(match.get("justification", "")).split())
            confidence = str(match.get("confidence", "medium")).strip().lower()
            if confidence not in {"high", "medium", "low"}:
                confidence = "medium"
            clean.append({
                "category": category,
                "subcategory": subcategory,
                "justification": justification or "Best fit based on the facts provided.",
                "confidence": confidence,
            })
        if clean:
            normalized[row_id] = clean
    missing = requested_ids - normalized.keys()
    if missing:
        raise ValueError(f"model omitted or invalidated rows: {sorted(missing)}")
    return normalized


def load_checkpoint(path: Path) -> dict[int, list[dict[str, str]]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw.items()}


def save_checkpoint(path: Path, results: dict[int, list[dict[str, str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def write_run_metadata(
    run_dir: Path,
    provider: str,
    model: str,
    input_path: Path,
    taxonomy_path: Path,
    taxonomy: list[dict[str, str]],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    (run_dir / "responses").mkdir(exist_ok=True)
    (run_dir / "taxonomy_snapshot.csv").write_text(
        taxonomy_path.read_text(encoding="utf-8-sig"), encoding="utf-8"
    )
    (run_dir / "prompt_template.txt").write_text(
        "The rendered prompt for each batch is saved under prompts/.\n"
        "The template is build_prompt() in create_silver_labels.py.\n",
        encoding="utf-8",
    )
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = {
        "provider": provider,
        "model": model,
        "input_file": str(input_path),
        "input_sha256": sha256(input_path),
        "taxonomy_file": str(taxonomy_path),
        "taxonomy_snapshot": "taxonomy_snapshot.csv",
        "taxonomy_sha256": sha256(run_dir / "taxonomy_snapshot.csv"),
        "taxonomy_rows": len(taxonomy),
        "prompt_builder": "create_silver_labels.py:build_prompt",
        "classification_rules": {
            "keyword_classifier": False,
            "spot_classifier": False,
            "max_matches_per_row": 3,
            "label_validation": "exact category/subcategory pair from taxonomy snapshot",
        },
    }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_prompt_files(run_dir: Path, taxonomy: list[dict[str, str]], rows: list[dict[str, str]], batch_size: int) -> None:
    text = taxonomy_block(taxonomy)
    for start in range(0, len(rows) - 1, batch_size):
        batch = [(i, row["A"]) for i, row in enumerate(rows[1:], start=2)][start : start + batch_size]
        prompt = build_prompt(text, batch)
        (run_dir / "prompts" / f"batch_{start // batch_size + 1:03d}.txt").write_text(prompt, encoding="utf-8")


def classify_rows(
    rows: list[dict[str, str]],
    taxonomy: list[dict[str, str]],
    valid_pairs: dict[tuple[str, str], dict[str, str]],
    model: str,
    batch_size: int,
    checkpoint_path: Path,
    max_completion_tokens: int,
    provider: str,
    run_dir: Path,
    input_path: Path,
    taxonomy_path: Path,
) -> dict[int, list[dict[str, str]]]:
    results = load_checkpoint(checkpoint_path)
    taxonomy_text = taxonomy_block(taxonomy)
    write_run_metadata(run_dir, provider, model, input_path, taxonomy_path, taxonomy)
    write_prompt_files(run_dir, taxonomy, rows, batch_size)
    pending = [(i, row["A"]) for i, row in enumerate(rows[1:], start=2) if i not in results]
    total = len(rows) - 1
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        requested = {row_id for row_id, _ in batch}
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                prompt = build_prompt(taxonomy_text, batch)
                response, raw_response = call_model(provider, prompt, model, max_completion_tokens)
                parsed = normalize_matches(response, requested, valid_pairs)
                results.update(parsed)
                save_checkpoint(checkpoint_path, results)
                batch_number = pending.index(batch[0]) // batch_size + 1
                (run_dir / "responses" / f"batch_{batch_number:03d}.json").write_text(
                    raw_response, encoding="utf-8"
                )
                print(f"classified {len(results)}/{total} rows", flush=True)
                last_error = None
                break
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 * attempt)
        if last_error is not None:
            raise RuntimeError(f"batch starting at row {batch[0][0]} failed: {last_error}")
    return results


def set_inline_cell(row: ET.Element, col: str, row_number: int, value: str, style: str | None = None) -> None:
    cell = ET.SubElement(row, f"{{{NS}}}c", {"r": f"{col}{row_number}", "t": "inlineStr"})
    if style is not None:
        cell.set("s", style)
    inline = ET.SubElement(cell, f"{{{NS}}}is")
    text = ET.SubElement(inline, f"{{{NS}}}t")
    if value[:1].isspace() or value[-1:].isspace():
        text.set(f"{{{XML_NS}}}space", "preserve")
    text.text = value


def update_styles(styles_xml: bytes) -> bytes:
    root = ET.fromstring(styles_xml)
    fills = root.find(f"{{{NS}}}fills")
    cell_xfs = root.find(f"{{{NS}}}cellXfs")
    if fills is None or cell_xfs is None:
        raise ValueError("input workbook styles are missing fills/cellXfs")
    fill = ET.SubElement(fills, f"{{{NS}}}fill")
    pattern = ET.SubElement(fill, f"{{{NS}}}patternFill", {"patternType": "solid"})
    ET.SubElement(pattern, f"{{{NS}}}fgColor", {"rgb": "FFFFE699"})
    ET.SubElement(pattern, f"{{{NS}}}bgColor", {"indexed": "64"})
    xf = ET.SubElement(cell_xfs, f"{{{NS}}}xf", {
        "numFmtId": "0", "fontId": "0", "fillId": str(len(fills) - 1),
        "borderId": "0", "pivotButton": "0", "quotePrefix": "0", "xfId": "0",
        "applyFill": "1",
    })
    ET.SubElement(xf, f"{{{NS}}}alignment", {"vertical": "top", "wrapText": "1"})
    fills.set("count", str(len(fills)))
    cell_xfs.set("count", str(len(cell_xfs)))
    return ET.tostring(root, encoding="utf-8", xml_declaration=False)


def write_workbook(
    source: Path,
    output: Path,
    rows: list[dict[str, str]],
    results: dict[int, list[dict[str, str]]],
    model: str,
) -> None:
    headers = [
        "ai_classified",
        "ai_category_1", "ai_subcategory_1", "ai_justification_1", "ai_confidence_1",
        "ai_category_2", "ai_subcategory_2", "ai_justification_2", "ai_confidence_2",
        "ai_category_3", "ai_subcategory_3", "ai_justification_3", "ai_confidence_3",
        "ai_model",
    ]
    columns = [chr(ord("D") + i) for i in range(len(headers))]
    with ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("input workbook has no sheet data")
    for row_el in sheet_data.findall(f"{{{NS}}}row"):
        row_num = int(row_el.get("r", "0"))
        if row_num == 1:
            for col, header in zip(columns, headers):
                set_inline_cell(row_el, col, row_num, header, "1")
        elif row_num >= 2:
            matches = results.get(row_num, [])
            values = ["yes" if matches else "no"]
            for i in range(3):
                match = matches[i] if i < len(matches) else {}
                values.extend([
                    match.get("category", ""), match.get("subcategory", ""),
                    match.get("justification", ""), match.get("confidence", ""),
                ])
            values.append(model if matches else "")
            for col, value in zip(columns, values):
                set_inline_cell(row_el, col, row_num, value, "2" if matches else None)
            if matches:
                for existing in row_el.findall(f"{{{NS}}}c"):
                    if existing.get("r", "").startswith(("A", "B", "C")):
                        existing.set("s", "2")

    dimension = root.find(f"{{{NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{columns[-1]}{len(rows)}")
    cols = root.find(f"{{{NS}}}cols")
    if cols is None:
        cols = ET.Element(f"{{{NS}}}cols")
        root.insert(2, cols)
    widths = [14, 28, 34, 72, 12, 28, 34, 72, 12, 28, 34, 72, 12, 18]
    for col_num, width in enumerate(widths, start=4):
        ET.SubElement(cols, f"{{{NS}}}col", {
            "width": str(width), "customWidth": "1", "min": str(col_num), "max": str(col_num)
        })
    auto_filter = root.find(f"{{{NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{columns[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    files["xl/styles.xml"] = update_styles(files["xl/styles.xml"])
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider", choices=["azure", "gemini"], default="azure")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--max-completion-tokens", type=int, default=16000)
    args = parser.parse_args()

    load_dotenv_if_needed(Path("../.env"))
    if args.model:
        model = args.model
    elif args.provider == "gemini":
        model = "gemini-3.1-pro-preview"
    else:
        model = os.environ.get("OPENAI_GPT_5_2_MODEL", "gpt-5.2")
    taxonomy, valid_pairs = read_taxonomy(args.taxonomy)
    rows = read_workbook_rows(args.input)
    results = classify_rows(
        rows, taxonomy, valid_pairs, model, args.batch_size, args.checkpoint,
        args.max_completion_tokens, args.provider, args.run_dir, args.input, args.taxonomy,
    )
    write_workbook(args.input, args.output, rows, results, model)
    print(f"wrote {args.output} ({len(results)} AI-classified rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
