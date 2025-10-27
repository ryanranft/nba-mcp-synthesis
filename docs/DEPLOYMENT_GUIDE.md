# NBA MCP Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the NBA MCP system across different environments.

**Audience:** DevOps Engineers, ML Engineers
**Version:** 2.0
**Last Updated:** October 2025

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development Deployment](#local-development-deployment)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Ubuntu 20.04+ or macOS 12+

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 200 GB SSD
- OS: Ubuntu 22.04 LTS

### Software Dependencies

**Required:**
- Python 3.10 or 3.11
- PostgreSQL 14+ (production) or SQLite (development)
- Git
- Docker (optional, for containerized deployment)

**Optional:**
- MLflow server
- AWS CLI (for S3 integration)
- nginx (for reverse proxy)

### Python Dependencies

Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- mlflow >= 2.8.0
- great-expectations >= 0.17.0
- pytest >= 7.4.0

---

## Environment Setup

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nba_mcp
# For development with SQLite:
# DATABASE_URL=sqlite:///./nba_mcp.db

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=nba_predictions

# Storage
MODEL_STORAGE_PATH=/var/nba-mcp/models
DATA_STORAGE_PATH=/var/nba-mcp/data
LOG_PATH=/var/log/nba-mcp

# AWS S3 (Production only)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=nba-mcp-production

# System Configuration
CACHE_SIZE=50
CACHE_TTL=3600
MAX_WORKERS=4
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_secret_key_here
ENABLE_RBAC=true
```

Load environment:
```bash
export $(cat .env | xargs)
```

### Directory Structure

Create required directories:
```bash
mkdir -p /var/nba-mcp/{models,data,logs}
mkdir -p /var/nba-mcp/backups/{db,models}
```

---

## Local Development Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/nba-mcp-synthesis.git
cd nba-mcp-synthesis
```

### Step 2: Setup Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Setup Database

**Using SQLite (Development):**
```bash
# SQLite database created automatically
# No additional setup needed
```

**Using PostgreSQL (Recommended):**
```bash
# Create database
createdb nba_mcp

# Initialize schema
psql nba_mcp < schema/init.sql
```

### Step 4: Initialize MLflow (Optional)

```bash
# Start MLflow server
mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlruns \
    --host 0.0.0.0 \
    --port 5000
```

Access at: http://localhost:5000

### Step 5: Run Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=mcp_server --cov-report=html

# Expected: 350+ tests passing
```

### Step 6: Start System

```bash
# In separate terminals:

# Terminal 1: MLflow (if using)
mlflow server --host 0.0.0.0 --port 5000

# Terminal 2: Health check
python -c "from mcp_server.system_health import SystemHealthChecker; print(SystemHealthChecker().get_health_summary())"
```

### Step 7: Verify Deployment

```python
from mcp_server.system_health import quick_health_check

if quick_health_check():
    print("✓ System healthy and ready")
else:
    print("✗ System has issues")
```

---

## Staging Deployment

### Step 1: Provision Infrastructure

**EC2 Instance:**
```bash
# Launch EC2 instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.large \
    --key-name nba-mcp-staging \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nba-mcp-staging}]'
```

**RDS PostgreSQL:**
```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier nba-mcp-staging \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 14.7 \
    --master-username admin \
    --master-user-password <secure-password> \
    --allocated-storage 100 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name nba-mcp-staging \
    --backup-retention-period 7
```

**S3 Bucket:**
```bash
# Create S3 bucket
aws s3 mb s3://nba-mcp-staging
aws s3api put-bucket-versioning \
    --bucket nba-mcp-staging \
    --versioning-configuration Status=Enabled
```

### Step 2: Deploy Application

**SSH to EC2:**
```bash
ssh -i nba-mcp-staging.pem ubuntu@<ec2-ip>
```

**Setup Application:**
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql-client

# Clone repository
git clone https://github.com/your-org/nba-mcp-synthesis.git
cd nba-mcp-synthesis

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.staging .env
# Edit .env with staging credentials

# Initialize database
export DATABASE_URL="postgresql://admin:pass@rds-endpoint:5432/nba_mcp"
python scripts/init_db.py
```

### Step 3: Deploy MLflow

**Using Docker:**
```bash
docker run -d \
    --name mlflow \
    -p 5000:5000 \
    -v /var/nba-mcp/mlruns:/mlruns \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    ghcr.io/mlflow/mlflow:latest \
    mlflow server \
        --backend-store-uri postgresql://admin:pass@rds-endpoint:5432/mlflow \
        --default-artifact-root s3://nba-mcp-staging/mlruns \
        --host 0.0.0.0
```

### Step 4: Configure systemd Service

Create `/etc/systemd/system/nba-mcp.service`:
```ini
[Unit]
Description=NBA MCP Service
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nba-mcp-synthesis
Environment="PATH=/home/ubuntu/nba-mcp-synthesis/venv/bin"
EnvironmentFile=/home/ubuntu/nba-mcp-synthesis/.env
ExecStart=/home/ubuntu/nba-mcp-synthesis/venv/bin/python -m mcp_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable nba-mcp
sudo systemctl start nba-mcp
sudo systemctl status nba-mcp
```

### Step 5: Setup nginx Reverse Proxy

Create `/etc/nginx/sites-available/nba-mcp`:
```nginx
server {
    listen 80;
    server_name nba-mcp-staging.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /mlflow/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/nba-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Production Deployment

### Step 1: Use Production Deployment Checklist

**Before proceeding, complete:** [Production Readiness Checklist](checklists/PRODUCTION_READINESS.md)

### Step 2: Provision Production Infrastructure

**High Availability Setup:**

**Load Balancer:**
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
    --name nba-mcp-prod \
    --subnets subnet-xxxxx subnet-yyyyy \
    --security-groups sg-xxxxx \
    --scheme internet-facing
```

