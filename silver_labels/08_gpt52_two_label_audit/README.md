# Stage 08 — Azure GPT-5.2 two-label audit

This stage is a fresh audit of the final AI silver-label dataset using Azure GPT-5.2. It asks whether each row is best represented by one label or by two distinct labels, and whether the existing final AI primary label remains supported.

## Inputs and prompt

- Original problem descriptions: `redaction_reviewed_v5_clean.xlsx`.
- Final AI silver-label context: [`../05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx`](../05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx).
- Current primary labels under audit: [`../04_review/final_review.json`](../04_review/final_review.json).
- Canonical taxonomy: `../app/data/taxonomy_detailed_descriptions.csv`, preserved as `taxonomy_snapshot.csv`.
- Provider/model: Azure OpenAI-compatible endpoint, `gpt-5.2`.
- Maximum returned labels: two.
- Keyword and SPOT classification: not used.

The exact prompt template is [`prompt_template.txt`](prompt_template.txt), and rendered prompts are in `prompts/`. The raw Azure responses are in `responses/`; normalized checkpointed outputs are in `checkpoint.json`. Runtime metadata, source hashes, model version, batch size, and the resume note are in [`run_metadata.json`](run_metadata.json).

The prompt deliberately supplies the current primary label for audit comparison but tells the model not to accept it automatically. It requires the second label to represent a distinct legal issue or explicitly requested service, not merely a neighboring taxonomy alternative or procedural reframing. The workbook treats returned labels as an unordered set; the raw ranked model assessment is retained separately for transparency.

## Results

| Audit result | Rows |
|---|---:|
| Current primary supported; one label sufficient | 297 |
| Current primary supported; two labels supported | 81 |
| Current primary supported; multi-label assessment uncertain | 2 |
| Current primary needs change; one label sufficient | 33 |
| Current primary needs change; two labels supported | 6 |
| Primary assessment uncertain; one label sufficient | 4 |
| Primary assessment uncertain; two labels supported | 3 |
| Primary assessment uncertain; multi-label assessment uncertain | 5 |

Headline counts:

- 90 rows were assessed as supporting two labels.
- 39 rows were assessed as needing a different primary label when label order is ignored.
- 12 rows had an uncertain primary assessment.
- 389 rows contain the existing primary somewhere in the unordered audit label set; 42 do not.
- 46 rows changed assessment when match order was ignored.
- 132 rows enter the review queue because they need a primary-label decision, have two labels, or are uncertain.

These are outputs from one fresh model audit, not independent-rater agreement. The “needs change” and “uncertain” results are review findings, not automatically applied corrections.

## Files

- [`redaction_reviewed_v5_clean_ai_silver_two_label_audit.xlsx`](redaction_reviewed_v5_clean_ai_silver_two_label_audit.xlsx) — review workbook. It carries forward the final AI silver workbook, adds the audit labels and justifications, and provides two blank human label slots.
- [`audit_summary.csv`](audit_summary.csv) — one-line summary for all 431 rows.
- [`review_queue.json`](review_queue.json) — rows requiring focused review.
- [`audit_results.json`](audit_results.json) — complete structured model audit, including problem text, current primary, labels, and justifications.
- [`analysis.json`](analysis.json) — machine-readable counts.
- [`TWO_LABEL_AUDIT_FINDINGS.md`](TWO_LABEL_AUDIT_FINDINGS.md) — human-readable interpretation and examples.

## Reproduction

From the repository root, with `../.env` or the process environment providing `OPENAI_API_KEY` and `OPENAI_BASE_URL`:

```bash
python run_two_label_gpt52_audit.py
```

The checkpoint makes the run resumable. This run initially completed some 20-row batches, then resumed with 10-row batches after a provider timeout; both sets of exact prompts and responses remain in this folder, and the metadata records that fact. A clean rerun can use the same script and checkpoint or a new output directory.
