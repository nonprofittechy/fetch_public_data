# Why these results differ from *On Wednesdays*

## Executive finding

The alarming result previously summarized as “176 rescued versus 307 harmed” was an **analysis mistake**, not an experimental finding. That calculation classified every initially-correct/finally-wrong case as harm. The *On Wednesdays* analysis code instead called a case harmful only when all three conditions held:

1. the expected initial category was present initially;
2. the expected final category was absent after the answer; and
3. the serialized first top-level category changed.

It classified an initially-correct/finally-wrong case with no top-category change as a neutral failure to flip. Applying that historical code exactly to the current 2,149 matched observations gives:

| Historical paper outcome | Current count | Share of matched |
|---|---:|---:|
| Initial correct and final correct | 1,643 | 76.45% |
| Neutral failure to flip | 301 | 14.01% |
| Harmed/degraded | 6 | 0.28% |
| Rescued | 176 | 8.19% |
| Initially wrong and still wrong | 23 | 1.07% |

The historical rescue-to-harm ratio is therefore **176:6 = 29.33:1**, compared with **18:4 = 4.5:1** in *On Wednesdays*. This historical ratio is included only for direct replication: its harm definition depends on serialized first-label order, which is not a criterion in the present unordered-set study.

The symmetric order-independent diagnostic remains:

| Expected final target | Added after answer | Lost after answer | Ratio | Net |
|---|---:|---:|---:|---:|
| Top-level category membership | 47 | 48 | 0.98:1 | −1 |
| Exact-label membership | 122 | 102 | 1.20:1 | +20 |

These answer different questions. The paper matrix asks whether a scenario moved from its expected initial side to its expected final side and uses a first-label change to distinguish harm from neutral failure. The symmetric set matrix asks whether the *same expected final member* appeared or disappeared after the answer.

## The same 200 scenarios do not reproduce a coverage collapse

The current dataset contains an exact textual copy of the paper's 200 candidates. A field-by-field check found zero differences in all 200 opening queries, hidden facts, answer phrasings, and relevant-question topics. Labels were normalized to the current taxonomy, but the hidden-information design was not changed.

| Metric | *On Wednesdays* | Current same 200, run 1 | Run 2 | Run 3 | Current pooled |
|---|---:|---:|---:|---:|---:|
| Initial category present | 77.0% | 76.0% | 74.0% | 74.0% | 74.67% |
| Question coverage | 69.0% | 65.5% | 68.0% | 65.5% | 66.33% |
| Final category present among matched | 65.2% | 78.63% | 75.0% | 78.63% | 77.39% |
| Historical rescues | 18 | 25 | 27 | 25 | 77 |
| Historical harms | 4 | 1 | 1 | 0 | 2 |

Initial accuracy and question coverage are close to the prior single run. The current coverage range of 65.5–68.0% is only 1–3.5 percentage points below 69%, so there is no evidence that the legacy facts were hidden in a materially harder way. Final category performance, however, is 9.8–13.4 points above the paper and outside the three-run current range. That is more consistent with a changed system condition than ordinary repeat variation.

As a rough scale check, a 69% proportion on 200 cases has a 95% Wilson interval of about 62.3–75.0%; all three current legacy coverage estimates fall inside it. The paper's 90/138 final result has an interval of about 57.0–72.7%, while current point estimates are 75.0–78.63%. These are descriptive intervals—not a valid independent-sample test because the same scenarios recur—but they reinforce that coverage is plausibly ordinary run variation while the final-classification shift deserves a system-condition explanation.

The paired scenario comparison shows churn beneath the similar aggregate coverage. Relative to the paper run, each current run lost matches on 21–25 of the original scenarios and gained matches on 17–19 formerly unmatched scenarios. Among scenarios matched in both the paper and a current run, current final classification changed more paper failures to successes (11–13 per run) than successes to failures (4–7 per run). This points to provider/question variability and changed system behavior, not uniformly harder hiding.

## Pair changes are large but offset one another

On the same legacy candidates, coverage did not move uniformly:

| Pair | Paper coverage | Current pooled coverage | Change |
|---|---:|---:|---:|
| `domestic_violence` | 10.0% | 40.0% | +30.0 points |
| `custody_vs_support` | 85.0% | 93.33% | +8.33 |
| `employee_vs_employer` | 90.0% | 95.0% | +5.0 |
| `dui_vs_dmv` | 100.0% | 100.0% | 0.0 |
| `debtor_vs_creditor` | 55.0% | 51.67% | −3.33 |
| `bankruptcy_vs_collections` | 45.0% | 41.67% | −3.33 |
| `employment_admin` | 20.0% | 13.33% | −6.67 |
| `tenant_vs_landlord` | 95.0% | 85.0% | −10.0 |
| `criminal_vs_restraining` | 95.0% | 73.33% | −21.67 |
| `injury_location` | 95.0% | 70.0% | −25.0 |

