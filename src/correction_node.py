from langfuse import observe

from src.graph_state import AgentState


@observe(name="correction")
def correction_node(state: AgentState) -> AgentState:

    retry_count = state["retry_count"] + 1

    return {
        **state,
        "retry_count": retry_count,
    }