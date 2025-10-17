"""
NBA MCP Synthesis - Prometheus Metrics Endpoint
Expose application metrics for Prometheus scraping
"""

import time
import logging
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    start_http_server,
    generate_latest,
)
from flask import Flask, Response, request
import threading
import os

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

SECRET_LOADING_TIME = Histogram(
    "secret_loading_duration_seconds", "Time taken to load secrets", ["secret_type"]
)

API_CALL_COUNT = Counter("api_calls_total", "Total API calls", ["provider", "status"])

API_CALL_DURATION = Histogram(
    "api_call_duration_seconds", "API call duration in seconds", ["provider"]
)

DATABASE_QUERY_COUNT = Counter(
    "database_queries_total", "Total database queries", ["operation", "status"]
)

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)

S3_OPERATION_COUNT = Counter(
    "s3_operations_total", "Total S3 operations", ["operation", "status"]
)

S3_OPERATION_DURATION = Histogram(
    "s3_operation_duration_seconds", "S3 operation duration in seconds", ["operation"]
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections", "Number of active connections", ["connection_type"]
)

SECRET_VALIDATION_FAILURES = Counter(
    "secret_validation_failures_total",
    "Total secret validation failures",
    ["secret_name", "validation_type"],
)

SECRET_REFRESH_COUNT = Counter(
    "secret_refresh_total", "Total secret refreshes", ["secret_name", "status"]
)

MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes", ["component"])

CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage percentage", ["component"])


class MetricsCollector:
    """Collect and expose application metrics"""

    def __init__(self, port: int = 9090):
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes for metrics"""

        @self.app.route("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            return Response(generate_latest(), mimetype="text/plain")

        @self.app.route("/health")
        def health():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": time.time()}

        @self.app.route("/")
        def root():
            """Root endpoint"""
            return {"service": "nba-mcp-synthesis-metrics", "version": "1.0.0"}

    def start(self):
        """Start the metrics server"""
        try:
            start_http_server(self.port)
            logger.info(f"Metrics server started on port {self.port}")

            # Start Flask app in a separate thread
            flask_thread = threading.Thread(
                target=self.app.run,
                kwargs={"host": "0.0.0.0", "port": self.port, "debug": False},
                daemon=True,
            )
            flask_thread.start()

        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    def record_secret_loading(self, secret_type: str, duration: float):
        """Record secret loading metrics"""
        SECRET_LOADING_TIME.labels(secret_type=secret_type).observe(duration)

    def record_api_call(self, provider: str, status: str, duration: float):
        """Record API call metrics"""
        API_CALL_COUNT.labels(provider=provider, status=status).inc()
        API_CALL_DURATION.labels(provider=provider).observe(duration)

    def record_database_query(self, operation: str, status: str, duration: float):
        """Record database query metrics"""
        DATABASE_QUERY_COUNT.labels(operation=operation, status=status).inc()
        DATABASE_QUERY_DURATION.labels(operation=operation).observe(duration)

    def record_s3_operation(self, operation: str, status: str, duration: float):
        """Record S3 operation metrics"""
        S3_OPERATION_COUNT.labels(operation=operation, status=status).inc()
        S3_OPERATION_DURATION.labels(operation=operation).observe(duration)

    def set_active_connections(self, connection_type: str, count: int):
        """Set active connections count"""
        ACTIVE_CONNECTIONS.labels(connection_type=connection_type).set(count)

    def record_secret_validation_failure(self, secret_name: str, validation_type: str):
        """Record secret validation failure"""
        SECRET_VALIDATION_FAILURES.labels(
            secret_name=secret_name, validation_type=validation_type
        ).inc()

    def record_secret_refresh(self, secret_name: str, status: str):
        """Record secret refresh"""
        SECRET_REFRESH_COUNT.labels(secret_name=secret_name, status=status).inc()

    def set_memory_usage(self, component: str, usage_bytes: int):
        """Set memory usage"""
        MEMORY_USAGE.labels(component=component).set(usage_bytes)

    def set_cpu_usage(self, component: str, usage_percent: float):
        """Set CPU usage"""
        CPU_USAGE.labels(component=component).set(usage_percent)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector


def start_metrics_server():
    """Start the metrics server"""
    metrics_collector.start()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Start metrics server
    start_metrics_server()

    # Keep the process running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Metrics server stopped")
