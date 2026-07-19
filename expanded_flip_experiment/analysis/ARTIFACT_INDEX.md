# Artifact index

This index points to the main study artifacts. `SHA256SUMS.txt` contains hashes for 181 source, input, intermediate, raw-result, and analysis files under `expanded_flip_experiment/` (excluding transient Python/pytest caches and the checksum file itself).

## Inputs and design

- `../candidates/expanded_flip_candidates_1000.csv` and `.jsonl`: frozen 1,000-candidate dataset.
- `source_dataset_profile.json`: workbook and benchmark counts.
- `multilabel_seed_rows.csv`: 93 reviewed workbook rows with at least two candidate labels.
- `HARDEST_SOURCE_SCENARIOS.md` and `PAPER_FAILURE_MODES.md`: design anchors from reviewed multi-label material and *On Wednesdays*.
- Local-only `on_wednesdays_extracted.txt`: layout-preserving PDF extraction used to check the prior tables; ignored with the source PDF to avoid republishing the paper in this dataset commit.
- `../build_candidates.py` and `../test_candidates.py`: deterministic builder and structural tests.

## Execution and reproducibility

- `EXECUTION_LOG.md`: chronological smoke, pilot, official-run, and analysis decisions. Failed and stopped pilots are retained rather than erased.
- `../run_experiment.py`: archived PromptFoo runner used during qualification.
- `../run_direct.py`: official concurrent runner with per-case fsynced JSONL output.
- `../two_step_provider_bridge.py`: compatibility bridge that forces FETCH provider caching off.
- `../promptfooconfig.no-cache.yaml`: PromptFoo reference condition, also cache-disabled.
- `VERIFICATION.md`: passing tests, syntax checks, configuration validation, and run-integrity criteria.

## Official paid raw runs

Each directory contains `command.txt`, `run_metadata.json`, frozen dataset/config/provider snapshots, `console.log`, incrementally written `results.partial.jsonl`, and final `results.json`.

| Run | Cases | Orchestration errors | Elapsed | Final JSON SHA-256 |
|---|---:|---:|---:|---|
| `results/final_run_1_20260714T170440Z/` | 1,000 | 0 | 4,090.66 s | `7a7dbfb7d78db699280708bbd81809ebb3f86ebb44c7369ed02c9021d1bf6302` |
| `results/final_run_2_20260714T181957Z/` | 1,000 | 0 | 4,141.08 s | `9ef6e50d09c13ac6bfe473ec9f6a3f2beb1c831d75e9d8781cd1e3d686231977` |
| `results/final_run_3_20260714T193500Z/` | 1,000 | 0 | 3,864.67 s | `48f295d794f51688edfe817c6a79a2b0a2c24bd91542a2fc51030941be57ec4a` |

All three metadata files record dataset SHA-256 `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261` and the same frozen intended-fact, GPT-5 + keyword, concurrency-4, 60-second, cache-disabled condition.

## Analysis outputs

- `runs/final_run_*/`: per-run `summary.json`, full `scenario_details.csv`, grouped tables, and quote candidates.
- `runs/cross_run_summary.json`: run-level means/ranges, pooled metrics, operational counts, and stability distributions.
- `runs/all_scenario_details.csv`: all 3,000 parsed observations.
- `runs/scenario_stability.csv`: one row per scenario across three runs.
- `runs/pooled_by_*.csv`: pooled pair, failure-mode, source, direction, multi-label, and DV strata.
- `METRIC_DEFINITIONS.md`: exact definitions for elicitation, order-independent set presence, membership transitions, and limitations.
- `TAXONOMY_COMPATIBILITY_AUDIT.md`: alias mapping and exact-denominator exclusions.
- `ON_WEDNESDAYS_DIFFERENCE_AUDIT.md`: root-cause analysis of dataset, pair, hidden-fact, system-condition, and outcome-matrix differences.
- `on_wednesdays_difference_summary.json` and `on_wednesdays_pair_comparison.csv`: reproducible machine-readable comparison outputs.
- `RUN_TRACEABILITY.md`: finding-to-result-file map with raw and derived SHA-256 hashes.
- `QUOTED_EVIDENCE.md`: reproducibly selected three-run result excerpts; scenario list fixed before run 3 inspection.
- `INITIAL_TAKE.md`: quote-grounded initial interpretation.
- `analyzer_final_console.txt`: saved console output from the final analysis build.

## Preserved intermediate checkpoints

- `intermediate/cross_run_summary_after_2_runs.json`
- `intermediate/scenario_stability_after_2_runs.csv`
- `intermediate/QUOTED_EVIDENCE_after_2_runs.md`
- `intermediate/INITIAL_TAKE_DRAFT_AFTER_2_RUNS.md`

The raw smoke tests and every stopped throughput/timeout pilot named in `EXECUTION_LOG.md` remain in `../results/`. These results are gitignored because of size and possible sensitive operational metadata, but they are not deleted.
