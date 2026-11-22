from groq import Groq
from dotenv import load_dotenv
from langfuse import observe
import os

from src.graph_state import AgentState


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@observe(name="generate_sql")
def generate_sql_node(state: AgentState) -> AgentState:

    # ---------------------------------------------------------
    # Evaluation replay mode
    # ---------------------------------------------------------

    if state.get("evaluation_replay", False):

        replay_sql = state.get("replay_sql", "")

        if replay_sql:
            return {
                **state,
                "generated_sql": replay_sql,
            }

    # ---------------------------------------------------------
    # Normal SQL generation
    # ---------------------------------------------------------

    question = state["user_question"]
    retry_count = state["retry_count"]

    feedback = ""

    if retry_count > 0:
        feedback = f"""
This is correction attempt {retry_count}.

The previous SQL failed.

Previous SQL:
{state["generated_sql"]}

Execution error:
{state["execution_error"]}

Validation error:
{state["validation_error"]}

Generate corrected SQL. Fix the reported issue while preserving the
user's requested output columns and meaning. Do not repeat the same error.
"""

    prompt = f"""
You are an expert DuckDB SQL generation assistant.

DATABASE SCHEMA AND BUSINESS CONTEXT:
{state["schema_context"]}

USER QUESTION:
{question}

{feedback}

Generate one SQL query that answers the user's question.

STRICT RULES:
1. Return ONLY a valid DuckDB SQL query. Do not include Markdown fences,
   explanations, comments, or natural-language text.
2. Use SELECT statements only. CTEs (WITH ... SELECT ...) are allowed.
   Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or other
   data-modifying statements.
3. Use only tables and columns explicitly present in the database schema
   above. Never guess, invent, or assume a column exists.
4. If the question asks for a descriptive field such as a customer name,
   product name, or country, select that descriptive field. Join the
   appropriate related table using the schema's actual key relationships
   when necessary.
5. Return exactly the information requested. Do not add primary keys,
   foreign keys, IDs, or other columns unless the user explicitly asks
   for them or they are necessary to answer the question and requested
   output cannot be expressed without them.
6. For aggregation questions, use the correct aggregate function and
   GROUP BY the requested descriptive dimension(s). Do not include
   unrequested identifier columns in SELECT or GROUP BY.
7. Calculate derived measures only from available columns and their
   documented meaning. For example, calculate order-item revenue from
   quantity multiplied by the related product price when those columns
   exist. Do not assume a precomputed revenue column exists.
8. Apply every filter and condition stated in the question. Do not add
   unstated filters.
9. Use DISTINCT only when the question requests unique values or when
   joins would otherwise duplicate the requested entities.
10. Apply ORDER BY and LIMIT only when requested or clearly implied by
    wording such as "top", "highest", "lowest", "earliest", or "latest".
11. Use valid DuckDB date and string functions. Keep the result's
    granularity aligned with the question (for example, month grouping
    should return one consistent month representation).
12. When correcting a failed query, use the execution and validation
    feedback above, verify every referenced table and column against
    the schema, and preserve the intended output shape.

Before returning SQL, check:
- Every referenced table and column exists in the provided schema.
- Joins use the correct key relationships.
- The SELECT list contains only the requested output fields.
- Aggregations and filters match the user's wording.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    sql = response.choices[0].message.content.strip()

    return {
        **state,
        "generated_sql": sql,
    }
