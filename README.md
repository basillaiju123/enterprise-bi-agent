# Enterprise BI Agent

An agentic **Text-to-SQL and business analytics platform** that allows users to query structured business data using natural language.

The system combines **LLM-based SQL generation, RAG, LangGraph orchestration, SQL guardrails, automatic self-correction, evaluation, observability, FastAPI, Docker, and CI/CD** into a stateful analytics workflow.

---

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
```

### Agent Workflow

The system is implemented as a stateful workflow using **LangGraph**.

Each stage operates on shared agent state containing information such as:

- User question
- Retrieved schema context
- Business knowledge
- Generated SQL
- Validation errors
- Execution errors
- Query results
- Retry count
- Evaluation state

---

## Key Features

- Natural-language to SQL generation
- Schema and business-knowledge retrieval
- Stateful LangGraph workflow
- SQLGlot SQL validation and safety guardrails
- Automatic SQL self-correction with retry limits
- Semantic SQL evaluation
- Exact query-result evaluation
- Langfuse observability
- FastAPI REST API
- DuckDB analytical database
- Docker deployment
- Pytest test suite
- GitHub Actions CI/CD

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| LLM | Groq — GPT-OSS-20B |
| Agent Orchestration | LangGraph |
| Database | DuckDB |
| SQL Validation | SQLGlot |
| RAG | Schema + Business Knowledge Retrieval |
| Observability | Langfuse |
| API | FastAPI |
| Testing | Pytest |
| Deployment | Docker |
| CI/CD | GitHub Actions |

---

# How It Works

## 1. Knowledge Retrieval

Before generating SQL, the agent retrieves relevant database schema information and business definitions.

The system maintains structured knowledge about the database and business terminology.

Examples include:

- Revenue
- Completed orders
- Cancelled orders
- Order quantity
- Average order value

This gives the LLM both **database structure** and **business context** before SQL generation.

---

## 2. SQL Generation

The LLM converts the user's natural-language question into DuckDB SQL using the retrieved context.

### Example

**Question**

```text
How many customers are from India?
```

**Generated SQL**

```sql
SELECT COUNT(*) AS num_customers
FROM customers
WHERE country = 'India';
```

---

## 3. SQL Guardrails

Generated SQL is validated using **SQLGlot** before execution.

The current implementation:

- Allows only a single SQL statement
- Allows only `SELECT` queries
- Rejects `INSERT`
- Rejects `UPDATE`
- Rejects `DELETE`
- Rejects `DROP`
- Rejects `ALTER`
- Rejects `CREATE`

This provides a read-only execution boundary for the generated SQL.

### Validation Flow

```text
Generated SQL
      ↓
   SQLGlot
      ↓
Valid SELECT?
   ↙       ↘
 Yes        No
 ↓           ↓
Execute    Reject
```

---

## 4. SQL Execution

Validated SQL is executed against a DuckDB business database.

The sample database contains:

- Customers
- Products
- Orders
- Order items

### Database Schema

```text
customers
├── customer_id
├── customer_name
├── country
└── signup_date

products
├── product_id
├── product_name
├── category
└── price

orders
├── order_id
├── customer_id
├── order_date
└── status

order_items
├── order_id
├── product_id
└── quantity
```

---

## 5. Self-Correction

If SQL execution or evaluation fails, the workflow feeds the failure information back into the SQL generation node.

The agent can retry SQL generation up to **three times**.

```text
SQL Generation
      ↓
Validation
      ↓
Execution
      ↓
   Failure?
   ↙      ↘
 Yes       No
 ↓          ↓
Correction Success
 ↓
Retry SQL
 ↓
