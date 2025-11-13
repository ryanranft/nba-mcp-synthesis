"""
Tests for MetricsReporter

Tests report generation, export functions, and baseline comparisons.
"""

import pytest
import json
import csv
import tempfile
from pathlib import Path
from mcp_server.profiling.performance import PerformanceProfiler, ProfileResult
from mcp_server.profiling.metrics_reporter import MetricsReporter


class TestMetricsReporter:
    """Test suite for MetricsReporter"""

    @pytest.fixture
    def profiler_with_data(self):
        """Create profiler with sample data"""
        profiler = PerformanceProfiler()
        profiler.reset()

        # Add sample profile data
        functions = [
            ("test.fast_function", 10.0, 5),
            ("test.slow_function", 150.0, 3),
            ("test.frequent_function", 20.0, 50),
        ]

        for func_name, exec_time, call_count in functions:
            for _ in range(call_count):
                profiler.record(ProfileResult(func_name, exec_time))

        return profiler

    @pytest.fixture
    def reporter(self, profiler_with_data):
        """Create metrics reporter instance"""
        return MetricsReporter(profiler_with_data)

    def test_export_to_json(self, reporter):
        """Test exporting metrics to JSON"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            success = reporter.export_to_json(output_path)
            assert success is True

            # Verify file exists and is valid JSON
            with open(output_path, "r") as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "summary" in data
            assert "function_stats" in data
            assert "slowest_functions" in data
            assert "most_called_functions" in data
            assert "bottlenecks" in data

            # Verify content
            assert data["summary"]["total_functions_profiled"] == 3

        finally:
            Path(output_path).unlink()

    def test_export_to_json_with_raw_data(self, reporter):
        """Test exporting with raw profile results"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            success = reporter.export_to_json(output_path, include_raw_data=True)
            assert success is True

            with open(output_path, "r") as f:
                data = json.load(f)

            assert "raw_profiles" in data
            assert len(data["raw_profiles"]) > 0

        finally:
            Path(output_path).unlink()

    def test_export_to_csv(self, reporter):
        """Test exporting metrics to CSV"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            output_path = f.name

        try:
            success = reporter.export_to_csv(output_path)
            assert success is True

            # Verify file exists and has correct structure
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 3  # Three functions
            assert "function_name" in rows[0]
            assert "call_count" in rows[0]
            assert "avg_time_ms" in rows[0]

        finally:
            Path(output_path).unlink()

    def test_generate_text_report(self, reporter):
        """Test generating text report"""
        report = reporter.generate_text_report()

        assert report is not None
        assert "PERFORMANCE PROFILING REPORT" in report
        assert "SUMMARY" in report
        assert "SLOWEST FUNCTIONS" in report
        assert "MOST FREQUENTLY CALLED" in report

        # Check that function names appear
        assert "test.slow_function" in report
        assert "test.frequent_function" in report

    def test_generate_html_report(self, reporter):
        """Test generating HTML report"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            output_path = f.name

        try:
            success = reporter.generate_html_report(output_path)
            assert success is True

            # Verify file exists and contains HTML
            with open(output_path, "r") as f:
                html_content = f.read()

            assert "<!DOCTYPE html>" in html_content
            assert "<title>Performance Profiling Report</title>" in html_content
            assert "test.slow_function" in html_content
            assert "test.frequent_function" in html_content

        finally:
            Path(output_path).unlink()

    def test_compare_with_baseline(self, reporter):
        """Test comparing with baseline metrics"""
        # Create a baseline file
        baseline_data = {
            "timestamp": "2024-01-01T00:00:00",
            "function_stats": {
                "test.fast_function": {
                    "avg_time_ms": 12.0,  # Baseline was slower
                    "call_count": 5,
                },
                "test.slow_function": {
                    "avg_time_ms": 100.0,  # Current is slower (regression)
                    "call_count": 3,
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(baseline_data, f)
            baseline_path = f.name

        try:
            comparison = reporter.compare_with_baseline(baseline_path)

            assert "baseline_timestamp" in comparison
            assert "current_timestamp" in comparison
            assert "regressions" in comparison
            assert "improvements" in comparison

            # test.slow_function should be a regression (150ms vs 100ms)
            regressions = comparison["regressions"]
            assert len(regressions) > 0
            assert any(r["function_name"] == "test.slow_function" for r in regressions)

            # test.fast_function should be an improvement (10ms vs 12ms)
            improvements = comparison["improvements"]
            assert any(i["function_name"] == "test.fast_function" for i in improvements)

        finally:
            Path(baseline_path).unlink()

    def test_empty_profiler_export(self):
        """Test exporting from empty profiler"""
        empty_profiler = PerformanceProfiler()
        empty_profiler.reset()
        reporter = MetricsReporter(empty_profiler)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            success = reporter.export_to_json(output_path)
            assert success is True

            with open(output_path, "r") as f:
                data = json.load(f)

            assert data["summary"]["total_functions_profiled"] == 0
            assert len(data["function_stats"]) == 0

        finally:
            Path(output_path).unlink()

    def test_text_report_with_bottlenecks(self):
        """Test text report includes bottlenecks"""
        profiler = PerformanceProfiler(slow_threshold_ms=50.0)

        # Create a bottleneck
        for _ in range(20):
            profiler.record(ProfileResult("bottleneck.function", 75.0))

        reporter = MetricsReporter(profiler)
        report = reporter.generate_text_report()

        assert "IDENTIFIED BOTTLENECKS" in report
        assert "bottleneck.function" in report
        assert "Impact Score" in report
        assert "Recommendations" in report

    def test_html_report_structure(self, reporter):
        """Test HTML report has proper structure"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            output_path = f.name

        try:
            success = reporter.generate_html_report(output_path)
            assert success is True

            with open(output_path, "r") as f:
                html = f.read()

            # Check for required HTML elements
            assert "<html>" in html
            assert "<head>" in html
            assert "<body>" in html
            assert "<table>" in html
            assert "<style>" in html

            # Check for metrics
            assert "Functions Profiled" in html
            assert "Total Calls" in html

        finally:
            Path(output_path).unlink()

    def test_compare_baseline_missing_file(self, reporter):
        """Test comparison with non-existent baseline file"""
        comparison = reporter.compare_with_baseline("/nonexistent/baseline.json")

        assert "error" in comparison

    def test_csv_export_column_names(self, reporter):
        """Test that CSV has correct column names"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            output_path = f.name

        try:
            reporter.export_to_csv(output_path)

            with open(output_path, "r") as f:
                reader = csv.reader(f)
                headers = next(reader)

            expected_columns = [
                "function_name",
                "call_count",
                "total_time_ms",
                "avg_time_ms",
                "min_time_ms",
                "max_time_ms",
                "median_time_ms",
                "slow_calls",
            ]

            assert headers == expected_columns

        finally:
            Path(output_path).unlink()
