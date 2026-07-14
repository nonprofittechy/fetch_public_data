# Initial take: expanded 1,000-candidate FETCH flip study

## Bottom line

Three uncached paid runs completed 3,000/3,000 intended-hidden-fact cases with no orchestration errors. FETCH generated a matcher-accepted question in **71.63%** of cases (run range 70.5–72.3%). That is close to the 69% coverage reported in *On Wednesdays*, but coverage is only the first gate.

FETCH returns an unordered set for this study. All primary classification metrics therefore ask whether the expected category or exact label appears anywhere in that set:

| Three-run metric | Pooled result |
|---|---:|
| Expected initial category anywhere in returned set | 90.17% |
| Expected initial exact label anywhere (2,670 scorable cases) | 77.57% |
| Matcher-accepted hidden-fact question | 71.63% |
| Expected final category anywhere, among matched | 84.64% |
| Expected exact final label anywhere, among 1,892 exact-scorable matched cases | 56.29% |
| Expected final category newly added after the hidden fact | 2.19% of matched |
| Expected exact final label newly added after the hidden fact | 6.45% of exact-scorable matched |

My initial take is therefore mixed. FETCH often asks something the matcher accepts, and the expected final category appears in 84.64% of matched outputs. Exact-label presence is substantially lower at 56.29%. More importantly for a *flip* study, most expected final outcomes were already present in the initial unordered set: only 47 matched observations newly gained the expected final category, and only 122 exact-scorable observations newly gained the expected final exact label. The earlier paper reported 77% initial-category accuracy, 69% coverage, and 65.2% final-category accuracy, but the present dataset and GPT-5 + keyword provider condition differ, so this is not a causal improvement estimate.

## Domestic violence: explicit screening remains the key gap

The dataset contains 85 intended hidden-domestic-violence cases, observed three times. GPT-4.1 accepted a generated question for **78.04%** of those 255 observations, but only **44.31%** of question sets explicitly mentioned safety, abuse, violence, threats, harm, stalking, control, or protective relief. The matcher accepted 93.81% of the explicit probes; the large gap comes from broad questions being treated as elicitation opportunities.

`x0041` shows why the aggregate matcher rate is too generous. In run 1:

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”
>
> Generated question: “What is the main issue you need help with right now?”
>
> Hidden fact: “The other parent hit me while I was holding our child and threatened to come back.”
>
> Matcher-selected question: “[none]”
>
> Final labels: “[no second classification]”

Run 2 accepted the similarly broad “What is the main issue right now?” and returned `Family Law > Domestic Violence`, but not the expected restraining-order label. Run 3 accepted “Which of these fits your situation best right now?” and did return:

> “Family Law > Child Custody/Visitation || Family Law > Restraining Orders”

That is useful repeat evidence, but it is not evidence that FETCH consistently *asked about violence*. The hidden fact happened to fit a generic prompt.

There are genuinely safety-aware examples. In all three runs, `x0011` explicitly asked some version of whether the user felt unsafe or needed an order making the other person stay away. Run 1 asked:

> “Do you feel unsafe and need a court order to make them stay away?”

The answer was:

> “My partner controls my money and has threatened violence when I ask to leave.”

Run 1 included `Family Law > Restraining Orders`; runs 2 and 3 instead included `Family Law > Domestic Violence` alongside divorce. The question succeeded as intake, but exact-label membership varied.

Across all 255 hidden-DV observations, the expected final category appeared somewhere after a match 91.46% of the time, while the expected exact label appeared in only 35.18%. The dedicated 20-case `domestic_violence` legacy pair was even more revealing: pooled coverage was 40%, almost exactly between the paper's 10% and the broader 78% matcher result. Explicit screening, broad-question matching, and final classification membership should remain three separate measures.

## The paper's hardest failure modes are still visible

The five carried-forward strata produced the following pooled results over three runs:

