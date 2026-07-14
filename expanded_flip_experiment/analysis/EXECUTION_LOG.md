# Execution log

This is the human-readable index for paid evaluation work. Machine-readable metadata, console output, immutable config/provider snapshots, and raw PromptFoo JSON are saved inside each corresponding `results/<run>_<UTC timestamp>/` directory.

## Pre-run preparation

1. Built the deterministic 1,000-row candidate file from the 200 legacy flip candidates and 800 workbook-grounded candidates.
2. Validated all initial, final, and counterfactual labels against FETCH's 209-pair detailed taxonomy.
3. Added paired intended-hidden-fact and counterfactual-hidden-fact providers.
4. Disabled FETCH's internal provider cache in both the YAML config and the Python bridge.
5. Required PromptFoo's independent `--no-cache` CLI control.
6. Added `run_experiment.py` to save the exact command, hashes, environment/version information, config and provider snapshots, console log, raw results, timestamps, and completion status for every paid run.

## Run index

Entries are appended after each run is inspected. No result should be included in the cross-run analysis unless its metadata status is `complete`, its result JSON exists, and provider errors are reported explicitly.

### `smoke_20260714T164246Z` — failed preflight, zero paid requests

- Scope: first 2 dataset rows × 2 fact conditions = 4 provider cases.
- Cache controls: both enabled as designed.
- Outcome: 4 provider errors, 0 successful cases, 0 model requests recorded, and reported cost 0.
- Exact error: `ClassificationService.__init__() got an unexpected keyword argument 'semantic_merge_model_override'`.
- Cause: the earlier study's `two_step_followup_provider.py` passed a constructor keyword retired by the current FETCH `ClassificationService`.
- Remedy: the local bridge now removes only that retired keyword. The current service continues to read its semantic-merge model from FETCH's environment configuration. The failed raw result, console log, config snapshot, provider snapshot, command, hashes, and metadata remain preserved under `results/smoke_20260714T164246Z/`.

### `smoke_retry_20260714T164329Z` — successful paid smoke

- Scope: first 2 dataset rows × 2 fact conditions = 4 usable paid FETCH results.
- Runtime: 51 seconds at concurrency 4; PromptFoo reported 1 all-assertion pass and 3 assertion failures, with 0 provider errors.
- Operational observation: Mistral returned transient `429 RateLimitReached` responses under four concurrent FETCH cases. FETCH still returned complete ensemble results, but full runs are therefore capped at concurrency 2.
- Evidence that the pipeline worked: for `x0584` the generated question was `What are you trying to protect?`; the intended patent fact produced `Intellectual Property > Other`, while the counterfactual copyright/trademark fact produced the exact expected `Intellectual Property > Trademark/Copyright` label.
- Evidence of a real classification problem: for legacy scenario `legacy_124`, FETCH asked whether the work was for `personal/home needs, or for your business?` but returned `Consumer Law > General` after both the intended and counterfactual answers.
- All raw and intermediate artifacts remain under `results/smoke_retry_20260714T164329Z/`. This smoke is not included in full-run aggregate estimates.

### `full_run_1_20260714T164523Z` — stopped paired throughput pilot

- Planned scope: 1,000 rows × intended and counterfactual conditions = 2,000 cases at concurrency 2.
- Observed throughput: 20 usable paid results in approximately 3 minutes 53 seconds, implying roughly 5½ hours per paired run.
- Preserved result: PromptFoo wrote all 2,000 result slots; 20 contain usable provider JSON and 1,980 record interruption errors. Metadata correctly marks the artifact `partial`.
- Decision: the three paper-comparable runs will evaluate the intended hidden fact only. Counterfactual fields remain available for a separate paired study.

### `full_run_1_intended_20260714T164938Z` — stopped provider-throughput pilot

- Planned scope: 1,000 intended-fact cases at concurrency 12.
- Observation: only four result rows reached PromptFoo's database after about 72 seconds because persistent Mistral 429 retries occupied the workers.
- The run was stopped and its command, input snapshot, bridge/config snapshots, metadata, and console log were preserved. PromptFoo did not emit a final result JSON before forced termination.
- Decision at this stage: exclude unavailable Mistral. The next pilots used GPT-5, Gemini, keyword, and SPOT; later evidence below led to the narrower frozen official set.

### `official_run_1_20260714T165225Z` — stopped PromptFoo serialization pilot

