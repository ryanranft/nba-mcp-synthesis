# Quick Start Guide for Experienced Operators

## Overview

This guide provides rapid deployment procedures for experienced Kubernetes and AWS operators who need to quickly deploy NBA MCP Synthesis to production.

## Prerequisites

- AWS CLI configured with appropriate permissions
- kubectl configured for EKS cluster access
- Helm 3.x installed
- Docker installed
- Terraform installed
- Basic understanding of NBA MCP Synthesis architecture

## Quick Deployment (30 minutes)

### 1. Infrastructure Setup (10 minutes)

```bash
# Clone repository and navigate to infrastructure
git clone <repository-url>
cd nba-mcp-synthesis/infrastructure/terraform

# Initialize Terraform
terraform init

# Deploy infrastructure
terraform apply -var-file="secrets.tfvars" -auto-approve

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name nba-mcp-synthesis-cluster
```

### 2. Secrets Migration (5 minutes)

```bash
# Navigate to scripts directory
cd ../../scripts

# Migrate secrets to AWS Secrets Manager
python3 migrate_secrets_to_aws.py --dry-run
python3 migrate_secrets_to_aws.py --execute

# Verify secrets
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)]'
```

### 3. Application Deployment (10 minutes)

```bash
# Navigate to k8s directory
cd ../k8s

# Apply Kubernetes manifests
kubectl apply -f namespace.yaml
kubectl apply -f external-secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Wait for deployment
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### 4. Monitoring Setup (5 minutes)

```bash
# Install Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values infrastructure/helm/prometheus-values.yaml

# Apply ServiceMonitor
kubectl apply -f servicemonitor.yaml

# Verify monitoring
kubectl get pods -n monitoring
```

## Essential Commands

### Health Checks
```bash
# Application health
kubectl get pods -n nba-mcp-synthesis
curl -f https://nba-mcp-synthesis.example.com/health

# Database health
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT 1;"

# Monitoring health
kubectl get pods -n monitoring
```

### Scaling
```bash
# Scale application
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=5

# Check HPA
kubectl get hpa -n nba-mcp-synthesis
kubectl describe hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis
```

### Logs
```bash
# Application logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis -f

# Database logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-postgres -f

# Monitoring logs
kubectl logs -n monitoring deployment/prometheus-server -f
```

## Configuration Quick Reference

### Environment Variables
```bash
# Key environment variables
export PROJECT_NAME="nba-mcp-synthesis"
export SPORT_NAME="NBA"
export NBA_MCP_CONTEXT="production"
export AWS_REGION="us-east-1"
export EKS_CLUSTER_NAME="nba-mcp-synthesis-cluster"
```

### Kubernetes Resources
```bash
# Namespace
kubectl get namespace nba-mcp-synthesis

# Deployments
kubectl get deployments -n nba-mcp-synthesis

# Services
kubectl get services -n nba-mcp-synthesis

# Ingress
kubectl get ingress -n nba-mcp-synthesis
```

### AWS Resources
```bash
# EKS Cluster
aws eks describe-cluster --name nba-mcp-synthesis-cluster --region us-east-1

# ECR Repository
aws ecr describe-repositories --repository-names nba-mcp-synthesis --region us-east-1

# Secrets Manager
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `nba-mcp-synthesis`)]'
```

## Troubleshooting Quick Fixes

### Common Issues

#### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -n nba-mcp-synthesis deployment/nba-mcp-synthesis --previous

# Check events
kubectl get events -n nba-mcp-synthesis --sort-by='.lastTimestamp'

# Restart deployment
kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n nba-mcp-synthesis

# Check ingress status
kubectl describe ingress nba-mcp-synthesis-ingress -n nba-mcp-synthesis

# Test service connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -f http://nba-mcp-synthesis-service:80/health
```

#### Database Connection Issues
```bash
# Check database pod
kubectl get pods -n nba-mcp-synthesis | grep postgres

# Test database connection
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres -c "SELECT 1;"

# Check database secrets
kubectl get secret nba-mcp-postgres-secret -n nba-mcp-synthesis -o yaml
```

## Performance Optimization

### Resource Tuning
```bash
# Check resource usage
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes

# Adjust resource limits
kubectl patch deployment nba-mcp-synthesis -n nba-mcp-synthesis -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"nba-mcp-synthesis","resources":{"requests":{"memory":"1Gi","cpu":"500m"},"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'
```

