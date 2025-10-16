#!/usr/bin/env python3
"""
Secrets Alerting System

Comprehensive alerting system for secrets health monitoring with multiple notification channels.
Provides intelligent alerting with escalation, deduplication, and customizable thresholds.

Features:
- Multi-channel notifications (Slack, Email, SMS, Webhook)
- Intelligent alert deduplication and throttling
- Escalation policies and alert routing
- Customizable alert thresholds and conditions
- Alert history and analytics
- Integration with secrets health monitor
- Template-based message formatting
"""

import os
import sys
import json
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
from collections import defaultdict, deque
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/secrets_alerting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    CONSOLE = "console"

@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    channels: List[AlertChannel]
    throttle_minutes: int = 15
    escalation_minutes: int = 60
    enabled: bool = True
    description: str = ""

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    message: str
    metadata: Dict[str, Any]
    timestamp: datetime
    channels: List[AlertChannel]
    escalated: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class NotificationTemplate:
    """Notification template"""
    channel: AlertChannel
    template: str
    subject_template: Optional[str] = None

class AlertDeduplicator:
    """Intelligent alert deduplication and throttling"""

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self.alert_history: deque = deque(maxlen=max_alerts)
        self.throttle_cache: Dict[str, datetime] = {}
        self.lock = threading.Lock()

    def should_send_alert(self, alert: Alert, throttle_minutes: int = 15) -> bool:
        """Check if alert should be sent based on deduplication rules"""
        with self.lock:
            # Generate deduplication key
            dedup_key = self._generate_dedup_key(alert)

            # Check throttle
            if dedup_key in self.throttle_cache:
                last_sent = self.throttle_cache[dedup_key]
                if datetime.now() - last_sent < timedelta(minutes=throttle_minutes):
                    logger.debug(f"Alert throttled: {alert.title}")
                    return False

            # Check for similar recent alerts
            cutoff_time = datetime.now() - timedelta(minutes=throttle_minutes)
            similar_alerts = [
                a for a in self.alert_history
                if a.timestamp >= cutoff_time and self._is_similar_alert(a, alert)
            ]

            if similar_alerts:
                logger.debug(f"Similar alert found, skipping: {alert.title}")
                return False

            # Add to history and cache
            self.alert_history.append(alert)
            self.throttle_cache[dedup_key] = datetime.now()

            return True

    def _generate_dedup_key(self, alert: Alert) -> str:
        """Generate deduplication key for alert"""
        key_data = f"{alert.rule_name}:{alert.title}:{alert.severity.value}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_similar_alert(self, alert1: Alert, alert2: Alert) -> bool:
        """Check if two alerts are similar"""
        return (
            alert1.rule_name == alert2.rule_name and
            alert1.title == alert2.title and
            alert1.severity == alert2.severity
        )

