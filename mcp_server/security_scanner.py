"""
Security Scanner Module
Scan for common security vulnerabilities and misconfigurations.
"""

import logging
from typing import Dict, Optional, Any, List
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityScanner:
    """Scan for security issues"""

    def __init__(self):
        """Initialize security scanner"""
        self.findings: List[Dict] = []

    def scan_environment_variables(
        self, env_vars: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Scan environment variables for exposed secrets.

        Args:
            env_vars: Environment variables (defaults to os.environ)

        Returns:
            List of findings
        """
        if env_vars is None:
            env_vars = dict(os.environ)

        findings = []
        sensitive_patterns = {
            "api_key": r"(api[_-]?key|apikey)",
            "secret": r"(secret|password|passwd|pwd)",
            "token": r"(token|auth)",
            "credential": r"(credential|cred)",
        }

        for var_name, var_value in env_vars.items():
            for pattern_name, pattern in sensitive_patterns.items():
                if re.search(pattern, var_name, re.IGNORECASE):
                    findings.append(
                        {
                            "severity": "HIGH",
                            "category": "Exposed Secrets",
                            "issue": f"Sensitive variable in environment: {var_name}",
                            "recommendation": "Use AWS Secrets Manager instead",
                        }
                    )

        self.findings.extend(findings)
        return findings

    def scan_sql_injection_risk(self, query_patterns: List[str]) -> List[Dict]:
        """
        Scan for SQL injection vulnerabilities.

        Args:
            query_patterns: SQL query patterns to check

        Returns:
            List of findings
        """
        findings = []

        for query in query_patterns:
            # Check for string concatenation
            if "+" in query or "%" in query or ".format(" in query:
                findings.append(
                    {
                        "severity": "CRITICAL",
                        "category": "SQL Injection",
                        "issue": f"Potential SQL injection: {query[:50]}...",
                        "recommendation": "Use parameterized queries",
                    }
                )

            # Check for unescaped user input
            if "user_input" in query.lower() or "request." in query:
                findings.append(
                    {
                        "severity": "HIGH",
                        "category": "SQL Injection",
                        "issue": f"User input in query: {query[:50]}...",
                        "recommendation": "Validate and sanitize user input",
                    }
                )

        self.findings.extend(findings)
        return findings

    def scan_authentication(self, auth_config: Dict[str, Any]) -> List[Dict]:
        """
        Scan authentication configuration.

        Args:
            auth_config: Authentication configuration

        Returns:
            List of findings
        """
        findings = []

        # Check for weak JWT secret
        jwt_secret = auth_config.get("jwt_secret", "")
        if len(jwt_secret) < 32:
            findings.append(
                {
                    "severity": "CRITICAL",
                    "category": "Weak Authentication",
                    "issue": "JWT secret too short",
                    "recommendation": "Use at least 32 characters for JWT secret",
                }
            )

        # Check token expiration
        token_expiry = auth_config.get("token_expiry_minutes", 0)
        if token_expiry > 1440:  # 24 hours
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "Session Management",
                    "issue": f"Token expiry too long: {token_expiry} minutes",
                    "recommendation": "Reduce token expiry to < 24 hours",
                }
            )

        # Check for missing rate limiting
        if not auth_config.get("rate_limiting_enabled"):
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "Brute Force Protection",
                    "issue": "Rate limiting not enabled",
                    "recommendation": "Enable rate limiting for auth endpoints",
                }
            )

        self.findings.extend(findings)
        return findings

    def scan_api_endpoints(self, endpoints: List[Dict[str, str]]) -> List[Dict]:
        """
        Scan API endpoints for security issues.

        Args:
            endpoints: List of endpoint configurations

        Returns:
            List of findings
        """
        findings = []

        for endpoint in endpoints:
            path = endpoint.get("path", "")
            method = endpoint.get("method", "")
            auth_required = endpoint.get("auth_required", False)

            # Check for unprotected sensitive endpoints
            sensitive_patterns = ["/admin", "/delete", "/update", "/create", "/config"]
            if any(pattern in path.lower() for pattern in sensitive_patterns):
                if not auth_required:
                    findings.append(
                        {
                            "severity": "CRITICAL",
                            "category": "Unauthorized Access",
                            "issue": f"Sensitive endpoint unprotected: {method} {path}",
                            "recommendation": "Require authentication",
                        }
                    )

            # Check for missing HTTPS
            if endpoint.get("protocol") == "http":
                findings.append(
                    {
                        "severity": "HIGH",
                        "category": "Data in Transit",
                        "issue": f"Endpoint using HTTP: {path}",
                        "recommendation": "Use HTTPS for all endpoints",
                    }
                )

        self.findings.extend(findings)
        return findings

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate security scan report"""
        if not self.findings:
            return {
                "status": "PASS",
                "message": "No security issues found",
                "total_findings": 0,
            }

        by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}

        for finding in self.findings:
            severity = finding.get("severity", "MEDIUM")
            by_severity[severity].append(finding)

        return {
            "status": (
                "FAIL" if by_severity["CRITICAL"] or by_severity["HIGH"] else "WARN"
            ),
            "total_findings": len(self.findings),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "critical_issues": by_severity["CRITICAL"],
            "high_issues": by_severity["HIGH"],
            "recommendations": [f["recommendation"] for f in self.findings[:5]],
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("SECURITY SCANNER DEMO")
    print("=" * 80)

    scanner = SecurityScanner()

    # Scan environment variables
    print("\n" + "=" * 80)
    print("SCANNING ENVIRONMENT VARIABLES")
    print("=" * 80)

    test_env = {"API_KEY": "secret123", "DB_PASSWORD": "password", "DEBUG_MODE": "true"}

    env_findings = scanner.scan_environment_variables(test_env)
    print(f"\n❌ Found {len(env_findings)} environment issues")

    # Scan SQL injection
    print("\n" + "=" * 80)
    print("SCANNING SQL INJECTION RISKS")
    print("=" * 80)

    test_queries = [
        "SELECT * FROM users WHERE id = " + "user_input",
        "SELECT * FROM games WHERE season = %s",  # Safe
    ]

    sql_findings = scanner.scan_sql_injection_risk(test_queries)
    print(f"\n❌ Found {len(sql_findings)} SQL injection risks")

    # Scan authentication
    print("\n" + "=" * 80)
    print("SCANNING AUTHENTICATION")
    print("=" * 80)

    test_auth = {
        "jwt_secret": "short",  # Too short
        "token_expiry_minutes": 2880,  # 2 days
        "rate_limiting_enabled": False,
    }

    auth_findings = scanner.scan_authentication(test_auth)
    print(f"\n❌ Found {len(auth_findings)} authentication issues")

    # Scan API endpoints
    print("\n" + "=" * 80)
    print("SCANNING API ENDPOINTS")
    print("=" * 80)

    test_endpoints = [
        {"path": "/api/admin/delete", "method": "DELETE", "auth_required": False},
        {"path": "/api/public/health", "method": "GET", "auth_required": False},
    ]

    api_findings = scanner.scan_api_endpoints(test_endpoints)
    print(f"\n❌ Found {len(api_findings)} API security issues")

    # Generate report
    print("\n" + "=" * 80)
    print("SECURITY SCAN REPORT")
    print("=" * 80)

    report = scanner.generate_security_report()
    print(f"\nStatus: {report['status']}")
    print(f"Total Findings: {report['total_findings']}")
    print(f"\nBy Severity:")
    for severity, count in report["by_severity"].items():
        if count > 0:
            print(f"  {severity}: {count}")

    if report["critical_issues"]:
        print(f"\nCritical Issues ({len(report['critical_issues'])}):")
        for issue in report["critical_issues"][:3]:
            print(f"  - {issue['issue']}")

    print("\n" + "=" * 80)
    print("Security Scanner Demo Complete!")
    print("=" * 80)
