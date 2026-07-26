# Flip experiment v2: five-provider re-classification ablation

**Run date:** 2026-07-26

**Question:** Did the post-fix improvement come from the LLMs receiving the
follow-up answer, or merely from dropping keyword and SPOT from the second
vote?

## Answer

The improvement remains large when keyword and SPOT stay in the
re-classification vote. Among the 692 matched cases with a complete
five-provider result, the expected final exact label was present in 381
(55.06%) before the answer and 623 (90.03%) after it. Re-classification gained
the expected label in 255 cases and lost it in 13: a net gain of 242 and a
19.6:1 gain-to-loss ratio.

This ablation therefore supports the intended interpretation of the post-fix
result: **the main difference is that the LLM classifiers receive and process
the disclosed answer, not that keyword and SPOT disappear from the second
vote.** Dropping the two non-context-aware providers is not necessary to
produce the large positive flip signal.

## Design

This is a paired re-classification-only ablation of post-fix condition B. It
reuses the archived `results/final_run_1_20260718T203325Z` opening
classifications, generated questions, and GPT-5 question/fact match decisions.
It repeats only the answer-bearing classification call.

The source condition and this ablation differ as follows:

| Stage | Post-fix condition B | Five-provider ablation |
|---|---|---|
| Opening classification | GPT-5, Gemini, Mistral, keyword, SPOT | Frozen from condition B |
| Generated questions and matcher decision | Fresh in condition B | Frozen from condition B |
| Answer supplied to LLMs | Yes | Yes |
| Re-classification vote | GPT-5, Gemini, Mistral | GPT-5, Gemini, Mistral, keyword, SPOT |
| Keyword/SPOT answer behavior | Excluded | Included, but ignore the answer by provider contract |

The explicit five-model list bypasses FETCH's normal refinement filter.
GPT-5, Gemini, and Mistral receive the matched question and answer as
conversation turns. Keyword and SPOT see the original narrative, ignore the
conversation, and still contribute their ordinary weighted votes. Thus both
the frozen opening result and new final result use the same five-provider
pool; answer availability to the three LLMs is the meaningful within-case
change.

The runner uses the same FETCH follow-up fix commit as condition B
(`41585d0a79de0c2d18a27355dd55b0729f8a968e`), vote mode, cache disabled,
concurrency 4, and 120-second provider timeouts. The source dataset and source
run hashes are recorded in the run metadata.

## Why 693 cases were re-classified, not 959

Flip v2 only makes the second call when FETCH asks a question that the hidden
fact directly answers. The frozen source run has:

| Funnel stage | Cases |
|---|---:|
| Opening classifications | 959 |
| No matcher call (no eligible follow-up question) | 52 |
| GPT-5 question/fact matcher calls | 907 |
| Matcher accepted a question | 693 |
| Matcher did not accept a question | 214 |

The 214 nonmatches include 2 matcher errors. In total, 693/959 (72.26%) cases
entered re-classification. Supplying the hidden disclosure to the remaining
266 cases without a matched question would test a different workflow:
unsolicited extra context rather than the benchmark's
question → answer → re-classification path.

## Primary results

One matched narrative,
`v2_small_claims_vs_construction_61`, produced five consecutive Mistral
timeouts: four at 120 seconds during the main run and one at 300 seconds in an
isolated repair attempt. It is retained as a matched provider error but has no
final score. The primary denominator is therefore 692 complete
re-classifications out of 693 matched cases.

### Exact-label transition matrix

| Before answer (five providers) | After answer (five providers) | Cases |
|---|---|---:|
| Correct | Correct | 368 |
| Correct | Wrong | 13 |
| Wrong | Correct | 255 |
| Wrong | Wrong | 56 |
| **Total scored** |  | **692** |

| Metric | Result |
|---|---:|
| Expected final exact label present before answer | 381/692 (55.06%) |
| Expected final exact label present after answer | 623/692 (90.03%) |
| Exact label gained | 255/692 (36.85%) |
| Exact label lost | 13/692 (1.88%) |
| Net gained minus lost | **+242** |
| Gain-to-loss ratio | **19.6:1** |
| Final exact accuracy, Wilson 95% CI | **90.03% (87.57–92.05%)** |

Among the 268 discordant cases, 255 moved in the intended direction and 13
moved in the wrong direction. A two-sided exact binomial/McNemar test against
equal directions gives `p = 1.95 × 10^-59`. This is descriptive evidence for
this authored benchmark, not a population estimate for legal-intake traffic.

The same conclusion holds at category level: final expected-category presence
was 97.25% among scored matched cases, and the expected category was newly
added in 110 cases (15.90%).

### By disagreement mechanism

| Mechanism | Scored | Final exact | Gained | Lost | Net |
|---|---:|---:|---:|---:|---:|
| M1 core vs. secondary issue | 84 | 72 (85.71%) | 37 | 5 | +32 |
| M2 specific vs. general fallback | 135 | 125 (92.59%) | 51 | 2 | +49 |
| M3 missing procedural/institutional fact | 417 | 374 (89.69%) | 145 | 6 | +139 |
| M4 competing framings | 56 | 52 (92.86%) | 22 | 0 | +22 |

