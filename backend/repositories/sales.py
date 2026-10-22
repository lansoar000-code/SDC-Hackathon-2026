"""销量读写；批量导入前检查冲突，整批通过后才写入。"""

from backend.errors import AppError


def list_sales(connection, before=None) -> list[dict]:
    where = "WHERE s.date < ?" if before else ""
    arguments = (str(before),) if before else ()
    rows = connection.execute(
        f"SELECT s.*, d.dish_name FROM sales s JOIN dishes d USING(dish_id) {where} ORDER BY s.date, s.dish_id",
        arguments,
    )
    return [dict(row) for row in rows]


def insert_sales(connection, records) -> int:
    seen = set()
    names = {row["dish_id"]: row["dish_name"] for row in connection.execute("SELECT * FROM dishes")}
    for record in records:
        key = (record.date.isoformat(), record.dish_id)
        if (
            key in seen
            or connection.execute(
                "SELECT 1 FROM sales WHERE date = ? AND dish_id = ?", key
            ).fetchone()
        ):
            raise AppError(f"重复记录：{key[0]} / {key[1]}；整批未写入", 409)
        seen.add(key)
        if record.dish_id in names and names[record.dish_id] != record.dish_name:
            raise AppError(
                f"菜品 {record.dish_id} 已对应名称 {names[record.dish_id]}，请统一名称", 409
            )
        names[record.dish_id] = record.dish_name

    for record in records:
        connection.execute(
            "INSERT OR IGNORE INTO dishes VALUES (?, ?)", (record.dish_id, record.dish_name)
        )
        connection.execute(
            "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.date.isoformat(),
                record.dish_id,
                record.sales_quantity,
                record.prepared_quantity,
                record.waste_quantity,
                record.weather,
                record.is_exam_week,
                record.has_event,
            ),
        )
    return len(records)
