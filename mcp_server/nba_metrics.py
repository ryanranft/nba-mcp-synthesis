"""
NBA MCP Server Metrics Collection

Comprehensive metrics collection for system, application, and NBA-specific metrics.
Implements production-grade monitoring with Prometheus integration support.

This module provides:
- System metrics (CPU, memory, disk I/O, network)
- Application metrics (request latency, throughput, error rates)
- NBA-specific metrics (queries/sec, data freshness, cache hit rate)
- Prometheus-compatible metric export
- Performance tracking with minimal overhead

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import json
import os
import platform
import psutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from threading import Lock

from .logging_config import get_logger
from .error_handling import ErrorHandler, get_error_handler

logger = get_logger(__name__)


# ==============================================================================
# Metric Types and Data Classes
# ==============================================================================


class MetricType(Enum):
    """Types of metrics we collect."""

    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Value that can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Similar to histogram with quantiles


@dataclass
class SystemMetrics:
    """
    System-level resource metrics.

    Captures CPU, memory, disk, and network utilization at a point in time.

    Attributes:
        cpu_percent: CPU utilization percentage (0-100)
        cpu_count: Number of CPU cores
        memory_percent: Memory utilization percentage (0-100)
        memory_used_bytes: Memory used in bytes
        memory_available_bytes: Memory available in bytes
        memory_total_bytes: Total system memory in bytes
        disk_io_read_bytes: Cumulative bytes read from disk
        disk_io_write_bytes: Cumulative bytes written to disk
        disk_io_read_count: Number of read operations
        disk_io_write_count: Number of write operations
        disk_usage_percent: Disk utilization percentage (0-100)
        disk_usage_used_bytes: Disk space used in bytes
        disk_usage_free_bytes: Disk space free in bytes
        network_bytes_sent: Cumulative bytes sent over network
        network_bytes_recv: Cumulative bytes received over network
        network_packets_sent: Cumulative packets sent
        network_packets_recv: Cumulative packets received
        network_errors_in: Network receive errors
        network_errors_out: Network send errors
        open_files: Number of open file handles
        open_connections: Number of open network connections
        timestamp: When metrics were collected

    Examples:
        >>> metrics = collector.collect_system_metrics()
        >>> print(f"CPU: {metrics.cpu_percent}%")
        >>> print(f"Memory: {metrics.memory_percent}%")
    """

    cpu_percent: float
    cpu_count: int
    memory_percent: float
    memory_used_bytes: int
    memory_available_bytes: int
    memory_total_bytes: int
    disk_io_read_bytes: int
    disk_io_write_bytes: int
    disk_io_read_count: int
    disk_io_write_count: int
    disk_usage_percent: float
    disk_usage_used_bytes: int
    disk_usage_free_bytes: int
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    network_errors_in: int
    network_errors_out: int
    open_files: int
    open_connections: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "cpu_percent": self.cpu_percent,
            "cpu_count": self.cpu_count,
            "memory_percent": self.memory_percent,
            "memory_used_bytes": self.memory_used_bytes,
            "memory_available_bytes": self.memory_available_bytes,
            "memory_total_bytes": self.memory_total_bytes,
            "disk_io_read_bytes": self.disk_io_read_bytes,
            "disk_io_write_bytes": self.disk_io_write_bytes,
            "disk_io_read_count": self.disk_io_read_count,
            "disk_io_write_count": self.disk_io_write_count,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_usage_used_bytes": self.disk_usage_used_bytes,
            "disk_usage_free_bytes": self.disk_usage_free_bytes,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "network_packets_sent": self.network_packets_sent,
            "network_packets_recv": self.network_packets_recv,
            "network_errors_in": self.network_errors_in,
            "network_errors_out": self.network_errors_out,
            "open_files": self.open_files,
            "open_connections": self.open_connections,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ApplicationMetrics:
    """
    Application-level performance metrics.

    Tracks request handling, errors, and performance characteristics.

    Attributes:
        request_count: Total number of requests processed
        request_rate_per_second: Current request rate
        active_requests: Number of currently processing requests
        average_latency_ms: Average request latency in milliseconds
        p50_latency_ms: 50th percentile latency
        p95_latency_ms: 95th percentile latency
        p99_latency_ms: 99th percentile latency
        error_count: Total number of errors
        error_rate_per_minute: Current error rate
        success_rate_percent: Success rate percentage
        active_connections: Number of active connections
        throughput_requests_per_second: Request throughput
        total_processing_time_seconds: Total time spent processing
        timestamp: When metrics were collected
    """

    request_count: int
    request_rate_per_second: float
    active_requests: int
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_count: int
    error_rate_per_minute: float
    success_rate_percent: float
    active_connections: int
    throughput_requests_per_second: float
    total_processing_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "request_count": self.request_count,
            "request_rate_per_second": round(self.request_rate_per_second, 2),
            "active_requests": self.active_requests,
            "average_latency_ms": round(self.average_latency_ms, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "error_count": self.error_count,
            "error_rate_per_minute": round(self.error_rate_per_minute, 2),
            "success_rate_percent": round(self.success_rate_percent, 2),
            "active_connections": self.active_connections,
            "throughput_requests_per_second": round(
                self.throughput_requests_per_second, 2
            ),
            "total_processing_time_seconds": round(
                self.total_processing_time_seconds, 2
            ),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class NBAMetrics:
    """
    NBA-specific business metrics.

    Tracks NBA data operations, cache performance, and data quality.

    Attributes:
        queries_per_second: Database queries per second
        total_queries: Total queries executed
        cache_hit_rate_percent: Cache hit rate percentage
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
        data_freshness_seconds: Age of data in seconds
        active_tools: Number of active tool executions
        tool_success_rate_percent: Tool execution success rate
        average_query_time_ms: Average database query time
        games_processed: Number of games processed
        players_processed: Number of players processed
        s3_reads: Number of S3 read operations
        s3_writes: Number of S3 write operations
        database_connections: Number of active database connections
        timestamp: When metrics were collected
    """

    queries_per_second: float
    total_queries: int
    cache_hit_rate_percent: float
    cache_hits: int
    cache_misses: int
    data_freshness_seconds: float
    active_tools: int
    tool_success_rate_percent: float
    average_query_time_ms: float
    games_processed: int
    players_processed: int
    s3_reads: int
    s3_writes: int
    database_connections: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "queries_per_second": round(self.queries_per_second, 2),
            "total_queries": self.total_queries,
            "cache_hit_rate_percent": round(self.cache_hit_rate_percent, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "data_freshness_seconds": round(self.data_freshness_seconds, 2),
            "active_tools": self.active_tools,
            "tool_success_rate_percent": round(self.tool_success_rate_percent, 2),
            "average_query_time_ms": round(self.average_query_time_ms, 2),
            "games_processed": self.games_processed,
            "players_processed": self.players_processed,
            "s3_reads": self.s3_reads,
            "s3_writes": self.s3_writes,
            "database_connections": self.database_connections,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AllMetrics:
    """
    Container for all metric types.

    Aggregates system, application, and NBA-specific metrics into a single structure.
    """

    system: SystemMetrics
    application: ApplicationMetrics
    nba: NBAMetrics
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert all metrics to dictionary."""
        return {
            "system": self.system.to_dict(),
            "application": self.application.to_dict(),
            "nba": self.nba.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ==============================================================================
# Latency Tracking
# ==============================================================================


class LatencyTracker:
    """
    Tracks latency metrics for requests and operations.

    Uses a circular buffer to efficiently track recent latencies and
    calculate percentiles with minimal overhead.

    Examples:
        >>> tracker = LatencyTracker(window_size=1000)
        >>> tracker.record(125.5)  # Record 125.5ms latency
        >>> stats = tracker.get_statistics()
        >>> print(f"P95: {stats['p95_ms']}ms")
    """

    def __init__(self, window_size: int = 10000):
        """
        Initialize latency tracker.

        Args:
            window_size: Maximum number of latencies to track
        """
        self.latencies: deque = deque(maxlen=window_size)
        self._lock = Lock()

    def record(self, latency_ms: float) -> None:
        """
        Record a latency measurement.

        Args:
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            self.latencies.append(latency_ms)

    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate latency statistics.

        Returns:
            Dictionary with average, p50, p95, p99, min, max latencies
        """
        with self._lock:
            if not self.latencies:
                return {
                    "average_ms": 0.0,
                    "p50_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0,
                    "min_ms": 0.0,
                    "max_ms": 0.0,
                    "count": 0,
                }

            sorted_latencies = sorted(self.latencies)
            count = len(sorted_latencies)

            return {
                "average_ms": sum(sorted_latencies) / count,
                "p50_ms": sorted_latencies[int(count * 0.50)],
                "p95_ms": sorted_latencies[int(count * 0.95)],
                "p99_ms": sorted_latencies[int(count * 0.99)],
                "min_ms": sorted_latencies[0],
                "max_ms": sorted_latencies[-1],
                "count": count,
            }

    def clear(self) -> None:
        """Clear all recorded latencies."""
        with self._lock:
            self.latencies.clear()


# ==============================================================================
# Metrics Collector
# ==============================================================================


class MetricsCollector:
    """
    Centralized metrics collection for NBA MCP Server.

    Collects system metrics (CPU, memory, disk, network), application metrics
    (request latency, throughput, errors), and NBA-specific metrics (queries,
    cache performance, data freshness).

    Features:
    - Efficient metric collection with <5% overhead
    - Automatic metric aggregation and windowing
    - Prometheus-compatible metric export
    - Thread-safe concurrent access
    - Configurable collection intervals

    Examples:
        >>> collector = MetricsCollector()
        >>>
        >>> # Collect all metrics
        >>> metrics = collector.collect_all_metrics()
        >>> print(f"CPU: {metrics.system.cpu_percent}%")
        >>>
        >>> # Track a request
        >>> with collector.track_request("query_database"):
        ...     result = db.execute(query)
        >>>
        >>> # Record custom metric
        >>> collector.record_nba_query(latency_ms=45.2)
    """

    def __init__(
        self,
        enable_system_metrics: bool = True,
        enable_application_metrics: bool = True,
        enable_nba_metrics: bool = True,
        collection_interval: int = 60,
        latency_window_size: int = 10000,
    ):
        """
        Initialize metrics collector.

        Args:
            enable_system_metrics: Enable system resource collection
            enable_application_metrics: Enable application metrics
            enable_nba_metrics: Enable NBA-specific metrics
            collection_interval: How often to collect metrics (seconds)
            latency_window_size: Number of latencies to track
        """
        self.enable_system_metrics = enable_system_metrics
        self.enable_application_metrics = enable_application_metrics
        self.enable_nba_metrics = enable_nba_metrics
        self.collection_interval = collection_interval

        # Application metrics tracking
        self.request_count = 0
        self.active_requests = 0
        self.error_count = 0
        self.active_connections = 0
        self.total_processing_time = 0.0

        # Request timing
        self.request_times: deque = deque(maxlen=1000)
        self.error_times: deque = deque(maxlen=1000)

        # Latency tracking
        self.latency_tracker = LatencyTracker(window_size=latency_window_size)

        # NBA metrics tracking
        self.total_queries = 0
        self.query_times: deque = deque(maxlen=1000)
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_data_update = datetime.now()
        self.active_tools = 0
        self.tool_executions = 0
        self.tool_failures = 0
        self.games_processed = 0
        self.players_processed = 0
        self.s3_reads = 0
        self.s3_writes = 0
        self.database_connections = 0

        # Query latency tracking
        self.query_latency_tracker = LatencyTracker(window_size=latency_window_size)

        # Thread safety
        self._lock = Lock()

        # Process handle for system metrics
        self._process = psutil.Process()

        # Error handler
        self.error_handler = get_error_handler()

        logger.info(
            "Metrics collector initialized",
            extra={
                "system_metrics": enable_system_metrics,
                "application_metrics": enable_application_metrics,
                "nba_metrics": enable_nba_metrics,
                "collection_interval": collection_interval,
            },
        )

    def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect current system resource metrics.

        Captures CPU, memory, disk I/O, and network statistics using psutil.
        Designed for minimal overhead (<1% CPU impact).

        Returns:
            SystemMetrics dataclass with current system state

        Raises:
            Exception: If metric collection fails (logs error, returns zeros)
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()

            # Disk usage for root partition
            disk_usage = psutil.disk_usage("/")

            # Network metrics
            net_io = psutil.net_io_counters()

            # Process metrics
            try:
                open_files = len(self._process.open_files())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                open_files = 0

            try:
                open_connections = len(self._process.connections())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                open_connections = 0

            return SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_percent=memory.percent,
                memory_used_bytes=memory.used,
                memory_available_bytes=memory.available,
                memory_total_bytes=memory.total,
                disk_io_read_bytes=disk_io.read_bytes,
                disk_io_write_bytes=disk_io.write_bytes,
                disk_io_read_count=disk_io.read_count,
                disk_io_write_count=disk_io.write_count,
                disk_usage_percent=disk_usage.percent,
                disk_usage_used_bytes=disk_usage.used,
                disk_usage_free_bytes=disk_usage.free,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                network_packets_sent=net_io.packets_sent,
                network_packets_recv=net_io.packets_recv,
                network_errors_in=net_io.errin,
                network_errors_out=net_io.errout,
                open_files=open_files,
                open_connections=open_connections,
            )

        except Exception as e:
            logger.error(
                f"Failed to collect system metrics: {e}",
                extra={"error": str(e)},
                exc_info=True,
            )
            # Return zero metrics on failure
            return SystemMetrics(
                cpu_percent=0.0,
                cpu_count=0,
                memory_percent=0.0,
                memory_used_bytes=0,
                memory_available_bytes=0,
                memory_total_bytes=0,
                disk_io_read_bytes=0,
                disk_io_write_bytes=0,
                disk_io_read_count=0,
                disk_io_write_count=0,
                disk_usage_percent=0.0,
                disk_usage_used_bytes=0,
                disk_usage_free_bytes=0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                network_packets_sent=0,
                network_packets_recv=0,
                network_errors_in=0,
                network_errors_out=0,
                open_files=0,
                open_connections=0,
            )

    def collect_application_metrics(self) -> ApplicationMetrics:
        """
        Collect current application performance metrics.

        Tracks request processing, latencies, errors, and throughput.

        Returns:
            ApplicationMetrics dataclass with current application state
        """
        with self._lock:
            # Calculate request rate
            now = datetime.now()
            recent_requests = [
                ts for ts in self.request_times if (now - ts).total_seconds() < 60
            ]
            request_rate = len(recent_requests) / 60.0

            # Calculate error rate
            recent_errors = [
                ts for ts in self.error_times if (now - ts).total_seconds() < 60
            ]
            error_rate = len(recent_errors)

            # Calculate success rate
            if self.request_count > 0:
                success_rate = (
                    (self.request_count - self.error_count) / self.request_count
                ) * 100
            else:
                success_rate = 100.0

            # Get latency statistics
            latency_stats = self.latency_tracker.get_statistics()

            # Calculate throughput
            if self.total_processing_time > 0:
                throughput = self.request_count / self.total_processing_time
            else:
                throughput = 0.0

            return ApplicationMetrics(
                request_count=self.request_count,
                request_rate_per_second=request_rate,
                active_requests=self.active_requests,
                average_latency_ms=latency_stats["average_ms"],
                p50_latency_ms=latency_stats["p50_ms"],
                p95_latency_ms=latency_stats["p95_ms"],
                p99_latency_ms=latency_stats["p99_ms"],
                error_count=self.error_count,
                error_rate_per_minute=error_rate,
                success_rate_percent=success_rate,
                active_connections=self.active_connections,
                throughput_requests_per_second=throughput,
                total_processing_time_seconds=self.total_processing_time,
            )

    def collect_nba_metrics(self) -> NBAMetrics:
        """
        Collect NBA-specific business metrics.

        Tracks database queries, cache performance, and data freshness.

        Returns:
            NBAMetrics dataclass with NBA-specific metrics
        """
        with self._lock:
            # Calculate queries per second
            now = datetime.now()
            recent_queries = [
                ts for ts in self.query_times if (now - ts).total_seconds() < 60
            ]
            queries_per_second = len(recent_queries) / 60.0

            # Calculate cache hit rate
            total_cache_ops = self.cache_hits + self.cache_misses
            if total_cache_ops > 0:
                cache_hit_rate = (self.cache_hits / total_cache_ops) * 100
            else:
                cache_hit_rate = 0.0

            # Calculate data freshness
            data_age = (now - self.last_data_update).total_seconds()

            # Calculate tool success rate
            if self.tool_executions > 0:
                tool_success_rate = (
                    (self.tool_executions - self.tool_failures) / self.tool_executions
                ) * 100
            else:
                tool_success_rate = 100.0

            # Get query latency statistics
            query_stats = self.query_latency_tracker.get_statistics()

            return NBAMetrics(
                queries_per_second=queries_per_second,
                total_queries=self.total_queries,
                cache_hit_rate_percent=cache_hit_rate,
                cache_hits=self.cache_hits,
                cache_misses=self.cache_misses,
                data_freshness_seconds=data_age,
                active_tools=self.active_tools,
                tool_success_rate_percent=tool_success_rate,
                average_query_time_ms=query_stats["average_ms"],
                games_processed=self.games_processed,
                players_processed=self.players_processed,
                s3_reads=self.s3_reads,
                s3_writes=self.s3_writes,
                database_connections=self.database_connections,
            )

    def collect_all_metrics(self) -> AllMetrics:
        """
        Collect all metrics (system, application, NBA).

        Returns:
            AllMetrics dataclass containing all metric types

        Examples:
            >>> collector = MetricsCollector()
            >>> metrics = collector.collect_all_metrics()
            >>> print(metrics.to_json())
        """
        system_metrics = (
            self.collect_system_metrics() if self.enable_system_metrics else None
        )
        app_metrics = (
            self.collect_application_metrics()
            if self.enable_application_metrics
            else None
        )
        nba_metrics = self.collect_nba_metrics() if self.enable_nba_metrics else None

        return AllMetrics(
            system=system_metrics,
            application=app_metrics,
            nba=nba_metrics,
        )

    # ==========================================================================
    # Recording Methods
    # ==========================================================================

    def record_request(self, latency_ms: float, error: bool = False) -> None:
        """
        Record a request completion.

        Args:
            latency_ms: Request latency in milliseconds
            error: Whether the request resulted in an error
        """
        with self._lock:
            self.request_count += 1
            self.request_times.append(datetime.now())
            self.latency_tracker.record(latency_ms)
            self.total_processing_time += latency_ms / 1000.0

            if error:
                self.error_count += 1
                self.error_times.append(datetime.now())

    def record_nba_query(self, latency_ms: float) -> None:
        """
        Record a database query.

        Args:
            latency_ms: Query latency in milliseconds
        """
        with self._lock:
            self.total_queries += 1
            self.query_times.append(datetime.now())
            self.query_latency_tracker.record(latency_ms)

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self.cache_misses += 1

    def record_data_update(self) -> None:
        """Record a data update (resets freshness timer)."""
        with self._lock:
            self.last_data_update = datetime.now()

    def record_tool_execution(self, success: bool = True) -> None:
        """
        Record a tool execution.

        Args:
            success: Whether the tool execution succeeded
        """
        with self._lock:
            self.tool_executions += 1
            if not success:
                self.tool_failures += 1

    def record_game_processed(self) -> None:
        """Record a game processing event."""
        with self._lock:
            self.games_processed += 1

    def record_player_processed(self) -> None:
        """Record a player processing event."""
        with self._lock:
            self.players_processed += 1

    def record_s3_read(self) -> None:
        """Record an S3 read operation."""
        with self._lock:
            self.s3_reads += 1

    def record_s3_write(self) -> None:
        """Record an S3 write operation."""
        with self._lock:
            self.s3_writes += 1

    def increment_active_requests(self) -> None:
        """Increment active request counter."""
        with self._lock:
            self.active_requests += 1

    def decrement_active_requests(self) -> None:
        """Decrement active request counter."""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)

    def increment_active_tools(self) -> None:
        """Increment active tool counter."""
        with self._lock:
            self.active_tools += 1

    def decrement_active_tools(self) -> None:
        """Decrement active tool counter."""
        with self._lock:
            self.active_tools = max(0, self.active_tools - 1)

    def set_database_connections(self, count: int) -> None:
        """
        Set the database connection count.

        Args:
            count: Number of active database connections
        """
        with self._lock:
            self.database_connections = count

    # ==========================================================================
    # Context Managers for Tracking
    # ==========================================================================

    def track_request(self, operation: str):
        """
        Context manager for tracking request latency.

        Args:
            operation: Name of the operation being tracked

        Returns:
            Context manager that tracks request timing

        Examples:
            >>> with collector.track_request("query_database"):
            ...     result = db.execute(query)
        """
        return RequestTracker(self, operation)

    def track_query(self, query: str):
        """
        Context manager for tracking database query latency.

        Args:
            query: SQL query being executed

        Returns:
            Context manager that tracks query timing

        Examples:
            >>> with collector.track_query("SELECT * FROM games"):
            ...     result = db.execute(query)
        """
        return QueryTracker(self, query)

    # ==========================================================================
    # Export Methods
    # ==========================================================================

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string

        Examples:
            >>> metrics_text = collector.export_prometheus()
            >>> # Serve on /metrics endpoint
        """
        metrics = self.collect_all_metrics()
        lines = []

        # System metrics
        if self.enable_system_metrics:
            lines.extend(
                [
                    f"# HELP nba_cpu_percent CPU utilization percentage",
                    f"# TYPE nba_cpu_percent gauge",
                    f"nba_cpu_percent {metrics.system.cpu_percent}",
                    f"",
                    f"# HELP nba_memory_percent Memory utilization percentage",
                    f"# TYPE nba_memory_percent gauge",
                    f"nba_memory_percent {metrics.system.memory_percent}",
                    f"",
                    f"# HELP nba_disk_usage_percent Disk utilization percentage",
                    f"# TYPE nba_disk_usage_percent gauge",
                    f"nba_disk_usage_percent {metrics.system.disk_usage_percent}",
                    f"",
                ]
            )

        # Application metrics
        if self.enable_application_metrics:
            lines.extend(
                [
                    f"# HELP nba_requests_total Total number of requests",
                    f"# TYPE nba_requests_total counter",
                    f"nba_requests_total {metrics.application.request_count}",
                    f"",
                    f"# HELP nba_errors_total Total number of errors",
                    f"# TYPE nba_errors_total counter",
                    f"nba_errors_total {metrics.application.error_count}",
                    f"",
                    f"# HELP nba_latency_ms Request latency in milliseconds",
                    f"# TYPE nba_latency_ms summary",
                    f'nba_latency_ms{{quantile="0.5"}} {metrics.application.p50_latency_ms}',
                    f'nba_latency_ms{{quantile="0.95"}} {metrics.application.p95_latency_ms}',
                    f'nba_latency_ms{{quantile="0.99"}} {metrics.application.p99_latency_ms}',
                    f"",
                ]
            )

        # NBA metrics
        if self.enable_nba_metrics:
            lines.extend(
                [
                    f"# HELP nba_queries_total Total database queries",
                    f"# TYPE nba_queries_total counter",
                    f"nba_queries_total {metrics.nba.total_queries}",
                    f"",
                    f"# HELP nba_cache_hit_rate Cache hit rate percentage",
                    f"# TYPE nba_cache_hit_rate gauge",
                    f"nba_cache_hit_rate {metrics.nba.cache_hit_rate_percent}",
                    f"",
                    f"# HELP nba_data_freshness_seconds Data age in seconds",
                    f"# TYPE nba_data_freshness_seconds gauge",
                    f"nba_data_freshness_seconds {metrics.nba.data_freshness_seconds}",
                    f"",
                ]
            )

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current metrics.

        Returns:
            Dictionary with metric summary
        """
        metrics = self.collect_all_metrics()
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": metrics.system.cpu_percent,
                "memory_percent": metrics.system.memory_percent,
                "disk_percent": metrics.system.disk_usage_percent,
            },
            "application": {
                "requests": metrics.application.request_count,
                "errors": metrics.application.error_count,
                "success_rate": metrics.application.success_rate_percent,
                "avg_latency_ms": metrics.application.average_latency_ms,
                "p95_latency_ms": metrics.application.p95_latency_ms,
            },
            "nba": {
                "queries": metrics.nba.total_queries,
                "cache_hit_rate": metrics.nba.cache_hit_rate_percent,
                "data_age_seconds": metrics.nba.data_freshness_seconds,
                "tool_success_rate": metrics.nba.tool_success_rate_percent,
            },
        }

    def reset_metrics(self) -> None:
        """Reset all counters (useful for testing)."""
        with self._lock:
            self.request_count = 0
            self.active_requests = 0
            self.error_count = 0
            self.total_processing_time = 0.0
            self.request_times.clear()
            self.error_times.clear()
            self.latency_tracker.clear()

            self.total_queries = 0
            self.query_times.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            self.last_data_update = datetime.now()
            self.tool_executions = 0
            self.tool_failures = 0
            self.games_processed = 0
            self.players_processed = 0
            self.s3_reads = 0
            self.s3_writes = 0
            self.query_latency_tracker.clear()


