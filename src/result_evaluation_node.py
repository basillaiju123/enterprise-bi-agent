from langfuse import observe

from src.graph_state import AgentState


@observe(name="evaluate_result")
def evaluate_result_node(state: AgentState) -> AgentState:

    # Normal production execution does not have an expected answer.
    if not state["evaluation_mode"]:
        return state

    expected = state["expected_result"]
    actual = state["query_result"]

    if actual == expected:
        return {
            **state,
            "validation_error": "",
        }

    return {
        **state,
        "validation_error": (
            f"Result mismatch. "
            f"Expected: {expected}. "
            f"Actual: {actual}."
        ),
    }