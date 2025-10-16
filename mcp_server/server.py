"""
NBA MCP Server - Main Server Implementation
Provides context from NBA project to AI models via MCP protocol

Updated to use the new unified secrets and configuration management system.
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, Resource

try:
    from .tools import (
        DatabaseTools,
        S3Tools,
        GlueTools,
        FileTools,
        ActionTools
    )
    from .config import MCPConfig
    from .connectors import (
        RDSConnector,
        S3Connector,
        GlueConnector,
        SlackNotifier
    )
    from .security import SecurityManager, SecurityConfig
    from .logging_config import setup_logging, get_logger, RequestContext, PerformanceLogger
    from .unified_configuration_manager import UnifiedConfigurationManager
except ImportError:
    # Fallback for when running as standalone script
    from tools import (
        DatabaseTools,
        S3Tools,
        GlueTools,
        FileTools,
        ActionTools
    )
    from config import MCPConfig
    from connectors import (
        RDSConnector,
        S3Connector,
        GlueConnector,
        SlackNotifier
    )
    from security import SecurityManager, SecurityConfig
    from logging_config import setup_logging, get_logger, RequestContext, PerformanceLogger
    from unified_configuration_manager import UnifiedConfigurationManager

# Load environment variables (for backward compatibility)
load_dotenv()

# Setup structured logging
setup_logging(
    log_level=os.getenv('MCP_LOG_LEVEL', 'INFO'),
    log_dir=os.getenv('MCP_LOG_DIR', 'logs'),
    enable_json=os.getenv('MCP_LOG_JSON', 'true').lower() == 'true',
    enable_console=True,
    enable_file=True
)
logger = get_logger(__name__)


class NBAMCPServer:
    """
    MCP Server for NBA Simulator Project
    Provides tools to access RDS, S3, Glue, and project files
    """

    def __init__(self, config: Optional[MCPConfig] = None, project: str = 'nba-mcp-synthesis', context: str = 'production'):
        """Initialize MCP server with unified configuration system"""
        # Load secrets using hierarchical loader
        logger.info(f"Loading secrets for project={project}, context={context}")
        try:
            result = subprocess.run([
                sys.executable,
                "/Users/ryanranft/load_env_hierarchical.py",
                project, "NBA", context
            ], capture_output=True, text=True, check=True)

            logger.info("✅ Secrets loaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load secrets: {e.stderr}")
            raise RuntimeError(f"Failed to load secrets: {e.stderr}")
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            raise RuntimeError(f"Error loading secrets: {e}")

        # Initialize unified configuration manager
        try:
            self.unified_config = UnifiedConfigurationManager(project, context)
            logger.info("✅ Unified configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load unified configuration: {e}")
            raise RuntimeError(f"Failed to load unified configuration: {e}")

        # Use unified config or fallback to old config
        self.config = config or MCPConfig.from_env()
        self.server = Server("nba-mcp-server")

        # Initialize concurrency control
        concurrency_limit = int(os.getenv("MCP_TOOL_CONCURRENCY", "5"))
        self.tool_semaphore = asyncio.Semaphore(concurrency_limit)
        logger.info(f"MCP tool concurrency limit set to: {concurrency_limit}")

        # Initialize security manager
        security_config = SecurityConfig()
        self.security_manager = SecurityManager(
            security_config,
            project_root=self.config.project_root
        )

        # Initialize connectors
        self._init_connectors()

        # Initialize tools
        self._init_tools()

        # Setup MCP handlers
        self._setup_handlers()

        logger.info("NBA MCP Server initialized (with security enabled)")

    def _init_connectors(self):
        """Initialize data source connectors"""
        try:
            # RDS PostgreSQL
            self.rds_connector = RDSConnector(
                host=self.config.rds_host,
                port=self.config.rds_port,
                database=self.config.rds_database,
                username=self.config.rds_username,
                password=self.config.rds_password
            )
            logger.info("RDS connector initialized")

            # S3
            self.s3_connector = S3Connector(
                bucket_name=self.config.s3_bucket,
                region=self.config.s3_region
            )
            logger.info("S3 connector initialized")

            # AWS Glue
            self.glue_connector = GlueConnector(
                database=self.config.glue_database,
                region=self.config.glue_region
            )
            logger.info("Glue connector initialized")

            # Slack (optional)
            if self.config.slack_webhook_url:
                self.slack_notifier = SlackNotifier(
                    webhook_url=self.config.slack_webhook_url
                )
                logger.info("Slack notifier initialized")
            else:
                self.slack_notifier = None

        except Exception as e:
            logger.error(f"Failed to initialize connectors: {e}")
            raise

    def _init_tools(self):
        """Initialize MCP tools"""
        self.database_tools = DatabaseTools(self.rds_connector)
        self.s3_tools = S3Tools(self.s3_connector)
        self.glue_tools = GlueTools(self.glue_connector, self.config)
        self.file_tools = FileTools(self.config.project_root)
        self.action_tools = ActionTools(
            project_root=self.config.project_root,
            synthesis_output_dir=os.path.join(self.config.project_root, "synthesis_outputs"),
            slack_notifier=self.slack_notifier
        )

        logger.info("MCP tools initialized")

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Return list of available MCP tools"""
            tools = []

            # Database tools
            tools.extend(self.database_tools.get_tool_definitions())

            # S3 tools
            tools.extend(self.s3_tools.get_tool_definitions())

            # Glue tools
            tools.extend(self.glue_tools.get_tool_definitions())

            # File tools
            tools.extend(self.file_tools.get_tool_definitions())

            # Action tools
            tools.extend(self.action_tools.get_tool_definitions())

            logger.info(f"Listing {len(tools)} available tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """Execute requested tool with arguments"""
            # Get client ID (in production, this would come from request context)
            client_id = arguments.get("_client_id", "default_client")

            # Use request context for tracking and performance measurement
            with RequestContext(logger, f"tool_call:{name}", client_id=client_id) as ctx:
                # Security validation
                valid, error_message = await self.security_manager.validate_request(
                    client_id=client_id,
                    tool_name=name,
                    arguments=arguments
                )

                if not valid:
                    logger.warning(
                        f"Security validation failed",
                        extra={"tool": name, "reason": error_message}
                    )
                    return {
                        "success": False,
                        "error": f"Security validation failed: {error_message}",
                        "tool": name,
                        "timestamp": datetime.now().isoformat()
                    }

                try:
                    # Use semaphore to limit concurrent tool executions
                    async with self.tool_semaphore:
                        # Route to appropriate tool handler
                        if name.startswith("query_") or name.startswith("get_table"):
                            result = await self.database_tools.execute(name, arguments)
                        elif name.startswith("fetch_s3") or name.startswith("list_s3"):
                            result = await self.s3_tools.execute(name, arguments)
                        elif name.startswith("get_glue"):
                            result = await self.glue_tools.execute(name, arguments)
                        elif name.startswith("read_") or name.startswith("search_"):
                            result = await self.file_tools.execute(name, arguments)
                        elif name in ["save_to_project", "log_synthesis_result", "send_notification"]:
                            result = await self.action_tools.execute(name, arguments)
                        else:
                            raise ValueError(f"Unknown tool: {name}")

                    # Log successful execution with extra fields
                    logger.info(
                        f"Tool executed successfully",
                        extra={
                            "tool": name,
                            "result_size": len(str(result)) if result else 0
                        }
                    )

                    # Notify on success if configured
                    if self.slack_notifier and self.config.notify_on_success:
                        await self._notify_tool_execution(name, arguments, result, success=True)

                    return result

                except Exception as e:
                    # Error logging with structured fields
                    logger.error(
                        f"Tool execution failed",
                        extra={
                            "tool": name,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        },
                        exc_info=True
                    )

                    # Notify on error
                    if self.slack_notifier:
                        await self._notify_tool_execution(name, arguments, str(e), success=False)

                    return {
                        "success": False,
                        "error": str(e),
                        "tool": name,
                        "timestamp": datetime.now().isoformat()
                    }

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources (databases, files, etc.)"""
            resources = []

            # Add database resource
            resources.append(Resource(
                uri=f"postgresql://{self.config.rds_host}/{self.config.rds_database}",
                name="NBA Simulator Database",
                description="PostgreSQL database with game data, player stats, and more"
            ))

            # Add S3 resource
            resources.append(Resource(
                uri=f"s3://{self.config.s3_bucket}",
                name="NBA Data Lake",
                description="S3 bucket with 146K+ game JSON files and raw data"
            ))

            # Add Glue catalog
            resources.append(Resource(
                uri=f"glue://{self.config.glue_database}",
                name="NBA Data Catalog",
                description="AWS Glue catalog with table schemas and metadata"
            ))

            # Add project directory
            resources.append(Resource(
                uri=f"file://{self.config.project_root}",
                name="NBA Simulator Project",
                description="Local project files and code"
            ))

            return resources

    async def _notify_tool_execution(
        self,
        tool_name: str,
        arguments: Dict,
        result: Any,
        success: bool
    ):
        """Send Slack notification for tool execution"""
        if not self.slack_notifier:
            return

        try:
            emoji = "✅" if success else "❌"
            status = "succeeded" if success else "failed"

            message = {
                "text": f"{emoji} MCP Tool {status}: {tool_name}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} MCP Tool Execution"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Tool:*\n{tool_name}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{status.title()}"
                            }
                        ]
                    }
                ]
            }

            if not success:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n```{result}```"
                    }
                })

            await self.slack_notifier.send_notification(message)

        except Exception as e:
            logger.warning(f"Failed to send Slack notification: {e}")

    async def start(self):
        """Start the MCP server"""
        logger.info(f"Starting NBA MCP Server")

        # Test connections
        await self._test_connections()

        # Start server using stdio transport (standard MCP pattern)
        import sys
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def _test_connections(self):
        """Test all data source connections"""
        logger.info("Testing data source connections...")

        # Test RDS
        try:
            await self.database_tools.execute("query_rds_database", {
                "sql_query": "SELECT 1"
            })
            logger.info("✅ RDS connection successful")
        except Exception as e:
            logger.error(f"❌ RDS connection failed: {e}")

        # Test S3
        try:
            await self.s3_tools.execute("list_s3_files", {
                "prefix": "",
                "max_keys": 1
            })
            logger.info("✅ S3 connection successful")
        except Exception as e:
            logger.error(f"❌ S3 connection failed: {e}")

        # Test Glue
        try:
            tables = await self.glue_connector.list_tables()
            logger.info(f"✅ Glue connection successful ({len(tables)} tables found)")
        except Exception as e:
            logger.error(f"❌ Glue connection failed: {e}")


async def main():
    """Main entry point for MCP server"""
    server = NBAMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
