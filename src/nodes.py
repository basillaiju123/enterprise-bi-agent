from groq import Groq
from dotenv import load_dotenv
from langfuse import observe
import os

from src.graph_state import AgentState


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@observe(name="generate_sql")
def generate_sql_node(state: AgentState) -> AgentState:

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

Generate corrected SQL.
"""

    prompt = f"""
You are a SQL expert.

Relevant database information:

{state["schema_context"]}

Convert the following natural-language question into DuckDB SQL.

Question:
{question}

{feedback}

Rules:
- Return ONLY SQL.
- Use only SELECT statements.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Use the exact table and column names from the provided database information.
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