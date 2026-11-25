# Orka.ai — Agentic Enterprise BI Assistant

An agentic Text-to-SQL analytics platform that lets users ask business questions in natural language and receive validated SQL and database-backed results.

Orka.ai combines a React chat interface with a Python/FastAPI analytics backend. The backend uses LangGraph to orchestrate retrieval, SQL generation, validation, authorization, optional human approval, execution, evaluation, and correction.

## Live Demo

- **Live website:** https://enterprise-bi-agent.vercel.app/
- **Backend API:** https://enterprise-bi-agent.onrender.com
- **Swagger UI:** https://enterprise-bi-agent.onrender.com/docs
- **Health check:** https://enterprise-bi-agent.onrender.com/health

## Product Overview

Users can ask questions such as:

- How many customers are from India?
- Show the top 5 customers by order count.
- What is the average order value for completed orders?
- Which products are available in the warehouse?

The agent retrieves relevant schema and business context, generates SQL, validates it, checks table permissions, and executes approved queries against the DuckDB analytics warehouse. The UI displays the generated SQL, returned rows, execution metadata, and a CSV export option.

## Application Interface

The frontend is built with React and Vite and branded as **orka.ai**, with a custom orca mascot and a chat-oriented analytics workspace.

Current interactive UI:
- Chat input for natural-language analytics questions.
- Quick-prompt actions for revenue analysis, SQL generation, workflow explanation, and insights.
- API health indicator.
- Generated SQL and query-result display.
- CSV export for returned rows.
- Human approval controls when the backend pauses a query.
- New-chat reset and a floating Orka assistant mascot.

The Agents, Workflows, Datasets, Reports, and Insights sidebar entries currently provide informational UI feedback; they are not separate fully implemented dashboard pages.

## Architecture

```text
Browser
  |
  v
React + Vite frontend (Vercel)
  |
  | HTTPS requests: /health, /query, /approve
  v
FastAPI backend (Render)
  |
  v
LangGraph workflow
  |
  +--> Semantic cache (SQLite + embeddings)
  |
  +--> Hybrid RAG
  |      +--> Dense semantic retrieval
  |      +--> BM25 keyword retrieval
  |      +--> Reciprocal Rank Fusion (RRF)
  |      +--> Qdrant vector store
  |      +--> Semantic relevance gate (reject unrelated questions)
  |
  +--> LLM SQL generation (Groq GPT-OSS-20B)
  |
  +--> SQLGlot AST validation
  |
  +--> Role-based table authorization (RBAC)
  |
  +--> Human-in-the-loop approval, when required
  |
  +--> DuckDB query execution
  |
  +--> SQL/result evaluation
          |
          +--> Success: return result and cache eligible response
          |
          +--> Failure: self-correction and retry (up to 3 retries)
  |
  v
Frontend renders SQL, result rows, status, and CSV export
```

## Backend Features

### 1. Natural-language Text-to-SQL

Converts a user's business question into SQL using the LLM and retrieved database/business context.

### 2. Hybrid RAG

Retrieves relevant schema details, business definitions, and SQL examples before SQL generation. Retrieval combines:
- Dense semantic retrieval.
- BM25 lexical retrieval.
- Reciprocal Rank Fusion (RRF).
- Qdrant local vector storage.

The Docker build runs the RAG ingestion process so the image does not depend on locally generated Qdrant files.

### 3. Business Knowledge Grounding

A configurable semantic relevance gate checks the maximum dense-retrieval similarity before either cached SQL or new SQL generation is used. The default cutoff is `0.302452`, calibrated against the current 11-query labeled robustness sample; it is a prototype heuristic, not a universal confidence score. Override it with the backend environment variable `RAG_MIN_SEMANTIC_SCORE` (a value from `0` to `1`). Irrelevant questions are returned without SQL generation. The relevance check also runs on semantic-cache hits.

The knowledge base includes business definitions such as:

