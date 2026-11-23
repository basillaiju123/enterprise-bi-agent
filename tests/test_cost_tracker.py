from types import SimpleNamespace

from src import cost_tracker


def test_record_groq_usage_calculates_and_persists_cost(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cost_tracker,
        "DB_PATH",
        tmp_path / "api_usage.sqlite",
    )

    usage = SimpleNamespace(
        prompt_tokens=10_000,
        completion_tokens=2_000,
        total_tokens=12_000,
    )

    recorded = cost_tracker.record_groq_usage(
        usage,
        thread_id="test-thread",
    )
    cost_tracker.record_query_outcome("test-thread", "success")
    summary = cost_tracker.get_usage_summary()

    expected_usd = (10_000 * 0.075 + 2_000 * 0.30) / 1_000_000

    assert recorded["input_tokens"] == 10_000
    assert recorded["output_tokens"] == 2_000
    assert recorded["total_tokens"] == 12_000
    assert recorded["cost_usd"] == round(expected_usd, 8)
    assert summary["totals"]["llm_calls"] == 1
    assert summary["totals"]["successful_queries"] == 1
    assert summary["totals"]["average_cost_per_successful_query_inr"] > 0
