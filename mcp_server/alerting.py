"""Alerting System - CRITICAL 6"""
import os
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    LOG = "log"


class Alert:
    """Alert model"""
    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        channels: List[AlertChannel],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.message = message
        self.severity = severity
        self.channels = channels
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()


class AlertManager:
    """Centralized alert management"""

    def __init__(self):
        self.alert_history = []

    def send_alert(self, alert: Alert):
        """Send an alert through configured channels"""
        self.alert_history.append(alert)

        for channel in alert.channels:
            if channel == AlertChannel.EMAIL:
                self._send_email(alert)
            elif channel == AlertChannel.SLACK:
                self._send_slack(alert)
            elif channel == AlertChannel.PAGERDUTY:
                self._send_pagerduty(alert)
            elif channel == AlertChannel.LOG:
                self._log_alert(alert)

    def _send_email(self, alert: Alert):
        """Send email alert (implement with SES)"""
        logger.info(f"📧 [EMAIL] {alert.severity.value.upper()}: {alert.title}")
        # TODO: Implement AWS SES integration

    def _send_slack(self, alert: Alert):
        """Send Slack alert"""
        logger.info(f"💬 [SLACK] {alert.severity.value.upper()}: {alert.title}")
        # TODO: Implement Slack webhook

    def _send_pagerduty(self, alert: Alert):
        """Send PagerDuty alert"""
        logger.info(f"🚨 [PAGERDUTY] {alert.severity.value.upper()}: {alert.title}")
        # TODO: Implement PagerDuty API

    def _log_alert(self, alert: Alert):
        """Log alert"""
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            logger.error(f"🚨 ALERT: {alert.title} - {alert.message}")
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(f"⚠️  ALERT: {alert.title} - {alert.message}")
        else:
            logger.info(f"ℹ️  ALERT: {alert.title} - {alert.message}")


# Global alert manager
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def alert(title: str, message: str, severity: AlertSeverity = AlertSeverity.INFO):
    """Quick alert function"""
    manager = get_alert_manager()
    alert_obj = Alert(
        title=title,
        message=message,
        severity=severity,
        channels=[AlertChannel.LOG, AlertChannel.SLACK]
    )
    manager.send_alert(alert_obj)


# Pre-configured alerts
def alert_database_down():
    """Alert when database is down"""
    alert(
        "Database Connection Failed",
        "Unable to connect to RDS database",
        AlertSeverity.CRITICAL
    )


def alert_high_error_rate(error_rate: float):
    """Alert when error rate is high"""
    alert(
        "High Error Rate Detected",
        f"Error rate: {error_rate:.2%} (threshold: 5%)",
        AlertSeverity.ERROR
    )


def alert_rate_limit_exceeded(user_id: str):
    """Alert when user exceeds rate limit"""
    alert(
        "Rate Limit Exceeded",
        f"User {user_id} exceeded rate limit",
        AlertSeverity.WARNING
    )

