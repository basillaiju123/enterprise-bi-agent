import sqlglot
from sqlglot import exp

from src.security.rbac import get_allowed_tables


def extract_tables(sql: str) -> set[str]:
    parsed = sqlglot.parse_one(sql, read="duckdb")

    tables = set()

    for table in parsed.find_all(exp.Table):
        tables.add(table.name.lower())

    return tables


def authorize_sql(sql: str, role: str) -> tuple[bool, str]:
    try:
        referenced_tables = extract_tables(sql)
        allowed_tables = get_allowed_tables(role)
    except Exception as e:
        return False, f"Authorization check failed: {e}"

    unauthorized_tables = referenced_tables - allowed_tables

    if unauthorized_tables:
        return (
            False,
            f"Role '{role}' is not authorized to access: "
            + ", ".join(sorted(unauthorized_tables)),
        )

    return True, "SQL is authorized."
