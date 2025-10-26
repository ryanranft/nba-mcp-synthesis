"""
System Optimizer Module

Provides caching, performance profiling, connection pooling, and optimization
utilities for the NBA MCP system.

Features:
- LRU cache for models and data
- Performance profiling decorators
- Connection pooling for database/external services
- Batch processing optimization
- Memory management utilities
- Query optimization helpers

Usage:
    from mcp_server.system_optimizer import (
        ModelCache,
        profile_performance,
        batch_optimize,
        ConnectionPool
    )

    # Cache models
    cache = ModelCache(max_size=100)
    cache.set("model_v1", model_object)
    model = cache.get("model_v1")

    # Profile function performance
    @profile_performance
    def slow_function():
        # ... complex logic
        pass

    # Optimize batch processing
    @batch_optimize(batch_size=100)
    def process_predictions(items):
        # ... process items
        pass
"""

import time
import functools
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache implementation.

    Automatically evicts least recently used items when capacity is reached.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]

            self.misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.move_to_end(key)
            else:
                # Add new key
                if len(self.cache) >= self.max_size:
                    # Remove least recently used item
                    self.cache.popitem(last=False)

            self.cache[key] = value

    def delete(self, key: str) -> bool:
        """
        Delete item from cache.

        Args:
            key: Cache key

        Returns:
            True if item was deleted, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "utilization": len(self.cache) / self.max_size
            }


class ModelCache:
    """
    Specialized cache for ML models with TTL support.

    Automatically expires models after specified time to live.
    """

    def __init__(self, max_size: int = 50, ttl_seconds: int = 3600):
        """
        Initialize model cache.

        Args:
            max_size: Maximum number of models to cache
            ttl_seconds: Time to live for cached models (default 1 hour)
        """
        self.cache = LRUCache(max_size=max_size)
        self.ttl_seconds = ttl_seconds
        self.timestamps: Dict[str, datetime] = {}
        self.lock = threading.Lock()

    def get(self, model_id: str) -> Optional[Any]:
        """
        Get model from cache if not expired.

        Args:
            model_id: Model identifier

        Returns:
            Cached model or None if not found/expired
        """
        with self.lock:
            # Check if expired
            if model_id in self.timestamps:
                age = datetime.now() - self.timestamps[model_id]
                if age > timedelta(seconds=self.ttl_seconds):
                    # Expired - remove from cache
                    self.cache.delete(model_id)
                    del self.timestamps[model_id]
                    return None

        return self.cache.get(model_id)

    def set(self, model_id: str, model: Any) -> None:
        """
        Set model in cache with current timestamp.

        Args:
            model_id: Model identifier
            model: Model object to cache
        """
        self.cache.set(model_id, model)
        with self.lock:
            self.timestamps[model_id] = datetime.now()

    def delete(self, model_id: str) -> bool:
        """
        Delete model from cache.

        Args:
            model_id: Model identifier

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if model_id in self.timestamps:
                del self.timestamps[model_id]

        return self.cache.delete(model_id)

    def clear(self) -> None:
        """Clear all models from cache."""
        self.cache.clear()
        with self.lock:
            self.timestamps.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics including model count and ages."""
        stats = self.cache.get_stats()

        with self.lock:
            if self.timestamps:
                ages = [
                    (datetime.now() - ts).total_seconds()
                    for ts in self.timestamps.values()
                ]
                stats["avg_age_seconds"] = sum(ages) / len(ages)
                stats["oldest_age_seconds"] = max(ages)
            else:
                stats["avg_age_seconds"] = 0
                stats["oldest_age_seconds"] = 0

        return stats


def profile_performance(func: Callable) -> Callable:
    """
    Decorator to profile function performance.

    Logs execution time and can track performance metrics.

    Usage:
        @profile_performance
        def expensive_function():
            # ... logic
            pass

    Args:
        func: Function to profile

    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.info(
                f"Performance: {func.__name__} completed in {elapsed:.4f}s"
            )

            # Store in result if it's a dict
            if isinstance(result, dict):
                result["_performance_ms"] = elapsed * 1000

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Performance: {func.__name__} failed after {elapsed:.4f}s: {e}"
            )
            raise

    return wrapper


