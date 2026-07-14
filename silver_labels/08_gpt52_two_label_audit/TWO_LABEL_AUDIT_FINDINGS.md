# Two-label audit findings

## Interpretation

The fresh GPT-5.2 pass supports the multi-label hypothesis. It identified 90 rows where two labels are independently supported by the text, including 53 rows where the existing AI primary was retained and 34 where the existing primary was judged incomplete or incorrect.

The audit also identified 81 rows where the existing primary should be reconsidered. This is a single-model audit signal, not a replacement for human review. It is especially important to inspect cases where the model changed the primary while also adding a second label.

## Representative findings

| Row | Existing primary | GPT-5.2 audit result | Reason |
|---:|---|---|---|
| 8 | Family Law / Child Custody/Visitation | Child Custody/Visitation + Child Support/Modification | Both matters are explicitly in the petition. |
| 12 | Labor & Employment / Wage and Hour Claims | Wage and Hour Claims + Wrongful Discharge | Missing wages and termination after complaint are distinct issues. |
| 24 | General Litigation / Wrongful Death | Wrongful Death + Malpractice-Medical | The description combines a death and alleged hospital negligence. |
| 28 | Workers' Comp / Third Party litigation | Workers' Comp / State + Personal Injury | No third party is identified; the work injury and injury claim remain separate routing issues. |
| 40 | Intellectual Property / Trademark/Copyright | Trademark/Copyright + Patent | Copyright, trademark, and patent filing help are expressly requested. |
| 43 | Real Property / General (residential) | General (residential) + Water Law | Home-purchase misrepresentation and water rights are separate issues. |
| 51 | Family Law / Paternity | Child Custody/Visitation + Paternity | The user requests both paternity and custody help. |
| 54 | Labor & Employment / Discrimination | Union Issues + Discrimination | Discrimination and an unresponsive union/grievance issue are both described. |
| 66 | Business & Corporate / Restaurant/OLCC | General business + General commercial real property | The text requests business counsel and investment-property services, without a clear OLCC issue. |
| 69 | General Litigation / Actions Against Police | Personal Injury + Actions Against Police | The description includes both assault injuries and alleged police misconduct. |
| 70 | General Litigation / Neighbor Disputes/Nuisance | Neighbor Disputes/Nuisance + Stalking Orders | The ongoing neighbor conduct includes facts supporting both routing categories. |
| 94 | Administrative Law / SSD | SSD + Social Security/SSI | Both SSD and SSI denials are explicitly stated. |
| 290 | Intellectual Property / Trademark/Copyright | Online Harassment/Doxing/Bullying + Libel/Slander/Defamation | The audit judged the developed harassment and reputational-harm claims stronger than the brief copyright reference. |
| 342 | Labor & Employment / Document Review/Severance Packages. | Document Review/Severance Packages. + FMLA | Separation-agreement review is combined with a distinct FMLA-related termination concern. |
| 419 | Family Law / Divorce/Separation | Divorce/Separation + Tenant Residential (uncertain) | The row lists divorce, eviction, and a criminal case but gives no detail; two labels are plausible but uncertain. |
| 420 | Workers' Comp / State | Workers' Comp / State + International Law / Gen. Immigration/Visas | Workplace injury and deportation concerns are both explicit; firing is secondary to those two routes. |

## What to review first

Start with [`review_queue.json`](review_queue.json) or filter the workbook by `two_label_audit_status`. Prioritize:

1. `primary_assessment = needs_change` and `multi_label_assessment = two_labels_supported`;
2. `primary_assessment = needs_change` and one-label output;
3. `primary_assessment = uncertain`.

Do not automatically accept every second label. Confirm that it represents a separate legal issue or explicitly requested service, rather than a neighboring taxonomy category, generic fallback, or different procedural framing of the same matter.
