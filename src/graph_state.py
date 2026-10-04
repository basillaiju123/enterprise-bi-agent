from typing import TypedDict


class AgentState(TypedDict):
    user_question: str
    schema_context: str
    generated_sql: str
    validation_error: str
    execution_error: str
    query_result: list
    retry_count: int

    # Optional fields used during offline evaluation
    expected_result: list
    evaluation_mode: bool