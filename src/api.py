from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command

from src.graph import graph
from src.security.rbac import validate_role
from src.cost_tracker import get_usage_summary


app = FastAPI(
    title="Enterprise BI Agent",
    description="Agentic Text-to-SQL and Business Analytics API",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    role: str = "analyst"


class QueryResponse(BaseModel):
    question: str
    sql: str
    result: list
    error: str
    retries: int
    cache_hit: bool
    thread_id: str
    approval_required: bool
    approval_status: str
    token_usage: dict
    estimated_cost_usd: float
    estimated_cost_inr: float


class ApprovalRequest(BaseModel):
    approved: bool


@app.get("/")
def root():
    return {
        "name": "Enterprise BI Agent",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "enterprise-bi-agent",
    }


def _request_usage(thread_id: str) -> dict:
    totals = get_usage_summary(thread_id=thread_id)["totals"]
    return {
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "total_tokens": totals["total_tokens"],
        "llm_calls": totals["llm_calls"],
        "cost_usd": totals["cost_usd"],
        "cost_inr": totals["cost_inr"],
    }


@app.post("/query", response_model=QueryResponse)
def query_database(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if not validate_role(request.role):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.role}",
        )

    thread_id = str(uuid4())

    initial_state = {
        "user_question": request.question,
        "user_role": request.role,
        "schema_context": "",
        "generated_sql": "",
        "validation_error": "",
        "authorization_error": "",
        "execution_error": "",
        "query_result": [],
        "retry_count": 0,
        "expected_result": [],
        "evaluation_mode": False,
        "approval_required": False,
        "approval_status": "",
        "cache_hit": False,
        "cache_key": "",
        "thread_id": thread_id,
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(initial_state, config)
        error = (
            result.get("authorization_error", "")
            or result.get("execution_error", "")
            or result.get("validation_error", "")
        )
        usage = _request_usage(thread_id)

        return {
            "question": request.question,
            "sql": result.get("generated_sql", ""),
            "result": result.get("query_result", []),
            "error": error,
            "retries": result.get("retry_count", 0),
            "cache_hit": result.get("cache_hit", False),
            "thread_id": thread_id,
            "approval_required": result.get("approval_required", False),
            "approval_status": result.get("approval_status", ""),
            "token_usage": usage,
            "estimated_cost_usd": usage["cost_usd"],
            "estimated_cost_inr": usage["cost_inr"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}",
        )


@app.get("/usage")
def usage_summary(limit: int = Query(default=100, ge=1, le=500)):
    """Lifetime Groq usage totals and recent per-node API calls."""
    return get_usage_summary(limit=limit)


@app.post("/approve")
def approve_query(
    thread_id: str,
    request: ApprovalRequest,
):
    try:
        result = graph.invoke(
            Command(resume=request.approved),
            {"configurable": {"thread_id": thread_id}},
        )

        error = (
            result.get("authorization_error", "")
            or result.get("execution_error", "")
            or result.get("validation_error", "")
        )
        usage = _request_usage(thread_id)

        return {
            "thread_id": thread_id,
            "sql": result.get("generated_sql", ""),
            "result": result.get("query_result", []),
            "error": error,
            "approval_status": result.get("approval_status", ""),
            "approval_required": (
                False
                if result.get("approval_status") == "approved"
                else result.get("approval_required", False)
            ),
            "retries": result.get("retry_count", 0),
            "cache_hit": result.get("cache_hit", False),
            "token_usage": usage,
            "estimated_cost_usd": usage["cost_usd"],
            "estimated_cost_inr": usage["cost_inr"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Approval failed: {str(e)}",
        )
