"""
Metrics Reporter for Performance Data

Generates reports, exports data, and creates performance dashboards.
"""

import json
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsReporter:
    """
    Generates performance reports and exports metrics data.

    Features:
    - JSON/CSV export
    - HTML report generation
    - Performance dashboard data
    - Comparison reports
    """

    def __init__(self, profiler):
        """
        Initialize metrics reporter.

        Args:
            profiler: PerformanceProfiler instance
        """
        self.profiler = profiler

    def export_to_json(
        self,
        output_path: str,
        include_raw_data: bool = False
    ) -> bool:
        """
        Export metrics to JSON file.

        Args:
            output_path: Path to output JSON file
            include_raw_data: Include all raw profile results

        Returns:
            True if successful
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "summary": self.profiler.get_summary(),
                "function_stats": self.profiler.get_all_stats(),
                "slowest_functions": self.profiler.get_slowest_functions(),
                "most_called_functions": self.profiler.get_most_called_functions(),
                "bottlenecks": self.profiler.identify_bottlenecks()
            }

            if include_raw_data:
                # Include raw profile results
                raw_data = {}
                for func_name, results in self.profiler.profiles.items():
                    raw_data[func_name] = [
                        {
                            "execution_time_ms": r.execution_time_ms,
                            "memory_peak_mb": r.memory_peak_mb,
                            "memory_delta_mb": r.memory_delta_mb,
                            "timestamp": r.timestamp.isoformat()
                        }
                        for r in results
                    ]
                data["raw_profiles"] = raw_data

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Metrics exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics to JSON: {e}")
            return False

    def export_to_csv(self, output_path: str) -> bool:
        """
        Export aggregated function stats to CSV file.

        Args:
            output_path: Path to output CSV file

        Returns:
            True if successful
        """
        try:
            stats = self.profiler.get_all_stats()

            with open(output_path, 'w', newline='') as f:
                fieldnames = [
                    "function_name", "call_count", "total_time_ms",
                    "avg_time_ms", "min_time_ms", "max_time_ms",
                    "median_time_ms", "slow_calls"
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for stat in stats.values():
                    writer.writerow({k: stat.get(k) for k in fieldnames})

            logger.info(f"Metrics exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics to CSV: {e}")
            return False

    def generate_text_report(self) -> str:
        """
        Generate human-readable text report.

        Returns:
            Formatted text report
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("PERFORMANCE PROFILING REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        summary = self.profiler.get_summary()
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"  Total Functions Profiled: {summary['total_functions_profiled']}")
        lines.append(f"  Total Function Calls: {summary['total_calls']}")
        lines.append(f"  Total Execution Time: {summary['total_time_ms']:.2f} ms")
        lines.append(f"  Average Time per Call: {summary['avg_time_per_call_ms']:.2f} ms")
        lines.append(f"  Slow Function Threshold: {summary['slow_threshold_ms']} ms")
        lines.append("")

        # Slowest Functions
        lines.append("SLOWEST FUNCTIONS (by average time)")
        lines.append("-" * 80)
        slowest = self.profiler.get_slowest_functions(10)
        for i, func in enumerate(slowest, 1):
            lines.append(
                f"{i:2d}. {func['function_name']:60s} "
                f"avg: {func['avg_time_ms']:7.2f} ms  "
                f"calls: {func['call_count']:4d}"
            )
        lines.append("")

        # Most Called Functions
        lines.append("MOST FREQUENTLY CALLED FUNCTIONS")
        lines.append("-" * 80)
        most_called = self.profiler.get_most_called_functions(10)
        for i, func in enumerate(most_called, 1):
            lines.append(
                f"{i:2d}. {func['function_name']:60s} "
                f"calls: {func['call_count']:4d}  "
                f"total: {func['total_time_ms']:7.2f} ms"
            )
        lines.append("")

        # Bottlenecks
        bottlenecks = self.profiler.identify_bottlenecks()
        if bottlenecks:
            lines.append("IDENTIFIED BOTTLENECKS")
            lines.append("-" * 80)
            for i, bottleneck in enumerate(bottlenecks, 1):
                lines.append(f"{i}. {bottleneck['function_name']}")
                lines.append(f"   Impact Score: {bottleneck['impact_score']:.2f}")
                lines.append(f"   Calls: {bottleneck['call_count']}, Avg Time: {bottleneck['avg_time_ms']:.2f} ms")

                if bottleneck['recommendations']:
                    lines.append("   Recommendations:")
                    for rec in bottleneck['recommendations']:
                        lines.append(f"     • {rec}")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_html_report(self, output_path: str) -> bool:
        """
        Generate HTML report with visualizations.

        Args:
            output_path: Path to output HTML file

        Returns:
            True if successful
        """
        try:
            summary = self.profiler.get_summary()
            slowest = self.profiler.get_slowest_functions(10)
            most_called = self.profiler.get_most_called_functions(10)
            bottlenecks = self.profiler.identify_bottlenecks()

            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Profiling Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: inline-block;
            margin-right: 30px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #666;
        }}
        .metric-value {{
            font-size: 24px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .slow {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .bottleneck {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin-bottom: 15px;
        }}
        .recommendation {{
            margin-left: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>Performance Profiling Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-label">Functions Profiled</div>
            <div class="metric-value">{summary['total_functions_profiled']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Calls</div>
            <div class="metric-value">{summary['total_calls']:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Time</div>
            <div class="metric-value">{summary['total_time_ms']:.2f} ms</div>
        </div>
        <div class="metric">
            <div class="metric-label">Avg Time/Call</div>
            <div class="metric-value">{summary['avg_time_per_call_ms']:.2f} ms</div>
        </div>
    </div>

    <h2>Slowest Functions</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Function</th>
            <th>Avg Time (ms)</th>
            <th>Call Count</th>
            <th>Total Time (ms)</th>
        </tr>
"""

            for i, func in enumerate(slowest, 1):
                slow_class = ' class="slow"' if func['avg_time_ms'] > summary['slow_threshold_ms'] else ''
                html += f"""
        <tr>
            <td>{i}</td>
            <td>{func['function_name']}</td>
            <td{slow_class}>{func['avg_time_ms']:.2f}</td>
            <td>{func['call_count']}</td>
            <td>{func['total_time_ms']:.2f}</td>
        </tr>
"""

            html += """
    </table>

    <h2>Most Called Functions</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Function</th>
            <th>Call Count</th>
            <th>Total Time (ms)</th>
            <th>Avg Time (ms)</th>
        </tr>
"""

            for i, func in enumerate(most_called, 1):
                html += f"""
        <tr>
            <td>{i}</td>
            <td>{func['function_name']}</td>
            <td>{func['call_count']}</td>
            <td>{func['total_time_ms']:.2f}</td>
            <td>{func['avg_time_ms']:.2f}</td>
        </tr>
"""

            html += """
    </table>
"""

            if bottlenecks:
                html += """
    <h2>Identified Bottlenecks</h2>
"""
                for i, bottleneck in enumerate(bottlenecks, 1):
                    html += f"""
    <div class="bottleneck">
        <h3>{i}. {bottleneck['function_name']}</h3>
        <p><strong>Impact Score:</strong> {bottleneck['impact_score']:.2f}</p>
        <p><strong>Calls:</strong> {bottleneck['call_count']}, <strong>Avg Time:</strong> {bottleneck['avg_time_ms']:.2f} ms</p>
"""
                    if bottleneck['recommendations']:
                        html += "<p><strong>Recommendations:</strong></p><ul>"
                        for rec in bottleneck['recommendations']:
                            html += f"<li class='recommendation'>{rec}</li>"
                        html += "</ul>"

                    html += "</div>"

            html += """
</body>
</html>
"""

            with open(output_path, 'w') as f:
                f.write(html)

            logger.info(f"HTML report generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return False

    def compare_with_baseline(
        self,
        baseline_path: str
    ) -> Dict[str, Any]:
        """
        Compare current metrics with baseline.

        Args:
            baseline_path: Path to baseline JSON file

        Returns:
            Dict with comparison results
        """
        try:
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)

            current_stats = self.profiler.get_all_stats()
            baseline_stats = baseline.get("function_stats", {})

            comparisons = []

            for func_name, current in current_stats.items():
                if func_name in baseline_stats:
                    baseline_func = baseline_stats[func_name]

                    # Calculate percentage changes
                    avg_time_change = (
                        (current["avg_time_ms"] - baseline_func["avg_time_ms"]) /
                        baseline_func["avg_time_ms"] * 100
                    )

                    comparisons.append({
                        "function_name": func_name,
                        "current_avg_time_ms": current["avg_time_ms"],
                        "baseline_avg_time_ms": baseline_func["avg_time_ms"],
                        "change_percent": avg_time_change,
                        "regression": avg_time_change > 10,  # 10% slower is regression
                        "improvement": avg_time_change < -10  # 10% faster is improvement
                    })

            # Sort by absolute change
            comparisons.sort(key=lambda c: abs(c["change_percent"]), reverse=True)

            regressions = [c for c in comparisons if c["regression"]]
            improvements = [c for c in comparisons if c["improvement"]]

            return {
                "baseline_file": baseline_path,
                "baseline_timestamp": baseline.get("timestamp"),
                "current_timestamp": datetime.now().isoformat(),
                "total_functions_compared": len(comparisons),
                "regressions": regressions,
                "improvements": improvements,
                "detailed_comparisons": comparisons
            }

        except Exception as e:
            logger.error(f"Failed to compare with baseline: {e}")
            return {"error": str(e)}
