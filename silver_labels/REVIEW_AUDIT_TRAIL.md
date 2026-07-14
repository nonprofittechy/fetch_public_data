# Central silver-label review and audit trail

This is the canonical index of every classification, review, audit, and prioritization pass completed for `redaction_reviewed_v5_clean.xlsx` during this work. Stage-specific READMEs contain additional detail; this document records the chronology, methods, results, current interpretation, and remaining human work in one place.

## Current status

- Dataset: 431 problem-description rows plus one header row.
- Canonical taxonomy: `../app/data/taxonomy_detailed_descriptions.csv`, containing 209 detailed category/subcategory entries.
- Primary silver labels: complete for all 431 rows in [`04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx`](04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx).
- Original human-label cross-check: 9 paper examples checked; 4 corrections recorded in the derived Stage 05 workbook.
- Multi-label conclusion: one exclusive label is inadequate for a material subset of rows.
- Latest two-label audit: 90 rows support two labels; after ignoring order, 39 rows are primary-change candidates and 12 remain uncertain.
- Latest human-review queue: 132 rows, prioritized into 52 P1, 14 P2, and 66 P3 rows.
- The two-label ceiling has been removed from the human workflow. The seven known 3–4 issue rows now have expanded unordered sets: rows 252/421/424 have four candidates and rows 290/384/419/420 have three.
- The Stage 10 workbook and web app allow the human to assign zero through four exact taxonomy pairs and retain all prior evidence. The app now stores independent decisions per reviewer, displays `Category > Subcategory`, and produces conservative gold and disagreement exports.
- The persistent review app is live at <https://fetch-silver-label-review.fly.dev/> in the Lemma Fly organization. It uses one auto-stopping 256 MB Machine in `iad`, an encrypted 1 GB volume, and password/session credentials stored as Fly secrets.
- Human adjudication is not yet complete. Audit and priority fields are recommendations; they have not overwritten the Stage 04 primary labels.
- The original `redaction_reviewed_v5_clean.xlsx` remains unchanged.

## Shared classification rules

All external-model classification passes used the detailed taxonomy rather than the simpler label-only taxonomy. Returned pairs were validated against the exact taxonomy pair set. The sole normalization was the source capitalization typo `General litigation` → `General Litigation`; no subcategories or descriptions were rewritten.

Keyword and SPOT classification were not used. Credentials were loaded from the process environment or `../.env` and were not written to artifacts. Exact rendered prompts, taxonomy snapshots, checkpoints, model metadata, and provider responses where captured are stored in the relevant stage folders.

## Chronological stage index

| Stage | Pass | Method/model | Main result | Primary artifacts |
|---|---|---|---|---|
| 01 | Independent classification | Azure `gpt-5.2`; up to 3 ranked matches | 431 taxonomy-valid row outputs | [`01_gpt52/`](01_gpt52/) |
| 02 | Independent classification | Gemini API `gemini-3.1-pro-preview`; same prompt/schema | 431 taxonomy-valid row outputs | [`02_gemini31_pro/`](02_gemini31_pro/) |
| 03 | Independent classification | Azure `deepseek-v4`; same prompt/schema | 431 taxonomy-valid row outputs | [`03_deepseek_v4/`](03_deepseek_v4/) |
| 04 | Primary-label adjudication | Internal context review; no API | One reviewed primary label and justification per row | [`04_review/`](04_review/) |
| 05 | Existing human-label cross-check | Internal review of `thats_so_fetch.pdf`, Table 3 | 9 examples checked; 4 human labels corrected in a derived workbook | [`05_human_label_review/`](05_human_label_review/) |
| 06 | Agreement analysis and human workspace | Deterministic comparison of 3 models plus derived review | 78 exact-pair disagreement rows; blank human fields added | [`06_human_review_workspace/`](06_human_review_workspace/) |
| 07 | Broad multi-label evidence audit | Post-hoc comparison of all three models' top-3 candidates; no API | 156 rows with ≥2 exact pairs repeated by ≥2 models | [`07_multilabel_audit/`](07_multilabel_audit/) |
| 08 | Focused two-label audit | Fresh Azure `gpt-5.2`; current primary supplied for audit; max 2 labels | 90 two-label rows; order-insensitive assessment and 132-row review queue | [`08_gpt52_two_label_audit/`](08_gpt52_two_label_audit/) |
| 09 | Human-review prioritization | Current Codex/GPT-5 internal context review; no external API | Queue divided into 52 P1, 14 P2, and 66 P3 rows | [`09_internal_priority_review/`](09_internal_priority_review/) |
| 10 | Cap-free focused adjudication and human interface | Current Codex/GPT-5 context; no external API; deterministic artifact builder | Seven 3–4 issue rows expanded; four human slots; persistent review app | [`10_four_label_human_review/`](10_four_label_human_review/), [`../human_review_app/`](../human_review_app/) |

