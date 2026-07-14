# Quoted result evidence

This pre-canonicalization appendix was generated from the first two completed official-run `scenario_details.csv` files. Its quoted text remains exact, but its exact-label booleans reproduce the earlier raw provider flags and its top-ranked annotations are not study criteria; the final appendix uses canonicalized, order-independent comparisons. The scenario list was frozen before run 3 was inspected. Text inside block quotes is copied from saved provider outputs and candidate facts; only `[none]` annotations are added.

## `x0011`

### final_run_1_20260714T170440Z

> Opening query: “Things at home have become unbearable and I want to leave the relationship. I do not know what to do next.”  
> Generated question(s): “Are you legally married to this person? || Do you have children together (including pregnancy)? || Do you feel unsafe and need a court order to make them stay away?”  
> Hidden fact: “My partner controls my money and has threatened violence when I ask to leave.”  
> Matcher-selected question: “Do you feel unsafe and need a court order to make them stay away?”  
> Initial labels: “Family Law > General (Divorce/Separation etc.) || Family Law > Domestic Violence”  
> Final labels: “Family Law > General (Divorce/Separation etc.) || Family Law > Restraining Orders”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `True`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “Things at home have become unbearable and I want to leave the relationship. I do not know what to do next.”  
> Generated question(s): “Which best describes your situation with your partner? || Do you need help with safety right now (like a court order to stay away)? || Do you have children together?”  
> Hidden fact: “My partner controls my money and has threatened violence when I ask to leave.”  
> Matcher-selected question: “Do you need help with safety right now (like a court order to stay away)?”  
> Initial labels: “Family Law > General (Divorce/Separation etc.) || Family Law > Domestic Violence”  
> Final labels: “Family Law > General (Divorce/Separation etc.) || Family Law > Domestic Violence”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `x0041`

### final_run_1_20260714T170440Z

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”  
> Generated question(s): “What is the main issue you need help with right now?”  
> Hidden fact: “The other parent hit me while I was holding our child and threatened to come back.”  
> Matcher-selected question: “[none]”  
> Initial labels: “Family Law > Child Custody/Visitation”  
> Final labels: “[no second classification]”

Expected final `Family Law > Restraining Orders`; matched `False`; expected exact label present `False`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “The other parent has been causing problems and I need advice about my child. I do not know what to do next.”  
> Generated question(s): “What is the main issue right now? || Do you already have a court order about custody or visits?”  
> Hidden fact: “The other parent hit me while I was holding our child and threatened to come back.”  
> Matcher-selected question: “What is the main issue right now?”  
> Initial labels: “Family Law > Child Custody/Visitation || Family Law > Restraining Orders”  
> Final labels: “Family Law > Child Custody/Visitation || Family Law > Domestic Violence”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `legacy_025`

### final_run_1_20260714T170440Z

> Opening query: “A person keeps pounding on my door late at night and shouting at me.”  
> Generated question(s): “Who is this person to you? || Have they threatened you or tried to hurt you?”  
> Hidden fact: “It's my child's father doing this and I want to keep him away from me.”  
> Matcher-selected question: “Who is this person to you?”  
> Initial labels: “General Litigation > Stalking Orders || Family Law > Restraining Orders”  
> Final labels: “General Litigation > Stalking Orders || General Litigation > Neighbor Disputes/Nuisance”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “A person keeps pounding on my door late at night and shouting at me.”  
> Generated question(s): “Who is this person to you? || Have they threatened to harm you or tried to get inside?”  
> Hidden fact: “It's my child's father doing this and I want to keep him away from me.”  
> Matcher-selected question: “Who is this person to you?”  
> Initial labels: “General Litigation > Stalking Orders || General Litigation > Neighbor Disputes/Nuisance”  
> Final labels: “General Litigation > Stalking Orders || Family Law > Restraining Orders”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `True`; expected exact label top-ranked `False`.

## `x0101`

### final_run_1_20260714T170440Z

> Opening query: “A person keeps sending messages and appearing at places I go. I do not know what to do next.”  
> Generated question(s): “Who is this person to you?”  
> Hidden fact: “The person is my child's other parent and has assaulted me before.”  
> Matcher-selected question: “Who is this person to you?”  
> Initial labels: “General Litigation > Stalking Orders || Family Law > Restraining Orders”  
> Final labels: “General Litigation > Stalking Orders”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “A person keeps sending messages and appearing at places I go. I do not know what to do next.”  
> Generated question(s): “What best describes your connection to this person?”  
> Hidden fact: “The person is my child's other parent and has assaulted me before.”  
> Matcher-selected question: “What best describes your connection to this person?”  
> Initial labels: “General Litigation > Stalking Orders || Family Law > Restraining Orders”  
> Final labels: “General Litigation > Stalking Orders || General Litigation > Online Harrassment/Doxing/Bullying”

Expected final `Family Law > Restraining Orders`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `x0157`

### final_run_1_20260714T170440Z

> Opening query: “I reported unfair treatment at my job and now there is a legal process. What are my options?”  
> Generated question(s): “What kind of problem did you report at work? || What happened to you after you reported it? || Where is the legal process happening right now?”  
> Hidden fact: “A state agency denied my complaint and scheduled an administrative appeal hearing.”  
> Matcher-selected question: “Where is the legal process happening right now?”  
> Initial labels: “Labor & Employment > Discrimination - Employee || Labor & Employment > Whistleblowers - Employee || Labor & Employment > Wrongful Discharge - Employee”  
> Final labels: “Labor & Employment > Discrimination - Employee || Labor & Employment > Whistleblowers - Employee”

