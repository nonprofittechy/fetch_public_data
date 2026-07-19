# Authoritative findings summary

**Status:** consolidated from the repository’s current findings documents and machine-readable outputs on 2026-07-17. This file is the cross-study index for paper drafting; the linked stage documents remain the detailed methods and evidence records.

## Executive synthesis

The repository supports four connected conclusions:

1. **The routing task is materially multi-label.** The source contains many descriptions with multiple independently meaningful legal issues. A single primary label is useful for routing, but it is not a complete representation of the problem.
2. **Annotation disagreement is concentrated at taxonomy boundaries.** Humans agree more than the model raters, and broad legal-domain agreement is stronger than exact specialist-route agreement. The recurring sources of disagreement are secondary issue inclusion, narrow versus fallback routes, missing party/procedural facts, and labels that describe competing framings of one dispute.
3. **FETCH usually reaches the correct legal domain and often retrieves at least one exact route, but it is incomplete on multi-label scenarios and overpredicts.** On the deduplicated consensus evaluation, pooled retrieval was 99.2% for at least one correct top-level category and 95.3% for at least one exact sublabel; all gold sublabels were retrieved in 81.4% of run-observations, while micro exact precision was 46.0%.
4. **The hidden-fact/flip study does not support a claim that follow-up questions harm classification more often than they rescue it.** The prior 307-harm interpretation was a coding error. Under the historical paper definition there were 176 rescues and 6 harms, but under the current order-independent membership criterion the expected final category was added 47 times and lost 48 times. Exact-label membership modestly favored additions, 122 versus 102. These are diagnostic paired observations, not causal estimates.

The most defensible paper framing is therefore: **multi-label legal-intake routing is feasible at the broad-domain level, but exact specialist routing and fact-sensitive disambiguation remain limited by taxonomy overlap, incomplete elicitation, answer-use failures, and output variability.**

## Evidence hierarchy and scope

The repository is a pipeline, not a collection of independent datasets:

```text
431 reviewed source rows
  └─ 373 whitespace-normalized unique descriptions
       ├─ 114 stories with two eligible human annotations + three model annotations
       └─ 373-scenario consensus-gold FETCH evaluation

Separate diagnostic benchmark:
200 legacy flip candidates + 800 workbook-grounded candidates
  └─ 1,000 candidates × 3 intended-fact runs = 3,000 observations
```

The canonical chronology and current status are maintained in [`silver_labels/REVIEW_AUDIT_TRAIL.md`](silver_labels/REVIEW_AUDIT_TRAIL.md). The cleaned source artifact is [`redaction_reviewed_v5_clean.xlsx`](redaction_reviewed_v5_clean.xlsx); the detailed 209-pair taxonomy used by the model passes is the parent-repository file [`../app/data/taxonomy_detailed_descriptions.csv`](../app/data/taxonomy_detailed_descriptions.csv).

The results below distinguish:

- **Consensus-gold evaluation:** a retrieval/coverage benchmark against a conservative derived reference set.
- **Flip benchmark:** a stress test of follow-up-question elicitation and post-answer classification, using synthetic candidate outcomes that are not yet de novo human gold.
- **Reliability analysis:** agreement among the available raters, not agreement with an external legal ground truth.

## Finding 1 — The labeling pipeline exposes a real multi-label problem

The three independent model passes used the same detailed taxonomy, prompt schema, and validation logic. Their rank-1 exact-pair agreement was:

| Relationship before internal review | Rows | Share |
|---|---:|---:|
| All three agree | 353 | 81.9% |
| Exactly two agree | 70 | 16.2% |
| All three differ | 8 | 1.9% |

The resulting Stage 04 workbook is a defensible **primary routing** artifact, not evidence that each description has only one correct label. The full row-level record is [`silver_labels/04_review/final_review.json`](silver_labels/04_review/final_review.json), with the reviewed workbook at [`silver_labels/04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx`](silver_labels/04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx).

The targeted cross-check of nine examples from the prior paper found four derived human-label corrections—rows 149, 188, 220, and 339. This was a check of named paper examples, not a full human relabeling; the original human columns remain unchanged. Stage 06 separately exposed 78 exact-pair disagreement rows, and its derived internal label is not an independent fourth rater. See [`silver_labels/05_human_label_review/README.md`](silver_labels/05_human_label_review/README.md) and [`silver_labels/06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md`](silver_labels/06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md).

