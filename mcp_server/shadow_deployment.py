"""
Shadow Deployment Module
Test new models in production without impacting users.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ShadowRequest:
    """Request sent to shadow model"""

    request_id: str
    timestamp: datetime
    inputs: Any
    primary_prediction: Any
    shadow_prediction: Any
    primary_latency_ms: float
    shadow_latency_ms: float
    match: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShadowDeploymentManager:
    """Manages shadow deployment of models"""

    def __init__(self):
        """Initialize shadow deployment manager"""
        self.shadow_configs: Dict[str, Dict] = {}
        self.shadow_requests: List[ShadowRequest] = []
        self.max_requests_stored = 10000

    def configure_shadow(
        self,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float = 100.0,
        compare_predictions: bool = True,
    ):
        """
        Configure shadow deployment for a model.

        Args:
            primary_model_id: Primary (production) model ID
            shadow_model_id: Shadow (test) model ID
            traffic_percentage: Percentage of traffic to shadow (0-100)
            compare_predictions: Whether to compare predictions
        """
        if not 0 <= traffic_percentage <= 100:
            raise ValueError("traffic_percentage must be between 0 and 100")

        self.shadow_configs[primary_model_id] = {
            "shadow_model_id": shadow_model_id,
            "traffic_percentage": traffic_percentage,
            "compare_predictions": compare_predictions,
            "enabled": True,
            "requests_shadowed": 0,
            "requests_matched": 0,
            "requests_total": 0,
        }

        logger.info(
            f"Configured shadow deployment: {primary_model_id} -> {shadow_model_id} "
            f"({traffic_percentage}% traffic)"
        )

    def should_shadow(self, primary_model_id: str) -> bool:
        """
        Determine if request should be shadowed.

        Args:
            primary_model_id: Primary model ID

        Returns:
            True if should shadow
        """
        config = self.shadow_configs.get(primary_model_id)
        if not config or not config["enabled"]:
            return False

        # Random sampling based on traffic percentage
        return random.random() * 100 < config["traffic_percentage"]

    def execute_shadow(
        self,
        request_id: str,
        primary_model_id: str,
        inputs: Any,
        primary_predict_fn: callable,
        shadow_predict_fn: callable,
    ) -> Dict[str, Any]:
        """
        Execute shadow deployment.

        Args:
            request_id: Request identifier
            primary_model_id: Primary model ID
            inputs: Model inputs
            primary_predict_fn: Function to get primary prediction
            shadow_predict_fn: Function to get shadow prediction

        Returns:
            Primary prediction (shadow runs in background)
        """
        config = self.shadow_configs.get(primary_model_id)
        if not config:
            return primary_predict_fn(inputs)

        config["requests_total"] += 1

        # Execute primary prediction (always)
        start_primary = datetime.utcnow()
        primary_result = primary_predict_fn(inputs)
        primary_latency = (datetime.utcnow() - start_primary).total_seconds() * 1000

        # Shadow execution (if enabled)
        if self.should_shadow(primary_model_id):
            config["requests_shadowed"] += 1

            try:
                start_shadow = datetime.utcnow()
                shadow_result = shadow_predict_fn(inputs)
                shadow_latency = (
                    datetime.utcnow() - start_shadow
                ).total_seconds() * 1000

                # Compare predictions
                match = (
                    (primary_result == shadow_result)
                    if config["compare_predictions"]
                    else None
                )
                if match:
                    config["requests_matched"] += 1

                # Log shadow request
                shadow_req = ShadowRequest(
                    request_id=request_id,
                    timestamp=datetime.utcnow(),
                    inputs=inputs,
                    primary_prediction=primary_result,
                    shadow_prediction=shadow_result,
                    primary_latency_ms=primary_latency,
                    shadow_latency_ms=shadow_latency,
                    match=match if match is not None else True,
                    metadata={
                        "primary_model": primary_model_id,
                        "shadow_model": config["shadow_model_id"],
                    },
                )

                self.shadow_requests.append(shadow_req)

                # Limit stored requests
                if len(self.shadow_requests) > self.max_requests_stored:
                    self.shadow_requests = self.shadow_requests[
                        -self.max_requests_stored :
                    ]

                logger.debug(
                    f"Shadow executed: match={match}, "
                    f"latency_delta={shadow_latency - primary_latency:.2f}ms"
                )

            except Exception as e:
                logger.error(f"Shadow execution failed: {e}")

        # Always return primary result
        return primary_result

    def get_shadow_metrics(self, primary_model_id: str) -> Dict[str, Any]:
        """
        Get shadow deployment metrics.

        Args:
            primary_model_id: Primary model ID

        Returns:
            Shadow metrics
        """
        config = self.shadow_configs.get(primary_model_id)
        if not config:
            return {"error": "No shadow configuration found"}

        # Calculate recent metrics
        recent_requests = [
            r
            for r in self.shadow_requests[-1000:]
            if r.metadata.get("primary_model") == primary_model_id
        ]

        if not recent_requests:
            agreement_rate = None
            avg_latency_delta = None
        else:
            agreement_rate = (
                sum(1 for r in recent_requests if r.match) / len(recent_requests) * 100
            )
            avg_latency_delta = sum(
                r.shadow_latency_ms - r.primary_latency_ms for r in recent_requests
            ) / len(recent_requests)

        return {
            "primary_model": primary_model_id,
            "shadow_model": config["shadow_model_id"],
            "traffic_percentage": config["traffic_percentage"],
            "enabled": config["enabled"],
            "requests_total": config["requests_total"],
            "requests_shadowed": config["requests_shadowed"],
            "requests_matched": config["requests_matched"],
            "shadow_percentage": (
                config["requests_shadowed"] / config["requests_total"] * 100
                if config["requests_total"] > 0
                else 0
            ),
            "agreement_rate_percent": agreement_rate,
            "avg_latency_delta_ms": avg_latency_delta,
        }

    def promote_shadow(self, primary_model_id: str):
        """
        Promote shadow model to primary.

        Args:
            primary_model_id: Current primary model ID
        """
        config = self.shadow_configs.get(primary_model_id)
        if not config:
            raise ValueError("No shadow configuration found")

        shadow_model_id = config["shadow_model_id"]

        logger.info(
            f"Promoting shadow model {shadow_model_id} to primary, "
            f"replacing {primary_model_id}"
        )

        # Remove shadow config
        del self.shadow_configs[primary_model_id]

        return shadow_model_id

    def disable_shadow(self, primary_model_id: str):
        """Disable shadow deployment"""
        if primary_model_id in self.shadow_configs:
            self.shadow_configs[primary_model_id]["enabled"] = False
            logger.info(f"Disabled shadow deployment for {primary_model_id}")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("SHADOW DEPLOYMENT DEMO")
    print("=" * 80)

    manager = ShadowDeploymentManager()

    # Configure shadow
    print("\n" + "=" * 80)
    print("CONFIGURING SHADOW DEPLOYMENT")
    print("=" * 80)

    manager.configure_shadow(
        primary_model_id="model_v1",
        shadow_model_id="model_v2",
        traffic_percentage=50.0,
        compare_predictions=True,
    )

    print("✅ Shadow deployment configured")

    # Simulate predictions
    print("\n" + "=" * 80)
    print("SIMULATING REQUESTS")
    print("=" * 80)

    def primary_predict(inputs):
        # Simulate primary model
        return sum(inputs) > 50

    def shadow_predict(inputs):
        # Simulate shadow model (slightly different)
        return sum(inputs) > 48

    for i in range(100):
        inputs = [random.randint(0, 20) for _ in range(5)]
        result = manager.execute_shadow(
            request_id=f"req_{i:04d}",
            primary_model_id="model_v1",
            inputs=inputs,
            primary_predict_fn=primary_predict,
            shadow_predict_fn=shadow_predict,
        )

    print(f"✅ Processed 100 requests")

    # Show metrics
    print("\n" + "=" * 80)
    print("SHADOW METRICS")
    print("=" * 80)

    metrics = manager.get_shadow_metrics("model_v1")
    print(f"\nPrimary Model: {metrics['primary_model']}")
    print(f"Shadow Model: {metrics['shadow_model']}")
    print(f"Traffic Percentage: {metrics['traffic_percentage']}%")
    print(f"Total Requests: {metrics['requests_total']}")
    print(f"Shadowed Requests: {metrics['requests_shadowed']}")
    print(f"Agreement Rate: {metrics['agreement_rate_percent']:.1f}%")
    print(f"Avg Latency Delta: {metrics['avg_latency_delta_ms']:.2f}ms")

    # Show decision
    print("\n" + "=" * 80)
    print("PROMOTION DECISION")
    print("=" * 80)

    if metrics["agreement_rate_percent"] and metrics["agreement_rate_percent"] >= 95:
        print("✅ Shadow model is ready for promotion!")
        print(
            f"   Agreement rate: {metrics['agreement_rate_percent']:.1f}% (threshold: 95%)"
        )
    else:
        print("⚠️  Shadow model needs more testing")
        print(
            f"   Agreement rate: {metrics['agreement_rate_percent']:.1f}% (threshold: 95%)"
        )

    print("\n" + "=" * 80)
    print("Shadow Deployment Demo Complete!")
    print("=" * 80)
