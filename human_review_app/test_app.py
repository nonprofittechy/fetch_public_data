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

    def csrf(self, path: str) -> str:
        self.client.get(path)
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def test_health_and_queue(self) -> None:
        health = self.client.get("/healthz")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["cases"], 132)
        queue = self.client.get("/")
        self.assertIn(b"Review labels as unordered sets of up to four", queue.data)

    def test_four_label_save_and_exports(self) -> None:
        case = self.module.CASE_BY_ROW[424]
        labels = [f"{item['category']} / {item['subcategory']}" for item in case["suggested_labels"]]
        token = self.csrf("/review/424")
        response = self.client.post(
            "/review/424",
            data={
                "csrf_token": token,
                "label_1": labels[0],
                "label_2": labels[1],
                "label_3": labels[2],
                "label_4": labels[3],
                "status": "accepted",
                "reviewer": "QA",
                "notes": "Four distinct issues.",
                "save_action": "stay",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.module.connect_db() as db:
            saved = db.execute("SELECT * FROM reviews WHERE row_number=424").fetchone()
            history = db.execute("SELECT count(*) FROM review_history WHERE row_number=424").fetchone()[0]
        self.assertEqual(len(json.loads(saved["labels_json"])), 4)
        self.assertEqual(history, 1)
        self.assertIn(b"Administrative Law", self.client.get("/export.csv").data)
        self.assertEqual(len(self.client.get("/export.json").get_json()["reviews"]), 1)

    def test_rejects_duplicate_labels(self) -> None:
        token = self.csrf("/review/290")
        label = "Intellectual Property / Trademark/Copyright"
        response = self.client.post(
            "/review/290",
            data={
                "csrf_token": token,
                "label_1": label,
                "label_2": label,
                "status": "corrected",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Each human label must be unique", response.data)
        with self.module.connect_db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM reviews").fetchone()[0], 0)

    def test_csrf_is_required(self) -> None:
        response = self.client.post("/review/252", data={"status": "accepted"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
