# FETCH multi-label consensus-gold findings

## Headline results

The primary benchmark contains **373 unique, whitespace-normalized scenarios**. Each uncached replicate used the full five-classifier FETCH vote ensemble (GPT-5.2, Gemini, Mistral, keyword, and SPOT). Exact sublabel comparisons apply the audited legacy/current taxonomy compatibility map described in [`FETCH_GOLD_ACCURACY_METHODS.md`](FETCH_GOLD_ACCURACY_METHODS.md).

| Run | N | All exact sublabels | Some exact sublabels | Top-level only | No correct category | Any exact sublabel | Any correct top-level | Graded score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| run1 | 373 | 80.4% | 14.5% | 4.0% | 1.1% | 94.9% | 98.9% | 92.6% |
| run2 | 373 | 82.3% | 13.4% | 3.8% | 0.5% | 95.7% | 99.5% | 93.5% |
| pooled | 746 | 81.4% | 13.9% | 3.9% | 0.8% | 95.3% | 99.2% | 93.0% |

Across the two run-observations per scenario, FETCH retrieved at least one exact sublabel in **95.3%** and at least one correct top-level category in **99.2%**. It retrieved every gold sublabel in **81.4%**. The lower strict-set result (**10.5%**) shows that the ensemble commonly adds plausible labels beyond the conservative gold set; it should not be confused with failure to retrieve the needed route.

## Rank-aware retrieval

| Run | Hits@1: any exact | Hits@2: any exact | All gold within top 2 | Gold-instance recall@1 | Gold-instance recall@2 |
|---|---:|---:|---:|---:|---:|
| run1 | 85.0% | 92.5% | 76.4% | 61.0% | 80.0% |
| run2 | 86.3% | 94.1% | 77.8% | 62.0% | 81.2% |
| pooled | 85.7% | 93.3% | 77.1% | 61.5% | 80.6% |

Hits@2 asks whether at least one exact gold sublabel appears among the first two ordered FETCH labels. The all-gold-within-top-2 measure is stricter for multi-label scenarios, while gold-instance recall@2 pools every expected label instance.

At the label-instance level, exact micro precision / recall / F1 were **46.0% / 84.5% / 59.6%**. For referral utility, recall and the outcome tiers are the more direct measures: one correct route may be useful even when extra routes are offered.

## Performance by number of gold issues

| Gold sublabels | Scenario-run observations | All exact | Some exact | Top-level only | No correct category | Mean exact coverage | Graded score |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 476 | 95.2% | 0.0% | 3.8% | 1.1% | 95.2% | 97.1% |
| 2 | 248 | 59.7% | 35.9% | 4.0% | 0.4% | 77.6% | 86.8% |
| 3 | 18 | 33.3% | 61.1% | 5.6% | 0.0% | 64.8% | 76.8% |
| 4 | 4 | 0.0% | 100.0% | 0.0% | 0.0% | 50.0% | 71.9% |

Multi-label rows make the distinction between *some* and *all* retrieval visible. A system can successfully expose one attorney-relevant route while still omitting a secondary issue; the graded score gives partial credit without calling that result complete.

## Performance by top-level legal category

A scenario with gold labels in more than one top-level category contributes to each applicable row.

| Gold top-level category | Scenario-run observations | Any exact sublabel | All exact sublabels | Any correct top-level | Exact coverage | Graded score |
|---|---:|---:|---:|---:|---:|---:|
| General Litigation | 96 | 94.8% | 71.9% | 100.0% | 82.8% | 89.1% |
| Real Property | 80 | 93.8% | 68.8% | 97.5% | 81.7% | 87.5% |
| Criminal Law | 72 | 95.8% | 87.5% | 100.0% | 91.4% | 95.1% |
| Family Law | 70 | 100.0% | 77.1% | 100.0% | 89.0% | 93.3% |
| Administrative Law | 66 | 97.0% | 78.8% | 100.0% | 88.6% | 92.8% |
| Consumer Law | 64 | 92.2% | 79.7% | 100.0% | 85.9% | 91.4% |
| Business and Corporate | 56 | 98.2% | 67.9% | 98.2% | 83.6% | 88.5% |
| Debtor/Creditor | 56 | 75.0% | 41.1% | 100.0% | 57.7% | 76.6% |
| Intellectual Property | 56 | 100.0% | 91.1% | 100.0% | 95.5% | 97.3% |
| Labor & Employment | 54 | 98.2% | 75.9% | 100.0% | 86.4% | 92.1% |
| Wills & Trusts | 50 | 98.0% | 78.0% | 100.0% | 88.0% | 93.2% |
| International Law | 48 | 91.7% | 79.2% | 95.8% | 85.4% | 89.6% |
| Bankruptcy | 42 | 100.0% | 81.0% | 100.0% | 91.3% | 95.6% |
| Workers' Comp | 38 | 97.4% | 89.5% | 97.4% | 93.4% | 95.4% |
| Taxation | 12 | 100.0% | 50.0% | 100.0% | 72.2% | 81.2% |

## Replicate stability