### Scaling Configuration
```bash
# Update HPA
kubectl patch hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis -p \
  '{"spec":{"minReplicas":2,"maxReplicas":10,"targetCPUUtilizationPercentage":70}}'
```

## Security Quick Checks

### Network Policies
```bash
# Check network policies
kubectl get networkpolicies -n nba-mcp-synthesis

# Test network connectivity
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-synthesis -- \
  curl -f http://nba-mcp-postgres-service:5432
```

### RBAC
```bash
# Check RBAC
kubectl get roles,rolebindings -n nba-mcp-synthesis

# Check service account
kubectl get serviceaccounts -n nba-mcp-synthesis
```

### Secrets
```bash
# Check secrets
kubectl get secrets -n nba-mcp-synthesis

# Verify secret rotation
aws secretsmanager describe-secret --secret-id nba-mcp-synthesis/production
```

## Monitoring Quick Setup

### Grafana Access
```bash
# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80 &

# Access Grafana
open http://localhost:3000
# Username: admin
# Password: admin123
```

### Prometheus Access
```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:80 &

# Access Prometheus
open http://localhost:9090
```

### Alertmanager Access
```bash
# Port forward Alertmanager
kubectl port-forward -n monitoring svc/alertmanager 9093:80 &

# Access Alertmanager
open http://localhost:9093
```

## Backup and Recovery

### Database Backup
```bash
# Manual backup
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  pg_dump -U postgres nba_mcp_synthesis > backup-$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql s3://nba-mcp-synthesis-backups/
```

### Configuration Backup
```bash
# Backup Kubernetes configurations
kubectl get all -n nba-mcp-synthesis -o yaml > k8s-backup-$(date +%Y%m%d).yaml

# Backup secrets
kubectl get secrets -n nba-mcp-synthesis -o yaml > secrets-backup-$(date +%Y%m%d).yaml
```

## Rollback Procedures

### Application Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/nba-mcp-synthesis -n nba-mcp-synthesis

# Check rollback status
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
kubectl rollout history deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### Database Rollback
```bash
# Stop application
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=0

# Restore database
kubectl exec -n nba-mcp-synthesis deployment/nba-mcp-postgres -- \
  psql -U postgres nba_mcp_synthesis < backup-$(date +%Y%m%d).sql

# Restart application
kubectl scale deployment nba-mcp-synthesis -n nba-mcp-synthesis --replicas=3
```

## Maintenance Tasks

### Daily Tasks
```bash
# Health check
kubectl get pods -n nba-mcp-synthesis
curl -f https://nba-mcp-synthesis.example.com/health

# Resource check
kubectl top pods -n nba-mcp-synthesis
kubectl top nodes
```

### Weekly Tasks
```bash
# Security scan
trivy image nba-mcp-synthesis:latest

# Performance review
kubectl get hpa -n nba-mcp-synthesis
kubectl describe hpa nba-mcp-synthesis-hpa -n nba-mcp-synthesis
```

### Monthly Tasks
```bash
# Cost review
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Backup verification
aws s3 ls s3://nba-mcp-synthesis-backups/ --recursive
```

## Emergency Procedures

### Complete System Restart
```bash
# Restart all components
kubectl rollout restart deployment/nba-mcp-synthesis -n nba-mcp-synthesis
kubectl rollout restart deployment/nba-mcp-postgres -n nba-mcp-synthesis
kubectl rollout restart deployment/nba-mcp-redis -n nba-mcp-synthesis

# Wait for rollout
kubectl rollout status deployment/nba-mcp-synthesis -n nba-mcp-synthesis
```

### Node Maintenance
```bash
# Drain node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# After maintenance, uncordon
kubectl uncordon <node-name>
```

### Cluster Maintenance
```bash
# Update cluster
aws eks update-cluster-version --name nba-mcp-synthesis-cluster --kubernetes-version 1.28

# Update node group
aws eks update-nodegroup-version --cluster-name nba-mcp-synthesis-cluster \
  --nodegroup-name nba-mcp-synthesis-nodes
```

## Conclusion

This quick start guide provides the essential commands and procedures for experienced operators to rapidly deploy and manage NBA MCP Synthesis in production. For detailed procedures, refer to the comprehensive deployment guide and troubleshooting documentation.

---

**Last Updated**: $(date)
**Version**: 1.0
**Next Review**: $(date -d "+1 month")


