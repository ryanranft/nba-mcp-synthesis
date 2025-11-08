"""
Integration Tests for Agent 9

Tests performance optimization components integration.

Agent Covered:
- Agent 9: Performance & Scalability
  - Query optimization
  - Cache management
  - Distributed processing
  - Performance profiling
"""

import pytest
import pandas as pd
import numpy as np
import time


@pytest.mark.agent_9
class TestQueryOptimizationIntegration:
    """Test query optimizer integrates with system"""

    def test_query_optimizer_with_monitoring(self):
        """Test query optimizer integrates with monitoring"""
        from mcp_server.optimization.query_optimizer import QueryOptimizer
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        optimizer = QueryOptimizer(slow_query_threshold_ms=100.0)

        @profile
        def execute_tracked_query(query, execution_time):
            metrics = optimizer.track_query_execution(query, execution_time)
            return metrics

        # Execute queries
        execute_tracked_query("SELECT * FROM players WHERE id=1", 50.0)
        execute_tracked_query("SELECT * FROM players WHERE id=2", 150.0)  # Slow

        # Verify both systems tracked execution
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 2

        # Verify optimizer tracked queries
        slow_queries = optimizer.get_slow_queries(min_executions=1)
        assert len(slow_queries) == 1
        assert slow_queries[0].avg_time_ms >= 100.0

    def test_query_metrics_tracking(self):
        """Test query metrics are properly tracked"""
        from mcp_server.optimization.query_optimizer import QueryOptimizer

        optimizer = QueryOptimizer(track_metrics=True)

        # Execute same query multiple times
        query = "SELECT points FROM players WHERE player_id=1"
        for exec_time in [45.0, 50.0, 55.0, 60.0, 65.0]:
            optimizer.track_query_execution(query, exec_time)

        # Get statistics
        stats = optimizer.get_statistics()
        assert stats['total_tracked_queries'] >= 1
        assert stats['metrics_tracking'] is True


@pytest.mark.agent_9
class TestCacheIntegration:
    """Test cache manager integrates with system"""

    def test_cache_with_profiling(self, temp_output_dir):
        """Test cache operations are profiled"""
        from mcp_server.optimization.cache_manager import CacheManager
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        # Use memory cache (no Redis required)
        cache = CacheManager(redis_url=None)

        @profile
        def cached_operation(key, value):
            cache.set(key, value, ttl=3600)
            return cache.get(key)

        # Execute cached operations
        result1 = cached_operation("test_key_1", {"data": "value1"})
        result2 = cached_operation("test_key_2", {"data": "value2"})

        # Verify profiling tracked operations
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 2

        # Verify cache worked
        assert result1 == {"data": "value1"}
        assert result2 == {"data": "value2"}

    def test_cache_hit_rate_tracking(self):
        """Test cache hit rate is tracked"""
        from mcp_server.optimization.cache_manager import CacheManager

        cache = CacheManager(redis_url=None)

        # Set values
        cache.set("key1", "value1", ttl=3600)
        cache.set("key2", "value2", ttl=3600)

        # Mix of hits and misses
        cache.get("key1")  # hit
        cache.get("key2")  # hit
        cache.get("key3")  # miss
        cache.get("key1")  # hit

        # Get statistics
        stats = cache.get_statistics()
        assert stats['hits'] >= 3
        assert stats['misses'] >= 1


