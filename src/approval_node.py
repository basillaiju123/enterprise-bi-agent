from langgraph.types import interrupt

from src.graph_state import AgentState


def approval_node(state: AgentState) -> AgentState:
    approval = interrupt(
        {
            "type": "sql_approval",
            "question": state["user_question"],
            "sql": state["generated_sql"],
            "message": "Human approval is required before executing this SQL.",
        }
    )

    

    if approval is True or approval == "approved":
        return {
            **state,
            "approval_status": "approved",
        }

    return {
        **state,
        "approval_status": "rejected",
        "execution_error": "SQL execution rejected by human.",
    }