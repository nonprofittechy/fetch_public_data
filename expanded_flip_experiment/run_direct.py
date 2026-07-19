#!/usr/bin/env python3
"""Run one concurrent, fully documented uncached FETCH evaluation directly.

This uses the same two-step provider as the PromptFoo study but avoids
PromptFoo's single persistent Python worker. Each completed case is appended to
JSONL immediately so an interruption still leaves analyzable evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
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
DATASET = HERE / "candidates/expanded_flip_candidates_1000.csv"
CONFIG = HERE / "promptfooconfig.no-cache.yaml"
BRIDGE = HERE / "two_step_provider_bridge.py"


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


async def main_async() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--concurrency", type=int, default=12)
    parser.add_argument("--first-n", type=int)
    parser.add_argument("--provider-timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()

    fetch_root = Path(os.environ.get("FETCH_REPO_ROOT", HERE.parents[1])).resolve()
    env_file = Path(os.environ.get("FETCH_ENV_FILE", fetch_root / ".env")).resolve()
    load_dotenv(env_file, override=False)
    os.environ["FETCH_REPO_ROOT"] = str(fetch_root)
    # Study-load concurrency needs a longer deadline than the production API's
    # latency-oriented default. Set this before importing FETCH modules.
    os.environ["CLASSIFIER_TIMEOUT_SECONDS"] = str(args.provider_timeout_seconds)
    os.environ["SEMANTIC_MERGE_TIMEOUT_SECONDS"] = str(args.provider_timeout_seconds)

    # Import only after FETCH_REPO_ROOT and credentials are available.
    from two_step_provider_bridge import call_api

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.label)
    out = RESULTS / f"{safe_label}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    partial_path = out / "results.partial.jsonl"
    final_path = out / "results.json"

    with DATASET.open(newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    if args.first_n is not None:
        cases = cases[: args.first_n]

    provider_config = {
        "condition": "intended",
        "enabled_providers": ["gpt-5", "keyword"],
        "decision_mode": "vote",
        "taxonomy_name": "default",
        "cache_enabled": False,
        "cache_dir": "../cache",
        "semantic_merge_model": "gpt-5",
        "match_model": "gpt-4.1",
    }
    command = [
        sys.executable, str(Path(__file__).resolve()), "--label", args.label,
        "--concurrency", str(args.concurrency),
        "--provider-timeout-seconds", str(args.provider_timeout_seconds),
    ]
    if args.first_n is not None:
        command.extend(["--first-n", str(args.first_n)])
    metadata = {
        "run_label": args.label,
        "orchestrator": "direct_asyncio_same_two_step_provider",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "command": command,
        "case_count": len(cases),
        "concurrency": args.concurrency,
        "provider_timeout_seconds": args.provider_timeout_seconds,
        "provider_config": provider_config,
        "cache_controls": {
            "fetch_provider_cache_enabled": False,
            "bridge_forces_cache_disabled": True,
            "promptfoo_cache": "not_applicable_direct_orchestration",
        },
        "inputs": {
            "dataset": {"path": str(DATASET), "sha256": sha256(DATASET)},
            "config_reference": {"path": str(CONFIG), "sha256": sha256(CONFIG)},
            "provider_bridge": {"path": str(BRIDGE), "sha256": sha256(BRIDGE)},
            "fetch_two_step_provider": {
                "path": str(fetch_root / "promptfoo/two_step_followup_provider.py"),
                "sha256": sha256(fetch_root / "promptfoo/two_step_followup_provider.py"),
            },
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "git_publishable_repo_head": os.popen(f"git -C {HERE.parent} rev-parse HEAD").read().strip(),
            "git_fetch_repo_head": os.popen(f"git -C {fetch_root} rev-parse HEAD").read().strip(),
            "credential_presence_only": {
                name: bool(os.environ.get(name))
                for name in ("OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")
            },
            "env_file_path": str(env_file),
        },
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (out / "command.txt").write_text(" ".join(command) + "\n")
    shutil.copy2(DATASET, out / "expanded_flip_candidates_1000.snapshot.csv")
    shutil.copy2(CONFIG, out / "promptfooconfig.reference.snapshot.yaml")
    shutil.copy2(BRIDGE, out / "two_step_provider_bridge.snapshot.py")
    console_path = out / "console.log"
    console_handle = console_path.open("a", encoding="utf-8")
    sys.stdout = Tee(sys.__stdout__, console_handle)
    sys.stderr = Tee(sys.__stderr__, console_handle)
    file_handler = logging.FileHandler(console_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(file_handler)

    semaphore = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    counters = {"completed": 0, "provider_errors": 0}
    results: list[dict] = []
    started = time.perf_counter()

    async def run_case(index: int, variables: dict) -> None:
        async with semaphore:
            case_started = time.perf_counter()
            record = {
                "index": index,
                "provider": {"label": "intended-hidden-fact", "id": "direct:two_step_provider_bridge"},
                "vars": variables,
                "response": None,
                "latencyMs": None,
                "orchestrator_error": "",
            }
            try:
                response = await call_api(
                    variables["opening_query"],
                    {"config": dict(provider_config)},
                    {"vars": dict(variables)},
                )
                record["response"] = response
            except Exception as exc:  # preserve and continue the benchmark
                record["orchestrator_error"] = f"{type(exc).__name__}: {exc}"
            record["latencyMs"] = round((time.perf_counter() - case_started) * 1000)
            async with write_lock:
                results.append(record)
                counters["completed"] += 1
                if record["orchestrator_error"]:
                    counters["provider_errors"] += 1
                with partial_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                if counters["completed"] % 25 == 0 or counters["completed"] == len(cases):
                    elapsed = time.perf_counter() - started
                    rate = counters["completed"] / elapsed * 60
                    print(
                        f"completed={counters['completed']}/{len(cases)} "
                        f"errors={counters['provider_errors']} elapsed_min={elapsed/60:.1f} "
                        f"rate_per_min={rate:.1f}",
                        flush=True,
                    )

    await asyncio.gather(*(run_case(i, row) for i, row in enumerate(cases)))
    results.sort(key=lambda row: row["index"])
    final_path.write_text(json.dumps({"schema": "direct_fetch_v1", "results": results}, ensure_ascii=False, indent=2) + "\n")

    metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["elapsed_seconds"] = round(time.perf_counter() - started, 2)
    metadata["status"] = "complete" if counters["provider_errors"] == 0 else "partial"
    metadata["result_integrity"] = {
        "total_cases": len(cases),
        "completed_cases": counters["completed"],
        "orchestrator_errors": counters["provider_errors"],
    }
    print(f"Run status: {metadata['status']}; artifacts: {out}", flush=True)
    metadata["artifacts"] = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(out.iterdir()) if path.is_file() and path.name != "run_metadata.json"
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    logging.getLogger().removeHandler(file_handler)
    file_handler.close()
    # Detach the Tee before closing its file stream so interpreter-shutdown
    # warnings cannot write to a closed console handle (run 2 exposed this).
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    console_handle.close()
    return 0 if metadata["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
