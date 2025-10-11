"""
AWS Glue Tools for MCP Server
Provides tools to interact with AWS Glue Data Catalog
"""

import logging
from typing import List, Dict, Any
from mcp.types import Tool

logger = logging.getLogger(__name__)


class GlueTools:
    """AWS Glue catalog tools"""

    def __init__(self, glue_connector, config):
        self.glue_connector = glue_connector
        self.config = config

    def get_tool_definitions(self) -> List[Tool]:
        """Return Glue tool definitions"""
        return [
            Tool(
                name="get_glue_table_metadata",
                description="Get metadata for a table from AWS Glue Data Catalog",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to get metadata for"
                        }
                    },
                    "required": ["table_name"]
                }
            ),
            Tool(
                name="list_glue_tables",
                description="List all tables in the AWS Glue Data Catalog",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Glue tool"""
        try:
            if tool_name == "get_glue_table_metadata":
                return await self._get_table_metadata(arguments["table_name"])
            elif tool_name == "list_glue_tables":
                return await self._list_tables()
            else:
                raise ValueError(f"Unknown Glue tool: {tool_name}")

        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    async def _get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """Get table metadata from Glue"""
        metadata = await self.glue_connector.get_table_metadata(table_name)
        return {
            "success": True,
            "table_name": table_name,
            "metadata": metadata
        }

    async def _list_tables(self) -> Dict[str, Any]:
        """List all tables in Glue catalog"""
        tables = await self.glue_connector.list_tables()
        return {
            "success": True,
            "tables": tables,
            "count": len(tables)
        }