Both runs contain 373 common scenarios. The exact/none success status was stable for **96.5%** of scenarios, while the full four-tier outcome was stable for **94.9%**. The returned label set was identical in **73.7%** and had mean cross-run Jaccard similarity **86.3%**. At least one exact sublabel appeared in every run for **93.6%**, and all gold sublabels appeared in every run for **79.4%**.

## Qualitative error patterns

The most informative misses fall into three groups:

1. **Partial multi-issue retrieval.** FETCH finds the dominant dispute but omits a secondary legal route, often when the narrative gives much more detail to one issue.
2. **Right domain, wrong specialist route.** The ensemble reaches the correct top-level area but chooses a neighboring subcategory. These cases are often genuinely ambiguous because procedural posture, party side, requested relief, or whether an issue is primary versus contextual is not explicit.
3. **Broad overprediction.** Exact recall is high relative to precision because the vote/merge ensemble commonly retains additional plausible routes. This may increase the chance of reaching a helpful attorney, but it also creates triage burden and explains the gap between all-label retrieval and strict exact-set matching.

### Illustrative partial or category-only cases

- **gold-0027 (run2; no correct category)** — “I was injured at work on 6/25/23. Was on worker’s compensation for about 6 months. Broke my hip and l4 & l5 on a slip and fall at Hawthorn Market’s distribution center while working in the freezer. Wondering what my options are for my personal injury.”
  - Gold: `Workers' Comp > State || Workers' Comp > Third Party litigation`
  - FETCH: `General Litigation > Personal Injury`
- **gold-0028 (run1; no correct category)** — “I have a signed contract with a roofing company to replace my roof, they did not do the roof, but they took $13,000 from me, and have now closed their business. I would like to file something to get my money back, I thought this was a small claims issue, but then I saw the maximum for small claims is $10,000. So, I need an attorney to help me get my money b…”
  - Gold: `Real Property > Construction/Contractors`
  - FETCH: `Business and Corporate > General (contracts, entities) || Consumer Law > General || General Litigation > General Litigation`
- **gold-0029 (run1; no correct category)** — “I owe taxes to Canada from my time working there over 10 years ago and need assistance in seeing if I can dispute them or remove the interest requirements. Also curious about their statute of limitations.”
  - Gold: `International Law > Taxation`
  - FETCH: `Taxation > Personal Income || Taxation > Litigation || Taxation > International`
- **gold-0117 (run1; no correct category)** — “we need an attorney who will complete the foreclosure on a business. We have filed the notice of liens and neither party answered. We sold my husbands business in 2016 on a sales contract. the other party has not made any payments in 2021 so we filed for foreclosure on the security in the sales contract.”
  - Gold: `Business & Corporate > Litigation`
  - FETCH: `Real Property > Foreclosure`
- **gold-0268 (run1; no correct category)** — “I feel I am a victim of abuse and would like to seek help from an immigration attorney experienced with VAWA to see if they can take my case. I live in fear to lose my kids.”
  - Gold: `International Law > Gen. Immigration/Visas`
  - FETCH: `Family Law > Domestic Violence`
- **gold-0137 (run1; top level only)** — “Auto shop negligence on a transmission repair causing danger to me and my children and damaging my vehicle. Looking to open a lawsuit.”
  - Gold: `General Litigation > Property Damage || Consumer Law > General`
  - FETCH: `General Litigation > Personal Injury || General Litigation > General Torts/Privacy || General Litigation > Products Liability`
- **gold-0142 (run1; top level only)** — “I sold my RV and did a written contract stating that this person would buy it and pay $1000 a month. They made one payment and took off with my RV. It has been a year and a half and I’ve been trying to figure this out I know they’re back in Oregon so I’m trying to solve this issue as quickly as possible. They owe me $14,000 or my RV back. I have tried to co…”
  - Gold: `Consumer Law > Problems Between Consumers || Debtor/Creditor > General (Creditor)`
  - FETCH: `General Litigation > General Litigation || Consumer Law > Automobiles/RV's/Mobile Homes`
- **gold-0192 (run1; top level only)** — “I thought I resolved a small claims issue but I just received a "motion to keep matter as a pending case" after it was already closed. I'm currently on a payment plan with the law office that bought my debt. Just wondering if this is normal and what I can do to get it dismissed. The best way to reach me is by email.”
  - Gold: `Debtor/Creditor > General (Debtor) || Consumer Law > Small Claims Advice`
  - FETCH: `Debtor/Creditor > Judgment Collection`

These examples are diagnostic, not a random sample. Row-level outcomes for every scenario and run are in [`scenario_results.csv`](scenario_results.csv).

## Scope and limitations

The gold set is a conservative consensus derived from two human raters, three independent LLM passes, and the internally reviewed primary label; it is not de novo adjudication by multiple specialist attorneys for every row. Some additional FETCH labels may be reasonable even when absent from gold. The metrics therefore report both retrieval-oriented recall and strict-set precision, preserve all raw predictions, and avoid treating top-level-only routing as equivalent to an exact specialist match.

The independent run/provider audit records final provider timeouts or errors. A transient provider traceback that succeeded on retry is not counted as a final provider failure. Any targeted GPT-5.2 repair is saved separately and integrated before the final tables.
