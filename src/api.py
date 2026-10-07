from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from src.graph import graph
from src.security.rbac import validate_role


app = FastAPI(
    title="Enterprise BI Agent",
    description="Agentic Text-to-SQL and Business Analytics API",
    version="1.0.0",
)


# ---------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------

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


class ApprovalRequest(BaseModel):
    approved: bool


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

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
# ---------------------------------------------------------
# Query Endpoint
# ---------------------------------------------------------

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

    try:

        # -------------------------------------------------
        # Initial Agent State
        # -------------------------------------------------

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
        }

        # -------------------------------------------------
        # Create persistent LangGraph thread
        # -------------------------------------------------

        thread_id = str(uuid4())

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # -------------------------------------------------
        # Run Agent
        # -------------------------------------------------

        result = graph.invoke(
            initial_state,
            config,
        )

        # -------------------------------------------------
        # Error Handling
        # -------------------------------------------------

        error = (
            result.get("authorization_error", "")
            or result.get("execution_error", "")
            or result.get("validation_error", "")
        )

        # -------------------------------------------------
        # API Response
        # -------------------------------------------------

        return {
            "question": request.question,
            "sql": result.get("generated_sql", ""),
            "result": result.get("query_result", []),
            "error": error,
            "retries": result.get("retry_count", 0),
            "cache_hit": result.get("cache_hit", False),
            "thread_id": thread_id,
            "approval_required": result.get(
                "approval_required",
                False,
            ),
            "approval_status": result.get(
                "approval_status",
                "",
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}",
        )


# ---------------------------------------------------------
# Human Approval Endpoint
# ---------------------------------------------------------

@app.post("/approve")
def approve_query(
    thread_id: str,
    request: ApprovalRequest,
):

    try:

        result = graph.invoke(
            Command(
                resume=request.approved
            ),
            {
                "configurable": {
                    "thread_id": thread_id,
                }
            },
        )

        # -------------------------------------------------
        # Error Handling
        # -------------------------------------------------

        error = (
            result.get("authorization_error", "")
            or result.get("execution_error", "")
            or result.get("validation_error", "")
        )

        # -------------------------------------------------
        # Approval Response
        # -------------------------------------------------

        return {
            "thread_id": thread_id,
            "sql": result.get(
                "generated_sql",
                "",
            ),
            "result": result.get(
                "query_result",
                [],
            ),
            "error": error,
            "approval_status": result.get(
                "approval_status",
                "",
            ),
            "approval_required": (
            False
            if result.get("approval_status") == "approved"
            else result.get("approval_required", False)
            ),
            "retries": result.get(
                "retry_count",
                0,
            ),
            "cache_hit": result.get(
                "cache_hit",
                False,
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Approval failed: {str(e)}",
        )