## Stages 01–03: independent model passes

The three passes received problem descriptions and the full detailed taxonomy. Existing expected labels were not supplied as a shortcut. Each model returned one to three ranked exact taxonomy matches with confidence and a concise explanation.

| Folder | Provider | Model | Exact prompt source |
|---|---|---|---|
| [`01_gpt52/`](01_gpt52/) | Azure OpenAI-compatible chat completions | `gpt-5.2` | `create_silver_labels.py:build_prompt`; rendered files under `prompts/` |
| [`02_gemini31_pro/`](02_gemini31_pro/) | Gemini generate-content API | `gemini-3.1-pro-preview` | Same builder and taxonomy; rendered files under `prompts/` |
| [`03_deepseek_v4/`](03_deepseek_v4/) | Azure OpenAI-compatible chat completions | `deepseek-v4` | Same builder and taxonomy; rendered files under `prompts/` |

The shared runner is [`../create_silver_labels.py`](../create_silver_labels.py). Each stage README and `run_metadata.json` records the source hashes, taxonomy hash, provider route, and output files.

## Stage 04: reviewed primary silver label

The internal pass compared the three rank-1 pairs, read competing justifications and detailed taxonomy entries for difficult rows, and selected one primary routing label. It made no API call.

Agreement before adjudication:

| Rank-1 comparison | Exact category/subcategory | Top-level category only |
|---|---:|---:|
| Unanimous 3/3 | 353 (81.9%) | 403 (93.5%) |
| Exactly 2/3 agree | 70 (16.2%) | 27 (6.3%) |
| All three differ | 8 (1.9%) | 1 (0.2%) |

Review basis in `final_review.json`:

- 353 rows retained three-model consensus;
- 77 rows received explicit in-context review;
- 1 row retained a two-model-consensus basis.

The output is a defensible primary routing label, not a claim that lower-ranked alternatives are wrong or that each row has only one issue. See [`04_review/README.md`](04_review/README.md) and [`04_review/final_review.json`](04_review/final_review.json).

## Stage 05: existing human-label check

Nine error examples from `interim_not_to_commit/thats_so_fetch.pdf`, Table 3 on PDF page 199, were checked. Four original human labels were corrected in the derived workbook:

- row 149: Consumer Law → Criminal Law / Post Conviction/ Appeals;
- row 188: Criminal Law → Consumer Law / Small Claims Advice;
- row 220: Debtor/Creditor → Administrative Law / Unemployment;
- row 339: Labor & Employment → Administrative Law / Professional Licensing.

The other five examples agreed at the top-level category. This was a targeted check of the paper examples, not a full human relabeling of all 431 rows. See [`05_human_label_review/README.md`](05_human_label_review/README.md).

## Stage 06: agreement and first human-review workspace

This stage exposed the original human label, all three models' ranked candidates and explanations, the internal reviewed label, agreement fields, and blank blue human-entry cells. It also produced a 78-row exact rank-1 disagreement extract.

The “fourth pass” in the four-pass comparison is the derived internal label, not an independent rater. Therefore the four-pass counts are descriptive and should not be reported as independent inter-rater reliability. See [`06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md`](06_human_review_workspace/DISAGREEMENT_AND_CONSENSUS.md).

## Stage 07: broad multi-label audit

This post-hoc audit ignored candidate order and counted an exact pair as model-supported when at least two of the three independent models included it anywhere in their top-three lists. A row entered the broad queue when at least two distinct pairs met that rule.

Results:

- 156/431 rows (36.2%) entered the broad multi-label evidence queue;
- 23 were three-label candidates;
- 52 were stronger two-label candidates under the audit's rank-support rule;
- 81 were possible two-label candidates.

This intentionally favors recall. Repeated alternatives can still be competing framings of one issue, so the 156 count is not a final multi-label prevalence estimate. See [`07_multilabel_audit/README.md`](07_multilabel_audit/README.md) and [`07_multilabel_audit/MULTILABEL_FINDINGS.md`](07_multilabel_audit/MULTILABEL_FINDINGS.md).

## Stage 08: fresh Azure GPT-5.2 two-label audit

GPT-5.2 received each problem, the current Stage 04 primary label for audit comparison, and the detailed taxonomy. It was required to return exactly one or two valid pairs and to add a second pair only for a distinct issue or explicitly requested service. Exact prompts and raw Azure responses are stored under `prompts/` and `responses/`.

