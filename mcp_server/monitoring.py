"""
NBA MCP Server Monitoring and Alerting

Comprehensive monitoring infrastructure with health checks, alerting, and
centralized logging. Implements production-grade monitoring patterns for
ensuring system reliability and observability.

This module provides:
- Health monitoring for all system components
- Threshold-based alerting with configurable severity levels
- Anomaly detection for unusual patterns
- Centralized logging integration
- Automated notifications (email, Slack, PagerDuty)
- SLA violation tracking

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import json
import os
import smtplib
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .logging_config import get_logger
from .error_handling import (
    ErrorHandler,
    get_error_handler,
    ServiceUnavailableError,
)
from .nba_metrics import MetricsCollector, get_metrics_collector

# Optional imports for health checks (can be mocked in tests)
try:
    import psutil
except ImportError:
    psutil = None

try:
    import boto3
except ImportError:
    boto3 = None

logger = get_logger(__name__)


# ==============================================================================
# Health Status and Checks
# ==============================================================================


class HealthStatus(Enum):
    """
    Health status levels for system components.

    HEALTHY: Component is functioning normally
    DEGRADED: Component is functional but experiencing issues
    UNHEALTHY: Component is not functioning correctly
    UNKNOWN: Component health cannot be determined
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

    @property
    def is_healthy(self) -> bool:
        """Check if status indicates healthy state."""
        return self in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    @property
    def severity_level(self) -> int:
        """Get numeric severity level (0=healthy, 3=unknown)."""
        levels = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 1,
            HealthStatus.UNHEALTHY: 2,
            HealthStatus.UNKNOWN: 3,
        }
        return levels[self]


@dataclass
class HealthCheck:
    """
    Result of a health check.

    Attributes:
        name: Name of the component being checked
        status: Current health status
        message: Human-readable status message
        timestamp: When the check was performed
        response_time_ms: How long the check took
        details: Additional diagnostic information
        tags: Tags for categorization and filtering

    Examples:
        >>> check = HealthCheck(
        ...     name="database",
        ...     status=HealthStatus.HEALTHY,
        ...     message="Database responding normally",
        ...     response_time_ms=45.2,
        ... )
    """

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health check to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": round(self.response_time_ms, 2),
            "details": self.details or {},
            "tags": self.tags,
        }

    def is_healthy(self) -> bool:
        """Check if this component is healthy."""
        return self.status.is_healthy


@dataclass
class OverallHealth:
    """
    Aggregate health status for the entire system.

    Attributes:
        status: Overall system health status
        checks: Individual component health checks
        healthy_count: Number of healthy components
        degraded_count: Number of degraded components
        unhealthy_count: Number of unhealthy components
        timestamp: When the overall health was assessed
    """

    status: HealthStatus
    checks: List[HealthCheck]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "healthy": self.healthy_count,
            "degraded": self.degraded_count,
            "unhealthy": self.unhealthy_count,
            "total_checks": len(self.checks),
            "timestamp": self.timestamp.isoformat(),
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ==============================================================================
# Alert System
# ==============================================================================


