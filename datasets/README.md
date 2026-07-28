# Dataset index

The paper names three datasets. D0 is not publicly distributed in full; D1 and
D2 are both placed here under their paper identifiers.

## D1 — consensus-label dataset

Directory: [`d1_consensus_labels/`](d1_consensus_labels/)

The paper's canonical D1 file is
[`d1_paper_dataset_355.csv`](d1_consensus_labels/d1_paper_dataset_355.csv).
It contains 355 distinct narratives after removing separately redacted re-sends
and imported fragments from the earlier 373-row exact-text-deduplicated file.

The row counts represent successive, documented views of the same source:

| File | Rows | Role |
|---|---:|---|
| [`source_dataset.xlsx`](d1_consensus_labels/source_dataset.xlsx) | 431 | Public, cleaned source rows; preserves repeated deliveries |
| [`consensus/gold_labels_consensus_full_431.csv`](d1_consensus_labels/consensus/gold_labels_consensus_full_431.csv) | 431 | Consensus labels mapped back to every source-row identity |
| [`consensus/gold_labels_consensus_unique.csv`](d1_consensus_labels/consensus/gold_labels_consensus_unique.csv) | 373 | Deduplicated only on normalized redacted text; retained for the completed 373-case analyses |
| [`d1_paper_dataset_355.csv`](d1_consensus_labels/d1_paper_dataset_355.csv) | 355 | Paper dataset; also removes 18 semantic re-sends/fragments |

Rebuild the paper file with:

```bash
python scripts/build_paper_d1.py
```

The complete label-generation and human-review chronology is in
[`labeling_audit/REVIEW_AUDIT_TRAIL.md`](d1_consensus_labels/labeling_audit/REVIEW_AUDIT_TRAIL.md).
Agreement and one-shot evaluation artifacts are in
[`consensus/`](d1_consensus_labels/consensus/). The optional review application
is in [`human_review_app/`](d1_consensus_labels/human_review_app/).

## D2 — synthetic disclosure-grounded flip dataset

Directory: [`d2_synthetic_flip/`](d2_synthetic_flip/)

The canonical tabular file is
[`candidates/flip_candidates_v2.csv`](d2_synthetic_flip/candidates/flip_candidates_v2.csv):
959 scenarios across 33 boundary families. The equivalent JSON Lines export is
beside it. The [`authoring/`](d2_synthetic_flip/authoring/) directory preserves
the family-level authored inputs and vetting notes; [`analysis/`](d2_synthetic_flip/analysis/)
contains frozen study outputs.

Rebuild and validate D2 with:

```bash
python datasets/d2_synthetic_flip/build_candidates.py
python -m pytest -q datasets/d2_synthetic_flip/test_candidates.py
```

See [`d2_synthetic_flip/README.md`](d2_synthetic_flip/README.md) for the
two-step benchmark, pipeline snapshot, conditions, and model-backed rerun
requirements.

## D0 — operational-label dataset

D0 is described in the paper and in the earlier FETCH publication, but the
full operational dataset is not included here. This repository does not
reconstruct or substitute a different file for D0.
