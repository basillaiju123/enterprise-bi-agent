import sqlglot
from sqlglot import exp


FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
)


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL before execution.

    Returns:
        (True, message) if safe
        (False, reason) if rejected
    """

    # Prevent multiple SQL statements
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except Exception as e:
        return False, f"Invalid SQL syntax: {e}"

    if len(statements) != 1:
        return False, "Multiple SQL statements are not allowed."

    parsed = statements[0]

    # Only SELECT queries are allowed
    if not isinstance(parsed, exp.Select):
        return False, "Only SELECT queries are allowed."

    # Check for forbidden operations
    for expression in parsed.walk():
        if isinstance(expression, FORBIDDEN_EXPRESSIONS):
            return False, f"Forbidden SQL operation: {type(expression).__name__}"

    return True, "SQL is valid."