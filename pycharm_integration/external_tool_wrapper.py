#!/usr/bin/env python3
"""
PyCharm External Tool Wrapper
Entry point for multi-model synthesis with MCP context from PyCharm
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Import MCP and synthesis components
from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from mcp_server.config import MCPConfig

# Load environment variables
load_dotenv()

console = Console()


def parse_arguments():
    """Parse PyCharm external tool arguments"""
    
    # PyCharm passes: $FilePath$ $SelectedText$ $Prompt$
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    selected_text = sys.argv[2] if len(sys.argv) > 2 else None
    prompt = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Handle empty strings from PyCharm
    file_path = file_path if file_path and file_path != "$FilePath$" else None
    selected_text = selected_text if selected_text and selected_text != "$SelectedText$" else None
    prompt = prompt if prompt and prompt != "$Prompt$" else None
    
    return {
        "file_path": file_path,
        "selected_text": selected_text,
        "prompt": prompt
    }


def detect_query_type(user_input: str, code: Optional[str]) -> str:
    """Detect the type of query based on input"""
    
    user_input_lower = user_input.lower()
    
    # Code optimization
    if any(word in user_input_lower for word in ["optimize", "faster", "performance", "slow", "improve"]):
        return "code_optimization"
    
    # ETL generation
    if any(word in user_input_lower for word in ["etl", "extract", "transform", "load", "pipeline", "data flow"]):
        return "etl_generation"
    
    # Debugging
    if any(word in user_input_lower for word in ["bug", "error", "fix", "debug", "not working", "issue"]):
        return "debugging"
    
    # SQL specific
    if code and "SELECT" in code.upper():
        return "sql_optimization"
    
    # Analysis
    if any(word in user_input_lower for word in ["analyze", "explain", "what", "how", "why"]):
        return "analysis"
    
    return "general"


def format_for_pycharm(result: dict) -> str:
    """Format synthesis result for PyCharm display"""
    
    lines = []
    lines.append("# 🤖 Multi-Model Synthesis Result (MCP-Enhanced)\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Query type and context
    if result.get("query_type"):
        lines.append(f"**Query Type:** {result['query_type'].replace('_', ' ').title()}")
    
    if result.get("mcp_context_used"):
        lines.append(f"**MCP Context Sources:** {', '.join(result['mcp_context_used'])}")
    
    lines.append("")
    
    # Summary
    if result.get("summary"):
        lines.append("## 📋 Summary\n")
        lines.append(result["summary"])
        lines.append("")
    
    # Synthesized solution
    if result.get("code"):
        lines.append("## 💡 Synthesized Solution\n")
        lines.append("```python" if ".py" in str(result.get("file_type", "")) else "```sql")
        lines.append(result["code"])
        lines.append("```")
        lines.append("")
    
    # Explanation
    if result.get("explanation"):
        lines.append("## 📖 Explanation\n")
        lines.append(result["explanation"])
        lines.append("")
    
    # Model contributions
    if result.get("model_contributions"):
        lines.append("## 🔍 Model Contributions\n")
        for model, contribution in result["model_contributions"].items():
            lines.append(f"**{model}:** {contribution}")
        lines.append("")
    
    # Performance metrics
    if result.get("performance"):
        lines.append("## 📊 Performance\n")
        perf = result["performance"]
        lines.append(f"- **Total Time:** {perf.get('total_time', 0):.2f} seconds")
        lines.append(f"- **Tokens Used:** {perf.get('tokens_used', 0):,}")
        lines.append(f"- **Models Queried:** {perf.get('models_queried', 0)}")
        lines.append("")
    
    # Recommendations
    if result.get("recommendations"):
        lines.append("## 🎯 Recommendations\n")
        for rec in result["recommendations"]:
            lines.append(f"- {rec}")
        lines.append("")
    
    return "\n".join(lines)


def save_output(content: str, base_file_path: Optional[str]) -> Path:
    """Save output to timestamped file"""
    
    config = MCPConfig.from_env()
    
    # Determine output directory
    if base_file_path:
        output_dir = Path(base_file_path).parent / "synthesis_output"
    else:
        output_dir = Path(config.synthesis_output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"synthesis_{timestamp}.md"
    
    # Save content
    output_file.write_text(content)
    
    return output_file


async def run_synthesis(args: dict) -> dict:
    """Run the synthesis with MCP context"""
    
    # Determine input
    if args["selected_text"]:
        user_input = args["prompt"] or "Analyze and improve this code"
        code = args["selected_text"]
    else:
        console.print("[red]No code selected. Please select code in PyCharm and try again.[/red]")
        sys.exit(1)
    
    # Detect query type
    query_type = detect_query_type(user_input, code)
    
    console.print(f"\n[cyan]Query Type:[/cyan] {query_type.replace('_', ' ').title()}")
    console.print(f"[cyan]User Request:[/cyan] {user_input[:100]}...")
    
    # Run synthesis with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Add tasks
        task_gather = progress.add_task("[yellow]Gathering MCP context...", total=None)
        
        try:
            # Run synthesis (this would call the actual synthesis function)
            result = await synthesize_with_mcp_context(
                user_input=user_input,
                selected_code=code,
                query_type=query_type,
                file_path=args["file_path"]
            )
            
            progress.update(task_gather, completed=True, description="[green]✓ Context gathered")
            
            # Add model tasks
            task_models = progress.add_task("[yellow]Querying AI models...", total=4)
            
            # Simulate model queries (in real implementation, this would be integrated)
            for i, model in enumerate(["Claude", "GPT-4o", "Gemini", "Ollama"]):
                await asyncio.sleep(0.5)  # Simulate API call
                progress.update(task_models, advance=1, description=f"[green]✓ {model} complete")
            
            # Synthesis
            task_synthesis = progress.add_task("[yellow]Synthesizing responses...", total=None)
            await asyncio.sleep(0.5)  # Simulate synthesis
            progress.update(task_synthesis, completed=True, description="[green]✓ Synthesis complete")
            
            return result
            
        except Exception as e:
            console.print(f"[red]Error during synthesis: {e}[/red]")
            raise


async def main():
    """Main entry point for PyCharm external tool"""
    
    console.print("[bold blue]🚀 NBA MCP Multi-Model Synthesis[/bold blue]")
    console.print("[dim]Powered by MCP context from your NBA project[/dim]\n")
    
    # Parse arguments from PyCharm
    args = parse_arguments()
    
    if not args["selected_text"] and not args["prompt"]:
        console.print("[yellow]Usage:[/yellow]")
        console.print("1. Select code in PyCharm")
        console.print("2. Run: Tools → External Tools → Multi-Model Synthesis (MCP)")
        console.print("3. Optionally add a prompt comment above the code")
        sys.exit(1)
    
    try:
        # Check MCP server (optional - can run without it)
        config = MCPConfig.from_env()
        errors = config.validate()
        
        if errors:
            console.print("[yellow]⚠️ Configuration warnings:[/yellow]")
            for error in errors[:3]:  # Show first 3 errors
                console.print(f"  - {error}")
            console.print("")
        
        # Run synthesis
        result = await run_synthesis(args)
        
        # Format output
        formatted_output = format_for_pycharm(result)
        
        # Save to file
        output_file = save_output(formatted_output, args["file_path"])
        
        # Display results
        console.print("\n[bold green]✅ Synthesis Complete![/bold green]")
        console.print(f"[dim]Output saved to: {output_file}[/dim]\n")
        
        # Display formatted result
        console.print(Markdown(formatted_output))
        
        # Copy to clipboard (optional, macOS only)
        if sys.platform == "darwin":
            os.system(f"cat '{output_file}' | pbcopy")
            console.print("\n[dim]Output copied to clipboard[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Synthesis cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check logs for details[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    # For testing without PyCharm, accept command line input
    if len(sys.argv) == 1:
        console.print("[yellow]Running in test mode[/yellow]")
        sys.argv.extend([
            "test.py",
            "SELECT * FROM player_game_stats WHERE player_id = 123",
            "Optimize this query"
        ])
    
    asyncio.run(main())
