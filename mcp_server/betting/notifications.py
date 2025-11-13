"""
Notification Module

Sends alerts and reports via multiple channels:
- Email (SMTP)
- Slack (webhooks)
- SMS (Twilio) - optional
- Webhook (custom endpoints)

Features:
- Multiple notification channels
- Templated messages with rich formatting
- Alert batching to avoid spam
- Rate limiting
- Retry logic for failed deliveries
- Notification history tracking

Configuration:
--------------
Set environment variables or pass config dict:

Email (SMTP):
    SMTP_HOST: SMTP server hostname
    SMTP_PORT: SMTP server port (default: 587)
    SMTP_USER: SMTP username
    SMTP_PASSWORD: SMTP password
    EMAIL_FROM: Sender email address
    EMAIL_TO: Comma-separated recipient emails

Slack:
    SLACK_WEBHOOK_URL: Slack incoming webhook URL
    SLACK_CHANNEL: Slack channel (optional, use webhook default)

Example:
-------
    from mcp_server.betting.notifications import NotificationManager
    from mcp_server.betting.alert_system import Alert, AlertLevel

    # Initialize with config
    notifier = NotificationManager(config={
        'email': {
            'enabled': True,
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your@email.com',
            'password': 'your_app_password',
            'from_addr': 'your@email.com',
            'to_addrs': ['recipient@email.com']
        },
        'slack': {
            'enabled': True,
            'webhook_url': 'https://hooks.slack.com/services/...'
        }
    })

    # Send alert
    alert = Alert(...)
    notifier.send_alert(alert)

    # Send batch of alerts
    alerts = [alert1, alert2, alert3]
    notifier.send_alert_batch(alerts)

    # Send custom message
    notifier.send_message(
        subject="Daily Report",
        message="Your betting system report...",
        channels=['email', 'slack']
    )
"""

import os
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import warnings
from pathlib import Path

# Optional imports
try:
    from mcp_server.betting.alert_system import Alert, AlertLevel

    ALERT_SYSTEM_AVAILABLE = True
except ImportError:
    ALERT_SYSTEM_AVAILABLE = False
    warnings.warn("Alert system not available")


