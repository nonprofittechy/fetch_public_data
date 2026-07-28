#!/usr/bin/env python3
"""Paired five-provider re-classification ablation for flip experiment v2.

This runner freezes condition B's opening classifications, generated questions,
and GPT-5 matcher decisions.  For every matched case, it repeats only the
answer-bearing classification call while explicitly enabling all five
providers: GPT-5, Gemini, Mistral, keyword, and SPOT.

The explicit ``enabled_models`` argument intentionally bypasses FETCH's normal
refinement-call filter.  The three LLM providers receive the follow-up answer;
keyword and SPOT participate in the vote but, by their provider contracts,
ignore the conversational answer.  This isolates the effect of retaining those
two non-context-aware providers from the effect of giving answers to the LLMs.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import platform
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DEFAULT_SOURCE_RUN = RESULTS / "final_run_1_20260718T203325Z"
FIVE_PROVIDERS = ["gpt-5", "gemini", "mistral", "keyword", "spot"]


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_label_present(labels: list[dict], category: str, subcategory: str) -> bool:
    expected = f"{category} > {subcategory}".strip().casefold()
    return any(str(label.get("label", "")).strip().casefold() == expected for label in labels)


def category_present(labels: list[dict], category: str) -> bool:
    expected = category.strip().casefold()
    return any(
        str(label.get("label", "")).split(" > ", 1)[0].strip().casefold() == expected
        for label in labels
    )


async def main_async() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--source-run", default=str(DEFAULT_SOURCE_RUN))
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--provider-timeout-seconds", type=float, default=120.0)
    parser.add_argument(
        "--max-provider-attempts",
        type=int,
        default=4,
        help="Retry a whole re-classification if any of the five providers fails.",
    )
    parser.add_argument(
        "--first-n-matched",
        type=int,
        help="Smoke-test mode: rerun only the first N matched cases.",
    )
    parser.add_argument(
        "--scenario-id",
        help="Repair mode: rerun only this matched scenario ID.",
    )
    args = parser.parse_args()

    source_run = Path(args.source_run).resolve()
    source_results_path = source_run / "results.json"
    source_metadata_path = source_run / "run_metadata.json"
    source_candidates_path = source_run / "flip_candidates_v2.snapshot.csv"
    for required in (source_results_path, source_metadata_path, source_candidates_path):
        if not required.exists():
            raise SystemExit(f"Required source artifact not found: {required}")

    fetch_root = Path(os.environ.get("FETCH_REPO_ROOT", HERE.parents[1])).resolve()
    env_file = Path(os.environ.get("FETCH_ENV_FILE", fetch_root / ".env")).resolve()
    load_dotenv(env_file, override=False)
    os.environ["FETCH_REPO_ROOT"] = str(fetch_root)
    os.environ["CLASSIFIER_TIMEOUT_SECONDS"] = str(args.provider_timeout_seconds)
    os.environ["SEMANTIC_MERGE_TIMEOUT_SECONDS"] = str(args.provider_timeout_seconds)
    sys.path.insert(0, str(fetch_root))

    # Import after the FETCH checkout and timeout configuration are fixed.
    from app.models.api_models import ClassificationRequest, FollowUpAnswer
    from app.services.classification_service import ClassificationService

    source_doc = json.loads(source_results_path.read_text(encoding="utf-8"))
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    source_items = source_doc.get("results", [])

    matched_items: list[tuple[int, dict, dict]] = []
    for index, item in enumerate(source_items):
        raw = (item.get("response") or {}).get("output")
        try:
            result = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            result = {}
        if result.get("question_matched") and result.get("matched_question"):
            matched_items.append((index, item, result))

    if args.first_n_matched is not None:
        matched_items = matched_items[: args.first_n_matched]
    if args.scenario_id:
        matched_items = [
            entry
            for entry in matched_items
            if (entry[1].get("vars") or {}).get("scenario_id") == args.scenario_id
        ]
        if not matched_items:
            raise SystemExit(
                f"Matched scenario not found in source run: {args.scenario_id}"
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.label)
    out = RESULTS / f"{safe_label}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    partial_path = out / "results.partial.jsonl"
    final_path = out / "results.json"

    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--label",
        args.label,
        "--source-run",
        str(source_run),
        "--concurrency",
        str(args.concurrency),
        "--provider-timeout-seconds",
        str(args.provider_timeout_seconds),
        "--max-provider-attempts",
        str(args.max_provider_attempts),
    ]
    if args.first_n_matched is not None:
        command.extend(["--first-n-matched", str(args.first_n_matched)])
    if args.scenario_id:
        command.extend(["--scenario-id", args.scenario_id])

    metadata = {
        "run_label": args.label,
        "benchmark": "flip_experiment_v2_five_provider_reclassification_ablation",
        "study_design": "paired_reclassification_only",
        "condition": (
            "Frozen condition-B initial outputs and matcher decisions; "
            "answer-bearing call explicitly votes across all five providers"
        ),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "command": command,
        "source_run": {
            "path": str(source_run),
            "run_label": source_metadata.get("run_label"),
            "git_fetch_repo_head": source_metadata.get("environment", {}).get(
                "git_fetch_repo_head"
            ),
            "results_sha256": sha256(source_results_path),
            "metadata_sha256": sha256(source_metadata_path),
            "candidates_sha256": sha256(source_candidates_path),
        },
        "case_counts": {
            "source_cases": len(source_items),
            "source_matched_cases": sum(
                1
                for item in source_items
                if json.loads((item.get("response") or {}).get("output") or "{}").get(
                    "question_matched"
                )
            ),
            "reclassifications_scheduled": len(matched_items),
        },
        "provider_config": {
            "enabled_providers": FIVE_PROVIDERS,
            "reclassification_enabled_models_explicit": FIVE_PROVIDERS,
            "decision_mode": "vote",
            "taxonomy_name": "default",
            "cache_enabled": False,
            "semantic_merge_model": "gpt-5",
            "provider_answer_behavior": {
                "gpt-5": "receives follow-up answer",
                "gemini": "receives follow-up answer",
                "mistral": "receives follow-up answer",
                "keyword": "votes but ignores follow-up answer",
                "spot": "votes but ignores follow-up answer",
            },
        },
        "cache_controls": {
            "fetch_provider_cache_enabled": False,
            "refinement_cache_bypassed_by_fetch": True,
        },
        "concurrency": args.concurrency,
        "provider_timeout_seconds": args.provider_timeout_seconds,
        "max_provider_attempts": args.max_provider_attempts,
        "inputs": {
            "runner": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256(Path(__file__).resolve()),
            },
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "git_publishable_repo_head": os.popen(
                f"git -C {HERE.parent} rev-parse HEAD"
            ).read().strip(),
            "git_fetch_repo_head": os.popen(
                f"git -C {fetch_root} rev-parse HEAD"
            ).read().strip(),
            "git_fetch_repo_branch": os.popen(
                f"git -C {fetch_root} branch --show-current"
            ).read().strip(),
            "credential_presence_only": {
                name: bool(os.environ.get(name))
                for name in ("OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")
            },
            "env_file_path": str(env_file),
        },
    }
    (out / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (out / "command.txt").write_text(" ".join(command) + "\n", encoding="utf-8")
    shutil.copy2(source_candidates_path, out / "flip_candidates_v2.snapshot.csv")
    shutil.copy2(Path(__file__).resolve(), out / Path(__file__).name)

    console_path = out / "console.log"
    console_handle = console_path.open("a", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, console_handle)
    sys.stderr = Tee(sys.__stderr__, console_handle)
    file_handler = logging.FileHandler(console_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)

    semaphore = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    completed_records: dict[int, dict] = {}
    counters = {"completed": 0, "errors": 0}
    started = time.perf_counter()

    async def rerun_case(source_index: int, source_item: dict, source_result: dict) -> None:
        async with semaphore:
            case_started = time.perf_counter()
            variables = source_item.get("vars") or {}
            record = {
                "index": source_index,
                "provider": {
                    "label": "five-provider-answer-bearing-reclassification",
                    "id": "direct:v2_five_provider_reclassification_ablation",
                },
                "vars": variables,
                "response": None,
                "latencyMs": None,
                "orchestrator_error": "",
                "source_run_index": source_item.get("index", source_index),
            }
            result = dict(source_result)
            service = None
            try:
                followup_answer = FollowUpAnswer(
                    question=result["matched_question"],
                    answer=variables.get("fact_as_answer")
                    or variables.get("hidden_fact", ""),
                )
                request = ClassificationRequest(
                    text=variables.get("opening_query", result.get("opening_query", "")),
                    taxonomy_name="default",
                    decision_mode="vote",
                    include_debug_details=True,
                    followup_answers=[followup_answer],
                    enabled_models=FIVE_PROVIDERS,
                )
                attempt_audits = []
                response = None
                provider_errors = []
                for attempt in range(1, args.max_provider_attempts + 1):
                    service = ClassificationService(
                        enabled_providers_override=FIVE_PROVIDERS,
                        cache_enabled=False,
                        cache_dir="../cache",
                    )
                    try:
                        response = await service.classify(
                            request, enabled_models=FIVE_PROVIDERS
                        )
                    finally:
                        try:
                            await service.cleanup()
                        except Exception:
                            pass
                        service = None

                    raw_provider_results = response.raw_provider_results or {}
                    provider_errors = [
                        provider_name
                        for provider_name in FIVE_PROVIDERS
                        if provider_name not in raw_provider_results
                        or (
                            isinstance(raw_provider_results.get(provider_name), dict)
                            and raw_provider_results[provider_name].get("error")
                        )
                    ]
                    attempt_audits.append(
                        {
                            "attempt": attempt,
                            "provider_errors": provider_errors,
                        }
                    )
                    if not provider_errors:
                        break
                    print(
                        f"PROVIDER_RETRY scenario={variables.get('scenario_id')} "
                        f"attempt={attempt} failed={','.join(provider_errors)}",
                        flush=True,
                    )

                if response is None or provider_errors:
                    raise RuntimeError(
                        "Provider failures remained after "
                        f"{args.max_provider_attempts} attempts: {provider_errors}"
                    )
                final_labels = [label.model_dump() for label in response.labels]
                result["final_labels"] = final_labels
                result["final_top_label"] = (
                    final_labels[0].get("label", "") if final_labels else ""
                )
                result["final_category_correct"] = category_present(
                    final_labels, variables.get("final_category", "")
                )
                result["final_subcategory_correct"] = exact_label_present(
                    final_labels,
                    variables.get("final_category", ""),
                    variables.get("final_subcategory", ""),
                )
                result["ablation_reclassification_providers"] = FIVE_PROVIDERS
                result["ablation_source_final_labels"] = source_result.get("final_labels")
                result["ablation_provider_attempts"] = attempt_audits
                result["ablation_raw_provider_results"] = response.raw_provider_results
                output_json = json.dumps(result, ensure_ascii=False, default=str)
                record["response"] = {
                    "output": output_json,
                    "metadata": {"raw_json": output_json},
                }
            except Exception as exc:
                record["orchestrator_error"] = f"{type(exc).__name__}: {exc}"
                # Preserve the frozen match decision while marking the new
                # re-classification unscorable.  Do not fall back to the
                # source run's three-provider final labels.
                failed_result = dict(source_result)
                failed_result["final_labels"] = None
                failed_result["final_top_label"] = None
                failed_result["final_category_correct"] = None
                failed_result["final_subcategory_correct"] = None
                failed_result["error"] = record["orchestrator_error"]
                failed_result["ablation_reclassification_providers"] = FIVE_PROVIDERS
                output_json = json.dumps(failed_result, ensure_ascii=False, default=str)
                record["response"] = {
                    "output": output_json,
                    "metadata": {"raw_json": output_json},
                }
            finally:
                if service is not None:
                    try:
                        await service.cleanup()
                    except Exception:
                        pass

            record["latencyMs"] = round((time.perf_counter() - case_started) * 1000)
            async with write_lock:
                completed_records[source_index] = record
                counters["completed"] += 1
                if record["orchestrator_error"]:
                    counters["errors"] += 1
                with partial_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                if counters["completed"] % 25 == 0 or counters["completed"] == len(
                    matched_items
                ):
                    elapsed = time.perf_counter() - started
                    rate = counters["completed"] / elapsed * 60 if elapsed else 0
                    print(
                        f"completed={counters['completed']}/{len(matched_items)} "
                        f"errors={counters['errors']} elapsed_min={elapsed/60:.1f} "
                        f"rate_per_min={rate:.1f}",
                        flush=True,
                    )

    await asyncio.gather(
        *(
            rerun_case(source_index, source_item, source_result)
            for source_index, source_item, source_result in matched_items
        )
    )

    final_items = []
    for source_index, source_item in enumerate(source_items):
        final_items.append(completed_records.get(source_index, source_item))
    final_path.write_text(
        json.dumps(
            {"schema": "direct_fetch_v1", "results": final_items},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    elapsed = time.perf_counter() - started
    metadata["status"] = "complete"
    metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["elapsed_seconds"] = round(elapsed, 2)
    metadata["result_integrity"] = {
        "source_cases": len(source_items),
        "reclassifications_completed": counters["completed"],
        "orchestrator_errors": counters["errors"],
        "final_records": len(final_items),
    }
    metadata["artifacts"] = {}
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name != "run_metadata.json":
            metadata["artifacts"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    (out / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"DONE out={out} reclassified={counters['completed']} "
        f"errors={counters['errors']} elapsed_min={elapsed/60:.1f}",
        flush=True,
    )
    return 0 if counters["errors"] == 0 else 2


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
