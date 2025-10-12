"""
Dependency Health Checks Module
Monitors health of external dependencies (databases, APIs, services).
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Dependency health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    dependency_name: str
    status: HealthStatus
    response_time_ms: float
    message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


class DependencyHealthMonitor:
    """Monitors health of external dependencies"""
    
    def __init__(self):
        self.dependencies: Dict[str, Dict[str, Any]] = {}
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.max_history_size = 100
    
    def register_dependency(
        self,
        name: str,
        check_func: callable,
        check_interval_seconds: int = 60,
        timeout_seconds: int = 5,
        critical: bool = True
    ):
        """
        Register a dependency for health monitoring.
        
        Args:
            name: Dependency name
            check_func: Health check function (returns bool)
            check_interval_seconds: How often to check
            timeout_seconds: Check timeout
            critical: If True, system is unhealthy when this fails
        """
        self.dependencies[name] = {
            "check_func": check_func,
            "check_interval": check_interval_seconds,
            "timeout": timeout_seconds,
            "critical": critical,
            "last_check": None,
            "status": HealthStatus.UNKNOWN
        }
        self.health_history[name] = []
        logger.info(f"Registered dependency: {name} (critical={critical})")
    
    def check_database(self, connection_func: callable) -> HealthCheckResult:
        """Check database health"""
        start_time = time.time()
        
        try:
            connection_func()
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 100:
                status = HealthStatus.HEALTHY
                message = "Database connection successful"
            elif response_time < 500:
                status = HealthStatus.DEGRADED
                message = f"Database slow ({response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = f"Database very slow ({response_time:.0f}ms)"
            
            return HealthCheckResult(
                dependency_name="database",
                status=status,
                response_time_ms=response_time,
                message=message
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                dependency_name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Database connection failed: {str(e)}"
            )
    
    def check_api(self, api_name: str, test_func: callable) -> HealthCheckResult:
        """Check external API health"""
        start_time = time.time()
        
        try:
            test_func()
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 200:
                status = HealthStatus.HEALTHY
                message = "API responding normally"
            elif response_time < 1000:
                status = HealthStatus.DEGRADED
                message = f"API slow ({response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = f"API very slow ({response_time:.0f}ms)"
            
            return HealthCheckResult(
                dependency_name=api_name,
                status=status,
                response_time_ms=response_time,
                message=message
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                dependency_name=api_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"API check failed: {str(e)}"
            )
    
    def check_service(self, service_name: str, check_func: callable) -> HealthCheckResult:
        """Check generic service health"""
        start_time = time.time()
        
        try:
            is_healthy = check_func()
            response_time = (time.time() - start_time) * 1000
            
            if is_healthy:
                status = HealthStatus.HEALTHY
                message = "Service healthy"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Service unhealthy"
            
            return HealthCheckResult(
                dependency_name=service_name,
                status=status,
                response_time_ms=response_time,
                message=message
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                dependency_name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Service check failed: {str(e)}"
            )
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run health checks for all registered dependencies"""
        results = {}
        
        for name, config in self.dependencies.items():
            try:
                result = config["check_func"]()
                
                # Update dependency status
                config["status"] = result.status
                config["last_check"] = result.timestamp
                
                # Store in history
                self.health_history[name].append(result)
                if len(self.health_history[name]) > self.max_history_size:
                    self.health_history[name] = self.health_history[name][-self.max_history_size:]
                
                results[name] = result
                
            except Exception as e:
                logger.error(f"Error checking {name}: {e}")
                result = HealthCheckResult(
                    dependency_name=name,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    message=f"Check error: {str(e)}"
                )
                results[name] = result
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.dependencies:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "message": "No dependencies registered"
            }
        
        critical_unhealthy = []
        degraded = []
        
        for name, config in self.dependencies.items():
            status = config["status"]
            
            if status == HealthStatus.UNHEALTHY and config["critical"]:
                critical_unhealthy.append(name)
            elif status == HealthStatus.DEGRADED:
                degraded.append(name)
        
        if critical_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
            message = f"Critical dependencies unhealthy: {critical_unhealthy}"
        elif degraded:
            overall_status = HealthStatus.DEGRADED
            message = f"Some dependencies degraded: {degraded}"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "All dependencies healthy"
        
        return {
            "status": overall_status.value,
            "message": message,
            "dependencies": {
                name: {
                    "status": config["status"].value,
                    "last_check": config["last_check"],
                    "critical": config["critical"]
                }
                for name, config in self.dependencies.items()
            }
        }
    
    def get_dependency_uptime(self, dependency_name: str, hours: int = 24) -> Optional[float]:
        """Calculate uptime percentage for a dependency"""
        if dependency_name not in self.health_history:
            return None
        
        history = self.health_history[dependency_name]
        if not history:
            return None
        
        # Filter to last N hours
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        recent_checks = [
            h for h in history
            if datetime.fromisoformat(h.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_checks:
            return None
        
        healthy_checks = sum(1 for h in recent_checks if h.status == HealthStatus.HEALTHY)
        uptime = (healthy_checks / len(recent_checks)) * 100
        
        return uptime


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("DEPENDENCY HEALTH CHECKS DEMO")
    print("=" * 80)
    
    monitor = DependencyHealthMonitor()
    
    # Mock dependency check functions
    def check_postgres():
        """Mock PostgreSQL health check"""
        time.sleep(0.05)  # Simulate latency
        return monitor.check_database(lambda: True)
    
    def check_redis():
        """Mock Redis health check"""
        time.sleep(0.02)
        return monitor.check_service("redis", lambda: True)
    
    def check_s3():
        """Mock S3 health check"""
        time.sleep(0.03)
        return monitor.check_service("s3", lambda: True)
    
    def check_mlflow_api():
        """Mock MLflow API health check"""
        time.sleep(0.1)
        return monitor.check_api("mlflow_api", lambda: True)
    
    # Register dependencies
    monitor.register_dependency("postgres", check_postgres, critical=True)
    monitor.register_dependency("redis", check_redis, critical=False)
    monitor.register_dependency("s3", check_s3, critical=True)
    monitor.register_dependency("mlflow_api", check_mlflow_api, critical=False)
    
    print(f"\n✅ Registered {len(monitor.dependencies)} dependencies")
    
    # Run health checks
    print("\n" + "=" * 80)
    print("RUNNING HEALTH CHECKS")
    print("=" * 80)
    
    results = monitor.check_all()
    
    for name, result in results.items():
        status_icon = "✅" if result.status == HealthStatus.HEALTHY else "⚠️" if result.status == HealthStatus.DEGRADED else "❌"
        print(f"\n{status_icon} {name}")
        print(f"   Status: {result.status.value}")
        print(f"   Response Time: {result.response_time_ms:.2f}ms")
        print(f"   Message: {result.message}")
    
    # Get system health
    print("\n" + "=" * 80)
    print("OVERALL SYSTEM HEALTH")
    print("=" * 80)
    
    system_health = monitor.get_system_health()
    print(f"\nStatus: {system_health['status']}")
    print(f"Message: {system_health['message']}")
    
    print("\nDependencies:")
    for dep_name, dep_info in system_health['dependencies'].items():
        critical_label = "CRITICAL" if dep_info['critical'] else "non-critical"
        print(f"  - {dep_name}: {dep_info['status']} ({critical_label})")
    
    # Calculate uptime
    print("\n" + "=" * 80)
    print("UPTIME CALCULATION")
    print("=" * 80)
    
    # Run multiple checks to build history
    for _ in range(10):
        monitor.check_all()
        time.sleep(0.1)
    
    for dep_name in monitor.dependencies.keys():
        uptime = monitor.get_dependency_uptime(dep_name, hours=1)
        if uptime is not None:
            print(f"{dep_name}: {uptime:.1f}% uptime (last hour)")
    
    print("\n" + "=" * 80)
    print("Dependency Health Checks Complete!")
    print("=" * 80)

