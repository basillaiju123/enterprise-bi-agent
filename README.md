Enterprise BI Agent
Agentic Text-to-SQL Analytics Platform for enterprise-style business intelligence.

Enterprise BI Agent converts natural-language business questions into validated SQL and grounded analytical results. It combines LangGraph orchestration, hybrid RAG, LLM-based Text-to-SQL, SQLGlot AST guardrails, RBAC, human-in-the-loop approval, self-correction, semantic caching, evaluation, Langfuse observability, FastAPI, Docker, and GitHub Actions CI/CD.
Live Demo
- API: https://enterprise-bi-agent.onrender.com
- Swagger UI: https://enterprise-bi-agent.onrender.com/docs
- Health: https://enterprise-bi-agent.onrender.com/health
Architecture
User Question
      |
      v
Semantic Cache
      |
      +---- cache hit --------------------+
      |                                   |
      +---- cache miss                    |
               |                          |
               v                          |
        Hybrid RAG                        |
     Qdrant + BM25 + RRF                  |
               |                          |
               +------------+-------------+
                            v
                    SQL Generation
                    LangGraph + LLM
                            |
                            v
                    SQLGlot Guardrails
                            |
                            v
                         RBAC
                            |
                            v
                     HITL Approval
                            |
                            v
                    DuckDB Execution
                            |
                            v
                  SQL + Result Evaluation
                            |
                    +-------+-------+
                    |               |
                  Success        Failure
                    |               |
                    v               v
                  Cache       Self-Correction
                                    |
                                    v
                                Retry SQL
                                Max 3 retries
Core Features
- Natural-language Text-to-SQL
- Hybrid semantic + BM25 retrieval with RRF
- Schema and business-knowledge grounding
- Stateful LangGraph workflow
- SQLGlot AST-based read-only SQL guardrails
- Role-based table authorization
- Human-in-the-loop approval for selected risky queries
- Automatic SQL self-correction with a maximum of 3 retries
- Semantic SQL evaluation
- Exact query-result evaluation
- Semantic caching
- Langfuse tracing
- FastAPI REST API
- DuckDB analytical warehouse
- Reproducible Docker builds
- GitHub Actions CI/CD
- Public Docker deployment on Render
How It Works
1. Hybrid RAG
Before SQL generation, the agent retrieves relevant schema, business definitions, and SQL examples.
Retrieval combines:
- Dense semantic retrieval
- BM25 lexical retrieval
- Reciprocal Rank Fusion (RRF)
- Qdrant local vector storage
The Docker build runs the RAG ingestion process itself, so the image does not depend on locally generated Qdrant files.
2. Business Knowledge Grounding
The knowledge base contains business definitions such as:
Revenue
= SUM(order_items.quantity * products.price)

Completed Order
= orders.status = 'Completed'

Cancelled Order
= orders.status = 'Cancelled'

Average Order Value
= completed revenue / completed order count
3. SQL Generation
Example:
Question:
How many customers are from India?
Generated SQL:
SELECT COUNT(*) AS num_customers
FROM customers
WHERE country = 'India';
4. SQLGlot Guardrails
Generated SQL is parsed before execution.
The system:
- Allows only one SQL statement
- Allows only SELECT queries
- Rejects INSERT
- Rejects UPDATE
- Rejects DELETE
- Rejects DROP
- Rejects ALTER
- Rejects CREATE
5. RBAC
Role	Allowed tables
admin	all business tables
analyst	all business tables
viewer	customers, products


Authorization is checked against the tables referenced by the parsed SQL.
6. Human-in-the-Loop
Selected non-aggregate queries can pause for explicit human approval.
Query
  |
  v
Risk check
  |
  v
Approval required
  |
  +---- approve ---> execute
  |
  +---- reject ----> stop
LangGraph persistence allows the workflow to resume using its thread ID.
7. Self-Correction
When validation, execution, or evaluation fails, the correction workflow feeds failure information back into SQL generation.
The agent can retry up to 3 times using:
- Previous SQL
- Validation errors
- Execution errors
- Evaluation feedback
Semantic Caching
The system uses a semantic cache backed by SQLite and all-MiniLM-L6-v2.
A local benchmark of five cold runs versus five cached runs produced:
Metric	Result
Cold median latency	1.726 s
Cached median latency	0.831 s
Median reduction	51.9%


This is a local project benchmark, not a production SLA.
Evaluation
The project evaluates both generated SQL and final database results.
30-query deterministic replay benchmark
Metric	Result
Execution accuracy	30/30
Result validation	30/30
Semantic evaluation	30/30
Fully passed	30/30
Replay accuracy	100%


The 100% result is for deterministic replay of recorded evaluation cases. An earlier fresh-generation run achieved 28/30 fully passed cases (93.3%). The replay figure should therefore not be interpreted as a general LLM accuracy guarantee.

Observability
Langfuse traces major workflow stages:
- Knowledge retrieval
- SQL generation
- SQL validation
- SQL execution
- SQL evaluation
- Result evaluation
- Self-correction
API
Method	Endpoint	Purpose
GET	/	Service information
GET	/health	Health check
POST	/query	Run an analytics query
POST	/approve	Resume human approval


