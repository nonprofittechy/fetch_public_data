# Failure modes carried forward from *On Wednesdays, We Ask Questions*

The paper's 200-scenario experiment reported 69% hidden-fact question coverage and 65.2% final-category accuracy among the 138 matched scenarios. A relevant follow-up rescued 18 initially wrong classifications and degraded 4 initially correct classifications.

The revised benchmark deliberately stresses the lowest-performing areas from Tables 5 and 6:

| Prior swap pair | Initial accuracy | Question coverage | Final accuracy when matched | Reported problem | Revised coverage |
|---|---:|---:|---:|---|---|
| `criminal_vs_restraining` | 0% | 95% | 15.8% | FETCH defaulted to `General Litigation > Stalking Orders` regardless of relationship context. | Relationship, caller role, charges-versus-protection, stalking-order, and domestic-violence variants. |
| `employment_admin` | 65% | 20% | 0% | Explicit state-agency hearing signals were ignored. | State contested-case, unemployment appeal, licensing-board, and direct-employer controls. |
| `injury_location` | 100% | 95% | 26.3% | Contractor/off-clock facts often failed to move Workers' Comp to Personal Injury. | Employee, contractor, off-clock, customer, third-party, and ordinary workplace facts. |
| `bankruptcy_vs_collections` | 50% | 45% | 88.9% | Debtor/creditor role and judgment posture were difficult initially. | Debtor/creditor, judgment winner/loser, personal/business bankruptcy, and dissolution variants. |
| `domestic_violence` | 100% | 10% | 100% | FETCH rarely asked about abuse, so the decisive fact was usually never elicited. | 85 intended hidden-DV rows plus counterfactual no-abuse controls, covering physical threats, stalking, child exchanges, and financial control. |

The paper's `custody_vs_support`, `dui_vs_dmv`, and `tenant_vs_landlord` pairs are retained as calibration strata. The benchmark also adds exact-subcategory scoring because a top-level category score cannot detect several of the paper's failures.

These numbers describe the paper's prior run, not results on the revised benchmark. The included PDF is the provenance source. No paper result was re-estimated here.

