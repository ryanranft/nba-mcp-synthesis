# 🚨 Disaster Recovery Plan - IMPORTANT 18

**Document Version:** 1.0
**Last Updated:** October 12, 2025
**Review Schedule:** Quarterly
**Owner:** Operations Team

---

## 📋 EXECUTIVE SUMMARY

This Disaster Recovery (DR) Plan outlines procedures to recover the NBA MCP system in the event of a catastrophic failure. Our Recovery Time Objective (RTO) is **4 hours** and Recovery Point Objective (RPO) is **15 minutes**.

---

## 🎯 OBJECTIVES

- **RTO (Recovery Time Objective):** 4 hours
- **RPO (Recovery Point Objective):** 15 minutes
- **Availability Target:** 99.9% (8.76 hours downtime/year)

---

## 🏗️ SYSTEM ARCHITECTURE

### **Critical Components:**

1. **Application Tier**
   - NBA MCP FastAPI Server
   - MLflow Server
   - Monitoring Stack (Prometheus/Grafana)

2. **Data Tier**
   - PostgreSQL RDS (primary data store)
   - Redis ElastiCache (caching)
   - S3 Buckets (artifacts, backups, books)

3. **ML Infrastructure**
   - Model Registry
   - Feature Store
   - Training Pipeline

4. **Observability**
   - Jaeger (tracing)
   - Prometheus (metrics)
   - CloudWatch Logs

---

## 📊 DISASTER SCENARIOS

### **Scenario 1: Database Failure (RDS)**

**Impact:** HIGH - Total service outage
**Probability:** LOW
**RTO:** 2 hours
**RPO:** 15 minutes

**Recovery Steps:**

1. **Detect** (automated)
   ```bash
   # Health check fails
   curl https://api.nba-mcp.com/health
   # Returns: {"database": "fail"}
   ```

2. **Assess**
   - Check RDS console for instance status
   - Review CloudWatch metrics
   - Identify failure type (hardware, software, corruption)

3. **Recover**

   **Option A: Restore from Automated Backup**
   ```bash
   # List available backups
   aws rds describe-db-snapshots \
     --db-instance-identifier nba-mcp-prod \
     --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]'

   # Restore from latest backup
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier nba-mcp-prod-restored \
     --db-snapshot-identifier rds:nba-mcp-prod-2025-10-12-04-00

   # Update DNS/connection string
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://dns-update.json
   ```

   **Option B: Failover to Read Replica**
   ```bash
   # Promote read replica to primary
   aws rds promote-read-replica \
     --db-instance-identifier nba-mcp-prod-replica

   # Update connection strings
   kubectl set env deployment/nba-mcp \
     DB_HOST=nba-mcp-prod-replica.xxxxx.us-east-1.rds.amazonaws.com
   ```

4. **Verify**
   ```bash
   # Test database connectivity
   psql -h <new-endpoint> -U postgres -d nba_stats -c "SELECT 1"

   # Run health checks
   curl https://api.nba-mcp.com/health | jq '.database'
   ```

5. **Post-Recovery**
   - Document incident in post-mortem
   - Update backup frequency if needed
   - Schedule follow-up testing

**Expected Time:** 1-2 hours

---

### **Scenario 2: Complete AWS Region Failure**

**Impact:** CRITICAL - Total outage
**Probability:** VERY LOW
**RTO:** 4 hours
**RPO:** 15 minutes

**Recovery Steps:**

1. **Declare Disaster**
   - Operations Lead declares disaster
   - Activate DR team
   - Notify stakeholders

2. **Activate DR Region** (us-west-2)

   ```bash
   # Set DR region
   export AWS_REGION=us-west-2

   # Restore latest RDS snapshot to DR region
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier nba-mcp-dr \
     --db-snapshot-identifier <latest-cross-region-snapshot> \
     --region us-west-2

   # Deploy application stack
   cd /infrastructure/terraform
   terraform workspace select dr
   terraform apply -auto-approve

   # Sync S3 data
   aws s3 sync s3://nba-mcp-data-us-east-1 \
                s3://nba-mcp-data-us-west-2 \
                --region us-west-2

   # Deploy ML models
   ./deploy_models_to_dr.sh

   # Update DNS to DR region
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://dr-failover.json
   ```

3. **Verify DR Environment**
   ```bash
   # Run smoke tests
   ./tests/smoke_tests.sh --env dr --region us-west-2

   # Verify data integrity
   ./scripts/verify_data_integrity.sh

   # Check model availability
   curl https://dr.nba-mcp.com/models/list
   ```

4. **Monitor Recovery**
   - Watch CloudWatch dashboards
   - Monitor error rates
   - Track user traffic

**Expected Time:** 3-4 hours

---

### **Scenario 3: Data Corruption**

**Impact:** HIGH - Potential data loss
**Probability:** LOW
**RTO:** 3 hours
**RPO:** 15 minutes (last backup)

**Recovery Steps:**

1. **Identify Scope**
   ```bash
   # Check affected tables
   psql -h <endpoint> -U postgres -d nba_stats -c "\
     SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) \
     FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

   # Run data integrity checks
   python scripts/check_data_integrity.py --table games --date 2025-10-12
   ```

2. **Isolate Corruption**
   - Stop writes to affected tables
   - Identify corruption timestamp
   - Determine affected records

