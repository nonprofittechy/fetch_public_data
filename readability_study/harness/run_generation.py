#!/usr/bin/env python3
"""Paired screen-generation runner for the nano-vs-full readability study.

For each of the 373 gold-consensus problem descriptions, generate one merged
FETCH screen per arm (nano ensemble, full ensemble). Screens where the
arm-defining OpenAI member failed/timed out, errored, or came back empty are
retried up to MAX_ATTEMPTS; the final `member_failed` flag is recorded so the
analysis can exclude contaminated screens from the paired comparison.

Output (one run directory per invocation):
  results/generation/<run_id>/screens.jsonl   # one JSON object per (scenario, arm)
  results/generation/<run_id>/meta.json       # provenance / config

The runner is resumable: re-invoking with the same --run-id skips (scenario, arm)
pairs already present in screens.jsonl.

Usage:
  python run_generation.py --run-id smoke --limit 5
  python run_generation.py --run-id main_YYYYMMDD --concurrency 4
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import fetch_screen  # noqa: E402  (sets up env, path, capture handler)

SCENARIOS = os.path.join(STUDY, "scenarios", "gold_consensus_373.csv")
RESULTS_ROOT = os.path.join(STUDY, "results", "generation")
ARMS = ["nano", "full"]
MAX_ATTEMPTS = 3


def load_scenarios(limit: int | None) -> list[dict]:
    with open(SCENARIOS, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if limit:
        rows = rows[:limit]
    return rows


def load_done(path: str) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    done.add((o["scenario_id"], o["arm"]))
                except Exception:
                    continue
    return done


async def gen_one(scenario: dict, arm: str, sem: asyncio.Semaphore) -> dict:
    sid = scenario["scenario_id"]
    query = scenario["problem_description"]
    async with sem:
        last = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            res = await fetch_screen._generate_screen_async(query, arm)
            last = res
            degraded = (
                res.get("error")
                or res.get("member_failed")
                or not res.get("merged_screen")
            )
            if not degraded:
                res["attempts"] = attempt
                res["scenario_id"] = sid
                res["gold_category_1"] = scenario.get("gold_category_1", "")
                res["gold_subcategory_1"] = scenario.get("gold_subcategory_1", "")
                return res
            await asyncio.sleep(1.5 * attempt)  # brief backoff before retry
        last["attempts"] = MAX_ATTEMPTS
        last["scenario_id"] = sid
        last["gold_category_1"] = scenario.get("gold_category_1", "")
        last["gold_subcategory_1"] = scenario.get("gold_subcategory_1", "")
        return last


async def main_async(args: argparse.Namespace) -> None:
    run_dir = os.path.join(RESULTS_ROOT, args.run_id)
    os.makedirs(run_dir, exist_ok=True)
    out_path = os.path.join(run_dir, "screens.jsonl")
    done = load_done(out_path)

    scenarios = load_scenarios(args.limit)
    tasks_spec = [
        (s, arm)
        for s in scenarios
        for arm in ARMS
        if (s["scenario_id"], arm) not in done
    ]
    print(
        f"[run {args.run_id}] {len(scenarios)} scenarios x {len(ARMS)} arms; "
        f"{len(done)} already done; {len(tasks_spec)} to generate; "
        f"concurrency={args.concurrency}"
    )

    meta = {
        "run_id": args.run_id,
        "started_utc": dt.datetime.utcnow().isoformat() + "Z",
        "scenarios_file": os.path.relpath(SCENARIOS, STUDY),
        "n_scenarios": len(scenarios),
        "arms": {
            arm: {
                "openai_member": fetch_screen.ARM_OPENAI_MEMBER[arm],
                "shared_members": fetch_screen.SHARED_MEMBERS,
                "merge_model": fetch_screen.ARM_OPENAI_MEMBER[arm],
            }
            for arm in ARMS
        },
        "classifier_timeout_s": os.environ.get("CLASSIFIER_TIMEOUT_SECONDS"),
        "semantic_merge_timeout_s": os.environ.get("SEMANTIC_MERGE_TIMEOUT_SECONDS"),
        "gpt_5_reasoning_effort": os.environ.get("GPT_5_REASONING_EFFORT"),
        "max_attempts": MAX_ATTEMPTS,
        "concurrency": args.concurrency,
    }
    with open(os.path.join(run_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    sem = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    written = 0
    total = len(tasks_spec)

    async def run_and_write(spec):
        nonlocal written
        s, arm = spec
        res = await gen_one(s, arm, sem)
        async with lock:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, default=str) + "\n")
            written += 1
            flag = "!" if (res.get("member_failed") or res.get("error") or not res.get("merged_screen")) else " "
            print(
                f"  [{written}/{total}]{flag} {res['scenario_id']} {arm} "
                f"q={len(res.get('merged_screen', []))} attempts={res.get('attempts')}"
            )

    await asyncio.gather(*(run_and_write(spec) for spec in tasks_spec))
    print(f"[run {args.run_id}] done. wrote {written} screens to {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
