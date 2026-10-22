"""为 API 和命令行提供相同预测入口，明确每道菜的结果来源。"""

import json
from datetime import timedelta
from decimal import Decimal
from math import ceil, floor
from pathlib import Path

from backend.errors import AppError
from forecasting.baseline import predict_baseline
from forecasting.estimators import predict_one
from forecasting.features import as_date, feature_vector, prior_sales
from forecasting.training import MODEL_VERSION, data_fingerprint

DEMO_RULES = [
    ("demo-rice", "Fried rice", 80, {"sunny": 5, "cloudy": 0, "rainy": -10}, 15, 25),
    ("demo-noodles", "Noodles", 65, {"sunny": 0, "cloudy": 5, "rainy": 10}, 10, 20),
    ("demo-chicken", "Chicken rice", 70, {"sunny": 10, "cloudy": 5, "rainy": -5}, 20, 30),
]


def load_artifact(path: Path):
    if not path.exists():
        return None
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        if artifact["version"] not in {MODEL_VERSION, "ridge-v1"} or not isinstance(
            artifact["models"], dict
        ):
            raise ValueError("模型格式不兼容")
        return artifact
    except (ValueError, KeyError, OSError) as error:
        raise AppError("模型文件损坏或不兼容，请重新训练，或明确选择基线模式", 422) from error


def predict(records, request, model_path: Path):
    items, warnings = [], []
    if request.mode == "demo":
        for dish_id, name, base, weather, exam, event in DEMO_RULES:
            change = (
                weather[request.weather] + exam * request.is_exam_week + event * request.has_event
            )
            items.append(
                _item(dish_id, name, base * (1 + change / 100), "demo", request.prep_buffer_percent)
            )
        return items, ["模拟演示：固定示例规则，不使用真实销量或训练模型。"], "demo-rules-v1"

    history = [row for row in records if as_date(row["date"]) < request.target_date]
    if not history:
        raise AppError("目标日期之前没有历史销量，请先导入数据，或选择模拟演示", 422)
    if any(row["dish_id"].startswith("synth_") for row in history):
        warnings.append(
            "包含明确标识的合成食堂数据；预测与评估只反映模拟场景，不代表真实餐厅效果。"
        )
    artifact = load_artifact(model_path) if request.mode == "auto" else None
    if artifact:
        # 新增或修改历史数据后，旧模型不能悄悄继续声称是最新训练版本。
        if artifact["trained_through"] >= request.target_date.isoformat() or artifact[
            "data_fingerprint"
        ] != data_fingerprint(history):
            warnings.append("训练数据与本次可用历史不一致，已改用历史基线；可重新训练。")
            artifact = None
    if request.mode == "auto" and artifact is None:
        warnings.append("当前使用历史基线；天气、考试周和活动不会被人为加成。")
    for dish_id in sorted({row["dish_id"] for row in history}):
        dish_history = prior_sales(history, dish_id, request.target_date)
        latest = dish_history[-1]
        method = "baseline"
        estimate = predict_baseline(history, dish_id, request.target_date)
        if artifact and dish_id in artifact["models"]:
            vector = feature_vector(history, dish_id, request.target_date, request.model_dump())
            estimate = predict_one(artifact["models"][dish_id], vector)
            method = "model"
        if len(dish_history) < 7:
            warnings.append(
                f"{latest['dish_name']} 只有 {len(dish_history)} 条历史记录，结果仅供初步参考。"
            )
        if as_date(latest["date"]) != request.target_date - timedelta(days=1):
            warnings.append(
                f"{latest['dish_name']} 最新记录为 {latest['date']}；存在日期缺口或预测跨度超过一天。"
            )
        item = _item(dish_id, latest["dish_name"], estimate, method, request.prep_buffer_percent)
        item["algorithm"] = (
            artifact["models"][dish_id].get("kind", "ridge") if method == "model" else "baseline"
        )
        items.append(item)
    if any(item["method"] == "baseline" for item in items):
        warnings.append("基线菜品仅依据历史销量；天气、考试周和活动暂不影响这些菜品。")
    if any(item["method"] == "model" for item in items):
        warnings.append("模型尚未在独立真实测试集验证；历史条件缺失会限制对应因素的学习。")
    return (
        items,
        list(dict.fromkeys(warnings)),
        artifact["version"]
        if any(item["method"] == "model" for item in items)
        else "history-baseline-v1",
    )


def _item(dish_id, name, estimate, method, buffer):
    quantity = max(0, floor(estimate + 0.5))
    return {
        "dish_id": dish_id,
        "dish_name": name,
        "predicted_sales_quantity": quantity,
        # 十进制运算避免 50 * 1.1 产生 55.00000000000001 后多向上取一份。
        "recommended_prep_quantity": ceil(Decimal(quantity) * (100 + Decimal(str(buffer))) / 100),
        "method": method,
    }
