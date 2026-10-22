"""按相同时间段比较历史基线、Ridge、XGBoost，逐菜选择验证 MAE 最低的方法。"""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.errors import AppError
from forecasting.baseline import predict_baseline
from forecasting.estimators import (
    XGBOOST_PARAMETERS,
    XGBOOST_ROUNDS,
    fit_ridge,
    fit_xgboost,
    predict_estimator,
)
from forecasting.evaluate import calculate_metrics
from forecasting.features import FEATURE_NAMES, HistoryIndex, feature_vector

MODEL_VERSION = "demand-selection-v2"


def data_fingerprint(records):
    canonical = []
    for row in records:
        normalized = dict(row)
        for field in ("is_exam_week", "has_event"):
            if normalized.get(field) is not None:
                normalized[field] = bool(normalized[field])
        canonical.append(normalized)
    canonical.sort(key=lambda row: (str(row["date"]), row["dish_id"]))
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, default=str).encode()).hexdigest()


def train_models(
    records,
    output_path: Path,
    *,
    validation_start: str | None = None,
    retain_candidates: bool = False,
):
    """末段 20% 日期作滚动单步验证；模型选择后用全量历史重训。"""
    dates = sorted({str(row["date"]) for row in records})
    if len(dates) < 21:
        raise AppError("训练至少需要 21 个有销量记录的日期；数据不足时仍可使用基线预测", 422)
    split_date = validation_start or dates[int(len(dates) * 0.8)]
    if split_date not in dates or split_date <= dates[0]:
        raise AppError("验证起点必须是已有日期，且晚于首个历史日期", 422)
    models, reports, comparison_models = {}, [], {}
    history_index = HistoryIndex(records)
    for dish_id in sorted({row["dish_id"] for row in records}):
        dish_rows = sorted(
            [row for row in records if row["dish_id"] == dish_id], key=lambda row: str(row["date"])
        )
        samples = [
            (row, feature_vector(history_index, dish_id, row["date"], row)) for row in dish_rows[1:]
        ]
        training = [(row, vector) for row, vector in samples if str(row["date"]) < split_date]
        validation = [(row, vector) for row, vector in samples if str(row["date"]) >= split_date]
        if len(training) < 10 or len(validation) < 3:
            reports.append(
                {"dish_id": dish_id, "selected": "baseline", "reason": "训练或验证样本不足"}
            )
            continue
        train_vectors = [vector for _, vector in training]
        train_quantities = [row["sales_quantity"] for row, _ in training]
        validation_vectors = [vector for _, vector in validation]
        actual = [row["sales_quantity"] for row, _ in validation]
        scores = {
            "baseline": calculate_metrics(
                actual,
                [predict_baseline(history_index, dish_id, row["date"]) for row, _ in validation],
            )
        }
        trainers = {"ridge": fit_ridge, "xgboost": fit_xgboost}
        for name, fit in trainers.items():
            candidate = fit(train_vectors, train_quantities)
            scores[name] = calculate_metrics(
                actual, predict_estimator(candidate, validation_vectors)
            )
        # 分数相同时按 baseline、ridge、xgboost 顺序选择，优先保持较简单方法。
        selected = min(scores, key=lambda name: scores[name]["mae"])
        all_vectors = [vector for _, vector in samples]
        all_quantities = [row["sales_quantity"] for row, _ in samples]
        # 只在离线对比时保留双方重训模型，线上文件仅保存实际选中的方法。
        refitted = {
            name: fit(all_vectors, all_quantities)
            for name, fit in trainers.items()
            if retain_candidates or name == selected
        }
        if selected != "baseline":
            models[dish_id] = refitted[selected]
        if retain_candidates:
            comparison_models[dish_id] = refitted
        reports.append({"dish_id": dish_id, "selected": selected, **scores})
    artifact = {
        "data_origin": "synthetic"
        if all(row["dish_id"].startswith("synth_") for row in records)
        else "imported",
        "version": MODEL_VERSION,
        "feature_names": FEATURE_NAMES,
        "candidates": ["baseline", "ridge", "xgboost"],
        "selection_metric": "validation_mae",
        "xgboost_parameters": XGBOOST_PARAMETERS,
        "xgboost_rounds": XGBOOST_ROUNDS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "trained_through": dates[-1],
        "validation_from": split_date,
        "data_fingerprint": data_fingerprint(records),
        "models": models,
        "reports": reports,
        "evaluation_note": "按日期滚动单步验证，较早验证日的实际销量可供之后日期使用；验证集用于模型选择，不是独立测试集。",
    }
    if retain_candidates:
        artifact["comparison_models"] = comparison_models
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 原子替换：预测请求不会读到只写了一半的 JSON 文件。
    descriptor, temporary = tempfile.mkstemp(dir=output_path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(artifact, stream, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporary, output_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return artifact
