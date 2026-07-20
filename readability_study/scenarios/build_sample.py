#!/usr/bin/env python3
"""Build the paired-generation scenario sample for the nano-vs-full readability study.

We reuse the opening queries from the flip_experiment_v2 candidate corpus
(959 Claude-authored, deliberately-ambiguous boundary scenarios across 33
"boundary families"). These are an ideal fit for the study design because they
are *hard cases by construction*: each opening query withholds a fact that a
good follow-up screen would need to surface. Random sampling of easy cases
would bias toward a null result (see study plan, "Scenarios").

Sampling: stratified by boundary_id, fixed seed, >= MIN_PER_FAMILY per family,
proportional beyond that, guaranteeing safety-sensitive rows are represented.
Only the opening_query (+ metadata for stratified analysis) is carried over;
the hidden_fact / flip machinery is irrelevant to a single-screen readability
measurement and is dropped.

Output: scenarios/study_scenarios.csv  (one row per scenario, used for BOTH arms)
"""
from __future__ import annotations

import csv
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "flip_experiment_v2", "candidates", "flip_candidates_v2.csv")
OUT = os.path.join(HERE, "study_scenarios.csv")

SEED = 42
TARGET_N = 88
MIN_PER_FAMILY = 2

CARRY_FIELDS = [
    "scenario_id",
    "boundary_id",
    "opening_query",
    "initial_category",
    "initial_subcategory",
    "safety_sensitive",
]


def main() -> None:
    rng = random.Random(SEED)
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_family: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_family[r["boundary_id"]].append(r)

    families = sorted(by_family)
    selected: list[dict] = []

    # Pass 1: guarantee MIN_PER_FAMILY, preferring at least one safety-sensitive
    # row per family when available so the safety stratum is well covered.
    for fam in families:
        pool = by_family[fam][:]
        rng.shuffle(pool)
        safety = [r for r in pool if r["safety_sensitive"] == "true"]
        picks: list[dict] = []
        if safety:
            picks.append(safety[0])
        for r in pool:
            if len(picks) >= MIN_PER_FAMILY:
                break
            if r not in picks:
                picks.append(r)
        selected.extend(picks)

    # Pass 2: fill to TARGET_N proportionally from the remaining pool.
    chosen_ids = {r["scenario_id"] for r in selected}
    remaining = [r for r in rows if r["scenario_id"] not in chosen_ids]
    rng.shuffle(remaining)
    for r in remaining:
        if len(selected) >= TARGET_N:
            break
        selected.append(r)

    selected.sort(key=lambda r: (r["boundary_id"], r["scenario_id"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CARRY_FIELDS)
        w.writeheader()
        for r in selected:
            w.writerow({k: r[k] for k in CARRY_FIELDS})

    n_safety = sum(1 for r in selected if r["safety_sensitive"] == "true")
    fam_counts = defaultdict(int)
    for r in selected:
        fam_counts[r["boundary_id"]] += 1
    print(f"Wrote {len(selected)} scenarios to {OUT}")
    print(f"  families covered: {len(fam_counts)}/{len(families)}")
    print(f"  safety-sensitive: {n_safety}")
    print(f"  per-family range: {min(fam_counts.values())}..{max(fam_counts.values())}")


if __name__ == "__main__":
    main()
