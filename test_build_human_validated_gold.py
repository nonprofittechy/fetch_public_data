from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import build_human_validated_gold as gold
import create_silver_labels as silver


class GoldBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.source = silver.read_workbook_rows(Path("redaction_reviewed_v5_clean.xlsx"))
        _, pairs = silver.read_taxonomy(Path("../app/data/taxonomy_detailed_descriptions.csv"))
        self.pairs = set(pairs)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_export(self, **updates: str) -> Path:
        path = Path(self.tempdir.name) / "gold.csv"
        fields = gold.output_fields()[:-1]
        row = {
            "row_number": "424",
            "problem_description": self.source[423]["A"],
            "original_human_category": self.source[423].get("B", ""),
            "original_human_subcategory": self.source[423].get("C", ""),
            "gold_label_count": "2",
            "gold_category_1": "Administrative Law",
            "gold_subcategory_1": "Military/Veterans",
            "gold_category_2": "Administrative Law",
            "gold_subcategory_2": "Professional Licensing",
            "reviewer_count": "2",
            "human_reviewers": "Alpha; Beta",
            "validation_basis": "multi_reviewer_consensus",
            "validated_at": "2026-07-14T16:00:00+00:00",
            **updates,
        }
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_valid_export(self) -> None:
        parsed = gold.read_gold(self.write_export(), self.pairs, self.source)
        self.assertEqual(set(parsed), {424})
        self.assertEqual(parsed[424]["reviewer_count"], "2")

    def test_rejects_problem_text_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "Problem text mismatch"):
            gold.read_gold(self.write_export(problem_description="wrong"), self.pairs, self.source)

    def test_rejects_invalid_taxonomy_pair(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid taxonomy pair"):
            gold.read_gold(self.write_export(gold_subcategory_2="Invented"), self.pairs, self.source)


if __name__ == "__main__":
    unittest.main()
