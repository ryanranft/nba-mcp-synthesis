#!/usr/bin/env python3
"""
Performance Benchmarking Suite
Establishes baseline performance metrics and tracks trends over time
"""

import asyncio
import time
import sys
import os
import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import psutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.mcp_client import MCPClient
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from mcp_server.connectors.rds_connector import RDSConnector
from mcp_server.connectors.s3_connector import S3Connector
from dotenv import load_dotenv

# Load environment
load_dotenv()


@dataclass
class BenchmarkResult:
    """Individual benchmark result"""

    benchmark_name: str
    category: str
    duration: float
    cost: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    success: bool = True
    error: str = None
    metadata: Dict = None


class PerformanceBenchmark:
    """Performance benchmarking system"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")

    async def benchmark(
        self, name: str, category: str, func, *args, **kwargs
    ) -> BenchmarkResult:
        """Run a single benchmark"""
        print(f"  Running: {name}...", end=" ", flush=True)

        start_time = time.time()
        success = True
        error = None
        cost = 0.0
        tokens_input = 0
        tokens_output = 0
        metadata = {}

        try:
            result = await func(*args, **kwargs)

            # Extract metrics if dict returned
            if isinstance(result, dict):
                cost = result.get("total_cost", 0.0)
                tokens_input = result.get("tokens_input", 0)
                tokens_output = result.get("tokens_output", 0)
                metadata = result.get("metadata", {})
                success = result.get("status") == "success"

        except Exception as e:
            success = False
            error = str(e)

        duration = time.time() - start_time

        result = BenchmarkResult(
            benchmark_name=name,
            category=category,
            duration=duration,
            cost=cost,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            success=success,
            error=error,
            metadata=metadata,
        )

        self.results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} ({duration:.2f}s)")

        return result

    # ===== Database Benchmarks =====

    async def benchmark_database_connection(self) -> Dict:
        """Benchmark database connection time"""
        connector = RDSConnector()
        await connector.connect()
        await connector.disconnect()
        return {"status": "success"}

    async def benchmark_database_simple_query(self) -> Dict:
        """Benchmark simple database query"""
        connector = RDSConnector()
        await connector.connect()

        try:
            result = await connector.execute_query("SELECT 1 AS test")
            return {"status": "success"}
        finally:
            await connector.disconnect()

    async def benchmark_database_table_list(self) -> Dict:
        """Benchmark listing database tables"""
        connector = RDSConnector()
        await connector.connect()

        try:
            tables = await connector.list_tables()
            return {"status": "success", "metadata": {"table_count": len(tables)}}
        finally:
            await connector.disconnect()

    async def benchmark_database_schema_query(self) -> Dict:
        """Benchmark schema retrieval"""
        connector = RDSConnector()
        await connector.connect()

        try:
            tables = await connector.list_tables()
            if tables:
                schema = await connector.get_table_schema(tables[0])
                return {"status": "success", "metadata": {"table": tables[0]}}
        finally:
            await connector.disconnect()

        return {"status": "success"}

    # ===== S3 Benchmarks =====

    async def benchmark_s3_list_files(self) -> Dict:
        """Benchmark S3 file listing"""
        connector = S3Connector()

        files = await connector.list_files(prefix="", max_keys=10)
        return {"status": "success", "metadata": {"files_found": len(files)}}

    # ===== AI Model Benchmarks =====

    async def benchmark_deepseek_simple_query(self) -> Dict:
        """Benchmark DeepSeek simple query"""
        model = DeepSeekModel()

        result = await model.query(
            prompt="What is 2 + 2?", temperature=0.3, max_tokens=100
        )

        return {
            "status": "success",
            "total_cost": result.get("cost", 0),
            "tokens_input": result.get("tokens_input", 0),
            "tokens_output": result.get("tokens_output", 0),
        }

    async def benchmark_deepseek_code_generation(self) -> Dict:
        """Benchmark DeepSeek code generation"""
        model = DeepSeekModel()

        result = await model.query(
            prompt="Write a Python function to calculate factorial",
            temperature=0.3,
            max_tokens=500,
        )

        return {
            "status": "success",
            "total_cost": result.get("cost", 0),
            "tokens_input": result.get("tokens_input", 0),
            "tokens_output": result.get("tokens_output", 0),
        }

    async def benchmark_claude_simple_query(self) -> Dict:
        """Benchmark Claude simple query"""
        model = ClaudeModel()

        result = await model.query(
            prompt="What is the capital of France?", temperature=0.3, max_tokens=100
        )

        return {
            "status": "success",
            "total_cost": result.get("cost", 0),
            "tokens_input": result.get("tokens_input", 0),
            "tokens_output": result.get("tokens_output", 0),
        }

    async def benchmark_claude_synthesis(self) -> Dict:
        """Benchmark Claude synthesis task"""
        model = ClaudeModel()

        prompt = """
        Primary answer: The factorial of 5 is 120.

        Please synthesize this answer into a clear explanation.
        """

        result = await model.query(prompt=prompt, temperature=0.1, max_tokens=300)

        return {
            "status": "success",
            "total_cost": result.get("cost", 0),
            "tokens_input": result.get("tokens_input", 0),
            "tokens_output": result.get("tokens_output", 0),
        }

    # ===== MCP Benchmarks =====

    async def benchmark_mcp_connection(self) -> Dict:
        """Benchmark MCP connection time"""
        client = MCPClient(server_url=self.mcp_server_url)

        await client.connect()
        await client.disconnect()

        return {"status": "success"}

    async def benchmark_mcp_tool_list(self) -> Dict:
        """Benchmark MCP tool listing"""
        client = MCPClient(server_url=self.mcp_server_url)

        await client.connect()
        try:
            tools = await client.list_available_tools()
            return {"status": "success", "metadata": {"tool_count": len(tools)}}
        finally:
            await client.disconnect()

    async def benchmark_mcp_database_query(self) -> Dict:
        """Benchmark MCP database query"""
        client = MCPClient(server_url=self.mcp_server_url)

        await client.connect()
        try:
            result = await client.call_tool(
                "query_database", {"sql": "SELECT COUNT(*) FROM games LIMIT 1"}
            )
            return {"status": "success" if result.get("success") else "failed"}
        finally:
            await client.disconnect()

    # ===== Full Synthesis Benchmarks =====

    async def benchmark_simple_synthesis(self) -> Dict:
        """Benchmark simple synthesis"""
        result = await synthesize_with_mcp_context(
            user_input="Calculate the sum of 1 to 10",
            query_type="general_analysis",
            enable_ollama_verification=False,
            mcp_server_url=self.mcp_server_url,
        )

        return result

    async def benchmark_sql_generation(self) -> Dict:
        """Benchmark SQL generation synthesis"""
        result = await synthesize_with_mcp_context(
            user_input="Generate SQL to find top 5 players by points",
            query_type="sql_optimization",
            enable_ollama_verification=False,
            mcp_server_url=self.mcp_server_url,
        )

        return result

    async def benchmark_code_debugging(self) -> Dict:
        """Benchmark code debugging synthesis"""
        code = """
