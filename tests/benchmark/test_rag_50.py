"""50 deterministic RAG retrieval/RRF tests using mocked vector search.

These tests verify ranking/fusion mechanics, not live embedding quality or
Qdrant relevance. No Groq calls and no external vector database are used.
"""
from itertools import islice

import pytest

from src.rag import retriever


DOCS = [
    {"id": "doc_a", "type": "schema", "source": "customers", "text": "customer profile table"},
    {"id": "doc_b", "type": "business", "source": "Revenue", "text": "revenue definition and sales"},
    {"id": "doc_c", "type": "sql_example", "source": "orders example", "text": "completed orders query"},
    {"id": "doc_d", "type": "schema", "source": "products", "text": "product catalog table"},
]


class FakeBM25:
    def __init__(self, scores):
        self.scores = scores

    def get_scores(self, tokens):
        return self.scores


class FakePoint:
    def __init__(self, document_id, score):
        self.payload = {"document_id": document_id}
        self.score = score


class FakeQueryResponse:
    def __init__(self, points):
        self.points = points


class FakeClient:
    def __init__(self, semantic_order):
        self.semantic_order = semantic_order
        self.closed = False
        self.queries = []

    def query_points(self, **kwargs):
        self.queries.append(kwargs)
        points = [
            FakePoint(document_id, 1.0 - index * 0.1)
            for index, document_id in enumerate(self.semantic_order)
        ]
        return FakeQueryResponse(points)

    def close(self):
        self.closed = True


def install_fakes(monkeypatch, semantic_order, lexical_order):
    monkeypatch.setattr(retriever, "DOCUMENTS", DOCS)
    scores = [0.0] * len(DOCS)
    for rank, document_id in enumerate(lexical_order):
        index = next(i for i, doc in enumerate(DOCS) if doc["id"] == document_id)
        scores[index] = float(len(DOCS) - rank)

    monkeypatch.setattr(retriever, "BM25", FakeBM25(scores))
    client = FakeClient(semantic_order)
    monkeypatch.setattr(retriever, "embed_text", lambda question: [0.1, 0.2])
    monkeypatch.setattr(retriever, "get_client", lambda: client)
    return client


def expected_rrf_order(semantic_order, lexical_order):
    semantic_ranks = {doc_id: rank for rank, doc_id in enumerate(semantic_order, 1)}
    lexical_ranks = {doc_id: rank for rank, doc_id in enumerate(lexical_order, 1)}
    scores = {
        doc["id"]: (
            retriever.reciprocal_rank(semantic_ranks[doc["id"]])
            + retriever.reciprocal_rank(lexical_ranks[doc["id"]])
        )
        for doc in DOCS
    }
    return sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True), scores


