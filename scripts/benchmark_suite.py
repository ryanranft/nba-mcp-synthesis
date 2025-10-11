#!/usr/bin/env python3
"""
Performance Benchmarking Suite
Detailed performance metrics for FastMCP server

Usage:
    python scripts/benchmark_suite.py
"""

import sys
import asyncio
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.fastmcp_lifespan import nba_lifespan
from mcp_server.tools.params import QueryDatabaseParams


@dataclass
class BenchmarkResult:
    """Result from a benchmark test"""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    operations_per_sec: float
    success_count: int
    failure_count: int
    timestamp: str


class BenchmarkSuite:
    """Performance benchmark coordinator"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    async def benchmark_query(
        self,
        rds_connector,
        query: str,
        iterations: int = 100,
        name: str = "Query Benchmark"
    ) -> BenchmarkResult:
        """Benchmark a database query"""

        print(f"\n{'=' * 60}")
        print(f"Benchmark: {name}")
        print(f"Iterations: {iterations}")
        print(f"Query: {query[:60]}...")
        print(f"{'=' * 60}")

        times: List[float] = []
        success_count = 0
        failure_count = 0

        for i in range(iterations):
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{iterations}", end="\r")

            start = time.perf_counter()
            try:
                await rds_connector.execute_query(query)
                success_count += 1
            except Exception as e:
                print(f"\nError on iteration {i + 1}: {e}")
                failure_count += 1
            end = time.perf_counter()

            times.append(end - start)

        print(f"\nProgress: {iterations}/{iterations} - Complete!")

        # Calculate statistics
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_sec = iterations / total_time if total_time > 0 else 0.0

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            operations_per_sec=ops_per_sec,
            success_count=success_count,
            failure_count=failure_count,
            timestamp=datetime.now().isoformat()
        )

        # Print results
        print(f"\n📊 Results:")
        print(f"  Total time:    {total_time:.3f}s")
        print(f"  Average time:  {avg_time:.4f}s")
        print(f"  Min time:      {min_time:.4f}s")
        print(f"  Max time:      {max_time:.4f}s")
        print(f"  Median time:   {median_time:.4f}s")
        print(f"  Std deviation: {std_dev:.4f}s")
        print(f"  Ops/sec:       {ops_per_sec:.2f}")
        print(f"  Success:       {success_count}/{iterations}")
        print(f"  Failures:      {failure_count}/{iterations}")

        self.results.append(result)
        return result

    async def benchmark_concurrent_queries(
        self,
        rds_connector,
        query: str,
        concurrent_count: int = 10,
        iterations: int = 5,
        name: str = "Concurrent Query Benchmark"
    ) -> BenchmarkResult:
        """Benchmark concurrent database queries"""

        print(f"\n{'=' * 60}")
        print(f"Benchmark: {name}")
        print(f"Concurrent queries: {concurrent_count}")
        print(f"Iterations: {iterations}")
        print(f"Total queries: {concurrent_count * iterations}")
        print(f"{'=' * 60}")

        times: List[float] = []
        success_count = 0
        failure_count = 0

        for i in range(iterations):
            print(f"Iteration {i + 1}/{iterations}...")

            start = time.perf_counter()

            # Create concurrent tasks
            tasks = [
                rds_connector.execute_query(query)
                for _ in range(concurrent_count)
            ]

            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end = time.perf_counter()
            times.append(end - start)

            # Count successes/failures
            for result in results:
                if isinstance(result, Exception):
                    failure_count += 1
                else:
                    success_count += 1

        # Calculate statistics
        total_queries = concurrent_count * iterations
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_sec = total_queries / total_time if total_time > 0 else 0.0

        result = BenchmarkResult(
            name=name,
            iterations=total_queries,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            operations_per_sec=ops_per_sec,
            success_count=success_count,
            failure_count=failure_count,
            timestamp=datetime.now().isoformat()
        )

        # Print results
        print(f"\n📊 Results:")
        print(f"  Total time:    {total_time:.3f}s")
        print(f"  Avg batch time: {avg_time:.4f}s")
        print(f"  Min batch time: {min_time:.4f}s")
        print(f"  Max batch time: {max_time:.4f}s")
        print(f"  Queries/sec:   {ops_per_sec:.2f}")
        print(f"  Success:       {success_count}/{total_queries}")
        print(f"  Failures:      {failure_count}/{total_queries}")

        self.results.append(result)
        return result

    def save_results(self, output_file: Path):
        """Save benchmark results to JSON"""

        data = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks": len(self.results),
            "results": [asdict(r) for r in self.results]
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

    def generate_summary(self) -> str:
        """Generate text summary of benchmarks"""

        lines = [
            "\n" + "=" * 60,
            "📊 BENCHMARK SUMMARY",
            "=" * 60,
            f"\nTotal benchmarks: {len(self.results)}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n" + "-" * 60
        ]

        for i, result in enumerate(self.results, 1):
            lines.extend([
                f"\n{i}. {result.name}",
                f"   Iterations: {result.iterations}",
                f"   Avg time: {result.avg_time:.4f}s",
                f"   Ops/sec: {result.operations_per_sec:.2f}",
                f"   Success rate: {result.success_count}/{result.iterations}"
            ])

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


async def main():
    """Run benchmark suite"""

    print("\n🏃 FastMCP Performance Benchmark Suite\n")

    # Create benchmark suite
    suite = BenchmarkSuite()

    # Mock app for lifespan
    class MockApp:
        pass

    app = MockApp()

    try:
        async with nba_lifespan(app) as context:
            rds_connector = context["rds_connector"]

            print("✅ Database connected")

            # Benchmark 1: Simple SELECT query
            await suite.benchmark_query(
                rds_connector,
                "SELECT 1 as test",
                iterations=100,
                name="Simple SELECT"
            )

            # Benchmark 2: Table listing query
            await suite.benchmark_query(
                rds_connector,
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                LIMIT 10
                """,
                iterations=50,
                name="List Tables (LIMIT 10)"
            )

            # Benchmark 3: Schema query
            await suite.benchmark_query(
                rds_connector,
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                LIMIT 20
                """,
                iterations=50,
                name="Schema Query (LIMIT 20)"
            )

            # Benchmark 4: Concurrent queries
            await suite.benchmark_concurrent_queries(
                rds_connector,
                "SELECT 1 as test",
                concurrent_count=10,
                iterations=10,
                name="Concurrent Queries (10x10)"
            )

            # Save results
            output_dir = Path("./benchmark_results")
            output_file = output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            suite.save_results(output_file)

            # Print summary
            print(suite.generate_summary())

            print("\n✅ Benchmark suite completed successfully!")
            return 0

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)