Maximum 3 retries
```

The correction process can use:

- Previous generated SQL
- Validation errors
- Execution errors
- Evaluation feedback

This allows the agent to recover from incorrect SQL instead of immediately failing.

---

# Evaluation

The project uses two levels of evaluation.

## Semantic SQL Evaluation

An LLM-based evaluator checks whether the generated SQL correctly addresses the user's natural-language question.

This evaluates the **meaning and intent** of the generated query.

## Exact Query-Result Evaluation

The actual database result is compared against the expected result in the evaluation dataset.

This provides a stronger correctness check and prevents semantically plausible but numerically incorrect SQL from being treated as correct.

---

## Development Benchmark

The initial benchmark contains **6 synthetic business questions** covering:

- Customer queries
- Product filtering
- Aggregation
- Order status
- Customer/order joins
- Revenue calculation

### Current Results

| Metric | Result |
|---|---:|
| Execution accuracy | 6/6 |
| Result validation | 6/6 |
| Semantic evaluation | 6/6 |
| Fully passed | 6/6 |
| Overall | 100% |

> **Note:** This benchmark is based on a small synthetic dataset and should not be interpreted as production-level accuracy.

---

# API

The project exposes a REST API using **FastAPI**.

## Start the API

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Swagger UI

Open:

```text
http://localhost:8000/docs
```

---

## Example Request

```json
{
  "question": "How many customers are from India?"
}
```

## Example Response

```json
{
  "question": "How many customers are from India?",
  "sql": "SELECT COUNT(*) AS num_customers FROM customers WHERE country = 'India';",
  "result": [[2]],
  "error": "",
  "retries": 0
}
```

---

# Docker

The application can be containerized using Docker.

## Build the Image

```bash
docker build -t enterprise-bi-agent .
```

## Run the Container

```bash
docker run --rm --env-file .env -p 8000:8000 enterprise-bi-agent
```

Then open:

```text
http://localhost:8000/docs
```

---

# Testing

The project includes an automated Pytest test suite.

Run:

```bash
pytest -q tests
```

### Current Test Status

```text
7 passed
```

The test suite covers:

- SQL safety guardrails
- Multiple-statement rejection
- Destructive SQL rejection
- FastAPI endpoints
- Invalid request handling
- Valid API responses

---

# CI/CD

GitHub Actions automatically runs the test suite on:

- Pushes
- Pull requests

The workflow:

1. Checks out the repository
2. Sets up Python
3. Installs project dependencies
4. Runs the automated test suite

```text
Git Push / Pull Request
          ↓
    GitHub Actions
          ↓
   Setup Python 3.13
          ↓
 Install Dependencies
          ↓
      Run Pytest
          ↓
    Pass / Fail
```

---

# Observability

**Langfuse** is integrated into the agent workflow to trace major execution stages.

Tracked stages include:

- Knowledge retrieval
- SQL generation
- SQL validation
- SQL execution
- SQL evaluation
- Result evaluation
- Self-correction

This provides visibility into:

- Agent execution
- LLM operations
- Failures
- Retries
- Execution flow

---

# Project Structure

```text
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
│   ├── run_evaluation.py
│   ├── run_graph.py
│   ├── schema_catalog.py
│   ├── schema_node.py
│   ├── telemetry.py
│   └── validation_node.py
│
├── tests/
│   ├── test_api.py
│   └── test_guardrails.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── create_database.py
├── requirements.txt
└── README.md
```

---

# Security Considerations

The current implementation restricts generated SQL to read-only `SELECT` statements.

The SQL guardrail layer rejects destructive operations such as:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
```

## Production Hardening

A production deployment would additionally require:

- Prompt-injection defenses
- Query timeout controls
- Query cost limits
- Result-size limits
- Sensitive-column access controls
- Database-level permissions
- Authentication
- Authorization
- Rate limiting
- Audit logging

---

# Future Improvements

Planned improvements include:

- Expand the evaluation benchmark from 6 to 30–50+ questions
- Add query latency metrics
- Add token-usage metrics
- Add LLM cost tracking
- Add stronger prompt-injection protection
- Add database access controls
- Add an interactive web frontend
- Add production-scale evaluation
- Improve failure analysis
- Improve observability
- Add richer analytics visualizations

---

# Project Status

### Current Implementation

- [x] Natural-language Text-to-SQL
- [x] Schema retrieval
- [x] Business knowledge retrieval
- [x] LangGraph orchestration
- [x] SQLGlot guardrails
- [x] DuckDB execution
- [x] Self-correction loop
- [x] Semantic SQL evaluation
- [x] Exact result evaluation
- [x] Langfuse observability
- [x] FastAPI API
- [x] Docker deployment
- [x] Pytest tests
- [x] GitHub Actions CI/CD

### Next Development Goals

- [ ] Expand evaluation benchmark
- [ ] Add latency and cost tracking
- [ ] Strengthen security controls
- [ ] Add interactive frontend
- [ ] Production-scale evaluation

---

# License

This project is intended as a portfolio and learning project demonstrating an agentic AI system for enterprise analytics.