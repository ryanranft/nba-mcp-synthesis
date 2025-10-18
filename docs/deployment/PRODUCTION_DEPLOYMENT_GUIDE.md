# NBA MCP Synthesis - Production Deployment Guide

## Quick Start Summary (5-minute overview)

This guide will deploy NBA MCP Synthesis to production on AWS EKS with enterprise monitoring, security, and operational procedures. Estimated total time: 4-6 hours.

### Prerequisites
- AWS account with EKS permissions
- kubectl, helm, terraform, aws-cli installed
- Domain name and SSL certificate
- PagerDuty service key
- Slack webhook URL

### Deployment Phases
1. **Infrastructure Setup** (1 hour) - EKS cluster, VPC, networking
2. **Secrets Migration** (30 minutes) - Move to AWS Secrets Manager
3. **Application Deployment** (1 hour) - Kubernetes manifests, HPA
4. **Monitoring Setup** (1 hour) - Prometheus, Grafana, Alertmanager
5. **Go-Live Validation** (30 minutes) - Health checks, smoke tests

## Prerequisites Checklist

### AWS Account Requirements
- [ ] AWS account with admin permissions
- [ ] EKS service quota: 3 clusters minimum
- [ ] EC2 quota: 20 instances minimum
- [ ] RDS quota: 5 instances minimum
- [ ] Route 53 hosted zone (if using custom domain)

### Required Tools
- [ ] AWS CLI v2.0+ configured
- [ ] kubectl v1.28+
- [ ] Helm v3.12+
- [ ] Terraform v1.0+
- [ ] Docker (for building images)