- Planned scope: 1,000 intended-fact cases with Mistral removed and nominal concurrency 12.
- Observation: PromptFoo's persistent Python-file provider used one worker, completing cases serially despite the concurrency flag.
- Sixteen database rows were exported to `eval_results.partial.json`; the command, dataset, config, bridge, metadata, and console log are also preserved.
- Remedy: `run_direct.py` calls the exact same two-step provider concurrently and writes each completed result immediately to JSONL.

### `direct_smoke_20260714T165513Z` — successful direct-orchestration smoke

- Scope: four intended hidden-fact cases at concurrency 4.
- Outcome: 4/4 completed with zero orchestration errors in about 32 seconds (7.6 cases/minute).
- This established that direct orchestration preserved the two-step provider output while avoiding PromptFoo's single-worker bottleneck.

### `paid_full_run_1_20260714T165556Z` — stopped broad-ensemble concurrency pilot

- Planned scope: 1,000 intended-fact cases using GPT-5, Gemini, keyword, and SPOT at true concurrency 16.
- Throughput improved to roughly 19.5 cases/minute, but SPOT repeatedly timed out and Gemini returned high-demand 503s. Because those internal failures can silently change vote composition, this pilot is excluded from accuracy estimates.
- Completed case records remain in `results.partial.jsonl`, together with all input and configuration snapshots.
- Official provider condition frozen after this pilot: GPT-5 plus deterministic keyword. This is narrower than the paper's broad FETCH ensemble but stable, paid, reproducible, and consistent across all three official runs.

### `stable_smoke_20260714T165744Z` — successful narrowed-provider smoke

- Scope: 4 intended-fact cases using GPT-5 + keyword.
- Outcome: 4/4 completed with zero orchestration errors at 10.5 cases/minute.

### `official_stable_run_1_20260714T165816Z` — stopped timeout pilot

- Planned scope: 1,000 intended-fact cases using GPT-5 + keyword at concurrency 16.
- Observation: FETCH's production-oriented 17-second classifier timeout caused multiple GPT-5 timeouts under synthetic benchmark load. Such rows would reduce to keyword-only classification and are not acceptable as official evidence.
- Decision: preserve the partial JSONL and logs, then set a study-only 60-second classifier and semantic-merge timeout before importing FETCH. The timeout change affects waiting, not prompts, model parameters, labels, or cache policy.

### Concurrency and timeout qualification smokes

- `timeout_smoke_20260714T170026Z`: 16 cases at concurrency 16 and a 60-second FETCH deadline; 16 completed, but the log contains repeated GPT-5 API timeouts.
- `concurrency8_smoke_20260714T170156Z`: 16 cases at concurrency 8; 16 completed, but five GPT-5 API timeouts were logged.
- `concurrency4_smoke_20260714T170258Z`: 16 cases at concurrency 4; 16 completed in about 69 seconds (13.9/minute) with no GPT-5 error in the console log.
- Frozen official execution condition: intended hidden facts, GPT-5 + keyword, concurrency 4, 60-second FETCH classifier/semantic-merge deadline, and all caches disabled.

### `final_run_1_20260714T170440Z` — complete official paid run 1

- Scope: all 1,000 intended-hidden-fact cases under the frozen condition.
- Outcome: 1,000/1,000 completed, zero orchestration errors, 4,090.66 seconds (68.18 minutes).
- Input dataset SHA-256: `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261`.
- Two GPT-5 classifier timeouts were observed in the live terminal. The root-file logging handler was installed after FETCH imported in this first official run, so these two lines are not in its saved `console.log`; that logging-order defect was fixed before run 2. This limitation is retained here rather than treating the missing log lines as zero timeouts.
- Raw results, the incrementally synced JSONL journal, console output, command, metadata, hashes, and frozen input snapshots are under `results/final_run_1_20260714T170440Z/`.

### `final_run_2_20260714T181957Z` — complete official paid run 2

- Scope: all 1,000 intended-hidden-fact cases under the same frozen condition.
- Outcome: 1,000/1,000 completed, zero orchestration errors, 4,141.08 seconds (69.02 minutes).
- Input dataset SHA-256: `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261`.
- Six GPT-5 classifier timeouts are captured in `console.log`. Each affected case still returned a result using FETCH's deterministic keyword provider; these are usable orchestration results but not full two-provider votes, and the analysis treats the six events as an operational caveat.
- The Python process exited with status 120 while shutting down its already-closed logging stream, after writing `status: complete`, all 1,000 results, the final metadata, and all hashes. Independent inspection confirmed the final artifacts are complete.
- Raw and intermediate artifacts are under `results/final_run_2_20260714T181957Z/`.

