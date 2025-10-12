"""
Security Hardening

Advanced security features and hardening:
- Vulnerability scanning
- Security policies
- Threat detection
- Access controls
- Encryption management
- Security audits

Features:
- Automated security scans
- Policy enforcement
- Threat intelligence
- Security scoring
- Compliance checks
- Incident response

Use Cases:
- Security audits
- Penetration testing
- Vulnerability management
- Compliance validation
- Threat monitoring
"""

import hashlib
import secrets
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


class ThreatType(Enum):
    """Types of security threats"""
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    CSRF = "cross_site_request_forgery"
    BRUTE_FORCE = "brute_force"
    DOS = "denial_of_service"
    DATA_LEAK = "data_leak"
    PRIVILEGE_ESCALATION = "privilege_escalation"


@dataclass
class SecurityFinding:
    """Security vulnerability or issue"""
    finding_id: str
    title: str
    description: str
    severity: SecurityLevel
    category: str
    affected_component: str
    timestamp: datetime = field(default_factory=datetime.now)
    remediation: Optional[str] = None
    cve_id: Optional[str] = None
    false_positive: bool = False


@dataclass
class ThreatEvent:
    """Security threat event"""
    event_id: str
    threat_type: ThreatType
    source_ip: str
    target_resource: str
    timestamp: datetime
    blocked: bool
    severity: SecurityLevel
    details: Dict[str, Any] = field(default_factory=dict)


class InputValidator:
    """Validate and sanitize user inputs"""
    
    # Common attack patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(';.*--)",
        r"(\bDROP\b\s+\bTABLE\b)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*="
    ]
    
    def __init__(self):
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
    
    def check_sql_injection(self, input_string: str) -> bool:
        """Check for SQL injection patterns"""
        for pattern in self.sql_patterns:
            if pattern.search(input_string):
                logger.warning(f"SQL injection detected: {input_string[:50]}")
                return True
        return False
    
    def check_xss(self, input_string: str) -> bool:
        """Check for XSS patterns"""
        for pattern in self.xss_patterns:
            if pattern.search(input_string):
                logger.warning(f"XSS detected: {input_string[:50]}")
                return True
        return False
    
    def sanitize_html(self, input_string: str) -> str:
        """Sanitize HTML input"""
        # Remove dangerous tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_string, flags=re.IGNORECASE)
        sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        # Escape remaining HTML
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized
    
    def validate_input(self, input_string: str, check_sql: bool = True, check_xss: bool = True) -> Dict[str, Any]:
        """Comprehensive input validation"""
        issues = []
        
        if check_sql and self.check_sql_injection(input_string):
            issues.append("SQL injection pattern detected")
        
        if check_xss and self.check_xss(input_string):
            issues.append("XSS pattern detected")
        
        is_safe = len(issues) == 0
        
        return {
            'is_safe': is_safe,
            'issues': issues,
            'sanitized': self.sanitize_html(input_string) if not is_safe else input_string
        }


