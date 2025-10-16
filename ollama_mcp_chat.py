#!/usr/bin/env python3
"""
Interactive chat interface using Ollama with NBA MCP tools.
Use this if Cursor doesn't support Ollama directly.
"""

import asyncio
import sys
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

# Connect to Ollama
ollama = OpenAI(
    base_url="http://34.226.246.126:11434/v1",
    api_key="ollama"
)

class MCPOllamaChat:
    def __init__(self):
        self.conversation = []
        self.mcp_tools = []

    async def initialize(self):
        """Load MCP tools."""
        try:
            from mcp_server.fastmcp_server import mcp
            self.mcp_tools = await mcp.list_tools()
            console.print(f"✅ Loaded {len(self.mcp_tools)} MCP tools", style="green")
        except Exception as e:
            console.print(f"⚠️  Could not load MCP tools: {e}", style="yellow")

    def get_system_prompt(self):
        """Create system prompt with MCP tools context."""
        tool_list = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self.mcp_tools[:20]
        ])

        return f"""You are an AI assistant with access to {len(self.mcp_tools)} NBA data tools.

Available NBA MCP Tools (showing 20 of {len(self.mcp_tools)}):
{tool_list}
... and {len(self.mcp_tools) - 20} more tools.

When users ask about NBA data:
1. Mention which tool would be used
2. Explain what data you could retrieve
3. Provide helpful examples

Be conversational and helpful!"""

    async def chat(self, user_message):
        """Send message to Ollama with MCP context."""
        # Add user message
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        # Prepare messages with system context
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation
        ]

        # Get response from Ollama
        console.print("\n[cyan]🤖 Ollama (Qwen2.5-Coder 32B) is thinking...[/cyan]\n")

        try:
            response = ollama.chat.completions.create(
                model="qwen2.5-coder:32b",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True  # Enable streaming for better UX
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    console.print(content, end="")
                    full_response += content

            console.print("\n")

            # Add assistant response to conversation
            self.conversation.append({
                "role": "assistant",
                "content": full_response
            })

            return full_response

        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
            return None

    async def run(self):
        """Main chat loop."""
        console.clear()

        # Header
        console.print(Panel.fit(
            "[bold cyan]🤖 Ollama + NBA MCP Chat[/bold cyan]\n"
            "[dim]Type 'exit' to quit, 'tools' to list all MCP tools[/dim]",
            border_style="cyan"
        ))

        # Initialize
        await self.initialize()
        console.print()

        # Chat loop
        while True:
            try:
                # Get user input
                user_input = console.input("\n[bold green]You:[/bold green] ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                    break

                if user_input.lower() == 'tools':
                    console.print(f"\n[cyan]📋 Available MCP Tools ({len(self.mcp_tools)}):[/cyan]")
                    for i, tool in enumerate(self.mcp_tools, 1):
                        console.print(f"  {i}. [bold]{tool.name}[/bold]: {tool.description}")
                    continue

                if user_input.lower() == 'clear':
                    self.conversation = []
                    console.clear()
                    console.print("[cyan]💬 Conversation cleared![/cyan]")
                    continue

                # Chat with Ollama
                await self.chat(user_input)

            except KeyboardInterrupt:
                console.print("\n\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except Exception as e:
                console.print(f"\n[red]❌ Error: {e}[/red]\n")

async def main():
    """Entry point."""
    chat = MCPOllamaChat()
    await chat.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)




