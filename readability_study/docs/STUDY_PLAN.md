# Does the nano→full switch actually improve FETCH's question screens?

**A paired, disclosure-blind readability & question-quality study of FETCH follow-up screens**

Status: active · Owner: Quinten Steenhuis · Harness: promptfoo + FETCH `ClassificationService` · Judges: DeepSeek-V4-pro + Claude Sonnet-5

---

## 1. Why this study exists

FETCH switched the OpenAI member of its classification ensemble (and the
semantic-merge model) from **gpt-5-nano** to **gpt-5.2 ("full")**. The switch was
made on the belief that the larger model writes better follow-up questions — but
that was never measured. This study fills that gap with a mechanical,
reproducible measurement.

**Research question.** Holding the rest of the ensemble constant
(gemini + mistral), does swapping the OpenAI member and the semantic-merge model
from nano to full measurably improve the *follow-up question screen* a user sees?

## 2. The reframe (what actually separates model tiers here)

For nano-vs-full, lexical and syntactic readability are probably **not** the
differentiator — the bigger model may even score *worse* on vocabulary
sophistication while being better overall. What separates model tiers on an
intake-question task is **grounding and question structure**:

- Does the question **presuppose facts** the applicant never gave?
- Does it ask **one thing or three** (double-barrel)?
- Can a **simulated respondent** actually answer it from what they know?

The metric battery is weighted accordingly: **metrics 1–4 are the study; 5–10 are
decoration** we run because the pipeline is already there.

## 3. Design

- **Inputs.** 373 unique, human-vetted problem descriptions
  (`scenarios/gold_consensus_373.csv`, the gold-label consensus set). Real intake
  language, deduplicated, each carrying a gold category for grounding checks.
- **Paired generation.** Each problem description → one screen per arm. Same
  input, two arms — the single decision that makes a small study viable.
- **The two arms** (ensemble question generation; only the OpenAI member and the
  merge model change — "adjust the model selection twice"):

  | Arm | Ensemble generators | Semantic-merge model |
  |-----|--------------------|----------------------|
  | **nano** | **gpt-5-nano** + gemini + mistral | **gpt-5-nano** |
  | **full** | **gpt-5.2** + gemini + mistral | **gpt-5.2** |

  `keyword` and `spot` are omitted: they only cast label votes and never emit
  questions, so they cannot affect the screen.
- **Unit of analysis.** The **merged screen** = FETCH's top-3 follow-up questions
  after semantic merge (`resp.follow_up_questions`), produced by the real
  `ClassificationService.classify()` path. Metrics are computed per question and
  **aggregated to the screen with `max`, not mean** (one bad question spoils a
  screen).
- **Contamination guard.** When the arm-defining OpenAI member times out or
  errors, the screen silently degrades to a gemini+mistral-only screen. The
  harness captures per-provider failures and **retries** such screens; any that
  remain degraded are flagged (`member_failed`) and **excluded** from the paired
  comparison.

## 4. Metrics

### Tier 1 — the four that decide this (pre-registered primary)

| # | Metric | How |
|---|--------|-----|
| 1 | **Unverified-presupposition rate** | LLM lists what each question takes for granted; a separate call checks each against the problem statement. Count `UNKNOWN` + `CONTRADICTED`. |
| 2 | **Double-barrel count** | LLM: "rewrite as the minimum number of questions each with exactly one answer." Score = length of the list; >1 is a flag. |
| 3 | **Simulated-respondent accuracy** | A persona with ground-truth facts answers the screen; score vs. truth, and record the `UNCLEAR` rate. |
| 4 | **Unintroduced hard vocabulary** | Content tokens with SUBTLEX/Zipf < 3, excluding words the applicant already used or that are glossed on-screen. |

### Tier 2 — cheap; run because the pipeline exists (exploratory)

