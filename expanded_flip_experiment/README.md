# Expanded 1,000-candidate FETCH flip benchmark

This folder contains a deterministic, reviewable candidate benchmark for testing whether FETCH asks a question that elicits a hidden legally decisive fact and then uses the answer correctly. The candidates are not gold labels: the expanded synthetic rows and the 200 legacy rows should receive human validation before publication or use as a definitive accuracy benchmark.

## What is included

- `candidates/expanded_flip_candidates_1000.csv` and `.jsonl`: 1,000 candidates, balanced 500/500 across A→B and B→A directions.
- `build_candidates.py`: offline builder; it makes no API or model calls.
- `analysis/source_dataset_profile.json`: source-workbook and generated-benchmark counts.
- `analysis/multilabel_seed_rows.csv`: the 93 reviewed-workbook rows with at least two four-label candidates, retained for review and provenance.
- `analysis/HARDEST_SOURCE_SCENARIOS.md`: a concise map of difficult reviewed rows to the new decision boundaries.
- `analysis/PAPER_FAILURE_MODES.md`: the prior paper's hardest hidden-fact cases and how this benchmark covers them.
- `promptfooconfig.no-cache.yaml`, `two_step_provider_bridge.py`, and `run_no_cache_replicates.sh`: paired intended/counterfactual reference design with both PromptFoo and FETCH caches disabled.
- `run_experiment.py`: one-run-at-a-time documented runner that archives hashes, environment metadata, snapshots, console output, and raw JSON.
- `run_direct.py`: concurrent official runner using the same two-step provider; it fsyncs every completed case to an intermediate JSONL journal before producing final JSON.
- `analyze_runs.py`: reproducible per-run, pooled, stability, outcome-matrix, and quote-evidence analysis.
- `analysis/EXECUTION_LOG.md`: append-only human-readable run index.
- `analysis/METRIC_DEFINITIONS.md` and `analysis/TAXONOMY_COMPATIBILITY_AUDIT.md`: scoring semantics, legacy/current label normalization, and exact-label denominator rules.
- `analysis/ON_WEDNESDAYS_DIFFERENCE_AUDIT.md` and `compare_on_wednesdays.py`: reproducible explanation of differences from the paper, including the corrected rescue/harm calculation and same-200-scenario comparison.
- `analysis/RUN_TRACEABILITY.md`: exact raw/derived filenames and hashes behind each headline finding.
- `analysis/INITIAL_TAKE.md` and `analysis/QUOTED_EVIDENCE.md`: three-run interpretation and reproducibly selected raw-result excerpts (created after the official runs).
- `analysis/VERIFICATION.md` and `analysis/ARTIFACT_INDEX.md`: test record and artifact/hash index.
- `test_candidates.py`: structural and coverage checks.

The source mixture is 200 legacy flip candidates plus 800 new workbook-grounded candidates. Every row contains an intended hidden fact that moves from the initial exact label to a different exact label and a counterfactual hidden fact that supports the opposing initial label. Of the 1,000 rows, 770 are grounded in reviewed multi-label examples, 488 target a paper-reported failure mode, and 85 use domestic violence as the intended hidden fact. The opening queries are 8–33 words (mean 16.96), closely matching the legacy candidates' 11–33 words (mean 18.39).

## Study design

For each opening query and fact condition:

1. FETCH classifies the opening query and generates follow-up questions.
2. A deterministic-temperature matcher decides whether the hidden fact directly answers any generated question.
3. Only when a question matches, FETCH receives the natural-language fact answer and classifies again.
4. Record question coverage, final category accuracy, and final exact category/subcategory accuracy.

The config runs two conditions for every row: the intended flip fact and the explicit counterfactual fact. Compare the two outcomes within scenario ID, then aggregate by swap pair, direction, source stratum, `paper_failure_mode`, `multi_label_grounded`, and `domestic_violence_hidden_fact`. Do not treat unmatched cases as final-classification successes or failures; report elicitation coverage separately.

The paired PromptFoo reference design can be run with:

```bash
cd expanded_flip_experiment
FIRST_N=10 REPEATS=3 ./run_no_cache_replicates.sh  # inexpensive smoke test
REPEATS=3 ./run_no_cache_replicates.sh             # full paired benchmark
```

The full paired command evaluates 1,000 rows × 2 fact conditions × 3 repeats and can be expensive. PromptFoo's persistent Python provider also serialized calls in qualification testing. The official study therefore evaluated the intended-hidden-fact condition only and used the direct concurrent orchestrator:

```bash
source /home/quinten/fetch/.venv/bin/activate
cd expanded_flip_experiment
python run_direct.py --label final_run_1 --concurrency 4 --provider-timeout-seconds 60
python run_direct.py --label final_run_2 --concurrency 4 --provider-timeout-seconds 60
python run_direct.py --label final_run_3 --concurrency 4 --provider-timeout-seconds 60
python analyze_runs.py
```

The official configuration freezes GPT-5 plus the deterministic keyword classifier, vote mode, GPT-4.1 fact/question matching, a study-only 60-second provider deadline, and `cache_enabled: false`. Direct orchestration does not use PromptFoo's result cache at all. Results are written under the gitignored `results/` directory. The counterfactual fields remain in every row for a future paired study; they were not included in the three official paid runs and must not be described as evaluated controls.

If FETCH is not the parent of this repository, set `FETCH_REPO_ROOT=/path/to/fetch`. The bridge delegates to FETCH's existing `promptfoo/two_step_followup_provider.py`, so the classifier and matcher remain the same as the earlier study.

## Rebuild and validate

Use the FETCH Python environment because it already includes `openpyxl`:

```bash
source /home/quinten/fetch/.venv/bin/activate
python expanded_flip_experiment/build_candidates.py
pytest -q expanded_flip_experiment/test_candidates.py
promptfoo validate -c expanded_flip_experiment/promptfooconfig.no-cache.yaml
```

The builder validates all exact labels against FETCH's 209-pair detailed taxonomy. Default source paths can be replaced with `--workbook`, `--legacy`, and `--taxonomy`.

## Review cautions

- Workbook row numbers are provenance pointers, not claims that the generated candidate repeats the source facts.
- Multi-label source rows are used to identify realistic decision boundaries. A flip benchmark still scores one intended exact outcome per fact condition.
- Questions about domestic violence should be safety-aware, explain why the question is asked, allow the person not to answer, and avoid implying that an automated referral tool is an emergency service.
- The paper PDF and workbook are source materials. Confirm redistribution rights before publishing either source artifact or the derived row-level text in `analysis/multilabel_seed_rows.csv`.
