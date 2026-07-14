# Stage 04 — in-context primary-label review

This stage created the single primary AI silver label used by the existing silver workbook. It did not make API calls and did not use the supplied credentials.

## Review procedure

1. Compare each model's rank-1 exact category/subcategory pair.
2. Retain a unanimous three-model choice as the primary label.
3. For model disagreement, read the problem text, all ranked model candidates, their justifications, and the relevant detailed taxonomy descriptions.
4. Select the most specific supported primary pair and record the basis and justification.
5. Validate every selected pair against the canonical detailed taxonomy.

## Results

- 353 of 431 rows had unanimous 3/3 rank-1 agreement.
- 70 rows had a 2/3 rank-1 split.
- 8 rows had three different rank-1 labels.
- 77 rows were reviewed in context; one additional row retained a two-model consensus basis.
- The output workbook is [`redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx`](redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx).
- The complete row-level record is [`final_review.json`](final_review.json).

The primary-label decision is intentionally not a claim that lower-ranked alternatives are wrong. The later [`07_multilabel_audit/`](../07_multilabel_audit/) stage checks those alternatives as possible additional labels.
