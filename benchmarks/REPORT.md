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

## Separate live Groq evaluation

A separate 50-question live evaluation harness is provided:

- Dataset: `benchmarks/datasets/groq_eval_50.json`
- Runner: `benchmarks/run_groq_eval.py`
- Output: `benchmarks/results/groq_eval_50_report.json`

Run it from the repository root after configuring `GROQ_API_KEY`, preparing the sample DuckDB database, and ensuring the local Qdrant knowledge collection is populated:

```powershell
python create_database.py
python -m src.rag.ingest
python benchmarks/run_groq_eval.py
```

The runner makes real Groq SQL-generation calls through the existing LangGraph application, uses the actual local RAG retrieval and DuckDB execution path, and calculates expected results by executing each dataset case's gold SQL. It disables the extra LLM judge and automatic graph retries so that a failed question does not silently trigger additional generation calls. It also bypasses semantic cache and HITL through the application's existing `evaluation_mode`.

The runner records generated SQL, execution results, pass/fail status, attempted Groq generation calls, token usage when returned by the API, and latency. **The 50-case live evaluation has not yet been executed or verified.** Do not report a live Groq score until the runner completes successfully and its JSON report has been reviewed.

The dataset is deliberately small and based on the repository's synthetic sample warehouse. It is a controlled integration check, not a broad estimate of enterprise text-to-SQL performance. The category labels describe question styles, not independently isolated model capabilities. The current harness does not test automatic self-correction because retries are disabled to enforce a predictable call budget; correction should be tested in a separately budgeted run.

## Expanded 100-question live Groq evaluation

The expanded live dataset is available at `benchmarks/datasets/groq_eval_100.json`. It contains the original 50 cases plus 50 additional cases, with 100 unique IDs across six categories:

| Category | Cases |
|---|---:|
| SQL generation | 20 |
| Execution correctness | 15 |
| RAG grounding | 15 |
| Complex analytics | 20 |
| Multi-condition SQL | 15 |
| Edge cases | 15 |
| **Total** | **100** |

The runner accepts a dataset path and run label. From the repository root:

```powershell
python benchmarks/run_groq_eval.py --run-id run1
python benchmarks/run_groq_eval.py --run-id run2
python benchmarks/run_groq_eval.py --run-id run3
```

Reports are written separately to `benchmarks/results/groq_eval_100_run1.json`, `run2.json`, and `run3.json`. A different dataset can be supplied with `--dataset path/to/dataset.json`.

The runner now checks generated result values and output column names against the gold query. The 100-case dataset has unique IDs and required fields. The benchmark remains a controlled test against the small synthetic warehouse. Gold SQL should be smoke-tested locally before spending live Groq quota; do not interpret API quota errors as incorrect model answers. The three runs are repeated evaluations on the same fixed questions, not three independent datasets.

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
