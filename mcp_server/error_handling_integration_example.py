"""
Integration Example: Using Error Handling in NBA MCP Server

This module demonstrates how to integrate the comprehensive error handling
and logging infrastructure into the NBA MCP server tools and endpoints.

This is an example file showing integration patterns. The actual integration
should be done in the main server files.

Author: NBA MCP Server Team
Date: 2025-01-18
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import error handling
from .error_handling import (
    # Exceptions
    DataValidationError,
    ToolExecutionError,
    ServiceUnavailableError,
    CircuitBreakerOpenError,
    # Error context
    ErrorContext,
    # Decorators
    with_retry,
    handle_errors,
    # Error handler
    get_error_handler,
)

# Import logging
from .logging_config import (
    get_logger,
    RequestContext,
    PerformanceLogger,
    setup_logging,
)

# Initialize logging
logger = get_logger(__name__)


# ==============================================================================
# Example 1: Basic Tool with Error Handling
# ==============================================================================


@handle_errors(context={"tool": "query_database"})
@with_retry(max_retries=3, backoff_factor=2.0)
async def query_database_with_error_handling(sql: str) -> Dict[str, Any]:
    """
    Query database with comprehensive error handling.

    This example shows how to add error handling and retry logic
    to a database query tool.

    Args:
        sql: SQL query to execute

    Returns:
        Query results

    Raises:
        DataValidationError: If SQL is invalid
        ServiceUnavailableError: If database is unavailable
        ToolExecutionError: If query execution fails
    """
    # Validate input
    if not sql or not sql.strip():
        raise DataValidationError("SQL query cannot be empty", details={"sql": sql})

    # Create request context
    with RequestContext(logger, "query_database"):
        # Track performance
        perf = PerformanceLogger(logger)

        with perf.measure("database_query"):
            try:
                # Simulate database query
                logger.info(f"Executing query", extra={"sql": sql})

                # In real implementation, this would call the actual database
                # result = await db.execute(sql)

                result = {
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": 150,
                }

                logger.info(
                    f"Query completed successfully",
                    extra={
                        "row_count": result["row_count"],
                        "execution_time_ms": result["execution_time_ms"],
                    },
                )

                return result

            except ConnectionError as e:
                # Database connection failed
                raise ServiceUnavailableError(
                    "Database connection failed",
                    details={
                        "sql": sql,
                        "error": str(e),
                        "retry_after": 60,
                    },
                )
            except Exception as e:
                # Unexpected error
                raise ToolExecutionError(
                    f"Query execution failed: {e}",
                    details={
                        "sql": sql,
                        "error_type": type(e).__name__,
                    },
                )


# ==============================================================================
# Example 2: Tool with Circuit Breaker
# ==============================================================================


async def fetch_external_api_with_circuit_breaker(endpoint: str) -> Dict[str, Any]:
    """
    Fetch data from external API with circuit breaker protection.

    This example shows how to protect external API calls with
    a circuit breaker to prevent cascading failures.

    Args:
        endpoint: API endpoint to call

    Returns:
        API response data

    Raises:
        CircuitBreakerOpenError: If circuit breaker is open
        ServiceUnavailableError: If API is unavailable
    """
    # Get error handler and circuit breaker
    error_handler = get_error_handler()
    breaker = error_handler.get_circuit_breaker(
        name="external_api",
        failure_threshold=5,
        timeout=60,
        expected_exception=ServiceUnavailableError,
    )

    @breaker.protect
    @with_retry(max_retries=2, backoff_factor=1.5)
    async def _fetch():
        """Inner function protected by circuit breaker."""
        with RequestContext(logger, "fetch_external_api"):
            logger.info(f"Fetching from API", extra={"endpoint": endpoint})

            try:
                # Simulate API call
                # In real implementation: response = await http_client.get(endpoint)

                response = {
                    "data": [],
                    "status": 200,
                }

                return response

            except Exception as e:
                raise ServiceUnavailableError(
                    f"API call failed: {e}", details={"endpoint": endpoint}
                )

    return await _fetch()


# ==============================================================================
# Example 3: Complex Operation with Multiple Error Handling Layers
# ==============================================================================


@handle_errors(context={"operation": "player_stats_analysis"})
async def analyze_player_stats_comprehensive(
    player_id: str, season: str
) -> Dict[str, Any]:
    """
    Comprehensive player stats analysis with full error handling.

    This example demonstrates a complex operation that:
    - Uses request context for tracking
    - Performs multiple sub-operations with retry
    - Handles various error types
    - Tracks performance metrics
    - Uses circuit breakers for external calls

    Args:
        player_id: Player identifier
        season: Season identifier (e.g., "2023-24")

    Returns:
        Comprehensive player statistics and analysis

    Raises:
        DataValidationError: If input parameters are invalid
        ToolExecutionError: If analysis fails
    """
    # Validate inputs
    if not player_id:
        raise DataValidationError(
            "Player ID is required", details={"player_id": player_id}
        )

    if not season or len(season) != 7:
        raise DataValidationError(
            "Invalid season format (expected: YYYY-YY)", details={"season": season}
        )

    # Create request context with tracking
    with RequestContext(
        logger,
        "analyze_player_stats",
        client_id="internal",
        request_id=f"analysis_{player_id}_{season}",
    ):
        logger.info(
            f"Starting player analysis",
            extra={"player_id": player_id, "season": season},
        )

        result = {
            "player_id": player_id,
            "season": season,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        # Step 1: Fetch player data (with retry and circuit breaker)
        try:
            perf = PerformanceLogger(logger)

            with perf.measure("fetch_player_data"):
                player_data = await fetch_player_data_with_protection(player_id, season)
                result["player_data"] = player_data

        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, return cached data or error
            logger.warning(
                f"Circuit breaker open for player data", extra={"player_id": player_id}
            )
            result["player_data"] = None
            result["player_data_error"] = "Service temporarily unavailable"

        # Step 2: Calculate advanced stats (with retry)
        try:
            with perf.measure("calculate_stats"):
                stats = await calculate_advanced_stats_with_retry(player_data)
                result["advanced_stats"] = stats

        except Exception as e:
            logger.error(
                f"Failed to calculate advanced stats: {e}",
                extra={"player_id": player_id},
            )
            result["advanced_stats"] = None
            result["stats_error"] = str(e)

        # Step 3: Compare with league averages (best effort)
        try:
            with perf.measure("league_comparison"):
                comparison = await compare_with_league_averages(stats, season)
                result["league_comparison"] = comparison

        except Exception as e:
            # Non-critical, log but don't fail
            logger.warning(
                f"Could not compare with league averages: {e}",
                extra={"player_id": player_id},
            )
            result["league_comparison"] = None

        logger.info(
            f"Player analysis completed",
            extra={
                "player_id": player_id,
                "has_player_data": result.get("player_data") is not None,
                "has_stats": result.get("advanced_stats") is not None,
            },
        )

        return result


# ==============================================================================
# Helper Functions (Simulated)
# ==============================================================================


@with_retry(max_retries=3, backoff_factor=2.0)
async def fetch_player_data_with_protection(
    player_id: str, season: str
) -> Dict[str, Any]:
    """Fetch player data with retry protection."""
    # Get circuit breaker
    error_handler = get_error_handler()
    breaker = error_handler.get_circuit_breaker(
        name="player_data_api",
        failure_threshold=5,
        timeout=30,
    )

    @breaker.protect
    async def _fetch():
        # Simulate API call
        logger.debug(f"Fetching player data", extra={"player_id": player_id})

        # In real implementation: data = await api.get_player(player_id, season)

        return {
            "player_id": player_id,
            "name": "Example Player",
            "games_played": 82,
            "points_per_game": 25.0,
        }

    return await _fetch()


@with_retry(max_retries=2, backoff_factor=1.5)
async def calculate_advanced_stats_with_retry(
    player_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate advanced stats with retry."""
    if not player_data:
        raise DataValidationError("Player data is required")

    logger.debug("Calculating advanced stats")

    # Simulate calculation
    return {
        "per": 25.5,
        "true_shooting_pct": 0.585,
        "usage_rate": 28.5,
        "bpm": 6.2,
    }


