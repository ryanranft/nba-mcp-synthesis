# NBA MCP Synthesis - Go-Live Runbook

## Overview

This runbook provides a detailed hour-by-hour timeline for the NBA MCP Synthesis production go-live deployment. Follow this guide precisely to ensure a smooth, successful launch.

## Pre-Go-Live Checklist

### Team Readiness
- [ ] All team members available and on-call
- [ ] Communication channels established
- [ ] Emergency contacts verified
- [ ] Rollback procedures tested
- [ ] Monitoring dashboards accessible

### Technical Readiness
- [ ] All prerequisites completed (see `PRE_DEPLOYMENT_CHECKLIST.md`)
- [ ] Staging environment validated
- [ ] Backup procedures tested
- [ ] Monitoring stack operational
- [ ] Alerting configured and tested

## Go-Live Timeline

### T-24 Hours: Final Pre-Checks

**Time**: 24 hours before go-live
**Duration**: 2 hours
**Team**: DevOps Lead, Technical Lead

#### Tasks
- [ ] **Infrastructure Verification**
  - Verify EKS cluster health
  - Check node capacity and scaling
  - Validate network connectivity
  - Confirm backup systems operational

- [ ] **Application Validation**
  - Run full test suite in staging
  - Verify all integrations working
  - Test monitoring and alerting
  - Validate secret management

- [ ] **Team Briefing**
  - Review go-live timeline
  - Confirm communication protocols
  - Verify emergency procedures
  - Distribute contact information

#### Success Criteria
- All systems green in staging
- Team fully briefed and ready
- Emergency procedures validated

#### Communication
- Send status update to stakeholders
- Confirm go-live window with team

---

### T-4 Hours: Team Briefing

**Time**: 4 hours before go-live
**Duration**: 1 hour
**Team**: All deployment team members

#### Tasks
- [ ] **Final Team Briefing**
  - Review deployment timeline
  - Confirm roles and responsibilities
  - Verify communication channels
  - Test emergency escalation

- [ ] **Environment Preparation**
  - Clear any staging deployments
  - Prepare production environment
  - Verify AWS quotas and limits
  - Check monitoring dashboards

#### Success Criteria
- All team members present and ready
- Communication channels tested
- Environment prepared for deployment

#### Communication
- Team briefing completed
- Stakeholders notified of upcoming deployment

---

### T-2 Hours: Infrastructure Verification

**Time**: 2 hours before go-live
**Duration**: 30 minutes
**Team**: DevOps Lead, Infrastructure Engineer

#### Tasks
- [ ] **Final Infrastructure Check**
  ```bash
  # Check EKS cluster status
  kubectl cluster-info
  kubectl get nodes

  # Verify AWS services
  aws eks describe-cluster --name nba-mcp-synthesis-prod
  aws secretsmanager list-secrets
  ```

- [ ] **Resource Validation**
  - Confirm sufficient node capacity
  - Verify auto-scaling configured
  - Check load balancer health
  - Validate security groups

#### Success Criteria
- All infrastructure components healthy
- Sufficient capacity for deployment
- No critical alerts

#### Communication
- Infrastructure status: GREEN
- Ready to proceed with deployment

---

### T-1 Hour: Deploy to Staging

**Time**: 1 hour before go-live
**Duration**: 30 minutes
**Team**: DevOps Lead, Application Engineer

#### Tasks
- [ ] **Staging Deployment**
  ```bash
  # Deploy to staging environment
  ./scripts/deploy_phase1_infrastructure.sh --dry-run
  ./scripts/deploy_phase2_secrets.sh --dry-run
  ./scripts/deploy_phase3_application.sh --dry-run
  ./scripts/deploy_phase4_monitoring.sh --dry-run
  ```

- [ ] **Staging Validation**
  - Verify all components deploy successfully
  - Test application functionality
  - Confirm monitoring working
  - Validate alerting

#### Success Criteria
- Staging deployment successful
- All tests passing
- Monitoring operational

#### Communication
- Staging deployment: SUCCESS
- Ready for production deployment

---

### T-30 Minutes: Final Smoke Tests

**Time**: 30 minutes before go-live
**Duration**: 15 minutes
**Team**: QA Lead, Application Engineer

#### Tasks
- [ ] **Critical Path Testing**
  - Test application startup
  - Verify database connectivity
  - Test API endpoints
  - Confirm monitoring metrics

- [ ] **Rollback Preparation**
  - Verify rollback procedures
  - Test backup restoration
  - Confirm emergency contacts
  - Prepare rollback commands