### External Services
- [ ] PagerDuty service key
- [ ] Slack webhook URL for alerts
- [ ] Domain name registered
- [ ] SSL certificate (Let's Encrypt or AWS Certificate Manager)

### Team Information
- [ ] Primary on-call contact
- [ ] Secondary on-call contact
- [ ] Team lead contact
- [ ] Engineering manager contact

## Phase 1: Infrastructure Setup

### Step 1.1: Deploy AWS Infrastructure

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create secrets.tfvars with actual values
cp secrets.tfvars.example secrets.tfvars
# Edit secrets.tfvars with your actual secret values

# Plan infrastructure deployment
terraform plan -var-file="secrets.tfvars"

# Deploy infrastructure
terraform apply -var-file="secrets.tfvars"
```

**Validation Steps:**
- [ ] EKS cluster is running
- [ ] All nodes are in Ready state
- [ ] VPC and subnets created
- [ ] Security groups configured
- [ ] NAT gateways operational

### Step 1.2: Configure kubectl Access

```bash
# Update kubectl configuration
aws eks update-kubeconfig --region us-east-1 --name nba-mcp-synthesis-prod

# Verify cluster access
kubectl get nodes
kubectl cluster-info
```

**Validation Steps:**
- [ ] kubectl can connect to cluster
- [ ] All nodes show Ready status
- [ ] Cluster info displays correctly

### Step 1.3: Install Required Helm Charts

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system --create-namespace
```

**Validation Steps:**
- [ ] External Secrets Operator pods running
- [ ] Helm charts installed successfully
- [ ] No error messages in logs

## Phase 2: Secrets Migration

### Step 2.1: Backup Current Secrets

```bash
# Create backup directory
mkdir -p backups/secrets/$(date +%Y%m%d-%H%M%S)

# Backup current secrets
cp -r /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production backups/secrets/$(date +%Y%m%d-%H%M%S)/
```

### Step 2.2: Migrate Secrets to AWS

```bash
# Run migration dry-run first
python3 scripts/migrate_secrets_to_aws.py --dry-run

# Execute actual migration
python3 scripts/migrate_secrets_to_aws.py

# Verify migration
python3 scripts/migrate_secrets_to_aws.py --verify
```

**Validation Steps:**
- [ ] All secrets created in AWS Secrets Manager
- [ ] Secret values match local files
- [ ] No migration errors
- [ ] External Secrets Operator can access secrets

### Step 2.3: Configure External Secrets

```bash
# Apply External Secrets configuration
kubectl apply -f k8s/external-secrets.yaml

# Verify secret sync
kubectl get externalsecrets -n nba-mcp-synthesis
kubectl get secrets -n nba-mcp-synthesis
```

**Validation Steps:**
- [ ] ExternalSecret resources created
- [ ] Kubernetes secrets populated
- [ ] Secret values accessible to pods

## Phase 3: Application Deployment

### Step 3.1: Build and Push Docker Image

```bash
# Build and push to ECR
./scripts/push_to_ecr.sh latest

# Verify image exists
aws ecr describe-images --repository-name nba-mcp-synthesis --image-ids imageTag=latest
```

**Validation Steps:**
- [ ] Docker image built successfully
- [ ] Image pushed to ECR
- [ ] Image accessible from EKS

### Step 3.2: Deploy Kubernetes Manifests

```bash
# Create namespaces
kubectl apply -f k8s/namespace.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/servicemonitor.yaml
```

**Validation Steps:**
- [ ] All pods running and ready
- [ ] HPA configured correctly
- [ ] Service endpoints accessible
- [ ] Ingress controller working

### Step 3.3: Verify Application Health

```bash
# Check pod status
kubectl get pods -n nba-mcp-synthesis

# Test health endpoints
kubectl port-forward service/nba-mcp-synthesis-service 8080:80 -n nba-mcp-synthesis
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

**Validation Steps:**
- [ ] All pods in Running state
- [ ] Health endpoint returns 200 OK
- [ ] Metrics endpoint accessible
- [ ] No error logs in pods

## Phase 4: Monitoring Setup

### Step 4.1: Install Prometheus Stack

```bash
# Install Prometheus stack
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f infrastructure/helm/prometheus-values.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
```

**Validation Steps:**
- [ ] Prometheus pods running
- [ ] Grafana pods running
- [ ] Alertmanager pods running
- [ ] ServiceMonitor created

### Step 4.2: Configure Dashboards and Alerting

```bash
# Access Grafana (port forward)
kubectl port-forward service/kube-prometheus-stack-grafana 3000:80 -n monitoring

# Access Prometheus
kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

**Validation Steps:**
- [ ] Grafana accessible at localhost:3000
- [ ] Prometheus accessible at localhost:9090
- [ ] NBA MCP dashboard visible
- [ ] Alerting rules active

### Step 4.3: Test Alerting Integration

```bash
# Test PagerDuty integration
# (Manual test by triggering a test alert)

# Test Slack integration
# (Manual test by triggering a test alert)
```

**Validation Steps:**
- [ ] PagerDuty receives test alerts
- [ ] Slack receives test alerts
- [ ] Alert routing works correctly

## Phase 5: Go-Live Validation

### Step 5.1: Comprehensive Health Check

```bash
# Run production health check
./scripts/health_check_production.sh

# Run deployment validation
python3 scripts/validate_deployment.py
```

**Validation Steps:**
- [ ] All health checks pass
- [ ] Infrastructure components healthy
- [ ] Application responding correctly
- [ ] Monitoring stack operational

### Step 5.2: Load Testing

```bash
# Basic load test (if tools available)
# ab -n 1000 -c 10 http://your-domain.com/health
```

**Validation Steps:**
- [ ] Application handles load
- [ ] No errors under load
- [ ] Response times acceptable
- [ ] Auto-scaling works

### Step 5.3: Final Smoke Tests

```bash
# Test all critical endpoints
curl -f https://your-domain.com/health
curl -f https://your-domain.com/metrics

# Test database connectivity
# Test S3 access
# Test API integrations
```

**Validation Steps:**
- [ ] All endpoints accessible
- [ ] Database connectivity works
- [ ] S3 operations successful
- [ ] External API calls working

## Success Criteria

### Infrastructure
- [ ] EKS cluster running with 3+ nodes
- [ ] All pods in Ready state
- [ ] Network policies applied
- [ ] Security groups configured

### Application
- [ ] NBA MCP Synthesis pods running
- [ ] Health endpoints responding
- [ ] Metrics being collected
- [ ] HPA scaling correctly

### Secrets
- [ ] All secrets in AWS Secrets Manager
- [ ] External Secrets Operator syncing
- [ ] No secrets in pod logs
- [ ] Secret validation passing

### Monitoring
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards active
- [ ] Alertmanager configured
- [ ] PagerDuty integration working

### Security
- [ ] Network policies enforced
- [ ] Pod security standards applied
- [ ] Secrets encrypted at rest
- [ ] Audit logging enabled

## Troubleshooting Common Issues

### Pod Startup Failures
```bash
# Check pod logs
kubectl logs -l app=nba-mcp-synthesis -n nba-mcp-synthesis

# Check pod description
kubectl describe pod POD_NAME -n nba-mcp-synthesis

# Common fixes:
# 1. Check secrets are loaded
# 2. Verify resource limits
# 3. Check image pull permissions
```

### Secret Sync Issues
```bash
# Check External Secrets status
kubectl get externalsecrets -n nba-mcp-synthesis
kubectl describe externalsecret nba-mcp-synthesis-secrets -n nba-mcp-synthesis

# Check AWS permissions
aws sts get-caller-identity
```

### Monitoring Issues
```bash
# Check Prometheus targets
kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
# Navigate to http://localhost:9090/targets

# Check Grafana datasources
kubectl port-forward service/kube-prometheus-stack-grafana 3000:80 -n monitoring
# Navigate to http://localhost:3000/datasources
```

## Rollback Procedures

### Application Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/nba-mcp-synthesis -n nba-mcp-synthesis

# Rollback to specific revision
kubectl rollout undo deployment/nba-mcp-synthesis --to-revision=REVISION -n nba-mcp-synthesis
```

### Complete System Rollback
```bash
# Scale down current deployment
kubectl scale deployment nba-mcp-synthesis --replicas=0 -n nba-mcp-synthesis

# Restore from backup
# (Implementation depends on backup strategy)
```

## Post-Deployment Checklist

### First Hour
- [ ] Monitor pod logs for errors
- [ ] Check Grafana dashboards
- [ ] Verify all alerts are green
- [ ] Test critical functionality

### First 24 Hours
- [ ] Review performance metrics
- [ ] Check cost implications
- [ ] Monitor error rates
- [ ] Validate backup procedures

### First Week
- [ ] Performance optimization
- [ ] Alert threshold tuning
- [ ] Documentation updates
- [ ] Team training completion

## Contact Information

### Internal Team
- **Primary On-Call**: [Contact Info]
- **Secondary On-Call**: [Contact Info]
- **Team Lead**: [Contact Info]
- **Engineering Manager**: [Contact Info]

### External Services
- **AWS Support**: [Support Case URL]
- **PagerDuty**: [PagerDuty URL]
- **Slack Channel**: `#nba-mcp-synthesis-alerts`

---

**Deployment Complete!** 🚀

Follow this guide step-by-step for a successful production deployment. Each phase includes validation steps to ensure everything is working correctly before proceeding to the next phase.


