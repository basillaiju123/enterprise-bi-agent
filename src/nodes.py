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

    # Retrieved RAG context supplies the relevant schema, relationships,
    # categorical values, and business definitions.
    prompt = f"""
Generate one valid DuckDB SELECT query for the user's question.

DATABASE KNOWLEDGE:
{state["schema_context"]}

QUESTION:
{question}

{feedback}

SQL GENERATION RULES:

1. SCHEMA GROUNDING
- Use only tables, columns, values, and relationships explicitly supported by the database knowledge.
- Use exact column names. Never guess conventional names such as "name" when the schema specifies "customer_name" or "product_name".
- Use documented foreign-key relationships for joins.

2. OUTPUT COLUMNS
- Return exactly the fields requested by the user; do not add IDs or other unrequested columns.
- When a customer name is requested, select customers.customer_name and join customers through customer_id.
- When a product name is requested, select products.product_name and join products through product_id.
- Never substitute an ID for a requested name.

3. BUSINESS METRICS
- Revenue = SUM(order_items.quantity * products.price).
- Join order_items to products using product_id.
- For order-specific revenue, join orders to order_items using order_id.
- For customer-specific revenue, join customers to orders using customer_id, orders to order_items using order_id, and order_items to products using product_id.
- When filtering revenue by order status, apply the status filter on orders.
- Order quantity = SUM(order_items.quantity); do not confuse quantity with revenue.
- Never invent a revenue column or use SUM(quantity) as revenue.
- Average order value = completed-order revenue divided by COUNT(DISTINCT orders.order_id).

4. AGGREGATION AND FILTERS
- Apply every condition stated in the question.
- Group only by the requested dimensions.
- Use COUNT(DISTINCT orders.order_id) when joins to order_items could multiply order rows.
- Use categorical values and aliases documented in the retrieved knowledge, such as UK for United Kingdom.

5. DUCKDB DIALECT
- Generate DuckDB-compatible SQL only; do not use syntax or functions specific to another SQL dialect.
- For monthly grouping, use DATE_TRUNC('month', date_column).
- Do not use unsupported functions such as TO_CHAR().
- Use DuckDB-compatible date literals and date functions.

6. SAFETY AND FORMAT
- Output SQL only, without Markdown, explanations, or comments.
- Use only SELECT or WITH ... SELECT. Never modify database data.
- For correction attempts, fix the reported error while preserving the question's intended result.

Return SQL only.
"""

    response = _generate_with_rate_limit_retry(prompt)
    message = response.choices[0].message.content or ""
    sql = message.strip()

    return {
        **state,
        "generated_sql": sql,
    }
