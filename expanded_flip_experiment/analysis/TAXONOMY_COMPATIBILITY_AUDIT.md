# Taxonomy compatibility audit

This audit was added after two official runs and before inspecting run 3. It prevents legacy label spelling from being counted as model error and prevents broad historical labels from being presented as exact current-taxonomy targets. It changes analysis only; the frozen candidate CSV, provider inputs, and raw outputs are untouched.

## Canonicalized aliases

The following are spelling, punctuation, or capitalization equivalents. Counts show appearances across the 1,000 initial plus 1,000 final expected labels; each appears equally often as an initial and final outcome because the flip set is direction-balanced.

| Candidate label | Current FETCH output label | Appearances |
|---|---|---:|
| `Business & Corporate > General (Contracts, Business, Organization)` | `Business and Corporate > General (contracts, entities)` | 20 |
| `Business & Corporate > Sale of Business` | `Business and Corporate > Sale Of Business` | 28 |
| `Debtor/Creditor > Judgement Collection` | `Debtor/Creditor > Judgment Collection` | 50 |
| `Family Law > General (Divorce/Separation)` | `Family Law > General (Divorce/Separation etc.)` | 80 |
| `General Litigation > Malpractice-Medical` | `General Litigation > Malpractice (Medical)` | 30 |
| `General Litigation > Online Harassment/Doxing/Bullying` | `General Litigation > Online Harrassment/Doxing/Bullying` | 28 |
| `Real Property > Government Loans (VA,FHA,Etc.)` | `Real Property > Government Loans (VA, FHA, etc.)` | 28 |
| `Workers' Comp > Third Party litigation` | `Workers' Comp > Third Party Litigation` | 30 |

The current FETCH spelling `Harrassment` is retained as the canonical *system-output* string even though it is misspelled English. Canonicalization is about comparing identifiers faithfully, not endorsing display text.

## Excluded from exact-label denominators

These labels still count in all category, elicitation, and stability analyses, but are not exact targets in the current taxonomy:

| Historical candidate label | Compatibility issue | Appearances |
|---|---|---:|
| `Administrative Law > SSD (Social Security Disability)` | Current FETCH combines Social Security/SSI rather than exposing standalone SSD. | 30 |
| `Labor & Employment > Discrimination` | Current FETCH branches this into employee and employer labels. | 80 |
| `Labor & Employment > Wage and Hour Claims` | Current FETCH branches this into employee and employer labels. | 30 |
| `Labor & Employment > Wrongful Discharge` | Current FETCH branches this into employee and employer labels. | 80 |

Per run, 890/1,000 initial expected labels remain exact-scorable. The matched final denominator varies with which cases receive a second classification. Original expected strings, canonical strings, scorable flags, and the provider's uncorrected booleans are all retained in `scenario_details.csv` so this decision can be audited or replaced.
