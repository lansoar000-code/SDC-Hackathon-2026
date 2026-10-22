"""模拟数据的结构、可复现性、销量约束和时间划分检查。"""

import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from forecasting.data import read_table
from forecasting.synthetic import generate_dataset


class SyntheticTests(unittest.TestCase):
    def test_reproducible_continuous_and_importable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = generate_dataset(root / "one", date(2026, 9, 30), days=180)
            second = generate_dataset(root / "two", date(2026, 9, 30), days=180)
            self.assertEqual(first["files"], second["files"])
            self.assertEqual(first["rows"], 1440)
            self.assertEqual(first["days"], 180)
            records = read_table(
                (root / "one" / first["sales_file"]).read_bytes(), first["sales_file"]
            )
            self.assertEqual(len(records), 1440)
            self.assertEqual(len({record.date for record in records}), 180)
            self.assertTrue(all(record.dish_id.startswith("synth_") for record in records))
            self.assertTrue(
                all(
                    record.sales_quantity + record.waste_quantity == record.prepared_quantity
                    for record in records
                )
            )
            dates = []
            for name in ["train", "validation", "test"]:
                with (root / "one" / f"splits/{name}.csv").open(encoding="utf-8-sig") as stream:
                    dates.append({row["date"] for row in csv.DictReader(stream)})
            self.assertTrue(max(dates[0]) < min(dates[1]))
            self.assertTrue(max(dates[1]) < min(dates[2]))
            self.assertEqual(sum(len(part) for part in dates), 180)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                generate_dataset(folder, date(2026, 9, 30), days=100)
            self.assertEqual((folder / "keep.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
