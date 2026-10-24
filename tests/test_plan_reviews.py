"""Exercise persisted approval state, role checks, conflicts and immutable forecasts."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.database import connect
from backend.main import create_app


class PlanReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(
            database_path=Path(self.temp.name) / "test.sqlite3",
            model_path=Path(self.temp.name) / "model.json",
        )
        self.client = TestClient(create_app(self.settings))
        self.client.__enter__()
        self.owner = {"X-Demo-Actor": "demo-owner"}
        self.prediction = self.client.post(
            "/api/predictions", json={"target_date": "2026-10-25", "mode": "demo"}
        ).json()
        self.plan = self.client.post(
            "/api/plan-reviews", json={"prediction_id": self.prediction["prediction_id"]}
        ).json()
        self.url = "/api/plan-reviews/" + self.plan["review_id"]

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def edit_body(self):
        return {
            "expected_revision": 1,
            "reason": "Owner expects a busy lunch",
            "items": [
                {"dish_id": x["dish_id"], "final_prep_quantity": 42} for x in self.plan["items"]
            ],
        }

    def test_staff_cannot_approve_even_when_body_claims_owner(self):
        self.assertEqual(
            self.client.post(self.url + "/approve", json={"expected_revision": 1}).status_code, 403
        )
        self.assertEqual(
            self.client.post(
                self.url + "/approve", json={"expected_revision": 1, "role": "owner"}
            ).status_code,
            422,
        )
        self.assertEqual(self.client.get(self.url).json()["status"], "pending")

    def test_final_export_requires_approval(self):
        self.assertEqual(self.client.get(self.url + "/export").status_code, 409)
        self.assertEqual(
            self.client.get(
                "/api/predictions/" + self.prediction["prediction_id"] + "/export"
            ).status_code,
            200,
        )

    def test_edit_approve_export_and_audit_do_not_modify_prediction(self):
        self.assertEqual(self.client.put(self.url, json=self.edit_body()).status_code, 200)
        result = self.client.post(
            self.url + "/approve", headers=self.owner, json={"expected_revision": 2}
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["approved_by"]["id"], "demo-owner")
        final = self.client.get(self.url).json()
        self.assertEqual(
            [x["action"] for x in final["events"]], ["submitted", "quantities_updated", "approved"]
        )
        self.assertEqual(final["events"][1]["details"]["changes"][0]["after"], 42)
        self.assertTrue(all(x["actor"] and x["timestamp"] for x in final["events"]))
        csv = self.client.get(self.url + "/export").text
        self.assertIn("final_prep_quantity", csv)
        self.assertIn(",42,Demo owner,", csv)
        self.assertEqual(
            self.client.get("/api/predictions/" + self.prediction["prediction_id"]).json(),
            self.prediction,
        )

    def test_conflicts_and_lock_do_not_add_events(self):
        self.client.put(self.url, json=self.edit_body())
        self.assertEqual(self.client.put(self.url, json=self.edit_body()).status_code, 409)
        self.assertEqual(
            self.client.post(
                self.url + "/approve", headers=self.owner, json={"expected_revision": 1}
            ).status_code,
            409,
        )
        self.client.post(self.url + "/approve", headers=self.owner, json={"expected_revision": 2})
        self.assertEqual(
            self.client.put(
                self.url, json={**self.edit_body(), "expected_revision": 3}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(
                self.url + "/approve", headers=self.owner, json={"expected_revision": 3}
            ).status_code,
            409,
        )
        self.assertEqual(len(self.client.get(self.url).json()["events"]), 3)

    def test_invalid_dishes_quantities_and_reason_are_atomic(self):
        body = self.edit_body()
        for patch in [
            {"items": body["items"][:1]},
            {"reason": " "},
            {"items": [{"dish_id": "other", "final_prep_quantity": 1}]},
            {"items": [{"dish_id": "other", "final_prep_quantity": -1}]},
            {"items": [body["items"][0], body["items"][0]]},
        ]:
            self.assertEqual(self.client.put(self.url, json={**body, **patch}).status_code, 422)
        self.assertEqual(self.client.get(self.url).json()["revision"], 1)
        self.assertEqual(len(self.client.get(self.url).json()["events"]), 1)

    def test_idempotent_submission_and_persistence(self):
        status_url = "/api/plan-review-status/" + self.prediction["prediction_id"]
        self.assertEqual(
            self.client.get(status_url).json()["review"]["review_id"], self.plan["review_id"]
        )
        other = self.client.post(
            "/api/plan-reviews",
            headers=self.owner,
            json={"prediction_id": self.prediction["prediction_id"]},
        ).json()
        self.assertEqual(other["review_id"], self.plan["review_id"])
        with TestClient(create_app(self.settings)) as reopened:
            self.assertEqual(reopened.get(self.url).json()["submitted_by"]["role"], "staff")
            self.assertEqual(len(reopened.get(self.url).json()["events"]), 1)
            self.assertEqual(len(reopened.get("/api/plan-reviews").json()["items"]), 1)

    def test_unknown_actor_and_missing_records(self):
        self.assertEqual(
            self.client.get(self.url, headers={"X-Demo-Actor": "fake"}).status_code, 403
        )
        self.assertEqual(self.client.get("/api/plan-reviews/missing").status_code, 404)
        self.assertEqual(
            self.client.post("/api/plan-reviews", json={"prediction_id": "missing"}).status_code,
            404,
        )

    def test_csv_formula_is_escaped(self):
        with connect(self.settings.database_path) as db:
            import json

            plan = dict(self.plan)
            plan["items"][0]["dish_name"] = "=1+1"
            db.execute(
                "UPDATE plan_reviews SET payload=? WHERE review_id=?",
                (json.dumps(plan), plan["review_id"]),
            )
        self.client.post(self.url + "/approve", headers=self.owner, json={"expected_revision": 1})
        self.assertIn("'=1+1", self.client.get(self.url + "/export").text)


if __name__ == "__main__":
    unittest.main()
