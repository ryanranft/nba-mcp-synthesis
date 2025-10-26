# Deployment Checklist

## Overview

Use this checklist for each production deployment of the NBA MCP system.

**Version:** 2.0
**Target Environment:** Production

---

## Pre-Deployment (T-24 hours)

### Code Preparation

- [ ] All code merged to `main` branch
- [ ] Version number updated (semantic versioning)
- [ ] CHANGELOG.md updated with release notes
- [ ] Git tag created (e.g., `v2.0.0`)
- [ ] No pending code reviews
- [ ] All CI/CD checks passing

**Verification:**
```bash
# Check branch status
git status
git log --oneline -5

# Verify CI/CD
# All GitHub Actions workflows should show ✓
```

### Testing

- [ ] All unit tests passing (350+ tests)
- [ ] All integration tests passing (36+ tests)
- [ ] Performance tests meet targets (<50ms p95)
- [ ] Security scan completed (no critical issues)
- [ ] Staging environment deployment successful
- [ ] Smoke tests on staging passed

**Commands:**
```bash
# Run full test suite
pytest tests/ -v --cov=mcp_server

# Expected: 350+ passed, 0 failed, >85% coverage
```

### Communication

- [ ] Deployment notification sent to stakeholders
- [ ] Deployment window scheduled and approved
- [ ] On-call engineer assigned and notified
- [ ] Rollback plan reviewed with team
- [ ] Status page updated (scheduled maintenance)

**Notification Template:**
```
Subject: NBA MCP Deployment - [Date] [Time]

Deployment Details:
- Version: v2.0.0
- Date: [Date]
- Time: [Start] - [End] UTC
- Expected Downtime: None (zero-downtime deployment)
- Rollback Window: 1 hour

Changes:
- [Feature 1]
- [Feature 2]
- [Bug fix 1]

On-Call: [Name] ([Contact])
```

### Infrastructure

- [ ] Production infrastructure healthy
- [ ] Database backup completed
- [ ] Model artifacts backed up to S3
- [ ] Sufficient disk space (>30% free)
- [ ] Sufficient memory (>30% free)
- [ ] Auto-scaling limits verified

**Health Check:**
```python
from mcp_server.system_health import SystemHealthChecker

health = SystemHealthChecker().check_system_health()
assert health['status'] == 'healthy'
assert health['healthy_components'] == health['total_components']
```

---

## Deployment (T-0)

### Pre-Deployment Verification

**Time: T-30 minutes**

- [ ] Final health check → All components healthy
- [ ] Database backup → Completed in last 2 hours
- [ ] Monitoring dashboard → All metrics green
- [ ] Team on standby → DevOps + On-call ready
- [ ] Rollback plan → Reviewed and accessible

### Deployment Execution

**Time: T-0 (Deployment Start)**

#### Step 1: Pre-Flight Checks

- [ ] Record current version: ___________
- [ ] Record current model version: ___________
- [ ] Capture baseline metrics:
  - Latency p95: _______ms
  - Error rate: _______%
  - Throughput: _______ req/s

```bash
# Capture current state
aws ecs describe-services --cluster nba-mcp-prod --services nba-mcp > pre-deploy-state.json
```

#### Step 2: Deploy New Version (Blue-Green)

**Blue Environment:** Current production (v1.9)
**Green Environment:** New version (v2.0)

- [ ] Build Docker image for v2.0
- [ ] Push image to ECR
- [ ] Create new ECS task definition (v2.0)
- [ ] Deploy green environment (v2.0)
- [ ] Wait for green environment to be healthy

```bash
# Build and push
docker build -t nba-mcp:2.0 .
docker tag nba-mcp:2.0 $ECR_REPO/nba-mcp:2.0
docker push $ECR_REPO/nba-mcp:2.0

# Update ECS task definition
aws ecs register-task-definition --cli-input-json file://task-def-v2.0.json

# Create green service
aws ecs create-service \
    --cluster nba-mcp-prod \
    --service-name nba-mcp-green \
    --task-definition nba-mcp-prod:v2.0 \
    --desired-count 3 \
    --load-balancers "targetGroupArn=$TARGET_GROUP_GREEN,..."
```

#### Step 3: Verify Green Environment

- [ ] Green environment health check → PASS
- [ ] Run smoke tests on green → PASS
- [ ] Check logs for errors → None
- [ ] Verify model serving → Working
- [ ] Check database connectivity → OK

```bash
# Health check on green environment
curl http://green.nba-mcp-prod.internal/health

# Smoke test
python scripts/smoke_test.py --endpoint http://green.nba-mcp-prod.internal
```

#### Step 4: Traffic Shift (Canary)

**Gradual rollout: 10% → 50% → 100%**

- [ ] Route 10% traffic to green
- [ ] Monitor for 10 minutes
  - Error rate: ______% (target: <1%)
  - Latency p95: _____ms (target: <50ms)
- [ ] Route 50% traffic to green
- [ ] Monitor for 10 minutes
  - Error rate: ______% (target: <1%)
  - Latency p95: _____ms (target: <50ms)
- [ ] Route 100% traffic to green
- [ ] Monitor for 10 minutes