**Auto Scaling Group:**
```bash
# Create launch template
aws ec2 create-launch-template \
    --launch-template-name nba-mcp-prod \
    --launch-template-data file://launch-template.json

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name nba-mcp-prod \
    --launch-template LaunchTemplateName=nba-mcp-prod,Version=1 \
    --min-size 2 \
    --max-size 10 \
    --desired-capacity 3 \
    --target-group-arns arn:aws:elasticloadbalancing:...
```

**RDS Multi-AZ:**
```bash
# Create production RDS with Multi-AZ
aws rds create-db-instance \
    --db-instance-identifier nba-mcp-prod \
    --db-instance-class db.r5.xlarge \
    --engine postgres \
    --engine-version 14.7 \
    --multi-az \
    --master-username admin \
    --master-user-password <secure-password> \
    --allocated-storage 500 \
    --iops 3000 \
    --storage-type io1 \
    --backup-retention-period 30 \
    --vpc-security-group-ids sg-xxxxx
```

### Step 3: Deploy Using Docker (ECS)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY mcp_server/ ./mcp_server/
COPY tests/ ./tests/

# Run health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "from mcp_server.system_health import quick_health_check; exit(0 if quick_health_check() else 1)"

# Start application
CMD ["python", "-m", "mcp_server"]
```

**Build and push:**
```bash
# Build image
docker build -t nba-mcp:2.0 .

# Tag for ECR
docker tag nba-mcp:2.0 123456789012.dkr.ecr.us-east-1.amazonaws.com/nba-mcp:2.0

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/nba-mcp:2.0
```

**ECS Task Definition:**
```json
{
  "family": "nba-mcp-prod",
  "taskRoleArn": "arn:aws:iam::123456789012:role/nba-mcp-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/nba-mcp-execution-role",
  "networkMode": "awsvpc",
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "nba-mcp",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/nba-mcp:2.0",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/nba-mcp-prod",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deploy to ECS:**
```bash
# Create ECS service
aws ecs create-service \
    --cluster nba-mcp-prod \
    --service-name nba-mcp \
    --task-definition nba-mcp-prod:1 \
    --desired-count 3 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=nba-mcp,containerPort=8000"
```

### Step 4: Configure Monitoring

**CloudWatch Alarms:**
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name nba-mcp-high-error-rate \
    --alarm-description "Alert when error rate exceeds 5%" \
    --metric-name ErrorRate \
    --namespace NBA-MCP \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 5.0 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:nba-mcp-alerts
```

### Step 5: Setup CI/CD Pipeline

See `.github/workflows/` for GitHub Actions CI/CD configuration.

---

## Post-Deployment Verification

### Health Checks

**System Health:**
```bash
curl http://nba-mcp-prod.example.com/health
# Expected: {"status": "healthy", "components": {...}}
```

**Component Health:**
```bash
# Check all components
for component in data_validation model_training model_deployment model_monitoring; do
    echo "Checking $component..."
    curl http://nba-mcp-prod.example.com/health/$component
done
```

### Smoke Tests

**Test Model Prediction:**
```python
import requests

# Test prediction API
response = requests.post(
    "http://nba-mcp-prod.example.com/predict",
    json={
        "model_id": "nba_win_predictor",
        "version": "v2.0",
        "features": {
            "home_score": 105,
            "away_score": 98,
            # ... more features
        }
    }
)

assert response.status_code == 200
assert "prediction" in response.json()
print("✓ Prediction API working")
```

### Performance Tests

**Load Test:**
```bash
# Using Apache Bench
ab -n 1000 -c 10 -T application/json -p test_data.json \
    http://nba-mcp-prod.example.com/predict

# Expected:
# - Requests per second: >100
# - Mean response time: <50ms
# - Failed requests: 0
```

### Monitoring Verification

**Check Metrics:**
```bash
# CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace NBA-MCP \
    --metric-name PredictionLatency \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average
```

---

## Rollback Procedures

### Quick Rollback (ECS)

**Rollback to previous task definition:**
```bash
# List task definitions
aws ecs list-task-definitions --family-prefix nba-mcp-prod

# Update service to previous version
aws ecs update-service \
    --cluster nba-mcp-prod \
    --service nba-mcp \
    --task-definition nba-mcp-prod:previous_version
```

### Model Rollback

**Rollback to previous model version:**
```python
from mcp_server.model_registry import ModelRegistry, ModelStage

registry = ModelRegistry()

# Promote previous version
registry.promote_model(
    model_name="nba_win_predictor",
    version="v1.9",  # Previous stable version
    target_stage=ModelStage.PRODUCTION
)
```

### Database Rollback

**Restore from backup:**
```bash
# Stop application
sudo systemctl stop nba-mcp

# Restore database
pg_restore -d nba_mcp /backups/db/nba_mcp_backup.sql

# Start application
sudo systemctl start nba-mcp

# Verify
python -c "from mcp_server.system_health import quick_health_check; print(quick_health_check())"
```

---

## Deployment Checklist

Before deploying to production, complete:
- [ ] [Production Readiness Checklist](checklists/PRODUCTION_READINESS.md)
- [ ] [Deployment Checklist](checklists/DEPLOYMENT_CHECKLIST.md)

After deployment, have ready:
- [ ] [Incident Response Guide](checklists/INCIDENT_RESPONSE.md)
- [ ] [Operations Guide](OPERATIONS_GUIDE.md)

---

## Support

For deployment issues:
1. Check logs: `tail -f /var/log/nba-mcp/app.log`
2. Run health checks: See [Operations Guide](OPERATIONS_GUIDE.md#health-checks)
3. Contact: DevOps team (#nba-mcp-ops)

**Deployment Status:** Production Ready ✅
