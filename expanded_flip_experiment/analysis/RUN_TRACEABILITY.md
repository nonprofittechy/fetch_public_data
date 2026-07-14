# Run and finding traceability

This file maps reported findings to the exact raw and derived result filenames. Paths are relative to `expanded_flip_experiment/` unless they begin with `/home`.

## Official raw results

| Run | Raw result file | Raw SHA-256 | Derived scenario file | Derived SHA-256 |
|---|---|---|---|---|
| 1 | `results/final_run_1_20260714T170440Z/results.json` | `7a7dbfb7d78db699280708bbd81809ebb3f86ebb44c7369ed02c9021d1bf6302` | `analysis/runs/final_run_1_20260714T170440Z/scenario_details.csv` | `2e67c16d99a30c0622cfc59a0eac5927470974be005d43f44d1a8a687b371015` |
| 2 | `results/final_run_2_20260714T181957Z/results.json` | `9ef6e50d09c13ac6bfe473ec9f6a3f2beb1c831d75e9d8781cd1e3d686231977` | `analysis/runs/final_run_2_20260714T181957Z/scenario_details.csv` | `15c08419c809426b18edf892af5aa742e4bcbd4b037c8d4dc43d196cc2cb216a` |
| 3 | `results/final_run_3_20260714T193500Z/results.json` | `48f295d794f51688edfe817c6a79a2b0a2c24bd91542a2fc51030941be57ec4a` | `analysis/runs/final_run_3_20260714T193500Z/scenario_details.csv` | `30b5b15ff0735e675a82ce961e2590d01464e846cea56f7bf9df6927f38556af` |

The raw directories also contain `results.partial.jsonl`, `run_metadata.json`, `console.log`, `command.txt`, and frozen input/config/provider snapshots. Raw run directories are intentionally gitignored because of size; hashes and parsed public analysis files are committed.

All runs used candidate CSV SHA-256 `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261`.

## Original paper run

| Artifact | Path | SHA-256 |
|---|---|---|
| Original result | `/home/quinten/fetch/results/followup_fact_results.json` | `f8a00784ebf48fc4a7ee90fe9d86e3d7ae6375cf54a89628f886c17c7350a350` |
| Original 200 scenarios | `/home/quinten/fetch/promptfoo/individual_facts/classification_flip_scenarios.csv` | `22a95ba20893e54890d44c169088491481199e971852b4bd66ddbdf0517e587b` |
| Original PromptFoo config | `/home/quinten/fetch/promptfoo/followup_fact_experiment.yaml` | `35a18bf14b73c19b90bfa0f7ea3de95b1b01848a50846c3fca8a3606f14a6c63` |

`compare_on_wednesdays.py` verified that all 200 copied legacy rows have identical `opening_query`, `hidden_fact`, `fact_as_answer`, and `relevant_question_topic` text.

## Finding-to-file map

| Finding | Numerator / denominator | Primary machine source |
|---|---|---|
| Overall question coverage | 2,149 / 3,000 | `analysis/runs/cross_run_summary.json` → `pooled.question_coverage_pct`; rows in `analysis/runs/all_scenario_details.csv` |
| Expected final category among matches | 1,819 / 2,149 | `analysis/runs/cross_run_summary.json` → `pooled.final_category_accuracy_when_matched_pct` |
| Expected final exact label among scorable matches | 1,065 / 1,892 | same file → `pooled.final_exact_accuracy_when_matched_pct` |
| Historical paper-style rescues | 176 | `analysis/on_wednesdays_difference_summary.json`; recomputed from `all_scenario_details.csv` |
| Historical paper-style harms | 6 | same; requires initial correct, final wrong, and `top_category_changed=true` |
| Historical neutral failures to flip | 301 | same; initial correct, final wrong, `top_category_changed=false` |
| Category membership additions / losses | 47 / 48 | `cross_run_summary.json` → `pooled.expected_final_category_set_transition_when_matched` |
| Exact membership additions / losses | 122 / 102 | same → `pooled.expected_final_exact_set_transition_when_matched` |
| Same-200 legacy comparison | 600 pooled observations | `analysis/on_wednesdays_difference_summary.json` → `current_by_source.legacy_200_snapshot` |
| Pair-level paper comparison | ten legacy pairs | `analysis/on_wednesdays_pair_comparison.csv` |
| Domestic-violence explicit probes | 113 / 255 | `cross_run_summary.json` → `pooled.domestic_violence_hidden_fact` |

## Reproduction commands

```bash
source /home/quinten/fetch/.venv/bin/activate
python expanded_flip_experiment/analyze_runs.py
python expanded_flip_experiment/compare_on_wednesdays.py
python expanded_flip_experiment/build_quoted_evidence.py
```

`analysis/SHA256SUMS.txt` hashes the committed experiment artifacts plus local raw/intermediate files present when the analysis was finalized.
