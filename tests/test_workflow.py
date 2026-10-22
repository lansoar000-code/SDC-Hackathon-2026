"""跨层回归：真实数据库事务、HTTP 输入、历史隔离、模型版本与指标口径。"""

import csv
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.database import connect
from backend.main import create_app
from forecasting.evaluate import calculate_metrics
from forecasting.features import feature_vector
from forecasting.training import data_fingerprint


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        folder = Path(self.temporary.name)
        self.settings = Settings(
            database_path=folder / "test.sqlite3", model_path=folder / "model.json"
        )
        self.client = TestClient(create_app(self.settings))
        self.client.__enter__()
        self.day = date.today() - timedelta(days=90)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temporary.cleanup()

    def row(self, offset=0, quantity=10, dish_id="rice", name="Rice"):
        return {
            "date": (self.day + timedelta(days=offset)).isoformat(),
            "dish_id": dish_id,
            "dish_name": name,
            "sales_quantity": quantity,
            "weather": "sunny",
            "is_exam_week": False,
            "has_event": False,
        }

    def save(self, records):
        return self.client.post("/api/sales", json={"records": records})

    def predict(self, **changes):
        request = {"target_date": (self.day + timedelta(days=60)).isoformat(), **changes}
        return self.client.post("/api/predictions", json=request)

    def upload(self, rows, name="sales.csv"):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return self.client.post(
            "/api/data/import",
            files={"file": (name, stream.getvalue().encode("utf-8"), "text/csv")},
        )

    def test_empty_data_does_not_silently_become_demo(self):
        self.assertEqual(self.predict().status_code, 422)
        result = self.predict(mode="demo").json()
        self.assertEqual(result["source"], "demo")
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(self.client.get("/api/reports/metrics").json()["metrics"]["count"], 0)

    def test_import_and_duplicates_are_atomic(self):
        self.assertEqual(self.upload([self.row()]).status_code, 201)
        response = self.upload([self.row(1), self.row()])
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get("/api/health").json()["sales"]["count"], 1)

    def test_bad_csv_reports_line_and_writes_nothing(self):
        response = self.upload([self.row(), self.row(1, quantity=-4)])
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["details"]["rows"][0]["row"], 3)
        self.assertEqual(self.client.get("/api/health").json()["sales"]["count"], 0)

    def test_csv_rejects_fraction_nan_missing_and_duplicate_columns(self):
        for value in ["1.5", "NaN", "Infinity"]:
            self.assertEqual(self.upload([self.row(quantity=value)]).status_code, 422)
        response = self.client.post(
            "/api/data/import", files={"file": ("x.csv", b"date,dish_id,dish_id\n2020-01-01,a,a")}
        )
        self.assertEqual(response.status_code, 400)

    def test_xlsx_and_csv_share_validation(self):
        from openpyxl import Workbook

        workbook = Workbook()
        row = self.row()
        workbook.active.append(list(row))
        workbook.active.append(list(row.values()))
        stream = io.BytesIO()
        workbook.save(stream)
        workbook.close()
        response = self.client.post(
            "/api/data/import", files={"file": ("history.xlsx", stream.getvalue())}
        )
        self.assertEqual(response.status_code, 201, response.text)

    def test_sales_validation_and_consistent_dish_names(self):
        self.assertEqual(
            self.save(
                [{**self.row(), "date": (date.today() + timedelta(days=1)).isoformat()}]
            ).status_code,
            422,
        )
        self.assertEqual(self.save([{**self.row(), "prepared_quantity": 5}]).status_code, 422)
        self.assertEqual(self.save([self.row(), self.row(1, name="Different")]).status_code, 409)
        self.assertEqual(self.client.get("/api/dishes").json()["items"], [])

    def test_future_rows_do_not_change_prediction(self):
        self.save([self.row(0, 10), self.row(1, 20)])
        before = self.predict(target_date=(self.day + timedelta(days=2)).isoformat()).json()
        self.save([self.row(3, 900000), self.row(4, 900000, "newdish", "Future dish")])
        after = self.predict(target_date=(self.day + timedelta(days=2)).isoformat()).json()
        self.assertEqual(before["items"], after["items"])
        self.assertEqual(after["total_predicted_sales"], 15)

    def test_buffer_rounding_and_detail_export(self):
        self.save([self.row(quantity=11, name="=SUM(1,2)")])
        result = self.predict(prep_buffer_percent=10).json()
        self.assertEqual(result["total_recommended_prep"], 13)
        prediction_id = result["prediction_id"]
        self.assertEqual(self.client.get(f"/api/predictions/{prediction_id}").json(), result)
        exported = self.client.get(f"/api/predictions/{prediction_id}/export")
        self.assertIn("'=SUM", exported.text)
        self.assertEqual(self.client.get("/api/predictions/unknown").status_code, 404)

    def test_database_persists_across_application_restart(self):
        self.save([self.row()])
        result = self.predict().json()
        with TestClient(create_app(self.settings)) as second:
            self.assertEqual(second.get("/api/health").json()["sales"]["count"], 1)
            self.assertEqual(second.get("/api/predictions").json()["items"][0], result)

    def test_input_limits_and_pagination(self):
        self.assertEqual(self.predict(prep_buffer_percent=51).status_code, 422)
        self.assertEqual(self.predict(is_exam_week="yes").status_code, 422)
        self.assertEqual(self.predict(weather="snow").status_code, 422)
        self.assertEqual(self.client.get("/api/predictions?offset=-1").status_code, 422)
        self.assertEqual(self.client.get("/api/sales?limit=1001").status_code, 422)

    def test_training_fingerprint_and_stale_fallback(self):
        self.assertEqual(self.client.post("/api/models/train", json={}).status_code, 422)
        self.save([self.row(index, 10 + index % 7 * 3) for index in range(42)])
        response = self.client.post("/api/models/train", json={})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("reports", response.json())
        self.assertTrue(self.settings.model_path.exists())
        first = self.predict(target_date=(self.day + timedelta(days=42)).isoformat()).json()
        self.assertNotIn("训练数据与本次可用历史不一致", " ".join(first["warnings"]))
        self.save([self.row(42, 80)])
        stale = self.predict(target_date=(self.day + timedelta(days=43)).isoformat()).json()
        self.assertEqual(stale["source"], "baseline")
        self.assertIn("训练数据与本次可用历史不一致", " ".join(stale["warnings"]))

    def test_backdated_model_is_never_used_for_earlier_date(self):
        self.save([self.row(index, 10 + index) for index in range(42)])
        trained = self.client.post("/api/models/train", json={}).json()
        self.assertTrue(any(row["selected"] == "ridge" for row in trained["reports"]))
        future = self.predict(target_date=(self.day + timedelta(days=42)).isoformat()).json()
        self.assertEqual(future["source"], "model")
        result = self.predict(target_date=(self.day + timedelta(days=20)).isoformat()).json()
        self.assertEqual(result["source"], "baseline")

    def test_decimal_prep_buffer_does_not_add_spurious_serving(self):
        self.save([self.row(quantity=50)])
        result = self.predict(prep_buffer_percent=10).json()
        self.assertEqual(result["total_recommended_prep"], 55)

    def test_retrospective_comparisons_are_separate(self):
        self.save([self.row(0, 10)])
        self.predict(target_date=(self.day + timedelta(days=1)).isoformat())
        self.save([self.row(1, 12)])
        report = self.client.get("/api/reports/metrics").json()
        self.assertEqual(report["metrics"]["count"], 0)
        self.assertEqual(report["all_comparisons_metrics"]["mae"], 2)
        self.assertTrue(report["comparisons"][0]["retrospective"])

    def test_server_only_exposes_frontend(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/../backend/config.py").status_code, 404)
        self.assertEqual(self.client.get("/models/forecast.json").status_code, 404)

    def test_later_retrospective_prediction_does_not_replace_prospective_metric(self):
        self.save([self.row(0, 10)])
        target = (self.day + timedelta(days=1)).isoformat()
        saved = self.predict(target_date=target).json()
        saved["created_at"] = self.day.isoformat() + "T01:00:00+00:00"
        with connect(self.settings.database_path) as connection:
            connection.execute(
                "UPDATE predictions SET created_at = ?, payload = ? WHERE prediction_id = ?",
                (saved["created_at"], json.dumps(saved), saved["prediction_id"]),
            )
        self.save([self.row(1, 12)])
        self.predict(target_date=target)
        report = self.client.get("/api/reports/metrics").json()
        self.assertEqual(report["metrics"]["count"], 1)
        self.assertEqual(report["metrics"]["mae"], 2)
        self.assertTrue(report["comparisons"][0]["retrospective"])
        self.assertFalse(report["prospective_comparisons"][0]["retrospective"])

    def test_synthetic_records_are_explicitly_labelled(self):
        self.save([self.row(dish_id="synth_rice", name="[SYNTHETIC] Rice")])
        result = self.predict().json()
        self.assertEqual(result["data_origin"], "synthetic")
        self.assertIn("合成食堂数据", " ".join(result["warnings"]))


class ForecastingTests(unittest.TestCase):
    def test_feature_isolation_calendar_gaps_and_future_perturbation(self):
        history = [
            {"date": "2020-01-01", "dish_id": "a", "sales_quantity": 10},
            {"date": "2020-01-10", "dish_id": "a", "sales_quantity": 20},
            {"date": "2020-01-11", "dish_id": "a", "sales_quantity": 999},
            {"date": "2020-01-10", "dish_id": "b", "sales_quantity": 999},
        ]
        features = feature_vector(history, "a", "2020-01-11", {})
        self.assertEqual(features[:2], [20, 20])
        history[2]["sales_quantity"] = 1
        self.assertEqual(features, feature_vector(history, "a", "2020-01-11", {}))

    def test_zero_actual_wape_and_signed_bias(self):
        metrics = calculate_metrics([0, 0], [1, 3])
        self.assertIsNone(metrics["wape_percent"])
        self.assertEqual(metrics["bias"], 2)
        self.assertEqual(calculate_metrics([10], [8])["bias"], -2)

    def test_csv_and_database_bool_fingerprints_match(self):
        a = [{"date": "2020-01-01", "dish_id": "a", "is_exam_week": True, "has_event": False}]
        b = [{**a[0], "is_exam_week": 1, "has_event": 0}]
        self.assertEqual(data_fingerprint(a), data_fingerprint(b))


if __name__ == "__main__":
    unittest.main()
