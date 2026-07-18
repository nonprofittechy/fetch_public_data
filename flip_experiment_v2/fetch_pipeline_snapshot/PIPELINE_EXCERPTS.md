# FETCH pipeline excerpts

Narrow, attributed quotes from the private FETCH repository — the specific
lines that determine this study's classification behavior. See
`README.md` for scope and redistribution notes. All file paths are relative
to the FETCH repo root; none of this repo's own paths.

## 1. The two fixed code paths (post-fix state, `fix/followup-context-and-provider-mix`)

These are exactly the bugs and fixes described in
`../analysis/RESULTS.md` and `../analysis/EXECUTION_LOG.md`.

**`app/providers/openai.py`, GPT-5-family Responses API call construction:**
```python
responses_params: Dict[str, Any] = {
    "model": self.model_name,
    "input": build_messages(prompt, problem_description, followup_answers),
}
```
Before the fix: `"input": f"SYSTEM:\n{prompt}\n\nUSER:\n{problem_description}"`
— built from `problem_description` alone, never referencing
`followup_answers`, so the second (post-disclosure) call was byte-identical
to the first.

**`app/services/classification_service.py`, refinement-call provider filter:**
```python
FOLLOWUP_EXCLUDED_PROVIDER_TYPES = {"keyword", "spot"}
...
if request.followup_answers:
    current_providers = [
        p for p in current_providers
        if p.provider_type not in FOLLOWUP_EXCLUDED_PROVIDER_TYPES
    ]
```
Before the fix: `isinstance(p, LLMClassifierProvider)` — correctly excluded
keyword/spot but also incorrectly excluded Gemini and Mistral, which are
real LLMs that subclass `ClassifierProvider` directly rather than
`LLMClassifierProvider` (only `OpenAIProvider` does).

## 2. Classification prompt (`app/prompts/default.txt`)

The system prompt sent to every provider (with `{{taxonomy}}` and
`{{taxonomy_hints}}` interpolated). Excerpted sections only — the full
taxonomy block is 209 category/subcategory rows and is not reproduced here
verbatim (the category/subcategory *names*, but not their enriched
descriptions or the surrounding prompt engineering, are already visible
throughout this benchmark's own candidate files and analysis output).

```
You are a legal expert AI. Your task is to classify a user's legal problem
based on the provided taxonomy and determine if their problem has a legal
solution.

CLASSIFICATION APPROACH:
1. Always try to provide your best guess classification, even with limited information
2. Match the user's problem to the most relevant categories in the taxonomy
3. Taxonomy terms are often written from the perspective of the person looking for help.
   Look for the user's role in their problem description and match it to the appropriate taxonomy.
4. IMPORTANT: If the user describes a situation using passive voice (e.g., "I am getting kicked out",
   "I'm being evicted"), this indicates they are the one BEING ACTED UPON, not the actor.
   They are the tenant or vulnerable party, not the landlord or party with authority.
5. Include targeted follow-up questions if they might be helpful to narrow down the user's problem between multiple categories
6. Only set categories to null if the problem is truly impossible to classify from the given information

FOLLOW-UP QUESTIONS GUIDELINES:
- Limit to 3 questions
- Prefer multiple choice over open-ended questions
- Focus on getting answers that would significantly change which taxonomy term you select to classify the problem
- Generate the MINIMUM number of questions needed. If the issue is clear, generate 0-1 questions.
- Do NOT ask about what the user plans to do or wants to do. Only ask routing and classification
  questions that help identify the legal issue type and appropriate attorney specialty.
- Before including a question, check: did the user already answer this? If yes, do NOT ask it.
```

This is directly relevant to reading this study's results: point 3/4 above
is FETCH's own built-in heuristic for inferring the user's role from passive
vs. active voice — a different (and narrower) mechanism than any of this
benchmark's disclosure-based facts, and worth distinguishing from v1's
role-reversal design, which this heuristic was presumably meant to help
FETCH resolve on its own without a follow-up question at all.

## 3. Multi-turn refinement message construction (`app/providers/utils.py`, `build_messages()`)

```python
messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": problem_description},
]
if followup_answers:
    for answer in followup_answers:
        messages.append({"role": "assistant", "content": q})   # the matched question
        messages.append({"role": "user", "content": a})        # the disclosed answer
    messages.append({
        "role": "user",
        "content": (
            "Based on my original problem and all my answers above, please "
            "provide your final classification as JSON. Do NOT ask any of "
            "these questions again, as I have already answered them:\n"
            + "\n".join(f"- {q}" for q in answered_questions)
        ),
    })
```
This is the function the fixed Responses API branch now calls (§1 above);
it already existed and was already correctly used by the non-GPT-5 chat-
completions code path — the bug was that the GPT-5-family branch built its
own flat string instead of calling this function.

## 4. Vote-determining constants

**Provider weights** (`app/core/config.py`, `CLASSIFIER_WEIGHTS`):
```python
{"gemini": 0.8, "gpt-4.1-mini": 0.8, "gpt-4.1-nano": 0.75, "gpt-5": 0.9,
 "gpt-5.2": 0.9, "spot": 0.6, "keyword": 0.5, "mistral": 0.8}
```

**Label-selection thresholds** (`app/services/classification_service.py`):
```python
DEFAULT_LABEL_SELECTION_MAX_LABELS = 3
DEFAULT_LABEL_SELECTION_SCORE_WINDOW = 0.9
```
A label makes the final set if it's within `SCORE_WINDOW` (90%) of the
top-scoring label's weighted vote total, capped at 3 labels, with a
"multi-issue" heuristic that can widen this based on the problem
description's punctuation/clause structure. Per-provider confidence is
hard-coded to `1.0` for every label a provider returns (verified in
`app/providers/openai.py`, `gemini.py`, `mistral.py`) — so in practice a
label's score is `sum(weight[p] for p in providers that named this label)`,
not a calibrated confidence signal.

**GPT-5 family and reasoning effort** (`app/providers/openai.py`,
`app/core/config.py`):
```python
GPT_5_FAMILY_MODELS = {"gpt-5", "gpt-5-mini", "gpt-5.2"}
GPT_5_REASONING_EFFORT = os.getenv("GPT_5_REASONING_EFFORT", "low").strip().lower()
```
GPT-5-family calls never set `temperature` (the Responses API branch omits
it entirely, per an inline comment: "Avoid temperature/response_format for
compatibility; enforce JSON via instructions") — only `reasoning_effort`,
defaulting to `"low"`. Two calls with byte-identical input are therefore not
guaranteed to return identical output, which is the mechanism behind the
pre-fix "resampling noise" explanation in `../analysis/RESULTS.md`.

## 5. This study's provider configuration

Recorded in full, per run, in each run's `results/<run>/run_metadata.json`
(`provider_config` key) and in `../run_direct.py`. Summary:

```python
provider_config = {
    "enabled_providers": ["gpt-5", "gemini", "mistral", "keyword", "spot"],
    "decision_mode": "vote",
    "cache_enabled": False,
    "semantic_merge_model": "gpt-5",
    "match_model": "gpt-5",
}
```
All 5 providers vote on the initial call; §1's fix means the follow-up call
automatically narrows to `gpt-5`, `gemini`, `mistral` (§4's constants
determine how their votes combine).
