"""Health Check Endpoints - IMPORTANT 17"""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthCheck:
    """Health check system"""

    def __init__(self):
        self.checks: Dict[str, callable] = {}

    def register(self, name: str, check_func: callable):
        """Register a health check"""
        self.checks[name] = check_func

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        for name, check_func in self.checks.items():
            try:
                check_result = (
                    await check_func()
                    if asyncio.iscoroutinefunction(check_func)
                    else check_func()
                )
                results["checks"][name] = {
                    "status": "pass" if check_result else "fail",
                    "details": check_result,
                }
            except Exception as e:
                results["checks"][name] = {"status": "fail", "error": str(e)}
                results["status"] = "degraded"

        # Overall status
        if any(c["status"] == "fail" for c in results["checks"].values()):
            results["status"] = "unhealthy"

        return results


# Global health check instance
_health_check = HealthCheck()


def get_health_check() -> HealthCheck:
    """Get global health check instance"""
    return _health_check


# Register standard checks
def check_database() -> bool:
    """Check database connectivity"""
    try:
        from mcp_server.database import get_database_engine

        engine = get_database_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_s3() -> bool:
    """Check S3 connectivity"""
    try:
        import boto3

        s3 = boto3.client("s3")
        s3.head_bucket(Bucket="nba-mcp-books-20251011")
        return True
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        return False


def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    import psutil

    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "percent": memory.percent,
        "status": "ok" if memory.percent < 90 else "critical",
    }


def check_disk() -> Dict[str, Any]:
    """Check disk usage"""
    import psutil

    disk = psutil.disk_usage("/")
    return {
        "total": disk.total,
        "free": disk.free,
        "percent": disk.percent,
        "status": "ok" if disk.percent < 90 else "critical",
    }


# Register all checks
get_health_check().register("database", check_database)
get_health_check().register("s3", check_s3)
get_health_check().register("memory", check_memory)
get_health_check().register("disk", check_disk)


# FastAPI endpoints (if using FastAPI)
"""
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return await get_health_check().check_all()

@app.get("/ready")
async def readiness():
    # Check if system is ready to serve requests
    health = await get_health_check().check_all()
    if health["status"] == "unhealthy":
        return {"ready": False}, 503
    return {"ready": True}

@app.get("/live")
async def liveness():
    # Simple liveness check
    return {"alive": True}
"""
