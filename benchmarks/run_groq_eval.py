"""Run 50 real Groq SQL-generation evaluations through Orka.ai's LangGraph.

This runner makes one generation attempt per case. It uses real RAG retrieval and
DuckDB execution, but uses the gold-query result as the correctness oracle and
disables the additional LLM judge and automatic retries to control cost.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
import duckdb

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_DATASET_PATH = ROOT / "benchmarks" / "datasets" / "groq_eval_100.json"
DB_PATH = ROOT / "data" / "sample_warehouse.duckdb"
RESULTS_DIR = ROOT / "benchmarks" / "results"
MODEL_NAME = "openai/gpt-oss-20b"


def json_safe(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value


def run_query_with_columns(sql: str):
    with duckdb.connect(str(DB_PATH), read_only=True) as connection:
        cursor = connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        return columns, cursor.fetchall()


def rows_match(expected, actual):
    from src.result_evaluation_node import normalize_result
    expected = normalize_result(expected)
    actual = normalize_result(actual)
    if expected == actual:
        return True
    return len(expected) == len(actual) and sorted(expected, key=str) == sorted(actual, key=str)


def parse_args():
    parser = argparse.ArgumentParser(description="Run Orka.ai live Groq SQL evaluation.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH), help="Path to a JSON evaluation dataset.")
    parser.add_argument("--run-id", default="run1", help="Run label for the output report filename.")
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is missing. Add it to the project .env file.")

    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}. Run python create_database.py first.")

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    if not cases:
        raise SystemExit("The evaluation dataset contains no cases.")
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset contains duplicate case IDs.")
    required = {"id", "category", "question", "gold_sql"}
    for index, case in enumerate(cases, start=1):
        missing = required - set(case)
        if missing:
            raise SystemExit(f"Case {index} is missing fields: {sorted(missing)}")

    # Import after loading environment variables. These are the actual app modules.
    from src import nodes, router, evaluation_node
    from src.graph import graph
    from src.result_evaluation_node import results_match

    # Stop after the first failed attempt. This makes the generation-call budget
    # predictable and prevents graph retries from silently multiplying API usage.
    router.MAX_RETRIES = 0

    usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    original_create = nodes.client.chat.completions.create

    def tracked_create(*args, **kwargs):
        # Count attempted API requests, including requests that raise an exception.
        usage["calls"] += 1
        response = original_create(*args, **kwargs)
        token_usage = getattr(response, "usage", None)
        if token_usage is not None:
            usage["prompt_tokens"] += getattr(token_usage, "prompt_tokens", 0) or 0
            usage["completion_tokens"] += getattr(token_usage, "completion_tokens", 0) or 0
            usage["total_tokens"] += getattr(token_usage, "total_tokens", 0) or 0
        return response

    results = []
    category_counts = Counter()
    started_all = time.perf_counter()

    # The independent gold-result oracle replaces the LLM judge. The actual
    # generate_sql_node, RAG retriever, SQL validator, RBAC, and DuckDB executor
    # remain active. A result mismatch is still marked as a failed case.
    with patch.object(nodes.client.chat.completions, "create", side_effect=tracked_create), \
         patch.object(evaluation_node, "evaluate_sql", return_value=(True, "LLM judge disabled; gold-result oracle is authoritative.")):

        for case in cases:
            category_counts[case["category"]] += 1
            case_started = time.perf_counter()
            expected_columns, expected = run_query_with_columns(case["gold_sql"])

            initial_state = {
                "user_question": case["question"],
                "user_role": "analyst",
                "schema_context": "",
                "generated_sql": "",
                "validation_error": "",
                "authorization_error": "",
                "execution_error": "",
                "query_result": [],
                "retry_count": 0,
                "expected_result": expected,
                "evaluation_mode": True,
                "approval_required": False,
                "approval_status": "",
                "cache_hit": False,
                "cache_key": "",
                "evaluation_replay": False,
                "replay_sql": "",
            }

            thread_id = f"groq-eval-{case['id']}-{int(time.time() * 1000)}"
            record = {
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "expected_result": json_safe(expected),
                "expected_columns": expected_columns,
            }
            calls_before = usage["calls"]
            rate_limit_retries_before = nodes.RATE_LIMIT_RETRY_COUNT

            try:
                final_state = graph.invoke(
                    initial_state,
                    {"configurable": {"thread_id": thread_id}},
                )
                actual = final_state.get("query_result", [])
                matched = rows_match(expected, actual)
                try:
                    actual_columns, _ = run_query_with_columns(final_state.get("generated_sql", ""))
                except Exception:
                    actual_columns = []
                columns_match = expected_columns == actual_columns
                record.update({
                    "status": "passed" if matched and columns_match and not final_state.get("execution_error") and not final_state.get("authorization_error") else "failed",
                    "generated_sql": final_state.get("generated_sql", ""),
                    "actual_result": json_safe(actual),
                    "result_match": matched,
                    "actual_columns": actual_columns,
                    "columns_match": columns_match,
                    "validation_error": final_state.get("validation_error", ""),
                    "execution_error": final_state.get("execution_error", ""),
                    "authorization_error": final_state.get("authorization_error", ""),
                    "retry_count": final_state.get("retry_count", 0),
                    "retrieved_context_present": bool(final_state.get("schema_context", "").strip()),
                })
            except Exception as exc:
                record.update({
                    "status": "error",
                    "generated_sql": "",
                    "actual_result": [],
                    "result_match": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })

            record["groq_generation_calls"] = usage["calls"] - calls_before
            record["rate_limit_retry_count"] = nodes.RATE_LIMIT_RETRY_COUNT - rate_limit_retries_before
            record["latency_seconds"] = round(time.perf_counter() - case_started, 3)
            results.append(record)

            print(
                f"[{len(results):02d}/{len(cases)}] {case['id']} "
                f"{record['status'].upper()} "
                f"calls={record['groq_generation_calls']} "
                f"latency={record['latency_seconds']:.2f}s"
            )

    passed = sum(item["status"] == "passed" for item in results)
    failed = sum(item["status"] == "failed" for item in results)
    errors = sum(item["status"] == "error" for item in results)
    latencies = sorted(item["latency_seconds"] for item in results)
    median_latency = latencies[len(latencies) // 2] if latencies else 0

    report = {
        "benchmark": "Orka.ai live Groq SQL evaluation",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "dataset": str(dataset_path),
        "run_id": args.run_id,
        "total_cases": len(cases),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate_percent": round(passed / len(cases) * 100, 2),
        "groq_generation_calls": usage["calls"],
        "token_usage": usage,
        "median_latency_seconds": median_latency,
        "total_duration_seconds": round(time.perf_counter() - started_all, 2),
        "category_counts": dict(category_counts),
        "methodology": {
            "real_groq_generation": True,
            "real_rag_retrieval": True,
            "real_sql_validation_and_rbac": True,
            "real_duckdb_execution": True,
            "gold_query_result_oracle": True,
            "llm_judge_calls": 0,
            "sql_correction_retries": False,
            "rate_limit_retries": True,
            "rate_limit_retry_count": nodes.RATE_LIMIT_RETRY_COUNT,
            "sdk_retries": False,
            "generation_calls_include_failed_http_requests": True,
            "semantic_cache": "bypassed using evaluation_mode",
            "human_approval": "bypassed using evaluation_mode",
        },
        "limitations": [
            "The sample warehouse is small and synthetic; results do not establish general enterprise SQL accuracy.",
            "Gold SQL is executed against the same local DuckDB database to produce expected results.",
            "RAG retrieval uses the locally configured Qdrant collection and embedding model; its quality is not independently graded here.",
            "This is a fixed synthetic-warehouse test set, not a statistical estimate of production performance.",
            "SQL correction retries are disabled; transient rate-limit retries may make multiple HTTP attempts for one case. Daily token quota exhaustion is detected and not retried.",
        ],
        "cases": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"groq_eval_100_{args.run_id}.json"
    output_path.write_text(json.dumps(report, indent=2, default=json_safe), encoding="utf-8")

    print("\n========== GROQ EVALUATION SUMMARY ==========")
    print(f"Passed: {passed}/{len(cases)} ({report['pass_rate_percent']}%)")
    print(f"Failed: {failed} | Errors: {errors}")
    print(f"Groq generation calls: {usage['calls']}")
    print(f"Token usage: {usage['total_tokens']}")
    print(f"Median latency: {median_latency:.3f}s")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
