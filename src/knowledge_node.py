from langfuse import observe

from src.graph_state import AgentState
from src.rag.retriever import retrieve_knowledge


@observe(name="retrieve_knowledge")
def retrieve_knowledge_node(state: AgentState) -> AgentState:

    question = state["user_question"]

    results = retrieve_knowledge(
        question,
        top_k=5,
    )

    context_parts = []

    for result in results:
        context_parts.append(
            f"""Knowledge Type: {result["type"]}
Source: {result["source"]}
Relevance Score: {result["score"]:.6f}

{result["text"]}
"""
        )

    combined_context = """
RETRIEVED KNOWLEDGE
===================

""" + "\n---\n".join(context_parts)

    return {
        **state,
        "schema_context": combined_context,
    }
