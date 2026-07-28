# Supplemental ICC analysis of five-rater annotations

## Why ICC is supplemental

The 114 reviewed scenarios have unordered, nominal multi-label sets from GPT-5.2, Gemini 3.1 Pro, DeepSeek V4, Jackie, and QS. Intraclass correlation is designed for numerical ratings, so it cannot by itself measure whether two raters chose the same legal subcategory. The primary set-content analysis therefore uses Jaccard distance and α-Jaccard in [`FINDINGS.md`](FINDINGS.md).

ICC is still reported here because it was explicitly requested and answers two narrower numerical questions: whether raters selected a similar **number of labels**, and whether they similarly selected/not-selected a proposed exact pair or top-level category after those choices are encoded as binary ratings.

The coefficient is two-way absolute-agreement ICC(A,1) for a single rater and ICC(A,k) for the mean of the included raters. All five-rater label-count confidence intervals use 2,000 scenario bootstrap samples.

## Results

| Numerical representation | Targets | Raters | ICC(A,1) | ICC(A,k) | Interpretation |
|---|---:|---:|---:|---:|---|
| Label count, all five raters | 114 | 5 | 0.328 (95% CI 0.216–0.421) | 0.709 (0.579–0.784) | Individual raters differed substantially in how many issues they retained; averaging five raters was materially more stable. |
| Label count, humans only | 114 | 2 | 0.304 | 0.466 | The two humans used different inclusion/scope thresholds even when they shared a core route. |
| Label count, LLMs only | 114 | 3 | 0.321 | 0.587 | The three models also differed in label volume; DeepSeek was the most conservative. |
| Conditional exact-pair incidence, all five | 340 proposed scenario/pair targets | 5 | 0.279 | 0.660 | Agreement was weakest at the exact subcategory level. |
| Conditional top-level incidence, all five | 193 proposed scenario/category targets | 5 | 0.390 | 0.761 | Broad legal-domain agreement was higher than exact-pair agreement. |
| All 209-pair incidence sensitivity analysis | 23,826 scenario/pair cells | 5 | 0.743 | 0.935 | This value is inflated by shared zeros and is not a headline reliability result. |

The exact-pair and top-level analyses are *conditional*: a target exists only when at least one of the five raters proposed that pair/category for that scenario. This avoids allowing the 209-label taxonomy's many unanimous non-selections to dominate reliability. The all-pair sensitivity analysis demonstrates that problem directly: almost every scenario/label cell is zero for every rater, producing an apparently high ICC that does not mean exact labels agree well.

## Interpretation alongside set agreement

The ICC pattern and the nominal-set analysis tell a consistent story. Top-level category selection is more reliable than exact specialist-route selection, and aggregation is more stable than relying on one rater. However, ICC should not be interpreted as a replacement for direct set agreement: the two humans had an exact unordered-set match on 61/114 scenarios (53.5%), and many remaining disagreements were one-label additions/omissions rather than wholly different readings.

The main ambiguity mechanisms were:

- whether to retain only the dominant requested service or also secondary legal issues;
- a narrow specialist route versus a broad fallback route;
- missing facts about party side, procedural posture, agency, or requested relief;
- multiple taxonomy labels describing different aspects of one dispute rather than independent matters.

Detailed examples and the full qualitative analysis are in [`FINDINGS.md`](FINDINGS.md) and [`human_disagreements.csv`](human_disagreements.csv). Machine-readable ICC inputs/results are preserved in [`icc_analysis.json`](icc_analysis.json).
