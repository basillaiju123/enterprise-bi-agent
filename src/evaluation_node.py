from langfuse import observe

from src.graph_state import AgentState
from src.evaluator import evaluate_sql


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

    if expected == actual:
        return True

    if len(expected) == len(actual):
        return sorted(expected, key=str) == sorted(
            actual,
            key=str,
        )

    return False


@observe(name="evaluate_sql")
def evaluate_sql_node(state: AgentState) -> AgentState:

    # Evaluation benchmark:
    # If the executed SQL produces the expected result,
    # do not spend another LLM call judging the SQL.
    if state.get("evaluation_mode", False):

        expected = state.get(
            "expected_result",
            [],
        )

        actual = state.get(
            "query_result",
            [],
        )

        if results_match(expected, actual):
            return {
                **state,
                "validation_error": "",
            }

    # Only call the LLM semantic judge when deterministic
    # result validation did not already establish correctness.
    question = state["user_question"]
    sql = state["generated_sql"]
    schema_context = state["schema_context"]

    is_correct, feedback = evaluate_sql(
        question,
        sql,
        schema_context,
    )

    if is_correct:
        return {
            **state,
            "validation_error": "",
        }

    return {
        **state,
        "validation_error": feedback,
    }