Subsequent audits quantify why the one-label interpretation is insufficient:

- The broad top-three evidence audit placed **156/431 rows** in a queue where at least two distinct exact pairs were proposed by at least two independent models. This is an intentionally high-recall evidence queue, not a prevalence estimate. See [`silver_labels/07_multilabel_audit/MULTILABEL_FINDINGS.md`](silver_labels/07_multilabel_audit/MULTILABEL_FINDINGS.md) and [`silver_labels/07_multilabel_audit/multilabel_candidate_rows.csv`](silver_labels/07_multilabel_audit/multilabel_candidate_rows.csv).
- The fresh GPT-5.2 two-label audit found **90 rows** with two supported labels, **39 primary-label change candidates**, **12 uncertain primary assessments**, and a **132-row union review queue** after treating labels as an unordered set. See [`silver_labels/08_gpt52_two_label_audit/TWO_LABEL_AUDIT_FINDINGS.md`](silver_labels/08_gpt52_two_label_audit/TWO_LABEL_AUDIT_FINDINGS.md), [`silver_labels/08_gpt52_two_label_audit/audit_results.json`](silver_labels/08_gpt52_two_label_audit/audit_results.json), and [`silver_labels/09_internal_priority_review/README.md`](silver_labels/09_internal_priority_review/README.md).
- The cap-free Stage 10 workflow allows zero through four labels and preserves the underlying evidence. Seven previously identified rows needed three or four candidate issues; the workbook and adjudication artifacts are in [`silver_labels/10_four_label_human_review/`](silver_labels/10_four_label_human_review/).

The consensus reconstruction contains **238 one-label, 124 two-label, 9 three-label, and 2 four-label** unique scenarios. Its provenance is explicit: 259 sets are supported by three-model plus internal consensus, 61 by exact agreement between two human reviewers, and 53 by human decisions corroborated by at least two models. This is a conservative, provenance-preserving consensus—not a complete independent attorney adjudication of every row. See [`gold_labels_consensus_20260716/README.md`](gold_labels_consensus_20260716/README.md), [`gold_labels_consensus_20260716/build_report.json`](gold_labels_consensus_20260716/build_report.json), and the two gold files [`gold_labels_consensus_20260716/gold_labels_consensus_unique.csv`](gold_labels_consensus_20260716/gold_labels_consensus_unique.csv) and [`gold_labels_consensus_20260716/gold_labels_consensus_full_431.csv`](gold_labels_consensus_20260716/gold_labels_consensus_full_431.csv).

## Finding 2 — Agreement is better for humans and broad domains than for exact routes

The primary reliability unit is one unique problem description. Each annotation is an unordered set of exact category/subcategory pairs. On the 114 descriptions with two eligible human annotations:

| Comparison | Mean Jaccard distance | α-Jaccard | Exact set match |
|---|---:|---:|---:|
| Humans | 0.251 (95% CI 0.198–0.305) | 0.744 (0.687–0.796) | 61/114 (53.5%) |
| LLMs | 0.362 (0.320–0.404) | 0.632 (0.586–0.672) | 125/342 (36.5%) |
| Human–LLM | 0.370 (0.330–0.411) | 0.623 (0.579–0.660) | 250/684 (36.5%) |
| All five | 0.355 (0.318–0.393) | 0.638 (0.598–0.673) | 436/1,140 (38.2%) |

The intervals are story-bootstrap percentile intervals from 2,000 samples. α-Jaccard is chance-corrected Jaccard disagreement; it should be reported alongside, not substituted for, the raw distance. The expected disagreement is close to one because independently pooled sets are nearly disjoint in a 209-label taxonomy.

Supplemental ICC results tell the same story but should not be the headline nominal-set statistic: label-count ICC(A,1) was **0.328** (95% CI 0.216–0.421), conditional exact-pair incidence ICC(A,1) was **0.279**, and conditional top-level incidence ICC(A,1) was **0.390**. The all-209-label sensitivity ICC is inflated by shared zero cells and is not a valid headline agreement estimate. See [`gold_labels_consensus_20260716/FINDINGS.md`](gold_labels_consensus_20260716/FINDINGS.md), [`gold_labels_consensus_20260716/AGREEMENT_METHODS.md`](gold_labels_consensus_20260716/AGREEMENT_METHODS.md), [`gold_labels_consensus_20260716/ICC_ANALYSIS.md`](gold_labels_consensus_20260716/ICC_ANALYSIS.md), and the machine-readable [`rater_agreement_analysis.json`](gold_labels_consensus_20260716/rater_agreement_analysis.json) and [`icc_analysis.json`](gold_labels_consensus_20260716/icc_analysis.json).

