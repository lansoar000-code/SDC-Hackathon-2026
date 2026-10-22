"""创建、分页查询预测；导出与详情读取使用同一份保存快照。"""

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from backend.database import connect
from backend.dependencies import get_settings
from backend.repositories.predictions import get_prediction, list_predictions
from backend.schemas import PredictionRequest
from backend.services.prediction_service import create_prediction

router = APIRouter()


@router.post("/predictions", status_code=201)
def predict(request: PredictionRequest, settings=Depends(get_settings)):
    return create_prediction(settings, request)


@router.get("/predictions")
def history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    settings=Depends(get_settings),
):
    with connect(settings.database_path) as connection:
        return {
            "items": list_predictions(connection, limit, offset),
            "limit": limit,
            "offset": offset,
        }


@router.get("/predictions/{prediction_id}")
def detail(prediction_id: str, settings=Depends(get_settings)):
    with connect(settings.database_path) as connection:
        return get_prediction(connection, prediction_id)


@router.get("/predictions/{prediction_id}/export")
def export(prediction_id: str, settings=Depends(get_settings)):
    result = detail(prediction_id, settings)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "target_date",
            "dish_id",
            "dish_name",
            "predicted_sales_quantity",
            "recommended_prep_quantity",
            "method",
        ]
    )
    for item in result["items"]:
        # 防止菜品名称作为 Excel 公式执行；保留显示文本。
        name = item["dish_name"]
        if name.lstrip().startswith(("=", "+", "-", "@")):
            name = "'" + name
        writer.writerow(
            [
                result["target_date"],
                item["dish_id"],
                name,
                item["predicted_sales_quantity"],
                item["recommended_prep_quantity"],
                item["method"],
            ]
        )
    return Response(
        "\ufeff" + stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prepwise-prediction.csv"'},
    )
