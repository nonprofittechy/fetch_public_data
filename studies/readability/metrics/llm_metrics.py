"""LLM-graded metrics for the readability study (primary metrics 1-3 + exp. 10).

Each function takes the applicant's original statement, the screen (list of
question dicts), and a `jcall` callable with signature
    jcall(system, user, temperature, seed, max_tokens) -> parsed JSON
so the same rubric can be driven by any judge backend (DeepSeek on Azure, or
Claude in-context). All rubrics operate on the WHOLE screen in one call to keep
the call budget down, and are blind to which arm produced the screen.

Aggregation to the screen uses MAX for "badness" counts (one bad question spoils
a screen), per the study plan.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

JCall = Callable[..., Any]


def _numbered(screen: List[Dict[str, Any]]) -> str:
    lines = []
    for i, q in enumerate(screen, 1):
        opts = q.get("options") or []
        opt_str = ""
        if opts:
            opt_str = " | options: " + "; ".join(str(o) for o in opts)
        lines.append(f"Q{i}: {q.get('question','')}{opt_str}")
    return "\n".join(lines)


# ---------------------------------------------------------------- metric 1
PRESUP_LIST_SYS = (
    "You are a precise linguistic analyst. A follow-up question can PRESUPPOSE "
    "facts -- things it treats as already true about the person's situation "
    "(e.g. 'Which court is your case in?' presupposes there is a case in court). "
    "Return only JSON."
)
PRESUP_VERIFY_SYS = (
    "You check whether presupposed facts are supported by what a person actually "
    "wrote. For each presupposition, decide: SUPPORTED (the person stated it or it "
    "is clearly implied), UNKNOWN (not derivable from what they wrote), or "
    "CONTRADICTED (their statement conflicts with it). Return only JSON."
)


def metric_presupposition(opening_query: str, screen: List[Dict[str, Any]], jcall: JCall,
                          temperature=0.0, seed=0) -> Dict[str, Any]:
    listing = jcall(
        PRESUP_LIST_SYS,
        "For EACH question below, list the factual presuppositions it makes about "
        "the person's situation (0 or more short statements each). Do not judge them "
        "yet.\n\nQuestions:\n" + _numbered(screen) +
        '\n\nReturn JSON: {"questions":[{"q":1,"presuppositions":["...","..."]},...]}',
        temperature=temperature, seed=seed, max_tokens=1200,
    )
    qlist = listing.get("questions", []) if isinstance(listing, dict) else []
    # flatten for verification
    flat = []
    for item in qlist:
        qi = item.get("q")
        for p in item.get("presuppositions", []) or []:
            flat.append({"q": qi, "presupposition": p})
    if not flat:
        return {"per_question": [0] * len(screen), "screen_max": 0, "screen_sum": 0, "detail": []}
    verify = jcall(
        PRESUP_VERIFY_SYS,
        f"The person wrote:\n\"{opening_query}\"\n\nClassify each presupposition as "
        "SUPPORTED, UNKNOWN, or CONTRADICTED against ONLY what they wrote.\n\n"
        "Presuppositions:\n" +
        "\n".join(f"{i}. (from Q{d['q']}) {d['presupposition']}" for i, d in enumerate(flat, 1)) +
        '\n\nReturn JSON: {"items":[{"i":1,"verdict":"SUPPORTED|UNKNOWN|CONTRADICTED"},...]}',
        temperature=temperature, seed=seed, max_tokens=1200,
    )
    verdicts = {it.get("i"): (it.get("verdict") or "").upper() for it in verify.get("items", [])}
    per_q = [0] * len(screen)
    detail = []
    for i, d in enumerate(flat, 1):
        v = verdicts.get(i, "UNKNOWN")
        bad = v in ("UNKNOWN", "CONTRADICTED")
        qi = d["q"]
        if isinstance(qi, int) and 1 <= qi <= len(screen) and bad:
            per_q[qi - 1] += 1
        detail.append({"q": qi, "presupposition": d["presupposition"], "verdict": v})
    return {
        "per_question": per_q,
        "screen_max": max(per_q) if per_q else 0,
        "screen_sum": sum(per_q),
        "detail": detail,
    }


# ---------------------------------------------------------------- metric 2
DOUBLE_SYS = (
    "You split questions into atomic questions. A question is 'double-barreled' if "
    "its wording asks about more than one distinct thing, so a single answer could "
    "be ambiguous (e.g. 'Are you employed and paid hourly?'). Rewrite each question "
    "STEM as the MINIMUM number of separate questions such that each asks exactly "
    "one thing. IMPORTANT: ignore any multiple-choice answer options -- a single "
    "question that offers several answer choices is ONE question and rewrites to a "
    "list of length 1. Only count distinct things asked by the question sentence "
    "itself. Return only JSON."
)


def _stems_only(screen: List[Dict[str, Any]]) -> str:
    return "\n".join(f"Q{i}: {q.get('question','')}" for i, q in enumerate(screen, 1))


def metric_double_barrel(opening_query: str, screen: List[Dict[str, Any]], jcall: JCall,
                         temperature=0.0, seed=0) -> Dict[str, Any]:
    out = jcall(
        DOUBLE_SYS,
        "Rewrite each question STEM as the minimum number of one-thing questions. "
        "Ignore answer options entirely.\n\n"
        "Questions:\n" + _stems_only(screen) +
        '\n\nReturn JSON: {"questions":[{"q":1,"atomic":["...","..."]},...]}',
        temperature=temperature, seed=seed, max_tokens=1400,
    )
    qlist = out.get("questions", []) if isinstance(out, dict) else []
    counts_by_q = {}
    for item in qlist:
        counts_by_q[item.get("q")] = max(1, len(item.get("atomic", []) or [""]))
    per_q = [counts_by_q.get(i, 1) for i in range(1, len(screen) + 1)]
    flags = [1 if c > 1 else 0 for c in per_q]
    return {
        "per_question": per_q,
        "screen_max": max(per_q) if per_q else 0,
        "screen_flag": 1 if any(flags) else 0,
        "n_double": sum(flags),
    }


# ---------------------------------------------------------------- metric 3
RESPONDENT_SYS = (
    "You role-play the ordinary person who wrote a request for legal help. You only "
    "know what your own statement implies about your situation; you are not a lawyer "
    "and you do not know legal jargon unless it was explained. For each follow-up "
    "question you are shown, decide honestly: ANSWERABLE (you understand it and can "
    "answer from what you know), UNCLEAR (you are not sure what it is asking, or a "
    "word is confusing), or NOT_APPLICABLE (clear, but doesn't fit your situation). "
    "Return only JSON."
)


def metric_simulated_respondent(opening_query: str, screen: List[Dict[str, Any]], jcall: JCall,
                                temperature=0.7, seed=0) -> Dict[str, Any]:
    out = jcall(
        RESPONDENT_SYS,
        f"Your statement was:\n\"{opening_query}\"\n\nHere is the screen of follow-up "
        "questions you are being asked:\n" + _numbered(screen) +
        '\n\nFor each question return your rating and a one-line answer or reason.\n'
        'Return JSON: {"questions":[{"q":1,"rating":"ANSWERABLE|UNCLEAR|NOT_APPLICABLE",'
        '"answer":"..."},...]}',
        temperature=temperature, seed=seed, max_tokens=1200,
    )
    qlist = out.get("questions", []) if isinstance(out, dict) else []
    ratings = {it.get("q"): (it.get("rating") or "").upper() for it in qlist}
    per_q = [ratings.get(i, "UNCLEAR") for i in range(1, len(screen) + 1)]
    n = len(screen)
    unclear = sum(1 for r in per_q if r == "UNCLEAR")
    answerable = sum(1 for r in per_q if r == "ANSWERABLE")
    na = sum(1 for r in per_q if r == "NOT_APPLICABLE")
    return {
        "per_question": per_q,
        "n": n,
        "unclear": unclear,
        "answerable": answerable,
        "not_applicable": na,
        "unclear_rate": round(unclear / n, 4) if n else 0.0,
        "answerable_rate": round(answerable / n, 4) if n else 0.0,
    }


# ---------------------------------------------------------------- metric 10
RESTATE_SYS = (
    "You paraphrase a single question into faithful plain-language restatements. "
    "Each restatement must preserve the exact intended meaning. Return only JSON."
)

_NLI = {}


def _nli():
    if not _NLI:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tok = AutoTokenizer.from_pretrained("roberta-large-mnli")
        model = AutoModelForSequenceClassification.from_pretrained("roberta-large-mnli")
        model.eval()
        _NLI.update(tok=tok, model=model, torch=torch,
                    ent_idx=[i for i, l in model.config.id2label.items() if l == "ENTAILMENT"][0])
    return _NLI


def _entails(a: str, b: str) -> float:
    g = _nli()
    tok, model, torch = g["tok"], g["model"], g["torch"]
    x = tok(a, b, return_tensors="pt", truncation=True)
    with torch.no_grad():
        probs = torch.softmax(model(**x).logits, dim=-1)[0]
    return probs[g["ent_idx"]].item()


def _cluster_by_entailment(texts: List[str], thr: float = 0.5) -> int:
    n = len(texts)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if _entails(texts[i], texts[j]) > thr and _entails(texts[j], texts[i]) > thr:
                parent[find(i)] = find(j)
    return len({find(i) for i in range(n)})


def metric_ambiguity(opening_query: str, screen: List[Dict[str, Any]], jcall: JCall,
                     temperature=1.0, seed=0) -> Dict[str, Any]:
    per_q = []
    for q in screen:
        qt = q.get("question", "")
        out = jcall(
            RESTATE_SYS,
            f'Produce 5 faithful plain-language restatements of this question:\n"{qt}"\n\n'
            'Return JSON: {"restatements":["...","...","...","...","..."]}',
            temperature=temperature, seed=seed, max_tokens=400,
        )
        rests = out.get("restatements", []) if isinstance(out, dict) else []
        variants = [qt] + [r for r in rests if isinstance(r, str) and r.strip()]
        n_clusters = _cluster_by_entailment(variants) if len(variants) > 1 else 1
        per_q.append(n_clusters)
    return {"per_question": per_q, "screen_max": max(per_q) if per_q else 0}
