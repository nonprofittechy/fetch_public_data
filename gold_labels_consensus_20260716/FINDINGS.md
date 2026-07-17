# Five-rater multi-label agreement findings

## Scope and interpretation

The analysis uses the 114 unique problem descriptions with eligible annotations from both human reviewers. Exact duplicate descriptions count once. The five raters are GPT-5.2, Gemini 3.1 Pro, DeepSeek V4, Jackie, and QS. Each annotation is treated as an unordered set of exact `(category, subcategory)` pairs.

The primary descriptive statistic is **Jaccard distance**, where 0 means identical sets and 1 means disjoint sets. The chance-corrected statistic is **Krippendorff's alpha using Jaccard distance**, written here as **α-Jaccard**. Intraclass correlation is not reported: it is a numerical-rating statistic and does not directly measure agreement between nominal multi-label sets. See [`AGREEMENT_METHODS.md`](AGREEMENT_METHODS.md) for formulas, bootstrap details, and artifact-level reproduction.

## Quantitative results

| Comparison | Pairs/story | Mean Jaccard distance (95% CI) | α-Jaccard (95% CI) | Exact set match | Mean absolute label-count difference | Mean labels/rating |
|---|---:|---:|---:|---:|---:|---:|
| Humans | 1 | 0.251 (0.198–0.305) | 0.744 (0.687–0.796) | 61/114 (53.5%) | 0.465 | 1.899 |
| LLMs | 3 | 0.362 (0.320–0.404) | 0.632 (0.586–0.672) | 125/342 (36.5%) | 0.544 | 1.962 |
| Human–LLM | 6 | 0.370 (0.330–0.411) | 0.623 (0.579–0.660) | 250/684 (36.5%) | 0.499 | 1.899 human; 1.962 LLM |
| All five | 10 | 0.355 (0.318–0.393) | 0.638 (0.598–0.673) | 436/1,140 (38.2%) | 0.509 | 1.937 |

All confidence intervals are percentile intervals from 2,000 bootstrap samples of the 114 stories. Rater pairs within a resampled story stay together. The human–LLM coefficient uses the same `1 - Do/De` construction but draws expected disagreement from separate pooled human and LLM marginals; it is therefore a cross-group analogue of α-Jaccard, not a standard interchangeable-rater alpha.

The human annotations disagreed less than the LLM annotations or the cross-type pairs. The all-five mean is not a neutral midpoint: 6 of its 10 rater pairs per story are human–LLM, so cross-type disagreement has the largest weight. Label volume also differed by rater: GPT-5.2 selected 2.22 labels/story, Gemini 2.11, DeepSeek 1.55, Jackie 1.82, and QS 1.97.

The expected Jaccard disagreements used by alpha are close to one (0.982 humans, 0.982 LLMs, and 0.981 all five) because independently pooled full label sets are almost always disjoint in a 209-label taxonomy. That explains why α-Jaccard is numerically much higher than `1 - mean Jaccard distance`; both values should be reported together.

## Label-level analysis

The exhaustive label table covers all 209 taxonomy pairs. At least one rater selected 129 labels in this 114-story subset; the remaining 80 labels were never selected, so their nominal per-label alpha is undefined rather than zero. For every label, the artifacts report each rater's selection count and prevalence, nominal five-rater alpha where estimable, and all ten rater-pair positive Jaccard and Dice/F1 scores.

These label-level statistics are diagnostic, especially for rare labels. A perfect alpha for a label selected on only one story does not establish broadly reliable performance. The analysis does not use flattened story-by-label binary accuracy as a headline measure, because the large number of shared non-selections would dominate it.

Repeated review was itself informative. Of 36 reviewer/description repeat pairs created by duplicate source descriptions, 30 (83.3%) produced the same set. The six changes were concentrated in multi-issue boundary cases such as contractor payment/liens, workplace injury versus third-party injury, domestic violence as context versus requested relief, and commercial versus residential property routing.

## Why raters disagreed

Four recurring ambiguity mechanisms explain most differences:

