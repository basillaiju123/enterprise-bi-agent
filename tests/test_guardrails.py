from src.guardrails.validator import validate_sql


def test_valid_select():
    sql = "SELECT * FROM customers;"
    is_valid, message = validate_sql(sql)

    assert is_valid is True


def test_delete_is_rejected():
    sql = "DELETE FROM customers;"
    is_valid, message = validate_sql(sql)

    assert is_valid is False


def test_drop_is_rejected():
    sql = "DROP TABLE customers;"
    is_valid, message = validate_sql(sql)

    assert is_valid is False


def test_multiple_statements_are_rejected():
    sql = "SELECT * FROM customers; SELECT * FROM orders;"
    is_valid, message = validate_sql(sql)

    assert is_valid is False