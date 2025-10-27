# Data Validation Security

**Phase 10A Week 2 - Agent 4 - Phase 5**
**Created**: 2025-10-25
**Status**: Production Ready

Security considerations and best practices for NBA MCP data validation infrastructure.

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Security Controls](#security-controls)
4. [Input Validation](#input-validation)
5. [Resource Limits](#resource-limits)
6. [Data Privacy](#data-privacy)
7. [Dependency Security](#dependency-security)
8. [Best Practices](#best-practices)
9. [Compliance](#compliance)
10. [Incident Response](#incident-response)

---

## Security Overview

The data validation system implements defense-in-depth security:

- **Input validation and sanitization**: Prevents malicious or malformed data from causing issues
- **Resource limit enforcement**: Protects against resource exhaustion attacks
- **Access control integration**: RBAC-ready architecture for authorization
- **Data privacy protection**: PII masking and sensitive data handling
- **Secure dependency management**: Regular security audits and updates

### Security Testing

Comprehensive security test suite: `tests/security/test_validation_security.py`

- Input validation tests (malformed data, extreme values, type violations)
- Resource limit tests (large payloads, dataset size limits)
- Data privacy tests (PII masking, sensitive data handling)
- Error handling tests (graceful degradation, exception recovery)

---

## Threat Model

### Potential Threats

#### 1. Malicious Input Data

**Threats:**
- Malformed data causing crashes or undefined behavior
- Extreme values (inf, nan, very large numbers) triggering errors
- Type confusion attacks exploiting weak type checking
- SQL injection if database operations are involved
- Path traversal in file operations

**Likelihood:** Medium
**Impact:** Medium to High
**Mitigation:** Input validation, type checking, sanitization

#### 2. Resource Exhaustion (DoS)

**Threats:**
- Very large datasets consuming all available memory
- Infinite loops in validation logic
- Excessive CPU usage through algorithmic complexity attacks
- Disk space exhaustion through logging or caching

**Likelihood:** Medium
**Impact:** High
**Mitigation:** Resource limits, timeouts, monitoring

#### 3. Unauthorized Access

**Threats:**
- Bypassing RBAC checks to execute unauthorized operations
- Accessing sensitive validation results without permission
- Privilege escalation through validation endpoints
- Session hijacking or token theft

**Likelihood:** Low to Medium
**Impact:** High
**Mitigation:** RBAC integration, authentication, audit logging

#### 4. Data Privacy Violations

**Threats:**
- PII exposure in logs, reports, or error messages
- Sensitive data leaking through validation output
- Unencrypted data transmission
- Data exfiltration through validation results

**Likelihood:** Medium
**Impact:** Critical
**Mitigation:** PII masking, encryption, data minimization

---

## Security Controls

### 1. Input Validation

**Implementation:**

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline

# Always validate input types
def validate_input(df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be pandas DataFrame")

    # Check for empty data
    if df.empty:
        raise ValueError("DataFrame is empty")

    return True

# Handle extreme values
df = df.replace([np.inf, -np.inf], np.nan)

# Validate dataset size
MAX_ROWS = 1_000_000
if len(df) > MAX_ROWS:
    raise ValueError(f"Dataset too large: {len(df)} > {MAX_ROWS}")
```

**Coverage:**
- Type checking on all inputs
- Range validation for numeric values
- Graceful handling of malformed data
- Null/None value handling
- Special character sanitization

**Tests:** `tests/security/test_validation_security.py::TestInputValidation`

---

### 2. Resource Limits

**Enforced Limits:**

| Resource | Limit | Configurable |
|----------|-------|-------------|
| Maximum dataset size | 1M rows | Yes |
| Maximum memory usage | 2 GB per validation | Yes |
| Maximum columns | 1000 | Yes |
| Timeout | 120 seconds | Yes |

**Configuration:**

```yaml
# config/validation_limits.yaml
resource_limits:
  max_rows: 1_000_000
  max_memory_mb: 2048
  timeout_seconds: 120
  max_columns: 1000
  max_cell_size_kb: 1024
```

**Implementation:**

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    """Context manager for operation timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation exceeded {seconds} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Usage
with timeout_context(120):
    result = pipeline.validate(large_df, 'player_stats')
```

**Tests:** `tests/security/test_validation_security.py::TestResourceLimits`

---

### 3. Authorization (RBAC Integration)

**Architecture:**

The validation pipeline is designed to integrate with the existing RBAC system:

```python
from mcp_server.rbac import RBACManager

def validate_with_rbac(df, dataset_type, user_id, operation='validation:execute'):
    """Validate data with RBAC permission check"""
    rbac = RBACManager()

    # Check permission
    if not rbac.check_permission(user_id, operation):
        raise PermissionError(f"User {user_id} not authorized for {operation}")

    # Log access attempt
    rbac.log_access(user_id, operation, dataset_type)

    # Execute validation
    pipeline = DataValidationPipeline()
    return pipeline.validate(df, dataset_type)
```

**Permissions:**

- `validation:execute` - Execute validation pipeline
- `validation:view` - View validation results
- `validation:configure` - Modify validation configuration
- `validation:admin` - Full validation system access

**Audit Logging:**

All validation operations should be logged:

```python
logger.info(
    "Validation executed",
    extra={
        'user_id': user_id,
        'dataset_type': dataset_type,
        'rows': len(df),
        'result': result.current_stage,
        'duration_ms': duration,
    }
)
```

---

### 4. Data Privacy

**PII Protection:**

```python
# Bad - exposes data
logger.error(f"Validation failed for row: {row}")

# Good - no data exposure
logger.error(f"Validation failed for row {row_index}, column '{col_name}'")

# Better - with context but no PII
logger.error(
    "Validation failed",
    extra={
        'row_index': row_index,
        'column': col_name,
        'rule': rule_name,
        'issue_type': 'missing_value'
    }
)
```

**Sensitive Field Handling:**

```python
# Define sensitive fields
SENSITIVE_FIELDS = ['ssn', 'password', 'api_key', 'email', 'phone']

def mask_sensitive_fields(df, sensitive_fields=SENSITIVE_FIELDS):
    """Mask sensitive fields in DataFrame"""
    df_masked = df.copy()
    for field in sensitive_fields:
        if field in df_masked.columns:
            df_masked[field] = '***REDACTED***'
    return df_masked

# Use before logging or reporting
df_safe = mask_sensitive_fields(df)
logger.info(f"Profiling dataset: {df_safe.head()}")
```

**Data Minimization:**

- Only collect and validate necessary fields
- Don't store validation data longer than needed
- Aggregate results rather than individual records
- Use column names and statistics, not raw values

**Tests:** `tests/security/test_validation_security.py::TestDataPrivacy`

---

## Dependency Security

### Security Audits

**Run regularly:**

```bash
# Using safety
pip install safety
safety check --json

# Using pip-audit
pip install pip-audit
pip-audit

# Using Snyk
snyk test --file=requirements.txt
```

**Schedule:** Weekly automated scans, monthly manual review

### Current Dependencies

**Core dependencies:**

- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `scikit-learn>=1.3.0` - ML algorithms (outlier detection)
- `great-expectations>=0.18.0` - Data quality (optional)

**Security considerations:**

- **pandas**: Monitor CVEs for pickle deserialization vulnerabilities
- **numpy**: Watch for buffer overflow issues in array operations
- **scikit-learn**: Generally secure, minimal attack surface
- **great-expectations**: Review SQLAlchemy usage if database features used

### Vulnerability Response

**Process:**

1. **Alert**: Automated security scan detects vulnerability
2. **Assess**: Determine if vulnerability affects our usage
3. **Patch**: Update dependency or apply workaround
4. **Test**: Run full test suite to ensure compatibility
5. **Deploy**: Deploy patched version
6. **Document**: Record in security log

---

## Best Practices

### 1. Least Privilege

- Run validation services with minimal system permissions
- Don't run as root/admin
- Use dedicated service accounts with limited scope
- Restrict file system access to necessary directories only

### 2. Secure Configuration

```python
# Bad - hardcoded secrets
DB_PASSWORD = "secret123"

# Good - environment variables
import os
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# Better - secrets manager
from mcp_server.secrets_manager import SecretsManager
secrets = SecretsManager()
DB_PASSWORD = secrets.get_secret('validation/db_password')
```

**Configuration checklist:**

- [ ] No secrets in code or config files
- [ ] Use environment variables or vault for secrets
- [ ] Encrypt configuration files if they contain sensitive data
- [ ] Use encrypted connections (TLS) for databases and APIs
- [ ] Rotate credentials regularly

### 3. Logging Security

**What to log:**

- Authentication/authorization attempts (success and failure)
- Validation operations (dataset type, size, duration)
- Errors and exceptions
- Resource usage (memory, CPU)
- Configuration changes

**What NOT to log:**

- PII (names, emails, SSNs, etc.)
- Passwords or API keys
- Full dataset contents
- Sensitive business data

**Log management:**

```python
import logging
from logging.handlers import RotatingFileHandler

# Rotate logs to prevent disk filling
handler = RotatingFileHandler(
    'validation.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
```

### 4. Monitoring and Alerting

**Security events to monitor:**

- Failed authentication attempts (> 5 per minute)
- Unusual validation patterns (very large datasets, frequent errors)
- Resource exhaustion (high memory/CPU usage)
- Unauthorized access attempts
- Dependency vulnerabilities detected

**Alert thresholds:**

```yaml
alerts:
  failed_auth_rate: 5 per minute
  memory_usage: 80% of limit
  error_rate: 10% of operations
  validation_duration: 90th percentile > 60s
```

---

## Compliance

### GDPR (General Data Protection Regulation)

**Right to be forgotten:**
- Validation is transient - data not stored permanently
- Logs can be purged on request
- No persistent storage of personal data

**Data minimization:**
- Only validate fields necessary for business logic
- Don't collect unnecessary PII
- Aggregate results rather than storing individual records

**Transparency:**
- All validation activities logged
- Users can request validation history
- Clear documentation of data processing

### SOC 2 (Service Organization Control 2)

**Access controls:**
- RBAC integration ensures proper authorization
- Audit logging of all operations
- Regular access reviews

**Security:**
- Encryption in transit (TLS for API calls)
- Encryption at rest (if results are stored)
- Regular security audits and penetration testing

**Availability:**
- Resource limits prevent DoS
- Graceful degradation under load
- Health checks and monitoring

---

## Incident Response

### Security Incident Procedure

#### 1. Detect

**Monitoring systems:**
- Security scan alerts
- Unusual traffic patterns
- Error rate spikes
- Resource exhaustion

#### 2. Contain

**Immediate actions:**
- Isolate affected systems
- Disable compromised accounts
- Block malicious IPs
- Enable additional logging

#### 3. Investigate

**Analysis:**
- Review logs for attack vector
- Determine scope of breach
- Identify affected data/systems
- Document timeline

#### 4. Remediate

**Resolution:**
- Apply security patches
- Update dependencies
- Fix vulnerable code
- Restore from clean backups if needed

#### 5. Document

**Incident report:**
- What happened
- When it happened
- How it was detected
- Actions taken
- Lessons learned

#### 6. Learn

**Post-incident:**
- Update security procedures
- Add tests to prevent recurrence
- Train team on new threats
- Review and improve monitoring

---

## Security Checklist

### Pre-Deployment

- [ ] All security tests passing
- [ ] Input validation on all external data
- [ ] Resource limits configured and enforced
- [ ] RBAC integration tested (if applicable)
- [ ] PII masking implemented in logs
- [ ] Dependencies scanned for vulnerabilities
- [ ] Secrets stored securely (not in code)
- [ ] TLS enabled for data transmission
- [ ] Security logging enabled
- [ ] Monitoring and alerting configured

### Operational

- [ ] Regular security scans (weekly)
- [ ] Dependency updates (monthly)
- [ ] Access reviews (quarterly)
- [ ] Penetration testing (annually)
- [ ] Incident response plan tested (annually)
- [ ] Security training for team (annually)

### Continuous

- [ ] Monitor security alerts
- [ ] Review access logs weekly
- [ ] Track failed authentication attempts
- [ ] Monitor resource usage trends
- [ ] Update threat model as system evolves

---

## Security Contact

**For security issues:**
- Email: security@nba-mcp.example.com
- PagerDuty: Escalate to security team
- Slack: #security-incidents

**Responsible disclosure:**
- Report vulnerabilities privately
- Allow 90 days for remediation
- Coordinate public disclosure

---

## Appendix: Security Test Coverage

### Test Classes

1. **TestInputValidation** - Malformed data, extreme values, type violations
2. **TestResourceLimits** - Large payloads, memory efficiency
3. **TestDataPrivacy** - PII masking, sensitive data handling
4. **TestInputSanitization** - SQL injection, special characters
5. **TestErrorHandling** - Graceful degradation, exception recovery
6. **TestIntegrityAndConsistency** - Referential integrity, temporal consistency

### Running Security Tests

```bash
# Run all security tests
pytest tests/security/test_validation_security.py -v

# Run specific test class
pytest tests/security/test_validation_security.py::TestInputValidation -v

# Run with coverage
pytest tests/security/test_validation_security.py --cov=mcp_server --cov-report=html
```

---

**Last Updated**: 2025-10-25
**Next Security Review**: 2026-01-25 (Quarterly)
**Version**: 1.0
**Owner**: Agent 4 - Data Validation Team
