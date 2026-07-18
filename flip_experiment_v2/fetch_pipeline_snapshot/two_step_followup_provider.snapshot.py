"""
Two-step promptfoo provider for the follow-up question experiment.

For each test case (scenario), this provider:
1. Calls the classification service with just the opening_query
   → records initial labels + follow-up questions
2. Uses an LLM to determine if any generated follow-up question is relevant
   to the hidden_fact in the test case
3. If a relevant question exists, calls classification service AGAIN with the
   hidden fact supplied as a follow-up answer
   → records final labels

Returns a JSON object with:
  - initial_labels: [{label, confidence}]
  - initial_top_label: str
  - follow_up_questions: [{question, options}]
  - question_matched: bool
  - matched_question: str or null
  - matched_question_index: int or null
  - final_labels: [{label, confidence}] (null if no match)
  - final_top_label: str or null (null if no match)
  - initial_category_correct: bool
  - final_category_correct: bool or null
  - hidden_fact: str (for reference)
  - opening_query: str (for reference)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import warnings
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

# Ensure repo root is in path
if os.path.isfile(__file__):
    promptfoo_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(promptfoo_dir)
else:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

os.chdir(repo_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.services.classification_service import ClassificationService
from app.models.api_models import ClassificationRequest, FollowUpAnswer
from app.providers.base import clear_all_prompt_caches


def _norm_label(label: str) -> str:
    """Normalize label for comparison (lowercase, strip whitespace)."""
    return (label or "").strip().lower()


def _top_category(labels: list) -> str:
    """Extract the top-level category name from the first label."""
    if not labels:
        return ""
    first = labels[0].get("label", "")
    return first.split(" > ")[0].strip()


def _label_matches_category(labels: list, expected_cat: str, expected_sub: str = "") -> bool:
    """Check if any label matches the expected top-level category.

    Top-level category match is the primary criterion (subcategory is informational only).
    """
    norm_cat = _norm_label(expected_cat)
    if not norm_cat:
        return False
    for label_obj in labels:
        lbl = _norm_label(label_obj.get("label", ""))
        top_cat = lbl.split(" > ")[0].strip()
        if top_cat == norm_cat:
            return True
    return False


def _label_matches_subcategory(labels: list, expected_cat: str, expected_sub: str) -> bool:
    """Check if any label matches the expected category AND subcategory exactly."""
    norm_cat = _norm_label(expected_cat)
    norm_sub = _norm_label(expected_sub)
    for label_obj in labels:
        lbl = _norm_label(label_obj.get("label", ""))
        parts = lbl.split(" > ")
        cat = parts[0].strip() if parts else ""
        sub = parts[1].strip() if len(parts) > 1 else ""
        if cat == norm_cat and sub == norm_sub:
            return True
    return False


async def _match_question_to_fact(
    questions: list,
    hidden_fact: str,
    client,
    model: str = "gpt-4.1",
) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Ask an LLM: which (if any) of these follow-up questions would be answered
    by revealing this hidden fact?

    Returns: (matched: bool, index: Optional[int], question_text: Optional[str])
    """
    if not questions or not hidden_fact:
        return False, None, None

    questions_text = "\n".join(
        f"{i+1}. {q.get('question', '')} (options: {q.get('options', [])})"
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
            temperature=0,
            max_tokens=200,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Strip markdown if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
        data = json.loads(raw)
        matched = bool(data.get("matched", False))
        idx = data.get("question_index")
        if matched and idx is not None:
            idx = int(idx) - 1  # convert to 0-based
            if 0 <= idx < len(questions):
                return True, idx, questions[idx].get("question", "")
        return False, None, None
    except Exception as e:
        # If matching fails, default to no match
        return False, None, None


async def call_api(
    prompt: str,
    options: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Main entrypoint called by PromptFoo."""
    clear_all_prompt_caches()

    config = options.get("config", {})
    enabled_providers = config.get("enabled_providers", ["gpt-5", "gemini", "mistral", "keyword", "spot"])
    decision_mode = config.get("decision_mode", "vote")
    taxonomy_name = config.get("taxonomy_name", "default")
    cache_enabled = config.get("cache_enabled", True)
    cache_dir = config.get("cache_dir", "./cache")
    semantic_merge_model = config.get("semantic_merge_model") or None
    match_model = config.get("match_model", "gpt-4.1")

    vars_ = context.get("vars", {})
    opening_query = vars_.get("opening_query", prompt)
    hidden_fact = vars_.get("hidden_fact", "")
    fact_as_answer = vars_.get("fact_as_answer", hidden_fact)
    initial_category = vars_.get("initial_category", "")
    initial_subcategory = vars_.get("initial_subcategory", "")
    final_category = vars_.get("final_category", "")
    final_subcategory = vars_.get("final_subcategory", "")

    import openai
    oai_client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )

    service = ClassificationService(
        enabled_providers_override=enabled_providers,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
        semantic_merge_model_override=semantic_merge_model,
    )

    result = {
        "opening_query": opening_query,
        "hidden_fact": hidden_fact,
        "initial_labels": [],
        "initial_top_label": "",
        "follow_up_questions": [],
        "question_matched": False,
        "matched_question": None,
        "matched_question_index": None,
        "match_reason": None,
        "final_labels": None,
        "final_top_label": None,
        "initial_category_correct": False,
        "initial_subcategory_correct": False,
        "final_category_correct": None,
        "final_subcategory_correct": None,
        "error": None,
    }

    try:
        # Step 1: Initial classification
        req1 = ClassificationRequest(
            text=opening_query,
            taxonomy_name=taxonomy_name,
            decision_mode=decision_mode,
            include_debug_details=False,
        )
        resp1 = await service.classify(req1)

        initial_labels = [lbl.model_dump() for lbl in resp1.labels]
        follow_up_qs = [q.model_dump() for q in resp1.follow_up_questions]

        result["initial_labels"] = initial_labels
        result["initial_top_label"] = initial_labels[0]["label"] if initial_labels else ""
        result["follow_up_questions"] = follow_up_qs
        result["initial_category_correct"] = _label_matches_category(
            initial_labels, initial_category
        )
        result["initial_subcategory_correct"] = _label_matches_subcategory(
            initial_labels, initial_category, initial_subcategory
        )

        # Step 2: Match follow-up questions to hidden fact
        if hidden_fact and follow_up_qs:
            matched, match_idx, matched_q_text = await _match_question_to_fact(
                follow_up_qs, hidden_fact, oai_client, match_model
            )
            result["question_matched"] = matched
            result["matched_question"] = matched_q_text
            result["matched_question_index"] = match_idx

            # Step 3: If matched, re-classify with the hidden fact as a follow-up answer
            if matched and matched_q_text:
                followup_answer = FollowUpAnswer(
                    question=matched_q_text,
                    answer=fact_as_answer or hidden_fact,
                )
                req2 = ClassificationRequest(
                    text=opening_query,
                    taxonomy_name=taxonomy_name,
                    decision_mode=decision_mode,
                    include_debug_details=False,
                    followup_answers=[followup_answer],
                )
                resp2 = await service.classify(req2)
                final_labels = [lbl.model_dump() for lbl in resp2.labels]
                result["final_labels"] = final_labels
                result["final_top_label"] = final_labels[0]["label"] if final_labels else ""
                result["final_category_correct"] = _label_matches_category(
                    final_labels, final_category
                )
                result["final_subcategory_correct"] = _label_matches_subcategory(
                    final_labels, final_category, final_subcategory
                )

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()[-500:]
    finally:
        try:
            await service.cleanup()
        except Exception:
            pass

    output_json = json.dumps(result, default=str)
    return {"output": output_json, "metadata": {"raw_json": output_json}}