async def compare_with_league_averages(
    stats: Dict[str, Any], season: str
) -> Dict[str, Any]:
    """Compare stats with league averages (best effort)."""
    logger.debug(f"Comparing with league averages", extra={"season": season})

    # Simulate comparison
    return {
        "per_percentile": 85,
        "ts_pct_percentile": 90,
        "usage_percentile": 75,
    }


# ==============================================================================
# Example 4: Error Handler Statistics and Monitoring
# ==============================================================================


async def get_error_statistics() -> Dict[str, Any]:
    """
    Get comprehensive error statistics for monitoring.

    This can be exposed as a health check endpoint or monitoring tool.

    Returns:
        Error statistics and circuit breaker status
    """
    error_handler = get_error_handler()
    stats = error_handler.get_error_stats()

    # Add additional monitoring data
    stats["timestamp"] = datetime.now().isoformat()

    # Add circuit breaker health
    stats["circuit_breaker_health"] = {
        name: breaker.state.value
        for name, breaker in error_handler.circuit_breakers.items()
    }

    return stats


# ==============================================================================
# Example 5: Custom Error Recovery
# ==============================================================================


async def fetch_with_fallback(
    primary_source: str, fallback_source: str
) -> Dict[str, Any]:
    """
    Fetch data with automatic fallback on failure.

    This example shows graceful degradation by falling back to
    an alternative data source if the primary fails.

    Args:
        primary_source: Primary data source
        fallback_source: Fallback data source

    Returns:
        Data from primary or fallback source
    """
    error_handler = get_error_handler()

    # Try primary source
    try:
        with RequestContext(logger, "fetch_primary"):
            logger.info(f"Fetching from primary source: {primary_source}")

            # Simulate fetch
            data = {"source": "primary", "data": []}

            return data

    except Exception as e:
        # Log primary failure
        error_context = ErrorContext(
            operation="fetch_primary", additional_context={"source": primary_source}
        )
        error_handler.handle_error(e, error_context, reraise=False)

        # Try fallback
        try:
            with RequestContext(logger, "fetch_fallback"):
                logger.warning(
                    f"Primary source failed, using fallback: {fallback_source}",
                    extra={"primary_error": str(e)},
                )

                # Simulate fallback fetch
                data = {"source": "fallback", "data": []}

                return data

        except Exception as fallback_error:
            # Both failed
            error_context = ErrorContext(
                operation="fetch_fallback",
                additional_context={"source": fallback_source},
            )
            error_handler.handle_error(
                fallback_error,
                error_context,
                notify=True,  # Alert on complete failure
                reraise=True,
            )


