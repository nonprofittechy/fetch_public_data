"""FETCH ensemble-screen generation bridge for the nano-vs-full readability study.

A "screen" is the merged set of follow-up questions FETCH shows a user after the
opening query. This study reproduces the *production* A/B that Quinten's team
already shipped: the FETCH classification ensemble with its OpenAI member set to
`gpt-5-nano` (the old default) versus `gpt-5.2` (the new default), with the
semantic-merge model swapped to match. Everything else in the ensemble
(gemini, mistral, keyword, spot) is held constant across arms, so any difference
in the screen is attributable to the swapped model tier at BOTH stages
(generation member + merge) -- the "adjust the model selection twice" the study
manipulates.

    arm=nano  ->  ensemble OpenAI member = gpt-5-nano,  merge model = gpt-5-nano
    arm=full  ->  ensemble OpenAI member = gpt-5.2,      merge model = gpt-5.2

Shared ensemble members (both arms): gemini, mistral. keyword/spot are omitted
because they only cast label votes and never emit follow-up questions, so they
cannot affect the screen under study.

Unit of analysis: the merged screen == resp.follow_up_questions (FETCH's top-3
after semantic merge). We use FETCH's real ClassificationService.classify() path
so generation, voting, singleton-rescue selection, and semantic merge all run
exactly as in production.

Implementation notes (reproducibility):

1. gpt-5-nano is not a registered provider and is not in GPT_5_FAMILY_MODELS, so
   (a) we add it to that set at runtime so it uses the Responses API (its
   chat.completions path returns empty content for reasoning models), and
   (b) we inject an OpenAIProvider(model_name="gpt-5-nano") into the service's
   provider list for the nano arm. No parent-repo source is modified.

2. The merge model is selected via the OPENAI_SEMANTIC_MERGE_MODEL env var, read
   by ClassificationService._get_semantic_merge_model_name() at call time. We set
   it per arm before each classify().

3. Merge fallback order is openai -> gemini -> mistral. openai (the target model)
   is tried first; we record app.log's "semantic_merge completed with model=X"
   line separately to confirm no fallback contaminated a run.

Credentials come from /home/quinten/fetch/.env (Azure endpoint).
"""
from __future__ import annotations

import asyncio
import os
import sys
import warnings
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

FETCH_REPO = os.environ.get("FETCH_REPO", "/home/quinten/fetch")

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(FETCH_REPO, ".env"))
except Exception:
    pass

# Telemetry export targets an Azure Monitor host that is unreachable from this
# environment; disable it so it adds neither latency nor log noise to the run.
os.environ["TELEMETRY_ENABLED"] = "false"

# Raise per-provider and merge timeouts (defaults 17s/12s) so a slow reasoning
# call on gpt-5.2/nano does not silently drop the arm-defining member from a
# screen. These are read at import time by app.core.config, so set them first.
os.environ.setdefault("CLASSIFIER_TIMEOUT_SECONDS", "90")
os.environ.setdefault("SEMANTIC_MERGE_TIMEOUT_SECONDS", "60")

if FETCH_REPO not in sys.path:
    sys.path.insert(0, FETCH_REPO)
os.chdir(FETCH_REPO)

import logging  # noqa: E402
from contextvars import ContextVar  # noqa: E402

import app.providers.openai as oai_mod  # noqa: E402
from app.models.api_models import ClassificationRequest  # noqa: E402
from app.services.classification_service import ClassificationService  # noqa: E402

# Make nano use the Responses API path.
oai_mod.GPT_5_FAMILY_MODELS.add("gpt-5-nano")

# --- Per-call provider-failure capture -------------------------------------
# FETCH logs provider failures/timeouts synchronously inside the classify
# coroutine. A ContextVar set at call start is visible to that log emit under
# asyncio, so we can attribute each failure to the specific screen being built
# even with concurrent scenarios in flight.
_capture_var: ContextVar = ContextVar("readability_capture", default=None)
_FAILURE_MARKERS = ("failed", "timed out", "Exception ->", "error:")


