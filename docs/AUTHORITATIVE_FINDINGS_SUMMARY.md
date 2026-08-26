# Authoritative findings summary

This document is the cross-study evidence index for the FETCH research
artifacts. Linked stage documents remain authoritative for detailed methods,
results, and reproduction.

**Evidence scope.** The index distinguishes (1) results reproducible from the
committed scripts and data in this public repository and (2) methodological
precursors from the private FETCH application repository. Private-repository
artifacts are not included and cannot be independently reproduced from this
repository; they are identified explicitly as prior-work context.

## Research questions mapped to evidence

| Research question | Evidence status | Headline evidence | Where |
|---|---|---|---|
| What makes a question good or bad? | **Partially answered by a multi-metric study** | The paired readability study (generated on 373 descriptions, scored on the 355 that survive deduplication) measures presupposition, double-barreling, respondent clarity/answerability, hard vocabulary, syntax, passive voice, surprisal, screen load, and conditional complexity. It reinforces that no single instrument is authoritative: DeepSeek and Claude agreed on only 21% of screens, and DeepSeek's apparent full-model grounding penalty disappeared under Claude. Older results likewise show a hard Dale–Chall gate and an LLM rubric diverging sharply. Human validation beyond the 29-pair Claude cross-check remains a limitation. | [Finding 6](#finding-6--nano-vs-full-question-screens-full-wins-on-coverage-not-per-question-readability); [Prior work §1](#1-readability--prompt-quality-experiments-private-repo-january-2026) |
| Can targeted prompting improve AI-generated questions? | **Yes, within the evaluated task** | Targeted prompt edits (explicit glossing, word-substitution list, anti-redundancy check, few-shot examples) raised the same 416-case eval's strict pass rate from 40.62% to 57.45% (+16.83pp) in one iteration; an earlier, less-targeted edit only moved it to 44.23%. | [Prior work §1](#1-readability--prompt-quality-experiments-private-repo-january-2026) |
| Do different AI models ask better questions? (nano vs. full) | **Yes for coverage; no robust per-question quality difference** | In a paired comparison scored on the deduplicated 355-narrative set, nano produced an empty screen in 85/348 paired cases (24.4%) versus 2/348 (0.6%) for full; 83 pairs were nano-empty/full-nonempty and none showed the reverse (McNemar p≈2×10⁻²⁵). When both arms asked, the second, cross-family judge found per-question quality essentially indistinguishable. Full screens were longer and denser. | [Finding 6](#finding-6--nano-vs-full-question-screens-full-wins-on-coverage-not-per-question-readability) |
| Can follow-up questions help improve classification vs. no follow-up? | **Yes, and the answer changed once a pipeline bug was fixed** | Pre-fix: net −7 exact-label change (looked like "no help/harm"). Two structural FETCH bugs meant GPT-5-family classifiers never actually received the disclosed answer on the second call. Post-fix, net **+181** (condition B) to **+220** (condition C) exact-label gains across 959 scenarios, confirmed stable across 6 reruns on a 200-case subsample (every run net +33 to +46). | [Finding 5](#finding-5--the-v2-disclosure-grounded-benchmark-the-decisive-post-fix-result) |
| Are digital twins evaluated? | **Not addressed** | No digital-twin artifact, design note, or experiment is included in the evidence base. | — |
| Can follow-up questions help non-legal classification? | **Not addressed** | Every study in both repos is legal-intake-specific (FETCH's taxonomy). No out-of-domain/non-legal replication exists. | — |

The sections below provide the evidence supporting each mapped research
question, including the labeling pipeline, FETCH retrieval accuracy, diagnostic
flip benchmarks, and question-screen comparison.

## Executive synthesis

The repository (both public data here and private-repo methodology history) supports six connected conclusions:

1. **The routing task is materially multi-label.** The source contains many descriptions with multiple independently meaningful legal issues. A single primary label is useful for routing, but it is not a complete representation of the problem.
2. **Annotation disagreement is concentrated at taxonomy boundaries.** Humans agree more than the model raters, and broad legal-domain agreement is stronger than exact specialist-route agreement.
3. **FETCH usually reaches the correct legal domain and often retrieves at least one exact route, but it is incomplete on multi-label scenarios and overpredicts.** Pooled retrieval was 99.2% for at least one correct top-level category and 95.3% for at least one exact sublabel; micro exact precision was 46.0%.
4. **Follow-up questions materially help classification in the post-fix
   pipeline.** The superseded 1,000-candidate `expanded_flip_experiment`
   reported a near-neutral result (47 gained / 48 lost category membership)
   under the same `GPT-5 + keyword` configuration later shown to omit disclosed
   answers from GPT-5-family reclassification calls. Its result is therefore
   treated as bug-affected resampling rather than evidence about disclosure
   value. The post-fix `flip_experiment_v2` produced net +181 to +220
   exact-label gains, with direction confirmed across six variability runs.
5. **A deterministic safety-net layer (screening protocols) adds a small, real, zero-downside rescue on top of the fixed LLM pipeline**, concentrated exactly in the safety/routing categories it targets (restraining orders, elder abuse, immigration consequences, third-party work injury) — about 1% of matched cases, isolated via a paired within-run comparison that holds LLM sampling constant.
6. **Switching the question-generation ensemble's OpenAI member and merge model from gpt-5-nano to gpt-5.2 fixes a large coverage failure, not a demonstrated readability failure.** Nano showed no questions on 24.4% of screens versus 0.6% for full. When both arms asked, their per-question quality was essentially tied under the independent Claude cross-check; full instead produced longer, denser, more information-rich screens.

The most defensible paper framing: **multi-label legal-intake routing is feasible at the broad-domain level; follow-up questions clearly help once the pipeline actually uses the answer; the full model reliably supplies questions that nano often omits; a deterministic backstop adds a small additional safety margin; and exact specialist routing remains limited by taxonomy overlap and incomplete elicitation.**

## Evidence hierarchy and scope

```text
431 reviewed source rows
  └─ 373 whitespace-normalized unique descriptions
       ├─ 114 stories with two eligible human annotations + three model annotations
       └─ 373-scenario consensus-gold FETCH evaluation

Diagnostic benchmark v1 (retired, bug-affected — see Finding 4 caveat):
200 legacy flip candidates + 800 workbook-grounded candidates
  └─ 1,000 candidates × 3 intended-fact runs = 3,000 observations (2026-07-14, pre-fix)

Diagnostic benchmark v2 (primary evidence for whether questions help):
959 Claude-authored disclosure-grounded scenarios, 33 boundary families
  ├─ pre-fix baseline (historical, same bug as v1)
  ├─ condition B: post-fix, 5-provider vote (2026-07-18)
  ├─ condition C: post-fix + PR #34 deterministic screening protocols (2026-07-18)
  └─ variability check: 3 reruns × 2 conditions on a fixed 200-case subsample (2026-07-19)

Paired question-screen study (primary evidence for nano versus full):
373 human-vetted opening descriptions × 2 arms = 746 generated screens
  ├─ gpt-5-nano vs. gpt-5.2 as OpenAI ensemble member + semantic-merge model
  ├─ Gemini + Mistral held constant; provider failures repaired rather than dropped
  ├─ deterministic readability/question-load metrics + blind DeepSeek judge
  └─ blind Claude cross-family check on 30 scenarios

Prior-work lineage (private repo only, not reproducible from this repo):
416-case follow-up-question readability/quality eval (Jan 2026, 2 experiments)
430-case label-selection/multi-issue eval (Apr 2026, 4 configurations)
200-scenario, 10-pair classification-flip pilot — direct ancestor of the 1,000-candidate v1 set
  (confirmed by matching schema and literal legacy_* scenario IDs carried into v1)
```

The canonical chronology is in
[`labeling_audit/REVIEW_AUDIT_TRAIL.md`](../datasets/d1_consensus_labels/labeling_audit/REVIEW_AUDIT_TRAIL.md).
The v2 flip benchmark is documented in
[`analysis/RESULTS.md`](../datasets/d2_synthetic_flip/analysis/RESULTS.md) and
the [D2 README](../datasets/d2_synthetic_flip/README.md).

- **Consensus-gold evaluation:** a retrieval/coverage benchmark against a conservative derived reference set.
- **Flip benchmarks (v1, v2):** stress tests of follow-up-question elicitation and post-answer classification.
- **Paired question-screen study:** a model-tier comparison of whether questions are produced and, conditional on nonempty screens, their readability and question quality; it does not measure downstream classification accuracy.
- **Reliability analysis:** agreement among the available raters, not agreement with an external legal ground truth.

## Finding 1 — The labeling pipeline exposes a real multi-label problem

The three independent model passes used the same detailed taxonomy, prompt schema, and validation logic. Their rank-1 exact-pair agreement was:

| Relationship before internal review | Rows | Share |
|---|---:|---:|
| All three agree | 353 | 81.9% |
| Exactly two agree | 70 | 16.2% |
| All three differ | 8 | 1.9% |

The resulting Stage 04 workbook is a defensible **primary routing** artifact, not evidence that each description has only one correct label. Full row-level record: [`final_review.json`](../datasets/d1_consensus_labels/labeling_audit/04_review/final_review.json).

The targeted cross-check of nine examples from the prior paper found four derived human-label corrections — rows 149, 188, 220, and 339. Stage 06 separately exposed 78 exact-pair disagreement rows. See the [human-label review](../datasets/d1_consensus_labels/labeling_audit/05_human_label_review/README.md) and [disagreement analysis](../datasets/d1_consensus_labels/labeling_audit/06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md).

Subsequent audits quantify why the one-label interpretation is insufficient:

- The broad top-three evidence audit placed **156/431 rows** in a high-recall evidence queue. See [the multilabel findings](../datasets/d1_consensus_labels/labeling_audit/07_multilabel_audit/MULTILABEL_FINDINGS.md).
- The fresh GPT-5.2 two-label audit found **90 rows** with two supported labels, **39 primary-label change candidates**, **12 uncertain primary assessments**, and a **132-row union review queue**. See [the two-label audit findings](../datasets/d1_consensus_labels/labeling_audit/08_gpt52_two_label_audit/TWO_LABEL_AUDIT_FINDINGS.md).
- The cap-free Stage 10 workflow allows zero through four labels; seven rows needed three or four candidate issues. See [the four-label review](../datasets/d1_consensus_labels/labeling_audit/10_four_label_human_review/).

The consensus reconstruction contains **238 one-label, 124 two-label, 9 three-label, and 2 four-label** unique scenarios, provenance-tagged: 259 sets from three-model plus internal consensus, 61 from exact human-reviewer agreement, 53 from human decisions corroborated by ≥2 models. See [the consensus README](../datasets/d1_consensus_labels/consensus/README.md).

## Finding 2 — Agreement is better for humans and broad domains than for exact routes

On the 114 descriptions with two eligible human annotations:

| Comparison | Mean Jaccard distance | α-Jaccard | Exact set match |
|---|---:|---:|---:|
| Humans | 0.251 (95% CI 0.198–0.305) | 0.744 (0.687–0.796) | 61/114 (53.5%) |
| LLMs | 0.362 (0.320–0.404) | 0.632 (0.586–0.672) | 125/342 (36.5%) |
| Human–LLM | 0.370 (0.330–0.411) | 0.623 (0.579–0.660) | 250/684 (36.5%) |
| All five | 0.355 (0.318–0.393) | 0.638 (0.598–0.673) | 436/1,140 (38.2%) |

Intervals are story-bootstrap percentile intervals (2,000 samples). Supplemental ICC: label-count ICC(A,1) = **0.328** (95% CI 0.216–0.421), conditional exact-pair incidence ICC(A,1) = **0.279**, conditional top-level incidence ICC(A,1) = **0.390**.

Four recurring ambiguity mechanisms explain most disagreement: (1) core problem vs. every visible secondary issue, (2) specific route vs. general fallback, (3) missing procedural posture/party role, (4) competing framings of one dispute. These four mechanisms are exactly what D2's 33 boundary families were built to stress-test (M1–M4 in that benchmark). Repeated review found 30/36 (83.3%) duplicate story/reviewer pairs received the same set. Largest boundary problems: General Litigation, Labor & Employment, Business & Corporate, Real Property, Debtor/Creditor. Full detail, illustrative disagreements: [consensus findings](../datasets/d1_consensus_labels/consensus/FINDINGS.md).

## Finding 3 — FETCH has high broad-domain retrieval and high any-exact retrieval, but incomplete multi-label recall and substantial overprediction

Two independent replicates ran the full five-classifier FETCH vote ensemble (GPT-5.2, Gemini, Mistral, keyword, SPOT — **note: this evaluation predates and is unaffected by the follow-up-answer bug in Finding 5, since it evaluates only the single opening-query classification, not the two-step follow-up mechanism**) against 373 unique consensus scenarios, Promptfoo and provider caches disabled.

| Outcome tier | Run 1 | Run 2 | Pooled |
|---|---:|---:|---:|
| All gold exact sublabels retrieved | 80.4% | 82.3% | **81.4%** |
| Some, but not all | 14.5% | 13.4% | **13.9%** |
| Correct top-level only | 4.0% | 3.8% | **3.9%** |
| No correct top-level category | 1.1% | 0.5% | **0.8%** |

Across 746 run-observations: **95.3%** ≥1 exact gold sublabel; **99.2%** ≥1 correct top-level category; exact gold-instance precision/recall/F1 = **46.0% / 84.5% / 59.6%**; mean graded retrieval score **93.0%**; strict exact-set match only **10.5%** (FETCH overpredicts — returns extra plausible labels).

All-exact retrieval fell sharply with gold-set size: 95.2% (one label) → 59.7% (two) → 33.3% (three) → 0/4 (four, though ≥1 exact route was still retrieved in every four-label case). Cross-run stability: any-exact status stable 96.5%, full four-tier outcome stable 94.9%, predicted-set Jaccard 86.3%.

Reproduction and caveats: [FETCH gold-accuracy findings](../datasets/d1_consensus_labels/consensus/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md). The classifier used the full GPT-5.2 deployment; no mini/nano model was substituted in this evaluation. The nano-vs.-full comparison in Finding 6 concerns follow-up-question generation and semantic merging, **not classification accuracy**.

The inherited 416-case PromptFoo suite (a separate, older follow-up-question quality baseline — see also [Prior work §1](#1-readability--prompt-quality-experiments-private-repo-january-2026)) remained **81/416 passed (19.47%)** after repair; only 240 descriptions overlap the consensus-gold population, so it is not part of the primary accuracy estimate.

## Finding 4 — The 1,000-candidate v1 hidden-fact benchmark: superseded, likely bug-affected

**This finding is retained for the audit trail but its headline "flip" numbers should no longer be presented as the paper's primary follow-up-question result — see Finding 5.**

The v1 benchmark (`expanded_flip_experiment/`) combined 200 legacy candidates (themselves descended from an even earlier 200-scenario, 10-pair pilot — see [Prior work §3b](#3-classification-flip-precursor-and-model-comparison-private-repo-aprilmay-2026)) with 800 new workbook-grounded candidates, run 2026-07-14, three official runs, 3,000 intended-fact observations, **using "GPT-5 plus the deterministic keyword classifier"** as its frozen official configuration (`expanded_flip_experiment/README.md`).

Pooled three-run result (as originally reported):

| Metric | Pooled result |
|---|---:|
| Expected initial exact label present, scorable cases | 77.57% |
| Matcher-accepted hidden-fact question | 71.63% |
| Expected final category present among matched | 84.64% |
| Expected final exact label present among matched | 56.29% |
| Expected final category newly **added** after the fact | 47/2,149 = 2.19% |
| Expected final exact label newly **added** after the fact | 122/1,892 = 6.45% |
| (Category lost: 48; exact label lost: 102 — nearly symmetric with the additions) | |

**Why this result is suspect:** D2's pre-fix baseline used the same `gpt-5 +
keyword` classifier configuration and showed the same near-neutral shape (24
gained, 31 lost; net −7). That baseline exposed two structural defects in
FETCH's `ClassificationService`: the GPT-5-family Responses API path omitted
`followup_answers` from the successful reclassification call, and a provider
filter also excluded Gemini and Mistral. Because v1 used the same affected
classifier family and provider mix before the fix, its 47-added/48-lost pattern
is likely the same resampling artifact rather than evidence that disclosed
facts are neutral. V1 was not rerun post-fix, so this remains a strong inference
from matched configuration and failure shape, not a second confirmed
measurement. See [why v1 was retired](../datasets/d2_synthetic_flip/README.md#why-v1-was-retired).

What remains usable from v1 without this caveat: the **matcher coverage** numbers (question-generation/matching is a separate call, unaffected by the reclassification bug), and the **domestic-violence-specific finding** that only 44.31% of hidden-DV question sets explicitly probed safety/abuse/violence/threats/control despite 78.04% matcher acceptance — a question-generation gap, not a reclassification gap, and structurally distinct from the bug above. The superseded v1 repository is not included in this publication repository.

## Finding 5 — The v2 disclosure-grounded benchmark: the decisive post-fix result

Dataset D2 replaced v1 with 959 Claude Fable 5-authored scenarios (33 boundary families) whose hidden facts are **case facts** (procedural posture, institutional identity, amounts, safety context) rather than v1's party-role reversals — real users know which side of a dispute they're on, so role-reversal flips rarely occur at intake. Every scenario is grounded in the Stage 11 gold-label human-disagreement mechanisms (Finding 2's M1–M4). Full design rationale: [D2 README](../datasets/d2_synthetic_flip/README.md).

### The bug, and why it mattered

After the first official run (`final_run_1`, 2026-07-18 00:26 UTC), gained/lost exact labels were small and roughly symmetric (24 gained, 31 lost, net −7) — not what a decisive disclosed fact should look like. Tracing directly through FETCH's source found:

1. **`app/providers/openai.py:177-179`** — for GPT-5-family models, the Responses API `input` is built from only the opening query; `followup_answers` is never referenced on the normal (successful) code path. **The second, post-disclosure classification call was byte-identical to the first.**
2. **`app/services/classification_service.py:1250-1261`** — the refinement-call provider filter (`isinstance(p, LLMClassifierProvider)`) was meant to exclude only keyword/SPOT providers, but also excludes Gemini and Mistral (neither subclasses `LLMClassifierProvider`), collapsing a 2-provider vote to 1 for this study's config.

Both were fixed on FETCH branch `fix/followup-context-and-provider-mix`, commit `41585d0`, with 107 passing regression tests.

### Post-fix result: do follow-up questions help?

Two fully independent 959-case runs, one per condition (5-provider vote: gpt-5, gemini, mistral, keyword, spot on the opening call; gpt-5, gemini, mistral on the follow-up call):

| Metric | Pre-fix baseline | Condition B (fixes only) | Condition C (fixes + screening protocols) |
|---|---:|---:|---:|
| Expected initial exact label present anywhere | 60.90% | 83.21% | 83.73% |
| Matcher: question answerable by hidden fact | 48.70% | 72.26% | 72.68% |
| Expected final exact label present, among matched | 49.43% | 88.56% | 91.44% |
| Exact label **gained** after re-classification | 24 (6.90%) | 194 (36.40%) | 228 (38.26%) |
| Exact label **lost** after re-classification | 31 | 13 | 8 |
| **Net gained − lost** | **−7** | **+181** | **+220** |

**Primary interpretation:** follow-up questions clearly help once the pipeline
uses the disclosed answer. Post-fix, gains outnumber losses about 15:1 (B) to
28:1 (C), and matched-case final accuracy rises from 49% to 89–91%.
Safety-sensitive rows (n=115) show zero losses in either post-fix condition (37
gained/0 lost in B, 41/0 in C), with final exact accuracy of 89.7% (B) and 93.8%
(C) among matched cases.

One caveat: condition B's five-provider mix also changed alongside the fix
relative to the two-provider pre-fix configuration. The pre-fix-to-post-fix
difference therefore compares complete pipeline configurations and does not
isolate the fixes' effect size.

### Does the deterministic screening protocol (PR #34) add anything beyond the fix?

Condition C merges FETCH PR #34's six deterministic screening rules (`family_safety`, `employment_retaliation`, `third_party_work_injury`, `elder_exploitation`, `immigration_consequences`, police/government) onto the fix branch. The clean test is a **paired, within-run** comparison — `effective_categories` (screening-aware) vs. raw model vote, on identical model outputs:

| | Count |
|---|---:|
| Matched cases with a final answer | 596 |
| Correct via screening-aware `effective_categories` | 545 |
| Correct via raw model vote alone | 539 |
| **Rescued** by the screening protocol | **6** |
| **Regressed** (sanity check) | **0** |

Small (~1% of matched cases) but real and zero-downside, concentrated exactly in the target categories (restraining orders, elder abuse, immigration, third-party work injury). **Bottom line: the LLM vote (once it correctly receives the disclosed answer) does 90%+ of the work; the deterministic layer is a clean, one-directional safety net, not a general accuracy gain.**

### Variability check: is any of this sampling noise?

Both headline comparisons above are single runs. A fixed, family-stratified 200-case subsample (seed 42) was run 3× per condition:

| Run | Final exact accuracy, among matched | Gained | Lost | Net |
|---|---:|---:|---:|---:|
| B1/B2/B3 | 87.88% / 87.13% / 90.53% | 37/39/37 | 4/6/2 | **+33/+33/+35** |
| C1/C2/C3 | 93.28% / 92.80% / 90.35% | 45/48/49 | 2/2/3 | **+43/+46/+46** |

Every one of 6 runs lands strongly net-positive, matching the official runs' direction and nowhere near the pre-fix baseline's net −7. On the net-gained-minus-lost metric, B-vs-C separation is complete across all 9 cross-run pairings. `cache_enabled: False` was verified as a full bypass by direct inspection of `ClassificationService`, ruling out caching as a confound. The B-vs-C *accuracy* gap (not gained/lost) is directionally consistent (C mean 92.14% vs. B mean 88.51%) but not airtight run-by-run with only 3 runs/condition — the paired within-run comparison above remains the more decisive evidence for the screening protocol specifically.

Full detail, quoted evidence, family-level breakdowns, and the safety-sensitive-rows gap: [D2 results](../datasets/d2_synthetic_flip/analysis/RESULTS.md).

### Validation limit and extension

Candidates are Claude-authored and marked
`claude_authored_awaiting_human_salience_audit`; they have not received an
independent human salience audit. `analyze_runs.py` can re-derive every table
after audited rows are pruned without repeating model calls.

## Finding 6 — Nano vs. full question screens: full wins on coverage, not per-question readability

The completed `readability_study/` is a paired, disclosure-blind comparison on the same **373 human-vetted opening descriptions** (746 generated screens), scored on the **355** that survive deduplication to D1. The two arms differ only in whether the OpenAI ensemble member and semantic-merge model use **gpt-5-nano** or **gpt-5.2**; Gemini and Mistral are held constant, while keyword and SPOT are omitted because they do not emit questions. The study uses the real `ClassificationService.classify()` path with caching disabled. Provider failures were repaired rather than dropped (103 reduced to 11); the remaining Azure content-filter failures arose from the input text itself and were concentrated in the same small set of scenarios across arms.

### Coverage is the decisive model difference

| Outcome | Nano | Full |
|---|---:|---:|
| Screens with zero questions | **85/348 (24.4%)** | **2/348 (0.6%)** |
| Mean questions per screen | **≈1.9** | **≈2.9** |

The paired asymmetry is extreme: **83 scenarios were nano-empty/full-nonempty, with 0 in the reverse direction** (McNemar p≈2×10⁻²⁵). Instrumented diagnostic reruns explain the mechanism: the OpenAI provider returned zero questions on **87%** of nano calls versus **3%** of full calls; shared Gemini and Mistral providers were also silent on roughly half their calls and therefore did not reliably backfill nano. For a system whose follow-up screen exists to elicit missing facts, the important gpt-5.2 advantage is reliably asking something at all.

### When both arms ask, there is no robust per-question quality winner

On the 273 pairs where both arms produced questions, the automated DeepSeek judge rated full slightly worse on presupposition and respondent clarity/answerability, with no difference in double-barreling. That apparent disadvantage **did not replicate** in the blind 30-scenario Claude cross-check: Claude found nano and full statistically indistinguishable on per-question quality. Judge agreement was only **22% of screens**, with especially large differences in double-barrel flag rates (about 83% for DeepSeek versus 5% for Claude), because DeepSeek systematically treated menu/option questions as double-barreled. The defensible conclusion is **per-question parity**, not that either tier writes better-grounded questions.

Judge-free exploratory metrics show a real tradeoff: full screens contained more tokens (median 43 vs. 29), introduced more entities (median 1 vs. 0), had slightly longer maximum dependency spans (18 vs. 16), and had higher maximum GPT-2 surprisal (16.5 vs. 15.2 bits), all FDR-significant. Agentless passive voice and negation-by-conditional complexity did not differ. Full therefore asks **more and denser** questions: greater elicitation coverage and information content at some cost in reading load.

**Bottom line:** keep the switch to gpt-5.2, but justify it by question coverage. Do not claim that full produces more readable or better-grounded individual questions. This study also strengthens the broader methodological warning from the older Dale–Chall work: readability and question quality require multiple instruments and cross-family validation; a single formula or LLM judge can produce a misleading conclusion. Full methods and results: [results](../studies/readability/analysis/RESULTS.md), [study plan](../studies/readability/docs/STUDY_PLAN.md), and [README](../studies/readability/README.md).

## Prior work (private repo, methodology precursors not in this public repo)

The following work predates and motivated the public-repository studies. Its
artifacts remain in private FETCH research records and are **not included in or
reproducible from this repository**. It is summarized only as methodological
lineage for the flip benchmark and question-quality studies.

### 1. Readability / prompt-quality experiments (private repo, January 2026)

A fixed 416-case eval combined a hard mechanical **Dale–Chall readability gate** (max grade 7.9) with **LLM-judge rubrics** (`followup_relevant`, `followup_jargon_appropriate`, via `gpt-5-nano`) and a sentence-length check.

| Stage | Change | Pass w/ Dale–Chall | Pass w/o Dale–Chall | Dale-only failures |
|---|---|---:|---:|---:|
| Baseline | — | 169/416 (40.62%) | 346/416 (83.17%) | 177 |
| Experiment 1 | Generic plain-language / 6th-grade guidance added to prompts | 184/416 (44.23%) | 349/416 (83.89%) | 165 |
| Experiment 2 | Explicit glossing rule, word-substitution list, anti-redundancy check, few-shot good/bad examples | **239/416 (57.45%)** | — | 135 |

The central finding is a measurement disagreement: cases failing only
Dale–Chall consistently passed both LLM rubrics despite Dale–Chall grades of
9–16, above the 7.9 cutoff. Non-Dale failures were dominated by unglossed
jargon or acronyms (about 89% in Experiment 1) and redundant questions.
Generic plain-language edits slightly increased non-Dale failures (55→67)
while improving Dale–Chall; explicit glossing, substitution, anti-redundancy,
and few-shot interventions produced the larger gain. A later human A/B
preference exercise compared gpt-5-nano, gpt-5, and gpt-5.2 across 416 cases,
but its workbook outcomes have not been extracted. Finding 6 provides the
independently reproducible nano-versus-full comparison; broader human preference
labeling would strengthen the per-question-quality inference.

### 2. Label-selection / multi-issue experiments (private repo, April 2026)

A separate 430-case eval (`selection_eval.yaml`) tested the classifier's label-selection/merge stage — not follow-up-question wording — specifically its ability to preserve a second, competing legal issue rather than collapsing to one dominant category:

| Configuration | OSB accuracy (419 cases) | Targeted multi-issue cases (11) |
|---|---:|---:|
| Baseline (context-aware) | 371/419 (88.5%) | 7/11 (63.6%) |
| Proposal 1: adaptive window | 368/419 (87.8%) — regression | 8/11 (72.7%) |
| Proposal 2: multi-issue diverse | 381/419 (90.9%) | 8/11 (72.7%) |
| **Proposal 3: singleton rescue (adopted)** | **388/419 (92.6%)** | **10/11 (90.9%)** |

Widening the label window indiscriminately (Proposal 1) improved multi-issue recall but regressed the main benchmark; the adopted approach (Proposal 3) only intervenes when a prompt looks mixed *and* the selected slate still duplicates one top-level category, improving both axes simultaneously. This work is the direct upstream precondition for scenarios (in both flip benchmarks) where a follow-up should surface a second, competing category — and the one remaining targeted failure (a mixed civil/criminal/government prompt) reflects weak administrative-law signal generation, a distinct root cause from label-slate sizing.

### 3. Classification-flip precursor and model comparison (private repo, April/May 2026)

The direct, confirmed ancestor of `expanded_flip_experiment` (v1) is a 200-scenario, 10-swap-pair classification-flip pilot (`followup-study-paper-repo/results/followup_experiment_summary.md`), not itself present in this public repo but confirmed via matching CSV schema and literal `legacy_*` scenario IDs carried forward into v1's 1,000-candidate set:

- Initial classification correct: 154/200 (77.0%); question matched hidden fact: 138/200 (69.0%); of matched, final correct: 90/138 (65.2%).
- Outcome matrix (matched, n=138): 72 correct→retained, 26 correct→unchanged, **4 correct→degraded**, **18 wrong→rescued**, 18 wrong→still wrong. **Net +14, a 4.5:1 rescue-to-degrade ratio** — this pilot already found the same qualitative direction (questions help more than they hurt) that `flip_experiment_v2` later confirmed at scale, though it predates and is structurally distinct from the GPT-5-family bug found in the 2026-07 work (it used a different provider/harness, `two_step_followup_provider.py` with a `FollowUpAnswer` field — whether it shares the same bug was not independently verified here).
- Per-pair heterogeneity previewed exactly the failure modes the v2 benchmark was designed around: `domestic_violence` had 100% initial accuracy but only **10% question coverage** (the system rarely asks about abuse history at all); `criminal_vs_restraining` had 0% initial accuracy and 95% coverage but only 15.8% final accuracy; `employment_admin` was worst on both axes.

## Claims supported by the evidence

- "Against the conservative consensus set, FETCH retrieved at least one exact route in 95.3% of run-observations and at least one correct top-level domain in 99.2%, but complete retrieval declined sharply as the number of gold issues increased."
- "Follow-up questions materially improve exact-label classification accuracy once the pipeline correctly incorporates the disclosed answer: net exact-label gains of +181 to +220 across 959 disclosure-grounded scenarios, confirmed stable across 6 independent reruns, versus a near-neutral net −7 when a confirmed answer-consumption bug is present."
- "A deterministic screening backstop rescues a further ~1% of matched cases with zero regressions, concentrated in safety- and routing-sensitive categories, on top of the fixed LLM pipeline."
- "In a paired comparison scored on the deduplicated 355-narrative set, switching the question-generation ensemble's OpenAI member and merge model from gpt-5-nano to gpt-5.2 reduced empty follow-up screens from 24.4% (85/348) to 0.6% (2/348); when both arms asked questions, an independent cross-family judge found no robust per-question quality difference."
- "Full-model screens are longer and denser than nano screens (including median 43 vs. 29 content tokens), so the switch trades higher elicitation coverage and information content for greater reading load; it should not be characterized as a demonstrated readability improvement."
- "Targeted, evidence-driven prompt engineering (explicit jargon-glossing rules, word-substitution lists, anti-redundancy checks, few-shot examples) nearly doubled question-quality pass rates on a fixed eval (40.62%→57.45%), while generic 'use plain language' instructions alone produced a much smaller gain and did not reduce jargon-specific failures."
- "Readability and question-quality instruments disagree substantially: older
  Dale–Chall-only failures were judged clear by an LLM rubric, while the paired
  question-screen study's two LLM judges agreed on only 22% of screens.
  Conclusions should therefore use multiple metrics and cross-family or human
  validation rather than a single formula or judge."

The evidence does **not** support:

- Any claim about digital twins (no work exists).
- Any claim about non-legal-domain follow-up-question benefit (no work exists; every study here is legal-intake-specific).
- Any claim that full produces more readable, clearer, or better-grounded individual questions than nano. The robust advantage is coverage; per-question quality was essentially tied in the Claude cross-check, and full screens were objectively denser.
- Treating the v1 1,000-candidate flip study's 47-added/48-lost result as a valid neutral finding — it very likely shares v2's pre-fix bug and should be described as superseded, not corroborating.
- A completed human salience audit of the 959-scenario v2 candidate set.
- A rules-versus-AI-prompt comparison for domestic-violence screening
  specifically. The closest evidence is v1's 44.31% explicit-safety-probe
  finding and v2's safety-sensitive-rows breakdown; both test FETCH's existing
  behavior rather than a designed rules-versus-prompt comparison.

## Reproduction map

| Evidence | Parent document | Reproduction |
|---|---|---|
| Silver labels and chronology | [D1 audit trail](../datasets/d1_consensus_labels/labeling_audit/REVIEW_AUDIT_TRAIL.md) | `python scripts/create_silver_labels.py ...`; `python scripts/build_reviewed_silver.py` |
| Consensus gold construction | [consensus README](../datasets/d1_consensus_labels/consensus/README.md) | `python scripts/build_gold_consensus.py` |
| Five-rater agreement | [agreement methods](../datasets/d1_consensus_labels/consensus/AGREEMENT_METHODS.md) | `python scripts/analyze_gold_rater_agreement.py` |
| FETCH consensus-gold evaluation | [accuracy methods](../datasets/d1_consensus_labels/consensus/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_METHODS.md) | `pytest -q tests/test_analyze_fetch_gold_accuracy.py`; `python scripts/analyze_fetch_gold_accuracy.py ...` |
| v1 expanded flip benchmark (superseded, see Finding 4) | Not included | Historical only |
| v2 disclosure-grounded flip benchmark | [D2 README](../datasets/d2_synthetic_flip/README.md) | `python datasets/d2_synthetic_flip/run_direct.py --label <name> ...`; `python datasets/d2_synthetic_flip/analyze_runs.py` |
| Screening-protocol marginal contribution | [D2 results](../datasets/d2_synthetic_flip/analysis/RESULTS.md#condition-b-vs-c-does-the-screening-protocol-add-anything) | `python datasets/d2_synthetic_flip/analyze_screening_contribution.py` |
| Variability / sampling-noise check | [D2 results](../datasets/d2_synthetic_flip/analysis/RESULTS.md#variability-is-this-llm-sampling-noise) | `python datasets/d2_synthetic_flip/build_variability_sample.py`; rerun `run_direct.py`/`analyze_runs.py` on the fixed subsample |
| Nano-vs.-full question-screen study | [readability results](../studies/readability/analysis/RESULTS.md) | See the [readability README](../studies/readability/README.md) |

The included verification record is the [D2 execution log](../datasets/d2_synthetic_flip/analysis/EXECUTION_LOG.md), including the bug's exact file/line citations. The superseded v1 verification record is not included.

## Evidence hierarchy for synthesis

1. Consensus-gold evaluation as the main retrieval result (Finding 3).
2. Agreement analysis as the annotation/reliability result (Finding 2).
3. The v2 flip benchmark's post-fix result as the primary "do follow-up questions help" experiment (Finding 5) — lead with this, not v1, and disclose the bug/fix as part of the methods narrative since it changed the paper's own conclusion.
4. The nano-vs.-full question-screen experiment (Finding 6) as the model-comparison result: emphasize the decisive coverage gain, per-question parity, density tradeoff, and two-judge disagreement.
5. The screening-protocol comparison as a secondary, smaller-effect-size result (Finding 5, condition B vs. C).
6. The private-repo prior work (readability prompt-engineering, label-selection tuning, the 200-scenario flip pilot) as methodology-evolution/prior-work narrative, not as headline results — it motivated and was superseded by the public-repo work above.
7. Research extensions: broader human validation of the
   readability/question-quality metrics, extraction of the older human
   preference workbooks, evaluation of lower-density full-model prompts, a
   human salience audit of the 959 D2 candidates, digital twins, and
   non-legal-domain replication.

Interpretation depends on preserving these distinctions: top-level versus
exact-subcategory routing; at-least-one-label versus complete multi-label
retrieval; matcher coverage versus explicit fact-sensitive questioning;
final-label presence versus a label newly added after disclosure; and a
classifier that receives the disclosed answer versus one that, as in v1 and
the v2 pre-fix baseline, silently does not.
