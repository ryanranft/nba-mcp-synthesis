#!/usr/bin/env python3
"""
MCP Test Client
Tests interaction with the NBA MCP Server via stdio
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.env_helper import get_hierarchical_env

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()


class MCPTestClient:
    """Test client for NBA MCP Server"""

    def __init__(self, server_script_path: str):
        """
        Initialize MCP test client

        Args:
            server_script_path: Path to MCP server script
        """
        self.server_script_path = server_script_path
        self.session = None
        self.client = None

    async def connect(self):
        """Connect to MCP server"""
        console.print("[yellow]Connecting to MCP server...[/yellow]")

        server_params = StdioServerParameters(
            command="python3",
            args=[self.server_script_path],
            env={
                "RDS_HOST": get_hierarchical_env(
                    "RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "localhost",
                "RDS_PORT": get_hierarchical_env(
                    "RDS_PORT", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "5432",
                "RDS_DATABASE": get_hierarchical_env(
                    "RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "nba_stats",
                "RDS_USERNAME": get_hierarchical_env(
                    "RDS_USERNAME", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "postgres",
                "RDS_PASSWORD": get_hierarchical_env(
                    "RDS_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "",
                "S3_BUCKET": get_hierarchical_env(
                    "S3_BUCKET", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "nba-mcp-books-20251011",
                "S3_REGION": get_hierarchical_env(
                    "S3_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "us-east-1",
            },
        )

        try:
            # Create stdio client context
            self.client = stdio_client(server_params)
            read, write = await self.client.__aenter__()

            # Create session
            self.session = ClientSession(read, write)
            await self.session.__aenter__()

            # Initialize the session (critical step!)
            await self.session.initialize()

            console.print("[green]✅ Connected to MCP server[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to connect: {e}[/red]")
            import traceback

            console.print(traceback.format_exc())
            return False

    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self.client:
            await self.client.__aexit__(None, None, None)
        console.print("[yellow]Disconnected from MCP server[/yellow]")

    async def list_tools(self):
        """List available MCP tools"""
        console.print("\n[bold cyan]Listing available tools...[/bold cyan]")

        try:
            result = await self.session.list_tools()

            table = Table(title="Available MCP Tools", show_header=True)
            table.add_column("Tool Name", style="cyan", width=25)
            table.add_column("Description", style="white", width=50)

            for tool in result.tools:
                table.add_row(tool.name, tool.description or "No description")

            console.print(table)
            console.print(f"\n[green]Found {len(result.tools)} tools[/green]")

            return result.tools

        except Exception as e:
            console.print(f"[red]Error listing tools: {e}[/red]")
            return []

    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        console.print(f"\n[bold yellow]Calling tool: {tool_name}[/bold yellow]")
        console.print(f"Arguments: {json.dumps(arguments, indent=2)}")

        try:
            start_time = datetime.now()

            result = await self.session.call_tool(tool_name, arguments)

            execution_time = (datetime.now() - start_time).total_seconds()

            console.print(
                f"\n[green]✅ Tool executed successfully ({execution_time:.2f}s)[/green]"
            )

            # Display result
            if hasattr(result, "content") and result.content:
                for content in result.content:
                    if hasattr(content, "text"):
                        # Try to parse as JSON for pretty printing
                        try:
                            result_data = json.loads(content.text)
                            console.print(
                                Panel(
                                    JSON(json.dumps(result_data, indent=2)),
                                    title=f"Result from {tool_name}",
                                )
                            )
                        except json.JSONDecodeError:
                            # Not JSON, just print as text
                            console.print(
                                Panel(
                                    content.text[:500]
                                    + ("..." if len(content.text) > 500 else ""),
                                    title=f"Result from {tool_name}",
                                )
                            )

            return result

        except Exception as e:
            console.print(f"[red]❌ Tool execution failed: {e}[/red]")
            import traceback

            console.print(traceback.format_exc())
            return None


async def test_list_tables(client: MCPTestClient):
    """Test list_tables tool"""
    console.print(Panel.fit("Test 1: List Tables", style="bold blue"))

    result = await client.call_tool("list_tables", {})
    return result


async def test_get_table_schema(client: MCPTestClient):
    """Test get_table_schema tool"""
    console.print("\n" + "=" * 80 + "\n")
    console.print(Panel.fit("Test 2: Get Table Schema", style="bold blue"))

    # First list tables to get a table name
    tables_result = await client.call_tool("list_tables", {})

    if tables_result and hasattr(tables_result, "content"):
        for content in tables_result.content:
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    if "tables" in data and data["tables"]:
                        # Get schema for first table
                        table_name = data["tables"][0]
                        console.print(
                            f"\n[cyan]Getting schema for: {table_name}[/cyan]"
                        )

                        schema_result = await client.call_tool(
                            "get_table_schema", {"table_name": table_name}
                        )
                        return schema_result
                except json.JSONDecodeError:
                    pass

    console.print("[yellow]Could not retrieve table schema[/yellow]")
    return None


async def test_query_database(client: MCPTestClient):
    """Test query_database tool"""
    console.print("\n" + "=" * 80 + "\n")
    console.print(Panel.fit("Test 3: Query Database", style="bold blue"))

    # Simple query
    sql = "SELECT version()"

    result = await client.call_tool("query_database", {"sql": sql})

    return result


async def test_list_s3_files(client: MCPTestClient):
    """Test list_s3_files tool"""
    console.print("\n" + "=" * 80 + "\n")
    console.print(Panel.fit("Test 4: List S3 Files", style="bold blue"))

    result = await client.call_tool("list_s3_files", {"prefix": "", "max_keys": 10})

    return result


async def test_complex_query(client: MCPTestClient):
    """Test complex database query"""
    console.print("\n" + "=" * 80 + "\n")
    console.print(Panel.fit("Test 5: Complex Query", style="bold blue"))

    # Get tables first
    tables_result = await client.call_tool("list_tables", {})

    # Try to find a suitable table for querying
    sql = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    LIMIT 20
    """

    result = await client.call_tool("query_database", {"sql": sql})

    return result


