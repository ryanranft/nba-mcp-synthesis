"""
Service Discovery & Registration

Dynamic service discovery for distributed systems:
- Service registration
- Health checking
- Load balancing
- Service catalog
- DNS-based discovery
- Consul/etcd integration

Features:
- Automatic registration
- Heartbeat monitoring
- Service metadata
- Tag-based filtering
- Multi-datacenter support
- Failover handling

Use Cases:
- Microservices coordination
- Dynamic scaling
- Service mesh integration
- Multi-region deployment
"""

import time
import threading
import requests
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceInstance:
    """Service instance definition"""
    service_id: str
    service_name: str
    host: str
    port: int
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat.isoformat() if self.last_heartbeat else None
        data['registered_at'] = self.registered_at.isoformat()
        return data

    @property
    def address(self) -> str:
        """Full service address"""
        return f"{self.host}:{self.port}"

    def is_healthy(self, timeout_seconds: int = 30) -> bool:
        """Check if service is considered healthy"""
        if self.status == ServiceStatus.MAINTENANCE:
            return False

        if not self.last_heartbeat:
            return False

        age = (datetime.now() - self.last_heartbeat).total_seconds()
        return age <= timeout_seconds


class ServiceRegistry:
    """Local service registry"""

    def __init__(self, heartbeat_timeout: int = 30):
        self.services: Dict[str, ServiceInstance] = {}
        self.heartbeat_timeout = heartbeat_timeout
        self._lock = threading.RLock()

    def register(self, instance: ServiceInstance) -> bool:
        """Register a service instance"""
        with self._lock:
            self.services[instance.service_id] = instance
            instance.last_heartbeat = datetime.now()
            logger.info(f"Registered service: {instance.service_id} at {instance.address}")
            return True

    def deregister(self, service_id: str) -> bool:
        """Deregister a service instance"""
        with self._lock:
            if service_id in self.services:
                del self.services[service_id]
                logger.info(f"Deregistered service: {service_id}")
                return True
            return False

    def heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat"""
        with self._lock:
            if service_id in self.services:
                self.services[service_id].last_heartbeat = datetime.now()
                self.services[service_id].status = ServiceStatus.HEALTHY
                return True
            return False

    def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """Get service by ID"""
        with self._lock:
            return self.services.get(service_id)

    def get_services_by_name(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of a service"""
        with self._lock:
            return [
                s for s in self.services.values()
                if s.service_name == service_name
            ]

    def get_healthy_services(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy instances of a service"""
        return [
            s for s in self.get_services_by_name(service_name)
            if s.is_healthy(self.heartbeat_timeout)
        ]

    def get_services_by_tag(self, tag: str) -> List[ServiceInstance]:
        """Get services with specific tag"""
        with self._lock:
            return [
                s for s in self.services.values()
                if tag in s.tags
            ]

    def list_all_services(self) -> List[ServiceInstance]:
        """List all registered services"""
        with self._lock:
            return list(self.services.values())

    def cleanup_stale_services(self) -> int:
        """Remove services with stale heartbeats"""
        removed = 0
        with self._lock:
            stale_ids = [
                service_id for service_id, instance in self.services.items()
                if not instance.is_healthy(self.heartbeat_timeout)
            ]
            for service_id in stale_ids:
                del self.services[service_id]
                removed += 1
                logger.warning(f"Removed stale service: {service_id}")
        return removed


class ServiceDiscovery:
    """Service discovery client"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._round_robin_indexes: Dict[str, int] = {}
        self._lock = threading.Lock()

    def discover(self, service_name: str, tags: Optional[List[str]] = None) -> Optional[ServiceInstance]:
        """Discover a healthy service instance using round-robin"""
        healthy_services = self.registry.get_healthy_services(service_name)

        # Filter by tags if provided
        if tags:
            healthy_services = [
                s for s in healthy_services
                if all(tag in s.tags for tag in tags)
            ]

        if not healthy_services:
            logger.warning(f"No healthy instances found for service: {service_name}")
            return None

        # Round-robin selection
        with self._lock:
            if service_name not in self._round_robin_indexes:
                self._round_robin_indexes[service_name] = 0

            index = self._round_robin_indexes[service_name]
            instance = healthy_services[index % len(healthy_services)]

            # Increment for next call
            self._round_robin_indexes[service_name] = (index + 1) % len(healthy_services)

        return instance

    def discover_all(self, service_name: str) -> List[ServiceInstance]:
        """Discover all healthy instances of a service"""
        return self.registry.get_healthy_services(service_name)


class HealthChecker:
    """Automated health checking"""

    def __init__(self, registry: ServiceRegistry, check_interval: int = 10):
        self.registry = registry
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._health_checks: Dict[str, Callable] = {}

    def register_health_check(self, service_name: str, check_func: Callable) -> None:
        """Register custom health check function"""
        self._health_checks[service_name] = check_func

    def _default_health_check(self, instance: ServiceInstance) -> bool:
        """Default HTTP health check"""
        try:
            url = f"http://{instance.address}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _check_service_health(self, instance: ServiceInstance) -> None:
        """Check health of a single service"""
        service_name = instance.service_name
        check_func = self._health_checks.get(service_name, self._default_health_check)

        try:
            is_healthy = check_func(instance)

            if is_healthy:
                instance.status = ServiceStatus.HEALTHY
                instance.last_heartbeat = datetime.now()
            else:
                instance.status = ServiceStatus.UNHEALTHY
                logger.warning(f"Service unhealthy: {instance.service_id}")
        except Exception as e:
            instance.status = ServiceStatus.UNHEALTHY
            logger.error(f"Health check failed for {instance.service_id}: {e}")

    def _health_check_loop(self) -> None:
        """Main health check loop"""
        while self._running:
            services = self.registry.list_all_services()

            for service in services:
                if service.status != ServiceStatus.MAINTENANCE:
                    self._check_service_health(service)

            # Cleanup stale services
            self.registry.cleanup_stale_services()

            time.sleep(self.check_interval)

    def start(self) -> None:
        """Start health checking"""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._thread.start()
        logger.info("Health checker started")

    def stop(self) -> None:
        """Stop health checking"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Health checker stopped")


class ConsulClient:
    """Consul integration for service discovery"""

    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        self.base_url = f"http://{consul_host}:{consul_port}/v1"
        self.session = requests.Session()

    def register_service(self, instance: ServiceInstance) -> bool:
        """Register service with Consul"""
        payload = {
            "ID": instance.service_id,
            "Name": instance.service_name,
            "Address": instance.host,
            "Port": instance.port,
            "Tags": instance.tags,
            "Meta": instance.metadata,
            "Check": {
                "HTTP": f"http://{instance.address}/health",
                "Interval": "10s",
                "Timeout": "5s"
            }
        }

        try:
            response = self.session.put(
                f"{self.base_url}/agent/service/register",
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Registered service with Consul: {instance.service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register with Consul: {e}")
            return False

    def deregister_service(self, service_id: str) -> bool:
        """Deregister service from Consul"""
        try:
            response = self.session.put(
                f"{self.base_url}/agent/service/deregister/{service_id}"
            )
            response.raise_for_status()
            logger.info(f"Deregistered service from Consul: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")
            return False

    def discover_services(self, service_name: str) -> List[Dict[str, Any]]:
        """Discover services from Consul"""
        try:
            response = self.session.get(
                f"{self.base_url}/health/service/{service_name}",
                params={"passing": "true"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to discover services from Consul: {e}")
            return []


# Global registry instance
_registry = None
_registry_lock = threading.Lock()


def get_registry() -> ServiceRegistry:
    """Get global service registry"""
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = ServiceRegistry()
        return _registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Service Discovery Demo ===\n")

    # Create registry
    registry = ServiceRegistry(heartbeat_timeout=10)

    # Register NBA MCP services
    services = [
        ServiceInstance(
            service_id="nba-mcp-1",
            service_name="nba-mcp-server",
            host="localhost",
            port=8000,
            tags=["api", "production", "v1"],
            metadata={"region": "us-east-1", "version": "1.0.0"}
        ),
        ServiceInstance(
            service_id="nba-mcp-2",
            service_name="nba-mcp-server",
            host="localhost",
            port=8001,
            tags=["api", "production", "v1"],
            metadata={"region": "us-east-1", "version": "1.0.0"}
        ),
        ServiceInstance(
            service_id="nba-analytics-1",
            service_name="nba-analytics",
            host="localhost",
            port=9000,
            tags=["analytics", "ml"],
            metadata={"region": "us-west-2", "version": "2.0.0"}
        )
    ]

    # Register services
    for service in services:
        registry.register(service)
        print(f"Registered: {service.service_id} at {service.address}")

    # Create discovery client
    discovery = ServiceDiscovery(registry)

    print("\n--- Service Discovery ---")

    # Discover NBA MCP server instances
    for i in range(5):
        instance = discovery.discover("nba-mcp-server")
        if instance:
            print(f"Discovered (round {i+1}): {instance.service_id} at {instance.address}")

    # Discover all analytics services
    print("\n--- All Analytics Services ---")
    analytics = discovery.discover_all("nba-analytics")
    for service in analytics:
        print(f"  - {service.service_id}: {service.address}")

    # Filter by tags
    print("\n--- Production Services ---")
    prod_services = registry.get_services_by_tag("production")
    for service in prod_services:
        print(f"  - {service.service_id}: {service.service_name}")

    # Health checker
    print("\n--- Starting Health Checker ---")
    health_checker = HealthChecker(registry, check_interval=5)
    health_checker.start()

    time.sleep(2)

    print("\n--- Service Status ---")
    for service in registry.list_all_services():
        print(f"  - {service.service_id}: {service.status.value}")

    health_checker.stop()

    print("\n=== Demo Complete ===")

