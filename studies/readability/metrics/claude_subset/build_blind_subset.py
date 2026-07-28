#!/usr/bin/env python3
"""Sample a blind paired subset for the Claude (cross-family) judge.

The Claude judge (run in-context, independent of the GPT+Gemini+Mistral
generators) scores a subset to check that the DeepSeek judge's arm effects
replicate under a different judge family. To keep the judge blind, each screen is
given an opaque id and the arm label is stripped; screens are shuffled. The
unblinding map is written separately and is NOT shown to the judge.

Output:
  claude_subset/screens_blind.jsonl   # {blind_id, opening_query, screen:[...]}
  claude_subset/unblind_map.json      # blind_id -> {scenario_id, arm}

Usage: python build_blind_subset.py --run-id main_20260719 --n-scenarios 30
"""
from __future__ import annotations

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, "..", ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--n-scenarios", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    path = os.path.join(STUDY, "results", "generation", args.run_id, "screens.jsonl")
    rows = [json.loads(l) for l in open(path)]
    by_sid = {}
    for r in rows:
        by_sid.setdefault(r["scenario_id"], {})[r["arm"]] = r

    # eligible: both arms clean AND both non-empty (need text to judge)
    eligible = [
        sid for sid, d in by_sid.items()
        if "nano" in d and "full" in d
        and not d["nano"].get("member_failed") and not d["full"].get("member_failed")
        and d["nano"].get("merged_screen") and d["full"].get("merged_screen")
    ]
    rng.shuffle(eligible)
    picked = eligible[: args.n_scenarios]

    blind = []
    unblind = {}
    counter = 0
    entries = []
    for sid in picked:
        for arm in ("nano", "full"):
            counter += 1
            bid = f"S{counter:04d}"
            rec = by_sid[sid][arm]
            entries.append((bid, sid, arm, rec))
    rng.shuffle(entries)
    for bid, sid, arm, rec in entries:
        blind.append({"blind_id": bid, "opening_query": rec["opening_query"],
                      "screen": [{"question": q.get("question"), "options": q.get("options")}
                                 for q in rec["merged_screen"]]})
        unblind[bid] = {"scenario_id": sid, "arm": arm}

    with open(os.path.join(HERE, "screens_blind.jsonl"), "w") as f:
        for b in blind:
            f.write(json.dumps(b) + "\n")
    with open(os.path.join(HERE, "unblind_map.json"), "w") as f:
        json.dump(unblind, f, indent=2)
    print(f"wrote {len(blind)} blind screens ({len(picked)} scenarios x 2 arms)")


if __name__ == "__main__":
    main()
