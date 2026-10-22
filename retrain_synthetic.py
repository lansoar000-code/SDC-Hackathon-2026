"""复用原有 80,000 行数据，比较 XGBoost、Ridge 与基线，不改动旧模型和旧报告。"""

import argparse
import json
from pathlib import Path

from backend.config import PROJECT_ROOT
from backend.database import connect
from backend.repositories.sales import list_sales
from forecasting.synthetic_evaluation import evaluate_holdout
from forecasting.training import data_fingerprint, train_models


def retrain(dataset: Path, output: Path, models: Path):
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    old_report = json.loads((dataset / "training_report.json").read_text(encoding="utf-8"))
    with connect(dataset / "training.sqlite3") as connection:
        records = list_sales(connection)
    if data_fingerprint(records) != old_report["final_data_fingerprint"]:
        raise ValueError("历史数据已改变，不能声称与上一版是在同一数据上比较")
    for folder in (output, models):
        if folder.exists() and any(folder.iterdir()):
            raise ValueError(f"输出目录已有文件，请另选目录：{folder}")
        folder.mkdir(parents=True, exist_ok=True)

    development = [row for row in records if row["date"] < manifest["test_from"]]
    print("1/3 使用相同 7000/1500 天训练与验证，比较三种方法…", flush=True)
    frozen = train_models(
        development,
        models / "holdout_model.json",
        validation_start=manifest["validation_from"],
        retain_candidates=True,
    )
    print("2/3 在相同的最后 1500 天比较固定参数模型…", flush=True)
    report = evaluate_holdout(records, frozen, manifest["test_from"], output)
    print("3/3 完成比较后，使用全部历史生成当前部署模型…", flush=True)
    final = train_models(records, models / "final_model.json")
    report["final_selected_methods"] = {row["dish_id"]: row["selected"] for row in final["reports"]}
    report["previous_ridge_selection_metrics"] = old_report["metrics"]
    report["test_reuse_note"] = (
        "这段测试已在上一版 Ridge 项目中查看；本次固定新增 XGBoost 参数、不根据测试结果选模型。它是同段对比，不能宣称一份全新未见测试集。"
    )
    report["final_model_note"] = (
        "最终模型使用全部10000天；留出指标仅属于训练至测试日前的 holdout_model。"
    )
    (output / "comparison_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "selected": report["metrics"],
                "candidates": report["candidate_metrics"],
                "final_selected_methods": report["final_selected_methods"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=PROJECT_ROOT / "data/synthetic/v1")
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "data/synthetic/v1/xgboost_comparison"
    )
    parser.add_argument("--models", type=Path, default=PROJECT_ROOT / "models/synthetic/xgboost-v2")
    args = parser.parse_args()
    retrain(args.dataset, args.output, args.models)


if __name__ == "__main__":
    main()
