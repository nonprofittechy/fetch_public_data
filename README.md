# FETCH research datasets and reproducibility materials

This repository is organized around the two publishable datasets named in the
companion paper, D1 and D2. Dataset D0 is intentionally not included: it is the
operational-label dataset from the earlier FETCH study and is not available for
full public release.

## Start here

| Paper dataset | Canonical public file | What it contains |
|---|---|---|
| **D1 — consensus labels** | [`datasets/d1_consensus_labels/d1_paper_dataset_355.csv`](datasets/d1_consensus_labels/d1_paper_dataset_355.csv) | 355 deduplicated, redacted legal-intake narratives with one to four consensus labels |
| **D2 — synthetic hidden facts** | [`datasets/d2_synthetic_flip/candidates/flip_candidates_v2.csv`](datasets/d2_synthetic_flip/candidates/flip_candidates_v2.csv) | 959 synthetic disclosure-grounded scenarios in 33 boundary families |

See [`datasets/README.md`](datasets/README.md) for provenance, intermediate
forms, row-count reconciliation, and the exact role of each file.

## Repository map

| Path | Purpose |
|---|---|
| [`datasets/`](datasets/) | D1 and D2, including their audit records and dataset-specific reproduction code |
| [`scripts/`](scripts/) | Shared labeling, adjudication, consensus, repair, scoring, and reporting utilities |
| [`tests/`](tests/) | Offline regression tests for the shared scripts |
| [`studies/`](studies/) | Readability/model-tier and deterministic-screening studies |
| [`prompts/`](prompts/) | Frozen runtime prompt snapshots |
| [`resources/`](resources/) | Shared taxonomy used to validate labels |
| [`configs/`](configs/) | Evaluation configuration |
| [`docs/`](docs/) | Cross-study findings and repository organization notes |

The shortest audit path is:

1. Read the [dataset index](datasets/README.md).
2. Inspect the D1 [labeling audit trail](datasets/d1_consensus_labels/labeling_audit/REVIEW_AUDIT_TRAIL.md)
   or D2 [methods and results](datasets/d2_synthetic_flip/README.md).
3. Use the matching command in [`scripts/README.md`](scripts/README.md).

## Validation

From the repository root:

```bash
python -m pytest -q tests datasets/d2_synthetic_flip/test_candidates.py \
  studies/screening_protocols/test_screening_protocols.py
python scripts/build_paper_d1.py
python datasets/d2_synthetic_flip/build_candidates.py
```

Model-backed reruns require provider credentials and, where noted, a compatible
FETCH checkout. Offline builders and analyses do not.