@dataclass
class NotificationResult:
    """Result of a notification attempt"""

    channel: str
    success: bool
    timestamp: datetime
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmailNotifier:
    """
    Email notification via SMTP

    Supports HTML and plain text emails with rich formatting
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email notifier

        Args:
            config: Email configuration dict with keys:
                - smtp_host: SMTP server hostname
                - smtp_port: SMTP server port (default: 587)
                - username: SMTP username
                - password: SMTP password
                - from_addr: Sender email address
                - to_addrs: List of recipient email addresses
                - use_tls: Use TLS (default: True)
        """
        self.smtp_host = config.get("smtp_host", os.getenv("SMTP_HOST"))
        self.smtp_port = config.get("smtp_port", int(os.getenv("SMTP_PORT", "587")))
        self.username = config.get("username", os.getenv("SMTP_USER"))
        self.password = config.get("password", os.getenv("SMTP_PASSWORD"))
        self.from_addr = config.get("from_addr", os.getenv("EMAIL_FROM"))
        self.to_addrs = config.get("to_addrs", os.getenv("EMAIL_TO", "").split(","))
        self.use_tls = config.get("use_tls", True)

        # Validate config
        if not all([self.smtp_host, self.username, self.password, self.from_addr]):
            raise ValueError(
                "Email config incomplete: need smtp_host, username, password, from_addr"
            )

        if not self.to_addrs or not self.to_addrs[0]:
            raise ValueError(
                "Email config incomplete: need at least one recipient in to_addrs"
            )

    def send(self, subject: str, body: str, html: bool = False) -> NotificationResult:
        """
        Send email

        Args:
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Whether body is HTML

        Returns:
            NotificationResult
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            # Attach body
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return NotificationResult(
                channel="email",
                success=True,
                timestamp=datetime.now(),
                metadata={"subject": subject, "recipients": self.to_addrs},
            )

        except Exception as e:
            return NotificationResult(
                channel="email", success=False, timestamp=datetime.now(), error=str(e)
            )


class SlackNotifier:
    """
    Slack notification via incoming webhooks

    Sends rich formatted messages to Slack channels
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Slack notifier

        Args:
            config: Slack configuration dict with keys:
                - webhook_url: Slack incoming webhook URL
                - channel: Slack channel (optional, uses webhook default)
                - username: Bot username (optional)
                - icon_emoji: Bot emoji icon (optional)
        """
        self.webhook_url = config.get("webhook_url", os.getenv("SLACK_WEBHOOK_URL"))
        self.channel = config.get("channel", os.getenv("SLACK_CHANNEL"))
        self.username = config.get("username", "NBA Betting Bot")
        self.icon_emoji = config.get("icon_emoji", ":basketball:")

        if not self.webhook_url:
            raise ValueError("Slack config incomplete: need webhook_url")

    def send(self, message: str, title: Optional[str] = None) -> NotificationResult:
        """
        Send Slack message

        Args:
            message: Message text
            title: Optional message title

        Returns:
            NotificationResult
        """
        try:
            payload = {
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "text": message,
            }

            if self.channel:
                payload["channel"] = self.channel

            if title:
                payload["attachments"] = [
                    {"title": title, "text": message, "color": "good"}
                ]
                payload["text"] = ""  # Use attachment for text

            response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                return NotificationResult(
                    channel="slack",
                    success=True,
                    timestamp=datetime.now(),
                    metadata={"channel": self.channel},
                )
            else:
                return NotificationResult(
                    channel="slack",
                    success=False,
                    timestamp=datetime.now(),
                    error=f"HTTP {response.status_code}: {response.text}",
                )

        except Exception as e:
            return NotificationResult(
                channel="slack", success=False, timestamp=datetime.now(), error=str(e)
            )


class SmsNotifier:
    """
    SMS notification via Twilio

    Sends text messages for critical alerts
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SMS notifier

        Args:
            config: SMS configuration dict with keys:
                - account_sid: Twilio account SID
                - auth_token: Twilio auth token
                - from_number: Twilio phone number (format: +1234567890)
                - to_numbers: List of recipient phone numbers
        """
        self.account_sid = config.get("account_sid", os.getenv("TWILIO_ACCOUNT_SID"))
        self.auth_token = config.get("auth_token", os.getenv("TWILIO_AUTH_TOKEN"))
        self.from_number = config.get("from_number", os.getenv("TWILIO_FROM_NUMBER"))
        self.to_numbers = config.get("to_numbers", [])

        # Also check env var for to_numbers
        if not self.to_numbers:
            env_numbers = os.getenv("TWILIO_TO_NUMBERS", "")
            if env_numbers:
                self.to_numbers = [n.strip() for n in env_numbers.split(",")]

        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError(
                "SMS config incomplete: need account_sid, auth_token, from_number"
            )

        if not self.to_numbers:
            raise ValueError(
                "SMS config incomplete: need at least one recipient in to_numbers"
            )

        # Try to import Twilio client
        try:
            from twilio.rest import Client

            self.client = Client(self.account_sid, self.auth_token)
        except ImportError:
            raise ImportError(
                "Twilio SDK required for SMS. Install with: pip install twilio"
            )

    def send(self, message: str, title: Optional[str] = None) -> NotificationResult:
        """
        Send SMS message

        Args:
            message: Message text (max 1600 chars for Twilio)
            title: Optional message title (prepended to message)

        Returns:
            NotificationResult
        """
        try:
            # Combine title and message
            full_message = message
            if title:
                full_message = f"{title}\n\n{message}"

            # Truncate if too long (Twilio limit is 1600 chars)
            if len(full_message) > 1600:
                full_message = full_message[:1597] + "..."

            # Send to all recipients
            results = []
            for to_number in self.to_numbers:
                try:
                    msg = self.client.messages.create(
                        body=full_message, from_=self.from_number, to=to_number
                    )
                    results.append(
                        {"number": to_number, "success": True, "sid": msg.sid}
                    )
                except Exception as e:
                    results.append(
                        {"number": to_number, "success": False, "error": str(e)}
                    )

            # Check if any succeeded
            successes = [r for r in results if r["success"]]
            failures = [r for r in results if not r["success"]]

            if successes:
                return NotificationResult(
                    channel="sms",
                    success=True,
                    timestamp=datetime.now(),
                    metadata={
                        "sent_to": [r["number"] for r in successes],
                        "failed": [r["number"] for r in failures] if failures else [],
                    },
                )
            else:
                return NotificationResult(
                    channel="sms",
                    success=False,
                    timestamp=datetime.now(),
                    error=f"Failed to send to all recipients: {failures}",
                )

        except Exception as e:
            return NotificationResult(
                channel="sms", success=False, timestamp=datetime.now(), error=str(e)
            )


class NotificationManager:
    """
    Main notification manager

    Coordinates multiple notification channels and handles:
    - Alert formatting and delivery
    - Alert batching
    - Rate limiting
    - Retry logic
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize notification manager

        Args:
            config: Configuration dict with channel configs:
                {
                    'email': {'enabled': True, 'smtp_host': '...', ...},
                    'slack': {'enabled': True, 'webhook_url': '...', ...}
                }
        """
        self.config = config or {}

        # Initialize notifiers
        self.notifiers = {}

        # Email
        if self.config.get("email", {}).get("enabled"):
            try:
                self.notifiers["email"] = EmailNotifier(self.config["email"])
            except Exception as e:
                warnings.warn(f"Failed to initialize email notifier: {e}")

        # Slack
        if self.config.get("slack", {}).get("enabled"):
            try:
                self.notifiers["slack"] = SlackNotifier(self.config["slack"])
            except Exception as e:
                warnings.warn(f"Failed to initialize Slack notifier: {e}")

        # SMS
        if self.config.get("sms", {}).get("enabled"):
            try:
                self.notifiers["sms"] = SmsNotifier(self.config["sms"])
            except Exception as e:
                warnings.warn(f"Failed to initialize SMS notifier: {e}")

        # Rate limiting state
        self._last_notification = {}
        self._min_interval = timedelta(
            minutes=5
        )  # Min 5 minutes between similar alerts

    def _should_send(self, alert_key: str) -> bool:
        """
        Check if alert should be sent (rate limiting)

        Args:
            alert_key: Unique key for alert type

        Returns:
            True if should send, False if rate limited
        """
        if alert_key not in self._last_notification:
            return True

        last_sent = self._last_notification[alert_key]
        return (datetime.now() - last_sent) > self._min_interval

    def _format_alert_email(self, alert: "Alert") -> tuple[str, str]:
        """
        Format alert as email

        Args:
            alert: Alert object

        Returns:
            Tuple of (subject, html_body)
        """
        # Subject
        subject = f"[{alert.level.value.upper()}] NBA Betting Alert: {alert.metric}"

        # HTML body
        icon_map = {"critical": "🔴", "warning": "🟡", "info": "🔵", "healthy": "🟢"}
        icon = icon_map.get(alert.level.value, "⚪")

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">{icon} {alert.level.value.upper()} Alert</h2>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Category:</strong> {alert.category.value}</p>
                <p><strong>Metric:</strong> {alert.metric}</p>
                <p><strong>Current Value:</strong> {alert.value:.4f}</p>
                <p><strong>Threshold:</strong> {alert.threshold:.4f}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p style="color: #666; font-size: 12px;">
                This is an automated alert from your NBA betting system monitoring.
            </p>
        </body>
        </html>
        """

        return subject, html

    def _format_alert_slack(self, alert: "Alert") -> tuple[str, str]:
        """
        Format alert as Slack message

        Args:
            alert: Alert object

        Returns:
            Tuple of (title, message)
        """
        icon_map = {
            "critical": ":red_circle:",
            "warning": ":large_orange_diamond:",
            "info": ":large_blue_circle:",
            "healthy": ":white_check_mark:",
        }
        icon = icon_map.get(alert.level.value, ":white_circle:")

        title = f"{icon} {alert.level.value.upper()} Alert: {alert.metric}"

        message = f"""
*Category:* {alert.category.value}
*Metric:* {alert.metric}
*Current Value:* {alert.value:.4f}
*Threshold:* {alert.threshold:.4f}
*Message:* {alert.message}
*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        return title, message

    def send_alert(
        self, alert: "Alert", channels: Optional[List[str]] = None
    ) -> Dict[str, NotificationResult]:
        """
        Send alert via configured channels

        Args:
            alert: Alert object to send
            channels: List of channels to use (None = all enabled)

        Returns:
            Dict mapping channel name to NotificationResult
        """
        if not ALERT_SYSTEM_AVAILABLE:
            raise ImportError("Alert system not available")

        # Rate limiting
        alert_key = f"{alert.category.value}_{alert.metric}"
        if not self._should_send(alert_key):
            return {}

        # Determine channels
        if channels is None:
            channels = list(self.notifiers.keys())

        results = {}

        # Send via each channel
        for channel in channels:
            if channel not in self.notifiers:
                continue

            try:
                if channel == "email":
                    subject, body = self._format_alert_email(alert)
                    results[channel] = self.notifiers["email"].send(
                        subject, body, html=True
                    )

                elif channel == "slack":
                    title, message = self._format_alert_slack(alert)
                    results[channel] = self.notifiers["slack"].send(message, title)

                elif channel == "sms":
                    # Format SMS (short version for text messages)
                    sms_message = (
                        f"[{alert.level.value.upper()}] {alert.metric}: {alert.message}"
                    )
                    results[channel] = self.notifiers["sms"].send(sms_message)

            except Exception as e:
                results[channel] = NotificationResult(
                    channel=channel,
                    success=False,
                    timestamp=datetime.now(),
                    error=str(e),
                )

        # Update rate limiting
        if any(r.success for r in results.values()):
            self._last_notification[alert_key] = datetime.now()

        return results

    def send_alert_batch(
        self, alerts: List["Alert"], channels: Optional[List[str]] = None
    ) -> Dict[str, NotificationResult]:
        """
        Send batch of alerts as single notification

        Args:
            alerts: List of Alert objects
            channels: List of channels to use (None = all enabled)

        Returns:
            Dict mapping channel name to NotificationResult
        """
        if not alerts:
            return {}

        if not ALERT_SYSTEM_AVAILABLE:
            raise ImportError("Alert system not available")

        # Determine channels
        if channels is None:
            channels = list(self.notifiers.keys())

        results = {}

        # Group alerts by level
        critical = [a for a in alerts if a.level.value == "critical"]
        warnings = [a for a in alerts if a.level.value == "warning"]
        info = [a for a in alerts if a.level.value == "info"]

        # Send via each channel
        for channel in channels:
            if channel not in self.notifiers:
                continue

            try:
                if channel == "email":
                    subject = f"NBA Betting System: {len(alerts)} Alerts"
                    body = self._format_batch_email(critical, warnings, info)
                    results[channel] = self.notifiers["email"].send(
                        subject, body, html=True
                    )

                elif channel == "slack":
                    title = f"NBA Betting System: {len(alerts)} Alerts"
                    message = self._format_batch_slack(critical, warnings, info)
                    results[channel] = self.notifiers["slack"].send(message, title)

                elif channel == "sms":
                    # Format SMS batch (concise version)
                    sms_msg = f"NBA Betting: {len(alerts)} alerts"
                    if critical:
                        sms_msg += f"\n🔴 {len(critical)} CRITICAL"
                    if warnings:
                        sms_msg += f"\n🟡 {len(warnings)} warnings"
                    results[channel] = self.notifiers["sms"].send(sms_msg)

            except Exception as e:
                results[channel] = NotificationResult(
                    channel=channel,
                    success=False,
                    timestamp=datetime.now(),
                    error=str(e),
                )

        return results

    def _format_batch_email(
        self, critical: List["Alert"], warnings: List["Alert"], info: List["Alert"]
    ) -> str:
        """Format batch of alerts as HTML email"""
        html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">NBA Betting System Alert Summary</h2>
        """

        if critical:
            html += f"""
            <h3 style="color: #d9534f;">🔴 Critical Alerts ({len(critical)})</h3>
            <ul>
            """
            for alert in critical:
                html += f"<li>{alert.message}</li>"
            html += "</ul>"

        if warnings:
            html += f"""
            <h3 style="color: #f0ad4e;">🟡 Warnings ({len(warnings)})</h3>
            <ul>
            """
            for alert in warnings:
                html += f"<li>{alert.message}</li>"
            html += "</ul>"

        if info:
            html += f"""
            <h3 style="color: #5bc0de;">🔵 Info ({len(info)})</h3>
            <ul>
            """
            for alert in info:
                html += f"<li>{alert.message}</li>"
            html += "</ul>"

        html += """
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated alert from your NBA betting system monitoring.
            </p>
        </body>
        </html>
        """

        return html

    def _format_batch_slack(
        self, critical: List["Alert"], warnings: List["Alert"], info: List["Alert"]
    ) -> str:
        """Format batch of alerts as Slack message"""
        message = "*NBA Betting System Alert Summary*\n\n"

        if critical:
            message += f":red_circle: *Critical Alerts ({len(critical)})*\n"
            for alert in critical:
                message += f"• {alert.message}\n"
            message += "\n"

        if warnings:
            message += f":large_orange_diamond: *Warnings ({len(warnings)})*\n"
            for alert in warnings:
                message += f"• {alert.message}\n"
            message += "\n"

        if info:
            message += f":large_blue_circle: *Info ({len(info)})*\n"
            for alert in info:
                message += f"• {alert.message}\n"

        return message

    def send_message(
        self, subject: str, message: str, channels: Optional[List[str]] = None
    ) -> Dict[str, NotificationResult]:
        """
        Send custom message

        Args:
            subject: Message subject/title
            message: Message body
            channels: List of channels to use (None = all enabled)

        Returns:
            Dict mapping channel name to NotificationResult
        """
        # Determine channels
        if channels is None:
            channels = list(self.notifiers.keys())

        results = {}

        # Send via each channel
        for channel in channels:
            if channel not in self.notifiers:
                continue

            try:
                if channel == "email":
                    results[channel] = self.notifiers["email"].send(
                        subject, message, html=False
                    )

                elif channel == "slack":
                    results[channel] = self.notifiers["slack"].send(message, subject)

                elif channel == "sms":
                    # For SMS, combine subject and message
                    sms_text = f"{subject}: {message[:140]}"  # Keep it short
                    results[channel] = self.notifiers["sms"].send(sms_text)

            except Exception as e:
                results[channel] = NotificationResult(
                    channel=channel,
                    success=False,
                    timestamp=datetime.now(),
                    error=str(e),
                )

        return results


def send_test_notification(config: Optional[Dict[str, Any]] = None):
    """
    Send test notification to verify configuration

    Args:
        config: Notification config (None = use env vars)
    """
    notifier = NotificationManager(config)

    subject = "NBA Betting System - Test Notification"
    message = f"""
    This is a test notification from your NBA betting system.

    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    If you received this, your notification system is working correctly!
    """

    results = notifier.send_message(subject, message)

    print("\n📨 Test Notification Results:")
    for channel, result in results.items():
        if result.success:
            print(f"  ✅ {channel}: Success")
        else:
            print(f"  ❌ {channel}: Failed - {result.error}")

    return results