The qualitative interpretation is consistent across the artifacts:

- one rater retains only the immediate requested service while another retains a secondary legal theory;
- a sparse description supports both a narrow specialist route and a general fallback;
- party role, procedural posture, agency, or requested relief is missing; or
- two labels describe competing framings of one dispute rather than separate legal matters.

Repeated review also shows nontrivial context sensitivity: 30 of 36 duplicate story/reviewer pairs received the same set (83.3%). The largest boundary problems are in General Litigation, Labor & Employment, Business & Corporate, Real Property, and Debtor/Creditor.

## Finding 3 — FETCH has high broad-domain retrieval and high any-exact retrieval, but incomplete multi-label recall and substantial overprediction

The primary evaluation uses the 373 unique consensus scenarios. Two independent replicates ran the full five-classifier FETCH vote ensemble—GPT-5.2, Gemini, Mistral, keyword, and SPOT—with Promptfoo and provider caches disabled. Run 1 began from a superseded 374-row exact-string file; the one whitespace-only alias was deterministically collapsed during scoring. Run 2 used the final 373-row file. Both produced 373 scored scenarios.

### Pooled retrieval result

| Outcome tier | Run 1 | Run 2 | Pooled run-observations |
|---|---:|---:|---:|
| All gold exact sublabels retrieved | 80.4% | 82.3% | **81.4%** |
| Some, but not all, exact sublabels retrieved | 14.5% | 13.4% | **13.9%** |
| Correct top-level only | 4.0% | 3.8% | **3.9%** |
| No correct top-level category | 1.1% | 0.5% | **0.8%** |

Across 746 run-observations:

- **95.3%** contained at least one exact gold sublabel;
- **99.2%** contained at least one correct top-level category;
- exact gold-instance precision / recall / F1 were **46.0% / 84.5% / 59.6%**;
- the mean graded retrieval score was **93.0%**;
- strict exact-set match was only **10.5%**, primarily because FETCH often returned additional plausible labels.

The rank-aware result is useful for routing: at least one exact gold sublabel appeared in the first output label in 85.7% of observations and in the first two labels in 93.3%. All gold sublabels appeared within the first two in 77.1%.

### Multi-label difficulty and stability

All-exact retrieval fell as the consensus set grew: **95.2%** for one-label scenarios, **59.7%** for two-label scenarios, **33.3%** for three-label scenarios, and **0/4** observations for the two four-label scenarios. At least one exact route was still retrieved in every four-label observation. Across the two replicates, any-exact status was stable for 96.5% of scenarios, the full four-tier outcome was stable for 94.9%, predicted sets were identical in 73.7%, and mean cross-run predicted-set Jaccard similarity was 86.3%.

The principal errors are not simply “wrong domain” errors:

- **partial multi-issue retrieval:** the dominant dispute is found while a secondary route is omitted;
- **right domain, wrong specialist route:** the system reaches the correct top-level category but misses the procedural or party-role distinction; and
- **broad overprediction:** extra plausible routes improve recall but reduce exact precision and strict set match.

Representative cases and every row-level outcome are in [`gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md`](gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md), [`gold_labels_consensus_20260716/fetch_gold_accuracy/scenario_results.csv`](gold_labels_consensus_20260716/fetch_gold_accuracy/scenario_results.csv), and [`gold_labels_consensus_20260716/fetch_gold_accuracy/metrics_by_gold_label_count.csv`](gold_labels_consensus_20260716/fetch_gold_accuracy/metrics_by_gold_label_count.csv).

### Reproduction and taxonomy caveat

