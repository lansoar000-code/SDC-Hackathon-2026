"""只生成浏览器验收用合成销量；不向真实数据库写入，不作为业务效果证据。"""

import csv
from datetime import date, timedelta
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent / "fixtures"
    folder.mkdir(exist_ok=True)
    path = folder / "synthetic_sales.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "date",
                "dish_id",
                "dish_name",
                "sales_quantity",
                "weather",
                "is_exam_week",
                "has_event",
            ]
        )
        for day in range(42):
            target = date(2026, 8, 1) + timedelta(days=day)
            for dish_id, name, base in [
                ("test-rice", "TEST Rice", 60),
                ("test-noodles", "TEST Noodles", 40),
            ]:
                writer.writerow(
                    [target, dish_id, name, base + (day % 7) * 3, "sunny", "false", "false"]
                )
    print(path)


if __name__ == "__main__":
    main()
