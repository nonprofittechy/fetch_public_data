# Authoritative findings summary

**Status:** consolidated on 2026-07-19. This revision supersedes the 2026-07-17 version: it folds in the post-fix `flip_experiment_v2` results (a pipeline-bug discovery and fix that flips the paper's central "do follow-up questions help" answer), adds a section mapping every finding to the current paper outline's research questions, and adds a companion prior-work section describing methodology precursors that live in the private FETCH repo rather than here. The linked stage documents remain the detailed methods and evidence records; this file is the cross-study index for paper drafting.

**Two-repo provenance note.** This document indexes two things: (1) results produced *in this public repo* (`publishable-repo`), which are reproducible from the committed scripts/data here, and (2) prior-work context from the *private* FETCH application repo (`/home/quinten/fetch`, plus a satellite snapshot `/home/quinten/fetch/followup-study-paper-repo`), cited here only as narrative/methodological lineage — those artifacts are not included in this repo and are not independently reproducible from it. Section headers say which is which.

## Research questions, mapped to evidence (read this first)

| Outline question | Status | Headline evidence | Where |
|---|---|---|---|
| What makes a question good or bad? | **Partially answered** | A hard Dale–Chall gate (≤7.9 grade) vs. an LLM-judge rubric diverge sharply: 40.6% pass with the mechanical gate vs. 83–84% with the LLM judge only, on the same 416 cases — the two instruments disagree about what "good" means. No formal rubric (vocabulary list, glossing rule, PassivePy, sentence structure) has been run yet; the outline's rubric is a design proposal, not yet executed. | [Prior work §1](#prior-work-private-repo-methodology-precursors-not-in-this-public-repo); outline's own "Readability test" section is future work |
| Can you get an AI to ask better questions? | **Yes, demonstrated** | Targeted prompt edits (explicit glossing, word-substitution list, anti-redundancy check, few-shot examples) raised the same 416-case eval's strict pass rate from 40.62% to 57.45% (+16.83pp) in one iteration; an earlier, less-targeted edit only moved it to 44.23%. | [Prior work §1b–1g](#1-readability--prompt-quality-experiments-private-repo-january-2026) |
| Do different AI models ask better questions? (nano vs. full) | **Infrastructure exists, result not yet extracted** | A blind human A/B labeling workflow comparing gpt-5-nano/gpt-5/gpt-5.2 follow-up-question quality was built and run (`eval-cpr-2026-05-01T20:01:43`, 416/416 cases), but the decoded preference percentages were not read out during this pass (they sit in unopened `.xlsx` workbooks in the private paper-repo snapshot). | [Prior work §3c](#3-classification-flip-precursor-and-model-comparison-private-repo-aprilmay-2026) |
| Can follow-up questions help improve classification vs. no follow-up? | **Yes, and the answer changed once a pipeline bug was fixed** | Pre-fix: net −7 exact-label change (looked like "no help/harm"). Two structural FETCH bugs meant GPT-5-family classifiers never actually received the disclosed answer on the second call. Post-fix, net **+181** (condition B) to **+220** (condition C) exact-label gains across 959 scenarios, confirmed stable across 6 reruns on a 200-case subsample (every run net +33 to +46). | [Finding 5](#finding-5--the-v2-disclosure-grounded-benchmark-the-decisive-post-fix-result) |
| Can we use a digital twin in this? | **Not addressed** | No digital-twin artifact, design note, or experiment exists anywhere in either repo. | — |
| Can follow-up questions help non-legal classification? | **Not addressed** | Every study in both repos is legal-intake-specific (FETCH's taxonomy). No out-of-domain/non-legal replication exists. | — |

The rest of this document is the detailed evidence supporting the "answered"/"partially answered" rows above, plus everything the pre-existing (2026-07-17) version already established about the labeling pipeline and FETCH's retrieval accuracy — which the paper outline's "Background," "Data and materials," and part of "Results" sections will draw on independent of the follow-up-question question.

## Executive synthesis

The repository (both public data here and private-repo methodology history) supports five connected conclusions:

1. **The routing task is materially multi-label.** The source contains many descriptions with multiple independently meaningful legal issues. A single primary label is useful for routing, but it is not a complete representation of the problem.
2. **Annotation disagreement is concentrated at taxonomy boundaries.** Humans agree more than the model raters, and broad legal-domain agreement is stronger than exact specialist-route agreement.
3. **FETCH usually reaches the correct legal domain and often retrieves at least one exact route, but it is incomplete on multi-label scenarios and overpredicts.** Pooled retrieval was 99.2% for at least one correct top-level category and 95.3% for at least one exact sublabel; micro exact precision was 46.0%.
4. **Follow-up questions materially help classification — but only once a real pipeline bug is fixed, and this supersedes an earlier, now-suspect result.** The 2026-07-17 version of this document reported a near-neutral flip result (47 gained / 48 lost category membership) from the 1,000-candidate `expanded_flip_experiment`. That study used the same `GPT-5 + keyword` configuration later shown, in `flip_experiment_v2`, to suffer from a bug where GPT-5-family classifiers never receive the disclosed follow-up answer on the reclassification call. Because the bug and the 1,000-candidate study's classifier configuration match exactly, and the 1,000-candidate runs predate the 2026-07-18 fix by four days, its near-neutral result should now be read the same way as `flip_experiment_v2`'s own pre-fix baseline: as resampling noise, not a measurement of whether disclosed facts help. The **post-fix** `flip_experiment_v2` result — net +181 to +220 exact-label gains, confirmed across 6 variability reruns — is the current, trustworthy answer, and it is unambiguously positive.
5. **A deterministic safety-net layer (screening protocols) adds a small, real, zero-downside rescue on top of the fixed LLM pipeline**, concentrated exactly in the safety/routing categories it targets (restraining orders, elder abuse, immigration consequences, third-party work injury) — about 1% of matched cases, isolated via a paired within-run comparison that holds LLM sampling constant.

The most defensible paper framing: **multi-label legal-intake routing is feasible at the broad-domain level; follow-up questions clearly help once the pipeline actually uses the answer; a deterministic backstop adds a small additional safety margin; and exact specialist routing remains limited by taxonomy overlap and incomplete elicitation.**

## Evidence hierarchy and scope

```text
431 reviewed source rows
  └─ 373 whitespace-normalized unique descriptions
       ├─ 114 stories with two eligible human annotations + three model annotations
       └─ 373-scenario consensus-gold FETCH evaluation

Diagnostic benchmark v1 (retired, bug-affected — see Finding 4 caveat):
200 legacy flip candidates + 800 workbook-grounded candidates
  └─ 1,000 candidates × 3 intended-fact runs = 3,000 observations (2026-07-14, pre-fix)

Diagnostic benchmark v2 (current, authoritative for "do questions help"):
959 Claude-authored disclosure-grounded scenarios, 33 boundary families
  ├─ pre-fix baseline (historical, same bug as v1)
  ├─ condition B: post-fix, 5-provider vote (2026-07-18)
  ├─ condition C: post-fix + PR #34 deterministic screening protocols (2026-07-18)
  └─ variability check: 3 reruns × 2 conditions on a fixed 200-case subsample (2026-07-19)

Prior-work lineage (private repo only, not reproducible from this repo):
416-case follow-up-question readability/quality eval (Jan 2026, 2 experiments)
430-case label-selection/multi-issue eval (Apr 2026, 4 configurations)
200-scenario, 10-pair classification-flip pilot — direct ancestor of the 1,000-candidate v1 set
  (confirmed by matching schema and literal legacy_* scenario IDs carried into v1)
```

The canonical chronology and current status are maintained in [`silver_labels/REVIEW_AUDIT_TRAIL.md`](silver_labels/REVIEW_AUDIT_TRAIL.md) and, for the v2 flip benchmark, [`flip_experiment_v2/analysis/RESULTS.md`](flip_experiment_v2/analysis/RESULTS.md) and [`flip_experiment_v2/README.md`](flip_experiment_v2/README.md).

- **Consensus-gold evaluation:** a retrieval/coverage benchmark against a conservative derived reference set.
- **Flip benchmarks (v1, v2):** stress tests of follow-up-question elicitation and post-answer classification.
- **Reliability analysis:** agreement among the available raters, not agreement with an external legal ground truth.

## Finding 1 — The labeling pipeline exposes a real multi-label problem

The three independent model passes used the same detailed taxonomy, prompt schema, and validation logic. Their rank-1 exact-pair agreement was:

| Relationship before internal review | Rows | Share |
|---|---:|---:|
| All three agree | 353 | 81.9% |
| Exactly two agree | 70 | 16.2% |
| All three differ | 8 | 1.9% |

The resulting Stage 04 workbook is a defensible **primary routing** artifact, not evidence that each description has only one correct label. Full row-level record: [`silver_labels/04_review/final_review.json`](silver_labels/04_review/final_review.json).

The targeted cross-check of nine examples from the prior paper found four derived human-label corrections — rows 149, 188, 220, and 339. Stage 06 separately exposed 78 exact-pair disagreement rows. See [`silver_labels/05_human_label_review/README.md`](silver_labels/05_human_label_review/README.md) and [`silver_labels/06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md`](silver_labels/06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md).

Subsequent audits quantify why the one-label interpretation is insufficient:

- The broad top-three evidence audit placed **156/431 rows** in a high-recall evidence queue. See [`silver_labels/07_multilabel_audit/MULTILABEL_FINDINGS.md`](silver_labels/07_multilabel_audit/MULTILABEL_FINDINGS.md).
- The fresh GPT-5.2 two-label audit found **90 rows** with two supported labels, **39 primary-label change candidates**, **12 uncertain primary assessments**, and a **132-row union review queue**. See [`silver_labels/08_gpt52_two_label_audit/TWO_LABEL_AUDIT_FINDINGS.md`](silver_labels/08_gpt52_two_label_audit/TWO_LABEL_AUDIT_FINDINGS.md).
- The cap-free Stage 10 workflow allows zero through four labels; seven rows needed three or four candidate issues. See [`silver_labels/10_four_label_human_review/`](silver_labels/10_four_label_human_review/).

The consensus reconstruction contains **238 one-label, 124 two-label, 9 three-label, and 2 four-label** unique scenarios, provenance-tagged: 259 sets from three-model plus internal consensus, 61 from exact human-reviewer agreement, 53 from human decisions corroborated by ≥2 models. See [`gold_labels_consensus_20260716/README.md`](gold_labels_consensus_20260716/README.md).

## Finding 2 — Agreement is better for humans and broad domains than for exact routes

On the 114 descriptions with two eligible human annotations:

| Comparison | Mean Jaccard distance | α-Jaccard | Exact set match |
|---|---:|---:|---:|
| Humans | 0.251 (95% CI 0.198–0.305) | 0.744 (0.687–0.796) | 61/114 (53.5%) |
| LLMs | 0.362 (0.320–0.404) | 0.632 (0.586–0.672) | 125/342 (36.5%) |
| Human–LLM | 0.370 (0.330–0.411) | 0.623 (0.579–0.660) | 250/684 (36.5%) |
| All five | 0.355 (0.318–0.393) | 0.638 (0.598–0.673) | 436/1,140 (38.2%) |

Intervals are story-bootstrap percentile intervals (2,000 samples). Supplemental ICC: label-count ICC(A,1) = **0.328** (95% CI 0.216–0.421), conditional exact-pair incidence ICC(A,1) = **0.279**, conditional top-level incidence ICC(A,1) = **0.390**.

Four recurring ambiguity mechanisms explain most disagreement: (1) core problem vs. every visible secondary issue, (2) specific route vs. general fallback, (3) missing procedural posture/party role, (4) competing framings of one dispute. These four mechanisms are exactly what `flip_experiment_v2`'s 33 boundary families were built to stress-test (M1–M4 in that benchmark). Repeated review found 30/36 (83.3%) duplicate story/reviewer pairs received the same set. Largest boundary problems: General Litigation, Labor & Employment, Business & Corporate, Real Property, Debtor/Creditor. Full detail, illustrative disagreements: [`gold_labels_consensus_20260716/FINDINGS.md`](gold_labels_consensus_20260716/FINDINGS.md).

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

Reproduction and caveats: [`gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md`](gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_FINDINGS.md). The classifier used the full GPT-5.2 deployment; no mini/nano model was substituted in this evaluation (see the open "nano vs. full" question in the RQ table above — that comparison exists only for follow-up-question generation quality, in the private-repo prior work, not for this classification-accuracy benchmark).

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

**Why this is now suspect:** `flip_experiment_v2`'s own pre-fix baseline (identical `gpt-5 + keyword` classifier configuration, run 2026-07-18 00:26 UTC — four days after this v1 study) showed the same shape of result (net −7 exact-label change: 24 gained, 31 lost) and was traced to two confirmed structural bugs in FETCH's `ClassificationService` (see [Finding 5](#finding-5--the-v2-disclosure-grounded-benchmark-the-decisive-post-fix-result)): the GPT-5-family Responses API branch never threads `followup_answers` into the reclassification call on the normal code path, and a provider-pool filter meant to exclude only keyword/SPOT providers also incorrectly excludes Gemini/Mistral. Because the v1 study used the exact same bug-affected classifier family and provider mix, and predates the fix, **its 47-added/48-lost near-neutral pattern is very likely the same resampling-noise artifact**, not evidence that disclosed facts are roughly neutral. This was not directly re-verified by rerunning v1's exact 1,000 candidates post-fix (the study owner's post-fix validation effort went into the newer, more realistic v2 candidate set instead — see [why v1 was retired](flip_experiment_v2/README.md#why-v1-was-retired)), so treat this as a strong inference from matching configuration and matching failure shape, not a second confirmed measurement.

What remains usable from v1 without this caveat: the **matcher coverage** numbers (question-generation/matching is a separate call, unaffected by the reclassification bug), and the **domestic-violence-specific finding** that only 44.31% of hidden-DV question sets explicitly probed safety/abuse/violence/threats/control despite 78.04% matcher acceptance — a question-generation gap, not a reclassification gap, and structurally distinct from the bug above. Full detail: [`expanded_flip_experiment/analysis/RESULTS.md`](expanded_flip_experiment/analysis/RESULTS.md) region and [`expanded_flip_experiment/analysis/QUOTED_EVIDENCE.md`](expanded_flip_experiment/analysis/QUOTED_EVIDENCE.md).

## Finding 5 — The v2 disclosure-grounded benchmark: the decisive post-fix result

`flip_experiment_v2/` replaced v1 with 959 Claude Fable 5-authored scenarios (33 boundary families) whose hidden facts are **case facts** (procedural posture, institutional identity, amounts, safety context) rather than v1's party-role reversals — real users know which side of a dispute they're on, so role-reversal flips rarely occur at intake. Every scenario is grounded in the Stage 11 gold-label human-disagreement mechanisms (Finding 2's M1–M4). Full design rationale: [`flip_experiment_v2/README.md`](flip_experiment_v2/README.md).

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

**This is the paper's central, current answer: follow-up questions clearly help, once the pipeline actually uses the disclosed answer.** Post-fix, gains outnumber losses ~15:1 (B) to ~28:1 (C), and matched-case final accuracy nearly doubles (49%→89–91%). Safety-sensitive rows (n=115) are the strongest part of the result: **zero losses in either post-fix condition** (37 gained/0 lost in B, 41/0 in C), final exact accuracy 89.7% (B) / 93.8% (C) among matched.

One caveat: condition B's provider mix (5 providers) also changed alongside the fix (vs. v1/pre-fix's 2-provider config), so the pre-fix→post-fix jump conflates the bug fixes with the provider-mix change; it should be read as "the pipeline as it exists now vs. before this work," not as isolating the code fixes' own effect size.

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

Full detail, quoted evidence, family-level breakdowns, and the safety-sensitive-rows gap: [`flip_experiment_v2/analysis/RESULTS.md`](flip_experiment_v2/analysis/RESULTS.md).

### What's still open for v2

Candidates are Claude-authored and marked `claude_authored_awaiting_human_salience_audit` — the planned human spot-check (the outline's "do human spot checking of the dataset... ~1000 examples") has not yet been performed. `analyze_runs.py` is designed to re-derive every table above after rows are pruned, with no model calls repeated.

## Prior work (private repo, methodology precursors not in this public repo)

The following predates and motivated the `publishable-repo` work above. It lives in `/home/quinten/fetch/promptfoo/EXPERIMENT_LOGS/` and a satellite snapshot `/home/quinten/fetch/followup-study-paper-repo/` — **neither is included in or reproducible from this repo**; it is cited here only because it directly answers or informs several outline research questions and establishes the methodological lineage of the flip-benchmark work.

### 1. Readability / prompt-quality experiments (private repo, January 2026)

A fixed 416-case eval combined a hard mechanical **Dale–Chall readability gate** (max grade 7.9) with **LLM-judge rubrics** (`followup_relevant`, `followup_jargon_appropriate`, via `gpt-5-nano`) and a sentence-length check.

| Stage | Change | Pass w/ Dale–Chall | Pass w/o Dale–Chall | Dale-only failures |
|---|---|---:|---:|---:|
| Baseline | — | 169/416 (40.62%) | 346/416 (83.17%) | 177 |
| Experiment 1 | Generic plain-language / 6th-grade guidance added to prompts | 184/416 (44.23%) | 349/416 (83.89%) | 165 |
| Experiment 2 | Explicit glossing rule, word-substitution list, anti-redundancy check, few-shot good/bad examples | **239/416 (57.45%)** | — | 135 |

**This is the direct precedent for the outline's "readability rubric" question**, and its central finding is exactly the tension the outline anticipates: cases failing *only* Dale–Chall consistently pass both LLM rubrics ("all questions use plain, accessible language" at a Dale–Chall grade of 9–16, well above the 7.9 cutoff) — i.e., the mechanical metric is stricter than, and sometimes disagrees with, an LLM judge. Non-Dale failures were dominated by unglossed jargon/acronyms (≈89% of non-Dale failures in Experiment 1) and redundant questions (asking things the user already stated). Experiment 1's edits, notably, *increased* non-Dale failures slightly (55→67) even while improving Dale–Chall — a useful null result showing generic "be plain" instructions aren't sufficient; Experiment 2's much more specific interventions (explicit gloss/substitution/anti-redundancy/few-shot) produced the larger, cleaner gain. A parallel, later thread (April–May 2026) added genuine **human** A/B preference labeling comparing gpt-5-nano/gpt-5/gpt-5.2 follow-up-question quality (`eval-cpr-2026-05-01T20:01:43`, 416/416 cases) — the labeled outcome data was not extracted during this indexing pass (it sits in unopened `.xlsx` workbooks) and is a natural next step for answering the outline's "do different models ask better questions" question with human ground truth rather than an LLM judge.

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

## What can safely be claimed in a paper

- "Against the conservative consensus set, FETCH retrieved at least one exact route in 95.3% of run-observations and at least one correct top-level domain in 99.2%, but complete retrieval declined sharply as the number of gold issues increased."
- "Follow-up questions materially improve exact-label classification accuracy once the pipeline correctly incorporates the disclosed answer: net exact-label gains of +181 to +220 across 959 disclosure-grounded scenarios, confirmed stable across 6 independent reruns, versus a near-neutral net −7 when a confirmed answer-consumption bug is present."
- "A deterministic screening backstop rescues a further ~1% of matched cases with zero regressions, concentrated in safety- and routing-sensitive categories, on top of the fixed LLM pipeline."
- "Targeted, evidence-driven prompt engineering (explicit jargon-glossing rules, word-substitution lists, anti-redundancy checks, few-shot examples) nearly doubled question-quality pass rates on a fixed eval (40.62%→57.45%), while generic 'use plain language' instructions alone produced a much smaller gain and did not reduce jargon-specific failures."
- "A hard mechanical readability metric (Dale–Chall) and an LLM-judge rubric disagree substantially on the same outputs — most Dale–Chall-only failures are judged fully clear and jargon-free by the LLM rubric — motivating a more deliberate, multi-instrument readability rubric (vocabulary frequency, glossing, passive voice, sentence structure) with human validation, rather than relying on either instrument alone."

The evidence does **not** yet support:

- Any claim about digital twins (no work exists).
- Any claim about non-legal-domain follow-up-question benefit (no work exists; every study here is legal-intake-specific).
- Any claim comparing "nano" vs. "full" model quality with numbers (the human-labeling infrastructure exists but results were not extracted in this pass).
- Treating the v1 1,000-candidate flip study's 47-added/48-lost result as a valid neutral finding — it very likely shares v2's pre-fix bug and should be described as superseded, not corroborating.
- A completed human spot-check of the 959-scenario v2 candidate set (planned, not yet done).
- A rules-vs-AI-prompt comparison for domestic-violence screening specifically (the outline's Massachusetts-informed DV question panel is not yet operationalized as a study; the closest existing evidence is v1's 44.31%-explicit-safety-probe finding and v2's safety-sensitive-rows breakdown, both of which test FETCH's existing behavior, not a designed rules-vs-prompt comparison).

## Reproduction map

| Evidence | Parent document | Reproduction |
|---|---|---|
| Silver labels and chronology | [`silver_labels/REVIEW_AUDIT_TRAIL.md`](silver_labels/REVIEW_AUDIT_TRAIL.md) | `python create_silver_labels.py ...`; `python build_reviewed_silver.py` |
| Consensus gold construction | [`gold_labels_consensus_20260716/README.md`](gold_labels_consensus_20260716/README.md) | `python build_gold_consensus.py` |
| Five-rater agreement | [`gold_labels_consensus_20260716/AGREEMENT_METHODS.md`](gold_labels_consensus_20260716/AGREEMENT_METHODS.md) | `python analyze_gold_rater_agreement.py` |
| FETCH consensus-gold evaluation | [`gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_METHODS.md`](gold_labels_consensus_20260716/fetch_gold_accuracy/FETCH_GOLD_ACCURACY_METHODS.md) | `pytest -q test_analyze_fetch_gold_accuracy.py`; `python analyze_fetch_gold_accuracy.py ...` |
| v1 expanded flip benchmark (superseded, see Finding 4) | [`expanded_flip_experiment/README.md`](expanded_flip_experiment/README.md) | `pytest -q expanded_flip_experiment/test_candidates.py` |
| v2 disclosure-grounded flip benchmark (current) | [`flip_experiment_v2/README.md`](flip_experiment_v2/README.md) | `python flip_experiment_v2/run_direct.py --label <name> ...`; `python flip_experiment_v2/analyze_runs.py` |
| Screening-protocol marginal contribution | [`flip_experiment_v2/analysis/RESULTS.md`](flip_experiment_v2/analysis/RESULTS.md#condition-b-vs-c-does-the-screening-protocol-add-anything) | `python flip_experiment_v2/analyze_screening_contribution.py` |
| Variability / sampling-noise check | [`flip_experiment_v2/analysis/RESULTS.md`](flip_experiment_v2/analysis/RESULTS.md#variability-is-this-llm-sampling-noise) | `python flip_experiment_v2/build_variability_sample.py`; rerun `run_direct.py`/`analyze_runs.py` on the fixed subsample |

The full verification record is [`expanded_flip_experiment/analysis/VERIFICATION.md`](expanded_flip_experiment/analysis/VERIFICATION.md) (v1) and [`flip_experiment_v2/analysis/EXECUTION_LOG.md`](flip_experiment_v2/analysis/EXECUTION_LOG.md) (v2, including the bug's exact file/line citations).

## Recommended paper presentation order

1. Consensus-gold evaluation as the main retrieval result (Finding 3).
2. Agreement analysis as the annotation/reliability result (Finding 2).
3. The v2 flip benchmark's post-fix result as the primary "do follow-up questions help" experiment (Finding 5) — lead with this, not v1, and disclose the bug/fix as part of the methods narrative since it changed the paper's own conclusion.
4. The screening-protocol comparison as a secondary, smaller-effect-size result (Finding 5, condition B vs. C).
5. The private-repo prior work (readability prompt-engineering, label-selection tuning, the 200-scenario flip pilot) as methodology-evolution/prior-work narrative, not as headline results — it motivated and was superseded by the public-repo work above.
6. Explicitly flag as future work: the formal readability rubric with human validation, the nano-vs-full model comparison with actual numbers, the human salience audit of the 959 v2 candidates, digital twins, and non-legal-domain replication.

Keep these distinctions visible throughout: top-level vs. exact-subcategory routing; at-least-one-label vs. complete multi-label retrieval; matcher coverage vs. explicit fact-sensitive questioning; final-label presence vs. a label newly added after disclosure; and — the most important new distinction — a classifier that receives the disclosed answer vs. one that (as in v1 and v2's pre-fix baseline) silently does not.
