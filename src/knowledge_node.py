from langfuse import observe

from src.graph_state import AgentState
from src.retriever import retrieve_schema
from src.business_retriever import retrieve_business_knowledge


@observe(name="retrieve_knowledge")
def retrieve_knowledge_node(state: AgentState) -> AgentState:

    question = state["user_question"]

    schema_context = retrieve_schema(question)
    business_context = retrieve_business_knowledge(question)

    combined_context = f"""
DATABASE SCHEMA CONTEXT
=======================

{schema_context}

BUSINESS KNOWLEDGE CONTEXT
==========================

{business_context}
"""

    return {
        **state,
        "schema_context": combined_context,
    }