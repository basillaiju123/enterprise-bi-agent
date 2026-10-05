from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.graph import graph
from src.security.rbac import validate_role


app = FastAPI(
    title="Enterprise BI Agent",
    description="Agentic Text-to-SQL and Business Analytics API",
    version="1.0.0",
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


@app.get("/")
def root():
    return {
        "name": "Enterprise BI Agent",
        "status": "running",
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

    try:
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

        # Each API request gets its own LangGraph thread.
        config = {
            "configurable": {
                "thread_id": str(uuid4()),
            }
        }

        result = graph.invoke(
            initial_state,
            config,
        )

        error = (
            result.get("authorization_error", "")
            or result.get("execution_error", "")
            or result.get("validation_error", "")
        )

        return {
            "question": request.question,
            "sql": result["generated_sql"],
            "result": result["query_result"],
            "error": error,
            "retries": result["retry_count"],
            "cache_hit": result.get("cache_hit", False),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}",
        )