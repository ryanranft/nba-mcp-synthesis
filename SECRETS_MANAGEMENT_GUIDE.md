# NBA MCP Synthesis - Secrets Management Guide

## Overview

This project uses a **hierarchical secrets management system** that provides secure, organized, and context-aware credential storage. The system prevents accidental commits of secrets while providing seamless integration across development, testing, and production environments.

## 🏗️ Architecture

### Directory Structure

```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/
├── sports_assets/
│   └── big_cat_bets_simulators/
│       └── NBA/
│           ├── nba-mcp-synthesis/
│           │   ├── .env.nba_mcp_synthesis.production/
│           │   │   ├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
│           │   │   ├── ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
│           │   │   └── ...
│           │   ├── .env.nba_mcp_synthesis.development/
│           │   │   ├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
│           │   │   ├── ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
│           │   │   └── ...
│           │   └── .env.nba_mcp_synthesis.test/
│           ├── nba-simulator-aws/
│           │   ├── .env.nba_simulator_aws.production/
│           │   ├── .env.nba_simulator_aws.development/
│           │   └── .env.nba_simulator_aws.test/
│           └── nba_mcp_synthesis_global/
│               ├── .env.nba_mcp_synthesis_global.production/
│               ├── .env.nba_mcp_synthesis_global.development/
│               └── .env.nba_mcp_synthesis_global.test/
```

### Key Components

1. **Unified Secrets Manager** (`mcp_server/unified_secrets_manager.py`)
   - Core logic for hierarchical loading
   - Context detection and validation
   - AWS Secrets Manager fallback
   - Naming convention enforcement

2. **Hierarchical Loader** (`/Users/ryanranft/load_env_hierarchical.py`)
   - Universal loader for all projects
   - Automatic context detection
   - Environment variable injection

3. **Health Monitor** (`mcp_server/secrets_health_monitor.py`)
   - Real-time secret validation
   - API connectivity checks
   - Continuous monitoring with alerting

4. **Docker Integration** (`docker/load_secrets_docker.py`)
   - Containerized secret loading
   - Volume mount support
   - Environment variable injection

## 🔧 Usage

### Basic Usage

```bash
# Load secrets for current project
source /Users/ryanranft/load_env_hierarchical.py

# Or use Python directly
python3 /Users/ryanranft/load_env_hierarchical.py

# Verify secrets are loaded
python3 mcp_server/secrets_health_monitor.py --once
```

### Advanced Usage

```bash
# Load specific project and context
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-simulator-aws --context development

# Run health monitoring continuously
python3 mcp_server/secrets_health_monitor.py --interval 300

# Test secret loading for all projects
python3 scripts/test_new_projects_secrets.py
```

### Docker Usage

```bash
# Build with secrets support
docker build -t nba-mcp-synthesis .

# Run with secrets mounted
docker run -v /Users/ryanranft/Desktop/++:/secrets:ro \
  -e PROJECT_NAME=nba-mcp-synthesis \
  -e SPORT_NAME=NBA \
  -e NBA_MCP_CONTEXT=WORKFLOW \
  nba-mcp-synthesis
```

## 📋 Naming Convention

### Format
`SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT`

### Examples
- `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
- `AWS_ACCESS_KEY_ID_NBA_SIMULATOR_AWS_DEVELOPMENT`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT`
- `TIMEZONE_GLOBAL_WORKFLOW`

### Components
- **SERVICE**: `GOOGLE`, `ANTHROPIC`, `AWS`, `RDS`, `S3`, `NBA`, `SPORTSDATA`
- **RESOURCE_TYPE**: `API_KEY`, `SECRET_KEY`, `ACCESS_KEY`, `PASSWORD`, `TOKEN`, `HOST`, `PORT`, `DATABASE`, `BUCKET`, `USERNAME`, `REGION`, `TIMEZONE`
- **PROJECT**: `NBA_MCP_SYNTHESIS`, `NBA_SIMULATOR_AWS`, `NBA_MCP_SYNTHESIS_GLOBAL`
- **CONTEXT**: `WORKFLOW`, `DEVELOPMENT`, `TEST`, `PRODUCTION`

## 🔒 Security Features

### File Permissions
- **Secret Files**: `600` (rw-------) - Owner read/write only
- **Secret Directories**: `700` (rwx------) - Owner read/write/execute only
- **Base Directory**: `755` (rwxr-xr-x) - Standard directory permissions

### Audit Script
```bash
# Audit permissions
scripts/audit_secret_permissions.sh

# Fix permissions automatically
scripts/audit_secret_permissions.sh fix
```

### Validation
- **Naming Convention**: Enforced for all secrets
- **Secret Strength**: Validates API key formats
- **Collision Detection**: Warns about duplicate variable names
- **Health Checks**: Continuous API connectivity validation

## 🚀 Migration Guide

### From Old System

If you're migrating from the old `.env.workflow` and `.env` files:

