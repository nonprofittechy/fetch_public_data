"""Structural checks for the v2 disclosure-flip candidate benchmark."""

import csv
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_rows():
    with (HERE / "candidates/flip_candidates_v2.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_builder_validates_cleanly():
    proc = subprocess.run(
        [sys.executable, str(HERE / "build_candidates.py")],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_row_count_and_uniqueness():
    rows = load_rows()
    assert 900 <= len(rows) <= 1100
    ids = [r["scenario_id"] for r in rows]
    assert len(ids) == len(set(ids))
    queries = [r["opening_query"].lower() for r in rows]
    assert len(queries) == len(set(queries))


def test_no_placeholders_and_real_flips():
    rows = load_rows()
    for row in rows:
        joined = " ".join(row.values())
        assert "PLACEHOLDER" not in joined, row["scenario_id"]
        assert "_HOLD" not in row["final_subcategory"], row["scenario_id"]
        assert "_KEEP" not in row["final_subcategory"], row["scenario_id"]
        initial = f"{row['initial_category']} > {row['initial_subcategory']}"
        final = f"{row['final_category']} > {row['final_subcategory']}"
        assert initial != final, row["scenario_id"]
        cf = f"{row['counterfactual_category']} > {row['counterfactual_subcategory']}"
        assert cf != final, row["scenario_id"]


def test_generator_provenance_recorded():
    rows = load_rows()
    assert all("claude-fable-5" in r["generator_model"] for r in rows)
