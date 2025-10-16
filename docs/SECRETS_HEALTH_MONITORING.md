# Secrets Health Monitoring System

A comprehensive health monitoring, metrics collection, and alerting system for secrets management. Provides real-time monitoring of secret health, API connectivity, automated Slack notifications, and detailed analytics.

## 🚀 Features

### Core Monitoring
- **Real-time Secret Validation**: Format validation, strength checks, and connectivity testing
- **API Health Checks**: Google, OpenAI, Anthropic, DeepSeek, and Slack API connectivity monitoring
- **Performance Metrics**: Response time tracking, uptime monitoring, and health scoring
- **Historical Data**: Trend analysis and performance analytics over time

### Alerting System
- **Multi-channel Notifications**: Slack, Email, SMS, Webhook, and Console alerts
- **Intelligent Deduplication**: Prevents alert spam with smart throttling and deduplication
- **Escalation Policies**: Configurable escalation rules and alert routing
- **Customizable Rules**: Define custom alert conditions and thresholds

### Dashboard & Visualization
- **Real-time Dashboard**: Web-based dashboard with live metrics and charts
- **CLI Interface**: Command-line dashboard for quick status checks
- **Chart Generation**: Automated chart generation for trend analysis
- **Data Export**: JSON and CSV export capabilities

### Integration
- **Unified System**: Seamless integration between monitoring, alerting, and dashboard
- **Hierarchical Loading**: Integration with the unified secrets management system
- **Docker Support**: Containerized deployment with proper secret handling
- **Kubernetes Ready**: Full Kubernetes integration with init containers

## 📁 File Structure

```
mcp_server/
├── secrets_health_monitor.py          # Core health monitoring system
├── secrets_metrics_dashboard.py       # Metrics dashboard and visualization
├── secrets_alerting_system.py        # Alerting and notification system
├── secrets_health_integration.py      # Unified integration system
└── templates/
    └── dashboard.html                 # Web dashboard template
```

## 🛠️ Installation

### Prerequisites
```bash
pip install requests flask flask-socketio matplotlib
```

### Optional Dependencies
```bash
# For web dashboard
pip install flask flask-socketio

# For chart generation
pip install matplotlib

# For email notifications
pip install smtplib (built-in)
```

## 🚀 Quick Start

### 1. Basic Health Check
```bash
# Run a one-time health check
python mcp_server/secrets_health_monitor.py --project nba-mcp-synthesis --context production --once
```

### 2. Start Continuous Monitoring
```bash
# Start continuous monitoring (5-minute intervals)
python mcp_server/secrets_health_monitor.py --project nba-mcp-synthesis --context production --interval 300
```

### 3. View Dashboard
```bash
# CLI dashboard
python mcp_server/secrets_metrics_dashboard.py --project nba-mcp-synthesis --context production --cli

# Web dashboard
python mcp_server/secrets_metrics_dashboard.py --project nba-mcp-synthesis --context production --web
```

### 4. Test Alerting
```bash
# Send test alert
python mcp_server/secrets_alerting_system.py --project nba-mcp-synthesis --context production --test

# View alert statistics
python mcp_server/secrets_alerting_system.py --project nba-mcp-synthesis --context production --stats
```

### 5. Integrated System
```bash
# Start integrated monitoring
python mcp_server/secrets_health_integration.py --project nba-mcp-synthesis --context production --start

# Generate comprehensive report
python mcp_server/secrets_health_integration.py --project nba-mcp-synthesis --context production --report --export report.json
```

## 📊 Usage Examples

### Health Monitoring

```python
from mcp_server.secrets_health_monitor import SecretsHealthMonitor

# Create monitor
monitor = SecretsHealthMonitor("nba-mcp-synthesis", "production")

# Run health checks
health_results = monitor.perform_health_checks()
validation_results = monitor.validate_all_secrets()

# Get metrics
metrics = monitor.metrics_collector.get_current_snapshot()
print(f"Health Score: {metrics.overall_health_score:.1f}%")
```

### Alerting System

```python
from mcp_server.secrets_alerting_system import AlertManager, AlertRule, AlertSeverity, AlertChannel

# Create alert manager
alert_manager = AlertManager("nba-mcp-synthesis", "production")

# Add custom alert rule
rule = AlertRule(
    name="custom_health_check",
    condition="metrics.get('overall_health_score', 0) < 80",
    severity=AlertSeverity.WARNING,
    channels=[AlertChannel.SLACK, AlertChannel.CONSOLE],
    description="Health score below 80%"
)
alert_manager.add_alert_rule(rule)

# Process metrics and send alerts
alerts = alert_manager.process_metrics(metrics_data)
```

### Metrics Dashboard

```python
from mcp_server.secrets_metrics_dashboard import MetricsDashboard

# Create dashboard
dashboard = MetricsDashboard("nba-mcp-synthesis", "production")

# Update metrics
dashboard.update_metrics(metrics_data)

# Generate charts
dashboard.generate_charts("/tmp/charts")

# Export data
dashboard.export_metrics("/tmp/metrics.json", "json")
```

## 🔧 Configuration

### Environment Variables

The system uses the hierarchical secrets loading system. Key environment variables:

