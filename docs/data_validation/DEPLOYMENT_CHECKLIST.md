# Data Validation Deployment Checklist

**Phase 10A Week 2 - Agent 4 - Phase 5**
**Created**: 2025-10-25

Quick reference checklist for deploying data validation infrastructure.

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All unit tests passing (`pytest tests/test_data_*.py`)
- [ ] All integration tests passing (`pytest tests/integration/`)
- [ ] Code coverage >80% on all validation modules
- [ ] No critical linting errors (`flake8 mcp_server/`)
- [ ] Security scan clean (`safety check`)
- [ ] All dependencies up to date
- [ ] Documentation updated

### Configuration

- [ ] Environment variables configured (`.env` file created)
- [ ] Secrets stored securely (not in code)
- [ ] Resource limits configured (`config/validation_config.yaml`)
- [ ] Logging configuration set (`LOG_LEVEL`, log file paths)
- [ ] Database credentials configured (if applicable)
- [ ] Monitoring endpoints configured

### Infrastructure

- [ ] Target server meets system requirements (CPU, RAM, disk)
- [ ] Python 3.9+ installed
- [ ] Network connectivity verified (database, monitoring)
- [ ] SSH access to deployment server
- [ ] Backup strategy in place
- [ ] Rollback plan documented

### Access & Permissions

- [ ] Deployment user has necessary permissions
- [ ] Git repository access configured
- [ ] AWS/cloud credentials configured (if applicable)
- [ ] Database access granted
- [ ] Secrets manager access granted
- [ ] Monitoring system access granted

---

## Deployment Checklist

### Step 1: Preparation

- [ ] Notify stakeholders of deployment window
- [ ] Verify no conflicting deployments scheduled
- [ ] Backup current production environment
- [ ] Tag release in Git (`git tag -a v1.0.0 -m "Release 1.0.0"`)
- [ ] Create deployment ticket/record

### Step 2: Environment Setup

- [ ] SSH into deployment server
- [ ] Navigate to deployment directory
- [ ] Activate Python virtual environment
- [ ] Verify Python version (`python --version >= 3.9`)
- [ ] Set environment variables (`source .env`)

### Step 3: Code Deployment

- [ ] Pull latest code (`git pull origin main` or `git checkout tags/v1.0.0`)
- [ ] Install/update dependencies (`pip install -r requirements.txt`)
- [ ] Run database migrations (if applicable)
- [ ] Copy configuration files to correct locations
- [ ] Set file permissions (`chmod`, `chown`)

### Step 4: Service Configuration

- [ ] Update systemd service file (if applicable)
- [ ] Reload systemd daemon (`sudo systemctl daemon-reload`)
- [ ] Enable service on boot (`sudo systemctl enable nba-mcp-validation`)

### Step 5: Service Deployment

- [ ] Stop existing service (if running)
- [ ] Start new service (`sudo systemctl start nba-mcp-validation`)
- [ ] Check service status (`sudo systemctl status nba-mcp-validation`)
- [ ] Verify service logs (`journalctl -u nba-mcp-validation -f`)

---

## Post-Deployment Checklist

### Health Checks

- [ ] Service is running (`systemctl status nba-mcp-validation`)
- [ ] Health endpoint returns 200 (`curl http://localhost:8000/health`)
- [ ] No errors in logs (`tail -f /var/log/nba-mcp/validation.log`)
- [ ] CPU/memory usage normal (`top`, `htop`)

### Smoke Tests

- [ ] Import test passes:
  ```bash
  python -c "from mcp_server.data_validation_pipeline import DataValidationPipeline; print('OK')"
  ```

- [ ] Basic validation test passes:
  ```bash
  python tests/smoke_test.py
  ```

- [ ] Integration tests pass:
  ```bash
  pytest tests/integration/ -v
  ```

### Functional Validation

- [ ] Run sample validation successfully
- [ ] Verify data cleaning works
- [ ] Verify data profiling works
- [ ] Verify integrity checking works
- [ ] Verify business rules work
- [ ] Check validation results are correct

### Performance Validation

- [ ] Run performance benchmark tests
- [ ] Verify performance meets baselines:
  - 1K rows < 500ms
  - 10K rows < 5s
  - 100K rows < 30s
- [ ] Check memory usage is within limits
- [ ] Verify no memory leaks

### Security Validation

- [ ] Run security tests (`pytest tests/security/`)
- [ ] Verify input validation works
- [ ] Verify resource limits enforced
- [ ] Check no secrets in logs
- [ ] Verify PII masking works

### Monitoring & Alerting

- [ ] Metrics being collected
- [ ] Monitoring dashboard shows data
- [ ] Health checks reporting correctly
- [ ] Alerts configured and working
- [ ] Logs being shipped to central logging

### Documentation

- [ ] Deployment documented in change log
- [ ] Runbook updated with new version
- [ ] Known issues documented
- [ ] Rollback procedure verified

---

## Rollback Checklist

**Trigger rollback if:**
- Critical tests failing
- Service won't start
- Health checks failing
- Unacceptable performance degradation
- Data corruption detected
- Security vulnerability discovered

### Rollback Steps

- [ ] Notify stakeholders of rollback
- [ ] Stop current service
- [ ] Identify backup to restore
- [ ] Restore previous version
- [ ] Restart service
- [ ] Verify health checks pass
- [ ] Run smoke tests
- [ ] Confirm rollback successful
- [ ] Document rollback reason
- [ ] Plan remediation

---

## Verification Matrix

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Python version | >= 3.9 | ___ | ☐ |
| Service status | active (running) | ___ | ☐ |
| Health endpoint | 200 OK | ___ | ☐ |
| Unit tests | 100% pass | ___ | ☐ |
| Integration tests | 100% pass | ___ | ☐ |
| Performance (1K rows) | < 500ms | ___ | ☐ |
| Performance (10K rows) | < 5s | ___ | ☐ |
| Memory usage | < 2GB | ___ | ☐ |
| CPU usage | < 50% | ___ | ☐ |
| Error rate | 0% | ___ | ☐ |
| Logs | No errors | ___ | ☐ |

---

## Sign-Off

**Deployment Information:**
- **Date**: ___________________
- **Version**: ___________________
- **Environment**: Production / Staging / Development
- **Deployed by**: ___________________

**Approvals:**
- [ ] Tech Lead: ___________________
- [ ] Operations: ___________________
- [ ] Security: ___________________

**Verification:**
- [ ] All pre-deployment checks passed
- [ ] All deployment steps completed
- [ ] All post-deployment checks passed
- [ ] Monitoring confirms healthy state
- [ ] Stakeholders notified of completion

**Notes:**
```
_______________________________________________
_______________________________________________
_______________________________________________
```

---

## Quick Command Reference

```bash
# Check service status
sudo systemctl status nba-mcp-validation

# View logs
journalctl -u nba-mcp-validation -f
tail -f /var/log/nba-mcp/validation.log

# Health check
curl http://localhost:8000/health

# Run tests
pytest tests/ -v

# Check Python version
python --version

# Check installed packages
pip list

# Restart service
sudo systemctl restart nba-mcp-validation

# Rollback (automated)
./scripts/deploy_validation_infrastructure.sh --rollback
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Owner**: Agent 4 - Data Validation Team
