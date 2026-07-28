#!/usr/bin/env python3
"""Run the LLM-graded metrics over generated screens with a chosen judge.

Primary metrics:
  1 presupposition        (temp 0, 1 seed -- near-deterministic)
  2 double_barrel         (temp 0, 1 seed)
  3 simulated_respondent  (temp 0.7, N seeds -- stochastic, default 3)
Exploratory:
  10 ambiguity            (temp 1.0, 1 pass; --with-m10 to enable; slow, local NLI)

Only clean screens are scored: non-empty AND not member_failed (the arm-defining
OpenAI member contributed). Empty / degraded screens are recorded with a status so
the analysis can account for them separately.

Resumable: re-invoking skips (scenario_id, arm) rows already in the output file.

Output: results/generation/<run_id>/metrics_llm_<judge>.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import judge as judge_mod  # noqa: E402
import llm_metrics as M  # noqa: E402


def make_jcall(model: str):
    def jcall(system, user, temperature=0.0, seed=0, max_tokens=1500):
        return judge_mod.judge_json(
            system, user, model=model, temperature=temperature, seed=seed, max_tokens=max_tokens
        )
    return jcall


def score_screen(rec: dict, jcall, seeds_m3, with_m10: bool) -> dict:
    sid, arm = rec.get("scenario_id"), rec.get("arm")
    screen = rec.get("merged_screen") or []
    oq = rec.get("opening_query", "")
    out = {
        "scenario_id": sid,
        "arm": arm,
        "n_questions": len(screen),
        "member_failed": bool(rec.get("member_failed")),
        "empty_screen": len(screen) == 0,
        "status": "ok",
    }
    if not screen or rec.get("member_failed"):
        out["status"] = "skipped_degraded"
        return out
    try:
        out["m1_presupposition"] = M.metric_presupposition(oq, screen, jcall, temperature=0.0, seed=0)
        out["m2_double_barrel"] = M.metric_double_barrel(oq, screen, jcall, temperature=0.0, seed=0)
        m3_runs = []
        for sd in seeds_m3:
            m3_runs.append(M.metric_simulated_respondent(oq, screen, jcall, temperature=0.7, seed=sd))
        n = len(screen)
        out["m3_simulated_respondent"] = {
            "seeds": seeds_m3,
            "runs": m3_runs,
            "unclear_rate_mean": round(sum(r["unclear_rate"] for r in m3_runs) / len(m3_runs), 4),
            "answerable_rate_mean": round(sum(r["answerable_rate"] for r in m3_runs) / len(m3_runs), 4),
            "unclear_count_mean": round(sum(r["unclear"] for r in m3_runs) / len(m3_runs), 4),
        }
        if with_m10:
            out["m10_ambiguity"] = M.metric_ambiguity(oq, screen, jcall, temperature=1.0, seed=0)
    except Exception as e:  # noqa: BLE001
        out["status"] = "error"
        out["error"] = str(e)[:300]
    return out


def load_done(path):
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                o = json.loads(line)
                done.add((o["scenario_id"], o["arm"]))
            except Exception:
                pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--judge-model", default="deepseek-v4")
    ap.add_argument("--seeds-m3", default="1,2,3")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--with-m10", action="store_true")
    args = ap.parse_args()

    run_dir = os.path.join(STUDY, "results", "generation", args.run_id)
    screens_path = os.path.join(run_dir, "screens.jsonl")
    judge_tag = args.judge_model.replace("/", "_")
    out_path = os.path.join(run_dir, f"metrics_llm_{judge_tag}.jsonl")

    seeds_m3 = [int(s) for s in args.seeds_m3.split(",") if s.strip()]
    jcall = make_jcall(args.judge_model)

    records = [json.loads(l) for l in open(screens_path)]
    if args.limit:
        records = records[: args.limit]
    done = load_done(out_path)
    todo = [r for r in records if (r.get("scenario_id"), r.get("arm")) not in done]
    print(f"[llm-metrics judge={args.judge_model}] {len(records)} screens; {len(done)} done; "
          f"{len(todo)} to score; seeds_m3={seeds_m3}; concurrency={args.concurrency}")

    lock = threading.Lock()
    written = [0]

    def work(rec):
        res = score_screen(rec, jcall, seeds_m3, args.with_m10)
        with lock:
            with open(out_path, "a") as f:
                f.write(json.dumps(res) + "\n")
            written[0] += 1
            if written[0] % 20 == 0:
                print(f"  {written[0]}/{len(todo)}")
        return res

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(work, r) for r in todo]
        for _ in as_completed(futs):
            pass
    print(f"[llm-metrics] wrote {out_path}")


if __name__ == "__main__":
    main()
