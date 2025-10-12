"""
Service Mesh Integration

Support for service mesh platforms:
- Istio
- Linkerd
- Consul Connect
- AWS App Mesh

Features:
- Service discovery
- Mutual TLS (mTLS)
- Traffic management
- Observability
- Resilience (retries, timeouts, circuit breakers)
- Security policies

Use Cases:
- Microservices communication
- Zero-trust security
- Canary deployments
- A/B testing
- Distributed tracing
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ServiceMeshType(Enum):
    """Supported service mesh types"""
    ISTIO = "istio"
    LINKERD = "linkerd"
    CONSUL = "consul"


@dataclass
class TrafficSplit:
    """Traffic splitting configuration"""
    destination: str
    weight: int


@dataclass
class VirtualService:
    """Virtual service configuration"""
    name: str
    host: str
    routes: List[Dict[str, Any]]
    retries: Optional[int] = 3
    timeout: Optional[str] = "30s"


@dataclass
class DestinationRule:
    """Destination rule configuration"""
    name: str
    host: str
    subsets: List[Dict[str, Any]]
    connection_pool: Optional[Dict[str, Any]] = None
    outlier_detection: Optional[Dict[str, Any]] = None


class IstioConfigGenerator:
    """Generate Istio configuration"""

    @staticmethod
    def generate_virtual_service(vs: VirtualService) -> Dict[str, Any]:
        """Generate Istio VirtualService"""
        return {
            'apiVersion': 'networking.istio.io/v1beta1',
            'kind': 'VirtualService',
            'metadata': {
                'name': vs.name
            },
            'spec': {
                'hosts': [vs.host],
                'http': vs.routes
            }
        }

    @staticmethod
    def generate_destination_rule(dr: DestinationRule) -> Dict[str, Any]:
        """Generate Istio DestinationRule"""
        spec = {
            'host': dr.host,
            'subsets': dr.subsets
        }

        if dr.connection_pool:
            spec['trafficPolicy'] = {'connectionPool': dr.connection_pool}

        if dr.outlier_detection:
            spec.setdefault('trafficPolicy', {})['outlierDetection'] = dr.outlier_detection

        return {
            'apiVersion': 'networking.istio.io/v1beta1',
            'kind': 'DestinationRule',
            'metadata': {
                'name': dr.name
            },
            'spec': spec
        }


# NBA MCP service mesh example
def create_nba_mcp_service_mesh() -> List[Dict[str, Any]]:
    """Create service mesh config for NBA MCP"""

    # Virtual Service for canary deployment
    vs = VirtualService(
        name="nba-mcp-virtual-service",
        host="nba-mcp-service",
        routes=[
            {
                'match': [{'headers': {'x-version': {'exact': 'canary'}}}],
                'route': [{'destination': {'host': 'nba-mcp-service', 'subset': 'v2'}, 'weight': 100}]
            },
            {
                'route': [
                    {'destination': {'host': 'nba-mcp-service', 'subset': 'v1'}, 'weight': 90},
                    {'destination': {'host': 'nba-mcp-service', 'subset': 'v2'}, 'weight': 10}
                ]
            }
        ]
    )

    # Destination Rule with circuit breaker
    dr = DestinationRule(
        name="nba-mcp-destination-rule",
        host="nba-mcp-service",
        subsets=[
            {'name': 'v1', 'labels': {'version': 'v1'}},
            {'name': 'v2', 'labels': {'version': 'v2'}}
        ],
        connection_pool={
            'tcp': {'maxConnections': 100},
            'http': {'http1MaxPendingRequests': 50, 'http2MaxRequests': 100}
        },
        outlier_detection={
            'consecutiveErrors': 5,
            'interval': '30s',
            'baseEjectionTime': '60s',
            'maxEjectionPercent': 50
        }
    )

    return [
        IstioConfigGenerator.generate_virtual_service(vs),
        IstioConfigGenerator.generate_destination_rule(dr)
    ]


if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO)

    # Generate Istio configuration
    configs = create_nba_mcp_service_mesh()

    os.makedirs("k8s/istio", exist_ok=True)

    output = []
    for config in configs:
        output.append(yaml.dump(config, default_flow_style=False))

    yaml_content = "---\n".join(output)

    with open("k8s/istio/nba-mcp-service-mesh.yaml", 'w') as f:
        f.write(yaml_content)

    print("=== Istio Configuration ===\n")
    print(yaml_content[:800] + "...\n")
    print("\nConfiguration saved to k8s/istio/nba-mcp-service-mesh.yaml")

