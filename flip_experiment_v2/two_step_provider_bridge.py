"""Bridge the v2 disclosure-flip benchmark to FETCH's two-step provider.

Differences from the v1 bridge:

- The question/hidden-fact relevance matcher runs on GPT-5 (``match_model``)
  instead of GPT-4.1. GPT-5 on the Azure OpenAI v1 chat-completions endpoint
  rejects ``temperature`` values other than the default and the legacy
  ``max_tokens`` parameter, so the provider's matcher is replaced with a
  GPT-5-compatible implementation. The replacement also logs matcher errors to
  stderr instead of silently returning "no match" (a v1 failure mode that
  would have zeroed coverage if the model call had been misconfigured).
- Matcher usage/reason metadata is recorded per call in a module-level list so
  the runner can archive it.

Set FETCH_REPO_ROOT when the FETCH checkout is not the grandparent of this
file. The bridge always disables FETCH's internal cache.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
FETCH_ROOT = Path(os.environ.get("FETCH_REPO_ROOT", HERE.parents[1])).resolve()
PROVIDER_PATH = FETCH_ROOT / "promptfoo/two_step_followup_provider.py"

if not PROVIDER_PATH.exists():
    raise FileNotFoundError(
        f"FETCH two-step provider not found at {PROVIDER_PATH}. "
        "Set FETCH_REPO_ROOT to the FETCH repository root."
    )

spec = importlib.util.spec_from_file_location("fetch_two_step_provider", PROVIDER_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load {PROVIDER_PATH}")
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)

# The study provider predates the current ClassificationService API and still
# passes ``semantic_merge_model_override``; drop only that retired keyword.
_CurrentClassificationService = provider.ClassificationService


def _compatible_classification_service(*args, semantic_merge_model_override=None, **kwargs):
    return _CurrentClassificationService(*args, **kwargs)


provider.ClassificationService = _compatible_classification_service


MATCHER_LOG: list[dict] = []
_MATCHER_LOG_LOCK = threading.Lock()
MATCHER_ERRORS = {"count": 0}


async def _match_question_to_fact_gpt5(
    questions: list,
    hidden_fact: str,
    client,
    model: str = "gpt-5",
) -> tuple[bool, Optional[int], Optional[str]]:
    """GPT-5-compatible replacement for the provider's matcher.

    Same contract and same prompt as the original (so results remain
    comparable), but uses ``max_completion_tokens`` and the default
    temperature, which GPT-5 requires, and gives the model reasoning headroom.
    """
    if not questions or not hidden_fact:
        return False, None, None

    questions_text = "\n".join(
        f"{i + 1}. {q.get('question', '')} (options: {q.get('options', [])})"
        for i, q in enumerate(questions)
    )

    prompt = f"""Given these follow-up questions that a legal intake assistant generated:

{questions_text}

And this hidden fact that a user has not yet revealed:
  "{hidden_fact}"

Which question number (1-{len(questions)}), if any, would be DIRECTLY answered by this hidden fact?
Answer ONLY with a JSON object: {{"matched": true/false, "question_index": 1-based-number-or-null, "reason": "brief reason"}}
If no question is relevant, set matched=false and question_index=null.
"""

    entry = {
        "model": model,
        "question_count": len(questions),
        "matched": False,
        "question_index": None,
        "reason": None,
        "error": None,
        "usage": None,
    }
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise evaluator. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=2000,
        )
        raw = (resp.choices[0].message.content or "").strip()
        if resp.usage is not None:
            entry["usage"] = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
        data = json.loads(raw)
        matched = bool(data.get("matched", False))
        idx = data.get("question_index")
        entry["reason"] = data.get("reason")
        if matched and idx is not None:
            idx = int(idx) - 1
            if 0 <= idx < len(questions):
                entry["matched"] = True
                entry["question_index"] = idx
                with _MATCHER_LOG_LOCK:
                    MATCHER_LOG.append(entry)
                return True, idx, questions[idx].get("question", "")
        with _MATCHER_LOG_LOCK:
            MATCHER_LOG.append(entry)
        return False, None, None
    except Exception as exc:  # log loudly; a silent failure poisons coverage
        entry["error"] = f"{type(exc).__name__}: {exc}"
        with _MATCHER_LOG_LOCK:
            MATCHER_LOG.append(entry)
            MATCHER_ERRORS["count"] += 1
        print(f"MATCHER_ERROR: {entry['error']}", file=sys.stderr, flush=True)
        return False, None, None


provider._match_question_to_fact = _match_question_to_fact_gpt5


async def call_api(prompt, options, context):
    options = dict(options or {})
    config = dict(options.get("config") or {})
    config["cache_enabled"] = False
    options["config"] = config

    context = dict(context or {})
    variables = dict(context.get("vars") or {})
    if config.get("condition") == "counterfactual":
        variables["hidden_fact"] = variables.get("counterfactual_hidden_fact", "")
        variables["fact_as_answer"] = variables.get("counterfactual_fact_as_answer", "")
        variables["final_category"] = variables.get("counterfactual_category", "")
        variables["final_subcategory"] = variables.get("counterfactual_subcategory", "")
    context["vars"] = variables
    return await provider.call_api(prompt, options, context)
