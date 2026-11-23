"""Persistent token and cost accounting for Groq chat-completion calls."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_NAME = "openai/gpt-oss-20b"
INPUT_USD_PER_MILLION = float(os.getenv("GROQ_INPUT_USD_PER_MILLION", "0.075"))
OUTPUT_USD_PER_MILLION = float(os.getenv("GROQ_OUTPUT_USD_PER_MILLION", "0.30"))
USD_TO_INR = float(os.getenv("USD_TO_INR", "89"))
DB_PATH = Path(os.getenv("API_USAGE_DB_PATH", "data/api_usage.sqlite"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _cost(prompt_tokens: int, completion_tokens: int) -> tuple[float, float]:
    usd = (
        prompt_tokens * INPUT_USD_PER_MILLION
        + completion_tokens * OUTPUT_USD_PER_MILLION
    ) / 1_000_000
    return usd, usd * USD_TO_INR


def record_groq_usage(
    usage: Any,
    *,
    thread_id: str | None,
    node: str = "generate_sql",
    model: str = MODEL_NAME,
) -> dict:
    """Persist usage returned by the Groq SDK and return its cost breakdown."""
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(
        getattr(usage, "total_tokens", prompt_tokens + completion_tokens)
        or prompt_tokens + completion_tokens
    )
    cost_usd, cost_inr = _cost(prompt_tokens, completion_tokens)
    created_at = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS groq_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                node TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                cost_inr REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO groq_usage (
                created_at, thread_id, node, model, prompt_tokens,
                completion_tokens, total_tokens, cost_usd, cost_inr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                thread_id or "untracked",
                node,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost_usd,
                cost_inr,
            ),
        )

    return {
        "model": model,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 8),
        "cost_inr": round(cost_inr, 6),
        "pricing": {
            "input_usd_per_million": INPUT_USD_PER_MILLION,
            "output_usd_per_million": OUTPUT_USD_PER_MILLION,
            "usd_to_inr": USD_TO_INR,
        },
    }


def get_usage_summary(thread_id: str | None = None, limit: int = 100) -> dict:
    """Return lifetime totals, node breakdown, and recent usage events."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS groq_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                node TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                cost_inr REAL NOT NULL
            )
            """
        )
        where = "WHERE thread_id = ?" if thread_id else ""
        params = (thread_id,) if thread_id else ()
        totals = connection.execute(
            f"""
            SELECT COUNT(*) AS llm_calls,
                   COUNT(DISTINCT thread_id) AS tracked_queries,
                   COALESCE(SUM(prompt_tokens), 0) AS input_tokens,
                   COALESCE(SUM(completion_tokens), 0) AS output_tokens,
                   COALESCE(SUM(total_tokens), 0) AS total_tokens,
                   COALESCE(SUM(cost_usd), 0) AS cost_usd,
                   COALESCE(SUM(cost_inr), 0) AS cost_inr
            FROM groq_usage {where}
            """,
            params,
        ).fetchone()
        by_node = connection.execute(
            f"""
            SELECT node, COUNT(*) AS calls,
                   SUM(prompt_tokens) AS input_tokens,
                   SUM(completion_tokens) AS output_tokens,
                   SUM(total_tokens) AS total_tokens,
                   SUM(cost_usd) AS cost_usd,
                   SUM(cost_inr) AS cost_inr
            FROM groq_usage {where}
            GROUP BY node ORDER BY cost_usd DESC
            """,
            params,
        ).fetchall()
        recent = connection.execute(
            f"""
            SELECT created_at, thread_id, node, model, prompt_tokens,
                   completion_tokens, total_tokens, cost_usd, cost_inr
            FROM groq_usage {where}
            ORDER BY id DESC LIMIT ?
            """,
            (*params, max(1, min(int(limit), 500))),
        ).fetchall()

    return {
        "model": MODEL_NAME,
        "currency": "USD",
        "exchange_rate_usd_to_inr": USD_TO_INR,
        "pricing": {
            "input_usd_per_million": INPUT_USD_PER_MILLION,
            "output_usd_per_million": OUTPUT_USD_PER_MILLION,
        },
        "totals": {
            **dict(totals),
            "cost_usd": round(totals["cost_usd"], 8),
            "cost_inr": round(totals["cost_inr"], 6),
        },
        "by_node": [dict(row) for row in by_node],
        "recent": [dict(row) for row in recent],
    }
