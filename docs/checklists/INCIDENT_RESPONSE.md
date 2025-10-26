# Incident Response Guide

## Overview

This guide provides procedures for responding to incidents in the NBA MCP production system.

**Version:** 2.0
**Last Updated:** October 2025

---

## Incident Severity Levels

### Severity 1 (Critical) - P1

**Definition:** Complete system outage or data loss

**Examples:**
- System completely down (all instances failing)
- Database corruption or data loss
- Security breach detected
- Predictions returning incorrect results for all users

**Response Time:** 15 minutes
**Escalation:** Immediate to all teams
**Communication:** Hourly updates to stakeholders

### Severity 2 (High) - P2

**Definition:** Significant degradation affecting multiple users

**Examples:**
- Error rate > 10%
- Latency > 500ms
- Single component failure (with redundancy)
- Model drift causing accuracy drop > 10%

**Response Time:** 1 hour
**Escalation:** DevOps + On-call engineer
**Communication:** Updates every 4 hours

### Severity 3 (Medium) - P3

**Definition:** Limited impact or non-critical issues

**Examples:**
- Error rate 1-5%
- Latency 50-200ms
- Non-critical feature unavailable
- Monitoring alerts for drift/performance

**Response Time:** 4 hours
**Escalation:** On-call engineer
**Communication:** Daily updates

### Severity 4 (Low) - P4

**Definition:** Minimal or no user impact

**Examples:**
- Cosmetic issues
- Performance optimization opportunities
- Documentation issues

**Response Time:** Next business day
**Escalation:** Not required
**Communication:** As needed

---

## Incident Response Process

### 1. Detection

**Automated Detection:**
- CloudWatch alarms trigger
- Health checks fail
- APM alerts fire
- User reports via support

**Manual Detection:**
- Monitoring dashboard anomalies
- Log analysis
- User complaints

### 2. Initial Response (First 15 Minutes)

#### Acknowledge Incident

- [ ] Acknowledge alert in PagerDuty/incident system
- [ ] Create incident ticket (Jira/GitHub)
- [ ] Assign severity level
- [ ] Notify on-call engineer

#### Assess Severity

```python
# Quick system health check
from mcp_server.system_health import SystemHealthChecker

checker = SystemHealthChecker()
health = checker.check_system_health()

print(f"Status: {health['status']}")
print(f"Healthy Components: {health['healthy_components']}/{health['total_components']}")

# Check specific components
for component, details in health['components'].items():
    if details['status'] != 'healthy':
        print(f"⚠️  {component}: {details['status']}")
```

#### Communicate

- [ ] Post to #nba-mcp-incidents Slack channel
- [ ] Update status page (if P1/P2)
- [ ] Notify stakeholders (if P1)

**Incident Template:**
```
INCIDENT: [Title]
Severity: [P1/P2/P3/P4]
Detected: [Time]
Impact: [Description]
Status: INVESTIGATING
Next Update: [Time]
```

### 3. Investigation (Next 30 Minutes)

#### Gather Information

- [ ] Check CloudWatch metrics
- [ ] Review application logs
- [ ] Check recent deployments
- [ ] Review database performance
- [ ] Check external dependencies

**Investigation Checklist:**
```bash
# 1. Check system health
python -c "from mcp_server.system_health import SystemHealthChecker; print(SystemHealthChecker().get_health_summary())"

# 2. Check recent errors
tail -f /var/log/nba-mcp/app.log | grep ERROR

# 3. Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace NBA-MCP \
    --metric-name ErrorRate \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average

# 4. Check ECS service health
aws ecs describe-services \
    --cluster nba-mcp-prod \
    --services nba-mcp

# 5. Check database
psql -h $DB_HOST -U admin -d nba_mcp -c "SELECT 1"
```

#### Identify Root Cause

**Common Patterns:**
- Recent deployment correlation
- Traffic spike
- Database performance
- External API issues
- Resource exhaustion

### 4. Mitigation (Immediate Action)

Choose appropriate mitigation based on incident type:

#### If: High Error Rate

```python
# 1. Check error logs
grep ERROR /var/log/nba-mcp/app.log | tail -100

# 2. Identify error pattern
# 3. If related to recent deployment → Rollback
# 4. If database issue → Check connection pool
# 5. If external API → Enable circuit breaker
```

#### If: High Latency

```python
# 1. Check cache hit rate
from mcp_server.system_optimizer import get_system_stats
stats = get_system_stats()
print(f"Cache hit rate: {stats['model_cache']['hit_rate']}")

# 2. If low cache hit rate → Warm cache
# 3. If database slow → Check slow queries
# 4. If model loading slow → Increase cache size
```

#### If: System Down

