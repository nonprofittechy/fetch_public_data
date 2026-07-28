#!/usr/bin/env python3
"""Paired analysis for the nano-vs-full readability study.

Joins the generated screens with the deterministic and LLM-judge metrics, pairs
each scenario's nano and full screens, and runs the pre-registered analysis:

  - Binary flags  -> McNemar (exact)
  - Continuous    -> Wilcoxon signed-rank + rank-biserial effect size
  - Screen-emptiness / hard-flag rates -> paired proportion diff + bootstrap 90% CI
  - Primary metrics (1-3): reported first; exploratory (4-10): Benjamini-Hochberg FDR
  - Equivalence: TOST-style bootstrap 90% CI vs SESOI = 5 percentage points on the
    composite hard-flag rate, so "nano is good enough" is a reportable result.

Direction convention: a POSITIVE (full - nano) difference on a "badness" metric
means full is WORSE. We report per-arm central tendency so direction is explicit.

Usage:
  python analyze.py --run-id main_20260719 --judge deepseek-v4
Writes analysis/<run_id>/results.json and prints a summary table.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))
SESOI_PP = 5.0  # smallest effect worth caring about, percentage points
random.seed(42)


def load_jsonl(path: str) -> List[dict]:
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def index_by(rows: List[dict]) -> Dict[Tuple[str, str], dict]:
    return {(r.get("scenario_id"), r.get("arm")): r for r in rows}


# ---- metric extractors: return a per-screen scalar (or None) ----------------
def det_get(rec: dict, path: List[str]) -> Optional[float]:
    cur = rec
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


METRICS = [
    # (key, tier, kind, extractor, higher_is_worse)
    ("m1_unverified_presup", "primary", "count",
     lambda d, l: det_get(l, ["m1_presupposition", "screen_max"]), True),
    ("m2_double_barrel_flag", "primary", "binary",
     lambda d, l: det_get(l, ["m2_double_barrel", "screen_flag"]), True),
    ("m3_unclear_rate", "primary", "cont",
     lambda d, l: det_get(l, ["m3_simulated_respondent", "unclear_rate_mean"]), True),
    ("m3_answerable_rate", "primary", "cont",
     lambda d, l: det_get(l, ["m3_simulated_respondent", "answerable_rate_mean"]), False),
    ("m4_hard_vocab", "exploratory", "count",
     lambda d, l: det_get(d, ["m4_unintroduced_hard_vocab", "screen_max"]), True),
    ("m5_dependency_len", "exploratory", "cont",
     lambda d, l: det_get(d, ["m5_max_dependency_length", "screen_max"]), True),
    ("m6_passive", "exploratory", "count",
     lambda d, l: det_get(d, ["m6_agentless_passive", "screen_max"]), True),
    ("m7_surprisal", "exploratory", "cont",
     lambda d, l: det_get(d, ["m7_max_surprisal", "screen_max"]), True),
    ("m8_screen_tokens", "exploratory", "cont",
     lambda d, l: det_get(d, ["m8_screen_load", "total_content_tokens"]), True),
    ("m8_new_entities", "exploratory", "count",
     lambda d, l: det_get(d, ["m8_screen_load", "new_entities"]), True),
    ("m9_neg_x_cond_flag", "exploratory", "binary",
     lambda d, l: det_get(d, ["m9_negation_x_conditional", "screen_flag"]), True),
]


def wilcoxon_rank_biserial(nano: List[float], full: List[float]):
    diffs = [f - n for n, f in zip(nano, full)]
    nz = [d for d in diffs if d != 0]
    if not nz:
        return {"n_pairs": len(diffs), "n_nonzero": 0, "p": 1.0, "rank_biserial": 0.0,
                "nano_median": _median(nano), "full_median": _median(full),
                "nano_mean": _mean(nano), "full_mean": _mean(full)}
    try:
        w = stats.wilcoxon(nano, full, zero_method="wilcox", alternative="two-sided")
        pval = float(w.pvalue)
    except Exception:
        pval = 1.0
    pos = sum(1 for d in nz if d > 0)
    neg = sum(1 for d in nz if d < 0)
    rb = (pos - neg) / len(nz)
    return {"n_pairs": len(diffs), "n_nonzero": len(nz), "p": pval, "rank_biserial": round(rb, 3),
            "nano_median": _median(nano), "full_median": _median(full),
            "nano_mean": round(_mean(nano), 3), "full_mean": round(_mean(full), 3),
            "full_worse_pairs": pos, "nano_worse_pairs": neg}


def mcnemar(nano: List[int], full: List[int]):
    # discordant pairs: b = nano0/full1 (full worse), c = nano1/full0 (nano worse)
    b = sum(1 for n, f in zip(nano, full) if n == 0 and f == 1)
    c = sum(1 for n, f in zip(nano, full) if n == 1 and f == 0)
    n = b + c
    if n == 0:
        p = 1.0
    else:
        p = float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5)))
    return {"n_pairs": len(nano), "full_worse_only": b, "nano_worse_only": c,
            "nano_rate": round(_mean(nano), 3), "full_rate": round(_mean(full), 3), "p": p}


def _mean(x):
    return sum(x) / len(x) if x else 0.0


def _median(x):
    return float(stats.scoreatpercentile(x, 50)) if x else 0.0


def bootstrap_paired_diff_ci(nano: List[float], full: List[float], iters=5000, ci=90):
    diffs = [f - n for n, f in zip(nano, full)]
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    boots = []
    for _ in range(iters):
        s = sum(diffs[random.randrange(n)] for _ in range(n)) / n
        boots.append(s)
    boots.sort()
    lo = boots[int((100 - ci) / 2 / 100 * iters)]
    hi = boots[int((100 + ci) / 2 / 100 * iters)]
    return (_mean(diffs), lo, hi)


def bh_fdr(pvals: List[float], q=0.05) -> List[bool]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    passed = [False] * m
    thresh = 0
    for rank, i in enumerate(order, 1):
        if pvals[i] <= rank / m * q:
            thresh = rank
    for rank, i in enumerate(order, 1):
        if rank <= thresh:
            passed[i] = True
    return passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--judge", default="deepseek-v4")
    args = ap.parse_args()

    run_dir = os.path.join(STUDY, "results", "generation", args.run_id)
    screens = index_by(load_jsonl(os.path.join(run_dir, "screens.jsonl")))
    det = index_by(load_jsonl(os.path.join(run_dir, "metrics_deterministic.jsonl")))
    judge_tag = args.judge.replace("/", "_")
    llm = index_by(load_jsonl(os.path.join(run_dir, f"metrics_llm_{judge_tag}.jsonl")))

    scen_ids = sorted({sid for (sid, _arm) in screens})

    # --- screen-emptiness (a structural outcome, all scenarios) --------------
    empty_pairs = []
    for sid in scen_ids:
        sn, sf = screens.get((sid, "nano")), screens.get((sid, "full"))
        if not sn or not sf or sn.get("member_failed") or sf.get("member_failed"):
            continue
        empty_pairs.append((1 if not sn.get("merged_screen") else 0,
                            1 if not sf.get("merged_screen") else 0))
    emptiness = mcnemar([n for n, _ in empty_pairs], [f for _, f in empty_pairs]) if empty_pairs else {}

    # --- paired metric arrays over clean, both-nonempty pairs ----------------
    results = {}
    pval_expl, key_expl = [], []
    for key, tier, kind, extract, hiw in METRICS:
        nano_vals, full_vals = [], []
        for sid in scen_ids:
            sn, sf = screens.get((sid, "nano")), screens.get((sid, "full"))
            dn, df = det.get((sid, "nano")), det.get((sid, "full"))
            ln, lf = llm.get((sid, "nano")), llm.get((sid, "full"))
            if not sn or not sf or sn.get("member_failed") or sf.get("member_failed"):
                continue
            if not sn.get("merged_screen") or not sf.get("merged_screen"):
                continue
            needs_llm = key.startswith(("m1", "m2", "m3"))
            if needs_llm and (not ln or not lf or ln.get("status") != "ok" or lf.get("status") != "ok"):
                continue
            vn = extract(dn or {}, ln or {})
            vf = extract(df or {}, lf or {})
            if vn is None or vf is None:
                continue
            nano_vals.append(float(vn))
            full_vals.append(float(vf))
        if not nano_vals:
            results[key] = {"tier": tier, "kind": kind, "n_pairs": 0}
            continue
        if kind == "binary":
            r = mcnemar([int(x) for x in nano_vals], [int(x) for x in full_vals])
        else:
            r = wilcoxon_rank_biserial(nano_vals, full_vals)
        mean, lo, hi = bootstrap_paired_diff_ci(nano_vals, full_vals)
        r.update({"tier": tier, "kind": kind, "higher_is_worse": hiw,
                  "paired_diff_full_minus_nano": round(mean, 4),
                  "diff_ci90": [round(lo, 4), round(hi, 4)]})
        results[key] = r
        if tier == "exploratory":
            pval_expl.append(r["p"])
            key_expl.append(key)

    # FDR on exploratory
    if pval_expl:
        passed = bh_fdr(pval_expl, q=0.05)
        for k, ok in zip(key_expl, passed):
            results[k]["bh_fdr_pass_q05"] = bool(ok)

    # --- composite hard-flag rate + equivalence (TOST-style bootstrap) -------
    hard_nano, hard_full = [], []
    for sid in scen_ids:
        sn, sf = screens.get((sid, "nano")), screens.get((sid, "full"))
        ln, lf = llm.get((sid, "nano")), llm.get((sid, "full"))
        if not sn or not sf or sn.get("member_failed") or sf.get("member_failed"):
            continue
        if not sn.get("merged_screen") or not sf.get("merged_screen"):
            continue
        if not ln or not lf or ln.get("status") != "ok" or lf.get("status") != "ok":
            continue

        def hard(l):
            m1 = det_get(l, ["m1_presupposition", "screen_max"]) or 0
            m2 = det_get(l, ["m2_double_barrel", "screen_flag"]) or 0
            return 1 if (m1 > 0 or m2 == 1) else 0
        hard_nano.append(hard(ln))
        hard_full.append(hard(lf))
    equiv = {}
    if hard_nano:
        mean, lo, hi = bootstrap_paired_diff_ci([x * 100 for x in hard_nano],
                                                [x * 100 for x in hard_full])
        mc = mcnemar(hard_nano, hard_full)
        within = (lo > -SESOI_PP) and (hi < SESOI_PP)
        equiv = {"n_pairs": len(hard_nano), "nano_hardflag_rate": round(_mean(hard_nano), 3),
                 "full_hardflag_rate": round(_mean(hard_full), 3),
                 "diff_pp_full_minus_nano": round(mean, 2), "diff_pp_ci90": [round(lo, 2), round(hi, 2)],
                 "sesoi_pp": SESOI_PP, "equivalent_within_sesoi": bool(within),
                 "mcnemar_p": mc["p"], "full_worse_only": mc["full_worse_only"],
                 "nano_worse_only": mc["nano_worse_only"]}

    out = {"run_id": args.run_id, "judge": args.judge,
           "n_scenarios": len(scen_ids),
           "screen_emptiness": emptiness, "metrics": results, "hard_flag_equivalence": equiv}
    out_dir = os.path.join(HERE, args.run_id)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"results_{judge_tag}.json"), "w") as f:
        json.dump(out, f, indent=2)

    # --- print summary -------------------------------------------------------
    print(f"\n=== nano vs full readability study | run={args.run_id} | judge={args.judge} ===")
    print(f"scenarios={len(scen_ids)}")
    if emptiness:
        print(f"\nSCREEN EMPTINESS (rate of 0-question screens):")
        print(f"  nano={emptiness['nano_rate']}  full={emptiness['full_rate']}  "
              f"McNemar p={emptiness['p']:.4g}  (nano-empty-only={emptiness['nano_worse_only']}, "
              f"full-empty-only={emptiness['full_worse_only']})")
    for tier in ["primary", "exploratory"]:
        print(f"\n{tier.upper()} METRICS:")
        for key, t, kind, _e, hiw in METRICS:
            if t != tier:
                continue
            r = results.get(key, {})
            if r.get("n_pairs", 0) == 0:
                print(f"  {key:26s} n=0 (no data yet)")
                continue
            if kind == "binary":
                extra = f"nano_rate={r['nano_rate']} full_rate={r['full_rate']} p={r['p']:.4g}"
            else:
                extra = (f"nano_med={r['nano_median']} full_med={r['full_median']} "
                         f"p={r['p']:.4g} rb={r.get('rank_biserial')}")
            fdr = "" if t == "primary" else f" fdr_pass={r.get('bh_fdr_pass_q05')}"
            print(f"  {key:26s} n={r['n_pairs']:3d} {extra}{fdr}")
    if equiv:
        print(f"\nCOMPOSITE HARD-FLAG (m1>0 or m2 double-barrel):")
        print(f"  nano={equiv['nano_hardflag_rate']} full={equiv['full_hardflag_rate']} "
              f"diff(full-nano)={equiv['diff_pp_full_minus_nano']}pp "
              f"CI90={equiv['diff_pp_ci90']} McNemar p={equiv['mcnemar_p']:.4g}")
        print(f"  equivalence within +/-{SESOI_PP}pp SESOI: {equiv['equivalent_within_sesoi']}")


if __name__ == "__main__":
    main()
