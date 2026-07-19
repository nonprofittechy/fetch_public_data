"""Two-step provider bridge for condition C: FETCH with deterministic
screening protocols (PR #34, https://github.com/LemmaLegalConsulting/fetch/pull/34)
merged on top of the follow-up-context fixes (commit 41585d0).

Differs from ``two_step_provider_bridge.py`` (condition B: fixes only, no
screening protocols) in that it calls ``ClassificationService.classify()``
directly instead of delegating to FETCH's
``promptfoo/two_step_followup_provider.py::call_api()``. That harness
function only ever reads ``response.labels`` and has no knowledge of the
screening-protocol response fields PR #34 adds
(``effective_categories``, ``mandatory_categories``, ``screening_questions``,
``screening_resolutions``).

The label set recorded as ``initial_labels``/``final_labels`` — the fields
this repo's ``analyze_runs.py`` scores against — is
``response.effective_categories`` when present: the screening-aware union of
the classifier's own labels and any deterministically mandatory categories a
well-behaved client is supposed to treat as authoritative per
``docs/SCREENING_PROTOCOLS.md``. This falls back to ``response.labels`` if
``effective_categories`` is ever empty while ``labels`` is not (defensive;
should not happen on the merged branch, which always populates it).
``*_labels_model_only`` fields separately record the classifier-only labels
(no screening union) so the screening protocol's specific marginal
contribution can be measured, not just condition B vs. C in aggregate.

Requires ``FETCH_REPO_ROOT`` to point at a FETCH checkout containing BOTH
fixes: see ``flip_experiment_v2/fetch_pipeline_snapshot/README.md`` for how
that checkout was built (a git worktree merging
``fix/followup-context-and-provider-mix`` with ``origin/main``).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

FETCH_ROOT = Path(os.environ.get("FETCH_REPO_ROOT", HERE.parents[1])).resolve()
if str(FETCH_ROOT) not in sys.path:
    sys.path.insert(0, str(FETCH_ROOT))

from app.services.classification_service import ClassificationService
from app.models.api_models import ClassificationRequest, FollowUpAnswer

# Reuse the GPT-5 relevance matcher and its logging from the non-screening
# bridge. This is this repo's own code (not FETCH's), so it's safe to import
# regardless of which FETCH branch/worktree FETCH_ROOT points at.
from two_step_provider_bridge import (  # noqa: E402
    _match_question_to_fact_gpt5,
    MATCHER_LOG,
    MATCHER_ERRORS,
)


def _labels_to_dicts(labels) -> List[Dict[str, Any]]:
    return [
        {"label": l.label, "confidence": l.confidence, "id": l.id}
        for l in (labels or [])
    ]


def _effective_to_dicts(effective) -> List[Dict[str, Any]]:
    return [
        {
            "label": ec.label,
            "confidence": ec.confidence,
            "id": ec.id,
            "mandatory": ec.mandatory,
            "sources": list(ec.sources),
        }
        for ec in (effective or [])
    ]


def _norm(label: str) -> str:
    return " ".join((label or "").strip().lower().split())


def _category_present(labels: List[Dict[str, Any]], expected_cat: str) -> bool:
    want = _norm(expected_cat)
    return any(_norm(l["label"]).split(" > ", 1)[0] == want for l in labels)


def _exact_present(labels: List[Dict[str, Any]], expected_cat: str, expected_sub: str) -> bool:
    want = _norm(f"{expected_cat} > {expected_sub}")
    return any(_norm(l["label"]) == want for l in labels)


async def call_api(prompt: str, options: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Same options/context contract and output JSON shape (for the fields
    shared with condition B) as two_step_provider_bridge.call_api(), plus
    screening-specific fields."""
    options = dict(options or {})
    config = dict(options.get("config") or {})
    context = dict(context or {})
    variables = dict(context.get("vars") or {})

    if config.get("condition") == "counterfactual":
        variables["hidden_fact"] = variables.get("counterfactual_hidden_fact", "")
        variables["fact_as_answer"] = variables.get("counterfactual_fact_as_answer", "")
        variables["final_category"] = variables.get("counterfactual_category", "")
        variables["final_subcategory"] = variables.get("counterfactual_subcategory", "")

    opening_query = variables.get("opening_query", prompt)
    hidden_fact = variables.get("hidden_fact", "")
    fact_as_answer = variables.get("fact_as_answer", hidden_fact)
    initial_category = variables.get("initial_category", "")
    initial_subcategory = variables.get("initial_subcategory", "")
    final_category = variables.get("final_category", "")
    final_subcategory = variables.get("final_subcategory", "")

    enabled_providers = config.get(
        "enabled_providers", ["gpt-5", "gemini", "mistral", "keyword", "spot"]
    )
    decision_mode = config.get("decision_mode", "vote")
    taxonomy_name = config.get("taxonomy_name", "default")
    cache_enabled = config.get("cache_enabled", False)
    cache_dir = config.get("cache_dir", "../cache")
    match_model = config.get("match_model", "gpt-5")

    import openai

    oai_client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )

    service = ClassificationService(
        enabled_providers_override=enabled_providers,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
    )

    result: Dict[str, Any] = {
        "opening_query": opening_query,
        "hidden_fact": hidden_fact,
        "initial_labels": [],
        "initial_labels_model_only": [],
        "initial_top_label": "",
        "follow_up_questions": [],
        "screening_questions": [],
        "screening_resolutions_initial": [],
        "question_matched": False,
        "matched_question": None,
        "matched_question_index": None,
        "match_reason": None,
        "final_labels": None,
        "final_labels_model_only": None,
        "final_top_label": None,
        "screening_resolutions_final": [],
        "mandatory_categories_final": [],
        "initial_category_correct": False,
        "initial_subcategory_correct": False,
        "final_category_correct": None,
        "final_subcategory_correct": None,
        "error": None,
    }

    try:
        req1 = ClassificationRequest(
            text=opening_query,
            taxonomy_name=taxonomy_name,
            decision_mode=decision_mode,
            include_debug_details=False,
        )
        resp1 = await service.classify(req1)

        effective1 = _effective_to_dicts(getattr(resp1, "effective_categories", None))
        model1 = _labels_to_dicts(resp1.labels)
        initial_labels = effective1 or model1
        follow_up_qs = [q.model_dump() for q in resp1.follow_up_questions]

        result["initial_labels"] = initial_labels
        result["initial_labels_model_only"] = model1
        result["initial_top_label"] = initial_labels[0]["label"] if initial_labels else ""
        result["follow_up_questions"] = follow_up_qs
        result["screening_questions"] = [
            q.model_dump() for q in getattr(resp1, "screening_questions", [])
        ]
        result["screening_resolutions_initial"] = [
            r.model_dump() for r in getattr(resp1, "screening_resolutions", [])
        ]
        result["initial_category_correct"] = _category_present(initial_labels, initial_category)
        result["initial_subcategory_correct"] = _exact_present(
            initial_labels, initial_category, initial_subcategory
        )

        if hidden_fact and follow_up_qs:
            matched, match_idx, matched_q_text = await _match_question_to_fact_gpt5(
                follow_up_qs, hidden_fact, oai_client, match_model
            )
            result["question_matched"] = matched
            result["matched_question"] = matched_q_text
            result["matched_question_index"] = match_idx

            if matched and matched_q_text:
                followup_answer = FollowUpAnswer(
                    question=matched_q_text, answer=fact_as_answer or hidden_fact
                )
                req2 = ClassificationRequest(
                    text=opening_query,
                    taxonomy_name=taxonomy_name,
                    decision_mode=decision_mode,
                    include_debug_details=False,
                    followup_answers=[followup_answer],
                )
                resp2 = await service.classify(req2)
                effective2 = _effective_to_dicts(getattr(resp2, "effective_categories", None))
                model2 = _labels_to_dicts(resp2.labels)
                final_labels = effective2 or model2
                result["final_labels"] = final_labels
                result["final_labels_model_only"] = model2
                result["final_top_label"] = final_labels[0]["label"] if final_labels else ""
                result["screening_resolutions_final"] = [
                    r.model_dump() for r in getattr(resp2, "screening_resolutions", [])
                ]
                result["mandatory_categories_final"] = [
                    m.model_dump() for m in getattr(resp2, "mandatory_categories", [])
                ]
                result["final_category_correct"] = _category_present(final_labels, final_category)
                result["final_subcategory_correct"] = _exact_present(
                    final_labels, final_category, final_subcategory
                )

    except Exception as exc:  # preserve and continue the benchmark
        result["error"] = str(exc)
        import traceback

        result["traceback"] = traceback.format_exc()[-500:]
    finally:
        try:
            await service.cleanup()
        except Exception:
            pass

    output_json = json.dumps(result, default=str)
    return {"output": output_json, "metadata": {"raw_json": output_json}}
