#!/usr/bin/env python3
"""
Health Check Module for Docker Containers

Provides health check functionality for containerized deployments.
Checks critical system components: secrets, database, filesystem.
"""

import os
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def check_health() -> Dict[str, Any]:
    """
    Perform comprehensive health check for Docker container.

    Returns:
        dict: Health status with component checks

    Example:
        {
            "status": "healthy",
            "checks": {
                "secrets": True,
                "database": True,
                "filesystem": True
            },
            "details": {
                "secrets_count": 15,
                "filesystem_writable": True
            }
        }
    """
    health = {
        "status": "healthy",
        "checks": {
            "secrets": check_secrets_loaded(),
            "filesystem": check_filesystem_access(),
            "python": check_python_imports(),
        },
        "details": {},
    }

    # Add database check if configured
    if os.getenv("CHECK_DATABASE", "false").lower() == "true":
        health["checks"]["database"] = check_database_connection()

    # Determine overall status
    if not all(health["checks"].values()):
        health["status"] = "unhealthy"
        failed_checks = [k for k, v in health["checks"].items() if not v]
        health["failed_checks"] = failed_checks

    return health


def check_secrets_loaded() -> bool:
    """
    Check if secrets are properly loaded.

    Returns:
        bool: True if secrets are loaded, False otherwise
    """
    try:
        from mcp_server.unified_secrets_manager import UnifiedSecretsManager

        sm = UnifiedSecretsManager()
        has_secrets = sm.verify_secrets_loaded()

        if has_secrets:
            logger.debug(
                f"Secrets check passed: {len(sm.get_all_secrets())} secrets loaded"
            )
        else:
            logger.warning("Secrets check failed: No secrets loaded")

        return has_secrets

    except Exception as e:
        logger.error(f"Secrets check failed with exception: {e}")
        return False


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        import psycopg2
        from mcp_server.unified_secrets_manager import get_secret

        # Get database configuration
        db_config = {
            "host": get_secret("DB_HOST") or "localhost",
            "port": int(get_secret("DB_PORT") or "5432"),
            "database": get_secret("DB_NAME") or "nba",
            "user": get_secret("DB_USER") or "postgres",
            "password": get_secret("DB_PASSWORD") or "",
        }

        # Attempt connection
        conn = psycopg2.connect(**db_config, connect_timeout=5)
        conn.close()

        logger.debug("Database check passed")
        return True

    except ImportError:
        logger.debug("Database check skipped: psycopg2 not installed")
        return True  # Don't fail if library not installed
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return False


def check_filesystem_access() -> bool:
    """
    Check if filesystem is accessible and writable.

    Returns:
        bool: True if filesystem is accessible, False otherwise
    """
    try:
        # Check data directory exists and is writable
        data_dir = Path("/app/data")
        logs_dir = Path("/app/logs")

        # Create directories if they don't exist
        data_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Test write access
        test_file = data_dir / ".health_check"
        test_file.write_text("health_check")
        test_file.unlink()

        logger.debug("Filesystem check passed")
        return True

    except Exception as e:
        logger.error(f"Filesystem check failed: {e}")
        return False


def check_python_imports() -> bool:
    """
    Check if critical Python modules can be imported.

    Returns:
        bool: True if all imports succeed, False otherwise
    """
    try:
        # Try importing critical modules
        import mcp_server
        import scripts
        import sympy
        import yaml

        logger.debug("Python imports check passed")
        return True

    except ImportError as e:
        logger.error(f"Python imports check failed: {e}")
        return False


def get_health_status_detailed() -> Dict[str, Any]:
    """
    Get detailed health status with additional metrics.

    Returns:
        dict: Detailed health information
    """
    basic_health = check_health()

    # Add system information
    try:
        import psutil

        basic_health["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        logger.debug("psutil not available for system metrics")

    # Add environment info
    basic_health["environment"] = {
        "docker": os.getenv("DOCKER_CONTAINER", "false"),
        "project": os.getenv("PROJECT", "unknown"),
        "context": os.getenv("CONTEXT", "unknown"),
    }

    return basic_health


if __name__ == "__main__":
    """Test health checks"""
    import sys
    import json

    logging.basicConfig(level=logging.INFO)

    print("Running health checks...")
    health = get_health_status_detailed()

    print(json.dumps(health, indent=2))

    if health["status"] != "healthy":
        print("\n❌ Health check FAILED")
        sys.exit(1)
    else:
        print("\n✅ Health check PASSED")
        sys.exit(0)
