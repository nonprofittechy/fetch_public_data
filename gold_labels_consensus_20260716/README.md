# FETCH consensus gold labels — 2026-07-16

This directory contains the reproducible consensus reconstruction requested after the Stage 10 four-label human review.

## Primary datasets

- `gold_labels_consensus_full_431.csv` is the row-compatible result for all 431 source rows. `source_row` is unique, and every row has one to four labels. The 58 normalized-description alias pairs deliberately receive identical scenario IDs and identical labels.
- `gold_labels_consensus_unique.csv` is the strictly deduplicated result: 373 whitespace-normalized unique problem descriptions, with the original row aliases retained in `source_row_aliases`.

The source has 431 rows but only 373 descriptions after collapsing formatting-only whitespace. Both files are supplied because it is impossible to simultaneously retain all 431 source row identities and claim that the descriptions are deduplicated.

## Consensus rule

Consensus is computed once per exact problem description and then mapped back to every source-row alias.

1. Eligible human decisions have status `accepted` or `corrected`, a nonempty label set, and reviewer key `jackie` or `qs`.
2. When a reviewer saw the same description more than once, that reviewer's latest saved eligible decision is used. Label order is ignored.
3. If the two humans selected the same set, that set is used exactly.
4. If they disagreed, a label is retained when both humans selected it, or when one human selected it and at least two of GPT-5.2, Gemini 3.1 Pro, and DeepSeek V4 independently proposed it. If that produces no label, the best-supported human-selected label is used, with the internal Stage 04 review as a tie-breaker.
5. Mutually exclusive criminal severity routes are reduced to the strongest supported route.
6. Outside the human-review queue, the Stage 04 internally reviewed primary is retained, together with any exact pair proposed by at least two of the three independent models.
7. Labels are capped at four. No scenario reached the cap with additional candidates left over.

This is a consensus-derived benchmark, not a claim that every one of the 373 unique descriptions received de novo expert legal adjudication. The `consensus_provenance` and `support_summary_json` fields expose the evidence for each row.

## Duplicate audit

- 267 raw review records; no duplicate `(source_row, reviewer_key)` keys.
- 18 descriptions were actually reviewed under more than one source-row alias.
- Those repeats produced 36 reviewer/description repeat pairs; 30/36 (83.3%) repeated the same unordered label set.
- 114 unique descriptions have eligible decisions from both humans.
- The source contains 57 exact-description pairs plus one pair differing only in whitespace. The deduplicated file has no repeated normalized description or repeated source row.

## Analysis and reproduction

- [`FINDINGS.md`](FINDINGS.md) reports and interprets the set-based agreement results.
- [`ICC_ANALYSIS.md`](ICC_ANALYSIS.md) preserves the requested numerical ICC(A,1)/ICC(A,k) analyses for label count and conditional binary incidence, with limitations made explicit.
- [`fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md`](fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md) reports two complete uncached FETCH replicates against all 373 gold scenarios, including exact-sublabel, top-level, graded, category, and stability tables.
- [`fetch_gold_accuracy/README.md`](fetch_gold_accuracy/README.md) records raw/repair/integrated run lineage, provider audits, Azure Mistral capacity, and reproduction commands.
- [`AGREEMENT_METHODS.md`](AGREEMENT_METHODS.md) defines Jaccard distance and α-Jaccard, the four comparison groups, the story bootstrap, label-level diagnostics, and exact reproduction steps.
- `rater_agreement_analysis.json` contains the machine-readable methods, results, input hashes, and artifact manifest.
- `rater_sets.csv` is the normalized story/rater/set input to every statistic.
- `story_pairwise_set_distances.csv` contains all 1,140 within-story rater-pair observations.
- `comparison_summary.csv` and `comparison_bootstrap.csv` contain the reported comparison results and all 2,000 bootstrap draws per comparison.
- `label_level_summary.csv` and `label_level_pairwise_positive_agreement.csv` contain the exhaustive 209-label diagnostics.
- `human_disagreements.csv` contains the 53 unique stories where the human sets differed, with all five raters' labels.
- `build_report.json` records consensus-dataset counts and validation results.
- [`../build_gold_consensus.py`](../build_gold_consensus.py) builds the datasets.
- [`../analyze_gold_rater_agreement.py`](../analyze_gold_rater_agreement.py) builds the analysis artifacts.
- [`../reproduce_agreement_from_rater_sets.py`](../reproduce_agreement_from_rater_sets.py) reproduces the headline results from the public normalized annotations without private review-source files.

Run from the publishable-repo root:

```bash
python -m unittest test_build_gold_consensus.py test_build_human_validated_gold.py test_analyze_gold_rater_agreement.py
python build_gold_consensus.py
python analyze_gold_rater_agreement.py
```
