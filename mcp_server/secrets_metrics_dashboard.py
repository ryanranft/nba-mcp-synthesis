#!/usr/bin/env python3
"""
Secrets Metrics Dashboard

Real-time dashboard for visualizing secrets health metrics, trends, and alerts.
Provides both CLI and web-based interfaces for monitoring secret health.

Features:
- Real-time metrics visualization
- Historical trend analysis
- Alert management and notification history
- Performance analytics and reporting
- Integration with secrets health monitor
- Export capabilities for metrics data
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import argparse
from pathlib import Path

# Optional web dashboard dependencies
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MetricsDashboard:
    """Main dashboard for secrets metrics visualization"""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        self.project = project
        self.context = context
        self.metrics_file = f"/tmp/secrets_metrics_{project}_{context}.json"
        self.history_file = f"/tmp/secrets_history_{project}_{context}.json"

        # Initialize metrics storage
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize metrics storage files"""
        if not os.path.exists(self.metrics_file):
            self._save_metrics(
                {
                    "timestamp": datetime.now().isoformat(),
                    "project": self.project,
                    "context": self.context,
                    "metrics": {
                        "total_secrets": 0,
                        "healthy_secrets": 0,
                        "warning_secrets": 0,
                        "critical_secrets": 0,
                        "avg_response_time_ms": 0.0,
                        "api_connectivity_score": 0.0,
                        "overall_health_score": 0.0,
                        "uptime_seconds": 0.0,
                    },
                    "trends": {
                        "trend": "no_data",
                        "message": "No recent health checks",
                    },
                    "monitoring_active": False,
                }
            )

        if not os.path.exists(self.history_file):
            self._save_history([])

    def _save_metrics(self, metrics: Dict[str, Any]):
        """Save current metrics to file"""
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _load_metrics(self) -> Dict[str, Any]:
        """Load current metrics from file"""
        try:
            with open(self.metrics_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return {}

    def _save_history(self, history: List[Dict[str, Any]]):
        """Save metrics history to file"""
        try:
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load metrics history from file"""
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def update_metrics(self, new_metrics: Dict[str, Any]):
        """Update metrics and add to history"""
        # Save current metrics
        self._save_metrics(new_metrics)

        # Add to history
        history = self._load_history()
        history.append(new_metrics)

        # Keep only last 1000 entries
        if len(history) > 1000:
            history = history[-1000:]

        self._save_history(history)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self._load_metrics()

    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""
        history = self._load_history()
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_history = []
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time >= cutoff_time:
                    filtered_history.append(entry)
            except ValueError:
                continue

        return filtered_history

    def generate_cli_dashboard(self):
        """Generate CLI dashboard"""
        metrics = self.get_current_metrics()

        if not metrics:
            print("❌ No metrics data available")
            return

        # Header
        print("=" * 80)
        print(
            f"🔍 SECRETS HEALTH DASHBOARD - {self.project.upper()} ({self.context.upper()})"
        )
        print("=" * 80)

        # Current status
        health_score = metrics.get("metrics", {}).get("overall_health_score", 0)
        api_score = metrics.get("metrics", {}).get("api_connectivity_score", 0)

        if health_score >= 90:
            status_emoji = "🟢"
            status_text = "HEALTHY"
        elif health_score >= 70:
            status_emoji = "🟡"
            status_text = "WARNING"
        else:
            status_emoji = "🔴"
            status_text = "CRITICAL"

        print(f"\n{status_emoji} OVERALL STATUS: {status_text}")
        print(f"📊 Health Score: {health_score:.1f}%")
        print(f"🌐 API Connectivity: {api_score:.1f}%")

        # Metrics breakdown
        metrics_data = metrics.get("metrics", {})
        print(f"\n📈 METRICS BREAKDOWN:")
        print(f"  Total Secrets: {metrics_data.get('total_secrets', 0)}")
        print(f"  Healthy: {metrics_data.get('healthy_secrets', 0)}")
        print(f"  Warning: {metrics_data.get('warning_secrets', 0)}")
        print(f"  Critical: {metrics_data.get('critical_secrets', 0)}")
        print(
            f"  Avg Response Time: {metrics_data.get('avg_response_time_ms', 0):.1f}ms"
        )
        print(f"  Uptime: {metrics_data.get('uptime_seconds', 0)/3600:.1f} hours")

        # Trends
        trends = metrics.get("trends", {})
        trend_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "fair": "🟠",
            "poor": "🔴",
            "no_data": "⚪",
        }.get(trends.get("trend", "no_data"), "⚪")

        print(f"\n📊 TREND ANALYSIS:")
        print(f"  Trend: {trend_emoji} {trends.get('trend', 'unknown').upper()}")
        if "healthy_ratio" in trends:
            print(f"  Healthy Ratio: {trends['healthy_ratio']:.1%}")
        if "total_checks" in trends:
            print(f"  Recent Checks: {trends['total_checks']}")

        # Monitoring status
        monitoring_active = metrics.get("monitoring_active", False)
        monitoring_emoji = "🟢" if monitoring_active else "🔴"
        print(
            f"\n🔍 MONITORING STATUS: {monitoring_emoji} {'ACTIVE' if monitoring_active else 'INACTIVE'}"
        )

        # Last update
        timestamp = metrics.get("timestamp", "")
        if timestamp:
            try:
                last_update = datetime.fromisoformat(timestamp)
                time_diff = datetime.now() - last_update
                print(
                    f"⏰ Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.total_seconds():.0f}s ago)"
                )
            except ValueError:
                print(f"⏰ Last Update: {timestamp}")

        print("=" * 80)

    def generate_charts(self, output_dir: str = "/tmp"):
        """Generate charts for metrics visualization"""
        if not MATPLOTLIB_AVAILABLE:
            print("❌ Matplotlib not available. Install with: pip install matplotlib")
            return

        history = self.get_metrics_history(24)
        if not history:
            print("❌ No historical data available for charting")
            return

        # Extract data for plotting
        timestamps = []
        health_scores = []
        api_scores = []
        response_times = []

        for entry in history:
            try:
                timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
                timestamps.append(timestamp)

                metrics = entry.get("metrics", {})
                health_scores.append(metrics.get("overall_health_score", 0))
                api_scores.append(metrics.get("api_connectivity_score", 0))
                response_times.append(metrics.get("avg_response_time_ms", 0))
            except ValueError:
                continue

        if not timestamps:
            print("❌ No valid timestamp data for charting")
            return

        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(
            f"Secrets Health Metrics - {self.project} ({self.context})", fontsize=16
        )

        # Health Score Trend
        ax1.plot(timestamps, health_scores, "g-", linewidth=2, label="Health Score")
        ax1.set_title("Overall Health Score Trend")
        ax1.set_ylabel("Health Score (%)")
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))

        # API Connectivity Trend
        ax2.plot(timestamps, api_scores, "b-", linewidth=2, label="API Connectivity")
        ax2.set_title("API Connectivity Trend")
        ax2.set_ylabel("API Score (%)")
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 100)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))

        # Response Time Trend
        ax3.plot(timestamps, response_times, "r-", linewidth=2, label="Response Time")
        ax3.set_title("Average Response Time Trend")
        ax3.set_ylabel("Response Time (ms)")
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax3.xaxis.set_major_locator(mdates.HourLocator(interval=2))

        # Health Score Distribution (histogram)
        ax4.hist(health_scores, bins=20, alpha=0.7, color="green", edgecolor="black")
        ax4.set_title("Health Score Distribution")
        ax4.set_xlabel("Health Score (%)")
        ax4.set_ylabel("Frequency")
        ax4.grid(True, alpha=0.3)

        # Rotate x-axis labels for better readability
        for ax in [ax1, ax2, ax3]:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # Save chart
        chart_file = os.path.join(
            output_dir, f"secrets_metrics_{self.project}_{self.context}.png"
        )
        plt.savefig(chart_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"📊 Charts saved to: {chart_file}")

    def export_metrics(self, output_file: str, format: str = "json"):
        """Export metrics data"""
        if format.lower() == "json":
            data = {
                "current_metrics": self.get_current_metrics(),
                "history": self.get_metrics_history(168),  # Last week
            }

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            print(f"📁 Metrics exported to: {output_file}")

        elif format.lower() == "csv":
            import csv

            history = self.get_metrics_history(168)
            if not history:
                print("❌ No historical data to export")
                return

            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(
                    [
                        "timestamp",
                        "health_score",
                        "api_score",
                        "response_time_ms",
                        "total_secrets",
                        "healthy_secrets",
                        "warning_secrets",
                        "critical_secrets",
                    ]
                )

                # Write data
                for entry in history:
                    metrics = entry.get("metrics", {})
                    writer.writerow(
                        [
                            entry.get("timestamp", ""),
                            metrics.get("overall_health_score", 0),
                            metrics.get("api_connectivity_score", 0),
                            metrics.get("avg_response_time_ms", 0),
                            metrics.get("total_secrets", 0),
                            metrics.get("healthy_secrets", 0),
                            metrics.get("warning_secrets", 0),
                            metrics.get("critical_secrets", 0),
                        ]
                    )

            print(f"📁 Metrics exported to: {output_file}")

        else:
            print(f"❌ Unsupported format: {format}")


class WebDashboard:
    """Web-based dashboard using Flask"""

    def __init__(self, dashboard: MetricsDashboard, port: int = 5000):
        if not FLASK_AVAILABLE:
            raise ImportError(
                "Flask and Flask-SocketIO not available. Install with: pip install flask flask-socketio"
            )

        self.dashboard = dashboard
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "secrets-dashboard-key"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self._setup_routes()
        self._setup_socketio()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            return render_template("dashboard.html")

        @self.app.route("/api/metrics")
        def get_metrics():
            return jsonify(self.dashboard.get_current_metrics())

        @self.app.route("/api/history")
        def get_history():
            hours = request.args.get("hours", 24, type=int)
            return jsonify(self.dashboard.get_metrics_history(hours))

        @self.app.route("/api/export")
        def export_metrics():
            format_type = request.args.get("format", "json")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"secrets_metrics_{self.dashboard.project}_{self.dashboard.context}_{timestamp}.{format_type}"

            # Create temporary file
            temp_file = f"/tmp/{filename}"
            self.dashboard.export_metrics(temp_file, format_type)

            return jsonify(
                {"filename": filename, "download_url": f"/download/{filename}"}
            )

    def _setup_socketio(self):
        """Setup SocketIO events"""

        @self.socketio.on("connect")
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit("status", {"message": "Connected to secrets dashboard"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")

        @self.socketio.on("request_metrics")
        def handle_metrics_request():
            metrics = self.dashboard.get_current_metrics()
            emit("metrics_update", metrics)

    def run(self, debug: bool = False):
        """Run the web dashboard"""
        print(f"🌐 Starting web dashboard on http://localhost:5000")
        self.socketio.run(self.app, debug=debug, port=5000)


def main():
    """Main entry point for metrics dashboard"""
    parser = argparse.ArgumentParser(description="Secrets Metrics Dashboard")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument(
        "--context", default="production", help="Context (production/development/test)"
    )
    parser.add_argument("--cli", action="store_true", help="Show CLI dashboard")
    parser.add_argument("--web", action="store_true", help="Start web dashboard")
    parser.add_argument("--charts", action="store_true", help="Generate charts")
    parser.add_argument("--export", help="Export metrics to file")
    parser.add_argument(
        "--format", default="json", choices=["json", "csv"], help="Export format"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of history to include"
    )

    args = parser.parse_args()

    # Create dashboard
    dashboard = MetricsDashboard(args.project, args.context)

    if args.cli:
        # Show CLI dashboard
        dashboard.generate_cli_dashboard()

    elif args.web:
        # Start web dashboard
        try:
            web_dashboard = WebDashboard(dashboard)
            web_dashboard.run(debug=True)
        except ImportError as e:
            print(f"❌ {e}")
            print("Install web dependencies with: pip install flask flask-socketio")

    elif args.charts:
        # Generate charts
        dashboard.generate_charts()

    elif args.export:
        # Export metrics
        dashboard.export_metrics(args.export, args.format)

    else:
        # Default: show CLI dashboard
        dashboard.generate_cli_dashboard()


if __name__ == "__main__":
    main()
