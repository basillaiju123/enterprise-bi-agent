import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
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
from src.hitl_node import check_approval_required
from src.approval_node import approval_node


builder = StateGraph(AgentState)

builder.add_node("retrieve_knowledge", retrieve_knowledge_node)
builder.add_node("generate_sql", generate_sql_node)
builder.add_node("validate_sql", validate_sql_node)
builder.add_node("check_approval", check_approval_required)
builder.add_node("approval", approval_node)
builder.add_node("execute_sql", execute_sql_node)
builder.add_node("evaluate_sql", evaluate_sql_node)
builder.add_node("evaluate_result", evaluate_result_node)
builder.add_node("correction", correction_node)

builder.add_edge(START, "retrieve_knowledge")
builder.add_edge("retrieve_knowledge", "generate_sql")
builder.add_edge("generate_sql", "validate_sql")
builder.add_edge("validate_sql", "check_approval")

builder.add_conditional_edges(
    "check_approval",
    lambda state: (
        "approval"
        if state["approval_required"]
        else "execute"
    ),
    {
        "approval": "approval",
        "execute": "execute_sql",
    },
)

builder.add_edge("approval", "execute_sql")
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


connection = sqlite3.connect(
    "data/hitl_checkpoints.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(connection)

graph = builder.compile(checkpointer=checkpointer)