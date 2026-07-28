# FETCH runtime prompts

The prompts the deployed FETCH service uses at runtime, mirrored here so the prompts cited
in the paper resolve to a versioned, public artifact rather than to a gist.

Copied from the private FETCH application repository at commit `c0c59ca`, from
`app/prompts/`. If you change a prompt there, re-copy it here.

## Files

| File | Role | Used by |
|---|---|---|
| `default.txt` | Classification **and** follow-up question generation. Sent to every LLM ensemble member. | All three LLM members |
| `default_no_followups.txt` | Classification only, for providers that deploy FETCH without the question layer. | Ensemble, no-followup mode |
| `semantic_merge.txt` | Merges the 9 candidate questions into one screen, drops irrelevant ones, and rewrites in plain language. | Merge model |
| `screening_resolution_system.txt` | Decides whether the opening narrative already discloses a screening-protocol fact, so the deterministic screen can be skipped. | Screening layer |
| `__mistral.txt` | **Inactive.** See below. | — |
| `prompt_variants/` | Prompt variants from the question-wording experiments. Not used in production. | Offline experiments only |

## How prompts are selected

`app/providers/base.py` resolves a prompt by provider name, falling back to the default:

```python
prompt_path = f"app/prompts/{provider_type}.txt"   # e.g. app/prompts/openai.txt
# falls back to app/prompts/default.txt when that file does not exist
```

No `openai.txt`, `gemini.txt`, or `mistral.txt` exists, so **all three LLM ensemble
members receive `default.txt`**. This is what the paper means by employing a single prompt
across the three models.

`__mistral.txt` is a Mistral-specific prompt that was written and then retired. The leading
double underscore takes it out of the lookup path — `provider_type` is `mistral`, so the
loader looks for `mistral.txt`, does not find it, and falls back. It is included here for
completeness, not because it runs.

`screening_resolution_system.txt` is stored inline as a Python string literal in
`app/services/classification_service.py` rather than as a prompt file; it was extracted
verbatim for publication. It runs on `OPENAI_SCREENING_MODEL`, which defaults to
`gpt-4.1-nano`.

## Note on the gist

An earlier revision of `default.txt` was published as a GitHub gist
(`ef36fb8da928f25c60cd0ecb82a80750`). That gist is **out of date** and should not be
treated as the prompt behind the reported results. It predates, among other changes:

- the `{{taxonomy_hints}}` template variable
- the passive-voice / party-role guidance that keeps tenants from being classified as landlords
- the plain-language vocabulary rules, including the prohibition on unexplained acronyms
  (SSA, SSI, EEOC, FMLA, ADA)
- the worked examples of good and bad follow-up questions
- the instruction to answer in the applicant's own language
- the instruction not to re-ask what the applicant already stated
- the instruction not to ask what the applicant *wants to do* rather than what happened

Several of those changes are the direct result of the Oregon State Bar focus-group
feedback described in the paper, so the gist does not reflect the system as evaluated.
Cite this directory instead.
