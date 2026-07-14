"""Persistent multi-reviewer interface for adjudicating silver labels."""

from __future__ import annotations

import csv
import hmac
import io
import json
import os
import secrets
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterable

from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix


HERE = Path(__file__).resolve().parent
CASES_PATH = Path(os.environ.get("REVIEW_CASES_PATH", HERE.parent / "silver_labels/10_four_label_human_review/review_cases.json"))
TAXONOMY_PATH = Path(os.environ.get("REVIEW_TAXONOMY_PATH", HERE.parent / "silver_labels/10_four_label_human_review/taxonomy.json"))
DB_PATH = Path(os.environ.get("REVIEW_DB_PATH", HERE / "data/reviews.sqlite3"))
COMPLETED_STATUSES = {"accepted", "corrected"}
ALLOWED_STATUSES = COMPLETED_STATUSES | {"needs_review", "needs_more_info", "skipped"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


CASES: list[dict[str, Any]] = load_json(CASES_PATH)
CASE_BY_ROW = {int(case["row_number"]): case for case in CASES}
TAXONOMY: list[dict[str, str]] = load_json(TAXONOMY_PATH)
TAXONOMY_BY_LABEL = {f"{item['category']} / {item['subcategory']}": item for item in TAXONOMY}
TAXONOMY_ORDER = {
    (item["category"], item["subcategory"]): index for index, item in enumerate(TAXONOMY)
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # type: ignore[method-assign]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_reviewer(value: str) -> str:
    return " ".join(value.split()).casefold()


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def table_columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in db.execute(f"PRAGMA table_info({table})").fetchall()}


def create_reviews_table(db: sqlite3.Connection) -> None:
    db.execute(
        """CREATE TABLE IF NOT EXISTS reviews (
            row_number INTEGER NOT NULL,
            reviewer_key TEXT NOT NULL,
            labels_json TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            reviewer TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (row_number, reviewer_key)
        )"""
    )


def init_db() -> None:
    """Initialize schema and migrate the original one-review-per-row table."""
    with connect_db() as db:
        db.execute("PRAGMA journal_mode = WAL")
        review_columns = table_columns(db, "reviews")
        if review_columns and "reviewer_key" not in review_columns:
            db.execute("ALTER TABLE reviews RENAME TO reviews_legacy")
            create_reviews_table(db)
            for row in db.execute("SELECT * FROM reviews_legacy").fetchall():
                reviewer = str(row["reviewer"] or "Legacy reviewer").strip() or "Legacy reviewer"
                db.execute(
                    "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        row["row_number"], normalize_reviewer(reviewer), row["labels_json"],
                        row["status"], row["notes"], reviewer, row["updated_at"],
                    ),
                )
            db.execute("DROP TABLE reviews_legacy")
        else:
            create_reviews_table(db)

        db.execute(
            """CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                row_number INTEGER NOT NULL,
                reviewer_key TEXT NOT NULL DEFAULT 'legacy reviewer',
                labels_json TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                reviewer TEXT NOT NULL DEFAULT '',
                saved_at TEXT NOT NULL
            )"""
        )
        history_columns = table_columns(db, "review_history")
        if "reviewer_key" not in history_columns:
            db.execute("ALTER TABLE review_history ADD COLUMN reviewer_key TEXT NOT NULL DEFAULT 'legacy reviewer'")
            for row in db.execute("SELECT id, reviewer FROM review_history").fetchall():
                reviewer = str(row["reviewer"] or "Legacy reviewer")
                db.execute(
                    "UPDATE review_history SET reviewer_key=? WHERE id=?",
                    (normalize_reviewer(reviewer), row["id"]),
                )
        db.execute(
            "CREATE INDEX IF NOT EXISTS review_history_row_reviewer ON review_history(row_number, reviewer_key, saved_at)"
        )


init_db()


def csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return str(session["csrf_token"])


app.jinja_env.globals["csrf_token"] = csrf_token


def require_csrf() -> None:
    supplied = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not supplied or not expected or not hmac.compare_digest(str(supplied), str(expected)):
        abort(400, "Invalid CSRF token")


