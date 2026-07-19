# FETCH pipeline snapshot (reproducibility artifacts)

FETCH's application code is not open source, so this study cannot point
readers at a public repository the way it can for everything else in
`publishable-repo`. This folder exists to close that gap for exactly the
pieces that determine classification behavior — without redistributing
FETCH's application source. Scope, by design:

- **Included:** the study-harness/orchestration file that bridges this
  benchmark to FETCH (a promptfoo-integration script, not production API
  code), plus narrow, attributed excerpts (a few lines each) of the specific
  prompt sections and code paths that materially affect the results in
  `../analysis/RESULTS.md`.
- **Not included:** FETCH's application source (`app/services/`,
  `app/providers/`, `app/prompts/`, `app/core/`, API routes, auth,
  deployment config, or anything beyond what's quoted below). If you need to
  verify a claim beyond what's excerpted here, that requires access to the
  private FETCH repository.

## Contents

- `two_step_followup_provider.snapshot.py` — full copy of
  `$FETCH_REPO_ROOT/promptfoo/two_step_followup_provider.py`, the two-step
  classify → generate-questions → reclassify-with-answer orchestration this
  study's `two_step_provider_bridge.py` wraps and (for the matcher) patches.
  **This file has no git history of its own** — `git status` on the FETCH
  checkout shows it as untracked (`?? promptfoo/two_step_followup_provider.py`),
  so a commit-SHA pointer would not have been reproducible even with private
  repo access; this copy is the only durable record of its exact content.
  SHA-256 of the source file at copy time: see `SHA256SUMS.txt`.
- `PIPELINE_EXCERPTS.md` — short, attributed quotes (file path + line
  numbers in the private repo) of: the classification prompt's approach and
  follow-up-question guidelines, the two code paths this study's root-cause
  investigation fixed (see `../analysis/RESULTS.md` and
  `../analysis/EXECUTION_LOG.md`), and the provider-weight/label-selection
  constants that determine how multi-provider votes become a final label set.
- `SHA256SUMS.txt` — hashes of the files in this folder plus the private
  source files they were copied/excerpted from, so drift can be detected if
  FETCH's code changes after this snapshot was taken.

## Provenance

Snapshot taken 2026-07-18 from a private checkout of
`git@github.com:LemmaLegalConsulting/fetch.git`, branch
`fix/followup-context-and-provider-mix`, commit `41585d0a79de0c2d18a27355dd55b0729f8a968e`
(the fix commit described in `../analysis/RESULTS.md`). The
`run_metadata.json` in each run's `results/` output additionally records the
exact FETCH commit SHA active for that run (`git_fetch_repo_head`), for
anyone with private-repo access who wants the full source at that point.

## Redistribution

Confirm redistribution rights with FETCH's maintainers (Lemma Legal
Consulting) before publishing this folder externally, same caution as for
the *On Wednesdays* paper PDF referenced in `../expanded_flip_experiment/README.md`.
