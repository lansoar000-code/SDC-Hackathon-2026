"""误差口径：WAPE 是误差率，不能称为准确率。"""

from math import sqrt


def calculate_metrics(actual, predicted):
    if len(actual) != len(predicted):
        raise ValueError("实际值与预测值长度不一致")
    if not actual:
        return {"count": 0, "mae": None, "rmse": None, "wape_percent": None, "bias": None}
    errors = [estimate - observed for observed, estimate in zip(actual, predicted)]
    absolute_error = sum(abs(error) for error in errors)
    total_actual = sum(abs(value) for value in actual)
    return {
        "count": len(actual),
        "mae": round(absolute_error / len(actual), 4),
        "rmse": round(sqrt(sum(error**2 for error in errors) / len(actual)), 4),
        "wape_percent": round(100 * absolute_error / total_actual, 4) if total_actual else None,
        "bias": round(sum(errors) / len(actual), 4),
    }
