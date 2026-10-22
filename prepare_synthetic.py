"""生成、校验、隔离入库、时间留出评估及训练。直接在 PyCharm 运行即可。"""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from backend.config import PROJECT_ROOT, Settings, business_today
from backend.database import connect, initialize
from backend.repositories.sales import list_sales
from backend.services.import_service import save_records
from forecasting.data import read_table
from forecasting.synthetic import generate_dataset
from forecasting.synthetic_evaluation import evaluate_holdout
from forecasting.training import data_fingerprint, train_models


def prepare_dataset(output: Path, model_folder: Path, days: int, end_date: date):
    if end_date >= business_today():
        raise ValueError("模拟历史截止日应早于业务当天，保留下一天预测空间")
    print("1/5 生成合成食堂数据…", flush=True)
    manifest = generate_dataset(output, end_date, days)
    settings = Settings(
        database_path=output / "training.sqlite3", model_path=model_folder / "final_model.json"
    )
    initialize(settings.database_path)
    print("2/5 逐批校验并写入独立合成训练库…", flush=True)
    for filename in manifest["import_batches"]:
        path = output / filename
        records = read_table(path.read_bytes(), path.name)
        save_records(settings, records)
    with connect(settings.database_path) as connection:
        all_records = list_sales(connection)
    if len(all_records) != days * manifest["dish_count"]:
        raise ValueError("入库行数与生成行数不一致")

    development = [row for row in all_records if row["date"] < manifest["test_from"]]
    print("3/5 用前 85% 日期开发模型，后 15% 保留为测试…", flush=True)
    selection_model = train_models(
        development,
        model_folder / "holdout_model.json",
        validation_start=manifest["validation_from"],
        retain_candidates=True,
    )
    print("4/5 测试段滚动单步评估（不用于选模型）…", flush=True)
    report = evaluate_holdout(all_records, selection_model, manifest["test_from"], output)
    print("5/5 冻结评估后，用全部模拟历史生成最终模型…", flush=True)
    final_model = train_models(all_records, settings.model_path)
    model_label = (
        settings.model_path.relative_to(PROJECT_ROOT)
        if settings.model_path.is_relative_to(PROJECT_ROOT)
        else settings.model_path.name
    )
    report["final_model"] = {
        "path": str(model_label),
        "trained_through": final_model["trained_through"],
        "selected_methods": {row["dish_id"]: row["selected"] for row in final_model["reports"]},
        "note": "最终模型已使用测试日期，因此测试指标仅属于 holdout_model，不能再次把这段当最终模型的独立测试。",
    }
    report["database_rows"] = len(all_records)
    report["final_data_fingerprint"] = data_fingerprint(all_records)
    (output / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "days": manifest["days"],
                "rows": manifest["rows"],
                "date_range": [manifest["start_date"], manifest["end_date"]],
                "holdout": report["metrics"],
                "baseline": report["baseline_metrics"],
                "output": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return manifest, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=10000)
    parser.add_argument(
        "--end-date", type=date.fromisoformat, default=business_today() - timedelta(days=1)
    )
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data/synthetic/v1")
    parser.add_argument("--models", type=Path, default=PROJECT_ROOT / "models/synthetic/v1")
    arguments = parser.parse_args()
    if arguments.models.exists() and any(arguments.models.iterdir()):
        parser.error("模型输出目录已有文件，请指定一个新目录，避免覆盖已有结果")
    prepare_dataset(arguments.output, arguments.models, arguments.days, arguments.end_date)


if __name__ == "__main__":
    main()