def auth_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if os.environ.get("REVIEW_PASSWORD") and not session.get("authenticated"):
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def decode_review(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["labels"] = json.loads(result.pop("labels_json"))
    return result


def get_reviews() -> list[dict[str, Any]]:
    with connect_db() as db:
        rows = db.execute("SELECT * FROM reviews ORDER BY row_number, reviewer_key").fetchall()
    return [decode_review(row) for row in rows]


def reviews_grouped_by_row(reviews: Iterable[dict[str, Any]] | None = None) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for review_item in reviews if reviews is not None else get_reviews():
        grouped[int(review_item["row_number"])].append(review_item)
    return dict(grouped)


def current_reviewer_key() -> str:
    return normalize_reviewer(str(session.get("reviewer", "")))


def case_order() -> list[int]:
    return [int(case["row_number"]) for case in CASES]


def adjacent_rows(row_number: int) -> tuple[int | None, int | None]:
    order = case_order()
    index = order.index(row_number)
    return (order[index - 1] if index else None, order[index + 1] if index + 1 < len(order) else None)


def label_set(labels: Iterable[dict[str, str]]) -> frozenset[tuple[str, str]]:
    return frozenset((label["category"], label["subcategory"]) for label in labels)


def suggested_label_set(case: dict[str, Any]) -> frozenset[tuple[str, str]]:
    return label_set(case["suggested_labels"])


@app.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if not os.environ.get("REVIEW_PASSWORD"):
        return redirect(url_for("index"))
    if request.method == "POST":
        require_csrf()
        if hmac.compare_digest(request.form.get("password", ""), os.environ["REVIEW_PASSWORD"]):
            session["authenticated"] = True
            destination = request.form.get("next", "")
            if not destination.startswith("/") or destination.startswith("//"):
                destination = url_for("index")
            return redirect(destination)
        flash("Incorrect review password.", "error")
    return render_template("login.html", next=request.args.get("next", ""))


@app.post("/logout")
def logout() -> Any:
    require_csrf()
    session.clear()
    return redirect(url_for("login"))


@app.post("/reviewer")
@auth_required
def set_reviewer() -> Any:
    require_csrf()
    reviewer = " ".join(request.form.get("reviewer", "").split())
    if not reviewer:
        flash("Enter your name or reviewer ID before reviewing.", "error")
    elif len(reviewer) > 100:
        flash("Reviewer name must be 100 characters or fewer.", "error")
    else:
        session["reviewer"] = reviewer
        flash(f"Reviewing as {reviewer}.", "success")
    destination = request.form.get("next", "")
    if not destination.startswith("/") or destination.startswith("//"):
        destination = url_for("index")
    return redirect(destination)


@app.get("/")
@auth_required
def index() -> Any:
    all_reviews = get_reviews()
    grouped = reviews_grouped_by_row(all_reviews)
    reviewer_key = current_reviewer_key()
    my_reviews = {
        int(review_item["row_number"]): review_item
        for review_item in all_reviews
        if reviewer_key and review_item["reviewer_key"] == reviewer_key
    }
    tier = request.args.get("tier", "").strip()
    state = request.args.get("state", "").strip()
    query = request.args.get("q", "").strip().lower()
    visible = []
    for case in CASES:
        row_number = int(case["row_number"])
        my_review = my_reviews.get(row_number)
        if tier and not case["priority"]["tier"].startswith(tier):
            continue
        if state == "reviewed" and my_review is None:
            continue
        if state == "unreviewed" and my_review is not None:
            continue
        if query and query not in str(row_number) and query not in case["problem_description"].lower():
            continue
        visible.append({
            **case,
            "human_review": my_review,
            "reviewer_count": len(grouped.get(row_number, [])),
        })
    counts = {
        "total": len(CASES),
        "reviewed": len(my_reviews),
        "unreviewed": len(CASES) - len(my_reviews),
        "focused": sum(bool(case["focused_four_label_review"]) for case in CASES),
        "all_review_records": len(all_reviews),
    }
    return render_template(
        "index.html", cases=visible, counts=counts, tier=tier, state=state,
        query=request.args.get("q", ""), reviewer=session.get("reviewer", ""),
    )


@app.route("/review/<int:row_number>", methods=["GET", "POST"])
@auth_required
def review(row_number: int) -> Any:
    case = CASE_BY_ROW.get(row_number)
    if case is None:
        abort(404)
    previous_row, next_row = adjacent_rows(row_number)
    if request.method == "POST":
        require_csrf()
        labels = [request.form.get(f"label_{slot}", "").strip() for slot in range(1, 5)]
        labels = [label for label in labels if label]
        reviewer = " ".join(request.form.get("reviewer", "").split())
        save_action = request.form.get("save_action", "save")
        error = ""
        if not reviewer:
            error = "Enter your name or reviewer ID before saving."
        elif len(reviewer) > 100:
            error = "Reviewer name must be 100 characters or fewer."
        elif len(labels) != len(set(labels)):
            error = "Each human label must be unique."
        elif any(label not in TAXONOMY_BY_LABEL for label in labels):
            error = "One or more labels are not in the canonical taxonomy."

        structured_labels = [
            {
                "category": TAXONOMY_BY_LABEL[label]["category"],
                "subcategory": TAXONOMY_BY_LABEL[label]["subcategory"],
            }
            for label in labels if label in TAXONOMY_BY_LABEL
        ]
        if save_action == "save_review":
            status = "accepted" if label_set(structured_labels) == suggested_label_set(case) else "corrected"
        else:
            status = request.form.get("status", "")
            if not status:
                error = error or "Choose a status before using Save, or use Save review to classify it automatically."
            elif status not in ALLOWED_STATUSES:
                abort(400, "Invalid status")

        if error:
            flash(error, "error")
        else:
            reviewer_key = normalize_reviewer(reviewer)
            session["reviewer"] = reviewer
            now = utc_now()
            payload = json.dumps(structured_labels, ensure_ascii=False)
            notes = request.form.get("notes", "").strip()
            with connect_db() as db:
                db.execute(
                    """INSERT INTO reviews(row_number, reviewer_key, labels_json, status, notes, reviewer, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(row_number, reviewer_key) DO UPDATE SET
                         labels_json=excluded.labels_json, status=excluded.status,
                         notes=excluded.notes, reviewer=excluded.reviewer, updated_at=excluded.updated_at""",
                    (row_number, reviewer_key, payload, status, notes, reviewer, now),
                )
                db.execute(
                    """INSERT INTO review_history(
                         row_number, reviewer_key, labels_json, status, notes, reviewer, saved_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row_number, reviewer_key, payload, status, notes, reviewer, now),
                )
            flash(f"Saved {status.replace('_', ' ')} review for row {row_number} as {reviewer}.", "success")
            if save_action == "save_review":
                reviewed_rows = {
                    int(item["row_number"]) for item in get_reviews()
                    if item["reviewer_key"] == reviewer_key
                }
                order = case_order()
                current_index = order.index(row_number)
                candidates = order[current_index + 1:] + order[:current_index]
                target = next((number for number in candidates if number not in reviewed_rows), None)
                return redirect(url_for("review", row_number=target)) if target else redirect(url_for("index"))
            return redirect(url_for("review", row_number=row_number))

    all_row_reviews = reviews_grouped_by_row().get(row_number, [])
    reviewer_key = current_reviewer_key()
    saved = next((item for item in all_row_reviews if item["reviewer_key"] == reviewer_key), None)
    other_reviews = [item for item in all_row_reviews if item["reviewer_key"] != reviewer_key]
    if saved:
        selected = [f"{label['category']} / {label['subcategory']}" for label in saved["labels"]]
    else:
        selected = [f"{item['category']} / {item['subcategory']}" for item in case["suggested_labels"]]
    selected += [""] * (4 - len(selected))
    taxonomy_by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in TAXONOMY:
        taxonomy_by_category[item["category"]].append(item)
    return render_template(
        "review.html", case=case, saved=saved, other_reviews=other_reviews,
        selected=selected[:4], taxonomy_by_category=dict(taxonomy_by_category),
        taxonomy_lookup=TAXONOMY_BY_LABEL, previous_row=previous_row, next_row=next_row,
        reviewer=session.get("reviewer", ""),
    )


def csv_response(rows: Iterable[dict[str, Any]], fields: list[str], filename: str) -> Response:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def flattened_review_rows(reviews: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for review_item in reviews:
        case = CASE_BY_ROW[int(review_item["row_number"])]
        row: dict[str, Any] = {
            "row_number": review_item["row_number"],
            "problem_description": case["problem_description"],
            "status": review_item["status"], "notes": review_item["notes"],
            "reviewer": review_item["reviewer"], "reviewer_key": review_item["reviewer_key"],
            "updated_at": review_item["updated_at"],
        }
        for index, label in enumerate(review_item["labels"], 1):
            row[f"human_category_{index}"] = label["category"]
            row[f"human_subcategory_{index}"] = label["subcategory"]
        rows.append(row)
    return rows


def gold_and_disagreements(min_reviewers: int = 1) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gold: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    grouped = reviews_grouped_by_row()
    for case in CASES:
        row_number = int(case["row_number"])
        eligible = [
            item for item in grouped.get(row_number, [])
            if item["status"] in COMPLETED_STATUSES and item["labels"]
        ]
        sets: dict[frozenset[tuple[str, str]], list[dict[str, Any]]] = defaultdict(list)
        for item in eligible:
            sets[label_set(item["labels"])].append(item)
        if len(sets) > 1:
            disagreements.append({
                "row_number": row_number,
                "problem_description": case["problem_description"],
                "review_count": len(eligible),
                "reviewer_label_sets_json": json.dumps([
                    {
                        "reviewer": item["reviewer"],
                        "status": item["status"],
                        "labels": sorted(
                            [f"{label['category']} > {label['subcategory']}" for label in item["labels"]]
                        ),
                    }
                    for item in eligible
                ], ensure_ascii=False),
            })
            continue
        if len(sets) != 1 or len(eligible) < min_reviewers:
            continue
        agreed_set = next(iter(sets))
        labels = sorted(agreed_set, key=lambda pair: TAXONOMY_ORDER[pair])
        row = {
            "row_number": row_number,
            "problem_description": case["problem_description"],
            "original_human_category": case["original_human_label"]["category"],
            "original_human_subcategory": case["original_human_label"]["subcategory"],
            "gold_label_count": len(labels),
            "reviewer_count": len(eligible),
            "human_reviewers": "; ".join(item["reviewer"] for item in eligible),
            "validation_basis": "multi_reviewer_consensus" if len(eligible) >= 2 else "single_reviewer_validated",
            "validated_at": max(item["updated_at"] for item in eligible),
        }
        for index, (category, subcategory) in enumerate(labels, 1):
            row[f"gold_category_{index}"] = category
            row[f"gold_subcategory_{index}"] = subcategory
        gold.append(row)
    return gold, disagreements


@app.get("/export.csv")
@auth_required
def export_csv() -> Response:
    fields = ["row_number", "problem_description", "reviewer", "reviewer_key"]
    for slot in range(1, 5):
        fields.extend([f"human_category_{slot}", f"human_subcategory_{slot}"])
    fields.extend(["status", "notes", "updated_at"])
    return csv_response(flattened_review_rows(get_reviews()), fields, "human_label_reviews.csv")


@app.get("/export.json")
@auth_required
def export_json() -> Response:
    return jsonify({"exported_at": utc_now(), "reviews": get_reviews()})


@app.get("/export/gold.csv")
@auth_required
def export_gold_csv() -> Response:
    try:
        minimum = int(request.args.get("min_reviewers", "1"))
    except ValueError:
        abort(400, "min_reviewers must be an integer")
    if minimum not in {1, 2}:
        abort(400, "min_reviewers must be 1 or 2")
    fields = [
        "row_number", "problem_description", "original_human_category",
        "original_human_subcategory", "gold_label_count",
    ]
    for slot in range(1, 5):
        fields.extend([f"gold_category_{slot}", f"gold_subcategory_{slot}"])
    fields.extend(["reviewer_count", "human_reviewers", "validation_basis", "validated_at"])
    gold, _ = gold_and_disagreements(minimum)
    return csv_response(gold, fields, f"human_validated_gold_min{minimum}.csv")


@app.get("/export/gold-disagreements.csv")
@auth_required
def export_gold_disagreements_csv() -> Response:
    _, disagreements = gold_and_disagreements()
    return csv_response(
        disagreements,
        ["row_number", "problem_description", "review_count", "reviewer_label_sets_json"],
        "human_gold_disagreements.csv",
    )


@app.get("/healthz")
def healthz() -> Response:
    try:
        with connect_db() as db:
            db.execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "cases": len(CASES)})
    except sqlite3.Error:
        return jsonify({"status": "error"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=False)
