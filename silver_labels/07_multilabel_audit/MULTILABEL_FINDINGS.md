# Multi-label findings

## Bottom line

Yes: the ranked outputs contain many rows where two or three labels are supported by separate facts in the description. The clearest cases are not merely model disagreement; the user explicitly asks about multiple legal matters. The current one-label silver workbook should therefore be treated as a primary routing label, not as evidence that every row has only one correct taxonomy label.

The broad evidence rule found 156 of 431 rows with at least two distinct exact pairs repeated by at least two models. Those 156 rows are in the review workbook. The count is intentionally a queue for human confirmation, because repeated alternatives can also be competing framings of one issue.

## Clear text-level examples

These examples have separate facts that map naturally to separate detailed-taxonomy pairs:

| Row | Text-level matters | Candidate labels to examine |
|---:|---|---|
| 8 | Custody/parenting time and child support are both named in the petition. | Family Law / Child Custody/Visitation; Family Law / Child Support/Modification |
| 12 | Missing wages and termination after complaining about the missing wages. | Labor & Employment / Wage and Hour Claims; Labor & Employment / Wrongful Discharge |
| 24 | Death after a hospital incident and an alleged medical-care failure. | General Litigation / Wrongful Death; General Litigation / Malpractice-Medical |
| 40 | The user explicitly requests copyright, trademark, and patent filing help. | Intellectual Property / Trademark/Copyright; Intellectual Property / Patent |
| 43 | Home-purchase misrepresentation and a separate water-rights question. | Real Property / General (residential); Real Property / Water Law |
| 51 | Paternity, custody, and a domestic-violence/restraining-order context. | Family Law / Paternity; Family Law / Child Custody/Visitation; Family Law / Restraining Orders |
| 63 | Disability/health insurance and an employment medical-leave/return-to-work issue. | General Litigation / Insurance (Health/Disability); Labor & Employment / FMLA |
| 71 | Power of attorney, suspected elder financial abuse, and possible guardianship. | Wills & Trusts / Power of Attorney; Wills & Trusts / Elder Abuse; Wills & Trusts / Conservatorship/Guardianship |
| 94 | The description separately says SSD was denied and an SSI application was filed and denied. | Administrative Law / SSD; Administrative Law / Social Security/SSI |
| 195 | Measure 11 assault, DUII, fleeing, and false-information allegations. | Criminal Law / Major Felony; Criminal Law / DUII/DWS |
| 282 | Copyright, trademark, and patent filings are all requested. | Intellectual Property / Trademark/Copyright; Intellectual Property / Patent |
| 290 | Copyright infringement, online harassment, and defamation are all explicit. | Intellectual Property / Trademark/Copyright; General Litigation / Online Harassment/Doxing/Bullying; General Litigation / Libel/Slander/Defamation |
| 342 | Separation/severance review, discrimination, and an FMLA-related concern. | Labor & Employment / Document Review/Severance Packages.; Labor & Employment / Discrimination; Labor & Employment / FMLA |
| 419 | The row itself lists divorce, eviction, and a criminal case. | Family Law / General (Divorce/Separation); Real Property / Tenant (Residential); Criminal Law / Other |
| 420 | Workplace injury, firing, and concern about deportation. | Workers' Comp / State; Labor & Employment / Wrongful Discharge; International Law / Deportation |
| 421 | A guardianship/POA dispute, a car injury, and a traffic ticket. | Wills & Trusts / Elder Abuse; General Litigation / Personal Injury; Criminal Law / Traffic Offenses |

These are examples for orientation, not a replacement for the human decision. The workbook preserves the exact model evidence for every candidate row, including cases not listed here.

## Cases that need caution

Some repeated pairs should probably remain one primary label unless the human reviewer sees a separate legal request:

- Rows 306 and 307 have two International Law alternatives, but each describes one immigration matter. `Other` versus `Gen. Immigration/Visas` is a taxonomy-framing choice, not automatically two labels.
- Rows 103 and 107 have Bankruptcy / Personal and Bankruptcy / Pro Se Coaching. The second may describe the desired service format rather than a separate legal issue.
- Rows 201–204 and 210–211 combine a debt lawsuit with settlement or payment-plan language. Those can be one debt matter even though both `General (Debtor)` and `Debt Counseling/Workouts` are plausible.
- Rows 297 and 300 include IP alternatives. A patent alternative should not be retained merely because the user wants to protect or monetize a creative design; the facts must support a patentable invention or an actual patent filing request.

## Human-review rule

For each candidate row, retain label 1, 2, or 3 only when the problem description supports that label as a distinct legal issue or an explicitly requested legal service. Do not add a label solely because it is a neighboring taxonomy entry, a generic “other” fallback, or a different procedural framing of the same matter. The three blank `your_multilabel_label_*` fields in the workbook are designed for that decision.
