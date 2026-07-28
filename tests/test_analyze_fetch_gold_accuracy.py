from analyze_fetch_gold_accuracy import (
    accepted_labels,
    canonical_label,
    score_record,
)


def gold(*labels):
    row = {"problem_description": "A scenario", "scenario_id": "gold-1", "source_row": "2"}
    for index, label in enumerate(labels, 1):
        category, subcategory = label.split(" > ", 1)
        row[f"gold_category_{index}"] = category
        row[f"gold_subcategory_{index}"] = subcategory
    return row


def record(*labels):
    import json

    raw = json.dumps({"labels": [{"label": label} for label in labels]})
    return {"response": {"metadata": {"raw_json": raw}}, "success": True, "latencyMs": 1}


def test_spelling_alias_is_exact_compatible():
    assert canonical_label("Debtor/Creditor > Judgement Collection") == canonical_label(
        "Debtor/Creditor > Judgment Collection"
    )


def test_legacy_employment_parent_accepts_current_child():
    accepted = accepted_labels("Labor & Employment > Discrimination")
    assert canonical_label("Labor & Employment > Discrimination - Employee") in accepted


def test_partial_exact_is_distinct_from_category_only():
    row = score_record(
        "run1",
        record("Family Law > Adoption", "Criminal Law > Misdemeanor"),
        gold("Family Law > Adoption", "Criminal Law > Major Felony"),
    )
    assert row["outcome_tier"] == "some_exact_sublabels"
    assert row["exact_hits"] == 1
    assert row["category_only_gold_labels"] == 1
    assert row["graded_retrieval_score"] == 0.75


def test_top_level_only_gets_half_credit():
    row = score_record(
        "run1",
        record("Family Law > Adoption"),
        gold("Family Law > Child Custody/Visitation"),
    )
    assert row["outcome_tier"] == "top_level_only"
    assert row["graded_retrieval_score"] == 0.5
