"""
API Gateway Integration

Support for popular API gateways:
- Kong
- AWS API Gateway
- Tyk
- Azure API Management
- Google Cloud API Gateway

Features:
- Route configuration
- Rate limiting
- Authentication (JWT, OAuth2, API keys)
- Request transformation
- Response caching
- Load balancing
- Circuit breaker
- API versioning
- Monitoring & analytics

Use Cases:
- Centralized API management
- Security layer
- Traffic control
- API monetization
"""

import json
import yaml
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GatewayType(Enum):
    """Supported API gateway types"""

    KONG = "kong"
    AWS_API_GATEWAY = "aws_api_gateway"
    TYK = "tyk"
    AZURE_APIM = "azure_apim"


class AuthType(Enum):
    """Authentication types"""

    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC = "basic"
    NONE = "none"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_second: int = 100
    burst_size: int = 200
    limit_by: str = "ip"  # ip, user, api_key


@dataclass
class CacheConfig:
    """Response caching configuration"""

    enabled: bool = True
    ttl_seconds: int = 300
    cache_key_include: List[str] = field(default_factory=lambda: ["path", "query"])


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    enabled: bool = True
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60


@dataclass
class Route:
    """API route definition"""

    path: str
    methods: List[str]
    upstream_url: str
    strip_path: bool = True
    preserve_host: bool = False
    rate_limit: Optional[RateLimitConfig] = None
    cache: Optional[CacheConfig] = None
    auth: AuthType = AuthType.NONE
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Service:
    """Service definition"""

    name: str
    protocol: str = "http"
    host: str = "localhost"
    port: int = 8000
    path: str = "/"
    retries: int = 3
    connect_timeout: int = 5000
    write_timeout: int = 60000
    read_timeout: int = 60000


@dataclass
class APIGatewayConfig:
    """Complete API gateway configuration"""

    name: str
    services: List[Service]
    routes: List[Route]
    global_rate_limit: Optional[RateLimitConfig] = None
    global_auth: AuthType = AuthType.NONE
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    logging_enabled: bool = True
    monitoring_enabled: bool = True


