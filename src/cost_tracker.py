"""Persistent token and cost accounting for Groq chat-completion calls."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_NAME = "openai/gpt-oss-20b"
INPUT_USD_PER_MILLION = float(os.getenv("GROQ_INPUT_USD_PER_MILLION", "0.075"))
OUTPUT_USD_PER_MILLION = float(os.getenv("GROQ_OUTPUT_USD_PER_MILLION", "0.30"))
CACHED_INPUT_USD_PER_MILLION = float(
    os.getenv("GROQ_CACHED_INPUT_USD_PER_MILLION", "0.0375")
)
USD_TO_INR = float(os.getenv("USD_TO_INR", "89"))
DB_PATH = Path(os.getenv("API_USAGE_DB_PATH", "data/api_usage.sqlite"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _read_usage_value(obj: Any, key: str, default: int = 0) -> int:
    if isinstance(obj, dict):
        return int(obj.get(key, default) or default)
    return int(getattr(obj, key, default) or default)


def _cost(
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
) -> tuple[float, float]:
    cached_tokens = max(0, min(cached_tokens, prompt_tokens))
    uncached_tokens = prompt_tokens - cached_tokens
    usd = (
        uncached_tokens * INPUT_USD_PER_MILLION
        + cached_tokens * CACHED_INPUT_USD_PER_MILLION
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
    prompt_tokens = _read_usage_value(usage, "prompt_tokens")
    completion_tokens = _read_usage_value(usage, "completion_tokens")
    total_tokens = _read_usage_value(
        usage, "total_tokens", prompt_tokens + completion_tokens
    )
    prompt_details = (
        usage.get("prompt_tokens_details", {})
        if isinstance(usage, dict)
        else getattr(usage, "prompt_tokens_details", None)
    )
    cached_tokens = _read_usage_value(prompt_details, "cached_tokens")
    cost_usd, cost_inr = _cost(
        prompt_tokens, completion_tokens, cached_tokens
    )
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
                cached_tokens INTEGER NOT NULL DEFAULT 0,
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
                completion_tokens, cached_tokens, total_tokens, cost_usd, cost_inr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                thread_id or "untracked",
                node,
                model,
                prompt_tokens,
                completion_tokens,
                cached_tokens,
                total_tokens,
                cost_usd,
                cost_inr,
            ),
        )

    return {
        "model": model,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "cached_input_tokens": cached_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 8),
        "cost_inr": round(cost_inr, 6),
        "pricing": {
            "input_usd_per_million": INPUT_USD_PER_MILLION,
            "output_usd_per_million": OUTPUT_USD_PER_MILLION,
            "cached_input_usd_per_million": CACHED_INPUT_USD_PER_MILLION,
            "usd_to_inr": USD_TO_INR,
        },
    }


def record_query_outcome(thread_id: str, status: str) -> None:
    """Upsert the final lifecycle status for a tracked agent request."""
    if status not in {"success", "failed", "pending"}:
        raise ValueError("status must be success, failed, or pending")
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_runs (
                thread_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO query_runs (thread_id, status, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (thread_id, status, datetime.now(timezone.utc).isoformat()),
        )


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
                   COALESCE(SUM(cached_tokens), 0) AS cached_input_tokens,
                   COALESCE(SUM(total_tokens), 0) AS total_tokens,
                   COALESCE(SUM(cost_usd), 0) AS cost_usd,
                   COALESCE(SUM(cost_inr), 0) AS cost_inr
            FROM groq_usage {where}
            """,
            params,
        ).fetchone()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_runs (
                thread_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        outcome_where = "WHERE thread_id = ?" if thread_id else ""
        outcomes = connection.execute(
            f"""
            SELECT
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_queries,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_queries,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_queries
            FROM query_runs {outcome_where}
            """,
            params,
        ).fetchone()
        successful_cost = connection.execute(
            f"""
            SELECT COALESCE(SUM(g.cost_usd), 0) AS cost_usd,
                   COALESCE(SUM(g.cost_inr), 0) AS cost_inr
            FROM groq_usage g
            INNER JOIN query_runs q ON q.thread_id = g.thread_id
            WHERE q.status = 'success' {"AND g.thread_id = ?" if thread_id else ""}
            """,
            params,
        ).fetchone()
        by_node = connection.execute(
            f"""
            SELECT node, COUNT(*) AS calls,
                   SUM(prompt_tokens) AS input_tokens,
                   SUM(completion_tokens) AS output_tokens,
                   SUM(cached_tokens) AS cached_input_tokens,
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
                   completion_tokens, cached_tokens, total_tokens, cost_usd, cost_inr
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
            "cached_input_usd_per_million": CACHED_INPUT_USD_PER_MILLION,
        },
        "totals": {
            **dict(totals),
            "cost_usd": round(totals["cost_usd"], 8),
            "cost_inr": round(totals["cost_inr"], 6),
            "successful_queries": outcomes["successful_queries"] or 0,
            "failed_queries": outcomes["failed_queries"] or 0,
            "pending_queries": outcomes["pending_queries"] or 0,
            "successful_query_cost_usd": round(successful_cost["cost_usd"], 8),
            "successful_query_cost_inr": round(successful_cost["cost_inr"], 6),
            "average_cost_per_successful_query_inr": round(
                successful_cost["cost_inr"] / outcomes["successful_queries"], 6
            ) if outcomes["successful_queries"] else 0.0,
        },
        "by_node": [dict(row) for row in by_node],
        "recent": [dict(row) for row in recent],
    }
