# Disagreement analysis and final consensus justification

## Scope and definitions

The comparison covers 431 spreadsheet data rows. The three independent rank-1 passes were GPT-5.2, Gemini 3.1 Pro Preview, and DeepSeek v4. The “fourth pass” is the derived in-context reviewed primary label; it is included for transparency, but it is not an independent rater because it was chosen from the model evidence and problem text.

## Rank-1 agreement

| Comparison | Rows | Share |
|---|---:|---:|
| Three-model unanimous | 353 | 81.9% |
| Exactly two models agree | 70 | 16.2% |
| All three rank-1 labels differ | 8 | 1.9% |
| Any independent-model disagreement | 78 | 18.1% |

The 78 disagreement rows are listed in [`disagreement_rows.csv`](disagreement_rows.csv). That extract includes the original human label, each model’s rank-1 label, all ranked alternatives and justifications, the internal primary label, and the agreement pattern.

## Derived four-pass comparison

| Comparison | Rows | Share |
|---|---:|---:|
| Four displayed labels agree | 353 | 81.9% |
| Three of four agree | 55 | 12.8% |
| Two of four agree | 23 | 5.3% |
| Any four-pass disagreement | 78 | 18.1% |

The internal primary label matched all three model rank-1 labels on 353 rows, two models on 55 rows, and one model on 23 rows. This describes how the review resolved cases; it should not be reported as independent-rater reliability.

## How the final primary label was justified

The final primary label uses the most specific taxonomy pair supported by the row’s facts. A unanimous rank-1 result was retained unless the text made a more specific competing interpretation clear. Disagreement rows were read in context, with particular attention to the user’s requested help, the legal role or posture, and the detailed taxonomy descriptions. The review record stores the resulting explanation in `final_review.json`.

This creates a defensible primary-label consensus, but it does not force every row into one exclusive legal issue. Several rows explicitly contain multiple matters; that is why the separate [`07_multilabel_audit/`](../07_multilabel_audit/) stage collects repeated rank-2/rank-3 alternatives for human review.

## Important interpretation

Agreement among rank-1 labels measures convergence on a routing primary, not proof that the row has only one correct label. Conversely, disagreement does not prove that one model is wrong: it can reflect a genuine multi-issue request or neighboring taxonomy categories. Use the one-label workbook for primary-label review and the multi-label workbook for deciding whether additional labels should be retained.
