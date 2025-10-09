#!/usr/bin/env python3
"""
Direct Synthesis Test Script
Tests the synthesis system without MCP server overhead
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from dotenv import load_dotenv

# Load environment
load_dotenv()

console = Console()


async def test_simple_query():
    """Test a simple SQL query request"""
    console.print(Panel.fit(
        "Test 1: Simple SQL Query Generation",
        style="bold blue"
    ))

    request = """
    Generate a SQL query to find the top 10 players by total points scored.
    Assume we have a table called 'player_game_stats' with columns:
    - player_id (INTEGER)
    - player_name (VARCHAR)
    - points (INTEGER)
    - game_date (DATE)
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running synthesis...", total=None)
        result = await synthesize_with_mcp_context(
            user_input=request,
            query_type="sql_optimization",
            enable_ollama_verification=False
        )
        progress.update(task, completed=True)

    # Display results
    console.print("\n[bold green]Results:[/bold green]")

    # Create results table
    table = Table(title="Synthesis Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Status", str(result.get('status')))
    table.add_row("Total Cost", f"${result.get('total_cost', 0):.6f}")
    table.add_row("Execution Time", f"{result.get('execution_time_seconds', 0):.2f}s")
    table.add_row("Models Used", ", ".join(result.get('models_used', [])))

    console.print(table)

    # Show DeepSeek result
    if result.get('deepseek_result'):
        ds = result['deepseek_result']
        console.print("\n[bold yellow]DeepSeek Solution:[/bold yellow]")
        response_text = ds.get('response', 'No response')[:500]
        console.print(Panel(response_text + ("..." if len(ds.get('response', '')) > 500 else ""),
                           title="DeepSeek Response (truncated)"))

    # Show Claude synthesis
    if result.get('claude_synthesis'):
        cs = result['claude_synthesis']
        console.print("\n[bold cyan]Claude Synthesis:[/bold cyan]")
        response_text = cs.get('response', 'No response')[:500]
        console.print(Panel(response_text + ("..." if len(cs.get('response', '')) > 500 else ""),
                           title="Claude Response (truncated)"))

    return result


async def test_code_debugging():
    """Test code debugging functionality"""
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit(
        "Test 2: Code Debugging",
        style="bold blue"
    ))

    buggy_code = """
def calculate_player_average(stats):
    total_points = sum([game['points'] for game in stats])
    return total_points / len(stats)  # Bug: Division by zero if empty

# Usage
player_stats = []
avg = calculate_player_average(player_stats)  # This will crash
"""

    request = f"""
    Debug this Python code:

    {buggy_code}

    The error is: ZeroDivisionError: division by zero

    Expected behavior: Should handle empty list gracefully and return 0 or None.
    """

    model = DeepSeekModel()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Debugging code...", total=None)
        result = await model.debug_code(
            code=buggy_code,
            error_message="ZeroDivisionError: division by zero",
            expected_behavior="Should handle empty list gracefully"
        )
        progress.update(task, completed=True)

    console.print("\n[bold green]Debug Result:[/bold green]")
    console.print(Panel(result.get('response', 'No response'), title="Fixed Code"))
    console.print(f"Cost: ${result.get('cost', 0):.6f}")

    return result


async def test_statistical_analysis():
    """Test statistical analysis"""
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit(
        "Test 3: Statistical Analysis",
        style="bold blue"
    ))

    request = """
    Analyze the relationship between:
    1. Player age
    2. Points per game
    3. Games played per season

    What statistical tests would be appropriate to determine:
    - If age affects scoring ability
    - If there's a correlation between age and games played
    - The optimal age range for peak performance
    """

    model = DeepSeekModel()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing statistics...", total=None)
        result = await model.analyze_statistics(
            data_description="Player age, points per game, games played",
            statistical_question="Correlation between age and performance"
        )
        progress.update(task, completed=True)

    console.print("\n[bold green]Analysis:[/bold green]")
    console.print(Panel(result.get('response', 'No response'),
                       title="Statistical Analysis"))
    console.print(f"Cost: ${result.get('cost', 0):.6f}")

    return result