@pytest.mark.agent_9
class TestDistributedProcessingIntegration:
    """Test distributed processing integrates with system"""

    def test_parallel_executor_with_monitoring(self):
        """Test parallel execution is monitored"""
        from mcp_server.distributed.parallel_executor import ParallelExecutor
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        executor = ParallelExecutor(max_workers=4, use_processes=False)

        @profile
        def parallel_task_wrapper(func, args_list):
            results = executor.execute_parallel(func, args_list)
            return results

        def simple_task(x):
            return x * 2

        # Execute parallel tasks
        task_args = [(1,), (2,), (3,), (4,), (5,)]
        results = parallel_task_wrapper(simple_task, task_args)

        # Verify monitoring tracked execution
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 1

        # Verify parallel execution worked
        assert len(results) == 5
        assert all(r.success for r in results)

    def test_parallel_execution_performance(self, test_helper):
        """Test parallel execution improves performance"""
        from mcp_server.distributed.parallel_executor import ParallelExecutor

        def compute_task(n):
            """Simulate computational work"""
            time.sleep(0.01)  # 10ms of work
            return n ** 2

        # Sequential execution
        sequential_start = time.time()
        sequential_results = [compute_task(i) for i in range(10)]
        sequential_time = (time.time() - sequential_start) * 1000

        # Parallel execution
        executor = ParallelExecutor(max_workers=4, use_processes=False)
        parallel_start = time.time()
        parallel_results = executor.execute_parallel(
            compute_task,
            [(i,) for i in range(10)]
        )
        parallel_time = (time.time() - parallel_start) * 1000

        # Verify parallel is faster (at least 2x speedup with 4 workers)
        assert parallel_time < sequential_time * 0.7, \
            f"Parallel ({parallel_time:.1f}ms) should be faster than sequential ({sequential_time:.1f}ms)"

        # Verify results match
        assert len(parallel_results) == 10
        assert sorted([r.result for r in parallel_results]) == sorted(sequential_results)


