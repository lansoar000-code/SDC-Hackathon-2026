"""菜品列表接口。"""

from fastapi import APIRouter, Depends

from backend.database import connect
from backend.dependencies import get_settings
from backend.repositories.dishes import list_dishes

router = APIRouter()


@router.get("/dishes")
def dishes(settings=Depends(get_settings)):
    with connect(settings.database_path) as connection:
        return {"items": list_dishes(connection)}
