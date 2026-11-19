import pytest
from httpx import AsyncClient
from app.core.telemetry import metrics_collector, trace_span


def test_metrics_collector():
    metrics_collector.record_call(status="completed")
    metrics_collector.record_call(status="failed")
    metrics_collector.record_unsupported_query()
    metrics_collector.record_latency("agent_execution", 150.0)
    metrics_collector.record_latency("agent_execution", 200.0)
    metrics_collector.record_tokens(1500)

    summary = metrics_collector.get_summary()
    assert summary["total_calls"] >= 2
    assert summary["failed_calls"] >= 1
    assert summary["tokens_consumed"] >= 1500
    assert summary["latencies"]["agent_execution"]["avg_ms"] > 0


def test_trace_span_context_manager():
    with trace_span("speech_to_text", {"provider": "deepgram"}):
        _ = 1 + 1
    summary = metrics_collector.get_summary()
    assert summary["latencies"]["speech_to_text"]["samples"] >= 1


@pytest.mark.asyncio
async def test_metrics_dashboard_api(client: AsyncClient):
    res = await client.get("/api/v1/metrics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "latencies" in data["data"]
    assert "tokens_consumed" in data["data"]