#### Success Criteria
- All smoke tests passing
- Rollback procedures ready
- Team prepared for deployment

#### Communication
- Smoke tests: PASSED
- Ready for production deployment

---

### T-0: Production Deployment

**Time**: Go-live time
**Duration**: 2 hours
**Team**: All deployment team members

#### Phase 1: Infrastructure (30 minutes)
**Team**: DevOps Lead, Infrastructure Engineer

- [ ] **Deploy Infrastructure**
  ```bash
  # Execute Phase 1
  ./scripts/deploy_phase1_infrastructure.sh
  ```

- [ ] **Verify Infrastructure**
  - Check EKS cluster status
  - Verify node health
  - Confirm External Secrets Operator
  - Validate network connectivity

#### Phase 2: Secrets Migration (30 minutes)
**Team**: Security Lead, DevOps Lead

- [ ] **Migrate Secrets**
  ```bash
  # Execute Phase 2
  ./scripts/deploy_phase2_secrets.sh
  ```

- [ ] **Verify Secrets**
  - Confirm AWS Secrets Manager
  - Test External Secrets sync
  - Validate Kubernetes secrets
  - Test secret access

#### Phase 3: Application Deployment (45 minutes)
**Team**: Application Engineer, DevOps Lead

- [ ] **Deploy Application**
  ```bash
  # Execute Phase 3
  ./scripts/deploy_phase3_application.sh
  ```

- [ ] **Verify Application**
  - Check pod status
  - Test health endpoints
  - Verify service connectivity
  - Confirm ingress working

#### Phase 4: Monitoring Setup (15 minutes)
**Team**: DevOps Lead, Monitoring Engineer

- [ ] **Deploy Monitoring**
  ```bash
  # Execute Phase 4
  ./scripts/deploy_phase4_monitoring.sh
  ```

- [ ] **Verify Monitoring**
  - Check Prometheus targets
  - Verify Grafana dashboards
  - Test alerting rules
  - Confirm metrics collection

#### Success Criteria
- All phases completed successfully
- Application responding correctly
- Monitoring operational
- No critical errors

#### Communication
- Production deployment: SUCCESS
- Application live and operational

---

### T+15 Minutes: Initial Validation

**Time**: 15 minutes after go-live
**Duration**: 30 minutes
**Team**: All deployment team members

#### Tasks
- [ ] **Comprehensive Health Check**
  ```bash
  # Run validation suite
  python3 scripts/validate_deployment.py
  ```

- [ ] **Critical Functionality Test**
  - Test all API endpoints
  - Verify database operations
  - Test S3 connectivity
  - Confirm external integrations

- [ ] **Monitoring Verification**
  - Check Grafana dashboards
  - Verify Prometheus metrics
  - Test alerting notifications
  - Confirm log aggregation

#### Success Criteria
- All validation checks passing
- Critical functionality working
- Monitoring fully operational

#### Communication
- Initial validation: SUCCESS
- System fully operational

---

### T+1 Hour: Extended Monitoring

**Time**: 1 hour after go-live
**Duration**: 2 hours
**Team**: On-call Engineer, DevOps Lead

#### Tasks
- [ ] **Performance Monitoring**
  - Monitor response times
  - Check resource utilization
  - Verify auto-scaling
  - Monitor error rates

- [ ] **User Acceptance Testing**
  - Test end-to-end workflows
  - Verify user interfaces
  - Test all integrations
  - Confirm data accuracy

- [ ] **Alert Tuning**
  - Adjust alert thresholds
  - Test notification channels
  - Verify escalation procedures
  - Confirm on-call rotation

#### Success Criteria
- Performance within acceptable limits
- No critical issues identified
- Alerting properly configured

#### Communication
- Extended monitoring: STABLE
- System performing as expected

---

### T+24 Hours: Post-Launch Review

**Time**: 24 hours after go-live
**Duration**: 1 hour
**Team**: All deployment team members

#### Tasks
- [ ] **Performance Analysis**
  - Review 24-hour metrics
  - Analyze performance trends
  - Identify optimization opportunities
  - Document lessons learned

- [ ] **Incident Review**
  - Review any incidents
  - Analyze root causes
  - Document improvements
  - Update procedures

- [ ] **Team Debrief**
  - Review deployment process
  - Identify successes and challenges
  - Plan improvements
  - Celebrate success

#### Success Criteria
- System stable and performing well
- No critical issues
- Team satisfied with deployment

#### Communication
- Post-launch review: SUCCESS
- System fully operational and stable

