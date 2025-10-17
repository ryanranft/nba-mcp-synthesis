"""
Smart Alerting System

Intelligent alerting with ML-based threshold detection:
- Dynamic thresholds
- Alert deduplication
- Smart escalation
- Alert fatigue reduction
- Anomaly-based alerts
- Context-aware notifications

Features:
- ML-based anomaly detection
- Alert correlation
- Auto-suppression
- Priority scoring
- Multi-channel delivery
- Alert analytics

Use Cases:
- System health monitoring
- Performance degradation
- Cost spikes
- Security incidents
- Data quality issues
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import threading
import hashlib

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Alert definition"""

    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    metric_name: str
    metric_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)

    # Context
    source: str = "system"
    tags: Dict[str, str] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    # State
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Priority (calculated)
    priority_score: float = 0.0

    def get_fingerprint(self) -> str:
        """Get unique fingerprint for deduplication"""
        content = f"{self.metric_name}:{self.title}:{self.source}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class AlertRule:
    """Alert rule definition"""

    rule_id: str
    metric_name: str
    condition: Callable[[float], bool]
    severity: AlertSeverity
    title_template: str
    description_template: str
    cooldown_seconds: int = 300  # 5 minutes
    enabled: bool = True


class DynamicThreshold:
    """Calculate dynamic thresholds based on historical data"""

    def __init__(self, window_size: int = 100, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity  # Standard deviations
        self.history: deque = deque(maxlen=window_size)

    def add_value(self, value: float) -> None:
        """Add value to history"""
        self.history.append(value)

    def get_threshold(self) -> Optional[float]:
        """Calculate dynamic threshold"""
        if len(self.history) < 10:  # Need minimum data
            return None

        # Calculate mean and std dev
        mean = sum(self.history) / len(self.history)
        variance = sum((x - mean) ** 2 for x in self.history) / len(self.history)
        std_dev = variance**0.5

        # Upper threshold = mean + (sensitivity * std_dev)
        threshold = mean + (self.sensitivity * std_dev)
        return threshold

    def is_anomaly(self, value: float) -> bool:
        """Check if value is anomalous"""
        threshold = self.get_threshold()
        if threshold is None:
            return False

        return value > threshold


class AlertDeduplicator:
    """Deduplicate similar alerts"""

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.recent_alerts: Dict[str, datetime] = {}
        self._lock = threading.RLock()

    def should_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent (not a duplicate)"""
        fingerprint = alert.get_fingerprint()

        with self._lock:
            if fingerprint in self.recent_alerts:
                last_alert_time = self.recent_alerts[fingerprint]
                time_since = (datetime.now() - last_alert_time).total_seconds()

                if time_since < self.window_seconds:
                    logger.debug(f"Alert suppressed (duplicate): {alert.title}")
                    return False

            # Record this alert
            self.recent_alerts[fingerprint] = datetime.now()

            # Cleanup old entries
            cutoff = datetime.now() - timedelta(seconds=self.window_seconds * 2)
            self.recent_alerts = {
                fp: ts for fp, ts in self.recent_alerts.items() if ts > cutoff
            }

            return True


class AlertCorrelator:
    """Correlate related alerts"""

    def __init__(self, correlation_window_seconds: int = 60):
        self.correlation_window = correlation_window_seconds
        self.recent_alerts: List[Alert] = []
        self._lock = threading.RLock()

    def add_alert(self, alert: Alert) -> Optional[str]:
        """Add alert and return correlation ID if correlated"""
        with self._lock:
            # Clean old alerts
            cutoff = datetime.now() - timedelta(seconds=self.correlation_window)
            self.recent_alerts = [a for a in self.recent_alerts if a.timestamp > cutoff]

            # Check for correlation
            for existing_alert in self.recent_alerts:
                if self._are_correlated(alert, existing_alert):
                    if existing_alert.correlation_id:
                        return existing_alert.correlation_id
                    else:
                        correlation_id = f"corr_{int(time.time())}"
                        existing_alert.correlation_id = correlation_id
                        return correlation_id

            # Add to recent
            self.recent_alerts.append(alert)
            return None

    def _are_correlated(self, alert1: Alert, alert2: Alert) -> bool:
        """Check if two alerts are correlated"""
        # Same source
        if alert1.source == alert2.source:
            return True

        # Similar metric names
        if alert1.metric_name.split("_")[0] == alert2.metric_name.split("_")[0]:
            return True

        # Common tags
        common_tags = set(alert1.tags.keys()) & set(alert2.tags.keys())
        if len(common_tags) >= 2:
            return True

        return False


class PriorityCalculator:
    """Calculate alert priority"""

    def calculate_priority(self, alert: Alert) -> float:
        """Calculate priority score (0-100)"""
        score = 0.0

        # Base score from severity
        severity_scores = {
            AlertSeverity.INFO: 10,
            AlertSeverity.WARNING: 30,
            AlertSeverity.ERROR: 60,
            AlertSeverity.CRITICAL: 90,
        }
        score = severity_scores[alert.severity]

        # Adjust based on how far metric is from threshold
        if alert.threshold > 0:
            deviation = abs(alert.metric_value - alert.threshold) / alert.threshold
            score += min(deviation * 10, 10)  # Max +10 points

        # Business hours boost (assume 9am-5pm is more important)
        hour = alert.timestamp.hour
        if 9 <= hour <= 17:
            score += 5

        # Tag-based priority
        if "production" in alert.tags.values():
            score += 10

        if "customer_facing" in alert.tags.values():
            score += 10

        return min(score, 100)


class AlertEscalator:
    """Handle alert escalation"""

    def __init__(self):
        self.escalation_rules: Dict[str, List[Dict[str, Any]]] = {}

    def add_escalation_rule(
        self, severity: AlertSeverity, levels: List[Dict[str, Any]]
    ) -> None:
        """
        Add escalation rule

        Example levels:
        [
            {'delay_seconds': 0, 'notify': ['oncall']},
            {'delay_seconds': 300, 'notify': ['oncall', 'manager']},
            {'delay_seconds': 900, 'notify': ['oncall', 'manager', 'director']}
        ]
        """
        self.escalation_rules[severity.name] = levels

    def get_notification_targets(
        self, alert: Alert, time_active_seconds: int
    ) -> List[str]:
        """Get who should be notified based on escalation"""
        levels = self.escalation_rules.get(alert.severity.name, [])

        targets = set()
        for level in levels:
            if time_active_seconds >= level["delay_seconds"]:
                targets.update(level["notify"])

        return list(targets)


class SmartAlertingSystem:
    """Main smart alerting system"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Components
        self.deduplicator = AlertDeduplicator()
        self.correlator = AlertCorrelator()
        self.priority_calc = PriorityCalculator()
        self.escalator = AlertEscalator()

        # Dynamic thresholds
        self.dynamic_thresholds: Dict[str, DynamicThreshold] = {}

        # Statistics
        self.total_alerts = 0
        self.suppressed_alerts = 0

        self._lock = threading.RLock()

    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule"""
        with self._lock:
            self.rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id}")

    def add_dynamic_threshold_metric(
        self, metric_name: str, window_size: int = 100, sensitivity: float = 2.0
    ) -> None:
        """Add metric with dynamic threshold"""
        self.dynamic_thresholds[metric_name] = DynamicThreshold(
            window_size=window_size, sensitivity=sensitivity
        )

    def check_metric(
        self,
        metric_name: str,
        value: float,
        source: str = "system",
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[Alert]:
        """Check metric value against rules"""

        # Update dynamic threshold
        if metric_name in self.dynamic_thresholds:
            dt = self.dynamic_thresholds[metric_name]
            dt.add_value(value)

            if dt.is_anomaly(value):
                return self._create_dynamic_alert(
                    metric_name, value, dt.get_threshold(), source, tags
                )

        # Check static rules
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if rule.metric_name == metric_name:
                if rule.condition(value):
                    return self._create_alert_from_rule(rule, value, source, tags)

        return None

    def _create_alert_from_rule(
        self, rule: AlertRule, value: float, source: str, tags: Optional[Dict[str, str]]
    ) -> Optional[Alert]:
        """Create alert from rule"""
        alert = Alert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            title=rule.title_template.format(metric=rule.metric_name, value=value),
            description=rule.description_template.format(
                metric=rule.metric_name, value=value
            ),
            severity=rule.severity,
            metric_name=rule.metric_name,
            metric_value=value,
            threshold=0.0,  # TODO: Extract from condition
            source=source,
            tags=tags or {},
        )

        return self._process_alert(alert)

    def _create_dynamic_alert(
        self,
        metric_name: str,
        value: float,
        threshold: float,
        source: str,
        tags: Optional[Dict[str, str]],
    ) -> Optional[Alert]:
        """Create alert from dynamic threshold"""
        alert = Alert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            title=f"Anomaly detected in {metric_name}",
            description=f"Value {value:.2f} exceeds dynamic threshold {threshold:.2f}",
            severity=AlertSeverity.WARNING,
            metric_name=metric_name,
            metric_value=value,
            threshold=threshold,
            source=source,
            tags=tags or {},
        )

        return self._process_alert(alert)

    def _process_alert(self, alert: Alert) -> Optional[Alert]:
        """Process and potentially send alert"""
        with self._lock:
            self.total_alerts += 1

            # Deduplication
            if not self.deduplicator.should_alert(alert):
                self.suppressed_alerts += 1
                alert.status = AlertStatus.SUPPRESSED
                return None

            # Correlation
            correlation_id = self.correlator.add_alert(alert)
            if correlation_id:
                alert.correlation_id = correlation_id

            # Priority calculation
            alert.priority_score = self.priority_calc.calculate_priority(alert)

            # Store alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

            logger.warning(
                f"ALERT: {alert.title} (severity: {alert.severity.name}, "
                f"priority: {alert.priority_score:.1f})"
            )

            return alert

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = user
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                del self.active_alerts[alert_id]
                logger.info(f"Alert {alert_id} resolved")
                return True
            return False

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None, min_priority: float = 0.0
    ) -> List[Alert]:
        """Get active alerts"""
        with self._lock:
            alerts = list(self.active_alerts.values())

            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            if min_priority > 0:
                alerts = [a for a in alerts if a.priority_score >= min_priority]

            # Sort by priority descending
            alerts.sort(key=lambda a: a.priority_score, reverse=True)

            return alerts

    def get_stats(self) -> Dict[str, Any]:
        """Get alerting statistics"""
        with self._lock:
            active_by_severity = defaultdict(int)
            for alert in self.active_alerts.values():
                active_by_severity[alert.severity.name] += 1

            return {
                "total_alerts": self.total_alerts,
                "suppressed_alerts": self.suppressed_alerts,
                "suppression_rate": (
                    self.suppressed_alerts / self.total_alerts * 100
                    if self.total_alerts > 0
                    else 0
                ),
                "active_alerts": len(self.active_alerts),
                "active_by_severity": dict(active_by_severity),
                "rules_configured": len(self.rules),
                "dynamic_thresholds": len(self.dynamic_thresholds),
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Smart Alerting System Demo ===\n")

    # Create system
    alerting = SmartAlertingSystem()

    # Add static rule
    print("--- Adding Alert Rules ---\n")
    alerting.add_rule(
        AlertRule(
            rule_id="high_cpu",
            metric_name="cpu_usage",
            condition=lambda x: x > 80.0,
            severity=AlertSeverity.WARNING,
            title_template="High CPU usage: {value}%",
            description_template="CPU usage ({value}%) exceeded threshold on {metric}",
        )
    )

    # Add dynamic threshold
    alerting.add_dynamic_threshold_metric(
        "response_time_ms", window_size=50, sensitivity=2.0
    )

    print("✓ Rules configured\n")

    # Simulate normal response times
    print("--- Learning Normal Behavior ---")
    for i in range(30):
        alerting.check_metric(
            "response_time_ms", 100 + (i % 10) * 5, tags={"env": "prod"}
        )
    print("✓ Baseline established\n")

    # Trigger alerts
    print("--- Triggering Alerts ---\n")

    # Static rule alert
    alert1 = alerting.check_metric(
        "cpu_usage", 85.0, source="server-01", tags={"env": "prod"}
    )
    if alert1:
        print(
            f"✓ Alert created: {alert1.title} (priority: {alert1.priority_score:.1f})"
        )

    # Dynamic threshold alert
    alert2 = alerting.check_metric(
        "response_time_ms", 250.0, source="api", tags={"env": "prod"}
    )
    if alert2:
        print(
            f"✓ Alert created: {alert2.title} (priority: {alert2.priority_score:.1f})"
        )

    # Duplicate (should be suppressed)
    alert3 = alerting.check_metric(
        "cpu_usage", 86.0, source="server-01", tags={"env": "prod"}
    )
    if not alert3:
        print("✓ Duplicate alert suppressed")

    # Get active alerts
    print("\n--- Active Alerts ---")
    active = alerting.get_active_alerts(min_priority=30)
    for alert in active:
        print(
            f"  - [{alert.severity.name}] {alert.title} (priority: {alert.priority_score:.1f})"
        )

    # Statistics
    print("\n--- Alerting Statistics ---")
    stats = alerting.get_stats()
    print(f"Total alerts: {stats['total_alerts']}")
    print(
        f"Suppressed: {stats['suppressed_alerts']} ({stats['suppression_rate']:.1f}%)"
    )
    print(f"Active: {stats['active_alerts']}")
    print(f"By severity: {stats['active_by_severity']}")

    print("\n=== Demo Complete ===")