def batch_optimize(batch_size: int = 100):
    """
    Decorator to optimize batch processing.

    Processes items in batches for better performance.

    Usage:
        @batch_optimize(batch_size=50)
        def process_items(items):
            # Process batch of items
            return results

    Args:
        batch_size: Number of items per batch

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items: List[Any], *args, **kwargs):
            if not items:
                return []

            results = []
            total_batches = (len(items) + batch_size - 1) // batch_size

            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_num = i // batch_size + 1

                logger.debug(
                    f"Processing batch {batch_num}/{total_batches} "
                    f"({len(batch)} items)"
                )

                batch_results = func(batch, *args, **kwargs)
                results.extend(batch_results)

            return results

        return wrapper

    return decorator


class ConnectionPool:
    """
    Generic connection pool for managing reusable connections.

    Useful for database connections, HTTP clients, etc.
    """

    def __init__(
        self,
        create_connection: Callable,
        max_size: int = 10,
        timeout: float = 30.0
    ):
        """
        Initialize connection pool.

        Args:
            create_connection: Function to create new connections
            max_size: Maximum number of connections
            timeout: Timeout for getting connection (seconds)
        """
        self.create_connection = create_connection
        self.max_size = max_size
        self.timeout = timeout
        self.pool: List[Any] = []
        self.in_use: set = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def get_connection(self) -> Any:
        """
        Get connection from pool or create new one.

        Returns:
            Connection object

        Raises:
            TimeoutError: If no connection available within timeout
        """
        start_time = time.time()

        with self.condition:
            while True:
                # Try to get from pool
                if self.pool:
                    conn = self.pool.pop()
                    self.in_use.add(id(conn))
                    return conn

                # Create new if under limit
                if len(self.in_use) < self.max_size:
                    conn = self.create_connection()
                    self.in_use.add(id(conn))
                    return conn

                # Wait for connection to be released
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError("Connection pool timeout")

                self.condition.wait(timeout=self.timeout - elapsed)

    def release_connection(self, conn: Any) -> None:
        """
        Release connection back to pool.

        Args:
            conn: Connection to release
        """
        with self.condition:
            conn_id = id(conn)
            if conn_id in self.in_use:
                self.in_use.remove(conn_id)
                self.pool.append(conn)
                self.condition.notify()

    def close_all(self) -> None:
        """Close all connections in pool."""
        with self.lock:
            for conn in self.pool:
                if hasattr(conn, 'close'):
                    try:
                        conn.close()
                    except Exception as e:
                        logger.warning(f"Error closing connection: {e}")

            self.pool.clear()
            self.in_use.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                "pool_size": len(self.pool),
                "in_use": len(self.in_use),
                "max_size": self.max_size,
                "utilization": len(self.in_use) / self.max_size
            }


class MemoryManager:
    """
    Memory management utilities for monitoring and optimization.
    """

    @staticmethod
    def get_object_size(obj: Any) -> int:
        """
        Get approximate size of object in bytes.

        Args:
            obj: Object to measure

        Returns:
            Size in bytes
        """
        import sys

        size = sys.getsizeof(obj)

        # Handle collections recursively
        if isinstance(obj, dict):
            size += sum(
                MemoryManager.get_object_size(k) +
                MemoryManager.get_object_size(v)
                for k, v in obj.items()
            )
        elif isinstance(obj, (list, tuple, set)):
            size += sum(MemoryManager.get_object_size(item) for item in obj)

        return size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format bytes as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class QueryOptimizer:
    """
    Query optimization utilities for data operations.
    """

    @staticmethod
    def optimize_dataframe_query(
        df,
        filters: List[Tuple[str, str, Any]],
        select_columns: Optional[List[str]] = None
    ):
        """
        Optimize pandas DataFrame queries.

        Applies filters efficiently and selects only needed columns.

        Args:
            df: pandas DataFrame
            filters: List of (column, operator, value) tuples
            select_columns: Columns to select (None = all)

        Returns:
            Filtered and optimized DataFrame
        """
        import pandas as pd

        # Start with full dataframe
        result = df

        # Apply filters efficiently
        for column, operator, value in filters:
            if operator == '==':
                result = result[result[column] == value]
            elif operator == '!=':
                result = result[result[column] != value]
            elif operator == '>':
                result = result[result[column] > value]
            elif operator == '>=':
                result = result[result[column] >= value]
            elif operator == '<':
                result = result[result[column] < value]
            elif operator == '<=':
                result = result[result[column] <= value]
            elif operator == 'in':
                result = result[result[column].isin(value)]
            elif operator == 'not in':
                result = result[~result[column].isin(value)]

        # Select only needed columns
        if select_columns:
            result = result[select_columns]

        return result

    @staticmethod
    def create_index_recommendations(df, query_columns: List[str]) -> List[str]:
        """
        Generate index recommendations for frequently queried columns.

        Args:
            df: pandas DataFrame
            query_columns: Columns used in queries

        Returns:
            List of recommended index columns
        """
        recommendations = []

        for column in query_columns:
            if column in df.columns:
                # Recommend index if high cardinality
                unique_ratio = df[column].nunique() / len(df)
                if unique_ratio > 0.1:  # More than 10% unique values
                    recommendations.append(column)

        return recommendations


# Global caches for system-wide use
_model_cache = ModelCache(max_size=50, ttl_seconds=3600)
_data_cache = LRUCache(max_size=100)


def get_model_cache() -> ModelCache:
    """Get global model cache instance."""
    return _model_cache


def get_data_cache() -> LRUCache:
    """Get global data cache instance."""
    return _data_cache


def clear_all_caches() -> None:
    """Clear all global caches."""
    _model_cache.clear()
    _data_cache.clear()
    logger.info("All caches cleared")


def get_system_stats() -> Dict[str, Any]:
    """
    Get comprehensive system optimization statistics.

    Returns:
        Dictionary with all cache and optimization stats
    """
    return {
        "model_cache": _model_cache.get_stats(),
        "data_cache": _data_cache.get_stats(),
        "timestamp": datetime.now().isoformat()
    }
