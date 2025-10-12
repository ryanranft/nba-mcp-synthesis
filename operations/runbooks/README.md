# 📚 Operational Runbooks - IMPORTANT 19

**Last Updated:** October 12, 2025
**Owner:** Operations Team

---

## 📋 RUNBOOK COLLECTION

Operational runbooks for common NBA MCP system tasks and incidents.

---

## 🚀 DEPLOYMENT RUNBOOKS

### **[RB-001] Deploy New Model to Production**

**Frequency:** Weekly
**Duration:** 30 minutes
**Risk Level:** MEDIUM

**Prerequisites:**
- Model tested in staging
- Performance metrics validated
- A/B test completed (if applicable)
- Rollback plan ready

**Procedure:**

```bash
# 1. Verify current production model
mlflow models list | grep production

# 2. Deploy new model via shadow deployment first
python -c "
from mcp_server.shadow_deployment import get_shadow_deployment
deployment = get_shadow_deployment()
deployment.register_shadow_model(
    name='nba_win_predictor_v2',
    version='2.0.0',
    model=new_model,
    predict_func=predict,
    sample_rate=0.1  # Start with 10% traffic
)
"

# 3. Monitor shadow performance for 24 hours
python scripts/monitor_shadow_model.py --model nba_win_predictor_v2 --duration 24h

# 4. Promote to production if metrics are good
python -c "
from mcp_server.shadow_deployment import get_shadow_deployment
deployment = get_shadow_deployment()
deployment.promote_shadow_to_production('nba_win_predictor_v2')
"

# 5. Verify production deployment
curl https://api.nba-mcp.com/models/current | jq '.version'

# 6. Monitor for 1 hour
python scripts/monitor_production.py --duration 1h
```

**Success Criteria:**
- ✅ Shadow model agreement rate > 95%
- ✅ No errors in production logs
- ✅ Latency < 100ms p99
- ✅ Model version updated in registry

**Rollback:**
```bash
# Revert to previous production model
mlflow models promote-to-production \
  --name nba_win_predictor \
  --version <previous-version>

# Verify rollback
curl https://api.nba-mcp.com/models/current
```

---

### **[RB-002] Scale Application

**Frequency:** As needed
**Duration:** 15 minutes
**Risk Level:** LOW

**Procedure:**

```bash
# 1. Check current resource usage
kubectl top pods -n nba-mcp

# 2. Scale horizontally (more pods)
kubectl scale deployment nba-mcp --replicas=10 -n nba-mcp

# 3. Or scale vertically (more resources per pod)
kubectl set resources deployment nba-mcp \
  --requests=cpu=2,memory=4Gi \
  --limits=cpu=4,memory=8Gi \
  -n nba-mcp

# 4. Verify scaling
kubectl get pods -n nba-mcp -w

# 5. Monitor performance
python scripts/check_performance.py --duration 15m
```

**Success Criteria:**
- ✅ All pods running and healthy
- ✅ Load balanced across pods
- ✅ Response times normal
- ✅ No pod restarts

---

## 🔥 INCIDENT RESPONSE RUNBOOKS

### **[RB-101] High Error Rate Alert**

**Severity:** HIGH
**Expected Duration:** 30-60 minutes

**Symptoms:**
- Error rate > 5% (alert triggered)
- Multiple 5xx responses
- Increased latency

**Investigation:**

```bash
# 1. Check recent deployments
kubectl rollout history deployment/nba-mcp -n nba-mcp

# 2. Review error logs
kubectl logs -n nba-mcp -l app=nba-mcp --tail=100 | grep ERROR

# 3. Check external dependencies
curl https://api.nba-mcp.com/health | jq '.'

# 4. Query error distribution
cat <<EOF | psql -h <db-host> -U postgres -d nba_stats
SELECT error_type, COUNT(*) as count
FROM error_log
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY error_type
ORDER BY count DESC
LIMIT 10;
EOF

# 5. Check resource usage
kubectl top pods -n nba-mcp
```

