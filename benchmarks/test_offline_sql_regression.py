"""Offline regression checks for the G048, G072, and G077 gold SQL cases.

These tests execute only the benchmark's gold SQL against the local sample
warehouse. They do not import the LangGraph app, call Groq, or contact Langfuse.

Run from the repository root:
    python -m unittest discover -s benchmarks -p "test_offline_sql_regression.py" -v
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "benchmarks" / "datasets" / "groq_eval_rag_regression_3.json"
DB_PATH = Path(
    os.getenv("ORKA_DB_PATH", str(ROOT / "data" / "sample_warehouse.duckdb"))
)


def load_cases() -> dict[str, dict]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return {case["id"]: case for case in dataset["cases"]}


def execute_gold_query(case_id: str) -> tuple[list[str], list[tuple]]:
    case = load_cases()[case_id]
    with duckdb.connect(str(DB_PATH), read_only=True) as connection:
        cursor = connection.execute(case["gold_sql"])
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return columns, rows


class OfflineSQLRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DATASET_PATH.is_file():
            raise FileNotFoundError(f"Regression dataset not found: {DATASET_PATH}")
        if not DB_PATH.is_file():
            raise FileNotFoundError(
                f"Sample warehouse not found: {DB_PATH}. "
                "Create it with: python create_database.py"
            )
        cls.cases = load_cases()
        expected_ids = {"G048", "G072", "G077"}
        missing = expected_ids - set(cls.cases)
        if missing:
            raise AssertionError(
                f"Regression dataset is missing cases: {sorted(missing)}"
            )

    def test_g048_cancelled_order_customers(self) -> None:
        columns, rows = execute_gold_query("G048")

        self.assertEqual(columns, ["customer_name"])
        self.assertEqual(rows, [("Charlie",)])
        self.assertEqual(len(rows), len(set(rows)))

    def test_g072_distinct_products_per_order(self) -> None:
        columns, rows = execute_gold_query("G072")

        self.assertEqual(columns, ["order_id", "distinct_products"])
        self.assertEqual(
            rows,
            [
                (1001, 2),
                (1002, 2),
                (1003, 1),
                (1004, 1),
                (1005, 1),
                (1006, 2),
            ],
        )

        # Independently calculate the expected distinct count from raw rows.
        with duckdb.connect(str(DB_PATH), read_only=True) as connection:
            independent_rows = connection.execute(
                """
                SELECT order_id, COUNT(DISTINCT product_id) AS distinct_products
                FROM order_items
                GROUP BY order_id
                ORDER BY order_id
                """
            ).fetchall()

        self.assertEqual(rows, independent_rows)

    def test_g077_highest_revenue_category(self) -> None:
        columns, rows = execute_gold_query("G077")

        self.assertEqual(columns, ["category", "revenue"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Electronics")
        self.assertAlmostEqual(rows[0][1], 2700.0, places=6)

        # Verify the selected category is the maximum across all categories.
        with duckdb.connect(str(DB_PATH), read_only=True) as connection:
            totals = connection.execute(
                """
                SELECT p.category, SUM(oi.quantity * p.price) AS revenue
                FROM products AS p
                JOIN order_items AS oi ON p.product_id = oi.product_id
                GROUP BY p.category
                ORDER BY revenue DESC, p.category
                """
            ).fetchall()

        self.assertEqual(rows[0], totals[0])


if __name__ == "__main__":
    unittest.main()
