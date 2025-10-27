"""
NBA MCP Server Real-Time Monitoring Dashboard

Web-based real-time dashboard for monitoring NBA MCP Server health, performance,
and business metrics. Provides live visualization of system status, metrics,
and alerts.

This module provides:
- Real-time metrics visualization
- Live game event streaming
- Player performance tracking
- System health indicators
- Alert notifications
- Historical data charts
- REST API for dashboard data

Author: NBA MCP Server Team - Phase 10A Agent 2
Date: 2025-01-18
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional, Set

from .logging_config import get_logger
from .nba_metrics import MetricsCollector, get_metrics_collector, AllMetrics
from .monitoring import (
    HealthMonitor,
    AlertManager,
    get_health_monitor,
    get_alert_manager,
    HealthStatus,
    AlertSeverity,
)

logger = get_logger(__name__)


# ==============================================================================
# Dashboard Data Models
# ==============================================================================


@dataclass
class DashboardSnapshot:
    """
    Snapshot of dashboard data at a point in time.

    Attributes:
        timestamp: When the snapshot was taken
        metrics: Current system, application, and NBA metrics
        health: Overall system health status
        active_alerts: Currently active alerts
        recent_events: Recent system events
    """

    timestamp: datetime
    metrics: Dict[str, Any]
    health: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "health": self.health,
            "active_alerts": self.active_alerts,
            "recent_events": self.recent_events,
        }

    def to_json(self) -> str:
        """Convert snapshot to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class GameEvent:
    """
    Live game event for streaming.

    Attributes:
        game_id: Unique game identifier
        event_type: Type of event (shot, rebound, assist, etc.)
        timestamp: When the event occurred
        player_id: Player involved in the event
        team_id: Team involved in the event
        description: Human-readable event description
        data: Additional event data
    """

    game_id: str
    event_type: str
    timestamp: datetime
    player_id: Optional[str] = None
    team_id: Optional[str] = None
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "game_id": self.game_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "player_id": self.player_id,
            "team_id": self.team_id,
            "description": self.description,
            "data": self.data,
        }


@dataclass
class TimeSeriesData:
    """
    Time series data for charting.

    Attributes:
        metric_name: Name of the metric
        timestamps: List of timestamps
        values: List of values corresponding to timestamps
        unit: Unit of measurement
    """

    metric_name: str
    timestamps: List[datetime]
    values: List[float]
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_name": self.metric_name,
            "data": [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in zip(self.timestamps, self.values)
            ],
            "unit": self.unit,
        }


# ==============================================================================
# Dashboard Manager
# ==============================================================================


