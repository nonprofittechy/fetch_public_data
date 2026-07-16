# FETCH multi-label gold evaluation methods

## Evaluation population

The primary evaluation population is the 374-row strictly deduplicated consensus file, `gold_labels_consensus_unique.csv`. Each unique problem description is evaluated once. The 431-row row-compatible file is retained for source-row traceability but is not used as though repeated descriptions were independent observations.

The earlier full Promptfoo run used the inherited `followup_questions_only.csv` suite (416 rows). Only 240 descriptions overlap the consensus gold population. It is therefore retained as a legacy follow-up-question-quality baseline, not treated as the primary gold-label accuracy run.

## System and run design

Each primary replicate runs the existing FETCH Promptfoo provider in vote mode with the same five classifiers:

- GPT-5.2 (`gpt-5.2`), the full configured deployment rather than a mini/nano variant
- Gemini (`gemini`)
- Mistral (`mistral`)
- keyword classifier (`keyword`)
- SPOT classifier (`spot`)

Both Promptfoo's cache and the provider's internal cache are disabled. Classifier and semantic-merge timeouts are 60 seconds. The two replicates are independent API executions over the same 374 gold scenarios.

## Taxonomy compatibility

The consensus labels came from an older spelling/version of the OSB taxonomy, while the live FETCH taxonomy has punctuation changes and side-specific refinements. `analyze_fetch_gold_accuracy.py` audits all 127 gold labels against the live taxonomy and provides explicit mappings. All 127 gold identifiers have at least one compatible live identifier.

One-to-one spelling, punctuation, capitalization, and terminology changes count as the same exact sublabel. Examples include `Judgement Collection` / `Judgment Collection`, `Lessor Felony` / `Lesser Felony`, and `Business & Corporate` / `Business and Corporate`. A legacy employment label that the live taxonomy divides into employee and employer children counts as retrieved when FETCH emits the corresponding current child. This compatibility is intentionally narrow and is saved in `accuracy_summary.json`; top-level similarity alone never creates an exact-sublabel match.

## Metrics

Let *G* be a scenario's set of gold sublabels and *P* the set returned by FETCH after compatibility normalization.

- **Any exact sublabel:** at least one member of *G* is present in *P*. This is the minimum successful specialist-routing signal requested for the paper.
- **All exact sublabels:** every member of *G* is present in *P*. Extra predictions do not erase retrieval, so this is a recall-completeness metric.
- **Strict exact set:** every gold label is retrieved and every prediction is compatible with a gold label. This penalizes extra labels.
- **Exact gold coverage:** `|retrieved gold labels| / |G|`, averaged by scenario; micro recall pools all gold label instances.
- **Exact precision:** the share of returned labels compatible with a gold label. Micro F1 combines pooled exact precision and recall.
- **Any/all correct top-level:** the analogous measures after reducing labels to their top-level legal categories.
- **Top-level only:** no exact sublabel was retrieved, but at least one correct top-level category was returned. This represents potentially useful broad routing despite the missed specialist route.
- **Graded retrieval score:** each gold label earns 1 point for an exact compatible sublabel, 0.5 if its top-level category is returned without that exact sublabel, and 0 otherwise; points are divided by the number of gold labels. Thus retrieving one of several issues is better than none, while retrieving all issues receives full credit.

The mutually exclusive paper-facing outcome tiers are: all exact sublabels; some but not all exact sublabels; top-level only; and no correct category. Results are also stratified by number of gold labels and by gold top-level category. A scenario with multiple top-level gold categories contributes to each applicable category stratum.

## Reproduction

Run the scorer after the Promptfoo JSON files are present:

```bash
python analyze_fetch_gold_accuracy.py \
  --gold gold_labels_consensus_20260716/gold_labels_consensus_unique.csv \
  --run run1=/path/to/no_cache_run1.json \
  --run run2=/path/to/no_cache_run2.json \
  --output-dir gold_labels_consensus_20260716/fetch_gold_accuracy
```

The scorer rejects duplicate gold descriptions and duplicate Promptfoo results for a scenario. It emits row-level results, by-label-count and by-category tables, a machine-readable summary, and cross-run stability statistics.
