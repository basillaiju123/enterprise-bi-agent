from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_empty_question():
    response = client.post(
        "/query",
        json={"question": ""},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


def test_valid_query():
    response = client.post(
        "/query",
        json={
            "question": "How many customers are from India?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] == ""
    assert data["result"] == [[2]]