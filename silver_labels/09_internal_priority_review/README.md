# Stage 09 — internal human-review prioritization

This stage prioritizes the 132 rows in the order-insensitive Azure GPT-5.2 review queue. It was performed inside the current Codex/GPT-5 context and did not call an external model or use credentials from `../.env`.

## Result

| Priority | Rows | Meaning |
|---|---:|---|
| P1 — human decision essential | 52 | Sparse facts, a substantive taxonomy boundary, conflicting evidence, more than two issues, or an internally inconsistent audit result makes human adjudication materially valuable. |
| P2 — human confirmation recommended | 14 | The proposed change or additional label is plausible, but should be checked against the detailed taxonomy before finalization. |
| P3 — confirmation likely sufficient | 66 | The text expressly names separate issues and the existing label remains in the unordered audit set; a quick accept/remove decision is likely enough. |

Priority is not a prediction that a label is wrong. It measures the expected value of human attention.

## Highest-priority patterns

The P1 queue is dominated by five recurring problems:

1. **Insufficient facts:** rows 17, 27, 176, 196, 299, 307, 325, 419, 429, and 430 cannot be resolved reliably from the text alone.
2. **Taxonomy boundaries:** examples include Animal Law versus Personal Injury (62/266), Actions Against Police versus Tort Claims Act (74/279), and securities versus general litigation (136).
3. **More issues than the two-label cap:** rows 252, 290, 384, 419–421, and 424 contain three or four meaningful issues.
4. **Questionable audit substitutions:** examples include mapping a camper-van build to Real Property/Construction (155), replacing explicit divorce with Military plus Tenant (252), and adding Third Party Workers' Comp without an identified third party (349).
5. **Overlapping legal posture and subject matter:** creditor-versus-underlying-dispute rows such as 4, 128, 212, and 213 require a decision about whether the taxonomy routes by posture, subject matter, or both.

The first rows by priority score are 27, 325, 419, 17, 299, 213, 28, 252, 384, 128, 172, 196, 307, 430, and 139. The complete P1 list and row-specific reasons are in `highest_priority_rows.csv`.

## Files

- [`redaction_reviewed_v5_clean_ai_silver_prioritized_human_review.xlsx`](redaction_reviewed_v5_clean_ai_silver_prioritized_human_review.xlsx) — the order-insensitive audit workbook with colored priority, score, reason, recommended action, evidence signals, and the existing human-entry fields.
- [`highest_priority_rows.csv`](highest_priority_rows.csv) — the 52 P1 rows, sorted by expected value of human review.
- [`prioritized_review_queue.csv`](prioritized_review_queue.csv) — all 132 rows sorted into P1/P2/P3.
- [`priority_analysis.json`](priority_analysis.json) — machine-readable counts and P1 row numbers.
- [`../../prioritize_human_review.py`](../../prioritize_human_review.py) — the reproducible prioritization and workbook builder.

## Method

For each queue row, the pass considered:

- the full problem description;
- the current final AI label;
- the unordered one- or two-label GPT-5.2 audit set;
- whether the current label was absent, supported, or uncertain;
- the three original models' rank-1 agreement pattern;
- repeated multi-label evidence from Stage 07;
- sparse descriptions, audit inconsistencies, taxonomy boundaries, and cases exceeding the two-label cap.

The script contains explicit row-level notes for P1 cases and a documented evidence score for sorting within tiers. It does not modify any final label.

## Reproduction

From the repository root:

```bash
python prioritize_human_review.py
```
