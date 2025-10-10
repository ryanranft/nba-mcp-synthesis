#!/usr/bin/env python3
"""
Load Testing Framework
Tests system performance under concurrent load with various scenarios
"""

import asyncio
import time
import sys
import os
import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, asdict
import psutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.mcp_client import MCPClient
from dotenv import load_dotenv

# Load environment
load_dotenv()


@dataclass
class LoadTestResult:
    """Individual load test result"""
    test_name: str
    request_id: int
    start_time: float
    end_time: float
    duration: float
    status: str
    error: str = None
    cost: float = 0.0
    tokens_used: int = 0


@dataclass
class LoadTestMetrics:
    """Aggregated load test metrics"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    requests_per_second: float

    # Response times
    min_response_time: float
    max_response_time: float
    mean_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float

    # Costs
    total_cost: float
    mean_cost_per_request: float

    # Resource utilization
    peak_cpu_percent: float
    peak_memory_mb: float

    # Error rate
    error_rate: float


class LoadTester:
    """Load testing framework for NBA MCP Synthesis system"""

    def __init__(self, mcp_server_url: str = "http://localhost:3000"):
        self.mcp_server_url = mcp_server_url
        self.results: List[LoadTestResult] = []
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.monitoring_task = None

    async def _monitor_resources(self, interval: float = 0.5):
        """Monitor CPU and memory usage during tests"""
        process = psutil.Process()

        while True:
            try:
                cpu = process.cpu_percent(interval=0.1)
                memory = process.memory_info().rss / 1024 / 1024  # MB

                self.cpu_samples.append(cpu)
                self.memory_samples.append(memory)

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Warning: Resource monitoring error: {e}")
                break

    async def _run_single_request(
        self,
        test_name: str,
        request_id: int,
        task_func: Callable,
        *args,
        **kwargs
    ) -> LoadTestResult:
        """Run a single request and capture metrics"""
        start_time = time.time()
        status = "success"
        error = None
        cost = 0.0
        tokens_used = 0

        try:
            result = await task_func(*args, **kwargs)

            # Extract metrics from result
            if isinstance(result, dict):
                if result.get('status') != 'success':
                    status = "partial_failure"
                cost = result.get('total_cost', 0.0)
                tokens_used = result.get('total_tokens', 0)

        except Exception as e:
            status = "failed"
            error = str(e)

        end_time = time.time()
        duration = end_time - start_time

        return LoadTestResult(
            test_name=test_name,
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            status=status,
            error=error,
            cost=cost,
            tokens_used=tokens_used
        )

    async def run_concurrent_load(
        self,
        test_name: str,
        task_func: Callable,
        num_concurrent: int,
        task_args: List = None,
        task_kwargs: Dict = None
    ) -> List[LoadTestResult]:
        """Run concurrent requests"""
        print(f"\n{'='*80}")
        print(f"Load Test: {test_name}")
        print(f"Concurrent Users: {num_concurrent}")
        print(f"{'='*80}\n")

        # Start resource monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_resources())

        # Prepare tasks
        tasks = []
        for i in range(num_concurrent):
            args = task_args or []
            kwargs = task_kwargs or {}

            task = self._run_single_request(
                test_name,
                i + 1,
                task_func,
                *args,
                **kwargs
            )
            tasks.append(task)

        # Run all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=False)
        total_duration = time.time() - start_time

        # Stop resource monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # Store results
        self.results.extend(results)

        # Print progress
        successful = sum(1 for r in results if r.status == "success")
        print(f"✅ Completed: {successful}/{num_concurrent} successful")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"⚡ Throughput: {num_concurrent/total_duration:.2f} requests/second")

        return results

    def calculate_metrics(self, test_name: str = None) -> LoadTestMetrics:
        """Calculate aggregated metrics from results"""
        # Filter results if test_name specified
        results = self.results
        if test_name:
            results = [r for r in results if r.test_name == test_name]

        if not results:
            raise ValueError("No results to calculate metrics from")

        # Basic counts
        total_requests = len(results)
        successful = sum(1 for r in results if r.status == "success")
        failed = total_requests - successful

        # Durations
        durations = [r.duration for r in results]
        total_duration = max(r.end_time for r in results) - min(r.start_time for r in results)
        rps = total_requests / total_duration if total_duration > 0 else 0

        # Response time percentiles
        sorted_durations = sorted(durations)
        p95_index = int(len(sorted_durations) * 0.95)
        p99_index = int(len(sorted_durations) * 0.99)

        # Costs
        costs = [r.cost for r in results if r.cost > 0]
        total_cost = sum(costs)
        mean_cost = total_cost / total_requests if total_requests > 0 else 0

        # Resource utilization
        peak_cpu = max(self.cpu_samples) if self.cpu_samples else 0
        peak_memory = max(self.memory_samples) if self.memory_samples else 0

        # Error rate
        error_rate = failed / total_requests if total_requests > 0 else 0

        return LoadTestMetrics(
            test_name=test_name or "all_tests",
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_duration=total_duration,
            requests_per_second=rps,
            min_response_time=min(durations),
            max_response_time=max(durations),
            mean_response_time=statistics.mean(durations),
            median_response_time=statistics.median(durations),
            p95_response_time=sorted_durations[p95_index] if sorted_durations else 0,
            p99_response_time=sorted_durations[p99_index] if sorted_durations else 0,
            total_cost=total_cost,
            mean_cost_per_request=mean_cost,
            peak_cpu_percent=peak_cpu,
            peak_memory_mb=peak_memory,
            error_rate=error_rate
        )

    def print_metrics(self, metrics: LoadTestMetrics):
        """Print metrics in formatted table"""
        print(f"\n{'='*80}")
        print(f"Load Test Metrics: {metrics.test_name}")
        print(f"{'='*80}\n")

        # Requests
        print("📊 Request Summary")
        print(f"  Total Requests:      {metrics.total_requests}")
        print(f"  Successful:          {metrics.successful_requests} ({(1-metrics.error_rate)*100:.1f}%)")
        print(f"  Failed:              {metrics.failed_requests} ({metrics.error_rate*100:.1f}%)")
        print(f"  Throughput:          {metrics.requests_per_second:.2f} req/s")
        print()

        # Response Times
        print("⏱️  Response Times (seconds)")
        print(f"  Min:                 {metrics.min_response_time:.3f}s")
        print(f"  Max:                 {metrics.max_response_time:.3f}s")
        print(f"  Mean:                {metrics.mean_response_time:.3f}s")
        print(f"  Median (p50):        {metrics.median_response_time:.3f}s")
        print(f"  p95:                 {metrics.p95_response_time:.3f}s")
        print(f"  p99:                 {metrics.p99_response_time:.3f}s")
        print()

        # Costs
        print("💰 Cost Analysis")
        print(f"  Total Cost:          ${metrics.total_cost:.6f}")
        print(f"  Cost per Request:    ${metrics.mean_cost_per_request:.6f}")
        print(f"  Cost per 1000 req:   ${metrics.mean_cost_per_request * 1000:.2f}")
        print()

        # Resources
        print("🖥️  Resource Utilization")
        print(f"  Peak CPU:            {metrics.peak_cpu_percent:.1f}%")
        print(f"  Peak Memory:         {metrics.peak_memory_mb:.1f} MB")
        print()

    def save_results(self, output_file: str):
        """Save detailed results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "metrics": asdict(self.calculate_metrics()) if self.results else None
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"📁 Results saved to: {output_file}")


