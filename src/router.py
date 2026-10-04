from src.graph_state import AgentState

MAX_RETRIES = 3


def route_after_execution(state: AgentState) -> str:
    # Authorization failures are not recoverable.
    if state["authorization_error"]:
        return "failure"

    # Human rejection is final.
    # Do not send a rejected query back to the LLM.
    if state.get("approval_status", "") == "rejected":
        return "failure"

    # SQL execution failed.
    if state["execution_error"]:
        if state["retry_count"] >= MAX_RETRIES:
            return "failure"
        return "retry"

    # Semantic evaluation failed.
    if state["validation_error"]:
        if state["retry_count"] >= MAX_RETRIES:
            return "failure"
        return "retry"

    return "success"