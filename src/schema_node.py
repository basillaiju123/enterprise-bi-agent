from src.graph_state import AgentState
from src.retriever import retrieve_schema


def retrieve_schema_node(state: AgentState) -> AgentState:

    question = state["user_question"]

    schema_context = retrieve_schema(question)

    return {
        **state,
        "schema_context": schema_context,
    }