**Common Causes & Fixes:**

**A) Database Connection Pool Exhausted**
```bash
# Check active connections
psql -h <db-host> -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size temporarily
kubectl set env deployment/nba-mcp DB_POOL_SIZE=50

# Or restart pods to reset connections
kubectl rollout restart deployment/nba-mcp
```

**B) Memory Leak**
```bash
# Check memory usage trend
kubectl top pods -n nba-mcp

# Restart leaking pods
kubectl delete pod <pod-name> -n nba-mcp

# Schedule heap dump collection
kubectl exec -it <pod-name> -n nba-mcp -- python -m memory_profiler app.py
```

**C) External API Failure**
```bash
# Check NBA API status
curl https://stats.nba.com/health

# Enable circuit breaker
python -c "
from mcp_server.graceful_degradation import get_circuit_breaker
cb = get_circuit_breaker('nba_api')
print(f'Circuit breaker state: {cb.state}')
"

# Fall back to cached data
kubectl set env deployment/nba-mcp USE_CACHE_FALLBACK=true
```

**Resolution:**
- Apply appropriate fix from above
- Monitor error rate for 15 minutes
- Close incident if error rate < 1%
- Update post-mortem document

---

### **[RB-102] Database Performance Degradation**

**Severity:** HIGH
**Expected Duration:** 45-90 minutes

**Symptoms:**
- Query latency > 1s
- Increased database CPU
- Slow API responses

**Investigation:**

```bash
# 1. Identify slow queries
psql -h <db-host> -U postgres -d nba_stats <<EOF
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- queries > 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;
EOF

# 2. Check for blocking queries
psql -h <db-host> -U postgres -d nba_stats <<EOF
SELECT pid, usename, pg_blocking_pids(pid), query
FROM pg_stat_activity
WHERE pg_blocking_pids(pid)::text != '{}';
EOF

# 3. Review database metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=nba-mcp-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 4. Check connection count
psql -h <db-host> -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**Immediate Actions:**

```bash
# Kill blocking/long-running queries
psql -h <db-host> -U postgres -c "SELECT pg_terminate_backend(<pid>);"

# Create missing index (if identified)
psql -h <db-host> -U postgres -d nba_stats <<EOF
CREATE INDEX CONCURRENTLY idx_games_season ON games(season);
EOF

# Increase RDS instance size temporarily
aws rds modify-db-instance \
  --db-instance-identifier nba-mcp-prod \
  --db-instance-class db.r5.2xlarge \
  --apply-immediately

# Enable read replica routing
kubectl set env deployment/nba-mcp USE_READ_REPLICA=true
```

---

### **[RB-103] Data Drift Detected**

**Severity:** MEDIUM
**Expected Duration:** 2-4 hours

**Symptoms:**
- Data drift alert triggered
- Model accuracy declining
- Feature distribution changed

**Investigation:**

```bash
# 1. Review drift report
python -c "
from mcp_server.data_drift import get_drift_detector
detector = get_drift_detector()
results = detector.check_all_features(current_data)
print(results)
"

# 2. Identify drifted features
python scripts/analyze_drift.py --date today --threshold 0.1

# 3. Compare feature distributions
python scripts/compare_distributions.py \
  --baseline 2025-10-01 \
  --current 2025-10-12
```

**Response Actions:**

```bash
# 1. Trigger model retraining
python -c "
from mcp_server.automated_retraining import get_retraining_pipeline
pipeline = get_retraining_pipeline()
result = pipeline.retrain_model(
    'nba_win_predictor',
    training_func=train_model,
    evaluation_func=evaluate_model
)
print(f'Retraining result: {result}')
"

# 2. Update feature baselines
python scripts/update_drift_baselines.py --date today

# 3. Review data sources
python scripts/check_data_sources.py

