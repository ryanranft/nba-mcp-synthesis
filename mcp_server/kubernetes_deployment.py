"""
Kubernetes Deployment Generator

Generate Kubernetes manifests for NBA MCP deployment:
- Deployment (pods, replicas, rolling updates)
- Service (ClusterIP, NodePort, LoadBalancer)
- ConfigMap (configuration)
- Secret (credentials)
- HorizontalPodAutoscaler (auto-scaling)
- Ingress (external access)
- PersistentVolumeClaim (storage)

Features:
- Multi-environment support (dev, staging, prod)
- Resource limits and requests
- Health checks (liveness, readiness)
- Rolling updates and rollbacks
- Auto-scaling based on CPU/memory
- Secret management
- Network policies
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceType(Enum):
    """Kubernetes service types"""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


@dataclass
class ResourceRequirements:
    """Pod resource requirements"""
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "256Mi"
    memory_limit: str = "512Mi"


@dataclass
class HealthProbe:
    """Health check configuration"""
    path: str = "/health"
    port: int = 8000
    initial_delay_seconds: int = 10
    period_seconds: int = 10
    timeout_seconds: int = 5
    success_threshold: int = 1
    failure_threshold: int = 3


@dataclass
class AutoScalingConfig:
    """Horizontal Pod Autoscaler configuration"""
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_percentage: int = 70
    target_memory_percentage: int = 80


@dataclass
class IngressConfig:
    """Ingress configuration"""
    enabled: bool = False
    host: str = "nba-mcp.example.com"
    path: str = "/"
    tls_enabled: bool = False
    tls_secret_name: str = "nba-mcp-tls"


@dataclass
class KubernetesConfig:
    """Complete Kubernetes deployment configuration"""
    app_name: str
    namespace: str = "default"
    image: str = "nba-mcp-server:latest"
    replicas: int = 3
    service_port: int = 8000
    container_port: int = 8000
    service_type: ServiceType = ServiceType.CLUSTER_IP
    resources: ResourceRequirements = field(default_factory=ResourceRequirements)
    liveness_probe: HealthProbe = field(default_factory=HealthProbe)
    readiness_probe: HealthProbe = field(default_factory=HealthProbe)
    autoscaling: Optional[AutoScalingConfig] = None
    ingress: Optional[IngressConfig] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    config_map_data: Dict[str, str] = field(default_factory=dict)


class KubernetesManifestGenerator:
    """Generate Kubernetes YAML manifests"""

    @staticmethod
    def generate_deployment(config: KubernetesConfig) -> Dict[str, Any]:
        """Generate Deployment manifest"""
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': config.app_name,
                'namespace': config.namespace,
                'labels': {
                    'app': config.app_name,
                    'version': 'v1'
                }
            },
            'spec': {
                'replicas': config.replicas,
                'selector': {
                    'matchLabels': {
                        'app': config.app_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': config.app_name,
                            'version': 'v1'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': config.app_name,
                            'image': config.image,
                            'ports': [{
                                'containerPort': config.container_port,
                                'protocol': 'TCP'
                            }],
                            'env': [
                                {'name': k, 'value': v}
                                for k, v in config.env_vars.items()
                            ] + [
                                {
                                    'name': k,
                                    'valueFrom': {
                                        'secretKeyRef': {
                                            'name': f"{config.app_name}-secrets",
                                            'key': k
                                        }
                                    }
                                }
                                for k in config.secrets.keys()
                            ],
                            'resources': {
                                'requests': {
                                    'cpu': config.resources.cpu_request,
                                    'memory': config.resources.memory_request
                                },
                                'limits': {
                                    'cpu': config.resources.cpu_limit,
                                    'memory': config.resources.memory_limit
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': config.liveness_probe.path,
                                    'port': config.liveness_probe.port
                                },
                                'initialDelaySeconds': config.liveness_probe.initial_delay_seconds,
                                'periodSeconds': config.liveness_probe.period_seconds,
                                'timeoutSeconds': config.liveness_probe.timeout_seconds,
                                'successThreshold': config.liveness_probe.success_threshold,
                                'failureThreshold': config.liveness_probe.failure_threshold
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': config.readiness_probe.path,
                                    'port': config.readiness_probe.port
                                },
                                'initialDelaySeconds': config.readiness_probe.initial_delay_seconds,
                                'periodSeconds': config.readiness_probe.period_seconds,
                                'timeoutSeconds': config.readiness_probe.timeout_seconds,
                                'successThreshold': config.readiness_probe.success_threshold,
                                'failureThreshold': config.readiness_probe.failure_threshold
                            }
                        }]
                    }
                },
                'strategy': {
                    'type': 'RollingUpdate',
                    'rollingUpdate': {
                        'maxSurge': 1,
                        'maxUnavailable': 0
                    }
                }
            }
        }

    @staticmethod
    def generate_service(config: KubernetesConfig) -> Dict[str, Any]:
        """Generate Service manifest"""
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': config.app_name,
                'namespace': config.namespace,
                'labels': {
                    'app': config.app_name
                }
            },
            'spec': {
                'type': config.service_type.value,
                'selector': {
                    'app': config.app_name
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': config.service_port,
                    'targetPort': config.container_port
                }]
            }
        }

    @staticmethod
    def generate_configmap(config: KubernetesConfig) -> Optional[Dict[str, Any]]:
        """Generate ConfigMap manifest"""
        if not config.config_map_data:
            return None

        return {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f"{config.app_name}-config",
                'namespace': config.namespace
            },
            'data': config.config_map_data
        }

    @staticmethod
    def generate_secret(config: KubernetesConfig) -> Optional[Dict[str, Any]]:
        """Generate Secret manifest"""
        if not config.secrets:
            return None

        return {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f"{config.app_name}-secrets",
                'namespace': config.namespace
            },
            'type': 'Opaque',
            'stringData': config.secrets
        }

    @staticmethod
    def generate_hpa(config: KubernetesConfig) -> Optional[Dict[str, Any]]:
        """Generate HorizontalPodAutoscaler manifest"""
        if not config.autoscaling:
            return None

        return {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': config.app_name,
                'namespace': config.namespace
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': config.app_name
                },
                'minReplicas': config.autoscaling.min_replicas,
                'maxReplicas': config.autoscaling.max_replicas,
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': config.autoscaling.target_cpu_percentage
                            }
                        }
                    },
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'memory',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': config.autoscaling.target_memory_percentage
                            }
                        }
                    }
                ]
            }
        }

    @staticmethod
    def generate_ingress(config: KubernetesConfig) -> Optional[Dict[str, Any]]:
        """Generate Ingress manifest"""
        if not config.ingress or not config.ingress.enabled:
            return None

        ingress_spec = {
            'rules': [{
                'host': config.ingress.host,
                'http': {
                    'paths': [{
                        'path': config.ingress.path,
                        'pathType': 'Prefix',
                        'backend': {
                            'service': {
                                'name': config.app_name,
                                'port': {
                                    'number': config.service_port
                                }
                            }
                        }
                    }]
                }
            }]
        }

        if config.ingress.tls_enabled:
            ingress_spec['tls'] = [{
                'hosts': [config.ingress.host],
                'secretName': config.ingress.tls_secret_name
            }]

        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': config.app_name,
                'namespace': config.namespace,
                'annotations': {
                    'kubernetes.io/ingress.class': 'nginx'
                }
            },
            'spec': ingress_spec
        }

    @staticmethod
    def generate_all(config: KubernetesConfig) -> List[Dict[str, Any]]:
        """Generate all Kubernetes manifests"""
        manifests = []

        # Always include deployment and service
        manifests.append(KubernetesManifestGenerator.generate_deployment(config))
        manifests.append(KubernetesManifestGenerator.generate_service(config))

        # Optional manifests
        configmap = KubernetesManifestGenerator.generate_configmap(config)
        if configmap:
            manifests.append(configmap)

        secret = KubernetesManifestGenerator.generate_secret(config)
        if secret:
            manifests.append(secret)

        hpa = KubernetesManifestGenerator.generate_hpa(config)
        if hpa:
            manifests.append(hpa)

        ingress = KubernetesManifestGenerator.generate_ingress(config)
        if ingress:
            manifests.append(ingress)

        return manifests


class KubernetesDeploymentManager:
    """Manage Kubernetes deployments"""

    def __init__(self):
        self.configs: Dict[str, KubernetesConfig] = {}

    def create_config(self, environment: Environment, **kwargs) -> KubernetesConfig:
        """Create environment-specific configuration"""
        defaults = {
            Environment.DEVELOPMENT: {
                'replicas': 1,
                'resources': ResourceRequirements(
                    cpu_request="50m",
                    cpu_limit="200m",
                    memory_request="128Mi",
                    memory_limit="256Mi"
                )
            },
            Environment.STAGING: {
                'replicas': 2,
                'resources': ResourceRequirements(
                    cpu_request="100m",
                    cpu_limit="500m",
                    memory_request="256Mi",
                    memory_limit="512Mi"
                ),
                'autoscaling': AutoScalingConfig(
                    min_replicas=2,
                    max_replicas=5
                )
            },
            Environment.PRODUCTION: {
                'replicas': 3,
                'resources': ResourceRequirements(
                    cpu_request="200m",
                    cpu_limit="1000m",
                    memory_request="512Mi",
                    memory_limit="1Gi"
                ),
                'autoscaling': AutoScalingConfig(
                    min_replicas=3,
                    max_replicas=10
                ),
                'ingress': IngressConfig(
                    enabled=True,
                    host="nba-mcp.example.com",
                    tls_enabled=True
                )
            }
        }

        # Merge defaults with provided kwargs
        env_defaults = defaults.get(environment, {})
        merged_config = {**env_defaults, **kwargs}

        return KubernetesConfig(**merged_config)

    def generate_yaml(self, config: KubernetesConfig, output_file: Optional[str] = None) -> str:
        """Generate YAML manifest file"""
        manifests = KubernetesManifestGenerator.generate_all(config)

        # Convert to YAML
        yaml_docs = []
        for manifest in manifests:
            yaml_docs.append(yaml.dump(manifest, default_flow_style=False))

        yaml_content = "---\n".join(yaml_docs)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(yaml_content)
            logger.info(f"Kubernetes manifests saved to {output_file}")

        return yaml_content


# Example NBA MCP Kubernetes configuration
def create_nba_mcp_k8s_config(environment: Environment = Environment.PRODUCTION) -> KubernetesConfig:
    """Create Kubernetes config for NBA MCP service"""
    manager = KubernetesDeploymentManager()

    return manager.create_config(
        environment=environment,
        app_name="nba-mcp-server",
        namespace="nba-mcp",
        image="your-registry/nba-mcp-server:v1.0.0",
        service_port=8000,
        container_port=8000,
        service_type=ServiceType.CLUSTER_IP,
        env_vars={
            'NBA_MCP_ENV': environment.value,
            'NBA_MCP_LOG_LEVEL': 'INFO' if environment == Environment.PRODUCTION else 'DEBUG',
            'PYTHONUNBUFFERED': '1'
        },
        secrets={
            'DB_PASSWORD': 'your-db-password',
            'API_KEY': 'your-api-key',
            'JWT_SECRET': 'your-jwt-secret'
        },
        config_map_data={
            'app.conf': 'max_connections=1000\ntimeout=30',
            'database.conf': 'pool_size=10\npool_timeout=5'
        }
    )


if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO)

    # Generate manifests for all environments
    environments = [Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]

    os.makedirs("k8s/manifests", exist_ok=True)

    for env in environments:
        print(f"\n=== Generating {env.value} manifests ===\n")

        config = create_nba_mcp_k8s_config(env)
        manager = KubernetesDeploymentManager()

        output_file = f"k8s/manifests/{env.value}.yaml"
        yaml_content = manager.generate_yaml(config, output_file)

        print(f"Generated {output_file}")
        print(f"Manifests:\n{yaml_content[:500]}...")  # Print first 500 chars