class SlackNotifier:
    """Enhanced Slack notification system"""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.session = requests.Session()

    def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            # Determine color based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9500",
                AlertSeverity.CRITICAL: "#ff0000",
                AlertSeverity.EMERGENCY: "#8b0000"
            }

            color = color_map.get(alert.severity, "#36a64f")

            # Create rich message
            message = {
                "channel": self.channel,
                "username": "Secrets Alert System",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Rule",
                                "value": alert.rule_name,
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.id[:8],
                                "short": True
                            }
                        ],
                        "footer": "Secrets Alert System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            # Add metadata if available
            if alert.metadata:
                metadata_text = "\n".join([
                    f"• {k}: {v}" for k, v in alert.metadata.items()
                ])
                message["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": metadata_text,
                    "short": False
                })

            response = self.session.post(self.webhook_url, json=message, timeout=10)

            if response.status_code == 200:
                logger.info(f"Slack alert sent successfully: {alert.title}")
                return True
            else:
                logger.warning(f"Failed to send Slack alert: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False

class EmailNotifier:
    """Email notification system"""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_alert(self, alert: Alert, recipients: List[str]) -> bool:
        """Send alert via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create HTML body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: {'#d4edda' if alert.severity == AlertSeverity.INFO else '#fff3cd' if alert.severity == AlertSeverity.WARNING else '#f8d7da'}; border: 1px solid {'#c3e6cb' if alert.severity == AlertSeverity.INFO else '#ffeaa7' if alert.severity == AlertSeverity.WARNING else '#f5c6cb'}; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 10px 0; color: {'#155724' if alert.severity == AlertSeverity.INFO else '#856404' if alert.severity == AlertSeverity.WARNING else '#721c24'};">
                            🚨 {alert.title}
                        </h2>
                        <p style="margin: 0; font-size: 14px; color: {'#155724' if alert.severity == AlertSeverity.INFO else '#856404' if alert.severity == AlertSeverity.WARNING else '#721c24'};">
                            Severity: {alert.severity.value.upper()} | Rule: {alert.rule_name}
                        </p>
                    </div>

                    <div style="background: #f8f9fa; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #495057;">Alert Details</h3>
                        <p style="margin: 0; white-space: pre-wrap;">{alert.message}</p>
                    </div>

                    <div style="background: #e9ecef; border-radius: 5px; padding: 15px;">
                        <h3 style="margin: 0 0 10px 0; color: #495057;">Metadata</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Alert ID:</strong> {alert.id}</li>
                            <li><strong>Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>Channels:</strong> {', '.join([c.value for c in alert.channels])}</li>
                        </ul>
                    </div>

                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d; font-size: 12px;">
                        This alert was generated by the Secrets Alert System
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)

            text = msg.as_string()
            server.sendmail(self.username, recipients, text)
            server.quit()

            logger.info(f"Email alert sent successfully: {alert.title}")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

class WebhookNotifier:
    """Generic webhook notification system"""

    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.session = requests.Session()

    def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook"""
        try:
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
                "channels": [c.value for c in alert.channels],
                "escalated": alert.escalated,
                "resolved": alert.resolved
            }

            response = self.session.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook alert sent successfully: {alert.title}")
                return True
            else:
                logger.warning(f"Failed to send webhook alert: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return False

class ConsoleNotifier:
    """Console notification system for debugging"""

    def send_alert(self, alert: Alert) -> bool:
        """Print alert to console"""
        try:
            severity_emoji = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.CRITICAL: "🚨",
                AlertSeverity.EMERGENCY: "🆘"
            }

            emoji = severity_emoji.get(alert.severity, "📢")

            print(f"\n{emoji} ALERT: {alert.title}")
            print(f"   Severity: {alert.severity.value.upper()}")
            print(f"   Rule: {alert.rule_name}")
            print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Message: {alert.message}")
            if alert.metadata:
                print(f"   Metadata: {alert.metadata}")
            print("-" * 50)

            return True

        except Exception as e:
            logger.error(f"Error printing console alert: {e}")
            return False

