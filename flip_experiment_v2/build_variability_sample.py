#!/usr/bin/env python3
"""Build a fixed, reproducible stratified subsample of the 959-case v2
candidate set for variability studies (multiple runs per condition would
take ~2.3 hours each at 959 cases; a smaller, proportionally-stratified
sample makes several runs per condition tractable).

Stratifies by `boundary_id` so every boundary family keeps roughly its full
share of the sample (minimum 2 rows/family so no family is silently
dropped), using a fixed random seed for full reproducibility. The same
output file is meant to be reused, unmodified, across every run of every
condition in a variability study -- that way the only source of run-to-run
difference is genuine LLM sampling variance, not which cases were drawn,
and condition comparisons stay exactly paired per scenario_id.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def stratified_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_family[row["boundary_id"]].append(row)

    rng = random.Random(seed)
    families = sorted(by_family)
    total = len(rows)

    # Proportional allocation with a floor of min(2, family size), then
    # distribute remaining slots by largest fractional remainder.
    quotas: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    allocated = 0
    for fam in families:
        fam_n = len(by_family[fam])
        exact = n * fam_n / total
        base = min(fam_n, max(min(2, fam_n), int(exact)))
        quotas[fam] = base
        allocated += base
        remainders.append((exact - int(exact), fam))

    remainders.sort(reverse=True)
    i = 0
    while allocated < n and i < len(remainders):
        _, fam = remainders[i]
        if quotas[fam] < len(by_family[fam]):
            quotas[fam] += 1
            allocated += 1
        i += 1
        if i == len(remainders):
            i = 0
            if all(quotas[f] >= len(by_family[f]) for f in families):
                break

    sample: list[dict] = []
    for fam in families:
        pool = by_family[fam][:]
        rng.shuffle(pool)
        sample.extend(pool[: quotas[fam]])

    rng.shuffle(sample)
    return sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(HERE / "candidates/flip_candidates_v2.csv"))
    parser.add_argument("--out", default=str(HERE / "candidates/flip_candidates_v2_variability_sample.csv"))
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.source, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)

    sample = stratified_sample(rows, args.n, args.seed)
    sample.sort(key=lambda r: r["scenario_id"])

    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample)

    by_family = defaultdict(int)
    for row in sample:
        by_family[row["boundary_id"]] += 1
    print(f"Wrote {len(sample)} rows ({len(by_family)} families) to {args.out}")
    print(f"seed={args.seed} source_total={len(rows)}")
    for fam in sorted(by_family):
        print(f"  {fam}: {by_family[fam]}")


if __name__ == "__main__":
    main()
