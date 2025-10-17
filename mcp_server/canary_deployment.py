"""
Canary Deployment Module
Gradually roll out new model versions to production traffic.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CanaryMetrics:
    """Metrics for canary deployment"""

    model_id: str
    requests: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    user_feedback_positive: int = 0
    user_feedback_negative: int = 0


class CanaryDeploymentManager:
    """Manages canary deployments"""

    def __init__(self):
        """Initialize canary deployment manager"""
        self.canary_configs: Dict[str, Dict] = {}
        self.metrics: Dict[str, CanaryMetrics] = {}

    def start_canary(
        self,
        stable_model_id: str,
        canary_model_id: str,
        initial_traffic_percent: float = 5.0,
        max_traffic_percent: float = 50.0,
        increment_step: float = 5.0,
        increment_interval_minutes: int = 30,
    ):
        """
        Start canary deployment.

        Args:
            stable_model_id: Stable (production) model ID
            canary_model_id: Canary (new) model ID
            initial_traffic_percent: Starting traffic percentage
            max_traffic_percent: Maximum traffic percentage
            increment_step: Traffic increment step
            increment_interval_minutes: Time between increments
        """
        self.canary_configs[stable_model_id] = {
            "canary_model_id": canary_model_id,
            "current_traffic_percent": initial_traffic_percent,
            "max_traffic_percent": max_traffic_percent,
            "increment_step": increment_step,
            "increment_interval_minutes": increment_interval_minutes,
            "started_at": datetime.utcnow(),
            "last_increment": datetime.utcnow(),
            "status": "active",
        }

        # Initialize metrics
        self.metrics[stable_model_id] = CanaryMetrics(model_id=stable_model_id)
        self.metrics[canary_model_id] = CanaryMetrics(model_id=canary_model_id)

        logger.info(
            f"Started canary deployment: {stable_model_id} -> {canary_model_id} "
            f"({initial_traffic_percent}% initial traffic)"
        )

    def route_request(self, stable_model_id: str, request_id: str) -> str:
        """
        Determine which model should handle the request.

        Args:
            stable_model_id: Stable model ID
            request_id: Request identifier

        Returns:
            Model ID to use
        """
        config = self.canary_configs.get(stable_model_id)
        if not config or config["status"] != "active":
            return stable_model_id

        # Auto-increment traffic if interval passed
        self._check_auto_increment(stable_model_id)

        # Route based on traffic percentage
        if random.random() * 100 < config["current_traffic_percent"]:
            return config["canary_model_id"]
        else:
            return stable_model_id

    def _check_auto_increment(self, stable_model_id: str):
        """Check if traffic should be auto-incremented"""
        config = self.canary_configs.get(stable_model_id)
        if not config:
            return

        now = datetime.utcnow()
        minutes_since_last = (now - config["last_increment"]).total_seconds() / 60

        if minutes_since_last >= config["increment_interval_minutes"]:
            # Check canary health before incrementing
            canary_healthy = self._is_canary_healthy(stable_model_id)

            if (
                canary_healthy
                and config["current_traffic_percent"] < config["max_traffic_percent"]
            ):
                old_percent = config["current_traffic_percent"]
                config["current_traffic_percent"] = min(
                    config["current_traffic_percent"] + config["increment_step"],
                    config["max_traffic_percent"],
                )
                config["last_increment"] = now

                logger.info(
                    f"Auto-incremented canary traffic: "
                    f"{old_percent}% -> {config['current_traffic_percent']}%"
                )

    def _is_canary_healthy(self, stable_model_id: str) -> bool:
        """
        Check if canary is healthy compared to stable.

        Args:
            stable_model_id: Stable model ID

        Returns:
            True if canary is healthy
        """
        config = self.canary_configs.get(stable_model_id)
        if not config:
            return False

        canary_model_id = config["canary_model_id"]
        stable_metrics = self.metrics.get(stable_model_id)
        canary_metrics = self.metrics.get(canary_model_id)

        if not stable_metrics or not canary_metrics:
            return False

        # Require minimum requests
        if canary_metrics.requests < 100:
            logger.debug("Canary needs more requests for health check")
            return False

        # Check error rate (canary should not exceed stable by >2%)
        error_rate_delta = canary_metrics.error_rate - stable_metrics.error_rate
        if error_rate_delta > 2.0:
            logger.warning(f"Canary error rate too high: +{error_rate_delta:.2f}%")
            return False

        # Check latency (canary should not exceed stable by >20%)
        if stable_metrics.avg_latency_ms > 0:
            latency_ratio = (
                canary_metrics.avg_latency_ms / stable_metrics.avg_latency_ms
            )
            if latency_ratio > 1.2:
                logger.warning(f"Canary latency too high: {latency_ratio:.2f}x")
                return False

        return True

    def record_request(self, model_id: str, success: bool, latency_ms: float):
        """
        Record request metrics.

        Args:
            model_id: Model ID
            success: Whether request succeeded
            latency_ms: Request latency
        """
        if model_id not in self.metrics:
            self.metrics[model_id] = CanaryMetrics(model_id=model_id)

        metrics = self.metrics[model_id]
        metrics.requests += 1

        if not success:
            metrics.errors += 1

        # Update average latency
        metrics.avg_latency_ms = (
            metrics.avg_latency_ms * (metrics.requests - 1) + latency_ms
        ) / metrics.requests

        # Update error rate
        metrics.error_rate = (metrics.errors / metrics.requests) * 100

    def get_canary_status(self, stable_model_id: str) -> Dict[str, Any]:
        """
        Get canary deployment status.

        Args:
            stable_model_id: Stable model ID

        Returns:
            Status dictionary
        """
        config = self.canary_configs.get(stable_model_id)
        if not config:
            return {"error": "No canary deployment found"}

        canary_model_id = config["canary_model_id"]
        stable_metrics = self.metrics.get(stable_model_id)
        canary_metrics = self.metrics.get(canary_model_id)

        return {
            "stable_model": stable_model_id,
            "canary_model": canary_model_id,
            "status": config["status"],
            "current_traffic_percent": config["current_traffic_percent"],
            "max_traffic_percent": config["max_traffic_percent"],
            "started_at": config["started_at"].isoformat(),
            "stable_metrics": {
                "requests": stable_metrics.requests if stable_metrics else 0,
                "error_rate": stable_metrics.error_rate if stable_metrics else 0,
                "avg_latency_ms": (
                    stable_metrics.avg_latency_ms if stable_metrics else 0
                ),
            },
            "canary_metrics": {
                "requests": canary_metrics.requests if canary_metrics else 0,
                "error_rate": canary_metrics.error_rate if canary_metrics else 0,
                "avg_latency_ms": (
                    canary_metrics.avg_latency_ms if canary_metrics else 0
                ),
            },
            "healthy": self._is_canary_healthy(stable_model_id),
        }

    def rollback_canary(self, stable_model_id: str):
        """
        Rollback canary deployment.

        Args:
            stable_model_id: Stable model ID
        """
        if stable_model_id in self.canary_configs:
            self.canary_configs[stable_model_id]["status"] = "rolled_back"
            self.canary_configs[stable_model_id]["current_traffic_percent"] = 0.0
            logger.warning(f"Rolled back canary for {stable_model_id}")

    def promote_canary(self, stable_model_id: str):
        """
        Promote canary to stable.

        Args:
            stable_model_id: Stable model ID
        """
        config = self.canary_configs.get(stable_model_id)
        if not config:
            raise ValueError("No canary deployment found")

        canary_model_id = config["canary_model_id"]
        config["status"] = "promoted"

        logger.info(f"Promoted canary {canary_model_id} to replace {stable_model_id}")

        return canary_model_id


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("CANARY DEPLOYMENT DEMO")
    print("=" * 80)

    manager = CanaryDeploymentManager()

    # Start canary
    print("\n" + "=" * 80)
    print("STARTING CANARY DEPLOYMENT")
    print("=" * 80)

    manager.start_canary(
        stable_model_id="model_v1",
        canary_model_id="model_v2",
        initial_traffic_percent=10.0,
        max_traffic_percent=50.0,
        increment_step=10.0,
        increment_interval_minutes=1,  # Fast for demo
    )

    print("✅ Canary deployment started at 10% traffic")

    # Simulate requests
    print("\n" + "=" * 80)
    print("SIMULATING REQUESTS")
    print("=" * 80)

    for i in range(1000):
        model_id = manager.route_request("model_v1", f"req_{i:04d}")

        # Simulate different error rates
        if model_id == "model_v1":
            success = random.random() > 0.01  # 1% error rate
            latency = random.uniform(50, 100)
        else:  # model_v2 (canary)
            success = random.random() > 0.015  # 1.5% error rate (slightly worse)
            latency = random.uniform(55, 110)

        manager.record_request(model_id, success, latency)

    print(f"✅ Processed 1000 requests")

    # Show status
    print("\n" + "=" * 80)
    print("CANARY STATUS")
    print("=" * 80)

    status = manager.get_canary_status("model_v1")

    print(f"\nStable Model: {status['stable_model']}")
    print(f"Canary Model: {status['canary_model']}")
    print(f"Status: {status['status']}")
    print(f"Current Traffic: {status['current_traffic_percent']}%")
    print(f"Healthy: {'✅' if status['healthy'] else '❌'}")

    print("\nStable Metrics:")
    print(f"  Requests: {status['stable_metrics']['requests']}")
    print(f"  Error Rate: {status['stable_metrics']['error_rate']:.2f}%")
    print(f"  Avg Latency: {status['stable_metrics']['avg_latency_ms']:.2f}ms")

    print("\nCanary Metrics:")
    print(f"  Requests: {status['canary_metrics']['requests']}")
    print(f"  Error Rate: {status['canary_metrics']['error_rate']:.2f}%")
    print(f"  Avg Latency: {status['canary_metrics']['avg_latency_ms']:.2f}ms")

    # Decision
    print("\n" + "=" * 80)
    print("PROMOTION DECISION")
    print("=" * 80)

    if status["healthy"]:
        print("✅ Canary is healthy and ready for more traffic")
    else:
        print("⚠️  Canary needs attention or rollback")

    print("\n" + "=" * 80)
    print("Canary Deployment Demo Complete!")
    print("=" * 80)
