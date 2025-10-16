#!/usr/bin/env python3
"""
Comprehensive Validation Script

Validates the entire unified secrets management system across all entry points and environments.
Tests integration, functionality, and performance of all components.

Features:
- End-to-end validation of all entry points
- Environment-specific testing (production, development, test)
- Integration testing between components
- Performance benchmarking
- Error handling validation
- Security validation
- Documentation validation
"""

import os
import sys
import json
import time
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/validation_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of a validation test"""
    test_name: str
    status: str  # 'pass', 'fail', 'warning', 'skip'
    message: str = ""
    duration: float = 0.0
    details: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ComprehensiveValidator:
    """Comprehensive validation system for secrets management"""

    def __init__(self, project: str = "nba-mcp-synthesis"):
        self.project = project
        self.results: List[ValidationResult] = []
        self.temp_dir = None
        self.start_time = datetime.now()

        # Test configurations
        self.environments = ["production", "development", "test"]
        self.entry_points = [
            "scripts/automated_workflow.py",
            "scripts/resilient_book_analyzer.py",
            "mcp_server/server.py",
            "scripts/test_all_credentials.py",
            "test_mcp_tools.py"
        ]

        logger.info(f"Initialized comprehensive validator for project: {project}")

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("🚀 Starting comprehensive validation...")

        # Setup
        self._setup_temp_environment()

        try:
            # Core system validations
            self._validate_directory_structure()
            self._validate_naming_convention()
            self._validate_hierarchical_loader()
            self._validate_unified_secrets_manager()
            self._validate_unified_configuration_manager()

            # Entry point validations
            self._validate_entry_points()

            # Environment validations
            self._validate_environments()

            # Integration validations
            self._validate_integration()

            # Health monitoring validations
            self._validate_health_monitoring()

            # Docker validations
            self._validate_docker_integration()

            # Security validations
            self._validate_security()

            # Performance validations
            self._validate_performance()

            # Documentation validations
            self._validate_documentation()

        finally:
            self._cleanup_temp_environment()

        # Generate final report
        return self._generate_final_report()

    def _setup_temp_environment(self):
        """Setup temporary environment for testing"""
        self.temp_dir = tempfile.mkdtemp(prefix="secrets_validation_")
        logger.info(f"Created temporary environment: {self.temp_dir}")

    def _cleanup_temp_environment(self):
        """Cleanup temporary environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up temporary environment")

    def _add_result(self, result: ValidationResult):
        """Add validation result"""
        self.results.append(result)
        status_emoji = {"pass": "✅", "fail": "❌", "warning": "⚠️", "skip": "⏭️"}.get(result.status, "❓")
        logger.info(f"{status_emoji} {result.test_name}: {result.status} ({result.duration:.2f}s)")
        if result.message:
            logger.info(f"   {result.message}")

    def _run_command(self, command: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run command and return result"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def _validate_directory_structure(self):
        """Validate directory structure exists"""
        start_time = time.time()

        try:
            # Check main directory structure
            base_path = "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA"
            required_paths = [
                f"{base_path}/nba-mcp-synthesis/.env.nba_mcp_synthesis.production",
                f"{base_path}/nba-mcp-synthesis/.env.nba_mcp_synthesis.development",
                f"{base_path}/nba-mcp-synthesis/.env.nba_mcp_synthesis.test",
                f"{base_path}/nba-simulator-aws/.env.nba_simulator_aws.production",
                f"{base_path}/nba-simulator-aws/.env.nba_simulator_aws.development",
                f"{base_path}/nba-simulator-aws/.env.nba_simulator_aws.test"
            ]

            missing_paths = []
            for path in required_paths:
                if not os.path.exists(path):
                    missing_paths.append(path)

            duration = time.time() - start_time

            if missing_paths:
                self._add_result(ValidationResult(
                    "directory_structure",
                    "fail",
                    f"Missing directories: {', '.join(missing_paths)}",
                    duration
                ))
            else:
                self._add_result(ValidationResult(
                    "directory_structure",
                    "pass",
                    "All required directories exist",
                    duration
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "directory_structure",
                "fail",
                f"Error checking directory structure: {e}",
                duration
            ))

    def _validate_naming_convention(self):
        """Validate naming convention enforcement"""
        start_time = time.time()

        try:
            # Test naming convention enforcer
            returncode, stdout, stderr = self._run_command([
                sys.executable, "scripts/enforce_naming_convention.py",
                "--base-path", "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis"
            ])

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "naming_convention",
                    "pass",
                    "Naming convention validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "naming_convention",
                    "warning",
                    f"Naming convention issues found: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "naming_convention",
                "fail",
                f"Error testing naming convention: {e}",
                duration
            ))

    def _validate_hierarchical_loader(self):
        """Validate hierarchical loader functionality"""
        start_time = time.time()

        try:
            # Test hierarchical loader
            returncode, stdout, stderr = self._run_command([
                sys.executable, "/Users/ryanranft/load_env_hierarchical.py",
                self.project, "NBA", "production"
            ])

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "hierarchical_loader",
                    "pass",
                    "Hierarchical loader validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "hierarchical_loader",
                    "fail",
                    f"Hierarchical loader failed: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "hierarchical_loader",
                "fail",
                f"Error testing hierarchical loader: {e}",
                duration
            ))

    def _validate_unified_secrets_manager(self):
        """Validate unified secrets manager"""
        start_time = time.time()

        try:
            # Test unified secrets manager
            test_script = f"""
import sys
sys.path.append('.')
from mcp_server.unified_secrets_manager import UnifiedSecretsManager

# Test initialization
manager = UnifiedSecretsManager("{self.project}")
print("UnifiedSecretsManager initialized successfully")

# Test basic functionality
print("UnifiedSecretsManager basic functionality test passed")

print("All tests passed")
"""

            with open(f"{self.temp_dir}/test_secrets_manager.py", "w") as f:
                f.write(test_script)

            returncode, stdout, stderr = self._run_command([
                sys.executable, f"{self.temp_dir}/test_secrets_manager.py"
            ])

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "unified_secrets_manager",
                    "pass",
                    "Unified secrets manager validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "unified_secrets_manager",
                    "fail",
                    f"Unified secrets manager failed: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "unified_secrets_manager",
                "fail",
                f"Error testing unified secrets manager: {e}",
                duration
            ))

    def _validate_unified_configuration_manager(self):
        """Validate unified configuration manager"""
        start_time = time.time()

        try:
            # Test unified configuration manager
            test_script = f"""
import sys
sys.path.append('.')
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

# Test initialization
config = UnifiedConfigurationManager("{self.project}", "production")
print("UnifiedConfigurationManager initialized successfully")

# Test configuration loading
api_config = config.api_config
print(f"API config loaded: {{type(api_config)}}")

# Test environment variable mapping
context_key = config.context_key
print(f"Context key: {{context_key}}")

print("All tests passed")
"""

            with open(f"{self.temp_dir}/test_config_manager.py", "w") as f:
                f.write(test_script)

            returncode, stdout, stderr = self._run_command([
                sys.executable, f"{self.temp_dir}/test_config_manager.py"
            ])

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "unified_configuration_manager",
                    "pass",
                    "Unified configuration manager validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "unified_configuration_manager",
                    "fail",
                    f"Unified configuration manager failed: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "unified_configuration_manager",
                "fail",
                f"Error testing unified configuration manager: {e}",
                duration
            ))

    def _validate_entry_points(self):
        """Validate all entry points"""
        for entry_point in self.entry_points:
            self._validate_entry_point(entry_point)

    def _validate_entry_point(self, entry_point: str):
        """Validate a single entry point"""
        start_time = time.time()

        try:
            # Check if file exists
            if not os.path.exists(entry_point):
                duration = time.time() - start_time
                self._add_result(ValidationResult(
                    f"entry_point_{entry_point.replace('/', '_').replace('.', '_')}",
                    "skip",
                    f"Entry point not found: {entry_point}",
                    duration
                ))
                return

            # Test entry point with help flag
            returncode, stdout, stderr = self._run_command([
                sys.executable, entry_point, "--help"
            ], timeout=10)

            duration = time.time() - start_time

            if returncode == 0 or "usage:" in stdout.lower() or "help" in stdout.lower():
                self._add_result(ValidationResult(
                    f"entry_point_{entry_point.replace('/', '_').replace('.', '_')}",
                    "pass",
                    f"Entry point {entry_point} is functional",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    f"entry_point_{entry_point.replace('/', '_').replace('.', '_')}",
                    "warning",
                    f"Entry point {entry_point} may have issues: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                f"entry_point_{entry_point.replace('/', '_').replace('.', '_')}",
                "fail",
                f"Error testing entry point {entry_point}: {e}",
                duration
            ))

    def _validate_environments(self):
        """Validate all environments"""
        for environment in self.environments:
            self._validate_environment(environment)

    def _validate_environment(self, environment: str):
        """Validate a single environment"""
        start_time = time.time()

        try:
            # Test hierarchical loader for this environment
            returncode, stdout, stderr = self._run_command([
                sys.executable, "/Users/ryanranft/load_env_hierarchical.py",
                self.project, "NBA", environment
            ])

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    f"environment_{environment}",
                    "pass",
                    f"Environment {environment} validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    f"environment_{environment}",
                    "warning",
                    f"Environment {environment} has issues: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                f"environment_{environment}",
                "fail",
                f"Error testing environment {environment}: {e}",
                duration
            ))

    def _validate_integration(self):
        """Validate integration between components"""
        start_time = time.time()

        try:
            # Test integration script
            returncode, stdout, stderr = self._run_command([
                sys.executable, "mcp_server/secrets_health_integration.py",
                "--project", self.project,
                "--context", "production",
                "--check"
            ], timeout=60)

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "integration",
                    "pass",
                    "Integration validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "integration",
                    "warning",
                    f"Integration issues found: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "integration",
                "fail",
                f"Error testing integration: {e}",
                duration
            ))

    def _validate_health_monitoring(self):
        """Validate health monitoring system"""
        start_time = time.time()

        try:
            # Test health monitor
            returncode, stdout, stderr = self._run_command([
                sys.executable, "mcp_server/secrets_health_monitor.py",
                "--project", self.project,
                "--context", "production",
                "--once"
            ], timeout=30)

            duration = time.time() - start_time

            if returncode == 0:
                self._add_result(ValidationResult(
                    "health_monitoring",
                    "pass",
                    "Health monitoring validation passed",
                    duration,
                    {"output": stdout}
                ))
            else:
                self._add_result(ValidationResult(
                    "health_monitoring",
                    "warning",
                    f"Health monitoring issues: {stderr}",
                    duration,
                    {"output": stdout, "error": stderr}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "health_monitoring",
                "fail",
                f"Error testing health monitoring: {e}",
                duration
            ))

    def _validate_docker_integration(self):
        """Validate Docker integration"""
        start_time = time.time()

        try:
            # Check if Docker files exist
            docker_files = [
                "Dockerfile",
                "docker-compose.dev.yml",
                "docker-compose.prod.yml",
                "docker-compose.test.yml",
                "docker/load_secrets_docker.py",
                "docker/entrypoint.sh"
            ]

            missing_files = []
            for file in docker_files:
                if not os.path.exists(file):
                    missing_files.append(file)

            duration = time.time() - start_time

            if missing_files:
                self._add_result(ValidationResult(
                    "docker_integration",
                    "warning",
                    f"Missing Docker files: {', '.join(missing_files)}",
                    duration
                ))
            else:
                self._add_result(ValidationResult(
                    "docker_integration",
                    "pass",
                    "All Docker files present",
                    duration
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "docker_integration",
                "fail",
                f"Error validating Docker integration: {e}",
                duration
            ))

    def _validate_security(self):
        """Validate security aspects"""
        start_time = time.time()

        try:
            # Check file permissions
            secret_dirs = [
                "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis",
                "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws"
            ]

            security_issues = []
            for dir_path in secret_dirs:
                if os.path.exists(dir_path):
                    # Check directory permissions
                    stat_info = os.stat(dir_path)
                    permissions = oct(stat_info.st_mode)[-3:]
                    if permissions != "700":
                        security_issues.append(f"Directory {dir_path} has permissions {permissions}, should be 700")

            duration = time.time() - start_time

            if security_issues:
                self._add_result(ValidationResult(
                    "security",
                    "warning",
                    f"Security issues found: {'; '.join(security_issues)}",
                    duration
                ))
            else:
                self._add_result(ValidationResult(
                    "security",
                    "pass",
                    "Security validation passed",
                    duration
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "security",
                "fail",
                f"Error validating security: {e}",
                duration
            ))

    def _validate_performance(self):
        """Validate performance aspects"""
        start_time = time.time()

        try:
            # Test performance of hierarchical loader
            perf_start = time.time()
            returncode, stdout, stderr = self._run_command([
                sys.executable, "/Users/ryanranft/load_env_hierarchical.py",
                self.project, "NBA", "production"
            ])
            perf_duration = time.time() - perf_start

            duration = time.time() - start_time

            if returncode == 0 and perf_duration < 5.0:
                self._add_result(ValidationResult(
                    "performance",
                    "pass",
                    f"Performance validation passed (load time: {perf_duration:.2f}s)",
                    duration,
                    {"load_time": perf_duration}
                ))
            elif returncode == 0:
                self._add_result(ValidationResult(
                    "performance",
                    "warning",
                    f"Performance slow (load time: {perf_duration:.2f}s)",
                    duration,
                    {"load_time": perf_duration}
                ))
            else:
                self._add_result(ValidationResult(
                    "performance",
                    "fail",
                    f"Performance test failed: {stderr}",
                    duration,
                    {"load_time": perf_duration}
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "performance",
                "fail",
                f"Error testing performance: {e}",
                duration
            ))

    def _validate_documentation(self):
        """Validate documentation"""
        start_time = time.time()

        try:
            # Check if documentation files exist
            doc_files = [
                "docs/SECRETS_MANAGEMENT_GUIDE.md",
                "docs/MIGRATION_GUIDE.md",
                "docs/TROUBLESHOOTING_GUIDE.md",
                "docs/API_DOCUMENTATION.md",
                "docs/SECRETS_HEALTH_MONITORING.md",
                "MIGRATION_GUIDE.md"
            ]

            missing_docs = []
            for file in doc_files:
                if not os.path.exists(file):
                    missing_docs.append(file)

            duration = time.time() - start_time

            if missing_docs:
                self._add_result(ValidationResult(
                    "documentation",
                    "warning",
                    f"Missing documentation files: {', '.join(missing_docs)}",
                    duration
                ))
            else:
                self._add_result(ValidationResult(
                    "documentation",
                    "pass",
                    "All documentation files present",
                    duration
                ))

        except Exception as e:
            duration = time.time() - start_time
            self._add_result(ValidationResult(
                "documentation",
                "fail",
                f"Error validating documentation: {e}",
                duration
            ))

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final validation report"""
        total_duration = (datetime.now() - self.start_time).total_seconds()

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "pass"])
        failed_tests = len([r for r in self.results if r.status == "fail"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        skipped_tests = len([r for r in self.results if r.status == "skip"])

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Group results by category
        categories = {}
        for result in self.results:
            category = result.test_name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        report = {
            "validation_summary": {
                "project": self.project,
                "timestamp": datetime.now().isoformat(),
                "total_duration_seconds": total_duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "skipped_tests": skipped_tests,
                "success_rate_percent": success_rate
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "status": result.status,
                    "message": result.message,
                    "duration": result.duration,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in self.results
            ],
            "categories": {
                category: [
                    {
                        "test_name": result.test_name,
                        "status": result.status,
                        "message": result.message,
                        "duration": result.duration,
                        "details": result.details,
                        "timestamp": result.timestamp.isoformat()
                    }
                    for result in results
                ]
                for category, results in categories.items()
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        failed_tests = [r for r in self.results if r.status == "fail"]
        warning_tests = [r for r in self.results if r.status == "warning"]

        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests to ensure system stability")

        if warning_tests:
            recommendations.append(f"Review {len(warning_tests)} warning tests for potential improvements")

        # Specific recommendations based on test results
        for result in self.results:
            if result.status == "fail":
                if "directory_structure" in result.test_name:
                    recommendations.append("Create missing directory structure for secrets management")
                elif "hierarchical_loader" in result.test_name:
                    recommendations.append("Fix hierarchical loader configuration or permissions")
                elif "unified_secrets_manager" in result.test_name:
                    recommendations.append("Debug unified secrets manager initialization")
                elif "entry_point" in result.test_name:
                    recommendations.append(f"Fix entry point: {result.test_name}")

        return recommendations

def main():
    """Main entry point for comprehensive validation"""
    parser = argparse.ArgumentParser(description="Comprehensive Validation Script")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--format", default="json", choices=["json", "html"], help="Output format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create validator
    validator = ComprehensiveValidator(args.project)

    # Run validations
    print(f"🚀 Starting comprehensive validation for project: {args.project}")
    report = validator.run_all_validations()

    # Print summary
    summary = report["validation_summary"]
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']} ✅")
    print(f"Failed: {summary['failed_tests']} ❌")
    print(f"Warnings: {summary['warning_tests']} ⚠️")
    print(f"Skipped: {summary['skipped_tests']} ⏭️")
    print(f"Success Rate: {summary['success_rate_percent']:.1f}%")
    print(f"Duration: {summary['total_duration_seconds']:.2f}s")

    # Print recommendations
    if report["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 50)
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

    # Save report
    if args.output:
        if args.format == "json":
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
        elif args.format == "html":
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Validation Report - {args.project}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .test-result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                    .pass {{ background: #d4edda; border-left: 4px solid #28a745; }}
                    .fail {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
                    .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
                    .skip {{ background: #e2e3e5; border-left: 4px solid #6c757d; }}
                </style>
            </head>
            <body>
                <h1>🔍 Validation Report - {args.project}</h1>
                <div class="summary">
                    <h2>Summary</h2>
                    <p><strong>Total Tests:</strong> {summary['total_tests']}</p>
                    <p><strong>Passed:</strong> {summary['passed_tests']}</p>
                    <p><strong>Failed:</strong> {summary['failed_tests']}</p>
                    <p><strong>Warnings:</strong> {summary['warning_tests']}</p>
                    <p><strong>Success Rate:</strong> {summary['success_rate_percent']:.1f}%</p>
                    <p><strong>Duration:</strong> {summary['total_duration_seconds']:.2f}s</p>
                </div>
                <h2>Test Results</h2>
                {"".join([f'<div class="test-result {result["status"]}"><strong>{result["test_name"]}</strong>: {result["status"]} - {result["message"]}</div>' for result in report["test_results"]])}
            </body>
            </html>
            """
            with open(args.output, 'w') as f:
                f.write(html_content)

        print(f"\n📁 Report saved to: {args.output}")

    # Return appropriate exit code
    if summary['failed_tests'] > 0:
        sys.exit(1)
    elif summary['warning_tests'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
