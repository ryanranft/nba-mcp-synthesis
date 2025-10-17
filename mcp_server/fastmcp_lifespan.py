"""
FastMCP Lifespan Manager for NBA MCP Server
Handles initialization and cleanup of shared resources
"""

from contextlib import asynccontextmanager
from typing import Any, Dict
import logging

# Import connectors
from .connectors import RDSConnector, S3Connector, GlueConnector, SlackNotifier
from .config import MCPConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def nba_lifespan(app):
    """
    Initialize shared resources for NBA MCP server.

    This lifespan manager creates and manages:
    - Database connection pool
    - S3 client
    - Glue client
    - Slack notifier (optional)

    Resources are available to all tools via ctx.request_context.lifespan_context
    """

    logger.info("🏀 Starting NBA MCP Server...")

    # Load configuration
    config = MCPConfig.from_env()
    logger.info("✅ Configuration loaded")

    # 1. Initialize RDS connector
    logger.info("📊 Connecting to RDS database...")
    try:
        rds_connector = RDSConnector(
            host=config.rds_host,
            port=config.rds_port,
            database=config.rds_database,
            username=config.rds_username,
            password=config.rds_password,
        )
        logger.info("✅ RDS connector initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RDS connector: {e}")
        raise

    # 2. Initialize S3 connector
    logger.info("☁️  Initializing S3 client...")
    try:
        s3_connector = S3Connector(
            bucket_name=config.s3_bucket, region=config.s3_region
        )
        logger.info("✅ S3 connector initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize S3 connector: {e}")
        raise

    # 3. Initialize Glue connector
    logger.info("📚 Initializing Glue client...")
    try:
        glue_connector = GlueConnector(
            database=config.glue_database, region=config.glue_region
        )
        logger.info("✅ Glue connector initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Glue connector: {e}")
        raise

    # 4. Initialize Slack notifier (optional)
    slack_notifier = None
    if config.slack_webhook_url:
        logger.info("💬 Initializing Slack notifier...")
        try:
            slack_notifier = SlackNotifier(webhook_url=config.slack_webhook_url)
            logger.info("✅ Slack notifier initialized")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Slack notifier: {e}")
            # Don't fail on Slack errors

    # Create context dictionary available to all tools
    context: Dict[str, Any] = {
        "rds_connector": rds_connector,
        "s3_connector": s3_connector,
        "glue_connector": glue_connector,
        "slack_notifier": slack_notifier,
        "config": config,
    }

    logger.info("✅ NBA MCP Server ready!")
    logger.info(f"   - RDS: {config.rds_host}/{config.rds_database}")
    logger.info(f"   - S3: {config.s3_bucket}")
    logger.info(f"   - Glue: {config.glue_database}")
    logger.info(f"   - Slack: {'enabled' if slack_notifier else 'disabled'}")

    try:
        yield context  # Server runs here with access to all resources
    finally:
        # Cleanup on shutdown
        logger.info("🛑 Shutting down NBA MCP Server...")

        # Close connectors (if they have close methods)
        if hasattr(rds_connector, "close"):
            try:
                await rds_connector.close()
                logger.info("✅ RDS connector closed")
            except Exception as e:
                logger.error(f"❌ Error closing RDS connector: {e}")

        if hasattr(s3_connector, "close"):
            try:
                await s3_connector.close()
                logger.info("✅ S3 connector closed")
            except Exception as e:
                logger.error(f"❌ Error closing S3 connector: {e}")

        if hasattr(glue_connector, "close"):
            try:
                await glue_connector.close()
                logger.info("✅ Glue connector closed")
            except Exception as e:
                logger.error(f"❌ Error closing Glue connector: {e}")

        logger.info("✅ Shutdown complete")
