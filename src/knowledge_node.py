from langfuse import observe

from src.graph_state import AgentState
from src.rag.retriever import retrieve_knowledge
from src.rag.relevance import get_min_semantic_score, is_relevant_score


@observe(name="retrieve_knowledge")
def retrieve_knowledge_node(state: AgentState) -> AgentState:

    question = state["user_question"]

    results = retrieve_knowledge(
        question,
        top_k=5,
        schema_top_k=8,
    )

    relevance_score = (
        float(results[0]["query_max_semantic_score"])
        if results else 0.0
    )
    threshold = get_min_semantic_score()

    if not is_relevant_score(relevance_score, threshold):
        return {
            **state,
            "schema_context": "",
            "retrieval_relevant": False,
            "retrieval_score": relevance_score,
            "retrieval_error": (
                "This question does not appear to relate to the connected "
                "business database. Ask a question about the available "
                "customers, products, orders, sales, or business metrics."
            ),
        }

    schema_results = [
        result for result in results
        if result["type"] == "schema"
    ]
    supporting_results = [
        result for result in results
        if result["type"] != "schema"
    ]

    def format_results(items: list[dict]) -> str:
        return "\n---\n".join(
            f"""Knowledge Type: {result["type"]}
Source: {result["source"]}
Relevance Score: {result["score"]:.6f}

{result["text"]}
"""
            for result in items
        )

    combined_context = f"""
RETRIEVED DATABASE SCHEMA
=========================

{format_results(schema_results)}

RETRIEVED BUSINESS KNOWLEDGE AND SQL EXAMPLES
=============================================

{format_results(supporting_results)}
"""

    return {
        **state,
        "schema_context": combined_context,
        "retrieval_relevant": True,
        "retrieval_score": relevance_score,
        "retrieval_error": "",
    }
