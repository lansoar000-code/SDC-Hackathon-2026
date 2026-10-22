"""以完整 JSON 快照保存预测，后续模型更新不会改写旧结果。"""

import json

from backend.errors import AppError


def save_prediction(connection, result):
    connection.execute(
        "INSERT INTO predictions VALUES (?, ?, ?, ?, ?)",
        (
            result["prediction_id"],
            result["created_at"],
            result["target_date"],
            result["source"],
            json.dumps(result, ensure_ascii=False, allow_nan=False),
        ),
    )


def get_prediction(connection, prediction_id):
    row = connection.execute(
        "SELECT payload FROM predictions WHERE prediction_id = ?", (prediction_id,)
    ).fetchone()
    if row is None:
        raise AppError("找不到这条预测记录", 404)
    return json.loads(row["payload"])


def list_predictions(connection, limit=50, offset=0):
    rows = connection.execute(
        "SELECT payload FROM predictions ORDER BY created_at DESC, prediction_id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    return [json.loads(row["payload"]) for row in rows]
