"""虚构校园食堂模拟器：可复现的需求、备餐、售出与浪费，而非真实历史。"""

import csv
import hashlib
import json
import platform
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np

VERSION = "synthetic-cafeteria-v1"
SEED = 20261022
SALES_FIELDS = [
    "date",
    "dish_id",
    "dish_name",
    "sales_quantity",
    "prepared_quantity",
    "waste_quantity",
    "weather",
    "is_exam_week",
    "has_event",
]
CLIMATE_SOURCE = "https://www.met.gov.my/en/pendidikan/iklim-malaysia/"


@dataclass(frozen=True)
class Dish:
    code: str
    name: str
    base_daily_demand: int
    rainy_effect: float
    exam_effect: float
    event_effect: float
    preference_drift: float


DISHES = [
    Dish("nasi_lemak", "Nasi Lemak", 105, -0.06, 0.02, 0.16, -0.05),
    Dish("chicken_rice", "Chicken Rice", 130, -0.03, 0.04, 0.22, 0.04),
    Dish("fried_rice", "Fried Rice", 85, -0.04, 0.07, 0.18, -0.03),
    Dish("mee_goreng", "Mee Goreng", 65, 0.03, 0.05, 0.12, -0.08),
    Dish("curry_rice", "Curry Rice", 70, 0.05, 0.02, 0.15, 0.01),
    Dish("vegetarian_rice", "Vegetarian Rice", 55, -0.01, 0.01, 0.10, 0.18),
    Dish("roti_canai", "Roti Canai", 45, -0.02, -0.02, 0.08, -0.02),
    Dish("noodle_soup", "Noodle Soup", 75, 0.18, 0.08, 0.12, 0.12),
]


def synthetic_calendar(day: date, index: int):
    """固定示例校历和压力场景；不对应任何真实学校校历或防疫政策。"""
    vacation = day.month in {1, 6, 7, 12}
    exam = day.month in {5, 11} and day.day >= 18
    maintenance = day.month == 6 and day.day == 15
    disruption = 0.38 if 4000 <= index < 4380 else 0.72 if 4380 <= index < 4700 else 1.0
    return vacation, exam, maintenance, disruption


