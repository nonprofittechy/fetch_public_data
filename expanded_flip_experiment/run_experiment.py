#!/usr/bin/env python3
"""Run one documented, uncached paid evaluation and preserve its artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
CONFIG = HERE / "promptfooconfig.no-cache.yaml"
DATASET = HERE / "candidates/expanded_flip_candidates_1000.csv"
BRIDGE = HERE / "two_step_provider_bridge.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return (result.stdout + result.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--first-n", type=int)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--max-concurrency", type=int, default=2)
    parser.add_argument("--provider-filter")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.label)
    out = RESULTS / f"{safe_label}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    fetch_root = Path(os.environ.get("FETCH_REPO_ROOT", HERE.parents[1])).resolve()
    env_file = Path(os.environ.get("FETCH_ENV_FILE", fetch_root / ".env")).resolve()
    output_json = out / "results.json"
    command = [
        "promptfoo", "eval", "--config", str(CONFIG), "--no-cache", "--no-share",
        "--repeat", str(args.repeat), "--output", str(output_json),
        "--max-concurrency", str(args.max_concurrency),
        "--description", f"expanded flip benchmark: {args.label}",
    ]
    if env_file.exists():
        command.extend(["--env-file", str(env_file)])
    if args.first_n is not None:
        command.extend(["--filter-first-n", str(args.first_n)])
    if args.provider_filter:
        command.extend(["--filter-providers", args.provider_filter])

    file_values = dotenv_values(env_file) if env_file.exists() else {}
    metadata = {
        "run_label": args.label,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "command": command,
        "cwd": str(HERE),
        "first_n": args.first_n,
        "repeat": args.repeat,
        "max_concurrency": args.max_concurrency,
        "provider_filter": args.provider_filter,
        "cache_controls": {
            "promptfoo_cli_no_cache": True,
            "fetch_provider_cache_enabled": False,
            "bridge_forces_cache_disabled": True,
        },
        "inputs": {
            "config": {"path": str(CONFIG), "sha256": sha256(CONFIG)},
            "dataset": {"path": str(DATASET), "sha256": sha256(DATASET)},
            "provider_bridge": {"path": str(BRIDGE), "sha256": sha256(BRIDGE)},
            "fetch_two_step_provider": {
                "path": str(fetch_root / "promptfoo/two_step_followup_provider.py"),
                "sha256": sha256(fetch_root / "promptfoo/two_step_followup_provider.py"),
            },
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "promptfoo_version": capture(["promptfoo", "--version"]),
            "git_publishable_repo_head": capture(["git", "rev-parse", "HEAD"], HERE),
            "git_fetch_repo_head": capture(["git", "rev-parse", "HEAD"], fetch_root),
            "credential_presence_only": {
                name: bool(os.environ.get(name) or file_values.get(name))
                for name in ("OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")
            },
            "env_file_path": str(env_file),
        },
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    shutil.copy2(CONFIG, out / "promptfooconfig.snapshot.yaml")
    shutil.copy2(BRIDGE, out / "two_step_provider_bridge.snapshot.py")
    shutil.copy2(DATASET, out / "expanded_flip_candidates_1000.snapshot.csv")
    (out / "command.txt").write_text(" ".join(command) + "\n")

    log_path = out / "console.log"
    print(f"Artifacts: {out}", flush=True)
    print("Command: " + " ".join(command), flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=HERE,
            env={**os.environ, "FETCH_REPO_ROOT": str(fetch_root)},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
            log.flush()
        return_code = process.wait()

    metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["return_code"] = return_code
    usable_cases = provider_errors = total_cases = 0
    if output_json.exists():
        try:
            result_doc = json.loads(output_json.read_text())
            result_rows = result_doc.get("results", {}).get("results", [])
            total_cases = len(result_rows)
            for row in result_rows:
                output = (row.get("response") or {}).get("output")
                if output:
                    try:
                        parsed = json.loads(output) if isinstance(output, str) else output
                        if isinstance(parsed, dict) and not parsed.get("error"):
                            usable_cases += 1
                            continue
                    except (TypeError, json.JSONDecodeError):
                        pass
                provider_errors += 1
        except (OSError, json.JSONDecodeError):
            provider_errors = 1
    metadata["result_integrity"] = {
        "total_cases": total_cases,
        "usable_provider_results": usable_cases,
        "provider_errors": provider_errors,
    }
    if total_cases and provider_errors == 0:
        metadata["status"] = "complete"
    elif usable_cases:
        metadata["status"] = "partial"
    else:
        metadata["status"] = "failed"
    metadata["artifacts"] = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(out.iterdir()) if path.is_file() and path.name != "run_metadata.json"
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Run status: {metadata['status']}; artifacts: {out}", flush=True)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