class _FailureCaptureHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        bucket = _capture_var.get()
        if bucket is None:
            return
        msg = record.getMessage()
        if any(m in msg for m in _FAILURE_MARKERS):
            bucket.append(msg)


def _install_capture_handler() -> None:
    handler = _FailureCaptureHandler(level=logging.WARNING)
    for name in ("app.services.classification_service", "app.providers"):
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.WARNING)


_install_capture_handler()

# The OpenAI ensemble member that differs between arms. gemini/mistral/keyword/
# spot are shared and identical across arms.
ARM_OPENAI_MEMBER = {
    "full": "gpt-5.2",
    "nano": "gpt-5-nano",
}
SHARED_MEMBERS = ["gemini", "mistral"]

_SERVICES: Dict[str, ClassificationService] = {}


def _build_service(arm: str) -> ClassificationService:
    """Build (and cache) a ClassificationService for one arm's ensemble."""
    openai_member = ARM_OPENAI_MEMBER[arm]
    if arm == "full":
        svc = ClassificationService(
            enabled_providers_override=[openai_member] + SHARED_MEMBERS,
            cache_enabled=False,
        )
    else:  # nano: inject a provider the registry doesn't know about
        svc = ClassificationService(
            enabled_providers_override=SHARED_MEMBERS,
            cache_enabled=False,
        )
        nano = oai_mod.OpenAIProvider(model_name="gpt-5-nano")
        svc._all_providers["gpt-5-nano"] = nano
        svc.providers = [nano] + list(svc.providers)
    return svc


def _get_service(arm: str) -> ClassificationService:
    if arm not in _SERVICES:
        _SERVICES[arm] = _build_service(arm)
    return _SERVICES[arm]


async def _generate_screen_async(
    opening_query: str, arm: str, taxonomy_name: str = "default"
) -> Dict[str, Any]:
    if arm not in ARM_OPENAI_MEMBER:
        raise ValueError(f"unknown arm {arm!r}; expected 'full' or 'nano'")
    merge_model = ARM_OPENAI_MEMBER[arm]
    os.environ["OPENAI_SEMANTIC_MERGE_MODEL"] = merge_model

    service = _get_service(arm)
    member = ARM_OPENAI_MEMBER[arm]
    result: Dict[str, Any] = {
        "opening_query": opening_query,
        "arm": arm,
        "openai_member": member,
        "merge_model": merge_model,
        "ensemble": [p.instance_name for p in service.providers],
        "labels": [],
        "merged_screen": [],
        "provider_failures": [],
        "member_failed": False,
        "error": None,
    }
    token = _capture_var.set([])
    try:
        req = ClassificationRequest(
            text=opening_query,
            taxonomy_name=taxonomy_name,
            decision_mode="vote",
            include_debug_details=False,
        )
        resp = await service.classify(req)
        result["labels"] = [lbl.model_dump() for lbl in resp.labels]
        result["merged_screen"] = [q.model_dump() for q in resp.follow_up_questions]
    except Exception as e:
        import traceback

        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()[-800:]
    finally:
        failures = _capture_var.get() or []
        _capture_var.reset(token)
        result["provider_failures"] = failures
        # The arm-defining OpenAI member dropping out degrades the screen to a
        # gemini+mistral-only screen and must not be pooled with clean screens.
        result["member_failed"] = any(member in f for f in failures)
    return result


def generate_screen(opening_query: str, arm: str, taxonomy_name: str = "default") -> Dict[str, Any]:
    """Synchronous entry point: generate one merged screen for one arm."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError("nested loop")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_generate_screen_async(opening_query, arm, taxonomy_name))


if __name__ == "__main__":
    import json

    arm = sys.argv[1] if len(sys.argv) > 1 else "full"
    q = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "My benefits got cut off last month and nobody at the office will explain anything."
    )
    print(json.dumps(generate_screen(q, arm), indent=2))
