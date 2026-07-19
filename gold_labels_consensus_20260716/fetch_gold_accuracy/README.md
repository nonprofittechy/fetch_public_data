# FETCH consensus-gold evaluation artifacts

This directory contains the two independent, fully cache-disabled FETCH replicates over the deduplicated multi-label consensus gold set, the targeted GPT-5.2 repairs, and the paper-facing accuracy analysis.

## Primary findings

- [`FETCH_GOLD_ACCURACY_FINDINGS.md`](FETCH_GOLD_ACCURACY_FINDINGS.md): detailed interpretation, paper-ready headline/category tables, replicate stability, and illustrative misses.
- [`FETCH_GOLD_ACCURACY_METHODS.md`](FETCH_GOLD_ACCURACY_METHODS.md): population, taxonomy compatibility, exact/top-level/graded metric definitions, and reproduction command.
- `accuracy_summary.json`: machine-readable run, pooled, and stability statistics.
- `scenario_results.csv`: every scenario/run gold set, predicted set, outcome tier, and component score.
- `metrics_by_gold_label_count.csv` and `metrics_by_top_level_category.csv`: table inputs.

## Run lineage

Both runs used `decision_mode: vote`, the live default taxonomy, and the configured providers `gpt-5.2`, `gemini`, `mistral`, `keyword`, and `spot`. The classifier is the full GPT-5.2 deployment; no mini or nano model was substituted. Promptfoo and FETCH provider caches were disabled, classifier and semantic-merge timeouts were 60 seconds, and concurrency was 2 for full runs and 1 for targeted repairs.

| Artifact | Eval ID | Input | Result |
|---|---|---:|---|
| `no_cache_run1_raw.json` | `eval-Fzo-2026-07-16T19:59:44` | 374 rows from the superseded exact-string-deduplicated file | Complete; its one whitespace-only alias is collapsed during scoring |
| `no_cache_run1_gpt_repair.json` | `eval-dT9-2026-07-17T01:00:49` | 28 GPT-5.2 non-success rows | GPT-5.2 succeeded on all 28 |
| `no_cache_run1_integrated.json` | lineage recorded in integration report | 374 rows | 28 repaired records replace their raw counterparts |
| `no_cache_run2_raw.json` | `eval-lB2-2026-07-17T01:07:40` | final 373-row normalized-deduplicated file | Complete |
| `no_cache_run2_gpt_repair.json` | `eval-Ot9-2026-07-17T02:09:38` | 4 GPT-5.2 exception rows | GPT-5.2 succeeded on all 4 |
| `no_cache_run2_integrated.json` | lineage recorded in integration report | 373 rows | 4 repaired records replace their raw counterparts |

The Promptfoo pass/fail result is the separate follow-up-question quality suite. It is preserved in raw outputs but is not the gold-label accuracy outcome; label accuracy is recomputed from `response.metadata.raw_json`.

## Provider and infrastructure audit

- `no_cache_run*_provider_audit.json` records final raw-run provider summary outcomes and validates GPT request order against the run input.
- `no_cache_run*_gpt_repair_provider_audit.json` confirms GPT-5.2 success in each targeted repair.
- `no_cache_run*_integration_report.json` records replaced-row counts, eval lineage, pass changes in the separate Promptfoo rubric, and SHA-256 hashes.

Before the uncached runs, the Azure Mistral deployment `mistral-small-2503` on account `quint-mln02sj6-eastus2` was increased from GlobalStandard capacity 1 to capacity 100. Azure reported provisioning state `Succeeded`, 100 RPM, and 100,000 TPM. This eliminated the 1,000-TPM quota mismatch with FETCH's approximately 15,000-character taxonomy prompt. Remaining Mistral failures were content-policy or transient service outcomes, not quota-limit responses.

Replicate 1 crossed a workstation hibernation/network interruption but its Promptfoo process survived and resumed. The raw audit found 27 GPT exceptions plus one GPT error result; all 28 were rerun successfully after connectivity recovered. Replicate 2 had four GPT exceptions, all repaired successfully. Raw and repaired files are both retained so this intervention is auditable.

## Relationship to the inherited baseline

The earlier full Promptfoo baseline in [`../fetch_full_runs/`](../fetch_full_runs/) used the inherited 416-row `followup_questions_only.csv` suite. Only 240 descriptions overlapped the consensus gold population, so it is retained as a follow-up-quality baseline and is not pooled with the two complete 373-scenario gold replicates.

## Reproduction

From the publishable repository root:

```bash
pytest -q test_analyze_fetch_gold_accuracy.py
python analyze_fetch_gold_accuracy.py \
  --gold gold_labels_consensus_20260716/gold_labels_consensus_unique.csv \
  --run run1=gold_labels_consensus_20260716/fetch_gold_accuracy/no_cache_run1_integrated.json \
  --run run2=gold_labels_consensus_20260716/fetch_gold_accuracy/no_cache_run2_integrated.json \
  --output-dir gold_labels_consensus_20260716/fetch_gold_accuracy
python render_fetch_gold_findings.py \
  --artifact-dir gold_labels_consensus_20260716/fetch_gold_accuracy
```
