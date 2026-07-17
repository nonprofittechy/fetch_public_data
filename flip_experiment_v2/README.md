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

1. FETCH (GPT-5 + keyword, vote mode, cache disabled) classifies the opening
   query and generates follow-up questions.
2. **GPT-5** (not GPT-4.1 as in v1) judges whether any generated question
   would be directly answered by the hidden fact. The v2 bridge
   (`two_step_provider_bridge.py`) replaces the provider's matcher with a
   GPT-5-compatible implementation (`max_completion_tokens`, default
   temperature), logs every decision with reason and token usage to
   `matcher_log.jsonl`, and reports matcher errors loudly instead of silently
   returning "no match".
3. On a match, FETCH re-classifies with the conversational answer
   (`fact_as_answer`) and both label sets are recorded.

## Reproduction

```bash
source /home/quinten/fetch/.venv/bin/activate      # FETCH env; .env creds in parent
cd flip_experiment_v2
python build_candidates.py                          # validate + rebuild candidates
python -m pytest -q test_candidates.py              # structural checks
python run_direct.py --label smoke --first-n 4 --concurrency 2   # cheap smoke
python run_direct.py --label final_run_1 --concurrency 6 --provider-timeout-seconds 90
python analyze_runs.py                              # per-run + pooled analysis
```

If FETCH is not the grandparent of this folder, set `FETCH_REPO_ROOT`.
Raw run artifacts (hash-stamped snapshots, fsynced JSONL journal, matcher log,
console) are written under the gitignored `results/`; the analysis outputs in
`analysis/runs_v2/` are committed.

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
| `two_step_provider_bridge.py` | FETCH bridge + GPT-5 matcher shim + matcher logging |
| `run_direct.py` | archived, journaled, uncached official runner |
| `analyze_runs.py` | join-by-scenario_id analysis (audit-editable) |
| `test_candidates.py` | structural checks |
| `analysis/candidate_profile.json` | dataset composition profile |
| `analysis/runs_v2/` | committed analysis outputs |
| `analysis/RESULTS.md` | headline findings (written after official runs) |