The evaluation uses a narrow compatibility map for spelling, punctuation, capitalization, and live-taxonomy refinements. It does not treat top-level similarity as exact agreement. The methods and reproduction command are in [`FETCH_GOLD_ACCURACY_METHODS.md`](gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_METHODS.md); the integrated raw inputs are [`no_cache_run1_integrated.json`](gold_labels_consensus_20260716/fetch_gold_accuracy/no_cache_run1_integrated.json) and [`no_cache_run2_integrated.json`](gold_labels_consensus_20260716/fetch_gold_accuracy/no_cache_run2_integrated.json), with provider audits and repair lineage in the same directory.

The inherited 416-case PromptFoo suite is a separate follow-up-question quality baseline, not part of the primary consensus-gold accuracy estimate. After repairing 17 GPT-5.2 timeout cases, it remained **81/416 passed (19.47%)**; only 240 descriptions overlap the consensus-gold population. Its caches, timeout policy, and test suite differ from the two primary replicates. The raw/repair lineage is in [`gold_labels_consensus_20260716/fetch_full_runs/README.md`](gold_labels_consensus_20260716/fetch_full_runs/README.md).

## Finding 4 — The 1,000-candidate hidden-fact benchmark measures elicitation and answer use, not a clean causal flip

The separate benchmark combines 200 legacy candidates with 800 new workbook-grounded candidates. It is balanced 500/500 across A→B and B→A directions. It contains 770 rows grounded in reviewed multi-label examples, 488 targeting a paper-reported failure mode, and 85 with domestic violence as the intended hidden fact. The frozen candidates and design are in [`expanded_flip_experiment/README.md`](expanded_flip_experiment/README.md), [`expanded_flip_experiment/candidates/expanded_flip_candidates_1000.csv`](expanded_flip_experiment/candidates/expanded_flip_candidates_1000.csv), and [`expanded_flip_experiment/analysis/multilabel_seed_rows.csv`](expanded_flip_experiment/analysis/multilabel_seed_rows.csv).

The three official runs evaluated **only the intended hidden-fact condition**. The counterfactual fields are retained for future work but were not paid/evaluated in the official runs. All 3,000 intended-fact cases completed with zero orchestration errors under a stable, cache-disabled GPT-5 + deterministic keyword condition.

### Pooled three-run result

| Metric | Pooled result |
|---|---:|
| Expected initial category present anywhere | 90.17% |
| Expected initial exact label present, 2,670 scorable cases | 77.57% |
| Matcher-accepted hidden-fact question | **71.63%** |
| Expected final category present among matched, 2,149 cases | **84.64%** |
| Expected final exact label present among 1,892 scorable matched cases | **56.29%** |
| Expected final category newly added after the fact | 47/2,149 = 2.19% |
| Expected final exact label newly added after the fact | 122/1,892 = 6.45% |

The headline final-category percentage must not be read as a flip rate. Among matched observations, the expected final category was already present in the initial unordered set 1,772 times; it was newly added 47 times and lost 48 times. For exact labels, it was already present and retained 943 times, newly added 122 times, and lost 102 times. Thus category membership was essentially neutral (47 additions versus 48 losses), while exact membership modestly favored additions (net +20).

### Corrected comparison with *On Wednesdays*

The historical paper-style matrix, reproduced only for comparability, yields:

| Historical outcome | Current count among 2,149 matched observations |
|---|---:|
| Initial correct, final correct | 1,643 |
| Neutral failure to flip | 301 |
| Harmed/degraded | **6** |
| Rescued | **176** |
| Initially wrong and still wrong | 23 |

The earlier 307-harm interpretation counted all 301 neutral failures to flip as harm. The paper’s code required an additional serialized top-category change, which is why the corrected harm count is 6. The current study treats FETCH outputs as unordered sets, so the symmetric additions/losses above are the preferred diagnostic. See [`expanded_flip_experiment/analysis/ON_WEDNESDAYS_DIFFERENCE_AUDIT.md`](expanded_flip_experiment/analysis/ON_WEDNESDAYS_DIFFERENCE_AUDIT.md), [`expanded_flip_experiment/analysis/on_wednesdays_difference_summary.json`](expanded_flip_experiment/analysis/on_wednesdays_difference_summary.json), and [`expanded_flip_experiment/analysis/on_wednesdays_pair_comparison.csv`](expanded_flip_experiment/analysis/on_wednesdays_pair_comparison.csv).

