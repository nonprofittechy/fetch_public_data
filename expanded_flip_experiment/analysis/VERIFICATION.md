# Verification record

Verification performed from `/home/quinten/fetch/publishable-repo` on 2026-07-14 using `/home/quinten/fetch/.venv`.

## Candidate structure and coverage

Command:

```text
pytest -q expanded_flip_experiment/test_candidates.py
```

Result:

```text
....                                                                     [100%]
4 passed in 0.05s
```

The tests check the 1,000-row count, required fields and identifiers, 500/500 direction balance, taxonomy membership and opposing outcomes, and required multi-label/paper-failure/domestic-violence coverage.

## Python syntax

Command:

```text
python -m py_compile expanded_flip_experiment/build_candidates.py expanded_flip_experiment/run_experiment.py expanded_flip_experiment/run_direct.py expanded_flip_experiment/analyze_runs.py expanded_flip_experiment/build_quoted_evidence.py
```

Result: exit status 0 with no diagnostic output.

## PromptFoo reference configuration

Command:

```text
promptfoo validate -c expanded_flip_experiment/promptfooconfig.no-cache.yaml
```

Result: `Configuration is valid.` PromptFoo also printed a non-blocking version notice: installed `0.120.14`, latest advertised `0.121.19`.

## Paid-run integrity

Each official run is accepted only when all of the following hold:

1. `run_metadata.json` records `status: complete`.
2. `result_integrity.completed_cases` is 1,000 and `orchestrator_errors` is zero.
3. `results.json` contains exactly 1,000 case records.
4. The snapshotted candidate CSV has SHA-256 `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261`.
5. Per-case intermediate records remain in `results.partial.jsonl`.

The final three-run integrity check and result hashes are recorded after run 3 in `ARTIFACT_INDEX.md`.

## Paper-difference audit

Command:

```text
python expanded_flip_experiment/compare_on_wednesdays.py
```

The audit verified 200/200 copied legacy rows and zero textual mismatches for opening query, hidden fact, answer phrasing, or relevant-question topic. It reproduced the paper's 200-row reference counts, generated the same-scenario paired transitions, and wrote `on_wednesdays_difference_summary.json` plus `on_wednesdays_pair_comparison.csv`.
