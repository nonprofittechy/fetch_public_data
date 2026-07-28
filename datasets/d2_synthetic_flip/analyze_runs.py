#!/usr/bin/env python3
"""Analyze v2 disclosure-flip runs.

Key design point: every metric is computed by joining raw run results to the
CURRENT candidate file by ``scenario_id``. If the human salience audit removes
rows from ``candidates/flip_candidates_v2.csv`` (or a copy passed with
``--candidates``), re-running this script regenerates every headline number
from the surviving rows only — no re-run of the model pipeline is needed.

Scoring is order-independent set membership, following the v1 study's metric
definitions: expected-category presence, expected-exact-label presence, and
whether the expected final label was NEWLY ADDED after the hidden-fact answer
(absent from the initial set, present in the final set). Expected labels use
FETCH's runtime taxonomy spellings, so exact comparison needs no alias table.

Usage:
    python analyze_runs.py                      # all final_* runs in results/
    python analyze_runs.py --runs results/final_run_1_*  --candidates my.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = HERE / "analysis/runs_v2"
DEFAULT_CANDIDATES = HERE / "candidates/flip_candidates_v2.csv"

DETAIL_FIELDS = [
    "run", "scenario_id", "boundary_id", "direction", "flip_type", "mechanism",
    "safety_sensitive", "opening_query", "hidden_fact",
    "expected_initial_label", "expected_final_label",
    "initial_labels", "initial_category_present", "initial_exact_present",
    "plausible_initial_present",
    "follow_up_question_count", "follow_up_questions", "question_matched",
    "matched_question", "final_labels", "final_category_present",
    "final_exact_present", "expected_final_category_present_initially",
    "expected_final_exact_present_initially", "expected_final_category_added",
    "expected_final_exact_added", "expected_final_exact_lost",
    "provider_error", "latency_ms",
]


def norm(label: str) -> str:
    return " ".join((label or "").strip().lower().split())


def category_of(label: str) -> str:
    return norm(label).split(" > ", 1)[0]


def label_set(labels) -> list[str]:
    return [lbl.get("label", "") for lbl in (labels or [])]


def cat_present(labels: list[str], expected: str) -> bool:
    want = category_of(expected)
    return any(category_of(l) == want for l in labels)


def exact_present(labels: list[str], expected: str) -> bool:
    want = norm(expected)
    return any(norm(l) == want for l in labels)


def pct(n: int, d: int):
    return round(100 * n / d, 2) if d else None


def parse_run(run_dir: Path, candidates: dict[str, dict]) -> list[dict]:
    doc = json.loads((run_dir / "results.json").read_text())
    rows = []
    for item in doc.get("results", []):
        variables = item.get("vars") or {}
        sid = variables.get("scenario_id", "")
        cand = candidates.get(sid)
        if cand is None:
            continue  # removed by the human audit — excluded from all metrics
        raw = (item.get("response") or {}).get("output")
        try:
            result = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            result = {}
        initial = label_set(result.get("initial_labels"))
        final = label_set(result.get("final_labels")) if result.get("final_labels") else []
        expected_initial = f"{cand['initial_category']} > {cand['initial_subcategory']}"
        expected_final = f"{cand['final_category']} > {cand['final_subcategory']}"
        plausible = [p.strip() for p in (cand.get("plausible_initial_labels") or expected_initial).split("||")]
        matched = bool(result.get("question_matched"))
        final_cat = cat_present(final, expected_final) if matched and final else None
        final_exact = exact_present(final, expected_final) if matched and final else None
        init_has_final_cat = cat_present(initial, expected_final)
        init_has_final_exact = exact_present(initial, expected_final)
        rows.append({
            "run": run_dir.name,
            "scenario_id": sid,
            "boundary_id": cand["boundary_id"],
            "direction": cand["direction"],
            "flip_type": cand["flip_type"],
            "mechanism": cand["mechanism"],
            "safety_sensitive": cand["safety_sensitive"],
            "opening_query": cand["opening_query"],
            "hidden_fact": cand["hidden_fact"],
            "expected_initial_label": expected_initial,
            "expected_final_label": expected_final,
            "initial_labels": " || ".join(initial),
            "initial_category_present": cat_present(initial, expected_initial),
            "initial_exact_present": exact_present(initial, expected_initial),
            "plausible_initial_present": any(exact_present(initial, p) for p in plausible),
            "follow_up_question_count": len(result.get("follow_up_questions") or []),
            "follow_up_questions": " || ".join(
                q.get("question", "") for q in (result.get("follow_up_questions") or [])),
            "question_matched": matched,
            "matched_question": result.get("matched_question") or "",
            "final_labels": " || ".join(final),
            "final_category_present": final_cat,
            "final_exact_present": final_exact,
            "expected_final_category_present_initially": init_has_final_cat,
            "expected_final_exact_present_initially": init_has_final_exact,
            "expected_final_category_added": (matched and final_cat and not init_has_final_cat) or False,
            "expected_final_exact_added": (matched and final_exact and not init_has_final_exact) or False,
            "expected_final_exact_lost": (matched and bool(final) and init_has_final_exact and not final_exact) or False,
            "provider_error": result.get("error") or item.get("orchestrator_error") or "",
            "latency_ms": item.get("latencyMs"),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    matched = [r for r in rows if r["question_matched"]]
    scored = [r for r in matched if r["final_labels"]]
    return {
        "observations": n,
        "scenarios": len({r["scenario_id"] for r in rows}),
        "initial_expected_category_present_pct": pct(sum(r["initial_category_present"] for r in rows), n),
        "initial_expected_exact_present_pct": pct(sum(r["initial_exact_present"] for r in rows), n),
        "initial_any_plausible_exact_present_pct": pct(sum(r["plausible_initial_present"] for r in rows), n),
        "question_match_coverage_pct": pct(len(matched), n),
        "final_expected_category_present_among_matched_pct": pct(
            sum(bool(r["final_category_present"]) for r in scored), len(scored)),
        "final_expected_exact_present_among_matched_pct": pct(
            sum(bool(r["final_exact_present"]) for r in scored), len(scored)),
        "expected_final_category_present_initially_pct": pct(
            sum(r["expected_final_category_present_initially"] for r in rows), n),
        "expected_final_exact_present_initially_pct": pct(
            sum(r["expected_final_exact_present_initially"] for r in rows), n),
        "expected_final_category_newly_added_pct_of_matched": pct(
            sum(r["expected_final_category_added"] for r in scored), len(scored)),
        "expected_final_exact_newly_added_pct_of_matched": pct(
            sum(r["expected_final_exact_added"] for r in scored), len(scored)),
        "expected_final_exact_added_count": sum(r["expected_final_exact_added"] for r in scored),
        "expected_final_exact_lost_count": sum(r["expected_final_exact_lost"] for r in scored),
        "provider_error_count": sum(bool(r["provider_error"]) for r in rows),
    }


def group_summaries(rows: list[dict], field: str) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[row[field]].append(row)
    out = []
    for key in sorted(groups):
        entry = {"group": key}
        entry.update(summarize(groups[key]))
        out.append(entry)
    return out


def write_csv(path: Path, rows: list[dict], fields=None) -> None:
    if not rows:
        return
    fields = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def matcher_stats(run_dir: Path) -> dict:
    path = run_dir / "matcher_log.jsonl"
    if not path.exists():
        return {}
    entries = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    total = len(entries)
    errors = sum(1 for e in entries if e.get("error"))
    matched = sum(1 for e in entries if e.get("matched"))
    tokens = [e["usage"]["completion_tokens"] for e in entries
              if e.get("usage") and e["usage"].get("completion_tokens") is not None]
    return {
        "matcher_calls": total,
        "matcher_errors": errors,
        "matcher_matched": matched,
        "matcher_match_rate_pct": pct(matched, total),
        "matcher_mean_completion_tokens": round(sum(tokens) / len(tokens), 1) if tokens else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))
    parser.add_argument("--runs", nargs="*",
                        help="run directories; default: results/final_run_*")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    with open(args.candidates, newline="", encoding="utf-8") as handle:
        candidates = {row["scenario_id"]: row for row in csv.DictReader(handle)}
    print(f"candidate file: {args.candidates} ({len(candidates)} active rows)")

    run_dirs = ([Path(p) for p in args.runs] if args.runs
                else sorted(RESULTS.glob("final_run_*")))
    if not run_dirs:
        raise SystemExit("No run directories found (expected results/final_run_*)")

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    per_run_summaries = {}
    for run_dir in run_dirs:
        rows = parse_run(run_dir, candidates)
        all_rows.extend(rows)
        run_out = out_root / run_dir.name
        run_out.mkdir(exist_ok=True)
        write_csv(run_out / "per_case_detail.csv", rows, DETAIL_FIELDS)
        summary = summarize(rows)
        summary.update(matcher_stats(run_dir))
        per_run_summaries[run_dir.name] = summary
        for field in ("boundary_id", "mechanism", "flip_type", "direction", "safety_sensitive"):
            write_csv(run_out / f"by_{field}.csv", group_summaries(rows, field))

    pooled = summarize(all_rows)
    stability = {}
    by_scenario = defaultdict(list)
    for row in all_rows:
        by_scenario[row["scenario_id"]].append(row)
    n_runs = len(run_dirs)
    if n_runs > 1:
        stability = {
            "runs": n_runs,
            "scenarios_matched_in_all_runs": sum(
                1 for rows in by_scenario.values()
                if len(rows) == n_runs and all(r["question_matched"] for r in rows)),
            "scenarios_matched_in_no_run": sum(
                1 for rows in by_scenario.values() if not any(r["question_matched"] for r in rows)),
            "scenarios_final_exact_present_in_all_runs": sum(
                1 for rows in by_scenario.values()
                if len(rows) == n_runs and all(r["final_exact_present"] for r in rows)),
            "scenarios_final_exact_present_in_no_run": sum(
                1 for rows in by_scenario.values() if not any(r["final_exact_present"] for r in rows)),
            "scenarios_with_divergent_question_sets": sum(
                1 for rows in by_scenario.values()
                if len({r["follow_up_questions"] for r in rows}) > 1),
        }

    report = {
        "candidates_file": str(args.candidates),
        "active_candidates": len(candidates),
        "runs": {name: s for name, s in per_run_summaries.items()},
        "pooled": pooled,
        "stability": stability,
    }
    (out_root / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    for field in ("boundary_id", "mechanism", "flip_type", "direction", "safety_sensitive"):
        write_csv(out_root / f"pooled_by_{field}.csv", group_summaries(all_rows, field))
    write_csv(out_root / "pooled_per_case_detail.csv", all_rows, DETAIL_FIELDS)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
