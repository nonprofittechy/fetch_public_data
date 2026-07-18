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
| 2026-07-17 19:15–20:34 | `final_run_1` at concurrency 16, 120s timeouts | **Failed — quarantined** as `failed_throttled_c16_final_run_1_20260717T191535Z`. All 959 cases "completed" with zero orchestration errors, but 943 GPT-5 `APITimeoutError`s left 802/959 cases with empty label sets: 16 concurrent cases exceeded the Azure deployment's rate limit, queuing classifier calls past the deadline while the (deadline-free) matcher calls succeeded. Detection: analysis showed 12.7% initial-category presence and 1.15% coverage — implausible against the v1 baseline — with empties uniform across the run. Lesson recorded: sequential probe latency (4–6s) proved the endpoint healthy; concurrency, not the endpoint, was the cause. |
| 2026-07-17 20:45 | `final_run_2` at concurrency 16 | Killed minutes in for the same reason; quarantined as `failed_killed_final_run_2`. |
| 2026-07-17 20:50 | `final_run_1` (official, second attempt) — concurrency 4, 120s timeouts | Running. Concurrency 4 matches the v1 official configuration and tonight's aborted c6 attempt showed zero empty-label cases. A 40-case quality checkpoint (empty-label rate) is armed. |
