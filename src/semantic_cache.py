import sqlite3
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


CACHE_DB = Path("data/semantic_cache.sqlite")

MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.70

_model = None


def _get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def _get_connection():
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(CACHE_DB)


def initialize_cache():
    with _get_connection() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS query_cache (
                cache_key TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                role TEXT NOT NULL,
                sql TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """
        )


def make_cache_key(question: str, role: str) -> str:
    normalized = " ".join(question.lower().split())
    return f"{role.lower()}::{normalized}"


def _embed(text: str) -> np.ndarray:
    model = _get_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return np.asarray(
        embedding,
        dtype=np.float32,
    )


def get_cached_sql(question: str, role: str):
    initialize_cache()

    query_embedding = _embed(question)

    with _get_connection() as con:
        rows = con.execute(
            """
            SELECT question, sql, embedding
            FROM query_cache
            WHERE role = ?
            """,
            (role,),
        ).fetchall()

    best_sql = None
    best_similarity = -1.0

    for cached_question, sql, embedding_blob in rows:

        cached_embedding = np.frombuffer(
            embedding_blob,
            dtype=np.float32,
        )

        similarity = float(
            np.dot(
                query_embedding,
                cached_embedding,
            )
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_sql = sql

    if best_similarity >= SIMILARITY_THRESHOLD:
        return best_sql

    return None


def cache_sql(question: str, role: str, sql: str):
    initialize_cache()

    embedding = _embed(question)

    cache_key = make_cache_key(
        question,
        role,
    )

    with _get_connection() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO query_cache
            (cache_key, question, role, sql, embedding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cache_key,
                question,
                role,
                sql,
                embedding.tobytes(),
            ),
        )