"""健康检查和数据概况。"""

from fastapi import APIRouter, Depends

from backend.database import connect
from backend.dependencies import get_settings

router = APIRouter()


@router.get("/health")
def health(settings=Depends(get_settings)):
    with connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count, COUNT(DISTINCT date) AS date_count, "
            "MIN(date) AS first_date, MAX(date) AS last_date FROM sales"
        ).fetchone()
    return {
        "status": "ok",
        "version": "1.0.0",
        "sales": dict(row),
        "import_limits": {
            "max_upload_bytes": settings.max_upload_bytes,
            "max_rows": settings.max_import_rows,
        },
        "training": {"minimum_dates": 21, "ready": row["date_count"] >= 21},
    }
