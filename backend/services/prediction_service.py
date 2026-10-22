"""协调预测和持久化；把用户条件、模型版本与数据截止日一起保存。"""

from datetime import datetime, timezone
from uuid import uuid4

from backend.database import connect
from backend.repositories.predictions import save_prediction
from backend.repositories.sales import list_sales
from forecasting.predictor import predict


def create_prediction(settings, request):
    with connect(settings.database_path) as connection:
        history = list_sales(connection, before=request.target_date)
        items, warnings, version = predict(history, request, settings.model_path)
        methods = {item["method"] for item in items}
        source = next(iter(methods)) if len(methods) == 1 else "mixed"
        result = {
            "prediction_id": uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_date": request.target_date.isoformat(),
            "source": source,
            "model_version": version,
            "conditions": request.model_dump(mode="json"),
            "data_through": max((row["date"] for row in history), default=None)
            if source != "demo"
            else None,
            "items": items,
            "total_predicted_sales": sum(item["predicted_sales_quantity"] for item in items),
            "total_recommended_prep": sum(item["recommended_prep_quantity"] for item in items),
            "warnings": warnings,
        }
        save_prediction(connection, result)
    return result
