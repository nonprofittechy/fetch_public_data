# Stage 02 — Gemini 3.1 Pro Preview pass

This folder contains the second independent LLM classification pass over all 431 data rows in `redaction_reviewed_v5_clean.xlsx`.

## What was done

- Model route: Gemini API.
- Model: `gemini-3.1-pro-preview`.
- Credential: `GEMINI_API_KEY`, read at runtime and never written to artifacts.
- Input: the problem description only; existing labels were not supplied as a shortcut.
- Taxonomy: the 209-row snapshot of `../app/data/taxonomy_detailed_descriptions.csv`, including detailed descriptions.
- Prompt: [`prompt_template.txt`](prompt_template.txt), rendered per batch in `prompts/batch_*.txt`.
- Batch size: 20 rows; 22 batches total.
- Output: up to three ranked exact category/subcategory pairs per row, with confidence and justification.
- Keyword classification and SPOT classification: not used.

## Results and audit trail

The normalized, taxonomy-validated output is in [`checkpoint.json`](checkpoint.json), and the row-level workbook is [`redaction_reviewed_v5_clean_gemini31_pro.xlsx`](redaction_reviewed_v5_clean_gemini31_pro.xlsx). Raw provider responses are in `responses/`; source hashes and model metadata are in [`run_metadata.json`](run_metadata.json); the exact taxonomy sent is [`taxonomy_snapshot.csv`](taxonomy_snapshot.csv).

The checkpoint is resumable. Re-run the command in the parent [`silver_labels/README.md`](../README.md) to reproduce the pass after the Gemini key is loaded from `../.env` or the process environment.
