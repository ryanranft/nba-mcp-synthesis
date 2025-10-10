# Monitoring System

Log-based monitoring for NBA MCP Synthesis System.

## Components

### 1. Metrics Collector (`collect_metrics.sh`)
Parses logs and extracts key metrics:
- Request counts
- Response times
- Error rates
- Cost tracking
- API usage

### 2. Simple Dashboard (`dashboard.sh`)
Terminal-based metrics display:
- Real-time metrics
- Historical trends
- Alert status

### 3. Alert Rules (`check_alerts.sh`)
Configurable alerting:
- Error rate thresholds
- Cost limits
- Performance degradation
- Slack webhook support

## Usage

```bash
# Collect current metrics
./monitoring/collect_metrics.sh

# View dashboard
./monitoring/dashboard.sh

# Check alerts
./monitoring/check_alerts.sh
```

## Configuration

Edit `monitoring/config.sh` to set:
- Alert thresholds
- Slack webhook URL
- Metrics retention period

## Metrics Tracked

- **Requests**: Total, successful, failed
- **Response Time**: p50, p95, p99
- **Cost**: Total, per request, per hour
- **Errors**: Count, rate, types
- **Resources**: CPU, memory, disk

## Alerts

Default thresholds:
- Error rate > 5%
- p95 response time > 30s
- Cost per hour > $5
- Disk usage > 90%
