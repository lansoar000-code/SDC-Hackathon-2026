"""五个编号脚本的公共命令行实现，避免复制读取和参数校验逻辑。"""

import argparse
import csv
import io
import json
from pathlib import Path

from backend.errors import AppError
from backend.schemas import PredictionRequest
from forecasting.data import read_table
from forecasting.features import feature_vector
from forecasting.predictor import predict
from forecasting.training import train_models


def run_step(step: int):
    parser = argparse.ArgumentParser(
        description=f"PrepWise 数据流程 step{step}，请从项目根目录运行"
    )
    parser.add_argument("--input", type=Path, required=True, help="UTF-8 CSV 或 XLSX 历史销量")
    parser.add_argument("--output", type=Path, help="输出文件（可选）")
    parser.add_argument("--model", type=Path, default=Path("models/forecast.json"))
    if step == 3:
        parser.add_argument("--target-date", required=True, help="YYYY-MM-DD")
        parser.add_argument("--weather", choices=["sunny", "cloudy", "rainy"], default="sunny")
        parser.add_argument("--exam-week", action="store_true")
        parser.add_argument("--event", action="store_true")
        parser.add_argument("--buffer", type=float, default=0)
        parser.add_argument("--mode", choices=["auto", "baseline"], default="auto")
    args = parser.parse_args()
    try:
        if args.output and args.output.resolve() == args.input.resolve():
            raise ValueError("输出路径不能与原始输入文件相同")
        records = read_table(args.input.read_bytes(), args.input.name)
        data = [record.model_dump(mode="json") for record in records]
        if step == 0:
            target = args.output or Path("data/processed/sales.csv")
            _write_csv(target, data)
            result = {"rows": len(data), "output": str(target)}
        elif step == 1:
            result = {
                "valid": True,
                "rows": len(data),
                "dishes": len({row["dish_id"] for row in data}),
                "first_date": min(row["date"] for row in data),
                "last_date": max(row["date"] for row in data),
            }
        elif step == 2:
            result = train_models(data, args.output or args.model)
        elif step == 3:
            request = PredictionRequest(
                target_date=args.target_date,
                weather=args.weather,
                is_exam_week=args.exam_week,
                has_event=args.event,
                prep_buffer_percent=args.buffer,
                mode=args.mode,
            )
            items, warnings, version = predict(data, request, args.model)
            target = args.output or Path("data/predictions/predictions.csv")
            _write_csv(target, [{"target_date": args.target_date, **item} for item in items])
            result = {
                "output": str(target),
                "items": items,
                "warnings": warnings,
                "version": version,
            }
        else:
            result = check_feature_consistency(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (AppError, ValueError, OSError) as error:
        parser.exit(1, f"处理失败：{error}\n")


def _write_csv(path, records):
    if not records:
        raise ValueError("没有可写入数据")
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    for record in records:
        safe = {
            key: "'" + value
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@"))
            else value
            for key, value in record.items()
        }
        writer.writerow(safe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stream.getvalue(), encoding="utf-8-sig")


def check_feature_consistency(records):
    checked = 0
    for dish_id in sorted({row["dish_id"] for row in records}):
        rows = sorted(
            [row for row in records if row["dish_id"] == dish_id], key=lambda row: row["date"]
        )
        if len(rows) < 2:
            continue
        target = rows[-1]
        original = feature_vector(records, dish_id, target["date"], target)
        # 修改目标日及之后的销量，历史特征不应改变。
        perturbed = [
            {**row, "sales_quantity": 999999} if row["date"] >= target["date"] else row
            for row in records
        ]
        changed = feature_vector(perturbed, dish_id, target["date"], target)
        if original != changed:
            raise ValueError(f"菜品 {dish_id} 的特征使用了目标日期或未来销量")
        checked += 1
    if checked == 0:
        raise ValueError("每道菜至少需要两天记录才能检查特征")
    return {
        "passed": True,
        "checked_dishes": checked,
        "note": "只修改未来销量；天气等预测时已知条件保持一致。",
    }