This is not a simple global regression. Domestic-violence probing improved materially, while work-injury and criminal/restraining coverage worsened. The gains and losses mostly cancel in the overall legacy coverage rate.

## The 800 expanded scenarios are not the source of lower overall coverage

The expanded scenarios had **72.96%** coverage, compared with **66.33%** for the repeated legacy scenarios. They therefore raise, rather than lower, the pooled 71.63% rate. Their final-category membership was also higher: 86.29% versus 77.39% among matched cases.

Their composition is different in a way that weakens a binary category-flip interpretation:

- 48.5% of expanded observations keep the same top-level category and change only exact subcategory, compared with 30.0% of legacy observations.
- Same-category expanded cases had 86.08% question coverage; cross-category expanded cases had 60.60%.
- The expected final category was already present initially in 1,515/1,751 matched expanded observations (86.52%).
- Expanded opening queries averaged 16.60 words versus 18.39 for legacy; hidden facts averaged 12.65 versus 13.65. There is no length evidence that expanded facts were harder to reveal.

The expanded benchmark therefore contains many realistic multi-label ambiguity tests, but relatively few clean category-membership flips. That is a benchmark-design limitation, not a FETCH failure.

## System conditions changed substantially

The current runs are not controlled replications of the paper:

| Component | *On Wednesdays* | Current official runs |
|---|---|---|
| Classifier ensemble | GPT-5, Gemini, Mistral, keyword, SPOT | GPT-5, keyword |
| FETCH provider cache | enabled | disabled and cleared per case |
| Replication | one cached run | three uncached runs |
| Semantic merge | GPT-5 | GPT-5 |
| Fact/question matcher | GPT-4.1, temperature 0 | GPT-4.1, temperature 0 |
| Code/taxonomy | earlier FETCH state | current FETCH state plus constructor compatibility shim |

Qualification pilots showed Mistral rate limits, Gemini 503s, and SPOT timeouts, which is why the official condition was narrowed. That made the runs stable, but it also changed ensemble votes and question generation. Because the exact paper commit/environment was not archived in its result metadata, code drift cannot be separated from provider-composition drift. The stable 75.0–78.63% final performance on the same legacy text, versus the paper's 65.2%, strongly suggests a systematic condition change.

## Actual mistakes and limitations

1. **Analysis mistake, now corrected:** 301 neutral failures to flip were incorrectly called harm. The exact paper-code harm count is 6, not 307.
2. **Not a controlled replication:** narrowing five providers to two prevents attribution of differences to the candidate dataset alone.
3. **Many candidates are not empirical flips:** expected final membership was usually present before the answer. Future construction should validate candidate flips against repeated initial outputs before paid evaluation.
4. **Matcher overbreadth:** GPT-4.1 sometimes accepts generic questions. For hidden-DV observations, matcher coverage was 78.04% but only 44.31% of question sets explicitly probed safety/abuse/protection.
5. **No paired counterfactual official run:** only intended facts were evaluated, so the study does not test whether opposing answers move the same query in opposing directions.
6. **No simultaneous no-answer control:** uncached second classifications can vary even without a fact, so added/lost membership is diagnostic rather than causal.
7. **Taxonomy drift:** spelling aliases were canonicalized and four historical exact labels were excluded from exact denominators; category metrics are unaffected.
8. **Synthetic candidates need review:** the 800 workbook-grounded scenarios are candidate tests, not human-adjudicated gold outcomes.

## Conclusion

The current evidence does **not** support the claim that follow-up questions harm classification more often than they rescue it. That claim came from an outcome-matrix coding error. On the historical paper calculation, the current runs appear more favorable than *On Wednesdays*; on the order-independent same-target calculation, category membership is neutral and exact-label membership improves modestly.

The overall coverage result is not meaningfully different from the paper when restricted to the same 200 cases. What changed materially is final classification performance and pair-specific behavior, most plausibly because the classifier ensemble, cache policy, code, and taxonomy changed. The expanded scenarios add useful multi-label stress tests, but their high rate of pre-existing final labels means they do not yet form a clean 800-case binary flip benchmark.

## Traceable evidence

- Machine summary: `analysis/on_wednesdays_difference_summary.json`
- Pair comparison: `analysis/on_wednesdays_pair_comparison.csv`
- All parsed observations: `analysis/runs/all_scenario_details.csv`
- Original paper-run result: `/home/quinten/fetch/results/followup_fact_results.json`, SHA-256 `f8a00784ebf48fc4a7ee90fe9d86e3d7ae6375cf54a89628f886c17c7350a350`
- Original 200 candidates: `/home/quinten/fetch/promptfoo/individual_facts/classification_flip_scenarios.csv`, SHA-256 `22a95ba20893e54890d44c169088491481199e971852b4bd66ddbdf0517e587b`
- Current raw results and their hashes are indexed in `RUN_TRACEABILITY.md`.
