"""
Tests for QueryOptimizer

Tests query plan analysis, optimization suggestions, and metrics tracking.
"""

import pytest
from datetime import datetime
from mcp_server.optimization.query_optimizer import (
    QueryOptimizer,
    QueryPlan,
    QueryMetrics,
)


class TestQueryOptimizer:
    """Test suite for QueryOptimizer"""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return QueryOptimizer(
            slow_query_threshold_ms=100.0, cache_enabled=True, track_metrics=True
        )

    @pytest.fixture
    def sample_query(self):
        """Sample SQL query"""
        return "SELECT * FROM player_stats WHERE player_id = 123 ORDER BY game_date"

    @pytest.fixture
    def sample_plan_with_seq_scan(self):
        """Sample query plan with sequential scan"""
        return [
            {
                "Plan": {
                    "Node Type": "Seq Scan",
                    "Relation Name": "player_stats",
                    "Total Cost": 450.5,
                    "Plans": [],
                },
                "Execution Time": 150.2,
            }
        ]

    @pytest.fixture
    def sample_plan_with_index(self):
        """Sample query plan with index scan"""
        return [
            {
                "Plan": {
                    "Node Type": "Index Scan",
                    "Relation Name": "player_stats",
                    "Index Name": "idx_player_stats_player_id",
                    "Total Cost": 8.5,
                    "Plans": [],
                },
                "Execution Time": 5.3,
            }
        ]

    def test_optimizer_initialization(self):
        """Test optimizer initializes with correct settings"""
        optimizer = QueryOptimizer(
            slow_query_threshold_ms=200.0, cache_enabled=False, track_metrics=False
        )

        assert optimizer.slow_query_threshold == 200.0
        assert optimizer.cache_enabled is False
        assert optimizer.track_metrics is False
        assert len(optimizer.query_metrics) == 0
        assert len(optimizer.plan_cache) == 0

    def test_analyze_query_plan_seq_scan(
        self, optimizer, sample_query, sample_plan_with_seq_scan
    ):
        """Test analyzing plan with sequential scan"""
        plan = optimizer.analyze_query_plan(
            query=sample_query,
            plan_json=sample_plan_with_seq_scan,
            execution_time_ms=150.2,
        )

        assert isinstance(plan, QueryPlan)
        assert plan.query == sample_query
        assert plan.execution_time_ms == 150.2
        assert plan.total_cost == 450.5
        assert plan.has_seq_scan is True
        assert plan.has_index_scan is False
        assert "player_stats" in plan.tables_accessed
        assert len(plan.optimization_suggestions) > 0

    def test_analyze_query_plan_index_scan(
        self, optimizer, sample_query, sample_plan_with_index
    ):
        """Test analyzing plan with index scan"""
        plan = optimizer.analyze_query_plan(
            query=sample_query, plan_json=sample_plan_with_index, execution_time_ms=5.3
        )

        assert plan.has_seq_scan is False
        assert plan.has_index_scan is True
        assert plan.execution_time_ms < optimizer.slow_query_threshold
        assert len(plan.suggested_indexes) == 0  # Already using index

    def test_track_query_execution(self, optimizer, sample_query):
        """Test query execution tracking"""
        # Execute query multiple times
        metrics1 = optimizer.track_query_execution(sample_query, 50.0)
        metrics2 = optimizer.track_query_execution(sample_query, 75.0)
        metrics3 = optimizer.track_query_execution(sample_query, 125.0)

        assert metrics3.execution_count == 3
        assert metrics3.total_time_ms == 250.0
        assert metrics3.avg_time_ms == pytest.approx(83.33, rel=0.01)
        assert metrics3.min_time_ms == 50.0
        assert metrics3.max_time_ms == 125.0
        assert metrics3.slow_query_count == 1  # One execution > 100ms

    def test_track_multiple_queries(self, optimizer):
        """Test tracking different queries separately"""
        query1 = "SELECT * FROM players"
        query2 = "SELECT * FROM games"

        optimizer.track_query_execution(query1, 50.0)
        optimizer.track_query_execution(query2, 75.0)
        optimizer.track_query_execution(query1, 60.0)

        assert len(optimizer.query_metrics) == 2

        # Check query1 metrics
        query1_hash = optimizer._hash_query(query1)
        assert optimizer.query_metrics[query1_hash].execution_count == 2
        assert optimizer.query_metrics[query1_hash].avg_time_ms == 55.0

        # Check query2 metrics
        query2_hash = optimizer._hash_query(query2)
        assert optimizer.query_metrics[query2_hash].execution_count == 1

    def test_get_slow_queries(self, optimizer):
        """Test retrieving slow queries"""
        fast_query = "SELECT id FROM players LIMIT 10"
        slow_query = "SELECT * FROM player_stats WHERE TRUE"

        # Execute fast query 10 times
        for _ in range(10):
            optimizer.track_query_execution(fast_query, 20.0)

        # Execute slow query 10 times
        for _ in range(10):
            optimizer.track_query_execution(slow_query, 150.0)

        # Get slow queries
        slow_queries = optimizer.get_slow_queries(min_executions=5)

        assert len(slow_queries) == 1
        assert slow_queries[0].avg_time_ms > optimizer.slow_query_threshold

    def test_get_query_recommendations(
        self, optimizer, sample_query, sample_plan_with_seq_scan
    ):
        """Test getting query recommendations"""
        # Analyze plan and track execution
        optimizer.analyze_query_plan(sample_query, sample_plan_with_seq_scan, 150.0)
        optimizer.track_query_execution(sample_query, 150.0)

        # Get recommendations
        recs = optimizer.get_query_recommendations(sample_query)

        assert "query_hash" in recs
        assert "optimizations" in recs
        assert "indexes" in recs
        assert recs["metrics"] is not None
        assert recs["plan"] is not None
        assert recs["plan"]["has_seq_scan"] is True

    def test_optimize_query_adds_limit(self, optimizer):
        """Test that optimizer adds LIMIT to queries"""
        query_without_limit = "SELECT * FROM players"
        optimized = optimizer.optimize_query(query_without_limit)

        assert "LIMIT" in optimized.upper()
        assert "1000" in optimized

    def test_optimize_query_preserves_limit(self, optimizer):
        """Test that optimizer doesn't add LIMIT if already present"""
        query_with_limit = "SELECT * FROM players LIMIT 50"
        optimized = optimizer.optimize_query(query_with_limit)

        assert optimized.count("LIMIT") == 1
        assert "LIMIT 50" in optimized

    def test_optimize_query_skips_aggregations(self, optimizer):
        """Test that LIMIT not added to aggregation queries"""
        agg_query = "SELECT COUNT(*) FROM players"
        optimized = optimizer.optimize_query(agg_query)

        assert "LIMIT" not in optimized.upper()

    def test_suggest_indexes_from_where_clause(self, optimizer):
        """Test index suggestions from WHERE clause"""
        query = "SELECT * FROM players WHERE team_id = 1 AND position = 'PG'"
        tables = ["players"]

        suggestions = optimizer._suggest_indexes(query, tables)

        assert len(suggestions) > 0
        assert any("team_id" in s for s in suggestions)
        assert any("position" in s for s in suggestions)

    def test_suggest_indexes_from_order_by(self, optimizer):
        """Test index suggestions from ORDER BY clause"""
        query = "SELECT * FROM players ORDER BY last_name"
        tables = ["players"]

        suggestions = optimizer._suggest_indexes(query, tables)

        assert len(suggestions) > 0
        assert any("last_name" in s for s in suggestions)
        assert any("_sort" in s for s in suggestions)

    def test_hash_query_normalization(self, optimizer):
        """Test that similar queries hash to same value"""
        query1 = "SELECT * FROM players WHERE id = 1"
        query2 = "select    *    from    players   where   id   =   1"
        query3 = "SELECT   *\nFROM players\nWHERE id=1"

        hash1 = optimizer._hash_query(query1)
        hash2 = optimizer._hash_query(query2)
        hash3 = optimizer._hash_query(query3)

        assert hash1 == hash2 == hash3

    def test_get_statistics(self, optimizer, sample_query):
        """Test getting optimizer statistics"""
        # Track some queries
        optimizer.track_query_execution(sample_query, 50.0)
        optimizer.track_query_execution(sample_query, 150.0)  # Slow

        stats = optimizer.get_statistics()

        assert stats["total_tracked_queries"] == 1
        assert stats["slow_queries_count"] == 1
        assert stats["slow_query_threshold_ms"] == 100.0
        assert stats["cache_enabled"] is True
        assert stats["metrics_tracking"] is True

    def test_disabled_metrics_tracking(self):
        """Test that metrics tracking can be disabled"""
        optimizer = QueryOptimizer(track_metrics=False)

        query = "SELECT * FROM players"
        result = optimizer.track_query_execution(query, 50.0)

        assert result is None
        assert len(optimizer.query_metrics) == 0