```bash
# 1. Check ECS tasks
aws ecs list-tasks --cluster nba-mcp-prod --service-name nba-mcp

# 2. Check task status
aws ecs describe-tasks --cluster nba-mcp-prod --tasks [task-id]

# 3. Check logs
aws logs tail /ecs/nba-mcp-prod --follow

# 4. Restart service if needed
aws ecs update-service \
    --cluster nba-mcp-prod \
    --service nba-mcp \
    --force-new-deployment
```

### 5. Resolution

#### Fix Implementation

- [ ] Implement fix (code change, config update, or rollback)
- [ ] Test fix in staging (if possible)
- [ ] Deploy fix to production
- [ ] Verify resolution

#### Verification

- [ ] Error rate normalized → ______%
- [ ] Latency normalized → _____ms
- [ ] Health checks passing → All green
- [ ] No new errors in logs
- [ ] Monitoring dashboard green

### 6. Post-Incident

#### Communication

- [ ] Update incident ticket → RESOLVED
- [ ] Post resolution to #nba-mcp-incidents
- [ ] Update status page
- [ ] Notify stakeholders

**Resolution Template:**
```
RESOLVED: [Incident Title]
Resolution Time: [Duration]
Root Cause: [Brief description]
Fix: [What was done]
Prevention: [Future prevention measures]
```

#### Post-Mortem (Required for P1/P2)

- [ ] Schedule post-mortem meeting (within 48 hours)
- [ ] Document incident timeline
- [ ] Identify root cause
- [ ] List action items
- [ ] Assign owners for follow-up

---

## Common Incident Scenarios

### Scenario 1: Complete System Outage

**Symptoms:**
- All health checks failing
- 100% error rate
- No successful predictions

**Diagnosis:**
```bash
# Check ECS service
aws ecs describe-services --cluster nba-mcp-prod --services nba-mcp

# Check database
psql -h $DB_HOST -U admin -d nba_mcp -c "SELECT 1"

# Check MLflow
curl http://mlflow-prod:5000/health
```

**Resolution Steps:**
1. [ ] Verify database connectivity
2. [ ] Check ECS task status
3. [ ] Review recent deployments
4. [ ] If recent deployment → Rollback immediately
5. [ ] If infrastructure issue → Restart services
6. [ ] Verify resolution with smoke tests

**Rollback Command:**
```bash
# Rollback to previous version
aws ecs update-service \
    --cluster nba-mcp-prod \
    --service nba-mcp \
    --task-definition nba-mcp-prod:[previous-version]
```

### Scenario 2: High Error Rate (> 5%)

**Symptoms:**
- Error rate > 5%
- CloudWatch alarm triggered
- Partial functionality working

**Diagnosis:**
```bash
# Check error distribution
grep ERROR /var/log/nba-mcp/app.log | cut -d' ' -f5- | sort | uniq -c | sort -rn

# Check specific error types
tail -100 /var/log/nba-mcp/app.log | grep ERROR
```

**Resolution Steps:**
1. [ ] Identify error pattern (DB, model, API)
2. [ ] If database errors → Check connection pool
3. [ ] If model errors → Check model loading
4. [ ] If API errors → Check external dependencies
5. [ ] Apply appropriate fix
6. [ ] Monitor error rate for 15 minutes

**Database Connection Fix:**
```python
# Restart connection pool
# In application code, add:
db_pool.close_all()
db_pool.reinitialize()
```

### Scenario 3: Model Drift Detected

**Symptoms:**
- Drift alert triggered
- Accuracy decreasing
- Input distribution changed

**Diagnosis:**
```python
from mcp_server.model_monitoring import ModelMonitor

monitor = ModelMonitor("nba_win_predictor", "v2.0")
drift_results = monitor.detect_feature_drift(current_data)

# Check drifted features
for feature, result in drift_results.items():
    if result['drift_detected']:
        print(f"Drift in {feature}: p-value={result['p_value']}")
```

**Resolution Steps:**
1. [ ] Investigate data quality issues
2. [ ] Verify data source changes
3. [ ] If data quality issue → Fix upstream
4. [ ] If legitimate drift → Retrain model
5. [ ] Update reference data if appropriate

**Retrain Model:**
```python
from mcp_server.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()
new_model = pipeline.train(updated_data)

# Deploy new model
from mcp_server.model_serving import ModelServingManager
serving = ModelServingManager()
serving.deploy_model("nba_win_predictor", "v2.1", new_model)
```

### Scenario 4: Database Performance Issues

**Symptoms:**
- Slow query performance
- Timeouts
- High database CPU

**Diagnosis:**
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

**Resolution Steps:**
1. [ ] Identify slow queries
2. [ ] Add missing indexes
3. [ ] Optimize queries
4. [ ] Scale database if needed
5. [ ] Consider read replicas

**Add Index Example:**
```sql
-- Add index to improve query performance
CREATE INDEX CONCURRENTLY idx_predictions_model_id_created
ON predictions(model_id, created_at);
```