### `final_run_3_20260714T193500Z` — complete official paid run 3

- Started only after run 2's final JSON and metadata were independently verified.
- Outcome: 1,000/1,000 completed, zero orchestration errors, 3,864.67 seconds (64.41 minutes), and zero GPT-5 classifier failure in the saved log.
- Input dataset SHA-256: `510ca8db9ffdf120266f7c52bc4cc24e22835a4b87b561c7cf8ab27b669f7261`, identical to runs 1 and 2.
- Like run 2, the already-complete process emitted exit status 120 during interpreter shutdown because the live runner had been loaded before the Tee-detachment fix. Final JSON, metadata, hashes, and all 1,000 incremental records were already written and independently verified.
- Raw and intermediate artifacts are under `results/final_run_3_20260714T193500Z/`.

## Analysis checkpoints and audits

1. After run 1, `analyze_runs.py` produced its per-run scenario details, grouped tables, summary, and quote candidates.
2. After run 2, the analyzer was rerun across both complete runs. The cross-run JSON, scenario-stability CSV, quote appendix, and an initial narrative draft were copied to `analysis/intermediate/` before any three-run overwrite.
3. The *On Wednesdays* PDF was converted with `pdftotext -layout` to `analysis/on_wednesdays_extracted.txt` so the prior outcome matrix, per-pair table, and named failure modes could be checked directly. SHA-256: `81a0946139ba10a6379095ab68dfea736c506b2ab8bd67fd3786cbeda8c538da`.
4. A taxonomy compatibility audit found spelling-only legacy/current aliases and four historical labels that are not exact current-taxonomy targets. Raw provider flags remain saved; analysis now canonicalizes true aliases and excludes only non-comparable labels from exact denominators. The decision and counts are in `analysis/TAXONOMY_COMPATIBILITY_AUDIT.md`.
5. A stricter domestic-violence question diagnostic was added before inspecting run 3. It looks for explicit language about safety, abuse, violence, threats, harm, stalking, control, or protective relief and is reported separately from GPT-4.1 matcher coverage.
6. Candidate tests, Python compilation, and PromptFoo configuration validation passed. Exact commands and output are in `analysis/VERIFICATION.md`.
7. After run 3, the analyzer was rerun from all three immutable `results.json` files. It produced 3,000 parsed observations, pooled/grouped tables, the final stability CSV, cross-run summary, and per-run quote candidates. `build_quoted_evidence.py` then regenerated the preselected excerpt appendix from three runs.
8. `analysis/INITIAL_TAKE.md` was written only after the three complete-run integrity checks and final analyzer build. `analysis/ARTIFACT_INDEX.md` and `analysis/SHA256SUMS.txt` index the final and intermediate artifacts.
9. After clarification that serialized label order is not a study criterion, the findings were revised to use only order-independent set membership. Rank-based discussion was removed from the initial take and quote appendix. The analyzer added before/after membership transitions: across 2,149 matches, the expected final category was newly added 47 times; across 1,892 exact-scorable matches, the expected final exact label was newly added 122 times. Historical order fields remain only as explicitly non-criterion machine diagnostics.
10. A source-code audit of the paper analyzer found that the initial comparison had incorrectly counted 301 neutral failures to flip as harm. The exact historical logic requires the serialized top category to change: it yields 176 rescues, 301 neutral failures, and 6 harms (29.33:1), not 176 rescues versus 307 harms. Because order is not a current-study criterion, the report separately gives the symmetric membership diagnostic—47 category additions versus 48 losses, and 122 exact-label additions versus 102 losses.
11. `compare_on_wednesdays.py` then isolated the same 200 legacy scenarios, verified zero textual changes in opening queries/hidden facts/answers/topics, compared every legacy pair, and separated legacy from expanded strata. Its machine outputs and interpretation are in `analysis/on_wednesdays_difference_summary.json`, `analysis/on_wednesdays_pair_comparison.csv`, and `analysis/ON_WEDNESDAYS_DIFFERENCE_AUDIT.md`.