class PasswordStrengthChecker:
    """Check password strength"""
    
    MIN_LENGTH = 12
    
    def __init__(self):
        # Common passwords to block
        self.common_passwords = set([
            'password', '123456', 'password123', 'admin', 'letmein',
            'welcome', 'monkey', '1234567890', 'qwerty', 'abc123'
        ])
    
    def check_strength(self, password: str) -> Dict[str, Any]:
        """Analyze password strength"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= self.MIN_LENGTH:
            score += 2
        else:
            feedback.append(f"Password should be at least {self.MIN_LENGTH} characters")
        
        # Character variety
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if has_lower:
            score += 1
        if has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1
        
        if not has_lower:
            feedback.append("Add lowercase letters")
        if not has_upper:
            feedback.append("Add uppercase letters")
        if not has_digit:
            feedback.append("Add numbers")
        if not has_special:
            feedback.append("Add special characters")
        
        # Common password check
        if password.lower() in self.common_passwords:
            score = 0
            feedback = ["This is a commonly used password - choose something unique"]
        
        # Repeated characters
        if re.search(r'(.)\1{2,}', password):
            score -= 1
            feedback.append("Avoid repeating characters")
        
        # Sequential characters
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            score -= 1
            feedback.append("Avoid sequential characters")
        
        # Determine strength level
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            'strength': strength,
            'score': max(0, score),
            'max_score': 6,
            'feedback': feedback,
            'is_acceptable': score >= 4
        }
    
    def generate_strong_password(self, length: int = 16) -> str:
        """Generate a strong random password"""
        import string
        
        # Ensure all character types
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation)
        ]
        
        # Fill remaining length
        all_chars = string.ascii_letters + string.digits + string.punctuation
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)


class RateLimitingEnhanced:
    """Enhanced rate limiting with threat detection"""
    
    def __init__(self):
        self.request_counts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, int] = {}
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """Check if identifier exceeds rate limit"""
        
        # Check if blocked
        if identifier in self.blocked_ips:
            return {
                'allowed': False,
                'reason': 'IP blocked',
                'requests_made': 0,
                'limit': max_requests
            }
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Initialize or clean old requests
        if identifier not in self.request_counts:
            self.request_counts[identifier] = []
        
        self.request_counts[identifier] = [
            ts for ts in self.request_counts[identifier]
            if ts > cutoff
        ]
        
        # Add current request
        self.request_counts[identifier].append(now)
        
        request_count = len(self.request_counts[identifier])
        
        # Check limit
        if request_count > max_requests:
            # Mark as suspicious
            self.suspicious_ips[identifier] = self.suspicious_ips.get(identifier, 0) + 1
            
            # Block if repeatedly exceeding
            if self.suspicious_ips[identifier] >= 3:
                self.blocked_ips.add(identifier)
                logger.warning(f"Blocked IP for rate limit violations: {identifier}")
            
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'requests_made': request_count,
                'limit': max_requests
            }
        
        return {
            'allowed': True,
            'requests_made': request_count,
            'limit': max_requests,
            'remaining': max_requests - request_count
        }
    
    def unblock_ip(self, identifier: str) -> bool:
        """Unblock an IP"""
        if identifier in self.blocked_ips:
            self.blocked_ips.remove(identifier)
            if identifier in self.suspicious_ips:
                del self.suspicious_ips[identifier]
            logger.info(f"Unblocked IP: {identifier}")
            return True
        return False


class SecurityScanner:
    """Scan for security vulnerabilities"""
    
    def __init__(self):
        self.findings: List[SecurityFinding] = []
        self.next_finding_id = 0
    
    def scan_dependencies(self, dependencies: List[Dict[str, str]]) -> List[SecurityFinding]:
        """Scan dependencies for known vulnerabilities"""
        findings = []
        
        # Simulated vulnerability database
        known_vulns = {
            'requests': {'version': '2.25.0', 'cve': 'CVE-2021-33503', 'severity': SecurityLevel.HIGH},
            'urllib3': {'version': '1.26.4', 'cve': 'CVE-2021-28363', 'severity': SecurityLevel.MEDIUM}
        }
        
        for dep in dependencies:
            package = dep['name']
            version = dep['version']
            
            if package in known_vulns:
                vuln = known_vulns[package]
                if version == vuln['version']:
                    finding = self._create_finding(
                        title=f"Vulnerable dependency: {package}",
                        description=f"Package {package} version {version} has known vulnerability",
                        severity=vuln['severity'],
                        category="dependency",
                        affected_component=package,
                        cve_id=vuln['cve'],
                        remediation=f"Upgrade {package} to latest version"
                    )
                    findings.append(finding)
        
        return findings
    
    def scan_configurations(self, configs: Dict[str, Any]) -> List[SecurityFinding]:
        """Scan configuration for security issues"""
        findings = []
        
        # Check for insecure configurations
        if configs.get('DEBUG', False):
            findings.append(self._create_finding(
                title="Debug mode enabled in production",
                description="DEBUG=True exposes sensitive information",
                severity=SecurityLevel.HIGH,
                category="configuration",
                affected_component="settings",
                remediation="Set DEBUG=False in production"
            ))
        
        if not configs.get('USE_SSL', True):
            findings.append(self._create_finding(
                title="SSL not enforced",
                description="Connections are not encrypted",
                severity=SecurityLevel.CRITICAL,
                category="configuration",
                affected_component="network",
                remediation="Enable SSL/TLS for all connections"
            ))
        
        return findings
    
    def _create_finding(
        self,
        title: str,
        description: str,
        severity: SecurityLevel,
        category: str,
        affected_component: str,
        cve_id: Optional[str] = None,
        remediation: Optional[str] = None
    ) -> SecurityFinding:
        """Create a security finding"""
        finding = SecurityFinding(
            finding_id=f"SEC-{self.next_finding_id:04d}",
            title=title,
            description=description,
            severity=severity,
            category=category,
            affected_component=affected_component,
            cve_id=cve_id,
            remediation=remediation
        )
        
        self.next_finding_id += 1
        self.findings.append(finding)
        
        return finding
    
    def get_findings_by_severity(self, min_severity: SecurityLevel = SecurityLevel.LOW) -> List[SecurityFinding]:
        """Get findings above minimum severity"""
        return [
            f for f in self.findings
            if f.severity.value >= min_severity.value and not f.false_positive
        ]
    
    def get_security_score(self) -> Dict[str, Any]:
        """Calculate overall security score"""
        total_score = 100
        
        # Deduct points based on severity
        deductions = {
            SecurityLevel.CRITICAL: 25,
            SecurityLevel.HIGH: 15,
            SecurityLevel.MEDIUM: 5,
            SecurityLevel.LOW: 2
        }
        
        for finding in self.findings:
            if not finding.false_positive:
                total_score -= deductions.get(finding.severity, 0)
        
        total_score = max(0, total_score)
        
        # Grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 70:
            grade = "C"
        elif total_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            'score': total_score,
            'grade': grade,
            'total_findings': len(self.findings),
            'critical_findings': len([f for f in self.findings if f.severity == SecurityLevel.CRITICAL]),
            'high_findings': len([f for f in self.findings if f.severity == SecurityLevel.HIGH])
        }


class SecurityHardening:
    """Main security hardening orchestrator"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.password_checker = PasswordStrengthChecker()
        self.rate_limiter = RateLimitingEnhanced()
        self.scanner = SecurityScanner()
        self.threat_events: List[ThreatEvent] = []
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        
        # Scan dependencies (example)
        deps = [
            {'name': 'requests', 'version': '2.25.0'},
            {'name': 'boto3', 'version': '1.18.0'}
        ]
        dep_findings = self.scanner.scan_dependencies(deps)
        
        # Scan configurations (example)
        configs = {
            'DEBUG': False,
            'USE_SSL': True
        }
        config_findings = self.scanner.scan_configurations(configs)
        
        # Get security score
        security_score = self.scanner.get_security_score()
        
        return {
            'security_score': security_score,
            'dependency_findings': len(dep_findings),
            'config_findings': len(config_findings),
            'total_findings': len(self.scanner.findings),
            'critical_findings': [
                f for f in self.scanner.findings
                if f.severity == SecurityLevel.CRITICAL
            ],
            'threat_events': len(self.threat_events)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Security Hardening Demo ===\n")
    
    # Create hardening
    security = SecurityHardening()
    
    # Input validation
    print("--- Input Validation ---\n")
    
    malicious_inputs = [
        "'; DROP TABLE users;--",
        "<script>alert('XSS')</script>",
        "normal input"
    ]
    
    for input_str in malicious_inputs:
        result = security.input_validator.validate_input(input_str)
        safe_status = "✓ SAFE" if result['is_safe'] else "✗ UNSAFE"
        print(f"{safe_status}: {input_str[:50]}")
        if not result['is_safe']:
            print(f"  Issues: {', '.join(result['issues'])}")
    
    # Password strength
    print("\n--- Password Strength ---\n")
    
    passwords = ["password123", "MyP@ssw0rd!2024Secure"]
    
    for pwd in passwords:
        result = security.password_checker.check_strength(pwd)
        print(f"Password: {'*' * len(pwd)}")
        print(f"  Strength: {result['strength'].upper()}")
        print(f"  Score: {result['score']}/{result['max_score']}")
        if result['feedback']:
            print(f"  Feedback: {', '.join(result['feedback'])}")
    
    # Run security audit
    print("\n--- Security Audit ---\n")
    audit = security.run_security_audit()
    
    print(f"Security Score: {audit['security_score']['score']}/100 (Grade: {audit['security_score']['grade']})")
    print(f"Total Findings: {audit['total_findings']}")
    print(f"  Critical: {audit['security_score']['critical_findings']}")
    print(f"  High: {audit['security_score']['high_findings']}")
    
    print("\n=== Demo Complete ===")

