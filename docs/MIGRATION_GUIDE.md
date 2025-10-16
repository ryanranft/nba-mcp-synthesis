# NBA MCP Synthesis - Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the old secrets management system to the new unified, hierarchical system with context-rich naming conventions.

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Migration Steps](#migration-steps)
3. [Code Updates](#code-updates)
4. [Testing Migration](#testing-migration)
5. [Rollback Procedures](#rollback-procedures)
6. [Post-Migration Validation](#post-migration-validation)
7. [Common Issues](#common-issues)

## Pre-Migration Checklist

### 1. Backup Current System

```bash
# Create backup directory
mkdir -p /Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)

# Backup current .env files
cp -r /Users/ryanranft/nba-mcp-synthesis/.env.workflow /Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)/

# Backup AWS Secrets Manager (if used)
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `NBA_MCP`)].Name' --output text > /Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)/aws_secrets_list.txt
```

### 2. Verify Current Secrets

```bash
# List current secrets
ls -la /Users/ryanranft/nba-mcp-synthesis/.env.workflow/

# Check secret values (without exposing them)
for file in /Users/ryanranft/nba-mcp-synthesis/.env.workflow/*; do
    echo "File: $(basename $file)"
    echo "Size: $(wc -c < $file) bytes"
    echo "---"
done
```

### 3. Document Current Usage

```bash
# Find all references to old environment variables
grep -r "GOOGLE_API_KEY" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
grep -r "DEEPSEEK_API_KEY" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
grep -r "ANTHROPIC_API_KEY" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
grep -r "OPENAI_API_KEY" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
grep -r "SLACK_WEBHOOK_URL" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
grep -r "LINEAR_API_KEY" /Users/ryanranft/nba-mcp-synthesis/ --exclude-dir=.git
```

## Migration Steps

### Step 1: Create New Directory Structure

```bash
# Create the new hierarchical directory structure
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.test

# Set proper permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.test
```

### Step 2: Migrate Secrets with New Naming Convention

#### Production Secrets Migration

```bash
# Navigate to production secrets directory
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Migrate Google API Key
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/GOOGLE_API_KEY GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate DeepSeek API Key
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/DEEPSEEK_API_KEY DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Anthropic API Key
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/ANTHROPIC_API_KEY ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate OpenAI API Key
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/OPENAI_API_KEY OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Slack Webhook URL
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/SLACK_WEBHOOK_URL SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Slack Channel
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/SLACK_CHANNEL SLACK_CHANNEL_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 SLACK_CHANNEL_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Linear API Key
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_API_KEY LINEAR_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 LINEAR_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Linear Team ID
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_TEAM_ID LINEAR_TEAM_ID_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 LINEAR_TEAM_ID_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Linear Project ID
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_PROJECT_ID LINEAR_PROJECT_ID_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 LINEAR_PROJECT_ID_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate workflow settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_ENABLE_NOTIFICATIONS WORKFLOW_ENABLE_NOTIFICATIONS_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_ENABLE_NOTIFICATIONS_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_ENABLE_LINEAR_ISSUES WORKFLOW_ENABLE_LINEAR_ISSUES_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_ENABLE_LINEAR_ISSUES_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate cost management settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_BUDGET_ALERT_THRESHOLD_1 WORKFLOW_BUDGET_ALERT_THRESHOLD_1_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_BUDGET_ALERT_THRESHOLD_1_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_BUDGET_ALERT_THRESHOLD_2 WORKFLOW_BUDGET_ALERT_THRESHOLD_2_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_BUDGET_ALERT_THRESHOLD_2_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_MAX_COST_PER_BOOK WORKFLOW_MAX_COST_PER_BOOK_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_MAX_COST_PER_BOOK_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate notification settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_NOTIFICATION_BATCH_SIZE WORKFLOW_NOTIFICATION_BATCH_SIZE_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_NOTIFICATION_BATCH_SIZE_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_ENABLE_SLACK_THREADS WORKFLOW_ENABLE_SLACK_THREADS_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_ENABLE_SLACK_THREADS_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate retry settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_MAX_RETRIES WORKFLOW_MAX_RETRIES_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_MAX_RETRIES_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_RETRY_DELAY WORKFLOW_RETRY_DELAY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_RETRY_DELAY_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_RETRY_BACKOFF WORKFLOW_RETRY_BACKOFF_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_RETRY_BACKOFF_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate checkpoint settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_ENABLE_CHECKPOINTS WORKFLOW_ENABLE_CHECKPOINTS_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_ENABLE_CHECKPOINTS_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_CHECKPOINT_INTERVAL WORKFLOW_CHECKPOINT_INTERVAL_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_CHECKPOINT_INTERVAL_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate Linear deduplication settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_ENABLE_DEDUPLICATION LINEAR_ENABLE_DEDUPLICATION_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 LINEAR_ENABLE_DEDUPLICATION_NBA_MCP_SYNTHESIS_WORKFLOW.env

cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_SIMILARITY_THRESHOLD LINEAR_SIMILARITY_THRESHOLD_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 LINEAR_SIMILARITY_THRESHOLD_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Migrate logging settings
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/WORKFLOW_LOG_LEVEL WORKFLOW_LOG_LEVEL_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 WORKFLOW_LOG_LEVEL_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

#### Development Secrets Migration

```bash
# Navigate to development secrets directory
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development

# Copy production secrets as development base (you can modify these later)
cp /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/* .

# Rename all files to use DEVELOPMENT context
for file in *_WORKFLOW.env; do
    new_name=$(echo $file | sed 's/_WORKFLOW\.env$/_DEVELOPMENT.env/')
    mv "$file" "$new_name"
done

# Set proper permissions
chmod 600 *.env
```

#### Test Secrets Migration

```bash
# Navigate to test secrets directory
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.test

# Create mock/test secrets
echo "mock_google_api_key_for_testing" > GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST.env
echo "mock_deepseek_api_key_for_testing" > DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_TEST.env
echo "mock_anthropic_api_key_for_testing" > ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_TEST.env
echo "mock_openai_api_key_for_testing" > OPENAI_API_KEY_NBA_MCP_SYNTHESIS_TEST.env
echo "https://hooks.slack.com/services/TEST/TEST/TEST" > SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST.env
echo "mock_linear_api_key_for_testing" > LINEAR_API_KEY_NBA_MCP_SYNTHESIS_TEST.env

# Set proper permissions
chmod 600 *.env
```

### Step 3: Create Global Secrets

```bash
# Create global secrets directory
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.production
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.development
mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.test

# Set proper permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.production
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.development
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.test

# Create global secrets (these can be shared across projects)
cd /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_global/.env.global.production

# Global Slack webhook (if different from project-specific)
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/SLACK_WEBHOOK_URL SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
chmod 600 SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW.env

# Global Linear API key (if different from project-specific)
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_API_KEY LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
chmod 600 LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_WORKFLOW.env

# Global Linear Team ID
cp /Users/ryanranft/nba-mcp-synthesis/.env.workflow/LINEAR_TEAM_ID LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
chmod 600 LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
```

### Step 4: Test New System

```bash
# Test the new enhanced loader
cd /Users/ryanranft/nba-mcp-synthesis
python3 load_env_nba_mcp_synthesis_workflow.py

# Test the hierarchical loader
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production

# Test shell loader
source /Users/ryanranft/load_secrets_universal.sh
```

## Code Updates

### Step 1: Update Import Statements

#### Old Code:
```python
from mcp_server.secrets_manager import SecretsManager
from mcp_server.config_manager import ConfigManager
```

#### New Code:
```python
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager
```

### Step 2: Update Initialization

#### Old Code:
```python
# Old secrets manager
secrets_manager = SecretsManager()
config_manager = ConfigManager()
```

#### New Code:
```python
# New unified managers
secrets_manager = UnifiedSecretsManager()
config_manager = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')
```

### Step 3: Update Environment Variable Access

#### Old Code:
```python
# Old short names
google_key = os.getenv('GOOGLE_API_KEY')
deepseek_key = os.getenv('DEEPSEEK_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
```

#### New Code:
```python
# New context-rich names (preferred)
google_key = os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
deepseek_key = os.getenv('DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
anthropic_key = os.getenv('ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')

# Old names still work (backward compatibility)
google_key = os.getenv('GOOGLE_API_KEY')  # Automatically resolves to full name
```

### Step 4: Update Entry Points

#### Old Code:
```python
# Old entry point
if __name__ == "__main__":
    main()
```

#### New Code:
```python
# New entry point with secrets loading
if __name__ == "__main__":
    # Load secrets first
    import subprocess
    subprocess.run([
        'python3', '/Users/ryanranft/load_env_hierarchical.py',
        '--project', 'nba-mcp-synthesis',
        '--context', 'production'
    ], check=True)

    # Initialize unified managers
    config_manager = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')

    main()
```

### Step 5: Update Configuration Access

#### Old Code:
```python
# Old configuration access
config = ConfigManager()
api_config = config.get_api_config()
google_key = api_config.get('google_api_key')
```

#### New Code:
```python
# New configuration access
config_manager = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')
api_config = config_manager.config.api_config
google_key = api_config.google_api_key
```

## Testing Migration

### Step 1: Unit Tests

```bash
# Run existing tests to ensure compatibility
cd /Users/ryanranft/nba-mcp-synthesis
python3 -m pytest tests/ -v

# Run new unified secrets manager tests
python3 -m pytest tests/test_unified_secrets_manager.py -v
```

### Step 2: Integration Tests

```bash
# Test secrets loading
python3 -c "
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
manager = UnifiedSecretsManager()
secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
print(f'Loaded {len(secrets)} secrets')
for key in sorted(secrets.keys()):
    print(f'  {key}: {\"*\" * 8}')
"

# Test configuration loading
python3 -c "
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager
config = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')
print(f'API Config: {config.config.api_config}')
print(f'Workflow Config: {config.config.workflow_config}')
"
```

### Step 3: End-to-End Tests

```bash
# Test complete workflow
python3 scripts/automated_workflow.py --project nba-mcp-synthesis --context production

# Test analyzer
python3 scripts/resilient_book_analyzer.py --project nba-mcp-synthesis --context production

# Test MCP server
python3 test_mcp_tools.py
```

### Step 4: Health Checks

```bash
# Run health checks
python3 -c "
from load_env_nba_mcp_synthesis_workflow import HealthChecker, load_workflow_secrets
secrets = load_workflow_secrets()
health_checker = HealthChecker(secrets)
summary = health_checker.get_health_summary()
print(f'Health Status: {summary[\"overall_health\"]}')
print(f'Issues: {summary[\"issues\"]}')
"
```

## Rollback Procedures

### Step 1: Stop New System

```bash
# Stop any running processes using new system
pkill -f "load_env_hierarchical.py"
pkill -f "unified_secrets_manager"
```

### Step 2: Restore Old System

```bash
# Restore old .env.workflow file
cp /Users/ryanranft/Desktop/++/backups/$(date +%Y-%m-%d)/.env.workflow/* /Users/ryanranft/nba-mcp-synthesis/.env.workflow/

# Restore old secrets manager
git checkout HEAD~1 -- mcp_server/secrets_manager.py
git checkout HEAD~1 -- mcp_server/config_manager.py
```

### Step 3: Revert Code Changes

```bash
# Revert to old code
git checkout HEAD~1 -- scripts/automated_workflow.py
git checkout HEAD~1 -- scripts/resilient_book_analyzer.py
git checkout HEAD~1 -- mcp_server/server.py
```

### Step 4: Test Rollback

```bash
# Test old system
cd /Users/ryanranft/nba-mcp-synthesis
python3 -c "
from mcp_server.secrets_manager import SecretsManager
manager = SecretsManager()
print('Old system restored successfully')
"
```

## Post-Migration Validation

### Step 1: Verify All Secrets Loaded

```bash
# Check all secrets are loaded
python3 -c "
import os
required_secrets = [
    'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW',
    'LINEAR_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'
]

missing = []
for secret in required_secrets:
    if not os.getenv(secret):
        missing.append(secret)

if missing:
    print(f'Missing secrets: {missing}')
else:
    print('All required secrets loaded successfully')
"
```

### Step 2: Verify Backward Compatibility

```bash
# Test backward compatibility
python3 -c "
import os
old_names = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY']
for name in old_names:
    value = os.getenv(name)
    if value:
        print(f'{name}: OK')
    else:
        print(f'{name}: MISSING')
"
```

### Step 3: Verify Health Checks

```bash
# Run comprehensive health checks
python3 load_env_nba_mcp_synthesis_workflow.py
```

### Step 4: Verify Slack Notifications

```bash
# Check Slack notifications are working
# Look for notifications in your Slack channel
```

### Step 5: Verify Logging

```bash
# Check logs
tail -f /tmp/nba_mcp_synthesis_workflow.log
```

## Common Issues

### Issue 1: Permission Denied

**Error:**
```
❌ Error loading: Permission denied
```

**Solution:**
```bash
# Fix permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/*.env
```

### Issue 2: Invalid API Key Format

**Error:**
```
⚠️ Validation warnings:
   - Invalid Google API key format: GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
```

**Solution:**
```bash
# Check and fix API key format
cat /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Google API keys should start with 'AIza' and be at least 30 characters
# Update with correct key if needed
```

### Issue 3: Missing Environment Variables

**Error:**
```
❌ Missing critical variables: ['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']
```

**Solution:**
```bash
# Check if file exists
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Create missing file
echo "your_google_api_key_here" > /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

### Issue 4: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'mcp_server.unified_secrets_manager'
```

**Solution:**
```bash
# Ensure new files are in place
ls -la mcp_server/unified_secrets_manager.py
ls -la mcp_server/unified_configuration_manager.py

# If missing, they should have been created during implementation
# Check if they exist and are properly installed
```

### Issue 5: Context Detection Issues

**Error:**
```
❌ Unable to detect context
```

**Solution:**
```bash
# Set context explicitly
export NBA_MCP_CONTEXT=production
export PROJECT_NAME=nba-mcp-synthesis
export SPORT_NAME=NBA

# Or use command line arguments
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production
```

## Migration Checklist

- [ ] Backup current system
- [ ] Create new directory structure
- [ ] Migrate production secrets
- [ ] Migrate development secrets
- [ ] Migrate test secrets
- [ ] Create global secrets
- [ ] Test new system
- [ ] Update code imports
- [ ] Update initialization code
- [ ] Update environment variable access
- [ ] Update entry points
- [ ] Update configuration access
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Run end-to-end tests
- [ ] Run health checks
- [ ] Verify all secrets loaded
- [ ] Verify backward compatibility
- [ ] Verify health checks
- [ ] Verify Slack notifications
- [ ] Verify logging
- [ ] Document any issues
- [ ] Update team documentation

## Support

If you encounter issues during migration:

1. **Check Logs**: Review log files in `/tmp/`
2. **Run Health Checks**: Use the built-in health check commands
3. **Validate Configuration**: Use the naming convention validator
4. **Test Connectivity**: Use the API connectivity tests
5. **Check Permissions**: Verify file and directory permissions
6. **Rollback if Needed**: Use the rollback procedures above

## Conclusion

This migration guide provides comprehensive steps for transitioning from the old secrets management system to the new unified, hierarchical system. The new system offers improved security, validation, monitoring, and scalability while maintaining backward compatibility.

After successful migration, you'll have:
- Context-rich naming conventions
- Hierarchical secret loading
- Comprehensive validation and health checks
- Slack integration for monitoring
- Enhanced security features
- Docker and Kubernetes integration
- Comprehensive logging and audit trails

For additional support, refer to the [Secrets Management Guide](SECRETS_MANAGEMENT_GUIDE.md) and [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md).

