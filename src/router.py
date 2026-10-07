from src.graph_state import AgentState


MAX_RETRIES = 3


def route_after_execution(state: AgentState) -> str:
    authorization_error = state.get("authorization_error", "")
    execution_error = state.get("execution_error", "")
    validation_error = state.get("validation_error", "")
    approval_status = state.get("approval_status", "")
    retry_count = state.get("retry_count", 0)

    if authorization_error:
        return "failure"

    if approval_status == "rejected":
        return "failure"

    if execution_error or validation_error:
        if retry_count >= MAX_RETRIES:
            return "failure"

        return "retry"

    return "success"