@pytest.mark.agent_9
class TestProfilingIntegration:
    """Test performance profiling integrates with system"""

    def test_profiling_across_agents(self, sample_player_data):
        """Test profiling works across different agent operations"""
        from mcp_server.profiling.performance import profile, get_profiler
        from mcp_server.profiling.metrics_reporter import MetricsReporter

        profiler = get_profiler()
        profiler.reset()

        @profile
        def data_validation():
            """Simulates Agent 4: Data validation"""
            return sample_player_data.dropna().describe()

        @profile
        def data_processing():
            """Simulates Agent 5: Data processing"""
            processed = sample_player_data.copy()
            processed['efficiency'] = processed['points'] / (processed['minutes'] + 0.1)
            return processed

        @profile
        def data_aggregation():
            """Simulates Agent 7: Aggregation"""
            return sample_player_data.groupby('player_id')['points'].mean()

        # Execute operations
        validation_result = data_validation()
        processing_result = data_processing()
        aggregation_result = data_aggregation()

        # Verify all operations profiled
        stats = profiler.get_summary()
        assert stats['total_functions_profiled'] >= 3
        assert stats['total_calls'] >= 3

        # Generate report
        reporter = MetricsReporter(profiler)
        report = reporter.generate_text_report()
        assert "data_validation" in report
        assert "data_processing" in report
        assert "data_aggregation" in report

    def test_bottleneck_identification(self):
        """Test bottleneck identification works"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        @profile
        def fast_operation():
            time.sleep(0.01)  # 10ms
            return "fast"

        @profile
        def slow_operation():
            time.sleep(0.15)  # 150ms - bottleneck
            return "slow"

        # Execute multiple times
        for _ in range(5):
            fast_operation()
            slow_operation()

        # Identify bottlenecks
        bottlenecks = profiler.identify_bottlenecks(
            time_threshold_ms=100.0,
            call_threshold=3
        )

        # Verify slow operation identified as bottleneck
        assert len(bottlenecks) >= 1
        bottleneck_names = [b['function_name'] for b in bottlenecks]
        assert any('slow_operation' in name for name in bottleneck_names)


@pytest.mark.agent_9
@pytest.mark.performance
class TestPerformanceOptimizationWorkflows:
    """Test complete performance optimization workflows"""

    def test_query_optimization_pipeline(self):
        """Test query optimization in data pipeline"""
        from mcp_server.optimization.query_optimizer import QueryOptimizer
        from mcp_server.optimization.cache_manager import CacheManager

        optimizer = QueryOptimizer()
        cache = CacheManager(redis_url=None)

        # Simulate query execution pipeline
        queries = [
            ("SELECT * FROM players WHERE id=?", 45.0),
            ("SELECT * FROM games WHERE date>?", 120.0),
            ("SELECT * FROM teams", 80.0),
        ]

        results = []
        for query, exec_time in queries:
            # Track execution
            metrics = optimizer.track_query_execution(query, exec_time)

            # Cache result
            cache_key = hash(query)
            cache.set(cache_key, {"query": query, "time": exec_time}, ttl=3600)

            results.append(metrics)

        # Verify pipeline worked
        assert len(results) == 3

        # Check for slow queries
        slow_queries = optimizer.get_slow_queries(min_executions=1)
        assert len(slow_queries) >= 1  # At least one slow query

        # Verify caching worked
        cache_stats = cache.get_statistics()
        assert cache_stats['sets'] >= 3

    def test_distributed_processing_with_profiling(self, large_player_dataset):
        """Test distributed processing with performance profiling"""
        from mcp_server.distributed.parallel_executor import ParallelExecutor
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        @profile
        def process_player_stats(player_data):
            """Process stats for a player"""
            return {
                'player_id': player_data['player_id'].iloc[0],
                'avg_points': player_data['points'].mean(),
                'avg_assists': player_data['assists'].mean()
            }

        # Split data by player
        player_groups = [
            group for _, group in large_player_dataset.groupby('player_id')
        ][:10]  # Process 10 players

        # Process in parallel
        executor = ParallelExecutor(max_workers=4, use_processes=False)
        results = executor.execute_parallel(
            process_player_stats,
            [(group,) for group in player_groups]
        )

        # Verify workflow completed
        assert len(results) == 10
        assert all(r.success for r in results)

        # Verify profiling tracked operations
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 10  # One call per player


@pytest.mark.agent_9
def test_comprehensive_agent_9_integration(sample_player_data, test_helper):
    """
    Comprehensive test of Agent 9 integration

    Tests: Query optimization + Caching + Distributed processing + Profiling
    """
    from mcp_server.optimization.query_optimizer import QueryOptimizer
    from mcp_server.optimization.cache_manager import CacheManager
    from mcp_server.distributed.parallel_executor import ParallelExecutor
    from mcp_server.profiling.performance import profile, get_profiler

    profiler = get_profiler()
    profiler.reset()

    workflow_state = {
        'query_optimization_active': False,
        'cache_operational': False,
        'parallel_execution_working': False,
        'profiling_tracking': False,
        'errors': []
    }

    # Step 1: Query Optimization
    try:
        optimizer = QueryOptimizer(slow_query_threshold_ms=100.0)
        optimizer.track_query_execution("SELECT * FROM test", 50.0)
        workflow_state['query_optimization_active'] = True
    except Exception as e:
        workflow_state['errors'].append(f"Query optimization: {str(e)}")

    # Step 2: Cache Management
    try:
        cache = CacheManager(redis_url=None)
        cache.set("test_key", "test_value", ttl=3600)
        cached_value = cache.get("test_key")
        workflow_state['cache_operational'] = cached_value == "test_value"
    except Exception as e:
        workflow_state['errors'].append(f"Cache: {str(e)}")

    # Step 3: Parallel Execution (with profiling)
    @profile
    def parallel_workflow():
        try:
            executor = ParallelExecutor(max_workers=2, use_processes=False)

            def simple_task(x):
                return x * 2

            results = executor.execute_parallel(simple_task, [(1,), (2,), (3,)])
            workflow_state['parallel_execution_working'] = len(results) == 3 and all(r.success for r in results)
            return results
        except Exception as e:
            workflow_state['errors'].append(f"Parallel execution: {str(e)}")
            return None

    parallel_results = parallel_workflow()

    # Step 4: Verify Profiling
    stats = profiler.get_summary()
    workflow_state['profiling_tracking'] = stats['total_calls'] >= 1

    # Verify workflow success
    assert workflow_state['query_optimization_active'], "Query optimization should be active"
    assert workflow_state['cache_operational'], "Cache should be operational"
    assert workflow_state['parallel_execution_working'], f"Parallel execution should work: {workflow_state['errors']}"
    assert workflow_state['profiling_tracking'], "Profiling should track operations"

    # Verify no critical errors
    assert len(workflow_state['errors']) == 0, f"Workflow should complete without errors: {workflow_state['errors']}"

    # Verify results
    assert parallel_results is not None
    assert len(parallel_results) == 3
