# NBA MCP Synthesis - Secrets Management Guide

## Overview

This guide covers the comprehensive secrets management system implemented for NBA MCP Synthesis and related projects. The system provides centralized, hierarchical, and context-aware secret management with enhanced security, validation, and monitoring capabilities.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Directory Structure](#directory-structure)
3. [Naming Convention](#naming-convention)
4. [Context Management](#context-management)
5. [Loading Mechanisms](#loading-mechanisms)
6. [Validation & Health Checks](#validation--health-checks)
7. [Slack Integration](#slack-integration)
8. [Security Features](#security-features)
9. [Docker Integration](#docker-integration)
10. [Kubernetes Integration](#kubernetes-integration)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## System Architecture

### Core Components

The secrets management system consists of several key components:

1. **Unified Secrets Manager** (`mcp_server/unified_secrets_manager.py`)
   - Centralized secret loading and management
   - AWS Secrets Manager fallback
   - Context detection and hierarchical loading
   - Naming convention enforcement

2. **Enhanced Loader Scripts**
   - `load_env_nba_mcp_synthesis_workflow.py` - Production/workflow secrets
   - `load_env_nba_mcp_synthesis_local.py` - Development secrets
   - Validation, health checks, and Slack integration

3. **Hierarchical Loader** (`/Users/ryanranft/load_env_hierarchical.py`)
   - Universal loader for all projects
   - Automatic context detection
   - Backward compatibility support

4. **Configuration Manager** (`mcp_server/unified_configuration_manager.py`)
   - Merged configuration management
   - Environment-specific settings
   - Secret interpolation

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Secrets Management System                 │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  ├── NBA MCP Synthesis                                      │
│  ├── NBA Simulator AWS                                      │
│  └── Future Projects                                        │
├─────────────────────────────────────────────────────────────┤
│  Loader Layer                                               │
│  ├── Enhanced Python Loaders                               │
│  ├── Hierarchical Loader                                   │
│  └── Shell Script Loaders                                  │
├─────────────────────────────────────────────────────────────┤
│  Management Layer                                           │
│  ├── Unified Secrets Manager                               │
│  ├── Configuration Manager                                 │
│  └── Validation & Health Checks                            │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                              │
│  ├── Local File System (/Users/ryanranft/Desktop/++/)      │
│  ├── AWS Secrets Manager (Fallback)                        │
│  └── Docker/Kubernetes Secrets                             │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

### Centralized Secrets Location

All secrets are stored in a centralized, hierarchical directory structure:

```
/Users/ryanranft/Desktop/++/
└── big_cat_bets_assets/
    └── sports_assets/
        ├── big_cat_bets_global/
        │   ├── .env.global.production/
        │   ├── .env.global.development/
        │   └── .env.global.test/
        └── big_cat_bets_simulators/
            └── NBA/
                ├── nba-mcp-synthesis/
                │   ├── .env.nba_mcp_synthesis.production/
                │   ├── .env.nba_mcp_synthesis.development/
                │   └── .env.nba_mcp_synthesis.test/
                └── nba-simulator-aws/
                    ├── .env.nba_simulator_aws.production/
                    ├── .env.nba_simulator_aws.development/
                    └── .env.nba_simulator_aws.test/
```

### Directory Naming Convention

- **Project Level**: `{project-name}/` (e.g., `nba-mcp-synthesis/`)
- **Environment Level**: `.env.{project}.{context}/` (e.g., `.env.nba_mcp_synthesis.production/`)
- **Secret Files**: `{VARIABLE_NAME}.env` (e.g., `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env`)

## Naming Convention

### Environment Variable Format

All environment variables follow this comprehensive format:

```
{SERVICE}_{RESOURCE_TYPE}_{PROJECT}_{CONTEXT}
```

### Examples

**Production (WORKFLOW) Context:**
- `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
- `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
- `DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
- `OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
- `DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW`
- `SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW`
- `LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_WORKFLOW`

**Development Context:**
- `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT`
- `DB_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT`
- `SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_DEVELOPMENT`

**Test Context:**
- `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST`
- `MOCK_API_KEY_NBA_MCP_SYNTHESIS_TEST`

### Naming Components

1. **SERVICE**: Provider/service name
   - `GOOGLE`, `ANTHROPIC`, `OPENAI`, `DEEPSEEK`
   - `SLACK`, `LINEAR`, `GITHUB`
   - `DB`, `AWS`, `REDIS`

2. **RESOURCE_TYPE**: What the secret is
   - `API_KEY`, `SECRET_KEY`, `ACCESS_KEY`
   - `PASSWORD`, `TOKEN`, `CERTIFICATE`
   - `WEBHOOK_URL`, `CONNECTION_STRING`

3. **PROJECT**: Full project identifier
   - `NBA_MCP_SYNTHESIS` (from nba-mcp-synthesis)
   - `NBA_SIMULATOR_AWS` (from nba-simulator-aws)
   - `BIG_CAT_BETS_GLOBAL` (global level)

4. **CONTEXT**: Environment context
   - `WORKFLOW` (production)
   - `DEVELOPMENT` (development)
   - `TEST` (testing)

### Benefits

1. **AI Assistant Clarity**: Chatbots immediately understand which service, project, and environment
2. **Human Readability**: Developers can instantly identify secrets without documentation
3. **Collision Prevention**: Impossible to confuse keys across projects
4. **Self-Documenting**: Variable name tells the complete story
5. **Search & Filter**: Easy to find all keys for a specific project or service
6. **Audit Trail**: Clear ownership and purpose in logs

## Context Management

### Context Types

The system supports three main contexts:

1. **WORKFLOW** (Production)
   - Used for production workflows and automated processes
   - Strict validation and health checks
   - Full Slack notifications
   - AWS Secrets Manager fallback

2. **DEVELOPMENT** (Development)
   - Used for local development and testing
   - Relaxed validation (warnings only)
   - Optional Slack notifications
   - Local file system only

3. **TEST** (Testing)
   - Used for automated testing
   - Mock secrets and test configurations
   - No external API calls
   - Isolated environment

### Context Detection

The system automatically detects context from:

1. **Environment Variables**:
   ```bash
   export NBA_MCP_CONTEXT=production
   export PROJECT_NAME=nba-mcp-synthesis
   export SPORT_NAME=NBA
   ```

2. **Command Line Arguments**:
   ```bash
   python load_env_hierarchical.py --project nba-mcp-synthesis --context production
   ```

3. **File System Detection**:
   - Checks for `.env.{project}.{context}/` directories
   - Uses the first available context

4. **Default Fallback**:
   - Defaults to `development` if no context is specified

## Loading Mechanisms

### Enhanced Python Loaders

#### Workflow Loader (`load_env_nba_mcp_synthesis_workflow.py`)

```python
#!/usr/bin/env python3
"""
NBA MCP Synthesis - Workflow Environment Loader
Enhanced with validation, health checks, and Slack integration
"""

# Features:
# - Comprehensive secret validation
# - API connectivity health checks
# - Slack notifications
# - Detailed logging
# - Performance monitoring
```

**Usage:**
```bash
python3 load_env_nba_mcp_synthesis_workflow.py
```

#### Local Development Loader (`load_env_nba_mcp_synthesis_local.py`)

```python
#!/usr/bin/env python3
"""
NBA MCP Synthesis - Local Development Environment Loader
Enhanced with validation, health checks, and Slack integration
"""

# Features:
# - Relaxed validation for development
# - Optional API connectivity checks
# - Development-specific Slack notifications
# - Local logging
```

**Usage:**
```bash
python3 load_env_nba_mcp_synthesis_local.py
```

### Hierarchical Loader

#### Universal Loader (`/Users/ryanranft/load_env_hierarchical.py`)

```python
#!/usr/bin/env python3
"""
Universal Hierarchical Secrets Loader
Supports all projects with automatic context detection
"""

# Features:
# - Multi-project support
# - Automatic context detection
# - Naming convention enforcement
# - Backward compatibility
# - AWS Secrets Manager fallback
```

**Usage:**
```bash
# Automatic detection
python3 /Users/ryanranft/load_env_hierarchical.py

# Explicit parameters
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production
```

### Shell Script Loaders

#### Universal Shell Loader (`/Users/ryanranft/load_secrets_universal.sh`)

```bash
#!/bin/bash
"""
Universal Shell Secrets Loader
Sources secrets into current shell environment
"""

# Usage:
source /Users/ryanranft/load_secrets_universal.sh
```

#### Project-Specific Loaders

```bash
# NBA MCP Synthesis Workflow
source /Users/ryanranft/run_with_credentials.sh nba-mcp-synthesis workflow

# NBA Simulator AWS Development
source /Users/ryanranft/nba-sim-credentials-autoload.sh development
```

## Validation & Health Checks

### Secret Validation

The system performs comprehensive validation on all loaded secrets:

#### API Key Validation

```python
class SecretsValidator:
    @staticmethod
    def validate_api_key(key: str, service: str) -> bool:
        """Validate API key format based on service"""
        if service.upper() == 'GOOGLE':
            return key.startswith('AIza') and len(key) >= 30
        elif service.upper() == 'OPENAI':
            return key.startswith('sk-') and len(key) >= 40
        elif service.upper() == 'ANTHROPIC':
            return key.startswith('sk-ant-') and len(key) >= 40
        # ... more services
```

#### URL Validation

```python
@staticmethod
def validate_webhook_url(url: str) -> bool:
    """Validate webhook URL format"""
    return url.startswith('https://hooks.slack.com/') or \
           url.startswith('https://discord.com/api/webhooks/')
```

#### UUID Validation

```python
@staticmethod
def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_str.lower()))
```

### Health Checks

#### API Connectivity Checks

```python
class HealthChecker:
    def check_api_connectivity(self) -> Dict[str, bool]:
        """Check API connectivity for loaded keys"""
        results = {}

        # Google API check
        if 'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW' in self.secrets:
            try:
                response = requests.get(
                    'https://generativelanguage.googleapis.com/v1beta/models',
                    params={'key': self.secrets['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']},
                    timeout=5
                )
                results['google_api'] = response.status_code == 200
            except:
                results['google_api'] = False

        # ... more API checks
        return results
```

#### Health Summary

```python
def get_health_summary(self) -> Dict[str, Any]:
    """Get comprehensive health summary"""
    return {
        'timestamp': datetime.now().isoformat(),
        'total_secrets': len(self.secrets),
        'connectivity_checks': connectivity,
        'strength_checks': strength,
        'overall_health': all(connectivity.values()) and all(strength.values()),
        'issues': [f"{service}: {'OK' if status else 'FAILED'}"
                  for service, status in {**connectivity, **strength}.items()]
    }
```

## Slack Integration

### Slack Notifications

The system provides comprehensive Slack integration for monitoring and alerting:

#### Notification Types

1. **Success Notifications**
   - Successful secret loading
   - Health check results
   - Performance metrics

2. **Warning Notifications**
   - Validation warnings
   - Partial health check failures
   - Performance issues

3. **Error Notifications**
   - Loading failures
   - Critical validation errors
   - System errors

#### Slack Notifier Class

```python
class SlackNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW')
        self.enabled = bool(self.webhook_url)

    def send_notification(self, message: str, level: str = 'info') -> bool:
        """Send notification to Slack"""
        payload = {
            'attachments': [{
                'color': color_map.get(level, '#36a64f'),
                'title': f'NBA MCP Synthesis - Secrets Loader',
                'text': message,
                'timestamp': int(time.time()),
                'footer': 'NBA MCP Synthesis Workflow'
            }]
        }
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        return response.status_code == 200
```

#### Notification Examples

**Success Notification:**
```
✅ Successfully loaded 15 secrets
Health Status: 🟢 Healthy
```

**Warning Notification:**
```
✅ Successfully loaded 12 secrets
Health Status: 🟡 Issues detected
Issues: google_api: FAILED, slack_webhook: FAILED
```

**Error Notification:**
```
❌ Secrets loading failed: No secrets loaded
```

## Security Features

### File Permissions

The system enforces strict file permissions:

```bash
# Directory permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/

# File permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/**/*.env
```

### Audit Logging

All secret access is logged:

```python
# Log file locations
/tmp/nba_mcp_synthesis_workflow.log  # Production logs
/tmp/nba_mcp_synthesis_local.log      # Development logs

# Log format
2024-01-15 10:30:45 - secrets_manager - INFO - Loaded secret: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
```

### Secret Rotation

Automated secret rotation support:

```bash
# Rotate secrets
./scripts/manage_rotation.sh rotate-api-key GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW

# Backup before rotation
./scripts/manage_rotation.sh backup-secrets nba-mcp-synthesis production
```

### Access Control

- **Local Only**: All secrets remain on local file system
- **No Cloud Sync**: Secrets never sync to cloud or browser
- **Encrypted Storage**: Optional encryption for sensitive secrets
- **User Isolation**: Each user has separate secret directories

## Docker Integration

### Docker Secrets Loading

The system provides comprehensive Docker integration:

#### Dockerfile Integration

```dockerfile
FROM python:3.9-slim

# Copy secrets loader
COPY docker/load_secrets_docker.py /app/
COPY mcp_server/unified_secrets_manager.py /app/mcp_server/

# Set entrypoint
ENTRYPOINT ["/app/load_secrets_docker.py"]
CMD ["python", "main.py"]
```

#### Docker Compose Integration

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  nba-mcp-synthesis:
    build: .
    environment:
      - NBA_MCP_CONTEXT=development
      - PROJECT_NAME=nba-mcp-synthesis
    volumes:
      - /Users/ryanranft/Desktop/++/big_cat_bets_assets:/secrets:ro
    command: ["python", "main.py"]
```

#### Docker Secrets Management

```bash
# Build and run with secrets
docker-compose -f docker-compose.dev.yml up --build

# Check secrets in container
docker exec -it nba-mcp-synthesis-dev python -c "import os; print(os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT'))"
```

## Kubernetes Integration

### Kubernetes Secrets

The system provides Kubernetes integration for production deployments:

#### Secret Manifests

```yaml
# k8s/secrets-prod.yaml
apiVersion: v1
kind: Secret
metadata:
  name: nba-mcp-synthesis-prod-secrets
  namespace: big-cat-bets
type: Opaque
data:
  GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW: <base64-encoded>
  DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW: <base64-encoded>
  # ... more secrets
```

#### Init Container Pattern

```yaml
# k8s/init-container.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nba-mcp-synthesis
spec:
  template:
    spec:
      initContainers:
      - name: secrets-loader
        image: nba-mcp-synthesis:latest
        command: ["python", "/app/load_secrets_docker.py"]
        env:
        - name: NBA_MCP_CONTEXT
          value: "production"
        volumeMounts:
        - name: secrets-volume
          mountPath: /secrets
      containers:
      - name: app
        image: nba-mcp-synthesis:latest
        volumeMounts:
        - name: secrets-volume
          mountPath: /secrets
          readOnly: true
```

#### Kubernetes Management

```bash
# Apply secrets
kubectl apply -f k8s/secrets-prod.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Check secrets
kubectl exec -it deployment/nba-mcp-synthesis -- env | grep NBA_MCP
```

## Best Practices

### Secret Management

1. **Use Full Names**: Always use the full context-rich naming convention
   ```python
   # ✅ Preferred
   google_key = os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')

   # ⚠️ Deprecated (but supported)
   google_key = os.getenv('GOOGLE_API_KEY')
   ```

2. **Context Awareness**: Always specify the correct context
   ```bash
   export NBA_MCP_CONTEXT=production
   export PROJECT_NAME=nba-mcp-synthesis
   ```

3. **Validation**: Always validate secrets after loading
   ```python
   if not verify_critical_vars():
       logger.error("Critical variables missing")
       sys.exit(1)
   ```

### Development Workflow

1. **Local Development**:
   ```bash
   # Load development secrets
   python3 load_env_nba_mcp_synthesis_local.py

   # Run application
   python3 main.py
   ```

2. **Production Deployment**:
   ```bash
   # Load production secrets
   python3 load_env_nba_mcp_synthesis_workflow.py

   # Verify health
   # Check Slack notifications

   # Deploy
   docker-compose -f docker-compose.prod.yml up
   ```

3. **Testing**:
   ```bash
   # Load test secrets
   export NBA_MCP_CONTEXT=test
   python3 /Users/ryanranft/load_env_hierarchical.py

   # Run tests
   pytest tests/
   ```

### Security Best Practices

1. **File Permissions**: Always use restrictive permissions
   ```bash
   chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/
   chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/**/*.env
   ```

2. **Audit Logging**: Monitor all secret access
   ```bash
   tail -f /tmp/nba_mcp_synthesis_workflow.log
   ```

3. **Regular Rotation**: Rotate secrets regularly
   ```bash
   ./scripts/manage_rotation.sh schedule-rotation GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
   ```

4. **Backup Strategy**: Always backup before changes
   ```bash
   ./scripts/manage_rotation.sh backup-secrets nba-mcp-synthesis production
   ```

## Troubleshooting

### Common Issues

#### 1. Secrets Directory Not Found

**Error:**
```
❌ Secrets directory not found: /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
```

**Solution:**
```bash
# Create the directory structure
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Set proper permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
```

#### 2. Invalid API Key Format

**Error:**
```
⚠️ Validation warnings:
   - Invalid Google API key format: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
```

**Solution:**
```bash
# Check the API key format
cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Google API keys should start with 'AIza' and be at least 30 characters
# Update with correct key
echo "AIzaSyBCM_xiH6LuDNSNdGS7ShJKSmt17GhH9vw" > /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### 3. API Connectivity Failures

**Error:**
```
📊 Health Summary:
   Overall Health: 🟡 Issues detected
   Connectivity Checks:
     google_api: ❌
     openai_api: ❌
```

**Solution:**
```bash
# Check network connectivity
ping googleapis.com
ping api.openai.com

# Check API key validity
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY"

# Check firewall/proxy settings
# Update API keys if expired
```

#### 4. Slack Notification Failures

**Error:**
```
Failed to send Slack notification: HTTP 400 Bad Request
```

**Solution:**
```bash
# Check webhook URL format
echo $SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW

# Test webhook manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW

# Update webhook URL if invalid
```

#### 5. Permission Denied Errors

**Error:**
```
❌ Error loading /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env: Permission denied
```

**Solution:**
```bash
# Check current permissions
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Fix permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env

# Check ownership
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Set debug environment variable
export NBA_MCP_DEBUG=true

# Run loader with debug output
python3 load_env_nba_mcp_synthesis_workflow.py

# Check debug logs
tail -f /tmp/nba_mcp_synthesis_workflow.log
```

### Health Check Commands

```bash
# Check overall system health
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
print(f'Loaded {len(secrets)} secrets')
"

# Check specific secret
python3 -c "
import os
print('GOOGLE_API_KEY:', os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'))
"

# Validate naming convention
python3 scripts/enforce_naming_convention.py --validate
```

### Log Analysis

```bash
# Check recent errors
grep -i error /tmp/nba_mcp_synthesis_workflow.log | tail -10

# Check validation warnings
grep -i warning /tmp/nba_mcp_synthesis_workflow.log | tail -10

# Check successful loads
grep -i "loaded secret" /tmp/nba_mcp_synthesis_workflow.log | tail -10
```

### Recovery Procedures

#### 1. Restore from Backup

```bash
# List available backups
ls -la /Users/ryanranft/Desktop/++/backups/

# Restore specific backup
./scripts/manage_rotation.sh restore-backup nba-mcp-synthesis production 2024-01-15
```

#### 2. Emergency Secret Loading

```bash
# Use emergency loader (bypasses validation)
python3 /Users/ryanranft/load_env_hierarchical.py --emergency --project nba-mcp-synthesis --context production
```

#### 3. Reset to Defaults

```bash
# Reset to default configuration
./scripts/manage_rotation.sh reset-config nba-mcp-synthesis production
```

## Support

For additional support:

1. **Check Logs**: Review log files in `/tmp/`
2. **Run Health Checks**: Use the built-in health check commands
3. **Validate Configuration**: Use the naming convention validator
4. **Test Connectivity**: Use the API connectivity tests
5. **Check Permissions**: Verify file and directory permissions

## Conclusion

The NBA MCP Synthesis secrets management system provides a comprehensive, secure, and scalable solution for managing secrets across all environments. With its context-rich naming convention, hierarchical loading, validation, health checks, and Slack integration, it ensures reliable and secure secret management for all projects.

For migration from the old system, refer to the [Migration Guide](MIGRATION_GUIDE.md). For additional troubleshooting, see the [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md).

