"""50 deterministic semantic-cache tests with temporary SQLite and fake embeddings.

No SentenceTransformer model download, Groq call, or external service is used.
These validate cache behavior, not production latency or semantic-model quality.
"""
import numpy as np
import pytest

from src import semantic_cache


KEY_CASES = [
    ("Show Customers", "viewer", "viewer::show customers"),
    (" show customers ", "viewer", "viewer::show customers"),
    ("SHOW CUSTOMERS", "viewer", "viewer::show customers"),
    ("Show   Customers", "viewer", "viewer::show customers"),
    ("\nShow Customers\t", "viewer", "viewer::show customers"),
    ("Revenue", "analyst", "analyst::revenue"),
    (" REVENUE ", "analyst", "analyst::revenue"),
    ("Total Revenue", "analyst", "analyst::total revenue"),
    ("total   revenue", "analyst", "analyst::total revenue"),
    ("Orders Completed", "admin", "admin::orders completed"),
    (" orders completed ", "admin", "admin::orders completed"),
    ("Customer Count", "viewer", "viewer::customer count"),
    ("customer count", "viewer", "viewer::customer count"),
    ("Product Sales", "analyst", "analyst::product sales"),
    (" product sales ", "analyst", "analyst::product sales"),
    ("Average Order Value", "admin", "admin::average order value"),
    ("average order value", "admin", "admin::average order value"),
    ("Show Orders", "analyst", "analyst::show orders"),
    (" show orders ", "analyst", "analyst::show orders"),
    ("List Products", "viewer", "viewer::list products"),
    ("LIST PRODUCTS", "viewer", "viewer::list products"),
    ("Cancelled Orders", "admin", "admin::cancelled orders"),
    (" cancelled   orders ", "admin", "admin::cancelled orders"),
    ("Revenue By Country", "analyst", "analyst::revenue by country"),
    (" revenue by country ", "analyst", "analyst::revenue by country"),
]


SIMILARITY_CASES = [
    (f"similar query {i:02d}", True) if i % 2 == 0
    else (f"different query {i:02d}", False)
    for i in range(25)
]


def configure_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(semantic_cache, "CACHE_DB", tmp_path / "cache.sqlite")

    def fake_embed(text):
        if text.startswith("different query"):
            return np.array([0.0, 1.0], dtype=np.float32)
        return np.array([1.0, 0.0], dtype=np.float32)

    monkeypatch.setattr(semantic_cache, "_embed", fake_embed)


@pytest.mark.parametrize("question,role,expected_key", KEY_CASES)
def test_cache_key_normalization(question, role, expected_key):
    assert semantic_cache.make_cache_key(question, role) == expected_key


@pytest.mark.parametrize("query,should_hit", SIMILARITY_CASES)
def test_cache_similarity_threshold_and_retrieval(
    monkeypatch, tmp_path, query, should_hit
):
    configure_cache(monkeypatch, tmp_path)

    semantic_cache.cache_sql(
        question="reference question",
        role="analyst",
        sql="SELECT * FROM customers",
    )

    result = semantic_cache.get_cached_sql(query, "analyst")

    if should_hit:
        assert result == "SELECT * FROM customers"
    else:
        assert result is None


def test_cache_is_role_scoped(monkeypatch, tmp_path):
    configure_cache(monkeypatch, tmp_path)
    semantic_cache.cache_sql("reference question", "analyst", "SELECT 1")

    assert semantic_cache.get_cached_sql("reference question", "viewer") is None
    assert semantic_cache.get_cached_sql("reference question", "analyst") == "SELECT 1"


def test_cache_replaces_existing_key(monkeypatch, tmp_path):
    configure_cache(monkeypatch, tmp_path)
    semantic_cache.cache_sql("same question", "analyst", "SELECT 1")
    semantic_cache.cache_sql("same question", "analyst", "SELECT 2")

    assert semantic_cache.get_cached_sql("same question", "analyst") == "SELECT 2"


def test_cache_does_not_return_below_threshold(monkeypatch, tmp_path):
    configure_cache(monkeypatch, tmp_path)
    semantic_cache.cache_sql("reference question", "analyst", "SELECT 1")

    monkeypatch.setattr(
        semantic_cache,
        "_embed",
        lambda text: np.array([0.6, 0.8], dtype=np.float32),
    )

    assert semantic_cache.get_cached_sql("unrelated question", "analyst") is None


def test_cache_accepts_similarity_at_threshold(monkeypatch, tmp_path):
    configure_cache(monkeypatch, tmp_path)
    semantic_cache.cache_sql("reference question", "analyst", "SELECT 1")

    monkeypatch.setattr(
        semantic_cache,
        "_embed",
        lambda text: np.array([0.70, (1 - 0.70**2) ** 0.5], dtype=np.float64),
    )

    assert semantic_cache.get_cached_sql("boundary question", "analyst") == "SELECT 1"


def test_cache_table_is_created_in_temporary_database(monkeypatch, tmp_path):
    configure_cache(monkeypatch, tmp_path)
    semantic_cache.initialize_cache()

    import sqlite3
    with sqlite3.connect(semantic_cache.CACHE_DB) as con:
        columns = {
            row[1] for row in con.execute("PRAGMA table_info(query_cache)")
        }

    assert {"cache_key", "question", "role", "sql", "embedding"} <= columns


def test_benchmark_has_exactly_50_cases():
    assert len(KEY_CASES) == 25
    assert len(SIMILARITY_CASES) == 25
    assert len(KEY_CASES) + len(SIMILARITY_CASES) == 50