class AlertManager:
    """Main alert management system"""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        self.project = project
        self.context = context
        self.deduplicator = AlertDeduplicator()
        self.notifiers = {}
        self.alert_rules = []
        self.alert_history: deque = deque(maxlen=10000)
        self.lock = threading.Lock()

        # Load configuration
        self._load_configuration()

        # Initialize notifiers
        self._initialize_notifiers()

        # Load default alert rules
        self._load_default_rules()

    def _load_configuration(self):
        """Load alerting configuration"""
        # Load secrets using hierarchical loader
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "/Users/ryanranft/load_env_hierarchical.py",
                self.project, "NBA", self.context
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"Failed to load secrets: {result.stderr}")

        except Exception as e:
            logger.error(f"Error loading secrets: {e}")

    def _initialize_notifiers(self):
        """Initialize notification channels"""
        # Slack notifier
        slack_webhook = os.getenv(f"SLACK_WEBHOOK_URL_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if slack_webhook:
            slack_channel = os.getenv(f"SLACK_CHANNEL_{self.project.upper().replace('-', '_')}_{self.context.upper()}", "#alerts")
            self.notifiers[AlertChannel.SLACK] = SlackNotifier(slack_webhook, slack_channel)

        # Email notifier
        smtp_server = os.getenv(f"SMTP_SERVER_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if smtp_server:
            smtp_port = int(os.getenv(f"SMTP_PORT_{self.project.upper().replace('-', '_')}_{self.context.upper()}", "587"))
            smtp_username = os.getenv(f"SMTP_USERNAME_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
            smtp_password = os.getenv(f"SMTP_PASSWORD_{self.project.upper().replace('-', '_')}_{self.context.upper()}")

            if smtp_username and smtp_password:
                self.notifiers[AlertChannel.EMAIL] = EmailNotifier(smtp_server, smtp_port, smtp_username, smtp_password)

        # Webhook notifier
        webhook_url = os.getenv(f"WEBHOOK_URL_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if webhook_url:
            self.notifiers[AlertChannel.WEBHOOK] = WebhookNotifier(webhook_url)

        # Console notifier (always available)
        self.notifiers[AlertChannel.CONSOLE] = ConsoleNotifier()

    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                name="health_score_critical",
                condition="metrics.get('overall_health_score', 0) < 50",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.CONSOLE],
                throttle_minutes=5,
                description="Overall health score drops below 50%"
            ),
            AlertRule(
                name="health_score_warning",
                condition="metrics.get('overall_health_score', 0) < 70",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.CONSOLE],
                throttle_minutes=15,
                description="Overall health score drops below 70%"
            ),
            AlertRule(
                name="api_connectivity_critical",
                condition="metrics.get('api_connectivity_score', 0) < 50",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.CONSOLE],
                throttle_minutes=5,
                description="API connectivity score drops below 50%"
            ),
            AlertRule(
                name="response_time_high",
                condition="metrics.get('avg_response_time_ms', 0) > 5000",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.CONSOLE],
                throttle_minutes=30,
                description="Average response time exceeds 5 seconds"
            ),
            AlertRule(
                name="critical_secrets_count",
                condition="metrics.get('critical_secrets', 0) > 0",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.CONSOLE],
                throttle_minutes=5,
                description="One or more secrets are in critical state"
            ),
            AlertRule(
                name="monitoring_inactive",
                condition="not metrics.get('monitoring_active', False)",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK, AlertChannel.CONSOLE],
                throttle_minutes=60,
                description="Secrets monitoring is inactive"
            )
        ]

        self.alert_rules.extend(default_rules)

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        with self.lock:
            self.alert_rules.append(rule)
            logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self.lock:
            self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def evaluate_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Evaluate all alert rules against current metrics"""
        triggered_alerts = []

        with self.lock:
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue

                try:
                    # Evaluate condition
                    if eval(rule.condition, {"metrics": metrics}):
                        # Create alert
                        alert = Alert(
                            id=f"{rule.name}_{int(time.time())}",
                            rule_name=rule.name,
                            severity=rule.severity,
                            title=f"{rule.name.replace('_', ' ').title()} Alert",
                            message=rule.description,
                            metadata=metrics,
                            timestamp=datetime.now(),
                            channels=rule.channels
                        )

                        triggered_alerts.append(alert)

                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.name}: {e}")

        return triggered_alerts

    def send_alert(self, alert: Alert) -> bool:
        """Send alert through all configured channels"""
        success_count = 0
        total_channels = len(alert.channels)

        for channel in alert.channels:
            if channel in self.notifiers:
                try:
                    if self.notifiers[channel].send_alert(alert):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error sending alert via {channel.value}: {e}")
            else:
                logger.warning(f"No notifier configured for channel: {channel.value}")

        # Add to history
        with self.lock:
            self.alert_history.append(alert)

        success_rate = success_count / total_channels if total_channels > 0 else 0
        logger.info(f"Alert sent: {alert.title} ({success_count}/{total_channels} channels)")

        return success_rate > 0.5  # Consider successful if more than half channels work

    def process_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Process metrics and send alerts"""
        # Evaluate alert rules
        triggered_alerts = self.evaluate_alerts(metrics)

        sent_alerts = []

        for alert in triggered_alerts:
            # Find the rule for this alert to get throttle_minutes
            rule = next((r for r in self.alert_rules if r.name == alert.rule_name), None)
            throttle_minutes = rule.throttle_minutes if rule else 15

            # Check deduplication
            if self.deduplicator.should_send_alert(alert, throttle_minutes):
                if self.send_alert(alert):
                    sent_alerts.append(alert)

        return sent_alerts

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.lock:
            return [
                alert for alert in self.alert_history
                if alert.timestamp >= cutoff_time
            ]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self.lock:
            total_alerts = len(self.alert_history)

            if total_alerts == 0:
                return {
                    "total_alerts": 0,
                    "severity_breakdown": {},
                    "rule_breakdown": {},
                    "channel_breakdown": {},
                    "recent_trend": "no_data"
                }

            # Calculate breakdowns
            severity_counts = defaultdict(int)
            rule_counts = defaultdict(int)
            channel_counts = defaultdict(int)

            for alert in self.alert_history:
                severity_counts[alert.severity.value] += 1
                rule_counts[alert.rule_name] += 1
                for channel in alert.channels:
                    channel_counts[channel.value] += 1

            # Calculate recent trend
            recent_alerts = [
                alert for alert in self.alert_history
                if alert.timestamp >= datetime.now() - timedelta(hours=1)
            ]

            if len(recent_alerts) > 0:
                trend = "increasing" if len(recent_alerts) > total_alerts / 24 else "stable"
            else:
                trend = "decreasing"

            return {
                "total_alerts": total_alerts,
                "severity_breakdown": dict(severity_counts),
                "rule_breakdown": dict(rule_counts),
                "channel_breakdown": dict(channel_counts),
                "recent_trend": trend,
                "recent_alerts_count": len(recent_alerts)
            }

