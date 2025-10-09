#!/usr/bin/env python3
"""
PyCharm External Tool Integration for NBA MCP Synthesis
Allows triggering MCP workflows directly from PyCharm IDE
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from synthesis.models import OllamaModel, ClaudeModel, DeepSeekModel
from synthesis.mcp_client import MCPClient
from rich.console import Console
from rich.panel import Panel

console = Console()


class PyCharmMCPTool:
    """External tool interface for PyCharm integration"""

    def __init__(self):
        self.mcp_client = MCPClient()
        self.ollama = OllamaModel()
        self.claude = ClaudeModel()
        self.deepseek = DeepSeekModel()

    async def analyze_code(
        self,
        code: str,
        request: str,
        use_ollama_primary: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze code with MCP synthesis

        Args:
            code: Code to analyze
            request: What to do with the code
            use_ollama_primary: Use Ollama first to avoid rate limits
        """
        console.print(Panel.fit(f"MCP Analysis: {request}", style="bold blue"))

        # Get database context if needed
        context = await self._get_relevant_context(request)

        # Build full prompt
        prompt = f"{request}\n\nCode:\n```\n{code}\n```"
        if context:
            prompt += f"\n\nDatabase Context:\n{context}"

        # Use Ollama-primary workflow to avoid rate limits
        if use_ollama_primary and self.ollama.is_available():
            console.print("[cyan]Using Ollama-primary workflow (no rate limits)[/cyan]")

            ollama_result = await self.ollama.query(
                prompt=prompt,
                temperature=0.3,
                max_tokens=4000
            )

            if ollama_result.get("success"):
                # Optionally verify with Claude
                synthesis_result = await self.claude.synthesize(
                    deepseek_result=ollama_result.get('response', ''),
                    original_request=request,
                    context_summary=f"PyCharm code analysis",
                    include_verification=True
                )

                return {
                    "success": True,
                    "primary_analysis": ollama_result.get('response'),
                    "verification": synthesis_result.get('response'),
                    "cost": synthesis_result.get('cost', 0),
                    "workflow": "ollama-primary"
                }

        # Fallback to DeepSeek + Claude
        console.print("[yellow]Using DeepSeek + Claude workflow[/yellow]")

        deepseek_result = await self.deepseek.query(
            prompt=prompt,
            temperature=0.3,
            max_tokens=4000
        )

        if deepseek_result.get("success"):
            synthesis_result = await self.claude.synthesize(
                deepseek_result=deepseek_result.get('response', ''),
                original_request=request,
                context_summary=f"PyCharm code analysis",
                include_verification=True
            )

            return {
                "success": True,
                "primary_analysis": deepseek_result.get('response'),
                "verification": synthesis_result.get('response'),
                "cost": deepseek_result.get('cost', 0) + synthesis_result.get('cost', 0),
                "workflow": "deepseek-claude"
            }

        return {"success": False, "error": "All models failed"}

    async def generate_scraper(
        self,
        url: Optional[str] = None,
        description: Optional[str] = None,
        selected_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate or improve web scraper code

        Args:
            url: Target URL to scrape
            description: What data to extract
            selected_code: Existing scraper code to improve
        """
        console.print(Panel.fit("Web Scraper Generation", style="bold green"))

        if selected_code:
            prompt = f"""Improve this web scraper:

{selected_code}

{f'Target URL: {url}' if url else ''}
{f'Extract: {description}' if description else ''}

Provide:
1. Improved code with error handling
2. Pagination handling
3. Rate limiting
4. Data validation
5. NBA-specific optimizations if applicable
"""
        else:
            prompt = f"""Generate a robust web scraper for:

URL: {url}
Extract: {description}

Requirements:
1. Use requests + BeautifulSoup or Scrapy
2. Include error handling and retries
3. Handle pagination automatically
4. Add rate limiting (respect robots.txt)
5. Save to database if NBA data
6. Include data validation
7. Add logging

Provide complete, production-ready code.
"""

        # Use Ollama for scraper generation (faster, free)
        if self.ollama.is_available():
            result = await self.ollama.query(
                prompt=prompt,
                temperature=0.4,
                max_tokens=6000
            )

            return {
                "success": result.get("success"),
                "scraper_code": result.get("response"),
                "cost": 0,
                "workflow": "ollama"
            }

        # Fallback to DeepSeek
        result = await self.deepseek.query(
            prompt=prompt,
            temperature=0.4,
            max_tokens=6000
        )

        return {
            "success": result.get("success"),
            "scraper_code": result.get("response"),
            "cost": result.get("cost", 0),
            "workflow": "deepseek"
        }

    async def generate_sql_query(
        self,
        natural_language: str,
        table_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language

        Args:
            natural_language: Description of what to query
            table_hint: Optional table name hint
        """
        console.print(Panel.fit("SQL Query Generation", style="bold magenta"))

        # Get schema context
        if table_hint:
            schema = await self._get_table_schema(table_hint)
        else:
            # Get all tables
            tables = await self.mcp_client.list_tables()
            schema = f"Available tables: {', '.join(tables)}"

        prompt = f"""Generate an optimized SQL query for:

{natural_language}

Database Schema:
{schema}

Provide:
1. Complete SQL query
2. Explanation of what it does
3. Performance considerations
4. Any necessary indexes
"""

        # Use Ollama for SQL generation
        if self.ollama.is_available():
            result = await self.ollama.query(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000
            )

            return {
                "success": result.get("success"),
                "sql_query": result.get("response"),
                "cost": 0,
                "workflow": "ollama"
            }

        # Fallback
        result = await self.deepseek.query(
            prompt=prompt,
            temperature=0.2,
            max_tokens=2000
        )

        return {
            "success": result.get("success"),
            "sql_query": result.get("response"),
            "cost": result.get("cost", 0),
            "workflow": "deepseek"
        }

    async def execute_query_with_explanation(
        self,
        query: str
    ) -> Dict[str, Any]:
        """
        Execute SQL query and explain results

        Args:
            query: SQL query to execute
        """
        console.print(Panel.fit("Executing Query", style="bold cyan"))

        # Execute via MCP
        result = await self.mcp_client.execute_query(query)

        if not result.get("success"):
            return result

        # Get AI explanation of results
        prompt = f"""Explain these query results:

Query:
{query}

Results:
{json.dumps(result.get('results', [])[:10], indent=2)}

Provide:
1. Summary of findings
2. Key insights
3. Data quality notes
4. Recommendations
"""

        if self.ollama.is_available():
            explanation = await self.ollama.query(prompt=prompt, temperature=0.3)

            return {
                "success": True,
                "results": result.get("results"),
                "explanation": explanation.get("response"),
                "row_count": result.get("row_count"),
                "cost": 0
            }

        return result

    async def _get_relevant_context(self, request: str) -> str:
        """Get relevant database context based on request"""
        # Check if request mentions specific tables
        tables = ["players", "teams", "games", "box_score", "stats"]
        mentioned = [t for t in tables if t.lower() in request.lower()]

        if mentioned:
            schemas = []
            for table in mentioned[:2]:  # Limit to 2 tables
                schema = await self._get_table_schema(table)
                schemas.append(schema)
            return "\n\n".join(schemas)

        return ""

    async def _get_table_schema(self, table: str) -> str:
        """Get schema for a specific table"""
        try:
            result = await self.mcp_client.describe_table(table)
            if result.get("success"):
                return f"Table: {table}\n{json.dumps(result.get('schema'), indent=2)}"
        except:
            pass
        return ""


async def main():
    """Main entry point for PyCharm external tool"""
    import argparse

    parser = argparse.ArgumentParser(description="NBA MCP PyCharm Integration")
    parser.add_argument("action", choices=[
        "analyze",
        "scraper",
        "sql",
        "execute"
    ])
    parser.add_argument("--code", help="Code to analyze")
    parser.add_argument("--request", help="What to do")
    parser.add_argument("--url", help="URL for scraper")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--query", help="SQL query")
    parser.add_argument("--table", help="Table hint")
    parser.add_argument("--file", help="File containing code/query")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--no-ollama", action="store_true", help="Disable Ollama-primary")

    args = parser.parse_args()

    # Read from file if specified
    code = args.code
    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()

    tool = PyCharmMCPTool()
    result = None

    try:
        if args.action == "analyze":
            if not code or not args.request:
                console.print("[red]Error: --code and --request required[/red]")
                sys.exit(1)
            result = await tool.analyze_code(
                code=code,
                request=args.request,
                use_ollama_primary=not args.no_ollama
            )

        elif args.action == "scraper":
            result = await tool.generate_scraper(
                url=args.url,
                description=args.description,
                selected_code=code
            )

        elif args.action == "sql":
            if not args.request:
                console.print("[red]Error: --request required[/red]")
                sys.exit(1)
            result = await tool.generate_sql_query(
                natural_language=args.request,
                table_hint=args.table
            )

        elif args.action == "execute":
            if not args.query:
                console.print("[red]Error: --query required[/red]")
                sys.exit(1)
            result = await tool.execute_query_with_explanation(
                query=args.query
            )

        # Display result
        if result and result.get("success"):
            console.print("\n" + "="*80 + "\n")
            console.print(Panel.fit("Result", style="bold green"))

            if "primary_analysis" in result:
                console.print(result["primary_analysis"])
            elif "scraper_code" in result:
                console.print(result["scraper_code"])
            elif "sql_query" in result:
                console.print(result["sql_query"])
            elif "explanation" in result:
                console.print(f"Results: {result.get('row_count')} rows\n")
                console.print(result["explanation"])

            console.print(f"\n[green]Cost: ${result.get('cost', 0):.4f}[/green]")

            # Save to file if specified
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                console.print(f"[cyan]Saved to {args.output}[/cyan]")
        else:
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
