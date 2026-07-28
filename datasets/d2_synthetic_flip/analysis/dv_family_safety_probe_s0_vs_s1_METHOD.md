# Method note: `dv_family_safety_probe_s0_vs_s1.csv`

Nomenclature: **S0** = post-fix baseline, no deterministic screening protocol
(previously called "condition B" in `RESULTS.md`). **S1** = identical
benchmark run against a worktree adding PR #34's deterministic screening
protocols (previously called "condition C"). Both are single official runs
(`runs_v2_postfix_condition_b/pooled_per_case_detail.csv` and
`runs_v2_postfix_condition_c/pooled_per_case_detail.csv`), not pooled reruns.

## Scenario selection (n=8)

From the 959 `flip_candidates_v2.csv` scenarios, manually selected the
`custody_safety` and `protective_order_relationship` boundary-family rows
whose **hidden_fact** (not the opening query) discloses intimate-partner or
co-parent violence, threats, or coercive control:
`v2_custody_safety_01, _02, _04, _06, _21, _27, _46,
v2_protective_order_relationship_24`.

Excluded from this family-adjacent pool: rows where the hidden fact
explicitly negates violence/relationship status (`_03`, `_10`, `_23`,
`protective_order_relationship_10`, `_46`), rows where DV is disclosed in
the opening query itself rather than hidden (`charge_severity_05`), and rows
where the safety-relevant conduct isn't intimate-partner/family in nature
(`protective_order_relationship_09`, `_63`). This is a manual, keyword-assisted
selection, not a field in the candidate schema — re-derivable from
`candidates/flip_candidates_v2.csv` but not an authoritative flag.

## Columns

- `question_matched` — FETCH's matcher accepted one of the generated
  follow-up questions (raw pipeline field).
- `explicit_safety_probe_in_question_set` — regex match
  (`safe|safety|unsafe|abuse|violen|threat|hurt|harm|hit|control|stalk|coerc|
  protective order|restraining order|afraid|scared|danger`, case-insensitive)
  against the full `follow_up_questions` string. Mechanical text match, not a
  human read — see raw question text in the same row to verify.
- `screening_protocol_rescue` — only populated for S1; `True` if the
  scenario appears in `screening_marginal_contribution.json`'s
  `rescue_detail` (a case where `effective_categories` added the correct
  label but the raw model-only vote did not).

## Known limitation

S1's screening question is a checkbox-style prompt ("Has anyone involved in
this family or relationship situation done any of the following?") whose
underlying option list is not captured in `follow_up_questions` — only the
header text is. The regex therefore does not credit this header as an
explicit probe unless other question text in the same set also matches,
which likely undercounts S1's true explicit-probe rate.