3. **Restore Clean Data**
   ```bash
   # Restore specific table from backup
   pg_restore --host=<endpoint> --username=postgres --dbname=nba_stats \
     --table=games --clean backup_2025-10-12.dump

   # Or use point-in-time recovery
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier nba-mcp-prod \
     --target-db-instance-identifier nba-mcp-pitr \
     --restore-time 2025-10-12T10:00:00Z
   ```

4. **Validate**
   ```bash
   # Run validation queries
   python scripts/validate_restored_data.py

   # Compare record counts
   ./scripts/compare_table_counts.sh
   ```

**Expected Time:** 2-3 hours

---

### **Scenario 4: Model Registry Failure**

**Impact:** MEDIUM - ML operations impacted
**Probability:** LOW
**RTO:** 2 hours
**RPO:** 1 hour

**Recovery Steps:**

1. **Backup MLflow Database**
   ```bash
   # Restore MLflow SQLite/Postgres
   aws s3 cp s3://nba-mcp-backups/mlflow/mlflow-db-latest.backup .

   # Restore to MLflow server
   pg_restore --host=mlflow-db --username=mlflow mlflow-db-latest.backup
   ```

2. **Restore Model Artifacts**
   ```bash
   # Sync from S3 backup
   aws s3 sync s3://nba-mcp-mlflow-backup/artifacts/ /mlflow/artifacts/

   # Restart MLflow server
   kubectl rollout restart deployment/mlflow
   ```

3. **Verify Models**
   ```bash
   # List registered models
   curl http://mlflow:5000/api/2.0/mlflow/registered-models/list

   # Test model loading
   python -c "import mlflow; model = mlflow.pyfunc.load_model('models:/nba_win_predictor/Production'); print('✅ Model loaded')"
   ```

**Expected Time:** 1-2 hours

---

## 🔄 BACKUP STRATEGY

### **Database Backups (RDS):**
- **Automated Snapshots:** Daily at 04:00 UTC
- **Retention:** 7 days
- **Cross-Region Replication:** Yes (us-west-2)
- **Manual Snapshots:** Before major deployments
- **Test Restores:** Monthly

### **S3 Backups:**
- **Versioning:** Enabled on all buckets
- **Cross-Region Replication:** us-east-1 → us-west-2
- **Lifecycle Policies:**
  - Move to Glacier after 90 days
  - Delete after 365 days (except prod data)

### **Configuration Backups:**
- **Git Repository:** All infrastructure as code
- **Secrets:** AWS Secrets Manager with automatic rotation
- **Kubernetes Configs:** Stored in GitOps repo

---

## 📞 CONTACT INFORMATION

### **DR Team:**

| Role | Name | Primary | Secondary |
|------|------|---------|-----------|
| **Incident Commander** | Ryan Ranft | +1-XXX-XXX-XXXX | Slack: @ryan |
| **Database Lead** | TBD | +1-XXX-XXX-XXXX | Slack: @dba |
| **Infrastructure Lead** | TBD | +1-XXX-XXX-XXXX | Slack: @infra |
| **ML Engineer** | TBD | +1-XXX-XXX-XXXX | Slack: @ml |

### **Escalation:**
1. On-call engineer (PagerDuty)
2. Team Lead
3. VP Engineering
4. CTO

---

## ✅ TESTING SCHEDULE

### **DR Drill Types:**

1. **Tabletop Exercise** (Quarterly)
   - Review scenarios
   - Walk through procedures
   - Update contact list
   - Duration: 2 hours

2. **Partial Failover** (Semi-annually)
   - Restore database backup
   - Test read replica promotion
   - Validate backup integrity
   - Duration: 4 hours

3. **Full DR Test** (Annually)
   - Complete region failover
   - All systems recovered in DR
   - End-to-end validation
   - Duration: 8 hours

### **Next Scheduled Tests:**
- ✅ Tabletop: November 15, 2025
- ✅ Partial: December 20, 2025
- ✅ Full: March 15, 2026

---

## 📝 POST-INCIDENT CHECKLIST

After any DR event:

- [ ] Document timeline of events
- [ ] Capture all recovery actions taken
- [ ] Note what worked / didn't work
- [ ] Calculate actual RTO/RPO
- [ ] Identify improvements
- [ ] Schedule post-mortem meeting
- [ ] Update DR plan based on learnings
- [ ] Communicate results to stakeholders
- [ ] Update runbooks if procedures changed

---

## 🔐 ACCESS REQUIREMENTS

**Required Access for DR:**
- AWS Console (production account)
- AWS CLI with appropriate IAM roles
- Database credentials (from Secrets Manager)
- Kubernetes cluster access (kubectl)
- Git repository access
- PagerDuty admin access
- DNS management (Route53)

**Pre-staging Checklist:**
- [ ] AWS credentials configured
- [ ] kubectl configured for both regions
- [ ] Backup scripts tested
- [ ] Contact list updated
- [ ] Runbooks accessible offline (PDF)
- [ ] DR region infrastructure pre-provisioned

---

## 📚 RELATED DOCUMENTATION

- [Runbook Collection](./runbooks/README.md)
- [Backup Verification Procedures](../scripts/verify_backups.sh)
- [Infrastructure as Code](../infrastructure/)
- [Monitoring & Alerting](../monitoring/README.md)
- [Security Incident Response](./security_incident_response.md)

---

**Document History:**
- v1.0 (2025-10-12): Initial creation
- Next Review: 2026-01-12

