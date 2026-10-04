from src.security.sql_authorizer import authorize_sql
from src.execution_node import execute_sql_node


def test_viewer_can_access_allowed_table():
    allowed, message = authorize_sql(
        "SELECT * FROM customers;",
        "viewer",
    )

    assert allowed is True
    assert message == "SQL is authorized."


def test_viewer_cannot_access_orders():
    allowed, message = authorize_sql(
        "SELECT * FROM orders;",
        "viewer",
    )

    assert allowed is False
    assert "orders" in message


def test_viewer_cannot_access_restricted_join():
    allowed, message = authorize_sql(
        """
        SELECT *
        FROM orders
        JOIN customers
            ON orders.customer_id = customers.customer_id;
        """,
        "viewer",
    )

    assert allowed is False
    assert "orders" in message


def test_admin_can_access_orders():
    allowed, message = authorize_sql(
        "SELECT * FROM orders;",
        "admin",
    )

    assert allowed is True
    assert message == "SQL is authorized."


def test_execution_blocks_unauthorized_query():
    state = {
        "user_question": "Show me orders",
        "user_role": "viewer",
        "schema_context": "",
        "generated_sql": "SELECT * FROM orders;",
        "validation_error": "",
        "authorization_error": "",
        "execution_error": "",
        "query_result": [],
        "retry_count": 0,
        "expected_result": [],
        "evaluation_mode": False,
    }

    result = execute_sql_node(state)

    assert result["authorization_error"] != ""
    assert "not authorized" in result["authorization_error"]
    assert result["query_result"] == []