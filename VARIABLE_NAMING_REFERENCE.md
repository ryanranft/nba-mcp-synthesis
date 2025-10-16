# Variable Naming Reference Guide

## Overview

This document provides a complete reference for the hierarchical environment variable naming convention used in the NBA MCP Synthesis system. The new system provides context-aware loading with backward compatibility.

## Naming Convention

The new naming convention follows this pattern:
```
SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT
```

### Components

- **SERVICE**: The service provider (GOOGLE, ANTHROPIC, OPENAI, DEEPSEEK, AWS, RDS, S3, GLUE, SLACK, LINEAR, NBA, SPORTSDATA, TIMEZONE)
- **RESOURCE_TYPE**: The type of resource (API_KEY, SECRET_KEY, ACCESS_KEY, PASSWORD, TOKEN, WEBHOOK_URL, HOST, PORT, DATABASE, BUCKET, USERNAME, REGION, TIMEZONE)
- **PROJECT**: The project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
- **CONTEXT**: The environment context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

## Complete Variable Mapping

### AI Model API Keys

| Service | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|---------|----------|---------------------|------------------------|-----------------|
| Google | `GOOGLE_API_KEY` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_TEST` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `OPENAI_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `OPENAI_API_KEY_NBA_MCP_SYNTHESIS_TEST` |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_TEST` |

### AI Model Configuration

| Service | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|---------|----------|---------------------|------------------------|-----------------|
| Google | `GOOGLE_MODEL` | `GOOGLE_MODEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `GOOGLE_MODEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `GOOGLE_MODEL_NBA_MCP_SYNTHESIS_TEST` |
| Anthropic | `CLAUDE_MODEL` | `CLAUDE_MODEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `CLAUDE_MODEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `CLAUDE_MODEL_NBA_MCP_SYNTHESIS_TEST` |
| OpenAI | `OPENAI_MODEL` | `OPENAI_MODEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `OPENAI_MODEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `OPENAI_MODEL_NBA_MCP_SYNTHESIS_TEST` |
| DeepSeek | `DEEPSEEK_MODEL` | `DEEPSEEK_MODEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `DEEPSEEK_MODEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `DEEPSEEK_MODEL_NBA_MCP_SYNTHESIS_TEST` |

### AWS Credentials

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Access Key | `AWS_ACCESS_KEY_ID` | `AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_WORKFLOW` | `AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_TEST` |
| Secret Key | `AWS_SECRET_ACCESS_KEY` | `AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_WORKFLOW` | `AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_TEST` |
| Region | `AWS_REGION` | `AWS_REGION_NBA_MCP_SYNTHESIS_WORKFLOW` | `AWS_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `AWS_REGION_NBA_MCP_SYNTHESIS_TEST` |

### RDS Database Configuration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Host | `RDS_HOST` | `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `RDS_HOST_NBA_MCP_SYNTHESIS_TEST` |
| Port | `RDS_PORT` | `RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_PORT_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `RDS_PORT_NBA_MCP_SYNTHESIS_TEST` |
| Database | `RDS_DATABASE` | `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `RDS_DATABASE_NBA_MCP_SYNTHESIS_TEST` |
| Username | `RDS_USERNAME` | `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `RDS_USERNAME_NBA_MCP_SYNTHESIS_TEST` |
| Password | `RDS_PASSWORD` | `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW` | `RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `RDS_PASSWORD_NBA_MCP_SYNTHESIS_TEST` |

### S3 Storage Configuration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Bucket | `S3_BUCKET` | `S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW` | `S3_BUCKET_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `S3_BUCKET_NBA_MCP_SYNTHESIS_TEST` |
| Region | `S3_REGION` | `S3_REGION_NBA_MCP_SYNTHESIS_WORKFLOW` | `S3_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `S3_REGION_NBA_MCP_SYNTHESIS_TEST` |
| Books Bucket | `S3_BOOKS_BUCKET` | `S3_BOOKS_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW` | `S3_BOOKS_BUCKET_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `S3_BOOKS_BUCKET_NBA_MCP_SYNTHESIS_TEST` |
| Books Region | `S3_BOOKS_REGION` | `S3_BOOKS_REGION_NBA_MCP_SYNTHESIS_WORKFLOW` | `S3_BOOKS_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `S3_BOOKS_REGION_NBA_MCP_SYNTHESIS_TEST` |

### Glue Data Catalog Configuration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Database | `GLUE_DATABASE` | `GLUE_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW` | `GLUE_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `GLUE_DATABASE_NBA_MCP_SYNTHESIS_TEST` |
| Region | `GLUE_REGION` | `GLUE_REGION_NBA_MCP_SYNTHESIS_WORKFLOW` | `GLUE_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `GLUE_REGION_NBA_MCP_SYNTHESIS_TEST` |

### Slack Integration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Webhook URL | `SLACK_WEBHOOK_URL` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST` |
| Channel | `SLACK_CHANNEL` | `SLACK_CHANNEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `SLACK_CHANNEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `SLACK_CHANNEL_NBA_MCP_SYNTHESIS_TEST` |

