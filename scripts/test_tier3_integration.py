#!/usr/bin/env python3
"""
Tier 3 Integration Test Suite

Tests all Tier 3 features to ensure they work together correctly:
- Resource Monitoring
- Workflow Monitor Dashboard
- Dependency Visualization
- Version Tracking
- A/B Testing Integration

Usage:
    python scripts/test_tier3_integration.py
    python scripts/test_tier3_integration.py --verbose
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


class Tier3IntegrationTests:
    """Integration tests for Tier 3 features."""

    def __init__(self):
        """Initialize test suite."""
        self.passed = 0
        self.failed = 0
        self.results = []

    def test_resource_monitor(self) -> bool:
        """Test Resource Monitoring System."""
        print("\n📊 Testing Resource Monitor...")
        try:
            from resource_monitor import ResourceMonitor

            # Initialize monitor
            monitor = ResourceMonitor()

            # Test API quota checking
            allowed, reason = monitor.check_api_quota('gemini', 1000)
            assert allowed, "API quota check failed"

            # Track usage
            monitor.track_api_usage('gemini', 1000)
            assert monitor.api_quotas['gemini']['used'] == 1000

            # Test disk space monitoring
            disk_metrics = monitor.monitor_disk_space()
            assert 'total_gb' in disk_metrics
            assert 'free_gb' in disk_metrics

            # Test memory monitoring
            memory_metrics = monitor.monitor_memory_usage()
            assert 'total_gb' in memory_metrics
            assert 'usage_percent' in memory_metrics

            # Test system metrics
            system_metrics = monitor.get_system_metrics()
            assert 'api_quotas' in system_metrics
            assert 'disk' in system_metrics
            assert 'memory' in system_metrics

            print("  ✅ Resource Monitor: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ Resource Monitor: FAILED - {e}")
            logger.error(f"Resource Monitor test failed: {e}", exc_info=True)
            return False

    def test_workflow_monitor(self) -> bool:
        """Test Workflow Monitor Dashboard."""
        print("\n🎯 Testing Workflow Monitor...")
        try:
            from workflow_monitor import WorkflowMonitor

            # Initialize monitor (don't auto-start)
            monitor = WorkflowMonitor(port=8081, auto_start=False)

            # Test state updates
            monitor.update_workflow_state(
                phase='Phase 2: Analysis',
                books_processed=10,
                total_books=51,
                active=True
            )

            # Test status data
            status = monitor.get_status_data()
            assert status['current_phase'] == 'Phase 2: Analysis'
            assert status['books']['processed'] == 10
            assert status['books']['total'] == 51
            assert status['workflow_active'] == True

            print("  ✅ Workflow Monitor: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ Workflow Monitor: FAILED - {e}")
            logger.error(f"Workflow Monitor test failed: {e}", exc_info=True)
            return False

    def test_dependency_visualizer(self) -> bool:
        """Test Dependency Visualization."""
        print("\n📊 Testing Dependency Visualizer...")
        try:
            from dependency_visualizer import DependencyVisualizer

            # Initialize visualizer
            visualizer = DependencyVisualizer()

            # Test Mermaid diagram generation
            diagram = visualizer.generate_mermaid_diagram(show_critical=True)
            assert 'graph TD' in diagram
            assert 'phase_0' in diagram

            # Test data flow diagram
            flow_diagram = visualizer.generate_data_flow_diagram()
            assert 'graph LR' in flow_diagram
            assert 'Books' in flow_diagram

            # Test critical path identification
            critical_path = visualizer.identify_critical_path()
            assert len(critical_path) > 0
            assert 'phase_0' in critical_path

            # Test bottleneck analysis
            bottlenecks = visualizer.analyze_bottlenecks()
            assert isinstance(bottlenecks, list)

            print("  ✅ Dependency Visualizer: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ Dependency Visualizer: FAILED - {e}")
            logger.error(f"Dependency Visualizer test failed: {e}", exc_info=True)
            return False

    def test_version_tracker(self) -> bool:
        """Test Version Tracking System."""
        print("\n📝 Testing Version Tracker...")
        try:
            from version_tracker import VersionTracker

            # Initialize tracker
            tracker = VersionTracker()

            # Test file header generation
            source_books = [
                {'title': 'Test Book 1', 'hash': 'abc123'},
                {'title': 'Test Book 2', 'hash': 'def456'}
            ]
            models_used = {
                'gemini': 'gemini-2.0-flash-exp',
                'claude': 'claude-sonnet-4'
            }

            header = tracker.generate_file_header(
                generator_script='test_script.py',
                source_books=source_books,
                models_used=models_used,
                regenerate_command='python test.py'
            )

            assert 'Generated by: NBA MCP Synthesis System' in header
            assert 'Test Book 1' in header
            assert 'gemini-2.0-flash-exp' in header

            # Test markdown header
            md_header = tracker.generate_markdown_header(
                generator_script='test_script.py',
                source_books=source_books,
                models_used=models_used
            )

            assert '<!-- Version Metadata' in md_header
            assert 'Test Book 1' in md_header

            print("  ✅ Version Tracker: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ Version Tracker: FAILED - {e}")
            logger.error(f"Version Tracker test failed: {e}", exc_info=True)
            return False

    def test_ab_testing_framework(self) -> bool:
        """Test A/B Testing Framework Integration."""
        print("\n🧪 Testing A/B Testing Framework...")
        try:
            from ab_testing_framework import ABTestingFramework, ModelConfig

            # Initialize framework
            framework = ABTestingFramework(results_dir=Path('/tmp/ab_test_results'))

            # Test config to model combination conversion
            config = ModelConfig(
                name='test_config',
                description='Test configuration',
                primary_model='gemini',
                secondary_model='claude',
                use_consensus=True,
                similarity_threshold=0.70
            )

            model_combo = framework._config_to_model_combination(config)
            assert model_combo in ['gemini+claude', 'gemini_only', 'claude_only']

            # Test predefined configs exist
            assert 'gemini_only' in framework.CONFIGS
            assert 'claude_only' in framework.CONFIGS
            assert 'gemini_claude_consensus' in framework.CONFIGS

            print("  ✅ A/B Testing Framework: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ A/B Testing Framework: FAILED - {e}")
            logger.error(f"A/B Testing Framework test failed: {e}", exc_info=True)
            return False

    def test_integration(self) -> bool:
        """Test integration between components."""
        print("\n🔗 Testing Component Integration...")
        try:
            from resource_monitor import ResourceMonitor
            from workflow_monitor import WorkflowMonitor

            # Initialize components
            resource_monitor = ResourceMonitor()
            workflow_monitor = WorkflowMonitor(port=8082, auto_start=False)

            # Test that workflow monitor can access resource monitor
            workflow_monitor.resource_monitor = resource_monitor

            # Get system metrics through workflow monitor
            metrics = resource_monitor.get_system_metrics()
            assert 'api_quotas' in metrics

            # Update workflow state and verify
            workflow_monitor.update_workflow_state(
                phase='Integration Test',
                books_processed=5,
                total_books=10,
                active=True
            )

            status = workflow_monitor.get_status_data()
            assert status['current_phase'] == 'Integration Test'

            print("  ✅ Component Integration: PASSED")
            return True

        except Exception as e:
            print(f"  ❌ Component Integration: FAILED - {e}")
            logger.error(f"Component Integration test failed: {e}", exc_info=True)
            return False

    def run_all_tests(self) -> Dict:
        """
        Run all integration tests.

        Returns:
            Dict with test results
        """
        print("\n" + "="*60)
        print("🧪 Tier 3 Integration Test Suite")
        print("="*60)

        tests = [
            ('Resource Monitor', self.test_resource_monitor),
            ('Workflow Monitor', self.test_workflow_monitor),
            ('Dependency Visualizer', self.test_dependency_visualizer),
            ('Version Tracker', self.test_version_tracker),
            ('A/B Testing Framework', self.test_ab_testing_framework),
            ('Component Integration', self.test_integration)
        ]

        results = []

        for test_name, test_func in tests:
            try:
                passed = test_func()
                results.append({
                    'test': test_name,
                    'status': 'PASSED' if passed else 'FAILED',
                    'passed': passed
                })
                if passed:
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                logger.error(f"Test {test_name} raised exception: {e}", exc_info=True)
                results.append({
                    'test': test_name,
                    'status': 'ERROR',
                    'passed': False,
                    'error': str(e)
                })
                self.failed += 1

        # Print summary
        print("\n" + "="*60)
        print("📊 Test Results Summary")
        print("="*60)
        print(f"\n✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {self.passed + self.failed}")

        if self.failed == 0:
            print("\n🎉 All tests PASSED!")
        else:
            print(f"\n⚠️  {self.failed} test(s) FAILED")

        print("="*60 + "\n")

        return {
            'passed': self.passed,
            'failed': self.failed,
            'total': self.passed + self.failed,
            'results': results,
            'success': self.failed == 0
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Tier 3 Integration Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    test_suite = Tier3IntegrationTests()
    results = test_suite.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()







