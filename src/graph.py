from langgraph.graph import StateGraph, START, END

from src.graph_state import AgentState
from src.knowledge_node import retrieve_knowledge_node
from src.nodes import generate_sql_node
from src.validation_node import validate_sql_node
from src.execution_node import execute_sql_node
from src.router import route_after_execution
from src.correction_node import correction_node
from src.evaluation_node import evaluate_sql_node
from src.result_evaluation_node import evaluate_result_node

builder = StateGraph(AgentState)
builder.add_node("evaluate_sql", evaluate_sql_node)
builder.add_node("retrieve_knowledge", retrieve_knowledge_node)
builder.add_node("generate_sql", generate_sql_node)
builder.add_node("evaluate_result", evaluate_result_node)



builder.add_node("validate_sql", validate_sql_node)
builder.add_node("execute_sql", execute_sql_node)
builder.add_node("correction", correction_node)

builder.add_edge(START, "retrieve_knowledge")
builder.add_edge("retrieve_knowledge", "generate_sql")
builder.add_edge("generate_sql", "validate_sql")
builder.add_edge("validate_sql", "execute_sql")
builder.add_edge("execute_sql", "evaluate_sql")
builder.add_edge("evaluate_sql", "evaluate_result")
builder.add_conditional_edges(
    "evaluate_result",
    route_after_execution,
    {
        "success": END,
        "retry": "correction",
        "failure": END,
    },
)

builder.add_edge("correction", "generate_sql")

graph = builder.compile()