### Ollama Configuration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| Host | `OLLAMA_HOST` | `OLLAMA_HOST_NBA_MCP_SYNTHESIS_WORKFLOW` | `OLLAMA_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `OLLAMA_HOST_NBA_MCP_SYNTHESIS_TEST` |
| Model | `OLLAMA_MODEL` | `OLLAMA_MODEL_NBA_MCP_SYNTHESIS_WORKFLOW` | `OLLAMA_MODEL_NBA_MCP_SYNTHESIS_DEVELOPMENT` | `OLLAMA_MODEL_NBA_MCP_SYNTHESIS_TEST` |

### Global Configuration

| Resource | Old Name | New Name (WORKFLOW) | New Name (DEVELOPMENT) | New Name (TEST) |
|----------|----------|---------------------|------------------------|-----------------|
| NBA API Key | `NBA_API_KEY` | `NBA_API_KEY_GLOBAL_WORKFLOW` | `NBA_API_KEY_GLOBAL_DEVELOPMENT` | `NBA_API_KEY_GLOBAL_TEST` |
| SportsData API Key | `SPORTSDATA_API_KEY` | `SPORTSDATA_API_KEY_GLOBAL_WORKFLOW` | `SPORTSDATA_API_KEY_GLOBAL_DEVELOPMENT` | `SPORTSDATA_API_KEY_GLOBAL_TEST` |
| Timezone | `TIMEZONE` | `TIMEZONE_GLOBAL_WORKFLOW` | `TIMEZONE_GLOBAL_DEVELOPMENT` | `TIMEZONE_GLOBAL_TEST` |

## Fallback Behavior

The system implements a hierarchical fallback mechanism:

1. **Primary**: Try the exact context requested (e.g., `WORKFLOW`)
2. **Secondary**: Try other contexts in order of preference:
   - `WORKFLOW` (production-like)
   - `DEVELOPMENT` (development environment)
   - `TEST` (testing environment)
   - `PRODUCTION` (production environment)
3. **Tertiary**: Fall back to the old naming convention

### Example Fallback Chain

For `GOOGLE_API_KEY` with context `DEVELOPMENT`:

1. `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT`
2. `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW`
3. `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST`
4. `GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_PRODUCTION`
5. `GOOGLE_API_KEY` (old naming convention)

## Usage Examples

### Programmatic Access

```python
from mcp_server.env_helper import get_hierarchical_env, get_api_key

# Get API key with hierarchical fallback
api_key = get_api_key("GOOGLE", "NBA_MCP_SYNTHESIS", "WORKFLOW")

# Get any environment variable with fallback
rds_host = get_hierarchical_env("RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW")

# Get with default value
port = get_hierarchical_env_int("RDS_PORT", 5432, "NBA_MCP_SYNTHESIS", "WORKFLOW")
```

### Manual Access

```bash
# Load secrets using the hierarchical loader
python3 /Users/ryanranft/load_env_hierarchical.py

# Or source the loader
source /Users/ryanranft/load_env_hierarchical.py
```

### Context-Specific Configuration

```bash
# Development environment
export GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT=dev-key-here
export RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT=dev-rds-host-here

# Test environment
export GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST=test-key-here
export RDS_HOST_NBA_MCP_SYNTHESIS_TEST=test-rds-host-here

# Production environment
export GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_PRODUCTION=prod-key-here
export RDS_HOST_NBA_MCP_SYNTHESIS_PRODUCTION=prod-rds-host-here
```

## Migration Guide

### For New Deployments

1. Use the new naming convention for all environment variables
2. Set up context-specific configurations as needed
3. Use the `mcp_server/env_helper.py` for programmatic access

### For Existing Deployments

1. Keep existing environment variables (backward compatibility)
2. Gradually migrate to new naming convention
3. Test with both old and new variables during transition
4. Remove old variables once migration is complete

### For Development

1. Use `DEVELOPMENT` context for local development
2. Use `TEST` context for testing
3. Use `WORKFLOW` context for production-like environments
4. Use `PRODUCTION` context for actual production

## Validation

The system includes validation to ensure proper naming conventions:

- **Format validation**: Ensures variables follow the `SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT` pattern
- **Service validation**: Validates that SERVICE is recognized
- **Resource type validation**: Validates that RESOURCE_TYPE is recognized
- **Project validation**: Validates that PROJECT is recognized
- **Context validation**: Validates that CONTEXT is recognized

## Security Considerations

1. **File permissions**: All secret files have 600 permissions, directories have 700
2. **Git exclusion**: Secret files are excluded from version control
3. **Context isolation**: Different contexts can have different security levels
4. **Audit logging**: All secret access is logged for security auditing

## Troubleshooting

### Common Issues

1. **"Invalid naming convention" warnings**: Check that variable names follow the exact pattern
2. **Secrets not loading**: Verify file permissions and directory structure
3. **Fallback not working**: Ensure old naming convention variables exist
4. **Context mismatch**: Verify the correct context is being used

### Debug Commands

```bash
# Check loaded environment variables
python3 -c "import os; [print(f'{k}={v}') for k, v in sorted(os.environ.items()) if 'NBA_MCP_SYNTHESIS' in k]"

# Test hierarchical loading
python3 mcp_server/env_helper.py

# Validate secrets health
python3 mcp_server/secrets_health_monitor.py --once
```

## Support

For questions or issues with the hierarchical secrets management system:

1. Check this reference guide
2. Review the `mcp_server/env_helper.py` source code
3. Run the health monitor for diagnostics
4. Check the unified secrets manager logs

