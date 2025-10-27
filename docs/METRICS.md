# NBA MCP Server Metrics Reference

Complete reference for all metrics collected by the NBA MCP Server monitoring system.

## Table of Contents

1. [Metrics Overview](#metrics-overview)
2. [System Metrics](#system-metrics)
3. [Application Metrics](#application-metrics)
4. [NBA-Specific Metrics](#nba-specific-metrics)
5. [Prometheus Metrics](#prometheus-metrics)
6. [Custom Metrics](#custom-metrics)

## Metrics Overview

The NBA MCP Server collects three categories of metrics:

- **System Metrics**: Hardware and OS-level resource utilization
- **Application Metrics**: Request handling and performance
- **NBA Metrics**: Business-specific operations and data quality

### Metric Types

| Type | Description | Example |
|------|-------------|---------|
| Counter | Monotonically increasing value | `total_requests` |
| Gauge | Value that can increase or decrease | `cpu_percent` |
| Histogram | Distribution of values | `request_latency` |
| Summary | Percentiles and aggregations | `latency_p95` |

## System Metrics

### CPU Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `cpu_percent` | Gauge | % | Current CPU utilization (0-100) |
| `cpu_count` | Gauge | cores | Number of CPU cores |

**Example:**
```python
metrics = collector.collect_system_metrics()
print(f"CPU: {metrics.cpu_percent}% across {metrics.cpu_count} cores")
```

### Memory Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `memory_percent` | Gauge | % | Memory utilization (0-100) |
| `memory_used_bytes` | Gauge | bytes | Memory currently in use |
| `memory_available_bytes` | Gauge | bytes | Memory available for allocation |
| `memory_total_bytes` | Gauge | bytes | Total system memory |

**Example:**
```python
used_gb = metrics.memory_used_bytes / (1024**3)
total_gb = metrics.memory_total_bytes / (1024**3)
print(f"Memory: {used_gb:.1f}GB / {total_gb:.1f}GB ({metrics.memory_percent}%)")
```

### Disk Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `disk_usage_percent` | Gauge | % | Disk space utilization |
| `disk_usage_used_bytes` | Gauge | bytes | Disk space used |
| `disk_usage_free_bytes` | Gauge | bytes | Disk space available |
| `disk_io_read_bytes` | Counter | bytes | Cumulative bytes read |
| `disk_io_write_bytes` | Counter | bytes | Cumulative bytes written |
| `disk_io_read_count` | Counter | operations | Cumulative read operations |
| `disk_io_write_count` | Counter | operations | Cumulative write operations |

**Example:**
```python
read_mb = metrics.disk_io_read_bytes / (1024**2)
write_mb = metrics.disk_io_write_bytes / (1024**2)
print(f"Disk I/O: {read_mb:.1f}MB read, {write_mb:.1f}MB written")
```

### Network Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `network_bytes_sent` | Counter | bytes | Cumulative bytes sent |
| `network_bytes_recv` | Counter | bytes | Cumulative bytes received |
| `network_packets_sent` | Counter | packets | Cumulative packets sent |
| `network_packets_recv` | Counter | packets | Cumulative packets received |
| `network_errors_in` | Counter | errors | Receive errors |
| `network_errors_out` | Counter | errors | Send errors |

**Example:**
```python
sent_mb = metrics.network_bytes_sent / (1024**2)
recv_mb = metrics.network_bytes_recv / (1024**2)
print(f"Network: {sent_mb:.1f}MB sent, {recv_mb:.1f}MB received")
```

### Process Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `open_files` | Gauge | count | Number of open file handles |
| `open_connections` | Gauge | count | Number of open network connections |

## Application Metrics

### Request Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `request_count` | Counter | requests | Total requests processed |
| `request_rate_per_second` | Gauge | req/s | Current request rate |
| `active_requests` | Gauge | requests | Currently processing requests |
| `active_connections` | Gauge | connections | Active client connections |

**Example:**
```python
metrics = collector.collect_application_metrics()
print(f"Requests: {metrics.request_count} total, {metrics.active_requests} active")
print(f"Rate: {metrics.request_rate_per_second:.2f} req/s")
```

### Latency Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `average_latency_ms` | Gauge | ms | Average request latency |
| `p50_latency_ms` | Gauge | ms | 50th percentile (median) |
| `p95_latency_ms` | Gauge | ms | 95th percentile |
| `p99_latency_ms` | Gauge | ms | 99th percentile |

**Example:**
```python
print(f"Latency: avg={metrics.average_latency_ms:.1f}ms, "
      f"p95={metrics.p95_latency_ms:.1f}ms, "
      f"p99={metrics.p99_latency_ms:.1f}ms")
```

**Interpretation:**
- **P50 (median)**: Half of requests are faster
- **P95**: 95% of requests are faster (good SLA metric)
- **P99**: 99% of requests are faster (catches outliers)

### Error Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `error_count` | Counter | errors | Total errors encountered |
| `error_rate_per_minute` | Gauge | errors/min | Current error rate |
| `success_rate_percent` | Gauge | % | Success rate (0-100) |

**Example:**
```python
print(f"Errors: {metrics.error_count} total, "
      f"{metrics.error_rate_per_minute:.1f}/min")
print(f"Success rate: {metrics.success_rate_percent:.2f}%")
```

### Throughput Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `throughput_requests_per_second` | Gauge | req/s | Actual throughput |
| `total_processing_time_seconds` | Counter | seconds | Total time spent processing |

## NBA-Specific Metrics

### Query Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `queries_per_second` | Gauge | queries/s | Database query rate |
| `total_queries` | Counter | queries | Total queries executed |
| `average_query_time_ms` | Gauge | ms | Average query latency |
| `database_connections` | Gauge | connections | Active DB connections |

**Example:**
```python
metrics = collector.collect_nba_metrics()
print(f"Queries: {metrics.total_queries} total, "
      f"{metrics.queries_per_second:.2f}/s")
print(f"Query latency: {metrics.average_query_time_ms:.1f}ms avg")
```

### Cache Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `cache_hits` | Counter | hits | Cache hits |
| `cache_misses` | Counter | misses | Cache misses |
| `cache_hit_rate_percent` | Gauge | % | Cache hit rate (0-100) |

**Example:**
```python
total_ops = metrics.cache_hits + metrics.cache_misses
print(f"Cache: {metrics.cache_hit_rate_percent:.1f}% hit rate "
      f"({metrics.cache_hits}/{total_ops} hits)")
```

**Optimization Guide:**
- **<50%**: Poor - consider cache tuning
- **50-70%**: Fair - room for improvement
- **70-85%**: Good - acceptable performance
- **>85%**: Excellent - well-optimized

### Data Quality Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `data_freshness_seconds` | Gauge | seconds | Age of data since last update |
| `games_processed` | Counter | games | Total games processed |
| `players_processed` | Counter | players | Total players processed |

**Example:**
```python
age_minutes = metrics.data_freshness_seconds / 60
print(f"Data age: {age_minutes:.1f} minutes")
print(f"Processed: {metrics.games_processed} games, "
      f"{metrics.players_processed} players")
```

### Tool Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `active_tools` | Gauge | tools | Currently executing tools |
| `tool_success_rate_percent` | Gauge | % | Tool execution success rate |

### Storage Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `s3_reads` | Counter | operations | S3 read operations |
| `s3_writes` | Counter | operations | S3 write operations |

**Example:**
```python
print(f"S3: {metrics.s3_reads} reads, {metrics.s3_writes} writes")
```

## Prometheus Metrics

### Prometheus Export Format

```
# HELP nba_cpu_percent CPU utilization percentage
# TYPE nba_cpu_percent gauge
nba_cpu_percent 42.5

# HELP nba_memory_percent Memory utilization percentage
# TYPE nba_memory_percent gauge
nba_memory_percent 67.3

# HELP nba_requests_total Total number of requests
# TYPE nba_requests_total counter
nba_requests_total 12345

# HELP nba_latency_ms Request latency in milliseconds
# TYPE nba_latency_ms summary
nba_latency_ms{quantile="0.5"} 45.2
nba_latency_ms{quantile="0.95"} 125.7
nba_latency_ms{quantile="0.99"} 245.1
```

### Exporting to Prometheus

```python
from mcp_server.nba_metrics import get_metrics_collector

collector = get_metrics_collector()
prometheus_text = collector.export_prometheus()

# Serve on /metrics endpoint
from flask import Flask, Response

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(prometheus_text, mimetype='text/plain')
```

## Custom Metrics

### Recording Custom Events

```python
from mcp_server.nba_metrics import get_metrics_collector

collector = get_metrics_collector()

# Record request with timing
with collector.track_request("my_operation"):
    # Your operation here
    result = process_data()

# Record database query
with collector.track_query("SELECT * FROM games WHERE season=2024"):
    results = db.execute(query)

# Record individual events
collector.record_cache_hit()
collector.record_cache_miss()
collector.record_game_processed()
collector.record_player_processed()
collector.record_s3_read()
collector.record_s3_write()
collector.record_data_update()
collector.record_tool_execution(success=True)
```

### Using Decorators

```python
from mcp_server.nba_metrics import track_latency

@track_latency("expensive_computation")
async def compute_player_stats(player_id: str):
    # Automatically tracked
    stats = await calculate_advanced_stats(player_id)
    return stats
```

### Best Practices

1. **Naming**: Use clear, descriptive names (e.g., `player_stats_computation_time`)
2. **Units**: Include units in metric names (e.g., `_ms`, `_percent`, `_bytes`)
3. **Labels**: Use labels sparingly (adds cardinality)
4. **Frequency**: Don't over-collect high-frequency events
5. **Cleanup**: Reset or remove unused metrics

### Performance Considerations

- Metrics collection overhead: <5% CPU
- Memory per metric: ~100 bytes
- Latency tracking window: 10,000 samples (configurable)
- History retention: Last 1,000 data points

---

**Related Documentation:**
- [MONITORING.md](./MONITORING.md) - Complete monitoring guide
- [ALERTING.md](./ALERTING.md) - Alert configuration guide