| # | Metric | How |
|---|--------|-----|
| 5 | Max dependency length | spaCy parse, longest head–dependent arc |
| 6 | Agentless passive count | PassivePy, sentence-level, truncated-passive flag |
| 7 | Max surprisal | GPT-2 Small, peak per-word −log P |
| 8 | Screen load | total tokens + count of newly introduced entities per screen |
| 9 | Negation × conditional | binary: contains both a negation and an if/unless/except |
| 10 | Ambiguity via restatement variance | 5 plain-language restatements at temp>0; cluster by NLI entailment; count clusters |

## 5. Judges & rubric hygiene

- **Two judges from different families, both independent of the generation
  pipeline** (the generators are GPT + Gemini + Mistral): **DeepSeek-V4-pro** and
  **Claude Sonnet-5**, both via OpenRouter. This satisfies "don't grade a
  GPT-family output with only a GPT-family judge."
- **Blind.** Screens are presented to judges without arm labels, in randomized
  order.
- **Seeds.** 3 seeds for the stochastic LLM metrics (esp. #3, #10).
- **Known-bad calibration.** ~5% deliberately broken items are mixed into each
  rubric batch; if a judge doesn't flag them, that judge/metric is treated as
  broken for that batch.

## 6. Validity check (half a day, before trusting any number)

Take 20 screens and **degrade each on exactly one dimension** — insert an
unsupported definite NP (presupposition), coordinate two predicates into one
question (double-barrel), swap a common word for a rare one (vocabulary) — and
confirm the corresponding metric moves in the right direction and the others stay
put. This is the minimum viable validation that keeps a reviewer from asking
whether the numbers mean anything.

## 7. Analysis

- **Paired tests per metric:** McNemar for binary flags (2, 9, and thresholded
  1/4); Wilcoxon signed-rank for continuous metrics (1, 4, 5, 6, 7, 8, 10);
  accuracy delta for 3.
- **Effect sizes** reported alongside every p-value.
- **Multiplicity:** metrics 1–3 pre-registered as primary; everything else is
  exploratory with **Benjamini–Hochberg FDR** correction.
- **Plan for the null.** There is a real chance nano is fine on readability and
  differs only on grounding. We pre-specify a **smallest effect worth caring
  about (SESOI) = 5 percentage points** on the hard-flag rate and run a **TOST
  equivalence test**, so "nano is good enough" is a reportable result, not an
  absence of one.

## 8. Reading list (justifies the method choices)

1. **Lenzner (2014)**, "Are Readability Formulas Valid Tools for Assessing Survey
   Question Difficulty?" *Sociological Methods & Research* 43(4). — Why FK/formulas
   are weak at flagging known-bad questions (<50% success): the reason tiers 1 is
   weighted over lexical readability.
2. **Graesser, Cai, Louwerse & Daniel (2006)**, "QUAID." *Public Opinion
   Quarterly* 70(1). — Five survey-question flags with concrete operationalizations
   (mostly counts/lookups) behind metrics 1, 2, 8.
3. **Martínez, Mollica & Gibson (2022)**, "Poor writing, not specialized concepts,
   drives processing difficulty in legal language." *Cognition* 224. — Which legal
   features actually matter (center-embedding, rare jargon, passive) → metrics 4,
   5, 6.
4. **Sepehri, Mirshafiee & Markowitz (2023)**, "PassivePy." *Journal of Consumer
   Psychology* 33(4). — The passive-voice tool used in metric 6; note it was
   validated on consumer complaints, not questions.
5. **Oh & Schuler (2023)**, "Why Does Surprisal From Larger Transformer-Based
   Language Models Provide a Poorer Fit to Human Reading Times?" *TACL* 11. — Use
   **GPT-2 Small**, not a big model, for metric 7.

## 9. Reproducibility layout

```
readability_study/
  docs/STUDY_PLAN.md          # this document
  scenarios/                  # the 373-set + sampler
  harness/                    # FETCH generation bridge + runner + promptfoo config
  metrics/                    # metric implementations + judge harness
  analysis/                   # paired stats, equivalence tests, figures
  results/                    # raw screens, computed metrics, run provenance
```

Every arm's model selection, timeout, and provider list is recorded in each run's
`meta.json`. Caching is disabled end-to-end.
