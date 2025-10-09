#!/usr/bin/env python3
"""
Ollama-Primary Synthesis Testing
Test synthesis with Ollama as primary model to avoid rate limits and reduce costs
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.models import OllamaModel, ClaudeModel
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()


async def test_ollama_primary_synthesis(user_input: str, code: str = None):
    """
    Test Ollama-primary synthesis workflow

    Workflow:
    1. Ollama generates initial solution (FREE, local)
    2. Claude synthesizes and verifies (minimal API cost)

    Args:
        user_input: User's request
        code: Optional code snippet
    """
    console.print(Panel.fit("Ollama-Primary Synthesis Test", style="bold blue"))

    results = {
        "ollama": {},
        "claude": {},
        "total_cost": 0.0,
        "execution_time": 0.0
    }

    # Step 1: Query Ollama (PRIMARY - FREE)
    console.print("\n[1/2] Querying Ollama (qwen2.5-coder:32b) - Local, FREE", style="cyan")

    ollama = OllamaModel()

    if not ollama.is_available():
        console.print("[red]❌ Ollama not available. Please start Ollama service.[/red]")
        return None

    # Build prompt
    prompt = user_input
    if code:
        prompt += f"\n\nCode to analyze:\n```\n{code}\n```"

    ollama_result = await ollama.query(
        prompt=prompt,
        temperature=0.3,  # Slightly higher for creativity
        max_tokens=4000
    )

    if ollama_result.get("success"):
        results["ollama"] = ollama_result
        console.print(f"[green]✓ Ollama completed: {ollama_result.get('tokens_used', 0)} tokens, $0.00 (local)[/green]")
        console.print(f"\nOllama Response Preview:\n{ollama_result.get('response', '')[:200]}...")
    else:
        console.print(f"[red]✗ Ollama failed: {ollama_result.get('error')}[/red]")
        return None

    # Step 2: Claude synthesis (SECONDARY - minimal cost)
    console.print("\n[2/2] Synthesizing with Claude (verification only)", style="cyan")

    claude = ClaudeModel()

    synthesis_result = await claude.synthesize(
        deepseek_result=ollama_result.get('response', ''),
        original_request=user_input,
        context_summary="Ollama-primary workflow",
        include_verification=True
    )

    if synthesis_result.get("success"):
        results["claude"] = synthesis_result
        results["total_cost"] = synthesis_result.get("cost", 0)
        console.print(f"[green]✓ Claude completed: {synthesis_result.get('tokens_used', 0)} tokens, ${synthesis_result.get('cost', 0):.4f}[/green]")
    else:
        console.print(f"[yellow]⚠ Claude synthesis failed: {synthesis_result.get('error')}[/yellow]")

    # Display results
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit("Final Results", style="bold green"))

    # Cost comparison table
    table = Table(title="Cost Comparison", show_header=True)
    table.add_column("Workflow", style="cyan")
    table.add_column("Models Used", style="white")
    table.add_column("Total Cost", style="green")
    table.add_column("Savings", style="yellow")

    # Old workflow (DeepSeek + Claude)
    old_cost = 0.012850  # From previous test
    table.add_row(
        "Old (DeepSeek+Claude)",
        "DeepSeek V3, Claude 3.7",
        f"${old_cost:.4f}",
        "—"
    )

    # New workflow (Ollama + Claude)
    new_cost = results["total_cost"]
    savings = ((old_cost - new_cost) / old_cost * 100) if old_cost > 0 else 0
    table.add_row(
        "New (Ollama+Claude)",
        "qwen2.5-coder:32b, Claude 3.7",
        f"${new_cost:.4f}",
        f"{savings:.1f}% saved"
    )

    console.print(table)

    # Display solutions
    console.print("\n" + "="*80 + "\n")
    console.print(Panel.fit("Ollama Solution", style="bold cyan"))
    console.print(results["ollama"].get("response", "No response"))

    if results["claude"].get("response"):
        console.print("\n" + "="*80 + "\n")
        console.print(Panel.fit("Claude Verification", style="bold magenta"))
        console.print(results["claude"].get("response", "No response"))

    console.print("\n" + "="*80 + "\n")
    console.print(f"[bold green]✅ Total Cost: ${results['total_cost']:.4f}[/bold green]")
    console.print(f"[bold yellow]💰 Savings vs DeepSeek workflow: {savings:.1f}%[/bold yellow]")

    return results


async def run_comparison_tests():
    """Run multiple test cases to demonstrate Ollama-primary workflow"""

    console.print(Panel.fit(
        "Ollama-Primary Synthesis Testing\n" +
        "Comparing: Ollama (local, free) + Claude (minimal cost) vs DeepSeek + Claude",
        style="bold white on blue"
    ))

    # Test 1: Simple SQL query
    console.print("\n\n" + "="*80 + "\n")
    console.print(Panel.fit("Test 1: Simple SQL Query", style="bold blue"))

    await test_ollama_primary_synthesis(
        user_input="Write an optimized SQL query to find the top 10 players by total points scored in the player_game_stats table",
        code=None
    )

    await asyncio.sleep(2)

    # Test 2: Code debugging
    console.print("\n\n" + "="*80 + "\n")
    console.print(Panel.fit("Test 2: Code Debugging", style="bold blue"))

    await test_ollama_primary_synthesis(
        user_input="Fix this bug and explain the issue",
        code="""def calculate_player_average(stats):
    total_points = sum([game['points'] for game in stats])
    return total_points / len(stats)

player_stats = []
avg = calculate_player_average(player_stats)  # ZeroDivisionError
"""
    )

    await asyncio.sleep(2)

    # Test 3: Code generation
    console.print("\n\n" + "="*80 + "\n")
    console.print(Panel.fit("Test 3: Python Function", style="bold blue"))

    await test_ollama_primary_synthesis(
        user_input="Write a Python function to calculate win percentage for NBA teams, including handling edge cases",
        code=None
    )


async def main():
    """Main entry point"""
    try:
        await run_comparison_tests()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
