# v2 execution log

Append-only human-readable index of every model-touching run in this folder.

| When (UTC) | What | Outcome |
|---|---|---|
| 2026-07-16 20:10 | `smoke_gpt5_matcher` — 4 cases, concurrency 2 | Complete. GPT-5 matcher works end-to-end (reasons + usage logged); 3/4 cases showed the target failure mode (matched answer, unmoved final labels). |
| 2026-07-17 19:12 | `final_run_1` first attempt — 959 cases, concurrency 6, 90s timeouts | **Aborted** after 13 cases: Azure GPT-5 latencies 40–70s/case put the full run at ~18h. Directory renamed `aborted_slow_final_run_1_20260717T191229Z`; journaled cases preserved, excluded from analysis by the `final_run_*` glob. |
| 2026-07-17 19:15 | `final_run_1` (official) — 959 cases, concurrency 16, 120s timeouts | Running; early latencies 7–13s/case. Results in `results/final_run_1_20260717T191535Z/`. |

Notes:

- All runs: FETCH GPT-5 + keyword, vote mode, cache disabled, GPT-5 matcher
  via the v2 bridge, `.env` credentials from the FETCH checkout.
- Scattered `APITimeoutError` lines from the GPT-5 classifier under load are
  expected; the keyword provider backs the vote and the case still completes
  (same behavior as the v1 official runs).
