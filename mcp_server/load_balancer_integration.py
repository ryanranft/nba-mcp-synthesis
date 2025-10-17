"""
Load Balancer Integration

Provides integration with common load balancers:
- HAProxy configuration generation
- Nginx upstream configuration
- AWS ALB/ELB integration
- Health check endpoints
- Weighted routing
- Session affinity
- SSL termination

Features:
- Dynamic backend registration
- Health monitoring
- Traffic distribution
- Failover support
- Connection pooling
- Rate limiting per backend
"""

import json
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LoadBalancerType(Enum):
    """Supported load balancer types"""

    HAPROXY = "haproxy"
    NGINX = "nginx"
    AWS_ALB = "aws_alb"
    AWS_ELB = "aws_elb"


class HealthCheckProtocol(Enum):
    """Health check protocols"""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    GRPC = "grpc"


class RoutingAlgorithm(Enum):
    """Load balancing algorithms"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"


@dataclass
class Backend:
    """Backend server configuration"""

    host: str
    port: int
    weight: int = 100
    max_connections: int = 1000
    backup: bool = False
    enabled: bool = True

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass
class HealthCheck:
    """Health check configuration"""

    protocol: HealthCheckProtocol = HealthCheckProtocol.HTTP
    path: str = "/health"
    interval_seconds: int = 10
    timeout_seconds: int = 5
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3
    expected_status: int = 200


@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""

    name: str
    listen_port: int
    backends: List[Backend]
    algorithm: RoutingAlgorithm = RoutingAlgorithm.ROUND_ROBIN
    health_check: Optional[HealthCheck] = None
    session_affinity: bool = False
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    connection_timeout_seconds: int = 30
    max_connections: int = 10000
    rate_limit_requests_per_second: Optional[int] = None


class HAProxyConfigGenerator:
    """Generate HAProxy configuration"""

    @staticmethod
    def generate(config: LoadBalancerConfig) -> str:
        """Generate HAProxy config file"""
        cfg = []

        # Global settings
        cfg.append("global")
        cfg.append("    log /dev/log local0")
        cfg.append("    log /dev/log local1 notice")
        cfg.append("    maxconn {}".format(config.max_connections))
        cfg.append("    user haproxy")
        cfg.append("    group haproxy")
        cfg.append("    daemon")
        cfg.append("")

        # Defaults
        cfg.append("defaults")
        cfg.append("    log global")
        cfg.append("    mode http")
        cfg.append("    option httplog")
        cfg.append("    option dontlognull")
        cfg.append("    timeout connect {}s".format(config.connection_timeout_seconds))
        cfg.append("    timeout client {}s".format(config.connection_timeout_seconds))
        cfg.append("    timeout server {}s".format(config.connection_timeout_seconds))
        cfg.append("")

        # Frontend
        cfg.append("frontend {}_frontend".format(config.name))

        if config.ssl_enabled and config.ssl_cert_path:
            cfg.append(
                "    bind *:{} ssl crt {}".format(
                    config.listen_port, config.ssl_cert_path
                )
            )
        else:
            cfg.append("    bind *:{}".format(config.listen_port))

        cfg.append("    default_backend {}_backend".format(config.name))

        # Rate limiting
        if config.rate_limit_requests_per_second:
            cfg.append(
                "    stick-table type ip size 100k expire 30s store http_req_rate(10s)"
            )
            cfg.append("    http-request track-sc0 src")
            cfg.append(
                "    http-request deny deny_status 429 if {{ sc_http_req_rate(0) gt {} }}".format(
                    config.rate_limit_requests_per_second
                )
            )

        cfg.append("")

        # Backend
        cfg.append("backend {}_backend".format(config.name))

        # Algorithm
        algo_map = {
            RoutingAlgorithm.ROUND_ROBIN: "roundrobin",
            RoutingAlgorithm.LEAST_CONNECTIONS: "leastconn",
            RoutingAlgorithm.IP_HASH: "source",
            RoutingAlgorithm.WEIGHTED_ROUND_ROBIN: "roundrobin",
        }
        cfg.append(
            "    balance {}".format(algo_map.get(config.algorithm, "roundrobin"))
        )

        # Session affinity
        if config.session_affinity:
            cfg.append("    cookie SERVERID insert indirect nocache")

        # Health check
        if config.health_check:
            hc = config.health_check
            cfg.append("    option httpchk GET {}".format(hc.path))
            cfg.append("    http-check expect status {}".format(hc.expected_status))

        # Servers
        for i, backend in enumerate(config.backends):
            if not backend.enabled:
                continue

            server_line = "    server server{} {} weight {} maxconn {}".format(
                i + 1, backend.address, backend.weight, backend.max_connections
            )

            if config.health_check:
                server_line += " check inter {}s".format(
                    config.health_check.interval_seconds
                )

            if backend.backup:
                server_line += " backup"

            if config.session_affinity:
                server_line += " cookie server{}".format(i + 1)

            cfg.append(server_line)

        return "\n".join(cfg)


class NginxConfigGenerator:
    """Generate Nginx configuration"""

    @staticmethod
    def generate(config: LoadBalancerConfig) -> str:
        """Generate Nginx config file"""
        cfg = []

        # Upstream block
        cfg.append("upstream {}_upstream {{".format(config.name))

        # Algorithm
        algo_map = {
            RoutingAlgorithm.LEAST_CONNECTIONS: "least_conn;",
            RoutingAlgorithm.IP_HASH: "ip_hash;",
            RoutingAlgorithm.WEIGHTED_ROUND_ROBIN: "",
        }
        algo_directive = algo_map.get(config.algorithm, "")
        if algo_directive:
            cfg.append("    " + algo_directive)

        # Servers
        for backend in config.backends:
            if not backend.enabled:
                continue

            server_line = "    server {}".format(backend.address)

            if backend.weight != 100:
                server_line += " weight={}".format(backend.weight)

            if backend.max_connections:
                server_line += " max_conns={}".format(backend.max_connections)

            if backend.backup:
                server_line += " backup"

            server_line += ";"
            cfg.append(server_line)

        cfg.append("}")
        cfg.append("")

        # Server block
        cfg.append("server {")

        if config.ssl_enabled:
            cfg.append("    listen {} ssl http2;".format(config.listen_port))
            if config.ssl_cert_path:
                cfg.append("    ssl_certificate {};".format(config.ssl_cert_path))
            if config.ssl_key_path:
                cfg.append("    ssl_certificate_key {};".format(config.ssl_key_path))
        else:
            cfg.append("    listen {};".format(config.listen_port))

        cfg.append("    server_name _;")
        cfg.append("")

        # Health check location
        if config.health_check:
            cfg.append("    location {} {{".format(config.health_check.path))
            cfg.append("        access_log off;")
            cfg.append("        return 200 'healthy';")
            cfg.append("        add_header Content-Type text/plain;")
            cfg.append("    }")
            cfg.append("")

        # Proxy settings
        cfg.append("    location / {")
        cfg.append("        proxy_pass http://{}_upstream;".format(config.name))
        cfg.append("        proxy_set_header Host $host;")
        cfg.append("        proxy_set_header X-Real-IP $remote_addr;")
        cfg.append(
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
        )
        cfg.append("        proxy_set_header X-Forwarded-Proto $scheme;")
        cfg.append(
            "        proxy_connect_timeout {}s;".format(
                config.connection_timeout_seconds
            )
        )
        cfg.append(
            "        proxy_send_timeout {}s;".format(config.connection_timeout_seconds)
        )
        cfg.append(
            "        proxy_read_timeout {}s;".format(config.connection_timeout_seconds)
        )

        # Rate limiting
        if config.rate_limit_requests_per_second:
            cfg.append(
                "        limit_req_zone $binary_remote_addr zone={}:10m rate={}r/s;".format(
                    config.name, config.rate_limit_requests_per_second
                )
            )
            cfg.append(
                "        limit_req zone={} burst=20 nodelay;".format(config.name)
            )

        cfg.append("    }")
        cfg.append("}")

        return "\n".join(cfg)


class LoadBalancerManager:
    """Manage load balancer configurations"""

    def __init__(self, lb_type: LoadBalancerType):
        self.lb_type = lb_type
        self.configs: Dict[str, LoadBalancerConfig] = {}

    def add_backend(self, config_name: str, backend: Backend) -> None:
        """Add backend to existing configuration"""
        if config_name in self.configs:
            self.configs[config_name].backends.append(backend)
            logger.info(f"Added backend {backend.address} to {config_name}")
        else:
            logger.warning(f"Configuration {config_name} not found")

    def remove_backend(self, config_name: str, backend_address: str) -> bool:
        """Remove backend from configuration"""
        if config_name in self.configs:
            config = self.configs[config_name]
            original_count = len(config.backends)
            config.backends = [
                b for b in config.backends if b.address != backend_address
            ]
            removed = len(config.backends) < original_count
            if removed:
                logger.info(f"Removed backend {backend_address} from {config_name}")
            return removed
        return False

    def enable_backend(self, config_name: str, backend_address: str) -> bool:
        """Enable a backend"""
        return self._toggle_backend(config_name, backend_address, True)

    def disable_backend(self, config_name: str, backend_address: str) -> bool:
        """Disable a backend"""
        return self._toggle_backend(config_name, backend_address, False)

    def _toggle_backend(
        self, config_name: str, backend_address: str, enabled: bool
    ) -> bool:
        """Toggle backend enabled status"""
        if config_name in self.configs:
            for backend in self.configs[config_name].backends:
                if backend.address == backend_address:
                    backend.enabled = enabled
                    logger.info(
                        f"{'Enabled' if enabled else 'Disabled'} backend {backend_address}"
                    )
                    return True
        return False

    def generate_config(self, config: LoadBalancerConfig) -> str:
        """Generate configuration file"""
        self.configs[config.name] = config

        if self.lb_type == LoadBalancerType.HAPROXY:
            return HAProxyConfigGenerator.generate(config)
        elif self.lb_type == LoadBalancerType.NGINX:
            return NginxConfigGenerator.generate(config)
        else:
            raise ValueError(f"Unsupported load balancer type: {self.lb_type}")

    def save_config(self, config: LoadBalancerConfig, output_path: str) -> None:
        """Generate and save configuration to file"""
        cfg_content = self.generate_config(config)
        with open(output_path, "w") as f:
            f.write(cfg_content)
        logger.info(f"Configuration saved to {output_path}")

    def get_backend_status(self, config_name: str) -> List[Dict[str, Any]]:
        """Get status of all backends"""
        if config_name not in self.configs:
            return []

        config = self.configs[config_name]
        return [
            {
                "address": b.address,
                "weight": b.weight,
                "enabled": b.enabled,
                "backup": b.backup,
                "max_connections": b.max_connections,
            }
            for b in config.backends
        ]


# Example NBA MCP load balancer configuration
def create_nba_mcp_load_balancer(port: int = 8000) -> LoadBalancerConfig:
    """Create load balancer config for NBA MCP service"""
    backends = [
        Backend(host="10.0.1.10", port=8000, weight=100),
        Backend(host="10.0.1.11", port=8000, weight=100),
        Backend(host="10.0.1.12", port=8000, weight=50),
        Backend(host="10.0.1.13", port=8000, weight=100, backup=True),
    ]

    health_check = HealthCheck(
        protocol=HealthCheckProtocol.HTTP,
        path="/health",
        interval_seconds=10,
        timeout_seconds=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    )

    return LoadBalancerConfig(
        name="nba_mcp",
        listen_port=port,
        backends=backends,
        algorithm=RoutingAlgorithm.WEIGHTED_ROUND_ROBIN,
        health_check=health_check,
        session_affinity=False,
        ssl_enabled=True,
        ssl_cert_path="/etc/ssl/certs/nba_mcp.crt",
        ssl_key_path="/etc/ssl/private/nba_mcp.key",
        connection_timeout_seconds=30,
        max_connections=10000,
        rate_limit_requests_per_second=1000,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create NBA MCP load balancer configuration
    config = create_nba_mcp_load_balancer()

    # Generate HAProxy configuration
    print("=== HAProxy Configuration ===\n")
    haproxy_manager = LoadBalancerManager(LoadBalancerType.HAPROXY)
    haproxy_config = haproxy_manager.generate_config(config)
    print(haproxy_config)

    print("\n\n=== Nginx Configuration ===\n")
    # Generate Nginx configuration
    nginx_manager = LoadBalancerManager(LoadBalancerType.NGINX)
    nginx_config = nginx_manager.generate_config(config)
    print(nginx_config)

    # Save configurations
    os.makedirs("config/load_balancers", exist_ok=True)
    haproxy_manager.save_config(config, "config/load_balancers/haproxy.cfg")
    nginx_manager.save_config(config, "config/load_balancers/nginx.conf")

    print("\n\n=== Backend Status ===\n")
    # Get backend status
    status = haproxy_manager.get_backend_status("nba_mcp")
    for backend in status:
        print(json.dumps(backend, indent=2))