# ==============================================================================
# Main Demo
# ==============================================================================


async def demo_error_handling():
    """Demonstrate error handling integration."""
    # Setup logging
    setup_logging(
        log_level="INFO",
        enable_json=False,
        enable_console=True,
        enable_file=False,
    )

    logger.info("=== Error Handling Integration Demo ===\n")

    # Demo 1: Basic query with retry
    logger.info("Demo 1: Query with error handling and retry")
    try:
        result = await query_database_with_error_handling("SELECT * FROM games")
        logger.info(f"Query result: {result}")
    except Exception as e:
        logger.error(f"Query failed: {e}")

    # Demo 2: Circuit breaker
    logger.info("\nDemo 2: External API with circuit breaker")
    try:
        result = await fetch_external_api_with_circuit_breaker("/api/players")
        logger.info(f"API result: {result}")
    except CircuitBreakerOpenError as e:
        logger.warning(f"Circuit breaker open: {e}")

    # Demo 3: Complex operation
    logger.info("\nDemo 3: Complex player analysis")
    try:
        result = await analyze_player_stats_comprehensive("player_001", "2023-24")
        logger.info(f"Analysis result keys: {list(result.keys())}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

    # Demo 4: Error statistics
    logger.info("\nDemo 4: Error statistics")
    stats = await get_error_statistics()
    logger.info(f"Total errors: {stats['total_errors']}")
    logger.info(f"Error rate: {stats['error_rate_per_minute']}/min")

    # Demo 5: Fallback strategy
    logger.info("\nDemo 5: Fetch with fallback")
    try:
        result = await fetch_with_fallback("primary_api", "backup_api")
        logger.info(f"Fetch result source: {result['source']}")
    except Exception as e:
        logger.error(f"All sources failed: {e}")

    logger.info("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(demo_error_handling())
