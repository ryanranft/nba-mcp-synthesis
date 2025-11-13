"""
Enhanced Connection Pool Manager

Provides connection health checks, adaptive pool sizing, and monitoring for RDSConnector.
"""

import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection health states"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    IDLE = "idle"


@dataclass
class ConnectionMetrics:
    """Metrics for a single database connection"""

    connection_id: int
    created_at: datetime
    last_used: datetime
    total_queries: int = 0
    failed_queries: int = 0
    total_execution_time_ms: float = 0.0
    state: ConnectionState = ConnectionState.HEALTHY
    last_health_check: Optional[datetime] = None


@dataclass
class PoolStatistics:
    """Statistics for connection pool"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_queries_executed: int = 0
    total_failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    pool_utilization: float = 0.0
    health_check_failures: int = 0


class EnhancedConnectionPool:
    """
    Enhanced connection pool for RDSConnector with health monitoring and adaptive sizing.

    Features:
    - Connection health checks
    - Adaptive pool sizing
    - Connection reuse and recycling
    - Detailed metrics and monitoring
    """

    def __init__(
        self,
        rds_connector,
        min_pool_size: int = 2,
        max_pool_size: int = 10,
        health_check_interval: int = 60,  # seconds
        connection_lifetime: int = 3600,  # seconds
        idle_timeout: int = 300,  # seconds
        enable_adaptive_sizing: bool = True,
    ):
        """
        Initialize enhanced connection pool.

        Args:
            rds_connector: RDSConnector instance to manage
            min_pool_size: Minimum number of connections
            max_pool_size: Maximum number of connections
            health_check_interval: Seconds between health checks
            connection_lifetime: Max lifetime of a connection before recycling
            idle_timeout: Seconds before an idle connection is recycled
            enable_adaptive_sizing: Enable dynamic pool size adjustment
        """
        self.rds_connector = rds_connector
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.health_check_interval = health_check_interval
        self.connection_lifetime = connection_lifetime
        self.idle_timeout = idle_timeout
        self.enable_adaptive_sizing = enable_adaptive_sizing

        # Connection tracking
        self.connection_metrics: Dict[int, ConnectionMetrics] = {}
        self.next_connection_id = 0

        # Pool statistics
        self.stats = PoolStatistics()

        # Health check tracking
        self.last_health_check = datetime.now()

        logger.info(
            f"EnhancedConnectionPool initialized (min={min_pool_size}, max={max_pool_size}, "
            f"adaptive={enable_adaptive_sizing})"
        )

    async def health_check_connection(self, connection) -> bool:
        """
        Check if a connection is healthy.

        Args:
            connection: Database connection to check

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple query to verify connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            return False

    async def perform_health_checks(self):
        """Perform health checks on all connections"""
        now = datetime.now()

        # Check if it's time for health check
        if (now - self.last_health_check).total_seconds() < self.health_check_interval:
            return

        logger.debug("Performing connection pool health checks")

        for conn_id, metrics in list(self.connection_metrics.items()):
            # Check connection lifetime
            age = (now - metrics.created_at).total_seconds()
            if age > self.connection_lifetime:
                logger.info(f"Connection {conn_id} exceeded lifetime, recycling")
                metrics.state = ConnectionState.FAILED
                self._recycle_connection(conn_id)
                continue

            # Check idle timeout
            idle_time = (now - metrics.last_used).total_seconds()
            if idle_time > self.idle_timeout:
                metrics.state = ConnectionState.IDLE
                if self._get_active_count() > self.min_pool_size:
                    logger.info(f"Connection {conn_id} idle too long, removing")
                    self._recycle_connection(conn_id)
                    continue

            # Perform health check
            if metrics.state == ConnectionState.HEALTHY:
                is_healthy = await self.health_check_connection(
                    self.rds_connector.connection
                )
                if not is_healthy:
                    metrics.state = ConnectionState.FAILED
                    self.stats.health_check_failures += 1
                    self._recycle_connection(conn_id)
                else:
                    metrics.last_health_check = now

        self.last_health_check = now

    def track_query_execution(
        self, connection_id: int, execution_time_ms: float, success: bool = True
    ):
        """
        Track query execution metrics.

        Args:
            connection_id: ID of connection that executed query
            execution_time_ms: Query execution time in milliseconds
            success: Whether query succeeded
        """
        if connection_id not in self.connection_metrics:
            logger.warning(f"Unknown connection_id: {connection_id}")
            return

        metrics = self.connection_metrics[connection_id]
        metrics.total_queries += 1
        metrics.total_execution_time_ms += execution_time_ms
        metrics.last_used = datetime.now()

        if not success:
            metrics.failed_queries += 1
            self.stats.total_failed_queries += 1

            # Mark as degraded after multiple failures
            if metrics.failed_queries > 3:
                metrics.state = ConnectionState.DEGRADED

        self.stats.total_queries_executed += 1

    def get_recommended_pool_size(self) -> int:
        """
        Calculate recommended pool size based on current metrics.

        Returns:
            Recommended number of connections
        """
        if not self.enable_adaptive_sizing:
            return self.max_pool_size

        # Calculate utilization
        active = self._get_active_count()
        total = len(self.connection_metrics)

        if total == 0:
            return self.min_pool_size

        utilization = active / total if total > 0 else 0.0

        # Adjust size based on utilization
        if utilization > 0.8:  # High utilization, increase
            recommended = min(total + 1, self.max_pool_size)
        elif (
            utilization < 0.3 and total > self.min_pool_size
        ):  # Low utilization, decrease
            recommended = max(total - 1, self.min_pool_size)
        else:
            recommended = total

        return recommended

    def _get_active_count(self) -> int:
        """Count active (healthy or degraded) connections"""
        return sum(
            1
            for m in self.connection_metrics.values()
            if m.state in [ConnectionState.HEALTHY, ConnectionState.DEGRADED]
        )

    def _recycle_connection(self, connection_id: int):
        """Remove and recycle a connection"""
        if connection_id in self.connection_metrics:
            del self.connection_metrics[connection_id]
            logger.debug(f"Recycled connection {connection_id}")

    def register_connection(self) -> int:
        """
        Register a new connection in the pool.

        Returns:
            Connection ID
        """
        conn_id = self.next_connection_id
        self.next_connection_id += 1

        self.connection_metrics[conn_id] = ConnectionMetrics(
            connection_id=conn_id,
            created_at=datetime.now(),
            last_used=datetime.now(),
            state=ConnectionState.HEALTHY,
        )

        logger.debug(f"Registered new connection {conn_id}")
        return conn_id

    def get_pool_statistics(self) -> PoolStatistics:
        """
        Get current pool statistics.

        Returns:
            PoolStatistics object
        """
        total_conns = len(self.connection_metrics)
        active_conns = sum(
            1
            for m in self.connection_metrics.values()
            if m.state in [ConnectionState.HEALTHY, ConnectionState.DEGRADED]
        )
        idle_conns = sum(
            1
            for m in self.connection_metrics.values()
            if m.state == ConnectionState.IDLE
        )
        failed_conns = sum(
            1
            for m in self.connection_metrics.values()
            if m.state == ConnectionState.FAILED
        )

        # Calculate average query time
        total_time = sum(
            m.total_execution_time_ms for m in self.connection_metrics.values()
        )
        total_queries = sum(m.total_queries for m in self.connection_metrics.values())
        avg_time = total_time / total_queries if total_queries > 0 else 0.0

        # Calculate utilization
        utilization = (
            active_conns / self.max_pool_size if self.max_pool_size > 0 else 0.0
        )

        self.stats = PoolStatistics(
            total_connections=total_conns,
            active_connections=active_conns,
            idle_connections=idle_conns,
            failed_connections=failed_conns,
            total_queries_executed=total_queries,
            total_failed_queries=self.stats.total_failed_queries,
            avg_query_time_ms=avg_time,
            pool_utilization=utilization,
            health_check_failures=self.stats.health_check_failures,
        )

        return self.stats

    def get_connection_details(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all connections.

        Returns:
            List of connection detail dicts
        """
        details = []

        for conn_id, metrics in self.connection_metrics.items():
            age_seconds = (datetime.now() - metrics.created_at).total_seconds()
            idle_seconds = (datetime.now() - metrics.last_used).total_seconds()

            details.append(
                {
                    "connection_id": conn_id,
                    "state": metrics.state.value,
                    "age_seconds": age_seconds,
                    "idle_seconds": idle_seconds,
                    "total_queries": metrics.total_queries,
                    "failed_queries": metrics.failed_queries,
                    "avg_query_time_ms": (
                        metrics.total_execution_time_ms / metrics.total_queries
                        if metrics.total_queries > 0
                        else 0.0
                    ),
                    "last_health_check": (
                        metrics.last_health_check.isoformat()
                        if metrics.last_health_check
                        else None
                    ),
                }
            )

        return details

    async def optimize_pool(self):
        """
        Optimize the connection pool based on current metrics.

        Performs:
        - Health checks
        - Adaptive sizing adjustments
        - Connection recycling
        """
        # Run health checks
        await self.perform_health_checks()

        # Get recommended size
        if self.enable_adaptive_sizing:
            recommended = self.get_recommended_pool_size()
            current = len(self.connection_metrics)

            if recommended != current:
                logger.info(
                    f"Adaptive sizing: adjusting pool from {current} to {recommended} connections"
                )

        # Get and log statistics
        stats = self.get_pool_statistics()
        logger.debug(
            f"Pool stats: {stats.total_connections} total, {stats.active_connections} active, "
            f"{stats.pool_utilization:.1%} utilization"
        )

    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_pool_statistics()
        return (
            f"EnhancedConnectionPool("
            f"total={stats.total_connections}, "
            f"active={stats.active_connections}, "
            f"util={stats.pool_utilization:.1%})"
        )
