# NBA MCP Synthesis - API Documentation

## Overview

This document provides comprehensive API documentation for the NBA MCP Synthesis secrets management system, including all classes, methods, and their usage.

## Table of Contents

1. [Unified Secrets Manager](#unified-secrets-manager)
2. [Unified Configuration Manager](#unified-configuration-manager)
3. [Enhanced Loader Scripts](#enhanced-loader-scripts)
4. [Validation Classes](#validation-classes)
5. [Health Check Classes](#health-check-classes)
6. [Slack Integration](#slack-integration)
7. [Utility Functions](#utility-functions)
8. [Error Handling](#error-handling)
9. [Examples](#examples)

## Unified Secrets Manager

### Class: `UnifiedSecretsManager`

The core class for managing secrets with hierarchical loading, context detection, and AWS fallback.

#### Constructor

```python
UnifiedSecretsManager(
    base_path: str = "/Users/ryanranft/Desktop/++/big_cat_bets_assets",
    aws_region: str = "us-east-1",
    enable_caching: bool = True,
    cache_ttl: int = 300
)
```

**Parameters:**
- `base_path` (str): Base path for secrets directory structure
- `aws_region` (str): AWS region for Secrets Manager fallback
- `enable_caching` (bool): Enable caching for AWS secrets
- `cache_ttl` (int): Cache TTL in seconds

**Example:**
```python
from mcp_server.unified_secrets_manager import UnifiedSecretsManager

# Basic initialization
manager = UnifiedSecretsManager()

# Custom configuration
manager = UnifiedSecretsManager(
    base_path="/custom/secrets/path",
    aws_region="us-west-2",
    enable_caching=True,
    cache_ttl=600
)
```

#### Methods

##### `load_secrets_hierarchical(project: str, context: str) -> Dict[str, str]`

Load secrets hierarchically from the directory structure.

**Parameters:**
- `project` (str): Project name (e.g., 'nba-mcp-synthesis')
- `context` (str): Context name (e.g., 'production', 'development', 'test')

**Returns:**
- `Dict[str, str]`: Dictionary of loaded secrets

**Example:**
```python
secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
print(f"Loaded {len(secrets)} secrets")
```

##### `get_secret(key: str, project: str = None, context: str = None) -> Optional[str]`

Get a specific secret by key.

**Parameters:**
- `key` (str): Secret key name
- `project` (str, optional): Project name for context-specific lookup
- `context` (str, optional): Context name for context-specific lookup

**Returns:**
- `Optional[str]`: Secret value or None if not found

**Example:**
```python
# Get secret with full context
google_key = manager.get_secret('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')

# Get secret with project/context
google_key = manager.get_secret('GOOGLE_API_KEY', 'nba-mcp-synthesis', 'production')
```

##### `_detect_context() -> str`

Automatically detect the current context.

**Returns:**
- `str`: Detected context name

**Example:**
```python
context = manager._detect_context()
print(f"Detected context: {context}")
```

##### `_is_valid_naming_convention(key: str) -> bool`

Validate if a key follows the naming convention.

**Parameters:**
- `key` (str): Key name to validate

**Returns:**
- `bool`: True if valid naming convention

**Example:**
```python
is_valid = manager._is_valid_naming_convention('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
print(f"Valid naming: {is_valid}")
```

##### `_load_from_aws(secret_name: str) -> Optional[str]`

Load secret from AWS Secrets Manager.

**Parameters:**
- `secret_name` (str): AWS secret name

**Returns:**
- `Optional[str]`: Secret value or None if not found

**Example:**
```python
aws_secret = manager._load_from_aws('nba-mcp-synthesis/production/google-api-key')
```

##### `_create_aliases(secrets: Dict[str, str]) -> Dict[str, str]`

Create backward-compatible aliases for secrets.

**Parameters:**
- `secrets` (Dict[str, str]): Dictionary of secrets

**Returns:**
- `Dict[str, str]`: Dictionary with aliases added

**Example:**
```python
secrets_with_aliases = manager._create_aliases(secrets)
```

## Unified Configuration Manager

### Class: `UnifiedConfigurationManager`

Manages configuration with environment-specific settings and secret interpolation.

#### Constructor

```python
UnifiedConfigurationManager(
    project: str,
    context: str = "production",
    config_file: Optional[str] = None,
    enable_watching: bool = False
)
```

**Parameters:**
- `project` (str): Project name
- `context` (str): Context name
- `config_file` (str, optional): Path to configuration file
- `enable_watching` (bool): Enable file watching for dynamic updates

**Example:**
```python
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

# Basic initialization
config = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')

# With file watching
config = UnifiedConfigurationManager(
    'nba-mcp-synthesis',
    'production',
    enable_watching=True
)
```

#### Methods

##### `get_config() -> Dict[str, Any]`

Get the current configuration.

**Returns:**
- `Dict[str, Any]`: Current configuration

**Example:**
```python
config_dict = config.get_config()
print(f"API Config: {config_dict['api_config']}")
```

##### `update_config(new_config: Dict[str, Any]) -> None`

Update the configuration.

**Parameters:**
- `new_config` (Dict[str, Any]): New configuration values

**Example:**
```python
config.update_config({
    'api_config': {
        'google_api_key': 'new_key_here'
    }
})
```

##### `validate_config() -> bool`

Validate the current configuration.

**Returns:**
- `bool`: True if configuration is valid

**Example:**
```python
is_valid = config.validate_config()
if not is_valid:
    print("Configuration validation failed")
```

##### `_load_from_environment() -> Dict[str, Any]`

Load configuration from environment variables.

**Returns:**
- `Dict[str, Any]`: Configuration from environment

**Example:**
```python
env_config = config._load_from_environment()
```

## Enhanced Loader Scripts

### Workflow Loader

#### Function: `load_workflow_secrets() -> Dict[str, str]`

Load all secrets from the centralized workflow directory with enhanced validation.

**Returns:**
- `Dict[str, str]`: Dictionary of loaded environment variables

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import load_workflow_secrets

secrets = load_workflow_secrets()
print(f"Loaded {len(secrets)} secrets")
```

#### Function: `verify_critical_vars() -> bool`

Verify that critical variables are loaded with enhanced validation.

**Returns:**
- `bool`: True if all critical variables are loaded and valid

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import verify_critical_vars

if verify_critical_vars():
    print("All critical variables loaded")
else:
    print("Critical variables missing")
```

#### Function: `perform_health_checks(secrets: Dict[str, str]) -> Dict[str, Any]`

Perform comprehensive health checks on loaded secrets.

**Parameters:**
- `secrets` (Dict[str, str]): Dictionary of loaded secrets

**Returns:**
- `Dict[str, Any]`: Health check summary

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import perform_health_checks, load_workflow_secrets

secrets = load_workflow_secrets()
health_summary = perform_health_checks(secrets)
print(f"Health Status: {health_summary['overall_health']}")
```

#### Function: `send_slack_notifications(secrets: Dict[str, str], health_summary: Dict[str, Any], error: Optional[str] = None)`

Send Slack notifications about secrets loading status.

**Parameters:**
- `secrets` (Dict[str, str]): Dictionary of loaded secrets
- `health_summary` (Dict[str, Any]): Health check summary
- `error` (str, optional): Error message if any

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import send_slack_notifications, load_workflow_secrets, perform_health_checks

secrets = load_workflow_secrets()
health_summary = perform_health_checks(secrets)
send_slack_notifications(secrets, health_summary)
```

### Local Development Loader

#### Function: `load_local_secrets() -> Dict[str, str]`

Load all secrets from the centralized local directory with enhanced validation.

**Returns:**
- `Dict[str, str]`: Dictionary of loaded environment variables

**Example:**
```python
from load_env_nba_mcp_synthesis_local import load_local_secrets

secrets = load_local_secrets()
print(f"Loaded {len(secrets)} development secrets")
```

## Validation Classes

### Class: `SecretsValidator`

Validates secret formats and values.

#### Static Methods

##### `validate_api_key(key: str, service: str) -> bool`

Validate API key format based on service.

**Parameters:**
- `key` (str): API key to validate
- `service` (str): Service name (e.g., 'GOOGLE', 'OPENAI')

**Returns:**
- `bool`: True if valid format

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import SecretsValidator

is_valid = SecretsValidator.validate_api_key('your_google_api_key_here', 'GOOGLE')
print(f"Valid Google API key: {is_valid}")
```

##### `validate_webhook_url(url: str) -> bool`

Validate webhook URL format.

**Parameters:**
- `url` (str): Webhook URL to validate

**Returns:**
- `bool`: True if valid format

**Example:**
```python
is_valid = SecretsValidator.validate_webhook_url('https://hooks.slack.com/services/YOUR/WEBHOOK/URL')
print(f"Valid webhook URL: {is_valid}")
```

##### `validate_uuid(uuid_str: str) -> bool`

Validate UUID format.

**Parameters:**
- `uuid_str` (str): UUID string to validate

**Returns:**
- `bool`: True if valid format

**Example:**
```python
is_valid = SecretsValidator.validate_uuid('2b00e93f-f123-424d-9571-0095c6299714')
print(f"Valid UUID: {is_valid}")
```

## Health Check Classes

### Class: `HealthChecker`

Performs health checks on loaded secrets.

#### Constructor

```python
HealthChecker(secrets: Dict[str, str])
```

**Parameters:**
- `secrets` (Dict[str, str]): Dictionary of loaded secrets

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import HealthChecker, load_workflow_secrets

secrets = load_workflow_secrets()
health_checker = HealthChecker(secrets)
```

#### Methods

##### `check_api_connectivity() -> Dict[str, bool]`

Check API connectivity for loaded keys.

**Returns:**
- `Dict[str, bool]`: Dictionary of connectivity results

**Example:**
```python
connectivity = health_checker.check_api_connectivity()
print(f"Google API: {'OK' if connectivity.get('google_api') else 'FAILED'}")
```

##### `check_secret_strength() -> Dict[str, bool]`

Check secret strength and format.

**Returns:**
- `Dict[str, bool]`: Dictionary of strength check results

**Example:**
```python
strength = health_checker.check_secret_strength()
print(f"Secret strength: {strength}")
```

##### `get_health_summary() -> Dict[str, Any]`

Get comprehensive health summary.

**Returns:**
- `Dict[str, Any]`: Health summary with all checks

**Example:**
```python
summary = health_checker.get_health_summary()
print(f"Overall health: {summary['overall_health']}")
print(f"Issues: {summary['issues']}")
```

## Slack Integration

### Class: `SlackNotifier`

Handles Slack notifications for secrets loading.

#### Constructor

```python
SlackNotifier(webhook_url: Optional[str] = None)
```

**Parameters:**
- `webhook_url` (str, optional): Slack webhook URL

**Example:**
```python
from load_env_nba_mcp_synthesis_workflow import SlackNotifier

# Use default webhook from environment
notifier = SlackNotifier()

# Use custom webhook
notifier = SlackNotifier('https://hooks.slack.com/services/YOUR/WEBHOOK/URL')
```

#### Methods

##### `send_notification(message: str, level: str = 'info') -> bool`

Send notification to Slack.

**Parameters:**
- `message` (str): Message to send
- `level` (str): Notification level ('success', 'warning', 'error', 'info')

**Returns:**
- `bool`: True if sent successfully

**Example:**
```python
success = notifier.send_notification("Secrets loaded successfully", "success")
print(f"Notification sent: {success}")
```

##### `notify_secrets_loaded(count: int, health_summary: Dict[str, Any]) -> bool`

Notify about successful secrets loading.

**Parameters:**
- `count` (int): Number of secrets loaded
- `health_summary` (Dict[str, Any]): Health check summary

**Returns:**
- `bool`: True if sent successfully

**Example:**
```python
success = notifier.notify_secrets_loaded(15, health_summary)
```

##### `notify_secrets_error(error: str) -> bool`

Notify about secrets loading error.

**Parameters:**
- `error` (str): Error message

**Returns:**
- `bool`: True if sent successfully

**Example:**
```python
success = notifier.notify_secrets_error("Failed to load secrets")
```

## Utility Functions

### Hierarchical Loader

#### Function: `load_env_hierarchical()`

Universal hierarchical secrets loader with automatic context detection.

**Example:**
```python
# Command line usage
python3 /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production

# Programmatic usage
import subprocess
subprocess.run([
    'python3', '/Users/ryanranft/load_env_hierarchical.py',
    '--project', 'nba-mcp-synthesis',
    '--context', 'production'
], check=True)
```

### Shell Loaders

#### Function: `load_secrets_universal.sh`

Universal shell secrets loader.

**Example:**
```bash
# Source into current shell
source /Users/ryanranft/load_secrets_universal.sh

# Check loaded secrets
echo $GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
```

#### Function: `run_with_credentials.sh`

Run commands with loaded credentials.

**Example:**
```bash
# Run command with credentials
source /Users/ryanranft/run_with_credentials.sh nba-mcp-synthesis workflow
python3 main.py
```

## Error Handling

### Exception Classes

#### `SecretsManagerError`

Base exception for secrets manager errors.

```python
class SecretsManagerError(Exception):
    """Base exception for secrets manager errors"""
    pass
```

#### `ValidationError`

Exception for validation errors.

```python
class ValidationError(SecretsManagerError):
    """Exception for validation errors"""
    pass
```

#### `ConfigurationError`

Exception for configuration errors.

```python
class ConfigurationError(SecretsManagerError):
    """Exception for configuration errors"""
    pass
```

### Error Handling Examples

```python
from mcp_server.unified_secrets_manager import UnifiedSecretsManager, SecretsManagerError

try:
    manager = UnifiedSecretsManager()
    secrets = manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')
except SecretsManagerError as e:
    print(f"Secrets manager error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

### Basic Usage

```python
from mcp_server.unified_secrets_manager import UnifiedSecretsManager
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

# Initialize managers
secrets_manager = UnifiedSecretsManager()
config_manager = UnifiedConfigurationManager('nba-mcp-synthesis', 'production')

# Load secrets
secrets = secrets_manager.load_secrets_hierarchical('nba-mcp-synthesis', 'production')

# Get specific secret
google_key = secrets_manager.get_secret('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')

# Get configuration
config = config_manager.get_config()
api_config = config['api_config']
```

### Enhanced Loader Usage

```python
from load_env_nba_mcp_synthesis_workflow import (
    load_workflow_secrets,
    verify_critical_vars,
    perform_health_checks,
    send_slack_notifications
)

# Load secrets with validation
secrets = load_workflow_secrets()

# Verify critical variables
if verify_critical_vars():
    print("All critical variables loaded")

    # Perform health checks
    health_summary = perform_health_checks(secrets)

    # Send Slack notifications
    send_slack_notifications(secrets, health_summary)
else:
    print("Critical variables missing")
```

### Validation Usage

```python
from load_env_nba_mcp_synthesis_workflow import SecretsValidator

# Validate API keys
google_key = "your_google_api_key_here"
is_valid = SecretsValidator.validate_api_key(google_key, 'GOOGLE')
print(f"Google API key valid: {is_valid}")

# Validate webhook URL
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
is_valid = SecretsValidator.validate_webhook_url(webhook_url)
print(f"Webhook URL valid: {is_valid}")

# Validate UUID
uuid_str = "2b00e93f-f123-424d-9571-0095c6299714"
is_valid = SecretsValidator.validate_uuid(uuid_str)
print(f"UUID valid: {is_valid}")
```

### Health Check Usage

```python
from load_env_nba_mcp_synthesis_workflow import HealthChecker, load_workflow_secrets

# Load secrets
secrets = load_workflow_secrets()

# Perform health checks
health_checker = HealthChecker(secrets)

# Check API connectivity
connectivity = health_checker.check_api_connectivity()
print(f"API Connectivity: {connectivity}")

# Check secret strength
strength = health_checker.check_secret_strength()
print(f"Secret Strength: {strength}")

# Get comprehensive summary
summary = health_checker.get_health_summary()
print(f"Health Summary: {summary}")
```

### Slack Integration Usage

```python
from load_env_nba_mcp_synthesis_workflow import SlackNotifier

# Initialize notifier
notifier = SlackNotifier()

# Send success notification
success = notifier.send_notification("Secrets loaded successfully", "success")
print(f"Success notification sent: {success}")

# Send warning notification
warning = notifier.send_notification("Some secrets have validation warnings", "warning")
print(f"Warning notification sent: {warning}")

# Send error notification
error = notifier.send_notification("Failed to load secrets", "error")
print(f"Error notification sent: {error}")
```

### Docker Integration Usage

```python
# In Docker container
import subprocess
import os

# Load secrets in Docker
subprocess.run([
    'python3', '/app/load_secrets_docker.py',
    '--project', 'nba-mcp-synthesis',
    '--context', 'production'
], check=True)

# Verify secrets are loaded
google_key = os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
print(f"Google API key loaded: {'Yes' if google_key else 'No'}")
```

### Kubernetes Integration Usage

```python
# In Kubernetes pod
import subprocess
import os

# Load secrets via init container
subprocess.run([
    'python3', '/app/load_secrets_docker.py',
    '--project', 'nba-mcp-synthesis',
    '--context', 'production'
], check=True)

# Verify secrets are available
secrets = [
    'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
    'ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'
]

for secret in secrets:
    value = os.getenv(secret)
    print(f"{secret}: {'Loaded' if value else 'Missing'}")
```

## Conclusion

This API documentation provides comprehensive information about all classes, methods, and functions in the NBA MCP Synthesis secrets management system. The system offers:

- **Hierarchical secret loading** with context detection
- **Comprehensive validation** for all secret types
- **Health checks** for API connectivity and secret strength
- **Slack integration** for monitoring and alerting
- **Docker and Kubernetes support** for containerized deployments
- **Backward compatibility** for existing code
- **Robust error handling** with detailed exception classes

For additional information, refer to:
- [Secrets Management Guide](SECRETS_MANAGEMENT_GUIDE.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)

