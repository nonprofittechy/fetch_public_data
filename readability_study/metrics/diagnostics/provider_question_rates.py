#!/usr/bin/env python3
"""Diagnostic: where do follow-up questions come from, and why are some nano
screens empty? For a sample of scenarios (or specifically the empty-nano cases),
re-run each arm capturing PER-PROVIDER question counts, the union size, whether
the semantic merge ran, and the merged screen size.

This distinguishes two explanations for an empty screen:
  (a) GENERATION: nano + gemini + mistral all emit 0 questions (union == 0), vs
  (b) MERGE COLLAPSE: union > 0 but the (nano) merge model returns an empty set.

Usage:
  python provider_question_rates.py --run-id main_20260719 --mode empty-nano
  python provider_question_rates.py --run-id main_20260719 --mode sample --n 25
Writes metrics/diagnostics/provider_rates_<mode>.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(STUDY, "harness"))
import fetch_screen as fs  # noqa: E402


async def probe(arm: str, query: str) -> dict:
    os.environ["OPENAI_SEMANTIC_MERGE_MODEL"] = fs.ARM_OPENAI_MEMBER[arm]
    svc = fs._get_service(arm)
    tax = svc.taxonomies.get("default")
    per = {}
    union = 0
    errs = {}
    for p in svc.providers:
        try:
            r = await p.classify(query, tax)
            qs = r.get("questions", []) or []
            per[p.instance_name] = len(qs)
            union += len(qs)
        except Exception as e:  # noqa: BLE001
            per[p.instance_name] = None
            errs[p.instance_name] = str(e)[:80]
    return {"arm": arm, "per_provider_q": per, "union_q": union, "errors": errs}


async def main_async(args):
    run_dir = os.path.join(STUDY, "results", "generation", args.run_id)
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "screens.jsonl"))]
    byid = {}
    for r in rows:
        byid.setdefault(r["scenario_id"], {})[r["arm"]] = r
    import csv
    scen = {r["scenario_id"]: r["problem_description"]
            for r in csv.DictReader(open(os.path.join(STUDY, "scenarios", "gold_consensus_373.csv")))}

    if args.mode == "empty-nano":
        sids = [sid for sid, d in byid.items()
                if d.get("nano") and not d["nano"].get("merged_screen")
                and not d["nano"].get("provider_failures") and not d["nano"].get("member_failed")]
        arms = ["nano"]
    else:
        rng = random.Random(1)
        sids = [sid for sid, d in byid.items() if "nano" in d and "full" in d]
        rng.shuffle(sids)
        sids = sids[: args.n]
        arms = ["nano", "full"]

    out_path = os.path.join(HERE, f"provider_rates_{args.mode}.jsonl")
    sem = asyncio.Semaphore(args.concurrency)
    results = []

    async def one(sid):
        async with sem:
            rec = {"scenario_id": sid, "query": scen.get(sid, "")[:120]}
            for arm in arms:
                rec[arm] = await probe(arm, scen[sid])
            results.append(rec)
            print(f"{sid}: " + " | ".join(
                f"{arm} per={rec[arm]['per_provider_q']} union={rec[arm]['union_q']} "
                f"final={len(byid[sid][arm].get('merged_screen',[]))}" for arm in arms))

    await asyncio.gather(*(one(s) for s in sids))
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    # summary
    def rate(arm):
        vals = [r[arm]["per_provider_q"] for r in results if arm in r]
        agg = {}
        for v in vals:
            for k, c in v.items():
                agg.setdefault(k, []).append(c)
        return {k: {"mean_q": round(sum(x for x in c if x is not None) / max(1, len([x for x in c if x is not None])), 2),
                    "pct_zero": round(sum(1 for x in c if x == 0) / len(c), 2)} for k, c in agg.items()}
    print("\n=== per-provider question rate ===")
    for arm in arms:
        print(f"{arm}: {rate(arm)}")
    print(f"\nwrote {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--mode", choices=["empty-nano", "sample"], default="empty-nano")
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--concurrency", type=int, default=3)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
