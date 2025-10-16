"""
Database Tools for MCP Server
Provides tools for querying RDS PostgreSQL database
"""

import logging
import re
from typing import Dict, Any, Optional, List
from pydantic import ValidationError
from mcp.types import Tool

try:
    from mcp_server.connectors.rds_connector import RDSConnector
    from mcp_server.responses import (
        success_response,
        error_response,
        validation_error,
        database_error
    )
    from mcp_server.tools.params import (
        QueryDatabaseParams,
        GetTableSchemaParams,
        ListTablesParams
    )
except ImportError:
    # Fallback for when running as standalone script
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from mcp_server.connectors.rds_connector import RDSConnector
    from mcp_server.responses import (
        success_response,
        error_response,
        validation_error,
        database_error
    )
    from mcp_server.tools.params import (
        QueryDatabaseParams,
        GetTableSchemaParams,
        ListTablesParams
    )

logger = logging.getLogger(__name__)


class DatabaseTools:
    """Tools for database operations"""

    def __init__(self, rds_connector: RDSConnector):
        """Initialize database tools with RDS connector"""
        self.rds = rds_connector

    async def query_rds_database(
        self,
        sql_query: str,
        max_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SQL query against RDS database with validation.

        Args:
            sql_query: SQL query to execute (SELECT only)
            max_rows: Maximum number of rows to return (default: 1000)

        Returns:
            Dict with query results or error information
        """
        try:
            # Validate query - only allow SELECT statements
            query_upper = sql_query.strip().upper()

            # Check for forbidden keywords
            forbidden_keywords = [
                'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
                'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE'
            ]

            for keyword in forbidden_keywords:
                if re.search(rf'\b{keyword}\b', query_upper):
                    logger.warning(f"Forbidden SQL keyword detected: {keyword}")
                    return {
                        "success": False,
                        "error": f"Forbidden SQL operation: {keyword}. Only SELECT queries are allowed.",
                        "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
                    }

            # Ensure it's a SELECT query
            if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
                logger.warning(f"Non-SELECT query attempted: {query_upper[:50]}")
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed. Use WITH...SELECT for CTEs.",
                    "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
                }

            # Execute query with row limit
            logger.info(f"Executing database query (max_rows={max_rows})")
            result = await self.rds.execute_query(
                query=sql_query,
                fetch_all=True,
                max_rows=max_rows
            )

            if result["success"]:
                logger.info(f"Query successful: {result['row_count']} rows returned in {result['execution_time']:.2f}s")
            else:
                logger.error(f"Query failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            logger.error(f"Database query error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
            }

    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get table schema information from RDS.

        Args:
            table_name: Name of the table to inspect

        Returns:
            Dict with schema information or error
        """
        try:
            # Validate table name to prevent SQL injection
            if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
                return {
                    "success": False,
                    "error": "Invalid table name. Only alphanumeric characters and underscores allowed."
                }

            logger.info(f"Fetching schema for table: {table_name}")
            result = await self.rds.get_table_schema(table_name)

            if result["success"]:
                logger.info(f"Schema retrieved: {result['column_count']} columns")
            else:
                logger.warning(f"Schema retrieval failed for table: {table_name}")

            return result

        except Exception as e:
            logger.error(f"Error getting table schema: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name
            }

    async def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Get table statistics (row counts, sizes, indexes).

        Args:
            table_name: Name of the table to analyze

        Returns:
            Dict with table statistics or error
        """
        try:
            # Validate table name
            if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
                return {
                    "success": False,
                    "error": "Invalid table name. Only alphanumeric characters and underscores allowed."
                }

            logger.info(f"Fetching statistics for table: {table_name}")
            result = await self.rds.get_table_statistics(table_name)

            if result["success"]:
                logger.info(f"Statistics retrieved: {result['row_count']} rows, {result['total_size']}")
            else:
                logger.warning(f"Statistics retrieval failed for table: {table_name}")

            return result

        except Exception as e:
            logger.error(f"Error getting table statistics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name
            }

    async def explain_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Get EXPLAIN plan for query optimization.

        Args:
            sql_query: SQL query to analyze

        Returns:
            Dict with execution plan or error
        """
        try:
            # Validate query - only allow SELECT statements
            query_upper = sql_query.strip().upper()

            # Check for forbidden keywords
            forbidden_keywords = [
                'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
                'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE'
            ]

            for keyword in forbidden_keywords:
                if re.search(rf'\b{keyword}\b', query_upper):
                    return {
                        "success": False,
                        "error": f"Forbidden SQL operation: {keyword}. Only SELECT queries can be explained.",
                        "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
                    }

            # Ensure it's a SELECT query
            if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
                return {
                    "success": False,
                    "error": "Only SELECT queries can be explained.",
                    "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
                }

            logger.info(f"Generating EXPLAIN plan for query")
            result = await self.rds.explain_query(sql_query)

            if result["success"]:
                logger.info("EXPLAIN plan generated successfully")
            else:
                logger.error(f"EXPLAIN plan failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            logger.error(f"Error generating EXPLAIN plan: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query
            }

    async def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the database.

        Returns:
            Dict with list of table names or error
        """
        try:
            logger.info("Listing database tables")
            tables = await self.rds.list_tables()

            return {
                "success": True,
                "tables": tables,
                "table_count": len(tables)
            }

        except Exception as e:
            logger.error(f"Error listing tables: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def get_tool_definitions(self) -> List[Tool]:
        """Return database tool definitions for MCP"""
        return [
            Tool(
                name="query_database",
                description="Execute SQL SELECT query against PostgreSQL database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL SELECT query to execute"
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "Maximum number of rows to return",
                            "default": 1000
                        }
                    },
                    "required": ["sql_query"]
                }
            ),
            Tool(
                name="get_table_schema",
                description="Get schema information for a database table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        }
                    },
                    "required": ["table_name"]
                }
            ),
            Tool(
                name="list_tables",
                description="List all tables in the database",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a database tool with Pydantic validation and standardized responses.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Standardized SuccessResponse or ErrorResponse
        """
        try:
            if tool_name == "query_database":
                # Validate parameters with Pydantic
                try:
                    params = QueryDatabaseParams(**arguments)
                except ValidationError as e:
                    return validation_error(
                        f"Invalid parameters: {e}",
                        details={"validation_errors": e.errors()}
                    )

                result = await self.query_rds_database(params.sql_query, params.max_rows)

                if result.get("success"):
                    return success_response(
                        message=f"Query executed successfully: {result['row_count']} rows returned",
                        data=result
                    )
                else:
                    return database_error(
                        result.get("error", "Unknown database error"),
                        details={"query": params.sql_query[:100]}
                    )

            elif tool_name == "get_table_schema":
                # Validate parameters with Pydantic
                try:
                    params = GetTableSchemaParams(**arguments)
                except ValidationError as e:
                    return validation_error(
                        f"Invalid parameters: {e}",
                        details={"validation_errors": e.errors()}
                    )

                result = await self.get_table_schema(params.table_name)

                if result.get("success"):
                    return success_response(
                        message=f"Schema retrieved for table: {params.table_name}",
                        data=result
                    )
                else:
                    return database_error(
                        result.get("error", "Unknown database error"),
                        details={"table_name": params.table_name}
                    )

            elif tool_name == "list_tables":
                # No parameters to validate
                result = await self.list_tables()

                if result.get("success"):
                    return success_response(
                        message=f"Found {result['table_count']} tables",
                        data=result
                    )
                else:
                    return database_error(
                        result.get("error", "Unknown database error")
                    )

            else:
                return error_response(
                    f"Unknown database tool: {tool_name}",
                    error_type="UnknownToolError"
                )

        except Exception as e:
            logger.error(f"Error executing database tool {tool_name}: {e}", exc_info=True)
            return error_response(
                str(e),
                error_type=type(e).__name__,
                details={"tool": tool_name}
            )
