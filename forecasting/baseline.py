"""历史基线：最近四次相同星期销量均值；不足两次时用最近七次均值。"""

from statistics import mean

from forecasting.features import as_date, prior_sales


def predict_baseline(records, dish_id, target_date) -> float:
    history = prior_sales(records, dish_id, target_date)
    if not history:
        raise ValueError("没有可用历史数据")
    same_weekday = []
    for row in reversed(history):
        if as_date(row["date"]).weekday() == as_date(target_date).weekday():
            same_weekday.append(row)
            if len(same_weekday) == 4:
                break
    selected = same_weekday[-4:] if len(same_weekday) >= 2 else history[-7:]
    return float(mean(row["sales_quantity"] for row in selected))