1. **Core problem versus every independently visible issue.** One rater often chose the immediate requested service, while another also retained secondary legal theories. This is visible in police misconduct (Tort Claims Act versus also Actions Against Police/Civil Rights), disability leave (insurance denial versus FMLA/employment), and contractor cases (construction route versus small claims/property damage).
2. **Specific route versus general fallback.** Raters differed over whether sparse facts satisfied a narrow taxonomy description. Examples include Business Litigation versus a general contracts label, Animal Law versus Personal Injury, and legal malpractice versus General Litigation.
3. **Procedural posture and party role were missing.** “Foreclosure on a business,” a debt suit, eviction, and bankruptcy involving an ex-spouse can route differently depending on whether the caller is creditor/debtor, buyer/seller, landlord/tenant, or filer/non-filing spouse. Several descriptions did not settle those roles cleanly.
4. **Multiple labels represented competing framings, not separate issues.** Misdemeanor versus lesser felony, disability insurance versus ERISA benefits, and residential versus commercial property sometimes described the same dispute through different taxonomy branches. The gold rule is conservative here and expressly removes competing criminal-severity labels.

The symmetric differences were concentrated in General Litigation (22 label appearances), followed by Labor & Employment (9), Business & Corporate (7), Real Property (7), and Debtor/Creditor (6). General Litigation's broad and overlapping subcategories make it the clearest taxonomy boundary problem.

## Illustrative disagreements

### Row 128 — business-sale security “foreclosure”

One human selected Bankruptcy/Business, general business contracts, and creditor; the other selected Business & Corporate/Litigation. The model votes split among Real Property/Foreclosure, creditor, Business Litigation, and Sale of Business. “Foreclosure” sounds like real property, but the collateral is security from a business sale, and no bankruptcy filing is actually described. The ambiguity comes from using a procedural word across property, secured-credit, and business-litigation taxonomies. The conservative consensus is **Business & Corporate > Litigation**.

### Row 196 — stated misdemeanors but serious alleged conduct

One human chose `Lessor Felony`; the other chose Misdemeanor. The description expressly says “four misdemeanors,” but also mentions assault and strangulation, which can sound felony-level. Four of five raters selected Misdemeanor and three selected the lesser-felony route. Because these are mutually exclusive severity classifications of the same prosecution, not separate issues, the consensus keeps only **Criminal Law > Misdemeanor**.

### Row 332 — termination, disability, and reporting negligence

One human chose Wrongful Discharge; the other chose ADA, Discrimination, and Whistleblowers. The user says they were fired after reporting coworker negligence and that the supervisor knew about dyslexia. Those facts support retaliation/whistleblowing and disability theories, while “wrongfully terminated” also names the consequence. The ambiguity is whether the taxonomy should encode the adverse action, the suspected unlawful motive, or both. Cross-rater support retained **Whistleblowers** and **ADA**.

### Row 213 — disability overpayment sent to collections

Both humans agreed on Debtor/Creditor/General (Debtor), but split among private disability insurance, consumer insurance, and ERISA benefits for the underlying policy. The description does not establish whether the plan is employer-sponsored, individually purchased, or governed by ERISA. Those labels are alternative institutional routes for the same overpayment dispute. The only high-confidence shared result is **Debtor/Creditor > General (Debtor)**.

### Row 252 — divorce plus military, immigration, and lease facts

Both humans retained Divorce. One added Military family law; the other added residential tenancy. The models strongly supported the military label and only GPT-5.2 proposed immigration; none proposed tenancy in the original three passes. The user clearly requests divorce and removal from a lease, while military service and conditional immigration status may be legally important context rather than separate requested services. This is a genuine “issue versus context” boundary. The conservative five-rater rule retains **Divorce** and **Military**; the lease and immigration possibilities remain visible in the raw disagreement evidence.

### Rows 421 and 424 — true four-issue scenarios

These show why four slots were necessary. Both humans exactly agreed on four distinct labels for each: row 421 combines guardianship, beneficiary litigation, personal injury, and a local-ordinance/parking matter; row 424 combines veterans benefits, professional licensing, neighbor nuisance, and will drafting. These are not alternative framings of one event, so reducing them to a primary label would destroy material information.

## Bottom line

The review supports multi-label gold data, but it also shows that a label-count ceiling is only part of the problem. Exact routing depends on an explicit policy for secondary issues, contextual facts, and overlapping taxonomy branches. The new consensus favors precision, exposes provenance per row, keeps up to four independently supported issues, and preserves every disagreement for later expert adjudication rather than presenting mechanical union as certainty.