```bash
# Slack notifications
SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_PRODUCTION=https://hooks.slack.com/services/...
SLACK_CHANNEL_NBA_MCP_SYNTHESIS_PRODUCTION=#alerts

# Email notifications
SMTP_SERVER_NBA_MCP_SYNTHESIS_PRODUCTION=smtp.gmail.com
SMTP_PORT_NBA_MCP_SYNTHESIS_PRODUCTION=587
SMTP_USERNAME_NBA_MCP_SYNTHESIS_PRODUCTION=your-email@gmail.com
SMTP_PASSWORD_NBA_MCP_SYNTHESIS_PRODUCTION=your-app-password

# Webhook notifications
WEBHOOK_URL_NBA_MCP_SYNTHESIS_PRODUCTION=https://your-webhook-endpoint.com/alerts
```

### Alert Rules

Default alert rules are automatically loaded:

- **Health Score Critical**: Overall health score < 50%
- **Health Score Warning**: Overall health score < 70%
- **API Connectivity Critical**: API connectivity score < 50%
- **Response Time High**: Average response time > 5 seconds
- **Critical Secrets**: One or more secrets in critical state
- **Monitoring Inactive**: Secrets monitoring is inactive

### Custom Alert Rules

```python
# Add custom alert rule
custom_rule = AlertRule(
    name="api_response_time",
    condition="metrics.get('avg_response_time_ms', 0) > 3000",
    severity=AlertSeverity.WARNING,
    channels=[AlertChannel.SLACK],
    throttle_minutes=30,
    description="API response time exceeds 3 seconds"
)
alert_manager.add_alert_rule(custom_rule)
```

## 📈 Monitoring Metrics

### Health Metrics
- **Overall Health Score**: Composite score based on all health checks (0-100%)
- **API Connectivity Score**: Percentage of healthy API connections (0-100%)
- **Response Time**: Average response time across all API calls (milliseconds)
- **Uptime**: Total system uptime (hours)

### Secret Metrics
- **Total Secrets**: Number of secrets being monitored
- **Healthy Secrets**: Number of secrets passing validation
- **Warning Secrets**: Number of secrets with warnings
- **Critical Secrets**: Number of secrets with critical issues

### Alert Metrics
- **Total Alerts**: Total number of alerts generated
- **Alert Frequency**: Alerts per hour/day
- **Channel Success Rate**: Success rate for each notification channel
- **Escalation Rate**: Percentage of alerts that required escalation

## 🚨 Alert Channels

### Slack
- Rich message formatting with attachments
- Color-coded severity levels
- Detailed metadata and context
- Thread support for related alerts

### Email
- HTML-formatted messages
- Multiple recipient support
- Rich formatting with tables and charts
- Attachment support for reports

### Webhook
- JSON payload with full alert data
- Custom headers support
- Retry logic and error handling
- Integration with external systems

### Console
- Colored output for different severities
- Detailed logging and debugging
- Development and testing support

## 🔍 Troubleshooting

### Common Issues

1. **Secrets Not Loading**
   ```bash
   # Check if hierarchical loader is working
   python /Users/ryanranft/load_env_hierarchical.py --project nba-mcp-synthesis --context production
   ```

2. **API Connectivity Issues**
   ```bash
   # Test individual API connections
   python mcp_server/secrets_health_monitor.py --project nba-mcp-synthesis --context production --once
   ```

3. **Alert Notifications Not Working**
   ```bash
   # Test alert system
   python mcp_server/secrets_alerting_system.py --project nba-mcp-synthesis --context production --test
   ```

4. **Dashboard Not Loading**
   ```bash
   # Check web dashboard dependencies
   pip install flask flask-socketio
   python mcp_server/secrets_metrics_dashboard.py --project nba-mcp-synthesis --context production --web
   ```

### Log Files
- `/tmp/secrets_health_monitor.log` - Health monitoring logs
- `/tmp/secrets_alerting.log` - Alerting system logs
- `/tmp/secrets_integration.log` - Integration system logs
- `/tmp/secrets_metrics_*.json` - Metrics data files

## 🔒 Security Considerations

- **Secret Validation**: All secrets are validated for format and strength
- **Secure Storage**: Metrics and logs are stored locally with appropriate permissions
- **Network Security**: All API calls use HTTPS with proper timeout handling
- **Access Control**: Dashboard and API endpoints should be secured in production

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker
docker build -t secrets-health-monitor .
docker run -d --name secrets-monitor secrets-health-monitor
```

### Kubernetes Deployment
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets-prod.yaml
kubectl apply -f k8s/deployment.yaml
```

### Systemd Service
```bash
# Create systemd service
sudo cp scripts/secrets-health-monitor.service /etc/systemd/system/
sudo systemctl enable secrets-health-monitor
sudo systemctl start secrets-health-monitor
```

## 📚 API Reference

### SecretsHealthMonitor
- `perform_health_checks()` - Run all health checks
- `validate_all_secrets()` - Validate all loaded secrets
- `start_monitoring(interval)` - Start continuous monitoring
- `stop_monitoring()` - Stop continuous monitoring
- `get_health_report()` - Get comprehensive health report

### AlertManager
- `add_alert_rule(rule)` - Add custom alert rule
- `remove_alert_rule(name)` - Remove alert rule
- `process_metrics(metrics)` - Process metrics and send alerts
- `get_alert_history(hours)` - Get alert history
- `get_alert_statistics()` - Get alert statistics

### MetricsDashboard
- `update_metrics(metrics)` - Update metrics data
- `get_current_metrics()` - Get current metrics
- `get_metrics_history(hours)` - Get historical metrics
- `generate_charts(output_dir)` - Generate charts
- `export_metrics(file, format)` - Export metrics data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the NBA MCP Synthesis system and follows the same licensing terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error messages
3. Test individual components
4. Create an issue with detailed information

---

**Note**: This system integrates with the unified secrets management system and requires proper configuration of the hierarchical secrets loader for full functionality.