| Pair | Question coverage | Expected final category present | Expected exact label present | Expected exact label newly added |
|---|---:|---:|---:|---:|
| `criminal_vs_restraining` | 73.33% | 47.73% | 36.36% | 6.82% |
| `employment_admin` | 13.33% | 50.00% | 0% (4 scorable matches) | 0% |
| `injury_location` | 70.00% | 28.57% | 28.57% | 14.29% |
| `bankruptcy_vs_collections` | 41.67% | 100% | 40.00% | 28.00% |
| `domestic_violence` | 40.00% | 100% | 62.50% | 0% |

For `legacy_025`, run 1 asked the legally decisive relationship question:

> Opening query: “A person keeps pounding on my door late at night and shouting at me.”
>
> Generated questions: “Who is this person to you? || Have they threatened you or tried to hurt you?”
>
> Hidden fact: “It's my child's father doing this and I want to keep him away from me.”
>
> Final labels: “General Litigation > Stalking Orders || General Litigation > Neighbor Disputes/Nuisance”

That reproduces the paper's stalking-order default despite relationship context. Runs 2 and 3 asked nearly the same relationship question and included `Family Law > Restraining Orders`. The expanded `x0101` was even more variable: runs 1–2 stayed in stalking/online-harassment labels after learning that the person was the user's child's other parent and had assaulted them; run 3 finally added the expected restraining-order label.

Administrative-law signals remain troublesome. In all three runs, `x0157` asked where or what kind of legal process was happening and received:

> “A state agency denied my complaint and scheduled an administrative appeal hearing.”

Yet every final result remained entirely in Labor & Employment. Run 3 returned:

> “Labor & Employment > Discrimination - Employee || Labor & Employment > Sexual Harassment - Employee || Labor & Employment > Whistleblowers - Employee”

No run returned `Administrative Law > General (State)`.

Work-injury behavior was also poor after successful elicitation. For `legacy_162`, all three runs asked where the fall happened and received:

> “The fall happened in the warehouse where I work.”

Run 1 included `Workers' Comp > State`; runs 2 and 3 returned only premises-liability and personal-injury labels. Across the full `injury_location` stratum, the expected exact result appeared in 28.57% of matched cases and was newly added in 14.29%.

Judgment collection shows why exact scoring matters. `legacy_002` revealed:

> “I sued someone for unpaid work and won, but can’t figure out how to collect the money.”

None of the three runs returned `Debtor/Creditor > Judgment Collection`. Run 3 instead returned:

> “Debtor/Creditor > General (Debtor) || Bankruptcy > Personal”

The `bankruptcy_vs_collections` category score is 100% among matches, but exact-label presence is only 40%; the expected exact label was newly added in 28% of matched observations.

## Most expected final outcomes were already in the initial set

Using the exact historical outcome logic from *On Wednesdays*, the 2,149 matched observations break down as follows:

| Paper-style outcome | Count | % of matched |
|---|---:|---:|
| Initial expected category present; final expected category present | 1,643 | 76.45% |
| Initial expected category present; final expected category absent, serialized top category unchanged (“neutral failure to flip”) | 301 | 14.01% |
| Initial expected category present; final expected category absent, serialized top category changed (“degraded/harmed”) | 6 | 0.28% |
| Initial expected category absent; final expected category present (“rescued”) | 176 | 8.19% |
| Initial expected category absent; final expected category absent | 23 | 1.07% |

On that historical paper metric, follow-up **rescued 176 classifications and harmed 6**, a rescue-to-harm ratio of **29.33:1**. The per-run rescue/harm counts were 55/3, 59/2, and 62/1. *On Wednesdays* reported 18 rescues and 4 degradations, or 4.5:1 in the beneficial direction.

The historical harm criterion depends on a changed serialized first category, even though order is not a present-study criterion. It is reported only to reproduce the paper comparison. The earlier 307-harm interpretation incorrectly treated all 301 neutral failures to flip as harm; `ON_WEDNESDAYS_DIFFERENCE_AUDIT.md` documents that correction. The symmetric set-membership comparison below is the appropriate order-independent diagnostic.

