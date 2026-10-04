from groq import Groq
from dotenv import load_dotenv
import os


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def evaluate_sql(
    question: str,
    sql: str,
    schema_context: str,
) -> tuple[bool, str]:

    prompt = f"""
You are a SQL correctness evaluator.

Determine whether the SQL correctly answers the user's question.

USER QUESTION:
{question}

DATABASE AND BUSINESS CONTEXT:
{schema_context}

GENERATED SQL:
{sql}

Evaluate:
1. Does the SQL answer the user's question?
2. Does it use the appropriate tables?
3. Does it use the correct filters?
4. Does it apply the correct business definition?
5. Are joins logically appropriate?

Return exactly this format:

PASS
<short reason>

or

FAIL
<short reason>
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

    result = response.choices[0].message.content.strip()

    if result.startswith("PASS"):
        return True, result

    return False, result