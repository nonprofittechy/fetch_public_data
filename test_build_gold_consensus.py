from __future__ import annotations

import unittest

from build_gold_consensus import HumanDecision, normalize_description, select_consensus


class ConsensusRuleTest(unittest.TestCase):
    def test_description_normalization_collapses_formatting_whitespace(self) -> None:
        self.assertEqual(
            normalize_description("  the same\n scenario\ttext  "),
            "the same scenario text",
        )

    def test_exact_human_consensus_controls_reviewed_scenario(self) -> None:
        a = ("A", "one")
        b = ("B", "two")
        humans = {
            "jackie": HumanDecision("jackie", 2, frozenset({a}), "accepted", "2026-07-16T00:00:00+00:00"),
            "qs": HumanDecision("qs", 2, frozenset({a}), "accepted", "2026-07-16T00:00:01+00:00"),
        }
        labels, provenance, _ = select_consensus(
            {"m1": [b], "m2": [b], "m3": [b]}, b, humans
        )
        self.assertEqual(labels, [a])
        self.assertEqual(provenance, "two_human_exact_consensus")

    def test_one_human_label_requires_model_corroboration(self) -> None:
        a = ("A", "one")
        b = ("B", "two")
        c = ("C", "three")
        humans = {
            "jackie": HumanDecision("jackie", 2, frozenset({a, c}), "accepted", "2026-07-16T00:00:00+00:00"),
            "qs": HumanDecision("qs", 2, frozenset({b}), "accepted", "2026-07-16T00:00:01+00:00"),
        }
        labels, _, _ = select_consensus(
            {"m1": [a, b], "m2": [a, b], "m3": [b]}, b, humans
        )
        self.assertEqual(set(labels), {a, b})
        self.assertNotIn(c, labels)

    def test_unreviewed_uses_model_majority_and_internal_primary(self) -> None:
        a = ("A", "one")
        b = ("B", "two")
        c = ("C", "three")
        labels, provenance, _ = select_consensus(
            {"m1": [a, b], "m2": [a], "m3": [c]}, c, {}
        )
        self.assertEqual(set(labels), {a, c})
        self.assertEqual(provenance, "three_model_plus_internal_consensus")


if __name__ == "__main__":
    unittest.main()
