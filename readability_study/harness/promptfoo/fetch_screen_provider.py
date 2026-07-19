"""promptfoo custom provider: generate one FETCH screen per arm.

Config:
  arm: "nano" | "full"

Reads the scenario's problem description from vars.problem_description (or the
prompt) and returns the merged screen as JSON. Wraps the study's fetch_screen
bridge so the promptfoo harness drives the exact same generation path as the
Python runner.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

HARNESS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HARNESS_DIR not in sys.path:
    sys.path.insert(0, HARNESS_DIR)

import fetch_screen  # noqa: E402


async def call_api(prompt: str, options: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    config = options.get("config", {})
    arm = config.get("arm", "full")
    vars_ = context.get("vars", {})
    query = vars_.get("problem_description") or prompt
    res = await fetch_screen._generate_screen_async(query, arm)
    payload = json.dumps(res, default=str)
    return {"output": payload, "metadata": {"raw_json": payload,
                                            "arm": arm,
                                            "member_failed": res.get("member_failed"),
                                            "n_questions": len(res.get("merged_screen", []))}}
