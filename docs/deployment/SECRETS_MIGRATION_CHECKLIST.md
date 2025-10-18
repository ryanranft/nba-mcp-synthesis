# NBA MCP Synthesis - Secrets Migration Checklist

## Overview

This checklist provides step-by-step instructions for migrating local secrets to AWS Secrets Manager for production deployment. Follow each step carefully and verify completion before proceeding.

## Pre-Migration Preparation

### Step 1: Backup Current Secrets
- [ ] Create backup directory: `mkdir -p backups/secrets/$(date +%Y%m%d-%H%M%S)`
- [ ] Backup production secrets: `cp -r /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production backups/secrets/$(date +%Y%m%d-%H%M%S)/`
- [ ] Backup development secrets: `cp -r /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development backups/secrets/$(date +%Y%m%d-%H%M%S)/`
- [ ] Backup test secrets: `cp -r /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.test backups/secrets/$(date +%Y%m%d-%H%M%S)/`
- [ ] Verify backup integrity: `ls -la backups/secrets/$(date +%Y%m%d-%H%M%S)/`
- [ ] Test restore procedure: `cp backups/secrets/$(date +%Y%m%d-%H%M%S)/.env.nba_mcp_synthesis.production /tmp/test-restore`

### Step 2: Verify AWS Access
- [ ] Check AWS credentials: `aws sts get-caller-identity`
- [ ] Verify Secrets Manager permissions: `aws secretsmanager list-secrets`
- [ ] Test secret creation: `aws secretsmanager create-secret --name test-secret --secret-string "test-value" --description "Test secret"`
- [ ] Clean up test secret: `aws secretsmanager delete-secret --secret-id test-secret --force-delete-without-recovery`

### Step 3: Review Secret Inventory
- [ ] List all production secrets: `ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production`
- [ ] Count total secrets: `wc -l /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production`
- [ ] Identify critical secrets (API keys, database passwords, etc.)
- [ ] Document secret purposes and owners
- [ ] Plan secret naming convention in AWS Secrets Manager

## Migration Execution

### Step 4: Run Migration Dry-Run
- [ ] Navigate to project directory: `cd /Users/ryanranft/nba-mcp-synthesis`
- [ ] Run dry-run migration: `python3 scripts/migrate_secrets_to_aws.py --dry-run`
- [ ] Review dry-run output for any errors or warnings
- [ ] Verify all secrets would be created correctly
- [ ] Check secret naming convention compliance
- [ ] Confirm no sensitive data in logs

### Step 5: Execute Migration
- [ ] Run actual migration: `python3 scripts/migrate_secrets_to_aws.py`
- [ ] Monitor migration progress
- [ ] Verify all secrets created successfully
- [ ] Check for any error messages
- [ ] Confirm migration completion message

### Step 6: Verify Migration
- [ ] Run verification: `python3 scripts/migrate_secrets_to_aws.py --verify`
- [ ] Check AWS Secrets Manager console for all secrets
- [ ] Verify secret values match local files
- [ ] Test secret retrieval: `aws secretsmanager get-secret-value --secret-id nba-mcp-synthesis-production`
- [ ] Confirm no secrets missing or corrupted

## Post-Migration Configuration

### Step 7: Configure External Secrets Operator
- [ ] Verify External Secrets Operator is installed: `kubectl get pods -n external-secrets-system`
- [ ] Apply External Secrets configuration: `kubectl apply -f k8s/external-secrets.yaml`
- [ ] Check ExternalSecret resources: `kubectl get externalsecrets -n nba-mcp-synthesis`
- [ ] Verify secret sync status: `kubectl describe externalsecret nba-mcp-synthesis-secrets -n nba-mcp-synthesis`
- [ ] Confirm Kubernetes secrets created: `kubectl get secrets -n nba-mcp-synthesis`

