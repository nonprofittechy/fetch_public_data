# Public redaction review data

This repository contains the public, cleaned redaction-review workbook and the Python utilities used during its preparation.

## Public dataset

[`redaction_reviewed_v5_clean.xlsx`](redaction_reviewed_v5_clean.xlsx) contains the columns:

- `problem_description`
- `expected_category`
- `expected_subcategory`

The original, unredacted question column and intermediate source files are not included.

The Python utilities expect local working inputs and are retained for reproducibility. The `privacy-filter` dependency is intentionally not vendored here because it is an existing public repository.

## Silver-label review record

The complete model-pass, adjudication, human-check, multi-label audit,
order-insensitive correction, and human-prioritization history is documented in
[`silver_labels/REVIEW_AUDIT_TRAIL.md`](silver_labels/REVIEW_AUDIT_TRAIL.md).

The latest review artifact allows up to four unordered labels per row. Use the
[`silver_labels/10_four_label_human_review/`](silver_labels/10_four_label_human_review/)
workbook or the persistent, taxonomy-aware
[`human_review_app/`](human_review_app/) browser interface.
