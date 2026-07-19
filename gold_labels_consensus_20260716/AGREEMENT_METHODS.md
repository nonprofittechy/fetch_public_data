# Reproducing the multi-label agreement analysis

## Statistical unit and scope

The independent sampling unit is one unique problem description (“story”). The analysis is restricted to the 114 stories for which both humans supplied an eligible annotation, so every comparison uses the same stories. Each of the five rater annotations for story `i` is represented as an unordered set `S_ir` of exact taxonomy pairs.

Duplicate source rows with identical problem descriptions are collapsed before analysis. If a human reviewed more than one source-row alias, the latest eligible saved decision is used. The normalized inputs used by the statistics are written to [`rater_sets.csv`](rater_sets.csv).

## Jaccard distance

For two annotation sets `A` and `B`:

```text
d_J(A, B) = 1 - |A ∩ B| / |A ∪ B|
```

The implementation defines the distance between two empty sets as 0, although none of the analyzed annotations is empty. Interpretation:

- `0`: identical sets;
- `1`: completely disjoint sets;
- between `0` and `1`: partial disagreement.

This measure does not reward agreement on taxonomy labels that neither rater selected. [`story_pairwise_set_distances.csv`](story_pairwise_set_distances.csv) contains the ten distances, exact-match indicators, and absolute label-count differences for every story.

MASI is a reasonable sensitivity measure when subset/superset disagreements should receive special credit. It is not used here because no annotation rule says that `{A, B}` versus `{A, B, C}` should be privileged over other overlaps with the same Jaccard distance. Ordinary Jaccard is consequently the simpler primary measure.

## α-Jaccard

Krippendorff's framework is evaluated with Jaccard distance as the disagreement function:

```text
alpha_J = 1 - D_o / D_e
```

`D_o` is the mean within-story Jaccard distance over the rater pairs in the comparison. `D_e` is the mean Jaccard distance between two distinct annotations drawn from the relevant pooled rater annotations, ignoring story membership. Alpha is undefined if `D_e = 0`.

For humans, LLMs, and all five raters, annotations within a group are treated as interchangeable for the standard pooled expected-disagreement calculation. For the human–LLM comparison, `D_o` averages the six within-story cross-type pairs and `D_e` averages all combinations of one pooled human annotation and one pooled LLM annotation. The resulting coefficient has the same chance-correction form, but it is explicitly reported as a **cross-group α-Jaccard analogue** because humans and LLMs are not interchangeable samples from one rater population.

The four comparison definitions are:

| Comparison | Rater pairs per story |
|---|---:|
| Humans | 1 |
| LLMs | 3 |
| Human–LLM | 6 |
| All five | 10 |

The all-five observed disagreement is weighted by those ten pairs; human–LLM pairs therefore account for 60% of it.

## Bootstrap intervals

The script creates 2,000 bootstrap samples with seed `20260716`. Each sample draws 114 stories with replacement and retains all ratings and pairs belonging to each sampled story. The 95% interval is the 2.5th to 97.5th percentile with linear interpolation. [`comparison_bootstrap.csv`](comparison_bootstrap.csv) preserves every bootstrap draw, and [`comparison_summary.csv`](comparison_summary.csv) contains the point estimates and intervals.

This bootstrap quantifies uncertainty over stories. With only two humans and three LLM systems, it does not quantify uncertainty over a wider population of possible human raters, prompts, models, or model runs.

## Label-level diagnostics

For each of the 209 taxonomy pairs, selected/not-selected is constructed separately for every story and rater:

- [`label_level_summary.csv`](label_level_summary.csv) reports selection counts and prevalence for all five raters and nominal five-rater Krippendorff alpha where expected disagreement is nonzero.
- [`label_level_pairwise_positive_agreement.csv`](label_level_pairwise_positive_agreement.csv) reports positive Jaccard and Dice/F1 for every label and all ten rater pairs. These compare the sets of stories on which each rater selected the label and do not reward joint non-selection.

Blank label-level alpha means that all 570 binary ratings have the same value. Blank positive Jaccard or Dice/F1 means neither member of that rater pair ever selected the label. Rare-label results should be interpreted descriptively.

## Files and exact reproduction

[`rater_agreement_analysis.json`](rater_agreement_analysis.json) is the machine-readable report. It records the method, scope, input SHA-256 hashes, rater summaries, point estimates, confidence intervals, bootstrap seed, and iteration count. [`human_disagreements.csv`](human_disagreements.csv) is a focused qualitative extract, not an additional statistical input.

From the repository root, run:

```bash
python -m unittest test_analyze_gold_rater_agreement.py
python analyze_gold_rater_agreement.py
```

The analysis uses only the Python standard library plus the repository's existing workbook reader. It reads the source workbook, taxonomy CSV, human-review export, and three model checkpoint files whose hashes are recorded in the JSON report. Re-running the script deterministically overwrites all analysis CSVs and the JSON report.

The human-review export is private source material. To reproduce the headline table without it or the external taxonomy file, use the checked-in normalized annotations:

```bash
python reproduce_agreement_from_rater_sets.py
```

That independent entry point reads only `rater_sets.csv` and recomputes all four point estimates and bootstrap intervals. A quick structural check can use `--bootstrap-iterations 10`; the published confidence intervals require the default 2,000 iterations.