### Step 8: Test Secret Access
- [ ] Deploy test pod: `kubectl run test-secret-access --image=busybox --rm -it --restart=Never -n nba-mcp-synthesis --env="SECRET_NAME=nba-mcp-synthesis-production"`
- [ ] Verify secrets are accessible in pod
- [ ] Test application can read secrets
- [ ] Confirm no permission errors
- [ ] Clean up test pod

### Step 9: Update Application Configuration
- [ ] Verify application uses External Secrets
- [ ] Test application startup with new secrets
- [ ] Confirm all API connections work
- [ ] Verify database connectivity
- [ ] Test S3 access
- [ ] Confirm monitoring and alerting work

## Rollback Procedures

### If Migration Fails
- [ ] Stop migration process immediately
- [ ] Restore from backup: `cp backups/secrets/$(date +%Y%m%d-%H%M%S)/.env.nba_mcp_synthesis.production /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production`
- [ ] Clean up partial AWS secrets: `aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)].Name' --output text | xargs -I {} aws secretsmanager delete-secret --secret-id {} --force-delete-without-recovery`
- [ ] Verify local secrets restored correctly
- [ ] Test application functionality
- [ ] Document failure reasons
- [ ] Plan remediation steps

### If Application Fails After Migration
- [ ] Check External Secrets Operator logs: `kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets`
- [ ] Verify secret sync: `kubectl get externalsecrets -n nba-mcp-synthesis`
- [ ] Check application logs: `kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis`
- [ ] Test secret access manually
- [ ] Rollback to local secrets if necessary
- [ ] Investigate and fix issues
- [ ] Re-attempt migration after fixes

## Security Verification

### Step 10: Security Checks
- [ ] Verify secrets are encrypted at rest in AWS
- [ ] Confirm no secrets in pod logs
- [ ] Check secret access logging is enabled
- [ ] Verify least privilege access policies
- [ ] Test secret rotation capability
- [ ] Confirm backup and recovery procedures

### Step 11: Audit Trail
- [ ] Document migration completion
- [ ] Record all secret names and purposes
- [ ] Update secret inventory documentation
- [ ] Notify security team of completion
- [ ] Schedule regular secret rotation
- [ ] Plan secret access review schedule

## Final Validation

### Step 12: End-to-End Testing
- [ ] Deploy application to staging with new secrets
- [ ] Run full test suite
- [ ] Verify all integrations work
- [ ] Test monitoring and alerting
- [ ] Confirm performance is acceptable
- [ ] Validate security controls

### Step 13: Production Deployment
- [ ] Deploy to production with new secrets
- [ ] Monitor application startup
- [ ] Verify all services healthy
- [ ] Test critical functionality
- [ ] Confirm monitoring active
- [ ] Document successful migration

## Success Criteria

- [ ] All local secrets successfully migrated to AWS Secrets Manager
- [ ] External Secrets Operator syncing secrets to Kubernetes
- [ ] Application running successfully with new secret source
- [ ] No secrets exposed in logs or configuration files
- [ ] Backup and rollback procedures tested and working
- [ ] Security controls and audit logging active
- [ ] Team trained on new secret management process

## Post-Migration Cleanup

### Step 14: Cleanup Local Secrets (Optional)
- [ ] **WARNING**: Only proceed after confirming production is stable
- [ ] Move local secrets to archive: `mv /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production /Users/ryanranft/Desktop/++/archived-secrets/`
- [ ] Update documentation to reflect new secret source
- [ ] Train team on new secret access procedures
- [ ] Schedule regular secret rotation
- [ ] Plan secret access review schedule

## Contact Information

### Migration Team
- **Primary Contact**: [Name and contact info]
- **Secondary Contact**: [Name and contact info]
- **AWS Support**: [Support case URL]
- **Security Team**: [Contact info]

### Emergency Contacts
- **On-Call Engineer**: [Contact info]
- **DevOps Lead**: [Contact info]
- **Security Lead**: [Contact info]

---

**Migration Complete**: All secrets successfully migrated to AWS Secrets Manager and application running with new secret source.

**Next Step**: Proceed to application deployment phase in `docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`.


