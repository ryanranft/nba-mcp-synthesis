#!/usr/bin/env python3
"""
Performance Diagnostics for NBA MCP Synthesis System
Tests network latency, API response times, and identifies bottlenecks
"""

import asyncio
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
load_dotenv()


def test_internet_speed():
    """Test basic internet connectivity and latency"""
    console.print("\n[yellow]Testing Internet Connectivity...[/yellow]")

    results = {}
    test_urls = {
        "Google": "https://www.google.com",
        "GitHub": "https://github.com",
        "DeepSeek API": "https://api.deepseek.com",
        "Anthropic API": "https://api.anthropic.com",
    }

    for name, url in test_urls.items():
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            latency = (time.time() - start) * 1000  # Convert to ms

            results[name] = {
                "status": "✅" if response.status_code < 400 else "⚠️",
                "latency": f"{latency:.0f}ms",
                "code": response.status_code,
            }
        except requests.exceptions.Timeout:
            results[name] = {"status": "❌", "latency": "Timeout", "code": "N/A"}
        except Exception as e:
            results[name] = {"status": "❌", "latency": f"Error", "code": str(e)[:20]}

    # Display results
    table = Table(title="Network Connectivity Test")
    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("Latency")
    table.add_column("Notes")

    for name, result in results.items():
        latency = result["latency"]

        # Determine if latency is good/bad
        if isinstance(latency, str) and "ms" in latency:
            ms = int(latency.replace("ms", ""))
            if ms < 100:
                note = "[green]Excellent[/green]"
            elif ms < 300:
                note = "[yellow]Good[/yellow]"
            elif ms < 1000:
                note = "[yellow]Slow[/yellow]"
            else:
                note = "[red]Very Slow[/red]"
        else:
            note = "[red]Connection Issue[/red]"

        table.add_row(name, result["status"], result["latency"], note)

    console.print(table)

    return results


async def test_deepseek_api_speed():
    """Test DeepSeek API response time"""
    console.print("\n[yellow]Testing DeepSeek API Performance...[/yellow]")

    try:
        from synthesis.models import DeepSeekModel

        model = DeepSeekModel()

        # Test 1: Simple query
        start = time.time()
        result1 = await model.query("What is 2+2?", temperature=0.1, max_tokens=10)
        time1 = time.time() - start

        # Test 2: Medium query
        start = time.time()
        result2 = await model.query(
            "Optimize: SELECT * FROM table", temperature=0.2, max_tokens=500
        )
        time2 = time.time() - start

        table = Table(title="DeepSeek API Performance")
        table.add_column("Test", style="cyan")
        table.add_column("Time")
        table.add_column("Tokens")
        table.add_column("Cost")
        table.add_column("Assessment")

        # Analyze results
        def assess_time(t):
            if t < 2:
                return "[green]Excellent[/green]"
            elif t < 5:
                return "[yellow]Good[/yellow]"
            elif t < 15:
                return "[yellow]Slow (Network?)[/yellow]"
            else:
                return "[red]Very Slow (Check Network!)[/red]"

        if result1.get("success"):
            table.add_row(
                "Simple Query",
                f"{time1:.2f}s",
                str(result1.get("tokens_used", "N/A")),
                f"${result1.get('cost', 0):.6f}",
                assess_time(time1),
            )

        if result2.get("success"):
            table.add_row(
                "SQL Optimization",
                f"{time2:.2f}s",
                str(result2.get("tokens_used", "N/A")),
                f"${result2.get('cost', 0):.6f}",
                assess_time(time2),
            )

        console.print(table)

        return {"simple": time1, "medium": time2}

    except Exception as e:
        console.print(f"[red]DeepSeek test failed: {e}[/red]")
        return None


