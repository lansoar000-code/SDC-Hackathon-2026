"""集中配置路径；默认从项目根目录运行，无需修改代码中的绝对路径。"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUSINESS_TIMEZONE = timezone(timedelta(hours=8))


def business_today():
    """业务日期统一为 UTC+8，避免服务器时区改变实际销量的日期校验。"""
    return datetime.now(BUSINESS_TIMEZONE).date()


@dataclass(frozen=True)
class Settings:
    database_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("PREPWISE_DATABASE", str(PROJECT_ROOT / "data" / "prepwise.sqlite3"))
        )
    )
    model_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("PREPWISE_MODEL", str(PROJECT_ROOT / "models" / "forecast.json"))
        )
    )
    frontend_path: Path = PROJECT_ROOT / "frontend"
    max_upload_bytes: int = 5 * 1024 * 1024
    max_import_rows: int = 20000
