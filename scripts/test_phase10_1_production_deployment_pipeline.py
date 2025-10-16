#!/usr/bin/env python3
"""
Test script for Phase 10.1: Production Deployment Pipeline

This script tests all the production deployment capabilities including:
- Application deployment with multiple strategies
- Rollback functionality
- Health checks
- Security scanning
- Performance testing
- Deployment status and history

Author: NBA MCP Server Development Team
Date: October 13, 2025
"""

import sys
import os
import unittest
import time
import json
import logging
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the deployment pipeline
from mcp_server.tools.production_deployment_pipeline import (
    ProductionDeploymentPipeline,
    deploy_application,
    rollback_deployment,
    check_deployment_health,
    scan_security,
    test_performance,
    get_deployment_status,
    list_deployments,
    get_deployment_history,
    DeploymentStatus,
    EnvironmentType,
    DeploymentStrategy
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase101TestSuite(unittest.TestCase):
    """Test suite for Phase 10.1: Production Deployment Pipeline"""

    def setUp(self):
        """Set up test environment"""
        self.pipeline = ProductionDeploymentPipeline()
        self.test_environments = ["development", "staging", "production"]
        self.test_versions = ["v1.0.0", "v1.1.0", "v1.2.0"]
        self.test_strategies = ["rolling", "blue_green", "canary", "recreate"]

    def test_pipeline_initialization(self):
        """Test deployment pipeline initialization"""
        logger.info("Testing pipeline initialization...")

        self.assertIsNotNone(self.pipeline)
        self.assertIsInstance(self.pipeline, ProductionDeploymentPipeline)

        # Check configuration
        self.assertIsNotNone(self.pipeline.config)
        self.assertIn('environments', self.pipeline.config)
        self.assertIn('deployment', self.pipeline.config)

        logger.info("✓ Pipeline initialization test passed")

    def test_deployment_rolling_strategy(self):
        """Test rolling deployment strategy"""
        logger.info("Testing rolling deployment strategy...")

        result = self.pipeline.deploy(
            environment="development",
            version="v1.0.0",
            strategy="rolling"
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.environment, EnvironmentType.DEVELOPMENT)
        self.assertEqual(result.version, "v1.0.0")
        self.assertEqual(result.status, DeploymentStatus.SUCCESS)
        self.assertIsNotNone(result.deployment_id)
        self.assertIsNotNone(result.start_time)
        self.assertIsNotNone(result.end_time)

        logger.info("✓ Rolling deployment strategy test passed")

    def test_deployment_blue_green_strategy(self):
        """Test blue-green deployment strategy"""
        logger.info("Testing blue-green deployment strategy...")

        result = self.pipeline.deploy(
            environment="staging",
            version="v1.1.0",
            strategy="blue_green"
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.environment, EnvironmentType.STAGING)
        self.assertEqual(result.version, "v1.1.0")
        self.assertEqual(result.status, DeploymentStatus.SUCCESS)

        logger.info("✓ Blue-green deployment strategy test passed")

    def test_deployment_canary_strategy(self):
        """Test canary deployment strategy"""
        logger.info("Testing canary deployment strategy...")

        result = self.pipeline.deploy(
            environment="production",
            version="v1.2.0",
            strategy="canary"
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.environment, EnvironmentType.PRODUCTION)
        self.assertEqual(result.version, "v1.2.0")
        self.assertEqual(result.status, DeploymentStatus.SUCCESS)

        logger.info("✓ Canary deployment strategy test passed")

    def test_deployment_recreate_strategy(self):
        """Test recreate deployment strategy"""
        logger.info("Testing recreate deployment strategy...")

        result = self.pipeline.deploy(
            environment="testing",
            version="v1.0.0",
            strategy="recreate"
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.environment, EnvironmentType.TESTING)
        self.assertEqual(result.version, "v1.0.0")
        self.assertEqual(result.status, DeploymentStatus.SUCCESS)

        logger.info("✓ Recreate deployment strategy test passed")

    def test_rollback_functionality(self):
        """Test rollback functionality"""
        logger.info("Testing rollback functionality...")

        # First deploy
        deploy_result = self.pipeline.deploy(
            environment="development",
            version="v1.1.0",
            strategy="rolling"
        )

        self.assertTrue(deploy_result.success)

        # Then rollback
        rollback_result = self.pipeline.rollback(
            deployment_id=deploy_result.deployment_id,
            target_version="v1.0.0"
        )

        self.assertIsNotNone(rollback_result)
        self.assertTrue(rollback_result.success)
        self.assertEqual(rollback_result.status, DeploymentStatus.ROLLED_BACK)
        self.assertEqual(rollback_result.version, "v1.0.0")

        logger.info("✓ Rollback functionality test passed")

    def test_health_check(self):
        """Test health check functionality"""
        logger.info("Testing health check functionality...")

        result = self.pipeline.health_check(
            endpoint="http://localhost:8080/health",
            timeout=30
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.endpoint)
        self.assertIsNotNone(result.status_code)
        self.assertIsNotNone(result.response_time_ms)
        self.assertIsNotNone(result.healthy)
        self.assertIsNotNone(result.timestamp)

        logger.info("✓ Health check functionality test passed")

    def test_security_scan(self):
        """Test security scan functionality"""
        logger.info("Testing security scan functionality...")

        result = self.pipeline.security_scan(
            image_name="nba-mcp-server:latest",
            scan_type="vulnerability"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.scan_type, "vulnerability")
        self.assertIsNotNone(result.vulnerabilities_found)
        self.assertIsNotNone(result.critical_vulnerabilities)
        self.assertIsNotNone(result.high_vulnerabilities)
        self.assertIsNotNone(result.medium_vulnerabilities)
        self.assertIsNotNone(result.low_vulnerabilities)
        self.assertIsNotNone(result.passed)
        self.assertIsNotNone(result.scan_duration_seconds)
        self.assertIsNotNone(result.recommendations)

        logger.info("✓ Security scan functionality test passed")

    def test_performance_test(self):
        """Test performance test functionality"""
        logger.info("Testing performance test functionality...")

        result = self.pipeline.performance_test(
            endpoint="http://localhost:8080/api",
            test_config={"duration": 60, "users": 10}
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.test_name, "load_test")
        self.assertIsNotNone(result.requests_per_second)
        self.assertIsNotNone(result.average_response_time_ms)
        self.assertIsNotNone(result.p95_response_time_ms)
        self.assertIsNotNone(result.p99_response_time_ms)
        self.assertIsNotNone(result.error_rate)
        self.assertIsNotNone(result.passed)
        self.assertIsNotNone(result.test_duration_seconds)
        self.assertIsNotNone(result.recommendations)

        logger.info("✓ Performance test functionality test passed")

    def test_deployment_status(self):
        """Test deployment status retrieval"""
        logger.info("Testing deployment status retrieval...")

        # First deploy
        deploy_result = self.pipeline.deploy(
            environment="development",
            version="v1.0.0",
            strategy="rolling"
        )

        # Get status
        status_result = self.pipeline.get_deployment_status(deploy_result.deployment_id)

        self.assertIsNotNone(status_result)
        self.assertEqual(status_result.deployment_id, deploy_result.deployment_id)
        self.assertEqual(status_result.environment, EnvironmentType.DEVELOPMENT)
        self.assertEqual(status_result.version, "v1.0.0")

        logger.info("✓ Deployment status retrieval test passed")

    def test_list_deployments(self):
        """Test deployment listing"""
        logger.info("Testing deployment listing...")

        # Create multiple deployments
        for i, env in enumerate(self.test_environments):
            self.pipeline.deploy(
                environment=env,
                version=f"v1.{i}.0",
                strategy="rolling"
            )

        # List all deployments
        all_deployments = self.pipeline.list_deployments()
        self.assertIsInstance(all_deployments, list)
        self.assertGreater(len(all_deployments), 0)

        # List deployments by environment
        dev_deployments = self.pipeline.list_deployments("development")
        self.assertIsInstance(dev_deployments, list)

        logger.info("✓ Deployment listing test passed")

    def test_deployment_history(self):
        """Test deployment history"""
        logger.info("Testing deployment history...")

        # Create some deployments
        for i in range(3):
            self.pipeline.deploy(
                environment="development",
                version=f"v1.{i}.0",
                strategy="rolling"
            )

        # Get history
        history = self.pipeline.get_deployment_history()

        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

        # Check history structure
        for record in history:
            self.assertIn('deployment_id', record)
            self.assertIn('environment', record)
            self.assertIn('version', record)
            self.assertIn('status', record)
            self.assertIn('start_time', record)
            self.assertIn('success', record)

        logger.info("✓ Deployment history test passed")

    def test_error_handling(self):
        """Test error handling"""
        logger.info("Testing error handling...")

        # Test invalid environment
        try:
            result = self.pipeline.deploy(
                environment="invalid_env",
                version="v1.0.0",
                strategy="rolling"
            )
            # Should handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            # Expected to fail gracefully
            self.assertIsInstance(e, ValueError)

        # Test invalid strategy
        try:
            result = self.pipeline.deploy(
                environment="development",
                version="v1.0.0",
                strategy="invalid_strategy"
            )
            # Should handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            # Expected to fail gracefully
            self.assertIsInstance(e, ValueError)

        logger.info("✓ Error handling test passed")

    def test_standalone_functions(self):
        """Test standalone functions"""
        logger.info("Testing standalone functions...")

        # Test deploy_application
        result = deploy_application(
            environment="development",
            version="v1.0.0",
            strategy="rolling"
        )

        self.assertIsInstance(result, dict)
        self.assertIn('deployment_id', result)
        self.assertIn('success', result)
        self.assertIn('status', result)

        # Test check_deployment_health
        health_result = check_deployment_health(
            endpoint="http://localhost:8080/health",
            timeout=30
        )

        self.assertIsInstance(health_result, dict)
        self.assertIn('endpoint', health_result)
        self.assertIn('healthy', health_result)

        # Test scan_security
        security_result = scan_security(
            image_name="nba-mcp-server:latest",
            scan_type="vulnerability"
        )

        self.assertIsInstance(security_result, dict)
        self.assertIn('scan_type', security_result)
        self.assertIn('vulnerabilities_found', security_result)

        # Test test_performance
        performance_result = test_performance(
            endpoint="http://localhost:8080/api"
        )

        self.assertIsInstance(performance_result, dict)
        self.assertIn('test_name', performance_result)
        self.assertIn('requests_per_second', performance_result)

        # Test get_deployment_status
        status_result = get_deployment_status(result['deployment_id'])

        if status_result:
            self.assertIsInstance(status_result, dict)
            self.assertIn('deployment_id', status_result)

        # Test list_deployments
        deployments = list_deployments()
        self.assertIsInstance(deployments, list)

        # Test get_deployment_history
        history = get_deployment_history()
        self.assertIsInstance(history, list)

        logger.info("✓ Standalone functions test passed")

    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        logger.info("Testing performance benchmarks...")

        start_time = time.time()

        # Test multiple deployments
        for i in range(5):
            result = self.pipeline.deploy(
                environment="development",
                version=f"v1.{i}.0",
                strategy="rolling"
            )
            self.assertTrue(result.success)

        end_time = time.time()
        total_time = end_time - start_time

        # Performance should be reasonable (less than 30 seconds for 5 deployments)
        self.assertLess(total_time, 30.0)

        logger.info(f"✓ Performance test passed: {total_time:.2f} seconds for 5 deployments")

    def test_integration_scenarios(self):
        """Test integration scenarios"""
        logger.info("Testing integration scenarios...")

        # Scenario 1: Deploy -> Health Check -> Rollback
        deploy_result = self.pipeline.deploy(
            environment="staging",
            version="v1.0.0",
            strategy="rolling"
        )

        self.assertTrue(deploy_result.success)

        # Health check
        health_result = self.pipeline.health_check("http://staging.example.com/health")
        self.assertIsNotNone(health_result)

        # Rollback
        rollback_result = self.pipeline.rollback(deploy_result.deployment_id)
        self.assertTrue(rollback_result.success)

        # Scenario 2: Security Scan -> Deploy -> Performance Test
        security_result = self.pipeline.security_scan("nba-mcp-server:v1.1.0")
        self.assertIsNotNone(security_result)

        deploy_result2 = self.pipeline.deploy(
            environment="production",
            version="v1.1.0",
            strategy="canary"
        )

        self.assertTrue(deploy_result2.success)

        performance_result = self.pipeline.performance_test("http://production.example.com/api")
        self.assertIsNotNone(performance_result)

        logger.info("✓ Integration scenarios test passed")

def run_performance_test():
    """Run performance test"""
    logger.info("Running performance test...")

    pipeline = ProductionDeploymentPipeline()

    start_time = time.time()

    # Test deployment performance
    result = pipeline.deploy(
        environment="development",
        version="v1.0.0",
        strategy="rolling"
    )

    end_time = time.time()
    deployment_time = end_time - start_time

    logger.info(f"Deployment completed in {deployment_time:.2f} seconds")
    logger.info(f"Success: {result.success}")

    return deployment_time < 10.0  # Should complete within 10 seconds

def main():
    """Main test function"""
    logger.info("Starting Phase 10.1: Production Deployment Pipeline Tests")
    logger.info("=" * 70)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase101TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Run performance test
    logger.info("\n" + "=" * 70)
    logger.info("Running Performance Test")
    logger.info("=" * 70)

    performance_passed = run_performance_test()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests

    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Errors: {error_tests}")
    logger.info(f"Performance Test: {'PASSED' if performance_passed else 'FAILED'}")

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1f}%")

    if result.wasSuccessful() and performance_passed:
        logger.info("\n🎉 ALL TESTS PASSED! Phase 10.1 implementation is working correctly.")
        return True
    else:
        logger.info(f"\n❌ {failed_tests + error_tests} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