### Scenario 5: Cache Performance Issues

**Symptoms:**
- Low cache hit rate (<70%)
- High model loading times
- Increased latency

**Diagnosis:**
```python
from mcp_server.system_optimizer import get_system_stats

stats = get_system_stats()
print(f"Model cache hit rate: {stats['model_cache']['hit_rate']:.2%}")
print(f"Model cache size: {stats['model_cache']['size']}/{stats['model_cache']['max_size']}")
```

**Resolution Steps:**
1. [ ] Increase cache size
2. [ ] Increase cache TTL
3. [ ] Warm cache with frequently used models
4. [ ] Monitor for improvement

**Increase Cache Size:**
```python
# In configuration
MODEL_CACHE_SIZE = 100  # Increase from 50
DATA_CACHE_SIZE = 200   # Increase from 100
```

---

## Escalation Matrix

### Tier 1: On-Call Engineer
**Response Time:** 15 minutes
**Handles:** All P3, P4, initial response for P1, P2

### Tier 2: DevOps Lead
**Escalate if:** Issue not resolved in 1 hour (P1, P2)
**Contact:** Slack DM + Phone

### Tier 3: Engineering Manager
**Escalate if:** Issue not resolved in 2 hours (P1) or major impact
**Contact:** Phone

### Tier 4: CTO/VP Engineering
**Escalate if:** Business-critical impact or data breach
**Contact:** Phone (emergency contact list)

---

## Contact Information

### Emergency Contacts

**On-Call Rotation:** Check PagerDuty schedule
**Slack:** #nba-mcp-incidents (fastest)
**Email:** nba-mcp-oncall@company.com

### External Vendors

**AWS Support:** 1-800-XXX-XXXX (Premium Support)
**MLflow Support:** support@databricks.com
**Database Support:** PostgreSQL community / AWS RDS Support

---

## Tools & Resources

### Monitoring Dashboards

- **CloudWatch:** https://console.aws.amazon.com/cloudwatch/
- **MLflow:** http://mlflow-prod.example.com/
- **Status Page:** https://status.nba-mcp.example.com/

### Log Locations

- **Application:** `/var/log/nba-mcp/app.log`
- **Access:** `/var/log/nginx/access.log`
- **Error:** `/var/log/nginx/error.log`
- **CloudWatch:** `/ecs/nba-mcp-prod`

### Runbooks

- [Deployment Rollback](../DEPLOYMENT_GUIDE.md#rollback-procedures)
- [Database Recovery](../OPERATIONS_GUIDE.md#backup--recovery)
- [Model Rollback](../OPERATIONS_GUIDE.md#managing-models)

---

## Incident Template

Use this template to document incidents:

```
# Incident Report: [Title]

**Incident ID:** INC-YYYYMMDD-###
**Severity:** [P1/P2/P3/P4]
**Status:** [INVESTIGATING/MITIGATING/RESOLVED]

## Timeline

| Time | Event |
|------|-------|
| HH:MM | Incident detected |
| HH:MM | Team notified |
| HH:MM | Root cause identified |
| HH:MM | Fix applied |
| HH:MM | Incident resolved |

## Impact

**Affected Users:** [Number/Percentage]
**Duration:** [Start] to [End] ([Duration])
**Services Affected:** [List]

## Root Cause

[Detailed description of what caused the incident]

## Resolution

[What was done to resolve the incident]

## Prevention

[What will be done to prevent this in the future]

## Action Items

- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]
- [ ] [Action 3] - Owner: [Name] - Due: [Date]
```

---

## Post-Mortem Template

**Meeting Date:** _______
**Attendees:** _______

### What Happened?
[Detailed timeline and description]

### What Went Well?
[Things that worked during incident response]

### What Could Be Improved?
[Areas for improvement]

### Root Cause Analysis
[Deep dive into why it happened]

### Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| | | | |

---

## Quick Reference

**Emergency Commands:**
```bash
# System health check
python -c "from mcp_server.system_health import SystemHealthChecker; print(SystemHealthChecker().get_health_summary())"

# Rollback deployment
aws ecs update-service --cluster nba-mcp-prod --service nba-mcp --task-definition nba-mcp-prod:[previous]

# Clear cache
python -c "from mcp_server.system_optimizer import clear_all_caches; clear_all_caches()"

# Database backup
pg_dump nba_mcp > /backups/emergency_$(date +%Y%m%d_%H%M%S).sql

# Restart service
aws ecs update-service --cluster nba-mcp-prod --service nba-mcp --force-new-deployment
```

**Severity Decision Tree:**
- System down or data loss → P1
- High error rate (>10%) or major degradation → P2
- Moderate issues, limited impact → P3
- Minor issues, no user impact → P4
