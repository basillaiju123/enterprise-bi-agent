from src.graph_state import AgentState
from src.semantic_cache import cache_sql


def cache_store_node(state: AgentState) -> AgentState:
    sql = state["generated_sql"]

    # Do not cache queries that required human approval.
    if state.get("approval_required", False):
        return state

    # Only cache successfully executed queries.
    if state.get("execution_error", ""):
        return state

    cache_sql(
        question=state["user_question"],
        role=state["user_role"],
        sql=sql,
    )

    return state