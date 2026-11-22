"""75 deterministic RBAC authorization cases. No LLM/API calls."""
import pytest

from src.security.sql_authorizer import authorize_sql


# Each query is evaluated against all three application roles.
# Viewer may access customers and products only; admin and analyst
# may access all four warehouse tables.
QUERY_CASES = [
    ("SELECT * FROM customers", True),
    ("SELECT customer_name FROM customers", True),
    ("SELECT * FROM products", True),
    ("SELECT product_name, price FROM products", True),
    ("SELECT c.customer_name FROM customers AS c", True),
    ("SELECT p.category, AVG(p.price) FROM products p GROUP BY p.category", True),
    ("SELECT DISTINCT country FROM customers", True),
    ("SELECT * FROM customers WHERE country = 'India'", True),
    ("SELECT * FROM products WHERE price > 100", True),
    ("SELECT COUNT(*) FROM customers", True),
    ("SELECT MIN(price), MAX(price) FROM products", True),
    ("SELECT * FROM customers c JOIN products p ON c.customer_id = p.product_id", True),
    ("SELECT * FROM orders", False),
    ("SELECT order_id, status FROM orders", False),
    ("SELECT * FROM order_items", False),
    ("SELECT order_id, quantity FROM order_items", False),
    ("SELECT * FROM customers c JOIN orders o ON c.customer_id = o.customer_id", False),
    ("SELECT * FROM orders o JOIN order_items i ON o.order_id = i.order_id", False),
    ("SELECT * FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_items i ON o.order_id = i.order_id", False),
    ("SELECT * FROM products p JOIN order_items i ON p.product_id = i.product_id", False),
    ("SELECT (SELECT COUNT(*) FROM orders) AS order_count", False),
    ("SELECT customer_id FROM orders UNION SELECT customer_id FROM customers", False),
    ("SELECT * FROM orders WHERE status = 'Completed'", False),
    ("SELECT SUM(quantity) FROM order_items", False),
    ("SELECT c.customer_name, o.status FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id", False),
]


@pytest.mark.parametrize(
    "sql,viewer_expected",
    QUERY_CASES,
    ids=[f"RBAC-{i:02d}" for i in range(1, len(QUERY_CASES) + 1)],
)
@pytest.mark.parametrize(
    "role",
    ["admin", "analyst", "viewer"],
)
def test_role_table_authorization(sql, viewer_expected, role):
    expected = True if role in {"admin", "analyst"} else viewer_expected

    authorized, message = authorize_sql(sql, role)

    assert authorized is expected, (
        f"Role={role!r}, SQL={sql!r}, expected={expected}, "
        f"actual={authorized}, message={message}"
    )


def test_benchmark_has_exactly_75_cases():
    assert len(QUERY_CASES) == 25
    assert len(QUERY_CASES) * 3 == 75
