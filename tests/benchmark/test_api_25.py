"""Deterministic FastAPI endpoint benchmark cases; no external services or LLM calls."""

import pytest
from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


@pytest.mark.parametrize("role", ["admin", "analyst", "viewer"])
def test_query_accepts_each_supported_role(monkeypatch, role):
    captured = {}

    def fake_invoke(state, config=None):
        captured["state"] = state
        return {"generated_sql": "SELECT 1", "query_result": [(1,)]}

    monkeypatch.setattr("src.api.graph.invoke", fake_invoke)
    response = client.post("/query", json={"question": "Return one", "role": role})

    assert response.status_code == 200
    assert captured["state"]["user_role"] == role
    assert response.json()["result"] == [[1]]


@pytest.mark.parametrize("question", ["", "   ", "\t\n"])
def test_query_rejects_blank_questions(monkeypatch, question):
    monkeypatch.setattr(
        "src.api.graph.invoke",
        lambda *args, **kwargs: pytest.fail("Graph must not run for blank input"),
    )
    response = client.post("/query", json={"question": question})
    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


@pytest.mark.parametrize("role", ["guest", "Viewer", ""])
def test_query_rejects_unsupported_roles(monkeypatch, role):
    monkeypatch.setattr(
        "src.api.graph.invoke",
        lambda *args, **kwargs: pytest.fail("Graph must not run for invalid role"),
    )
    response = client.post("/query", json={"question": "Show customers", "role": role})
    assert response.status_code == 400
    assert response.json()["detail"] == f"Invalid role: {role}"


@pytest.mark.parametrize(
    "payload",
    [{}, {"question": None}, {"question": 123}],
)
def test_query_validates_question_payload(payload):
    response = client.post("/query", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "graph_result, expected_error",
    [
        ({"authorization_error": "Access denied", "execution_error": "DB error"}, "Access denied"),
        ({"execution_error": "DB unavailable", "validation_error": "Bad SQL"}, "DB unavailable"),
        ({"validation_error": "Only SELECT allowed"}, "Only SELECT allowed"),
    ],
)
def test_query_maps_graph_errors_to_response(monkeypatch, graph_result, expected_error):
    monkeypatch.setattr("src.api.graph.invoke", lambda *args, **kwargs: graph_result)
    response = client.post("/query", json={"question": "Run report"})

    assert response.status_code == 200
    assert response.json()["error"] == expected_error


def test_query_converts_graph_exception_to_http_500(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("controlled test failure")

    monkeypatch.setattr("src.api.graph.invoke", fail)
    response = client.post("/query", json={"question": "Run report"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Agent execution failed: controlled test failure"


def test_query_returns_approval_state(monkeypatch):
    monkeypatch.setattr(
        "src.api.graph.invoke",
        lambda *args, **kwargs: {
            "generated_sql": "SELECT name FROM customers",
            "approval_required": True,
            "approval_status": "pending",
        },
    )
    response = client.post("/query", json={"question": "List customer names"})

    assert response.status_code == 200
    assert response.json()["approval_required"] is True
    assert response.json()["approval_status"] == "pending"


def test_query_generates_distinct_thread_ids(monkeypatch):
    monkeypatch.setattr(
        "src.api.graph.invoke",
        lambda *args, **kwargs: {"generated_sql": "SELECT 1"},
    )
    first = client.post("/query", json={"question": "First"}).json()["thread_id"]
    second = client.post("/query", json={"question": "Second"}).json()["thread_id"]

    assert first
    assert second
    assert first != second


def test_query_response_contains_contract_fields(monkeypatch):
    monkeypatch.setattr(
        "src.api.graph.invoke",
        lambda *args, **kwargs: {"generated_sql": "SELECT 1"},
    )
    data = client.post("/query", json={"question": "Check response"}).json()

    expected = {
        "question", "sql", "result", "error", "retries", "cache_hit",
        "thread_id", "approval_required", "approval_status",
    }
    assert set(data) == expected


@pytest.mark.parametrize("approved", [True, False])
def test_approval_endpoint_resumes_with_boolean(monkeypatch, approved):
    captured = {}

    def fake_invoke(command, config=None):
        captured["command"] = command
        captured["config"] = config
        return {
            "generated_sql": "SELECT COUNT(*) FROM customers",
            "query_result": [(4,)],
            "approval_status": "approved" if approved else "rejected",
            "approval_required": not approved,
            "retry_count": 0,
            "cache_hit": False,
        }

    monkeypatch.setattr("src.api.graph.invoke", fake_invoke)
    response = client.post(
        "/approve?thread_id=benchmark-thread",
        json={"approved": approved},
    )

    assert response.status_code == 200
    assert captured["config"]["configurable"]["thread_id"] == "benchmark-thread"
    assert captured["command"].resume is approved
    assert response.json()["approval_status"] == ("approved" if approved else "rejected")


def test_approval_endpoint_handles_graph_exception(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("resume failed")

    monkeypatch.setattr("src.api.graph.invoke", fail)
    response = client.post(
        "/approve?thread_id=benchmark-thread",
        json={"approved": True},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Approval failed: resume failed"


def test_approval_requires_thread_id():
    response = client.post("/approve", json={"approved": True})
    assert response.status_code == 422


def test_approval_rejects_non_boolean_value():
    response = client.post(
        "/approve?thread_id=benchmark-thread",
        json={"approved": "not-a-boolean"},
    )
    assert response.status_code == 422


def test_query_defaults_role_to_analyst(monkeypatch):
    captured = {}

    def fake_invoke(state, config=None):
        captured["role"] = state["user_role"]
        return {"generated_sql": "SELECT 1"}

    monkeypatch.setattr("src.api.graph.invoke", fake_invoke)
    response = client.post("/query", json={"question": "Default role"})

    assert response.status_code == 200
    assert captured["role"] == "analyst"


