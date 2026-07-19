# Disclosure-grounded flip benchmark (v2)

This folder replaces the expanded 1,000-candidate flip audit
([`../expanded_flip_experiment/`](../expanded_flip_experiment/)) with a
benchmark built around a different — and, we believe, far more realistic —
notion of a "hidden fact."

## Why v1 was retired

The v1 candidate set (and the original *On Wednesdays* 200) leaned heavily on
**party-role reversals**: an opening query that reads as a wrongful-discharge
plaintiff flips to employment-defense when the "hidden fact" reveals the user
is actually the employer; a tenant intake flips to landlord; and so on. Real
users know which side of a dispute they are on and state it or imply it
immediately. A benchmark whose flips hinge on the user's own role measures a
fact pattern that essentially never occurs at intake, and the v1 initial take
(`../expanded_flip_experiment/analysis/INITIAL_TAKE.md`) showed a second
problem: most "expected final" labels were already present in the initial
output set, so few rows tested a true flip.

## What v2 tests instead

Every v2 scenario hides a **case fact the user genuinely holds but plausibly
omitted from a first message**, drawn from the fact types that made trained
human reviewers disagree in the Stage 11 gold-label study:

- **Procedural/institutional posture** — has a judgment been entered, a
  bankruptcy filed, a Notice to Appear served, a will probated, a survey
  recorded, a criminal charge filed vs. resolved (mechanism M3 in
  [`../gold_labels_consensus_20260716/FINDINGS.md`](../gold_labels_consensus_20260716/FINDINGS.md)).
- **Which institution** — SSI vs SSD, Medicaid vs private insurance, federal
  vs state comp, public vs private defendant, dealer vs private seller,
  employer-sponsored (ERISA) vs individual policy.
- **Specific-vs-general routing** — amount in controversy vs the small-claims
  cap, licensed-professional error vs ordinary negligence, doxing vs
  defamation (mechanism M2/M4).
- **Safety-relevant context** — qualifying relationships for FAPA restraining
  orders vs stalking orders, DV disclosure inside custody framings, DHS
  involvement (the paper's hardest failure modes, handled with safety-aware
  wording).

Routing/clarification flips (e.g., SSI↔SSD, where the enriched taxonomy
description itself instructs intake to ask the disambiguating question) are
included deliberately at the study owner's request.

## Provenance and generator model

**Every scenario was individually authored and vetted by Claude Fable 5
(Anthropic, model id `claude-fable-5`), running in Claude Code on
2026-07-16/17.** No OpenAI or Google model wrote or filtered any candidate
text, so the generation step is provider-independent from the evaluated
pipeline (GPT-5 + keyword classifier) and from the GPT-5 relevance matcher.
The generator identity is stamped on every row (`generator_model`) and in
every run's `run_metadata.json`.

Grounding sources (all in this repository or the FETCH checkout):

- `../gold_labels_consensus_20260716/human_disagreements.csv` — the 53
  scenarios on which two trained human reviewers disagreed; most families cite
  specific rows (`grounding_source_rows`).
- `../gold_labels_consensus_20260716/FINDINGS.md` — the four disagreement
  mechanisms every family is tagged with.
- `$FETCH_REPO_ROOT/app/data/taxonomy_detailed_descriptions.csv` — enriched
  descriptions used to pick decisive boundary facts.
- The v1 paper-failure-mode strata (criminal_vs_restraining, injury_location,
  bankruptcy_vs_collections, employment_admin, domestic_violence) are all
  rebuilt here with disclosure-based facts instead of role swaps.

## Dataset

- `candidates/flip_candidates_v2.csv` / `.jsonl` — 959 scenarios, 33 boundary
  families. Directions: 799 A→B, 160 B→A. Flip types: 777
  routing-disambiguation, 182 label-change. 115 safety-sensitive rows.
  Opening queries are 10–24 words (mean 17.0), matching the legacy length
  distribution.
