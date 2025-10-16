#!/usr/bin/env python3
"""
Secrets Health Monitor

Comprehensive health monitoring, metrics collection, and alerting system for secrets management.
Provides real-time monitoring of secret health, API connectivity, and automated Slack notifications.

Features:
- Real-time secret validation and health checks
- API connectivity monitoring with timeout handling
- Metrics collection and performance tracking
- Automated Slack notifications for alerts and status updates
- Historical health data and trend analysis
- Configurable alert thresholds and notification channels
- Integration with unified secrets manager
"""

import os
import sys
import time
import json
import logging
import hashlib
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict, deque
import signal
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/secrets_health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    service: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SecretValidationResult:
    """Result of secret validation"""
    secret_name: str
    is_valid: bool
    validation_type: str  # 'format', 'connectivity', 'strength'
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class MetricsSnapshot:
    """Snapshot of current metrics"""
    timestamp: datetime
    total_secrets: int
    healthy_secrets: int
    warning_secrets: int
    critical_secrets: int
    avg_response_time_ms: float
    api_connectivity_score: float
    overall_health_score: float
    uptime_seconds: float

class SecretsValidator:
    """Enhanced secrets validation with comprehensive checks"""

    @staticmethod
    def validate_api_key_format(api_key: str, service: str) -> Tuple[bool, str]:
        """Validate API key format for various services"""
        if not api_key or len(api_key.strip()) == 0:
            return False, "API key is empty"

        api_key = api_key.strip()

        # Service-specific validation patterns
        patterns = {
            'google': r'^AIza[0-9A-Za-z-_]{35}$',
            'openai': r'^sk-[A-Za-z0-9]{48}$',
            'anthropic': r'^sk-ant-api[0-9]{2}-[A-Za-z0-9-_]{100,}$',
            'deepseek': r'^sk-[a-f0-9]{32}$',
            'linear': r'^lin_api_[A-Za-z0-9]{32}$'
        }

        if service.lower() in patterns:
            import re
            if not re.match(patterns[service.lower()], api_key):
                return False, f"Invalid {service} API key format"

        # General strength checks
        if len(api_key) < 20:
            return False, "API key too short (minimum 20 characters)"

        if len(api_key) > 200:
            return False, "API key too long (maximum 200 characters)"

        return True, "Valid format"

    @staticmethod
    def validate_webhook_url(url: str) -> Tuple[bool, str]:
        """Validate webhook URL format"""
        if not url or len(url.strip()) == 0:
            return False, "Webhook URL is empty"

        url = url.strip()

        if not url.startswith(('http://', 'https://')):
            return False, "Webhook URL must start with http:// or https://"

        if 'hooks.slack.com' not in url and 'webhook' not in url.lower():
            return False, "Webhook URL should contain 'hooks.slack.com' or 'webhook'"

        return True, "Valid webhook URL"

    @staticmethod
    def validate_uuid(uuid_str: str) -> Tuple[bool, str]:
        """Validate UUID format"""
        if not uuid_str or len(uuid_str.strip()) == 0:
            return False, "UUID is empty"

        uuid_str = uuid_str.strip()

        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

        if not re.match(uuid_pattern, uuid_str, re.IGNORECASE):
            return False, "Invalid UUID format"

        return True, "Valid UUID"