Expected final `Administrative Law > General (State)`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “I reported unfair treatment at my job and now there is a legal process. What are my options?”  
> Generated question(s): “What did you report at work? || What kind of legal process is happening now? || Did your employer take action against you after you reported it?”  
> Hidden fact: “A state agency denied my complaint and scheduled an administrative appeal hearing.”  
> Matcher-selected question: “What kind of legal process is happening now?”  
> Initial labels: “Labor & Employment > Discrimination - Employee || Labor & Employment > Whistleblowers - Employee”  
> Final labels: “Labor & Employment > Whistleblowers - Employee || Labor & Employment > Discrimination - Employee”

Expected final `Administrative Law > General (State)`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `legacy_162`

### final_run_1_20260714T170440Z

> Opening query: “I slipped and fell and now my knee is swollen. I wanted to see if I have any options.”  
> Generated question(s): “Where did you fall? || Did you tell the property owner/manager or your employer about the fall and make a written report?”  
> Hidden fact: “The fall happened in the warehouse where I work.”  
> Matcher-selected question: “Where did you fall?”  
> Initial labels: “General Litigation > Premises Liability || General Litigation > Personal Injury”  
> Final labels: “General Litigation > Premises Liability || Workers' Comp > State”

Expected final `Workers' Comp > State`; matched `True`; expected exact label present `True`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “I slipped and fell and now my knee is swollen. I wanted to see if I have any options.”  
> Generated question(s): “Where did you fall?”  
> Hidden fact: “The fall happened in the warehouse where I work.”  
> Matcher-selected question: “Where did you fall?”  
> Initial labels: “General Litigation > Personal Injury || General Litigation > Premises Liability”  
> Final labels: “General Litigation > Premises Liability || General Litigation > Personal Injury”

Expected final `Workers' Comp > State`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `legacy_002`

### final_run_1_20260714T170440Z

> Opening query: “I'm overwhelmed by unpaid bills and not sure what steps to take to get my money.”  
> Generated question(s): “Is this about debts you owe, or money that other people/businesses owe you?”  
> Hidden fact: “I sued someone for unpaid work and won, but can’t figure out how to collect the money.”  
> Matcher-selected question: “Is this about debts you owe, or money that other people/businesses owe you?”  
> Initial labels: “Debtor/Creditor > General (Debtor) || Debtor/Creditor > General (Creditor) || Debtor/Creditor > Debt Counseling/Workouts”  
> Final labels: “Debtor/Creditor > Debt Counseling/Workouts || Debtor/Creditor > General (Creditor)”

Expected final `Debtor/Creditor > Judgement Collection`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “I'm overwhelmed by unpaid bills and not sure what steps to take to get my money.”  
> Generated question(s): “Which best describes your situation right now?”  
> Hidden fact: “I sued someone for unpaid work and won, but can’t figure out how to collect the money.”  
> Matcher-selected question: “Which best describes your situation right now?”  
> Initial labels: “Debtor/Creditor > Debt Counseling/Workouts || Bankruptcy > Personal”  
> Final labels: “Debtor/Creditor > General (Debtor) || Debtor/Creditor > General (Creditor)”

Expected final `Debtor/Creditor > Judgement Collection`; matched `True`; expected exact label present `False`; expected exact label top-ranked `False`.

## `x0584`

### final_run_1_20260714T170440Z

> Opening query: “I need legal help protecting a project I have been developing. Can a lawyer help me?”  
> Generated question(s): “What best describes your project? (Pick all that fit.) || Have you already shared or released any part of the project to the public (posted online, sold, shown at events)?”  
> Hidden fact: “I need a patent application for a new machine before publicly disclosing it.”  
> Matcher-selected question: “What best describes your project? (Pick all that fit.)”  
> Initial labels: “Intellectual Property > Trademark/Copyright || Intellectual Property > Patent (Reg Patent Attys Only) || Intellectual Property > Computer Law & Internet Law”  
> Final labels: “Intellectual Property > Trademark/Copyright || Intellectual Property > Patent (Reg Patent Attys Only) || Intellectual Property > Computer Law & Internet Law”

Expected final `Intellectual Property > Patent (Reg Patent Attys Only)`; matched `True`; expected exact label present `True`; expected exact label top-ranked `False`.

### final_run_2_20260714T181957Z

> Opening query: “I need legal help protecting a project I have been developing. Can a lawyer help me?”  
> Generated question(s): “What kind of project is it? This helps match you to the right lawyer.”  
> Hidden fact: “I need a patent application for a new machine before publicly disclosing it.”  
> Matcher-selected question: “What kind of project is it? This helps match you to the right lawyer.”  
> Initial labels: “Intellectual Property > Other || Business and Corporate > General (contracts, entities)”  
> Final labels: “Intellectual Property > Trademark/Copyright || Intellectual Property > Patent (Reg Patent Attys Only) || Business and Corporate > General (contracts, entities)”

Expected final `Intellectual Property > Patent (Reg Patent Attys Only)`; matched `True`; expected exact label present `True`; expected exact label top-ranked `False`.
