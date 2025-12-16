"""
OpenTelemetry metrics instrumentation for Hindsight API.

This module provides metrics for:
- Operation latency (retain, recall, reflect) with percentiles
- Token usage (input/output) per operation
- Per-bank granularity via labels
"""

import logging
import time
from contextlib import contextmanager

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

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

    # Create meter provider with Prometheus exporter
    provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])

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
    def record_operation(self, operation: str, bank_id: str, budget: str | None = None, max_tokens: int | None = None):
        """Context manager to record operation duration and status."""
        raise NotImplementedError

    def record_tokens(
        self,
        operation: str,
        bank_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """Record token usage for an operation."""
        raise NotImplementedError


class NoOpMetricsCollector(MetricsCollectorBase):
    """No-op metrics collector that does nothing. Used when metrics are disabled."""

    @contextmanager
    def record_operation(self, operation: str, bank_id: str, budget: str | None = None, max_tokens: int | None = None):
        """No-op context manager."""
        yield

    def record_tokens(
        self,
        operation: str,
        bank_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """No-op token recording."""
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

        # Token usage counters
        self.tokens_input = self.meter.create_counter(
            name="hindsight.tokens.input", description="Number of input tokens consumed", unit="tokens"
        )

        self.tokens_output = self.meter.create_counter(
            name="hindsight.tokens.output", description="Number of output tokens generated", unit="tokens"
        )

        # Operation counter (success/failure)
        self.operation_total = self.meter.create_counter(
            name="hindsight.operation.total", description="Total number of operations executed", unit="operations"
        )

    @contextmanager
    def record_operation(self, operation: str, bank_id: str, budget: str | None = None, max_tokens: int | None = None):
        """
        Context manager to record operation duration and status.

        Usage:
            with metrics.record_operation("recall", bank_id="user123", budget="mid", max_tokens=4096):
                # ... perform operation
                pass

        Args:
            operation: Operation name (retain, recall, reflect)
            bank_id: Memory bank ID
            budget: Optional budget level (low, mid, high)
            max_tokens: Optional max tokens for the operation
        """
        start_time = time.time()
        attributes = {
            "operation": operation,
            "bank_id": bank_id,
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

    def record_tokens(
        self,
        operation: str,
        bank_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        budget: str | None = None,
        max_tokens: int | None = None,
    ):
        """
        Record token usage for an operation.

        Args:
            operation: Operation name (retain, recall, reflect)
            bank_id: Memory bank ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            budget: Optional budget level
            max_tokens: Optional max tokens for the operation
        """
        attributes = {
            "operation": operation,
            "bank_id": bank_id,
        }
        if budget:
            attributes["budget"] = budget
        if max_tokens:
            attributes["max_tokens"] = str(max_tokens)

        if input_tokens > 0:
            self.tokens_input.add(input_tokens, attributes)

        if output_tokens > 0:
            self.tokens_output.add(output_tokens, attributes)


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