class APIConnectivityChecker:
    """Enhanced API connectivity checker with comprehensive monitoring"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SecretsHealthMonitor/1.0'
        })

    def check_google_api(self, api_key: str) -> HealthCheckResult:
        """Check Google API connectivity"""
        start_time = time.time()

        try:
            # Test with a simple API call
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = self.session.get(url, timeout=self.timeout)

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    service="Google API",
                    status="healthy",
                    response_time_ms=response_time,
                    metadata={"status_code": response.status_code}
                )
            elif response.status_code == 403:
                return HealthCheckResult(
                    service="Google API",
                    status="critical",
                    response_time_ms=response_time,
                    error_message="API key invalid or quota exceeded",
                    metadata={"status_code": response.status_code}
                )
            else:
                return HealthCheckResult(
                    service="Google API",
                    status="warning",
                    response_time_ms=response_time,
                    error_message=f"Unexpected status code: {response.status_code}",
                    metadata={"status_code": response.status_code}
                )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service="Google API",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message="Request timeout"
            )
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                service="Google API",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"Request failed: {str(e)}"
            )

    def check_openai_api(self, api_key: str) -> HealthCheckResult:
        """Check OpenAI API connectivity"""
        start_time = time.time()

        try:
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = self.session.get(url, headers=headers, timeout=self.timeout)

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    service="OpenAI API",
                    status="healthy",
                    response_time_ms=response_time,
                    metadata={"status_code": response.status_code}
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="OpenAI API",
                    status="critical",
                    response_time_ms=response_time,
                    error_message="API key invalid",
                    metadata={"status_code": response.status_code}
                )
            else:
                return HealthCheckResult(
                    service="OpenAI API",
                    status="warning",
                    response_time_ms=response_time,
                    error_message=f"Unexpected status code: {response.status_code}",
                    metadata={"status_code": response.status_code}
                )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service="OpenAI API",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message="Request timeout"
            )
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                service="OpenAI API",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"Request failed: {str(e)}"
            )

    def check_slack_webhook(self, webhook_url: str) -> HealthCheckResult:
        """Check Slack webhook connectivity"""
        start_time = time.time()

        try:
            # Send a test message
            test_payload = {
                "text": "🔍 Secrets Health Monitor - Test Message",
                "username": "Secrets Monitor",
                "icon_emoji": ":shield:"
            }

            response = self.session.post(webhook_url, json=test_payload, timeout=self.timeout)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    service="Slack Webhook",
                    status="healthy",
                    response_time_ms=response_time,
                    metadata={"status_code": response.status_code}
                )
            else:
                return HealthCheckResult(
                    service="Slack Webhook",
                    status="warning",
                    response_time_ms=response_time,
                    error_message=f"Unexpected status code: {response.status_code}",
                    metadata={"status_code": response.status_code}
                )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service="Slack Webhook",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message="Request timeout"
            )
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                service="Slack Webhook",
                status="critical",
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"Request failed: {str(e)}"
            )

class MetricsCollector:
    """Collects and analyzes metrics from health checks"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.health_history: deque = deque(maxlen=max_history)
        self.secret_history: deque = deque(maxlen=max_history)
        self.start_time = datetime.now()
        self.lock = threading.Lock()

    def add_health_check(self, result: HealthCheckResult):
        """Add a health check result to history"""
        with self.lock:
            self.health_history.append(result)

    def add_secret_validation(self, result: SecretValidationResult):
        """Add a secret validation result to history"""
        with self.lock:
            self.secret_history.append(result)

    def get_current_snapshot(self) -> MetricsSnapshot:
        """Get current metrics snapshot"""
        with self.lock:
            now = datetime.now()
            uptime = (now - self.start_time).total_seconds()

            # Calculate health metrics
            total_checks = len(self.health_history)
            if total_checks == 0:
                return MetricsSnapshot(
                    timestamp=now,
                    total_secrets=0,
                    healthy_secrets=0,
                    warning_secrets=0,
                    critical_secrets=0,
                    avg_response_time_ms=0.0,
                    api_connectivity_score=0.0,
                    overall_health_score=0.0,
                    uptime_seconds=uptime
                )

            # Count statuses
            status_counts = defaultdict(int)
            response_times = []

            for check in self.health_history:
                status_counts[check.status] += 1
                response_times.append(check.response_time_ms)

            # Calculate scores
            healthy_count = status_counts.get('healthy', 0)
            warning_count = status_counts.get('warning', 0)
            critical_count = status_counts.get('critical', 0)

            api_connectivity_score = (healthy_count / total_checks) * 100 if total_checks > 0 else 0
            overall_health_score = ((healthy_count + warning_count * 0.5) / total_checks) * 100 if total_checks > 0 else 0

            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

            return MetricsSnapshot(
                timestamp=now,
                total_secrets=total_checks,
                healthy_secrets=healthy_count,
                warning_secrets=warning_count,
                critical_secrets=critical_count,
                avg_response_time_ms=avg_response_time,
                api_connectivity_score=api_connectivity_score,
                overall_health_score=overall_health_score,
                uptime_seconds=uptime
            )

    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified hours"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_checks = [check for check in self.health_history if check.timestamp >= cutoff_time]

            if not recent_checks:
                return {"trend": "no_data", "message": "No recent health checks"}

            # Calculate trend
            status_counts = defaultdict(int)
            for check in recent_checks:
                status_counts[check.status] += 1

            total_recent = len(recent_checks)
            healthy_ratio = status_counts.get('healthy', 0) / total_recent

            if healthy_ratio >= 0.9:
                trend = "excellent"
            elif healthy_ratio >= 0.7:
                trend = "good"
            elif healthy_ratio >= 0.5:
                trend = "fair"
            else:
                trend = "poor"

            return {
                "trend": trend,
                "healthy_ratio": healthy_ratio,
                "total_checks": total_recent,
                "status_breakdown": dict(status_counts)
            }