```text
Revenue
= SUM(order_items.quantity * products.price)

Completed Order
= orders.status = 'Completed'

Cancelled Order
= orders.status = 'Cancelled'

Average Order Value
= completed revenue / completed order count
```

### 4. SQLGlot Guardrails

Generated SQL is parsed before execution. The system allows a single read-only SELECT statement and rejects destructive or modifying statements such as INSERT, UPDATE, DELETE, DROP, ALTER, and CREATE.

### 5. Role-Based Access Control

Authorization is checked against the tables referenced by the parsed SQL.

| Role | Allowed tables |
|---|---|
| admin | All business tables |
| analyst | All business tables |
| viewer | customers, products |

### 6. Human-in-the-Loop Approval

Selected non-aggregate queries can pause for explicit human approval. The user can approve and resume the workflow or reject it. LangGraph persistence uses a thread ID to resume the paused workflow.

### 7. SQL Self-Correction

When validation, execution, or evaluation fails, the correction workflow uses the previous SQL and failure feedback to attempt a correction. The workflow can retry up to three times.

### 8. Semantic Caching

A semantic cache backed by SQLite and all-MiniLM-L6-v2 can reuse results for sufficiently similar questions.

A local benchmark of five cold runs versus five cached runs reported:

| Metric | Result |
|---|---:|
| Cold median latency | 1.726 s |
| Cached median latency | 0.831 s |
| Median reduction | 51.9% |

This is a local project benchmark, not a production SLA.

### 9. Evaluation and Observability

The project evaluates generated SQL and final database results. Langfuse traces major workflow stages, including retrieval, SQL generation, validation, execution, evaluation, and self-correction.

A 30-query deterministic replay benchmark reported 30/30 cases passed. This replay result is not a guarantee of general LLM accuracy; an earlier fresh-generation run achieved 28/30 fully passed cases (93.3%).

## Benchmarking

The project includes a **500-case deterministic benchmark plan** across seven areas: SQL correctness and DuckDB execution (150), SQL guardrails (100), RBAC (75), RAG retrieval (50), workflow/HITL (50), semantic caching (50), and FastAPI endpoint reliability (25). The recorded runs passed all 500 planned cases.

The benchmark is intended to validate deterministic application behavior, not to claim 100% fresh LLM accuracy or production reliability. Some components are mocked: RAG tests mock Qdrant/BM25, workflow tests isolate node/routing behavior, and API tests mock LangGraph invocation. The SQL correctness set contains 150 statements derived from 30 base query patterns with five LIMIT variants each.

See **[the benchmark report](benchmarks/REPORT.md)** for methodology, results, limitations, and reproduction commands.

A separate 50-question **live Groq evaluation** harness is also provided at `benchmarks/run_groq_eval.py`, using `benchmarks/datasets/groq_eval_50.json`. It calls the real LangGraph generation path and records SQL execution accuracy, token usage, and latency. Run it only after preparing the local DuckDB database and Qdrant knowledge collection; see the report for commands. Its live score is pending execution and is separate from the deterministic 500-case suite.

**Reproducibility note:** the six pytest benchmark modules are committed under `tests/benchmark/`. The SQL correctness runner and its generated dataset/report were local artifacts and were not present on the `benchmark-500` branch when the report was prepared. Commit those files to make all 500 cases reproducible from a clean clone.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Service information |
| GET | `/health` | Health check |
| POST | `/query` | Run an analytics question |
| POST | `/approve` | Resume a human-approval workflow |

Example request:

```json
{
  "question": "How many customers are from India?",
  "role": "analyst"
}
```

Example response:

```json
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
```

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 6, JavaScript |
| UI icons | Lucide React |
| Backend language | Python 3.13 |
| API | FastAPI |
| LLM | Groq — GPT-OSS-20B |
| Agent orchestration | LangGraph |
| Retrieval | Qdrant, BM25, RRF |
| Embeddings | Sentence Transformers |
| SQL validation | SQLGlot |
| Analytical database | DuckDB |
| Semantic cache | SQLite + Sentence Transformers |
| Observability | Langfuse |
| Testing | Pytest |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Frontend hosting | Vercel |
| Backend hosting | Render |

