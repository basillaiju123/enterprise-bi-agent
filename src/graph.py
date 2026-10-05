import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

from src.graph_state import AgentState

from src.cache_node import cache_lookup_node
from src.cache_store_node import cache_store_node

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


# ---------------------------------------------------------
# Build Graph
# ---------------------------------------------------------

builder = StateGraph(AgentState)


# ---------------------------------------------------------
# Nodes
# ---------------------------------------------------------

builder.add_node("cache_lookup", cache_lookup_node)
builder.add_node("cache_store", cache_store_node)

builder.add_node("retrieve_knowledge", retrieve_knowledge_node)
builder.add_node("generate_sql", generate_sql_node)
builder.add_node("validate_sql", validate_sql_node)

builder.add_node("check_approval", check_approval_required)
builder.add_node("approval", approval_node)

builder.add_node("execute_sql", execute_sql_node)

builder.add_node("evaluate_sql", evaluate_sql_node)
builder.add_node("evaluate_result", evaluate_result_node)

builder.add_node("correction", correction_node)


# ---------------------------------------------------------
# START → Cache Lookup
# ---------------------------------------------------------

builder.add_edge(
    START,
    "cache_lookup",
)


# ---------------------------------------------------------
# Cache Lookup
#
# HIT  → Skip RAG + LLM
# MISS → Normal RAG + LLM pipeline
# ---------------------------------------------------------

builder.add_conditional_edges(
    "cache_lookup",
    lambda state: (
        "hit"
        if state["cache_hit"]
        else "miss"
    ),
    {
        "hit": "validate_sql",
        "miss": "retrieve_knowledge",
    },
)


# ---------------------------------------------------------
# RAG → LLM
# ---------------------------------------------------------

builder.add_edge(
    "retrieve_knowledge",
    "generate_sql",
)

builder.add_edge(
    "generate_sql",
    "validate_sql",
)


# ---------------------------------------------------------
# Validation → HITL Check
# ---------------------------------------------------------

builder.add_edge(
    "validate_sql",
    "check_approval",
)


# ---------------------------------------------------------
# HITL Routing
#
# Risky query → Human approval
# Safe query  → Execution
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Human Approval → Execution
# ---------------------------------------------------------

builder.add_edge(
    "approval",
    "execute_sql",
)


# ---------------------------------------------------------
# Execution → Evaluation
# ---------------------------------------------------------

builder.add_edge(
    "execute_sql",
    "evaluate_sql",
)

builder.add_edge(
    "evaluate_sql",
    "evaluate_result",
)


# ---------------------------------------------------------
# Result Evaluation
#
# Successful safe query → Cache
# Failed query           → Retry / Failure
# ---------------------------------------------------------

builder.add_conditional_edges(
    "evaluate_result",
    lambda state: (
        "cache"
        if not state["execution_error"]
        and not state.get("approval_required", False)
        else route_after_execution(state)
    ),
    {
        "cache": "cache_store",
        "success": END,
        "retry": "correction",
        "failure": END,
    },
)


# ---------------------------------------------------------
# Cache Store → END
# ---------------------------------------------------------

builder.add_edge(
    "cache_store",
    END,
)


# ---------------------------------------------------------
# Correction → Regenerate SQL
# ---------------------------------------------------------

builder.add_edge(
    "correction",
    "generate_sql",
)


# ---------------------------------------------------------
# SQLite Checkpointing
# ---------------------------------------------------------

connection = sqlite3.connect(
    "data/hitl_checkpoints.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    connection
)


# ---------------------------------------------------------
# Compile Graph
# ---------------------------------------------------------

graph = builder.compile(
    checkpointer=checkpointer
)