# Test Scenarios

async def scenario_mcp_database_query(mcp_server_url: str):
    """Scenario: MCP database query"""
    client = MCPClient(server_url=mcp_server_url)

    try:
        await client.connect()
        result = await client.call_tool("query_database", {
            "sql": "SELECT COUNT(*) FROM games LIMIT 1"
        })
        await client.disconnect()

        return {
            "status": "success" if result.get('success') else "failed",
            "total_cost": 0,  # MCP calls are free
            "total_tokens": 0
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "total_cost": 0
        }


async def scenario_simple_synthesis(mcp_server_url: str):
    """Scenario: Simple synthesis request"""
    request = "Calculate the sum of numbers 1 to 10"

    result = await synthesize_with_mcp_context(
        user_input=request,
        query_type="general_analysis",
        enable_ollama_verification=False,
        mcp_server_url=mcp_server_url
    )

    return result


async def scenario_sql_generation(mcp_server_url: str):
    """Scenario: SQL query generation"""
    request = "Generate a SQL query to find players with more than 1000 points"

    result = await synthesize_with_mcp_context(
        user_input=request,
        query_type="sql_optimization",
        enable_ollama_verification=False,
        mcp_server_url=mcp_server_url
    )

    return result


async def run_load_tests():
    """Run comprehensive load test suite"""
    print("="*80)
    print("NBA MCP Synthesis - Load Testing Framework")
    print("="*80)

    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    tester = LoadTester(mcp_server_url)

    # Test 1: Light load (1 concurrent user baseline)
    print("\n🧪 Test 1: Baseline (1 concurrent user)")
    await tester.run_concurrent_load(
        test_name="baseline_simple_synthesis",
        task_func=scenario_simple_synthesis,
        num_concurrent=1,
        task_args=[mcp_server_url]
    )

    # Test 2: Moderate load (5 concurrent users)
    print("\n🧪 Test 2: Moderate Load (5 concurrent users)")
    await tester.run_concurrent_load(
        test_name="moderate_simple_synthesis",
        task_func=scenario_simple_synthesis,
        num_concurrent=5,
        task_args=[mcp_server_url]
    )

    # Test 3: High load (10 concurrent users)
    print("\n🧪 Test 3: High Load (10 concurrent users)")
    await tester.run_concurrent_load(
        test_name="high_simple_synthesis",
        task_func=scenario_simple_synthesis,
        num_concurrent=10,
        task_args=[mcp_server_url]
    )

    # Test 4: MCP-only load (25 concurrent database queries)
    print("\n🧪 Test 4: MCP Database Load (25 concurrent queries)")
    await tester.run_concurrent_load(
        test_name="mcp_database_load",
        task_func=scenario_mcp_database_query,
        num_concurrent=25,
        task_args=[mcp_server_url]
    )

    # Test 5: Stress test (25 concurrent synthesis requests)
    print("\n🧪 Test 5: Stress Test (25 concurrent synthesis)")
    await tester.run_concurrent_load(
        test_name="stress_synthesis",
        task_func=scenario_simple_synthesis,
        num_concurrent=25,
        task_args=[mcp_server_url]
    )

    # Calculate and print overall metrics
    print("\n" + "="*80)
    print("OVERALL TEST RESULTS")
    print("="*80)

    metrics = tester.calculate_metrics()
    tester.print_metrics(metrics)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"load_test_results_{timestamp}.json"
    tester.save_results(output_file)

    # Performance assertions
    print("\n" + "="*80)
    print("PERFORMANCE VALIDATION")
    print("="*80 + "\n")

    passed = True

    # Check p95 response time
    if metrics.p95_response_time > 30:
        print(f"❌ FAIL: p95 response time ({metrics.p95_response_time:.2f}s) > 30s")
        passed = False
    else:
        print(f"✅ PASS: p95 response time ({metrics.p95_response_time:.2f}s) < 30s")

    # Check error rate
    if metrics.error_rate > 0.05:  # 5% error rate threshold
        print(f"❌ FAIL: Error rate ({metrics.error_rate*100:.1f}%) > 5%")
        passed = False
    else:
        print(f"✅ PASS: Error rate ({metrics.error_rate*100:.1f}%) < 5%")

    # Check cost per 1000 requests
    cost_per_1000 = metrics.mean_cost_per_request * 1000
    if cost_per_1000 > 15:
        print(f"❌ FAIL: Cost per 1000 requests (${cost_per_1000:.2f}) > $15")
        passed = False
    else:
        print(f"✅ PASS: Cost per 1000 requests (${cost_per_1000:.2f}) < $15")

    # Check throughput
    if metrics.requests_per_second < 0.5:
        print(f"⚠️  WARN: Low throughput ({metrics.requests_per_second:.2f} req/s)")
    else:
        print(f"✅ PASS: Throughput ({metrics.requests_per_second:.2f} req/s) acceptable")

    print("\n" + "="*80)
    if passed:
        print("✅ ALL PERFORMANCE CHECKS PASSED")
    else:
        print("❌ SOME PERFORMANCE CHECKS FAILED")
    print("="*80 + "\n")

    return passed


if __name__ == "__main__":
    success = asyncio.run(run_load_tests())
    sys.exit(0 if success else 1)
