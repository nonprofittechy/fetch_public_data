# Quote candidates

Direct excerpts from this run's provider results.

### legacy_089 — intended — `domestic_violence`

> Opening query: “I need advice on how to separate from my partner. We’ve had a lot of disagreements lately.”
>
> Generated question(s): “Are you and your partner legally married or in a registered domestic partnership, or not married? || Do you have any children together who are under 18? || Are you worried about your safety or do you need a court order to stay away (protective order)?”
>
> Hidden-fact answer: “My partner cut off my access to our bank account and won’t let me have money.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Family Law > Restraining Orders`; matched=False; expected category present=False; expected exact label present=False.

### x0041 — intended — `custody_vs_restraining`

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”
>
> Generated question(s): “Which of these fits your situation best right now?”
>
> Hidden-fact answer: “The other parent hit me while I was holding our child and threatened to come back.”
>
> Matcher-selected question: “Which of these fits your situation best right now?”
>
> Initial returned label set: “Family Law > Child Custody/Visitation”
>
> Final returned label set: “Family Law > Child Custody/Visitation || Family Law > Restraining Orders”

Expected final: `Family Law > Restraining Orders`; matched=True; expected category present=True; expected exact label present=True.

### x0310 — intended — `judgment_vs_bankruptcy`

> Opening query: “There is already a decision about a debt and I need to know the next step. I do not know what to do next.”
>
> Generated question(s): “Which one fits you best?”
>
> Hidden-fact answer: “Several creditors have judgments against me and I cannot meet basic expenses.”
>
> Matcher-selected question: “Which one fits you best?”
>
> Initial returned label set: “Debtor/Creditor > General (Debtor) || Debtor/Creditor > Judgment Collection”
>
> Final returned label set: “Debtor/Creditor > Judgment Collection || Debtor/Creditor > General (Debtor) || Debtor/Creditor > General (Creditor)”

Expected final: `Bankruptcy > Personal`; matched=True; expected category present=False; expected exact label present=False.

### legacy_091 — intended — `domestic_violence`

> Opening query: “Hi, I want to separate from my husband and need to know what my options are.”
>
> Generated question(s): “Are you looking to end the marriage now, or to do a legal separation (stay married but live apart)? || Do you and your spouse have any children under 18? || Do you have any urgent safety concerns, like abuse, and need a court order to stay away?”
>
> Hidden-fact answer: “My husband has never hurt or threatened me.”
>
> Matcher-selected question: “Do you have any urgent safety concerns, like abuse, and need a court order to stay away?”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “Family Law > General (Divorce/Separation etc.)”

Expected final: `Family Law > General (Divorce/Separation)`; matched=True; expected category present=True; expected exact label present=True.

### legacy_124 — intended — `employee_vs_employer`

> Opening query: “I told someone we wouldn't be needing their help anymore, and now they're demanding payment for work they haven't done yet.”
>
> Generated question(s): “Was this agreement for your personal/home use, or for your business? || Do you have a written contract that mentions cancellation or early termination fees? || Did they already do any work or buy materials for your project?”
>
> Hidden-fact answer: “I run a catering business and hire chefs on a per-event contract basis.”
>
> Matcher-selected question: “Was this agreement for your personal/home use, or for your business?”
>
> Initial returned label set: “Consumer Law > General || Business and Corporate > General (contracts, entities)”
>
> Final returned label set: “Consumer Law > General || Business and Corporate > General (contracts, entities)”

Expected final: `Business & Corporate > General (Contracts, Business, Organization)`; matched=True; expected category present=True; expected exact label present=True.

### x0772 — intended — `medicaid_vs_guardianship`

> Opening query: “Our family cannot act for an incapacitated parent and care decisions are overdue. Can a lawyer help me?”
>
> Generated question(s): “Did your parent already sign any papers giving someone authority, like a power of attorney (lets someone handle money) or a health care directive/health care power of attorney (lets someone make medical choices)? || Do you need legal authority for medical decisions, money decisions, or both?”
>
> Hidden-fact answer: “A government health program denied continued coverage for the care facility.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Wills & Trusts > Conservatorship/Guardianship || Wills & Trusts > Power of Attorney”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Administrative Law > Medicare/Medicaid`; matched=False; expected category present=False; expected exact label present=False.

### legacy_075 — intended — `debtor_vs_creditor`

> Opening query: “Someone bought my old phone, but now they won’t pay me.”
>
> Generated question(s): “Who did you sell the phone to? || Did the buyer already get the phone from you? || How were they supposed to pay you?”
>
> Hidden-fact answer: “They said the phone didn’t work as described and they’re not paying.”
>
> Matcher-selected question: “How were they supposed to pay you?”
>
> Initial returned label set: “Consumer Law > Problems Between Consumers || Consumer Law > Small Claims Advice”
>
> Final returned label set: “Consumer Law > Problems Between Consumers || Consumer Law > Small Claims Advice”

Expected final: `Consumer Law > General`; matched=True; expected category present=True; expected exact label present=False.

