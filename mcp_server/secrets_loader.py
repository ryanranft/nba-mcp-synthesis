#!/usr/bin/env python3
"""
Secrets Loader - Centralized Initialization

This module provides a single function to initialize secrets for any script.
Call this at the beginning of your scripts to load secrets from the hierarchical structure.

Usage:
    from mcp_server.secrets_loader import init_secrets

    # At the beginning of your script
    init_secrets()  # Auto-detects project and context

    # Or specify explicitly
    init_secrets(project="nba-mcp-synthesis", context="WORKFLOW")

    # Then use env_helper functions
    from mcp_server.env_helper import get_api_key
    anthropic_key = get_api_key('ANTHROPIC')

Author: NBA MCP Synthesis System
Date: 2025-10-22
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from unified_secrets_manager import UnifiedSecretsManager

logger = logging.getLogger(__name__)

# Global flag to prevent multiple initializations
_secrets_initialized = False


def init_secrets(
    project: Optional[str] = None,
    sport: Optional[str] = None,
    context: Optional[str] = None,
    force: bool = False,
    base_path: Optional[str] = None,
    quiet: bool = False
) -> bool:
    """
    Initialize secrets from hierarchical structure.

    This function loads secrets from the hierarchical file structure defined in
    SECRETS_STRUCTURE.md and sets them as environment variables.

    Args:
        project: Project name (e.g., 'nba-mcp-synthesis', 'nba-simulator-aws')
                Default: auto-detect from current directory or 'nba-mcp-synthesis'
        sport: Sport name (e.g., 'NBA')
              Default: 'NBA'
        context: Context/environment (e.g., 'WORKFLOW', 'DEVELOPMENT', 'TEST')
                Default: auto-detect from NBA_MCP_CONTEXT env var or 'WORKFLOW'
        force: Force reinitialization even if already initialized
        base_path: Override base path for secrets
                  Default: /Users/ryanranft/Desktop/++/big_cat_bets_assets
        quiet: Suppress informational logging

    Returns:
        True if secrets loaded successfully, False otherwise

    Examples:
        >>> # Auto-detect everything
        >>> init_secrets()

        >>> # Explicit project and context
        >>> init_secrets(project='nba-mcp-synthesis', context='WORKFLOW')

        >>> # For nba-simulator-aws project in development
        >>> init_secrets(project='nba-simulator-aws', context='DEVELOPMENT')
    """
    global _secrets_initialized

    # Check if already initialized
    if _secrets_initialized and not force:
        if not quiet:
            logger.debug("Secrets already initialized (use force=True to reinitialize)")
        return True

    # Auto-detect project from current directory
    if project is None:
        cwd = Path.cwd()
        if 'nba-simulator-aws' in str(cwd):
            project = 'nba-simulator-aws'
        else:
            project = os.getenv('PROJECT_NAME', 'nba-mcp-synthesis')

    # Default sport
    if sport is None:
        sport = os.getenv('SPORT_NAME', 'NBA')

    # Auto-detect context
    if context is None:
        context = os.getenv('NBA_MCP_CONTEXT', 'WORKFLOW')

    # Convert context to match directory naming
    context_map = {
        'WORKFLOW': 'production',
        'PRODUCTION': 'production',
        'DEVELOPMENT': 'development',
        'DEV': 'development',
        'TEST': 'test',
        'TESTING': 'test'
    }
    dir_context = context_map.get(context.upper(), 'production')

    if not quiet:
        logger.info(f"🔐 Initializing secrets for {project} ({sport}) - {context}")

    try:
        # Initialize secrets manager
        secrets_manager = UnifiedSecretsManager(
            base_path=base_path or "/Users/ryanranft/Desktop/++/big_cat_bets_assets"
        )

        # Load secrets hierarchically
        result = secrets_manager.load_secrets_hierarchical(
            project=project,
            sport=sport,
            context=dir_context
        )

        if result.success:
            # Set environment variables from loaded secrets
            for name, value in secrets_manager.get_all_secrets().items():
                os.environ[name] = value

            # Set aliases
            for alias, full_name in secrets_manager.get_aliases().items():
                if full_name in os.environ:
                    os.environ[alias] = os.environ[full_name]

            if not quiet:
                logger.info(f"✅ Loaded {result.secrets_loaded} secrets")
                if result.warnings:
                    for warning in result.warnings[:3]:  # Show first 3 warnings
                        logger.warning(f"⚠️  {warning}")

            _secrets_initialized = True
            return True
        else:
            logger.error(f"❌ Failed to load secrets")
            for error in result.errors:
                logger.error(f"   Error: {error}")
            return False

    except Exception as e:
        logger.error(f"❌ Exception loading secrets: {e}")
        return False


def is_initialized() -> bool:
    """
    Check if secrets have been initialized.

    Returns:
        True if init_secrets() has been called successfully
    """
    return _secrets_initialized


def reset():
    """
    Reset initialization flag (for testing).

    Note: This does not clear environment variables, only resets the flag
    so init_secrets() can be called again.
    """
    global _secrets_initialized
    _secrets_initialized = False


def validate_required_secrets(required_secrets: list[str]) -> tuple[bool, list[str]]:
    """
    Validate that required secrets are available.

    Args:
        required_secrets: List of secret base names (e.g., ['ANTHROPIC_API_KEY', 'AWS_ACCESS_KEY_ID'])

    Returns:
        Tuple of (all_present: bool, missing_secrets: list[str])

    Example:
        >>> success, missing = validate_required_secrets(['ANTHROPIC_API_KEY', 'GOOGLE_API_KEY'])
        >>> if not success:
        ...     print(f"Missing secrets: {missing}")
    """
    from env_helper import get_hierarchical_env

    missing = []
    for secret in required_secrets:
        if not get_hierarchical_env(secret):
            missing.append(secret)

    return (len(missing) == 0, missing)


# Convenience function for common use case
def init_for_automated_deployment() -> bool:
    """
    Initialize secrets specifically for automated deployment system.

    This is a convenience function that:
    - Loads secrets for nba-mcp-synthesis project
    - Uses WORKFLOW context (production)
    - Validates that ANTHROPIC_API_KEY is present

    Returns:
        True if initialization successful and required secrets present

    Example:
        >>> from mcp_server.secrets_loader import init_for_automated_deployment
        >>> if not init_for_automated_deployment():
        ...     print("Failed to initialize secrets for deployment")
        ...     sys.exit(1)
    """
    if not init_secrets(project='nba-mcp-synthesis', context='WORKFLOW'):
        return False

    # Validate required secrets for deployment
    success, missing = validate_required_secrets(['ANTHROPIC_API_KEY'])
    if not success:
        logger.error(f"❌ Missing required secrets for deployment: {missing}")
        return False

    return True


if __name__ == '__main__':
    """
    Test secrets initialization.

    Usage:
        python mcp_server/secrets_loader.py
        python mcp_server/secrets_loader.py --project nba-simulator-aws
        python mcp_server/secrets_loader.py --context DEVELOPMENT
    """
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Test secrets initialization')
    parser.add_argument('--project', help='Project name', default=None)
    parser.add_argument('--sport', help='Sport name', default=None)
    parser.add_argument('--context', help='Context (WORKFLOW/DEVELOPMENT/TEST)', default=None)
    parser.add_argument('--force', action='store_true', help='Force reinitialization')
    args = parser.parse_args()

    print("="*70)
    print("Secrets Loader Test")
    print("="*70)

    # Initialize secrets
    success = init_secrets(
        project=args.project,
        sport=args.sport,
        context=args.context,
        force=args.force
    )

    if success:
        print("\n✅ Secrets initialized successfully")

        # Test loading some common secrets
        from env_helper import get_api_key, get_database_config

        print("\n📋 Testing secret access:")

        test_secrets = {
            'ANTHROPIC': get_api_key('ANTHROPIC'),
            'GOOGLE': get_api_key('GOOGLE'),
            'OPENAI': get_api_key('OPENAI'),
            'DEEPSEEK': get_api_key('DEEPSEEK')
        }

        for name, value in test_secrets.items():
            status = '✓' if value else '✗'
            masked = f"{value[:10]}..." if value else 'Not set'
            print(f"  {status} {name}_API_KEY: {masked}")

        # Test validation
        print("\n🔍 Validating required secrets:")
        success, missing = validate_required_secrets([
            'ANTHROPIC_API_KEY',
            'GOOGLE_API_KEY'
        ])

        if success:
            print("  ✅ All required secrets present")
        else:
            print(f"  ❌ Missing secrets: {missing}")

    else:
        print("\n❌ Failed to initialize secrets")
        sys.exit(1)

    print("\n" + "="*70)
    print("Test complete")
    print("="*70)