Example request:
{
  "question": "How many customers are from India?",
  "role": "analyst"
}
Example response:
{
  "question": "How many customers are from India?",
  "sql": "SELECT COUNT(*) AS num_customers FROM customers WHERE country = 'India';",
  "result": [[2]],
  "error": "",
  "retries": 0,
  "cache_hit": false,
  "approval_required": false,
  "approval_status": "not_required"
}
Tech Stack
Layer	Technology
Language	Python 3.13
LLM	Groq — GPT-OSS-20B
Orchestration	LangGraph
RAG	Qdrant + BM25 + RRF
Embeddings	Sentence Transformers
SQL validation	SQLGlot
Database	DuckDB
Cache	SQLite + Sentence Transformers
API	FastAPI
Observability	Langfuse
Testing	Pytest
Containerization	Docker
CI/CD	GitHub Actions
Deployment	Render


Project Structure
enterprise-bi-agent/
├── .github/workflows/tests.yml
├── data/
│   ├── sample_warehouse.duckdb
│   └── evaluation_replay.json
├── src/
│   ├── api.py
│   ├── graph.py
│   ├── graph_state.py
│   ├── nodes.py
│   ├── execution_node.py
│   ├── correction_node.py
│   ├── validation_node.py
│   ├── evaluation_node.py
│   ├── result_evaluation_node.py
│   ├── approval_node.py
│   ├── hitl_node.py
│   ├── cache_node.py
│   ├── cache_store_node.py
│   ├── semantic_cache.py
│   ├── rag/
│   ├── guardrails/
│   └── security/
├── tests/
│   ├── test_api.py
│   ├── test_guardrails.py
│   └── test_rbac.py
├── Dockerfile
├── requirements.txt
├── create_database.py
├── README.md
└── .gitignore
Local Setup
git clone https://github.com/basillaiju123/enterprise-bi-agent.git
cd enterprise-bi-agent
python -m venv .venv
Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Create .env:
GROQ_API_KEY=your_groq_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
Run:
uvicorn src.api:app --host 0.0.0.0 --port 8000
Swagger:
http://localhost:8000/docs
Docker
Build:
docker build -t enterprise-bi-agent .
Run:
docker run --rm --env-file .env -e PORT=8000 -p 8000:8000 enterprise-bi-agent
The Docker build automatically runs RAG ingestion and creates the enterprise_knowledge Qdrant collection inside the image.
Testing
Run:
python -m pytest -q tests
Current suite:
14 passed
Coverage includes SQL safety, multi-statement rejection, destructive SQL rejection, RBAC, FastAPI endpoints, invalid requests, zero-result queries, and the health endpoint.
CI/CD
GitHub Actions runs on pushes and pull requests:
Git Push / Pull Request
        |
        v
Python 3.13
        |
        v
Install dependencies
        |
        v
Run 14 tests
        |
        v
Build Docker image
        |
        v
PASS / FAIL
The Docker build also validates reproducible RAG ingestion.
Deployment
The application is deployed as a Docker Web Service on Render.
https://enterprise-bi-agent.onrender.com
Health:
https://enterprise-bi-agent.onrender.com/health
Swagger:
https://enterprise-bi-agent.onrender.com/docs
Secrets are supplied through deployment environment variables and are not stored in the repository.
Engineering Highlights
This project demonstrates production-oriented GenAI engineering patterns:
- Agent orchestration: LangGraph models the workflow as explicit state and transitions.
- Grounding: Hybrid retrieval supplies schema and business context before generation.
- Guardrails: SQLGlot enforces a read-only SQL boundary.
- Authorization: RBAC restricts table access by role.
- Human oversight: HITL approval can pause and resume execution.
- Reliability: Self-correction and result evaluation handle incorrect SQL.
- Performance: Semantic caching reduced local median latency by 51.9%.
- Evaluation: A reproducible 30-query benchmark supports regression testing.
- Deployment: Docker + GitHub Actions + Render provide a complete delivery path.
Security Considerations
The current implementation provides:
- Read-only SQL enforcement
- AST-level SQL validation
- Table-level RBAC
- Human approval for selected risky queries
- Environment-based secret management
A larger enterprise deployment would additionally require authentication, stronger prompt-injection defenses, query timeouts, query cost limits, result-size limits, sensitive-column controls, database-level permissions, rate limiting, audit logging, and production secret rotation.
Project Status
Completed
- [x] Natural-language Text-to-SQL
- [x] Schema retrieval
- [x] Business knowledge retrieval
- [x] Hybrid semantic + BM25 retrieval
- [x] LangGraph orchestration
- [x] SQLGlot guardrails
- [x] RBAC
- [x] DuckDB execution
- [x] Self-correction
- [x] Human-in-the-loop approval
- [x] Semantic SQL evaluation
- [x] Exact result evaluation
- [x] Semantic caching
- [x] Langfuse observability
- [x] FastAPI API
- [x] Docker
- [x] Reproducible Qdrant ingestion
- [x] Pytest suite
- [x] GitHub Actions CI/CD
- [x] Public deployment
Portfolio Summary
Enterprise BI Agent demonstrates how LLMs can be combined with retrieval, structured validation, authorization, human oversight, evaluation, caching, observability, and deployment to build a more reliable Text-to-SQL analytics system.
The focus is engineering reliability around LLMs, rather than treating the LLM as the entire application.
License
This project is intended as a portfolio and learning project demonstrating an agentic AI system for enterprise analytics.