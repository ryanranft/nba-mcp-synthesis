"""
Alert System Module

Monitors betting system health and generates alerts for:
- Poor performance (ROI, win rate, Sharpe ratio)
- Calibration drift (Brier score, log loss)
- Risk metrics (max drawdown, losing streaks)
- Data quality issues

Features:
- Configurable thresholds for critical/warning/healthy states
- Alert history tracking
- Integration with notification systems (email, Slack)
- Calibration drift detection
- Performance trend analysis

Key Concepts:
-------------
1. **Alert Levels:**
   - CRITICAL (🔴): Immediate action required, system at risk
   - WARNING (🟡): Monitor closely, potential issues
   - INFO (🔵): Notable events, no action needed
   - HEALTHY (🟢): System operating normally

2. **Alert Categories:**
   - Performance: ROI, win rate, Sharpe ratio
   - Risk: Drawdown, losing streaks, bet sizing
   - Calibration: Brier score, log loss, prediction accuracy
   - Data Quality: Missing data, stale predictions

3. **Alert Persistence:**
   - All alerts saved to SQLite database
   - Alert history for trend analysis
   - Deduplication to avoid spam

Example:
-------
    from mcp_server.betting.alert_system import AlertSystem
    from mcp_server.betting.paper_trading import PaperTradingEngine
    from mcp_server.betting.probability_calibration import SimulationCalibrator

    # Initialize alert system
    alert_system = AlertSystem(
        db_path="data/alerts.db",
        notification_config={
            'email_enabled': True,
            'slack_enabled': False
        }
    )

    # Check paper trading performance
    engine = PaperTradingEngine(...)
    stats = engine.get_performance_stats()

    alerts = alert_system.check_performance_metrics(stats)

    # Check calibration quality
    calibrator = SimulationCalibrator(...)
    brier = calibrator.calibration_quality()

    cal_alerts = alert_system.check_calibration_quality(brier)

    # Send notifications for critical alerts
    critical_alerts = [a for a in alerts if a.level == 'CRITICAL']
    if critical_alerts:
        alert_system.send_notifications(critical_alerts)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import sqlite3
import json
from pathlib import Path
import warnings


class AlertLevel(str, Enum):
    """Alert severity levels"""

    CRITICAL = "critical"  # 🔴 Immediate action required
    WARNING = "warning"  # 🟡 Monitor closely
    INFO = "info"  # 🔵 Notable event
    HEALTHY = "healthy"  # 🟢 System normal


class AlertCategory(str, Enum):
    """Alert category types"""

    PERFORMANCE = "performance"
    RISK = "risk"
    CALIBRATION = "calibration"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"


@dataclass
class Alert:
    """
    Represents a single alert

    Attributes:
        alert_id: Unique identifier
        timestamp: When alert was generated
        level: Alert severity (critical, warning, info, healthy)
        category: Alert category
        metric: Metric that triggered alert
        value: Current metric value
        threshold: Threshold that was breached
        message: Human-readable alert message
        metadata: Additional context
        resolved: Whether alert has been resolved
        resolved_at: When alert was resolved
    """

    alert_id: str
    timestamp: datetime
    level: AlertLevel
    category: AlertCategory
    metric: str
    value: float
    threshold: float
    message: str
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d["level"] = self.level.value
        d["category"] = self.category.value
        d["timestamp"] = self.timestamp.isoformat()
        if self.resolved_at:
            d["resolved_at"] = self.resolved_at.isoformat()
        return d

    def __str__(self) -> str:
        """String representation"""
        icons = {
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.WARNING: "🟡",
            AlertLevel.INFO: "🔵",
            AlertLevel.HEALTHY: "🟢",
        }
        icon = icons.get(self.level, "⚪")
        return (
            f"{icon} [{self.level.value.upper()}] {self.category.value}: {self.message}"
        )


class AlertDatabase:
    """
    SQLite database for alert persistence

    Tracks alert history, enables deduplication, and provides
    trend analysis capabilities.
    """

    def __init__(self, db_path: str = "data/alerts.db"):
        """
        Initialize alert database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                threshold REAL NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Index for querying by timestamp and level
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
            ON alerts(timestamp DESC)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_level
            ON alerts(level)
        """
        )

        conn.commit()
        conn.close()

    def save_alert(self, alert: Alert):
        """
        Save alert to database

        Args:
            alert: Alert to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO alerts (
                alert_id, timestamp, level, category, metric,
                value, threshold, message, metadata, resolved, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alert.alert_id,
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.category.value,
                alert.metric,
                alert.value,
                alert.threshold,
                alert.message,
                json.dumps(alert.metadata) if alert.metadata else None,
                1 if alert.resolved else 0,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
            ),
        )

        conn.commit()
        conn.close()

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Retrieve alert by ID

        Args:
            alert_id: Alert identifier

        Returns:
            Alert object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT alert_id, timestamp, level, category, metric,
                   value, threshold, message, metadata, resolved, resolved_at
            FROM alerts WHERE alert_id = ?
        """,
            (alert_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Alert(
            alert_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            level=AlertLevel(row[2]),
            category=AlertCategory(row[3]),
            metric=row[4],
            value=row[5],
            threshold=row[6],
            message=row[7],
            metadata=json.loads(row[8]) if row[8] else None,
            resolved=bool(row[9]),
            resolved_at=datetime.fromisoformat(row[10]) if row[10] else None,
        )

    def get_recent_alerts(
        self,
        hours: int = 24,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None,
    ) -> List[Alert]:
        """
        Get recent alerts

        Args:
            hours: Number of hours to look back
            level: Filter by alert level
            category: Filter by alert category

        Returns:
            List of Alert objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        query = """
            SELECT alert_id, timestamp, level, category, metric,
                   value, threshold, message, metadata, resolved, resolved_at
            FROM alerts WHERE timestamp >= ?
        """
        params = [cutoff]

        if level:
            query += " AND level = ?"
            params.append(level.value)

        if category:
            query += " AND category = ?"
            params.append(category.value)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            Alert(
                alert_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                level=AlertLevel(row[2]),
                category=AlertCategory(row[3]),
                metric=row[4],
                value=row[5],
                threshold=row[6],
                message=row[7],
                metadata=json.loads(row[8]) if row[8] else None,
                resolved=bool(row[9]),
                resolved_at=datetime.fromisoformat(row[10]) if row[10] else None,
            )
            for row in rows
        ]

    def resolve_alert(self, alert_id: str):
        """
        Mark alert as resolved

        Args:
            alert_id: Alert to resolve
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE alerts
            SET resolved = 1, resolved_at = ?
            WHERE alert_id = ?
        """,
            (datetime.now().isoformat(), alert_id),
        )

        conn.commit()
        conn.close()


