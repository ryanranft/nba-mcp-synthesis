# NBA MCP Synthesis - Operational Runbook

## Overview

This runbook provides operational procedures for the NBA MCP Synthesis production system deployed on AWS EKS.

## Table of Contents

1. [System Overview](#system-overview)
2. [Deployment Procedures](#deployment-procedures)
3. [Rollback Procedures](#rollback-procedures)
4. [Scaling Procedures](#scaling-procedures)
5. [Incident Response](#incident-response)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [On-Call Rotation](#on-call-rotation)
8. [Emergency Contacts](#emergency-contacts)

## System Overview

### Architecture
- **Platform**: AWS EKS (Kubernetes)
- **Namespace**: `nba-mcp-synthesis`
- **Deployment**: `nba-mcp-synthesis`
- **Service**: `nba-mcp-synthesis-service`
- **Ingress**: AWS Application Load Balancer
- **Monitoring**: Prometheus + Grafana + PagerDuty
- **Secrets**: AWS Secrets Manager + External Secrets Operator

### Key Components
- NBA MCP Synthesis Application
- PostgreSQL Database (RDS)
- S3 Data Lake
- AWS Glue Data Catalog
- Prometheus Metrics Collection
- Grafana Dashboards
- Alertmanager + PagerDuty Integration

## Deployment Procedures

### Standard Deployment

1. **Pre-deployment Checklist**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity

   # Check EKS cluster connectivity
   kubectl cluster-info

   # Verify namespace exists
   kubectl get namespace nba-mcp-synthesis

   # Check current deployment status
   kubectl get deployment nba-mcp-synthesis -n nba-mcp-synthesis
   ```

2. **Build and Push Docker Image**
   ```bash
   # Build and push to ECR
   ./scripts/push_to_ecr.sh latest

   # Verify image exists
   aws ecr describe-images --repository-name nba-mcp-synthesis --image-ids imageTag=latest
   ```

3. **Deploy to Production**
   ```bash
   # Run comprehensive deployment script
   ./scripts/deploy_production.sh latest

   # Or manual deployment
   kubectl set image deployment/nba-mcp-synthesis \
     nba-mcp-synthesis=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/nba-mcp-synthesis:latest \
     -n nba-mcp-synthesis

   # Wait for rollout
   kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
   ```

4. **Post-deployment Verification**
   ```bash
   # Check pod status
   kubectl get pods -l app=nba-mcp-synthesis -n nba-mcp-synthesis

   # Verify health endpoints
   kubectl port-forward service/nba-mcp-synthesis-service 8080:80 -n nba-mcp-synthesis
   curl http://localhost:8080/health
   curl http://localhost:8080/metrics
   ```

### Emergency Deployment

For critical fixes that bypass normal CI/CD:

1. **Quick Fix Deployment**
   ```bash
   # Build and push emergency image
   ./scripts/push_to_ecr.sh emergency-$(date +%Y%m%d-%H%M%S)

   # Deploy immediately
   kubectl set image deployment/nba-mcp-synthesis \
     nba-mcp-synthesis=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/nba-mcp-synthesis:emergency-TAG \
     -n nba-mcp-synthesis
   ```

2. **Monitor Deployment**
   ```bash
   # Watch rollout progress
   kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis --watch
   ```

## Rollback Procedures

### Automatic Rollback

The deployment script automatically rolls back on failure:

```bash
# Manual rollback
kubectl rollout undo deployment/nba-mcp-synthesis -n nba-mcp-synthesis
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### Manual Rollback to Specific Version

```bash
# List rollout history
kubectl rollout history deployment/nba-mcp-synthesis -n nba-mcp-synthesis

# Rollback to specific revision
kubectl rollout undo deployment/nba-mcp-synthesis --to-revision=REVISION -n nba-mcp-synthesis
```

### Emergency Rollback

```bash
# Scale down current deployment
kubectl scale deployment nba-mcp-synthesis --replicas=0 -n nba-mcp-synthesis

# Deploy previous known-good image
kubectl set image deployment/nba-mcp-synthesis \
  nba-mcp-synthesis=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/nba-mcp-synthesis:PREVIOUS_TAG \
  -n nba-mcp-synthesis

# Scale back up
kubectl scale deployment nba-mcp-synthesis --replicas=3 -n nba-mcp-synthesis
```

## Scaling Procedures

### Horizontal Pod Autoscaler (HPA)

The system uses HPA for automatic scaling:

```bash
# Check HPA status
kubectl get hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis

# View HPA metrics
kubectl describe hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis
```

### Manual Scaling

```bash
# Scale up
kubectl scale deployment nba-mcp-synthesis --replicas=5 -n nba-mcp-synthesis

# Scale down
kubectl scale deployment nba-mcp-synthesis --replicas=2 -n nba-mcp-synthesis

# Check scaling status
kubectl get pods -l app=nba-mcp-synthesis -n nba-mcp-synthesis
```

### Vertical Scaling (Resource Limits)

```bash
# Update resource limits
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "nba-mcp-synthesis",
          "resources": {
            "requests": {"memory": "2Gi", "cpu": "1000m"},
            "limits": {"memory": "4Gi", "cpu": "2000m"}
          }
        }]
      }
    }
  }
}'
```

## Incident Response

### Severity Classification

- **P1 (Critical)**: Complete service outage, data loss, security breach
- **P2 (High)**: Significant functionality degraded, performance issues
- **P3 (Medium)**: Minor functionality issues, non-critical alerts
- **P4 (Low)**: Cosmetic issues, enhancement requests

### P1 Incident Response

1. **Immediate Actions**
   - Acknowledge alert in PagerDuty
   - Join incident Slack channel: `#incident-response`
   - Assess impact and scope
   - Notify stakeholders

2. **Investigation**
   ```bash
   # Check system status
   kubectl get pods -n nba-mcp-synthesis
   kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp'

   # Check logs
   kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis --tail=100

   # Check metrics
   kubectl port-forward service/nba-mcp-synthesis-service 8080:80 -n nba-mcp-synthesis
   curl http://localhost:8080/metrics
   ```

3. **Resolution**
   - Implement fix or workaround
   - Monitor for resolution
   - Document incident details

4. **Post-Incident**
   - Conduct post-mortem within 48 hours
   - Update runbooks if needed
   - Implement preventive measures

### Common Issues and Solutions

#### Pod CrashLoopBackOff
```bash
# Check pod logs
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis

# Check pod description
kubectl describe pod POD_NAME -n nba-mcp-synthesis

# Common fixes:
# 1. Check secrets are properly loaded
# 2. Verify database connectivity
# 3. Check resource limits
# 4. Restart deployment
kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n nba-mcp-synthesis

# Check HPA status
kubectl get hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis

# Scale up if needed
kubectl scale deployment nba-mcp-synthesis --replicas=5 -n nba-mcp-synthesis
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl run db-test --image=postgres:13 --rm -it --restart=Never -- \
  psql -h nba-simulator-db.cluster-xyz.us-east-1.rds.amazonaws.com -U username -d nba_simulator

# Check secrets
kubectl get secret nba-mcp-synthesis-secrets -n nba-mcp-synthesis -o yaml
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Application Metrics**
   - Request rate and latency
   - Error rate
   - Active connections
   - Secret validation status

2. **Infrastructure Metrics**
   - Pod CPU/Memory usage
   - Node health
   - Database connections
   - S3 operation latency

3. **Business Metrics**
   - API call success rate
   - Data processing throughput
   - Cost per operation

### Grafana Dashboards

- **Main Dashboard**: `https://grafana.nba-mcp-synthesis.example.com/d/nba-mcp-dashboard`
- **Secrets Health**: `https://grafana.nba-mcp-synthesis.example.com/d/secrets-health-dashboard`
- **Infrastructure**: `https://grafana.nba-mcp-synthesis.example.com/d/kubernetes-cluster-monitoring`

### Alerting Rules

Critical alerts are routed to PagerDuty:
- High error rate (>5% for 5 minutes)
- Pod memory usage >90%
- Secret validation failures
- Database connection failures
- Service unavailable

### Manual Health Checks

```bash
# Application health
curl -f https://nba-mcp-synthesis.example.com/health

# Metrics endpoint
curl -f https://nba-mcp-synthesis.example.com/metrics

# Database connectivity
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
from mcp_server.connectors import RDSConnector
manager = UnifiedSecretsManager('nba-mcp-synthesis')
manager.load_secrets_hierarchical('production')
connector = RDSConnector()
print('DB OK' if connector.test_connection() else 'DB FAILED')
"
```

## On-Call Rotation

### Primary On-Call
- **Schedule**: Monday-Friday, 9 AM - 5 PM EST
- **Responsibilities**: P1/P2 incidents, deployments, monitoring
- **Escalation**: PagerDuty → Slack → Phone

### Secondary On-Call
- **Schedule**: Monday-Friday, 5 PM - 9 AM EST, Weekends
- **Responsibilities**: P1 incidents only, escalate to primary
- **Escalation**: PagerDuty → Slack

### On-Call Handoff

**Daily Handoff (9 AM EST)**
1. Review overnight alerts
2. Check system status
3. Review any incidents
4. Update handoff notes in Slack

**Weekly Handoff (Monday 9 AM EST)**
1. Review previous week's incidents
2. Check system health trends
3. Review upcoming deployments
4. Update on-call schedule

## Emergency Contacts

### Internal Team
- **Primary On-Call**: [Contact Info]
- **Secondary On-Call**: [Contact Info]
- **Team Lead**: [Contact Info]
- **Engineering Manager**: [Contact Info]

### External Services
- **AWS Support**: [Support Case URL]
- **PagerDuty**: [PagerDuty URL]
- **Slack Channel**: `#nba-mcp-synthesis-alerts`

### Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| P1 | 15 minutes | On-Call → Team Lead → Manager |
| P2 | 1 hour | On-Call → Team Lead |
| P3 | 4 hours | On-Call |
| P4 | Next business day | On-Call |

## Maintenance Windows

### Scheduled Maintenance
- **Database Backups**: Daily at 2 AM EST
- **Secret Rotation**: Monthly
- **Security Updates**: As needed
- **Capacity Planning**: Monthly review

### Maintenance Procedures

1. **Database Backup Verification**
   ```bash
   # Check backup status
   aws rds describe-db-snapshots --db-instance-identifier nba-simulator-db

   # Verify backup integrity
   # (Implementation depends on backup verification process)
   ```

2. **Secret Rotation**
   ```bash
   # Run secret rotation script
   python3 scripts/rotate_secrets.py --dry-run
   python3 scripts/rotate_secrets.py

   # Verify rotation
   python3 scripts/migrate_secrets_to_aws.py --verify
   ```

## Troubleshooting Commands

### Quick Diagnostics
```bash
# System overview
kubectl get all -n nba-mcp-synthesis

# Pod status
kubectl get pods -n nba-mcp-synthesis -o wide

# Service endpoints
kubectl get svc -n nba-mcp-synthesis

# Recent events
kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes
```

### Log Analysis
```bash
# Application logs
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis --tail=100

# Logs from specific pod
kubectl logs POD_NAME -n nba-mcp-synthesis --tail=100

# Follow logs in real-time
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis -f

# Logs with timestamps
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis --timestamps
```

### Network Diagnostics
```bash
# Test connectivity from pod
kubectl exec -it POD_NAME -n nba-mcp-synthesis -- curl http://localhost:8000/health

# Test external connectivity
kubectl exec -it POD_NAME -n nba-mcp-synthesis -- curl https://api.openai.com/v1/models

# Check DNS resolution
kubectl exec -it POD_NAME -n nba-mcp-synthesis -- nslookup nba-simulator-db.cluster-xyz.us-east-1.rds.amazonaws.com
```

This runbook should be reviewed and updated regularly based on operational experience and system changes.


