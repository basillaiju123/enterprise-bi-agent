from langfuse import observe

from src.graph_state import AgentState
from src.guardrails.validator import validate_sql


@observe(name="validate_sql")
def validate_sql_node(state: AgentState) -> AgentState:

    sql = state["generated_sql"]

    is_valid, message = validate_sql(sql)

    if is_valid:
        return {
            **state,
            "validation_error": "",
        }

    return {
        **state,
        "validation_error": message,
    }