## Repository Structure

```text
enterprise-bi-agent/
├── .github/workflows/       # GitHub Actions CI workflow
├── data/                    # Sample warehouse and evaluation replay data
├── frontend/
│   ├── public/images/       # Orka mascot assets
│   ├── src/                 # React application and styles
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
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
├── Dockerfile
├── requirements.txt
├── create_database.py
└── README.md
```

## Local Development

### Backend

1. Clone the repository and enter the project directory:

```bash
git clone https://github.com/basillaiju123/enterprise-bi-agent.git
cd enterprise-bi-agent
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a root-level `.env` file with your own credentials:

```dotenv
GROQ_API_KEY=your_groq_api_key
RAG_MIN_SEMANTIC_SCORE=0.302452
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

5. Start the API:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Backend docs: http://localhost:8000/docs

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Start the Vite development server:

```bash
npm run dev
```

Vite prints the local frontend URL in the terminal (normally http://localhost:5173).

The frontend defaults to the deployed Render API if `VITE_API_BASE_URL` is not set. Use the local value above when running the backend locally.

## Deployment

### Frontend — Vercel

The frontend is a Vite application in the `frontend/` directory.

1. Import `basillaiju123/enterprise-bi-agent` into Vercel.
2. Set the project Root Directory to `frontend`.
3. Select the Vite framework preset.
4. Use `npm run build` as the build command and `dist` as the output directory.
5. Configure `VITE_API_BASE_URL` as `https://enterprise-bi-agent.onrender.com` for Production (and Preview if required).
6. Deploy and use the production domain shown in the Vercel project dashboard.

Vite environment variables prefixed with `VITE_` are included in the client bundle. Do not put private API keys or secrets in frontend environment variables.

### Backend — Render

The backend is deployed as a Docker Web Service on Render:

- API: https://enterprise-bi-agent.onrender.com
- Health: https://enterprise-bi-agent.onrender.com/health
- Swagger: https://enterprise-bi-agent.onrender.com/docs

Backend secrets are supplied through deployment environment variables and should not be committed to Git.

### Automatic deployments

The repository is connected to GitHub. Vercel can create deployments from Git commits, while the backend deployment is managed separately on Render. Verify both deployments after changing API or frontend code.

## Docker

Build the backend image:

```bash
docker build -t enterprise-bi-agent .
```

Run it:

```bash
docker run --rm --env-file .env -e PORT=8000 -p 8000:8000 enterprise-bi-agent
```

The Docker build automatically runs RAG ingestion and creates the `enterprise_knowledge` Qdrant collection inside the image.

## Testing

Run the backend test suite:

```bash
python -m pytest -q tests
```

The original application test suite contains 14 tests covering SQL safety, RBAC, and FastAPI behavior. The additional deterministic benchmark modules are under `tests/benchmark/`; see [Benchmarking](benchmarks/REPORT.md) for category-level commands and the scope of each benchmark.

GitHub Actions runs on pushes and pull requests. The documented workflow installs dependencies, runs tests, and builds the Docker image.

## Security Notes and Limitations

Current protections include:
- Read-only SQL enforcement through SQL parsing and validation.
- Table-level RBAC.
- Human approval for selected risky queries.
- Environment-based secret configuration.

This is a portfolio and learning project, not a certified production security platform. A larger deployment should additionally consider authentication, stronger prompt-injection defenses, query timeouts and cost limits, result-size limits, sensitive-column controls, database-level permissions, rate limiting, audit logging, and secret rotation.

The current frontend is a chat-focused interface. Sidebar items for Agents, Workflows, Datasets, Reports, and Insights are informational UI actions rather than separate fully implemented pages.

## License

This project is intended as a portfolio and learning project demonstrating an agentic AI system for enterprise analytics.
