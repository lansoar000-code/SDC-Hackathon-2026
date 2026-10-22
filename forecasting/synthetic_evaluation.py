"""保持模型参数固定，按测试日期逐日滚动；只能读取更早日期的实际销量。"""

import csv
import json
from math import floor

from forecasting.baseline import predict_baseline
from forecasting.evaluate import calculate_metrics
from forecasting.features import HistoryIndex, feature_vector
from forecasting.training import apply_ridge


def evaluate_holdout(records, artifact, test_from, output):
    history = HistoryIndex(records)
    test_rows = [row for row in records if row["date"] >= test_from]
    actual, estimates, baselines, details = [], [], [], []
    by_dish = {}
    for row in test_rows:
        baseline = predict_baseline(history, row["dish_id"], row["date"])
        candidate = artifact["models"].get(row["dish_id"])
        estimate = baseline
        if candidate:
            estimate = apply_ridge(
                candidate, feature_vector(history, row["dish_id"], row["date"], row)
            )
        estimate, baseline = floor(estimate + 0.5), floor(baseline + 0.5)
        actual.append(row["sales_quantity"])
        estimates.append(estimate)
        baselines.append(baseline)
        details.append(
            {
                "date": row["date"],
                "dish_id": row["dish_id"],
                "actual_sales": row["sales_quantity"],
                "prediction": estimate,
                "baseline": baseline,
                "method": "model" if candidate else "baseline",
            }
        )
        series = by_dish.setdefault(
            row["dish_id"], {"actual": [], "prediction": [], "baseline": []}
        )
        series["actual"].append(row["sales_quantity"])
        series["prediction"].append(estimate)
        series["baseline"].append(baseline)
    with (output / "holdout_predictions.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(details[0]))
        writer.writeheader()
        writer.writerows(details)
    report = {
        "data_origin": "synthetic",
        "test_from": test_from,
        "test_through": max(row["date"] for row in test_rows),
        "development_through": artifact["trained_through"],
        "metrics": calculate_metrics(actual, estimates),
        "baseline_metrics": calculate_metrics(actual, baselines),
        "by_dish": {
            dish: {
                "selected": "model" if dish in artifact["models"] else "baseline",
                "metrics": calculate_metrics(series["actual"], series["prediction"]),
                "baseline_metrics": calculate_metrics(series["actual"], series["baseline"]),
            }
            for dish, series in by_dish.items()
        },
        "protocol": "前 70% 日期训练，接着 15% 验证选方法，再用前 85% 重训。最后 15% 测试时模型参数固定；后一天可使用更早测试日已观察销量。测试目标为售出份数，不是含未满足订单的潜在需求。",
        "limitation": "全部数据为同一模拟器生成；即使时间留出成绩良好，也不能证明真实食堂效果。特征未显式提供假期、关闭日与隐含供给冲击。",
    }
    (output / "holdout_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
