import time
from contextlib import contextmanager
from typing import Dict, Any, List
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from app.core.logger import logger

# Initialize OpenTelemetry Tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("personal_ai_twin", "1.0.0")


class MetricsCollector:
    """In-memory collector for real-time observability and dashboard analytics."""

    def __init__(self):
        self.call_count = 0
        self.failed_calls = 0
        self.unsupported_queries = 0
        self.latencies: Dict[str, List[float]] = {
            "incoming_call": [],
            "speech_to_text": [],
            "agent_execution": [],
            "gmail_retrieval": [],
            "calendar_retrieval": [],
            "evidence_validation": [],
            "time_to_first_spoken_response": [],
        }
        self.tokens_consumed = 0
        self.estimated_total_cost_usd = 0.0

    def record_call(self, status: str = "completed"):
        self.call_count += 1
        if status == "failed":
            self.failed_calls += 1

    def record_unsupported_query(self):
        self.unsupported_queries += 1

    def record_latency(self, metric_name: str, duration_ms: float):
        if metric_name in self.latencies:
            self.latencies[metric_name].append(duration_ms)

    def record_tokens(self, tokens: int):
        self.tokens_consumed += tokens
        # Approx $0.0001 per 1k tokens for modern Flash / Gemini API
        self.estimated_total_cost_usd += (tokens / 1000.0) * 0.00015

    def get_summary(self) -> Dict[str, Any]:
        """Compute aggregated statistics for the metrics dashboard."""
        def calc_avg(arr: List[float]) -> float:
            return round(sum(arr) / len(arr), 2) if arr else 0.0

        def calc_p95(arr: List[float]) -> float:
            if not arr:
                return 0.0
            sorted_arr = sorted(arr)
            idx = int(len(sorted_arr) * 0.95)
            return round(sorted_arr[min(idx, len(sorted_arr) - 1)], 2)

        failed_rate = round((self.failed_calls / self.call_count * 100), 2) if self.call_count else 0.0
        unsupported_rate = round((self.unsupported_queries / max(self.call_count, 1) * 100), 2)

        return {
            "total_calls": self.call_count,
            "failed_calls": self.failed_calls,
            "failed_call_rate_pct": failed_rate,
            "unsupported_response_rate_pct": unsupported_rate,
            "tokens_consumed": self.tokens_consumed,
            "estimated_cost_usd": round(self.estimated_total_cost_usd, 4),
            "latencies": {
                name: {
                    "avg_ms": calc_avg(values),
                    "p95_ms": calc_p95(values),
                    "samples": len(values),
                }
                for name, values in self.latencies.items()
            },
        }


metrics_collector = MetricsCollector()


@contextmanager
def trace_span(span_name: str, attributes: Dict[str, Any] | None = None):
    """Context manager for tracing execution spans and collecting latency."""
    t0 = time.perf_counter()
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        try:
            yield span
        finally:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            span.set_attribute("duration_ms", duration_ms)
            metrics_collector.record_latency(span_name, duration_ms)
