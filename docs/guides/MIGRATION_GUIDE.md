# Migration Guide: Old Configuration Managers → Unified System

## Overview

This guide helps you migrate from the deprecated configuration managers to the new unified secrets and configuration management system.

## Deprecated Components

The following components are deprecated and will be removed in version 2.0.0:

- `mcp_server.config_manager.ConfigManager`
- `mcp_server.configuration_manager.ConfigurationManager`
- `mcp_server.secrets_manager.SecretsManager`

## New Unified Components

Replace the deprecated components with:

- `mcp_server.unified_configuration_manager.UnifiedConfigurationManager`
- `mcp_server.unified_secrets_manager.UnifiedSecretsManager`
- `/Users/ryanranft/load_env_hierarchical.py` (for loading secrets)

## Migration Steps

### 1. Load Secrets First

**Before (Old Way):**
```python
from mcp_server.secrets_manager import SecretsManager

# Secrets loaded automatically when SecretsManager is instantiated
secrets = SecretsManager()
```

**After (New Way):**
```python
# Load secrets using hierarchical loader
import subprocess
import sys

# Load secrets for nba-mcp-synthesis project in production context
result = subprocess.run([
    sys.executable,
    "/Users/ryanranft/load_env_hierarchical.py",
    "nba-mcp-synthesis", "NBA", "production"
], capture_output=True, text=True)

if result.returncode != 0:
    raise RuntimeError(f"Failed to load secrets: {result.stderr}")

# Now secrets are available as environment variables
```

### 2. Replace Configuration Managers

**Before (Old Way):**
```python
from mcp_server.config_manager import ConfigManager
from mcp_server.configuration_manager import ConfigurationManager

# Old config manager
config = ConfigManager("production")

# Old configuration manager
config_mgr = ConfigurationManager("production", "config")
```

**After (New Way):**
```python
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

# New unified configuration manager
config = UnifiedConfigurationManager("nba-mcp-synthesis", "production")
```

### 3. Update Environment Variable Names

**Before (Old Way):**
```python
# Old naming convention
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

**After (New Way):**
```python
# New context-rich naming convention
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW")
DB_PASSWORD = os.getenv("DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW")
```

### 4. Update Secret Storage

**Before (Old Way):**
- Secrets stored in AWS Secrets Manager
- Single `.env.workflow` file
- Manual secret management

**After (New Way):**
- Secrets stored in `/Users/ryanranft/Desktop/++/big_cat_bets_assets/` hierarchy
- Individual `.env` files per secret
- Context-specific directories (production, development, test)
- Automatic context detection

## Directory Structure Changes

### Old Structure
```
/Users/ryanranft/nba-mcp-synthesis/
├── .env.workflow
└── config/
    ├── base.json
    └── production.json
```

### New Structure
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/
└── sports_assets/
    └── big_cat_bets_simulators/
        └── NBA/
            └── nba-mcp-synthesis/
                ├── .env.nba_mcp_synthesis.production/
                │   ├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
                │   ├── ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
                │   └── ...
                ├── .env.nba_mcp_synthesis.development/
                └── .env.nba_mcp_synthesis.test/
```

## Configuration Access Changes

### Database Configuration

**Before:**
```python
from mcp_server.config_manager import ConfigManager
config = ConfigManager("production")
db_config = config.get_database_config()
```

**After:**
```python
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager
config = UnifiedConfigurationManager("nba-mcp-synthesis", "production")
db_config = config.database_config
```

### API Configuration

**Before:**
```python
api_key = os.getenv("GOOGLE_API_KEY")
```

**After:**
```python
api_key = os.getenv("GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW")
# Or access through config object
api_key = config.api_config.google_api_key
```

### Workflow Configuration

**Before:**
```python
notifications_enabled = config.get("workflow.enable_notifications", True)
```

**After:**
```python
notifications_enabled = config.workflow_config.enable_notifications
```

## Context Mapping

The new system uses context-rich naming. Here's the mapping:

| Old Context | New Context Key | Example Variable |
|-------------|-----------------|------------------|
| `production` | `WORKFLOW` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` |
| `development` | `DEVELOPMENT` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` |
| `test` | `TEST` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST` |

## Shell Script Changes

### Loading Secrets in Shell

**Before:**
```bash
# Manual environment loading
source /Users/ryanranft/nba-mcp-synthesis/.env.workflow
```

**After:**
```bash
# Use universal loader
source /Users/ryanranft/load_secrets_universal.sh
load_secrets "nba-mcp-synthesis" "NBA" "production"
```

## Testing Changes

### Test Configuration

**Before:**
```python
def test_with_config():
    config = ConfigManager("test")
    # test code
```

**After:**
```python
def test_with_config():
    # Load test secrets first
    subprocess.run([
        sys.executable,
        "/Users/ryanranft/load_env_hierarchical.py",
        "nba-mcp-synthesis", "NBA", "test"
    ])

    config = UnifiedConfigurationManager("nba-mcp-synthesis", "test")
    # test code
```

## Common Issues and Solutions

### Issue: "Secret not found"
**Solution:** Ensure secrets are loaded using the hierarchical loader before accessing them.

### Issue: "Invalid naming convention"
**Solution:** Use the context-rich naming convention: `SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT`

### Issue: "Configuration not loading"
**Solution:** Check that the project and context parameters match your directory structure.

## Validation

After migration, validate your setup:

```python
# Test secrets loading
from mcp_server.unified_secrets_manager import get_secrets_manager
secrets_manager = get_secrets_manager()
secrets = secrets_manager.get_all_secrets()
print(f"Loaded {len(secrets)} secrets")

# Test configuration loading
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager
config = UnifiedConfigurationManager("nba-mcp-synthesis", "production")
print(f"API keys configured: {bool(config.api_config.google_api_key)}")
```

## Support

For questions or issues during migration:

1. Check the deprecation warnings in your logs
2. Review `/centralized-secrets-management.plan.md`
3. Test with the validation scripts above
4. Ensure all environment variables follow the new naming convention

## Timeline

- **Now**: Deprecation warnings active
- **Version 2.0.0**: Deprecated components removed
- **Recommendation**: Migrate as soon as possible to avoid breaking changes


