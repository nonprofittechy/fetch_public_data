# Initial take after two official runs (pre-canonicalization intermediate, not final)

This checkpoint was frozen before the third run completed, before a taxonomy-compatibility audit found legacy spelling aliases and non-comparable exact labels, and before confirming that serialized label order is not a study criterion. Its 43% exact-presence figures reproduce the raw provider flags, and its rank-based discussion is inapplicable. It is retained to show how the interpretation developed; the final `INITIAL_TAKE.md` and `METRIC_DEFINITIONS.md` supersede it.

## Provisional result

Across the first two 1,000-case runs, FETCH found a matcher-accepted question for 70.5% and 72.1% of cases. An expected final top-level category appeared somewhere in the returned multi-label set for 83.0% and 82.3% of matched cases, but the intended exact category/subcategory appeared for only 43.4% and 43.0%. More strictly, the intended exact result was first-ranked in only 21.6% and 21.6% of matched cases. The complete first-ranked label changed after the hidden fact in only 12.8% and 16.0%.

That distinction changes the story. The broad category-presence figure looks encouraging relative to *On Wednesdays*' 65.2% final-category result, but FETCH often retains or adds several candidates instead of actually flipping its leading route. These runs also use a different 1,000-candidate mixture and a narrower GPT-5 + keyword ensemble, so the comparison is diagnostic, not an improvement claim.

## Domestic violence: better prompting than the paper, but broad matching overstates it

The benchmark has 85 cases whose intended hidden fact involves domestic violence. The matcher reported coverage of 77.7% and 78.8%. A stricter lexical audit found an explicit safety/abuse/protection probe in only 41.2% and 45.9% of those question sets. Broad questions account for much of the gap.

For `x0041`, run 1 did not surface violence:

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”
>
> Generated question: “What is the main issue you need help with right now?”
>
> Hidden fact: “The other parent hit me while I was holding our child and threatened to come back.”
>
> Matcher-selected question: “[none]”
>
> Initial labels: “Family Law > Child Custody/Visitation”
>
> Final labels: “[no second classification]”

Run 2 varied on the same fixed candidate. It accepted the equally broad “What is the main issue right now?” and returned `Family Law > Domestic Violence`, but it still did not return the benchmark's exact `Family Law > Restraining Orders` outcome:

> Generated questions: “What is the main issue right now? || Do you already have a court order about custody or visits?”
>
> Hidden fact: “The other parent hit me while I was holding our child and threatened to come back.”
>
> Matcher-selected question: “What is the main issue right now?”
>
> Final labels: “Family Law > Child Custody/Visitation || Family Law > Domestic Violence”

There are also genuinely targeted questions. In run 1, `x0011` asked:

> “Are you legally married to this person? || Do you have children together (including pregnancy)? || Do you feel unsafe and need a court order to make them stay away?”

The answer was:

> “My partner controls my money and has threatened violence when I ask to leave.”

FETCH then returned:

> “Family Law > General (Divorce/Separation etc.) || Family Law > Restraining Orders”

But run 2's similarly appropriate question—“Do you need help with safety right now (like a court order to stay away)?”—produced `Family Law > Domestic Violence` rather than the expected restraining-order exact label. This is a useful distinction between eliciting danger and routing it consistently.

## The paper's hardest classification failures remain recognizable

The criminal-versus-restraining pattern is still unstable. For `legacy_025`, run 1 asked the legally decisive relationship question:

> Opening query: “A person keeps pounding on my door late at night and shouting at me.”
>
> Generated questions: “Who is this person to you? || Have they threatened you or tried to hurt you?”
>
> Hidden fact: “It's my child's father doing this and I want to keep him away from me.”
>
> Final labels: “General Litigation > Stalking Orders || General Litigation > Neighbor Disputes/Nuisance”

That reproduces the paper's core observation: even after relationship context, the expected `Family Law > Restraining Orders` was missing. Run 2, however, asked almost the same question and did include the expected label:

> Generated questions: “Who is this person to you? || Have they threatened to harm you or tried to get inside?”
>
> Final labels: “General Litigation > Stalking Orders || Family Law > Restraining Orders”

The expanded `x0101` failed in both runs. The model asked “Who is this person to you?” / “What best describes your connection to this person?” and received:

> “The person is my child's other parent and has assaulted me before.”

Yet the final labels were respectively:

> “General Litigation > Stalking Orders”

and:

> “General Litigation > Stalking Orders || General Litigation > Online Harrassment/Doxing/Bullying”

Thus asking the right relationship question is not sufficient; the classifier can continue to ignore the answer.

The administrative-hearing problem is similarly persistent. In `x0157`, FETCH asked “Where is the legal process happening right now?” and the hidden answer was:

> “A state agency denied my complaint and scheduled an administrative appeal hearing.”

Run 1 stayed with:

> “Labor & Employment > Discrimination - Employee || Labor & Employment > Whistleblowers - Employee”

Run 2 stayed with the same two labels in the opposite order. Neither returned `Administrative Law > General (State)`.

Work-injury classification is highly variable. For `legacy_162`, the opening query only said, “I slipped and fell and now my knee is swollen.” Both runs asked where the fall occurred, and both received:

> “The fall happened in the warehouse where I work.”

Run 1 added the exact `Workers' Comp > State` label; run 2 returned only personal-injury and premises-liability labels. The evidence supports repeated uncached runs: one execution would yield a materially different conclusion for this candidate.

Judgment collection shows why exact-label scoring matters. For `legacy_002`, FETCH asked whether the issue concerned debts owed or money others owed and received:

> “I sued someone for unpaid work and won, but can’t figure out how to collect the money.”

Both runs reached the broad `Debtor/Creditor` category, but neither returned `Debtor/Creditor > Judgement Collection`. The first returned “Debt Counseling/Workouts” and “General (Creditor)”; the second returned “General (Debtor)” and “General (Creditor).” Broad final-category presence therefore credits a result that would still route away from the expected exact service.

## Multi-label cases show both the value and limitation of candidate sets

For `x0584`, a short opening—“I need legal help protecting a project I have been developing.”—was followed by “What best describes your project?” / “What kind of project is it?” The fact was:

> “I need a patent application for a new machine before publicly disclosing it.”

Run 1 already had patent in its initial three-label set and returned the same three labels after the answer, so no leading flip occurred. Run 2 began with `Intellectual Property > Other` plus a corporate label and then returned:

> “Intellectual Property > Trademark/Copyright || Intellectual Property > Patent (Reg Patent Attys Only) || Business and Corporate > General (contracts, entities)”

The expected patent label is present, but not first. On realistic multi-label material, “did the right candidate survive?” and “would the user be routed to it?” are different evaluation questions.

## Provisional recommendations

1. Keep the three-run design and report stability per scenario. A single run hides meaningful variation.
2. Treat explicit domestic-violence screening as a separate metric from matcher coverage. The matcher is too permissive to answer whether FETCH deliberately probes for abuse.
3. Score both returned-set presence and first-ranked routing. Category presence alone is too forgiving for exact services such as restraining orders, administrative law, judgment collection, and workers' compensation.
4. Human-review the candidate labels and a stratified sample of matcher judgments before making accuracy claims.
5. Troubleshoot classification after successful elicitation separately from question generation. The saved quotes show repeated cases where the question was legally on point but the answer was not used.
