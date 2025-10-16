# NBA MCP Synthesis - Rollback Procedures

## Overview

This document provides detailed rollback procedures for NBA MCP Synthesis production deployment. These procedures should be executed when critical issues arise that cannot be resolved through standard troubleshooting.

## Rollback Decision Matrix

| Issue Type | Severity | Impact | Rollback Decision |
|------------|----------|--------|-------------------|
| Application Crash | Critical | Complete outage | **IMMEDIATE ROLLBACK** |
| Data Corruption | Critical | Data loss risk | **IMMEDIATE ROLLBACK** |
| Security Breach | Critical | Security risk | **IMMEDIATE ROLLBACK** |
| Performance Degradation | High | >50% performance loss | **ROLLBACK IF PERSISTS >15 MIN** |
| Minor Functionality | Medium | Limited impact | **FIX IN PLACE** |
| Monitoring Issues | Low | No user impact | **CONTINUE, FIX POST-DEPLOYMENT** |

## Rollback Types

### 1. Application Rollback (Recommended)
**Estimated Time**: 5-10 minutes
**Impact**: Minimal downtime
**Use Case**: Application-level issues

### 2. Secrets Rollback
**Estimated Time**: 10-15 minutes
**Impact**: Brief service interruption
**Use Case**: Secret management issues

### 3. Infrastructure Rollback
**Estimated Time**: 30-60 minutes
**Impact**: Extended downtime
**Use Case**: Infrastructure-level issues

### 4. Complete System Rollback
**Estimated Time**: 2-4 hours
**Impact**: Complete outage
**Use Case**: Nuclear option for critical failures

## Rollback Procedures

### Application Rollback

#### Prerequisites
- [ ] kubectl access to EKS cluster
- [ ] Previous deployment revision available
- [ ] Team communication established

#### Steps

1. **Assess Current State**
   ```bash
   # Check current deployment status
   kubectl get deployment nba-mcp-synthesis -n nba-mcp-synthesis
   kubectl rollout history deployment/nba-mcp-synthesis -n nba-mcp-synthesis
   ```

2. **Identify Target Revision**
   ```bash
   # List available revisions
   kubectl rollout history deployment/nba-mcp-synthesis -n nba-mcp-synthesis

   # Get details of specific revision
   kubectl rollout history deployment/nba-mcp-synthesis --revision=2 -n nba-mcp-synthesis
   ```

3. **Execute Rollback**
   ```bash
   # Rollback to previous revision
   kubectl rollout undo deployment/nba-mcp-synthesis -n nba-mcp-synthesis

   # Or rollback to specific revision
   kubectl rollout undo deployment/nba-mcp-synthesis --to-revision=2 -n nba-mcp-synthesis
   ```

4. **Monitor Rollback Progress**
   ```bash
   # Watch rollout status
   kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis --timeout=300s

   # Check pod status
   kubectl get pods -n nba-mcp-synthesis -l app=nba-mcp-synthesis
   ```

5. **Verify Rollback Success**
   ```bash
   # Test health endpoints
   kubectl port-forward service/nba-mcp-synthesis-service 8080:80 -n nba-mcp-synthesis &
   curl -f http://localhost:8080/health

   # Check application logs
   kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis --tail=50
   ```

#### Success Criteria
- [ ] Previous revision successfully deployed
- [ ] All pods running and ready
- [ ] Health endpoints responding
- [ ] No critical errors in logs

#### Communication Template
```
Subject: NBA MCP Synthesis - Application Rollback Initiated

Team,

We are initiating application rollback due to [reason].

Rollback Type: Application
Target Revision: [Revision Number]
ETA: 5-10 minutes
Impact: Minimal downtime

Please standby for further updates.

Best regards,
[Name]
```

---

### Secrets Rollback

#### Prerequisites
- [ ] AWS Secrets Manager access
- [ ] Local secrets backup available
- [ ] External Secrets Operator access

#### Steps

1. **Stop External Secrets Sync**
   ```bash
   # Scale down External Secrets Operator
   kubectl scale deployment external-secrets -n external-secrets-system --replicas=0
   ```

2. **Restore Local Secrets**
   ```bash
   # Restore from backup
   cp -r backups/secrets/[timestamp]/nba-mcp-synthesis/* /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/
   ```

3. **Update Application Configuration**
   ```bash
   # Update deployment to use local secrets
   kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","env":[{"name":"USE_LOCAL_CREDENTIALS","value":"true"}]}]}}}}'
   ```

