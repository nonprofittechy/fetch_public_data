# Quote candidates

Direct excerpts from this run's provider results.

### x0041 — intended — `custody_vs_restraining`

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”
>
> Generated question(s): “What is the main issue you need help with right now?”
>
> Hidden-fact answer: “The other parent hit me while I was holding our child and threatened to come back.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Family Law > Child Custody/Visitation”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Family Law > Restraining Orders`; matched=False; expected category present=False; expected exact label present=False.

### x0014 — intended — `divorce_vs_restraining`

> Opening query: “My spouse and I cannot keep living together and I need legal help. Can a lawyer help me?”
>
> Generated question(s): “What kind of help do you need right now?”
>
> Hidden-fact answer: “My partner threatened to hurt me if I leave and has blocked the door before.”
>
> Matcher-selected question: “What kind of help do you need right now?”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “Family Law > General (Divorce/Separation etc.) || Family Law > Restraining Orders”

Expected final: `Family Law > Restraining Orders`; matched=True; expected category present=True; expected exact label present=True.

### legacy_025 — intended — `criminal_vs_restraining`

> Opening query: “A person keeps pounding on my door late at night and shouting at me.”
>
> Generated question(s): “Who is this person to you? || Have they threatened you or tried to hurt you?”
>
> Hidden-fact answer: “It's my child's father doing this and I want to keep him away from me.”
>
> Matcher-selected question: “Who is this person to you?”
>
> Initial returned label set: “General Litigation > Stalking Orders || Family Law > Restraining Orders”
>
> Final returned label set: “General Litigation > Stalking Orders || General Litigation > Neighbor Disputes/Nuisance”

Expected final: `Family Law > Restraining Orders`; matched=True; expected category present=False; expected exact label present=False.

### legacy_091 — intended — `domestic_violence`

> Opening query: “Hi, I want to separate from my husband and need to know what my options are.”
>
> Generated question(s): “Are you looking for a legal separation (stay married but live apart), to end your marriage (divorce), or are you not sure yet? || Do you and your husband have any children under 18? || Do you have any safety concerns, like abuse, and need a court order to stay away?”
>
> Hidden-fact answer: “My husband has never hurt or threatened me.”
>
> Matcher-selected question: “Do you have any safety concerns, like abuse, and need a court order to stay away?”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “Family Law > General (Divorce/Separation etc.)”

Expected final: `Family Law > General (Divorce/Separation)`; matched=True; expected category present=True; expected exact label present=True.

### legacy_124 — intended — `employee_vs_employer`

> Opening query: “I told someone we wouldn't be needing their help anymore, and now they're demanding payment for work they haven't done yet.”
>
> Generated question(s): “Did you sign a written agreement (contract) that says what happens if you cancel? || Was this hire for your business or for personal/household work? || Did they already do any work or did you pay a deposit/retainer (money paid upfront)?”
>
> Hidden-fact answer: “I run a catering business and hire chefs on a per-event contract basis.”
>
> Matcher-selected question: “Was this hire for your business or for personal/household work?”
>
> Initial returned label set: “Consumer Law > General || Business and Corporate > General (contracts, entities)”
>
> Final returned label set: “Consumer Law > General || Business and Corporate > General (contracts, entities)”

Expected final: `Business & Corporate > General (Contracts, Business, Organization)`; matched=True; expected category present=True; expected exact label present=True.

### legacy_075 — intended — `debtor_vs_creditor`

> Opening query: “Someone bought my old phone, but now they won’t pay me.”
>
> Generated question(s): “How did the sale happen?”
>
> Hidden-fact answer: “They said the phone didn’t work as described and they’re not paying.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Consumer Law > Problems Between Consumers || Consumer Law > Small Claims Advice”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Consumer Law > General`; matched=False; expected category present=False; expected exact label present=False.

### x0722 — intended — `veterans_benefits_vs_va_loan`

> Opening query: “A VA-related decision is affecting my finances and I need help. What are my options?”
>
> Generated question(s): “What kind of VA decision is affecting your money?”
>
> Hidden-fact answer: “The dispute concerns the terms and servicing of my VA-backed construction loan.”
>
> Matcher-selected question: “What kind of VA decision is affecting your money?”
>
> Initial returned label set: “Administrative Law > Military/Veterans || Debtor/Creditor > General (Debtor)”
>
> Final returned label set: “Administrative Law > Military/Veterans”

Expected final: `Real Property > Government Loans (VA,FHA,Etc.)`; matched=True; expected category present=False; expected exact label present=False.

