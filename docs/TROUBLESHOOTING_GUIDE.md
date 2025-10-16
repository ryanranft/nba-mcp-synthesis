# NBA MCP Synthesis - Troubleshooting Guide

## Overview

This troubleshooting guide provides comprehensive solutions for common issues encountered with the NBA MCP Synthesis secrets management system. It covers diagnosis, resolution, and prevention strategies.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Common Issues](#common-issues)
3. [System-Specific Issues](#system-specific-issues)
4. [Performance Issues](#performance-issues)
5. [Security Issues](#security-issues)
6. [Integration Issues](#integration-issues)
7. [Recovery Procedures](#recovery-procedures)
8. [Prevention Strategies](#prevention-strategies)
9. [Debug Tools](#debug-tools)
10. [Support Resources](#support-resources)

## Quick Diagnosis

### Health Check Commands

```bash
# Quick system health check
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
try:
    secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
    print(f'✅ System healthy: {len(secrets)} secrets loaded')
except Exception as e:
    print(f'❌ System error: {e}')
"

# Check environment variables
python3 -c "
import os
critical_vars = [
    'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'
]
missing = [var for var in critical_vars if not os.getenv(var)]
if missing:
    print(f'❌ Missing variables: {missing}')
else:
    print('✅ All critical variables present')
"

# Check file permissions
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check recent logs
tail -20 /tmp/nba_mcp_synthesis_workflow.log
```

### Status Indicators

| Status | Indicator | Meaning |
|--------|-----------|---------|
| 🟢 | `✅ System healthy` | All systems operational |
| 🟡 | `⚠️ Warnings detected` | Non-critical issues present |
| 🔴 | `❌ System error` | Critical issues requiring attention |
| ⚪ | `No output` | System not responding |

## Common Issues

### Issue 1: Secrets Directory Not Found

#### Symptoms
```
❌ Secrets directory not found: /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
Please ensure the centralized secrets structure is set up
```

#### Diagnosis
```bash
# Check if directory exists
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check parent directories
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/
```

#### Resolution
```bash
# Create missing directory structure
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Set proper permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Verify creation
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

#### Prevention
- Always create directory structure before migration
- Use automated setup scripts
- Verify directory creation in deployment scripts

### Issue 2: Permission Denied Errors

#### Symptoms
```
❌ Error loading /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env: Permission denied
```

#### Diagnosis
```bash
# Check file permissions
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check directory permissions
ls -ld /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check ownership
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/ | head -5
```

#### Resolution
```bash
# Fix directory permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Fix file permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env

# Fix ownership (if needed)
sudo chown -R $(whoami):$(whoami) /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
```

#### Prevention
- Use automated permission scripts
- Set permissions immediately after file creation
- Regular permission audits

### Issue 3: Invalid API Key Format

#### Symptoms
```
⚠️ Validation warnings:
   - Invalid Google API key format: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
   - Invalid OpenAI API key format: OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
```

#### Diagnosis
```bash
# Check API key format
cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Check key length
wc -c /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Check for whitespace
hexdump -C /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### Resolution
```bash
# Google API keys should start with 'AIza' and be at least 30 characters
# OpenAI API keys should start with 'sk-' and be at least 40 characters
# Anthropic API keys should start with 'sk-ant-' and be at least 40 characters

# Fix Google API key
echo "your_google_api_key_here" > /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Fix OpenAI API key
echo "your_openai_api_key_here" > /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Set proper permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env
```

#### Prevention
- Validate API keys during creation
- Use automated validation scripts
- Regular format checks

### Issue 4: Missing Critical Variables

#### Symptoms
```
❌ Missing critical variables: ['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW', 'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']
```

#### Diagnosis
```bash
# Check which files exist
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check file contents
for file in /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env; do
    echo "File: $(basename $file)"
    echo "Size: $(wc -c < $file) bytes"
    echo "Content preview: $(head -c 10 $file)..."
    echo "---"
done
```

#### Resolution
```bash
# Create missing files
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Create missing Google API key
echo "your_google_api_key_here" > GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Create missing DeepSeek API key
echo "your_deepseek_api_key_here" > DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### Prevention
- Use migration scripts
- Validate all required files exist
- Regular inventory checks

### Issue 5: API Connectivity Failures

#### Symptoms
```
📊 Health Summary:
   Overall Health: 🟡 Issues detected
   Connectivity Checks:
     google_api: ❌
     openai_api: ❌
     slack_webhook: ❌
```

#### Diagnosis
```bash
# Test network connectivity
ping -c 3 googleapis.com
ping -c 3 api.openai.com
ping -c 3 hooks.slack.com

# Test API endpoints
curl -I https://generativelanguage.googleapis.com/v1beta/models
curl -I https://api.openai.com/v1/models

# Check DNS resolution
nslookup googleapis.com
nslookup api.openai.com
```

#### Resolution
```bash
# Check API key validity
GOOGLE_KEY=$(cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env)
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_KEY"

# Check OpenAI API key
OPENAI_KEY=$(cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env)
curl -H "Authorization: Bearer $OPENAI_KEY" https://api.openai.com/v1/models

# Check Slack webhook
SLACK_URL=$(cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW.env)
curl -X POST -H 'Content-type: application/json' --data '{"text":"Test message"}' $SLACK_URL
```

#### Prevention
- Regular API key rotation
- Monitor API usage limits
- Test connectivity before deployment

## System-Specific Issues

### Issue 6: Context Detection Problems

#### Symptoms
```
❌ Unable to detect context
❌ Invalid context: unknown
```

#### Diagnosis
```bash
# Check environment variables
echo "NBA_MCP_CONTEXT: $NBA_MCP_CONTEXT"
echo "PROJECT_NAME: $PROJECT_NAME"
echo "SPORT_NAME: $SPORT_NAME"

# Check available contexts
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.*/
```

#### Resolution
```bash
# Set context explicitly
export NBA_MCP_CONTEXT=production
export PROJECT_NAME=nba-mcp-synthesis
export SPORT_NAME=NBA

# Or use command line arguments
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production
```

#### Prevention
- Always set context environment variables
- Use explicit context in scripts
- Document context requirements

### Issue 7: Backward Compatibility Issues

#### Symptoms
```
❌ GOOGLE_API_KEY environment variable is not set
❌ DEEPSEEK_API_KEY environment variable is not set
```

#### Diagnosis
```bash
# Check if old names are available
python3 -c "
import os
old_names = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY']
for name in old_names:
    value = os.getenv(name)
    if value:
        print(f'{name}: {value[:10]}...')
    else:
        print(f'{name}: NOT SET')
"

# Check if new names are available
python3 -c "
import os
new_names = ['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW', 'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']
for name in new_names:
    value = os.getenv(name)
    if value:
        print(f'{name}: {value[:10]}...')
    else:
        print(f'{name}: NOT SET')
"
```

#### Resolution
```bash
# Ensure backward compatibility is enabled
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
manager._create_aliases({'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW': 'test_key'})
print('Backward compatibility enabled')
"

# Or update code to use new names
# Replace os.getenv('GOOGLE_API_KEY') with os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
```

#### Prevention
- Use new naming convention in new code
- Gradually migrate old code
- Test backward compatibility regularly

## Performance Issues

### Issue 8: Slow Secret Loading

#### Symptoms
```
⏱️ Execution time: 15.23 seconds
```

#### Diagnosis
```bash
# Profile secret loading
python3 -c "
import time
import cProfile
from mcp_server.unified_secrets_manager import UnifiedSecretsManager

def profile_loading():
    manager = UnifiedSecretsManager()
    start = time.time()
    secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
    end = time.time()
    print(f'Loading time: {end - start:.2f} seconds')
    print(f'Secrets loaded: {len(secrets)}')

cProfile.run('profile_loading()')
"

# Check file system performance
time ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

#### Resolution
```bash
# Optimize file system
# Use SSD storage
# Reduce number of files
# Use caching

# Enable caching in unified secrets manager
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
manager.enable_caching = True
print('Caching enabled')
"
```

#### Prevention
- Use SSD storage
- Minimize number of secret files
- Enable caching
- Regular performance monitoring

### Issue 9: Memory Usage Issues

#### Symptoms
```
Memory usage: 500MB for 1000 secrets
```

#### Diagnosis
```bash
# Check memory usage
python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Profile memory usage
python3 -c "
import tracemalloc
from mcp_server.unified_secrets_manager import UnifiedSecretsManager

tracemalloc.start()
manager = UnifiedSecretsManager()
secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
current, peak = tracemalloc.get_traced_memory()
print(f'Current memory: {current / 1024 / 1024:.2f} MB')
print(f'Peak memory: {peak / 1024 / 1024:.2f} MB')
"
```

#### Resolution
```bash
# Optimize memory usage
# Use lazy loading
# Clear unused secrets
# Use generators instead of lists

# Enable lazy loading
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
manager.lazy_loading = True
print('Lazy loading enabled')
"
```

#### Prevention
- Use lazy loading
- Clear unused secrets
- Monitor memory usage
- Optimize data structures

## Security Issues

### Issue 10: Insecure File Permissions

#### Symptoms
```
-rw-r--r-- 1 user staff 32 Jan 15 10:30 GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### Diagnosis
```bash
# Check file permissions
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Check directory permissions
ls -ld /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

#### Resolution
```bash
# Fix file permissions
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env

# Fix directory permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Verify fix
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

#### Prevention
- Use automated permission scripts
- Regular permission audits
- Security monitoring

### Issue 11: Secret Exposure in Logs

#### Symptoms
```
2024-01-15 10:30:45 - secrets_manager - INFO - Loaded secret: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW=your_google_api_key_here
```

#### Diagnosis
```bash
# Check logs for secret exposure
grep -i "api_key\|password\|secret" /tmp/nba_mcp_synthesis_workflow.log

# Check for full secret values
grep -E "=[A-Za-z0-9]{20,}" /tmp/nba_mcp_synthesis_workflow.log
```

#### Resolution
```bash
# Update logging to mask secrets
python3 -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mask secret values
def mask_secret(value):
    if len(value) > 8:
        return value[:4] + '*' * (len(value) - 8) + value[-4:]
    return '*' * len(value)

secret_value = 'your_google_api_key_here'
logger.info(f'Loaded secret: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW={mask_secret(secret_value)}')
"

# Clear existing logs
> /tmp/nba_mcp_synthesis_workflow.log
```

#### Prevention
- Mask secret values in logs
- Use structured logging
- Regular log audits
- Secure log storage

## Integration Issues

### Issue 12: Docker Integration Problems

#### Symptoms
```
❌ Docker container failed to start
❌ Secrets not available in container
```

#### Diagnosis
```bash
# Check Docker container
docker ps -a | grep nba-mcp-synthesis

# Check container logs
docker logs nba-mcp-synthesis-dev

# Check volume mounts
docker inspect nba-mcp-synthesis-dev | grep -A 10 "Mounts"
```

#### Resolution
```bash
# Fix volume mounts
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up --build

# Check secrets in container
docker exec -it nba-mcp-synthesis-dev env | grep NBA_MCP

# Test secrets loading in container
docker exec -it nba-mcp-synthesis-dev python -c "
import os
print('GOOGLE_API_KEY:', os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT'))
"
```

#### Prevention
- Test Docker integration regularly
- Use proper volume mounts
- Validate secrets in containers

### Issue 13: Kubernetes Integration Problems

#### Symptoms
```
❌ Pod failed to start
❌ Init container failed
❌ Secrets not available in pod
```

#### Diagnosis
```bash
# Check pod status
kubectl get pods -n big-cat-bets

# Check pod logs
kubectl logs -n big-cat-bets deployment/nba-mcp-synthesis

# Check init container logs
kubectl logs -n big-cat-bets deployment/nba-mcp-synthesis -c secrets-loader
```

#### Resolution
```bash
# Fix Kubernetes secrets
kubectl apply -f k8s/secrets-prod.yaml

# Restart deployment
kubectl rollout restart deployment/nba-mcp-synthesis -n big-cat-bets

# Check secrets in pod
kubectl exec -it deployment/nba-mcp-synthesis -n big-cat-bets -- env | grep NBA_MCP
```

#### Prevention
- Test Kubernetes integration regularly
- Use proper secret manifests
- Validate secrets in pods

## Recovery Procedures

### Emergency Recovery

#### Step 1: Stop All Processes
```bash
# Stop all NBA MCP processes
pkill -f "nba-mcp-synthesis"
pkill -f "load_env_hierarchical"
pkill -f "unified_secrets_manager"
```

#### Step 2: Restore from Backup
```bash
# List available backups
ls -la /Users/ryanranft/Desktop/++/backups/

# Restore latest backup
BACKUP_DATE=$(ls -t /Users/ryanranft/Desktop/++/backups/ | head -1)
cp -r /Users/ryanranft/Desktop/++/backups/$BACKUP_DATE/.env.workflow/* /Users/ryanranft/nba-mcp-synthesis/.env.workflow/
```

#### Step 3: Use Emergency Loader
```bash
# Use emergency loader (bypasses validation)
python3 /Users/ryanranft/load_env_hierarchical.py --emergency --project nba-mcp-synthesis --context production
```

#### Step 4: Verify Recovery
```bash
# Test system functionality
python3 -c "
import os
print('GOOGLE_API_KEY:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')
print('DEEPSEEK_API_KEY:', 'SET' if os.getenv('DEEPSEEK_API_KEY') else 'NOT SET')
"
```

### Partial Recovery

#### Step 1: Identify Working Components
```bash
# Check which secrets are working
python3 -c "
import os
secrets = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
working = [s for s in secrets if os.getenv(s)]
print(f'Working secrets: {working}')
print(f'Broken secrets: {[s for s in secrets if s not in working]}')
"
```

#### Step 2: Fix Broken Components
```bash
# Fix individual secrets
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Fix specific secret
echo "new_api_key_here" > BROKEN_SECRET_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 BROKEN_SECRET_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### Step 3: Test Partial Recovery
```bash
# Test with working secrets only
python3 -c "
import os
if os.getenv('GOOGLE_API_KEY'):
    print('✅ Google API working')
if os.getenv('DEEPSEEK_API_KEY'):
    print('✅ DeepSeek API working')
"
```

## Prevention Strategies

### Regular Maintenance

#### Daily Checks
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check ==="
echo "Date: $(date)"

# Check system health
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
print(f'Secrets loaded: {len(secrets)}')
"

# Check file permissions
find /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/ -type f ! -perm 600 -exec echo "Insecure file: {}" \;

# Check recent errors
grep -i error /tmp/nba_mcp_synthesis_workflow.log | tail -5

echo "=== Health Check Complete ==="
```

#### Weekly Checks
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== Weekly Maintenance ==="
echo "Date: $(date)"

# Backup current secrets
BACKUP_DIR="/Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR
cp -r /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production $BACKUP_DIR/

# Rotate logs
mv /tmp/nba_mcp_synthesis_workflow.log /tmp/nba_mcp_synthesis_workflow.log.$(date +%Y%m%d)
touch /tmp/nba_mcp_synthesis_workflow.log

# Check for stale secrets
python3 -c "
import os
import time
stale_threshold = 30 * 24 * 3600  # 30 days
for file in os.listdir('/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/'):
    if file.endswith('.env'):
        file_path = os.path.join('/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/', file)
        mtime = os.path.getmtime(file_path)
        if time.time() - mtime > stale_threshold:
            print(f'Stale secret: {file}')
"

echo "=== Weekly Maintenance Complete ==="
```

### Monitoring and Alerting

#### Health Monitoring
```bash
#!/bin/bash
# health_monitor.sh

# Check system health every 5 minutes
while true; do
    python3 -c "
    from mcp_server.unified_secrets_manager import UnifiedSecretsManager
    manager = UnifiedSecretsManager()
    try:
        secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
        if len(secrets) < 10:
            print('ALERT: Low secret count')
        else:
            print('OK: System healthy')
    except Exception as e:
        print(f'ALERT: System error - {e}')
    "
    sleep 300  # 5 minutes
done
```

#### Slack Alerts
```bash
#!/bin/bash
# slack_alert.sh

# Send alert to Slack
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"NBA MCP Synthesis: System health check failed"}' \
  $SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW
```

## Debug Tools

### Debug Mode

#### Enable Debug Mode
```bash
# Set debug environment variable
export NBA_MCP_DEBUG=true

# Run with debug output
python3 load_env_nba_mcp_synthesis_workflow.py

# Check debug logs
tail -f /tmp/nba_mcp_synthesis_workflow.log
```

#### Debug Scripts
```bash
#!/bin/bash
# debug_secrets.sh

echo "=== Secrets Debug Information ==="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo

echo "=== Environment Variables ==="
echo "NBA_MCP_CONTEXT: $NBA_MCP_CONTEXT"
echo "PROJECT_NAME: $PROJECT_NAME"
echo "SPORT_NAME: $SPORT_NAME"
echo

echo "=== File System ==="
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
echo

echo "=== Python Environment ==="
python3 -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python path: {sys.path[:3]}...')
"
echo

echo "=== Secrets Status ==="
python3 -c "
import os
secrets = ['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW', 'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']
for secret in secrets:
    value = os.getenv(secret)
    if value:
        print(f'{secret}: SET ({len(value)} chars)')
    else:
        print(f'{secret}: NOT SET')
"
echo

echo "=== Debug Complete ==="
```

### Log Analysis

#### Log Parsing
```bash
#!/bin/bash
# analyze_logs.sh

LOG_FILE="/tmp/nba_mcp_synthesis_workflow.log"

echo "=== Log Analysis ==="
echo "Log file: $LOG_FILE"
echo "File size: $(wc -c < $LOG_FILE) bytes"
echo "Last modified: $(stat -f "%Sm" $LOG_FILE)"
echo

echo "=== Recent Errors ==="
grep -i error $LOG_FILE | tail -10
echo

echo "=== Recent Warnings ==="
grep -i warning $LOG_FILE | tail -10
echo

echo "=== Recent Success ==="
grep -i "loaded secret" $LOG_FILE | tail -10
echo

echo "=== Performance Metrics ==="
grep "Execution time" $LOG_FILE | tail -5
echo

echo "=== Log Analysis Complete ==="
```

## Support Resources

### Documentation
- [Secrets Management Guide](SECRETS_MANAGEMENT_GUIDE.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)

### Tools
- `scripts/enforce_naming_convention.py` - Naming convention validation
- `scripts/manage_permissions.sh` - Permission management
- `scripts/manage_rotation.sh` - Secret rotation
- `scripts/manage_audit.sh` - Audit logging

### Logs
- `/tmp/nba_mcp_synthesis_workflow.log` - Production logs
- `/tmp/nba_mcp_synthesis_local.log` - Development logs
- `/tmp/nba_mcp_synthesis_test.log` - Test logs

### Backup Locations
- `/Users/ryanranft/Desktop/++/backups/` - Secret backups
- `/Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)/` - Daily backups

### Emergency Contacts
- System Administrator: [Contact Information]
- Security Team: [Contact Information]
- Development Team: [Contact Information]

## Conclusion

This troubleshooting guide provides comprehensive solutions for common issues with the NBA MCP Synthesis secrets management system. Regular maintenance, monitoring, and following best practices will help prevent most issues.

For additional support:
1. Check the logs first
2. Run health checks
3. Use debug tools
4. Follow recovery procedures
5. Contact support if needed

Remember to always backup your secrets before making changes and test recovery procedures regularly.