```bash
# Run migration script
scripts/migrate_to_hierarchical_structure.sh

# Verify migration
scripts/enforce_naming_convention.py
```

### Manual Migration

1. **Create directory structure**:
   ```bash
   mkdir -p /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production
   ```

2. **Create individual secret files**:
   ```bash
   echo "your-api-key" > /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
   ```

3. **Set secure permissions**:
   ```bash
   chmod 600 *.env
   chmod 700 .env.*/
   ```

## 🔍 Monitoring & Health Checks

### Health Monitor Features
- **Real-time Validation**: Checks secret format and presence
- **API Connectivity**: Tests actual API endpoints
- **Metrics Collection**: Tracks health scores and trends
- **Alerting**: Configurable notifications for failures

### Usage
```bash
# One-time health check
python3 mcp_server/secrets_health_monitor.py --once

# Continuous monitoring
python3 mcp_server/secrets_health_monitor.py --interval 300

# With custom project/context
python3 mcp_server/secrets_health_monitor.py --project nba-simulator-aws --context development
```

### Systemd Service
```bash
# Setup continuous monitoring
scripts/setup-monitoring.sh

# Check service status
sudo systemctl status nba-secrets-monitor.service
```

## 🐳 Docker Integration

### Dockerfile Updates
The Dockerfile has been updated to use the unified secrets manager:

```dockerfile
# Copy secrets loader
COPY docker/load_secrets_docker.py /app/load_secrets_docker.py

# Set entrypoint
ENTRYPOINT ["python3", "/app/load_secrets_docker.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  nba-mcp-synthesis:
    build: .
    volumes:
      - /Users/ryanranft/Desktop/++:/secrets:ro
    environment:
      - PROJECT_NAME=nba-mcp-synthesis
      - SPORT_NAME=NBA
      - NBA_MCP_CONTEXT=WORKFLOW
    command: python3 -m mcp_server.fastmcp_server
```

## 🧪 Testing

### Test Scripts
```bash
# Test secret loading for all projects
python3 scripts/test_new_projects_secrets.py

# Test health monitoring
python3 mcp_server/secrets_health_monitor.py --once

# Test Docker integration
docker-compose -f docker-compose.secrets.yml up --build
```

### Validation
- **Naming Convention**: `scripts/enforce_naming_convention.py`
- **Permissions**: `scripts/audit_secret_permissions.sh`
- **Health Checks**: `mcp_server/secrets_health_monitor.py`

## 📚 API Reference

### UnifiedSecretsManager

```python
from mcp_server.unified_secrets_manager import UnifiedSecretsManager

# Initialize manager
manager = UnifiedSecretsManager()

# Load secrets (instance method - returns dict)
secrets = manager.load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "WORKFLOW")

# Load secrets (standalone function - sets os.environ)
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
success = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "WORKFLOW")
```

### Health Monitor

```python
from mcp_server.secrets_health_monitor import SecretsHealthMonitor

# Initialize monitor
monitor = SecretsHealthMonitor("nba-mcp-synthesis", "WORKFLOW")

# Run health checks
results = monitor.perform_health_checks()

# Get metrics
metrics = monitor.metrics_collector.get_metrics()
```

## 🚨 Troubleshooting

### Common Issues

1. **Secrets not loading**:
   ```bash
   # Check if secrets exist
   ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

   # Verify permissions
   scripts/audit_secret_permissions.sh
   ```

2. **Naming convention warnings**:
   ```bash
   # Check naming convention
   scripts/enforce_naming_convention.py
   ```

3. **Health monitor showing 0%**:
   ```bash
   # Check if secrets are loaded in current process
   python3 -c "import os; print('GOOGLE_API_KEY' in os.environ)"
   ```

### Debug Mode
```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
python3 mcp_server/secrets_health_monitor.py --once
```

## 📈 Best Practices

1. **Never commit secrets**: All secret files are in `.gitignore`
2. **Use context-appropriate secrets**: Development vs. production
3. **Regular health checks**: Monitor secret validity
4. **Secure permissions**: Always use 600/700 permissions
5. **Backup secrets**: Keep secure backups of production secrets
6. **Rotate secrets**: Regular rotation of API keys and passwords

## 🔄 Future Enhancements

- **AWS Secrets Manager Integration**: Automatic fallback for production
- **Secret Rotation**: Automated secret rotation workflows
- **Multi-User Support**: User-specific override directories
- **Visual Hierarchy Browser**: TUI for browsing secret hierarchy
- **Secret Templates**: Scaffolding for new projects

## 📞 Support

For issues or questions about the secrets management system:

1. Check the troubleshooting section above
2. Run health checks: `python3 mcp_server/secrets_health_monitor.py --once`
3. Review logs: `tail -f logs/secrets_health_monitor.log`
4. Check permissions: `scripts/audit_secret_permissions.sh`

---

**Last Updated**: October 15, 2025
**Version**: 1.0
**Status**: Production Ready ✅

