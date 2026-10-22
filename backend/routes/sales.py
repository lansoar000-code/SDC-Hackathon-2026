"""实际销量录入及查询，与文件导入共用原子保存逻辑。"""

from fastapi import APIRouter, Depends, Query

from backend.database import connect
from backend.dependencies import get_settings
from backend.schemas import SaleBatch
from backend.services.import_service import save_records

router = APIRouter()


@router.post("/sales", status_code=201)
def record_sales(batch: SaleBatch, settings=Depends(get_settings)):
    return save_records(settings, batch.records)


@router.get("/sales")
def sales(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    settings=Depends(get_settings),
):
    with connect(settings.database_path) as connection:
        rows = connection.execute(
            "SELECT s.*, d.dish_name FROM sales s JOIN dishes d USING(dish_id) ORDER BY date DESC, dish_id LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return {"items": [dict(row) for row in rows]}
