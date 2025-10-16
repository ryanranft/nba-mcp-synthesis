# Team Migration Guide: NBA MCP Synthesis Secrets Management

## 🎯 Overview

This guide helps team members migrate from the old secrets system to the new hierarchical secrets management system. The new system provides better security, organization, and context-aware loading.

## 📋 Pre-Migration Checklist

- [ ] Backup existing `.env.workflow` and `.env` files
- [ ] Review current secrets and their usage
- [ ] Understand the new naming convention
- [ ] Plan for development vs. production contexts

## 🔄 Migration Steps

### Step 1: Backup Current Secrets

```bash
# Create backup directory
mkdir -p ~/secrets_backup_$(date +%Y%m%d)

# Backup existing files
cp .env.workflow ~/secrets_backup_$(date +%Y%m%d)/
cp .env ~/secrets_backup_$(date +%Y%m%d)/
```

### Step 2: Run Automated Migration

```bash
# Run the migration script
scripts/migrate_to_hierarchical_structure.sh

# Verify migration was successful
scripts/enforce_naming_convention.py
```

### Step 3: Verify New System

```bash
# Test secret loading
python3 /Users/ryanranft/load_env_hierarchical.py

# Run health checks
python3 mcp_server/secrets_health_monitor.py --once

# Test all projects
python3 scripts/test_new_projects_secrets.py
```

### Step 4: Update Your Workflow

Replace old secret loading with new system:

**Before:**
```bash
# Old way
source .env.workflow
```

**After:**
```bash
# New way
source /Users/ryanranft/load_env_hierarchical.py
```

## 🔧 Configuration Changes

### Environment Variables

The new system uses context-rich naming. Here's how variables map:

| Old Name | New Name (Production) | New Name (Development) |
|----------|---------------------|----------------------|
| `GOOGLE_API_KEY` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` |
| `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` |
| `RDS_HOST` | `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT` |

### Code Changes

Update your code to use the new environment variables:

**Before:**
```python
import os
api_key = os.getenv('GOOGLE_API_KEY')
```

**After:**
```python
import os
api_key = os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
```

## 🐳 Docker Changes

### Dockerfile Updates

The Dockerfile now uses the unified secrets manager:

```dockerfile
# Old entrypoint
ENTRYPOINT ["python3", "-m", "mcp_server.fastmcp_server"]

# New entrypoint (automatically loads secrets)
ENTRYPOINT ["python3", "/app/load_secrets_docker.py"]
```

### Docker Compose Updates

```yaml
# Old compose
services:
  nba-mcp-synthesis:
    build: .
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

# New compose
services:
  nba-mcp-synthesis:
    build: .
    volumes:
      - /Users/ryanranft/Desktop/++:/secrets:ro
    environment:
      - PROJECT_NAME=nba-mcp-synthesis
      - SPORT_NAME=NBA
      - NBA_MCP_CONTEXT=WORKFLOW
```

## 🔍 Monitoring Changes

### Health Monitoring

The new system includes continuous health monitoring:

```bash
# Start monitoring service
scripts/setup-monitoring.sh

# Check status
sudo systemctl status nba-secrets-monitor.service

# View logs
sudo journalctl -u nba-secrets-monitor.service -f
```

### Health Checks

```bash
# One-time check
python3 mcp_server/secrets_health_monitor.py --once

# Continuous monitoring
python3 mcp_server/secrets_health_monitor.py --interval 300
```

## 🚨 Common Issues & Solutions

### Issue 1: Secrets Not Loading

**Symptoms:**
- Environment variables not set
- API calls failing
- Health monitor showing 0%

**Solutions:**
```bash
# Check if secrets exist
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

# Verify permissions
scripts/audit_secret_permissions.sh

# Test loading manually
python3 /Users/ryanranft/load_env_hierarchical.py
```

### Issue 2: Naming Convention Warnings

**Symptoms:**
- "Invalid naming convention" warnings
- Secrets not recognized

**Solutions:**
```bash
# Check naming convention
scripts/enforce_naming_convention.py

# Fix naming issues
scripts/migrate_to_hierarchical_structure.sh
```

### Issue 3: Permission Errors

**Symptoms:**
- "Permission denied" errors
- Cannot read secret files

**Solutions:**
```bash
# Fix permissions
scripts/audit_secret_permissions.sh fix

# Verify fix
scripts/audit_secret_permissions.sh
```

## 📚 New Features

### Context-Aware Loading

The new system automatically detects context:

```bash
# Automatically loads based on current directory and environment
source /Users/ryanranft/load_env_hierarchical.py

# Or specify explicitly
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-simulator-aws --context development
```

### Health Monitoring

Continuous monitoring with alerting:

```bash
# Start monitoring
python3 mcp_server/secrets_health_monitor.py --interval 300

# Check health status
python3 mcp_server/secrets_health_monitor.py --once
```

### Docker Integration

Seamless container deployment:

```bash
# Build with secrets support
docker build -t nba-mcp-synthesis .

# Run with secrets
docker run -v /Users/ryanranft/Desktop/++:/secrets:ro nba-mcp-synthesis
```

## 🔒 Security Improvements

### File Permissions

All secret files now have secure permissions:

- **Secret Files**: `600` (rw-------) - Owner read/write only
- **Secret Directories**: `700` (rwx------) - Owner read/write/execute only

### Audit Scripts

Regular security audits:

```bash
# Audit permissions
scripts/audit_secret_permissions.sh

# Enforce naming convention
scripts/enforce_naming_convention.py
```

## 📞 Support & Help

### Getting Help

1. **Check Documentation**: [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md)
2. **Run Health Checks**: `python3 mcp_server/secrets_health_monitor.py --once`
3. **Check Logs**: `tail -f logs/secrets_health_monitor.log`
4. **Audit System**: `scripts/audit_secret_permissions.sh`

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export MCP_LOG_LEVEL=DEBUG
python3 mcp_server/secrets_health_monitor.py --once
```

## ✅ Post-Migration Checklist

- [ ] All secrets migrated successfully
- [ ] Health monitor showing 100% health
- [ ] Docker containers working with new system
- [ ] All applications using new environment variables
- [ ] Monitoring service running
- [ ] Permissions secure (600/700)
- [ ] Backup of old secrets created
- [ ] Team members trained on new system

## 🎉 Benefits of New System

1. **Better Security**: Secure permissions, no accidental commits
2. **Context Awareness**: Automatic environment detection
3. **Health Monitoring**: Continuous validation and alerting
4. **Docker Integration**: Seamless container deployment
5. **Scalability**: Easy to add new projects and contexts
6. **Audit Trail**: Comprehensive logging and monitoring

---

**Migration Status**: ✅ Complete
**Last Updated**: October 15, 2025
**Support**: See [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md) for detailed documentation