```bash
# Shift traffic using ALB target group weights
# 10% to green, 90% to blue
aws elbv2 modify-listener --listener-arn $LISTENER_ARN \
    --default-actions "Type=forward,ForwardConfig={TargetGroups=[{TargetGroupArn=$TG_BLUE,Weight=90},{TargetGroupArn=$TG_GREEN,Weight=10}]}"

# Wait and monitor...

# 50% to green
aws elbv2 modify-listener --listener-arn $LISTENER_ARN \
    --default-actions "Type=forward,ForwardConfig={TargetGroups=[{TargetGroupArn=$TG_BLUE,Weight=50},{TargetGroupArn=$TG_GREEN,Weight=50}]}"

# Wait and monitor...

# 100% to green
aws elbv2 modify-listener --listener-arn $LISTENER_ARN \
    --default-actions "Type=forward,TargetGroupArn=$TG_GREEN"
```

#### Step 5: Verify Production Traffic

- [ ] 100% traffic to v2.0 → Confirmed
- [ ] Error rate < 1% → ______%
- [ ] Latency p95 < 50ms → _____ms
- [ ] No critical errors in logs
- [ ] Model predictions working correctly
- [ ] Database queries performing well

```bash
# Monitor CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace NBA-MCP \
    --metric-name ErrorRate \
    --start-time $(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average
```

#### Step 6: Cleanup Blue Environment

**Only after 1 hour of stable v2.0 operation**

- [ ] Blue environment (v1.9) kept for rollback → 1 hour
- [ ] No issues detected in production
- [ ] Monitoring confirms stability
- [ ] Ready to decommission blue

```bash
# After 1 hour of stable operation
aws ecs update-service \
    --cluster nba-mcp-prod \
    --service nba-mcp-blue \
    --desired-count 0
```

---

## Post-Deployment (T+1 hour)

### Immediate Verification

- [ ] Health check → All components healthy
- [ ] Error rate → <1%
- [ ] Latency → Within targets
- [ ] No critical alerts
- [ ] Logs clean (no unexpected errors)

### Monitoring (First Hour)

**Monitor every 15 minutes for first hour:**

| Time | Error Rate | Latency p95 | Status | Notes |
|------|-----------|-------------|--------|-------|
| T+15 | _____% | _____ms | ☐ OK / ☐ Issue | |
| T+30 | _____% | _____ms | ☐ OK / ☐ Issue | |
| T+45 | _____% | _____ms | ☐ OK / ☐ Issue | |
| T+60 | _____% | _____ms | ☐ OK / ☐ Issue | |

### Smoke Tests

- [ ] Test prediction API → Working
- [ ] Test model loading → Working
- [ ] Test data validation → Working
- [ ] Test drift detection → Working
- [ ] Test monitoring → Working

```python
# Comprehensive smoke test
python scripts/smoke_test_full.py --environment production

# Expected: All tests PASS
```

---

## Post-Deployment (T+24 hours)

### 24-Hour Review

- [ ] No critical incidents in 24 hours
- [ ] Error rate average < 1%
- [ ] Latency within targets
- [ ] User feedback collected
- [ ] No unexpected behavior reported

### Cleanup

- [ ] Blue environment decommissioned (if not already)
- [ ] Old Docker images cleaned up
- [ ] Deployment logs archived
- [ ] Metrics exported for review

### Documentation

- [ ] Deployment notes added to CHANGELOG
- [ ] Any issues documented
- [ ] Lessons learned captured
- [ ] Runbooks updated (if needed)

---

## Rollback Procedure

**Execute if any of these conditions are met:**
- Error rate > 5%
- Latency p95 > 100ms
- Critical functionality broken
- Data corruption detected
- Security incident

### Immediate Rollback Steps

**Time: T+X (Issue Detected)**

1. **Stop Traffic to Green**
   ```bash
   # Route 100% back to blue (v1.9)
   aws elbv2 modify-listener --listener-arn $LISTENER_ARN \
       --default-actions "Type=forward,TargetGroupArn=$TG_BLUE"
   ```

2. **Verify Blue is Healthy**
   ```bash
   curl http://blue.nba-mcp-prod.internal/health
   ```

3. **Monitor Rollback**
   - [ ] Traffic back to v1.9 → Confirmed
   - [ ] Error rate normalized → ______%
   - [ ] Latency normalized → _____ms
   - [ ] System stable

4. **Communicate**
   - [ ] Notify stakeholders of rollback
   - [ ] Update status page
   - [ ] Document issue

5. **Post-Rollback Analysis**
   - [ ] Root cause identified
   - [ ] Fix developed and tested
   - [ ] Re-deployment scheduled

### Rollback Checklist

- [ ] Rollback decision made by: _______________
- [ ] Rollback initiated at: _______________
- [ ] Rollback completed at: _______________
- [ ] System stable after rollback: ☐ YES / ☐ NO
- [ ] Incident report created: ☐ YES / ☐ NO

---

## Sign-Off

**Deployment Lead:** _______________ Date: _______ Time: _______

**Deployment Status:**

☐ **SUCCESS** - Deployment complete and stable
☐ **ROLLED BACK** - Issues detected, rolled back to previous version
☐ **IN PROGRESS** - Deployment ongoing

**Next Steps:**

- [ ] Post-deployment review scheduled
- [ ] Metrics analysis completed
- [ ] Lessons learned documented

---

## Notes

_Deployment notes, issues encountered, or special considerations:_




---

**Quick Reference:**

**Go Criteria:**
- All tests passing
- All health checks green
- Team on standby
- Rollback plan ready

**No-Go Criteria:**
- Critical tests failing
- Infrastructure issues
- Missing on-call coverage
- No rollback plan

**Rollback Triggers:**
- Error rate > 5%
- Latency p95 > 100ms
- Critical functionality broken
- Data issues detected
