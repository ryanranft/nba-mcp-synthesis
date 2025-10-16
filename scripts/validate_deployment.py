#!/usr/bin/env python3

"""
NBA MCP Synthesis - Deployment Validation Suite

This script performs comprehensive validation of the production deployment
including infrastructure, secrets, application, database, S3, monitoring,
and alerting components.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    status: str  # 'PASS', 'FAIL', 'WARN', 'SKIP'
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None

@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: List[ValidationResult]
    summary: str

class DeploymentValidator:
    """Main deployment validation class"""

    def __init__(self, verbose: bool = False, namespace: str = "nba-mcp-synthesis"):
        self.verbose = verbose
        self.namespace = namespace
        self.results: List[ValidationResult] = []
        self.start_time = time.time()

    def log(self, message: str, color: str = Colors.BLUE):
        """Log message with color"""
        if self.verbose:
            print(f"{color}[Validator]{Colors.NC} {message}")

    def log_success(self, message: str):
        """Log success message"""
        self.log(f"✓ {message}", Colors.GREEN)

    def log_warning(self, message: str):
        """Log warning message"""
        self.log(f"⚠ {message}", Colors.YELLOW)

    def log_error(self, message: str):
        """Log error message"""
        self.log(f"✗ {message}", Colors.RED)

    def add_result(self, name: str, status: str, message: str,
                   details: Optional[Dict[str, Any]] = None, duration_ms: Optional[int] = None):
        """Add validation result"""
        result = ValidationResult(
            name=name,
            status=status,
            message=message,
            details=details,
            duration_ms=duration_ms
        )
        self.results.append(result)

        if status == 'PASS':
            self.log_success(f"{name}: {message}")
        elif status == 'FAIL':
            self.log_error(f"{name}: {message}")
        elif status == 'WARN':
            self.log_warning(f"{name}: {message}")
        else:
            self.log(f"{name}: {message}", Colors.CYAN)

    def run_command(self, command: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def validate_infrastructure(self):
        """Validate EKS cluster and infrastructure"""
        self.log("Validating infrastructure...")

        # Check EKS cluster
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(['kubectl', 'cluster-info'])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            self.add_result(
                "EKS Cluster Access",
                "PASS",
                "Successfully connected to EKS cluster",
                {"output": stdout.strip()},
                duration_ms
            )
        else:
            self.add_result(
                "EKS Cluster Access",
                "FAIL",
                f"Failed to connect to EKS cluster: {stderr}",
                {"error": stderr},
                duration_ms
            )
            return

        # Check nodes
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(['kubectl', 'get', 'nodes'])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            lines = stdout.strip().split('\n')[1:]  # Skip header
            ready_nodes = [line for line in lines if 'Ready' in line]

            if len(ready_nodes) > 0:
                self.add_result(
                    "Node Status",
                    "PASS",
                    f"Found {len(ready_nodes)} ready nodes",
                    {"ready_nodes": len(ready_nodes), "total_nodes": len(lines)},
                    duration_ms
                )
            else:
                self.add_result(
                    "Node Status",
                    "FAIL",
                    "No ready nodes found",
                    {"total_nodes": len(lines)},
                    duration_ms
                )
        else:
            self.add_result(
                "Node Status",
                "FAIL",
                f"Failed to get node status: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check namespace
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(['kubectl', 'get', 'namespace', self.namespace])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            self.add_result(
                "Namespace",
                "PASS",
                f"Namespace '{self.namespace}' exists",
                {},
                duration_ms
            )
        else:
            self.add_result(
                "Namespace",
                "FAIL",
                f"Namespace '{self.namespace}' not found",
                {"error": stderr},
                duration_ms
            )

    def validate_secrets(self):
        """Validate AWS Secrets Manager and External Secrets"""
        self.log("Validating secrets...")

        # Check AWS Secrets Manager access
        start_time = time.time()
        try:
            secrets_client = boto3.client('secretsmanager')
            response = secrets_client.list_secrets()
            duration_ms = int((time.time() - start_time) * 1000)

            nba_secrets = [s for s in response['SecretList'] if 'nba-mcp-synthesis' in s['Name']]

            if len(nba_secrets) > 0:
                self.add_result(
                    "AWS Secrets Manager",
                    "PASS",
                    f"Found {len(nba_secrets)} NBA MCP secrets",
                    {"secrets": [s['Name'] for s in nba_secrets]},
                    duration_ms
                )
            else:
                self.add_result(
                    "AWS Secrets Manager",
                    "WARN",
                    "No NBA MCP secrets found",
                    {},
                    duration_ms
                )

        except NoCredentialsError:
            self.add_result(
                "AWS Secrets Manager",
                "FAIL",
                "AWS credentials not configured",
                {},
                int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            self.add_result(
                "AWS Secrets Manager",
                "FAIL",
                f"Failed to access AWS Secrets Manager: {str(e)}",
                {"error": str(e)},
                int((time.time() - start_time) * 1000)
            )

        # Check External Secrets Operator
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'pods', '-n', 'external-secrets-system'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'Running' in stdout:
                self.add_result(
                    "External Secrets Operator",
                    "PASS",
                    "External Secrets Operator is running",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "External Secrets Operator",
                    "WARN",
                    "External Secrets Operator may not be ready",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "External Secrets Operator",
                "FAIL",
                f"Failed to check External Secrets Operator: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check ExternalSecret resources
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'externalsecrets', '-n', self.namespace
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if stdout.strip():
                self.add_result(
                    "ExternalSecret Resources",
                    "PASS",
                    "ExternalSecret resources found",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "ExternalSecret Resources",
                    "WARN",
                    "No ExternalSecret resources found",
                    {},
                    duration_ms
                )
        else:
            self.add_result(
                "ExternalSecret Resources",
                "FAIL",
                f"Failed to get ExternalSecret resources: {stderr}",
                {"error": stderr},
                duration_ms
            )

    def validate_application(self):
        """Validate application deployment"""
        self.log("Validating application...")

        # Check deployment
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'deployment', '-n', self.namespace
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'nba-mcp-synthesis' in stdout:
                self.add_result(
                    "Application Deployment",
                    "PASS",
                    "NBA MCP Synthesis deployment found",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "Application Deployment",
                    "FAIL",
                    "NBA MCP Synthesis deployment not found",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "Application Deployment",
                "FAIL",
                f"Failed to get deployments: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check pods
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'pods', '-n', self.namespace, '-l', 'app=nba-mcp-synthesis'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            lines = stdout.strip().split('\n')[1:]  # Skip header
            running_pods = [line for line in lines if 'Running' in line]

            if len(running_pods) > 0:
                self.add_result(
                    "Application Pods",
                    "PASS",
                    f"Found {len(running_pods)} running pods",
                    {"running_pods": len(running_pods), "total_pods": len(lines)},
                    duration_ms
                )
            else:
                self.add_result(
                    "Application Pods",
                    "FAIL",
                    "No running pods found",
                    {"total_pods": len(lines)},
                    duration_ms
                )
        else:
            self.add_result(
                "Application Pods",
                "FAIL",
                f"Failed to get pods: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check service
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'service', '-n', self.namespace
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'nba-mcp-synthesis-service' in stdout:
                self.add_result(
                    "Application Service",
                    "PASS",
                    "NBA MCP Synthesis service found",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "Application Service",
                    "FAIL",
                    "NBA MCP Synthesis service not found",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "Application Service",
                "FAIL",
                f"Failed to get services: {stderr}",
                {"error": stderr},
                duration_ms
            )

    def validate_health_endpoints(self):
        """Validate application health endpoints"""
        self.log("Validating health endpoints...")

        # Get service endpoint
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'service', 'nba-mcp-synthesis-service', '-n', self.namespace, '-o', 'jsonpath={.spec.clusterIP}'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code != 0:
            self.add_result(
                "Service Endpoint",
                "FAIL",
                f"Failed to get service endpoint: {stderr}",
                {"error": stderr},
                duration_ms
            )
            return

        service_ip = stdout.strip()

        # Test health endpoint
        start_time = time.time()
        try:
            # Port forward to test health endpoint
            port_forward_cmd = [
                'kubectl', 'port-forward', f'service/nba-mcp-synthesis-service',
                '8080:80', '-n', self.namespace
            ]

            # Start port forward in background
            pf_process = subprocess.Popen(port_forward_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)  # Wait for port forward to establish

            # Test health endpoint
            response = requests.get('http://localhost:8080/health', timeout=10)
            duration_ms = int((time.time() - start_time) * 1000)

            # Clean up port forward
            pf_process.terminate()
            pf_process.wait()

            if response.status_code == 200:
                self.add_result(
                    "Health Endpoint",
                    "PASS",
                    "Health endpoint responding correctly",
                    {"status_code": response.status_code, "response": response.text},
                    duration_ms
                )
            else:
                self.add_result(
                    "Health Endpoint",
                    "FAIL",
                    f"Health endpoint returned status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text},
                    duration_ms
                )

        except requests.exceptions.RequestException as e:
            self.add_result(
                "Health Endpoint",
                "FAIL",
                f"Failed to connect to health endpoint: {str(e)}",
                {"error": str(e)},
                int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            self.add_result(
                "Health Endpoint",
                "FAIL",
                f"Unexpected error testing health endpoint: {str(e)}",
                {"error": str(e)},
                int((time.time() - start_time) * 1000)
            )

        # Test metrics endpoint
        start_time = time.time()
        try:
            # Port forward to test metrics endpoint
            port_forward_cmd = [
                'kubectl', 'port-forward', f'service/nba-mcp-synthesis-service',
                '9090:9090', '-n', self.namespace
            ]

            # Start port forward in background
            pf_process = subprocess.Popen(port_forward_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)  # Wait for port forward to establish

            # Test metrics endpoint
            response = requests.get('http://localhost:9090/metrics', timeout=10)
            duration_ms = int((time.time() - start_time) * 1000)

            # Clean up port forward
            pf_process.terminate()
            pf_process.wait()

            if response.status_code == 200 and 'nba_mcp' in response.text:
                self.add_result(
                    "Metrics Endpoint",
                    "PASS",
                    "Metrics endpoint responding with NBA MCP metrics",
                    {"status_code": response.status_code, "metrics_count": len(response.text.split('\n'))},
                    duration_ms
                )
            else:
                self.add_result(
                    "Metrics Endpoint",
                    "WARN",
                    f"Metrics endpoint returned status {response.status_code}",
                    {"status_code": response.status_code},
                    duration_ms
                )

        except requests.exceptions.RequestException as e:
            self.add_result(
                "Metrics Endpoint",
                "WARN",
                f"Failed to connect to metrics endpoint: {str(e)}",
                {"error": str(e)},
                int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            self.add_result(
                "Metrics Endpoint",
                "WARN",
                f"Unexpected error testing metrics endpoint: {str(e)}",
                {"error": str(e)},
                int((time.time() - start_time) * 1000)
            )

    def validate_monitoring(self):
        """Validate monitoring stack"""
        self.log("Validating monitoring...")

        # Check Prometheus
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'app.kubernetes.io/name=prometheus'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'Running' in stdout:
                self.add_result(
                    "Prometheus",
                    "PASS",
                    "Prometheus is running",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "Prometheus",
                    "WARN",
                    "Prometheus may not be ready",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "Prometheus",
                "FAIL",
                f"Failed to check Prometheus: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check Grafana
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'app.kubernetes.io/name=grafana'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'Running' in stdout:
                self.add_result(
                    "Grafana",
                    "PASS",
                    "Grafana is running",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "Grafana",
                    "WARN",
                    "Grafana may not be ready",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "Grafana",
                "FAIL",
                f"Failed to check Grafana: {stderr}",
                {"error": stderr},
                duration_ms
            )

        # Check Alertmanager
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'app.kubernetes.io/name=alertmanager'
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'Running' in stdout:
                self.add_result(
                    "Alertmanager",
                    "PASS",
                    "Alertmanager is running",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "Alertmanager",
                    "WARN",
                    "Alertmanager may not be ready",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "Alertmanager",
                "FAIL",
                f"Failed to check Alertmanager: {stderr}",
                {"error": stderr},
                duration_ms
            )

    def validate_alerting(self):
        """Validate alerting configuration"""
        self.log("Validating alerting...")

        # Check ServiceMonitor
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command([
            'kubectl', 'get', 'servicemonitor', '-n', self.namespace
        ])
        duration_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            if 'nba-mcp-synthesis' in stdout:
                self.add_result(
                    "ServiceMonitor",
                    "PASS",
                    "NBA MCP Synthesis ServiceMonitor found",
                    {},
                    duration_ms
                )
            else:
                self.add_result(
                    "ServiceMonitor",
                    "WARN",
                    "NBA MCP Synthesis ServiceMonitor not found",
                    {"output": stdout},
                    duration_ms
                )
        else:
            self.add_result(
                "ServiceMonitor",
                "FAIL",
                f"Failed to get ServiceMonitor: {stderr}",
                {"error": stderr},
                duration_ms
            )

    def generate_report(self) -> ValidationReport:
        """Generate validation report"""
        total_checks = len(self.results)
        passed = len([r for r in self.results if r.status == 'PASS'])
        failed = len([r for r in self.results if r.status == 'FAIL'])
        warnings = len([r for r in self.results if r.status == 'WARN'])
        skipped = len([r for r in self.results if r.status == 'SKIP'])

        # Generate summary
        if failed == 0 and warnings == 0:
            summary = "All validations passed successfully"
        elif failed == 0:
            summary = f"Validation completed with {warnings} warnings"
        else:
            summary = f"Validation failed with {failed} failures and {warnings} warnings"

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_checks=total_checks,
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=self.results,
            summary=summary
        )

    def print_summary(self, report: ValidationReport):
        """Print validation summary"""
        print(f"\n{Colors.PURPLE}{'='*60}{Colors.NC}")
        print(f"{Colors.PURPLE}NBA MCP Synthesis - Deployment Validation Report{Colors.NC}")
        print(f"{Colors.PURPLE}{'='*60}{Colors.NC}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Checks: {report.total_checks}")
        print(f"Passed: {Colors.GREEN}{report.passed}{Colors.NC}")
        print(f"Failed: {Colors.RED}{report.failed}{Colors.NC}")
        print(f"Warnings: {Colors.YELLOW}{report.warnings}{Colors.NC}")
        print(f"Skipped: {Colors.CYAN}{report.skipped}{Colors.NC}")
        print(f"\nSummary: {report.summary}")

        if report.failed > 0:
            print(f"\n{Colors.RED}Failed Checks:{Colors.NC}")
            for result in report.results:
                if result.status == 'FAIL':
                    print(f"  ✗ {result.name}: {result.message}")

        if report.warnings > 0:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.NC}")
            for result in report.results:
                if result.status == 'WARN':
                    print(f"  ⚠ {result.name}: {result.message}")

    def save_report(self, report: ValidationReport, output_file: str):
        """Save validation report to file"""
        report_data = asdict(report)

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.log_success(f"Validation report saved to {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate NBA MCP Synthesis deployment')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-n', '--namespace', default='nba-mcp-synthesis', help='Kubernetes namespace')
    parser.add_argument('-o', '--output', help='Output file for validation report')
    parser.add_argument('--skip-infrastructure', action='store_true', help='Skip infrastructure validation')
    parser.add_argument('--skip-secrets', action='store_true', help='Skip secrets validation')
    parser.add_argument('--skip-application', action='store_true', help='Skip application validation')
    parser.add_argument('--skip-monitoring', action='store_true', help='Skip monitoring validation')

    args = parser.parse_args()

    validator = DeploymentValidator(verbose=args.verbose, namespace=args.namespace)

    try:
        print(f"{Colors.BLUE}Starting NBA MCP Synthesis deployment validation...{Colors.NC}")

        # Run validations
        if not args.skip_infrastructure:
            validator.validate_infrastructure()

        if not args.skip_secrets:
            validator.validate_secrets()

        if not args.skip_application:
            validator.validate_application()
            validator.validate_health_endpoints()

        if not args.skip_monitoring:
            validator.validate_monitoring()
            validator.validate_alerting()

        # Generate and display report
        report = validator.generate_report()
        validator.print_summary(report)

        # Save report if requested
        if args.output:
            validator.save_report(report, args.output)

        # Exit with appropriate code
        if report.failed > 0:
            print(f"\n{Colors.RED}Validation failed with {report.failed} failures{Colors.NC}")
            sys.exit(1)
        elif report.warnings > 0:
            print(f"\n{Colors.YELLOW}Validation completed with {report.warnings} warnings{Colors.NC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.GREEN}All validations passed successfully{Colors.NC}")
            sys.exit(0)

    except KeyboardInterrupt:
        validator.log_warning("Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        validator.log_error(f"Validation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()