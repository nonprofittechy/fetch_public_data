#!/usr/bin/env python3
"""Repair every screen touched by a provider failure, to avoid selection bias.

Excluding failed screens would bias the paired comparison: provider timeouts/
rate-limits can correlate with arm (gpt-5.2 is slower than nano) or with scenario
difficulty, so dropping them is not missing-at-random. This pass re-generates any
screen where:

  - the arm-defining OpenAI member failed (member_failed), OR
  - classify() errored, OR
  - ANY ensemble provider failed (provider_failures non-empty)

at LOW concurrency with more attempts and longer backoff, and rewrites
screens.jsonl in place. A screen that comes back empty with NO provider failures
is a genuine "no questions" outcome (kept as-is). Repeats up to --rounds passes
until no repairable screens remain.

Usage:
  python repair_failures.py --run-id main_20260719 --concurrency 2 --rounds 6
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import fetch_screen  # noqa: E402

REPAIR_ATTEMPTS = 6


def needs_repair(rec: dict) -> bool:
    return bool(rec.get("member_failed") or rec.get("error") or rec.get("provider_failures"))


def load_scenarios() -> dict:
    import csv
    path = os.path.join(STUDY, "scenarios", "gold_consensus_373.csv")
    return {r["scenario_id"]: r for r in csv.DictReader(open(path))}


async def regen(sid: str, arm: str, query: str, sem: asyncio.Semaphore, meta: dict) -> dict:
    async with sem:
        best = None
        for attempt in range(1, REPAIR_ATTEMPTS + 1):
            res = await fetch_screen._generate_screen_async(query, arm)
            res["scenario_id"] = sid
            res["gold_category_1"] = meta.get("gold_category_1", "")
            res["gold_subcategory_1"] = meta.get("gold_subcategory_1", "")
            res["attempts"] = attempt
            res["repaired"] = True
            # success = member contributed, no error, and either has questions or a
            # clean empty (no provider failures at all)
            clean = (not res.get("member_failed") and not res.get("error")
                     and not res.get("provider_failures"))
            if clean:
                return res
            best = res
            await asyncio.sleep(3.0 * attempt)  # longer backoff for rate-limit recovery
        return best


async def main_async(args):
    run_dir = os.path.join(STUDY, "results", "generation", args.run_id)
    path = os.path.join(run_dir, "screens.jsonl")
    scen = load_scenarios()

    for rnd in range(1, args.rounds + 1):
        rows = [json.loads(l) for l in open(path)]
        by_key = {(r["scenario_id"], r["arm"]): r for r in rows}
        targets = [k for k, r in by_key.items() if needs_repair(r)]
        print(f"[repair round {rnd}] {len(targets)} screens need repair")
        if not targets:
            print("[repair] nothing left to repair; clean.")
            break
        sem = asyncio.Semaphore(args.concurrency)

        async def run_one(k):
            sid, arm = k
            q = scen[sid]["problem_description"]
            new = await regen(sid, arm, q, sem, scen[sid])
            by_key[k] = new
            status = "clean" if not needs_repair(new) else "STILL-FAILED"
            print(f"  {sid} {arm}: q={len(new.get('merged_screen',[]))} {status}")

        await asyncio.gather(*(run_one(k) for k in targets))
        # rewrite file sorted by (scenario_id, arm)
        with open(path, "w") as f:
            for k in sorted(by_key):
                f.write(json.dumps(by_key[k], default=str) + "\n")

    rows = [json.loads(l) for l in open(path)]
    remaining = sum(1 for r in rows if needs_repair(r))
    print(f"[repair] done. screens={len(rows)}; still-failing={remaining}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=6)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
