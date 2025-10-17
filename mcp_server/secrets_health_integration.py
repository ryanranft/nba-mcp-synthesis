#!/usr/bin/env python3
"""
Secrets Health Integration

Comprehensive integration script that combines health monitoring, metrics collection,
alerting, and dashboard functionality into a unified system.

Features:
- Unified health monitoring and alerting
- Real-time metrics collection and visualization
- Automated alert processing and notification
- Dashboard integration and data export
- Performance analytics and reporting
- Integration with secrets health monitor
"""

import os
import sys
import json
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import argparse
import signal
import atexit

# Import our modules
try:
    from mcp_server.secrets_health_monitor import (
        SecretsHealthMonitor,
        HealthCheckResult,
        SecretValidationResult,
    )
    from mcp_server.secrets_metrics_dashboard import MetricsDashboard
    from mcp_server.secrets_alerting_system import AlertManager, Alert, AlertSeverity
except ImportError:
    # Fallback for when running as standalone script
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_server.secrets_health_monitor import (
        SecretsHealthMonitor,
        HealthCheckResult,
        SecretValidationResult,
    )
    from mcp_server.secrets_metrics_dashboard import MetricsDashboard
    from mcp_server.secrets_alerting_system import AlertManager, Alert, AlertSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/secrets_integration.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SecretsHealthIntegration:
    """Main integration class for secrets health system"""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        self.project = project
        self.context = context
        self.running = False

        # Initialize components
        self.health_monitor = SecretsHealthMonitor(project, context)
        self.metrics_dashboard = MetricsDashboard(project, context)
        self.alert_manager = AlertManager(project, context)

        # Integration settings
        self.monitoring_interval = 300  # 5 minutes
        self.alerting_enabled = True
        self.dashboard_enabled = True

        # Threading
        self.monitor_thread = None
        self.alert_thread = None

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup)

        logger.info(f"Secrets Health Integration initialized for {project} ({context})")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)

    def _cleanup(self):
        """Cleanup resources on exit"""
        if self.running:
            self.stop()

    def start_monitoring(self, interval_seconds: int = 300):
        """Start the integrated monitoring system"""
        if self.running:
            logger.warning("Integration system is already running")
            return

        self.running = True
        self.monitoring_interval = interval_seconds

        # Start health monitoring
        self.health_monitor.start_monitoring(interval_seconds)

        # Start alert processing thread
        self.alert_thread = threading.Thread(
            target=self._alert_processing_loop, daemon=True
        )
        self.alert_thread.start()

        logger.info(
            f"Started integrated secrets health monitoring (interval: {interval_seconds}s)"
        )

    def stop(self):
        """Stop the integrated monitoring system"""
        if not self.running:
            return

        self.running = False

        # Stop health monitoring
        self.health_monitor.stop_monitoring()

        # Wait for threads to finish
        if self.alert_thread:
            self.alert_thread.join(timeout=5)

        logger.info("Stopped integrated secrets health monitoring")

    def _alert_processing_loop(self):
        """Main alert processing loop"""
        while self.running:
            try:
                # Get current metrics from dashboard
                metrics = self.metrics_dashboard.get_current_metrics()

                if metrics and self.alerting_enabled:
                    # Process alerts
                    alerts = self.alert_manager.process_metrics(
                        metrics.get("metrics", {})
                    )

                    if alerts:
                        logger.info(f"Processed {len(alerts)} alerts")

                # Update dashboard with latest metrics
                if self.dashboard_enabled:
                    # Get health report from monitor
                    health_report = self.health_monitor.get_health_report()
                    self.metrics_dashboard.update_metrics(health_report)

            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")

            # Wait for next cycle
            time.sleep(60)  # Check every minute

    def run_health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check"""
        logger.info("Running comprehensive health check...")

        # Perform health checks
        health_results = self.health_monitor.perform_health_checks()
        validation_results = self.health_monitor.validate_all_secrets()

        # Get metrics
        metrics = self.health_monitor.metrics_collector.get_current_snapshot()

        # Create comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": self.project,
            "context": self.context,
            "health_checks": [asdict(result) for result in health_results],
            "secret_validations": [asdict(result) for result in validation_results],
            "metrics": asdict(metrics),
            "alert_statistics": self.alert_manager.get_alert_statistics(),
            "overall_status": self._determine_overall_status(
                metrics, health_results, validation_results
            ),
        }

        # Update dashboard
        self.metrics_dashboard.update_metrics(report)

        # Process alerts
        if self.alerting_enabled:
            alerts = self.alert_manager.process_metrics(asdict(metrics))
            report["triggered_alerts"] = [asdict(alert) for alert in alerts]

        return report

    def _determine_overall_status(
        self, metrics, health_results, validation_results
    ) -> str:
        """Determine overall system status"""
        # Check for critical health issues
        critical_health = any(result.status == "critical" for result in health_results)
        critical_validation = any(not result.is_valid for result in validation_results)

        # Check metrics
        health_score = metrics.overall_health_score
        api_score = metrics.api_connectivity_score

        if critical_health or critical_validation or health_score < 50:
            return "critical"
        elif health_score < 70 or api_score < 70:
            return "warning"
        else:
            return "healthy"

    def generate_comprehensive_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        # Get current metrics
        current_metrics = self.metrics_dashboard.get_current_metrics()

        # Get historical data
        history = self.metrics_dashboard.get_metrics_history(hours)

        # Get alert history
        alert_history = self.alert_manager.get_alert_history(hours)

        # Get alert statistics
        alert_stats = self.alert_manager.get_alert_statistics()

        # Calculate trends
        trends = self._calculate_trends(history)

        # Generate report
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "project": self.project,
            "context": self.context,
            "report_period_hours": hours,
            "current_status": current_metrics.get("overall_status", "unknown"),
            "current_metrics": current_metrics,
            "historical_data": history,
            "alert_history": [asdict(alert) for alert in alert_history],
            "alert_statistics": alert_stats,
            "trends": trends,
            "recommendations": self._generate_recommendations(
                current_metrics, trends, alert_stats
            ),
        }

        return report

    def _calculate_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trends from historical data"""
        if not history:
            return {"trend": "no_data", "message": "No historical data available"}

        # Extract metrics
        health_scores = [
            entry.get("metrics", {}).get("overall_health_score", 0) for entry in history
        ]
        api_scores = [
            entry.get("metrics", {}).get("api_connectivity_score", 0)
            for entry in history
        ]
        response_times = [
            entry.get("metrics", {}).get("avg_response_time_ms", 0) for entry in history
        ]

        # Calculate trends
        health_trend = self._calculate_trend(health_scores)
        api_trend = self._calculate_trend(api_scores)
        response_trend = self._calculate_trend(
            response_times, reverse=True
        )  # Lower is better

        return {
            "health_score_trend": health_trend,
            "api_connectivity_trend": api_trend,
            "response_time_trend": response_trend,
            "overall_trend": self._determine_overall_trend(
                health_trend, api_trend, response_trend
            ),
        }

    def _calculate_trend(self, values: List[float], reverse: bool = False) -> str:
        """Calculate trend for a series of values"""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend calculation
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        change = second_avg - first_avg
        if reverse:
            change = -change

        if abs(change) < 1:
            return "stable"
        elif change > 0:
            return "improving"
        else:
            return "declining"

    def _determine_overall_trend(
        self, health_trend: str, api_trend: str, response_trend: str
    ) -> str:
        """Determine overall trend from individual trends"""
        trends = [health_trend, api_trend, response_trend]

        if all(t == "improving" for t in trends):
            return "excellent"
        elif trends.count("improving") >= 2:
            return "good"
        elif trends.count("declining") >= 2:
            return "poor"
        else:
            return "stable"

    def _generate_recommendations(
        self,
        current_metrics: Dict[str, Any],
        trends: Dict[str, Any],
        alert_stats: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on current state"""
        recommendations = []

        # Health score recommendations
        health_score = current_metrics.get("metrics", {}).get("overall_health_score", 0)
        if health_score < 70:
            recommendations.append(
                "Health score is below 70%. Review secret configurations and API connectivity."
            )

        # API connectivity recommendations
        api_score = current_metrics.get("metrics", {}).get("api_connectivity_score", 0)
        if api_score < 80:
            recommendations.append(
                "API connectivity is below 80%. Check API keys and network connectivity."
            )

        # Response time recommendations
        response_time = current_metrics.get("metrics", {}).get(
            "avg_response_time_ms", 0
        )
        if response_time > 2000:
            recommendations.append(
                "Average response time exceeds 2 seconds. Consider optimizing API calls."
            )

        # Alert frequency recommendations
        recent_alerts = alert_stats.get("recent_alerts_count", 0)
        if recent_alerts > 10:
            recommendations.append(
                "High alert frequency detected. Review alert thresholds and system stability."
            )

        # Trend-based recommendations
        overall_trend = trends.get("overall_trend", "stable")
        if overall_trend == "declining":
            recommendations.append(
                "System performance is declining. Investigate root causes."
            )
        elif overall_trend == "improving":
            recommendations.append(
                "System performance is improving. Continue current practices."
            )

        return recommendations

    def export_report(
        self, report: Dict[str, Any], output_file: str, format: str = "json"
    ):
        """Export comprehensive report"""
        if format.lower() == "json":
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
        elif format.lower() == "html":
            html_content = self._generate_html_report(report)
            with open(output_file, "w") as f:
                f.write(html_content)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Report exported to: {output_file}")

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secrets Health Report - {report['project']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4f8; border-radius: 5px; }}
                .alert {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .alert-critical {{ background: #ffebee; border-left: 4px solid #f44336; }}
                .alert-warning {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
                .alert-info {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
                .recommendation {{ background: #f1f8e9; padding: 10px; margin: 5px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Secrets Health Report</h1>
                <p><strong>Project:</strong> {report['project']} | <strong>Context:</strong> {report['context']}</p>
                <p><strong>Generated:</strong> {report['report_timestamp']}</p>
                <p><strong>Period:</strong> Last {report['report_period_hours']} hours</p>
            </div>

            <div class="section">
                <h2>📊 Current Status</h2>
                <div class="metric">
                    <strong>Overall Status:</strong> {report['current_status'].upper()}
                </div>
                <div class="metric">
                    <strong>Health Score:</strong> {report['current_metrics'].get('metrics', {}).get('overall_health_score', 0):.1f}%
                </div>
                <div class="metric">
                    <strong>API Connectivity:</strong> {report['current_metrics'].get('metrics', {}).get('api_connectivity_score', 0):.1f}%
                </div>
            </div>

            <div class="section">
                <h2>📈 Trends</h2>
                <p><strong>Overall Trend:</strong> {report['trends'].get('overall_trend', 'unknown').upper()}</p>
                <p><strong>Health Score Trend:</strong> {report['trends'].get('health_score_trend', 'unknown')}</p>
                <p><strong>API Connectivity Trend:</strong> {report['trends'].get('api_connectivity_trend', 'unknown')}</p>
            </div>

            <div class="section">
                <h2>🚨 Recent Alerts</h2>
                <p><strong>Total Alerts:</strong> {report['alert_statistics'].get('total_alerts', 0)}</p>
                <p><strong>Recent Trend:</strong> {report['alert_statistics'].get('recent_trend', 'unknown')}</p>
            </div>

            <div class="section">
                <h2>💡 Recommendations</h2>
                {"".join([f"<div class='recommendation'>{rec}</div>" for rec in report.get('recommendations', [])])}
            </div>
        </body>
        </html>
        """

        return html


def main():
    """Main entry point for secrets health integration"""
    parser = argparse.ArgumentParser(description="Secrets Health Integration")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument(
        "--context", default="production", help="Context (production/development/test)"
    )
    parser.add_argument(
        "--start", action="store_true", help="Start integrated monitoring"
    )
    parser.add_argument("--check", action="store_true", help="Run health check")
    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive report"
    )
    parser.add_argument("--export", help="Export report to file")
    parser.add_argument(
        "--format", default="json", choices=["json", "html"], help="Export format"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of history for report"
    )
    parser.add_argument(
        "--interval", type=int, default=300, help="Monitoring interval in seconds"
    )

    args = parser.parse_args()

    # Create integration system
    integration = SecretsHealthIntegration(args.project, args.context)

    if args.start:
        # Start integrated monitoring
        print(f"🚀 Starting integrated secrets health monitoring...")
        integration.start_monitoring(args.interval)

        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            integration.stop()

    elif args.check:
        # Run health check
        print("🔍 Running comprehensive health check...")
        report = integration.run_health_check()

        print(f"\n📊 Health Check Results:")
        print(f"  Overall Status: {report['overall_status'].upper()}")
        print(
            f"  Health Score: {report['metrics'].get('overall_health_score', 0):.1f}%"
        )
        print(
            f"  API Connectivity: {report['metrics'].get('api_connectivity_score', 0):.1f}%"
        )
        print(
            f"  Response Time: {report['metrics'].get('avg_response_time_ms', 0):.1f}ms"
        )

        if report.get("triggered_alerts"):
            print(f"\n🚨 Triggered Alerts: {len(report['triggered_alerts'])}")
            for alert in report["triggered_alerts"]:
                print(f"  • {alert['title']} ({alert['severity']})")

    elif args.report:
        # Generate comprehensive report
        print(f"📋 Generating comprehensive report for last {args.hours} hours...")
        report = integration.generate_comprehensive_report(args.hours)

        print(f"\n📊 Comprehensive Report:")
        print(f"  Project: {report['project']}")
        print(f"  Context: {report['context']}")
        print(f"  Current Status: {report['current_status'].upper()}")
        print(f"  Overall Trend: {report['trends']['overall_trend'].upper()}")
        print(f"  Total Alerts: {report['alert_statistics']['total_alerts']}")
        print(f"  Recommendations: {len(report['recommendations'])}")

        if args.export:
            integration.export_report(report, args.export, args.format)
            print(f"📁 Report exported to: {args.export}")

    else:
        print("Secrets Health Integration System")
        print("Use --start to begin integrated monitoring")
        print("Use --check to run a health check")
        print("Use --report to generate a comprehensive report")
        print("Use --export <file> to export report data")


if __name__ == "__main__":
    main()
