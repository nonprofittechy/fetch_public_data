#!/usr/bin/env python3
"""Restore frozen match data for failed ablation re-classifications.

Early versions of the ablation runner recorded a provider-exhaustion row with
``response=None``.  That makes the generic analyzer count the row as unmatched,
even though matching was frozen from the source condition-B run.  This
finalizer restores the source response, clears only its old three-provider
final classification, and keeps the new orchestrator error.  The fsynced
partial journal remains the immutable raw execution record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--source-run", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run).resolve()
    source_dir = Path(args.source_run).resolve()
    results_path = run_dir / "results.json"
    source_path = source_dir / "results.json"
    metadata_path = run_dir / "run_metadata.json"

    doc = json.loads(results_path.read_text(encoding="utf-8"))
    source_doc = json.loads(source_path.read_text(encoding="utf-8"))
    source_by_scenario = {
        (item.get("vars") or {}).get("scenario_id"): item
        for item in source_doc.get("results", [])
    }

    restored = []
    for item in doc.get("results", []):
        if not item.get("orchestrator_error") or item.get("response"):
            continue
        scenario_id = (item.get("vars") or {}).get("scenario_id")
        source_item = source_by_scenario.get(scenario_id)
        if source_item is None:
            raise SystemExit(f"Source row not found: {scenario_id}")
        source_raw = (source_item.get("response") or {}).get("output")
        source_result = json.loads(source_raw)
        if not source_result.get("question_matched"):
            raise SystemExit(f"Failed row was not source-matched: {scenario_id}")
        source_result["final_labels"] = None
        source_result["final_top_label"] = None
        source_result["final_category_correct"] = None
        source_result["final_subcategory_correct"] = None
        source_result["error"] = item["orchestrator_error"]
        source_result["ablation_reclassification_providers"] = [
            "gpt-5",
            "gemini",
            "mistral",
            "keyword",
            "spot",
        ]
        output_json = json.dumps(source_result, ensure_ascii=False)
        item["response"] = {
            "output": output_json,
            "metadata": {"raw_json": output_json},
        }
        restored.append(scenario_id)

    results_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["post_run_finalization"] = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Restore frozen question-match data for provider-exhaustion rows "
            "while leaving their five-provider final classification unscorable"
        ),
        "restored_scenario_ids": restored,
        "source_results_sha256": sha256(source_path),
        "results_sha256_after_finalization": sha256(results_path),
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata["post_run_finalization"], indent=2))


if __name__ == "__main__":
    main()