Every mechanism is net-positive. M3 contributes the most gains because it is
the largest stratum, while all four mechanisms show the same direction.

### Safety-sensitive cases

| Safety flag | Scored | Final exact | Gained | Lost | Net |
|---|---:|---:|---:|---:|---:|
| No | 609 | 547 (89.82%) | 211 | 13 | +198 |
| Yes | 83 | 76 (91.57%) | 44 | 0 | +44 |

The safety-sensitive subset is also strongly positive, with no expected exact
labels lost in this run.

## Relationship to the published three-provider post-fix result

The original condition-B summary reported 194 gains, 13 losses, and net +181,
with 88.56% final exact accuracy among its 533 matched cases that returned
nonempty final labels. This ablation reports 255 gains, 13 losses, and net
+242, with 90.03% final exact accuracy among 692 complete five-provider
results.

Those headline counts should not be treated as a randomized comparison of
three providers versus five. The ablation freezes the opening and match stages
but necessarily makes fresh LLM calls seven days later, and the original run
had 160 matched rows with empty final outputs under the older service
conditions. On the 533 cases with nonempty finals in both runs, the paired
exact-label outcomes were:

| Original three-provider final | New five-provider final | Cases |
|---|---|---:|
| Correct | Correct | 466 |
| Correct | Wrong | 6 |
| Wrong | Correct | 14 |
| Wrong | Wrong | 47 |

The new five-provider result is 90.06% exact on that common subset versus
88.56% in the original run, but ordinary LLM resampling and changed service
reliability can explain a small difference of this size. The defensible
conclusion is narrower: **keeping keyword and SPOT does not eliminate, or even
substantially weaken, the answer-associated improvement.** This study was
designed to rule out provider removal as the sole cause, not to estimate
whether three or five providers is the better production ensemble.

## Provider-completeness audit

All 692 scored records archive raw results under each of the five exact
provider keys: `gpt-5`, `gemini`, `mistral`, `keyword`, and `spot`. No scored
record contains a missing provider or provider error.

- 656 rows succeeded with all five providers on the first attempt.
- 36 rows succeeded on the second attempt.
- The repaired first attempts were 35 SPOT failures and 1 Gemini failure.
- The one unscored case exhausted four Mistral attempts, then failed a
  separate 300-second repair call.
- Cache use was disabled, including on retries.

This retry policy matters: accepting first-attempt partial votes would have
turned the nominal five-provider arm into an undocumented mixture of four-
and five-provider results.

## Limitations

1. The 959 candidates are Claude-authored and still marked
   `claude_authored_awaiting_human_salience_audit`; they are not human gold
   intake narratives.
2. Only cases with a matched generated question are eligible for
   re-classification. The result measures answer use conditional on the
   question-generation and matching gate.
3. LLM calls remain stochastic. Freezing the initial outputs, questions, and
   matcher decisions removes most cross-condition variation, but the new final
   LLM responses are fresh samples.
4. Keyword and SPOT do not consume the answer. This is intentional: the
   ablation asks whether their unchanged votes can explain away the apparent
   benefit of answer-aware LLM re-classification.
5. One of 693 matched cases (0.14%) is unscorable because Mistral repeatedly
   timed out.

## Reproduction and artifacts

Runner:
[`run_five_provider_reclassification_ablation.py`](../run_five_provider_reclassification_ablation.py)

Failure finalizer:
[`finalize_five_provider_ablation.py`](../finalize_five_provider_ablation.py)

Committed derived analysis:
[`five_provider_reclassification_ablation/`](five_provider_reclassification_ablation/)
including the compact
[`ablation_transition_summary.json`](five_provider_reclassification_ablation/ablation_transition_summary.json).

The raw run is under the gitignored results directory:
`flip_experiment_v2/results/five_provider_reclassification_ablation_full_validated_20260726T171603Z/`.
Its `run_metadata.json` records the source hashes, code hash, FETCH commit,
provider policy, retry ceiling, environment, integrity counts, and
post-run handling of the single unscorable case.

```bash
FETCH_REPO_ROOT=/path/to/fetch-at-41585d0 \
FETCH_ENV_FILE=/path/to/fetch/.env \
python /path/to/publishable-repo/flip_experiment_v2/run_five_provider_reclassification_ablation.py \
  --label five_provider_reclassification_ablation_full_validated \
  --source-run /path/to/final_run_1_20260718T203325Z \
  --concurrency 4 \
  --provider-timeout-seconds 120 \
  --max-provider-attempts 4

python flip_experiment_v2/analyze_runs.py \
  --candidates flip_experiment_v2/candidates/flip_candidates_v2.csv \
  --runs flip_experiment_v2/results/five_provider_reclassification_ablation_full_validated_<timestamp> \
  --out flip_experiment_v2/analysis/five_provider_reclassification_ablation
```
