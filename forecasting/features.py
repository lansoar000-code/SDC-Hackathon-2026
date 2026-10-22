"""训练和在线预测共用同一特征函数；只读取目标日之前的记录。"""

from bisect import bisect_left
from datetime import date, timedelta
from math import cos, sin, tau
from statistics import mean

FEATURE_NAMES = [
    "recent_mean",
    "last_sales",
    "weekday_sin",
    "weekday_cos",
    "sunny",
    "cloudy",
    "rainy",
    "exam_week",
    "event",
]


def as_date(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


class HistoryIndex:
    """批量训练时先按菜品和日期建索引，避免每个样本都重新扫描全部菜品。"""

    def __init__(self, records):
        self.rows = {}
        for row in records:
            self.rows.setdefault(row["dish_id"], []).append(row)
        self.dates = {}
        for dish_id, rows in self.rows.items():
            rows.sort(key=lambda row: as_date(row["date"]))
            self.dates[dish_id] = [as_date(row["date"]) for row in rows]

    def before(self, dish_id, target):
        dates = self.dates.get(dish_id, [])
        position = bisect_left(dates, target)
        return self.rows.get(dish_id, [])[:position]


def prior_sales(records, dish_id, target_date):
    target = as_date(target_date)
    if isinstance(records, HistoryIndex):
        return records.before(dish_id, target)
    return sorted(
        (row for row in records if row["dish_id"] == dish_id and as_date(row["date"]) < target),
        key=lambda row: as_date(row["date"]),
    )


def feature_vector(records, dish_id, target_date, conditions):
    target = as_date(target_date)
    history = prior_sales(records, dish_id, target)
    if not history:
        raise ValueError(f"菜品 {dish_id} 没有目标日期之前的销量")
    recent = [
        row["sales_quantity"]
        for row in history[-7:]
        if as_date(row["date"]) >= target - timedelta(days=7)
    ]
    # 缺失日期不填 0；最近一周无记录时，退回最近七次营业记录。
    recent_mean = mean(recent or [row["sales_quantity"] for row in history[-7:]])
    angle = tau * target.weekday() / 7
    return [
        recent_mean,
        history[-1]["sales_quantity"],
        sin(angle),
        cos(angle),
        *[float(conditions.get("weather") == value) for value in ("sunny", "cloudy", "rainy")],
        float(bool(conditions.get("is_exam_week"))),
        float(bool(conditions.get("has_event"))),
    ]
