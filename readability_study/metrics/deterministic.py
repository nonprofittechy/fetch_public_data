#!/usr/bin/env python3
"""Deterministic (no-API) metrics for the readability study.

Covers the cheap Tier-2 metrics plus metric 4 (unintroduced hard vocabulary),
which is deterministic even though it is a Tier-1 primary:

  4  unintroduced_hard_vocab   content tokens with Zipf < 3, excluding words the
                               applicant already used or that are glossed on-screen
  5  max_dependency_length     spaCy parse, longest head-dependent arc
  6  agentless_passive         PassivePy, agentless/truncated passive count
  7  max_surprisal             GPT-2 Small, peak per-token -log2 P
  8  screen_load               total content tokens + newly-introduced entities
  9  negation_x_conditional    question contains BOTH a negation and a conditional

Plus descriptive readability (FKGL, Dale-Chall) for context.

A "screen" aggregates its questions with MAX (one bad question spoils a screen),
per the study plan. Each function returns both per-question detail and the screen
aggregate.

Usage:
  python deterministic.py --run-id main_20260719
Writes results/generation/<run_id>/metrics_deterministic.jsonl (one row/screen).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import warnings
from typing import Any, Dict, List

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))

# ---- lazy singletons -------------------------------------------------------
_NLP = None
_GPT2 = {}
_PASSIVE = None


def nlp():
    global _NLP
    if _NLP is None:
        import spacy

        _NLP = spacy.load("en_core_web_sm")
    return _NLP


def gpt2():
    if not _GPT2:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained("gpt2")
        model = AutoModelForCausalLM.from_pretrained("gpt2")
        model.eval()
        _GPT2["tok"] = tok
        _GPT2["model"] = model
        _GPT2["torch"] = torch
    return _GPT2


def passive():
    global _PASSIVE
    if _PASSIVE is None:
        from PassivePySrc import PassivePy

        _PASSIVE = PassivePy.PassivePyAnalyzer(spacy_model="en_core_web_sm")
    return _PASSIVE


# ---- text helpers ----------------------------------------------------------
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
NEGATIONS = {"no", "not", "never", "none", "cannot", "n't", "without", "neither", "nor"}
CONDITIONALS = {"if", "unless", "except", "whether", "when", "provided", "assuming"}


def question_text(q: Dict[str, Any]) -> str:
    return (q.get("question") or "").strip()


def option_texts(q: Dict[str, Any]) -> List[str]:
    return [str(o) for o in (q.get("options") or [])]


def screen_full_text(screen: List[Dict[str, Any]]) -> str:
    parts = []
    for q in screen:
        parts.append(question_text(q))
        parts.extend(option_texts(q))
    return "\n".join(p for p in parts if p)


def _tokens_lower(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z'\-]+", (text or "").lower()))


# ---- metric 4: unintroduced hard vocabulary --------------------------------
def _glossed_terms(text: str) -> set[str]:
    """Words that are explained on-screen: any content word that is immediately
    followed by a parenthetical/dash gloss, plus every word inside the gloss.
    A term the screen bothers to explain is, by construction, introduced.
    """
    glossed: set[str] = set()
    # words inside parentheses are the explanation itself
    for m in re.finditer(r"\(([^)]*)\)", text):
        glossed |= _tokens_lower(m.group(1))
    # the head word(s) right before a "(" or " - "/" -- " gloss
    for m in re.finditer(r"([A-Za-z][A-Za-z'\-]+)\s*[\(—\-]", text):
        glossed.add(m.group(1).lower())
    # acronyms defined like "Supplemental Security Income (SSI)" — the acronym
    for m in re.finditer(r"\(([A-Z]{2,6})\)", text):
        glossed.add(m.group(1).lower())
    return glossed


def metric_unintroduced_hard_vocab(opening_query: str, screen: List[Dict[str, Any]], zipf_floor: float = 3.0):
    from wordfreq import zipf_frequency

    applicant = _tokens_lower(opening_query)
    per_q = []
    hard_words_screen: set[str] = set()
    for q in screen:
        qtext = question_text(q)
        gloss = _glossed_terms(qtext + " " + " ".join(option_texts(q)))
        doc = nlp()(qtext + ("\n" + "\n".join(option_texts(q)) if option_texts(q) else ""))
        hard = []
        for tok in doc:
            if tok.pos_ not in CONTENT_POS:
                continue
            if not tok.is_alpha or len(tok.text) < 3:
                continue
            lemma = tok.lemma_.lower()
            surface = tok.text.lower()
            if surface in applicant or lemma in applicant:
                continue
            if surface in gloss or lemma in gloss:
                continue
            z = zipf_frequency(surface, "en")
            if z < zipf_floor:
                hard.append(surface)
        per_q.append(len(set(hard)))
        hard_words_screen |= set(hard)
    return {
        "per_question": per_q,
        "screen_max": max(per_q) if per_q else 0,
        "screen_unique": len(hard_words_screen),
        "hard_words": sorted(hard_words_screen),
    }


# ---- metric 5: max dependency length ---------------------------------------
def metric_max_dependency_length(screen: List[Dict[str, Any]]):
    per_q = []
    for q in screen:
        doc = nlp()(question_text(q))
        longest = 0
        for tok in doc:
            if tok.head is not None:
                longest = max(longest, abs(tok.i - tok.head.i))
        per_q.append(longest)
    return {"per_question": per_q, "screen_max": max(per_q) if per_q else 0}


# ---- metric 6: agentless passive -------------------------------------------
def metric_agentless_passive(screen: List[Dict[str, Any]]):
    pp = passive()
    per_q = []
    truncated_flags = []
    for q in screen:
        txt = question_text(q)
        try:
            df = pp.match_text(txt)
            # PassivePy returns a one-row df with passive counts
            row = df.iloc[0] if len(df) else None
            count = int(row.get("passive_count", 0)) if row is not None else 0
            # truncated == agentless passive (no "by ..." agent)
            truncated = 0
            if row is not None:
                truncated = int(row.get("truncated_passive_count", row.get("passive_count", 0)) or 0)
        except Exception:
            count, truncated = 0, 0
        per_q.append(count)
        truncated_flags.append(truncated)
    return {
        "per_question": per_q,
        "screen_max": max(per_q) if per_q else 0,
        "truncated_per_question": truncated_flags,
        "screen_truncated_max": max(truncated_flags) if truncated_flags else 0,
    }


# ---- metric 7: max GPT-2 surprisal -----------------------------------------
def metric_max_surprisal(screen: List[Dict[str, Any]]):
    g = gpt2()
    tok, model, torch = g["tok"], g["model"], g["torch"]
    per_q = []
    for q in screen:
        txt = question_text(q)
        if not txt:
            per_q.append(0.0)
            continue
        ids = tok(txt, return_tensors="pt")["input_ids"]
        if ids.shape[1] < 2:
            per_q.append(0.0)
            continue
        with torch.no_grad():
            logits = model(ids).logits
        logprobs = torch.log_softmax(logits, dim=-1)
        # surprisal of token t predicted from tokens < t
        surprisals = []
        for t in range(1, ids.shape[1]):
            lp = logprobs[0, t - 1, ids[0, t]].item()
            surprisals.append(-lp / math.log(2))  # bits
        per_q.append(max(surprisals) if surprisals else 0.0)
    return {"per_question": [round(x, 3) for x in per_q], "screen_max": round(max(per_q), 3) if per_q else 0.0}


# ---- metric 8: screen load -------------------------------------------------
def metric_screen_load(opening_query: str, screen: List[Dict[str, Any]]):
    applicant_ents = {e.lower() for e in _tokens_lower(opening_query)}
    total_content_tokens = 0
    new_entities = set()
    for q in screen:
        doc = nlp()(question_text(q) + "\n" + "\n".join(option_texts(q)))
        total_content_tokens += sum(1 for t in doc if t.pos_ in CONTENT_POS and t.is_alpha)
        for ent in doc.ents:
            key = ent.text.lower()
            if not any(w in applicant_ents for w in _tokens_lower(ent.text)):
                new_entities.add(key)
    return {
        "n_questions": len(screen),
        "total_content_tokens": total_content_tokens,
        "new_entities": len(new_entities),
        "new_entity_list": sorted(new_entities),
    }


# ---- metric 9: negation x conditional --------------------------------------
def metric_negation_x_conditional(screen: List[Dict[str, Any]]):
    per_q = []
    for q in screen:
        toks = _tokens_lower(question_text(q))
        raw = question_text(q).lower()
        has_neg = bool(toks & NEGATIONS) or "n't" in raw
        has_cond = bool(toks & CONDITIONALS)
        per_q.append(1 if (has_neg and has_cond) else 0)
    return {"per_question": per_q, "screen_flag": 1 if any(per_q) else 0}


# ---- descriptive readability ----------------------------------------------
def descriptive_readability(screen: List[Dict[str, Any]]):
    import textstat

    txt = " ".join(question_text(q) for q in screen).strip()
    if not txt:
        return {"fkgl": None, "dale_chall": None}
    return {
        "fkgl": round(textstat.flesch_kincaid_grade(txt), 2),
        "dale_chall": round(textstat.dale_chall_readability_score(txt), 2),
    }


def compute_all(record: Dict[str, Any]) -> Dict[str, Any]:
    screen = record.get("merged_screen") or []
    oq = record.get("opening_query", "")
    out = {
        "scenario_id": record.get("scenario_id"),
        "arm": record.get("arm"),
        "n_questions": len(screen),
        "member_failed": bool(record.get("member_failed")),
        "empty_screen": len(screen) == 0,
    }
    if not screen:
        return out
    out["m4_unintroduced_hard_vocab"] = metric_unintroduced_hard_vocab(oq, screen)
    out["m5_max_dependency_length"] = metric_max_dependency_length(screen)
    out["m6_agentless_passive"] = metric_agentless_passive(screen)
    out["m7_max_surprisal"] = metric_max_surprisal(screen)
    out["m8_screen_load"] = metric_screen_load(oq, screen)
    out["m9_negation_x_conditional"] = metric_negation_x_conditional(screen)
    out["descriptive"] = descriptive_readability(screen)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--in", dest="infile", default=None)
    args = ap.parse_args()
    run_dir = os.path.join(STUDY, "results", "generation", args.run_id)
    infile = args.infile or os.path.join(run_dir, "screens.jsonl")
    out_path = os.path.join(run_dir, "metrics_deterministic.jsonl")
    records = [json.loads(l) for l in open(infile)]
    with open(out_path, "w") as f:
        for i, rec in enumerate(records):
            res = compute_all(rec)
            f.write(json.dumps(res) + "\n")
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(records)}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
