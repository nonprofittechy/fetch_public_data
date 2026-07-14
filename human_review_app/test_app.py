from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path


class ReviewAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ["REVIEW_DB_PATH"] = str(Path(cls.tempdir.name) / "reviews.sqlite3")
        os.environ["COOKIE_SECURE"] = "0"
        os.environ["SECRET_KEY"] = "test-only-secret"
        os.environ.pop("REVIEW_PASSWORD", None)
        cls.module = importlib.import_module("app")
        cls.module.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def setUp(self) -> None:
        with self.module.connect_db() as db:
            db.execute("DELETE FROM review_history")
            db.execute("DELETE FROM reviews")
        self.client = self.module.app.test_client()

    def csrf(self, client, path: str) -> str:
        client.get(path)
        with client.session_transaction() as session:
            return session["csrf_token"]

    def set_reviewer(self, client, reviewer: str) -> None:
        token = self.csrf(client, "/")
        response = client.post(
            "/reviewer",
            data={"csrf_token": token, "reviewer": reviewer, "next": "/"},
        )
        self.assertEqual(response.status_code, 302)

    def save(self, client, row_number: int, reviewer: str, labels: list[str], status: str = "accepted", action: str = "save"):
        token = self.csrf(client, f"/review/{row_number}")
        data = {
            "csrf_token": token,
            "reviewer": reviewer,
            "status": status,
            "save_action": action,
        }
        data.update({f"label_{index}": label for index, label in enumerate(labels, 1)})
        return client.post(f"/review/{row_number}", data=data)

    def suggested(self, row_number: int) -> list[str]:
        return [
            f"{item['category']} / {item['subcategory']}"
            for item in self.module.CASE_BY_ROW[row_number]["suggested_labels"]
        ]

    def test_health_queue_and_category_display(self) -> None:
        health = self.client.get("/healthz")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["cases"], 132)
        self.set_reviewer(self.client, "Reviewer A")
        queue = self.client.get("/")
        self.assertIn(b"Review labels as unordered sets of up to four", queue.data)
        page = self.client.get("/review/424")
        self.assertIn(b"Administrative Law &gt; Military/Veterans", page.data)
        self.assertIn(b"Supporting evidence and prior passes", page.data)

    def test_new_row_has_no_default_status_and_save_requires_one(self) -> None:
        self.set_reviewer(self.client, "Reviewer A")
        page = self.client.get("/review/290")
        self.assertIn(b'name="status"', page.data)
        self.assertNotIn(b'name="status" value="needs_review" checked', page.data)
        token = self.csrf(self.client, "/review/290")
        response = self.client.post(
            "/review/290",
            data={
                "csrf_token": token,
                "reviewer": "Reviewer A",
                "label_1": self.suggested(290)[0],
                "save_action": "save",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Choose a status", response.data)
        self.assertEqual(len(self.module.get_reviews()), 0)

    def test_save_review_assigns_accepted_or_corrected_from_unordered_set(self) -> None:
        self.set_reviewer(self.client, "Reviewer A")
        labels = list(reversed(self.suggested(424)))
        accepted = self.save(self.client, 424, "Reviewer A", labels, status="", action="save_review")
        self.assertEqual(accepted.status_code, 302)
        record = self.module.get_reviews()[0]
        self.assertEqual(record["status"], "accepted")

        corrected_labels = self.suggested(290)[:2]
        corrected = self.save(self.client, 290, "Reviewer A", corrected_labels, status="", action="save_review")
        self.assertEqual(corrected.status_code, 302)
        record = next(item for item in self.module.get_reviews() if item["row_number"] == 290)
        self.assertEqual(record["status"], "corrected")

    def test_two_reviewers_are_independent_and_history_is_append_only(self) -> None:
        first = self.module.app.test_client()
        second = self.module.app.test_client()
        self.set_reviewer(first, "Reviewer Alpha")
        self.set_reviewer(second, "Reviewer Beta")
        labels = self.suggested(424)
        self.assertEqual(self.save(first, 424, "Reviewer Alpha", labels).status_code, 302)
        self.assertEqual(self.save(second, 424, "Reviewer Beta", labels).status_code, 302)
        reviews = self.module.get_reviews()
        self.assertEqual(len(reviews), 2)
        self.assertEqual({item["reviewer"] for item in reviews}, {"Reviewer Alpha", "Reviewer Beta"})
        with self.module.connect_db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM review_history").fetchone()[0], 2)

    def test_gold_consensus_and_disagreement_exports(self) -> None:
        first = self.module.app.test_client()
        second = self.module.app.test_client()
        self.set_reviewer(first, "Reviewer Alpha")
        self.set_reviewer(second, "Reviewer Beta")
        labels = self.suggested(424)
        self.save(first, 424, "Reviewer Alpha", labels)
        self.save(second, 424, "Reviewer Beta", labels)
        strict_gold = first.get("/export/gold.csv?min_reviewers=2")
        self.assertIn(b"multi_reviewer_consensus", strict_gold.data)
        self.assertIn(b"Reviewer Alpha; Reviewer Beta", strict_gold.data)

        self.save(second, 424, "Reviewer Beta", labels[:3], status="corrected")
        strict_gold = first.get("/export/gold.csv?min_reviewers=2")
        self.assertNotIn(b"Not getting my vet benefits", strict_gold.data)
        disagreement = first.get("/export/gold-disagreements.csv")
        self.assertIn(b"Reviewer Alpha", disagreement.data)
        self.assertIn(b"Reviewer Beta", disagreement.data)

    def test_four_label_export_and_reviewer_scoped_queue(self) -> None:
        self.set_reviewer(self.client, "QA")
        labels = self.suggested(424)
        response = self.save(self.client, 424, "QA", labels)
        self.assertEqual(response.status_code, 302)
        saved = self.module.get_reviews()[0]
        self.assertEqual(len(saved["labels"]), 4)
        self.assertIn(b"Administrative Law", self.client.get("/export.csv").data)
        self.assertEqual(len(self.client.get("/export.json").get_json()["reviews"]), 1)
        reviewed_queue = self.client.get("/?state=reviewed")
        self.assertIn(b"Row 424", reviewed_queue.data)

    def test_rejects_duplicate_labels(self) -> None:
        self.set_reviewer(self.client, "Reviewer A")
        label = "Intellectual Property / Trademark/Copyright"
        response = self.save(self.client, 290, "Reviewer A", [label, label], status="corrected")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Each human label must be unique", response.data)
        self.assertEqual(len(self.module.get_reviews()), 0)

    def test_csrf_is_required(self) -> None:
        response = self.client.post("/review/252", data={"status": "accepted"})
        self.assertEqual(response.status_code, 400)

    def test_optional_password_login(self) -> None:
        os.environ["REVIEW_PASSWORD"] = "test-password"
        try:
            self.assertEqual(self.client.get("/").status_code, 302)
            token = self.csrf(self.client, "/login")
            wrong = self.client.post("/login", data={"csrf_token": token, "password": "wrong"})
            self.assertIn(b"Incorrect review password", wrong.data)
            accepted = self.client.post(
                "/login",
                data={"csrf_token": token, "password": "test-password", "next": "/"},
            )
            self.assertEqual(accepted.status_code, 302)
            self.assertEqual(accepted.headers["Location"], "/")
        finally:
            os.environ.pop("REVIEW_PASSWORD", None)


if __name__ == "__main__":
    unittest.main()
