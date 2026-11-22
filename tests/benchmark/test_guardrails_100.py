"""Deterministic tests for Orka.ai SQL guardrails. No LLM/API calls."""
import pytest

from src.guardrails.validator import validate_sql


VALID_QUERIES = [
    "SELECT 1",
    "SELECT 10 + 20",
    "SELECT 'Orka'",
    "SELECT TRUE",
    "SELECT NULL",
    "SELECT 1 AS id",
    "SELECT 1, 2, 3",
    "SELECT UPPER('orka')",
    "SELECT LOWER('ORKA')",
    "SELECT LENGTH('Orka')",
    "SELECT ABS(-10)",
    "SELECT ROUND(10.567, 2)",
    "SELECT COALESCE(NULL, 10)",
    "SELECT CASE WHEN 1 > 0 THEN 'yes' ELSE 'no' END",
    "SELECT 1 WHERE 1 = 1",
    "SELECT 1 WHERE 1 > 0",
    "SELECT 1 WHERE 1 < 5",
    "SELECT 1 WHERE 1 <> 2",
    "SELECT 1 WHERE 1 BETWEEN 0 AND 5",
    "SELECT 1 WHERE 1 IN (1, 2, 3)",
    "SELECT 1 WHERE 1 NOT IN (4, 5)",
    "SELECT 1 WHERE 'orka' LIKE 'or%'",
    "SELECT 1 WHERE 1 = 1 AND 2 = 2",
    "SELECT 1 WHERE 1 = 1 OR 2 = 3",
    "SELECT 1 ORDER BY 1",
    "SELECT 1 LIMIT 1",
    "SELECT 1 OFFSET 0",
    "SELECT 1 ORDER BY 1 LIMIT 5",
    "SELECT COUNT(*) FROM customers",
    "SELECT SUM(price) FROM products",
    "SELECT AVG(price) FROM products",
    "SELECT MIN(price) FROM products",
    "SELECT MAX(price) FROM products",
    "SELECT category, COUNT(*) FROM products GROUP BY category",
    "SELECT category, AVG(price) FROM products GROUP BY category",
    "SELECT category FROM products GROUP BY category HAVING COUNT(*) > 1",
    "SELECT * FROM customers",
    "SELECT customer_name FROM customers",
    "SELECT customer_name AS name FROM customers",
    "SELECT c.customer_name FROM customers AS c",
    "SELECT * FROM customers c WHERE c.customer_id = 1",
    "SELECT * FROM customers JOIN orders USING (customer_id)",
    "SELECT * FROM customers c JOIN orders o ON c.customer_id = o.customer_id",
    "SELECT * FROM products WHERE price > 100",
    "SELECT * FROM orders WHERE status = 'Completed'",
    "SELECT (SELECT COUNT(*) FROM customers) AS total",
    "WITH sample AS (SELECT 1 AS id) SELECT id FROM sample",
    "SELECT DISTINCT country FROM customers",
    "SELECT CASE WHEN price > 100 THEN 'High' ELSE 'Low' END FROM products",
]

FORBIDDEN_QUERIES = [
    "INSERT INTO customers VALUES (6, 'Test', 'India', DATE '2025-01-01')",
    "UPDATE customers SET country = 'India'",
    "DELETE FROM customers",
    "DROP TABLE customers",
    "DROP DATABASE warehouse",
    "ALTER TABLE customers ADD COLUMN age INTEGER",
    "CREATE TABLE test_table (id INTEGER)",
    "CREATE VIEW test_view AS SELECT 1",
    "CREATE INDEX idx_test ON customers(customer_id)",
    "INSERT INTO products VALUES (106, 'Test', 'Other', 10)",
    "UPDATE products SET price = 0",
    "DELETE FROM orders WHERE order_id = 1001",
    "DROP VIEW test_view",
    "ALTER TABLE products DROP COLUMN price",
    "CREATE SCHEMA test_schema",
    "INSERT INTO orders VALUES (1007, 1, DATE '2025-01-01', 'Completed')",
    "UPDATE orders SET status = 'Cancelled'",
    "DELETE FROM order_items",
    "DROP TABLE IF EXISTS products",
    "CREATE TEMP TABLE temp_table (id INTEGER)",
    "SELECT 1; SELECT 2",
    "SELECT customer_id FROM orders UNION SELECT customer_id FROM customers",
    "SELECT * FROM customers; DELETE FROM customers",
    "SELECT 1; DROP TABLE customers",
    "SELECT 1; UPDATE customers SET country = 'UK'",
    "SELECT 1; INSERT INTO customers VALUES (6, 'X', 'UK', DATE '2025-01-01')",
    "SELECT 1; ALTER TABLE customers ADD COLUMN age INTEGER",
    "SELECT 1; CREATE TABLE test_table (id INTEGER)",
    "SELECT 1;; SELECT 2",
    "SELECT FROM",
    "SELEC 1",
    "SELECT * FORM customers",
    "SELECT WHERE",
    "INSERT INTO",
    "UPDATE customers SET",
    "DELETE FROM",
    "DROP",
    "ALTER TABLE",
    "CREATE TABLE",
    "",
    "   ",
    "SELECT * FROM",
    "SELECT 1 +",
    "SELECT (1 + 2",
    "SELECT * FRM customers",
    "SELCT customer_name FROM customers",
    "SELECT 1 WHERE",
    "SELECT COUNT( FROM customers",
    "SELECT * WHERE customer_id =",
    "SELECT 'unterminated",
    "SELECT 1 + * 2",
]


@pytest.mark.parametrize("sql", VALID_QUERIES)
def test_safe_select_queries_are_accepted(sql):
    valid, message = validate_sql(sql)
    assert valid is True, f"Unexpected rejection: {sql} | {message}"


@pytest.mark.parametrize("sql", FORBIDDEN_QUERIES)
def test_forbidden_or_invalid_queries_are_rejected(sql):
    valid, message = validate_sql(sql)
    assert valid is False, f"Unexpected acceptance: {sql}"


def test_benchmark_has_exactly_100_cases():
    assert len(VALID_QUERIES) == 49
    assert len(FORBIDDEN_QUERIES) == 51
    assert len(VALID_QUERIES) + len(FORBIDDEN_QUERIES) == 100
