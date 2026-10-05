from uuid import uuid4

from src.graph import graph
from src.evaluation_dataset import EVALUATION_DATASET
from src.evaluator import evaluate_sql


def normalize_result(result):
    """
    Normalize simple query results for comparison.
    """
    return [
        tuple(row) if isinstance(row, (list, tuple)) else (row,)
        for row in result
    ]


def result_contains_expected(actual, expected):
    """
    Check whether the expected values are present in the actual result.

    This allows the generated SQL to return additional columns while
    still checking the important expected values.
    """
    actual = normalize_result(actual)
    expected = normalize_result(expected)

    if len(actual) != len(expected):
        return False

    for expected_row, actual_row in zip(expected, actual):

        # Exact match
        if expected_row == actual_row:
            continue

        # Expected values appear as a subset of returned columns
        if len(expected_row) <= len(actual_row):
            found = False

            for start in range(
                len(actual_row) - len(expected_row) + 1
            ):
                if (
                    actual_row[
                        start:start + len(expected_row)
                    ]
                    == expected_row
                ):
                    found = True
                    break

            if found:
                continue

        return False

    return True


def run_evaluation():

    total = len(EVALUATION_DATASET)

    execution_passed = 0
    result_passed = 0
    semantic_passed = 0
    fully_passed = 0

    for i, test_case in enumerate(
        EVALUATION_DATASET,
        start=1,
    ):

        question = test_case["question"]
        expected_result = test_case["expected_result"]

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
            "evaluation_mode": True,
            "approval_required": False,
            "approval_status": "not_required",

            # Evaluation bypasses semantic cache.
            "cache_hit": False,
            "cache_key": "evaluation-bypass",
        }

        # Use a completely fresh checkpoint thread for every
        # evaluation case to prevent previous runs from
        # contaminating the current benchmark.
        thread_id = f"evaluation-{uuid4()}"

        result = graph.invoke(
            initial_state,
            {
                "configurable": {
                    "thread_id": thread_id,
                }
            },
        )

        actual_result = result["query_result"]
        generated_sql = result["generated_sql"]

        execution_ok = not result["execution_error"]

        result_ok = result_contains_expected(
            actual_result,
            expected_result,
        )

        semantic_ok, semantic_feedback = evaluate_sql(
            question,
            generated_sql,
            result["schema_context"],
        )

        if execution_ok:
            execution_passed += 1

        if result_ok:
            result_passed += 1

        if semantic_ok:
            semantic_passed += 1

        if (
            execution_ok
            and result_ok
            and semantic_ok
        ):
            fully_passed += 1

        print("\n" + "=" * 60)
        print(f"Test {i}/{total}")
        print("=" * 60)

        print(f"Question:\n{question}")

        print("\nGenerated SQL:")
        print(generated_sql)

        print("\nExpected Result:")
        print(expected_result)

        print("\nActual Result:")
        print(actual_result)

        print("\nExecution:")
        print(
            "PASS"
            if execution_ok
            else "FAIL"
        )

        print("\nResult Validation:")
        print(
            "PASS"
            if result_ok
            else "FAIL"
        )

        print("\nSemantic Evaluation:")
        print(
            "PASS"
            if semantic_ok
            else "FAIL"
        )

        print("\nEvaluator Feedback:")
        print(semantic_feedback)

        print("\nRetries:")
        print(result["retry_count"])

    execution_accuracy = (
        execution_passed / total
    ) * 100

    result_accuracy = (
        result_passed / total
    ) * 100

    semantic_accuracy = (
        semantic_passed / total
    ) * 100

    overall_accuracy = (
        fully_passed / total
    ) * 100

    print("\n")
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(
        f"Total Tests:          {total}"
    )

    print(
        f"Execution Passed:     "
        f"{execution_passed}/{total}"
    )

    print(
        f"Execution Accuracy:   "
        f"{execution_accuracy:.2f}%"
    )

    print(
        f"\nResult Validation:    "
        f"{result_passed}/{total}"
    )

    print(
        f"Result Accuracy:      "
        f"{result_accuracy:.2f}%"
    )

    print(
        f"\nSemantic Passed:      "
        f"{semantic_passed}/{total}"
    )

    print(
        f"Semantic Accuracy:    "
        f"{semantic_accuracy:.2f}%"
    )

    print(
        f"\nFully Passed:         "
        f"{fully_passed}/{total}"
    )

    print(
        f"Overall Accuracy:     "
        f"{overall_accuracy:.2f}%"
    )


if __name__ == "__main__":
    run_evaluation()