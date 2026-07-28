# Focused adjudication method

## Reviewer and execution context

- Reviewer: Codex internal context review, based on GPT-5.
- Execution date: 2026-07-14.
- External model/API calls: none.
- User API keys: not accessed.
- Canonical guide: `../app/data/taxonomy_detailed_descriptions.csv` (209 exact pairs).
- Inputs: the seven source problem descriptions, original human labels, Stage 04 internal primaries, all three independent models' candidates and explanations, the Stage 08 unordered audit, and Stage 09 priority notes.

Unlike an API pass, this in-context review has no separately submitted hidden system prompt or provider response payload. The complete task instruction and decision rubric are recorded below, and every output decision is encoded in `build_four_label_review.py` for deterministic regeneration.

## Review instruction

> Carefully re-adjudicate rows 252, 290, 384, 419–421, and 424 against the canonical detailed taxonomy. Treat matches as an unordered set. Permit up to four matches and let the number follow the distinct legal issues in the row rather than a target count. Include an exact taxonomy pair only when the text supports a separate requested service or independently meaningful issue. Preserve ambiguity and explain taxonomy mismatches. Do not call external APIs.

## Review sequence

1. Read the full source text without assuming the current label is correct.
2. Enumerate distinct legal problems before looking at label count.
3. Compare each problem against the enriched taxonomy descriptions.
4. Reject candidates that are merely alternate framings or fail a key description element.
5. Compare the resulting set with all prior passes to identify omissions caused by the two-label ceiling.
6. Record one to four exact pairs, per-pair confidence and rationale, and an overall consensus justification.
7. Mark boundary cases for human verification instead of resolving missing facts by assumption.

## Reproducibility note

Candidate order carries no meaning. JSON list order is stable only to make generated artifacts deterministic. Human review and agreement calculations must compare sets of exact category/subcategory pairs.