The same 200 legacy scenarios were textually verified against the prior candidate file. Current pooled question coverage was 66.33% versus 69.0% in the paper; current final-category presence among matched observations was 77.39% versus 65.2% in the paper. This is not a controlled improvement comparison: the current official condition used GPT-5 plus keyword with caches disabled, whereas the paper used a broader five-provider ensemble with caching, and the code/taxonomy environment also changed. The comparison is therefore evidence of changed system behavior, not an attribution of improvement to the new candidates.

### Domestic-violence and hard-boundary findings

For the 85 intended hidden-DV candidates observed three times, the matcher accepted a question in **78.04%** of observations, but only **44.31%** of generated question sets explicitly probed safety, abuse, violence, threats, harm, stalking, control, or protective relief. Final expected-category presence among matched cases was 91.46%, while expected exact-label presence was only 35.18%. Broad-question matching therefore overstates deliberate safety-aware elicitation.

The carried-forward hard strata show the same separation between asking and using the answer:

| Stratum | Question coverage | Expected final category | Expected exact label |
|---|---:|---:|---:|
| Criminal vs restraining | 73.33% | 47.73% | 36.36% |
| Employment vs administrative | 13.33% | 50.00% | 0% (4 scorable matches) |
| Injury location | 70.00% | 28.57% | 28.57% |
| Bankruptcy vs collections | 41.67% | 100% | 40.00% |
| Domestic violence | 40.00% | 100% | 62.50% |

These results are diagnostic examples of failure modes, not a representative estimate for all legal intake. The detailed quote appendix is [`expanded_flip_experiment/analysis/QUOTED_EVIDENCE.md`](expanded_flip_experiment/analysis/QUOTED_EVIDENCE.md), and the concise design map is [`expanded_flip_experiment/analysis/PAPER_FAILURE_MODES.md`](expanded_flip_experiment/analysis/PAPER_FAILURE_MODES.md).

## What can safely be claimed in a paper

The evidence supports statements such as:

- “The dataset contains a substantial multi-label component, and exact-route agreement is materially weaker than broad-domain agreement.”
- “Against the conservative consensus set, FETCH retrieved at least one exact route in 95.3% of run-observations and at least one correct top-level domain in 99.2%, but complete retrieval declined sharply as the number of gold issues increased.”
- “In the hidden-fact benchmark, the matcher accepted a follow-up question in 71.63% of observations; exact final-label presence among matched, scorable observations was 56.29%.”
- “The hidden-fact results do not establish that follow-up questions cause more harm than benefit; the order-independent category-membership transition was 47 additions versus 48 losses.”
- “Safety-aware domestic-violence screening remains weaker than broad matcher-based elicitation: only 44.31% of hidden-DV question sets contained an explicit safety/abuse probe.”

The evidence does **not** support:

- treating the 373 consensus scenarios as attorney-adjudicated gold truth for every row;
- treating 95.3% any-exact retrieval as complete multi-label accuracy;
- treating 84.64% final-category presence as a binary flip success rate;
- treating the 176/6 historical matrix as a causal rescue-versus-harm estimate;
- pooling the expanded synthetic candidates with the consensus-gold accuracy benchmark; or
- claiming that the current system improvement or degradation relative to *On Wednesdays* is caused by candidate construction alone.

## Reproduction map

All commands below are intended to be run from the repository root. The raw API result directories for the flip study are locally present but gitignored; their hashes and exact paths are indexed in [`expanded_flip_experiment/analysis/RUN_TRACEABILITY.md`](expanded_flip_experiment/analysis/RUN_TRACEABILITY.md). The gold-evaluation raw and repaired JSON files are checked into the working tree but may be excluded by a default public-data ignore policy.

