from src.graph_state import AgentState
from src.semantic_cache import get_cached_sql, make_cache_key


def cache_lookup_node(state: AgentState) -> AgentState:
    question = state["user_question"]
    role = state["user_role"]

    cached_sql = get_cached_sql(question, role)

    if cached_sql is None:
        return {
            **state,
            "cache_hit": False,
            "cache_key": make_cache_key(question, role),
        }

    return {
        **state,
        "cache_hit": True,
        "cache_key": make_cache_key(question, role),
        "generated_sql": cached_sql,
    }