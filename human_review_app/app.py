"""Small persistent web interface for adjudicating silver labels."""

from __future__ import annotations

import csv
import hmac
import io
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

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


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


CASES: list[dict[str, Any]] = load_json(CASES_PATH)
CASE_BY_ROW = {int(case["row_number"]): case for case in CASES}
TAXONOMY: list[dict[str, str]] = load_json(TAXONOMY_PATH)
TAXONOMY_BY_LABEL = {
    f"{item['category']} / {item['subcategory']}": item for item in TAXONOMY
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


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db() -> None:
    with connect_db() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                row_number INTEGER PRIMARY KEY,
                labels_json TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                reviewer TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                row_number INTEGER NOT NULL,
                labels_json TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                reviewer TEXT NOT NULL DEFAULT '',
                saved_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS review_history_row_number
            ON review_history(row_number, saved_at);
            """
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


def get_reviews() -> dict[int, dict[str, Any]]:
    with connect_db() as db:
        rows = db.execute("SELECT * FROM reviews").fetchall()
    return {
        int(row["row_number"]): {
            **dict(row),
            "labels": json.loads(row["labels_json"]),
        }
        for row in rows
    }


def case_order() -> list[int]:
    return [int(case["row_number"]) for case in CASES]


def adjacent_rows(row_number: int) -> tuple[int | None, int | None]:
    order = case_order()
    index = order.index(row_number)
    return (order[index - 1] if index else None, order[index + 1] if index + 1 < len(order) else None)


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


@app.get("/")
@auth_required
def index() -> Any:
    reviews = get_reviews()
    tier = request.args.get("tier", "").strip()
    state = request.args.get("state", "").strip()
    query = request.args.get("q", "").strip().lower()
    visible = []
    for case in CASES:
        row_number = int(case["row_number"])
        review = reviews.get(row_number)
        if tier and not case["priority"]["tier"].startswith(tier):
            continue
        if state == "reviewed" and review is None:
            continue
        if state == "unreviewed" and review is not None:
            continue
        if query and query not in str(row_number) and query not in case["problem_description"].lower():
            continue
        visible.append({**case, "human_review": review})
    counts = {
        "total": len(CASES),
        "reviewed": len(reviews),
        "unreviewed": len(CASES) - len(reviews),
        "focused": sum(bool(case["focused_four_label_review"]) for case in CASES),
    }
    return render_template("index.html", cases=visible, counts=counts, tier=tier, state=state, query=request.args.get("q", ""))


@app.route("/review/<int:row_number>", methods=["GET", "POST"])
@auth_required
def review(row_number: int) -> Any:
    case = CASE_BY_ROW.get(row_number)
    if case is None:
        abort(404)
    previous_row, next_row = adjacent_rows(row_number)
    reviews = get_reviews()
    saved = reviews.get(row_number)
    if request.method == "POST":
        require_csrf()
        labels = [request.form.get(f"label_{slot}", "").strip() for slot in range(1, 5)]
        labels = [label for label in labels if label]
        if len(labels) != len(set(labels)):
            flash("Each human label must be unique.", "error")
        elif any(label not in TAXONOMY_BY_LABEL for label in labels):
            flash("One or more labels are not in the canonical taxonomy.", "error")
        else:
            status = request.form.get("status", "needs_review")
            allowed_statuses = {"accepted", "corrected", "needs_more_info", "skipped", "needs_review"}
            if status not in allowed_statuses:
                abort(400, "Invalid status")
            structured_labels = [
                {
                    "category": TAXONOMY_BY_LABEL[label]["category"],
                    "subcategory": TAXONOMY_BY_LABEL[label]["subcategory"],
                }
                for label in labels
            ]
            now = utc_now()
            payload = json.dumps(structured_labels, ensure_ascii=False)
            notes = request.form.get("notes", "").strip()
            reviewer = request.form.get("reviewer", "").strip()
            with connect_db() as db:
                db.execute(
                    """INSERT INTO reviews(row_number, labels_json, status, notes, reviewer, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(row_number) DO UPDATE SET
                         labels_json=excluded.labels_json, status=excluded.status,
                         notes=excluded.notes, reviewer=excluded.reviewer, updated_at=excluded.updated_at""",
                    (row_number, payload, status, notes, reviewer, now),
                )
                db.execute(
                    "INSERT INTO review_history(row_number, labels_json, status, notes, reviewer, saved_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row_number, payload, status, notes, reviewer, now),
                )
            flash(f"Saved human review for row {row_number}.", "success")
            if request.form.get("save_action") == "next_unreviewed":
                current_reviews = get_reviews()
                order = case_order()
                current_index = order.index(row_number)
                candidates = order[current_index + 1:] + order[:current_index]
                target = next((number for number in candidates if number not in current_reviews), None)
                return redirect(url_for("review", row_number=target)) if target else redirect(url_for("index"))
            return redirect(url_for("review", row_number=row_number))

    if saved:
        selected = [f"{label['category']} / {label['subcategory']}" for label in saved["labels"]]
    else:
        selected = [f"{item['category']} / {item['subcategory']}" for item in case["suggested_labels"]]
    selected += [""] * (4 - len(selected))
    taxonomy_by_category: dict[str, list[dict[str, str]]] = {}
    for item in TAXONOMY:
        taxonomy_by_category.setdefault(item["category"], []).append(item)
    return render_template(
        "review.html",
        case=case,
        saved=saved,
        selected=selected[:4],
        taxonomy_by_category=taxonomy_by_category,
        taxonomy_lookup=json.dumps(TAXONOMY_BY_LABEL, ensure_ascii=False),
        previous_row=previous_row,
        next_row=next_row,
    )


@app.get("/export.csv")
@auth_required
def export_csv() -> Response:
    reviews = get_reviews()
    output = io.StringIO()
    fields = ["row_number", "problem_description"]
    for slot in range(1, 5):
        fields.extend([f"human_category_{slot}", f"human_subcategory_{slot}"])
    fields.extend(["status", "notes", "reviewer", "updated_at"])
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for case in CASES:
        review_item = reviews.get(int(case["row_number"]))
        if not review_item:
            continue
        row: dict[str, Any] = {
            "row_number": case["row_number"],
            "problem_description": case["problem_description"],
            "status": review_item["status"],
            "notes": review_item["notes"],
            "reviewer": review_item["reviewer"],
            "updated_at": review_item["updated_at"],
        }
        for index, label in enumerate(review_item["labels"], 1):
            row[f"human_category_{index}"] = label["category"]
            row[f"human_subcategory_{index}"] = label["subcategory"]
        writer.writerow(row)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=human_label_reviews.csv"})


@app.get("/export.json")
@auth_required
def export_json() -> Response:
    return jsonify({"exported_at": utc_now(), "reviews": list(get_reviews().values())})


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
