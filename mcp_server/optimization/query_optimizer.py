"""
Query Optimizer for PostgreSQL Database

Analyzes query plans, suggests optimizations, and provides caching strategies.
"""

import re
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Represents a PostgreSQL query execution plan"""

    query: str
    plan_json: Dict[str, Any]
    execution_time_ms: float
    total_cost: float
    has_seq_scan: bool = False
    has_index_scan: bool = False
    tables_accessed: List[str] = field(default_factory=list)
    suggested_indexes: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class QueryMetrics:
    """Tracks metrics for a specific query"""

    query_hash: str
    query: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_executed: Optional[datetime] = None
    slow_query_count: int = 0  # Count of executions >100ms


class QueryOptimizer:
    """
    Optimizes SQL queries for PostgreSQL database.

    Features:
    - Query plan analysis
    - Index recommendations
    - Performance metrics tracking
    - Optimization suggestions
    """

    def __init__(
        self,
        slow_query_threshold_ms: float = 100.0,
        cache_enabled: bool = True,
        track_metrics: bool = True
    ):
        """
        Initialize query optimizer.

        Args:
            slow_query_threshold_ms: Threshold for flagging slow queries
            cache_enabled: Enable query result caching
            track_metrics: Track query performance metrics
        """
        self.slow_query_threshold = slow_query_threshold_ms
        self.cache_enabled = cache_enabled
        self.track_metrics = track_metrics

        # Query metrics storage
        self.query_metrics: Dict[str, QueryMetrics] = {}

        # Query plan cache
        self.plan_cache: Dict[str, QueryPlan] = {}

        logger.info(
            f"QueryOptimizer initialized (slow_threshold={slow_query_threshold_ms}ms, "
            f"cache={cache_enabled}, metrics={track_metrics})"
        )

    def analyze_query_plan(
        self,
        query: str,
        plan_json: Dict[str, Any],
        execution_time_ms: float
    ) -> QueryPlan:
        """
        Analyze a PostgreSQL query execution plan.

        Args:
            query: SQL query string
            plan_json: Query plan from EXPLAIN (ANALYZE, FORMAT JSON)
            execution_time_ms: Actual execution time in milliseconds

        Returns:
            QueryPlan object with analysis results
        """
        # Extract plan details
        plan = plan_json[0] if isinstance(plan_json, list) else plan_json
        plan_node = plan.get("Plan", {})

        total_cost = plan_node.get("Total Cost", 0.0)

        # Analyze plan for optimization opportunities
        has_seq_scan = self._has_sequential_scan(plan_node)
        has_index_scan = self._has_index_scan(plan_node)
        tables = self._extract_tables(plan_node)

        # Create QueryPlan object
        query_plan = QueryPlan(
            query=query,
            plan_json=plan_json,
            execution_time_ms=execution_time_ms,
            total_cost=total_cost,
            has_seq_scan=has_seq_scan,
            has_index_scan=has_index_scan,
            tables_accessed=tables
        )

        # Generate optimization suggestions
        query_plan.optimization_suggestions = self._generate_suggestions(query_plan)

        # Suggest indexes if needed
        if has_seq_scan and execution_time_ms > self.slow_query_threshold:
            query_plan.suggested_indexes = self._suggest_indexes(query, tables)

        # Cache the plan
        query_hash = self._hash_query(query)
        self.plan_cache[query_hash] = query_plan

        logger.debug(
            f"Analyzed query plan: cost={total_cost:.2f}, time={execution_time_ms:.2f}ms, "
            f"seq_scan={has_seq_scan}, tables={len(tables)}"
        )

        return query_plan

    def track_query_execution(
        self,
        query: str,
        execution_time_ms: float
    ) -> QueryMetrics:
        """
        Track metrics for query execution.

        Args:
            query: SQL query string
            execution_time_ms: Execution time in milliseconds

        Returns:
            Updated QueryMetrics object
        """
        if not self.track_metrics:
            return None

        query_hash = self._hash_query(query)

        # Get or create metrics
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query=query[:500]  # Store first 500 chars
            )

        metrics = self.query_metrics[query_hash]

        # Update metrics
        metrics.execution_count += 1
        metrics.total_time_ms += execution_time_ms
        metrics.avg_time_ms = metrics.total_time_ms / metrics.execution_count
        metrics.min_time_ms = min(metrics.min_time_ms, execution_time_ms)
        metrics.max_time_ms = max(metrics.max_time_ms, execution_time_ms)
        metrics.last_executed = datetime.now()

        if execution_time_ms > self.slow_query_threshold:
            metrics.slow_query_count += 1
            logger.warning(
                f"Slow query detected: {execution_time_ms:.2f}ms (threshold: {self.slow_query_threshold}ms)"
            )

        return metrics

    def get_slow_queries(
        self,
        min_executions: int = 5
    ) -> List[QueryMetrics]:
        """
        Get list of slow queries based on average execution time.

        Args:
            min_executions: Minimum number of executions to consider

        Returns:
            List of QueryMetrics for slow queries, sorted by avg time
        """
        slow_queries = [
            metrics for metrics in self.query_metrics.values()
            if metrics.execution_count >= min_executions
            and metrics.avg_time_ms > self.slow_query_threshold
        ]

        return sorted(slow_queries, key=lambda m: m.avg_time_ms, reverse=True)

    def get_query_recommendations(
        self,
        query: str
    ) -> Dict[str, Any]:
        """
        Get optimization recommendations for a query.

        Args:
            query: SQL query string

        Returns:
            Dict with recommendations and metrics
        """
        query_hash = self._hash_query(query)

        recommendations = {
            "query_hash": query_hash,
            "optimizations": [],
            "indexes": [],
            "metrics": None,
            "plan": None
        }

        # Add metrics if available
        if query_hash in self.query_metrics:
            metrics = self.query_metrics[query_hash]
            recommendations["metrics"] = {
                "execution_count": metrics.execution_count,
                "avg_time_ms": metrics.avg_time_ms,
                "slow_query_count": metrics.slow_query_count
            }

        # Add plan analysis if available
        if query_hash in self.plan_cache:
            plan = self.plan_cache[query_hash]
            recommendations["plan"] = {
                "has_seq_scan": plan.has_seq_scan,
                "has_index_scan": plan.has_index_scan,
                "total_cost": plan.total_cost,
                "tables": plan.tables_accessed
            }
            recommendations["optimizations"] = plan.optimization_suggestions
            recommendations["indexes"] = plan.suggested_indexes

        return recommendations

    def optimize_query(
        self,
        query: str
    ) -> str:
        """
        Attempt to automatically optimize a query.

        Args:
            query: SQL query string

        Returns:
            Optimized query string
        """
        optimized = query.strip()

        # Add LIMIT if missing and no aggregation
        if not re.search(r'\bLIMIT\b', optimized, re.IGNORECASE):
            if not re.search(r'\b(COUNT|SUM|AVG|MIN|MAX|GROUP BY)\b', optimized, re.IGNORECASE):
                logger.info("Adding LIMIT clause to query")
                optimized += " LIMIT 1000"

        # Suggest using specific columns instead of SELECT *
        if re.search(r'SELECT\s+\*', optimized, re.IGNORECASE):
            logger.warning("Query uses SELECT * - consider specifying columns")

        # Check for missing WHERE clause
        if re.search(r'\bFROM\b', optimized, re.IGNORECASE):
            if not re.search(r'\bWHERE\b', optimized, re.IGNORECASE):
                logger.warning("Query missing WHERE clause - may scan entire table")

        return optimized

    def _hash_query(self, query: str) -> str:
        """Generate hash for query (normalize first)"""
        # Normalize whitespace and case for hashing
        normalized = query.strip().lower()
        # Normalize whitespace (including newlines)
        normalized = re.sub(r'\s+', ' ', normalized)
        # Normalize around operators
        normalized = re.sub(r'\s*=\s*', '=', normalized)
        normalized = re.sub(r'\s*<\s*', '<', normalized)
        normalized = re.sub(r'\s*>\s*', '>', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _has_sequential_scan(self, plan_node: Dict[str, Any]) -> bool:
        """Check if plan contains sequential scan"""
        if plan_node.get("Node Type") == "Seq Scan":
            return True

        # Check child nodes recursively
        for key in ["Plans", "Subplans"]:
            if key in plan_node:
                for child in plan_node[key]:
                    if self._has_sequential_scan(child):
                        return True

        return False

    def _has_index_scan(self, plan_node: Dict[str, Any]) -> bool:
        """Check if plan uses index scan"""
        node_type = plan_node.get("Node Type", "")
        if "Index" in node_type:  # Index Scan, Index Only Scan, Bitmap Index Scan
            return True

        # Check child nodes recursively
        for key in ["Plans", "Subplans"]:
            if key in plan_node:
                for child in plan_node[key]:
                    if self._has_index_scan(child):
                        return True

        return False

    def _extract_tables(self, plan_node: Dict[str, Any]) -> List[str]:
        """Extract table names from plan"""
        tables = []

        # Get table name if this is a scan node
        if "Relation Name" in plan_node:
            tables.append(plan_node["Relation Name"])

        # Check child nodes recursively
        for key in ["Plans", "Subplans"]:
            if key in plan_node:
                for child in plan_node[key]:
                    tables.extend(self._extract_tables(child))

        return list(set(tables))  # Remove duplicates

    def _suggest_indexes(
        self,
        query: str,
        tables: List[str]
    ) -> List[str]:
        """
        Suggest indexes based on query patterns.

        Args:
            query: SQL query string
            tables: List of tables accessed in query

        Returns:
            List of suggested index creation statements
        """
        suggestions = []

        # Extract WHERE clause columns
        where_match = re.search(r'WHERE\s+(.+?)(?:GROUP BY|ORDER BY|LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)

            # Find column names in WHERE clause
            columns = re.findall(r'(\w+)\s*[=<>!]', where_clause)

            for table in tables:
                for column in columns:
                    index_name = f"idx_{table}_{column}"
                    suggestions.append(f"CREATE INDEX {index_name} ON {table}({column});")

        # Extract ORDER BY columns
        order_match = re.search(r'ORDER BY\s+(.+?)(?:LIMIT|$)', query, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            columns = re.findall(r'(\w+)', order_clause)

            for table in tables:
                for column in columns:
                    index_name = f"idx_{table}_{column}_sort"
                    suggestions.append(f"CREATE INDEX {index_name} ON {table}({column});")

        return suggestions

    def _generate_suggestions(self, query_plan: QueryPlan) -> List[str]:
        """Generate optimization suggestions based on query plan"""
        suggestions = []

        if query_plan.has_seq_scan:
            suggestions.append("Query uses sequential scan - consider adding indexes")

        if query_plan.execution_time_ms > self.slow_query_threshold:
            suggestions.append(f"Query exceeds slow threshold ({self.slow_query_threshold}ms)")

        if query_plan.total_cost > 10000:
            suggestions.append("High query cost - consider query rewriting or partitioning")

        if len(query_plan.tables_accessed) > 5:
            suggestions.append("Query accesses many tables - consider denormalization or caching")

        return suggestions

    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        total_queries = len(self.query_metrics)
        slow_queries = len([m for m in self.query_metrics.values()
                           if m.avg_time_ms >= self.slow_query_threshold])

        return {
            "total_tracked_queries": total_queries,
            "slow_queries_count": slow_queries,
            "cached_plans": len(self.plan_cache),
            "slow_query_threshold_ms": self.slow_query_threshold,
            "cache_enabled": self.cache_enabled,
            "metrics_tracking": self.track_metrics
        }