async def main():
    """Run MCP client tests"""
    console.print(
        Panel.fit(
            "NBA MCP Server - Client Testing Suite\n"
            + "Testing MCP server communication via stdio",
            style="bold white on blue",
        )
    )

    # Determine server script path
    project_root = Path(__file__).parent.parent
    server_script = project_root / "mcp_server" / "server_simple.py"

    if not server_script.exists():
        console.print(f"[red]Error: Server script not found at {server_script}[/red]")
        return

    console.print(f"\n[cyan]Server script: {server_script}[/cyan]")

    # Create client
    client = MCPTestClient(str(server_script))

    # Connect
    if not await client.connect():
        console.print("[red]Failed to connect to server. Exiting.[/red]")
        return

    try:
        # List available tools
        tools = await client.list_tools()

        if not tools:
            console.print(
                "[yellow]No tools available. Check server configuration.[/yellow]"
            )
            return

        # Run tests
        results = []

        console.print("\n" + "=" * 80 + "\n")
        console.print(Panel.fit("Running Tests", style="bold green"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Test 1: List tables
            task1 = progress.add_task("Test 1: List tables", total=1)
            result1 = await test_list_tables(client)
            results.append(("list_tables", result1 is not None))
            progress.update(task1, completed=1)

            # Test 2: Get schema
            task2 = progress.add_task("Test 2: Get table schema", total=1)
            result2 = await test_get_table_schema(client)
            results.append(("get_table_schema", result2 is not None))
            progress.update(task2, completed=1)

            # Test 3: Simple query
            task3 = progress.add_task("Test 3: Query database", total=1)
            result3 = await test_query_database(client)
            results.append(("query_database", result3 is not None))
            progress.update(task3, completed=1)

            # Test 4: List S3
            task4 = progress.add_task("Test 4: List S3 files", total=1)
            result4 = await test_list_s3_files(client)
            results.append(("list_s3_files", result4 is not None))
            progress.update(task4, completed=1)

            # Test 5: Complex query
            task5 = progress.add_task("Test 5: Complex query", total=1)
            result5 = await test_complex_query(client)
            results.append(("complex_query", result5 is not None))
            progress.update(task5, completed=1)

        # Summary
        console.print("\n" + "=" * 80 + "\n")
        console.print(Panel.fit("Test Summary", style="bold green"))

        summary_table = Table(title="Test Results", show_header=True)
        summary_table.add_column("Test", style="cyan", width=30)
        summary_table.add_column("Status", style="white", width=15)

        for test_name, success in results:
            summary_table.add_row(
                test_name, "[green]✅ PASS[/green]" if success else "[red]❌ FAIL[/red]"
            )

        console.print(summary_table)

        success_count = sum(1 for _, success in results if success)
        console.print(f"\n[bold]Passed: {success_count}/{len(results)}[/bold]")

        if success_count == len(results):
            console.print("[bold green]✅ All tests passed![/bold green]")
        else:
            console.print(
                f"[bold yellow]⚠️  {len(results) - success_count} test(s) failed[/bold yellow]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        console.print(traceback.format_exc())
    finally:
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
