import sqlglot
from sqlglot import exp

from src.graph_state import AgentState


def check_approval_required(state: AgentState) -> AgentState:

    # Evaluation runs must be fully autonomous.
    # Do not interrupt the benchmark for human approval.
    if state.get("evaluation_mode", False):
        return {
            **state,
            "approval_required": False,
            "approval_status": "not_required",
        }

    sql = state["generated_sql"]

    try:
        parsed = sqlglot.parse_one(
            sql,
            read="duckdb",
        )

        has_aggregate = any(
            isinstance(
                node,
                (
                    exp.Count,
                    exp.Sum,
                    exp.Avg,
                    exp.Min,
                    exp.Max,
                ),
            )
            for node in parsed.walk()
        )

        if not has_aggregate:
            return {
                **state,
                "approval_required": True,
                "approval_status": "pending",
            }

        return {
            **state,
            "approval_required": False,
            "approval_status": "not_required",
        }

    except Exception:
        return {
            **state,
            "approval_required": True,
            "approval_status": "pending",
        }