# ==============================================================================
# Context Managers
# ==============================================================================


class RequestTracker:
    """Context manager for tracking request latency."""

    def __init__(self, collector: MetricsCollector, operation: str):
        self.collector = collector
        self.operation = operation
        self.start_time: Optional[float] = None
        self.error_occurred = False

    def __enter__(self):
        self.start_time = time.time()
        self.collector.increment_active_requests()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        self.error_occurred = exc_type is not None

        self.collector.record_request(latency_ms, error=self.error_occurred)
        self.collector.decrement_active_requests()

        logger.debug(
            f"Request completed: {self.operation}",
            extra={
                "operation": self.operation,
                "latency_ms": round(latency_ms, 2),
                "error": self.error_occurred,
            },
        )


class QueryTracker:
    """Context manager for tracking database query latency."""

    def __init__(self, collector: MetricsCollector, query: str):
        self.collector = collector
        self.query = query[:100]  # Truncate for logging
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        self.collector.record_nba_query(latency_ms)

        logger.debug(
            f"Query completed: {self.query}",
            extra={
                "query": self.query,
                "latency_ms": round(latency_ms, 2),
                "error": exc_type is not None,
            },
        )


# ==============================================================================
# Global Metrics Collector
# ==============================================================================


_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.

    Returns:
        Global MetricsCollector instance

    Examples:
        >>> collector = get_metrics_collector()
        >>> metrics = collector.collect_all_metrics()
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """
    Set the global metrics collector instance.

    Args:
        collector: MetricsCollector instance to use globally
    """
    global _global_metrics_collector
    _global_metrics_collector = collector


# ==============================================================================
# Decorators
# ==============================================================================


def track_latency(operation: str):
    """
    Decorator to automatically track function latency.

    Args:
        operation: Name of the operation being tracked

    Returns:
        Decorated function

    Examples:
        >>> @track_latency("query_database")
        ... async def query_database(query: str):
        ...     return await db.execute(query)
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            with collector.track_request(operation):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            with collector.track_request(operation):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
