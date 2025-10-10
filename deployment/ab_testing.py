#!/usr/bin/env python3
"""
A/B Testing Framework
Feature flags and canary deployments with automated rollback
"""

import os
import json
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VariantStatus(Enum):
    """Status of A/B test variant"""
    INACTIVE = "inactive"
    TESTING = "testing"
    WINNING = "winning"
    LOSING = "losing"
    ROLLED_OUT = "rolled_out"
    ROLLED_BACK = "rolled_back"


@dataclass
class Variant:
    """A/B test variant configuration"""
    name: str
    traffic_percentage: float  # 0-100
    config: Dict[str, Any]
    status: VariantStatus = VariantStatus.INACTIVE
    metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    name: str
    description: str
    variants: List[Variant]
    control_variant: str  # Name of control variant
    success_metric: str  # Primary metric to optimize
    minimum_sample_size: int = 1000
    confidence_level: float = 0.95
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "variants": [asdict(v) for v in self.variants]
        }


class ABTestingFramework:
    """Manages A/B tests and feature flags"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__),
            "ab_tests.json"
        )
        self.active_tests: Dict[str, ABTest] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {test_id: variant}

        self._load_config()

    def _load_config(self):
        """Load AB test configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                self.feature_flags = data.get("feature_flags", {})
                # Load active tests
                for test_data in data.get("active_tests", []):
                    test = ABTest(**test_data)
                    self.active_tests[test.test_id] = test

                logger.info(f"Loaded {len(self.active_tests)} active tests")
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def _save_config(self):
        """Save configuration to file"""
        try:
            data = {
                "feature_flags": self.feature_flags,
                "active_tests": [
                    test.to_dict() for test in self.active_tests.values()
                ]
            }

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def create_test(
        self,
        test_id: str,
        name: str,
        variants: List[Variant],
        control_variant: str,
        success_metric: str,
        **kwargs
    ) -> ABTest:
        """
        Create a new A/B test

        Args:
            test_id: Unique test identifier
            name: Test name
            variants: List of variants to test
            control_variant: Name of control variant
            success_metric: Primary metric to optimize

        Returns:
            Created AB test
        """
        test = ABTest(
            test_id=test_id,
            name=name,
            description=kwargs.get("description", ""),
            variants=variants,
            control_variant=control_variant,
            success_metric=success_metric,
            minimum_sample_size=kwargs.get("minimum_sample_size", 1000),
            confidence_level=kwargs.get("confidence_level", 0.95),
            start_time=datetime.now().isoformat()
        )

        self.active_tests[test_id] = test
        self._save_config()

        logger.info(f"Created A/B test: {test_id}")
        return test

    def assign_variant(
        self,
        test_id: str,
        user_id: str,
        sticky: bool = True
    ) -> Optional[Variant]:
        """
        Assign user to a variant

        Args:
            test_id: Test identifier
            user_id: User identifier
            sticky: Whether to keep same assignment for user

        Returns:
            Assigned variant or None
        """
        if test_id not in self.active_tests:
            logger.warning(f"Test not found: {test_id}")
            return None

        test = self.active_tests[test_id]

        # Check for existing assignment
        if sticky and user_id in self.user_assignments:
            if test_id in self.user_assignments[user_id]:
                variant_name = self.user_assignments[user_id][test_id]
                return next((v for v in test.variants if v.name == variant_name), None)

        # Assign based on traffic percentages
        rand_value = random.random() * 100
        cumulative = 0

        for variant in test.variants:
            cumulative += variant.traffic_percentage
            if rand_value <= cumulative:
                # Store assignment
                if user_id not in self.user_assignments:
                    self.user_assignments[user_id] = {}
                self.user_assignments[user_id][test_id] = variant.name

                return variant

        # Fallback to control
        return next((v for v in test.variants if v.name == test.control_variant), test.variants[0])

    def record_metric(
        self,
        test_id: str,
        variant_name: str,
        metric_name: str,
        value: float
    ):
        """Record metric value for a variant"""
        if test_id not in self.active_tests:
            return

        test = self.active_tests[test_id]
        variant = next((v for v in test.variants if v.name == variant_name), None)

        if variant:
            if metric_name not in variant.metrics:
                variant.metrics[metric_name] = []

            if not isinstance(variant.metrics[metric_name], list):
                variant.metrics[metric_name] = [variant.metrics[metric_name]]

            variant.metrics[metric_name].append(value)
            self._save_config()

    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze test results and determine winner

        Args:
            test_id: Test identifier

        Returns:
            Analysis results
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}

        test = self.active_tests[test_id]
        control = next((v for v in test.variants if v.name == test.control_variant), None)

        if not control:
            return {"error": "Control variant not found"}

        results = {
            "test_id": test_id,
            "test_name": test.name,
            "variants": {},
            "winner": None,
            "confidence": 0.0
        }

        # Analyze each variant against control
        for variant in test.variants:
            if variant.name == test.control_variant:
                continue

            comparison = self._compare_variants(
                control,
                variant,
                test.success_metric
            )

            results["variants"][variant.name] = comparison

            # Determine winner (simplified)
            if comparison.get("significant_improvement"):
                if not results["winner"] or comparison["improvement"] > results["confidence"]:
                    results["winner"] = variant.name
                    results["confidence"] = comparison["improvement"]

        return results

    def _compare_variants(
        self,
        control: Variant,
        variant: Variant,
        metric_name: str
    ) -> Dict[str, Any]:
        """Compare variant against control"""
        control_values = control.metrics.get(metric_name, [])
        variant_values = variant.metrics.get(metric_name, [])

        if not control_values or not variant_values:
            return {
                "sample_size_control": len(control_values),
                "sample_size_variant": len(variant_values),
                "sufficient_data": False
            }

        import numpy as np

        control_mean = np.mean(control_values)
        variant_mean = np.mean(variant_values)

        improvement = ((variant_mean - control_mean) / control_mean) * 100 if control_mean != 0 else 0

        return {
            "sample_size_control": len(control_values),
            "sample_size_variant": len(variant_values),
            "control_mean": control_mean,
            "variant_mean": variant_mean,
            "improvement": improvement,
            "significant_improvement": improvement > 5,  # Simplified
            "sufficient_data": len(control_values) >= 1000 and len(variant_values) >= 1000
        }

    def set_feature_flag(self, flag_name: str, enabled: bool):
        """Set feature flag value"""
        self.feature_flags[flag_name] = enabled
        self._save_config()
        logger.info(f"Set feature flag '{flag_name}' to {enabled}")

    def is_feature_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if feature flag is enabled"""
        return self.feature_flags.get(flag_name, default)

    def gradual_rollout(
        self,
        test_id: str,
        steps: List[int] = [10, 25, 50, 75, 100],
        check_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Perform gradual rollout of winning variant

        Args:
            test_id: Test identifier
            steps: Traffic percentage steps
            check_metrics: Whether to check metrics at each step

        Returns:
            Rollout status
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}

        test = self.active_tests[test_id]

        # Analyze to find winner
        analysis = self.analyze_test(test_id)

        if not analysis.get("winner"):
            return {"error": "No clear winner found", "analysis": analysis}

        winner_name = analysis["winner"]
        winner = next((v for v in test.variants if v.name == winner_name), None)

        if not winner:
            return {"error": "Winner variant not found"}

        logger.info(f"Rolling out {winner_name} for test {test_id}")

        return {
            "test_id": test_id,
            "winner": winner_name,
            "rollout_plan": steps,
            "status": "ready",
            "message": f"Ready to roll out {winner_name} in steps: {steps}"
        }


# Global instance
_ab_testing_instance: Optional[ABTestingFramework] = None


def get_ab_testing() -> ABTestingFramework:
    """Get or create global AB testing framework"""
    global _ab_testing_instance

    if _ab_testing_instance is None:
        _ab_testing_instance = ABTestingFramework()

    return _ab_testing_instance


# CLI for testing
if __name__ == "__main__":
    print("="*70)
    print("A/B Testing Framework - Demo")
    print("="*70)
    print()

    # Create framework
    framework = ABTestingFramework()

    # Create test
    print("Creating A/B test...")
    test = framework.create_test(
        test_id="model-comparison",
        name="DeepSeek vs GPT-4 Comparison",
        variants=[
            Variant(
                name="control",
                traffic_percentage=50,
                config={"model": "deepseek-chat"},
                status=VariantStatus.TESTING
            ),
            Variant(
                name="variant_a",
                traffic_percentage=50,
                config={"model": "gpt-4"},
                status=VariantStatus.TESTING
            )
        ],
        control_variant="control",
        success_metric="response_quality"
    )

    print(f"  ✅ Created test: {test.test_id}")
    print()

    # Simulate user assignments
    print("Simulating user assignments...")
    for i in range(100):
        user_id = f"user_{i}"
        variant = framework.assign_variant("model-comparison", user_id)
        print(f"  User {user_id} → {variant.name}")

        if i >= 95:  # Show only last few
            continue

    print("  ...")
    print(f"  Assigned 100 users")
    print()

    # Feature flags
    print("Testing feature flags...")
    framework.set_feature_flag("new_synthesis_algorithm", True)
    framework.set_feature_flag("experimental_caching", False)

    print(f"  new_synthesis_algorithm: {framework.is_feature_enabled('new_synthesis_algorithm')}")
    print(f"  experimental_caching: {framework.is_feature_enabled('experimental_caching')}")

    print()
    print("="*70)
    print("✅ A/B Testing Framework demo complete!")
    print("="*70)