4. **Restart Application**
   ```bash
   # Restart deployment
   kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis

   # Wait for rollout
   kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis --timeout=300s
   ```

5. **Verify Secrets Access**
   ```bash
   # Test secret access
   kubectl exec -it deployment/nba-mcp-synthesis -n nba-mcp-synthesis -- env | grep -E "(API_KEY|SECRET|PASSWORD)"
   ```

#### Success Criteria
- [ ] Local secrets restored
- [ ] Application using local secrets
- [ ] All API connections working
- [ ] No secret-related errors

#### Communication Template
```
Subject: NBA MCP Synthesis - Secrets Rollback Initiated

Team,

We are initiating secrets rollback due to [reason].

Rollback Type: Secrets
Method: Restore local secrets
ETA: 10-15 minutes
Impact: Brief service interruption

Please standby for further updates.

Best regards,
[Name]
```

---

### Infrastructure Rollback

#### Prerequisites
- [ ] Terraform state available
- [ ] AWS credentials configured
- [ ] Team coordination established

#### Steps

1. **Assess Infrastructure State**
   ```bash
   # Check Terraform state
   cd infrastructure/terraform
   terraform show
   terraform state list
   ```

2. **Plan Infrastructure Rollback**
   ```bash
   # Plan rollback to previous state
   terraform plan -var-file="secrets.tfvars" -destroy
   ```

3. **Execute Infrastructure Rollback**
   ```bash
   # Destroy current infrastructure
   terraform destroy -var-file="secrets.tfvars" -auto-approve
   ```

4. **Restore Previous Infrastructure**
   ```bash
   # Apply previous configuration
   terraform apply -var-file="secrets.tfvars" -auto-approve
   ```

5. **Verify Infrastructure**
   ```bash
   # Check EKS cluster
   aws eks describe-cluster --name nba-mcp-synthesis-prod

   # Verify kubectl access
   kubectl cluster-info
   kubectl get nodes
   ```

#### Success Criteria
- [ ] Previous infrastructure restored
- [ ] EKS cluster operational
- [ ] All nodes healthy
- [ ] Network connectivity restored

#### Communication Template
```
Subject: NBA MCP Synthesis - Infrastructure Rollback Initiated

Team,

We are initiating infrastructure rollback due to [reason].

Rollback Type: Infrastructure
Method: Terraform destroy/apply
ETA: 30-60 minutes
Impact: Extended downtime

Please standby for further updates.

Best regards,
[Name]
```

---

### Complete System Rollback

#### Prerequisites
- [ ] Complete system backup available
- [ ] All team members available
- [ ] Stakeholder communication established

#### Steps

1. **Initiate Emergency Procedures**
   ```bash
   # Send emergency notification
   # Activate incident response team
   # Notify stakeholders
   ```

2. **Stop All Services**
   ```bash
   # Scale down all deployments
   kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=0
   kubectl scale deployment kube-prometheus-stack-prometheus -n monitoring --replicas=0
   kubectl scale deployment kube-prometheus-stack-grafana -n monitoring --replicas=0
   ```

3. **Destroy Current Infrastructure**
   ```bash
   # Destroy all infrastructure
   cd infrastructure/terraform
   terraform destroy -var-file="secrets.tfvars" -auto-approve
   ```

4. **Restore from Backup**
   ```bash
   # Restore complete system from backup
   # This step depends on backup strategy
   # May involve database restoration, file system restoration, etc.
   ```

5. **Verify Complete Restoration**
   ```bash
   # Verify all components restored
   # Test all functionality
   # Confirm system stability
   ```

#### Success Criteria
- [ ] Complete system restored
- [ ] All services operational
- [ ] Data integrity verified
- [ ] System stable and performing

#### Communication Template
```
Subject: URGENT - NBA MCP Synthesis - Complete System Rollback

Team,

We are initiating complete system rollback due to [critical reason].

Rollback Type: Complete System
Method: Full restoration from backup
ETA: 2-4 hours
Impact: Complete outage

This is a critical incident requiring immediate attention.

Best regards,
[Name]
```

## Rollback Validation

### Post-Rollback Checklist

#### Application Rollback
- [ ] Previous revision deployed successfully
- [ ] All pods running and ready
- [ ] Health endpoints responding correctly
- [ ] Application logs show no critical errors
- [ ] Performance metrics within acceptable range
- [ ] User functionality verified

#### Secrets Rollback
- [ ] Local secrets restored and accessible
- [ ] Application using local secrets
- [ ] All API connections working
- [ ] Database connectivity verified
- [ ] S3 access confirmed
- [ ] No secret-related errors in logs

