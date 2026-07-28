from __future__ import annotations

import unittest

from analyze_gold_rater_agreement import (
    cross_group_alpha,
    jaccard_distance,
    krippendorff_alpha,
)


class SetAgreementTest(unittest.TestCase):
    def test_jaccard_distance(self) -> None:
        self.assertEqual(jaccard_distance(frozenset(), frozenset()), 0.0)
        self.assertEqual(jaccard_distance(frozenset({"A"}), frozenset({"B"})), 1.0)
        self.assertAlmostEqual(
            jaccard_distance(frozenset({"A", "B"}), frozenset({"A", "C"})),
            2 / 3,
        )

    def test_alpha_is_one_for_perfect_within_story_agreement(self) -> None:
        units = [
            {"r1": frozenset({"A"}), "r2": frozenset({"A"})},
            {"r1": frozenset({"B"}), "r2": frozenset({"B"})},
        ]
        result = krippendorff_alpha(units, ("r1", "r2"), jaccard_distance)
        self.assertEqual(result["observed_disagreement"], 0.0)
        self.assertEqual(result["alpha"], 1.0)

    def test_cross_group_alpha_uses_separate_marginals(self) -> None:
        units = [
            {"h": frozenset({"A"}), "m": frozenset({"A"})},
            {"h": frozenset({"B"}), "m": frozenset({"B"})},
        ]
        result = cross_group_alpha(units, ("h",), ("m",), jaccard_distance)
        self.assertEqual(result["observed_disagreement"], 0.0)
        self.assertEqual(result["expected_disagreement"], 0.5)
        self.assertEqual(result["alpha"], 1.0)


if __name__ == "__main__":
    unittest.main()
