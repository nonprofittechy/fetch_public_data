# Readability study: does nano→full improve FETCH's question screens?

A paired, disclosure-blind study of the follow-up-question **screen** FETCH shows
after an opening query, comparing the classification ensemble with its OpenAI
member (and semantic-merge model) set to **gpt-5-nano** vs **gpt-5.2** — the exact
production switch the team already shipped but never measured.

**Full design & rationale:** [`docs/STUDY_PLAN.md`](docs/STUDY_PLAN.md).

## The two arms

Only the OpenAI ensemble member and the merge model change; gemini + mistral are
held constant (keyword/spot are omitted — they never emit questions).

| Arm | Ensemble generators | Merge model |
|-----|--------------------|-------------|
| nano | **gpt-5-nano** + gemini + mistral | gpt-5-nano |
| full | **gpt-5.2** + gemini + mistral | gpt-5.2 |

## Pipeline

```
scenarios/gold_consensus_373.csv          373 human-vetted problem descriptions
        │
        ▼  harness/run_generation.py  (or harness/promptfoo/)
results/generation/<run>/screens.jsonl    one merged screen per (scenario, arm)
        │                                  + harness/repair_failures.py (de-bias)
        ├─▶ metrics/deterministic.py   → metrics_deterministic.jsonl   (m4–m9)
        ├─▶ metrics/run_llm_metrics.py → metrics_llm_deepseek-v4.jsonl  (m1–m3,10)
        │        judge: DeepSeek-V4-Pro on Azure (independent of the generators)
        ▼
analysis/analyze.py                       paired stats + equivalence → results_*.json
        │        cross-family robustness: metrics/claude_subset/ (Claude judge)
        ▼
analysis/RESULTS.md                        writeup
```

## Metrics (see study plan for definitions)

- **Primary (pre-registered):** 1 unverified-presupposition rate · 2 double-barrel
  count · 3 simulated-respondent unclear/answerable rate · 4 unintroduced hard vocab.
- **Exploratory:** 5 dependency length · 6 agentless passive · 7 GPT-2 surprisal ·
  8 screen load · 9 negation×conditional · 10 ambiguity (restatement variance).
- Aggregated to the screen with **max**. Judges are **blind** to arm.

## Judges

- **DeepSeek-V4-Pro** (Azure deployment `deepseek-v4`) — scalable automated judge,
  independent of the GPT+Gemini+Mistral generators (no same-family bias).
- **Claude Sonnet-5 / Claude (in-context)** — independent second-family judge on a
  blind subset for cross-family robustness.

## Reproduce

```bash
# 1. generate the paired screens (resumable)
python harness/run_generation.py --run-id main_20260719 --concurrency 8
python harness/repair_failures.py --run-id main_20260719      # de-bias failures
# 2. metrics
python metrics/deterministic.py --run-id main_20260719
python metrics/run_llm_metrics.py --run-id main_20260719 --judge-model deepseek-v4
# 3. validity + analysis
python validation/validity_check.py --judge deepseek-v4
python analysis/analyze.py --run-id main_20260719 --judge deepseek-v4
```

Credentials come from `/home/quinten/fetch/.env` (Azure). Caching is disabled
end-to-end; every run records its config in `meta.json`.

## Environment & settings (reproducibility)

- **Python deps:** `requirements.txt` (+ `python -m spacy download en_core_web_sm`).
  GPT-2 and `roberta-large-mnli` weights auto-download on first use. Run inside the
  FETCH venv (`/home/quinten/fetch/.venv`) so `app.*` imports resolve.
- **Models / deployments** (Azure AI Services account `quint-mln02sj6-eastus2`,
  reached via the OpenAI-compatible route in `/home/quinten/fetch/.env`):
  - generators: `gpt-5.2`, `gpt-5-nano` (OpenAI), `mistral-small-2503` (Mistral),
    `gemini` (Google, via `GEMINI_API_KEY`)
  - judge: `deepseek-v4` (DeepSeek-V4-Pro) — independent of the generators;
    Claude judging was done in-context (Anthropic is in the Azure catalog as
    `claude-sonnet-5` but its deployment requires `ModelProviderData`).
- **Deployment capacities bumped** to clear 429 throttling during the run (large
  quota headroom existed; these were low default allocations):
  `mistral-small-2503` 100→500, `gpt-5.2` 150→1000.
- **Harness-set env** (see `harness/fetch_screen.py`): `TELEMETRY_ENABLED=false`,
  `CLASSIFIER_TIMEOUT_SECONDS=90`, `SEMANTIC_MERGE_TIMEOUT_SECONDS=60`,
  `OPENAI_SEMANTIC_MERGE_MODEL` set per arm; `gpt-5-nano` is registered into the
  Responses-API family at runtime. `GPT_5_REASONING_EFFORT=low`.
- **Known exclusions:** ~7 scenarios (gold-0008/0067/0068/0069/0158/0205/0370)
  trigger Azure content-filter 400s in both arms → unrepairable, arm-symmetric.
- **Run provenance** is captured per run in
  `results/generation/<run_id>/meta.json`.

## Status

Validity check passed (presupposition sensitivity 1.0, double-barrel 6/7,
vocabulary 6/7, known-bad 2/2 flagged). See `analysis/RESULTS.md` for findings.
