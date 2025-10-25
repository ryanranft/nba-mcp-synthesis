# Logging Configuration Guide

Comprehensive guide to structured logging in the NBA MCP Server.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Formatters](#formatters)
4. [Performance Logging](#performance-logging)
5. [Request Context](#request-context)
6. [Log Configuration](#log-configuration)
7. [Best Practices](#best-practices)
8. [Log Analysis](#log-analysis)
9. [Troubleshooting](#troubleshooting)

## Overview

The NBA MCP Server uses structured logging with JSON formatting for production environments and human-readable colored output for development.

### Key Features

- 📝 **JSON structured logging** for easy parsing and analysis
- 🎨 **Colored console output** for development
- 🔄 **Automatic log rotation** by size and time
- 📊 **Performance metrics tracking** with timing data
- 🔍 **Request context tracking** with IDs
- 📂 **Multiple log files** (application, errors, performance, access)
- ⚡ **Contextual logging** with automatic field injection

## Quick Start

### Basic Setup

```python
from mcp_server.logging_config import setup_logging, get_logger

# Setup logging (call once at application startup)
setup_logging(
    log_level="INFO",
    log_dir="logs",
    enable_json=True,
    enable_console=True,
    enable_file=True,
)

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

### Quick Example

```python
from mcp_server.logging_config import (
    setup_logging,
    get_logger,
    RequestContext,
    PerformanceLogger,
)

# Setup
setup_logging(log_level="INFO")
logger = get_logger(__name__)

# Use request context for tracking
with RequestContext(logger, "process_query", client_id="client_123"):
    logger.info("Processing query")

    # Track performance
    perf = PerformanceLogger(logger)
    with perf.measure("database_query"):
        # Your code here
        result = query_database()

    logger.info("Query completed", extra={"result_count": len(result)})
```

## Formatters

### JSON Formatter

Outputs logs in JSON format for structured logging systems (ELK, Splunk, etc.).

#### Features

- Structured JSON output
- Automatic timestamp in ISO format
- Exception details with traceback
- Request context (request_id, client_id)
- Custom extra fields
- Machine-readable format

#### Example Output

```json
{
  "timestamp": "2025-01-18T12:00:00.123Z",
  "level": "INFO",
  "logger": "mcp_server.tools",
  "message": "Query executed successfully",
  "module": "query_tools",
  "function": "execute_query",
  "line": 42,
  "request_id": "req_abc123",
  "client_id": "client_456",
  "operation": "database_query",
  "duration_ms": 150.5,
  "rows_returned": 100
}
```

#### Usage

```python
from mcp_server.logging_config import JSONFormatter

formatter = JSONFormatter(include_extra=True)
handler.setFormatter(formatter)
```

### Colored Formatter

Human-readable colored output for console (development).

#### Features

- Color-coded log levels
- Timestamp formatting
- Request ID display (truncated)
- Exception formatting
- Easy to read during development

#### Example Output

```
2025-01-18 12:00:00.123 INFO     mcp_server.tools [req_abc1]: Query executed successfully
```

#### Usage

```python
from mcp_server.logging_config import ColoredFormatter

formatter = ColoredFormatter()
handler.setFormatter(formatter)
```

### Choosing a Formatter

- **JSON Formatter**: Use in production for log aggregation
- **Colored Formatter**: Use in development for readability

```python
# Development
setup_logging(
    log_level="DEBUG",
    enable_json=False,  # Use colored output
    enable_file=False    # Console only
)

# Production
setup_logging(
    log_level="INFO",
    enable_json=True,   # Use JSON output
    enable_file=True     # Write to files
)
```

## Performance Logging

Track execution time and resource usage.

### PerformanceLogger Class

#### Basic Usage

```python
from mcp_server.logging_config import PerformanceLogger, get_logger

logger = get_logger(__name__)
perf = PerformanceLogger(logger)

# Start/end tracking
perf.start("database_query")
result = execute_query()
perf.end("database_query")
```

#### Context Manager (Recommended)

```python
# Automatic timing with context manager
with perf.measure("database_query"):
    result = execute_query()

# Logs:
# - Start: "Started: database_query" (DEBUG level)
# - End: "Completed: database_query" (INFO level)
#   with extra fields: {"duration_ms": 150.5, "success": True}
```

#### With Extra Fields

```python
perf.end("database_query", query="SELECT *", rows=100)

# Logs with extra fields:
# {
#   "operation": "database_query",
#   "duration_ms": 150.5,
#   "query": "SELECT *",
#   "rows": 100
# }
```

#### Error Handling

```python
try:
    with perf.measure("risky_operation"):
        result = risky_function()
except Exception:
    # Automatically logs error with performance data
    # {
    #   "operation": "risky_operation",
    #   "duration_ms": 50.0,
    #   "success": False,
    #   "error": "ValueError: Something went wrong"
    # }
    pass
```

### Helper Function

```python
from mcp_server.logging_config import log_performance

# Quick performance logging
log_performance(
    logger,
    "query_operation",
    duration_ms=150.5,
    query="SELECT *",
    rows=100
)
```

## Request Context

Track requests with automatic ID assignment and lifecycle logging.

### RequestContext Class

#### Basic Usage

```python
from mcp_server.logging_config import RequestContext, get_logger

logger = get_logger(__name__)

with RequestContext(logger, "process_query"):
    # All logs within this context will include request_id
    logger.info("Processing started")
    result = process_data()
    logger.info("Processing completed")

# Logs:
# - Request started: process_query (with request_id, phase: start)
# - Your log messages (with request_id)
# - Request completed: process_query (with request_id, phase: complete, duration_ms)
```

#### With Client ID

```python
with RequestContext(
    logger,
    "process_query",
    client_id="client_123"
):
    # All logs include both request_id and client_id
    logger.info("Processing for client")
```

#### Custom Request ID

```python
with RequestContext(
    logger,
    "process_query",
    request_id="custom_req_id"
):
    logger.info("Using custom request ID")
```

#### Automatic Context Variables

```python
from mcp_server.logging_config import request_id_var, client_id_var

# Within RequestContext, these are automatically set
with RequestContext(logger, "operation", request_id="req_123"):
    # Access context variables
    current_request_id = request_id_var.get()  # "req_123"

# Outside context, they are None
current_request_id = request_id_var.get()  # None
```

### Helper Function

```python
from mcp_server.logging_config import log_request

# Quick request logging
log_request(
    logger,
    "query_operation",
    user_id="user_123",
    query="SELECT *"
)
```

## Log Configuration

### setup_logging() Function

Complete logging configuration in one call.

#### Parameters

```python
setup_logging(
    log_level="INFO",           # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir="logs",             # Directory for log files
    enable_json=True,           # Use JSON formatting
    enable_console=True,        # Enable console output
    enable_file=True,           # Enable file logging
    max_file_size_mb=100,       # Max size per log file
    backup_count=5              # Number of backup files
)
```

#### Log Files Created

When `enable_file=True`, the following files are created:

1. **application.log**: All log messages (DEBUG and above)
2. **errors.log**: Only ERROR and CRITICAL messages
3. **performance.log**: Only logs with `duration_ms` field
4. **access.log**: Only logs with `request_id` field

#### Examples

##### Development Configuration

```python
setup_logging(
    log_level="DEBUG",
    enable_json=False,      # Colored output
    enable_console=True,    # Show in console
    enable_file=False       # Don't write files
)
```

##### Production Configuration

```python
setup_logging(
    log_level="INFO",
    log_dir="/var/log/nba-mcp",
    enable_json=True,       # JSON for parsing
    enable_console=True,    # Also show in console
    enable_file=True,       # Write to files
    max_file_size_mb=100,   # 100MB per file
    backup_count=10         # Keep 10 backups
)
```

##### Testing Configuration

```python
setup_logging(
    log_level="WARNING",    # Reduce noise
    enable_console=False,   # No console output
    enable_file=False       # No file output
)
```

### Log Levels

Choose appropriate log level:

- **DEBUG**: Detailed diagnostic information
  ```python
  logger.debug("Variable x = %s", x)
  ```

- **INFO**: General informational messages
  ```python
  logger.info("Processing started")
  ```

- **WARNING**: Warning messages (non-critical)
  ```python
  logger.warning("Retry attempt %d failed", attempt)
  ```

- **ERROR**: Error messages (recoverable)
  ```python
  logger.error("Failed to connect to database")
  ```

- **CRITICAL**: Critical errors (system failure)
  ```python
  logger.critical("Database connection pool exhausted")
  ```

## Best Practices

### 1. Use Structured Logging

Always use extra fields for structured data:

```python
# Bad: String interpolation
logger.info(f"Query returned {count} rows in {duration}ms")

# Good: Structured fields
logger.info(
    "Query completed",
    extra={
        "row_count": count,
        "duration_ms": duration,
        "query_type": "SELECT"
    }
)
```

### 2. Use Request Context for All Operations

```python
# Wrap operations in RequestContext
with RequestContext(logger, "user_operation", client_id=client_id):
    # All logs automatically include request_id and client_id
    logger.info("Operation started")
    result = perform_operation()
    logger.info("Operation completed")
```

### 3. Track Performance for All Operations

```python
# Always track timing for operations
perf = PerformanceLogger(logger)

with perf.measure("database_query"):
    result = db.execute(query)

with perf.measure("api_call"):
    response = api.fetch_data()
```

### 4. Log Exceptions Properly

```python
# Bad: Convert exception to string
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")

# Good: Include exception info
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            "operation": "risky_operation",
            "error_type": type(e).__name__
        },
        exc_info=True  # Include full traceback
    )
```

### 5. Use Helper Functions

```python
from mcp_server.logging_config import log_error, log_performance, log_request

# Quick error logging
try:
    result = operation()
except Exception as e:
    log_error(logger, "operation_name", e, user_id="user_123")

# Quick performance logging
log_performance(logger, "query", duration_ms=150.5, rows=100)

# Quick request logging
log_request(logger, "api_call", endpoint="/players")
```

### 6. Configure Once at Startup

```python
# In main application entry point
def main():
    # Setup logging first thing
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=os.getenv("LOG_DIR", "logs"),
        enable_json=os.getenv("ENVIRONMENT") == "production"
    )

    # Then start application
    app.run()
```

### 7. Use Module-Level Loggers

```python
# At module level
logger = get_logger(__name__)

# Then use throughout module
def function1():
    logger.info("Function 1 called")

def function2():
    logger.info("Function 2 called")
```

### 8. Separate Sensitive Data

```python
# Don't log sensitive information
# Bad
logger.info("User login", extra={"password": password})

# Good
logger.info("User login", extra={"user_id": user_id})

# If you must log, redact
logger.debug("Request", extra={"headers": redact_sensitive(headers)})
```

## Log Analysis

### Analyzing JSON Logs

#### Using jq

```bash
# Count errors by type
cat logs/errors.log | jq -r '.error_type' | sort | uniq -c

# Find slow queries (> 1000ms)
cat logs/performance.log | jq 'select(.duration_ms > 1000)'

# Group by operation
cat logs/performance.log | jq -r '.operation' | sort | uniq -c

# Average duration by operation
cat logs/performance.log | jq -r '[.operation, .duration_ms] | @tsv'
```

#### Using Python

```python
import json

# Read and parse logs
logs = []
with open('logs/application.log') as f:
    for line in f:
        if line.strip():
            logs.append(json.loads(line))

# Filter errors
errors = [log for log in logs if log['level'] == 'ERROR']

# Calculate average duration
durations = [log['duration_ms'] for log in logs if 'duration_ms' in log]
avg_duration = sum(durations) / len(durations)

# Group by operation
from collections import Counter
operations = Counter(log['operation'] for log in logs if 'operation' in log)
```

### Common Queries

#### Find All Errors for a Request

```bash
grep "req_abc123" logs/application.log | jq .
```

#### Calculate P95 Latency

```python
import json
import numpy as np

durations = []
with open('logs/performance.log') as f:
    for line in f:
        log = json.loads(line)
        if 'duration_ms' in log:
            durations.append(log['duration_ms'])

p95 = np.percentile(durations, 95)
print(f"P95 latency: {p95:.2f}ms")
```

#### Find Slowest Operations

```bash
cat logs/performance.log | \
  jq -r '[.operation, .duration_ms] | @tsv' | \
  sort -k2 -nr | \
  head -20
```

## Troubleshooting

### Common Issues

#### Issue 1: Log Files Not Created

**Symptom**: No log files in log directory

**Solutions**:
```python
# Check that enable_file is True
setup_logging(enable_file=True)

# Check directory permissions
import os
os.makedirs("logs", exist_ok=True)

# Log a message to trigger file creation
logger = get_logger(__name__)
logger.info("Test message")
```

#### Issue 2: Request ID Not Appearing in Logs

**Symptom**: request_id field missing from log entries

**Solutions**:
```python
# Make sure to use RequestContext
with RequestContext(logger, "operation"):
    logger.info("Message")  # Will include request_id

# Or set context variable manually
from mcp_server.logging_config import request_id_var
request_id_var.set("req_123")
logger.info("Message")  # Will include request_id
request_id_var.set(None)  # Clean up
```

#### Issue 3: Performance Logs Not in Separate File

**Symptom**: performance.log is empty or doesn't exist

**Solutions**:
```python
# Make sure to use PerformanceLogger or include duration_ms
perf = PerformanceLogger(logger)
with perf.measure("operation"):
    pass

# Or include duration_ms manually
logger.info("Operation", extra={"duration_ms": 100.0})
```

#### Issue 4: Logs Too Verbose

**Symptom**: Too many log messages

**Solutions**:
```python
# Increase log level
setup_logging(log_level="WARNING")  # Only warnings and errors

# Disable specific loggers
logging.getLogger("verbose_module").setLevel(logging.WARNING)

# Use log level in code
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Expensive debug info: %s", expensive_computation())
```

#### Issue 5: Log Files Growing Too Large

**Symptom**: Log files consuming too much disk space

**Solutions**:
```python
# Reduce max file size
setup_logging(max_file_size_mb=50)  # Smaller files

# Reduce backup count
setup_logging(backup_count=3)  # Keep fewer backups

# Increase log level
setup_logging(log_level="WARNING")  # Less logging

# Implement log cleanup
import glob
import os
import time

# Delete logs older than 7 days
for log_file in glob.glob("logs/*.log.*"):
    if os.path.getmtime(log_file) < time.time() - 7 * 86400:
        os.remove(log_file)
```

### Debugging Tips

1. **Enable debug logging temporarily**:
   ```python
   logger.setLevel(logging.DEBUG)
   ```

2. **Check log file permissions**:
   ```bash
   ls -la logs/
   ```

3. **Verify log rotation**:
   ```bash
   ls -lh logs/application.log*
   ```

4. **Test log configuration**:
   ```python
   from mcp_server.logging_config import setup_logging, get_logger

   setup_logging(log_level="DEBUG", enable_console=True, enable_file=True)
   logger = get_logger("test")

   logger.debug("Debug message")
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message")
   ```

## Example Integration

Complete example showing all features:

```python
from mcp_server.logging_config import (
    setup_logging,
    get_logger,
    RequestContext,
    PerformanceLogger,
    log_error,
)

# Setup at application startup
setup_logging(
    log_level="INFO",
    log_dir="logs",
    enable_json=True,
    enable_console=True,
    enable_file=True,
)

# Get logger
logger = get_logger(__name__)

async def process_request(request_data: dict) -> dict:
    """Process a request with full logging."""

    # Use request context
    with RequestContext(
        logger,
        "process_request",
        client_id=request_data.get("client_id")
    ):
        logger.info(
            "Request received",
            extra={
                "endpoint": request_data["endpoint"],
                "method": request_data["method"]
            }
        )

        # Track performance
        perf = PerformanceLogger(logger)

        # Validate input
        with perf.measure("validate_input"):
            validate(request_data)

        # Fetch data
        try:
            with perf.measure("fetch_data"):
                data = await fetch_data(request_data["query"])
                logger.info(
                    "Data fetched",
                    extra={"row_count": len(data)}
                )
        except Exception as e:
            log_error(logger, "fetch_data", e)
            raise

        # Process data
        with perf.measure("process_data"):
            result = process(data)

        logger.info(
            "Request completed successfully",
            extra={"result_count": len(result)}
        )

        return result
```

## Additional Resources

- **Tests**: See `tests/test_logging_config.py` for usage examples
- **Error Handling Guide**: See `docs/ERROR_HANDLING.md`
- **API Reference**: See module docstrings in `mcp_server/logging_config.py`

## Support

For questions or issues:
1. Check test files for usage examples
2. Enable debug logging for detailed information
3. Review log files for patterns
4. Check file permissions and disk space
