import os

import duckdb
from dotenv import load_dotenv
from groq import Groq

from guardrails.validator import validate_sql


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DB_PATH = "data/sample_warehouse.duckdb"


SCHEMA = """
Database schema:

customers(
    customer_id INTEGER,
    customer_name VARCHAR,
    country VARCHAR,
    signup_date DATE
)

products(
    product_id INTEGER,
    product_name VARCHAR,
    category VARCHAR,
    price DOUBLE
)

orders(
    order_id INTEGER,
    customer_id INTEGER,
    order_date DATE,
    status VARCHAR
)

order_items(
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)
"""


def generate_sql(question: str, feedback: str = "") -> str:

    prompt = f"""
You are a SQL expert.

{SCHEMA}

Convert the following natural-language question into DuckDB SQL.

Question:
{question}

{feedback}

Rules:
- Return ONLY SQL.
- Use only SELECT statements.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Use the exact table and column names from the schema.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return response.choices[0].message.content.strip()


def execute_sql(sql: str):

    is_valid, message = validate_sql(sql)

    print("\nSQL Validation:")
    print(message)

    if not is_valid:
        return None, f"SQL rejected: {message}"

    con = duckdb.connect(DB_PATH)

    try:
        result = con.execute(sql).fetchall()
        return result, None

    except Exception as e:
        return None, str(e)

    finally:
        con.close()


question = input("Enter your question: ")

feedback = ""


for attempt in range(3):

    print(f"\n--- Attempt {attempt + 1} ---")

    sql = generate_sql(question, feedback)

    print("\nGenerated SQL:")
    print(sql)

    result, error = execute_sql(sql)

    if error:

        print("\nExecution Error:")
        print(error)

        feedback = f"""
The previous SQL failed with this error:

{error}

Generate corrected SQL.
"""

        continue


    print("\nResult:")

    for row in result:
        print(row)


    # Detect suspicious zero-result aggregate
    if (
        len(result) == 1
        and len(result[0]) == 1
        and result[0][0] == 0
    ):

        feedback = """
The SQL executed successfully, but the result was 0.

This may indicate that a filtering condition does not match
the actual database values.

Reconsider the SQL carefully.

Check:
- exact string values
- capitalization
- filtering conditions
- joins
- column names

Generate corrected SQL.
"""

        continue


    # Successful result
    break


else:

    print("\nUnable to obtain a valid result after 3 attempts.")
