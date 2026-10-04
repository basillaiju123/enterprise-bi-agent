from langfuse import observe

from src.graph_state import AgentState
from src.evaluator import evaluate_sql


@observe(name="evaluate_sql")
def evaluate_sql_node(state: AgentState) -> AgentState:

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