# Human-review workspace

Use `redaction_reviewed_v5_clean_human_review_workspace.xlsx` for the next review.

The workbook includes the original human label, all ranked outputs from GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4, the internal reviewed label, and blue blank cells for `your_review_category`, `your_review_subcategory`, `your_review_status`, and `your_review_notes`.

The disagreement-only extract is `disagreement_rows.csv`; it includes all ranked candidates and justifications. Machine-readable counts are in `agreement_analysis.json`, and the human-readable interpretation is in [`DISAGREEMENT_AND_CONSENSUS.md`](DISAGREEMENT_AND_CONSENSUS.md).

## Agreement

Three independent models: 353 unanimous 3/3 (81.9%), 70 with 2/3 agreement (16.2%), and 8 all-distinct rows (1.9%). Any rank-1 disagreement: 78 rows.

Four displayed passes (three models plus the internal reviewed label): 353 unanimous 4/4 (81.9%), 55 with 3/4 agreement (12.8%), and 23 with 2/4 agreement (5.3%). Any four-pass disagreement: 78 rows.

Caveat: the internal reviewed label is derived from the three model outputs plus in-context review, so four-pass agreement is descriptive, not independent-rater reliability.

The original workbook and original human-label columns remain unchanged. The blank human fields are intentionally not prefilled.
