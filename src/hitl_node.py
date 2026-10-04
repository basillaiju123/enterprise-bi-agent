import sqlglot
from sqlglot import exp

from src.graph_state import AgentState


def check_approval_required(state: AgentState) -> AgentState:
    sql = state["generated_sql"]

    try:
        parsed = sqlglot.parse_one(sql, read="duckdb")

        # Aggregate queries are considered low-risk.
        has_aggregate = any(
            isinstance(node, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max))
            for node in parsed.walk()
        )

        # Direct row-level retrieval requires human approval.
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