"""promptfoo python assertions computing screen-level readability on the merged
screen JSON emitted by fetch_screen_provider. These mirror the cheap descriptive
readability gates; the full metric battery (presupposition, double-barrel,
simulated respondent, ...) lives in ../../metrics and ../../analysis.
"""
from __future__ import annotations

import json
from typing import Any, Dict


def _screen_questions_text(output: str) -> str:
    try:
        data = json.loads(output)
    except Exception:
        return ""
    qs = data.get("merged_screen", []) or []
    return " ".join((q.get("question") or "") for q in qs).strip()


def dale_chall(output: str, context: Dict[str, Any]) -> Dict[str, Any]:
    import textstat
    txt = _screen_questions_text(output)
    if not txt:
        return {"pass": True, "score": 1, "reason": "empty screen (no text to grade)"}
    score = textstat.dale_chall_readability_score(txt)
    ok = score <= 7.9
    return {"pass": bool(ok), "score": float(score), "reason": f"Dale-Chall={score:.2f} (<=7.9 target)"}


def fkgl(output: str, context: Dict[str, Any]) -> Dict[str, Any]:
    import textstat
    txt = _screen_questions_text(output)
    if not txt:
        return {"pass": True, "score": 1, "reason": "empty screen"}
    g = textstat.flesch_kincaid_grade(txt)
    return {"pass": True, "score": float(g), "reason": f"FKGL={g:.2f} (display-only)"}


def get_assert(output: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # default entrypoint used by promptfoo file://...py assertions
    return dale_chall(output, context)
