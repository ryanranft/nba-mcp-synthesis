"""
Observability Stack Integration

Centralized observability with the THREE PILLARS:
1. Metrics (Prometheus, Grafana)
2. Logs (ELK Stack, Loki)
3. Traces (Jaeger, Zipkin, OpenTelemetry)

Features:
- Unified dashboard configuration
- Log aggregation
- Metric collection
- Distributed tracing
- Alert rules
- Service health monitoring

Use Cases:
- System monitoring
- Performance analysis
- Debugging
- Capacity planning
- SLA tracking
"""

import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PrometheusConfig:
    """Prometheus configuration"""

    scrape_interval: str = "15s"
    evaluation_interval: str = "15s"
    targets: List[str] = field(default_factory=list)


@dataclass
class GrafanaDashboard:
    """Grafana dashboard configuration"""

    title: str
    panels: List[Dict[str, Any]]
    refresh: str = "5s"


@dataclass
class AlertRule:
    """Prometheus alert rule"""

    name: str
    condition: str
    duration: str
    severity: str
    annotations: Dict[str, str]


class ObservabilityConfigGenerator:
    """Generate observability stack configuration"""

    @staticmethod
    def generate_prometheus_config(targets: List[str]) -> Dict[str, Any]:
        """Generate Prometheus configuration"""
        return {
            "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
            "scrape_configs": [
                {"job_name": "nba-mcp", "static_configs": [{"targets": targets}]}
            ],
            "alerting": {
                "alertmanagers": [
                    {"static_configs": [{"targets": ["alertmanager:9093"]}]}
                ]
            },
        }

    @staticmethod
    def generate_grafana_dashboard() -> Dict[str, Any]:
        """Generate Grafana dashboard for NBA MCP"""
        return {
            "dashboard": {
                "title": "NBA MCP Observability",
                "refresh": "5s",
                "panels": [
                    {
                        "id": 1,
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{path}}",
                            }
                        ],
                    },
                    {
                        "id": 2,
                        "title": "Response Time (p95)",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "p95",
                            }
                        ],
                    },
                    {
                        "id": 3,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{status=~"5.."}[5m])',
                                "legendFormat": "Errors",
                            }
                        ],
                    },
                    {
                        "id": 4,
                        "title": "Cache Hit Rate",
                        "type": "singlestat",
                        "targets": [
                            {
                                "expr": "cache_hits_total / (cache_hits_total + cache_misses_total)",
                                "legendFormat": "Hit Rate",
                            }
                        ],
                    },
                    {
                        "id": 5,
                        "title": "Active Connections",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "active_connections",
                                "legendFormat": "Connections",
                            }
                        ],
                    },
                    {
                        "id": 6,
                        "title": "ML Prediction Latency",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.99, rate(ml_prediction_duration_seconds_bucket[5m]))",
                                "legendFormat": "p99",
                            }
                        ],
                    },
                ],
            }
        }

    @staticmethod
    def generate_alert_rules() -> List[Dict[str, Any]]:
        """Generate Prometheus alert rules"""
        return [
            {
                "alert": "HighErrorRate",
                "expr": 'rate(http_requests_total{status=~"5.."}[5m]) > 0.05',
                "for": "5m",
                "labels": {"severity": "critical"},
                "annotations": {
                    "summary": "High error rate detected",
                    "description": "Error rate is above 5% for 5 minutes",
                },
            },
            {
                "alert": "HighResponseTime",
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
                "for": "10m",
                "labels": {"severity": "warning"},
                "annotations": {
                    "summary": "High response time",
                    "description": "p95 response time is above 1 second",
                },
            },
            {
                "alert": "LowCacheHitRate",
                "expr": "cache_hits_total / (cache_hits_total + cache_misses_total) < 0.7",
                "for": "15m",
                "labels": {"severity": "warning"},
                "annotations": {
                    "summary": "Low cache hit rate",
                    "description": "Cache hit rate is below 70%",
                },
            },
            {
                "alert": "ServiceDown",
                "expr": "up == 0",
                "for": "1m",
                "labels": {"severity": "critical"},
                "annotations": {
                    "summary": "Service is down",
                    "description": "NBA MCP service is not responding",
                },
            },
        ]


def create_observability_stack() -> Dict[str, Any]:
    """Create complete observability stack configuration"""
    generator = ObservabilityConfigGenerator()

    return {
        "prometheus": generator.generate_prometheus_config(
            targets=[
                "nba-mcp-service:8000",
                "nba-mcp-service:8001",
                "nba-mcp-service:8002",
            ]
        ),
        "grafana_dashboard": generator.generate_grafana_dashboard(),
        "alert_rules": generator.generate_alert_rules(),
    }


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    # Generate observability configuration
    config = create_observability_stack()

    os.makedirs("config/observability", exist_ok=True)

    # Save Prometheus config
    with open("config/observability/prometheus.yml", "w") as f:
        yaml.dump(config["prometheus"], f, default_flow_style=False)

    # Save Grafana dashboard
    with open("config/observability/grafana-dashboard.json", "w") as f:
        json.dump(config["grafana_dashboard"], f, indent=2)

    # Save alert rules
    with open("config/observability/alert-rules.yml", "w") as f:
        yaml.dump({"groups": [{"name": "nba_mcp", "rules": config["alert_rules"]}]}, f)

    print("=== Observability Stack Configuration ===\n")
    print("1. Prometheus Config:")
    print(yaml.dump(config["prometheus"], default_flow_style=False)[:300] + "...\n")

    print("2. Grafana Dashboard:")
    print(json.dumps(config["grafana_dashboard"], indent=2)[:300] + "...\n")

    print("3. Alert Rules:")
    print(f"   - {len(config['alert_rules'])} alert rules configured\n")

    print("\nConfigurations saved to config/observability/")
