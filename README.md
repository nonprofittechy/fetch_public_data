# Public redaction review data

This repository contains the public, cleaned redaction-review workbook and the Python utilities used during its preparation.

## Public dataset

[`redaction_reviewed_v5_clean.xlsx`](redaction_reviewed_v5_clean.xlsx) contains the columns:

- `problem_description`
- `expected_category`
- `expected_subcategory`

The original, unredacted question column and intermediate source files are not included.

The Python utilities expect local working inputs and are retained for reproducibility. The `privacy-filter` dependency is intentionally not vendored here because it is an existing public repository.
