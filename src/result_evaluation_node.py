from src.graph_state import AgentState


def normalize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def normalize_result(result):
    normalized = []

    for row in result:
        if isinstance(row, (list, tuple)):
            normalized.append(
                tuple(
                    normalize_value(value)
                    for value in row
                )
            )
        else:
            normalized.append(
                (normalize_value(row),)
            )

    return normalized


def results_match(expected, actual):
    expected = normalize_result(expected)
    actual = normalize_result(actual)

    # Exact match
    if expected == actual:
        return True

    # Same rows, different order
    if len(expected) == len(actual):
        return sorted(expected, key=str) == sorted(actual, key=str)

    return False


def evaluate_result_node(state: AgentState) -> AgentState:

    if not state["evaluation_mode"]:
        return state

    expected = state["expected_result"]
    actual = state["query_result"]

    if results_match(expected, actual):
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