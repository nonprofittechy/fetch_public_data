# Results — does nano→full improve FETCH's question screens?

Paired, disclosure-blind study of the follow-up-question **screen** FETCH shows
after an opening query, comparing the classification ensemble with its OpenAI
member (+ semantic-merge model) set to **gpt-5-nano** vs **gpt-5.2** — the
production switch the team shipped but never measured.

- **373** human-vetted problem descriptions → **746 screens** (one per arm).
- Arms differ *only* in the OpenAI member + merge model; gemini + mistral held
  constant; keyword/spot omitted (they emit no questions).
- Real FETCH `ClassificationService.classify()`, caching off. Provider failures
  were **repaired**, not dropped (103 → 11). The 11 unrepairable remainders are
  Azure **content-filter 400s on the input text itself** — mostly the *same ~7
  scenarios failing in both arms*, so their exclusion is arm-symmetric and
  unbiased (they cannot be classified by either tier).
- Judges, blind to arm: **DeepSeek-V4-Pro** (Azure, automated, full set) +
  **Claude** (in-context, blind 30-scenario subset, cross-family check).

## TL;DR

**The switch is justified — but by *coverage*, not readability.** gpt-5.2
reliably asks ~3 questions; **gpt-5-nano asks *nothing* on ~1 in 4 screens.** For
an intake system that exists to disambiguate, silently asking nothing is the
core failure, and it is nano's dominant, judge-independent weakness. Claims that
one tier writes *better-grounded* questions did **not** survive a second judge:
DeepSeek flagged full's richer questions as worse, but Claude found the two arms'
per-question quality essentially identical, and the two judges agreed on only
22% of screens. The honest read: **when both arms ask, question quality is
similar; the difference that matters is whether a question gets asked at all.**

## 1. Coverage — the decisive, robust finding

| | nano | full |
|---|---|---|
| screens with **0 questions** | **24.6%** (92/373) | **0.5%** (2/373) |
| mean questions / screen | **~1.8** | **~2.9** |

McNemar on paired emptiness: **88 scenarios where nano asked nothing but full
did, 0 the other way, p ≈ 6×10⁻²⁷.** This is objective (counting questions), so
it is judge-independent. It is the single largest effect in the study.

### Why is nano empty so often? (mechanism, `diagnostics/`)

Re-running generation with per-provider instrumentation:

| provider | mean q / call | % of calls with 0 questions |
|---|---|---|
| **gpt-5.2** (full arm) | 2.9 | **3%** |
| **gpt-5-nano** (nano arm) | 0.27 | **87%** |
| gemini (shared) | 0.6 | 53% |
| mistral (shared) | 0.97 | 50% |

- nano returns "confident classification, *no questions*" on **87%** of calls.
- gemini and mistral are each silent ~50% of the time, so they **do not
  reliably backfill**. When all three happen to be silent (common, because nano
  usually is), the union of proposed questions is **0 before any merge runs** →
  empty screen. Confirmed on the empty-nano cases (all three ≈0).
- So the follow-up screen is effectively the **OpenAI member's** output. That
  makes this a clean measurement of the swapped variable — and explains why the
  switch mattered: gpt-5.2 single-handedly carries the screen.
- nano is also **erratic**: the same scenario yields 0 questions on one call and
  3 on another.

## 2. Per-question quality — needs two judges, and the effect is not robust

On the pairs where **both** arms asked ≥1 question, the automated **DeepSeek**
judge reported full as slightly *worse*:

| metric (DeepSeek, n=273) | nano | full | p | direction |
|---|---|---|---|---|
| 1 unverified presupposition (median) | 0 | 1 | 9×10⁻⁵ | full worse |
| 3 respondent unclear rate (median) | 0.00 | 0.17 | 0.002 | full worse |
| 3 answerable rate (median) | 0.89 | 0.78 | 0.002 | full worse |
| 2 double-barrel flag rate | 0.80 | 0.80 | 1.0 | no diff |

**But this did not replicate under Claude.** On the blind 30-scenario subset:

