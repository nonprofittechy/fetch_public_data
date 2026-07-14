# Human review to validated gold data

The app keeps independent decisions by `(source row, reviewer ID)`. Two people can review the same row without overwriting one another. Reusing the same reviewer ID intentionally updates that reviewer's current decision; every save remains in `review_history`.

## Gold decision rule

Only reviews with status `accepted` or `corrected` and at least one selected label are eligible. Label order is ignored.

- If all eligible reviewers for a row selected the same exact label set, the row is included in gold.
- One eligible reviewer produces `single_reviewer_validated` gold.
- Two or more agreeing reviewers produce `multi_reviewer_consensus` gold.
- If eligible reviewers selected different sets, the row is excluded from gold and appears in the disagreement export. No majority vote silently resolves it.
- Draft (`needs_review`), needs-more-information, and skipped records never enter gold.

## Exports

From the authenticated application:

- `/export/gold.csv` — validated rows with one or more agreeing reviewers;
- `/export/gold.csv?min_reviewers=2` — strict two-or-more-reviewer consensus only;
- `/export/gold-disagreements.csv` — rows requiring adjudication;
- `/export.csv` and `/export.json` — all current reviewer records for provenance.

The gold CSV contains the original source text and label, one through four gold category/subcategory pairs, reviewer count and IDs, validation basis, and timestamp.

## Merge back into a repository dataset

Download the desired gold CSV, then validate it against the source workbook and canonical taxonomy:

```bash
python build_human_validated_gold.py \
  --gold-export ~/Downloads/human_validated_gold_min2.csv \
  --min-reviewers 2 \
  --mode reviewed-only \
  --output silver_labels/11_human_gold/human_validated_gold.csv \
  --report silver_labels/11_human_gold/human_validated_gold_report.json
```

Use `--mode full` to emit all 431 source rows, with blank gold fields and `gold_source=unreviewed` where validation is incomplete. The builder rejects text mismatches, invented taxonomy pairs, duplicate labels, invalid row numbers, and malformed label/reviewer counts.

For a final gold release, preserve alongside the merged CSV:

1. the raw `/export.json` provenance export;
2. the strict consensus CSV;
3. the disagreement CSV and subsequent adjudication record;
4. the generated validation report;
5. the application commit and export timestamp.
