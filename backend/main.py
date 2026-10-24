"""应用组装入口。启动：python run.py；接口文档：/docs。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Settings
from backend.database import initialize
from backend.errors import AppError
from backend.routes import dishes, health, imports, plan_reviews, predictions, reports, sales

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        initialize(settings.database_path)
        plan_reviews.initialize_reviews(settings.database_path)
        yield

    app = FastAPI(title="PrepWise", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings

    @app.exception_handler(AppError)
    async def business_error(request: Request, error: AppError):
        return JSONResponse(
            {"error": {"message": error.message, "details": error.details}},
            status_code=error.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
            for item in error.errors()
        ]
        return JSONResponse(
            {"error": {"message": "请检查输入字段", "details": details}}, status_code=422
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        logger.exception("请求处理失败：%s", request.url.path)
        return JSONResponse(
            {"error": {"message": "服务处理失败，请查看运行窗口中的错误记录"}}, status_code=500
        )

    for module in (health, dishes, imports, predictions, sales, reports):
        app.include_router(module.router, prefix="/api")

    app.include_router(plan_reviews.router, prefix="/api")

    # API 路由优先，剩余路径才交给前端；数据库和模型目录不会被公开。
    app.mount("/", StaticFiles(directory=settings.frontend_path, html=True), name="frontend")
    return app


app = create_app()