| Evidence | Parent document | Core artifacts | Reproduction |
|---|---|---|---|
| Silver labels and chronology | [`silver_labels/README.md`](silver_labels/README.md), [`silver_labels/REVIEW_AUDIT_TRAIL.md`](silver_labels/REVIEW_AUDIT_TRAIL.md) | [`redaction_reviewed_v5_clean.xlsx`](redaction_reviewed_v5_clean.xlsx), Stage 04 JSON/workbook, model prompts/checkpoints | `python create_silver_labels.py ...` for each model; `python build_reviewed_silver.py` |
| Multi-label evidence audit | [`MULTILABEL_FINDINGS.md`](silver_labels/07_multilabel_audit/MULTILABEL_FINDINGS.md) | [`multilabel_candidate_rows.csv`](silver_labels/07_multilabel_audit/multilabel_candidate_rows.csv), [`multilabel_analysis.json`](silver_labels/07_multilabel_audit/multilabel_analysis.json) | `python audit_multilabel_candidates.py` |
| Consensus gold construction | [`gold_labels_consensus_20260716/README.md`](gold_labels_consensus_20260716/README.md) | [`gold_labels_consensus_unique.csv`](gold_labels_consensus_20260716/gold_labels_consensus_unique.csv), [`build_report.json`](gold_labels_consensus_20260716/build_report.json) | `python build_gold_consensus.py` |
| Five-rater agreement | [`AGREEMENT_METHODS.md`](gold_labels_consensus_20260716/AGREEMENT_METHODS.md) | [`rater_sets.csv`](gold_labels_consensus_20260716/rater_sets.csv), [`comparison_summary.csv`](gold_labels_consensus_20260716/comparison_summary.csv), [`rater_agreement_analysis.json`](gold_labels_consensus_20260716/rater_agreement_analysis.json) | `python reproduce_agreement_from_rater_sets.py` for public normalized inputs; full rebuild: `python analyze_gold_rater_agreement.py` |
| Supplemental ICC | [`ICC_ANALYSIS.md`](gold_labels_consensus_20260716/ICC_ANALYSIS.md) | [`icc_analysis.json`](gold_labels_consensus_20260716/icc_analysis.json) | `python analyze_gold_rater_agreement.py` |
| FETCH consensus-gold evaluation | [`FETCH_GOLD_ACCURACY_METHODS.md`](gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_METHODS.md) | [`scenario_results.csv`](gold_labels_consensus_20260716/fetch_gold_accuracy/scenario_results.csv), [`accuracy_summary.json`](gold_labels_consensus_20260716/fetch_gold_accuracy/accuracy_summary.json), integrated runs | `pytest -q test_analyze_fetch_gold_accuracy.py` then `python analyze_fetch_gold_accuracy.py ...` |
| Expanded candidate benchmark | [`expanded_flip_experiment/README.md`](expanded_flip_experiment/README.md) | [`expanded_flip_candidates_1000.csv`](expanded_flip_experiment/candidates/expanded_flip_candidates_1000.csv), [`ARTIFACT_INDEX.md`](expanded_flip_experiment/analysis/ARTIFACT_INDEX.md) | `pytest -q expanded_flip_experiment/test_candidates.py`; official run commands are in the README |
| Expanded-run findings | [`INITIAL_TAKE.md`](expanded_flip_experiment/analysis/INITIAL_TAKE.md), [`METRIC_DEFINITIONS.md`](expanded_flip_experiment/analysis/METRIC_DEFINITIONS.md) | [`cross_run_summary.json`](expanded_flip_experiment/analysis/runs/cross_run_summary.json), [`all_scenario_details.csv`](expanded_flip_experiment/analysis/runs/all_scenario_details.csv), pooled tables | `python expanded_flip_experiment/analyze_runs.py` |
| Paper comparison and correction | [`ON_WEDNESDAYS_DIFFERENCE_AUDIT.md`](expanded_flip_experiment/analysis/ON_WEDNESDAYS_DIFFERENCE_AUDIT.md) | comparison JSON/CSV, legacy raw paths and hashes | `python expanded_flip_experiment/compare_on_wednesdays.py` |

The full verification record—including candidate tests, syntax checks, configuration validation, and official-run integrity criteria—is [`expanded_flip_experiment/analysis/VERIFICATION.md`](expanded_flip_experiment/analysis/VERIFICATION.md). The source paper PDF is not included in this publishable repository; its extracted claims and the legacy candidate/result paths are documented in the linked comparison and failure-mode records.

## Recommended paper presentation order

Use the consensus-gold evaluation as the main retrieval result, the agreement analysis as the annotation/reliability result, and the expanded flip study as a separate diagnostic experiment. Keep the following distinctions visible in the paper:

1. top-level routing versus exact subcategory routing;
2. at-least-one-label retrieval versus complete multi-label retrieval;
3. matcher coverage versus explicit fact-sensitive questioning;
4. final-label presence versus a label newly added after the hidden fact; and
5. descriptive paired transitions versus causal effects.
