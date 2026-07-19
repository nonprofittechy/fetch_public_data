#!/usr/bin/env python3
"""Unblind the Claude judgments and compare (a) nano vs full under Claude, and
(b) Claude vs DeepSeek on the same subset (do the arm effects and absolute rates
agree across judge families?)."""
from __future__ import annotations

import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, "..", ".."))


def load_jsonl(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def main():
    unblind = json.load(open(os.path.join(HERE, "unblind_map.json")))
    claude = {j["blind_id"]: j for j in load_jsonl(os.path.join(HERE, "claude_judgments.jsonl"))}
    ds = {(r["scenario_id"], r["arm"]): r for r in
          load_jsonl(os.path.join(STUDY, "results", "generation", "main_20260719",
                                  "metrics_llm_deepseek-v4.jsonl"))}

    # Claude arm aggregates
    arm_vals = defaultdict(lambda: defaultdict(list))
    pairs = []
    for bid, info in unblind.items():
        sid, arm = info["scenario_id"], info["arm"]
        cj = claude.get(bid)
        if not cj:
            continue
        arm_vals[arm]["m1"].append(cj["m1_screen_max"])
        arm_vals[arm]["m2"].append(cj["m2_screen_flag"])
        arm_vals[arm]["m3_unclear_rate"].append(cj["m3_unclear_rate"])
        arm_vals[arm]["m3_answerable_rate"].append(cj["m3_answerable_rate"])
        pairs.append((sid, arm, bid, cj))

    def mean(x):
        return round(sum(x) / len(x), 3) if x else None

    print("=== Claude (in-context) judge, blind subset ===")
    for arm in ("nano", "full"):
        v = arm_vals[arm]
        print(f"  {arm}: n={len(v['m1'])} m1_presup_mean={mean(v['m1'])} "
              f"m2_double_rate={mean(v['m2'])} m3_unclear_rate={mean(v['m3_unclear_rate'])} "
              f"m3_answerable_rate={mean(v['m3_answerable_rate'])}")

    # Claude vs DeepSeek on the same (sid, arm) screens
    print("\n=== Claude vs DeepSeek on the SAME subset screens ===")
    c_m1, d_m1, c_m2, d_m2 = [], [], [], []
    for bid, info in unblind.items():
        sid, arm = info["scenario_id"], info["arm"]
        cj = claude.get(bid)
        dr = ds.get((sid, arm))
        if not cj or not dr or dr.get("status") != "ok":
            continue
        c_m1.append(cj["m1_screen_max"])
        d_m1.append(dr["m1_presupposition"]["screen_max"])
        c_m2.append(cj["m2_screen_flag"])
        d_m2.append(dr["m2_double_barrel"]["screen_flag"])
    print(f"  matched screens: {len(c_m1)}")
    print(f"  m1 presup (mean screen_max): Claude={round(sum(c_m1)/len(c_m1),3)}  "
          f"DeepSeek={round(sum(d_m1)/len(d_m1),3)}")
    print(f"  m2 double-barrel (flag rate): Claude={round(sum(c_m2)/len(c_m2),3)}  "
          f"DeepSeek={round(sum(d_m2)/len(d_m2),3)}")
    agree_m2 = sum(1 for a, b in zip(c_m2, d_m2) if a == b) / len(c_m2)
    print(f"  m2 flag agreement rate: {round(agree_m2,3)}")


if __name__ == "__main__":
    main()
