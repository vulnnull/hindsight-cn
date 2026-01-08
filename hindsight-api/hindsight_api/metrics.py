"""
OpenTelemetry metrics instrumentation for Hindsight API.

This module provides metrics for:
- Operation latency (retain, recall, reflect) with percentiles
- Token usage (input/output) per operation
- Per-bank granularity via labels
- LLM call latency and token usage with scope dimension
"""

import logging
import time
from contextlib import contextmanager

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource

# Custom bucket boundaries for operation duration (in seconds)
# Fine granularity in 0-30s range where most operations complete
DURATION_BUCKETS = (0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 60.0, 120.0)

# LLM duration buckets (finer granularity for faster LLM calls)
LLM_DURATION_BUCKETS = (0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0, 60.0, 120.0)


def get_token_bucket(token_count: int) -> str:
    """
    Convert a token count to a bucket label for use as a dimension.

    This allows analyzing token usage patterns without high-cardinality issues.

    Buckets:
    - "0-100": Very small requests/responses
    - "100-500": Small requests/responses
    - "500-1k": Medium requests/responses
    - "1k-5k": Large requests/responses
    - "5k-10k": Very large requests/responses
    - "10k-50k": Huge requests/responses
    - "50k+": Extremely large requests/responses

    Args:
        token_count: Number of tokens

    Returns:
        Bucket label string
    """
    if token_count < 100:
        return "0-100"
    elif token_count < 500:
        return "100-500"
    elif token_count < 1000:
        return "500-1k"
    elif token_count < 5000:
        return "1k-5k"
    elif token_count < 10000:
        return "5k-10k"
    elif token_count < 50000:
        return "10k-50k"
    else:
        return "50k+"


logger = logging.getLogger(__name__)

# Global meter instance
_meter = None


def initialize_metrics(service_name: str = "hindsight-api", service_version: str = "1.0.0"):
    """
    Initialize OpenTelemetry metrics with Prometheus exporter.

    This should be called once during application startup.

    Args:
        service_name: Name of the service for resource attributes
        service_version: Version of the service

    Returns:
        PrometheusMetricReader instance (for accessing metrics endpoint)
    """
    global _meter

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    # Create Prometheus metric reader
    prometheus_reader = PrometheusMetricReader()

    # Create view with custom bucket boundaries for duration histogram
    duration_view = View(
        instrument_name="hindsight.operation.duration",
        aggregation=ExplicitBucketHistogramAggregation(boundaries=DURATION_BUCKETS),
    )

    # Create view with custom bucket boundaries for LLM duration histogram
    llm_duration_view = View(
        instrument_name="hindsight.llm.duration",
        aggregation=ExplicitBucketHistogramAggregation(boundaries=LLM_DURATION_BUCKETS),
    )

    # Create meter provider with Prometheus exporter and custom views
    provider = MeterProvider(
        resource=resource, metric_readers=[prometheus_reader], views=[duration_view, llm_duration_view]
    )

    # Set the global meter provider
    metrics.set_meter_provider(provider)

    # Get meter for this application
    _meter = metrics.get_meter(__name__)

    return prometheus_reader


def get_meter():
    """Get the global meter instance."""
    if _meter is None:
        raise RuntimeError("Metrics not initialized. Call initialize_metrics() first.")
    return _meter