def generate_dataset(output: Path, end_date: date, days: int = 10000, seed: int = SEED):
    """每一天每道菜一行，零销量仅表示模拟确实售出零份，不表示缺失。"""
    if days < 100:
        raise ValueError("为保留时间划分，至少生成 100 天")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"输出目录已有文件，请选择新目录，避免覆盖：{output}")
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    start = end_date - timedelta(days=days - 1)
    rows, daily, oracle = [], [], []
    # 下列概率、系数均为设计假设。官方来源仅支持季节性雨量的方向。
    weekday_factors = [1.00, 1.03, 1.04, 1.02, 0.94, 0.62, 0.54]
    previous_weather, shared_noise = "cloudy", 0.0
    for index in range(days):
        day = start + timedelta(days=index)
        vacation, exam, maintenance, disruption = synthetic_calendar(day, index)
        rain_probability = 0.51 if day.month in {4, 5, 10, 11} else 0.29
        weather = str(
            rng.choice(
                ["sunny", "cloudy", "rainy"], p=[0.72 - rain_probability, 0.28, rain_probability]
            )
        )
        if rng.random() < 0.25:
            weather = previous_weather
        previous_weather = weather
        event = bool(not maintenance and rng.random() < (0.012 if vacation else 0.045))
        shared_noise = 0.65 * shared_noise + rng.normal(0, 0.035)
        progress = index / max(days - 1, 1)
        traffic = weekday_factors[day.weekday()] * (0.48 if vacation else 1.0)
        traffic *= (0.9 if exam else 1.0) * disruption * (1 + 0.25 * progress)
        traffic *= 1.03 if day.day >= 25 or day.day <= 3 else 1.0
        if maintenance:
            traffic = 0.0
        day_sales, day_prep, day_demand, stockout_dishes = 0, 0, 0, 0
        for dish in DISHES:
            effect = 1 + (dish.rainy_effect if weather == "rainy" else 0)
            effect *= 1 + dish.exam_effect * exam
            effect *= 1 + dish.event_effect * event
            effect *= 1 + dish.preference_drift * progress
            expected = dish.base_daily_demand * traffic * effect
            # 需求含共同客流扰动、菜品随机波动和泊松噪声；备餐看不到当天的随机需求。
            demand = int(rng.poisson(expected * np.exp(shared_noise) * rng.lognormal(-0.005, 0.10)))
            preparation = int(round(expected * 1.08 * rng.lognormal(-0.0032, 0.08)))
            supply_incident = bool(expected > 0 and rng.random() < 0.025)
            if supply_incident:
                preparation = int(preparation * rng.uniform(0.58, 0.8))
            sold = min(demand, preparation)
            waste = preparation - sold
            dish_id = "synth_" + dish.code
            row = dict(
                zip(
                    SALES_FIELDS,
                    [
                        day.isoformat(),
                        dish_id,
                        "[SYNTHETIC] " + dish.name,
                        sold,
                        preparation,
                        waste,
                        weather,
                        exam,
                        event,
                    ],
                )
            )
            rows.append(row)
            # 真值侧表不进入训练输入；用于识别售罄造成的销量截断。
            oracle.append(
                {
                    "date": day.isoformat(),
                    "dish_id": dish_id,
                    "latent_demand": demand,
                    "unmet_demand": demand - sold,
                    "stockout": demand > preparation,
                    "supply_incident": supply_incident,
                }
            )
            day_sales += sold
            day_prep += preparation
            day_demand += demand
            stockout_dishes += demand > preparation
        daily.append(
            {
                "date": day.isoformat(),
                "sales_quantity": day_sales,
                "prepared_quantity": day_prep,
                "waste_quantity": day_prep - day_sales,
                "weather": weather,
                "is_exam_week": exam,
                "has_event": event,
                "is_vacation": vacation,
                "is_closed": maintenance,
                "disruption_factor": disruption,
                "latent_demand": day_demand,
                "stockout_dishes": stockout_dishes,
            }
        )

    sales_file = f"SYNTHETIC_sales_{days}_days.csv"
    _write_csv(output / sales_file, rows)
    _write_csv(output / "daily_context.csv", daily)
    _write_csv(output / "audit_oracle_NOT_FOR_TRAINING.csv", oracle)
    # API 单次上限 20,000 行：八道菜，每个导入包恰好最多 2,500 天。
    batches = []
    for number, first in enumerate(range(0, len(rows), 20000), start=1):
        filename = f"import_batches/SYNTHETIC_batch_{number:02d}.csv"
        _write_csv(output / filename, rows[first : first + 20000])
        batches.append(filename)
    train_days, development_days = int(days * 0.70), int(days * 0.85)
    for name, low, high in [
        ("train", 0, train_days),
        ("validation", train_days, development_days),
        ("test", development_days, days),
    ]:
        _write_csv(output / f"splits/{name}.csv", rows[low * len(DISHES) : high * len(DISHES)])
    manifest = {
        "dataset_id": VERSION,
        "data_origin": "synthetic",
        "seed": seed,
        "days": days,
        "rows": len(rows),
        "dish_count": len(DISHES),
        "start_date": start.isoformat(),
        "end_date": end_date.isoformat(),
        "sales_file": sales_file,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "train_days": train_days,
        "validation_days": development_days - train_days,
        "test_days": days - development_days,
        "validation_from": daily[train_days]["date"],
        "test_from": daily[development_days]["date"],
        "development_through": daily[development_days - 1]["date"],
        "climate_background_source": CLIMATE_SOURCE,
        "source_limit": "官方来源仅提供季节性方向；逐日天气、校历、需求与所有系数为作者模拟，不是实测。",
        "dishes": [asdict(dish) for dish in DISHES],
        "import_batches": batches,
        "checks": {
            "unique_date_dish_pairs": len({(row["date"], row["dish_id"]) for row in rows}),
            "continuous_dates": len({row["date"] for row in rows}) == days,
            "quantity_reconciliation": all(
                row["sales_quantity"] + row["waste_quantity"] == row["prepared_quantity"]
                for row in rows
            ),
            "closed_days": sum(day["is_closed"] for day in daily),
            "stockout_rows": sum(row["stockout"] for row in oracle),
        },
        "summary": {
            "total_sales": sum(row["sales_quantity"] for row in rows),
            "total_prepared": sum(row["prepared_quantity"] for row in rows),
            "total_waste": sum(row["waste_quantity"] for row in rows),
            "mean_daily_sales": round(float(np.mean([day["sales_quantity"] for day in daily])), 2),
            "weather_days": {
                label: sum(day["weather"] == label for day in daily)
                for label in ["sunny", "cloudy", "rainy"]
            },
            "exam_days": sum(day["is_exam_week"] for day in daily),
            "event_days": sum(day["has_event"] for day in daily),
        },
    }
    manifest["files"] = {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*.csv"))
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "README.md").write_text(
        f"# 合成食堂训练数据\n\n全部人工生成，不是真实食堂记录。\n\n"
        f"{start} 至 {end_date}：{days} 天，{len(DISHES)} 道菜，{len(rows)} 条记录。\n"
        f"随机种子 {seed}；参数、环境和 CSV 校验码见 manifest.json。\n\n"
        "导入使用 import_batches 下的分批文件。splits 按日期保留训练、验证、测试。\n"
        "daily_context 为日汇总；audit_oracle_NOT_FOR_TRAINING 为潜在需求真值，不进入模型特征。\n"
        "天气只有季节性方向参考 METMalaysia，其余逐日天气、校历、系数、销量均为模拟。\n"
        f"背景来源：{CLIMATE_SOURCE}\n\n"
        "holdout_report 为冻结模型的时间留出测试；最终全量模型已使用全部日期，不能再以同段做独立测试。\n"
        "完整假设和训练口径见项目 docs/11-synthetic-data.md。\n",
        encoding="utf-8",
    )
    return manifest


def _write_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
