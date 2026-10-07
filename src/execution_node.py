import duckdb
from langfuse import observe

from src.graph_state import AgentState
from src.guardrails.validator import validate_sql
from src.security.sql_authorizer import authorize_sql

DB_PATH = "data/sample_warehouse.duckdb"


@observe(name="execute_sql")
def execute_sql_node(state: AgentState) -> AgentState:
    sql = state["generated_sql"]
    role = state["user_role"]

    if state.get("approval_status", "") == "rejected":
        return {
            **state,
            "query_result": [],
            "execution_error": "SQL execution rejected by human.",
        }

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

    is_authorized, authorization_message = authorize_sql(sql, role)

    if not is_authorized:
        return {
            **state,
            "authorization_error": authorization_message,
            "execution_error": "",
        }

    con = duckdb.connect(DB_PATH)

    try:
        result = con.execute(sql).fetchall()

       

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