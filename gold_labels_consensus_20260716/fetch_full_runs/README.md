# Full FETCH PromptFoo runs — 2026-07-16

## Baseline and GPT-5.2 repair

The existing `promptfoo/followup_questions_eval.yaml` suite ran all 416 cases with GPT-5.2, Gemini, Mistral, keyword, and SPOT at concurrency 2. FETCH provider caching and PromptFoo caching were enabled. GPT-5.2 is the full `gpt-5.2` Responses API provider with low reasoning effort, not a mini/nano model.

- Eval ID: `eval-xCn-2026-07-16T14:59:27`
- Runtime: 1h16m57s
- Raw result: 81 passed, 335 failed, 0 PromptFoo errors (19.47%)
- GPT-5.2 classifier timeout: 17 unique cases under the existing 17-second deadline
- Semantic-merge timeout: 24 unique events under the existing 12-second deadline (48 duplicate logger lines)

`prepare_fetch_repair.py` validated that all 416 logged GPT start-description lengths exactly matched test CSV order, collapsed duplicate logger output, and extracted the 17 classifier-timeout cases. The repair used the same five-provider setup with 60-second classifier and semantic-merge deadlines:

- Repair eval ID: `eval-sGP-2026-07-16T19:07:51`
- Runtime: 4m41s
- GPT-5.2 starts: 17
- 60-second GPT-5.2 or semantic-merge timeouts: 0
- Repair subset result: 7 passed, 10 failed

`integrate_promptfoo_repair.py` replaced the 17 complete test records by exact `problem_description`, retained baseline order/indexes, and recomputed aggregate metrics. Four tests changed fail→pass and four changed pass→fail, so the repaired baseline remains 81/416 (19.47%). The raw baseline remains untouched.

## Artifacts

- `baseline_raw.json` — untouched raw 416-case baseline.
- `baseline_gpt52_timeout_repair_cases.csv` — exact 17-case repair subset.
- `baseline_timeout_repair_manifest.json` — log matching and row evidence.
- `baseline_gpt52_repair.json` — raw 17-case repair eval.
- `baseline_repaired_integrated.json` — repaired 416-case derivative.
- `baseline_repair_integration_report.json` — hashes and before/after counts.

The repository-root `promptfoo_full_no_cache_20260716.yaml` freezes the next condition with FETCH provider caching disabled. The replicate CLI also passes PromptFoo `--no-cache`, so both cache layers are disabled.
