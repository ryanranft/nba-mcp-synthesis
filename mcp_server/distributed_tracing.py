"""Distributed Tracing - IMPORTANT 15"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from functools import wraps
from typing import Callable, Any
import logging
import time

logger = logging.getLogger(__name__)


class DistributedTracer:
    """Distributed tracing with OpenTelemetry"""

    def __init__(
        self,
        service_name: str = "nba-mcp",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831
    ):
        """
        Initialize distributed tracer

        Args:
            service_name: Name of the service
            jaeger_host: Jaeger agent host
            jaeger_port: Jaeger agent port
        """
        self.service_name = service_name

        # Create resource
        resource = Resource(attributes={
            "service.name": service_name,
            "service.version": "1.0.0"
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )

        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        logger.info(f"✅ Distributed tracing initialized for {service_name}")

    def start_span(self, name: str, **attributes):
        """
        Start a new span

        Args:
            name: Span name
            **attributes: Span attributes

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            name,
            attributes=attributes
        )

    def trace_function(self, span_name: str = None):
        """
        Decorator to trace a function

        Args:
            span_name: Custom span name (defaults to function name)

        Usage:
            @trace_function("my_operation")
            def my_function():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                name = span_name or func.__name__

                with self.start_span(
                    name,
                    function=func.__name__,
                    module=func.__module__
                ) as span:
                    try:
                        # Add function args as attributes
                        if args:
                            span.set_attribute("args.count", len(args))
                        if kwargs:
                            span.set_attribute("kwargs.count", len(kwargs))

                        # Execute function
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time

                        # Add success attributes
                        span.set_attribute("status", "success")
                        span.set_attribute("duration_ms", duration * 1000)

                        return result

                    except Exception as e:
                        # Add error attributes
                        span.set_attribute("status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.record_exception(e)
                        raise

            return wrapper
        return decorator

    def add_event(self, name: str, **attributes):
        """
        Add an event to the current span

        Args:
            name: Event name
            **attributes: Event attributes
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes)


# Global tracer
_tracer: DistributedTracer = None


def get_tracer() -> DistributedTracer:
    """Get global distributed tracer"""
    global _tracer
    if _tracer is None:
        _tracer = DistributedTracer()
    return _tracer


def trace(span_name: str = None):
    """
    Decorator for tracing functions

    Usage:
        @trace("query_database")
        def query_db(query: str):
            ...
    """
    tracer = get_tracer()
    return tracer.trace_function(span_name)


# Example traced functions
@trace("fetch_player_stats")
def fetch_player_stats(player_id: int, season: str):
    """Fetch player statistics"""
    tracer = get_tracer()

    with tracer.start_span(
        "database_query",
        player_id=player_id,
        season=season
    ):
        # Simulate database query
        time.sleep(0.1)
        return {"player_id": player_id, "points": 25}


@trace("calculate_metrics")
def calculate_metrics(stats: dict):
    """Calculate advanced metrics"""
    tracer = get_tracer()

    with tracer.start_span("metric_calculation"):
        # Simulate calculation
        time.sleep(0.05)
        tracer.add_event("metrics_calculated", metric_count=5)
        return {"efficiency": 0.85}


# Example usage
if __name__ == "__main__":
    # Initialize tracer
    tracer = DistributedTracer()

    # Traced operations
    with tracer.start_span("process_player_request"):
        stats = fetch_player_stats(player_id=123, season="2024")
        metrics = calculate_metrics(stats)

        tracer.add_event("processing_complete", result_count=1)

    logger.info("✅ Tracing example complete - view in Jaeger UI at http://localhost:16686")