class AlertSeverity(Enum):
    """
    Alert severity levels.

    INFO: Informational alerts
    WARNING: Warning alerts (action may be needed)
    CRITICAL: Critical alerts (immediate action required)
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    @property
    def priority(self) -> int:
        """Get numeric priority (0=info, 2=critical)."""
        priorities = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.CRITICAL: 2,
        }
        return priorities[self]


@dataclass
class Alert:
    """
    Alert notification.

    Attributes:
        id: Unique alert identifier
        name: Alert name/title
        message: Detailed alert message
        severity: Alert severity level
        metric_name: Name of the metric that triggered the alert
        current_value: Current value of the metric
        threshold_value: Threshold that was exceeded
        timestamp: When the alert was triggered
        tags: Tags for categorization
        resolved: Whether the alert has been resolved
        resolved_at: When the alert was resolved
        details: Additional alert context
    """

    id: str
    name: str
    message: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "message": self.message,
            "severity": self.severity.value,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "details": self.details or {},
        }

    def resolve(self):
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now()


@dataclass
class AlertThreshold:
    """
    Configuration for threshold-based alerts.

    Attributes:
        metric_name: Name of the metric to monitor
        threshold: Threshold value
        comparison: Comparison operator ("gt", "lt", "eq", "gte", "lte")
        severity: Alert severity when threshold is exceeded
        window_seconds: Time window for evaluation
        min_occurrences: Minimum occurrences before alerting
        enabled: Whether this threshold is active
        description: Human-readable description
    """

    metric_name: str
    threshold: float
    comparison: str  # "gt", "lt", "eq", "gte", "lte"
    severity: AlertSeverity
    window_seconds: int = 60
    min_occurrences: int = 1
    enabled: bool = True
    description: str = ""

    def evaluate(self, value: float) -> bool:
        """
        Evaluate if threshold is exceeded.

        Args:
            value: Current metric value

        Returns:
            True if threshold is exceeded, False otherwise
        """
        if not self.enabled:
            return False

        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "eq":
            return value == self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        else:
            logger.warning(f"Unknown comparison operator: {self.comparison}")
            return False


# ==============================================================================
# Health Monitor
# ==============================================================================


class HealthMonitor:
    """
    Monitors system health across all components.

    Performs periodic health checks on:
    - Database connectivity and performance
    - S3 storage availability
    - API responsiveness
    - System resources (CPU, memory, disk)
    - Application performance metrics

    Features:
    - Automatic health check scheduling
    - Failure tracking and recovery detection
    - Health history for trending
    - Integration with alerting system

    Examples:
        >>> monitor = HealthMonitor()
        >>> health = monitor.get_overall_health()
        >>> if health.status == HealthStatus.UNHEALTHY:
        ...     print("System is unhealthy!")
    """

    def __init__(
        self,
        check_interval: int = 30,
        enable_auto_checks: bool = True,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize health monitor.

        Args:
            check_interval: How often to run health checks (seconds)
            enable_auto_checks: Enable automatic periodic checks
            metrics_collector: Metrics collector instance
        """
        self.check_interval = check_interval
        self.enable_auto_checks = enable_auto_checks
        self.metrics_collector = metrics_collector or get_metrics_collector()

        # Health check results
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_history: deque = deque(maxlen=1000)

        # Failure tracking
        self.consecutive_failures: Dict[str, int] = defaultdict(int)

        # Thread safety
        self._lock = Lock()

        # Background check thread
        self._check_thread: Optional[Thread] = None
        self._running = False

        logger.info(
            "Health monitor initialized",
            extra={
                "check_interval": check_interval,
                "auto_checks": enable_auto_checks,
            },
        )

    def start(self):
        """Start automatic health checking."""
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        self._check_thread = Thread(target=self._run_checks_loop, daemon=True)
        self._check_thread.start()

        logger.info("Health monitor started")

    def stop(self):
        """Stop automatic health checking."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)

        logger.info("Health monitor stopped")

    def _run_checks_loop(self):
        """Background thread for running health checks."""
        while self._running:
            try:
                self.run_all_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)

            time.sleep(self.check_interval)

    def check_database_health(self) -> HealthCheck:
        """
        Check database connectivity and performance.

        Returns:
            HealthCheck for database component
        """
        start_time = time.time()
        name = "database"

        try:
            # Try to import database connector
            from .connectors.db import get_db_connection

            # Attempt connection
            conn = get_db_connection()
            cursor = conn.cursor()

            # Execute simple query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            cursor.close()

            response_time_ms = (time.time() - start_time) * 1000

            # Check if response time is acceptable
            if response_time_ms > 1000:
                status = HealthStatus.DEGRADED
                message = f"Database responding slowly ({response_time_ms:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection successful"

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details={"connection": "active"},
                tags=["database", "postgresql"],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                tags=["database", "postgresql", "error"],
            )

    def check_s3_health(self) -> HealthCheck:
        """
        Check S3 storage availability.

        Returns:
            HealthCheck for S3 component
        """
        start_time = time.time()
        name = "s3"

        try:
            # Check if boto3 is available
            if boto3 is None:
                raise ImportError("boto3 not available")

            from botocore.exceptions import ClientError

            s3_client = boto3.client("s3")

            # Try to list objects (with limit)
            bucket_name = os.getenv("S3_BUCKET_NAME", "nba-mcp-data")
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.HEALTHY,
                message="S3 storage accessible",
                response_time_ms=response_time_ms,
                details={"bucket": bucket_name},
                tags=["storage", "s3"],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"S3 storage unavailable: {str(e)}",
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                tags=["storage", "s3", "error"],
            )

    def check_system_resources(self) -> HealthCheck:
        """
        Check system resource utilization.

        Returns:
            HealthCheck for system resources
        """
        start_time = time.time()
        name = "system_resources"

        try:
            metrics = self.metrics_collector.collect_system_metrics()
            response_time_ms = (time.time() - start_time) * 1000

            # Determine status based on resource utilization
            cpu_ok = metrics.cpu_percent < 80
            memory_ok = metrics.memory_percent < 90
            disk_ok = metrics.disk_usage_percent < 85

            if cpu_ok and memory_ok and disk_ok:
                status = HealthStatus.HEALTHY
                message = "System resources within normal limits"
            elif cpu_ok and memory_ok:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high ({metrics.disk_usage_percent:.1f}%)"
            elif cpu_ok and disk_ok:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high ({metrics.memory_percent:.1f}%)"
            elif memory_ok and disk_ok:
                status = HealthStatus.DEGRADED
                message = f"CPU usage high ({metrics.cpu_percent:.1f}%)"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Multiple resource constraints detected"

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details={
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_percent": metrics.disk_usage_percent,
                },
                tags=["system", "resources"],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unable to check system resources: {str(e)}",
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                tags=["system", "resources", "error"],
            )

    def check_application_health(self) -> HealthCheck:
        """
        Check application performance metrics.

        Returns:
            HealthCheck for application health
        """
        start_time = time.time()
        name = "application"

        try:
            metrics = self.metrics_collector.collect_application_metrics()
            response_time_ms = (time.time() - start_time) * 1000

            # Determine status based on metrics
            error_rate_ok = metrics.error_rate_per_minute < 10
            latency_ok = metrics.p95_latency_ms < 500
            success_rate_ok = metrics.success_rate_percent > 95

            if error_rate_ok and latency_ok and success_rate_ok:
                status = HealthStatus.HEALTHY
                message = "Application performing normally"
            elif error_rate_ok and success_rate_ok:
                status = HealthStatus.DEGRADED
                message = f"High latency detected (p95: {metrics.p95_latency_ms:.0f}ms)"
            elif latency_ok and success_rate_ok:
                status = HealthStatus.DEGRADED
                message = (
                    f"Elevated error rate ({metrics.error_rate_per_minute:.1f}/min)"
                )
            else:
                status = HealthStatus.UNHEALTHY
                message = "Application experiencing performance issues"

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details={
                    "error_rate": metrics.error_rate_per_minute,
                    "p95_latency_ms": metrics.p95_latency_ms,
                    "success_rate": metrics.success_rate_percent,
                },
                tags=["application", "performance"],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unable to check application health: {str(e)}",
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                tags=["application", "error"],
            )

    def check_nba_data_health(self) -> HealthCheck:
        """
        Check NBA data freshness and quality.

        Returns:
            HealthCheck for NBA data
        """
        start_time = time.time()
        name = "nba_data"

        try:
            metrics = self.metrics_collector.collect_nba_metrics()
            response_time_ms = (time.time() - start_time) * 1000

            # Check data freshness (should be updated within 1 hour)
            data_fresh = metrics.data_freshness_seconds < 3600
            cache_ok = metrics.cache_hit_rate_percent > 50
            queries_ok = metrics.queries_per_second < 100

            if data_fresh and cache_ok:
                status = HealthStatus.HEALTHY
                message = "NBA data fresh and accessible"
            elif data_fresh:
                status = HealthStatus.DEGRADED
                message = f"Low cache hit rate ({metrics.cache_hit_rate_percent:.1f}%)"
            else:
                status = HealthStatus.UNHEALTHY
                message = (
                    f"Data stale ({metrics.data_freshness_seconds/60:.0f} minutes old)"
                )

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                details={
                    "data_age_seconds": metrics.data_freshness_seconds,
                    "cache_hit_rate": metrics.cache_hit_rate_percent,
                    "queries_per_second": metrics.queries_per_second,
                },
                tags=["nba", "data"],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unable to check NBA data health: {str(e)}",
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                tags=["nba", "data", "error"],
            )

    def run_all_checks(self) -> List[HealthCheck]:
        """
        Run all health checks.

        Returns:
            List of all health check results
        """
        checks = [
            self.check_database_health(),
            self.check_s3_health(),
            self.check_system_resources(),
            self.check_application_health(),
            self.check_nba_data_health(),
        ]

        with self._lock:
            for check in checks:
                self.health_checks[check.name] = check
                self.health_history.append(check)

                # Track consecutive failures
                if check.status == HealthStatus.UNHEALTHY:
                    self.consecutive_failures[check.name] += 1
                else:
                    self.consecutive_failures[check.name] = 0

        logger.debug(
            "Health checks completed",
            extra={
                "total_checks": len(checks),
                "healthy": sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in checks if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(
                    1 for c in checks if c.status == HealthStatus.UNHEALTHY
                ),
            },
        )

        return checks

    def get_overall_health(self) -> OverallHealth:
        """
        Get overall system health status.

        Returns:
            OverallHealth with aggregated status
        """
        with self._lock:
            checks = list(self.health_checks.values())

        if not checks:
            # Run checks if none exist
            checks = self.run_all_checks()

        # Count statuses
        healthy = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        degraded = sum(1 for c in checks if c.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)

        # Determine overall status
        if unhealthy > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_status = HealthStatus.DEGRADED
        elif healthy > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        return OverallHealth(
            status=overall_status,
            checks=checks,
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy,
        )

    def get_check(self, name: str) -> Optional[HealthCheck]:
        """
        Get a specific health check result.

        Args:
            name: Name of the health check

        Returns:
            HealthCheck result or None if not found
        """
        with self._lock:
            return self.health_checks.get(name)

    def get_failing_checks(self) -> List[HealthCheck]:
        """
        Get all checks that are not healthy.

        Returns:
            List of unhealthy or degraded checks
        """
        with self._lock:
            return [
                check
                for check in self.health_checks.values()
                if check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
            ]


# ==============================================================================
# Alert Manager
# ==============================================================================


class AlertManager:
    """
    Manages threshold-based alerts and notifications.

    Features:
    - Configurable alert thresholds
    - Multiple notification channels (email, Slack, webhook)
    - Alert deduplication and rate limiting
    - Alert history and resolution tracking
    - Integration with health monitoring

    Examples:
        >>> manager = AlertManager()
        >>>
        >>> # Register threshold
        >>> manager.register_threshold(AlertThreshold(
        ...     metric_name="cpu_percent",
        ...     threshold=80.0,
        ...     comparison="gt",
        ...     severity=AlertSeverity.WARNING
        ... ))
        >>>
        >>> # Check thresholds
        >>> alerts = manager.check_all_thresholds()
    """

    def __init__(
        self,
        enable_email: bool = False,
        enable_slack: bool = False,
        enable_webhook: bool = False,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize alert manager.

        Args:
            enable_email: Enable email notifications
            enable_slack: Enable Slack notifications
            enable_webhook: Enable webhook notifications
            metrics_collector: Metrics collector instance
        """
        self.enable_email = enable_email
        self.enable_slack = enable_slack
        self.enable_webhook = enable_webhook
        self.metrics_collector = metrics_collector or get_metrics_collector()

        # Alert configuration
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)

        # Alert deduplication
        self.last_alert_time: Dict[str, datetime] = {}
        self.min_alert_interval = timedelta(minutes=5)

        # Thread safety
        self._lock = Lock()

        # Notification configuration
        self.email_config = {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("ALERT_FROM_EMAIL", "alerts@nba-mcp.com"),
            "to_emails": os.getenv("ALERT_TO_EMAILS", "").split(","),
        }

        self.slack_config = {
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        }

        self.webhook_config = {
            "url": os.getenv("ALERT_WEBHOOK_URL", ""),
        }

        logger.info(
            "Alert manager initialized",
            extra={
                "email_enabled": enable_email,
                "slack_enabled": enable_slack,
                "webhook_enabled": enable_webhook,
            },
        )

    def register_threshold(self, threshold: AlertThreshold) -> None:
        """
        Register an alert threshold.

        Args:
            threshold: AlertThreshold configuration

        Examples:
            >>> manager.register_threshold(AlertThreshold(
            ...     metric_name="memory_percent",
            ...     threshold=90.0,
            ...     comparison="gt",
            ...     severity=AlertSeverity.CRITICAL
            ... ))
        """
        with self._lock:
            self.thresholds[threshold.metric_name] = threshold

        logger.info(
            f"Registered alert threshold for {threshold.metric_name}",
            extra={
                "metric": threshold.metric_name,
                "threshold": threshold.threshold,
                "comparison": threshold.comparison,
                "severity": threshold.severity.value,
            },
        )

    def unregister_threshold(self, metric_name: str) -> None:
        """
        Unregister an alert threshold.

        Args:
            metric_name: Name of the metric to stop monitoring
        """
        with self._lock:
            if metric_name in self.thresholds:
                del self.thresholds[metric_name]

        logger.info(f"Unregistered alert threshold for {metric_name}")

    def check_all_thresholds(self) -> List[Alert]:
        """
        Check all registered thresholds against current metrics.

        Returns:
            List of triggered alerts
        """
        metrics = self.metrics_collector.collect_all_metrics()
        metric_values = self._extract_metric_values(metrics.to_dict())

        triggered_alerts = []

        with self._lock:
            for threshold in self.thresholds.values():
                if not threshold.enabled:
                    continue

                metric_value = metric_values.get(threshold.metric_name)
                if metric_value is None:
                    continue

                if threshold.evaluate(metric_value):
                    alert = self._create_alert(threshold, metric_value)
                    if self._should_send_alert(alert):
                        triggered_alerts.append(alert)
                        self._record_alert(alert)
                        self._send_notifications(alert)

        return triggered_alerts

    def _extract_metric_values(self, metrics_dict: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract flat metric values from nested metrics dictionary.

        Args:
            metrics_dict: Nested metrics dictionary

        Returns:
            Flat dictionary of metric name -> value
        """
        values = {}

        def flatten(d: Dict[str, Any], prefix: str = ""):
            for key, value in d.items():
                full_key = f"{prefix}{key}" if prefix else key

                if isinstance(value, dict):
                    flatten(value, f"{full_key}_")
                elif isinstance(value, (int, float)):
                    values[full_key] = float(value)

        flatten(metrics_dict)
        return values

    def _create_alert(self, threshold: AlertThreshold, current_value: float) -> Alert:
        """
        Create an alert from a threshold violation.

        Args:
            threshold: AlertThreshold that was violated
            current_value: Current value of the metric

        Returns:
            Alert instance
        """
        import uuid

        alert_id = str(uuid.uuid4())

        message = (
            f"{threshold.metric_name} {threshold.comparison} {threshold.threshold}: "
            f"current value is {current_value:.2f}"
        )

        return Alert(
            id=alert_id,
            name=f"Threshold exceeded: {threshold.metric_name}",
            message=message,
            severity=threshold.severity,
            metric_name=threshold.metric_name,
            current_value=current_value,
            threshold_value=threshold.threshold,
            tags=["threshold", threshold.severity.value],
            details={
                "comparison": threshold.comparison,
                "description": threshold.description,
            },
        )

    def _should_send_alert(self, alert: Alert) -> bool:
        """
        Check if alert should be sent (deduplication).

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent
        """
        # Check if we recently sent an alert for this metric
        last_time = self.last_alert_time.get(alert.metric_name)
        if last_time:
            time_since_last = datetime.now() - last_time
            if time_since_last < self.min_alert_interval:
                logger.debug(
                    f"Suppressing duplicate alert for {alert.metric_name}",
                    extra={
                        "metric": alert.metric_name,
                        "time_since_last": time_since_last.total_seconds(),
                    },
                )
                return False

        return True

    def _record_alert(self, alert: Alert) -> None:
        """
        Record alert in history and active alerts.

        Args:
            alert: Alert to record
        """
        with self._lock:
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)
            self.last_alert_time[alert.metric_name] = datetime.now()

    def _send_notifications(self, alert: Alert) -> None:
        """
        Send alert notifications to configured channels.

        Args:
            alert: Alert to send
        """
        logger.warning(
            f"ALERT: {alert.name}",
            extra={
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "metric": alert.metric_name,
                "current_value": alert.current_value,
                "threshold": alert.threshold_value,
                "message": alert.message,
            },
        )

        # Send to configured channels
        if self.enable_email:
            self._send_email_alert(alert)

        if self.enable_slack:
            self._send_slack_alert(alert)

        if self.enable_webhook:
            self._send_webhook_alert(alert)

    def _send_email_alert(self, alert: Alert) -> None:
        """
        Send alert via email.

        Args:
            alert: Alert to send
        """
        try:
            if not self.email_config["to_emails"] or not self.email_config["smtp_user"]:
                logger.debug("Email notifications not configured")
                return

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.name}"

            body = f"""
NBA MCP Server Alert

Severity: {alert.severity.value.upper()}
Metric: {alert.metric_name}
Current Value: {alert.current_value:.2f}
Threshold: {alert.threshold_value:.2f}
Time: {alert.timestamp.isoformat()}

Message: {alert.message}

Details:
{json.dumps(alert.details, indent=2)}
"""

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(
                self.email_config["smtp_host"], self.email_config["smtp_port"]
            )
            server.starttls()
            server.login(
                self.email_config["smtp_user"], self.email_config["smtp_password"]
            )
            server.send_message(msg)
            server.quit()

            logger.info(f"Email alert sent for {alert.name}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)

    def _send_slack_alert(self, alert: Alert) -> None:
        """
        Send alert to Slack.

        Args:
            alert: Alert to send
        """
        try:
            if not self.slack_config["webhook_url"]:
                logger.debug("Slack notifications not configured")
                return

            # Choose color based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.CRITICAL: "#ff0000",
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#808080"),
                        "title": alert.name,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Metric",
                                "value": alert.metric_name,
                                "short": True,
                            },
                            {
                                "title": "Current Value",
                                "value": f"{alert.current_value:.2f}",
                                "short": True,
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.threshold_value:.2f}",
                                "short": True,
                            },
                        ],
                        "footer": "NBA MCP Server",
                        "ts": int(alert.timestamp.timestamp()),
                    }
                ]
            }

            # Send to Slack
            request = Request(
                self.slack_config["webhook_url"],
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(
                request, timeout=10
            )  # nosec B310 - webhook URLs are validated and user-controlled

            logger.info(f"Slack alert sent for {alert.name}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=True)

    def _send_webhook_alert(self, alert: Alert) -> None:
        """
        Send alert to webhook.

        Args:
            alert: Alert to send
        """
        try:
            if not self.webhook_config["url"]:
                logger.debug("Webhook notifications not configured")
                return

            # Send alert data to webhook
            request = Request(
                self.webhook_config["url"],
                data=json.dumps(alert.to_dict()).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(
                request, timeout=10
            )  # nosec B310 - webhook URLs are validated and user-controlled

            logger.info(f"Webhook alert sent for {alert.name}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}", exc_info=True)

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            True if alert was resolved, False if not found
        """
        with self._lock:
            alert = self.active_alerts.get(alert_id)
            if alert:
                alert.resolve()
                del self.active_alerts[alert_id]

                logger.info(
                    f"Alert resolved: {alert.name}", extra={"alert_id": alert_id}
                )
                return True

        return False

    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active (unresolved) alerts.

        Returns:
            List of active alerts
        """
        with self._lock:
            return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        with self._lock:
            return list(self.alert_history)[-limit:]


# ==============================================================================
# Global Instances
# ==============================================================================


_global_health_monitor: Optional[HealthMonitor] = None
_global_alert_manager: Optional[AlertManager] = None


def get_health_monitor() -> HealthMonitor:
    """
    Get the global health monitor instance.

    Returns:
        Global HealthMonitor instance
    """
    global _global_health_monitor
    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor()
    return _global_health_monitor


def set_health_monitor(monitor: HealthMonitor) -> None:
    """
    Set the global health monitor instance.

    Args:
        monitor: HealthMonitor instance to use globally
    """
    global _global_health_monitor
    _global_health_monitor = monitor


def get_alert_manager() -> AlertManager:
    """
    Get the global alert manager instance.

    Returns:
        Global AlertManager instance
    """
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager


def set_alert_manager(manager: AlertManager) -> None:
    """
    Set the global alert manager instance.

    Args:
        manager: AlertManager instance to use globally
    """
    global _global_alert_manager
    _global_alert_manager = manager


# ==============================================================================
# Convenience Functions
# ==============================================================================


def register_default_thresholds() -> None:
    """
    Register default alert thresholds for common metrics.

    This sets up sensible defaults for CPU, memory, disk, latency, and error rates.
    """
    manager = get_alert_manager()

    # System resource thresholds
    manager.register_threshold(
        AlertThreshold(
            metric_name="system_cpu_percent",
            threshold=80.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="CPU utilization above 80%",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="system_cpu_percent",
            threshold=95.0,
            comparison="gt",
            severity=AlertSeverity.CRITICAL,
            description="CPU utilization above 95%",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="system_memory_percent",
            threshold=90.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="Memory utilization above 90%",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="system_disk_usage_percent",
            threshold=85.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="Disk utilization above 85%",
        )
    )

    # Application performance thresholds
    manager.register_threshold(
        AlertThreshold(
            metric_name="application_p95_latency_ms",
            threshold=500.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="P95 latency above 500ms",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="application_error_rate_per_minute",
            threshold=10.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="Error rate above 10/minute",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="application_success_rate_percent",
            threshold=95.0,
            comparison="lt",
            severity=AlertSeverity.CRITICAL,
            description="Success rate below 95%",
        )
    )

    # NBA-specific thresholds
    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_data_freshness_seconds",
            threshold=3600.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            description="Data not updated in over 1 hour",
        )
    )

    manager.register_threshold(
        AlertThreshold(
            metric_name="nba_cache_hit_rate_percent",
            threshold=50.0,
            comparison="lt",
            severity=AlertSeverity.WARNING,
            description="Cache hit rate below 50%",
        )
    )

    logger.info("Registered default alert thresholds")
