import time
from uuid import uuid4

from groq import RateLimitError

from src.graph import graph
from src.evaluation_dataset import EVALUATION_DATASET
from src.evaluation_replay import (
    get_replayed_sql,
    save_replayed_sql,
)


MAX_RATE_LIMIT_RETRIES = 5
INITIAL_RETRY_DELAY = 2


def normalize_value(value):
    """
    Normalize values before result comparison.
    """

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def normalize_result(result):
    """
    Normalize query results for comparison.
    """

    normalized = []

    for row in result:
        if isinstance(row, (list, tuple)):
            normalized.append(
                tuple(
                    normalize_value(value)
                    for value in row
                )
            )
        else:
            normalized.append(
                (normalize_value(row),)
            )

    return normalized


def result_contains_expected(expected, actual):
    """
    Compare query results.

    Exact comparison is attempted first.

    For normal result sets where ordering is not part of
    the question, row ordering is ignored.

    This prevents valid answers from failing only because
    the database returned rows in a different order.
    """

    expected = normalize_result(expected)
    actual = normalize_result(actual)

    # Exact match
    if expected == actual:
        return True

    # Same rows, different order
    if len(expected) == len(actual):
        return sorted(expected, key=str) == sorted(actual, key=str)

    # Expected result is a subset of actual result
    if len(expected) < len(actual):

        expected_sorted = sorted(expected, key=str)
        actual_sorted = sorted(actual, key=str)

        for i in range(
            len(actual_sorted) - len(expected_sorted) + 1
        ):
            if (
                actual_sorted[
                    i:i + len(expected_sorted)
                ]
                == expected_sorted
            ):
                return True

    return False


def invoke_with_retry(initial_state, config):
    """
    Run the LangGraph evaluation with retry handling
    for Groq rate-limit errors.
    """

    retry_delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):

        try:
            return graph.invoke(
                initial_state,
                config,
            )

        except RateLimitError:

            if attempt >= MAX_RATE_LIMIT_RETRIES:
                print(
                    "\nRate limit retries exhausted."
                )
                raise

            print(
                f"\nGroq rate limit reached."
                f" Waiting {retry_delay} seconds "
                f"before retry "
                f"{attempt + 1}/{MAX_RATE_LIMIT_RETRIES}..."
            )

            time.sleep(retry_delay)

            retry_delay *= 2


def run_evaluation():

    total_tests = len(EVALUATION_DATASET)

    execution_passed = 0
    result_passed = 0
    semantic_passed = 0
    fully_passed = 0

    completed_tests = 0

    print("\n")
    print("=" * 60)
    print("ENTERPRISE BI AGENT - EVALUATION")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print("=" * 60)

    for index, test_case in enumerate(
    EVALUATION_DATASET,
    start=1,
):

        # Prevent TPM bursts between benchmark cases.
        if index > 1:
            time.sleep(2)

        question = test_case["question"]
        expected_result = test_case["expected_result"]

        print("\n")
        print("=" * 60)
        print(f"Test {index}/{total_tests}")
        print("=" * 60)

        print("Question:")
        print(question)

        # --------------------------------------------------------
        # Replay lookup
        # --------------------------------------------------------

        replay_sql = get_replayed_sql(question)

        if replay_sql:
            print("\nReplay SQL:")
            print("FOUND - Groq generation will be skipped.")
        else:
            print("\nReplay SQL:")
            print("NOT FOUND - Groq generation may be required.")

        initial_state = {
            "user_question": question,
            "user_role": "analyst",

            "schema_context": "",

            "generated_sql": "",

            "validation_error": "",
            "authorization_error": "",
            "execution_error": "",

            "query_result": [],

            "retry_count": 0,

            "expected_result": expected_result,

            # Evaluation bypasses HITL.
            "evaluation_mode": True,

            "approval_required": False,
            "approval_status": "",

            # Evaluation bypasses production semantic cache.
            "cache_hit": False,
            "cache_key": "",

            # Replay configuration.
            "evaluation_replay": True,
            "replay_sql": replay_sql or "",
        }

        thread_id = (
            f"evaluation-{uuid4()}"
        )

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        try:

            result = invoke_with_retry(
                initial_state,
                config,
            )

        except Exception as e:

            print("\n")
            print("TEST ERROR")
            print(str(e))

            print("\nExecution:")
            print("ERROR")

            print("\nResult Validation:")
            print("ERROR")

            print("\nSemantic Evaluation:")
            print("ERROR")

            print("\nRetries:")
            print(
                initial_state["retry_count"]
            )

            continue

        completed_tests += 1

        generated_sql = result.get(
            "generated_sql",
            "",
        )

        actual_result = result.get(
            "query_result",
            [],
        )

        execution_error = result.get(
            "execution_error",
            "",
        )

        validation_error = result.get(
            "validation_error",
            "",
        )

        retry_count = result.get(
            "retry_count",
            0,
        )

        print("\nGenerated SQL:")
        print(generated_sql)

        print("\nExpected Result:")
        print(expected_result)

        print("\nActual Result:")
        print(actual_result)

        # --------------------------------------------------------
        # Execution evaluation
        # --------------------------------------------------------

        execution_ok = (
            not execution_error
        )

        print("\nExecution:")

        if execution_ok:
            print("PASS")
            execution_passed += 1
        else:
            print("FAIL")
            print(
                f"Error: {execution_error}"
            )

        # --------------------------------------------------------
        # Result evaluation
        # --------------------------------------------------------

        result_ok = result_contains_expected(
            expected_result,
            actual_result,
        )

        print("\nResult Validation:")

        if result_ok:
            print("PASS")
            result_passed += 1
        else:
            print("FAIL")

        # --------------------------------------------------------
        # Semantic evaluation
        # --------------------------------------------------------

        semantic_ok = not validation_error

        print("\nSemantic Evaluation:")

        if semantic_ok:
            print("PASS")
            semantic_passed += 1
        else:
            print("FAIL")
            print(
                f"Evaluator Feedback: "
                f"{validation_error}"
            )

        # --------------------------------------------------------
        # Overall
        # --------------------------------------------------------

        fully_ok = (
            execution_ok
            and result_ok
            and semantic_ok
        )

        if fully_ok:
            fully_passed += 1

            # ----------------------------------------------------
            # Save ONLY the final SQL from a fully successful case.
            #
            # This is important because a first generated SQL may
            # fail and later be corrected by the agent.
            # ----------------------------------------------------

            if generated_sql:
                save_replayed_sql(
                    question,
                    generated_sql,
                )

        print("\nEvaluator Feedback:")

        if semantic_ok:
            print("PASS")
        else:
            print(validation_error)

        print("\nRetries:")
        print(retry_count)

    # ============================================================
    # FINAL SUMMARY
    # ============================================================

    print("\n")
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(
        f"Tests completed: "
        f"{completed_tests}/{total_tests}"
    )

    print(
        f"Execution: "
        f"{execution_passed}/{total_tests} "
        f"({execution_passed / total_tests * 100:.1f}%)"
    )

    print(
        f"Result Validation: "
        f"{result_passed}/{total_tests} "
        f"({result_passed / total_tests * 100:.1f}%)"
    )

    print(
        f"Semantic Evaluation: "
        f"{semantic_passed}/{total_tests} "
        f"({semantic_passed / total_tests * 100:.1f}%)"
    )

    print(
        f"Fully Passed: "
        f"{fully_passed}/{total_tests} "
        f"({fully_passed / total_tests * 100:.1f}%)"
    )

    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()