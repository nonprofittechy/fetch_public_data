# Quote candidates

Direct excerpts from this run's provider results.

### legacy_089 — intended — `domestic_violence`

> Opening query: “I need advice on how to separate from my partner. We’ve had a lot of disagreements lately.”
>
> Generated question(s): “Are you legally married or in a registered domestic partnership with your partner? || Do you and your partner have children together, or are you pregnant? || Is there any safety issue like threats, hitting, or stalking where you might need a court order to stay away?”
>
> Hidden-fact answer: “My partner cut off my access to our bank account and won’t let me have money.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.) || Family Law > Informal Living Arrangements”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Family Law > Restraining Orders`; matched=False; expected category present=False; expected exact label present=False.

### x0014 — intended — `divorce_vs_restraining`

> Opening query: “My spouse and I cannot keep living together and I need legal help. Can a lawyer help me?”
>
> Generated question(s): “What do you mainly need help with right now?”
>
> Hidden-fact answer: “My partner threatened to hurt me if I leave and has blocked the door before.”
>
> Matcher-selected question: “What do you mainly need help with right now?”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “Family Law > General (Divorce/Separation etc.) || Family Law > Restraining Orders”

Expected final: `Family Law > Restraining Orders`; matched=True; expected category present=True; expected exact label present=True.

### x0310 — intended — `judgment_vs_bankruptcy`

> Opening query: “There is already a decision about a debt and I need to know the next step. I do not know what to do next.”
>
> Generated question(s): “Which side are you on for this debt decision?”
>
> Hidden-fact answer: “Several creditors have judgments against me and I cannot meet basic expenses.”
>
> Matcher-selected question: “Which side are you on for this debt decision?”
>
> Initial returned label set: “Debtor/Creditor > Judgment Collection || Debtor/Creditor > General (Debtor)”
>
> Final returned label set: “Debtor/Creditor > General (Debtor) || Debtor/Creditor > Judgment Collection”

Expected final: `Bankruptcy > Personal`; matched=True; expected category present=False; expected exact label present=False.

### legacy_091 — intended — `domestic_violence`

> Opening query: “Hi, I want to separate from my husband and need to know what my options are.”
>
> Generated question(s): “Do you and your husband have any minor children together? || Is there any abuse or safety concern where you might need a court order to stay away?”
>
> Hidden-fact answer: “My husband has never hurt or threatened me.”
>
> Matcher-selected question: “Is there any abuse or safety concern where you might need a court order to stay away?”
>
> Initial returned label set: “Family Law > General (Divorce/Separation etc.)”
>
> Final returned label set: “Family Law > General (Divorce/Separation etc.)”

Expected final: `Family Law > General (Divorce/Separation)`; matched=True; expected category present=True; expected exact label present=True.

### legacy_124 — intended — `employee_vs_employer`

> Opening query: “I told someone we wouldn't be needing their help anymore, and now they're demanding payment for work they haven't done yet.”
>
> Generated question(s): “Who hired this person or company? || Did you sign a written agreement that talks about deposits, cancellation, or non‑refundable fees? || Have they done any work or bought materials yet?”
>
> Hidden-fact answer: “I run a catering business and hire chefs on a per-event contract basis.”
>
> Matcher-selected question: “Who hired this person or company?”
>
> Initial returned label set: “Consumer Law > General || Business and Corporate > General (contracts, entities)”
>
> Final returned label set: “Business and Corporate > General (contracts, entities) || Consumer Law > General”

Expected final: `Business & Corporate > General (Contracts, Business, Organization)`; matched=True; expected category present=True; expected exact label present=True.

### x0185 — intended — `wrongful_discharge_vs_unemployment`

> Opening query: “I was fired and need help because I have no income now. What are my options?”
>
> Generated question(s): “Do you think you were fired for an illegal reason (like discrimination, punishment for reporting a problem, or because you took protected leave), or was it a layoff/no reason given? || Have you already applied for state unemployment benefits? || Were you given anything in writing about the firing?”
>
> Hidden-fact answer: “I need representation at a state unemployment-benefits hearing.”
>
> Matcher-selected question: “[none]”
>
> Initial returned label set: “Labor & Employment > Wrongful Discharge - Employee || Labor & Employment > General - Employee || Administrative Law > Unemployment”
>
> Final returned label set: “[no final classification because the fact was not elicited]”

Expected final: `Administrative Law > Unemployment`; matched=False; expected category present=False; expected exact label present=False.

### x0722 — intended — `veterans_benefits_vs_va_loan`

> Opening query: “A VA-related decision is affecting my finances and I need help. What are my options?”
>
> Generated question(s): “What kind of VA decision is hurting your finances?”
>
> Hidden-fact answer: “The dispute concerns the terms and servicing of my VA-backed construction loan.”
>
> Matcher-selected question: “What kind of VA decision is hurting your finances?”
>
> Initial returned label set: “Administrative Law > Military/Veterans”
>
> Final returned label set: “Administrative Law > Military/Veterans”

Expected final: `Real Property > Government Loans (VA,FHA,Etc.)`; matched=True; expected category present=False; expected exact label present=False.

