#!/usr/bin/env python3
"""
Test Report Generator
Consolidates results from multiple test runs into comprehensive reports

Usage:
    python scripts/generate_test_report.py
    python scripts/generate_test_report.py --input test_results/
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import statistics


class ReportGenerator:
    """Generate comprehensive test reports from JSON results"""

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir
        self.test_results: List[Dict] = []
        self.benchmark_results: List[Dict] = []

    def load_results(self):
        """Load all test and benchmark results from input directory"""

        print(f"📁 Loading results from: {self.input_dir}")

        # Load test results
        test_files = list(self.input_dir.glob("test_report*.json"))
        for file in test_files:
            with open(file) as f:
                data = json.load(f)
                self.test_results.append({"file": file.name, "data": data})
                print(f"  ✅ Loaded test: {file.name}")

        # Load benchmark results
        benchmark_dir = Path("./benchmark_results")
        if benchmark_dir.exists():
            benchmark_files = list(benchmark_dir.glob("benchmark_*.json"))
            for file in benchmark_files:
                with open(file) as f:
                    data = json.load(f)
                    self.benchmark_results.append({"file": file.name, "data": data})
                    print(f"  ✅ Loaded benchmark: {file.name}")

        print(
            f"\n📊 Found {len(self.test_results)} test runs, {len(self.benchmark_results)} benchmarks\n"
        )

    def generate_consolidated_html(self, output_file: Path):
        """Generate consolidated HTML report"""

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <title>NBA MCP Test Report - Consolidated</title>",
            "    <style>",
            "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }",
            "        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }",
            "        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }",
            "        h2 { color: #34495e; margin-top: 30px; }",
            "        h3 { color: #7f8c8d; }",
            "        .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }",
            "        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }",
            "        .metric { background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }",
            "        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }",
            "        .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }",
            "        table { width: 100%; border-collapse: collapse; margin: 20px 0; }",
            "        th { background: #34495e; color: white; padding: 12px; text-align: left; }",
            "        td { padding: 10px; border-bottom: 1px solid #ecf0f1; }",
            "        tr:hover { background: #f8f9fa; }",
            "        .pass { color: #27ae60; font-weight: bold; }",
            "        .fail { color: #e74c3c; font-weight: bold; }",
            "        .timestamp { color: #95a5a6; font-size: 14px; }",
            "        .chart { margin: 20px 0; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='container'>",
            f"        <h1>🧪 NBA MCP Consolidated Test Report</h1>",
            f"        <p class='timestamp'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        ]

        # Overall summary
        total_tests = sum(len(r["data"].get("tests", [])) for r in self.test_results)
        total_passed = sum(
            sum(1 for t in r["data"].get("tests", []) if t.get("passed"))
            for r in self.test_results
        )
        total_failed = total_tests - total_passed
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        html_parts.extend(
            [
                "        <div class='summary'>",
                "            <h2>📊 Overall Summary</h2>",
                "            <div class='summary-grid'>",
                "                <div class='metric'>",
                f"                    <div class='metric-value'>{len(self.test_results)}</div>",
                "                    <div class='metric-label'>Test Runs</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='metric-value'>{total_tests}</div>",
                "                    <div class='metric-label'>Total Tests</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='metric-value' style='color: #27ae60;'>{total_passed}</div>",
                "                    <div class='metric-label'>Passed</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='metric-value' style='color: #e74c3c;'>{total_failed}</div>",
                "                    <div class='metric-label'>Failed</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='metric-value'>{pass_rate:.1f}%</div>",
                "                    <div class='metric-label'>Pass Rate</div>",
                "                </div>",
                "            </div>",
                "        </div>",
            ]
        )

        # Test runs details
        html_parts.append("        <h2>🧪 Test Runs</h2>")

        for i, result in enumerate(self.test_results, 1):
            data = result["data"]
            summary = data.get("summary", {})

            html_parts.extend(
                [
                    f"        <h3>Run {i}: {result['file']}</h3>",
                    "        <table>",
                    "            <thead>",
                    "                <tr>",
                    "                    <th>Test Name</th>",
                    "                    <th>Category</th>",
                    "                    <th>Status</th>",
                    "                    <th>Duration</th>",
                    "                </tr>",
                    "            </thead>",
                    "            <tbody>",
                ]
            )

            for test in data.get("tests", []):
                status_class = "pass" if test.get("passed") else "fail"
                status_text = "✅ PASS" if test.get("passed") else "❌ FAIL"
                duration = test.get("duration", 0)

                html_parts.extend(
                    [
                        "                <tr>",
                        f"                    <td>{test.get('name', 'Unknown')}</td>",
                        f"                    <td>{test.get('category', 'N/A')}</td>",
                        f"                    <td class='{status_class}'>{status_text}</td>",
                        f"                    <td>{duration:.3f}s</td>",
                        "                </tr>",
                    ]
                )

            html_parts.extend(
                [
                    "            </tbody>",
                    "        </table>",
                ]
            )

        # Benchmark results
        if self.benchmark_results:
            html_parts.append("        <h2>⚡ Performance Benchmarks</h2>")

            for i, result in enumerate(self.benchmark_results, 1):
                data = result["data"]

                html_parts.extend(
                    [
                        f"        <h3>Benchmark {i}: {result['file']}</h3>",
                        "        <table>",
                        "            <thead>",
                        "                <tr>",
                        "                    <th>Benchmark</th>",
                        "                    <th>Iterations</th>",
                        "                    <th>Avg Time</th>",
                        "                    <th>Ops/sec</th>",
                        "                    <th>Success Rate</th>",
                        "                </tr>",
                        "            </thead>",
                        "            <tbody>",
                    ]
                )

                for bench in data.get("results", []):
                    success_rate = (
                        bench.get("success_count", 0) / bench.get("iterations", 1) * 100
                    )

                    html_parts.extend(
                        [
                            "                <tr>",
                            f"                    <td>{bench.get('name', 'Unknown')}</td>",
                            f"                    <td>{bench.get('iterations', 0)}</td>",
                            f"                    <td>{bench.get('avg_time', 0):.4f}s</td>",
                            f"                    <td>{bench.get('operations_per_sec', 0):.2f}</td>",
                            f"                    <td>{success_rate:.1f}%</td>",
                            "                </tr>",
                        ]
                    )

                html_parts.extend(
                    [
                        "            </tbody>",
                        "        </table>",
                    ]
                )

        html_parts.extend(
            [
                "    </div>",
                "</body>",
                "</html>",
            ]
        )

        # Write HTML
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(html_parts))

        print(f"✅ Consolidated HTML report: {output_file}")

    def generate_summary_text(self, output_file: Path):
        """Generate text summary"""

        lines = [
            "=" * 70,
            "NBA MCP TEST SUMMARY",
            "=" * 70,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Test results
        if self.test_results:
            lines.extend(
                [
                    "TEST RUNS",
                    "-" * 70,
                ]
            )

            for i, result in enumerate(self.test_results, 1):
                data = result["data"]
                summary = data.get("summary", {})

                lines.extend(
                    [
                        f"\nRun {i}: {result['file']}",
                        f"  Total:  {summary.get('total', 0)}",
                        f"  Passed: {summary.get('passed', 0)}",
                        f"  Failed: {summary.get('failed', 0)}",
                        f"  Rate:   {summary.get('pass_rate', 0):.1f}%",
                    ]
                )

        # Benchmark results
        if self.benchmark_results:
            lines.extend(
                [
                    "",
                    "BENCHMARKS",
                    "-" * 70,
                ]
            )

            for i, result in enumerate(self.benchmark_results, 1):
                data = result["data"]

                lines.append(f"\nBenchmark {i}: {result['file']}")

                for bench in data.get("results", []):
                    lines.extend(
                        [
                            f"  {bench.get('name', 'Unknown')}:",
                            f"    Avg time: {bench.get('avg_time', 0):.4f}s",
                            f"    Ops/sec:  {bench.get('operations_per_sec', 0):.2f}",
                        ]
                    )

        lines.append("\n" + "=" * 70)

        # Write text
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(lines))

        print(f"✅ Summary text file: {output_file}")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="Generate consolidated test reports")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("./test_results"),
        help="Input directory with test results (default: ./test_results)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./reports"),
        help="Output directory for reports (default: ./reports)",
    )

    args = parser.parse_args()

    print("\n📊 Test Report Generator\n")

    # Check input directory
    if not args.input.exists():
        print(f"❌ Input directory not found: {args.input}")
        print("   Run tests first to generate results!")
        return 1

    # Create generator
    generator = ReportGenerator(args.input)

    # Load results
    generator.load_results()

    if not generator.test_results and not generator.benchmark_results:
        print("⚠️  No results found!")
        return 1

    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    args.output.mkdir(parents=True, exist_ok=True)

    generator.generate_consolidated_html(
        args.output / f"consolidated_report_{timestamp}.html"
    )

    generator.generate_summary_text(args.output / f"summary_{timestamp}.txt")

    print(f"\n✅ Reports generated in: {args.output}\n")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