async def test_sql_optimization():
    """Test SQL query optimization"""
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit(
        "Test 4: SQL Optimization",
        style="bold blue"
    ))

    slow_query = """
    SELECT
        p.player_name,
        COUNT(*) as games_played,
        AVG(gs.points) as avg_points,
        MAX(gs.points) as max_points
    FROM players p
    JOIN player_game_stats gs ON p.player_id = gs.player_id
    WHERE gs.season = 2023
    GROUP BY p.player_name
    ORDER BY avg_points DESC
    """

    model = DeepSeekModel()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Optimizing SQL...", total=None)
        result = await model.optimize_sql(
            sql_query=slow_query,
            table_stats={
                "players": {"row_count": 5000, "has_index_on": ["player_id"]},
                "player_game_stats": {"row_count": 500000, "has_index_on": ["player_id", "season"]}
            }
        )
        progress.update(task, completed=True)

    console.print("\n[bold green]Optimized Query:[/bold green]")
    console.print(Panel(result.get('response', 'No response'),
                       title="SQL Optimization"))
    console.print(f"Cost: ${result.get('cost', 0):.6f}")

    return result


async def test_full_workflow():
    """Test complete synthesis workflow with context"""
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit(
        "Test 5: Full Synthesis Workflow",
        style="bold blue"
    ))

    request = """
    I need to analyze which NBA teams have the best home court advantage.

    Requirements:
    1. Calculate win percentage at home vs away for each team
    2. Identify top 5 teams with biggest home advantage
    3. Provide SQL query and statistical analysis
    4. Include data visualization suggestions
    """

    context = {
        "tables": ["teams", "games", "team_stats"],
        "schemas": {
            "games": {
                "game_id": "INTEGER",
                "home_team_id": "INTEGER",
                "away_team_id": "INTEGER",
                "home_score": "INTEGER",
                "away_score": "INTEGER",
                "game_date": "DATE"
            },
            "teams": {
                "team_id": "INTEGER",
                "team_name": "VARCHAR",
                "city": "VARCHAR"
            }
        }
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running full synthesis...", total=None)
        result = await synthesize_with_mcp_context(
            user_input=request,
            query_type="statistical_analysis",
            enable_ollama_verification=False
        )
        progress.update(task, completed=True)

    # Display comprehensive results
    console.print("\n[bold green]Complete Results:[/bold green]\n")

    # Metrics table
    table = Table(title="Synthesis Metrics", show_header=True)
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="magenta")

    table.add_row("Status", "✅" if result.get('status') == 'success' else "❌")
    table.add_row("Total Cost", f"${result.get('total_cost', 0):.6f}")
    table.add_row("Execution Time", f"{result.get('execution_time_seconds', 0):.2f}s")
    table.add_row("Models Used", ", ".join(result.get('models_used', [])))

    if result.get('deepseek_result'):
        ds = result['deepseek_result']
        table.add_row("DeepSeek Tokens", f"{ds.get('tokens_used', 0):,}")
        table.add_row("DeepSeek Cost", f"${ds.get('cost', 0):.6f}")

    if result.get('claude_synthesis'):
        cl = result['claude_synthesis']
        table.add_row("Claude Tokens", f"{cl.get('tokens_used', 0):,}")
        table.add_row("Claude Cost", f"${cl.get('cost', 0):.6f}")

    console.print(table)

    # Show final synthesis
    if result.get('final_explanation'):
        console.print("\n[bold cyan]Final Solution:[/bold cyan]")
        explanation_text = result['final_explanation'][:1000]
        md = Markdown(explanation_text + ("\n\n...(truncated)" if len(result['final_explanation']) > 1000 else ""))
        console.print(Panel(md, title="Synthesized Solution"))

    return result


async def main():
    """Run all tests"""
    console.print(Panel.fit(
        "NBA MCP Synthesis - Direct Testing Suite\n" +
        "Testing synthesis system without MCP server",
        style="bold white on blue"
    ))

    results = []

    try:
        # Run all tests
        results.append(await test_simple_query())
        results.append(await test_code_debugging())
        results.append(await test_statistical_analysis())
        results.append(await test_sql_optimization())
        results.append(await test_full_workflow())

        # Summary
        console.print("\n" + "="*80 + "\n")
        console.print(Panel.fit("Test Summary", style="bold green"))

        total_cost = sum(r.get('total_cost', r.get('cost', 0)) for r in results)
        total_time = sum(r.get('execution_time_seconds', r.get('execution_time', 0)) for r in results)
        success_count = sum(1 for r in results if r.get('status') == 'success' or r.get('success', False))

        summary_table = Table(title="Overall Results")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("Tests Run", str(len(results)))
        summary_table.add_row("Successful", str(success_count))
        summary_table.add_row("Failed", str(len(results) - success_count))
        summary_table.add_row("Total Cost", f"${total_cost:.6f}")
        summary_table.add_row("Total Time", f"{total_time:.2f}s")
        summary_table.add_row("Avg Cost/Test", f"${total_cost/len(results):.6f}")

        console.print(summary_table)

        if success_count == len(results):
            console.print("\n[bold green]✅ All tests passed![/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️  {len(results) - success_count} test(s) failed[/bold yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())