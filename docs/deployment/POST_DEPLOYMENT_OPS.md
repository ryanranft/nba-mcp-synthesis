# Post-Deployment Operations Guide

## Overview

This guide covers ongoing operations, monitoring, maintenance, and optimization tasks for the NBA MCP Synthesis system after successful deployment to production.

## Table of Contents

1. [Initial Post-Deployment Tasks](#initial-post-deployment-tasks)
2. [Daily Operations](#daily-operations)
3. [Weekly Maintenance](#weekly-maintenance)
4. [Monthly Reviews](#monthly-reviews)
5. [Performance Monitoring](#performance-monitoring)
6. [Security Operations](#security-operations)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling Operations](#scaling-operations)
9. [Incident Response](#incident-response)
10. [Documentation Updates](#documentation-updates)

## Initial Post-Deployment Tasks

### First 24 Hours

#### Immediate Verification (0-2 hours)
```bash
# Verify all services are running
kubectl get pods -n nba-mcp-synthesis
kubectl get services -n nba-mcp-synthesis
kubectl get ingress -n nba-mcp-synthesis

# Check application health
curl -f https://nba-mcp-synthesis.example.com/health
curl -f https://nba-mcp-synthesis.example.com/metrics

# Verify monitoring stack
kubectl get pods -n monitoring
```

#### Performance Baseline (2-6 hours)
```bash
# Run comprehensive health checks
./scripts/health_check_production.sh

# Generate initial performance report
python3 scripts/validate_deployment.py --generate-report

# Check resource utilization
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes
```

#### Alert Configuration (6-12 hours)
```bash
# Verify alerting rules are active
kubectl get prometheusrules -n monitoring

# Test alert channels
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert from NBA MCP Synthesis"}' \
  $SLACK_WEBHOOK_URL

# Configure PagerDuty integration
# (Manual step - configure in PagerDuty dashboard)
```

#### Documentation Review (12-24 hours)
- Review deployment logs
- Update runbooks with any issues encountered
- Document any configuration changes made during deployment
- Verify all team members have access to monitoring dashboards

### First Week

#### Daily Health Checks
```bash
#!/bin/bash
# scripts/daily_health_check.sh

echo "=== NBA MCP Synthesis Daily Health Check ==="
echo "Date: $(date)"

# Application health
echo "1. Application Status:"
kubectl get pods -n nba-mcp-synthesis --no-headers | awk '{print $1, $3}'

# Database connectivity
echo "2. Database Status:"
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import psycopg2; print('DB: OK')" 2>/dev/null || echo "DB: ERROR"

# S3 connectivity
echo "3. S3 Status:"
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import boto3; print('S3: OK')" 2>/dev/null || echo "S3: ERROR"

# API endpoints
echo "4. API Endpoints:"
curl -s -o /dev/null -w "%{http_code}" https://nba-mcp-synthesis.example.com/health
echo " - Health endpoint"

# Resource usage
echo "5. Resource Usage:"
kubectl top pods -n nba-mcp-synthesis --no-headers | head -5

echo "=== Health Check Complete ==="
```

#### Performance Monitoring Setup
```bash
# Configure Grafana dashboards
kubectl port-forward -n monitoring svc/grafana 3000:80 &
# Access http://localhost:3000 and import dashboards

# Set up custom metrics collection
kubectl apply -f k8s/servicemonitor.yaml

# Configure log aggregation
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --tail=100
```

## Daily Operations

### Morning Checklist

#### System Health Review
```bash
# Check overnight alerts
kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp' | tail -20

# Review resource usage trends
kubectl top pods -n nba-mcp-synthesis --containers

# Check application logs for errors
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --since=24h | grep -i error
```

#### Performance Metrics
```bash
# CPU and Memory usage
kubectl top pods -n nba-mcp-synthesis

# Network I/O
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  cat /proc/net/dev

# Disk usage
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  df -h
```

#### Security Monitoring
```bash
# Check for security events
kubectl get events -n nba-mcp-synthesis | grep -i security

# Review access logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | grep -i "access\|auth"

# Verify secret rotation status
aws secretsmanager describe-secret --secret-id nba-mcp-synthesis/production
```

### Afternoon Tasks

#### Capacity Planning
```bash
# Analyze resource trends
kubectl top pods -n nba-mcp-synthesis --sort-by=cpu
kubectl top pods -n nba-mcp-synthesis --sort-by=memory

# Check HPA status
kubectl get hpa -n nba-mcp-synthesis

# Review scaling events
kubectl describe hpa -n nba-mcp-synthesis
```

#### Backup Verification
```bash
# Database backup status
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_dump --version

# S3 backup verification
aws s3 ls s3://nba-mcp-synthesis-backups/ --recursive | tail -10

# Configuration backup
kubectl get configmap -n nba-mcp-synthesis -o yaml > \
  backups/configmaps-$(date +%Y%m%d).yaml
```

## Weekly Maintenance

### Monday: Performance Review

#### Resource Optimization
```bash
# Analyze resource usage patterns
kubectl top pods -n nba-mcp-synthesis --sort-by=cpu
kubectl top pods -n nba-mcp-synthesis --sort-by=memory

# Review HPA metrics
kubectl get hpa -n nba-mcp-synthesis
kubectl describe hpa -n nba-mcp-synthesis

# Check for resource requests/limits optimization
kubectl get pods -n nba-mcp-synthesis -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'
```

#### Performance Tuning
```bash
# Database performance
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -c "SELECT * FROM pg_stat_activity;"

# Application performance
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import time; print('Response time test')"

# Cache performance
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-redis -- \
  redis-cli info stats
```

### Wednesday: Security Review

#### Security Audit
```bash
# Check for security updates
kubectl get pods -n nba-mcp-synthesis -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'

# Review access patterns
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(login|auth|access)" | tail -50

# Check secret rotation
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)]'
```

#### Vulnerability Assessment
```bash
# Scan container images
trivy image nba-mcp-synthesis:latest

# Check Kubernetes security
kubectl get networkpolicies -n nba-mcp-synthesis
kubectl get podsecuritypolicies

# Review RBAC
kubectl get roles,rolebindings,clusterroles,clusterrolebindings -n nba-mcp-synthesis
```

### Friday: Backup and Recovery Testing

#### Backup Verification
```bash
# Test database restore
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_restore --help

# Verify S3 backups
aws s3 ls s3://nba-mcp-synthesis-backups/ --recursive

# Test configuration restore
kubectl apply -f backups/configmaps-$(date +%Y%m%d).yaml --dry-run=client
```

#### Disaster Recovery Testing
```bash
# Test pod restart
kubectl delete pod -n nba-mcp-synthesis -l app=nba-mcp-synthesis

# Test node failure simulation
kubectl drain <node-name> --ignore-daemonsets

# Test ingress failover
kubectl get ingress -n nba-mcp-synthesis
```

## Monthly Reviews

### Performance Analysis

#### Resource Utilization Trends
```bash
# Generate monthly resource report
kubectl top pods -n nba-mcp-synthesis --sort-by=cpu > \
  reports/resource-usage-$(date +%Y%m).txt

# Analyze scaling patterns
kubectl get events -n nba-mcp-synthesis --field-selector reason=SuccessfulRescale | \
  grep $(date +%Y-%m) > reports/scaling-events-$(date +%Y%m).txt
```

#### Cost Optimization
```bash
# Review AWS costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Analyze resource efficiency
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

### Security Review

#### Access Audit
```bash
# Review user access patterns
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(user|access|login)" | wc -l

# Check API usage
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(api|request)" | tail -100
```

#### Compliance Check
```bash
# Verify security policies
kubectl get networkpolicies -n nba-mcp-synthesis
kubectl get podsecuritypolicies

# Check secret management
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)]'
```

## Performance Monitoring

### Key Metrics to Track

#### Application Metrics
- Response time (p50, p95, p99)
- Throughput (requests per second)
- Error rate
- Memory usage
- CPU utilization

#### Infrastructure Metrics
- Pod resource usage
- Node resource utilization
- Network I/O
- Storage I/O
- Database connections

#### Business Metrics
- Active users
- API calls per hour
- Data processing volume
- System availability

### Monitoring Commands

#### Real-time Monitoring
```bash
# Watch pod status
watch kubectl get pods -n nba-mcp-synthesis

# Monitor resource usage
watch kubectl top pods -n nba-mcp-synthesis

# Track logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis -f
```

#### Historical Analysis
```bash
# Generate performance report
python3 scripts/performance_analysis.py --start-date 2024-01-01 --end-date 2024-01-31

# Analyze error patterns
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --since=7d | \
  grep -i error | sort | uniq -c | sort -nr
```

## Security Operations

### Daily Security Tasks

#### Access Monitoring
```bash
# Check authentication logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(auth|login|access)" | tail -20

# Review API access patterns
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(api|request)" | tail -50
```

#### Threat Detection
```bash
# Check for suspicious activity
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis | \
  grep -E "(error|exception|fail)" | tail -30

# Monitor network traffic
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  netstat -tuln
```

### Weekly Security Tasks

#### Vulnerability Scanning
```bash
# Scan container images
trivy image nba-mcp-synthesis:latest

# Check for security updates
kubectl get pods -n nba-mcp-synthesis -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'
```

#### Access Review
```bash
# Review user permissions
kubectl get roles,rolebindings -n nba-mcp-synthesis

# Check service account usage
kubectl get serviceaccounts -n nba-mcp-synthesis
```

## Backup and Recovery

### Daily Backup Tasks

#### Database Backups
```bash
# Automated database backup
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_dump -U postgres nba_mcp_synthesis > \
  backups/db-backup-$(date +%Y%m%d).sql

# Verify backup integrity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_restore --list backups/db-backup-$(date +%Y%m%d).sql
```

#### Configuration Backups
```bash
# Backup Kubernetes configurations
kubectl get all -n nba-mcp-synthesis -o yaml > \
  backups/k8s-config-$(date +%Y%m%d).yaml

# Backup secrets (encrypted)
kubectl get secrets -n nba-mcp-synthesis -o yaml > \
  backups/secrets-$(date +%Y%m%d).yaml
```

### Weekly Recovery Testing

#### Database Recovery Test
```bash
# Test database restore
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_restore --help

# Verify backup completeness
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -c "SELECT COUNT(*) FROM information_schema.tables;"
```

#### Application Recovery Test
```bash
# Test pod restart
kubectl delete pod -n nba-mcp-synthesis -l app=nba-mcp-synthesis

# Verify service recovery
kubectl get pods -n nba-mcp-synthesis
kubectl get services -n nba-mcp-synthesis
```

## Scaling Operations

### Horizontal Scaling

#### Auto-scaling Configuration
```bash
# Check HPA status
kubectl get hpa -n nba-mcp-synthesis

# Review scaling metrics
kubectl describe hpa -n nba-mcp-synthesis

# Adjust scaling parameters
kubectl patch hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis -p \
  '{"spec":{"minReplicas":2,"maxReplicas":10}}'
```

#### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=5

# Verify scaling
kubectl get pods -n nba-mcp-synthesis
```

### Vertical Scaling

#### Resource Adjustment
```bash
# Update resource requests/limits
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","resources":{"requests":{"memory":"1Gi","cpu":"500m"},"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'

# Verify changes
kubectl describe deployment nba-mcp-synthesis -n nba-mcp-synthesis
```

## Incident Response

### Incident Classification

#### Severity Levels
- **P1 (Critical)**: Complete service outage
- **P2 (High)**: Significant functionality impact
- **P3 (Medium)**: Minor functionality impact
- **P4 (Low)**: Cosmetic or non-functional issues

#### Response Procedures

##### P1 Incident Response
```bash
# Immediate response
kubectl get pods -n nba-mcp-synthesis
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --tail=100

# Check system resources
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes

# Verify external dependencies
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import requests; print(requests.get('https://api.example.com').status_code)"
```

##### P2 Incident Response
```bash
# Check application health
curl -f https://nba-mcp-synthesis.example.com/health

# Review recent changes
kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp' | tail -20

# Analyze performance metrics
kubectl top pods -n nba-mcp-synthesis --sort-by=cpu
```

### Post-Incident Review

#### Incident Documentation
```bash
# Collect system state
kubectl get all -n nba-mcp-synthesis > incident-reports/system-state-$(date +%Y%m%d).txt

# Gather logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --since=1h > \
  incident-reports/logs-$(date +%Y%m%d).txt

# Document resolution steps
echo "Incident resolved at $(date)" >> incident-reports/resolution-$(date +%Y%m%d).txt
```

## Documentation Updates

### Regular Documentation Tasks

#### Weekly Updates
- Update runbooks with any new procedures
- Document any configuration changes
- Review and update troubleshooting guides

#### Monthly Updates
- Update architecture diagrams
- Review and update security procedures
- Update disaster recovery procedures

#### Quarterly Updates
- Comprehensive documentation review
- Update training materials
- Review and update operational procedures

### Documentation Standards

#### Change Documentation
```bash
# Document configuration changes
echo "$(date): Updated resource limits for nba-mcp-synthesis" >> \
  docs/changelog.md

# Update runbooks
echo "New procedure added: $(date)" >> docs/runbooks/README.md
```

#### Incident Documentation
```bash
# Create incident report template
cat > incident-reports/template.md << EOF
# Incident Report Template

## Incident Details
- **Date**:
- **Time**:
- **Severity**:
- **Duration**:

## Description
Brief description of the incident

## Root Cause
Analysis of the root cause

## Resolution
Steps taken to resolve the incident

## Prevention
Measures to prevent similar incidents

## Lessons Learned
Key takeaways from the incident
EOF
```

## Conclusion

This guide provides a comprehensive framework for post-deployment operations. Regular execution of these tasks ensures:

- **High Availability**: Proactive monitoring and maintenance
- **Performance**: Continuous optimization and scaling
- **Security**: Regular security reviews and updates
- **Reliability**: Comprehensive backup and recovery procedures
- **Documentation**: Up-to-date operational procedures

For questions or clarifications, refer to the troubleshooting guide or contact the operations team.

---

**Last Updated**: $(date)
**Version**: 1.0
**Next Review**: $(date -d "+1 month")

