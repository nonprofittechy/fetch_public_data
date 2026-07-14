# Multi-label audit

This stage checks whether a row may legitimately have two or three labels. It is a post-hoc audit of the three completed LLM passes; it does not call an API and does not use keyword or SPOT classification.

## Method

For each row, I collected every exact category/subcategory pair appearing in each model's top-three ranked list. A pair counts as **model-supported** when at least two of the three independent passes included that exact pair. A row enters the candidate extract when at least two distinct pairs meet that threshold.

This is intentionally a generous review queue. Repeated model support is evidence that a second label deserves attention, not a final determination that it is correct. Some alternatives are different descriptions of the same issue; others reflect separate legal problems. The human reviewer should use the problem text and the canonical detailed taxonomy to make that distinction.

## Results

Of 431 rows, 156 (36.2%) have at least two distinct exact pairs supported by at least two models.

- Three-label candidates: 23.
- Two-label candidates: 52.
- Possible two-label candidates: 81.

The extract includes all model-supported alternatives, support counts, rank-1 support, every model that proposed each pair, and the original model justifications. The full JSON also preserves all top-three model candidates and the internal reviewed primary label.

## Files

- [`multilabel_candidate_rows.csv`](multilabel_candidate_rows.csv) — review queue, one row per candidate row.
- [`multilabel_candidate_evidence.json`](multilabel_candidate_evidence.json) — complete structured evidence for every candidate row.
- [`multilabel_analysis.json`](multilabel_analysis.json) — machine-readable counts and definitions.
- The prior [`../06_human_review_workspace/`](../06_human_review_workspace/) workbook remains the one-label human review workspace; this stage does not overwrite it.

## Reproduction

Run `python audit_multilabel_candidates.py` from the repository root after the completed model outputs and `silver_labels/04_review/final_review.json` are present.

## Model passes

The evidence combines GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4. The internal reviewed primary label is shown for context but is not counted as an independent model in the candidate definition.

