#!/usr/bin/env python3
"""
Quick Start Demo for NBA MCP Synthesis System
Demonstrates the multi-model synthesis workflow with DeepSeek + Claude
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import env helper
from mcp_server.env_helper import get_hierarchical_env

from synthesis import synthesize_with_mcp_context
from synthesis.models import DeepSeekModel, ClaudeModel, OllamaModel

console = Console()


async def demo_sql_optimization():
    """Demo 1: SQL Query Optimization"""
    console.print("\n[bold blue]Demo 1: SQL Query Optimization[/bold blue]")
    console.print("[dim]Optimizing a player stats query...[/dim]\n")

    user_input = "Optimize this query for better performance on a large table"
    sql_query = """
    SELECT *
    FROM player_game_stats
    WHERE player_id = 123
    AND season = '2023-24'
    ORDER BY game_date DESC
    """

    console.print(f"[yellow]Original Query:[/yellow]\n{sql_query}")

    result = await synthesize_with_mcp_context(
        user_input=user_input,
        selected_code=sql_query,
        query_type="sql_optimization"
    )

    if result['status'] == 'success':
        console.print(f"\n[green]✓ Optimization Complete![/green]")
        console.print(f"[dim]Total Cost: ${result['total_cost']:.4f}[/dim]")
        console.print(f"[dim]Execution Time: {result['execution_time']:.2f}s[/dim]\n")

        # Display optimized query
        if result.get('final_code'):
            console.print(Panel(
                result['final_code'],
                title="Optimized Query",
                border_style="green"
            ))

        # Display explanation
        if result.get('final_explanation'):
            console.print("\n[bold]Explanation:[/bold]")
            console.print(Markdown(result['final_explanation'][:500] + "..."))

    else:
        console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")


async def demo_statistical_analysis():
    """Demo 2: Statistical Analysis"""
    console.print("\n[bold blue]Demo 2: Statistical Analysis[/bold blue]")
    console.print("[dim]Calculating correlation between player metrics...[/dim]\n")

    user_input = """
    Calculate the correlation between player points per game and assists per game.
    Use the player_stats table for the 2023-24 season.
    """

    result = await synthesize_with_mcp_context(
        user_input=user_input,
        query_type="statistical_analysis"
    )

    if result['status'] == 'success':
        console.print(f"\n[green]✓ Analysis Complete![/green]")
        console.print(f"[dim]Cost: ${result['total_cost']:.4f} | Time: {result['execution_time']:.2f}s[/dim]\n")

        if result.get('final_code'):
            console.print(Panel(
                result['final_code'][:400] + "...",
                title="Statistical Code",
                border_style="blue"
            ))
    else:
        console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")


async def demo_quick_synthesis():
    """Demo 3: Quick Synthesis (Simplified API)"""
    console.print("\n[bold blue]Demo 3: Quick Synthesis[/bold blue]")
    console.print("[dim]Using simplified API for quick tasks...[/dim]\n")

    from synthesis.multi_model_synthesis import quick_synthesis

    result = await quick_synthesis(
        "Write a function to calculate Player Efficiency Rating (PER)"
    )

    if result['status'] == 'success':
        console.print(f"\n[green]✓ Synthesis Complete![/green]")
        console.print(f"[dim]Cost: ${result['total_cost']:.4f}[/dim]\n")

        if result.get('final_code'):
            console.print(Panel(
                result['final_code'][:300] + "...",
                title="Generated Function",
                border_style="cyan"
            ))
    else:
        console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")


async def test_model_connections():
    """Test individual model connections"""
    console.print("\n[bold blue]Testing Model Connections[/bold blue]\n")

    results = {}

    # Test DeepSeek
    try:
        console.print("[yellow]Testing DeepSeek...[/yellow]")
        deepseek = DeepSeekModel()
        result = await deepseek.query("Hello", temperature=0.3)
        if result.get('success'):
            console.print(f"  [green]✓ DeepSeek connected (Cost: ${result['cost']:.4f})[/green]")
            results['deepseek'] = True
        else:
            console.print(f"  [red]✗ DeepSeek failed: {result.get('error')}[/red]")
            results['deepseek'] = False
    except Exception as e:
        console.print(f"  [red]✗ DeepSeek error: {e}[/red]")
        results['deepseek'] = False

    # Test Claude
    try:
        console.print("[yellow]Testing Claude...[/yellow]")
        claude = ClaudeModel()
        result = await claude.synthesize(
            deepseek_result="Test result",
            original_request="Test",
            context_summary="Test context",
            include_verification=False
        )
        if result.get('success'):
            console.print(f"  [green]✓ Claude connected (Cost: ${result['cost']:.4f})[/green]")
            results['claude'] = True
        else:
            console.print(f"  [red]✗ Claude failed: {result.get('error')}[/red]")
            results['claude'] = False
    except Exception as e:
        console.print(f"  [red]✗ Claude error: {e}[/red]")
        results['claude'] = False

    # Test Ollama (optional)
    try:
        console.print("[yellow]Testing Ollama (optional)...[/yellow]")
        ollama = OllamaModel()
        if ollama.is_available():
            result = await ollama.quick_verify("print('test')")
            if result.get('success'):
                console.print(f"  [green]✓ Ollama connected (Local, $0)[/green]")
                results['ollama'] = True
            else:
                console.print(f"  [yellow]⚠ Ollama available but verification failed[/yellow]")
                results['ollama'] = False
        else:
            console.print(f"  [dim]⏭ Ollama not available (optional)[/dim]")
            results['ollama'] = None
    except Exception as e:
        console.print(f"  [dim]⏭ Ollama not available: {e}[/dim]")
        results['ollama'] = None

    return results


async def main():
    """Main demo function"""
    console.print(Panel(
        "[bold]NBA MCP Synthesis System - Quick Start Demo[/bold]\n"
        "[dim]Multi-Model AI with DeepSeek, Claude, and Ollama[/dim]",
        style="blue"
    ))

    # Check for required API keys
    missing_keys = []
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        missing_keys.append("DEEPSEEK_API_KEY")
    if not get_hierarchical_env("ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        missing_keys.append("ANTHROPIC_API_KEY")

    if missing_keys:
        console.print(f"\n[red]✗ Missing required API keys:[/red]")
        for key in missing_keys:
            console.print(f"  - {key}")
        console.print("\n[yellow]Please set these in your .env file[/yellow]")
        return

    # Test connections first
    console.print("\n[bold cyan]Step 1: Testing Model Connections[/bold cyan]")
    connections = await test_model_connections()

    if not connections.get('deepseek'):
        console.print("\n[red]✗ DeepSeek connection failed - cannot proceed[/red]")
        return

    if not connections.get('claude'):
        console.print("\n[yellow]⚠ Claude connection failed - synthesis will be limited[/yellow]")

    # Run demos
    console.print("\n[bold cyan]Step 2: Running Synthesis Demos[/bold cyan]")

    demos = [
        ("SQL Optimization", demo_sql_optimization),
        ("Statistical Analysis", demo_statistical_analysis),
        ("Quick Synthesis", demo_quick_synthesis)
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]✗ Demo '{name}' failed: {e}[/red]")

    # Summary
    console.print("\n" + "="*60)
    console.print(Panel(
        "[bold green]Quick Start Complete![/bold green]\n\n"
        "Next Steps:\n"
        "1. Check synthesis_output/ for saved results\n"
        "2. Review logs/ for detailed execution logs\n"
        "3. Try the PyCharm integration for live synthesis\n"
        "4. Explore synthesis/example_usage.py for more examples\n\n"
        "[dim]For full documentation, see synthesis/README.md[/dim]",
        style="green"
    ))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Exited by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()