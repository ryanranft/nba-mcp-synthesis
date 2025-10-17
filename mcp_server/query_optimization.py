"""Database Query Optimization - IMPORTANT 14"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from mcp_server.database import get_database_engine
from mcp_server.performance import profile

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimize database queries"""

    def __init__(self):
        self.engine = None
        self.query_stats = {}

    def init_engine(self):
        """Initialize database engine"""
        if not self.engine:
            self.engine = get_database_engine()

    @profile
    def explain_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Explain query execution plan

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query plan
        """
        self.init_engine()

        explain_query = f"EXPLAIN (FORMAT JSON) {query}"

        with self.engine.connect() as conn:
            result = conn.execute(text(explain_query), params or {})
            plan = result.fetchone()[0]

            logger.info(f"📊 Query plan for: {query[:50]}...")
            logger.info(f"   {plan}")

            return plan

    def analyze_slow_queries(self, threshold_ms: float = 100.0) -> List[Dict]:
        """
        Find slow queries from pg_stat_statements

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow queries
        """
        self.init_engine()

        query = """
        SELECT
            query,
            calls,
            mean_exec_time,
            total_exec_time
        FROM pg_stat_statements
        WHERE mean_exec_time > :threshold
        ORDER BY mean_exec_time DESC
        LIMIT 20
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"threshold": threshold_ms})
            slow_queries = [dict(row) for row in result]

            if slow_queries:
                logger.warning(f"⚠️  Found {len(slow_queries)} slow queries")
                for q in slow_queries[:5]:
                    logger.warning(
                        f"   {q['query'][:50]}... ({q['mean_exec_time']:.2f}ms avg)"
                    )

            return slow_queries

    def suggest_indexes(self, table_name: str) -> List[str]:
        """
        Suggest indexes for a table based on usage patterns

        Args:
            table_name: Name of table

        Returns:
            List of suggested CREATE INDEX statements
        """
        self.init_engine()

        # Analyze table
        query = f"""
        SELECT
            attname as column_name,
            n_distinct,
            correlation
        FROM pg_stats
        WHERE tablename = :table_name
        ORDER BY abs(correlation) DESC
        """

        suggestions = []

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            columns = list(result)

            for col in columns:
                # Suggest index if high cardinality
                if col["n_distinct"] and abs(col["n_distinct"]) > 100:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col['column_name']} "
                        f"ON {table_name}({col['column_name']});"
                    )

        if suggestions:
            logger.info(f"💡 Index suggestions for {table_name}:")
            for suggestion in suggestions:
                logger.info(f"   {suggestion}")

        return suggestions

    @profile
    def optimize_query(self, query: str, params: Optional[Dict] = None) -> str:
        """
        Automatically optimize a query

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Optimized query
        """
        # Simple optimizations
        optimized = query.strip()

        # Add LIMIT if missing
        if "LIMIT" not in optimized.upper() and "SELECT" in optimized.upper():
            optimized += " LIMIT 1000"

        # Suggest using specific columns instead of SELECT *
        if "SELECT *" in optimized.upper():
            logger.warning("⚠️  Query uses SELECT * - consider specifying columns")

        # Check for missing WHERE clause
        if "WHERE" not in optimized.upper() and "DELETE" in optimized.upper():
            logger.error("🚨 DELETE without WHERE clause detected!")

        return optimized


# Global optimizer
_query_optimizer = None


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer"""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


# Optimized query helpers
@profile
def query_with_cache(query: str, params: Optional[Dict] = None, cache_ttl: int = 300):
    """
    Execute query with result caching

    Args:
        query: SQL query
        params: Query parameters
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Query results
    """
    import hashlib
    import json

    # Generate cache key
    cache_key = hashlib.md5(
        f"{query}{json.dumps(params or {}, sort_keys=True)}".encode()
    ).hexdigest()

    # TODO: Check Redis cache
    # For now, execute directly

    optimizer = get_query_optimizer()
    optimizer.init_engine()

    with optimizer.engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        rows = [dict(row) for row in result]

        # TODO: Store in Redis cache

        return rows


# Example usage
if __name__ == "__main__":
    optimizer = get_query_optimizer()

    # Analyze slow queries
    slow_queries = optimizer.analyze_slow_queries(threshold_ms=50.0)

    # Suggest indexes
    suggestions = optimizer.suggest_indexes("games")

    # Explain a query
    query = "SELECT * FROM players WHERE team = :team"
    plan = optimizer.explain_query(query, {"team": "Lakers"})
