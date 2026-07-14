# FETCH human label review app

This is a deliberately small review interface for the 132-row prioritized silver-label queue. It displays the source text, original human label, internal primary, three independent model passes, the GPT-5.2 audit, the current one-to-four-label suggestion set, and the canonical detailed description beside every selected label.

The human can choose zero through four exact taxonomy pairs. Candidate order has no meaning. Each person selects a reviewer name/ID, so two humans can independently review the same row without overwriting each other. Saved work goes to SQLite, every save is appended to a history table, and results can be exported as review provenance or validated gold data.

## Live instance

- URL: <https://fetch-silver-label-review.fly.dev/>
- Fly organization: `lemma` (Lemma)
- App: `fetch-silver-label-review`
- Region: `iad`
- Compute: one `shared-cpu-1x:256MB` Machine with automatic stop/start and zero minimum running Machines
- Storage: one encrypted 1 GB `review_data` volume mounted at `/data`
- Deployed and production-verified: 2026-07-14

`REVIEW_PASSWORD` and `SECRET_KEY` are deployed as Fly secrets and are not stored in this repository. The generated reviewer password was handed to the project owner at deployment.

## Local use

Use a virtual environment from the repository root:

```bash
python -m venv .venv-review
.venv-review/bin/pip install -r human_review_app/requirements.txt
REVIEW_DB_PATH="$PWD/human_review_app/data/reviews.sqlite3" \
  .venv-review/bin/python human_review_app/app.py
```

Open `http://localhost:8080`. For shared local use, also set `REVIEW_PASSWORD` and a stable random `SECRET_KEY`.

Run the tests with:

```bash
cd human_review_app
../.venv-review/bin/python -m unittest -v test_app.py
cd ..
.venv-review/bin/python -m unittest -v test_build_human_validated_gold.py
```

## Review interaction

- All labels are displayed as `Category > Subcategory`; the stored value remains the exact canonical pair.
- A new row has no preselected status radio.
- `Save` requires the reviewer to select a status. `Needs review` is the draft/pause state.
- `Save review + next` compares the unordered human set with the AI recommendation and automatically records `accepted` when identical or `corrected` when different.
- The default screen contains only the problem, compact AI recommendation, selectors, reviewer/status, and notes. Priority analysis, original/internal labels, rationales, model passes, and other-human decisions are collapsed under “Supporting evidence and prior passes.”

## Persistence and exports

The database path comes from `REVIEW_DB_PATH`. Its two tables are:

- `reviews`: the latest decision for each `(row_number, reviewer_key)`;
- `review_history`: an append-only snapshot for every successful save.

Reviewer queue progress is session-specific. Reusing the same normalized reviewer ID updates that person's current decision; using a different ID creates an independent decision. See [`GOLD_DATA_WORKFLOW.md`](GOLD_DATA_WORKFLOW.md) for the consensus rule, disagreement handling, gold endpoints, and repository merge command.

The database is local state and is intentionally ignored by git. Use the in-app CSV/JSON exports for portable results. On Fly.io, `/data/reviews.sqlite3` resides on the attached `review_data` volume and survives machine restarts and deployments.

## Production E2E verification

On 2026-07-14 the deployed site was exercised through real HTTPS forms with two isolated browser-cookie sessions:

1. `E2E Persistence Alpha` and `E2E Persistence Beta` independently submitted row 424.
2. Both were automatically marked `accepted`; strict gold reported `multi_reviewer_consensus`, 2 reviewers, and 4 labels.
3. The Fly Machine was explicitly stopped and confirmed `stopped`.
4. An HTTPS request cold-started it; both reviewer records and the same strict-gold row remained on the attached volume.
5. A separate production form test confirmed no status was preselected, blank-status `Save` was rejected, `Category > Subcategory` was rendered, and a changed set was automatically marked `corrected`.
6. E2E records and history were deleted afterward. Three pre-existing draft rows were preserved and migrated as `Legacy reviewer`.

SQLite plus a Fly volume is a single-machine design. Keep exactly one app Machine in one region. Fly volumes are not automatically replicated; make periodic snapshots or download exports. If simultaneous high-volume review or multi-region redundancy is later required, move the two tables to managed Postgres.

## Fly.io deployment

The included [`fly.toml`](fly.toml) and [`Dockerfile`](Dockerfile) reproduce the one-Machine deployment in `iad`. This follows Fly's official [Flask deployment guidance](https://fly.io/docs/python/frameworks/flask/), [`fly.toml` mount configuration](https://fly.io/docs/reference/configuration/), and [volume workflow](https://fly.io/docs/volumes/volume-manage/). For a new app, choose a globally unique name by editing `app` in `fly.toml`, then from the repository root run:

```bash
fly apps create fetch-silver-label-review
fly volumes create review_data --app fetch-silver-label-review --region iad --size 1
fly secrets set --app fetch-silver-label-review \
  REVIEW_PASSWORD='use-a-long-unique-password' \
  SECRET_KEY='use-a-long-random-secret'
fly deploy --config human_review_app/fly.toml
fly scale count 1 --app fetch-silver-label-review
```

If the chosen name differs, update both the commands and `fly.toml`. Do not deploy without `REVIEW_PASSWORD`: the app contains redacted but potentially sensitive legal-help descriptions. The health check is intentionally unauthenticated and returns only status and case count.

After deployment:

```bash
fly status --app fetch-silver-label-review
fly checks list --app fetch-silver-label-review
fly logs --app fetch-silver-label-review
```

To make an out-of-band SQLite backup, first stop writes and use a Fly SSH console or volume snapshot workflow. The in-app exports are safer for routine reviewer handoff because they avoid copying database internals.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `REVIEW_DB_PATH` | `human_review_app/data/reviews.sqlite3` | Persistent SQLite file |
| `REVIEW_CASES_PATH` | Stage 10 `review_cases.json` | Review queue and model evidence |
| `REVIEW_TAXONOMY_PATH` | Stage 10 `taxonomy.json` | All 209 exact pairs and descriptions |
| `REVIEW_PASSWORD` | unset | Enables shared-password login when set |
| `SECRET_KEY` | random per process | Signs sessions; must be stable in deployment |
| `COOKIE_SECURE` | `0` locally, `1` in image | Sends session cookie over HTTPS only |

## Security and scope

- State-changing forms use a per-session CSRF token.
- Password comparisons use constant-time comparison.
- Labels are accepted only when they match the committed canonical taxonomy snapshot.
- Duplicate labels in one human decision are rejected.
- The app does not call any model API and does not load `../.env`.
- The shared password is suitable for a small invited reviewer group, not public internet self-service. Put an identity-aware proxy in front if per-user authentication or access revocation is required.

## Updating the queue

Regenerate Stage 10 first:

```bash
python build_four_label_review.py
```

Then rebuild/redeploy the image. Existing reviews remain keyed by source `row_number` and normalized reviewer ID; the deploy does not modify the mounted database.