class SlackNotifier:
    """Enhanced Slack notification system with rich formatting"""

    def __init__(self, webhook_url: str, channel: str = "#nba-simulator-notifications"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.session = requests.Session()

    def send_health_alert(self, metrics: MetricsSnapshot, critical_issues: List[str] = None):
        """Send health alert to Slack"""
        if not critical_issues:
            critical_issues = []

        # Determine alert level and emoji
        if metrics.overall_health_score >= 90:
            alert_level = "🟢 HEALTHY"
            color = "good"
        elif metrics.overall_health_score >= 70:
            alert_level = "🟡 WARNING"
            color = "warning"
        else:
            alert_level = "🔴 CRITICAL"
            color = "danger"

        # Create rich message
        message = {
            "channel": self.channel,
            "username": "Secrets Health Monitor",
            "icon_emoji": ":shield:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{alert_level} - Secrets Health Report",
                    "fields": [
                        {
                            "title": "Overall Health Score",
                            "value": f"{metrics.overall_health_score:.1f}%",
                            "short": True
                        },
                        {
                            "title": "API Connectivity",
                            "value": f"{metrics.api_connectivity_score:.1f}%",
                            "short": True
                        },
                        {
                            "title": "Healthy Secrets",
                            "value": f"{metrics.healthy_secrets}/{metrics.total_secrets}",
                            "short": True
                        },
                        {
                            "title": "Avg Response Time",
                            "value": f"{metrics.avg_response_time_ms:.1f}ms",
                            "short": True
                        },
                        {
                            "title": "Uptime",
                            "value": f"{metrics.uptime_seconds/3600:.1f} hours",
                            "short": True
                        },
                        {
                            "title": "Last Check",
                            "value": metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        }
                    ],
                    "footer": "Secrets Health Monitor",
                    "ts": int(metrics.timestamp.timestamp())
                }
            ]
        }

        # Add critical issues if any
        if critical_issues:
            message["attachments"][0]["fields"].append({
                "title": "Critical Issues",
                "value": "\n".join([f"• {issue}" for issue in critical_issues]),
                "short": False
            })

        try:
            response = self.session.post(self.webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info("Health alert sent to Slack successfully")
            else:
                logger.warning(f"Failed to send Slack alert: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    def send_secret_validation_alert(self, validation_results: List[SecretValidationResult]):
        """Send secret validation alert to Slack"""
        failed_validations = [r for r in validation_results if not r.is_valid]

        if not failed_validations:
            return  # No failures to report

        message = {
            "channel": self.channel,
            "username": "Secrets Health Monitor",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": "danger",
                    "title": f"🔴 Secret Validation Failures ({len(failed_validations)} issues)",
                    "fields": [
                        {
                            "title": "Failed Validations",
                            "value": "\n".join([
                                f"• {r.secret_name}: {r.error_message or 'Unknown error'}"
                                for r in failed_validations[:10]  # Limit to 10 for readability
                            ]),
                            "short": False
                        }
                    ],
                    "footer": "Secrets Health Monitor",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        try:
            response = self.session.post(self.webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info("Secret validation alert sent to Slack successfully")
            else:
                logger.warning(f"Failed to send Slack validation alert: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack validation alert: {e}")

class SecretsHealthMonitor:
    """Main secrets health monitoring system"""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "WORKFLOW"):
        self.project = project
        self.context = context
        self.metrics_collector = MetricsCollector()
        self.api_checker = APIConnectivityChecker()
        self.validator = SecretsValidator()
        self.slack_notifier = None
        self.monitoring_active = False
        self.monitor_thread = None

        # Load secrets using hierarchical loader
        self._load_secrets()

        # Setup Slack notifier if webhook is available
        slack_webhook = os.getenv(f"SLACK_WEBHOOK_URL_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if slack_webhook:
            slack_channel = os.getenv(f"SLACK_CHANNEL_{self.project.upper().replace('-', '_')}_{self.context.upper()}", "#nba-simulator-notifications")
            self.slack_notifier = SlackNotifier(slack_webhook, slack_channel)

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup)

    def _load_secrets(self):
        """Load secrets using unified secrets manager directly"""
        try:
            # Import and use the standalone function that sets environment variables
            try:
                from mcp_server.unified_secrets_manager import load_secrets_hierarchical
            except ImportError:
                # Fallback: try to load from the project directory
                sys.path.insert(0, '/Users/ryanranft/nba-mcp-synthesis')
                from mcp_server.unified_secrets_manager import load_secrets_hierarchical

            # Load secrets and set environment variables
            success = load_secrets_hierarchical(self.project, "NBA", self.context)

            if success:
                logger.info("Secrets loaded successfully using UnifiedSecretsManager")
                return True
            else:
                logger.error("Failed to load secrets using UnifiedSecretsManager")
                return False

        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            return False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_monitoring()
        sys.exit(0)

    def _cleanup(self):
        """Cleanup resources on exit"""
        if self.monitoring_active:
            self.stop_monitoring()

    def validate_all_secrets(self) -> List[SecretValidationResult]:
        """Validate all loaded secrets"""
        results = []

        # Get all environment variables that look like secrets
        secret_patterns = [
            'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
            'DEEPSEEK_API_KEY', 'LINEAR_API_KEY', 'SLACK_WEBHOOK_URL'
        ]

        for pattern in secret_patterns:
            env_var_name = f"{pattern}_{self.project.upper().replace('-', '_')}_{self.context.upper()}"
            secret_value = os.getenv(env_var_name)

            if secret_value:
                # Format validation
                if 'API_KEY' in pattern:
                    service = pattern.replace('_API_KEY', '').lower()
                    is_valid, error_msg = self.validator.validate_api_key_format(secret_value, service)
                    results.append(SecretValidationResult(
                        secret_name=env_var_name,
                        is_valid=is_valid,
                        validation_type="format",
                        error_message=error_msg if not is_valid else None
                    ))
                elif 'WEBHOOK_URL' in pattern:
                    is_valid, error_msg = self.validator.validate_webhook_url(secret_value)
                    results.append(SecretValidationResult(
                        secret_name=env_var_name,
                        is_valid=is_valid,
                        validation_type="format",
                        error_message=error_msg if not is_valid else None
                    ))

        return results

    def perform_health_checks(self) -> List[HealthCheckResult]:
        """Perform comprehensive health checks"""
        results = []

        # Check Google API
        google_api_key = os.getenv(f"GOOGLE_API_KEY_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if google_api_key:
            result = self.api_checker.check_google_api(google_api_key)
            results.append(result)
            self.metrics_collector.add_health_check(result)

        # Check OpenAI API
        openai_api_key = os.getenv(f"OPENAI_API_KEY_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if openai_api_key:
            result = self.api_checker.check_openai_api(openai_api_key)
            results.append(result)
            self.metrics_collector.add_health_check(result)

        # Check Slack webhook
        slack_webhook = os.getenv(f"SLACK_WEBHOOK_URL_{self.project.upper().replace('-', '_')}_{self.context.upper()}")
        if slack_webhook:
            result = self.api_checker.check_slack_webhook(slack_webhook)
            results.append(result)
            self.metrics_collector.add_health_check(result)

        return results

    def start_monitoring(self, interval_seconds: int = 300):
        """Start continuous monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started secrets health monitoring (interval: {interval_seconds}s)")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped secrets health monitoring")

    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform health checks
                health_results = self.perform_health_checks()

                # Validate secrets
                validation_results = self.validate_all_secrets()
                for result in validation_results:
                    self.metrics_collector.add_secret_validation(result)

                # Get current metrics
                metrics = self.metrics_collector.get_current_snapshot()

                # Send alerts if needed
                if self.slack_notifier:
                    critical_issues = []

                    # Check for critical health issues
                    for result in health_results:
                        if result.status == 'critical':
                            critical_issues.append(f"{result.service}: {result.error_message}")

                    # Check for validation failures
                    failed_validations = [r for r in validation_results if not r.is_valid]
                    for validation in failed_validations:
                        critical_issues.append(f"Secret validation failed: {validation.secret_name}")

                    # Send alert if there are critical issues or if health score is low
                    if critical_issues or metrics.overall_health_score < 70:
                        self.slack_notifier.send_health_alert(metrics, critical_issues)

                    # Send validation alert if there are failures
                    if failed_validations:
                        self.slack_notifier.send_secret_validation_alert(failed_validations)

                # Log metrics
                logger.info(f"Health Score: {metrics.overall_health_score:.1f}%, "
                           f"API Connectivity: {metrics.api_connectivity_score:.1f}%, "
                           f"Response Time: {metrics.avg_response_time_ms:.1f}ms")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait for next check
            time.sleep(interval_seconds)

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        metrics = self.metrics_collector.get_current_snapshot()
        trends = self.metrics_collector.get_health_trends(24)

        return {
            "timestamp": metrics.timestamp.isoformat(),
            "project": self.project,
            "context": self.context,
            "metrics": asdict(metrics),
            "trends": trends,
            "monitoring_active": self.monitoring_active
        }

def main():
    """Main entry point for secrets health monitor"""
    import argparse

    parser = argparse.ArgumentParser(description="Secrets Health Monitor")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument("--context", default="WORKFLOW", help="Context (WORKFLOW/development/test)")
    parser.add_argument("--interval", type=int, default=300, help="Monitoring interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once instead of continuous monitoring")
    parser.add_argument("--report", action="store_true", help="Generate health report and exit")

    args = parser.parse_args()

    # Create monitor
    monitor = SecretsHealthMonitor(args.project, args.context)

    if args.report:
        # Generate and print health report
        report = monitor.get_health_report()
        print(json.dumps(report, indent=2))
        return

    if args.once:
        # Run health checks once
        print("🔍 Running one-time health checks...")
        health_results = monitor.perform_health_checks()
        validation_results = monitor.validate_all_secrets()

        print(f"\n📊 Health Check Results:")
        for result in health_results:
            status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(result.status, "❓")
            print(f"  {status_emoji} {result.service}: {result.status} ({result.response_time_ms:.1f}ms)")
            if result.error_message:
                print(f"    Error: {result.error_message}")

        print(f"\n🔐 Secret Validation Results:")
        for result in validation_results:
            status_emoji = "✅" if result.is_valid else "❌"
            print(f"  {status_emoji} {result.secret_name}: {result.validation_type}")
            if result.error_message:
                print(f"    Error: {result.error_message}")

        # Get metrics
        metrics = monitor.metrics_collector.get_current_snapshot()
        print(f"\n📈 Overall Health Score: {metrics.overall_health_score:.1f}%")
        print(f"🌐 API Connectivity Score: {metrics.api_connectivity_score:.1f}%")
        print(f"⏱️  Average Response Time: {metrics.avg_response_time_ms:.1f}ms")

    else:
        # Start continuous monitoring
        print(f"🚀 Starting continuous monitoring for {args.project} ({args.context})...")
        monitor.start_monitoring(args.interval)

        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            monitor.stop_monitoring()

if __name__ == "__main__":
    main()
