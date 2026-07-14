"""Bridge this publishable benchmark to FETCH's existing two-step provider.

Set FETCH_REPO_ROOT when the FETCH checkout is not the parent of this repo.
The bridge always disables FETCH's internal cache, even if a config attempts
to enable it. PromptFoo's cache must also be disabled at the CLI with
``--no-cache``.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


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

# The earlier study provider predates the current ClassificationService API and
# still passes ``semantic_merge_model_override``. Preserve the study provider's
# behavior while discarding only that retired constructor keyword; the current
# service obtains its semantic-merge model from FETCH's environment settings.
_CurrentClassificationService = provider.ClassificationService


def _compatible_classification_service(*args, semantic_merge_model_override=None, **kwargs):
    return _CurrentClassificationService(*args, **kwargs)


provider.ClassificationService = _compatible_classification_service


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
