# Reproducibility scripts

Scripts are grouped here so the repository root exposes datasets and study
documentation first. They use canonical paths from `repo_paths.py` and are
intended to be run from the repository root.

## Primary audit path

| Script | Role |
|---|---|
| `build_paper_d1.py` | Convert the 373-row normalized-text D1 view into the paper's 355-narrative dataset |
| `build_gold_consensus.py` | Reconstruct 431-row and 373-row consensus outputs from model and human evidence |
| `analyze_gold_rater_agreement.py` | Rebuild rater-set agreement artifacts |
| `reproduce_agreement_from_rater_sets.py` | Reproduce headline agreement from public normalized annotations alone |
| `analyze_fetch_gold_accuracy.py` | Score the frozen one-shot FETCH runs |
| `render_fetch_gold_findings.py` | Render paper-facing accuracy findings |
| `audit_fetch_provider_run.py` | Audit provider completeness and repair subsets |
| `prepare_fetch_repair.py` / `integrate_promptfoo_repair.py` | Preserve raw-run repair lineage |

## Labeling and adjudication lineage

`create_silver_labels.py`, `build_reviewed_silver.py`,
`review_human_labels.py`, `build_human_review_workspace.py`,
`audit_multilabel_candidates.py`, `build_multilabel_review_workspace.py`,
`run_two_label_gpt52_audit.py`, `prioritize_human_review.py`,
`build_four_label_review.py`, and `build_human_validated_gold.py` correspond to
the numbered stages under `datasets/d1_consensus_labels/labeling_audit/`.

Some stages call external models and require credentials. Their frozen prompts,
responses, checkpoints, and outputs are already stored in the audit directory.

## Scope exclusions

Five exploratory prototypes are outside the public reproducibility surface:
three workbook inspection/diff utilities and two superseded automatic-redaction
experiments. They depended on unavailable private inputs, had no tests or
command-line contract, were not referenced by the audit trail, and do not
reproduce a published artifact.
