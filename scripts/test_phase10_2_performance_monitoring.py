#!/usr/bin/env python3
"""
Test script for Phase 10.2: Performance Monitoring & Optimization

Tests comprehensive performance monitoring capabilities including metrics collection,
alerting, reporting, and optimization features.
"""

import sys
import os
import time
import unittest
import uuid
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.tools.performance_monitoring import (
    PerformanceMonitor,
    MetricType,
    AlertSeverity,
    OptimizationType,
    start_performance_monitoring,
    stop_performance_monitoring,
    record_performance_metric,
    record_request_performance,
    create_performance_alert_rule,
    get_performance_metrics,
    get_performance_alerts,
    generate_performance_report,
    optimize_performance,
    get_monitoring_status,
)


class Phase102TestSuite(unittest.TestCase):
    """Test suite for Phase 10.2: Performance Monitoring & Optimization"""

    def setUp(self):
        """Set up test environment"""
        self.monitor = PerformanceMonitor()
        self.test_metric_type = "cpu_usage"
        self.test_value = 75.5
        self.test_tags = {"host": "test-server", "environment": "testing"}

    def test_monitor_initialization(self):
        """Test performance monitor initialization"""
        print("\n=== Testing Monitor Initialization ===")

        # Test basic initialization
        monitor = PerformanceMonitor()
        self.assertIsInstance(monitor, PerformanceMonitor)
        self.assertFalse(monitor.monitoring_active)
        self.assertEqual(monitor.collection_interval, 5)

        print("✓ Monitor initialization successful")

    def test_start_stop_monitoring(self):
        """Test starting and stopping performance monitoring"""
        print("\n=== Testing Start/Stop Monitoring ===")

        # Test starting monitoring
        result = self.monitor.start_monitoring()
        self.assertEqual(result["status"], "started")
        self.assertTrue(self.monitor.monitoring_active)

        # Wait a moment for monitoring to collect some data
        time.sleep(2)

        # Test stopping monitoring
        result = self.monitor.stop_monitoring()
        self.assertEqual(result["status"], "stopped")
        self.assertFalse(self.monitor.monitoring_active)

        print("✓ Start/stop monitoring successful")

    def test_metric_recording(self):
        """Test recording custom metrics"""
        print("\n=== Testing Metric Recording ===")

        # Test recording custom metric
        result = self.monitor.record_custom_metric(
            MetricType.CPU_USAGE, self.test_value, self.test_tags
        )
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["metric_type"], "cpu_usage")
        self.assertEqual(result["value"], self.test_value)

        # Test recording request metrics
        result = self.monitor.record_request_metrics(
            response_time=150.5, success=True, endpoint="/api/test"
        )
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["response_time"], 150.5)
        self.assertTrue(result["success"])

        print("✓ Metric recording successful")

    def test_alert_rules(self):
        """Test alert rule creation and management"""
        print("\n=== Testing Alert Rules ===")

        # Create alert rule
        from mcp_server.tools.performance_monitoring import AlertRule

        rule_obj = AlertRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            metric_type=MetricType.CPU_USAGE,
            threshold=80.0,
            operator=">",
            severity=AlertSeverity.WARNING,
            description="High CPU usage alert",
        )
        rule = self.monitor.create_alert_rule(rule_obj)
        self.assertEqual(rule["status"], "created")
        self.assertIn("rule_id", rule)

        # Record metric that should trigger alert
        self.monitor.record_custom_metric(MetricType.CPU_USAGE, 85.0)

        # Check alert rules
        self.monitor._check_alert_rules()

        # Verify alert was created
        self.assertGreater(len(self.monitor.active_alerts), 0)

        print("✓ Alert rules successful")

    def test_metrics_retrieval(self):
        """Test retrieving current metrics"""
        print("\n=== Testing Metrics Retrieval ===")

        # Record some test metrics
        self.monitor.record_custom_metric(MetricType.CPU_USAGE, 65.0)
        self.monitor.record_custom_metric(MetricType.MEMORY_USAGE, 70.0)

        # Get current metrics
        result = self.monitor.get_current_metrics()
        self.assertEqual(result["status"], "success")
        self.assertIn("current_metrics", result)

        # Verify metrics are present
        metrics = result["current_metrics"]
        self.assertIn("cpu_usage", metrics)
        self.assertIn("memory_usage", metrics)

        print("✓ Metrics retrieval successful")

    def test_metric_history(self):
        """Test retrieving metric history"""
        print("\n=== Testing Metric History ===")

        # Record multiple metrics
        for i in range(5):
            self.monitor.record_custom_metric(MetricType.CPU_USAGE, 60.0 + i)
            time.sleep(0.1)

        # Get metric history using the monitor directly
        result = self.monitor.get_metric_history(MetricType.CPU_USAGE, hours=1)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["metric_type"], "cpu_usage")
        self.assertGreaterEqual(result["count"], 5)

        print("✓ Metric history successful")

    def test_performance_report(self):
        """Test generating performance reports"""
        print("\n=== Testing Performance Report ===")

        # Record various metrics
        self.monitor.record_custom_metric(MetricType.CPU_USAGE, 70.0)
        self.monitor.record_custom_metric(MetricType.MEMORY_USAGE, 75.0)
        self.monitor.record_custom_metric(MetricType.RESPONSE_TIME, 200.0)

        # Generate report
        result = self.monitor.generate_performance_report(hours=1)
        self.assertEqual(result["status"], "success")
        self.assertIn("report", result)

        report = result["report"]
        self.assertIn("report_id", report)
        self.assertIn("performance_score", report)
        self.assertIn("metrics_summary", report)
        self.assertIn("optimization_recommendations", report)

        print("✓ Performance report successful")

    def test_optimization(self):
        """Test performance optimization"""
        print("\n=== Testing Performance Optimization ===")

        # Test memory optimization
        result = self.monitor.optimize_performance(OptimizationType.MEMORY_OPTIMIZATION)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["optimization_type"], "memory_optimization")
        self.assertIn("optimization_id", result)

        # Test CPU optimization
        result = self.monitor.optimize_performance(OptimizationType.CPU_OPTIMIZATION)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["optimization_type"], "cpu_optimization")

        print("✓ Performance optimization successful")

    def test_monitoring_status(self):
        """Test getting monitoring status"""
        print("\n=== Testing Monitoring Status ===")

        # Get status
        result = self.monitor.get_monitoring_status()
        self.assertEqual(result["status"], "success")
        self.assertIn("monitoring_active", result)
        self.assertIn("total_metrics", result)
        self.assertIn("active_alerts", result)

        print("✓ Monitoring status successful")

    def test_standalone_functions(self):
        """Test standalone functions for MCP integration"""
        print("\n=== Testing Standalone Functions ===")

        # Test start monitoring
        result = start_performance_monitoring()
        self.assertEqual(result["status"], "started")

        # Test record metric
        result = record_performance_metric("cpu_usage", 65.0, {"test": "true"})
        self.assertEqual(result["status"], "recorded")

        # Test record request performance
        result = record_request_performance(150.0, True, "/api/test")
        self.assertEqual(result["status"], "recorded")

        # Test create alert rule
        result = create_performance_alert_rule(
            "memory_usage", 85.0, ">", "critical", "High memory usage"
        )
        self.assertEqual(result["status"], "created")

        # Test get metrics
        result = get_performance_metrics()
        self.assertEqual(result["status"], "success")

        # Test get alerts
        result = get_performance_alerts()
        self.assertEqual(result["status"], "success")

        # Test get metric history
        result = get_performance_metrics()
        self.assertEqual(result["status"], "success")

        # Test generate report
        result = generate_performance_report(1)
        self.assertEqual(result["status"], "success")

        # Test optimize performance
        result = optimize_performance("memory_optimization")
        self.assertEqual(result["status"], "applied")

        # Test get monitoring status
        result = get_monitoring_status()
        self.assertEqual(result["status"], "success")

        # Test stop monitoring
        result = stop_performance_monitoring()
        self.assertEqual(result["status"], "stopped")

        print("✓ Standalone functions successful")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n=== Testing Error Handling ===")

        # Test invalid metric type
        result = record_performance_metric("invalid_metric", 50.0)
        self.assertEqual(result["status"], "error")

        # Test invalid optimization type
        result = optimize_performance("invalid_optimization")
        self.assertEqual(result["status"], "error")

        # Test invalid alert rule parameters
        result = create_performance_alert_rule(
            "invalid_metric", 50.0, "invalid_op", "invalid_severity"
        )
        self.assertEqual(result["status"], "error")

        print("✓ Error handling successful")

    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n=== Testing Performance Benchmarks ===")

        # Test metric recording performance
        start_time = time.time()
        for i in range(100):
            self.monitor.record_custom_metric(MetricType.CPU_USAGE, 50.0 + i)
        end_time = time.time()

        recording_time = end_time - start_time
        self.assertLess(recording_time, 1.0)  # Should be fast

        # Test report generation performance
        start_time = time.time()
        result = self.monitor.generate_performance_report(hours=1)
        end_time = time.time()

        report_time = end_time - start_time
        self.assertLess(report_time, 2.0)  # Should be reasonably fast
        self.assertEqual(result["status"], "success")

        print(
            f"✓ Performance benchmarks successful (recording: {recording_time:.3f}s, report: {report_time:.3f}s)"
        )


def run_tests():
    """Run all Phase 10.2 tests"""
    print("=" * 60)
    print("Phase 10.2: Performance Monitoring & Optimization Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase102TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