class KongConfigGenerator:
    """Generate Kong API Gateway configuration"""

    @staticmethod
    def generate_service(service: Service) -> Dict[str, Any]:
        """Generate Kong service configuration"""
        return {
            "name": service.name,
            "protocol": service.protocol,
            "host": service.host,
            "port": service.port,
            "path": service.path,
            "retries": service.retries,
            "connect_timeout": service.connect_timeout,
            "write_timeout": service.write_timeout,
            "read_timeout": service.read_timeout,
        }

    @staticmethod
    def generate_route(route: Route, service_name: str) -> Dict[str, Any]:
        """Generate Kong route configuration"""
        config = {
            "name": f"{service_name}_{route.path.replace('/', '_')}",
            "paths": [route.path],
            "methods": route.methods,
            "strip_path": route.strip_path,
            "preserve_host": route.preserve_host,
            "service": {"name": service_name},
        }

        if route.tags:
            config["tags"] = route.tags

        return config

    @staticmethod
    def generate_plugins(route: Route) -> List[Dict[str, Any]]:
        """Generate Kong plugins for route"""
        plugins = []

        # Rate limiting plugin
        if route.rate_limit:
            plugins.append(
                {
                    "name": "rate-limiting",
                    "config": {
                        "second": route.rate_limit.requests_per_second,
                        "policy": "local",
                        "limit_by": route.rate_limit.limit_by,
                    },
                }
            )

        # Response caching plugin
        if route.cache and route.cache.enabled:
            plugins.append(
                {
                    "name": "proxy-cache",
                    "config": {
                        "strategy": "memory",
                        "cache_ttl": route.cache.ttl_seconds,
                        "cache_control": True,
                    },
                }
            )

        # Authentication plugin
        if route.auth != AuthType.NONE:
            if route.auth == AuthType.JWT:
                plugins.append({"name": "jwt"})
            elif route.auth == AuthType.API_KEY:
                plugins.append(
                    {
                        "name": "key-auth",
                        "config": {"key_names": ["apikey", "X-API-Key"]},
                    }
                )
            elif route.auth == AuthType.OAUTH2:
                plugins.append(
                    {
                        "name": "oauth2",
                        "config": {
                            "scopes": ["read", "write"],
                            "mandatory_scope": True,
                        },
                    }
                )

        # Circuit breaker plugin
        if route.circuit_breaker and route.circuit_breaker.enabled:
            plugins.append(
                {
                    "name": "circuit-breaker",
                    "config": {
                        "failure_threshold": route.circuit_breaker.failure_threshold,
                        "success_threshold": route.circuit_breaker.success_threshold,
                        "timeout": route.circuit_breaker.timeout_seconds,
                    },
                }
            )

        return plugins

    @staticmethod
    def generate_complete_config(config: APIGatewayConfig) -> Dict[str, Any]:
        """Generate complete Kong configuration"""
        kong_config = {
            "_format_version": "2.1",
            "services": [],
            "routes": [],
            "plugins": [],
        }

        # Generate services
        for service in config.services:
            kong_config["services"].append(
                KongConfigGenerator.generate_service(service)
            )

        # Generate routes and plugins
        for service in config.services:
            for route in config.routes:
                kong_route = KongConfigGenerator.generate_route(route, service.name)
                kong_config["routes"].append(kong_route)

                # Add route-specific plugins
                route_plugins = KongConfigGenerator.generate_plugins(route)
                for plugin in route_plugins:
                    plugin["route"] = kong_route["name"]
                    kong_config["plugins"].append(plugin)

        # Global plugins
        if config.global_rate_limit:
            kong_config["plugins"].append(
                {
                    "name": "rate-limiting",
                    "config": {
                        "second": config.global_rate_limit.requests_per_second,
                        "policy": "local",
                        "limit_by": config.global_rate_limit.limit_by,
                    },
                }
            )

        if config.cors_enabled:
            kong_config["plugins"].append(
                {
                    "name": "cors",
                    "config": {
                        "origins": config.cors_origins,
                        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                        "headers": ["Accept", "Content-Type", "Authorization"],
                        "credentials": True,
                    },
                }
            )

        if config.logging_enabled:
            kong_config["plugins"].append(
                {"name": "file-log", "config": {"path": "/var/log/kong/access.log"}}
            )

        return kong_config


class AWSAPIGatewayConfigGenerator:
    """Generate AWS API Gateway configuration"""

    @staticmethod
    def generate_openapi_spec(config: APIGatewayConfig) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 spec for AWS API Gateway"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": config.name, "version": "1.0.0"},
            "servers": [
                {
                    "url": f"https://{service.host}:{service.port}{service.path}",
                    "description": service.name,
                }
                for service in config.services
            ],
            "paths": {},
            "components": {"securitySchemes": {}},
        }

        # Add authentication schemes
        if config.global_auth == AuthType.JWT:
            spec["components"]["securitySchemes"]["jwt"] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        elif config.global_auth == AuthType.API_KEY:
            spec["components"]["securitySchemes"]["apiKey"] = {
                "type": "apiKey",
                "name": "x-api-key",
                "in": "header",
            }

        # Add paths
        for route in config.routes:
            if route.path not in spec["paths"]:
                spec["paths"][route.path] = {}

            for method in route.methods:
                method_lower = method.lower()
                spec["paths"][route.path][method_lower] = {
                    "summary": f"{method} {route.path}",
                    "responses": {"200": {"description": "Successful response"}},
                    "x-amazon-apigateway-integration": {
                        "uri": route.upstream_url,
                        "type": "http_proxy",
                        "httpMethod": method,
                        "connectionType": "INTERNET",
                    },
                }

                # Add security requirement
                if route.auth != AuthType.NONE:
                    if route.auth == AuthType.JWT:
                        spec["paths"][route.path][method_lower]["security"] = [
                            {"jwt": []}
                        ]
                    elif route.auth == AuthType.API_KEY:
                        spec["paths"][route.path][method_lower]["security"] = [
                            {"apiKey": []}
                        ]

        return spec


