# Difficult reviewed-workbook scenarios used as design anchors

These examples come from the 431-row four-label human-review workbook. They are useful benchmark anchors because a short opening query can conceal role, procedure, or a second independently meaningful legal issue. The labels below are candidate review judgments, not final human gold.

| Workbook row | Why it is difficult | Candidate issues reflected in the expanded benchmark |
|---:|---|---|
| 28 / 349 | A workplace slip-and-fall can support ordinary state workers' compensation, a personal-injury theory, or third-party workers' compensation litigation depending on employment status and who caused the hazard. | `work_injury_vs_personal_injury`; `workers_comp_vs_third_party` |
| 51 | Paternity, custody, and violence/restraining-order facts occur in one narrative. Removing the violence fact creates a realistic hidden-domestic-violence test rather than an artificial unrelated category swap. | `custody_vs_restraining`; `paternity_vs_custody`; `divorce_vs_restraining` |
| 63 / 335 | Return-to-work, FMLA, and private disability-insurance facts overlap; the immediate decision-maker and requested remedy determine routing. | The benchmark uses the same decision-maker distinction in employment-versus-administrative and licensing-versus-employment pairs. |
| 71 / 404 / 411 | Dementia, suspected exploitation, benefits eligibility, power of attorney, and guardianship can coexist. The missing fact must distinguish lack of legal authority from actual financial abuse or a Medicaid denial. | `guardianship_vs_elder_abuse`; `medicaid_vs_guardianship` |
| 94 | The source explicitly contains both denied SSD and denied SSI claims, which are easy to collapse despite separate taxonomy entries. | `ssd_vs_ssi` |
| 290 | Copyright, defamation, and online harassment are independently pleaded theories. | `defamation_vs_online_harassment`; `copyright_vs_patent` |
| 342 / 344 | Severance, FMLA, age discrimination, harassment, and wage issues appear together. A single broad employment label obscures which fact changes the requested service. | `wages_vs_wrongful_discharge`; `wrongful_discharge_vs_unemployment`; `employment_vs_state_hearing` |
| 384 | Trust planning, residential transfer, a VA construction loan, and tax language appear together; the focused review retained three labels and rejected property tax because no assessment dispute was stated. | `veterans_benefits_vs_va_loan` plus exact-label counterfactual controls |
| 419 | “Divorce. Eviction. Criminal Case.” supplies three issues but almost no role or procedural facts, so exact subcategories are low-confidence. | Role-focused housing and criminal/protection pairs; no attempt to convert its placeholder labels into gold |
| 420 | One sentence combines a work injury, firing, and deportation concern. | Work-injury and wrongful-discharge boundaries, tagged as multi-label grounded |
| 421 | Guardianship/beneficiary litigation, a car injury, and a parking citation create four possible labels with uneven taxonomy fit. | Guardianship-versus-abuse and exact-subcategory scoring |
| 424 | Veterans benefits, professional licensing, neighbor nuisance, and will drafting each map to a distinct issue. | `veterans_benefits_vs_va_loan`; `license_vs_employment_discrimination` |

The complete 93-row set with two to four candidate labels is in `multilabel_seed_rows.csv`. Repeated problem descriptions are intentionally preserved there because the reviewed workbook contains repeated source rows with potentially different adjudication context.

