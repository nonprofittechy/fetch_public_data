# v2 disclosure-grounded flip benchmark: results

**Status (2026-07-19): the pipeline bugs described below under "Root cause"
are fixed, and the current, definitive answer to "do follow-up questions
help?" is in [Post-fix results](#post-fix-results-do-follow-up-questions-help),
[Condition B vs C](#condition-b-vs-c-does-the-screening-protocol-add-anything),
and [Variability](#variability-is-this-llm-sampling-noise) (6 reruns confirm
the post-fix results are not a sampling-noise artifact) below — read those
three sections first.** Everything from "Root cause"
through "Family-level extremes" documents the **pre-fix baseline**
(`final_run_1_20260718T002609Z`, GPT-5 + keyword only, 2-provider vote) and
is retained for the audit trail: it's what motivated the fix, not a
current-state measurement. Its gained/lost numbers reflect a classifier
call that never actually received the disclosed answer — see "Root cause."

Full method, provenance, and reproduction commands: [`../README.md`](../README.md).
Run-by-run mechanics: [`EXECUTION_LOG.md`](EXECUTION_LOG.md).

## Post-fix results: do follow-up questions help?

Two fully independent 959-case runs, both on the fixed pipeline (FETCH
commit `41585d0`, 5-provider vote — `gpt-5`, `gemini`, `mistral`, `keyword`,
`spot` — on the opening call; `gpt-5`, `gemini`, `mistral` on the
follow-up-answer call), one run per condition (per study-owner decision,
2026-07-18):

- **Condition B** — fixes only, no screening protocols.
  `results/final_run_1_20260718T203325Z`, analysis in
  [`runs_v2_postfix_condition_b/`](runs_v2_postfix_condition_b/). 959/959
  cases, 0 orchestrator errors, 2 matcher errors, 137.0 minutes.
- **Condition C** — fixes plus PR #34's deterministic screening protocols
  (see [Condition B vs C](#condition-b-vs-c-does-the-screening-protocol-add-anything)
  below). `results/final_run_1_20260718T225512Z`, analysis in
  [`runs_v2_postfix_condition_c/`](runs_v2_postfix_condition_c/). 959/959
  cases, 0 orchestrator errors, 4 matcher errors, 142.6 minutes.

| Metric | Pre-fix baseline | Condition B (post-fix) | Condition C (post-fix + screening) |
|---|---:|---:|---:|
| Expected initial exact label present anywhere | 60.90% | 83.21% | 83.73% |
| GPT-5 matcher: question judged answerable by hidden fact | 48.70% | 72.26% | 72.68% |
| Expected final exact label present, among matched | 49.43% | 88.56% | 91.44% |
| Expected final exact label already present **initially**, among matched | 29.93% | 47.24% | 48.49% |
| Expected final exact label **gained** after re-classification, among matched | 24 (6.90%) | 194 (36.40%) | 228 (38.26%) |
| Expected final exact label **lost** after re-classification, among matched | 31 | 13 | 8 |
| Net gained − lost | **−7** | **+181** | **+220** |

**This is the direct answer to "are follow-up questions helpful": yes,
clearly, once the pipeline actually uses the disclosed answer.** Pre-fix,
losses outnumbered gains (net −7) — the pattern that originally looked like
"questions don't help, or actively hurt." That was an artifact of the two
bugs under "Root cause," not a property of the disclosed facts or of FETCH's
reasoning: the second call was silently re-sampling the first call's prompt,
so any change in the label set was sampling noise, and losses were exactly
as likely as gains. Post-fix, gains outnumber losses by roughly 15:1
(condition B) to 28:1 (condition C), and matched-case final accuracy nearly
doubles (49% → 89–91%). The gain/loss asymmetry, not just the accuracy
level, is the evidence that the model is now incorporating the disclosed
fact rather than resampling.

Safety-sensitive rows (n=115) are, if anything, the strongest part of this
result: **zero losses in either post-fix condition** (37 gained / 0 lost in
B, 41 gained / 0 lost in C), with final exact accuracy among matched cases
at 89.7% (B) and 93.8% (C) — see
[`runs_v2_postfix_condition_b/pooled_by_safety_sensitive.csv`](runs_v2_postfix_condition_b/pooled_by_safety_sensitive.csv)
and the condition-C equivalent.

One methodological note for anyone trying to attribute the pre-fix-to-B
jump specifically to the code fixes: the pre-fix baseline run also used a
narrower 2-provider vote (`gpt-5`, `keyword` only), while condition B uses
the full 5-provider mix adopted alongside the fix (task-tracked
alongside it, not a separate experiment). The pre-fix vs. post-fix
comparison therefore conflates the bug fixes with the provider-mix change
and should not be read as isolating the fixes' own effect size — only as
"the pipeline as it exists now, vs. as it existed before this work,"
which is the comparison that matters for the "are questions helpful"
question this section answers.

## Condition B vs C: does the screening protocol add anything?

PR #34 added deterministic screening protocols to FETCH: six
checkbox/keyword-driven rules (`family_safety`, `employment_retaliation`,
`third_party_work_injury`, `elder_exploitation`, `immigration_consequences`,
police/government) that can add a **mandatory category** to
`effective_categories` — the field FETCH's own docs say clients should treat
as authoritative — independent of what the LLM vote alone concluded.
Condition C runs the identical benchmark against a worktree merging PR #34
onto the fix branch, and the harness
([`two_step_provider_bridge_screening.py`](../two_step_provider_bridge_screening.py))
scores `effective_categories` (falling back to raw `labels` only if
`effective_categories` is ever empty) while separately recording the raw
model-only labels, so the screening protocol's own contribution can be
isolated from ordinary run-to-run LLM variance.

**Between-run comparison (B vs C, one run each):** C is better on every
headline metric in the table above — final exact accuracy among matched
cases (91.44% vs 88.56%), gains (228 vs 194), losses (8 vs 13). But B and C
are each a single run of a stochastic pipeline, so part of that gap is
ordinary sampling noise, not necessarily the screening protocol; with one
run per condition (study-owner decision, see above) this comparison alone
can't cleanly separate the two.

**Within-run, paired comparison (the clean test):** for every condition-C
case, [`analyze_screening_contribution.py`](../analyze_screening_contribution.py)
compares `effective_categories` against the raw model vote (`labels`) *on
the same case, same underlying model outputs* — isolating just the
deterministic-union step and holding the LLM sampling constant. Full output:
[`runs_v2_postfix_condition_c/screening_marginal_contribution.json`](runs_v2_postfix_condition_c/screening_marginal_contribution.json).

| | Count |
|---|---:|
| Matched cases with a final answer | 596 |
| Correct via `effective_categories` (screening-aware) | 545 |
| Correct via raw model vote alone | 539 |
| **Rescued** by screening protocol (effective correct, model vote alone wrong) | **6** |
| **Regressed** by screening protocol (sanity check — should be 0) | **0** |

The screening layer rescues a small but real slice — about 1% of matched
cases — with **zero downside** (0 regressions is expected by construction,
since `effective_categories` is a union, but it's a useful sanity check that
the union logic behaves as documented). The 6 rescues are concentrated
exactly where the protocols are designed to fire:

| Scenario | Expected label | Triggering protocol |
|---|---|---|
| `v2_custody_safety_02` | Family Law > Restraining Orders | `family_safety.v1` (controlling/threatening) |
| `v2_immigration_posture_44` | International Law > General Immigration/Visas | `immigration_consequences.v1` |
| `v2_tenancy_property_type_46` | Wills & Trusts > Elder Abuse | `elder_exploitation.v1` (pressure/control) |
| `v2_wc_state_vs_third_party_21` | Workers' Comp > Third Party Litigation | `work_injury_third_party.v1` |
| `v2_wc_state_vs_third_party_43` | Workers' Comp > Third Party Litigation | `work_injury_third_party.v1` |
| `v2_wc_state_vs_third_party_46` | Workers' Comp > Third Party Litigation | `work_injury_third_party.v1` |

**Bottom line:** the LLM vote (now that it correctly receives the disclosed
answer) already does most of the work — 90%+ of the screening layer's
"correct" cases would have been correct anyway. But the deterministic
protocols add a small, clean, one-directional safety net on top, concentrated
in exactly the safety/routing-sensitive categories they were built for
(restraining orders, elder abuse, immigration consequences, third-party
work-injury litigation), at no cost in the cases where the model was already
right. That's consistent with the protocols' design intent — a backstop for
categories where a missed disclosure has outsized real-world consequences —
rather than a general accuracy improvement.

## Variability: is this LLM sampling noise?

Both headline comparisons above (pre-fix vs. post-fix, and B vs. C) are each
based on a single run per condition, so the natural follow-up question is
whether the reported gaps are stable signals or could just as easily flip
under ordinary LLM sampling noise. To check without re-running the full
959-case set six more times (~2.3h/run), a fixed, reproducible,
family-stratified 200-case subsample was built
([`build_variability_sample.py`](../build_variability_sample.py), seed 42 —
[`candidates/flip_candidates_v2_variability_sample.csv`](../candidates/flip_candidates_v2_variability_sample.csv),
33/33 boundary families represented) and run **three independent times per
condition**, same pipeline and provider mix as the official runs, cache
disabled throughout (`cache_enabled: False` is a full bypass in FETCH's
`ClassificationService` — verified directly against
`app/services/classification_service.py`, not inferred from config alone).

| Run | Final exact accuracy, among matched | Gained | Lost | Net |
|---|---:|---:|---:|---:|
| B1 | 87.88% | 37 | 4 | +33 |
| B2 | 87.13% | 39 | 6 | +33 |
| B3 | 90.53% | 37 | 2 | +35 |
| **B mean (sd)** | **88.51% (±1.79)** | 37.7 | 4.0 | **+33.7** |
| C1 | 93.28% | 45 | 2 | +43 |
| C2 | 92.80% | 48 | 2 | +46 |
| C3 | 90.35% | 49 | 3 | +46 |
| **C mean (sd)** | **92.14% (±1.57)** | 47.3 | 2.3 | **+45.0** |

Full per-run and pooled breakdowns:
[`variability_condition_b/`](variability_condition_b/),
[`variability_condition_c/`](variability_condition_c/).

**The "questions help" result is not noise.** Every one of the 6 variability
runs lands strongly net-positive (+33 to +46), matching the official 959-case
runs' direction (B +181, C +220) and nowhere close to the pre-fix baseline's
net −7. On the net-gained-minus-lost metric specifically, the separation
between conditions is complete: the *lowest* condition-C run (+43) still
beats the *highest* condition-B run (+35) — all 9 possible B-vs-C run
pairings agree on the direction. Pooling each condition's 3×200 observations
(600 each) gives the same picture with more power: 88.47% final-exact-among-matched
for B vs. 92.18% for C, gained 113/lost 12 (B) vs. gained 142/lost 7 (C).

**The B-vs-C accuracy gap is directionally consistent but not airtight on a
single-run basis.** Condition C's mean (92.14%) is ~3.6 points above
condition B's (88.51%), and 2 of 3 C runs clear the entire B range, but C3
(90.35%) and B3 (90.53%) overlap by design-of-experiment chance — with only
3 runs per condition, the accuracy metric alone (as opposed to the
gained/lost/net metric above) isn't strong enough to rule out sampling noise
run-by-run. The paired within-run comparison in the previous section (596
matched cases, same model outputs, only the deterministic screening step
varies) remains the more decisive evidence that screening protocols add a
small positive rescue effect — the variability runs corroborate the
direction without needing to carry that argument alone.

Both official 959-case single runs (B: 88.56%, C: 91.44%) fall inside their
respective 200-case variability ranges (B: 87.13–90.53%, C: 90.35–93.28%),
which is a useful sanity check that the smaller subsample isn't itself
biased relative to the full candidate set.

One honest caveat at the individual-case level: which follow-up question the
matcher selects (and therefore which cases even get a chance to change
label) is itself stochastic — only 93/200 (B) and 103/200 (C) scenarios were
matched to a question in *all three* runs of their condition, and 192/200
(B) / 194/200 (C) scenarios saw their matched question set vary across runs
at all (see `stability` in each condition's `summary.json`). Aggregate
accuracy is stable; which specific cases flip on any given run is not.

## Configuration

- 959 candidates (33 boundary families), all Claude Fable 5-authored.
- FETCH: GPT-5 + keyword classifier, vote mode, cache disabled.
- Relevance matcher: **GPT-5** (upgraded from v1's GPT-4.1).
- `final_run_1`: concurrency 4, 120s provider timeout. Two earlier attempts
  at concurrency 6 and 16 were aborted/quarantined for excessive Azure
  throttling — see the execution log. 0 orchestrator errors, 1 matcher error
  (of 870 calls), elapsed 127.6 minutes.

## Root cause: why the disclosed fact rarely changed the outcome

After `final_run_1` completed, the per-case data showed a pattern worth
explaining rather than just reporting: among 348 matched-and-scored cases,
24 gained the expected exact label after the disclosure, 31 lost it, and 145
matched cases never had it either before or after. That's a small, roughly
symmetric churn around a large "no effect" bucket — not what you'd expect if
the model were reliably incorporating a decisive new fact.

Tracing directly through the FETCH source (`/home/quinten/fetch`, not the
study harness) found two structural bugs in `ClassificationService.classify()`
that both fire specifically on the second, `followup_answers`-bearing call:

1. **GPT-5-family models never receive the follow-up answer on the normal
   code path.** `app/providers/openai.py:177-179` builds the Responses API
   `input` as:
   ```python
   responses_params = {
       "model": self.model_name,
       "input": f"SYSTEM:\n{prompt}\n\nUSER:\n{problem_description}",
   }
   ```
   using only the *original opening query*. The `followup_answers` parameter
   (line 104) is never referenced anywhere in the `GPT_5_FAMILY_MODELS`
   branch (lines 155-220). It's only consumed by `build_messages()`, which
   correctly threads the Q&A in as structured chat turns, but that function
   is called solely inside `except TypeError` / `except AttributeError`
   fallback handlers (lines 254-256, 270-272) — reached only if the
   `responses.create` call itself throws. In the normal, successful case —
   the overwhelming majority of calls, including in this study — **call 2
   sends the byte-identical prompt as call 1.** Since this study's classifier
   is `gpt-5`, the disclosed fact was never actually seen by the model, on
   either official run.

2. **The provider-pool filter for refinement calls is broader than intended.**
   `app/services/classification_service.py:1250-1261`:
   ```python
   if request.followup_answers:
       current_providers = [p for p in current_providers if isinstance(p, LLMClassifierProvider)]
       # comment: "excluding non-LLM providers like spot/keyword"
   ```
   Verified against the class hierarchy: `KeywordClassifierProvider` and
   `SpotProvider` are correctly excluded (both subclass `ClassifierProvider`
   directly). But `GeminiProvider` and `MistralProvider` *also* aren't
   subclasses of `LLMClassifierProvider` — only `OpenAIProvider` is — so real
   LLMs get excluded too, despite the comment's stated intent. For this
   study's `["gpt-5", "keyword"]` configuration, this collapses the vote pool
   from 2 providers (weight 0.9 + 0.5, per `CLASSIFIER_WEIGHTS` in
   `app/core/config.py`) to 1 (weight 0.9 alone) on call 2. Any label call 1
   surfaced only because `keyword` co-voted for it has no path to survive
   into call 2, regardless of what the disclosed fact said.

**Combined effect:** call 2 has exactly one voting provider, and that
provider is re-answering a prompt it has already answered once. GPT-5-family
calls also never set `temperature` — only `reasoning_effort` — so two calls
with identical input are not even guaranteed to return identical output. The
24-gained/31-lost split is best explained as **GPT-5 resampling noise
between two calls with identical input**, not as evidence the model
reasoned about the disclosed fact and sometimes got it right, sometimes
wrong. The 145 "never" cases are not "FETCH considered the fact and
rejected it" — they are "FETCH never received the fact."

**What this means for every number below:** the headline coverage and
category/exact-label statistics are still valid measurements of *this
pipeline configuration as actually deployed* — that's a legitimate and
useful thing to have measured, and the safety-sensitive gap and per-family
breakdown below are real, observed behavior. But the specific "did the
disclosed fact change the classification" comparisons should not be read as
a test of whether FETCH's *reasoning* handles disclosed facts well. They are,
inadvertently, closer to a test of "what happens when FETCH is asked the
same question twice" for the classifier actually in production use.

**Suggested fixes** (described here for the record; no code was changed as
part of this study):
1. Fix the Responses API branch to include `followup_answers` — either as a
   structured multi-turn `input` array analogous to `build_messages()`, or
   via `previous_response_id` chaining off call 1's response object.
2. Correct the `isinstance(p, LLMClassifierProvider)` filter to match its
   stated intent, e.g. `not isinstance(p, (KeywordClassifierProvider, SpotProvider))`,
   or make `GeminiProvider`/`MistralProvider` subclass `LLMClassifierProvider`.
3. After both fixes, re-running this benchmark (starting with the
   `ssi_vs_ssd` family, the cleanest single fact-dependent test in the set)
   is the natural validation step.

Full file/line citations are in `EXECUTION_LOG.md`.

## Headline metrics (pre-fix baseline, historical — `final_run_1_20260718T002609Z`, 959 observations)

**Superseded by [Post-fix results](#post-fix-results-do-follow-up-questions-help)
above.** Kept for the audit trail; the gained/lost numbers below reflect the
call-2-never-sees-the-answer bug, not the disclosed facts themselves.

| Metric | Result |
|---|---:|
| Expected initial category present anywhere | 69.76% |
| Expected initial exact label present anywhere | 60.90% |
| Any authored plausible-initial label present | 68.30% |
| GPT-5 matcher: generated question judged answerable by hidden fact | 48.70% (467/959) |
| Expected final category present, among matched | 79.02% |
| Expected final exact label present, among matched | 49.43% |
| Expected final category already present **initially** | 54.22% of all rows |
| Expected final exact label already present **initially** | 29.93% of all rows |
| Expected final category gained / lost after re-classification, among matched | 12 / 13 (net −1) |
| Expected final exact label gained / lost after re-classification, among matched | 24 / 31 (net −7) |

Given the root cause above, "matcher coverage" (48.70%) should be read as
*"the matcher judged the generated question answerable by the fact"* — a
real measurement of question-generation quality — while the gained/lost
rows should be read as *"resampling noise from a classifier call that never
received the fact,"* not as evidence about whether disclosed facts help or
hurt FETCH's reasoning. The matcher coverage number is unaffected by the
bug (the matcher is a separate, correctly-implemented call in the study
harness) and remains a valid, comparable-to-v1 measurement; see the
"Coverage" note below.

**Coverage moved from 71.6% (v1, GPT-4.1 matcher) to 48.7% (v2, GPT-5
matcher).** This is not necessarily worse — GPT-5 is judging whether a
disclosure about, say, a recorded easement or an ERISA plan source *directly*
answers a generated question, and v2's disambiguating facts are deliberately
subtler than v1's role reveals. A stricter, more accurate matcher plausibly
explains part of the drop; some may also be legitimate under-elicitation by
FETCH's question generator. The `matcher_log.jsonl` reason field (logged for
every call) lets this be separated on the human audit pass.

## By mechanism (M1–M4)

| Mechanism | n | Match coverage | Final exact among matched | Exact gained/lost |
|---|---:|---:|---:|---:|
| M1 core-vs-secondary-issue | 122 | 53.28% | 40.43% | see per-case CSV |
| M2 specific-vs-general fallback | 197 | 44.67% | 50.72% | see per-case CSV |
| M3 missing procedural/institutional fact | 572 | 49.30% | 51.94% | see per-case CSV |
| M4 competing framings of one dispute | 68 | 47.06% | 42.31%* | see per-case CSV |

\* `M4` is additionally depressed by the `reputation_harm_type` outage window
described below; treat with extra caution.

## Data-quality caveat: a transient outage window

Two boundary families — `reputation_harm_type` (26 rows) and
`vehicle_purchase_source` (28 rows), 54 rows total, ~5.6% of the run —
returned an empty classifier label set on nearly every case (25/26 and
28/28 respectively), each with `error: None` and no orchestrator error,
unlike the scattered, roughly-24%-of-cases timeout noise seen elsewhere in
the run. These two families are contiguous blocks in the candidate file, so
at concurrency 4 they were dispatched within a narrow wall-clock window
each; the pattern is consistent with a short Azure GPT-5 outage or
throttling episode rather than anything about the candidate content. All
other families show normal, non-systematic empty-label rates. These two
families' numbers should be treated as unreliable pending a re-run limited
to just those rows (not a full second official run — see the root-cause
section for why a full rerun wasn't pursued).

## Safety-sensitive rows

The 115 safety-sensitive rows (custody-safety, protective-order-relationship,
some immigration and criminal-posture scenarios) show a **materially worse**
final-category outcome than the rest of the set:

| | n | Match coverage | Final category among matched | Final exact among matched |
|---|---:|---:|---:|---:|
| Safety-sensitive | 115 | 54.78% | **62.50%** | 40.00% |
| All other rows | 844 | 47.87% | 81.17% | 50.65% |

This reproduces, on new material, the paper's and v1's central safety
concern: FETCH's question generator engages more readily with
safety-relevant disambiguation (higher match rate) but the classifier lands
on the safety-specific label markedly less often. Given the root cause
above, part of this gap is now explained mechanically — the classifier
never receives the safety disclosure either — but the *initial*-call
numbers (before any follow-up) are unaffected by the bug and still show
FETCH's baseline handling of safety-adjacent openings is weaker than the
rest of the set (compare `expected_final_category_present_initially_pct`
across groups in `runs_v2/pooled_by_safety_sensitive.csv`).

## Quoted evidence

**The paper's hardest failure mode, reproduced on new material — now with a
confirmed mechanical cause.** FETCH's question generator asks exactly the
right disambiguating question, the matcher correctly judges that the hidden
fact answers it, and the final classification is unchanged:

> Opening query: "A person keeps pounding on my door late at night and
> shouting at me. I want it to stop."
>
> Generated question: "Who is the person to you?"
>
> Hidden fact: "It's my child's father. We lived together until last year,
> and I want him kept away from me."
>
> Matched: yes — "Who is the person to you?"
>
> Final labels: `General Litigation > Stalking Orders` (unchanged)
>
> Expected: `Family Law > Restraining Orders`

Given the root cause, this is not evidence that FETCH weighed the disclosed
relationship and decided it wasn't decisive — the reclassification call
never received it. The observed behavior (question generation succeeds,
final classification is unmoved) is the same shape as the v1/`On Wednesdays`
`legacy_025` failure, but the mechanism is now understood precisely: the
question generator and the relevance matcher are working; the
answer-consumption step is not wired up for this classifier family.

**Apparent "flips" that should not be read as causal successes.** These two
cases show the expected label absent in call 1 and present in call 2:

> Opening query: "My bank has been taking money out of my account in ways I
> never agreed to."
>
> Initial labels: `Consumer Law > Banking`
>
> Hidden fact: "The withdrawals trace to a loan someone opened in my name
> with a fake ID..."
>
> Final labels: `Consumer Law > Banking`, `Consumer Law > Identity Theft`

> Opening query: "The city denied my application and gave me two sentences
> of explanation after eight months of waiting."
>
> Initial labels: `Administrative Law > General (Local/Municipal)`
>
> Hidden fact: "It's a variance application — I want to build an accessory
> dwelling my lot's zoning doesn't allow..."
>
> Final labels: adds `Real Property > Land Use/Zoning`

Both looked, before the root-cause analysis, like the disclosed fact
resolving genuine ambiguity. Given that GPT-5 never received either
disclosed fact, the more accurate description is: **GPT-5 was asked the
identical opening-query-only prompt twice, and on the second sample
happened to include the label a human would expect** — plausibly because
the opening query itself carries enough latent signal for the label to be
within the model's uncertainty band even without the disclosure, not
because the disclosure did anything. These remain useful as illustrations
of *output-level* volatility across repeated calls; they are not evidence
that the flip mechanism is working.

**A genuine matcher near-miss** (unaffected by the root-cause bug, since
matching happens before the reclassification call) — FETCH asked a related
but non-decisive question, and the GPT-5 matcher correctly declined to force
a match:

> Opening query: "I got a letter saying my disability claim was denied and I
> don't know what to do next."
>
> Generated question: "Who denied your disability claim?"
>
> Hidden fact: "I worked as a welder for 22 years and paid Social Security
> taxes the whole time before my back gave out." (SSD-routing fact)
>
> Matched: no

The generated question asks about the denying agency, not the work-history
fact the SSI/SSD boundary turns on — a legitimate case where the follow-up
*question* itself, not the matcher and not the reclassification bug,
under-elicited the disambiguating fact.

## Family-level extremes (n ≥ 15, `final_run_1`)

Lowest expected-exact-among-matched: `creditor_judgment_bankruptcy` (0%,
n=30, only 16.7% match coverage), `ip_protection_type` (0%, n=28),
`small_claims_vs_construction` (0%, n=44, only 6.8% coverage — very few
matched-with-answer cases, so this number is not statistically meaningful
as-is), `tax_dispute_route` (0%, n=16).

Highest: `ssi_vs_ssd` (92.6%, n=44, 77.3% coverage — the strongest-performing
family in the set, and the cleanest candidate for re-validating the fix),
`government_defendant` (85.7%, n=30), `estate_posture` (75.0%, n=34).

## Reproducing and extending this analysis

```bash
source /home/quinten/fetch/.venv/bin/activate
cd flip_experiment_v2
python analyze_runs.py                 # picks up results/final_run_1_*
```

After the planned human salience audit removes rows from
`candidates/flip_candidates_v2.csv`, re-run the same command (or pass
`--candidates <edited.csv>`) to regenerate every table above from the
surviving rows with no model calls repeated. Once the two pipeline bugs
above are fixed, re-running the classifier is the appropriate next step to
get a real read on the flip mechanism itself (this run's data cannot answer
that question).

## Detailed artifacts

- `runs_v2/summary.json` — machine-readable version of every number above.
- `runs_v2/pooled_by_{boundary_id,mechanism,flip_type,direction,safety_sensitive}.csv`
  — full per-group tables (33 boundary families).
- `runs_v2/final_run_1_20260718T002609Z/per_case_detail.csv` — every one of
  the 959 observations with initial/final label sets, matcher decision, and
  all derived flags.
- `results/final_run_1_20260718T002609Z/matcher_log.jsonl` — every matcher
  call's reasoning and token usage.
- `EXECUTION_LOG.md` — full run history, including the exact file/line
  citations for the root-cause finding.
