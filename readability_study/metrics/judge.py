"""LLM-judge client for the readability study.

Primary automated judge: DeepSeek-V4-Pro, deployed on the study's Azure endpoint
(deployment name `deepseek-v4`) and reached over the OpenAI-compatible route with
the same credentials FETCH uses. DeepSeek is independent of the generation
pipeline (GPT + Gemini + Mistral), so it cannot exhibit same-family favoritism
toward either arm.

A second, cross-family judge (Claude) is applied separately, in-context, on a
blind subset -- see metrics/claude_subset/.

The client returns parsed JSON and retries on transient errors / malformed JSON.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv("/home/quinten/fetch/.env")

import openai

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "deepseek-v4")

_client: Optional[openai.OpenAI] = None


def client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_BASE_URL"],
            max_retries=0,
        )
    return _client


def _extract_json(raw: str) -> Any:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        # grab the first {...} or [...] block
        m = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        raise


def judge_json(
    system: str,
    user: str,
    *,
    model: str = None,
    temperature: float = 0.0,
    seed: Optional[int] = None,
    max_tokens: int = 1500,
    retries: int = 4,
) -> Dict[str, Any]:
    """Call the judge and return parsed JSON. Retries on transient/parse errors."""
    model = model or JUDGE_MODEL
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if seed is not None:
                kwargs["seed"] = seed
            resp = client().chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            return _extract_json(content)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.2 * attempt)
    raise RuntimeError(f"judge_json failed after {retries} attempts: {last_err}")
