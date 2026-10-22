"""表格上传入口；只把文件内容传给解析服务，不使用上传文件名作为路径。"""

from fastapi import APIRouter, Depends, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.dependencies import get_settings
from backend.errors import AppError
from backend.services.import_service import import_file

router = APIRouter()


@router.post("/data/import", status_code=201)
async def import_sales(file: UploadFile, settings=Depends(get_settings)):
    try:
        content = await file.read(settings.max_upload_bytes + 1)
        if len(content) > settings.max_upload_bytes:
            raise AppError("文件不能超过 5 MB", 413)
        return await run_in_threadpool(import_file, settings, content, file.filename or "")
    finally:
        await file.close()
