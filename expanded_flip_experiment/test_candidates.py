from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent


def rows():
    with (HERE / "candidates/expanded_flip_candidates_1000.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_benchmark_shape_and_balance():
    data = rows()
    assert len(data) == 1000
    assert len({r["scenario_id"] for r in data}) == 1000
    assert Counter(r["direction"] for r in data) == {"AtoB": 500, "BtoA": 500}
    assert Counter(r["source_stratum"] for r in data) == {
        "legacy_200_snapshot": 200,
        "expanded_workbook_grounded": 800,
    }


def test_every_row_has_opposing_binary_outcomes():
    for row in rows():
        initial = (row["initial_category"], row["initial_subcategory"])
        final = (row["final_category"], row["final_subcategory"])
        counterfactual = (row["counterfactual_category"], row["counterfactual_subcategory"])
        assert final != initial
        assert counterfactual == initial
        assert row["hidden_fact"].strip()
        assert row["counterfactual_hidden_fact"].strip()


def test_priority_coverage():
    data = rows()
    assert sum(r["domestic_violence_hidden_fact"] == "true" for r in data) >= 80
    assert sum(bool(r["paper_failure_mode"]) for r in data) >= 450
    assert sum(r["multi_label_grounded"] == "true" for r in data) >= 700


def test_recorded_profile_has_no_validation_errors():
    profile = json.loads((HERE / "analysis/source_dataset_profile.json").read_text())
    assert profile["benchmark_summary"]["validation_errors"] == []

