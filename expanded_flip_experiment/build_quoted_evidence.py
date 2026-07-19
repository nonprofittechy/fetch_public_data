#!/usr/bin/env python3
"""Build a reproducible excerpt appendix from completed official runs."""

from __future__ import annotations

import csv
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUN_ANALYSIS = HERE / "analysis/runs"
OUTPUT = HERE / "analysis/QUOTED_EVIDENCE.md"

# Chosen before run 3 was inspected. They represent the requested strata and
# include successes, failures, and cross-run variability rather than cherry-
# picking only positive outcomes.
SCENARIOS = [
    "x0011",       # explicit domestic-violence safety question; variable exact result
    "x0041",       # domestic violence hidden behind custody; variable elicitation
    "legacy_025",  # paper criminal/restraining failure mode
    "x0101",       # expanded stalking/restraining failure mode
    "x0157",       # administrative-hearing signal ignored
    "legacy_162",  # workplace-location fact; variable final classification
    "legacy_002",  # judgment/collection fact; broad category but exact miss
    "x0584",       # multi-label intellectual-property example
]


def quote(row: dict) -> str:
    final = row["final_labels"] or "[no second classification]"
    match = row["matched_question"] or "[none]"
    return (
        f"> Opening query: “{row['opening_query']}”  \n"
        f"> Generated question(s): “{row['follow_up_questions'] or '[none]'}”  \n"
        f"> Hidden fact: “{row['hidden_fact']}”  \n"
        f"> Matcher-selected question: “{match}”  \n"
        f"> Initial labels: “{row['initial_labels'] or '[none]'}”  \n"
        f"> Final labels: “{final}”\n\n"
        f"Expected final `{row['expected_final_label']}`; matched `{row['question_matched']}`; "
        f"expected exact label present `{row['final_subcategory_correct']}`.\n\n"
    )


def main() -> None:
    runs = []
    for path in sorted(RUN_ANALYSIS.glob("final_run_*/scenario_details.csv")):
        rows = {r["scenario_id"]: r for r in csv.DictReader(path.open())}
        runs.append((path.parent.name, rows))
    chunks = [
        "# Quoted result evidence\n\n",
        "This appendix is generated from the completed official-run `scenario_details.csv` files. "
        "The scenario list was frozen before run 3 was inspected. Text inside block quotes is copied "
        "from saved provider outputs and candidate facts; only `[none]` annotations are added.\n\n",
    ]
    for scenario_id in SCENARIOS:
        chunks.append(f"## `{scenario_id}`\n\n")
        for run, rows in runs:
            if scenario_id not in rows:
                continue
            chunks.append(f"### {run}\n\n")
            chunks.append(quote(rows[scenario_id]))
    OUTPUT.write_text("".join(chunks), encoding="utf-8")
    print(f"Wrote {OUTPUT} from {len(runs)} run(s)")


if __name__ == "__main__":
    main()
