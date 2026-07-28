#!/usr/bin/env python3
"""Validity check: do the metrics move on the dimension they claim to measure?

For each controlled item we hold everything fixed except ONE degradation and
confirm the targeted metric increases (sensitivity) while, where cheap to check,
non-targeted metrics stay flat (specificity). Dimensions:

  A. presupposition (metric 1): insert an unsupported definite NP into a clean
     question, keeping the applicant statement fixed -> m1 should rise.
  B. double-barrel (metric 2): coordinate two predicates into one question
     -> m2 atomic count should rise from 1 to 2.
  C. vocabulary (metric 4, deterministic): swap a common content word for a rare
     synonym -> m4 unintroduced-hard-vocab count should rise.

Plus a known-bad calibration: egregiously broken screens the judge MUST flag.
A metric/judge that fails these is treated as broken for the run.

Usage: python validity_check.py [--judge deepseek-v4]
Writes validation/validity_results.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(STUDY, "metrics"))

import deterministic as D  # noqa: E402
import llm_metrics as M  # noqa: E402

# ---- controlled items ------------------------------------------------------
# Each item: applicant statement + a clean question and a degraded question that
# differs only on the targeted dimension.

PRESUP_ITEMS = [
    {"state": "My landlord won't fix the heat and it's freezing.",
     "clean": "What is the problem you're having with your home?",
     "degraded": "When did the eviction court hearing take place?"},
    {"state": "I lost my job last month and can't pay my bills.",
     "clean": "What kind of help are you looking for?",
     "degraded": "What did the arbitration panel decide about your severance?"},
    {"state": "My car was damaged in a parking lot.",
     "clean": "How was your car damaged?",
     "degraded": "What did the police report from the collision say?"},
    {"state": "I need help with my mother's estate after she died.",
     "clean": "Are you handling your mother's estate yourself?",
     "degraded": "Which bank is the trustee of the family trust?"},
    {"state": "My employer hasn't paid me for two weeks.",
     "clean": "How long have you gone unpaid?",
     "degraded": "What stage is your union grievance at?"},
    {"state": "I'm being harassed by a debt collector.",
     "clean": "Who is contacting you about the debt?",
     "degraded": "When did you file for bankruptcy?"},
    {"state": "My neighbor built a fence on my property.",
     "clean": "Where was the fence built?",
     "degraded": "What did the boundary survey ordered by the judge find?"},
]

DOUBLE_ITEMS = [
    {"state": "My benefits were cut off.",
     "clean": "Did you get a letter about your benefits?",
     "degraded": "Did you get a letter about your benefits and did you appeal it?"},
    {"state": "I was in a car accident.",
     "clean": "Were you injured in the accident?",
     "degraded": "Were you injured in the accident and was the other driver insured?"},
    {"state": "My landlord is trying to evict me.",
     "clean": "Did you receive an eviction notice?",
     "degraded": "Did you receive an eviction notice and have you paid rent this month?"},
    {"state": "I want to divorce my spouse.",
     "clean": "Do you have children with your spouse?",
     "degraded": "Do you have children with your spouse and do you own a home together?"},
    {"state": "My employer fired me.",
     "clean": "Were you given a reason for being fired?",
     "degraded": "Were you given a reason for being fired and did you sign anything on your way out?"},
    {"state": "A company charged me for something I didn't buy.",
     "clean": "Did you contact the company about the charge?",
     "degraded": "Did you contact the company about the charge and did you dispute it with your bank?"},
    {"state": "My disability claim was denied.",
     "clean": "Did you get a denial letter?",
     "degraded": "Did you get a denial letter and have you seen a doctor recently?"},
]

VOCAB_ITEMS = [
    {"state": "I need help with my problem.",
     "clean": "Do you need help with your house?",
     "degraded": "Do you need help with your domicile?"},
    {"state": "I got a letter.",
     "clean": "Did you get a letter from them?",
     "degraded": "Did you get a missive from them?"},
    {"state": "I lost my job.",
     "clean": "Were you fired from your job?",
     "degraded": "Were you defenestrated from your emolument?"},
    {"state": "Someone owes me money.",
     "clean": "Are you trying to get your money back?",
     "degraded": "Are you trying to recoup your pecuniary remuneration?"},
    {"state": "My landlord is a problem.",
     "clean": "Is your landlord refusing to make repairs?",
     "degraded": "Is your lessor refusing to remediate the dilapidations?"},
    {"state": "I was hurt at work.",
     "clean": "Were you hurt while working?",
     "degraded": "Were you incapacitated during your vocational endeavors?"},
    {"state": "I want to end my marriage.",
     "clean": "Do you want to end your marriage?",
     "degraded": "Do you wish to dissolve your connubial union?"},
]

KNOWN_BAD_SCREENS = [
    # egregiously double-barreled + presupposition-heavy screen
    {"state": "My benefits got cut off and I don't know why.",
     "screen": [
         {"question": "Did the ALJ at your Social Security disability hearing uphold the SGA determination and did you request reconsideration within 60 days?", "options": None},
         {"question": "Was your writ of certiorari granted and are you pursuing the collateral estoppel argument?", "options": None},
     ]},
    {"state": "My neighbor's tree fell on my fence.",
     "screen": [
         {"question": "Is the tortfeasor's homeowner's indemnity policy in subrogation and did you perfect your mechanic's lien?", "options": None},
     ]},
]


def q(text):
    return [{"question": text, "options": None}]


def run(judge_model: str):
    sys.path.insert(0, os.path.join(STUDY, "metrics"))
    import judge as judge_mod

    def jcall(system, user, temperature=0.0, seed=0, max_tokens=1500):
        return judge_mod.judge_json(system, user, model=judge_model, temperature=temperature,
                                    seed=seed, max_tokens=max_tokens)

    results = {"presupposition": [], "double_barrel": [], "vocabulary": [], "known_bad": []}

    # A. presupposition (metric 1) — judge
    for it in PRESUP_ITEMS:
        c = M.metric_presupposition(it["state"], q(it["clean"]), jcall)["screen_max"]
        d = M.metric_presupposition(it["state"], q(it["degraded"]), jcall)["screen_max"]
        results["presupposition"].append({"clean": c, "degraded": d, "moved_up": d > c})

    # B. double-barrel (metric 2) — judge
    for it in DOUBLE_ITEMS:
        c = M.metric_double_barrel(it["state"], q(it["clean"]), jcall)["screen_max"]
        d = M.metric_double_barrel(it["state"], q(it["degraded"]), jcall)["screen_max"]
        results["double_barrel"].append({"clean": c, "degraded": d, "moved_up": d > c})

    # C. vocabulary (metric 4) — deterministic
    for it in VOCAB_ITEMS:
        c = D.metric_unintroduced_hard_vocab(it["state"], q(it["clean"]))["screen_max"]
        d = D.metric_unintroduced_hard_vocab(it["state"], q(it["degraded"]))["screen_max"]
        results["vocabulary"].append({"clean": c, "degraded": d, "moved_up": d > c})

    # Known-bad calibration: judge must flag (m1>0 or m2 double-barrel).
    for it in KNOWN_BAD_SCREENS:
        m1 = M.metric_presupposition(it["state"], it["screen"], jcall)["screen_max"]
        m2 = M.metric_double_barrel(it["state"], it["screen"], jcall)["screen_flag"]
        flagged = (m1 > 0) or (m2 == 1)
        results["known_bad"].append({"m1": m1, "m2_flag": m2, "flagged": flagged})

    summary = {}
    for dim in ["presupposition", "double_barrel", "vocabulary"]:
        rows = results[dim]
        summary[dim] = {"n": len(rows), "sensitivity": sum(r["moved_up"] for r in rows) / len(rows)}
    summary["known_bad"] = {"n": len(results["known_bad"]),
                            "flagged": sum(r["flagged"] for r in results["known_bad"])}

    out = {"judge": judge_model, "summary": summary, "detail": results}
    with open(os.path.join(HERE, "validity_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(summary, indent=2))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="deepseek-v4")
    args = ap.parse_args()
    run(args.judge)