# 4. Schedule follow-up analysis
echo "*/6 * * * * python scripts/monitor_drift.py" | crontab -
```

---

## 🔧 MAINTENANCE RUNBOOKS

### **[RB-201] Weekly Maintenance**

**Schedule:** Every Sunday 02:00-04:00 UTC
**Duration:** 2 hours
**Risk Level:** LOW

**Tasks:**

```bash
# 1. Database maintenance
psql -h <db-host> -U postgres -d nba_stats <<EOF
VACUUM ANALYZE;
REINDEX DATABASE nba_stats;
EOF

# 2. Clean old logs
kubectl delete pods --field-selector=status.phase==Succeeded -n nba-mcp
aws s3 rm s3://nba-mcp-logs/ --recursive --exclude "*" --include "*2025-09*"

# 3. Rotate secrets
python scripts/rotate_secrets.py --age-days 90

# 4. Update dependencies
pip-compile requirements.in -o requirements.txt
docker build -t nba-mcp:latest .

# 5. Run security scans
trivy image nba-mcp:latest

# 6. Backup verification
python scripts/verify_backups.py --days 7

# 7. Generate weekly report
python scripts/generate_weekly_report.py --output weekly-report.html
```

---

### **[RB-202] Monthly Capacity Planning**

**Schedule:** First Monday of month
**Duration:** 4 hours
**Risk Level:** LOW

```bash
# 1. Generate capacity report
python scripts/capacity_analysis.py --month last

# 2. Review growth trends
python scripts/analyze_growth.py \
  --metrics "requests,users,data_size" \
  --period 6months

# 3. Forecast next month
python scripts/forecast_capacity.py \
  --horizon 30days \
  --confidence 0.95

# 4. Update scaling policies
kubectl edit hpa nba-mcp-autoscaler -n nba-mcp

# 5. Review costs
aws ce get-cost-and-usage \
  --time-period Start=2025-09-01,End=2025-10-01 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## 📞 ESCALATION PROCEDURES

### **Severity Levels:**

**P0 - CRITICAL**
- Complete service outage
- Data loss occurring
- Security breach
- **Response:** Immediate (< 15 min)
- **Escalate to:** VP Engineering, CTO

**P1 - HIGH**
- Partial service degradation
- High error rates
- Performance severely impacted
- **Response:** < 30 minutes
- **Escalate to:** Team Lead

**P2 - MEDIUM**
- Minor service degradation
- Non-critical feature broken
- Performance degraded
- **Response:** < 2 hours
- **Escalate to:** On-call engineer

**P3 - LOW**
- Minor issues
- Feature requests
- Non-urgent bugs
- **Response:** Next business day
- **Escalate to:** Product team

---

## ✅ RUNBOOK TESTING

All runbooks should be tested quarterly. Track completion:

| Runbook | Last Tested | Next Test | Status |
|---------|-------------|-----------|--------|
| RB-001 | 2025-10-01 | 2026-01-01 | ✅ PASS |
| RB-002 | 2025-10-05 | 2026-01-05 | ✅ PASS |
| RB-101 | 2025-09-15 | 2025-12-15 | ⏳ DUE |
| RB-102 | 2025-09-20 | 2025-12-20 | ⏳ DUE |
| RB-103 | 2025-10-10 | 2026-01-10 | ✅ PASS |
| RB-201 | Weekly | N/A | ✅ ACTIVE |
| RB-202 | Monthly | N/A | ✅ ACTIVE |

---

## 📚 RELATED DOCUMENTATION

- [Disaster Recovery Plan](../disaster_recovery_plan.md)
- [Monitoring & Alerting](../../monitoring/README.md)
- [Architecture Documentation](../../docs/architecture/)
- [API Documentation](../../mcp_server/api_docs.py)

---

**Document Maintenance:**
- Update runbooks after each incident
- Test procedures quarterly
- Review and revise annually
- Keep procedures < 30 steps when possible

