"""误差查询与训练接口。训练结果保留时间验证口径。"""

from fastapi import APIRouter, Depends

from backend.config import business_today
from backend.database import connect
from backend.dependencies import get_settings
from backend.repositories.sales import list_sales
from backend.schemas import TrainingRequest
from backend.services.report_service import build_report
from forecasting.predictor import load_artifact
from forecasting.training import train_models

router = APIRouter()


@router.get("/reports/metrics")
def metrics(settings=Depends(get_settings)):
    return build_report(settings)


@router.post("/models/train")
def train(request: TrainingRequest, settings=Depends(get_settings)):
    cutoff = min(request.cutoff_date or business_today(), business_today()).isoformat()
    with connect(settings.database_path) as connection:
        records = [row for row in list_sales(connection) if row["date"] <= cutoff]
    artifact = train_models(records, settings.model_path)
    # 前端只需要比较分数，不在响应中传输整套树模型。
    return {
        key: value for key, value in artifact.items() if key not in {"models", "comparison_models"}
    }


@router.get("/models/status")
def model_status(settings=Depends(get_settings)):
    artifact = load_artifact(settings.model_path)
    if artifact is None:
        return {"trained": False, "message": "尚未训练，自动模式使用历史基线"}
    return {
        "trained": True,
        **{
            key: value
            for key, value in artifact.items()
            if key not in {"models", "comparison_models"}
        },
    }
