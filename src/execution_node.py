import duckdb
from langfuse import observe

from src.graph_state import AgentState
from src.guardrails.validator import validate_sql

DB_PATH = "data/sample_warehouse.duckdb"


@observe(name="execute_sql")
def execute_sql_node(state: AgentState) -> AgentState:

    sql = state["generated_sql"]

    if state["validation_error"]:
        return {
            **state,
            "execution_error": "SQL validation failed.",
        }

    is_valid, message = validate_sql(sql)

    if not is_valid:
        return {
            **state,
            "validation_error": message,
            "execution_error": "SQL validation failed.",
        }

    con = duckdb.connect(DB_PATH)

    try:
        result = con.execute(sql).fetchall()

        if (
            len(result) == 1
            and len(result[0]) == 1
            and result[0][0] == 0
        ):
            return {
                **state,
                "query_result": result,
                "execution_error": (
                    "Query executed successfully but returned 0. "
                    "Check filtering conditions, exact values, "
                    "capitalization, joins, and column names."
                ),
            }

        return {
            **state,
            "query_result": result,
            "execution_error": "",
        }

    except Exception as e:
        return {
            **state,
            "query_result": [],
            "execution_error": str(e),
        }

    finally:
        con.close()