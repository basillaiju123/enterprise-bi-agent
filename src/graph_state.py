from typing import TypedDict


class AgentState(TypedDict):
    user_question: str
    user_role: str
    schema_context: str
    generated_sql: str
    validation_error: str
    authorization_error: str
    execution_error: str
    query_result: list
    retry_count: int
    expected_result: list
    evaluation_mode: bool
    approval_required: bool
    approval_status: str
    cache_hit: bool
    cache_key: str