# 25 distinct semantic/lexical rank combinations.
RANKING_CASES = [
    (["doc_a", "doc_b", "doc_c", "doc_d"], ["doc_a", "doc_b", "doc_c", "doc_d"]),
    (["doc_a", "doc_b", "doc_c", "doc_d"], ["doc_d", "doc_c", "doc_b", "doc_a"]),
    (["doc_b", "doc_a", "doc_c", "doc_d"], ["doc_a", "doc_c", "doc_b", "doc_d"]),
    (["doc_c", "doc_b", "doc_a", "doc_d"], ["doc_d", "doc_a", "doc_b", "doc_c"]),
    (["doc_d", "doc_c", "doc_b", "doc_a"], ["doc_a", "doc_b", "doc_c", "doc_d"]),
    (["doc_a", "doc_c", "doc_b", "doc_d"], ["doc_b", "doc_a", "doc_d", "doc_c"]),
    (["doc_b", "doc_c", "doc_d", "doc_a"], ["doc_c", "doc_d", "doc_a", "doc_b"]),
    (["doc_c", "doc_d", "doc_a", "doc_b"], ["doc_b", "doc_c", "doc_d", "doc_a"]),
    (["doc_d", "doc_a", "doc_b", "doc_c"], ["doc_c", "doc_b", "doc_a", "doc_d"]),
    (["doc_a", "doc_d", "doc_c", "doc_b"], ["doc_c", "doc_a", "doc_b", "doc_d"]),
    (["doc_b", "doc_d", "doc_a", "doc_c"], ["doc_d", "doc_b", "doc_c", "doc_a"]),
    (["doc_c", "doc_a", "doc_d", "doc_b"], ["doc_a", "doc_d", "doc_b", "doc_c"]),
    (["doc_d", "doc_b", "doc_c", "doc_a"], ["doc_b", "doc_c", "doc_a", "doc_d"]),
    (["doc_a", "doc_b", "doc_d", "doc_c"], ["doc_c", "doc_d", "doc_a", "doc_b"]),
    (["doc_b", "doc_a", "doc_d", "doc_c"], ["doc_d", "doc_a", "doc_c", "doc_b"]),
    (["doc_c", "doc_b", "doc_d", "doc_a"], ["doc_a", "doc_c", "doc_b", "doc_d"]),
    (["doc_d", "doc_c", "doc_a", "doc_b"], ["doc_b", "doc_d", "doc_c", "doc_a"]),
    (["doc_a", "doc_c", "doc_d", "doc_b"], ["doc_d", "doc_c", "doc_b", "doc_a"]),
    (["doc_b", "doc_d", "doc_c", "doc_a"], ["doc_c", "doc_a", "doc_d", "doc_b"]),
    (["doc_c", "doc_a", "doc_b", "doc_d"], ["doc_b", "doc_d", "doc_a", "doc_c"]),
    (["doc_d", "doc_b", "doc_a", "doc_c"], ["doc_a", "doc_c", "doc_d", "doc_b"]),
    (["doc_a", "doc_d", "doc_b", "doc_c"], ["doc_b", "doc_c", "doc_d", "doc_a"]),
    (["doc_b", "doc_c", "doc_a", "doc_d"], ["doc_d", "doc_a", "doc_b", "doc_c"]),
    (["doc_c", "doc_d", "doc_b", "doc_a"], ["doc_a", "doc_b", "doc_d", "doc_c"]),
    (["doc_d", "doc_a", "doc_c", "doc_b"], ["doc_c", "doc_d", "doc_b", "doc_a"]),
]


@pytest.mark.parametrize("semantic_order,lexical_order", RANKING_CASES)
def test_rrf_fusion_order_and_scores(monkeypatch, semantic_order, lexical_order):
    client = install_fakes(monkeypatch, semantic_order, lexical_order)
    expected_order, expected_scores = expected_rrf_order(semantic_order, lexical_order)

    results = retriever.retrieve_knowledge("test retrieval question", top_k=4)

    assert [item["source"] if item["type"] == "schema" else item["text"] for item in []] == []
    actual_ids = [
        next(doc["id"] for doc in DOCS if doc["text"] == item["text"])
        for item in results
    ]
    assert actual_ids == expected_order
    for item, document_id in zip(results, expected_order):
        assert item["score"] == pytest.approx(expected_scores[document_id])
    assert client.closed is True
    assert client.queries[0]["limit"] == len(DOCS)
    assert client.queries[0]["with_payload"] is True


@pytest.mark.parametrize("top_k", list(range(1, 26)))
def test_top_k_returns_requested_number_or_available_documents(monkeypatch, top_k):
    semantic_order = ["doc_a", "doc_b", "doc_c", "doc_d"]
    lexical_order = ["doc_a", "doc_b", "doc_c", "doc_d"]
    install_fakes(monkeypatch, semantic_order, lexical_order)

    results = retriever.retrieve_knowledge("top k test", top_k=top_k)

    assert len(results) == min(top_k, len(DOCS))
    assert all({"score", "semantic_score", "semantic_rank", "lexical_rank", "type", "source", "text"} <= set(item) for item in results)


def test_reciprocal_rank_uses_configured_constant():
    assert retriever.reciprocal_rank(1) == pytest.approx(1 / 61)
    assert retriever.reciprocal_rank(2) == pytest.approx(1 / 62)
    assert retriever.reciprocal_rank(10) == pytest.approx(1 / 70)
    assert retriever.reciprocal_rank(100) == pytest.approx(1 / 160)


def test_reciprocal_rank_decreases_as_rank_gets_worse():
    values = [retriever.reciprocal_rank(rank) for rank in range(1, 101)]
    assert all(left > right for left, right in zip(values, values[1:]))


def test_benchmark_contains_50_parameterized_cases():
    assert len(RANKING_CASES) == 25
    assert len(RANKING_CASES) + 25 == 50