- `authoring/family_*.json` — the authored source of every row, including a
  per-row `vetting_note` explaining why the flip is realistic, for use during
  the planned **human salience audit**.
- Expected labels are validated against **FETCH's runtime taxonomy**
  (`app/data/taxonomy.csv`, 225 pairs), so exact-label scoring needs no alias
  table and has no "unscorable" exclusions (a v1 defect).
- Every row carries a real, specific **counterfactual disclosure** supporting
  the opposing label, for a future paired study; the official runs evaluate
  the intended condition only.

Candidate status is `claude_authored_awaiting_human_salience_audit`: these are
Claude-vetted candidates, not human gold labels.

## Pipeline

Same two-step design as v1 and the paper:

1. FETCH classifies the opening query and generates follow-up questions.
   Vote mode across all 5 enabled providers (`gpt-5`, `gemini`, `mistral`,
   `keyword`, `spot`), cache disabled.
2. **GPT-5** (not GPT-4.1 as in v1) judges whether any generated question
   would be directly answered by the hidden fact. The v2 bridge
   (`two_step_provider_bridge.py`) replaces the provider's matcher with a
   GPT-5-compatible implementation (`max_completion_tokens`, default
   temperature), logs every decision with reason and token usage to
   `matcher_log.jsonl`, and reports matcher errors loudly instead of silently
   returning "no match".
3. On a match, FETCH re-classifies with the conversational answer
   (`fact_as_answer`), voting across the 3 LLM-backed providers (`gpt-5`,
   `gemini`, `mistral` — keyword and SPOT cannot use the extra context and
   are excluded), and both label sets are recorded.

**Pipeline fix (2026-07-18):** the initial official run (`final_run_1`,
2026-07-18 00:26 UTC) uncovered two structural bugs in FETCH itself that
made step 3 not actually use the disclosed answer for GPT-5-family
classifiers. Both were fixed in the FETCH repo
(`fix/followup-context-and-provider-mix` branch, commit `41585d0`) with
regression tests; every run from `final_run_1` (2026-07-18 20:xx UTC)
onward uses the fixed pipeline. Root-cause details, before/after evidence,
and the narrow reproducibility excerpts of the fixed FETCH code are in
[`analysis/RESULTS.md`](analysis/RESULTS.md),
[`analysis/EXECUTION_LOG.md`](analysis/EXECUTION_LOG.md), and
[`fetch_pipeline_snapshot/`](fetch_pipeline_snapshot/) (FETCH is not open
source; that folder captures only the narrow slice needed to reproduce this
study's results, not FETCH's application code).