The original model response was ranked, producing raw assessment counts of 338 `supported`, 81 `needs_change`, and 12 `uncertain`. The user then clarified that label order is irrelevant. Stage 08 was therefore recalculated as an unordered-set comparison while preserving the raw ranked assessment in a separate field.

Final order-insensitive interpretation:

| Result | Rows |
|---|---:|
| Existing primary supported | 380 |
| Existing primary needs change | 39 |
| Primary assessment uncertain | 12 |
| Existing primary appears anywhere in audit set | 389 |
| Existing primary absent from audit set | 42 |
| Two labels supported | 90 |
| Multi-label decision uncertain | 7 |
| Union review queue | 132 |

Forty-six rows changed assessment when order was removed: most were raw `needs_change` decisions where the current label was still present as the other returned label; two raw `supported` decisions did not actually include the current label and were corrected by set membership.

Use `two_label_audit_primary_assessment` for the order-insensitive decision. `two_label_audit_model_primary_assessment` preserves the raw ranked response, and `two_label_audit_current_primary_in_label_set` shows exact set membership. See [`08_gpt52_two_label_audit/README.md`](08_gpt52_two_label_audit/README.md).

## Stage 09: internal priority pass

The 132-row order-insensitive queue received another internal context review after the model-strength change. No external API or user credential was used. The pass considered the full text, current label, unordered audit set, original three-model agreement, Stage 07 evidence, sparse descriptions, taxonomy boundaries, audit inconsistencies, and rows exceeding the two-label cap.

Results:

- 52 P1 — human decision essential;
- 14 P2 — human confirmation recommended;
- 66 P3 — quick confirmation likely sufficient.

P1 is an attention priority, not a prediction that the label is wrong. The highest-scored rows begin with 27, 325, 419, 17, 299, 213, 28, 252, 384, 128, 172, 196, 307, 430, and 139. See [`09_internal_priority_review/README.md`](09_internal_priority_review/README.md).

## Stage 10: four-label focused review and persistent human interface

The seven rows previously flagged as exceeding the two-label ceiling were read again against the enriched descriptions, all prior model candidates, the Stage 04 primary, the unordered Stage 08 audit, and Stage 09 notes. This was an internal context review with no external API or credential use. Candidate order remains irrelevant.

| Row | Candidate count | Set-level conclusion |
|---:|---:|---|
| 252 | 4 | Divorce, military family law, immigration, and residential tenancy; immigration is medium confidence. |
| 290 | 3 | Copyright, defamation, and online harassment. |
| 384 | 3 | General trust/estate planning, residential property transfer, and VA loan; Property Tax rejected under its assessment-dispute description. |
| 419 | 3 | Divorce, tenant eviction, and generic criminal matter, all low confidence because facts and party role are absent. |
| 420 | 3 | State workers' compensation, possible wrongful discharge, and deportation. |
| 421 | 4 | Guardianship, possible beneficiary litigation, personal injury, and a parking citation; the beneficiary-litigation and parking mappings are marked as taxonomy-boundary decisions. |
| 424 | 4 | Veterans benefits, professional licensing, neighbor nuisance, and will drafting. |

These are proposed review sets, not final human labels. The focused instructions, reviewer context, exact rationales, and per-pair confidence are recorded in [`10_four_label_human_review/ADJUDICATION_METHOD.md`](10_four_label_human_review/ADJUDICATION_METHOD.md), `focused_multilabel_adjudication.json`, and [`../build_four_label_review.py`](../build_four_label_review.py).

The new workbook preserves all preceding columns, highlights the focused AI candidates in purple, and supplies four blue human-label slots plus status, notes, reviewer, and timestamp. Its companion [`../human_review_app/`](../human_review_app/) exposes all 209 exact pairs and descriptions and saves current decisions by `(row, reviewer)` plus append-only history. Labels display as `Category > Subcategory`; status uses no-default radios; `Save review + next` automatically records accepted versus corrected from an unordered-set comparison; supporting evidence is collapsed to reduce distraction.

Gold generation is deterministic and conservative: completed agreeing sets enter gold, two agreeing humans are marked `multi_reviewer_consensus`, and disagreements are excluded into a separate export. [`../human_review_app/GOLD_DATA_WORKFLOW.md`](../human_review_app/GOLD_DATA_WORKFLOW.md) documents the rule and [`../build_human_validated_gold.py`](../build_human_validated_gold.py) validates/merges an app export back into the source dataset.

