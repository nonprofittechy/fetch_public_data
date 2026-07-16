# Five-rater agreement and disagreement findings

## Scope and interpretation

The reliability analysis uses the 114 unique problem descriptions with eligible labels from both human reviewers. Exact duplicate descriptions are one target, not repeated targets. The five raters are GPT-5.2, Gemini 3.1 Pro, DeepSeek V4, Jackie, and QS. Every rating is treated as an unordered set.

ICC is naturally defined for numerical ratings, while these labels are nominal multi-label sets. The main ICC therefore measures **how many labels** each rater selected. Two supplemental ICCs turn each plausible scenario/label choice into a binary selected/not-selected rating: one at the exact taxonomy-pair level and one at the top-level category. Pairwise Jaccard, label F1, and exact-set agreement are more directly interpretable for the nominal label contents.

## Quantitative results

| Measure | ICC(A,1), single rater | ICC(A,k), mean of raters | Interpretation |
|---|---:|---:|---|
| Label count, all five raters (114 scenarios) | 0.328 (bootstrap 95% CI 0.216–0.421) | 0.709 (0.579–0.784) | Individual raters differed substantially in how many issues they retained; aggregation was materially more stable. |
| Label count, two humans | 0.304 | 0.466 | The humans' scope threshold differed even when they often shared the core label. |
| Label count, three LLMs | 0.321 | 0.587 | DeepSeek was notably more conservative than GPT-5.2 and Gemini. |
| Exact-pair incidence, conditional on a pair being proposed (340 targets) | 0.279 | 0.660 | Exact subcategory agreement was the weakest reliability dimension. |
| Top-level incidence, conditional on a category being proposed (193 targets) | 0.390 | 0.761 | Raters agreed more readily on broad legal domain than exact routing label. |

The apparently high all-taxonomy incidence sensitivity result—ICC(A,1) 0.743 across 23,826 scenario/pair cells—is misleading because the five raters jointly reject almost all of the 209 possible labels for each scenario. Shared zeros dominate it. It is reported for completeness, not as the headline reliability estimate.

The humans selected the exact same unordered set on 61/114 scenarios (53.5%). Their mean Jaccard similarity was 0.749 and mean label F1 was 0.818, showing that many non-exact disagreements were one-label additions or omissions rather than wholly different readings. GPT-5.2 and Gemini were the closest LLM pair (mean Jaccard 0.730; 59/114 exact sets). Mean label counts were 2.22 for GPT-5.2, 2.11 for Gemini, 1.55 for DeepSeek, 1.82 for Jackie, and 1.97 for QS.

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
