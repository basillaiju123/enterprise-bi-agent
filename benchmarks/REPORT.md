# Orka.ai Benchmark Report

## Executive summary

The planned deterministic benchmark suite for Orka.ai completed with **500/500 target cases passing** across seven categories.

| Category | Target cases | Recorded result |
|---|---:|---:|
| SQL correctness and DuckDB execution | 150 | 150 passed |
| SQL security and guardrails | 100 | 100 passed |
| Role-based table authorization (RBAC) | 75 | 75 passed |
| Hybrid RAG retrieval ranking | 50 | 50 passed |
| Workflow routing, HITL, and result evaluation | 50 | 50 passed |
| Semantic cache behavior | 50 | 50 passed |
| FastAPI endpoint reliability | 25 | 25 passed |
| **Total** | **500** | **500 passed** |

The recorded category runs were performed separately. Pytest output for parameterized categories also included additional dataset-integrity or supporting checks; those additional pytest items are not included in the 500-case target count.

## What was tested

### 1. SQL correctness and DuckDB execution — 150 cases

- Executed generated read-only SQL against the sample DuckDB warehouse.
- Compared returned columns, row counts, and result rows against expected results.
- Used deterministic ordering to avoid unstable row-order comparisons.
- Dataset construction used 30 base query patterns with five LIMIT variants each.

**Interpretation:** 150 SQL test statements were exercised, but they represent 30 underlying query patterns rather than 150 fully independent business-question patterns.

### 2. SQL security and guardrails — 100 cases

- Exercised accepted read-only SELECT statements.
- Exercised rejected modifying, destructive, invalid, and multi-statement SQL.
- Tested the current validator's single-SELECT policy. UNION is rejected by the current implementation because the parsed root expression is not a plain SELECT.

### 3. RBAC — 75 cases

- Tested 25 SQL patterns against three roles: admin, analyst, and viewer.
- Covered table access, aliases, joins, aggregations, subqueries, and authorization boundaries.
- Verified viewer restrictions against tables outside its allowed set.

### 4. RAG retrieval — 50 cases

- Tested top-k behavior and Reciprocal Rank Fusion ordering.
- Used mocked Qdrant and BM25 components for deterministic tests.

**Limitation:** These tests validate retrieval orchestration and ranking behavior, not semantic relevance of a live Qdrant index or embedding model on a representative external evaluation set.

### 5. Workflow and HITL — 50 cases

- Tested workflow routing, retry/failure decisions, human-approval decisions, and result comparison.
- Checked deterministic evaluation behavior and isolated the LLM judge path with mocks.

**Limitation:** This category tests workflow components and decisions deterministically; it is not a load test or a complete production end-to-end test against live external services.

### 6. Semantic cache — 50 cases

- Tested cache-key normalization, similarity hit/miss behavior, role scoping, replacement, threshold behavior, and SQLite storage integrity.
- Used a temporary SQLite database and mocked embeddings to avoid model downloads and external API calls.

### 7. FastAPI reliability — 25 cases

- Tested supported roles, blank and malformed requests, invalid roles, response contract fields, error mapping, thread IDs, and approval/resume behavior.
- Mocked the LangGraph invocation so endpoint tests do not require Groq or live infrastructure.

## Reproducibility

The six pytest benchmark modules are in `tests/benchmark/`:

```powershell
python -m pytest tests/benchmark/test_guardrails_100.py -v
python -m pytest tests/benchmark/test_rbac_75.py -v
python -m pytest tests/benchmark/test_rag_50.py -v
python -m pytest tests/benchmark/test_workflow_50.py -v
python -m pytest tests/benchmark/test_cache_50.py -v
python -m pytest tests/benchmark/test_api_25.py -v
```

Run the six pytest modules together:

```powershell
python -m pytest tests/benchmark -v
```

### SQL correctness artifact availability

The SQL correctness dataset and runner were generated and executed locally during this benchmark work:

- `benchmarks/generate_sql_dataset.py`
- `benchmarks/run_sql_correctness.py`
- `benchmarks/datasets/sql_correctness_150.json`
- `benchmarks/results/sql_correctness_report.json`

**These four SQL correctness artifacts were not found on the `benchmark-500` GitHub branch when this report was prepared.** Therefore, the 150-case SQL correctness result is recorded here, but a clean clone cannot currently reproduce that category from the repository alone. Commit those local files (after checking that the dataset/report contain no sensitive data) to make the entire 500-case benchmark reproducible from GitHub.

The six pytest modules above are committed and reproducible from the repository, subject to installing the project's test dependencies and preparing the expected local environment.

## Evaluation boundaries

This benchmark measures deterministic software behavior under controlled test conditions. It does **not** establish:

- 100% accuracy for newly generated LLM SQL.
- Live RAG relevance or production Qdrant quality.
- Production availability, throughput, concurrency, or latency SLAs.
- End-to-end reliability of Groq, Render, Vercel, Langfuse, or other external services.

Keep deterministic replay separate from fresh LLM evaluation. A previously recorded fresh-generation evaluation achieved **28/30 fully passed cases (93.3%)**. That result is a separate sample and must not be combined with the 500 deterministic benchmark cases or described as a 500-case LLM accuracy score.

A previous 30/30 deterministic replay result is also separate from this benchmark.

## Suggested interpretation

A defensible summary is:

> Built and executed a 500-case deterministic benchmark suite for an agentic BI platform, covering SQL execution, SQL guardrails, RBAC, RAG retrieval orchestration, workflow/HITL behavior, semantic caching, and FastAPI endpoint handling. All 500 planned cases passed under controlled test conditions.

When presenting this result, disclose the 30-base-pattern SQL dataset design and the mocked components described above.