def main():
    """Main entry point for alerting system"""
    import argparse

    parser = argparse.ArgumentParser(description="Secrets Alerting System")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument("--context", default="production", help="Context (production/development/test)")
    parser.add_argument("--test", action="store_true", help="Send test alert")
    parser.add_argument("--stats", action="store_true", help="Show alert statistics")
    parser.add_argument("--history", type=int, help="Show alert history (hours)")

    args = parser.parse_args()

    # Create alert manager
    alert_manager = AlertManager(args.project, args.context)

    if args.test:
        # Send test alert
        test_alert = Alert(
            id=f"test_{int(time.time())}",
            rule_name="test_alert",
            severity=AlertSeverity.INFO,
            title="Test Alert",
            message="This is a test alert from the Secrets Alerting System",
            metadata={"test": True},
            timestamp=datetime.now(),
            channels=[AlertChannel.CONSOLE, AlertChannel.SLACK]
        )

        print("🧪 Sending test alert...")
        success = alert_manager.send_alert(test_alert)
        print(f"✅ Test alert sent: {success}")

    elif args.stats:
        # Show statistics
        stats = alert_manager.get_alert_statistics()
        print("\n📊 ALERT STATISTICS")
        print("=" * 50)
        print(f"Total Alerts: {stats['total_alerts']}")
        print(f"Recent Trend: {stats['recent_trend']}")
        print(f"Recent Alerts (1h): {stats['recent_alerts_count']}")

        print(f"\nSeverity Breakdown:")
        for severity, count in stats['severity_breakdown'].items():
            print(f"  {severity}: {count}")

        print(f"\nRule Breakdown:")
        for rule, count in stats['rule_breakdown'].items():
            print(f"  {rule}: {count}")

        print(f"\nChannel Breakdown:")
        for channel, count in stats['channel_breakdown'].items():
            print(f"  {channel}: {count}")

    elif args.history:
        # Show history
        history = alert_manager.get_alert_history(args.history)
        print(f"\n📜 ALERT HISTORY (Last {args.history} hours)")
        print("=" * 50)

        if not history:
            print("No alerts in the specified time period")
        else:
            for alert in history[-10:]:  # Show last 10
                severity_emoji = {
                    AlertSeverity.INFO: "ℹ️",
                    AlertSeverity.WARNING: "⚠️",
                    AlertSeverity.CRITICAL: "🚨",
                    AlertSeverity.EMERGENCY: "🆘"
                }

                emoji = severity_emoji.get(alert.severity, "📢")
                print(f"{emoji} {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {alert.title}")
                print(f"   Rule: {alert.rule_name} | Channels: {', '.join([c.value for c in alert.channels])}")

    else:
        print("Secrets Alerting System initialized")
        print("Use --test to send a test alert")
        print("Use --stats to show alert statistics")
        print("Use --history <hours> to show alert history")

if __name__ == "__main__":
    main()
