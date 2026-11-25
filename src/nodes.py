from groq import Groq, RateLimitError, APITimeoutError
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
    timeout=60.0,
    max_retries=0,
)

MODEL_NAME = "openai/gpt-oss-20b"

MAX_RATE_LIMIT_RETRIES = 3
MAX_TIMEOUT_RETRIES = 1
MAX_TOTAL_RETRIES = 3
TIMEOUT_RETRY_DELAY = 2.0


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


RATE_LIMIT_RETRY_COUNT = 0
TIMEOUT_RETRY_COUNT = 0


def _generate_with_rate_limit_retry(prompt: str):
    global RATE_LIMIT_RETRY_COUNT
    global TIMEOUT_RETRY_COUNT

    rate_limit_retries = 0
    timeout_retries = 0
    total_retries = 0

    while True:
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
            )

        except APITimeoutError:
            if (
                timeout_retries >= MAX_TIMEOUT_RETRIES
                or total_retries >= MAX_TOTAL_RETRIES
            ):
                raise

            TIMEOUT_RETRY_COUNT += 1
            timeout_retries += 1
            total_retries += 1

            time.sleep(TIMEOUT_RETRY_DELAY)

        except RateLimitError as error:
            if "tokens per day (tpd)" in str(error).lower():
                raise

            if (
                rate_limit_retries >= MAX_RATE_LIMIT_RETRIES
                or total_retries >= MAX_TOTAL_RETRIES
            ):
                raise

            wait_seconds = _rate_limit_wait_seconds(
                error,
                rate_limit_retries,
            )

            RATE_LIMIT_RETRY_COUNT += 1
            rate_limit_retries += 1
            total_retries += 1

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

2. OUTPUT COLUMNS AND RESULT GRAIN
- Before writing SQL, determine the result grain: one row per entity, one row per group, one scalar aggregate, or one row per entity-and-period.
- Build the SELECT projection from the question's requested answer, not merely from columns convenient for filtering or joining.
- Return every requested output field and metric, in the order requested. Do not omit a requested dimension, descriptive attribute, or calculated metric.
- Return only those fields. Never expose join keys, internal IDs, or other columns used only for filtering/grouping unless the question asks for them.
- For "for each X" questions, include X and every requested measure. For ranked questions such as "which category has the highest revenue", return both the winning category and the metric used to rank it unless the user explicitly asks for the entity/name only.
- When a question asks to list or show matching records and mentions descriptive attributes that characterize those records (such as status, country, or date), include those attributes unless the wording explicitly requests names only. A customer/order ID supplied only as a filter is not an output field.
- For threshold questions about grouped entities (for example, customers with at least two orders), return the entity's requested display name and the qualifying count when the count is part of the condition. Do not return only its identifier.
- When a question asks for a count of distinct items within a group, count the distinct item identifier and return the count as a metric; do not list the individual item names instead.
- When a retrieved SQL example closely matches the user question and demonstrates the intended result grain and aggregation, follow that example unless the question explicitly requests a different output.
- For aggregate expressions, always use a descriptive snake_case alias. Derive the alias from the metric phrase in the question, preserving meaningful qualifiers such as status, time period, and entity. Do not discard a qualifier and fall back to a generic alias such as order_count when the question asks for completed or cancelled orders.
- Prefer the question's metric wording for aliases (for example, "average quantity" -> average_quantity, "latest order date" -> latest_order_date, and "maximum price" -> maximum_price).
- For product-category revenue ranking questions such as "Which product category has the highest total revenue?", use the canonical metric alias revenue (not total_revenue), consistent with the category-revenue SQL example. If no clear phrase exists, create the shortest unambiguous descriptive alias. Never leave database-generated names such as count_star() or sum(...).
- Do not rename ordinary dimension columns without a reason; a source column named status should normally remain status, not order_status.
- When grouping by an ordinary dimension such as orders.status, keep the source column name unchanged unless the user explicitly requests a different label.
- When the question requests multiple output fields, preserve their stated order in the SELECT projection; do not reorder dimensions for convenience.
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
- Average order value = revenue divided by the distinct order count for the population requested in the question.
- When calculating average order value, use average_order_value as the output alias, never avg_order_value.
- Apply a Completed status filter only when the question explicitly requests completed orders.
- If the question says all orders, include all order statuses unless another explicit condition restricts them.
- Keep the revenue numerator and distinct-order denominator consistent with the same requested population.

4. AGGREGATION AND FILTERS
- Apply every condition stated in the question.
- QUESTION SCOPE PRESERVATION:
  - Do not add status, date, country, category, or other filters unless explicitly requested or required by a documented business definition.
  - Do not assume that revenue, spending, or order-value questions refer only to completed orders.
  - Words such as "all", "each", and "every" must preserve the full population specified by the question.
  - Do not silently narrow the population using inferred business assumptions.
- AGGREGATION CORRECTNESS:
  - Identify the exact entity being counted or aggregated before choosing COUNT, SUM, or AVG.
  - Use COUNT(DISTINCT entity_id) when joins can multiply that entity.
  - Do not change the requested aggregation into a different metric.
  - Preserve the requested grouping dimensions and sort order when specified.
- For top-N rankings, use the requested metric in descending order and add the requested entity's display name as a deterministic secondary sort key when ties are possible.
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