## Communication Templates

### Status Updates

#### Pre-Deployment
```
Subject: NBA MCP Synthesis - Pre-Deployment Status

Team,

We are preparing for the NBA MCP Synthesis production deployment.

Current Status: [GREEN/YELLOW/RED]
Next Milestone: [Description]
Timeline: [Time]

Please ensure you are available during the deployment window.

Best regards,
[Name]
```

#### During Deployment
```
Subject: NBA MCP Synthesis - Deployment Update

Team,

NBA MCP Synthesis deployment is in progress.

Current Phase: [Phase Name]
Status: [SUCCESS/IN_PROGRESS/ISSUE]
Duration: [Time elapsed]
Next: [Next phase]

[Additional details]

Best regards,
[Name]
```

#### Post-Deployment
```
Subject: NBA MCP Synthesis - Deployment Complete

Team,

NBA MCP Synthesis has been successfully deployed to production.

Status: SUCCESS
Duration: [Total time]
Issues: [None/Minor/Major]

The system is now live and operational.

Best regards,
[Name]
```

### Incident Communication

#### Critical Issue
```
Subject: URGENT - NBA MCP Synthesis Deployment Issue

Team,

We are experiencing a critical issue during deployment.

Issue: [Description]
Impact: [Description]
Action: [Description]
ETA: [Time]

Please standby for further updates.

Best regards,
[Name]
```

#### Rollback Decision
```
Subject: NBA MCP Synthesis - Rollback Initiated

Team,

We are initiating rollback procedures due to [reason].

Rollback ETA: [Time]
Impact: [Description]
Next Steps: [Description]

Please standby for further updates.

Best regards,
[Name]
```

## Emergency Procedures

### Critical Issue Response

1. **Immediate Assessment**
   - Assess severity and impact
   - Notify team lead immediately
   - Document issue details

2. **Communication**
   - Send incident notification
   - Update stakeholders
   - Escalate if necessary

3. **Resolution**
   - Follow troubleshooting procedures
   - Implement fix or rollback
   - Verify resolution

4. **Post-Incident**
   - Document incident
   - Conduct post-mortem
   - Update procedures

### Rollback Decision Matrix

| Issue Type | Severity | Action |
|------------|----------|--------|
| Application Crash | Critical | Immediate rollback |
| Performance Degradation | High | Monitor, rollback if persists |
| Minor Functionality | Medium | Fix in place |
| Monitoring Issues | Low | Continue, fix post-deployment |

### Emergency Contacts

#### Primary Contacts
- **Deployment Lead**: [Name] - [Phone] - [Email]
- **Technical Lead**: [Name] - [Phone] - [Email]
- **DevOps Lead**: [Name] - [Phone] - [Email]

#### Secondary Contacts
- **Application Engineer**: [Name] - [Phone] - [Email]
- **Infrastructure Engineer**: [Name] - [Phone] - [Email]
- **Security Lead**: [Name] - [Phone] - [Email]

#### External Contacts
- **AWS Support**: [Support case URL]
- **PagerDuty**: [Service URL]
- **Slack Channel**: `#nba-mcp-synthesis-alerts`

## Success Criteria

### Technical Success
- [ ] All deployment phases completed successfully
- [ ] Application responding correctly
- [ ] Monitoring operational
- [ ] No critical errors or issues
- [ ] Performance within acceptable limits

### Operational Success
- [ ] Team communication effective
- [ ] Procedures followed correctly
- [ ] Documentation updated
- [ ] Lessons learned captured
- [ ] Stakeholders satisfied

### Business Success
- [ ] System meets performance requirements
- [ ] User experience positive
- [ ] Business objectives achieved
- [ ] ROI targets met
- [ ] Future improvements identified

## Post-Go-Live Checklist

### Immediate (First 2 hours)
- [ ] Monitor system stability
- [ ] Verify all functionality
- [ ] Check monitoring dashboards
- [ ] Respond to any alerts
- [ ] Document any issues

### Short-term (First 24 hours)
- [ ] Monitor performance trends
- [ ] Review user feedback
- [ ] Analyze metrics
- [ ] Plan optimizations
- [ ] Schedule team debrief

### Long-term (First week)
- [ ] Performance optimization
- [ ] User training
- [ ] Documentation updates
- [ ] Process improvements
- [ ] Future planning

---

**Go-Live Complete**: NBA MCP Synthesis successfully deployed to production and operational.

**Next Steps**: Follow `POST_DEPLOYMENT_OPS.md` for ongoing operational procedures.


