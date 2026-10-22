"""健康检查和数据概况。"""

from fastapi import APIRouter, Depends

from backend.database import connect
from backend.dependencies import get_settings

router = APIRouter()


@router.get("/health")
def health(settings=Depends(get_settings)):
    with connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count, MIN(date) AS first_date, MAX(date) AS last_date FROM sales"
        ).fetchone()
    return {"status": "ok", "version": "1.0.0", "sales": dict(row)}
