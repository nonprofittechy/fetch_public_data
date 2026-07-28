from __future__ import annotations

import csv

from build_paper_d1 import DEFAULT_INPUT, DEFAULT_OUTPUT, find_repeats


def test_paper_d1_deduplication_counts() -> None:
    with DEFAULT_INPUT.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    dropped, pairs = find_repeats(rows)

    assert len(rows) == 373
    assert len(dropped) == 18
    assert len(pairs) == 18
    assert len(rows) - len(dropped) == 355

    with DEFAULT_OUTPUT.open(encoding="utf-8-sig", newline="") as stream:
        paper_rows = list(csv.DictReader(stream))
    assert [row["scenario_id"] for row in paper_rows] == [
        row["scenario_id"] for row in rows if row["scenario_id"] not in dropped
    ]
