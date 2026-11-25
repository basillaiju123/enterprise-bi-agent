"""Pure routing and response-status helpers for the BI agent."""


def route_after_retrieval(state: dict) -> str:
    """Reject irrelevant questions before cache validation or SQL generation."""
    if not state.get("retrieval_relevant", False):
        return "reject"
    if state.get("cache_hit", False):
        return "cached"
    return "generate"


def get_query_status(result: dict) -> str:
    """Map the final graph state to a stable API status."""
    if not result.get("retrieval_relevant", False):
        return "rejected"
    if result.get("approval_required", False):
        return "awaiting_approval"
    if (
        result.get("authorization_error")
        or result.get("execution_error")
        or result.get("validation_error")
    ):
        return "error"
    return "completed"
