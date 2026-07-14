# Stage 10 — four-label human-review workspace

This stage removes the former two-label ceiling from human adjudication. It re-reviews rows 252, 290, 384, 419–421, and 424 in the current Codex/GPT-5 context and gives the human reviewer four unordered label slots for every row in the 132-row priority queue.

No external API or credential was used in this pass. The executable record of the focused decisions is `FOCUSED_ADJUDICATIONS` in [`../../build_four_label_review.py`](../../build_four_label_review.py). The detailed taxonomy remains canonical.

## Focused result

| Row | Suggested labels | Important qualification |
|---:|---:|---|
| 252 | 4 | Divorce, military-family-law, immigration, and residential tenancy are visible. Immigration is medium confidence because status facts are explicit but an immigration service is not directly requested. |
| 290 | 3 | Copyright, defamation, and online harassment are three independently pleaded theories. |
| 384 | 3 | General trusts/estates, residential property transfer, and a VA loan are supported. Property Tax was rejected because its detailed description requires an assessment-value dispute. |
| 419 | 3 | Divorce, eviction, and a criminal case are named, but all exact subcategories are low-confidence placeholders because the row has no facts. |
| 420 | 3 | State workers' compensation, possible wrongful discharge, and deportation are distinct issues. The latter two need factual confirmation. |
| 421 | 4 | Guardianship, beneficiary litigation, personal injury, and a parking citation are separate matters. The litigation and parking-ticket mappings are low confidence because the taxonomy descriptions do not fit them exactly. |
| 424 | 4 | Veterans benefits, professional licensing, neighbor nuisance, and will drafting each map cleanly to a distinct detailed entry. |

These are review candidates, not final human labels. A human may select from zero to four labels and may replace any suggestion.

## Artifacts

- `redaction_reviewed_v5_clean_four_label_human_review.xlsx` — Stage 09 workbook plus four highlighted AI candidate slots, an overall justification, and four blank blue human-label slots with status, notes, reviewer, and timestamp fields.
- `review_cases.json` — complete seed data for the 132-row web review queue, including original label, internal primary, three independent model outputs, two-label audit, priority, expanded suggestions, rationales, confidence, and taxonomy descriptions.
- `taxonomy.json` — normalized 209-pair snapshot used by the web app's dropdowns and validation.
- `focused_multilabel_adjudication.json` — full structured evidence for the seven focused rows.
- `focused_multilabel_adjudication.csv` — compact extract of those seven rows.
- [`../../build_four_label_review.py`](../../build_four_label_review.py) — deterministic builder and the exact row-level adjudications.

The newly re-adjudicated AI cells are purple in the workbook. Human-entry cells are blue. Existing source and audit columns are preserved.

## Human review interface

[`../../human_review_app/`](../../human_review_app/) is the companion audit interface for all 132 queue rows. It exposes all 209 taxonomy pairs in four dropdowns, shows the enriched description under each choice, preloads but does not auto-save the AI suggestions, and keeps prior model/audit evidence visible. Human decisions persist in SQLite with an append-only save history and can be exported to CSV or JSON.

The app includes a tested container and valid Fly.io configuration with `/data` mounted for the database. It was not deployed in this stage: a production deployment should not be created until a shared review password, stable session secret, final app name, and associated Fly cost are intentionally accepted. Exact local and Fly commands are in the app README.

## Decision rubric

1. Treat the output as an unordered set; candidate position is not a preference or score.
2. Add a label only for a distinct requested legal service or independently meaningful issue in the text.
3. Use exact category/subcategory pairs from `../app/data/taxonomy_detailed_descriptions.csv` and apply its enriched descriptions.
4. Do not add neighboring labels for alternate procedural framings of one issue.
5. Do not force four labels. One, two, three, or four are all valid outcomes.
6. Preserve uncertainty when the text does not establish party role, legal posture, or a taxonomy element.

## Reproduction

From the repository root:

```bash
python build_four_label_review.py
```

The script validates every focused pair against the canonical taxonomy and writes deterministic XLSX/JSON/CSV outputs. It does not invoke a model. Reproducing the judgment itself means reviewing the static row text, rubric, detailed taxonomy descriptions, and row-level rationales embedded in the script.