class MetricsCollectorBase:
    """Base class for metrics collectors."""

    @contextmanager
    def record_operation(
        self,
        operation: str,
        bank_id: str,
        source: str = "api",
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """Context manager to record operation duration and status."""
        raise NotImplementedError

    def record_llm_call(
        self,
        provider: str,
        model: str,
        scope: str,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
    ):
        """
        Record metrics for an LLM call.

        Args:
            provider: LLM provider name (openai, anthropic, gemini, groq, ollama, lmstudio)
            model: Model name
            scope: Scope identifier (e.g., "memory", "reflect", "entity_observation")
            duration: Call duration in seconds
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            success: Whether the call was successful
        """
        raise NotImplementedError


class NoOpMetricsCollector(MetricsCollectorBase):
    """No-op metrics collector that does nothing. Used when metrics are disabled."""

    @contextmanager
    def record_operation(
        self,
        operation: str,
        bank_id: str,
        source: str = "api",
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """No-op context manager."""
        yield

    def record_llm_call(
        self,
        provider: str,
        model: str,
        scope: str,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
    ):
        """No-op LLM call recording."""
        pass


class MetricsCollector(MetricsCollectorBase):
    """
    Collector for Hindsight API metrics.

    Provides methods to record latency and token usage for operations.
    """

    def __init__(self):
        self.meter = get_meter()

        # Operation latency histogram (in seconds)
        # Records duration of retain, recall, reflect operations
        self.operation_duration = self.meter.create_histogram(
            name="hindsight.operation.duration", description="Duration of Hindsight operations in seconds", unit="s"
        )

        # Operation counter (success/failure)
        self.operation_total = self.meter.create_counter(
            name="hindsight.operation.total", description="Total number of operations executed", unit="operations"
        )

        # LLM call latency histogram (in seconds)
        # Records duration of LLM API calls with provider, model, and scope dimensions
        self.llm_duration = self.meter.create_histogram(
            name="hindsight.llm.duration", description="Duration of LLM API calls in seconds", unit="s"
        )

        # LLM token usage counters with bucket labels
        self.llm_tokens_input = self.meter.create_counter(
            name="hindsight.llm.tokens.input", description="Number of input tokens for LLM calls", unit="tokens"
        )

        self.llm_tokens_output = self.meter.create_counter(
            name="hindsight.llm.tokens.output", description="Number of output tokens from LLM calls", unit="tokens"
        )

        # LLM call counter (success/failure)
        self.llm_calls_total = self.meter.create_counter(
            name="hindsight.llm.calls.total", description="Total number of LLM API calls", unit="calls"
        )

    @contextmanager
    def record_operation(
        self,
        operation: str,
        bank_id: str,
        source: str = "api",
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """
        Context manager to record operation duration and status.

        Usage:
            with metrics.record_operation("recall", bank_id="user123", source="api", budget="mid", max_tokens=4096):
                # ... perform operation
                pass

        Args:
            operation: Operation name (retain, recall, reflect, entity_observation)
            bank_id: Memory bank ID
            source: Source of the operation (api, reflect, internal)
            budget: Optional budget level (low, mid, high)
            max_tokens: Optional max tokens for the operation
        """
        start_time = time.time()
        attributes = {
            "operation": operation,
            "bank_id": bank_id,
            "source": source,
        }
        if budget:
            attributes["budget"] = budget
        if max_tokens:
            attributes["max_tokens"] = str(max_tokens)

        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            attributes["success"] = str(success).lower()

            # Record duration
            self.operation_duration.record(duration, attributes)

            # Record operation count
            self.operation_total.add(1, attributes)

    def record_llm_call(
        self,
        provider: str,
        model: str,
        scope: str,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
    ):
        """
        Record metrics for an LLM call.

        Args:
            provider: LLM provider name (openai, anthropic, gemini, groq, ollama, lmstudio)
            model: Model name
            scope: Scope identifier (e.g., "memory", "reflect", "entity_observation")
            duration: Call duration in seconds
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            success: Whether the call was successful
        """
        # Base attributes for all metrics
        base_attributes = {
            "provider": provider,
            "model": model,
            "scope": scope,
            "success": str(success).lower(),
        }

        # Record duration
        self.llm_duration.record(duration, base_attributes)

        # Record call count
        self.llm_calls_total.add(1, base_attributes)

        # Record tokens with bucket labels for cardinality control
        if input_tokens > 0:
            input_attributes = {
                **base_attributes,
                "token_bucket": get_token_bucket(input_tokens),
            }
            self.llm_tokens_input.add(input_tokens, input_attributes)

        if output_tokens > 0:
            output_attributes = {
                **base_attributes,
                "token_bucket": get_token_bucket(output_tokens),
            }
            self.llm_tokens_output.add(output_tokens, output_attributes)


# Global metrics collector instance (defaults to no-op)
_metrics_collector: MetricsCollectorBase = NoOpMetricsCollector()


def get_metrics_collector() -> MetricsCollectorBase:
    """
    Get the global metrics collector instance.

    Returns a no-op collector if metrics are not initialized.
    """
    return _metrics_collector


def create_metrics_collector() -> MetricsCollector:
    """
    Create and set the global metrics collector.

    Should be called after initialize_metrics().
    """
    global _metrics_collector
    _metrics_collector = MetricsCollector()
    return _metrics_collector
