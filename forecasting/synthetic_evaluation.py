"""固定参数的滚动单日评估；各候选方法使用完全相同的日期与特征。"""

import csv
import json
from math import floor

from forecasting.baseline import predict_baseline
from forecasting.estimators import predict_estimator
from forecasting.evaluate import calculate_metrics
from forecasting.features import HistoryIndex, feature_vector


def evaluate_holdout(records, artifact, test_from, output):
    if artifact["trained_through"] >= test_from:
        raise ValueError("评估模型的训练截止日必须早于测试起点")
    history = HistoryIndex(records)
    test_rows = [row for row in records if row["date"] >= test_from]
    if not test_rows:
        raise ValueError("测试日期没有数据")
    selected_methods = {row["dish_id"]: row["selected"] for row in artifact["reports"]}
    details, by_dish = [], {}
    for dish_id in sorted({row["dish_id"] for row in test_rows}):
        dish_rows = [row for row in test_rows if row["dish_id"] == dish_id]
        vectors = [feature_vector(history, dish_id, row["date"], row) for row in dish_rows]
        actual = [row["sales_quantity"] for row in dish_rows]
        forecasts = {
            "baseline": [
                floor(predict_baseline(history, dish_id, row["date"]) + 0.5) for row in dish_rows
            ]
        }
        comparison_models = artifact.get("comparison_models", {}).get(dish_id, {})
        selected_model = artifact["models"].get(dish_id)
        if selected_model:
            comparison_models = {
                selected_model.get("kind", "ridge"): selected_model,
                **comparison_models,
            }
        for name, model in comparison_models.items():
            forecasts[name] = [floor(value + 0.5) for value in predict_estimator(model, vectors)]
        selected = selected_methods.get(dish_id, "baseline")
        predicted = forecasts[selected]
        by_dish[dish_id] = {
            "selected": selected,
            "metrics": calculate_metrics(actual, predicted),
            "baseline_metrics": calculate_metrics(actual, forecasts["baseline"]),
            "candidate_metrics": {
                name: calculate_metrics(actual, values) for name, values in forecasts.items()
            },
        }
        for index, row in enumerate(dish_rows):
            details.append(
                {
                    "date": row["date"],
                    "dish_id": dish_id,
                    "actual_sales": actual[index],
                    "prediction": predicted[index],
                    "baseline": forecasts["baseline"][index],
                    "ridge": forecasts["ridge"][index] if "ridge" in forecasts else None,
                    "xgboost": forecasts["xgboost"][index] if "xgboost" in forecasts else None,
                    "method": selected,
                }
            )
    details.sort(key=lambda row: (row["date"], row["dish_id"]))
    output.mkdir(parents=True, exist_ok=True)
    with (output / "holdout_predictions.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(details[0]))
        writer.writeheader()
        writer.writerows(details)
    report = {
        "data_origin": "synthetic",
        "test_from": test_from,
        "test_through": max(row["date"] for row in test_rows),
        "development_through": artifact["trained_through"],
        "metrics": _score_column(details, "prediction"),
        "baseline_metrics": _score_column(details, "baseline"),
        "candidate_metrics": {
            name: _score_column(details, name) for name in ["baseline", "ridge", "xgboost"]
        },
        "by_dish": by_dish,
        "protocol": "前70%日期训练，接着15%验证选方法，再用前85%重训；最后15%参数固定，仅滚动更新已观察的历史特征。每个候选方法使用相同日期和特征，测试结果不用于改选方法。",
        "limitation": "全部数据来自同一模拟器；不能证明真实食堂效果。特征未显式提供假期、关闭日与隐含供给冲击。",
    }
    (output / "holdout_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def _score_column(details, column):
    available = [row for row in details if row.get(column) is not None]
    return calculate_metrics(
        [row["actual_sales"] for row in available], [row[column] for row in available]
    )
