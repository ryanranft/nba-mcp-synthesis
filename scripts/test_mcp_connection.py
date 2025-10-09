#!/usr/bin/env python3
"""
Test MCP Connection Script
Verifies MCP server is running and all connections work
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.config import MCPConfig
from mcp_server.connectors.rds_connector import RDSConnector
from mcp_server.connectors.s3_connector import S3Connector
from mcp_server.connectors.slack_notifier import SlackNotifier

# Load environment variables
load_dotenv()

console = Console()


async def test_rds_connection(config: MCPConfig) -> dict:
    """Test RDS PostgreSQL connection"""
    try:
        console.print("\n[yellow]Testing RDS PostgreSQL connection...[/yellow]")
        
        connector = RDSConnector(
            host=config.rds_host,
            port=config.rds_port,
            database=config.rds_database,
            username=config.rds_username,
            password=config.rds_password
        )
        
        # Test basic query
        result = await connector.execute_query("SELECT version()")
        
        if result["success"]:
            version = result["rows"][0]["version"] if result["rows"] else "Unknown"
            
            # Get table list
            tables = await connector.list_tables()
            
            return {
                "status": "✅ Connected",
                "details": f"PostgreSQL {version.split(',')[0]}",
                "tables": len(tables)
            }
        else:
            return {
                "status": "❌ Failed",
                "details": result.get("error", "Unknown error"),
                "tables": 0
            }
            
    except Exception as e:
        return {
            "status": "❌ Failed",
            "details": str(e),
            "tables": 0
        }


async def test_s3_connection(config: MCPConfig) -> dict:
    """Test S3 bucket connection"""
    try:
        console.print("\n[yellow]Testing S3 bucket connection...[/yellow]")
        
        connector = S3Connector(
            bucket_name=config.s3_bucket,
            region=config.s3_region
        )
        
        # Check connection
        connected = await connector.check_connection()
        
        if connected:
            # List some files
            result = await connector.list_files(max_keys=5)
            
            if result["success"]:
                return {
                    "status": "✅ Connected",
                    "details": f"Bucket: {config.s3_bucket}",
                    "files": result["file_count"]
                }
            else:
                return {
                    "status": "⚠️ Connected but error",
                    "details": result.get("error", "Unknown error"),
                    "files": 0
                }
        else:
            return {
                "status": "❌ Failed",
                "details": "Cannot access bucket",
                "files": 0
            }
            
    except Exception as e:
        return {
            "status": "❌ Failed",
            "details": str(e),
            "files": 0
        }


async def test_slack_connection(config: MCPConfig) -> dict:
    """Test Slack webhook (optional)"""
    if not config.slack_webhook_url:
        return {
            "status": "⏭️ Skipped",
            "details": "No webhook configured",
            "sent": False
        }
    
    try:
        console.print("\n[yellow]Testing Slack webhook...[/yellow]")
        
        notifier = SlackNotifier(
            webhook_url=config.slack_webhook_url
        )
        
        # Send test message
        message = {
            "text": "🔧 MCP Server Connection Test",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Testing MCP server connections..."
                    }
                }
            ]
        }
        
        success = await notifier.send_notification(message)
        
        if success:
            return {
                "status": "✅ Connected",
                "details": "Test message sent",
                "sent": True
            }
        else:
            return {
                "status": "⚠️ Failed to send",
                "details": "Check webhook URL",
                "sent": False
            }
            
    except Exception as e:
        return {
            "status": "❌ Failed",
            "details": str(e),
            "sent": False
        }


def test_project_paths(config: MCPConfig) -> dict:
    """Test project path configuration"""
    try:
        project_path = Path(config.project_root)
        
        if project_path.exists():
            # Count Python files
            py_files = list(project_path.rglob("*.py"))
            sql_files = list(project_path.rglob("*.sql"))
            
            return {
                "status": "✅ Found",
                "details": str(project_path),
                "files": f"{len(py_files)} .py, {len(sql_files)} .sql"
            }
        else:
            return {
                "status": "⚠️ Not Found",
                "details": f"Path does not exist: {project_path}",
                "files": "N/A"
            }
            
    except Exception as e:
        return {
            "status": "❌ Error",
            "details": str(e),
            "files": "N/A"
        }


def test_api_keys() -> dict:
    """Test if API keys are configured"""
    keys = {
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "Google": bool(os.getenv("GOOGLE_API_KEY")),
        "AWS": bool(os.getenv("AWS_ACCESS_KEY_ID"))
    }
    
    configured = sum(keys.values())
    total = len(keys)
    
    if configured == total:
        status = "✅ All configured"
    elif configured > 0:
        status = f"⚠️ {configured}/{total} configured"
    else:
        status = "❌ None configured"
    
    details = ", ".join([k for k, v in keys.items() if v])
    
    return {
        "status": status,
        "details": details or "No API keys",
        "count": f"{configured}/{total}"
    }


async def main():
    """Run all connection tests"""
    
    rprint("\n[bold blue]🔧 MCP Server Connection Test[/bold blue]")
    rprint("[dim]Testing all configured connections...[/dim]\n")
    
    # Load configuration
    config = MCPConfig.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        console.print("[red]Configuration errors found:[/red]")
        for error in errors:
            console.print(f"  ❌ {error}")
        console.print("\n[yellow]Some tests may fail due to missing configuration[/yellow]")
    
    # Run tests
    results = {}
    
    # Test API keys
    results["API Keys"] = test_api_keys()
    
    # Test project paths
    results["Project Path"] = test_project_paths(config)
    
    # Test RDS
    results["RDS Database"] = await test_rds_connection(config)
    
    # Test S3
    results["S3 Bucket"] = await test_s3_connection(config)
    
    # Test Slack
    results["Slack Webhook"] = await test_slack_connection(config)
    
    # Display results table
    console.print("\n[bold]Test Results:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Service", style="dim")
    table.add_column("Status")
    table.add_column("Details")
    table.add_column("Info")
    
    for service, result in results.items():
        # Get the info value and convert to string
        info_value = result.get("files", result.get("tables", result.get("count", "N/A")))
        info_str = str(info_value) if info_value is not None else "N/A"

        table.add_row(
            service,
            result["status"],
            result["details"],
            info_str
        )
    
    console.print(table)
    
    # Overall status
    all_success = all("✅" in r["status"] for r in results.values())
    any_failure = any("❌" in r["status"] for r in results.values())
    
    console.print()
    if all_success:
        rprint("[bold green]✅ All connections successful![/bold green]")
        rprint("\n[dim]Your MCP server is ready to start:[/dim]")
        rprint("  python -m mcp_server.server")
        return 0
    elif any_failure:
        rprint("[bold red]❌ Some connections failed[/bold red]")
        rprint("\n[dim]Please check your configuration in .env[/dim]")
        return 1
    else:
        rprint("[bold yellow]⚠️ Some connections need attention[/bold yellow]")
        rprint("\n[dim]Review the warnings above[/dim]")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
