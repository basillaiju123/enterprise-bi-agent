from groq import Groq, RateLimitError
from dotenv import load_dotenv
from langfuse import observe
import os
import re
import time

from src.graph_state import AgentState


load_dotenv()

# Disable SDK-level retries so the bounded retry policy below is predictable.
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    max_retries=0,
)

MODEL_NAME = "openai/gpt-oss-20b"
MAX_RATE_LIMIT_RETRIES = 3


def _rate_limit_wait_seconds(error: RateLimitError, attempt: int) -> float:
    """Read Groq's suggested wait from the error, else use bounded backoff."""
    message = str(error)
    match = re.search(
        r"try again in\s+([0-9.]+)\s*(ms|milliseconds|s|seconds|minutes)",
        message,
        re.IGNORECASE,
    )
    if match:
        amount = float(match.group(1))
        unit = match.group(2).lower()
        multiplier = 0.001 if unit in {"ms", "milliseconds"} else 60 if unit == "minutes" else 1
        return min(amount * multiplier, 30.0)

    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return min(max(float(retry_after), 0.0), 30.0)
        except (TypeError, ValueError):
            pass

    return min(2 ** attempt, 8.0)


def _generate_with_rate_limit_retry(prompt: str):
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
            )
        except RateLimitError as error:
            if attempt >= MAX_RATE_LIMIT_RETRIES:
                raise
            wait_seconds = _rate_limit_wait_seconds(error, attempt)
            time.sleep(wait_seconds)


@observe(name="generate_sql")
def generate_sql_node(state: AgentState) -> AgentState:

    # Evaluation replay mode
    if state.get("evaluation_replay", False):
        replay_sql = state.get("replay_sql", "")
        if replay_sql:
            return {**state, "generated_sql": replay_sql}

    question = state["user_question"]
    retry_count = state["retry_count"]

    feedback = ""
    if retry_count > 0:
        feedback = f"""
CORRECTION FEEDBACK
Previous SQL: {state["generated_sql"]}
Execution error: {state["execution_error"]}
Validation error: {state["validation_error"]}
Fix the reported issue. Preserve the requested output columns and meaning.
"""

    # Keep instructions concise; retrieved RAG context supplies schema,
    # relationships, and business definitions relevant to this question.
    prompt = f"""
Generate one valid DuckDB SELECT query for the user's question.

RETRIEVED DATABASE KNOWLEDGE:
{state["schema_context"]}

QUESTION:
{question}

{feedback}

RULES:
- Output SQL only; no Markdown, explanation, or comments.
- Use only tables, columns, values, and relationships supported by the retrieved knowledge.
- Return exactly the requested fields. If a name is requested, select the name and join its table; do not substitute an ID.
- For customer names, join customers through customer_id. For product names, join products through product_id.
- Revenue means SUM(order_items.quantity * products.price), joining order_items to products and, when filtering by order status, joining orders by order_id. Never use quantity alone as revenue or invent a revenue column.
- Average order value means completed-order revenue divided by COUNT(DISTINCT orders.order_id).
- Order quantity means SUM(order_items.quantity); do not confuse it with revenue.
- Count orders with COUNT(DISTINCT orders.order_id) when joins to order_items could multiply rows.
- Apply every stated filter. Use stored categorical values from retrieved knowledge when available (for example, UK may be the stored value for United Kingdom).
- Group only by the requested dimensions; do not add unrequested IDs to the output.
- Use only SELECT or WITH ... SELECT. Never modify database data.
- For correction attempts, fix the reported error without changing the question's intended result.
"""

    response = _generate_with_rate_limit_retry(prompt)
    message = response.choices[0].message.content or ""
    sql = message.strip()

    return {
        **state,
        "generated_sql": sql,
    }
