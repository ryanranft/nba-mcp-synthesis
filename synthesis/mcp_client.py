"""
MCP Client for Context Gathering
Connects to NBA MCP Server to gather relevant context for AI synthesis
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import json
from pathlib import Path

try:
    from .resilience import retry_with_backoff, get_circuit_breaker
    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False
    # Fallback no-op decorator
    def retry_with_backoff(**kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP Client for gathering context from NBA project

    Connects to MCP server to retrieve:
    - Database schemas and table statistics
    - SQL query EXPLAIN plans
    - Sample data from tables
    - AWS Glue metadata
    - Project files and code
    """

    def __init__(self, server_url: str = "http://localhost:3000"):
        """
        Initialize MCP client

        Args:
            server_url: URL of the MCP server
        """
        self.server_url = server_url
        self.connected = False
        self.available_tools = []
        logger.info(f"MCP Client initialized for {server_url}")

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        retry_on=(ConnectionError, TimeoutError, OSError)
    )
    async def connect(self, server_url: Optional[str] = None) -> bool:
        """
        Connect to MCP server (with automatic retry)

        Args:
            server_url: Override server URL if provided

        Returns:
            True if connected successfully
        """
        if server_url:
            self.server_url = server_url

        try:
            # In a real implementation, this would establish connection to MCP server
            # For now, we'll simulate connection and tool discovery
            self.connected = True

            # Simulate tool discovery
            self.available_tools = [
                "query_rds_database",
                "get_table_schema",
                "get_table_stats",
                "get_explain_plan",
                "fetch_s3_sample_data",
                "get_glue_table_metadata",
                "read_project_file",
                "search_codebase"
            ]

            logger.info(f"Connected to MCP server: {self.server_url}")
            logger.info(f"Available tools: {len(self.available_tools)}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False

    @retry_with_backoff(
        max_retries=2,
        base_delay=0.5,
        retry_on=(ConnectionError, TimeoutError)
    )
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool (with automatic retry on network errors)

        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool

        Returns:
            Tool execution result
        """
        if not self.connected:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        if tool_name not in self.available_tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        logger.info(f"Calling MCP tool: {tool_name}")
        logger.debug(f"Parameters: {params}")

        try:
            # In a real implementation, this would make HTTP/WebSocket call to MCP server
            # For now, we'll simulate tool responses
            result = await self._simulate_tool_call(tool_name, params)

            logger.info(f"Tool {tool_name} completed successfully")
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def gather_context(
        self,
        query_type: str,
        user_input: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gather relevant context based on query type

        Args:
            query_type: Type of query (sql_optimization, code_optimization, etc.)
            user_input: User's request or question
            code: Optional code snippet provided by user

        Returns:
            Dictionary with gathered context
        """
        logger.info(f"Gathering context for query type: {query_type}")

        context = {
            "query_type": query_type,
            "user_input": user_input,
            "code": code,
            "metadata": {},
            "gathered_at": datetime.now().isoformat()
        }

        try:
            # Route to appropriate context gathering method
            if query_type == "sql_optimization":
                context.update(await self._gather_sql_context(user_input, code))
            elif query_type == "code_optimization":
                context.update(await self._gather_code_context(user_input, code))
            elif query_type == "statistical_analysis":
                context.update(await self._gather_stats_context(user_input))
            elif query_type == "etl_generation":
                context.update(await self._gather_etl_context(user_input))
            elif query_type == "debugging":
                context.update(await self._gather_debug_context(user_input, code))
            elif query_type == "general_analysis":
                context.update(await self._gather_general_context(user_input, code))
            else:
                logger.warning(f"Unknown query type: {query_type}")

            logger.info(f"Context gathered: {len(context)} sections")
            return context

        except Exception as e:
            logger.error(f"Failed to gather context: {e}")
            context["error"] = str(e)
            return context

    async def _gather_sql_context(self, user_input: str, sql_query: Optional[str]) -> Dict[str, Any]:
        """Gather context for SQL optimization"""
        context = {}

        # Extract table names from query
        tables = self._extract_table_names(sql_query or user_input)
        logger.info(f"Identified tables: {tables}")

        # Get schema for each table
        schemas = {}
        for table in tables:
            schema_result = await self.call_tool("get_table_schema", {"table_name": table})
            if schema_result["success"]:
                schemas[table] = schema_result["result"]

        context["schemas"] = schemas

        # Get table statistics
        stats = {}
        for table in tables:
            stats_result = await self.call_tool("get_table_stats", {"table_name": table})
            if stats_result["success"]:
                stats[table] = stats_result["result"]

        context["table_stats"] = stats

        # Get EXPLAIN plan if we have a full query
        if sql_query:
            explain_result = await self.call_tool("get_explain_plan", {"sql_query": sql_query})
            if explain_result["success"]:
                context["explain_plan"] = explain_result["result"]

        return context

    async def _gather_code_context(self, user_input: str, code: Optional[str]) -> Dict[str, Any]:
        """Gather context for code optimization"""
        context = {}

        # Extract file references
        files = self._extract_file_references(user_input)

        # Read related files
        file_contents = {}
        for file_path in files:
            file_result = await self.call_tool("read_project_file", {"file_path": file_path})
            if file_result["success"]:
                file_contents[file_path] = file_result["result"]

        context["related_files"] = file_contents

        # Search for similar patterns in codebase
        if code:
            # Extract key functions/classes from code
            patterns = self._extract_code_patterns(code)
            search_results = {}

            for pattern in patterns[:3]:  # Limit to top 3 patterns
                search_result = await self.call_tool(
                    "search_codebase",
                    {"pattern": pattern, "max_results": 5}
                )
                if search_result["success"]:
                    search_results[pattern] = search_result["result"]

            context["similar_code"] = search_results

        return context

    async def _gather_stats_context(self, user_input: str) -> Dict[str, Any]:
        """Gather context for statistical analysis"""
        context = {}

        # Extract table/dataset names
        tables = self._extract_table_names(user_input)

        # Get sample data
        sample_data = {}
        for table in tables:
            sample_result = await self.call_tool(
                "fetch_s3_sample_data",
                {"table_name": table, "sample_size": 100}
            )
            if sample_result["success"]:
                sample_data[table] = sample_result["result"]

        context["sample_data"] = sample_data

        # Get Glue metadata for data types and partitions
        metadata = {}
        for table in tables:
            meta_result = await self.call_tool(
                "get_glue_table_metadata",
                {"table_name": table}
            )
            if meta_result["success"]:
                metadata[table] = meta_result["result"]

        context["metadata"] = metadata

        return context

    async def _gather_etl_context(self, user_input: str) -> Dict[str, Any]:
        """Gather context for ETL generation"""
        context = {}

        # Extract source and target information
        sources = self._extract_table_names(user_input, source_type="source")
        targets = self._extract_table_names(user_input, source_type="target")

        # Get source schemas
        source_schemas = {}
        for table in sources:
            schema_result = await self.call_tool("get_table_schema", {"table_name": table})
            if schema_result["success"]:
                source_schemas[table] = schema_result["result"]

        context["source_schemas"] = source_schemas

        # Get target schemas
        target_schemas = {}
        for table in targets:
            schema_result = await self.call_tool("get_table_schema", {"table_name": table})
            if schema_result["success"]:
                target_schemas[table] = schema_result["result"]

        context["target_schemas"] = target_schemas

        # Get sample data from sources
        sample_data = {}
        for table in sources:
            sample_result = await self.call_tool(
                "fetch_s3_sample_data",
                {"table_name": table, "sample_size": 50}
            )
            if sample_result["success"]:
                sample_data[table] = sample_result["result"]

        context["source_samples"] = sample_data

        return context

    async def _gather_debug_context(self, user_input: str, code: Optional[str]) -> Dict[str, Any]:
        """Gather context for debugging"""
        context = {}

        # Extract error messages or stack traces
        error_info = self._extract_error_info(user_input)
        context["error_info"] = error_info

        # Get related files
        files = self._extract_file_references(user_input + (code or ""))
        file_contents = {}

        for file_path in files:
            file_result = await self.call_tool("read_project_file", {"file_path": file_path})
            if file_result["success"]:
                file_contents[file_path] = file_result["result"]

        context["related_files"] = file_contents

        # If code references database tables, get their schemas
        if code:
            tables = self._extract_table_names(code)
            schemas = {}

            for table in tables:
                schema_result = await self.call_tool("get_table_schema", {"table_name": table})
                if schema_result["success"]:
                    schemas[table] = schema_result["result"]

            context["table_schemas"] = schemas

        return context

    async def _gather_general_context(self, user_input: str, code: Optional[str]) -> Dict[str, Any]:
        """Gather general context"""
        context = {}

        # Extract any table references
        tables = self._extract_table_names(user_input + (code or ""))
        if tables:
            schemas = {}
            for table in tables[:3]:  # Limit to 3 tables
                schema_result = await self.call_tool("get_table_schema", {"table_name": table})
                if schema_result["success"]:
                    schemas[table] = schema_result["result"]
            context["schemas"] = schemas

        # Extract any file references
        files = self._extract_file_references(user_input + (code or ""))
        if files:
            file_contents = {}
            for file_path in files[:3]:  # Limit to 3 files
                file_result = await self.call_tool("read_project_file", {"file_path": file_path})
                if file_result["success"]:
                    file_contents[file_path] = file_result["result"]
            context["files"] = file_contents

        return context

    # Helper methods for extracting information

    def _extract_table_names(self, text: str, source_type: Optional[str] = None) -> List[str]:
        """Extract table names from text"""
        tables = []

        # Common NBA table patterns
        nba_tables = [
            "player_stats", "team_stats", "game_logs", "play_by_play",
            "shot_chart", "boxscores", "advanced_stats", "tracking_stats",
            "games", "players", "teams", "seasons"
        ]

        text_lower = text.lower()

        # Check for explicit table mentions
        for table in nba_tables:
            if table in text_lower:
                tables.append(table)

        # Extract from SQL-like patterns (FROM clause)
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(from_pattern, text, re.IGNORECASE)
        tables.extend(matches)

        # Extract from JOIN clauses
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(join_pattern, text, re.IGNORECASE)
        tables.extend(matches)

        # Filter by source type if specified
        if source_type == "source":
            source_keywords = ["from", "source", "extract", "read"]
            tables = [t for t in tables if any(k in text_lower for k in source_keywords)]
        elif source_type == "target":
            target_keywords = ["to", "target", "load", "write", "insert"]
            tables = [t for t in tables if any(k in text_lower for k in target_keywords)]

        return list(set(tables))  # Remove duplicates

    def _extract_file_references(self, text: str) -> List[str]:
        """Extract file paths from text"""
        files = []

        # Pattern for file paths
        path_patterns = [
            r'([/\\]?[\w-]+[/\\][\w-]+[/\\][\w.-]+\.py)',  # Python files
            r'([/\\]?[\w-]+[/\\][\w-]+[/\\][\w.-]+\.sql)',  # SQL files
            r'([/\\]?[\w-]+[/\\][\w-]+[/\\][\w.-]+\.json)',  # JSON files
            r'`([^`]+\.(?:py|sql|json|yaml|yml))`',  # Files in backticks
            r'"([^"]+\.(?:py|sql|json|yaml|yml))"',  # Files in quotes
        ]

        for pattern in path_patterns:
            matches = re.findall(pattern, text)
            files.extend(matches)

        return list(set(files))

    def _extract_code_patterns(self, code: str) -> List[str]:
        """Extract key patterns from code (function names, class names, etc.)"""
        patterns = []

        # Extract function definitions
        func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        functions = re.findall(func_pattern, code)
        patterns.extend(functions)

        # Extract class definitions
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        classes = re.findall(class_pattern, code)
        patterns.extend(classes)

        # Extract important variable names (avoid common ones)
        var_pattern = r'([a-zA-Z_][a-zA-Z0-9_]{4,})\s*='
        variables = re.findall(var_pattern, code)
        common_vars = {"self", "data", "result", "value", "item", "temp"}
        patterns.extend([v for v in variables if v not in common_vars])

        return patterns[:10]  # Return top 10 patterns

    def _extract_error_info(self, text: str) -> Dict[str, Any]:
        """Extract error information from text"""
        error_info = {}

        # Extract error type
        error_type_pattern = r'(\w+Error|\w+Exception):\s*(.+)'
        match = re.search(error_type_pattern, text)
        if match:
            error_info["error_type"] = match.group(1)
            error_info["error_message"] = match.group(2)

        # Extract traceback file references
        traceback_pattern = r'File\s+"([^"]+)",\s+line\s+(\d+)'
        matches = re.findall(traceback_pattern, text)
        if matches:
            error_info["traceback"] = [
                {"file": file, "line": int(line)}
                for file, line in matches
            ]

        return error_info

    async def _simulate_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Simulate MCP tool calls for development
        In production, this would make actual HTTP/WebSocket calls
        """
        # Simulate small delay
        await asyncio.sleep(0.1)

        # Return simulated results based on tool
        if tool_name == "get_table_schema":
            return {
                "table": params.get("table_name"),
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "value", "type": "NUMERIC", "nullable": True}
                ],
                "primary_key": ["id"],
                "indexes": ["idx_name"]
            }

        elif tool_name == "get_table_stats":
            return {
                "table": params.get("table_name"),
                "row_count": 1000000,
                "size_mb": 250.5,
                "indexes": 3,
                "last_analyzed": "2025-10-08T10:00:00Z"
            }

        elif tool_name == "get_explain_plan":
            return {
                "query": params.get("sql_query"),
                "plan": "Seq Scan on table (cost=0.00..1000.00 rows=1000)",
                "execution_time_ms": 150.5
            }

        elif tool_name == "fetch_s3_sample_data":
            return {
                "table": params.get("table_name"),
                "sample_size": params.get("sample_size", 100),
                "data": [{"id": 1, "value": 100}, {"id": 2, "value": 200}]
            }

        elif tool_name == "get_glue_table_metadata":
            return {
                "table": params.get("table_name"),
                "location": f"s3://bucket/path/{params.get('table_name')}",
                "format": "parquet",
                "partitions": ["season", "team"]
            }

        elif tool_name == "read_project_file":
            return {
                "file": params.get("file_path"),
                "content": "# Sample file content\nprint('Hello NBA')"
            }

        elif tool_name == "search_codebase":
            return {
                "pattern": params.get("pattern"),
                "matches": [
                    {"file": "/path/to/file1.py", "line": 42},
                    {"file": "/path/to/file2.py", "line": 105}
                ]
            }

        elif tool_name == "query_rds_database":
            return {
                "success": True,
                "query": params.get("sql_query"),
                "results": [
                    {"team_id": 1, "team_name": "Lakers", "wins": 47},
                    {"team_id": 2, "team_name": "Celtics", "wins": 45},
                    {"team_id": 3, "team_name": "Warriors", "wins": 43}
                ],
                "row_count": 3,
                "execution_time_ms": 25.5
            }

        else:
            return {"message": "Tool executed successfully"}

    async def list_tables(self) -> List[str]:
        """List all available tables"""
        # This is simulated - in production would query actual MCP server
        return [
            "players", "teams", "games", "box_score_players", "box_score_teams",
            "play_by_play", "player_game_stats", "team_game_stats",
            "advanced_stats", "tracking_stats", "shot_chart", "lineups",
            "injuries", "transactions", "schedules", "standings"
        ]

    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table schema description"""
        return await self.call_tool("get_table_schema", {"table_name": table_name})

    async def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        return await self.call_tool("query_rds_database", {"sql_query": query})

    async def disconnect(self):
        """Disconnect from MCP server"""
        self.connected = False
        logger.info("Disconnected from MCP server")
