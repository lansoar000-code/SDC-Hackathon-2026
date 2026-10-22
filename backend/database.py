"""每次业务操作使用独立连接；with 块整体提交或回滚并关闭连接。"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS dishes (
    dish_id TEXT PRIMARY KEY,
    dish_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sales (
    date TEXT NOT NULL,
    dish_id TEXT NOT NULL REFERENCES dishes(dish_id),
    sales_quantity INTEGER NOT NULL CHECK(sales_quantity >= 0),
    prepared_quantity INTEGER CHECK(prepared_quantity >= 0),
    waste_quantity INTEGER CHECK(waste_quantity >= 0),
    weather TEXT,
    is_exam_week INTEGER,
    has_event INTEGER,
    PRIMARY KEY(date, dish_id)
);
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    target_date TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS predictions_date ON predictions(target_date);
"""


@contextmanager
def connect(database_path: Path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(database_path: Path) -> None:
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)