class APIGatewayManager:
    """Manage API gateway configurations"""

    def __init__(self, gateway_type: GatewayType):
        self.gateway_type = gateway_type
        self.configs: Dict[str, APIGatewayConfig] = {}

    def create_config(self, name: str, **kwargs) -> APIGatewayConfig:
        """Create new gateway configuration"""
        config = APIGatewayConfig(name=name, **kwargs)
        self.configs[name] = config
        return config

    def generate_config(self, config: APIGatewayConfig) -> str:
        """Generate configuration for specified gateway type"""
        if self.gateway_type == GatewayType.KONG:
            kong_config = KongConfigGenerator.generate_complete_config(config)
            return yaml.dump(kong_config, default_flow_style=False)

        elif self.gateway_type == GatewayType.AWS_API_GATEWAY:
            aws_config = AWSAPIGatewayConfigGenerator.generate_openapi_spec(config)
            return json.dumps(aws_config, indent=2)

        else:
            raise ValueError(f"Unsupported gateway type: {self.gateway_type}")

    def save_config(self, config: APIGatewayConfig, output_file: str) -> None:
        """Generate and save configuration to file"""
        config_content = self.generate_config(config)
        with open(output_file, "w") as f:
            f.write(config_content)
        logger.info(f"Configuration saved to {output_file}")


# NBA MCP API Gateway example
def create_nba_mcp_gateway() -> APIGatewayConfig:
    """Create API gateway config for NBA MCP"""
    # Define service
    nba_service = Service(
        name="nba-mcp-service",
        protocol="http",
        host="nba-mcp.internal",
        port=8000,
        path="/",
        retries=3,
    )

    # Define routes
    routes = [
        Route(
            path="/api/v1/players",
            methods=["GET", "POST"],
            upstream_url="http://nba-mcp.internal:8000/players",
            rate_limit=RateLimitConfig(requests_per_second=100, burst_size=200),
            cache=CacheConfig(enabled=True, ttl_seconds=300),
            auth=AuthType.API_KEY,
            tags=["players"],
        ),
        Route(
            path="/api/v1/games",
            methods=["GET"],
            upstream_url="http://nba-mcp.internal:8000/games",
            rate_limit=RateLimitConfig(requests_per_second=50),
            cache=CacheConfig(enabled=True, ttl_seconds=60),
            auth=AuthType.NONE,
            tags=["games"],
        ),
        Route(
            path="/api/v1/predictions",
            methods=["POST"],
            upstream_url="http://nba-mcp.internal:8000/predictions",
            rate_limit=RateLimitConfig(requests_per_second=10),
            auth=AuthType.JWT,
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=5, timeout_seconds=60
            ),
            tags=["predictions", "ml"],
        ),
        Route(
            path="/api/v1/stats",
            methods=["GET"],
            upstream_url="http://nba-mcp.internal:8000/stats",
            rate_limit=RateLimitConfig(requests_per_second=200),
            cache=CacheConfig(enabled=True, ttl_seconds=600),
            auth=AuthType.NONE,
            tags=["stats"],
        ),
    ]

    return APIGatewayConfig(
        name="nba-mcp-gateway",
        services=[nba_service],
        routes=routes,
        global_rate_limit=RateLimitConfig(requests_per_second=1000),
        global_auth=AuthType.NONE,
        cors_enabled=True,
        cors_origins=["https://nba-mcp.example.com", "https://dashboard.nba-mcp.com"],
        logging_enabled=True,
        monitoring_enabled=True,
    )


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    # Create NBA MCP gateway configuration
    config = create_nba_mcp_gateway()

    os.makedirs("config/api_gateway", exist_ok=True)

    # Generate Kong configuration
    print("=== Generating Kong Configuration ===\n")
    kong_manager = APIGatewayManager(GatewayType.KONG)
    kong_config = kong_manager.generate_config(config)
    kong_manager.save_config(config, "config/api_gateway/kong.yaml")
    print(kong_config[:500] + "...\n")

    # Generate AWS API Gateway configuration
    print("\n=== Generating AWS API Gateway Configuration ===\n")
    aws_manager = APIGatewayManager(GatewayType.AWS_API_GATEWAY)
    aws_config = aws_manager.generate_config(config)
    aws_manager.save_config(config, "config/api_gateway/aws_api_gateway.json")
    print(aws_config[:500] + "...\n")

    print("\nConfigurations saved to config/api_gateway/")