**Screening-protocol comparison (2026-07-18):** a second post-fix condition
(**condition C**) runs the identical benchmark against a worktree merging
FETCH PR #34 (deterministic screening protocols) onto the fix branch, to
answer "does the screening layer add anything beyond the fixed follow-up
mechanism?" alongside the base fixed-pipeline condition (**condition B**).
The condition-C harness (`two_step_provider_bridge_screening.py`,
`run_direct_screening.py`) scores `effective_categories` — FETCH's
screening-aware union of model labels and mandatory categories — while
separately recording raw model-only labels so the protocol's own marginal
contribution can be isolated from ordinary run-to-run LLM variance. Results,
methodology, and the paired within-run isolation analysis are in
[`analysis/RESULTS.md`](analysis/RESULTS.md#condition-b-vs-c-does-the-screening-protocol-add-anything).

## Reproduction

```bash
source /home/quinten/fetch/.venv/bin/activate      # FETCH env; .env creds in parent
cd flip_experiment_v2
python build_candidates.py                          # validate + rebuild candidates
python -m pytest -q test_candidates.py              # structural checks
python run_direct.py --label smoke --first-n 4 --concurrency 2   # cheap smoke
python run_direct.py --label final_run_1 --concurrency 4 --provider-timeout-seconds 120
python analyze_runs.py --runs results/final_run_1_<timestamp> \
    --out analysis/runs_v2_postfix_condition_b        # condition B: fixes only

# Condition C: fixes + PR #34 screening protocols. Requires a FETCH worktree
# merging the fix branch with PR #34's origin/main and FETCH_REPO_ROOT set to
# it (see fetch_pipeline_snapshot/README.md); also needs the untracked
# promptfoo/two_step_followup_provider.py copied into that worktree, since
# git worktree add does not carry over untracked files.
FETCH_REPO_ROOT=/path/to/merged/worktree python run_direct_screening.py \
    --label final_run_1 --concurrency 4 --provider-timeout-seconds 120
python analyze_runs.py --runs results/final_run_1_<timestamp> \
    --out analysis/runs_v2_postfix_condition_c
python analyze_screening_contribution.py --run results/final_run_1_<timestamp> \
    --out analysis/runs_v2_postfix_condition_c/screening_marginal_contribution.json
```

If FETCH is not the grandparent of this folder, set `FETCH_REPO_ROOT`.
Raw run artifacts (hash-stamped snapshots, fsynced JSONL journal, matcher log,
console) are written under the gitignored `results/`; the analysis outputs in
`analysis/runs_v2/` (pre-fix baseline, historical),
`analysis/runs_v2_postfix_condition_b/`, and
`analysis/runs_v2_postfix_condition_c/` are committed. Each condition's runs
are analyzed in isolation (`--runs` pointed at just that condition's run
directory) rather than pooled together, since B and C are different pipeline
configurations, not repeated samples of the same one.

## Re-running after the human audit

The analysis joins raw results to the candidate CSV **by scenario_id**. To
regenerate every finding after pruning rows:

1. Delete the rejected rows from `candidates/flip_candidates_v2.csv` (or save
   an edited copy).
2. `python analyze_runs.py --candidates <edited.csv>`

Removed rows are excluded from every metric; no model calls are repeated. The
per-row `vetting_note` column and the authoring files give the audit context.

## Metrics

`analyze_runs.py` reports, per run and pooled, overall and by boundary family
/ mechanism / flip type / direction / safety flag:

- expected initial category and exact-label presence (plus presence of any
  authored plausible initial label);
- question-match coverage (GPT-5 matcher);
- expected final category / exact-label presence among matched cases;
- whether the expected final category/exact label was **already present
  initially** and whether it was **newly added** after the answer — the true
  flip signal v1 showed must be separated from retention;
- exact-label losses, matcher error counts, and cross-run stability.

## Files

| File | Role |
|---|---|
| `authoring/family_*.json` | Claude-authored scenarios with grounding + vetting notes |
| `build_candidates.py` | deterministic validator/assembler (no model calls) |
| `candidates/flip_candidates_v2.csv/.jsonl` | frozen candidate set |
| `two_step_provider_bridge.py` | FETCH bridge + GPT-5 matcher shim + matcher logging (condition B) |
| `two_step_provider_bridge_screening.py` | condition-C bridge: scores `effective_categories` against the screening-protocol worktree |
| `run_direct.py` | archived, journaled, uncached official runner (condition B) |
| `run_direct_screening.py` | condition-C runner, points `FETCH_REPO_ROOT` at the screening-protocol worktree by default |
| `analyze_runs.py` | join-by-scenario_id analysis (audit-editable) |
| `analyze_screening_contribution.py` | paired within-run isolation of the screening protocol's own marginal contribution |
| `test_candidates.py` | structural checks |
| `analysis/candidate_profile.json` | dataset composition profile |
| `analysis/runs_v2/` | committed analysis outputs, pre-fix baseline (historical) |
| `analysis/runs_v2_postfix_condition_b/` | committed analysis outputs, post-fix condition B |
| `analysis/runs_v2_postfix_condition_c/` | committed analysis outputs, post-fix condition C |
| `analysis/RESULTS.md` | headline findings (written after official runs) |
