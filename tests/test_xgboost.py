"""XGBoost 原生模型往返、方法择优、旧版兼容与测试日期边界。"""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from backend.schemas import PredictionRequest
from forecasting.estimators import fit_xgboost, predict_estimator
from forecasting.features import FEATURE_NAMES
from forecasting.predictor import load_artifact, predict
from forecasting.synthetic_evaluation import evaluate_holdout
from forecasting.training import data_fingerprint, train_models


class XGBoostTests(unittest.TestCase):
    def test_native_json_round_trip_and_reproducibility(self):
        rng = np.random.default_rng(42)
        vectors = rng.random((256, len(FEATURE_NAMES)))
        quantities = 20 + 60 * ((vectors[:, 0] > 0.5) & (vectors[:, 1] > 0.5))
        first = fit_xgboost(vectors, quantities)
        second = fit_xgboost(vectors, quantities)
        restored = json.loads(json.dumps(first))
        self.assertEqual(first["model_json"], second["model_json"])
        np.testing.assert_array_equal(
            predict_estimator(first, vectors), predict_estimator(restored, vectors)
        )
        self.assertEqual(first["kind"], "xgboost")
        self.assertLess(
            np.mean(np.abs(np.asarray(predict_estimator(first, vectors)) - quantities)), 5
        )

    def test_nonlinear_weather_exam_interaction_selects_xgboost(self):
        rng = np.random.default_rng(10)
        records = []
        start = date(2020, 1, 1)
        for index in range(420):
            rainy, exam = bool(rng.integers(2)), bool(rng.integers(2))
            records.append(
                {
                    "date": (start + timedelta(days=index)).isoformat(),
                    "dish_id": "synth_interaction",
                    "dish_name": "[SYNTHETIC] Interaction",
                    "sales_quantity": 20 + 80 * (rainy and exam),
                    "weather": "rainy" if rainy else "sunny",
                    "is_exam_week": exam,
                    "has_event": False,
                    "prepared_quantity": None,
                    "waste_quantity": None,
                }
            )
        with tempfile.TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "model.json"
            artifact = train_models(records, model_path, retain_candidates=True)
            self.assertEqual(artifact["reports"][0]["selected"], "xgboost")
            self.assertEqual(artifact["models"]["synth_interaction"]["kind"], "xgboost")
            self.assertEqual(
                set(artifact["comparison_models"]["synth_interaction"]), {"ridge", "xgboost"}
            )
            loaded = load_artifact(model_path)
            self.assertEqual(loaded["candidates"], ["baseline", "ridge", "xgboost"])
            request = PredictionRequest(
                target_date=start + timedelta(days=420), weather="rainy", is_exam_week=True
            )
            items, _, version = predict(records, request, model_path)
            self.assertEqual(items[0]["algorithm"], "xgboost")
            self.assertGreater(items[0]["predicted_sales_quantity"], 85)
            self.assertEqual(version, "demand-selection-v2")
            # 已使用测试日期的全量模型，不能再拿来冒充留出模型。
            with self.assertRaises(ValueError):
                evaluate_holdout(records, artifact, records[-10]["date"], Path(temporary))

    def test_legacy_ridge_model_remains_loadable(self):
        records = [
            {"date": "2020-01-01", "dish_id": "rice", "dish_name": "Rice", "sales_quantity": 10}
        ]
        artifact = {
            "version": "ridge-v1",
            "feature_names": FEATURE_NAMES,
            "trained_through": "2020-01-01",
            "data_fingerprint": data_fingerprint(records),
            "models": {
                "rice": {
                    "center": [0] * len(FEATURE_NAMES),
                    "scale": [1] * len(FEATURE_NAMES),
                    "coefficients": [20] + [0] * len(FEATURE_NAMES),
                }
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "old.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")
            items, _, version = predict(records, PredictionRequest(target_date="2020-01-02"), path)
            self.assertEqual(items[0]["predicted_sales_quantity"], 20)
            self.assertEqual(items[0]["algorithm"], "ridge")
            self.assertEqual(version, "ridge-v1")


if __name__ == "__main__":
    unittest.main()
