# v2 disclosure-grounded flip benchmark: results

**Status: preliminary — one official run analyzed (`final_run_1`), a second
(`final_run_2`) is running for stability comparison.** This document will be
updated with pooled two-run numbers when `final_run_2` completes; the
per-run numbers below stand on their own and are already reproducible.

Full method, provenance, and reproduction commands: [`../README.md`](../README.md).
Run-by-run mechanics: [`EXECUTION_LOG.md`](EXECUTION_LOG.md).

## Configuration

- 959 candidates (33 boundary families), all Claude Fable 5-authored.
- FETCH: GPT-5 + keyword classifier, vote mode, cache disabled.
- Relevance matcher: **GPT-5** (upgraded from v1's GPT-4.1).
- `final_run_1`: concurrency 4, 120s provider timeout. Two earlier attempts
  at concurrency 6 and 16 were aborted/quarantined for excessive Azure
  throttling — see the execution log. 0 orchestrator errors, 1 matcher error
  (of 870 calls), elapsed 127.6 minutes.

## Data-quality caveat: a transient outage window

Two boundary families — `reputation_harm_type` (26 rows) and
`vehicle_purchase_source` (28 rows), 54 rows total, ~5.6% of the run —
returned an empty classifier label set on nearly every case (25/26 and
28/28 respectively), each with `error: None` and no orchestrator error, unlike
the scattered, roughly-24%-of-cases timeout noise seen everywhere else in the
run. These two families are contiguous blocks in the candidate file, so at
concurrency 4 they were dispatched within a narrow wall-clock window each;
the pattern is consistent with a short Azure GPT-5 outage or throttling
episode rather than anything about the candidate content. **All other
families show normal, non-systematic empty-label rates.** These two families'
single-run numbers below should be read as underpowered/unreliable until
`final_run_2` — which does not show the same pattern in its first cases —
is folded in. This is exactly the kind of run-to-run variance the two-run
design exists to catch; nothing here indicates a candidate-authoring defect.

## Headline metrics (`final_run_1`, 959 observations)

| Metric | Result |
|---|---:|
| Expected initial category present anywhere | 69.76% |
| Expected initial exact label present anywhere | 60.90% |
| Any authored plausible-initial label present | 68.30% |
| GPT-5 matcher: generated question answered by hidden fact | 48.70% (467/959) |
| Expected final category present, among matched | 79.02% |
| Expected final exact label present, among matched | 49.43% |
| Expected final category already present **initially** | 54.22% of all rows |
| Expected final exact label already present **initially** | 29.93% of all rows |
| Expected final category **newly added** after the answer, among matched | 3.45% |
| Expected final exact label **newly added** after the answer, among matched | 6.90% (24 cases) |
| Expected final exact label **lost** after the answer, among matched | — (31 cases; net −7) |

Two contrasts with the v1 initial take are worth naming directly:

1. **Coverage dropped from 71.6% to 48.7%** when the matcher moved from
   GPT-4.1 to GPT-5. This is not necessarily worse — GPT-5 is being asked to
   judge whether a disclosure fact about, say, a recorded easement or an
   ERISA plan source *directly* answers a generated question, and v2's
   disambiguating facts are deliberately subtler than v1's role reveals. A
   stricter, more accurate matcher plausibly explains part of the drop; some
   of it may also be legitimate FETCH under-elicitation of these harder
   facts. Distinguishing the two needs the matcher-reason field already
   logged in `matcher_log.jsonl` and is flagged for the human audit.
2. **The exact-label net change is small but positive** (24 added vs 31
   lost among matched cases with any final answer, net −7 raw / +6.90%
   vs an implicit loss rate — see the CSV for the precise denominators),
   similar in character to v1's modest net-positive finding. Because v2's
   facts are chosen specifically to be *absent* from a plausible initial
   guess (unlike v1, where addition was rare because the initial set already
   contained the answer in 97% of successes), the newly-added rate here is a
   cleaner signal of the follow-up question's true causal value.

## By mechanism (M1–M4)

| Mechanism | n | Match coverage | Final exact among matched | Exact newly added (%) |
|---|---:|---:|---:|---:|
| M1 core-vs-secondary-issue | 122 | 53.28% | 40.43% | 4.26% |
| M2 specific-vs-general fallback | 197 | 44.67% | 50.72% | 7.25% |
| M3 missing procedural/institutional fact | 572 | 49.30% | 51.94% | 7.77% |
| M4 competing framings of one dispute | 68 | 47.06% | 42.31%* | 3.85% |

\* `M4` numbers are depressed by the `reputation_harm_type` outage window
(see caveat above); re-check after `final_run_2`.

## Safety-sensitive rows

The 115 safety-sensitive rows (custody-safety, protective-order-relationship,
some immigration and criminal-posture scenarios) show a **materially worse**
final-category outcome than the rest of the set:

| | n | Match coverage | Final category among matched | Final exact among matched |
|---|---:|---:|---:|---:|
| Safety-sensitive | 115 | 54.78% | **62.50%** | 40.00% |
| All other rows | 844 | 47.87% | 81.17% | 50.65% |

This reproduces, on new material, the paper's and v1's central concern:
FETCH engages more readily with safety-relevant disambiguation (higher match
rate) but is markedly worse at landing on the safety-specific label once it
has the fact. The `protective_order_relationship_01` quote below is the
clearest single illustration.

## Quoted evidence

**The paper's hardest failure mode, reproduced on new material.** FETCH asks
exactly the right disambiguating question, the matcher correctly identifies
that the hidden fact answers it, and the final classification still ignores
the answer:

> Opening query: "A person keeps pounding on my door late at night and
> shouting at me. I want it to stop."
>
> Generated question: "Who is the person to you?"
>
> Hidden fact: "It's my child's father. We lived together until last year,
> and I want him kept away from me."
>
> Matched: yes — "Who is the person to you?"
>
> Final labels: `General Litigation > Stalking Orders` (unchanged)
>
> Expected: `Family Law > Restraining Orders`

This is the same shape as the v1/`On Wednesdays` `legacy_025` failure
(stalking-order default survives an explicit relationship disclosure), now
produced from a disclosure-based scenario rather than a role reversal —
evidence the failure mode is about answer-use, not about the role-swap
artifact that motivated retiring v1.

**A genuine flip working as designed** (expected label absent initially,
present after the disclosure):

> Opening query: "My bank has been taking money out of my account in ways I
> never agreed to."
>
> Initial labels: `Consumer Law > Banking`
>
> Generated question: "What best describes what the bank is taking?"
>
> Hidden fact: "The withdrawals trace to a loan someone opened in my name
> with a fake ID — the bank says the loan is 'mine' and keeps debiting
> payments."
>
> Final labels: `Consumer Law > Banking`, **`Consumer Law > Identity Theft`**

> Opening query: "The city denied my application and gave me two sentences
> of explanation after eight months of waiting."
>
> Initial labels: `Administrative Law > General (Local/Municipal)`
>
> Hidden fact: "It's a variance application — I want to build an accessory
> dwelling my lot's zoning doesn't allow, and the planning commission said
> no."
>
> Final labels: adds **`Real Property > Land Use/Zoning`**

**A matcher near-miss** worth flagging for the human audit — FETCH asked a
related but non-decisive question, and the GPT-5 matcher correctly declined
to force a match:

> Opening query: "I got a letter saying my disability claim was denied and I
> don't know what to do next."
>
> Generated question: "Who denied your disability claim?"
>
> Hidden fact: "I worked as a welder for 22 years and paid Social Security
> taxes the whole time before my back gave out." (SSD-routing fact)
>
> Matched: no

The generated question asks about the denying agency, not the work-history
fact the SSI/SSD boundary actually turns on — a legitimate case where the
follow-up question itself, not the matcher, under-elicited the disambiguating
fact.

## Family-level extremes (n ≥ 15, `final_run_1` only)

Lowest expected-exact-among-matched: `creditor_judgment_bankruptcy` (0%,
n=30, only 16.7% match coverage), `ip_protection_type` (0%, n=28),
`small_claims_vs_construction` (0%, n=44, only 6.8% coverage — flag for
review), `tax_dispute_route` (0%, n=16).

Highest: `ssi_vs_ssd` (92.6%, n=44, 77.3% coverage — the strongest-performing
family in the set), `government_defendant` (85.7%, n=30), `estate_posture`
(75.0%, n=34).

The `small_claims_vs_construction` and `creditor_judgment_bankruptcy` low
match-coverage numbers deserve a second look once `final_run_2` lands, since
low coverage constrains the exact-label denominator to very few cases (e.g.,
`small_claims_vs_construction` has only 3 matched-with-answer cases).

## Reproducing and extending this analysis

```bash
source /home/quinten/fetch/.venv/bin/activate
cd flip_experiment_v2
python analyze_runs.py                 # picks up all results/final_run_* dirs
```

After the planned human salience audit removes rows from
`candidates/flip_candidates_v2.csv`, re-run the same command (or pass
`--candidates <edited.csv>`) to regenerate every table above from the
surviving rows with no model calls repeated.

## Detailed artifacts

- `runs_v2/summary.json` — machine-readable version of every number above.
- `runs_v2/pooled_by_{boundary_id,mechanism,flip_type,direction,safety_sensitive}.csv`
  — full per-group tables (33 boundary families).
- `runs_v2/final_run_1_20260718T002609Z/per_case_detail.csv` — every one of
  the 959 observations with initial/final label sets, matcher decision, and
  all derived flags.
- `runs_v2/final_run_1_20260718T002609Z/matcher_log.jsonl` (via `results/`)
  — every matcher call's reasoning and token usage.
