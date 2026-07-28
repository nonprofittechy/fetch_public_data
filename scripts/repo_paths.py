"""Canonical repository paths shared by the reproducibility scripts."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = REPO_ROOT / "datasets"
D1_DIR = DATASETS_DIR / "d1_consensus_labels"
D1_SOURCE = D1_DIR / "source_dataset.xlsx"
D1_AUDIT_DIR = D1_DIR / "labeling_audit"
D1_CONSENSUS_DIR = D1_DIR / "consensus"
D2_DIR = DATASETS_DIR / "d2_synthetic_flip"
TAXONOMY = REPO_ROOT / "resources" / "taxonomy_detailed_descriptions.csv"