Unit tests, a Gunicorn smoke test, a Docker bind-mount persistence test, and `fly config validate` passed. The app was deployed on 2026-07-14 at <https://fetch-silver-label-review.fly.dev/> in the `lemma` organization. Production E2E used two isolated reviewer sessions on one row, confirmed strict two-reviewer gold consensus, explicitly stopped the Machine, cold-started it through HTTPS, and verified both records and consensus survived on `/data`. It also confirmed the no-default status guard and automatic corrected status. E2E data was removed afterward; three earlier drafts were preserved as `Legacy reviewer`.

## Recommended files now

| Purpose | File |
|---|---|
| Stable one-label silver baseline | [`04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx`](04_review/redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx) |
| Human-checked paper examples | [`05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx`](05_human_label_review/redaction_reviewed_v5_clean_ai_silver_reviewed_human_checked.xlsx) |
| Most current human-review workbook | [`10_four_label_human_review/redaction_reviewed_v5_clean_four_label_human_review.xlsx`](10_four_label_human_review/redaction_reviewed_v5_clean_four_label_human_review.xlsx) |
| Browser-based human review | <https://fetch-silver-label-review.fly.dev/>; source and operations in [`../human_review_app/`](../human_review_app/) |
| Focused seven-row adjudication | [`10_four_label_human_review/focused_multilabel_adjudication.csv`](10_four_label_human_review/focused_multilabel_adjudication.csv) |
| P1-only review extract | [`09_internal_priority_review/highest_priority_rows.csv`](09_internal_priority_review/highest_priority_rows.csv) |
| Full prioritized queue | [`09_internal_priority_review/prioritized_review_queue.csv`](09_internal_priority_review/prioritized_review_queue.csv) |

## What remains

1. Have each human choose a distinct reviewer ID and review the 52 P1 rows first.
2. Confirm the 14 P2 rows and rapidly accept/correct the 66 P3 rows.
3. Download strict two-reviewer gold and the disagreement export; adjudicate disagreements explicitly.
4. Run `build_human_validated_gold.py` to validate and merge the app export into a consolidated one-through-four-label gold dataset.
5. Keep the Stage 04 primary label and all model/audit evidence in the final provenance record rather than silently replacing them.

## Reproduction scripts

| Script | Purpose |
|---|---|
| [`../create_silver_labels.py`](../create_silver_labels.py) | Initial independent LLM passes and validation |
| [`../build_reviewed_silver.py`](../build_reviewed_silver.py) | Stage 04 reviewed primary workbook |
| [`../review_human_labels.py`](../review_human_labels.py) | Stage 05 paper-example human-label check |
| [`../build_human_review_workspace.py`](../build_human_review_workspace.py) | Stage 06 agreement workspace |
| [`../audit_multilabel_candidates.py`](../audit_multilabel_candidates.py) | Stage 07 broad multi-label evidence audit |
| [`../build_multilabel_review_workspace.py`](../build_multilabel_review_workspace.py) | Stage 07 review workbook |
| [`../run_two_label_gpt52_audit.py`](../run_two_label_gpt52_audit.py) | Stage 08 Azure two-label audit and order-insensitive outputs |
| [`../prioritize_human_review.py`](../prioritize_human_review.py) | Stage 09 priority queue and workbook |
| [`../build_four_label_review.py`](../build_four_label_review.py) | Stage 10 expanded sets, four-slot workbook, app seed, and taxonomy snapshot |
| [`../build_human_validated_gold.py`](../build_human_validated_gold.py) | Validate an app gold export and merge it with the 431-row public source |

## Commit trail

| Commit | Work captured |
|---|---|
| `29ffa64` | Multi-model human-review workspace and initial classification/review artifacts |
| `f609d36`, `c9777a0` | Multi-label candidate audit implementation and generated outputs |
| `25b3728` | Per-stage documentation and agreement review |
| `56cd621`, `0b22b90` | Multi-label findings, review guidance, and reproducible workbook generation |
| `25a3282` | Azure GPT-5.2 two-label audit |
| `f6f67a8` | Order-insensitive two-label interpretation |
| `d6c279e` | Internal prioritization of the human-review queue |
| `2093ec8` | Canonical central review/audit trail through Stage 09 |
| `8e40744` | Seven-row three/four-label adjudication and expanded workbook |
| `6fbc86d` | Persistent taxonomy-aware human review app and Fly-ready deployment artifact |
| `9760c54` | Correct Fly Dockerfile resolution and restricted remote build context |
| `7e2daaa` | Independent per-reviewer decisions, concise UI, automatic status, and gold/disagreement exports |

Future review or label-changing commits should be appended here and linked to their stage documentation.
