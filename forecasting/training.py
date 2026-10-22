"""按时间验证每道菜的 Ridge 模型；不优于基线时保留基线。模型以 JSON 保存。"""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from backend.errors import AppError
from forecasting.baseline import predict_baseline
from forecasting.evaluate import calculate_metrics
from forecasting.features import FEATURE_NAMES, HistoryIndex, feature_vector

MODEL_VERSION = "ridge-v1"


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


def fit_ridge(vectors, quantities):
    matrix = np.asarray(vectors, dtype=float)
    center, scale = matrix.mean(axis=0), matrix.std(axis=0)
    scale[scale == 0] = 1
    design = np.column_stack([np.ones(len(matrix)), (matrix - center) / scale])
    penalty = np.eye(design.shape[1]) * 10.0
    penalty[0, 0] = 0  # 不惩罚截距，避免把整体销量强行推向零。
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ np.asarray(quantities))
    return {
        "center": center.tolist(),
        "scale": scale.tolist(),
        "coefficients": coefficients.tolist(),
    }


def apply_ridge(model, vector):
    standardized = (np.asarray(vector) - np.asarray(model["center"])) / np.asarray(model["scale"])
    return max(0.0, float(np.dot(np.r_[1.0, standardized], model["coefficients"])))


def train_models(records, output_path: Path, *, validation_start: str | None = None):
    """末段 20% 日期作滚动单步验证；模型选择后用全量历史重训。"""
    dates = sorted({str(row["date"]) for row in records})
    if len(dates) < 21:
        raise AppError("训练至少需要 21 个有销量记录的日期；数据不足时仍可使用基线预测", 422)
    split_date = validation_start or dates[int(len(dates) * 0.8)]
    if split_date not in dates or split_date <= dates[0]:
        raise AppError("验证起点必须是已有日期，且晚于首个历史日期", 422)
    models, reports = {}, []
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
        candidate = fit_ridge(
            [vector for _, vector in training], [row["sales_quantity"] for row, _ in training]
        )
        actual = [row["sales_quantity"] for row, _ in validation]
        ridge_metrics = calculate_metrics(
            actual, [apply_ridge(candidate, vector) for _, vector in validation]
        )
        baseline_metrics = calculate_metrics(
            actual, [predict_baseline(history_index, dish_id, row["date"]) for row, _ in validation]
        )
        selected = "ridge" if ridge_metrics["mae"] < baseline_metrics["mae"] else "baseline"
        if selected == "ridge":
            models[dish_id] = fit_ridge(
                [vector for _, vector in samples], [row["sales_quantity"] for row, _ in samples]
            )
        reports.append(
            {
                "dish_id": dish_id,
                "selected": selected,
                "ridge": ridge_metrics,
                "baseline": baseline_metrics,
            }
        )
    artifact = {
        "data_origin": "synthetic"
        if all(row["dish_id"].startswith("synth_") for row in records)
        else "imported",
        "version": MODEL_VERSION,
        "feature_names": FEATURE_NAMES,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "trained_through": dates[-1],
        "validation_from": split_date,
        "data_fingerprint": data_fingerprint(records),
        "models": models,
        "reports": reports,
        "evaluation_note": "按日期滚动单步验证，较早验证日的实际销量可供之后日期使用；验证集用于模型选择，不是独立测试集。",
    }
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