class AlertSystem:
    """
    Main alert system for monitoring betting system health

    Checks performance metrics, calibration quality, and risk metrics
    against configurable thresholds. Generates and persists alerts.
    """

    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "roi": {"critical": -0.10, "warning": 0.0, "healthy": 0.05},
        "win_rate": {"critical": 0.45, "warning": 0.50, "healthy": 0.55},
        "sharpe_ratio": {"critical": 0.5, "warning": 1.0, "healthy": 1.5},
        "brier_score": {"critical": 0.20, "warning": 0.15, "healthy": 0.10},
        "log_loss": {"critical": 0.70, "warning": 0.60, "healthy": 0.50},
        "max_drawdown": {"critical": 0.30, "warning": 0.20, "healthy": 0.15},
        "clv": {"critical": -0.05, "warning": 0.0, "healthy": 0.02},
        "losing_streak": {"critical": 10, "warning": 5, "healthy": 3},
    }

    def __init__(
        self,
        db_path: str = "data/alerts.db",
        thresholds: Optional[Dict[str, Dict[str, float]]] = None,
        notification_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize alert system

        Args:
            db_path: Path to alert database
            thresholds: Custom thresholds (overrides defaults)
            notification_config: Notification settings
        """
        self.db = AlertDatabase(db_path)
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.notification_config = notification_config or {}

    def _generate_alert_id(self, category: str, metric: str) -> str:
        """Generate unique alert ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{category}_{metric}_{timestamp}"

    def _get_alert_level(self, metric: str, value: float) -> AlertLevel:
        """
        Determine alert level for a metric

        Args:
            metric: Metric name
            value: Metric value

        Returns:
            AlertLevel enum
        """
        if metric not in self.thresholds:
            return AlertLevel.INFO

        thresholds = self.thresholds[metric]

        # Handle metrics where lower is better
        if metric in ["brier_score", "log_loss", "max_drawdown", "losing_streak"]:
            if value >= thresholds["critical"]:
                return AlertLevel.CRITICAL
            elif value >= thresholds["warning"]:
                return AlertLevel.WARNING
            else:
                return AlertLevel.HEALTHY
        else:
            # Higher is better
            if value <= thresholds["critical"]:
                return AlertLevel.CRITICAL
            elif value <= thresholds["warning"]:
                return AlertLevel.WARNING
            else:
                return AlertLevel.HEALTHY

    def check_performance_metrics(self, stats: Dict[str, Any]) -> List[Alert]:
        """
        Check performance metrics and generate alerts

        Args:
            stats: Performance statistics from PaperTradingEngine

        Returns:
            List of Alert objects
        """
        alerts = []

        # Only check if we have enough data
        if stats.get("total_bets", 0) < 10:
            return alerts

        # Metrics to check
        metrics_to_check = {
            "roi": (stats.get("roi", 0), "ROI", AlertCategory.PERFORMANCE),
            "win_rate": (
                stats.get("win_rate", 0),
                "Win Rate",
                AlertCategory.PERFORMANCE,
            ),
            "sharpe_ratio": (
                stats.get("sharpe_ratio", 0),
                "Sharpe Ratio",
                AlertCategory.RISK,
            ),
            "max_drawdown": (
                abs(stats.get("max_drawdown", 0)) / stats.get("bankroll", 1),
                "Max Drawdown",
                AlertCategory.RISK,
            ),
            "clv": (stats.get("avg_clv", 0), "CLV", AlertCategory.PERFORMANCE),
        }

        for metric_key, (value, metric_name, category) in metrics_to_check.items():
            level = self._get_alert_level(metric_key, value)

            # Only create alert for critical/warning
            if level in [AlertLevel.CRITICAL, AlertLevel.WARNING]:
                threshold = self.thresholds[metric_key][level.value]

                # Create alert message
                if metric_key in ["roi", "win_rate", "clv"]:
                    message = f"{metric_name} is {value*100:.1f}% (threshold: {threshold*100:.1f}%)"
                elif metric_key == "max_drawdown":
                    message = f"{metric_name} is {value*100:.1f}% (threshold: {threshold*100:.1f}%)"
                else:
                    message = (
                        f"{metric_name} is {value:.2f} (threshold: {threshold:.2f})"
                    )

                alert = Alert(
                    alert_id=self._generate_alert_id(category.value, metric_key),
                    timestamp=datetime.now(),
                    level=level,
                    category=category,
                    metric=metric_key,
                    value=value,
                    threshold=threshold,
                    message=message,
                    metadata={"stats": stats},
                )

                self.db.save_alert(alert)
                alerts.append(alert)

        return alerts

    def check_calibration_quality(
        self,
        brier_score: float,
        log_loss: Optional[float] = None,
        num_predictions: int = 0,
    ) -> List[Alert]:
        """
        Check calibration quality and generate alerts

        Args:
            brier_score: Current Brier score
            log_loss: Current log loss (optional)
            num_predictions: Number of predictions in calibration dataset

        Returns:
            List of Alert objects
        """
        alerts = []

        # Only check if we have enough data
        if num_predictions < 20:
            return alerts

        # Check Brier score
        level = self._get_alert_level("brier_score", brier_score)

        if level in [AlertLevel.CRITICAL, AlertLevel.WARNING]:
            threshold = self.thresholds["brier_score"][level.value]

            alert = Alert(
                alert_id=self._generate_alert_id("calibration", "brier_score"),
                timestamp=datetime.now(),
                level=level,
                category=AlertCategory.CALIBRATION,
                metric="brier_score",
                value=brier_score,
                threshold=threshold,
                message=f"Brier score is {brier_score:.4f} (threshold: {threshold:.4f})",
                metadata={"num_predictions": num_predictions},
            )

            self.db.save_alert(alert)
            alerts.append(alert)

        # Check log loss if provided
        if log_loss is not None:
            level = self._get_alert_level("log_loss", log_loss)

            if level in [AlertLevel.CRITICAL, AlertLevel.WARNING]:
                threshold = self.thresholds["log_loss"][level.value]

                alert = Alert(
                    alert_id=self._generate_alert_id("calibration", "log_loss"),
                    timestamp=datetime.now(),
                    level=level,
                    category=AlertCategory.CALIBRATION,
                    metric="log_loss",
                    value=log_loss,
                    threshold=threshold,
                    message=f"Log loss is {log_loss:.4f} (threshold: {threshold:.4f})",
                    metadata={"num_predictions": num_predictions},
                )

                self.db.save_alert(alert)
                alerts.append(alert)

        return alerts

    def check_losing_streak(self, current_streak: int) -> List[Alert]:
        """
        Check for dangerous losing streaks

        Args:
            current_streak: Current losing streak (negative number)

        Returns:
            List of Alert objects
        """
        alerts = []

        if current_streak >= 0:  # Not a losing streak
            return alerts

        losing_streak = abs(current_streak)
        level = self._get_alert_level("losing_streak", losing_streak)

        if level in [AlertLevel.CRITICAL, AlertLevel.WARNING]:
            threshold = self.thresholds["losing_streak"][level.value]

            alert = Alert(
                alert_id=self._generate_alert_id("risk", "losing_streak"),
                timestamp=datetime.now(),
                level=level,
                category=AlertCategory.RISK,
                metric="losing_streak",
                value=losing_streak,
                threshold=threshold,
                message=f"Losing streak of {losing_streak} bets (threshold: {threshold})",
                metadata={"current_streak": current_streak},
            )

            self.db.save_alert(alert)
            alerts.append(alert)

        return alerts

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of recent alerts

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with alert summary
        """
        all_alerts = self.db.get_recent_alerts(hours=hours)

        critical = [a for a in all_alerts if a.level == AlertLevel.CRITICAL]
        warnings = [a for a in all_alerts if a.level == AlertLevel.WARNING]
        info = [a for a in all_alerts if a.level == AlertLevel.INFO]

        return {
            "total_alerts": len(all_alerts),
            "critical": len(critical),
            "warnings": len(warnings),
            "info": len(info),
            "critical_alerts": critical,
            "warning_alerts": warnings,
            "info_alerts": info,
            "has_critical": len(critical) > 0,
            "has_warnings": len(warnings) > 0,
        }

    def send_notifications(self, alerts: List[Alert]) -> Dict[str, Any]:
        """
        Send notifications for alerts via configured channels

        Args:
            alerts: List of alerts to notify about

        Returns:
            Dict with notification results per channel
        """
        if not alerts:
            return {}

        # Check if notification is enabled
        if not self.notification_config:
            warnings.warn("Notification config not provided. Skipping notifications.")
            return {}

        try:
            from mcp_server.betting.notifications import NotificationManager

            # Initialize notification manager
            notifier = NotificationManager(config=self.notification_config)

            # Send batch notification
            if len(alerts) == 1:
                results = notifier.send_alert(alerts[0])
            else:
                results = notifier.send_alert_batch(alerts)

            return {
                "sent": sum(1 for r in results.values() if r.success),
                "failed": sum(1 for r in results.values() if not r.success),
                "results": results,
            }

        except ImportError:
            warnings.warn("Notification module not available")
            return {}
        except Exception as e:
            warnings.warn(f"Failed to send notifications: {e}")
            return {}
