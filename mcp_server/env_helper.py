#!/usr/bin/env python3
"""
Environment Variable Helper for NBA MCP Synthesis

Provides a reusable helper function for getting environment variables
with hierarchical fallback support for the new naming convention.
"""

import os
from typing import Optional, List


def get_hierarchical_env(
    base_name: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """
    Get environment variable with hierarchical fallback.

    Args:
        base_name: Base variable name (e.g., "GOOGLE_API_KEY")
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        Value from environment or None
    """
    # Try new naming convention
    new_name = f"{base_name}_{project}_{context}"
    value = os.getenv(new_name)

    if value:
        return value

    # Try other contexts in order of preference
    for ctx in ["WORKFLOW", "DEVELOPMENT", "TEST", "PRODUCTION"]:
        if ctx != context:
            fallback_name = f"{base_name}_{project}_{ctx}"
            value = os.getenv(fallback_name)
            if value:
                return value

    # Fallback to old naming convention
    return os.getenv(base_name)


def get_hierarchical_env_with_default(
    base_name: str,
    default: str,
    project: str = "NBA_MCP_SYNTHESIS",
    context: str = "WORKFLOW",
) -> str:
    """
    Get environment variable with hierarchical fallback and default value.

    Args:
        base_name: Base variable name (e.g., "GOOGLE_API_KEY")
        default: Default value if not found
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        Value from environment or default
    """
    value = get_hierarchical_env(base_name, project, context)
    return value if value is not None else default


def get_hierarchical_env_int(
    base_name: str,
    default: int,
    project: str = "NBA_MCP_SYNTHESIS",
    context: str = "WORKFLOW",
) -> int:
    """
    Get environment variable as integer with hierarchical fallback and default value.

    Args:
        base_name: Base variable name (e.g., "PORT")
        default: Default integer value if not found
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        Integer value from environment or default
    """
    value = get_hierarchical_env(base_name, project, context)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_hierarchical_env_bool(
    base_name: str,
    default: bool,
    project: str = "NBA_MCP_SYNTHESIS",
    context: str = "WORKFLOW",
) -> bool:
    """
    Get environment variable as boolean with hierarchical fallback and default value.

    Args:
        base_name: Base variable name (e.g., "ENABLED")
        default: Default boolean value if not found
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        Boolean value from environment or default
    """
    value = get_hierarchical_env(base_name, project, context)
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


def get_all_hierarchical_envs(
    base_names: List[str], project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> dict:
    """
    Get multiple environment variables with hierarchical fallback.

    Args:
        base_names: List of base variable names
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        Dictionary mapping base names to their values (or None if not found)
    """
    result = {}
    for base_name in base_names:
        result[base_name] = get_hierarchical_env(base_name, project, context)
    return result


def validate_required_envs(
    required_names: List[str],
    project: str = "NBA_MCP_SYNTHESIS",
    context: str = "WORKFLOW",
) -> List[str]:
    """
    Validate that required environment variables are set.

    Args:
        required_names: List of required base variable names
        project: Project name (NBA_MCP_SYNTHESIS, NBA_SIMULATOR_AWS, GLOBAL)
        context: Context (WORKFLOW, DEVELOPMENT, TEST, PRODUCTION)

    Returns:
        List of missing variable names
    """
    missing = []
    for base_name in required_names:
        if not get_hierarchical_env(base_name, project, context):
            missing.append(base_name)
    return missing


# Convenience functions for common use cases
def get_api_key(
    service: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get API key for a service (e.g., 'GOOGLE', 'ANTHROPIC', 'OPENAI', 'DEEPSEEK')"""
    return get_hierarchical_env(f"{service}_API_KEY", project, context)


def get_aws_credential(
    credential_type: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get AWS credential (e.g., 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')"""
    return get_hierarchical_env(credential_type, project, context)


def get_database_config(
    config_type: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get database configuration (e.g., 'RDS_HOST', 'RDS_USERNAME', 'RDS_PASSWORD', 'RDS_DATABASE')"""
    return get_hierarchical_env(config_type, project, context)


def get_s3_config(
    config_type: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get S3 configuration (e.g., 'S3_BUCKET', 'S3_REGION')"""
    return get_hierarchical_env(config_type, project, context)


def get_glue_config(
    config_type: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get Glue configuration (e.g., 'GLUE_DATABASE', 'GLUE_REGION')"""
    return get_hierarchical_env(config_type, project, context)


def get_slack_config(
    config_type: str, project: str = "NBA_MCP_SYNTHESIS", context: str = "WORKFLOW"
) -> Optional[str]:
    """Get Slack configuration (e.g., 'SLACK_WEBHOOK_URL')"""
    return get_hierarchical_env(config_type, project, context)


def get_model_config(
    model_type: str,
    config_type: str = "MODEL",
    project: str = "NBA_MCP_SYNTHESIS",
    context: str = "WORKFLOW",
) -> Optional[str]:
    """Get model configuration (e.g., 'GOOGLE_MODEL', 'CLAUDE_MODEL', 'OPENAI_MODEL')"""
    return get_hierarchical_env(f"{model_type}_{config_type}", project, context)


# Example usage and testing
if __name__ == "__main__":
    # Test the helper functions
    print("Testing Environment Variable Helper...")

    # Test basic functionality
    test_vars = [
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "RDS_HOST",
        "S3_BUCKET",
    ]

    print("\nTesting hierarchical loading:")
    for var in test_vars:
        value = get_hierarchical_env(var)
        print(f"  {var}: {'✓' if value else '✗'}")

    print("\nTesting convenience functions:")
    services = ["GOOGLE", "ANTHROPIC", "OPENAI", "DEEPSEEK"]
    for service in services:
        api_key = get_api_key(service)
        print(f"  {service} API Key: {'✓' if api_key else '✗'}")

    print("\nTesting validation:")
    missing = validate_required_envs(["GOOGLE_API_KEY", "ANTHROPIC_API_KEY"])
    if missing:
        print(f"  Missing required variables: {missing}")
    else:
        print("  All required variables are present")
