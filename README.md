# Enterprise BI Agent

An agentic Text-to-SQL and business analytics platform that allows users to query structured business data using natural language.

The system combines **LLM-based SQL generation, RAG, LangGraph orchestration, SQL guardrails, automatic self-correction, evaluation, observability, FastAPI, Docker, and CI/CD**.

## Architecture

```text
User Question
      ↓
Query Understanding
      ↓
Schema + Business Knowledge Retrieval
      ↓
SQL Generation
      ↓
SQL Guardrails
      ↓
DuckDB Execution
      ↓
SQL + Result Evaluation
      ↓
   Success
      │
      └──────── Failure
                  ↓
            Self-Correction
                  ↓
             Retry SQL
                  │
                  └── Max 3 retries
Key Features
Natural-language to SQL generation
Schema and business-knowledge retrieval
Stateful LangGraph workflow
SQLGlot SQL validation and safety guardrails
Automatic SQL self-correction with retry limits
Semantic SQL evaluation
Exact query-result evaluation
Langfuse observability
FastAPI REST API
Docker deployment
Pytest test suite
GitHub Actions CI/CD
Tech Stack
Component	Technology
Language	Python
LLM	Groq — GPT-OSS-20B
Agent Orchestration	LangGraph
Database	DuckDB
SQL Validation	SQLGlot
RAG	Schema + Business Knowledge Retrieval
Observability	Langfuse
API	FastAPI
Testing	Pytest
Deployment	Docker
CI/CD	GitHub Actions
How It Works
1. Knowledge Retrieval

Before generating SQL, the agent retrieves relevant database schema information and business definitions.

Examples of business definitions include:

Revenue
Completed orders
Cancelled orders
Order quantity
Average order value

This gives the LLM both database structure and business context.

2. SQL Generation

The LLM converts the user's natural-language question into DuckDB SQL using the retrieved context.

Example:

Question:
How many customers are from India?

Generated SQL:
SELECT COUNT(*) AS num_customers
FROM customers
WHERE country = 'India';
3. SQL Guardrails

Generated SQL is validated using SQLGlot before execution.

The current implementation:

Allows only a single SQL statement
Allows only SELECT queries
Rejects INSERT
Rejects UPDATE
Rejects DELETE
Rejects DROP
Rejects ALTER
Rejects CREATE

This prevents the agent from executing destructive database operations.

4. SQL Execution

Validated SQL is executed against a DuckDB business database.

The sample database contains:

Customers
Products
Orders
Order items
5. Self-Correction

If SQL execution or evaluation fails, the workflow feeds the error back into the SQL generation node.

The agent can retry up to three times before returning a failure.

SQL Generation
      ↓
Validation
      ↓
Execution
      ↓
Failure?
   ↙       ↘
 Yes        No
 ↓           ↓
Correction  Success
 ↓
Retry
6. Evaluation

The project uses two levels of evaluation:

Semantic SQL Evaluation

An LLM-based evaluator checks whether the generated SQL correctly addresses the user's question.

Exact Query-Result Evaluation

The actual database result is compared against the expected result.

This prevents semantically plausible but numerically incorrect SQL from being treated as correct.

Evaluation

The initial benchmark contains 6 synthetic business questions covering:

Customer queries
Product filtering
Aggregation
Order status
Customer/order joins
Revenue calculation
Current Development Benchmark
Execution accuracy:       6/6
Result validation:        6/6
Semantic evaluation:     6/6
Fully passed:             6/6
Overall:                 100%

This benchmark is based on a small synthetic dataset and should not be interpreted as production-level accuracy.

API

Start the FastAPI server:

uvicorn src.api:app --host 0.0.0.0 --port 8000

Open Swagger UI:

http://localhost:8000/docs

Example Request
{
  "question": "How many customers are from India?"
}
Example Response
{
  "question": "How many customers are from India?",
  "sql": "SELECT COUNT(*) AS num_customers FROM customers WHERE country = 'India';",
  "result": [[2]],
  "error": "",
  "retries": 0
}
Docker

Build the image:

docker build -t enterprise-bi-agent .

Run the container:

docker run --rm --env-file .env -p 8000:8000 enterprise-bi-agent

Then open:

http://localhost:8000/docs

Testing

Run the automated test suite:

pytest -q tests

The test suite covers:

SQL safety guardrails
Multiple-statement rejection
Destructive SQL rejection
FastAPI endpoints
Invalid request handling
Valid API responses

Current test status:

7 passed
CI/CD

GitHub Actions automatically:

Checks out the repository
Sets up Python
Installs dependencies
Runs the automated test suite

Every push and pull request triggers the workflow.

Observability

Langfuse is integrated into the agent workflow to trace major execution stages, including:

Knowledge retrieval
SQL generation
SQL validation
SQL execution
SQL evaluation
Result evaluation
Self-correction

This provides visibility into:

Agent execution
LLM operations
Failures
Retries
Execution flow
Project Structure
enterprise-bi-agent/
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── data/
│   └── sample_warehouse.duckdb
│
├── src/
│   ├── guardrails/
│   │   ├── validator.py
│   │   └── test_validator.py
│   │
│   ├── api.py
│   ├── business_catalog.py
│   ├── business_retriever.py
│   ├── correction_node.py
│   ├── database.py
│   ├── evaluation_dataset.py
│   ├── evaluation_node.py
│   ├── evaluator.py
│   ├── execution_node.py
│   ├── graph.py
│   ├── graph_state.py
│   ├── knowledge_node.py
│   ├── nodes.py
│   ├── result_evaluation_node.py
│   ├── retriever.py
│   ├── router.py
│   └── ...
│
├── tests/
│   ├── test_api.py
│   └── test_guardrails.py
│
├── Dockerfile
├── requirements.txt
└── create_database.py
Security Considerations

The current implementation restricts generated SQL to read-only SELECT statements.

Production hardening would additionally include:

Prompt-injection defenses
Query timeout controls
Query cost limits
Result-size limits
Sensitive-column access controls
Database-level permissions
Authentication and authorization
Future Improvements
Expand the evaluation benchmark from 6 to 30–50+ questions
Add query latency metrics
Add token-usage and cost metrics
Add stronger prompt-injection protection
Add database access controls
Add an interactive web frontend
Add production-scale evaluation
Improve failure analysis and observability