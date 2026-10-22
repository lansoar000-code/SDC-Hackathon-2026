"""预测与实际销量比较：同日期同菜品只选最近一次；演示记录不进入报表。"""

import json
from datetime import datetime

from backend.config import BUSINESS_TIMEZONE
from backend.database import connect
from backend.repositories.sales import list_sales
from forecasting.evaluate import calculate_metrics


def build_report(settings):
    with connect(settings.database_path) as connection:
        actuals = {
            (row["date"], row["dish_id"]): row["sales_quantity"] for row in list_sales(connection)
        }
        predictions = [
            json.loads(row["payload"])
            for row in connection.execute(
                "SELECT payload FROM predictions WHERE source != 'demo' ORDER BY created_at DESC, prediction_id DESC"
            )
        ]
    comparisons, seen = [], set()
    prospective, seen_prospective = [], set()
    for prediction in predictions:
        for item in prediction["items"]:
            key = (prediction["target_date"], item["dish_id"])
            if key not in actuals:
                continue
            # 对过去日期补做的预测也可查看，但不能冒充事前预测表现。
            saved_date = (
                datetime.fromisoformat(prediction["created_at"])
                .astimezone(BUSINESS_TIMEZONE)
                .date()
            )
            retrospective = saved_date.isoformat() >= prediction["target_date"]
            comparison = {
                "date": key[0],
                "dish_id": key[1],
                "dish_name": item["dish_name"],
                "actual": actuals[key],
                "predicted": item["predicted_sales_quantity"],
                "retrospective": retrospective,
                "prediction_id": prediction["prediction_id"],
            }
            if key not in seen:
                comparisons.append(comparison)
                seen.add(key)
            # 后来补做的历史预测不能把此前真实保存的事前预测挤出主指标。
            if not retrospective and key not in seen_prospective:
                prospective.append(comparison)
                seen_prospective.add(key)
    return {
        "metrics": calculate_metrics(
            [row["actual"] for row in prospective], [row["predicted"] for row in prospective]
        ),
        "all_comparisons_metrics": calculate_metrics(
            [row["actual"] for row in comparisons], [row["predicted"] for row in comparisons]
        ),
        "comparisons": comparisons,
        "prospective_comparisons": prospective,
        "note": "主指标取同日期同菜品最后一条事前预测；表格取最新预测，补做历史记录标 retrospective。WAPE 为误差率，分母为零时为空。",
    }