async def test_claude_api_speed():
    """Test Claude API response time"""
    console.print("\n[yellow]Testing Claude API Performance...[/yellow]")

    try:
        from synthesis.models import ClaudeModel

        model = ClaudeModel()

        # Simple synthesis test
        start = time.time()
        result = await model.synthesize(
            deepseek_result="The query is optimized",
            original_request="Optimize query",
            context_summary="Test",
            include_verification=False,
        )
        time_taken = time.time() - start

        table = Table(title="Claude API Performance")
        table.add_column("Test", style="cyan")
        table.add_column("Time")
        table.add_column("Tokens")
        table.add_column("Cost")
        table.add_column("Assessment")

        def assess_time(t):
            if t < 3:
                return "[green]Excellent[/green]"
            elif t < 10:
                return "[yellow]Good[/yellow]"
            elif t < 20:
                return "[yellow]Slow (Network?)[/yellow]"
            else:
                return "[red]Very Slow (Check Network!)[/red]"

        if result.get("success"):
            table.add_row(
                "Synthesis",
                f"{time_taken:.2f}s",
                str(result.get("tokens_used", "N/A")),
                f"${result.get('cost', 0):.6f}",
                assess_time(time_taken),
            )

        console.print(table)

        return time_taken

    except Exception as e:
        console.print(f"[red]Claude test failed: {e}[/red]")
        return None


def diagnose_bottleneck(network_results, deepseek_time, claude_time):
    """Diagnose where the bottleneck is"""
    console.print("\n[bold cyan]Diagnosis:[/bold cyan]\n")

    issues = []
    recommendations = []

    # Check network connectivity
    deepseek_latency = network_results.get("DeepSeek API", {}).get("latency", "0ms")
    anthropic_latency = network_results.get("Anthropic API", {}).get("latency", "0ms")

    if "Timeout" in str(deepseek_latency) or "Error" in str(deepseek_latency):
        issues.append("❌ Cannot reach DeepSeek API")
        recommendations.append("Check firewall/VPN settings")
        recommendations.append("Try a different network")
    elif "ms" in str(deepseek_latency):
        ms = int(deepseek_latency.replace("ms", ""))
        if ms > 500:
            issues.append(f"⚠️  High latency to DeepSeek API ({ms}ms)")
            recommendations.append("Network latency is causing slowdowns")
            recommendations.append("Consider using a VPN or different ISP")

    # Check API response times
    if deepseek_time and deepseek_time.get("simple", 0) > 10:
        issues.append(
            f"⚠️  DeepSeek API very slow ({deepseek_time['simple']:.1f}s for simple query)"
        )
        recommendations.append("This is likely a network issue, not your modem")
        recommendations.append("Try: Restart router, check bandwidth usage")

    if claude_time and claude_time > 20:
        issues.append(f"⚠️  Claude API very slow ({claude_time:.1f}s)")
        recommendations.append("Network bottleneck detected")

    # Display issues
    if issues:
        console.print("[yellow]Issues Found:[/yellow]")
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("[green]✅ No major issues detected![/green]")

    # Display recommendations
    if recommendations:
        console.print(f"\n[cyan]Recommendations:[/cyan]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"  {i}. {rec}")

    # Modem/Router diagnosis
    console.print(f"\n[bold]Is it your modem/router?[/bold]")

    google_latency = network_results.get("Google", {}).get("latency", "0ms")
    if "ms" in str(google_latency):
        google_ms = int(google_latency.replace("ms", ""))
        if google_ms < 100:
            console.print(
                "  [green]✅ Unlikely - your connection to Google is fast[/green]"
            )
            console.print(
                "  [dim]The slowdown is probably API server latency, not your modem[/dim]"
            )
        else:
            console.print(
                "  [yellow]⚠️  Possible - your general internet is slow[/yellow]"
            )
            console.print(
                "  [yellow]Try: Restart modem/router, check for ISP issues[/yellow]"
            )

    # Performance expectations
    console.print(f"\n[bold]Expected Performance:[/bold]")
    console.print("  • DeepSeek simple query: 1-5s (your network + API processing)")
    console.print("  • DeepSeek SQL optimization: 10-25s (complex reasoning)")
    console.print("  • Claude synthesis: 5-15s")
    console.print("  • Total synthesis: 15-40s")
    console.print(
        "\n  [dim]Note: 20-25s of this is actual AI processing, not network![/dim]"
    )


async def main():
    """Run all diagnostic tests"""
    console.print("[bold blue]🔍 NBA MCP Synthesis Performance Diagnostics[/bold blue]")
    console.print("[dim]Testing network connectivity and API performance...[/dim]")

    # Test 1: Network connectivity
    network_results = test_internet_speed()

    # Test 2: DeepSeek API
    deepseek_times = await test_deepseek_api_speed()

    # Test 3: Claude API
    claude_time = await test_claude_api_speed()

    # Diagnose bottleneck
    diagnose_bottleneck(network_results, deepseek_times, claude_time)

    console.print("\n[bold green]Diagnostic Complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
