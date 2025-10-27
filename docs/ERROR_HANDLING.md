# Error Handling Guide

Comprehensive guide to error handling in the NBA MCP Server.

## Table of Contents

1. [Overview](#overview)
2. [Custom Exceptions](#custom-exceptions)
3. [Error Context](#error-context)
4. [Retry Logic](#retry-logic)
5. [Circuit Breaker](#circuit-breaker)
6. [Error Handler](#error-handler)
7. [Integration Patterns](#integration-patterns)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The NBA MCP Server includes a comprehensive error handling system that provides:

- **Custom exception hierarchy** for clear error categorization
- **Retry logic** with multiple strategies (exponential backoff, linear, etc.)
- **Circuit breaker pattern** to prevent cascading failures
- **Error tracking and metrics** for monitoring and alerting
- **Graceful degradation** strategies for resilience
- **Context-aware error handling** with detailed debugging information

### Key Features

- 🔄 **Automatic retry** with configurable strategies
- 🛡️ **Circuit breakers** to protect against service failures
- 📊 **Error metrics** and statistics
- 🔍 **Detailed error context** for debugging
- ⚡ **Async/sync support** for all decorators
- 🎯 **Graceful degradation** with fallback mechanisms

## Custom Exceptions

The system provides a hierarchy of custom exceptions extending the existing error infrastructure.

### Exception Hierarchy

```
NBAMCPError (base from error_handler.py)
├── DataValidationError
├── ToolExecutionError
├── ConfigurationError
├── ServiceUnavailableError
├── CircuitBreakerOpenError
├── AuthenticationError
├── DatabaseError
├── RateLimitError
└── NotFoundError
```

### Using Custom Exceptions

```python
from mcp_server.error_handling import (
    DataValidationError,
    ToolExecutionError,
    ServiceUnavailableError,
)

# Data validation error
if not player_id:
    raise DataValidationError(
        "Player ID is required",
        details={"field": "player_id", "value": None}
    )

# Tool execution error
try:
    result = execute_complex_operation()
except Exception as e:
    raise ToolExecutionError(
        f"Operation failed: {e}",
        details={"operation": "complex_op", "error": str(e)}
    )

# Service unavailable error
raise ServiceUnavailableError(
    "Database connection failed",
    details={"service": "postgresql", "retry_after": 60}
)
```

### Error Attributes

All custom exceptions include:

- `message`: Human-readable error message
- `category`: Error category (from ErrorCategory enum)
- `severity`: Error severity (from ErrorSeverity enum)
- `details`: Dictionary with additional context
- `timestamp`: When the error occurred
- `error_code`: Unique error code string

### Error Serialization

Convert errors to dictionaries for API responses:

```python
try:
    result = risky_operation()
except DataValidationError as e:
    error_dict = e.to_dict()
    # Returns:
    # {
    #     "error": "Player ID is required",
    #     "category": "validation",
    #     "severity": "low",
    #     "details": {"field": "player_id"},
    #     "timestamp": "2025-01-18T12:00:00"
    # }
```

## Error Context

Use `ErrorContext` to provide detailed context about where and when errors occur.

### Creating Error Context

```python
from mcp_server.error_handling import ErrorContext

# Basic context
context = ErrorContext(
    tool_name="query_database",
    user_id="user_123",
    request_id="req_456",
    operation="SELECT query"
)

# With additional context
context = ErrorContext(
    tool_name="analyze_player",
    additional_context={
        "player_id": "player_001",
        "season": "2023-24",
        "analysis_type": "advanced_stats"
    }
)

# Convert to dictionary for logging
context_dict = context.to_dict()
```

### Using Context with Error Handler

```python
from mcp_server.error_handling import get_error_handler, ErrorContext

handler = get_error_handler()

try:
    result = query_database(sql)
except Exception as e:
    context = ErrorContext(
        tool_name="query_database",
        operation="execute_query",
        additional_context={"sql": sql}
    )
    handler.handle_error(e, context)
```

## Retry Logic

Automatic retry with multiple strategies and configurable backoff.

### Basic Retry Decorator

```python
from mcp_server.error_handling import with_retry

# Simple retry with defaults (3 retries, exponential backoff)
@with_retry()
async def query_database(sql: str):
    return await db.execute(sql)

# Custom retry configuration
@with_retry(
    max_retries=5,
    backoff_factor=2.0,
    retry_on=(DatabaseError, ServiceUnavailableError)
)
async def fetch_player_data(player_id: str):
    return await api.get_player(player_id)
```

### Retry Strategies

The system supports multiple retry strategies:

1. **Exponential Backoff** (default)
   - Delay: base_delay * (backoff_factor ^ attempt)
   - Best for: Most use cases
   - Example: 1s, 2s, 4s, 8s, 16s...

2. **Linear Backoff**
   - Delay: base_delay * (attempt + 1)
   - Best for: Predictable retry intervals
   - Example: 1s, 2s, 3s, 4s, 5s...

3. **Fixed Delay**
   - Delay: base_delay (constant)
   - Best for: Simple, predictable retries
   - Example: 2s, 2s, 2s, 2s, 2s...

4. **Fibonacci Backoff**
   - Delay: base_delay * fibonacci(attempt)
   - Best for: Graceful backoff with moderate growth
   - Example: 1s, 1s, 2s, 3s, 5s, 8s...

```python
from mcp_server.error_handling import with_retry, RetryStrategy

# Exponential backoff (default)
@with_retry(
    max_retries=3,
    backoff_factor=2.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)
async def operation_exponential():
    pass

# Linear backoff
@with_retry(
    max_retries=5,
    strategy=RetryStrategy.LINEAR_BACKOFF
)
async def operation_linear():
    pass

# Fixed delay
@with_retry(
    max_retries=3,
    strategy=RetryStrategy.FIXED_DELAY,
    base_delay=2.0
)
async def operation_fixed():
    pass

# Fibonacci backoff
@with_retry(
    max_retries=6,
    strategy=RetryStrategy.FIBONACCI_BACKOFF
)
async def operation_fibonacci():
    pass
```

### Retry Configuration Options

```python
@with_retry(
    max_retries=3,              # Maximum retry attempts
    backoff_factor=2.0,         # Backoff multiplier
    retry_on=(Exception,),      # Exceptions to retry on
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    on_retry=callback_function  # Optional callback on each retry
)
```

### Retry Callback

Execute custom logic on each retry:

```python
def on_retry_callback(error: Exception, attempt: int):
    logger.warning(f"Retry attempt {attempt} after {type(error).__name__}")
    # Send metric, update counter, etc.

@with_retry(
    max_retries=3,
    on_retry=on_retry_callback
)
async def operation_with_callback():
    pass
```

### Synchronous and Asynchronous Support

The retry decorator automatically detects function type:

```python
# Async function
@with_retry(max_retries=3)
async def async_operation():
    return await some_async_call()

# Sync function
@with_retry(max_retries=3)
def sync_operation():
    return some_sync_call()
```

## Circuit Breaker

Prevent cascading failures by temporarily blocking operations that are likely to fail.

### Circuit Breaker States

1. **CLOSED** (Normal operation)
   - All calls go through
   - Failures are counted
   - Opens when failure threshold reached

2. **OPEN** (Blocking calls)
   - All calls immediately fail
   - No actual operations executed
   - After timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing recovery)
   - Limited calls allowed through
   - Success closes circuit
   - Failure reopens circuit

### Basic Circuit Breaker Usage

```python
from mcp_server.error_handling import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    name="database_queries",
    failure_threshold=5,    # Open after 5 failures
    success_threshold=2,    # Close after 2 successes
    timeout=60,            # Try to recover after 60 seconds
    expected_exception=DatabaseError
)

# Protect a function
@breaker.protect
async def query_database(sql: str):
    return await db.execute(sql)
```

### Using Circuit Breaker with Error Handler

```python
from mcp_server.error_handling import get_error_handler

# Get error handler
handler = get_error_handler()

# Get or create circuit breaker
breaker = handler.get_circuit_breaker(
    name="external_api",
    failure_threshold=5,
    timeout=30
)

# Use circuit breaker
@breaker.protect
async def call_external_api():
    return await api.fetch_data()
```

### Circuit Breaker Callbacks

Execute custom logic on state changes:

```python
def on_circuit_open():
    logger.critical("Circuit breaker opened!")
    send_alert("Circuit breaker triggered")

def on_circuit_close():
    logger.info("Circuit breaker closed, service recovered")

breaker = CircuitBreaker(
    name="critical_service",
    failure_threshold=3,
    timeout=60,
    on_open=on_circuit_open,
    on_close=on_circuit_close
)
```

### Circuit Breaker Statistics

```python
# Get statistics
stats = breaker.get_stats()

# Returns:
# {
#     "name": "database_queries",
#     "state": "closed",
#     "stats": {
#         "failure_count": 10,
#         "success_count": 100,
#         "consecutive_failures": 0,
#         "consecutive_successes": 5,
#         "last_failure_time": "2025-01-18T10:00:00",
#         "last_success_time": "2025-01-18T12:00:00",
#         "total_state_changes": 3
#     },
#     "config": {
#         "failure_threshold": 5,
#         "success_threshold": 2,
#         "timeout": 60
#     }
# }
```

### Handling Circuit Breaker Open Error

```python
from mcp_server.error_handling import CircuitBreakerOpenError

try:
    result = await protected_operation()
except CircuitBreakerOpenError as e:
    # Circuit is open, use fallback or return cached data
    logger.warning(f"Circuit breaker is open: {e}")
    result = get_cached_data()
```

## Error Handler

Centralized error handling with tracking, metrics, and alerting.

### Using Error Handler

```python
from mcp_server.error_handling import get_error_handler, ErrorContext

# Get global error handler
handler = get_error_handler()

# Handle an error
try:
    result = risky_operation()
except Exception as e:
    context = ErrorContext(
        tool_name="risky_operation",
        operation="execute"
    )
    handler.handle_error(
        error=e,
        context=context,
        notify=True,     # Send alerts for this error
        reraise=False    # Don't re-raise after handling
    )
```

### Error Statistics

```python
# Get comprehensive error statistics
stats = handler.get_error_stats()

# Returns:
# {
#     "total_errors": 150,
#     "errors_by_type": {
#         "validation:DataValidationError": 50,
#         "internal:ToolExecutionError": 30,
#         "external_api:ServiceUnavailableError": 70
#     },
#     "error_rate_per_minute": 5,
#     "recent_errors": [
#         {
#             "timestamp": "2025-01-18T12:00:00",
#             "error": "Database connection failed",
#             "category": "external_api",
#             "severity": "high"
#         },
#         # ... more errors
#     ],
#     "circuit_breakers": {
#         "database_queries": {
#             "state": "closed",
#             "stats": {...}
#         }
#     }
# }
```

### Custom Error Handler Instance

```python
from mcp_server.error_handling import ErrorHandler, set_error_handler

# Create custom error handler
custom_handler = ErrorHandler(enable_alerting=True)

# Set as global instance
set_error_handler(custom_handler)

# Now all calls to get_error_handler() return this instance
```

## Integration Patterns

Common patterns for integrating error handling into your code.

### Pattern 1: Basic Tool with Retry

```python
from mcp_server.error_handling import with_retry, DataValidationError

@with_retry(max_retries=3)
async def query_tool(sql: str) -> dict:
    if not sql:
        raise DataValidationError("SQL query required")

    return await db.execute(sql)
```

### Pattern 2: Tool with Circuit Breaker

```python
from mcp_server.error_handling import get_error_handler

async def external_api_tool(endpoint: str) -> dict:
    handler = get_error_handler()
    breaker = handler.get_circuit_breaker(
        name="external_api",
        failure_threshold=5
    )

    @breaker.protect
    @with_retry(max_retries=2)
    async def _fetch():
        return await api.get(endpoint)

    return await _fetch()
```

### Pattern 3: Comprehensive Error Handling

```python
from mcp_server.error_handling import (
    handle_errors,
    with_retry,
    ErrorContext,
    get_error_handler,
)

@handle_errors(context={"tool": "analyze_player"})
async def analyze_player_tool(player_id: str) -> dict:
    # Get circuit breaker
    handler = get_error_handler()
    breaker = handler.get_circuit_breaker("player_api")

    # Fetch data with protection
    @breaker.protect
    @with_retry(max_retries=3)
    async def fetch_data():
        return await api.get_player(player_id)

    try:
        data = await fetch_data()
        stats = calculate_stats(data)
        return {"player_id": player_id, "stats": stats}

    except CircuitBreakerOpenError:
        # Graceful degradation: return cached data
        return get_cached_player_stats(player_id)
```

### Pattern 4: Graceful Degradation with Fallback

```python
async def fetch_with_fallback(
    primary_source: str,
    fallback_source: str
) -> dict:
    handler = get_error_handler()

    # Try primary
    try:
        return await fetch_from_source(primary_source)
    except Exception as e:
        error_context = ErrorContext(
            operation="fetch_primary",
            additional_context={"source": primary_source}
        )
        handler.handle_error(e, error_context, reraise=False)

        # Try fallback
        try:
            return await fetch_from_source(fallback_source)
        except Exception as fallback_error:
            # Both failed, alert and raise
            error_context = ErrorContext(
                operation="fetch_fallback",
                additional_context={"source": fallback_source}
            )
            handler.handle_error(
                fallback_error,
                error_context,
                notify=True,
                reraise=True
            )
```

### Pattern 5: Error Statistics Endpoint

```python
async def get_health_status() -> dict:
    """Health check endpoint with error statistics."""
    handler = get_error_handler()
    stats = handler.get_error_stats()

    return {
        "status": "healthy" if stats["error_rate_per_minute"] < 10 else "degraded",
        "error_rate": stats["error_rate_per_minute"],
        "total_errors": stats["total_errors"],
        "circuit_breakers": {
            name: breaker["state"]
            for name, breaker in stats["circuit_breakers"].items()
        }
    }
```

## Best Practices

### 1. Choose Appropriate Retry Strategy

- **Exponential backoff**: Most use cases (database, external APIs)
- **Linear backoff**: When you want predictable intervals
- **Fixed delay**: Simple cases with consistent timing
- **Fibonacci backoff**: Moderate growth for graceful recovery

### 2. Set Reasonable Retry Limits

```python
# Too few retries (might fail on transient issues)
@with_retry(max_retries=1)  # ❌ May not be enough

# Too many retries (delays user response)
@with_retry(max_retries=10)  # ❌ Too many

# Reasonable retry count
@with_retry(max_retries=3)  # ✅ Good balance
```

### 3. Use Circuit Breakers for External Services

```python
# Always protect external service calls
handler = get_error_handler()
breaker = handler.get_circuit_breaker(
    name="external_api",
    failure_threshold=5,
    timeout=60
)

@breaker.protect
@with_retry(max_retries=2)
async def call_external_api():
    return await api.fetch()
```

### 4. Provide Detailed Error Context

```python
# Bad: Minimal context
raise ToolExecutionError("Query failed")

# Good: Detailed context
raise ToolExecutionError(
    "Query failed",
    details={
        "sql": sql,
        "error_code": error_code,
        "affected_tables": ["games", "players"],
        "execution_time_ms": 1500
    }
)
```

### 5. Implement Graceful Degradation

```python
# Always have a fallback strategy
try:
    return await primary_operation()
except CircuitBreakerOpenError:
    # Return cached data or degraded response
    return get_cached_data()
except Exception as e:
    # Log and return safe default
    logger.error(f"Operation failed: {e}")
    return get_default_response()
```

### 6. Monitor Error Rates

```python
# Periodically check error statistics
async def monitor_errors():
    handler = get_error_handler()
    stats = handler.get_error_stats()

    if stats["error_rate_per_minute"] > 10:
        alert("High error rate detected")

    for name, breaker in stats["circuit_breakers"].items():
        if breaker["state"] == "open":
            alert(f"Circuit breaker {name} is open")
```

### 7. Clear Stats in Tests

```python
# Clear stats between tests
def test_error_handling():
    handler = get_error_handler()
    handler.clear_stats()  # Start with clean slate

    # Test code...

    assert handler.get_stats()["total_errors"] == expected_count
```

## Troubleshooting

### Common Issues

#### Issue 1: All Retries Exhausted

**Symptom**: Function fails after all retry attempts

**Solution**:
```python
# Check if retry count is appropriate
@with_retry(max_retries=5)  # Increase if needed

# Check if exception is being caught
@with_retry(
    retry_on=(SpecificError,)  # Make sure to include all retriable errors
)

# Add retry callback to debug
def debug_retry(error, attempt):
    logger.debug(f"Retry {attempt}: {error}")

@with_retry(on_retry=debug_retry)
```

#### Issue 2: Circuit Breaker Stuck Open

**Symptom**: Circuit breaker remains open even after service recovers

**Solution**:
```python
# Check timeout configuration
breaker = CircuitBreaker(
    name="service",
    timeout=30  # Increase if service takes longer to recover
)

# Check success threshold
breaker = CircuitBreaker(
    name="service",
    success_threshold=1  # Lower threshold for faster recovery
)

# Manual reset if needed
breaker.state = CircuitBreakerState.CLOSED
breaker.stats.consecutive_failures = 0
```

#### Issue 3: Errors Not Being Tracked

**Symptom**: Error statistics show zero errors

**Solution**:
```python
# Make sure to use the error handler
handler = get_error_handler()

try:
    risky_operation()
except Exception as e:
    handler.handle_error(e, reraise=False)  # Don't forget to call handle_error

# Or use decorator
@handle_errors()
async def operation():
    pass
```

#### Issue 4: Performance Impact from Retries

**Symptom**: Requests taking too long due to retry delays

**Solution**:
```python
# Reduce retry count
@with_retry(max_retries=2)  # Fewer retries

# Use faster backoff strategy
@with_retry(
    strategy=RetryStrategy.FIXED_DELAY,
    base_delay=0.5  # Shorter delays
)

# Or reduce backoff factor
@with_retry(backoff_factor=1.5)  # Slower growth
```

### Debugging Tips

1. **Enable debug logging**:
   ```python
   import logging
   logging.getLogger("mcp_server.error_handling").setLevel(logging.DEBUG)
   ```

2. **Check error statistics**:
   ```python
   stats = handler.get_error_stats()
   print(json.dumps(stats, indent=2))
   ```

3. **Monitor circuit breaker states**:
   ```python
   for name, breaker in handler.circuit_breakers.items():
       print(f"{name}: {breaker.state.value}")
   ```

4. **Add custom logging in retry callback**:
   ```python
   def debug_callback(error, attempt):
       logger.debug(f"Retry {attempt}: {type(error).__name__}: {error}")

   @with_retry(on_retry=debug_callback)
   async def operation():
       pass
   ```

## Additional Resources

- **Example Integration**: See `mcp_server/error_handling_integration_example.py`
- **Tests**: See `tests/test_error_handling.py`
- **Logging Guide**: See `docs/LOGGING.md`
- **API Reference**: See module docstrings in `mcp_server/error_handling.py`

## Support

For questions or issues:
1. Check the test files for usage examples
2. Review the integration example file
3. Enable debug logging for detailed information
4. Check error statistics for patterns
