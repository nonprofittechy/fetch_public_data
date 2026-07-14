# Metric definitions and interpretation limits

The analysis deliberately keeps elicitation and classification separate. A case receives a second classification only when GPT-4.1, run at deterministic temperature, judges that the saved hidden-fact answer directly responds to at least one generated question.

## Elicitation

- **Question coverage**: percentage of usable opening-query cases for which the matcher selects at least one generated question as answerable by the hidden fact.
- The denominator is scenario-runs, not individual questions. Across the three official runs, 2,149/3,000 scenario-runs were matched (71.63%). FETCH generated 5,356 questions across 2,862 scenario-runs, but the matcher returned at most one selected question per scenario-run; it did not grade all 5,356 questions independently.
- A match is a model judgment, not a human gold decision. Broad questions such as “What do you need help with?” can be accepted even when they do not specifically probe the decisive fact. Quotes and matcher-selected questions therefore accompany the aggregate rate.
- Unmatched cases have no final classification. They are excluded from final-classification denominators rather than scored as classification failures.

## Multi-label classification

FETCH returns an unordered label set for this study. The classification criteria are therefore:

- **Expected category present**: at least one returned label has the expected top-level category.
- **Expected exact label present**: at least one returned label exactly matches the expected `category > subcategory` pair.

The JSON and CSV fields ending in `category_accuracy` and `exact_accuracy` implement presence anywhere in the returned set. Serialized order is irrelevant. Historical `*_is_top_*`, `classification_changed`, and top-category fields remain in machine-readable outputs as non-criterion diagnostics because the provider emitted an ordered list, but they must not be interpreted as accuracy, success, routing priority, or a benchmark requirement.

## Taxonomy canonicalization and exact-label denominators

Raw provider flags are preserved in the `provider_*_flag` columns. The analysis recomputes metrics after canonicalizing spelling-only aliases between the candidate files and current FETCH output, including `Business & Corporate` → `Business and Corporate`, `Judgement Collection` → `Judgment Collection`, and the current punctuation/capitalization of several other exact labels. Both original and canonical expected labels are saved per case.

Four legacy expected labels are not exact current-taxonomy targets and are excluded from exact-label denominators: unsuffixed Labor & Employment `Discrimination`, `Wage and Hour Claims`, and `Wrongful Discharge` (the current taxonomy branches these into employee/employer variants), plus the old standalone SSD label (current FETCH combines Social Security/SSI). They remain fully included in top-level category and question-coverage metrics. This exclusion was defined from taxonomy compatibility, not observed success or failure.

## Change and outcome matrices

- The primary set-presence outcome matrix crosses whether the expected initial category appeared anywhere initially with whether the expected final category appeared anywhere after a matched follow-up.
- `expected_final_category_set_transition_when_matched` and its exact-label counterpart directly compare membership of the expected final outcome before and after the hidden fact. `absent_initially_present_after` is the order-independent “newly added” count.
- Historical top/order matrices are retained only to avoid deleting generated intermediate data; they are outside the study criteria and are not used in the revised findings.
- Set transitions are paired observations, but they are not clean causal estimates. Cache disabling permits model variation, and the second prompt includes both a generated question and an answer. The three repeats help expose that variability.

## Candidate-label caution

The 1,000 expected outcomes are benchmark candidates, not adjudicated gold. The 800 new cases use the reviewed workbook to select realistic legal boundaries, especially multi-label boundaries, but their synthetic opening queries and hidden facts require expert human review before publication as accuracy claims. Metrics should be read as troubleshooting signals about FETCH under this frozen configuration.
