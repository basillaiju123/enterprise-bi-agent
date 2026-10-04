from src.graph_state import AgentState


MAX_RETRIES = 3


def route_after_execution(state: AgentState) -> str:

    # Authorization failures are not recoverable.
    # Do not send them back to the LLM for correction.
    if state["authorization_error"]:
        return "failure"

    # SQL execution failed
    if state["execution_error"]:
        if state["retry_count"] >= MAX_RETRIES:
            return "failure"

        return "retry"

    # Semantic evaluation failed
    if state["validation_error"]:
        if state["retry_count"] >= MAX_RETRIES:
            return "failure"

        return "retry"

    # Everything passed
    return "success"