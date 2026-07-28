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
  deployment config, or anything beyond the quoted excerpts). Claims outside
  this scope require access to the private FETCH repository.

## Contents

- `two_step_followup_provider.snapshot.py` — full copy of
  `$FETCH_REPO_ROOT/promptfoo/two_step_followup_provider.py`, the two-step
  classify → generate-questions → reclassify-with-answer orchestration this
  study's `two_step_provider_bridge.py` wraps and (for the matcher) patches.
  The source file was untracked in the FETCH checkout
  (`?? promptfoo/two_step_followup_provider.py`), so it has no independent
  commit history. This frozen copy and its SHA-256 entry in `SHA256SUMS.txt`
  provide the durable content record.
- `PIPELINE_EXCERPTS.md` — short, attributed quotes (file path + line
  numbers in the private repo) of: the classification prompt's approach and
  follow-up-question guidelines, the two code paths this study's root-cause
  investigation fixed (see `../analysis/RESULTS.md` and
  `../analysis/EXECUTION_LOG.md`), and the provider-weight/label-selection
  constants that determine how multi-provider votes become a final label set.
- `SHA256SUMS.txt` — hashes of the files in this folder plus the private
  source files from which they were copied or excerpted. The hashes distinguish
  the evaluated implementation from later FETCH revisions.

## Provenance

Snapshot taken 2026-07-18 from a private checkout of
`git@github.com:LemmaLegalConsulting/fetch.git`, branch
`fix/followup-context-and-provider-mix`, commit `41585d0a79de0c2d18a27355dd55b0729f8a968e`
(the fix commit described in `../analysis/RESULTS.md`). The
`run_metadata.json` in each run's `results/` output additionally records the
exact FETCH commit SHA active for that run (`git_fetch_repo_head`), allowing
authorized researchers to resolve the complete source revision.

## Redistribution

Redistribution of this folder requires authorization from FETCH's maintainers
(Lemma Legal Consulting), consistent with the restrictions governing the
private source excerpts.
