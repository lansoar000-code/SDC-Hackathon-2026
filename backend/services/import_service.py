"""导入服务：校验、事务保存；错误时不写入任何一行。"""

import sqlite3

from backend.database import connect
from backend.errors import AppError
from backend.repositories.sales import insert_sales
from forecasting.data import read_table


def save_records(settings, records):
    try:
        with connect(settings.database_path) as connection:
            count = insert_sales(connection, records)
    except sqlite3.IntegrityError as error:
        raise AppError("记录冲突，整批未写入，请刷新后检查重复日期和菜品", 409) from error
    return {"imported_rows": count, "message": f"成功保存 {count} 条销量记录"}


def import_file(settings, content, filename):
    records = read_table(content, filename, settings.max_import_rows)
    return save_records(settings, records)
