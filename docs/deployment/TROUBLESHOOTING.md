# Deployment Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for common deployment issues encountered during NBA MCP Synthesis production deployment and operations.

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Infrastructure Issues](#infrastructure-issues)
3. [Application Issues](#application-issues)
4. [Database Issues](#database-issues)
5. [Secrets Management Issues](#secrets-management-issues)
6. [Monitoring Issues](#monitoring-issues)
7. [Network Issues](#network-issues)
8. [Performance Issues](#performance-issues)
9. [Security Issues](#security-issues)
10. [Recovery Procedures](#recovery-procedures)

## Quick Reference

### Emergency Commands
```bash
# Check overall system status
kubectl get all -n nba-mcp-synthesis
kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp'

# Check application health
curl -f https://nba-mcp-synthesis.example.com/health
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --tail=50

# Check resource usage
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes

# Restart application
kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### Common Error Patterns
- **Pod CrashLoopBackOff**: Check logs, resource limits, secrets
- **ImagePullBackOff**: Check image registry access, credentials
- **Pending Pods**: Check resource availability, node capacity
- **Service Unavailable**: Check ingress, service configuration
- **Database Connection Failed**: Check secrets, network policies

## Infrastructure Issues

### EKS Cluster Issues

#### Cluster Not Accessible
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify cluster exists
aws eks describe-cluster --name nba-mcp-synthesis-cluster --region us-east-1

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name nba-mcp-synthesis-cluster

# Test cluster connectivity
kubectl get nodes
```

#### Node Group Issues
```bash
# Check node group status
aws eks describe-nodegroup --cluster-name nba-mcp-synthesis-cluster \
  --nodegroup-name nba-mcp-synthesis-nodes --region us-east-1

# Check node capacity
kubectl get nodes
kubectl describe nodes

# Check for resource pressure
kubectl top nodes
```

#### VPC/Networking Issues
```bash
# Check VPC configuration
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=nba-mcp-synthesis-vpc"

# Check subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxx"

# Check security groups
aws ec2 describe-security-groups --filters "Name=group-name,Values=nba-mcp-synthesis*"

# Test network connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  ping -c 3 8.8.8.8
```

### Terraform Issues

#### Terraform State Issues
```bash
# Check terraform state
terraform state list

# Refresh state
terraform refresh

# Import existing resources
terraform import aws_eks_cluster.main nba-mcp-synthesis-cluster

# Plan and apply
terraform plan
terraform apply
```

#### Resource Conflicts
```bash
# Check for resource conflicts
terraform plan -detailed-exitcode

# Resolve conflicts
terraform state rm aws_instance.example
terraform import aws_instance.example i-1234567890abcdef0
```

## Application Issues

### Pod Startup Issues

#### CrashLoopBackOff
```bash
# Check pod status
kubectl get pods -n nba-mcp-synthesis
kubectl describe pod <pod-name> -n nba-mcp-synthesis

# Check logs
kubectl logs <pod-name> -n nba-mcp-synthesis --previous

# Check events
kubectl get events -n nba-mcp-synthesis --field-selector involvedObject.name=<pod-name>
```

**Common Causes:**
- Missing environment variables
- Invalid secrets
- Resource limits too low
- Application configuration errors

**Solutions:**
```bash
# Check environment variables
kubectl exec <pod-name> -n nba-mcp-synthesis -- env | grep -E "(API|DB|SECRET)"

# Verify secrets
kubectl get secrets -n nba-mcp-synthesis
kubectl describe secret <secret-name> -n nba-mcp-synthesis

# Check resource limits
kubectl describe pod <pod-name> -n nba-mcp-synthesis | grep -A 5 "Limits:"
```

#### ImagePullBackOff
```bash
# Check image pull secrets
kubectl get secrets -n nba-mcp-synthesis | grep docker

# Check ECR access
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Verify image exists
aws ecr describe-images --repository-name nba-mcp-synthesis --region us-east-1
```

**Solutions:**
```bash
# Create image pull secret
kubectl create secret docker-registry ecr-secret \
  --docker-server=<account-id>.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1) \
  --namespace=nba-mcp-synthesis

# Update deployment to use secret
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"ecr-secret"}]}}}}'
```

#### Pending Pods
```bash
# Check pod status
kubectl get pods -n nba-mcp-synthesis
kubectl describe pod <pod-name> -n nba-mcp-synthesis

# Check node capacity
kubectl describe nodes
kubectl top nodes
```

**Common Causes:**
- Insufficient resources
- Node selector issues
- Persistent volume issues
- Network policy restrictions

**Solutions:**
```bash
# Check resource requests
kubectl describe pod <pod-name> -n nba-mcp-synthesis | grep -A 10 "Requests:"

# Check node selectors
kubectl get nodes --show-labels

# Check persistent volumes
kubectl get pv
kubectl get pvc -n nba-mcp-synthesis
```

### Service Issues

#### Service Not Accessible
```bash
# Check service status
kubectl get services -n nba-mcp-synthesis
kubectl describe service nba-mcp-synthesis-service -n nba-mcp-synthesis

# Check endpoints
kubectl get endpoints -n nba-mcp-synthesis

# Test service connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -f http://nba-mcp-synthesis-service:80/health
```

**Solutions:**
```bash
# Check pod labels match service selector
kubectl get pods -n nba-mcp-synthesis --show-labels
kubectl get service nba-mcp-synthesis-service -n nba-mcp-synthesis -o yaml

# Restart service
kubectl delete service nba-mcp-synthesis-service -n nba-mcp-synthesis
kubectl apply -f k8s/service.yaml
```

#### Ingress Issues
```bash
# Check ingress status
kubectl get ingress -n nba-mcp-synthesis
kubectl describe ingress nba-mcp-synthesis-ingress -n nba-mcp-synthesis

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

**Solutions:**
```bash
# Check ALB status
aws elbv2 describe-load-balancers --names nba-mcp-synthesis-alb

# Check target groups
aws elbv2 describe-target-groups --load-balancer-arn <alb-arn>

# Check target health
aws elbv2 describe-target-health --target-group-arn <tg-arn>
```

## Database Issues

### Connection Issues

#### Database Connection Failed
```bash
# Check database pod status
kubectl get pods -n nba-mcp-synthesis | grep postgres
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-postgres --tail=50

# Test database connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT 1;"
```

**Common Causes:**
- Database pod not running
- Incorrect connection string
- Network policy blocking access
- Authentication issues

**Solutions:**
```bash
# Check database secrets
kubectl get secret nba-mcp-postgres-secret -n nba-mcp-synthesis -o yaml

# Verify connection string
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  env | grep -E "(DB|POSTGRES)"

# Test connection from application pod
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import psycopg2; print('DB connection test')"
```

#### Database Performance Issues
```bash
# Check database metrics
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check database size
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('nba_mcp_synthesis'));"

# Check slow queries
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Solutions:**
```bash
# Check resource usage
kubectl top pods -n nba-mcp-synthesis | grep postgres

# Check database configuration
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SHOW ALL;" | grep -E "(shared_buffers|work_mem|max_connections)"

# Optimize database
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "VACUUM ANALYZE;"
```

### Backup Issues

#### Backup Failures
```bash
# Check backup job status
kubectl get jobs -n nba-mcp-synthesis | grep backup
kubectl logs -n nba-mcp-synthesis job/nba-mcp-postgres-backup

# Check S3 backup status
aws s3 ls s3://nba-mcp-synthesis-backups/ --recursive
```

**Solutions:**
```bash
# Manual backup
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_dump -U postgres nba_mcp_synthesis > backup-$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql s3://nba-mcp-synthesis-backups/

# Verify backup
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_restore --list backup-$(date +%Y%m%d).sql
```

## Secrets Management Issues

### Secret Loading Issues

#### Secrets Not Loading
```bash
# Check secret files
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/

# Test hierarchical loader
python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA production

# Check environment variables
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- env | grep -E "(API|SECRET)"
```

**Common Causes:**
- Missing secret files
- Incorrect file permissions
- Invalid secret format
- AWS Secrets Manager access issues

**Solutions:**
```bash
# Check file permissions
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Fix permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Test secret loading
python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA production --dry-run
```

#### AWS Secrets Manager Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# List secrets
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)]'

# Test secret retrieval
aws secretsmanager get-secret-value --secret-id nba-mcp-synthesis/production
```

**Solutions:**
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name <username>

# Test secret access
aws secretsmanager get-secret-value --secret-id nba-mcp-synthesis/production --query SecretString --output text
```

### Secret Validation Issues

#### Invalid Secret Format
```bash
# Check secret validation
python3 scripts/enforce_naming_convention.py

# Validate specific secrets
python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA production --validate-only
```

**Solutions:**
```bash
# Fix naming convention
python3 scripts/enforce_naming_convention.py --fix

# Regenerate secrets
python3 scripts/generate_production_config.py
```

## Monitoring Issues

### Prometheus Issues

#### Metrics Not Collecting
```bash
# Check Prometheus status
kubectl get pods -n monitoring | grep prometheus
kubectl logs -n monitoring deployment/prometheus-server --tail=50

# Check ServiceMonitor
kubectl get servicemonitor -n nba-mcp-synthesis
kubectl describe servicemonitor nba-mcp-synthesis-metrics -n nba-mcp-synthesis
```

**Solutions:**
```bash
# Check scrape configuration
kubectl exec -n monitoring deployment/prometheus-server -- \
  cat /etc/prometheus/prometheus.yml | grep -A 10 "nba-mcp-synthesis"

# Test metrics endpoint
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -f http://localhost:9090/metrics
```

#### Grafana Issues
```bash
# Check Grafana status
kubectl get pods -n monitoring | grep grafana
kubectl logs -n monitoring deployment/grafana --tail=50

# Check Grafana configuration
kubectl exec -n monitoring deployment/grafana -- \
  cat /etc/grafana/grafana.ini | grep -E "(admin|database)"
```

**Solutions:**
```bash
# Reset Grafana admin password
kubectl exec -n monitoring deployment/grafana -- \
  grafana-cli admin reset-admin-password newpassword

# Check data source configuration
kubectl exec -n monitoring deployment/grafana -- \
  curl -u admin:admin http://localhost:3000/api/datasources
```

### Alerting Issues

#### Alerts Not Firing
```bash
# Check Alertmanager status
kubectl get pods -n monitoring | grep alertmanager
kubectl logs -n monitoring deployment/alertmanager --tail=50

# Check alert rules
kubectl get prometheusrules -n monitoring
kubectl describe prometheusrules nba-mcp-synthesis-alerts -n monitoring
```

**Solutions:**
```bash
# Test alert rules
kubectl exec -n monitoring deployment/prometheus-server -- \
  promtool check rules /etc/prometheus/rules/nba-mcp-synthesis-alerts.yml

# Check alert configuration
kubectl exec -n monitoring deployment/alertmanager -- \
  cat /etc/alertmanager/alertmanager.yml
```

#### Notification Issues
```bash
# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert from NBA MCP Synthesis"}' \
  $SLACK_WEBHOOK_URL

# Check PagerDuty integration
curl -H "Authorization: Token token=$PAGERDUTY_TOKEN" \
  https://api.pagerduty.com/services
```

**Solutions:**
```bash
# Verify webhook URLs
kubectl get secret alertmanager-secret -n monitoring -o yaml

# Test notification channels
kubectl exec -n monitoring deployment/alertmanager -- \
  amtool config show
```

## Network Issues

### DNS Issues

#### DNS Resolution Problems
```bash
# Test DNS resolution
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  nslookup nba-mcp-synthesis-service

# Check DNS configuration
kubectl get configmap -n kube-system coredns -o yaml
```

**Solutions:**
```bash
# Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system

# Check DNS pods
kubectl get pods -n kube-system | grep coredns
kubectl logs -n kube-system deployment/coredns
```

### Network Policy Issues

#### Network Connectivity Blocked
```bash
# Check network policies
kubectl get networkpolicies -n nba-mcp-synthesis
kubectl describe networkpolicy nba-mcp-synthesis-network-policy -n nba-mcp-synthesis

# Test connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -f http://nba-mcp-postgres-service:5432
```

**Solutions:**
```bash
# Temporarily disable network policy
kubectl delete networkpolicy nba-mcp-synthesis-network-policy -n nba-mcp-synthesis

# Update network policy
kubectl apply -f k8s/network-policy.yaml
```

## Performance Issues

### High CPU Usage

#### CPU Bottlenecks
```bash
# Check CPU usage
kubectl top pods -n nba-mcp-synthesis --sort-by=cpu
kubectl top nodes

# Check CPU limits
kubectl describe pod <pod-name> -n nba-mcp-synthesis | grep -A 5 "Limits:"
```

**Solutions:**
```bash
# Increase CPU limits
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","resources":{"limits":{"cpu":"2000m"}}}]}}}}'

# Check for CPU-intensive processes
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  top -n 1
```

### High Memory Usage

#### Memory Issues
```bash
# Check memory usage
kubectl top pods -n nba-mcp-synthesis --sort-by=memory
kubectl describe pod <pod-name> -n nba-mcp-synthesis | grep -A 5 "Limits:"
```

**Solutions:**
```bash
# Increase memory limits
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","resources":{"limits":{"memory":"4Gi"}}}]}}}}'

# Check for memory leaks
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import psutil; print(psutil.virtual_memory())"
```

### Slow Response Times

#### Performance Bottlenecks
```bash
# Check response times
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Check database performance
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

**Solutions:**
```bash
# Enable connection pooling
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","env":[{"name":"DB_POOL_SIZE","value":"20"}]}]}}}}'

# Optimize database queries
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "ANALYZE;"
```

## Security Issues

### Authentication Issues

#### API Authentication Failures
```bash
# Check API key configuration
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  env | grep -E "(API_KEY|AUTH)"

# Test API authentication
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/test
```

**Solutions:**
```bash
# Verify API key format
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  python3 -c "import re; print(re.match(r'^[A-Za-z0-9_-]{20,}$', '$API_KEY'))"

# Regenerate API key
python3 scripts/generate_production_config.py --regenerate-api-keys
```

### Authorization Issues

#### Permission Denied Errors
```bash
# Check RBAC configuration
kubectl get roles,rolebindings -n nba-mcp-synthesis
kubectl describe role nba-mcp-synthesis-role -n nba-mcp-synthesis

# Check service account
kubectl get serviceaccounts -n nba-mcp-synthesis
kubectl describe serviceaccount nba-mcp-synthesis-sa -n nba-mcp-synthesis
```

**Solutions:**
```bash
# Update RBAC permissions
kubectl apply -f k8s/rbac.yaml

# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name <username>
```

## Recovery Procedures

### Application Recovery

#### Complete Application Restart
```bash
# Restart all application components
kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis
kubectl rollout restart deployment/nba-mcp-postgres -n nba-mcp-synthesis
kubectl rollout restart deployment/nba-mcp-redis -n nba-mcp-synthesis

# Wait for rollout to complete
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

#### Application Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/nba-mcp-synthesis -n nba-mcp-synthesis

# Check rollback status
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
kubectl rollout history deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### Database Recovery

#### Database Restore
```bash
# Stop application
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=0

# Restore database
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "DROP DATABASE IF EXISTS nba_mcp_synthesis;"
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "CREATE DATABASE nba_mcp_synthesis;"
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres nba_mcp_synthesis < backup-$(date +%Y%m%d).sql

# Restart application
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=3
```

### Infrastructure Recovery

#### Node Recovery
```bash
# Drain problematic node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Uncordon node after repair
kubectl uncordon <node-name>
```

#### Cluster Recovery
```bash
# Check cluster status
aws eks describe-cluster --name nba-mcp-synthesis-cluster --region us-east-1

# Update cluster
aws eks update-cluster-version --name nba-mcp-synthesis-cluster --kubernetes-version 1.28

# Check node group
aws eks describe-nodegroup --cluster-name nba-mcp-synthesis-cluster \
  --nodegroup-name nba-mcp-synthesis-nodes --region us-east-1
```

## Conclusion

This troubleshooting guide provides comprehensive procedures for diagnosing and resolving common deployment issues. For issues not covered in this guide:

1. Check the application logs
2. Review Kubernetes events
3. Consult the monitoring dashboards
4. Contact the operations team
5. Escalate to the development team if needed

Remember to document any new issues and solutions for future reference.

---

**Last Updated**: $(date)
**Version**: 1.0
**Next Review**: $(date -d "+1 month")


