"""
NBA MCP Server - Main Server Implementation
Provides context from NBA project to AI models via MCP protocol
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

from mcp import Server
from mcp.types import Tool, TextContent, ImageContent, Resource
from mcp.server import Request, Response

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

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv('MCP_LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NBAMCPServer:
    """
    MCP Server for NBA Simulator Project
    Provides tools to access RDS, S3, Glue, and project files
    """
    
    def __init__(self, config: Optional[MCPConfig] = None):
        """Initialize MCP server with configuration"""
        self.config = config or MCPConfig.from_env()
        self.server = Server("nba-mcp-server")
        
        # Initialize connectors
        self._init_connectors()
        
        # Initialize tools
        self._init_tools()
        
        # Setup MCP handlers
        self._setup_handlers()
        
        logger.info("NBA MCP Server initialized")
    
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
        self.database_tools = DatabaseTools(self.rds_connector, self.config)
        self.s3_tools = S3Tools(self.s3_connector, self.config)
        self.glue_tools = GlueTools(self.glue_connector, self.config)
        self.file_tools = FileTools(self.config)
        self.action_tools = ActionTools(
            self.config,
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
            logger.info(f"Calling tool: {name}")
            
            try:
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
                
                # Log successful execution
                if self.slack_notifier and self.config.notify_on_success:
                    await self._notify_tool_execution(name, arguments, result, success=True)
                
                return result
                
            except Exception as e:
                logger.error(f"Tool execution failed: {name} - {e}")
                
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
        logger.info(f"Starting NBA MCP Server on {self.config.host}:{self.config.port}")
        
        # Test connections
        await self._test_connections()
        
        # Start server
        await self.server.run(
            host=self.config.host,
            port=self.config.port
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