| metric | Claude nano | Claude full | DeepSeek nano | DeepSeek full |
|---|---|---|---|---|
| 1 presupposition (mean screen-max) | 0.03 | 0.00 | ~0.7 (both) | |
| 2 double-barrel (flag rate) | 0.03 | 0.07 | 0.83 (both) | |
| 3 unclear rate | 0.00 | 0.01 | | |
| 3 answerable rate | 1.00 | 0.99 | | |

- Under Claude, **nano and full are statistically indistinguishable** per-question.
- **Judge disagreement is enormous:** double-barrel flag rate 5% (Claude) vs 83%
  (DeepSeek); presupposition 0.017 vs 0.70; the two judges agree on only **22%**
  of screens. DeepSeek systematically over-flags menu/option questions.
- On reading, the screens that *do* ask questions are mostly clean, single-topic,
  and heavily glossed ("medically stationary (not expected to get much better)",
  "lienholder (the lender's legal claim on the car)"). Genuine defects are rare —
  e.g., one screen invented "student loans" the applicant never mentioned.

**Conclusion:** the "full is worse on grounding" signal is a **judge artifact**,
not a property of the models. This is precisely the failure the study plan
guarded against by requiring two judge families ("don't grade a GPT-family output
with only one judge"). The safe conclusion is **per-question parity**.

## 3. Exploratory metrics — full asks *more and denser* (objective, FDR-corrected)

| metric (DeepSeek, n=276) | nano med | full med | p | FDR |
|---|---|---|---|---|
| 8 screen content tokens | 29 | 43 | 7×10⁻²³ | ✓ |
| 8 newly-introduced entities | 0 | 1 | 5×10⁻⁹ | ✓ |
| 4 unintroduced hard vocab | 0 | 0 | 5×10⁻⁵ | ✓ |
| 5 max dependency length | 16 | 18 | 1×10⁻⁴ | ✓ |
| 7 max GPT-2 surprisal (bits) | 15.2 | 16.5 | 6×10⁻¹⁰ | ✓ |
| 6 agentless passive | 0 | 0 | 0.23 | ✗ |
| 9 negation × conditional | 0.01 | 0.01 | 1.0 | ✗ |

All significant effects point the same way: **full asks longer, denser, more
information-rich screens** (more tokens, more entities, slightly longer sentences,
higher surprisal). These are deterministic and judge-free. Whether "more/denser"
is better or worse is a design question — it is more *thorough* disambiguation at
some cost in reading load, not a defect.

## 4. Equivalence / planning for the null

Composite hard-flag rate (m1>0 or m2 double-barrel), SESOI = 5pp: nano 0.90,
full 0.94, paired diff **+4.0pp** (90% CI [0.4, 8.1]), McNemar p = 0.12 — neither
significantly different nor equivalent within ±5pp. **However this composite is
dominated by DeepSeek's inflated ~80% double-barrel base rate** (see §2) and is
not trustworthy in absolute terms; the informative, robust comparison is coverage
(§1), where the arms are decisively *not* equivalent.

## 5. Validity check (metrics measure what they claim)

Controlled clean-vs-degraded items + known-bad calibration
(`validation/validity_results.json`): presupposition sensitivity **1.00**,
double-barrel **0.86**, vocabulary **0.86**, known-bad screens flagged **2/2**.
The metrics move on the dimension they target; the judge catches egregious screens.

## 6. Bottom line & recommendation

- **Keep the switch to gpt-5.2.** It is justified — but the reason is **coverage**
  (nano abstains from asking anything ~24% of the time, and gemini/mistral don't
  backfill), not superior question readability or grounding.
- **Do not claim nano writes worse-grounded questions.** When nano *does* ask,
  its questions are about as clean as full's; the apparent grounding gap was a
  single-judge (DeepSeek) artifact that a Claude cross-check dissolved.
- **The lever worth tuning next** is full's *density*: it asks longer, more
  information-heavy screens. If reading load is a concern, that is the axis to
  prompt-tune — not grounding.
- **Methodological takeaway:** the two-judge, blind design earned its keep here.
  A single automated judge would have shipped a wrong "full is worse on grounding"
  conclusion.

---
*Numbers from `analysis/results_deepseek-v4.json`, `metrics/claude_subset/`,
`metrics/diagnostics/`, `validation/`. Judge disagreement (§2) is itself a
reportable result about LLM-as-judge reliability on this task.*