Order is irrelevant, but set membership before and after the answer still matters for diagnosing whether the hidden fact changed the output. Among 2,149 matched observations:

| Expected final category | Count |
|---|---:|
| Absent initially, present after the answer | 47 |
| Present initially and after the answer | 1,772 |
| Present initially, absent after the answer | 48 |
| Absent initially and after the answer | 282 |

Among the 1,892 exact-scorable matched observations, the expected exact label was newly added 122 times, present both before and after 943 times, lost 102 times, and absent both times 725 times. Thus the answer produced a small net increase of 20 expected-exact memberships across the pooled repeats.

This same-target comparison is the cleaner estimate of directional benefit under unordered-set scoring. At category level, 47 additions versus 48 losses is essentially neutral (0.98:1, net −1). At exact-label level, 122 additions versus 102 losses modestly favors benefit (1.20:1, net +20). Because the model runs are stochastic and no no-answer control was run alongside each second classification, even these are paired diagnostics rather than causal effects.

This reframes the apparent 84.64% final-category success. It is a valid criterion result, but in 97.4% of those final-category successes the expected final category was already somewhere in the initial set. That is unsurprising for many same-category and multi-label scenarios, yet it means this candidate set is much better at testing *retention/presence* than demonstrating a binary set-membership flip. The next benchmark revision should require the expected final exact label to be absent from a validated initial output—or otherwise define success as maintaining both plausible labels until the fact resolves uncertainty.

## Multi-label realism is valuable, and membership must remain the criterion

`x0584` began, “I need legal help protecting a project I have been developing,” and revealed:

> “I need a patent application for a new machine before publicly disclosing it.”

All three runs matched a project/protection question and included the exact patent label after the answer. Run 3 returned:

> “Intellectual Property > Trademark/Copyright || Intellectual Property > Patent (Reg Patent Attys Only) || Intellectual Property > Computer Law & Internet Law”

The patent label is present in the returned set, so this is a success under the study criterion. Its position in the serialized list is irrelevant.

## Stability and operational evidence

Despite caching being disabled, only 603/1,000 scenarios matched a question in all three runs; 172 never matched, and 225 matched in one or two runs. A striking 967 scenarios generated different question sets across runs, and 452 produced different final label sets across their matched runs. Only 272 scenarios had the expected exact final label present in all three runs; 563 never did (including non-scorable historical exact labels).

Runs 1–3 took 68.18, 69.02, and 64.41 minutes. Run 1 had two GPT-5 timeouts observed live but not captured because of a logging-order defect; run 2 captured six; run 3 captured zero. All affected cases still produced a keyword-backed FETCH result. The three final datasets share the same SHA-256 and each contains 1,000 records with zero orchestration errors.

## Recommended next pass

1. Human-review all 1,000 candidate outcomes, prioritizing the 770 multi-label-grounded cases and the four exact-label compatibility exclusions before treating this as an accuracy benchmark.
2. Human-grade a stratified sample of matcher decisions. Broad prompts should not count as deliberate domestic-violence screening.
3. Keep classification scoring order-independent. Report expected category membership, exact-label membership, and whether the expected label was newly added after the hidden fact.
4. Separate question-generation failures from answer-use failures. The quotes repeatedly show relevant questions followed by classification that ignores the answer.
5. Run the retained counterfactual condition as a separate paired experiment. The three official runs evaluated intended facts only, so this study does not yet establish that the same opening query responds directionally to opposing answers.
6. For domestic violence, add a safety-aware screening protocol rather than relying on ordinary uncertainty-driven question generation.

This is an initial diagnostic interpretation, not a publication-ready causal or accuracy claim. The raw results, per-run tables, stability data, taxonomy audit, exact metric definitions, and complete quote appendix are preserved alongside it.