def factorial(n):
    result = 1
    for i in range(n):  # Bug: should be range(1, n+1)
        result *= i
    return result
"""

        result = await synthesize_with_mcp_context(
            user_input=f"Debug this factorial function:\n{code}",
            query_type="code_debugging",
            enable_ollama_verification=False,
            mcp_server_url=self.mcp_server_url,
        )

        return result

    async def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("=" * 80)
        print("NBA MCP Synthesis - Performance Benchmark Suite")
        print("=" * 80)
        print()

        # Database Benchmarks
        print("📊 Database Benchmarks")
        print("-" * 80)
        await self.benchmark(
            "DB Connection", "database", self.benchmark_database_connection
        )
        await self.benchmark(
            "DB Simple Query", "database", self.benchmark_database_simple_query
        )
        await self.benchmark(
            "DB Table List", "database", self.benchmark_database_table_list
        )
        await self.benchmark(
            "DB Schema Query", "database", self.benchmark_database_schema_query
        )
        print()

        # S3 Benchmarks
        print("📁 S3 Benchmarks")
        print("-" * 80)
        await self.benchmark("S3 List Files", "s3", self.benchmark_s3_list_files)
        print()

        # AI Model Benchmarks
        print("🤖 AI Model Benchmarks")
        print("-" * 80)
        await self.benchmark(
            "DeepSeek Simple Query", "ai_model", self.benchmark_deepseek_simple_query
        )
        await self.benchmark(
            "DeepSeek Code Gen", "ai_model", self.benchmark_deepseek_code_generation
        )
        await self.benchmark(
            "Claude Simple Query", "ai_model", self.benchmark_claude_simple_query
        )
        await self.benchmark(
            "Claude Synthesis", "ai_model", self.benchmark_claude_synthesis
        )
        print()

        # MCP Benchmarks
        print("🔌 MCP Benchmarks")
        print("-" * 80)
        await self.benchmark("MCP Connection", "mcp", self.benchmark_mcp_connection)
        await self.benchmark("MCP Tool List", "mcp", self.benchmark_mcp_tool_list)
        await self.benchmark("MCP DB Query", "mcp", self.benchmark_mcp_database_query)
        print()

        # Full Synthesis Benchmarks
        print("⚡ Full Synthesis Benchmarks")
        print("-" * 80)
        await self.benchmark(
            "Simple Synthesis", "synthesis", self.benchmark_simple_synthesis
        )
        await self.benchmark(
            "SQL Generation", "synthesis", self.benchmark_sql_generation
        )
        await self.benchmark(
            "Code Debugging", "synthesis", self.benchmark_code_debugging
        )
        print()

    def generate_report(self) -> Dict:
        """Generate comprehensive benchmark report"""
        # Group results by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)

        # Calculate category stats
        category_stats = {}
        for category, results in by_category.items():
            durations = [r.duration for r in results if r.success]
            costs = [r.cost for r in results if r.cost > 0]
            successful = sum(1 for r in results if r.success)

            category_stats[category] = {
                "total_benchmarks": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "mean_duration": statistics.mean(durations) if durations else 0,
                "median_duration": statistics.median(durations) if durations else 0,
                "total_cost": sum(costs),
                "mean_cost": statistics.mean(costs) if costs else 0,
            }

        # Overall stats
        all_durations = [r.duration for r in self.results if r.success]
        all_costs = [r.cost for r in self.results if r.cost > 0]

        overall_stats = {
            "total_benchmarks": len(self.results),
            "successful": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "total_duration": sum(all_durations),
            "mean_duration": statistics.mean(all_durations) if all_durations else 0,
            "median_duration": statistics.median(all_durations) if all_durations else 0,
            "total_cost": sum(all_costs),
            "mean_cost": statistics.mean(all_costs) if all_costs else 0,
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "overall": overall_stats,
            "by_category": category_stats,
            "detailed_results": [asdict(r) for r in self.results],
        }

    def print_report(self):
        """Print formatted benchmark report"""
        report = self.generate_report()

        print("=" * 80)
        print("BENCHMARK REPORT")
        print("=" * 80)
        print()

        # Overall stats
        overall = report["overall"]
        print("📈 Overall Statistics")
        print(f"  Total Benchmarks:    {overall['total_benchmarks']}")
        print(f"  Successful:          {overall['successful']}")
        print(f"  Failed:              {overall['failed']}")
        print(f"  Total Duration:      {overall['total_duration']:.2f}s")
        print(f"  Mean Duration:       {overall['mean_duration']:.3f}s")
        print(f"  Median Duration:     {overall['median_duration']:.3f}s")
        print(f"  Total Cost:          ${overall['total_cost']:.6f}")
        print(f"  Mean Cost:           ${overall['mean_cost']:.6f}")
        print()

        # Category breakdown
        print("📊 Category Breakdown")
        print("-" * 80)
        for category, stats in report["by_category"].items():
            print(f"\n  {category.upper()}")
            print(
                f"    Benchmarks:        {stats['total_benchmarks']} ({stats['successful']} successful)"
            )
            print(f"    Mean Duration:     {stats['mean_duration']:.3f}s")
            print(f"    Total Cost:        ${stats['total_cost']:.6f}")
        print()

        # Performance targets
        print("=" * 80)
        print("PERFORMANCE TARGETS")
        print("=" * 80)
        print()

        passed = True

        # Target 1: Synthesis < 30s (p95)
        synthesis_durations = [
            r.duration for r in self.results if r.category == "synthesis" and r.success
        ]
        if synthesis_durations:
            sorted_durations = sorted(synthesis_durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p95_synthesis = sorted_durations[p95_index]

            if p95_synthesis < 30:
                print(f"✅ Synthesis p95 < 30s: {p95_synthesis:.2f}s")
            else:
                print(f"❌ Synthesis p95 > 30s: {p95_synthesis:.2f}s")
                passed = False

        # Target 2: Mean cost < $0.015
        synthesis_costs = [
            r.cost for r in self.results if r.category == "synthesis" and r.cost > 0
        ]
        if synthesis_costs:
            mean_synthesis_cost = statistics.mean(synthesis_costs)

            if mean_synthesis_cost < 0.015:
                print(f"✅ Mean synthesis cost < $0.015: ${mean_synthesis_cost:.6f}")
            else:
                print(f"❌ Mean synthesis cost > $0.015: ${mean_synthesis_cost:.6f}")
                passed = False

        # Target 3: Database query < 1s
        db_durations = [
            r.duration for r in self.results if r.category == "database" and r.success
        ]
        if db_durations:
            mean_db_time = statistics.mean(db_durations)

            if mean_db_time < 1:
                print(f"✅ Mean DB query < 1s: {mean_db_time:.3f}s")
            else:
                print(f"⚠️  Mean DB query > 1s: {mean_db_time:.3f}s")

        print()
        print("=" * 80)
        if passed:
            print("✅ ALL PERFORMANCE TARGETS MET")
        else:
            print("❌ SOME PERFORMANCE TARGETS NOT MET")
        print("=" * 80)
        print()

        return passed

    def save_report(self, output_file: str):
        """Save benchmark report to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📁 Benchmark report saved to: {output_file}")

    def save_markdown_report(self, output_file: str):
        """Save benchmark report as markdown"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()
        overall = report["overall"]

        md = []
        md.append(f"# Benchmark Report")
        md.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        md.append("## Overall Statistics\n")
        md.append(f"- **Total Benchmarks:** {overall['total_benchmarks']}")
        md.append(f"- **Successful:** {overall['successful']}")
        md.append(f"- **Failed:** {overall['failed']}")
        md.append(f"- **Total Duration:** {overall['total_duration']:.2f}s")
        md.append(f"- **Mean Duration:** {overall['mean_duration']:.3f}s")
        md.append(f"- **Median Duration:** {overall['median_duration']:.3f}s")
        md.append(f"- **Total Cost:** ${overall['total_cost']:.6f}")
        md.append(f"- **Mean Cost:** ${overall['mean_cost']:.6f}\n")

        md.append("## Category Breakdown\n")
        for category, stats in report["by_category"].items():
            md.append(f"### {category.upper()}\n")
            md.append(
                f"- Benchmarks: {stats['total_benchmarks']} ({stats['successful']} successful)"
            )
            md.append(f"- Mean Duration: {stats['mean_duration']:.3f}s")
            md.append(f"- Total Cost: ${stats['total_cost']:.6f}\n")

        md.append("## Detailed Results\n")
        md.append("| Benchmark | Category | Duration | Cost | Status |")
        md.append("|-----------|----------|----------|------|--------|")

        for result in self.results:
            status = "✅" if result.success else "❌"
            md.append(
                f"| {result.benchmark_name} | {result.category} | "
                f"{result.duration:.3f}s | ${result.cost:.6f} | {status} |"
            )

        with open(output_path, "w") as f:
            f.write("\n".join(md))

        print(f"📁 Markdown report saved to: {output_file}")


async def main():
    """Run benchmark suite"""
    benchmark = PerformanceBenchmark()

    # Run all benchmarks
    await benchmark.run_all_benchmarks()

    # Generate and print report
    passed = benchmark.print_report()

    # Save reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark.save_report(f"benchmark_results_{timestamp}.json")
    benchmark.save_markdown_report(f"benchmark_results_{timestamp}.md")

    return passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
