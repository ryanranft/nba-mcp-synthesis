#!/usr/bin/env python3
"""
Distributed Tracing with OpenTelemetry and Jaeger
Provides end-to-end request tracking across all services
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
import asyncio

# Try to import OpenTelemetry (optional dependency)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None
    TracerProvider = None

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for distributed tracing"""

    def __init__(
        self,
        service_name: str = "nba-mcp-synthesis",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        enabled: bool = True
    ):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.enabled = enabled and TRACING_AVAILABLE


class DistributedTracer:
    """Manages distributed tracing with Jaeger"""

    def __init__(self, config: Optional[TracingConfig] = None):
        self.config = config or TracingConfig()
        self.tracer = None
        self.provider = None

        if self.config.enabled:
            self._initialize_tracing()
        else:
            if not TRACING_AVAILABLE:
                logger.info("OpenTelemetry not installed. Tracing disabled.")
            else:
                logger.info("Tracing disabled by configuration")

    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource with service info
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": "1.0.0",
                "deployment.environment": os.getenv("ENVIRONMENT", "development")
            })

            # Create tracer provider
            self.provider = TracerProvider(resource=resource)

            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_host,
                agent_port=self.config.jaeger_port,
            )

            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self.provider.add_span_processor(span_processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self.provider)

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

            # Auto-instrument libraries
            RequestsInstrumentor().instrument()
            AsyncioInstrumentor().instrument()

            logger.info(f"✅ Distributed tracing initialized (Jaeger: {self.config.jaeger_host}:{self.config.jaeger_port})")

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            self.config.enabled = False

    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[Any] = None
    ):
        """
        Create a new span

        Args:
            name: Span name
            attributes: Optional attributes to add to span
            parent_context: Optional parent context for nested spans

        Returns:
            Span context manager or no-op context manager
        """
        if not self.config.enabled or not self.tracer:
            return _NoOpSpan()

        try:
            span = self.tracer.start_span(
                name,
                context=parent_context,
                attributes=attributes or {}
            )
            return span
        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            return _NoOpSpan()

    def trace_function(
        self,
        span_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to trace a function

        Args:
            span_name: Optional span name (defaults to function name)
            attributes: Optional attributes to add to span

        Example:
            @tracer.trace_function()
            async def my_function(arg1, arg2):
                return result
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.config.enabled:
                    return await func(*args, **kwargs)

                name = span_name or f"{func.__module__}.{func.__name__}"
                attrs = attributes or {}

                # Add function info
                attrs["function.name"] = func.__name__
                attrs["function.module"] = func.__module__

                with self.create_span(name, attrs) as span:
                    try:
                        result = await func(*args, **kwargs)
                        if hasattr(span, 'set_status'):
                            span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if hasattr(span, 'set_status'):
                            span.set_status(
                                Status(StatusCode.ERROR, str(e))
                            )
                            span.set_attribute("exception.type", type(e).__name__)
                            span.set_attribute("exception.message", str(e))
                        raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.config.enabled:
                    return func(*args, **kwargs)

                name = span_name or f"{func.__module__}.{func.__name__}"
                attrs = attributes or {}

                attrs["function.name"] = func.__name__
                attrs["function.module"] = func.__module__

                with self.create_span(name, attrs) as span:
                    try:
                        result = func(*args, **kwargs)
                        if hasattr(span, 'set_status'):
                            span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if hasattr(span, 'set_status'):
                            span.set_status(
                                Status(StatusCode.ERROR, str(e))
                            )
                            span.set_attribute("exception.type", type(e).__name__)
                            span.set_attribute("exception.message", str(e))
                        raise

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the current span"""
        if not self.config.enabled:
            return

        try:
            span = trace.get_current_span()
            if span:
                span.add_event(name, attributes or {})
        except Exception as e:
            logger.debug(f"Failed to add event: {e}")

    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the current span"""
        if not self.config.enabled:
            return

        try:
            span = trace.get_current_span()
            if span:
                span.set_attribute(key, value)
        except Exception as e:
            logger.debug(f"Failed to set attribute: {e}")

    def shutdown(self):
        """Shutdown tracing provider"""
        if self.provider:
            try:
                self.provider.shutdown()
                logger.info("Tracing provider shutdown")
            except Exception as e:
                logger.error(f"Error shutting down tracing: {e}")


class _NoOpSpan:
    """No-op span for when tracing is disabled"""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_status(self, *args, **kwargs):
        pass

    def set_attribute(self, *args, **kwargs):
        pass

    def add_event(self, *args, **kwargs):
        pass


# Global tracer instance
_tracer_instance: Optional[DistributedTracer] = None


def get_tracer() -> DistributedTracer:
    """Get or create global tracer instance"""
    global _tracer_instance

    if _tracer_instance is None:
        # Read config from environment
        config = TracingConfig(
            service_name=os.getenv("TRACING_SERVICE_NAME", "nba-mcp-synthesis"),
            jaeger_host=os.getenv("JAEGER_HOST", "localhost"),
            jaeger_port=int(os.getenv("JAEGER_PORT", "6831")),
            enabled=os.getenv("TRACING_ENABLED", "true").lower() == "true"
        )
        _tracer_instance = DistributedTracer(config)

    return _tracer_instance


# Convenience decorator
def trace(span_name: Optional[str] = None, **attributes):
    """
    Convenience decorator for tracing functions

    Example:
        @trace("my_operation", component="synthesis")
        async def my_function():
            pass
    """
    tracer = get_tracer()
    return tracer.trace_function(span_name, attributes)


# Context manager for manual spans
class traced_span:
    """
    Context manager for creating traced spans

    Example:
        with traced_span("database_query", db="postgres") as span:
            result = await db.query(sql)
            span.set_attribute("rows_returned", len(result))
    """

    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
        self.tracer = get_tracer()
        self.span = None

    def __enter__(self):
        self.span = self.tracer.create_span(self.name, self.attributes)
        if hasattr(self.span, '__enter__'):
            return self.span.__enter__()
        return self

    def __exit__(self, *args):
        if hasattr(self.span, '__exit__'):
            return self.span.__exit__(*args)
        return False

    def set_attribute(self, key: str, value: Any):
        """Set attribute on the span"""
        if self.span and hasattr(self.span, 'set_attribute'):
            self.span.set_attribute(key, value)

    def add_event(self, name: str, **attributes):
        """Add event to the span"""
        if self.span and hasattr(self.span, 'add_event'):
            self.span.add_event(name, attributes)


# CLI for testing
if __name__ == "__main__":
    import sys

    print("="*70)
    print("NBA MCP Synthesis - Distributed Tracing Test")
    print("="*70)
    print()

    if not TRACING_AVAILABLE:
        print("❌ OpenTelemetry not installed")
        print()
        print("To install:")
        print("pip install opentelemetry-api opentelemetry-sdk \\")
        print("            opentelemetry-exporter-jaeger \\")
        print("            opentelemetry-instrumentation-requests \\")
        print("            opentelemetry-instrumentation-asyncio")
        sys.exit(1)

    # Create tracer
    config = TracingConfig(enabled=True)
    tracer = DistributedTracer(config)

    if not tracer.config.enabled:
        print("❌ Tracing initialization failed")
        sys.exit(1)

    print(f"✅ Tracing initialized")
    print(f"   Service: {config.service_name}")
    print(f"   Jaeger: {config.jaeger_host}:{config.jaeger_port}")
    print()

    # Test span creation
    print("Testing span creation...")

    async def test_traced_function():
        @trace("test_operation", component="test")
        async def my_operation():
            await asyncio.sleep(0.1)
            return {"result": "success"}

        result = await my_operation()
        return result

    # Run test
    result = asyncio.run(test_traced_function())
    print(f"✅ Traced function executed: {result}")
    print()

    # Test manual span
    print("Testing manual span...")
    with traced_span("manual_operation", test="true") as span:
        span.set_attribute("custom_attribute", "value")
        span.add_event("test_event", detail="event data")

    print("✅ Manual span created")
    print()

    # Shutdown
    tracer.shutdown()

    print("="*70)
    print("✅ Tracing test complete!")
    print()
    print("To view traces:")
    print("1. Start Jaeger: docker-compose -f docker-compose.jaeger.yml up -d")
    print("2. Open: http://localhost:16686")
    print("3. Select service: nba-mcp-synthesis")
    print("="*70)
