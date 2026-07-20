#!/usr/bin/env python3
"""Encode the Claude (in-context) judgments of the 60 blind screens.

This is a rapid expert pass by Claude (the agent), blind to arm, applying the
same rubrics as the DeepSeek judge:
  m1_screen_max   : max unverified presuppositions in any one question
  m2_screen_flag  : 1 if any question stem is genuinely double-barreled
  m3_*            : per-question answerable / unclear / not-applicable counts

Defaults are "clean" (m1=0, m2=0, all questions answerable); documented
exceptions below record the specific defects found on reading each screen
against its applicant statement. n_questions is filled from the blind file.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# blind_id -> overrides. Absent keys default to clean.
JUDGMENTS = {
    "S0051": {"m1_screen_max": 1, "note": "Q2/Q3 presuppose 'student loans' never mentioned by applicant"},
    "S0045": {"m2_screen_flag": 1, "note": "Q1 stem bundles 'is there a will/trust' AND 'are you named beneficiary'"},
    "S0028": {"m2_screen_flag": 1, "note": "Q1 'did you get a 1099-C? if yes, what tax year' = two asks"},
    "S0006": {"m2_screen_flag": 1, "note": "Q1 bundles 'is your main problem X' and 'do you want a protective order'"},
    "S0004": {"m3_unclear": 1, "note": "Q2 introduces needs-based/disability trust, a non-sequitur for this writer"},
    "S0035": {"m3_unclear": 0, "note": "Q1 and Q2 are near-duplicate restraining-order asks (redundant, not unclear)"},
}


def main():
    blind = [json.loads(l) for l in open(os.path.join(HERE, "screens_blind.jsonl"))]
    out = []
    for b in blind:
        bid = b["blind_id"]
        n = len(b["screen"])
        j = {"blind_id": bid, "n_questions": n,
             "m1_screen_max": 0, "m2_screen_flag": 0,
             "m3_unclear": 0, "m3_answerable": n, "m3_not_applicable": 0}
        ov = JUDGMENTS.get(bid, {})
        for k, v in ov.items():
            if k == "note":
                j["note"] = v
            else:
                j[k] = v
        # keep answerable consistent if unclear/na set
        j["m3_answerable"] = max(0, n - j["m3_unclear"] - j["m3_not_applicable"])
        j["m3_unclear_rate"] = round(j["m3_unclear"] / n, 4) if n else 0.0
        j["m3_answerable_rate"] = round(j["m3_answerable"] / n, 4) if n else 0.0
        out.append(j)
    with open(os.path.join(HERE, "claude_judgments.jsonl"), "w") as f:
        for j in out:
            f.write(json.dumps(j) + "\n")
    print(f"wrote {len(out)} Claude judgments")


if __name__ == "__main__":
    main()
