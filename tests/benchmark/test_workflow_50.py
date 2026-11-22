"""50 deterministic LangGraph workflow/HITL decision tests.

Tests node and router behaviour directly with controlled AgentState inputs.
No graph checkpoint DB, Groq request, or external service is used.
"""
import pytest

from src.router import MAX_RETRIES, route_after_execution
from src.hitl_node import check_approval_required
from src.result_evaluation_node import evaluate_result_node
from src.evaluation_node import evaluate_sql_node


def state(**overrides):
    base = {
        "user_question": "Show customer details",
        "user_role": "analyst",
        "schema_context": "customers(customer_id, customer_name)",
        "generated_sql": "SELECT * FROM customers",
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
        "evaluation_replay": False,
        "replay_sql": "",
    }
    base.update(overrides)
    return base


ROUTER_CASES = [
    ({"authorization_error": "not allowed"}, "failure"),
    ({"authorization_error": "denied", "execution_error": "runtime"}, "failure"),
    ({"approval_status": "rejected"}, "failure"),
    ({"approval_status": "rejected", "retry_count": 0}, "failure"),
    ({"execution_error": "syntax", "retry_count": 0}, "retry"),
    ({"execution_error": "runtime", "retry_count": 1}, "retry"),
    ({"execution_error": "runtime", "retry_count": 2}, "retry"),
    ({"execution_error": "runtime", "retry_count": 3}, "failure"),
    ({"execution_error": "runtime", "retry_count": 4}, "failure"),
    ({"validation_error": "invalid SQL", "retry_count": 0}, "retry"),
    ({"validation_error": "invalid SQL", "retry_count": 1}, "retry"),
    ({"validation_error": "invalid SQL", "retry_count": 2}, "retry"),
    ({"validation_error": "invalid SQL", "retry_count": 3}, "failure"),
    ({"execution_error": "runtime", "validation_error": "invalid", "retry_count": 2}, "retry"),
    ({"execution_error": "runtime", "authorization_error": "denied", "retry_count": 0}, "failure"),
    ({"approval_status": "approved"}, "success"),
    ({"approval_status": "not_required"}, "success"),
    ({"retry_count": 0}, "success"),
    ({"retry_count": 1}, "success"),
    ({"retry_count": 3}, "success"),
    ({"authorization_error": "", "execution_error": "", "validation_error": ""}, "success"),
    ({"authorization_error": " ", "retry_count": 0}, "failure"),
    ({"execution_error": "error", "retry_count": MAX_RETRIES - 1}, "retry"),
    ({"execution_error": "error", "retry_count": MAX_RETRIES}, "failure"),
    ({"validation_error": "error", "retry_count": MAX_RETRIES + 1}, "failure"),
]


@pytest.mark.parametrize("overrides,expected", ROUTER_CASES)
def test_router_decision_matrix(overrides, expected):
    assert route_after_execution(state(**overrides)) == expected


HITL_CASES = [
    ("SELECT * FROM customers", True, False),
    ("SELECT customer_name FROM customers", True, False),
    ("SELECT customer_id FROM customers WHERE customer_id = 1", True, False),
    ("SELECT COUNT(*) FROM customers", False, False),
    ("SELECT SUM(price) FROM products", False, False),
    ("SELECT AVG(price) FROM products", False, False),
    ("SELECT MIN(price) FROM products", False, False),
    ("SELECT MAX(price) FROM products", False, False),
    ("SELECT COUNT(*) + SUM(price) FROM products", False, False),
    ("SELECT * FROM customers", False, True),
    ("not valid sql", True, False),
    ("", True, False),
    ("SELECT customer_name FROM customers", False, True),
    ("SELECT COUNT(*) FROM customers", False, True),
    ("SELECT * FROM orders", False, True),
]


@pytest.mark.parametrize("sql,expected_approval,evaluation_mode", HITL_CASES)
def test_hitl_approval_decision(sql, expected_approval, evaluation_mode):
    result = check_approval_required(
        state(generated_sql=sql, evaluation_mode=evaluation_mode)
    )
    assert result["approval_required"] is expected_approval
    if expected_approval:
        assert result["approval_status"] == "pending"
    else:
        assert result["approval_status"] == "not_required"


RESULT_CASES = [
    ([(1,)], [(1,)], True),
    ([(1,), (2,)], [(1,), (2,)], True),
    ([(1,), (2,)], [(2,), (1,)], True),
    ([], [], True),
    ([("Alice",)], [("Alice",)], True),
    ([(1, "A")], [(1, "A")], True),
    ([(1,)], [(2,)], False),
    ([(1,), (2,)], [(1,)], False),
    ([(1, "A")], [(1, "B")], False),
    ([(None,)], [(None,)], True),
]


@pytest.mark.parametrize("expected,actual,should_match", RESULT_CASES)
def test_result_evaluation_cases(expected, actual, should_match):
    result = evaluate_result_node(
        state(
            evaluation_mode=True,
            expected_result=expected,
            query_result=actual,
        )
    )
    if should_match:
        assert result["validation_error"] == ""
    else:
        assert result["validation_error"].startswith("Result mismatch.")


def test_non_evaluation_mode_skips_result_comparison():
    original = state(
        evaluation_mode=False,
        expected_result=[(1,)],
        query_result=[(2,)],
        validation_error="existing error",
    )
    result = evaluate_result_node(original)
    assert result is original
    assert result["validation_error"] == "existing error"


def test_evaluation_sql_node_avoids_judge_when_results_match(monkeypatch):
    def unexpected_llm_call(*args, **kwargs):
        raise AssertionError("LLM judge must not be called for matching results")

    monkeypatch.setattr("src.evaluation_node.evaluate_sql", unexpected_llm_call)

    result = evaluate_sql_node(
        state(
            evaluation_mode=True,
            expected_result=[(1,), (2,)],
            query_result=[(2,), (1,)],
        )
    )
    assert result["validation_error"] == ""


def test_evaluation_sql_node_uses_judge_for_non_evaluation_mode(monkeypatch):
    calls = []

    def fake_judge(question, sql, schema):
        calls.append((question, sql, schema))
        return True, ""

    monkeypatch.setattr("src.evaluation_node.evaluate_sql", fake_judge)

    result = evaluate_sql_node(state(evaluation_mode=False))

    assert len(calls) == 1
    assert result["validation_error"] == ""


def test_evaluation_sql_node_records_judge_feedback(monkeypatch):
    monkeypatch.setattr(
        "src.evaluation_node.evaluate_sql",
        lambda *args: (False, "Semantic mismatch"),
    )

    result = evaluate_sql_node(state(evaluation_mode=False))

    assert result["validation_error"] == "Semantic mismatch"


def test_benchmark_has_exactly_50_cases():
    assert len(ROUTER_CASES) == 25
    assert len(HITL_CASES) == 15
    assert len(RESULT_CASES) == 10
    assert len(ROUTER_CASES) + len(HITL_CASES) + len(RESULT_CASES) == 50