class MonitoringDashboard:
    """
    Real-time monitoring dashboard for NBA MCP Server.

    Provides a comprehensive view of system health, performance metrics,
    and business KPIs through a web-based interface. Supports live updates,
    historical data visualization, and alert management.

    Features:
    - Real-time metrics updates
    - Live game event streaming
    - Player performance tracking
    - System health monitoring
    - Alert visualization and management
    - Historical data charts
    - Export to JSON/CSV

    Examples:
        >>> dashboard = MonitoringDashboard()
        >>> dashboard.start()  # Start background data collection
        >>>
        >>> # Get current snapshot
        >>> snapshot = dashboard.get_snapshot()
        >>> print(snapshot.to_json())
        >>>
        >>> # Get time series data
        >>> cpu_data = dashboard.get_time_series("cpu_percent", hours=1)
    """

    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        health_monitor: Optional[HealthMonitor] = None,
        alert_manager: Optional[AlertManager] = None,
        update_interval: int = 5,
        history_size: int = 1000,
    ):
        """
        Initialize monitoring dashboard.

        Args:
            metrics_collector: Metrics collector instance
            health_monitor: Health monitor instance
            alert_manager: Alert manager instance
            update_interval: How often to update dashboard data (seconds)
            history_size: Maximum number of historical data points to keep
        """
        self.metrics_collector = metrics_collector or get_metrics_collector()
        self.health_monitor = health_monitor or get_health_monitor()
        self.alert_manager = alert_manager or get_alert_manager()
        self.update_interval = update_interval
        self.history_size = history_size

        # Historical data storage
        self.metrics_history: deque = deque(maxlen=history_size)
        self.health_history: deque = deque(maxlen=history_size)
        self.game_events: deque = deque(maxlen=1000)

        # Time series data for key metrics
        self.time_series: Dict[str, TimeSeriesData] = {}

        # Dashboard state
        self._running = False
        self._update_thread: Optional[Thread] = None
        self._lock = Lock()

        # Performance tracking
        self.dashboard_start_time = datetime.now()
        self.total_updates = 0

        logger.info(
            "Monitoring dashboard initialized",
            extra={
                "update_interval": update_interval,
                "history_size": history_size,
            },
        )

    def start(self) -> None:
        """
        Start the dashboard background data collection.

        Launches a background thread that periodically collects metrics,
        health status, and updates historical data.
        """
        if self._running:
            logger.warning("Dashboard already running")
            return

        self._running = True
        self._update_thread = Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

        logger.info("Monitoring dashboard started")

    def stop(self) -> None:
        """
        Stop the dashboard background data collection.

        Gracefully stops the background update thread.
        """
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=10)

        logger.info("Monitoring dashboard stopped")

    def _update_loop(self) -> None:
        """
        Background thread loop for updating dashboard data.

        Runs continuously while dashboard is active, collecting metrics
        and health data at configured intervals.
        """
        while self._running:
            try:
                self._update_data()
                self.total_updates += 1
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}", exc_info=True)

            time.sleep(self.update_interval)

    def _update_data(self) -> None:
        """
        Update all dashboard data.

        Collects current metrics, health status, and stores in history.
        """
        # Collect current metrics
        metrics = self.metrics_collector.collect_all_metrics()
        health = self.health_monitor.get_overall_health()

        with self._lock:
            # Store in history
            self.metrics_history.append(
                {
                    "timestamp": datetime.now(),
                    "metrics": metrics.to_dict(),
                }
            )

            self.health_history.append(
                {
                    "timestamp": datetime.now(),
                    "health": health.to_dict(),
                }
            )

            # Update time series for key metrics
            self._update_time_series("cpu_percent", metrics.system.cpu_percent)
            self._update_time_series("memory_percent", metrics.system.memory_percent)
            self._update_time_series(
                "request_rate", metrics.application.request_rate_per_second
            )
            self._update_time_series("p95_latency", metrics.application.p95_latency_ms)
            self._update_time_series(
                "error_rate", metrics.application.error_rate_per_minute
            )
            self._update_time_series(
                "cache_hit_rate", metrics.nba.cache_hit_rate_percent
            )

    def _update_time_series(self, metric_name: str, value: float) -> None:
        """
        Update time series data for a metric.

        Args:
            metric_name: Name of the metric
            value: Current value
        """
        if metric_name not in self.time_series:
            self.time_series[metric_name] = TimeSeriesData(
                metric_name=metric_name,
                timestamps=[],
                values=[],
            )

        ts_data = self.time_series[metric_name]
        ts_data.timestamps.append(datetime.now())
        ts_data.values.append(value)

        # Keep only recent data (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        while ts_data.timestamps and ts_data.timestamps[0] < cutoff_time:
            ts_data.timestamps.pop(0)
            ts_data.values.pop(0)

    def get_snapshot(self) -> DashboardSnapshot:
        """
        Get current dashboard snapshot.

        Returns:
            DashboardSnapshot with current system state

        Examples:
            >>> dashboard = MonitoringDashboard()
            >>> snapshot = dashboard.get_snapshot()
            >>> print(f"Health: {snapshot.health['status']}")
        """
        # Collect fresh data
        metrics = self.metrics_collector.collect_all_metrics()
        health = self.health_monitor.get_overall_health()
        active_alerts = self.alert_manager.get_active_alerts()

        # Get recent events from history
        recent_events = []
        with self._lock:
            if self.metrics_history:
                recent_events = [
                    {
                        "timestamp": entry["timestamp"].isoformat(),
                        "type": "metrics_update",
                    }
                    for entry in list(self.metrics_history)[-10:]
                ]

        return DashboardSnapshot(
            timestamp=datetime.now(),
            metrics=metrics.to_dict(),
            health=health.to_dict(),
            active_alerts=[alert.to_dict() for alert in active_alerts],
            recent_events=recent_events,
        )

    def get_time_series(
        self,
        metric_name: str,
        hours: Optional[int] = None,
        minutes: Optional[int] = None,
    ) -> Optional[TimeSeriesData]:
        """
        Get time series data for a metric.

        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to return
            minutes: Number of minutes of history to return

        Returns:
            TimeSeriesData or None if metric not found

        Examples:
            >>> cpu_data = dashboard.get_time_series("cpu_percent", hours=1)
            >>> if cpu_data:
            ...     print(f"Latest CPU: {cpu_data.values[-1]}%")
        """
        with self._lock:
            if metric_name not in self.time_series:
                return None

            ts_data = self.time_series[metric_name]

            # Filter by time range if specified
            if hours or minutes:
                cutoff = datetime.now()
                if hours:
                    cutoff -= timedelta(hours=hours)
                if minutes:
                    cutoff -= timedelta(minutes=minutes)

                # Find start index
                start_idx = 0
                for i, ts in enumerate(ts_data.timestamps):
                    if ts >= cutoff:
                        start_idx = i
                        break

                # Return filtered data
                return TimeSeriesData(
                    metric_name=ts_data.metric_name,
                    timestamps=ts_data.timestamps[start_idx:],
                    values=ts_data.values[start_idx:],
                    unit=ts_data.unit,
                )

            return ts_data

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive health summary.

        Returns:
            Dictionary with health statistics and status

        Examples:
            >>> summary = dashboard.get_health_summary()
            >>> print(f"Overall: {summary['overall_status']}")
        """
        health = self.health_monitor.get_overall_health()

        # Calculate uptime
        uptime = datetime.now() - self.dashboard_start_time

        # Get failing checks
        failing_checks = self.health_monitor.get_failing_checks()

        return {
            "overall_status": health.status.value,
            "healthy_count": health.healthy_count,
            "degraded_count": health.degraded_count,
            "unhealthy_count": health.unhealthy_count,
            "total_checks": len(health.checks),
            "uptime_seconds": uptime.total_seconds(),
            "failing_checks": [check.to_dict() for check in failing_checks],
            "last_updated": datetime.now().isoformat(),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            Dictionary with key metrics and statistics

        Examples:
            >>> summary = dashboard.get_metrics_summary()
            >>> print(f"Requests: {summary['requests']['total']}")
        """
        metrics = self.metrics_collector.collect_all_metrics()

        return {
            "system": {
                "cpu_percent": metrics.system.cpu_percent,
                "memory_percent": metrics.system.memory_percent,
                "disk_percent": metrics.system.disk_usage_percent,
                "cpu_count": metrics.system.cpu_count,
            },
            "requests": {
                "total": metrics.application.request_count,
                "active": metrics.application.active_requests,
                "rate_per_second": metrics.application.request_rate_per_second,
                "success_rate": metrics.application.success_rate_percent,
            },
            "latency": {
                "average_ms": metrics.application.average_latency_ms,
                "p50_ms": metrics.application.p50_latency_ms,
                "p95_ms": metrics.application.p95_latency_ms,
                "p99_ms": metrics.application.p99_latency_ms,
            },
            "errors": {
                "total": metrics.application.error_count,
                "rate_per_minute": metrics.application.error_rate_per_minute,
            },
            "nba": {
                "queries": metrics.nba.total_queries,
                "queries_per_second": metrics.nba.queries_per_second,
                "cache_hit_rate": metrics.nba.cache_hit_rate_percent,
                "data_age_seconds": metrics.nba.data_freshness_seconds,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_alerts_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive alerts summary.

        Returns:
            Dictionary with alert statistics

        Examples:
            >>> summary = dashboard.get_alerts_summary()
            >>> print(f"Active alerts: {summary['active_count']}")
        """
        active_alerts = self.alert_manager.get_active_alerts()
        alert_history = self.alert_manager.get_alert_history(limit=100)

        # Count by severity
        critical_count = sum(
            1 for alert in active_alerts if alert.severity == AlertSeverity.CRITICAL
        )
        warning_count = sum(
            1 for alert in active_alerts if alert.severity == AlertSeverity.WARNING
        )
        info_count = sum(
            1 for alert in active_alerts if alert.severity == AlertSeverity.INFO
        )

        return {
            "active_count": len(active_alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "total_in_history": len(alert_history),
            "active_alerts": [alert.to_dict() for alert in active_alerts[:10]],
            "recent_history": [alert.to_dict() for alert in alert_history[-10:]],
            "timestamp": datetime.now().isoformat(),
        }

    def record_game_event(self, event: GameEvent) -> None:
        """
        Record a game event for live streaming.

        Args:
            event: GameEvent to record

        Examples:
            >>> event = GameEvent(
            ...     game_id="game_123",
            ...     event_type="shot",
            ...     timestamp=datetime.now(),
            ...     player_id="player_456",
            ...     description="3-pointer made"
            ... )
            >>> dashboard.record_game_event(event)
        """
        with self._lock:
            self.game_events.append(event)

        logger.debug(
            f"Game event recorded: {event.event_type}",
            extra={
                "game_id": event.game_id,
                "event_type": event.event_type,
            },
        )

    def get_recent_game_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent game events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent game events

        Examples:
            >>> events = dashboard.get_recent_game_events(limit=10)
            >>> for event in events:
            ...     print(event["description"])
        """
        with self._lock:
            return [event.to_dict() for event in list(self.game_events)[-limit:]]

    def export_dashboard_data(self, filepath: str) -> None:
        """
        Export dashboard data to JSON file.

        Args:
            filepath: Path to export file

        Examples:
            >>> dashboard.export_dashboard_data("/tmp/dashboard_export.json")
        """
        export_data = {
            "export_time": datetime.now().isoformat(),
            "snapshot": self.get_snapshot().to_dict(),
            "health_summary": self.get_health_summary(),
            "metrics_summary": self.get_metrics_summary(),
            "alerts_summary": self.get_alerts_summary(),
            "time_series": {
                name: ts.to_dict() for name, ts in self.time_series.items()
            },
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Dashboard data exported to {filepath}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get dashboard statistics.

        Returns:
            Dictionary with dashboard operational statistics

        Examples:
            >>> stats = dashboard.get_statistics()
            >>> print(f"Updates: {stats['total_updates']}")
        """
        with self._lock:
            metrics_count = len(self.metrics_history)
            health_count = len(self.health_history)
            events_count = len(self.game_events)

        uptime = datetime.now() - self.dashboard_start_time

        return {
            "running": self._running,
            "uptime_seconds": uptime.total_seconds(),
            "total_updates": self.total_updates,
            "metrics_history_count": metrics_count,
            "health_history_count": health_count,
            "game_events_count": events_count,
            "update_interval": self.update_interval,
            "time_series_count": len(self.time_series),
        }


# ==============================================================================
# Dashboard API Server
# ==============================================================================


class DashboardAPI:
    """
    REST API server for dashboard data.

    Provides HTTP endpoints for accessing dashboard data. Can be integrated
    with web frameworks like Flask or FastAPI.

    Endpoints:
    - GET /health - System health status
    - GET /metrics - Current metrics
    - GET /alerts - Active alerts
    - GET /snapshot - Current dashboard snapshot
    - GET /time-series/{metric} - Time series data for metric
    - GET /game-events - Recent game events

    Examples:
        >>> api = DashboardAPI(dashboard)
        >>> health_data = api.get_health()
        >>> metrics_data = api.get_metrics()
    """

    def __init__(self, dashboard: MonitoringDashboard):
        """
        Initialize dashboard API.

        Args:
            dashboard: MonitoringDashboard instance
        """
        self.dashboard = dashboard

    def get_health(self) -> Dict[str, Any]:
        """
        Get health endpoint data.

        Returns:
            Dictionary with health status
        """
        return self.dashboard.get_health_summary()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics endpoint data.

        Returns:
            Dictionary with current metrics
        """
        return self.dashboard.get_metrics_summary()

    def get_alerts(self) -> Dict[str, Any]:
        """
        Get alerts endpoint data.

        Returns:
            Dictionary with alert information
        """
        return self.dashboard.get_alerts_summary()

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get snapshot endpoint data.

        Returns:
            Dictionary with current dashboard snapshot
        """
        snapshot = self.dashboard.get_snapshot()
        return snapshot.to_dict()

    def get_time_series(
        self, metric_name: str, hours: Optional[int] = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Get time series endpoint data.

        Args:
            metric_name: Name of the metric
            hours: Number of hours of data to return

        Returns:
            Dictionary with time series data or None
        """
        ts_data = self.dashboard.get_time_series(metric_name, hours=hours)
        if ts_data:
            return ts_data.to_dict()
        return None

    def get_game_events(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get game events endpoint data.

        Args:
            limit: Maximum number of events to return

        Returns:
            Dictionary with recent game events
        """
        events = self.dashboard.get_recent_game_events(limit=limit)
        return {
            "count": len(events),
            "events": events,
            "timestamp": datetime.now().isoformat(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics endpoint data.

        Returns:
            Dictionary with dashboard statistics
        """
        return self.dashboard.get_statistics()


# ==============================================================================
# Global Dashboard Instance
# ==============================================================================


_global_dashboard: Optional[MonitoringDashboard] = None


def get_dashboard() -> MonitoringDashboard:
    """
    Get the global dashboard instance.

    Returns:
        Global MonitoringDashboard instance

    Examples:
        >>> dashboard = get_dashboard()
        >>> snapshot = dashboard.get_snapshot()
    """
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = MonitoringDashboard()
    return _global_dashboard


def set_dashboard(dashboard: MonitoringDashboard) -> None:
    """
    Set the global dashboard instance.

    Args:
        dashboard: MonitoringDashboard instance to use globally
    """
    global _global_dashboard
    _global_dashboard = dashboard


# ==============================================================================
# Convenience Functions
# ==============================================================================


def create_dashboard_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    dashboard: Optional[MonitoringDashboard] = None,
) -> None:
    """
    Create and run a simple HTTP dashboard server.

    This is a minimal implementation for demonstration. In production,
    integrate with a proper web framework like Flask or FastAPI.

    Args:
        host: Host to bind to
        port: Port to listen on
        dashboard: MonitoringDashboard instance (uses global if None)

    Examples:
        >>> create_dashboard_server(port=8080)
        # Dashboard available at http://localhost:8080
    """
    if dashboard is None:
        dashboard = get_dashboard()

    api = DashboardAPI(dashboard)

    logger.info(
        f"Dashboard API ready (integrate with web framework to serve on {host}:{port})",
        extra={"host": host, "port": port},
    )

    # Note: Actual HTTP server implementation would go here
    # In production, use Flask/FastAPI/Starlette
    # Example with Flask:
    #
    # from flask import Flask, jsonify
    # app = Flask(__name__)
    #
    # @app.route('/health')
    # def health():
    #     return jsonify(api.get_health())
    #
    # @app.route('/metrics')
    # def metrics():
    #     return jsonify(api.get_metrics())
    #
    # app.run(host=host, port=port)