#### Infrastructure Rollback
- [ ] Previous infrastructure restored
- [ ] EKS cluster operational and healthy
- [ ] All nodes in Ready state
- [ ] Network connectivity restored
- [ ] Load balancers operational
- [ ] Security groups configured correctly

#### Complete System Rollback
- [ ] Complete system restored
- [ ] All services operational
- [ ] Data integrity verified
- [ ] System stability confirmed
- [ ] Performance acceptable
- [ ] All integrations working

### Validation Commands

```bash
# Application validation
kubectl get pods -n nba-mcp-synthesis
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis --tail=50
curl -f http://localhost:8080/health

# Infrastructure validation
kubectl cluster-info
kubectl get nodes
aws eks describe-cluster --name nba-mcp-synthesis-prod

# Monitoring validation
kubectl get pods -n monitoring
kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
curl -f http://localhost:9090/api/v1/query?query=up
```

## Rollback Communication

### Internal Team Communication

#### Rollback Initiation
```
Subject: NBA MCP Synthesis - Rollback Initiated

Team,

We are initiating [rollback type] rollback due to [reason].

Details:
- Rollback Type: [Type]
- Reason: [Reason]
- ETA: [Time]
- Impact: [Impact]

Please standby for further updates.

Best regards,
[Name]
```

#### Rollback Progress
```
Subject: NBA MCP Synthesis - Rollback Progress

Team,

Rollback is in progress.

Current Status: [Status]
Progress: [Percentage]
ETA: [Updated time]

[Additional details]

Best regards,
[Name]
```

#### Rollback Complete
```
Subject: NBA MCP Synthesis - Rollback Complete

Team,

Rollback has been completed successfully.

Status: SUCCESS
Duration: [Time]
Issues: [None/Minor/Major]

The system is now stable and operational.

Best regards,
[Name]
```

### Stakeholder Communication

#### Rollback Notification
```
Subject: NBA MCP Synthesis - Service Interruption

Stakeholders,

We are experiencing issues with the NBA MCP Synthesis deployment and are initiating rollback procedures.

Impact: [Impact description]
ETA: [Estimated time]
Next Update: [Time]

We will provide regular updates throughout the process.

Best regards,
[Name]
```

## Post-Rollback Procedures

### Immediate Actions (First 30 minutes)
- [ ] Verify system stability
- [ ] Monitor critical metrics
- [ ] Check for any remaining issues
- [ ] Notify stakeholders of resolution
- [ ] Document incident details

### Short-term Actions (First 2 hours)
- [ ] Conduct root cause analysis
- [ ] Identify lessons learned
- [ ] Plan remediation steps
- [ ] Update procedures if needed
- [ ] Schedule post-incident review

### Long-term Actions (First 24 hours)
- [ ] Complete incident documentation
- [ ] Conduct post-mortem meeting
- [ ] Implement preventive measures
- [ ] Update rollback procedures
- [ ] Plan future deployment strategy

## Rollback Prevention

### Pre-Deployment Measures
- [ ] Comprehensive testing in staging
- [ ] Rollback procedures tested
- [ ] Backup systems verified
- [ ] Team training completed
- [ ] Communication protocols established

### During Deployment
- [ ] Continuous monitoring
- [ ] Early issue detection
- [ ] Quick response protocols
- [ ] Clear escalation procedures
- [ ] Regular status updates

### Post-Deployment
- [ ] Extended monitoring period
- [ ] Performance validation
- [ ] User acceptance testing
- [ ] Feedback collection
- [ ] Continuous improvement

## Emergency Contacts

### Primary Contacts
- **Deployment Lead**: [Name] - [Phone] - [Email]
- **Technical Lead**: [Name] - [Phone] - [Email]
- **DevOps Lead**: [Name] - [Phone] - [Email]

### Secondary Contacts
- **Application Engineer**: [Name] - [Phone] - [Email]
- **Infrastructure Engineer**: [Name] - [Phone] - [Email]
- **Security Lead**: [Name] - [Phone] - [Email]

### External Contacts
- **AWS Support**: [Support case URL]
- **PagerDuty**: [Service URL]
- **Slack Channel**: `#nba-mcp-synthesis-alerts`

---

**Rollback Procedures Complete**: NBA MCP Synthesis rollback procedures documented and ready for execution.

**Next Steps**: Follow `POST_DEPLOYMENT_OPS.md` for ongoing operational procedures after successful rollback.

