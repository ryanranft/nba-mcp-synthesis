"""
Integration Validator (Agent 19, Module 3)

Validate system integration and health:
- Module availability checks
- Dependency verification
- Integration tests
- Performance benchmarks
- System diagnostics

Helps users:
- Verify installation
- Diagnose issues
- Test integrations
- Benchmark performance
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import time

import numpy as np

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModuleHealth:
    """Health status for a module"""

    module_name: str
    status: HealthStatus
    available: bool
    dependencies_met: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "module": self.module_name,
            "status": self.status.value,
            "available": self.available,
            "dependencies_met": self.dependencies_met,
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass
class SystemHealth:
    """Overall system health"""

    status: HealthStatus
    modules: Dict[str, ModuleHealth]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "modules": {
                name: health.to_dict() for name, health in self.modules.items()
            },
            "summary": self.summary,
        }


class IntegrationValidator:
    """
    Validate system integration and health.

    Features:
    - Check module availability
    - Verify dependencies
    - Run integration tests
    - Generate health report
    """

    def __init__(self):
        """Initialize validator"""
        self.module_checks: Dict[str, ModuleHealth] = {}
        logger.info("IntegrationValidator initialized")

    def check_module(self, module_name: str) -> ModuleHealth:
        """
        Check if module is available and healthy.

        Args:
            module_name: Module to check

        Returns:
            ModuleHealth
        """
        issues = []
        warnings = []
        available = False
        dependencies_met = True

        try:
            # Try to import module
            if module_name == "econometric":
                from mcp_server import panel_data, time_series, causal_inference

                available = True

            elif module_name == "streaming":
                from mcp_server.simulations import streaming

                available = True

            elif module_name == "spatial":
                from mcp_server import spatial

                available = True

            elif module_name == "network":
                from mcp_server import network

                available = True

            elif module_name == "ml_bridge":
                from mcp_server import ml_bridge

                available = True
                # Check optional dependencies
                if not ml_bridge.check_ml_available()["sklearn"]:
                    warnings.append("scikit-learn not available, ML features limited")
                    dependencies_met = False

            elif module_name == "econometric_completion":
                from mcp_server import econometric_completion

                available = True
                # Check optional dependencies
                if not econometric_completion.check_statsmodels_available():
                    warnings.append("statsmodels not available, some features limited")

            else:
                issues.append(f"Unknown module: {module_name}")
                available = False

        except ImportError as e:
            issues.append(f"Import error: {e}")
            available = False
            dependencies_met = False
        except Exception as e:
            issues.append(f"Error: {e}")
            available = False

        # Determine status
        if not available:
            status = HealthStatus.UNHEALTHY
        elif issues:
            status = HealthStatus.DEGRADED
        elif warnings:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        health = ModuleHealth(
            module_name=module_name,
            status=status,
            available=available,
            dependencies_met=dependencies_met,
            issues=issues,
            warnings=warnings,
        )

        self.module_checks[module_name] = health

        return health

    def check_all_modules(self) -> Dict[str, ModuleHealth]:
        """
        Check all major modules.

        Returns:
            Dictionary of module health
        """
        modules = [
            "econometric",
            "streaming",
            "spatial",
            "network",
            "ml_bridge",
            "econometric_completion",
        ]

        for module in modules:
            self.check_module(module)

        return self.module_checks

    def run_integration_test(self) -> Dict[str, Any]:
        """
        Run basic integration test.

        Returns:
            Test results
        """
        logger.info("Running integration test...")

        results = {"passed": True, "tests": []}

        # Test 1: Import all modules
        try:
            from mcp_server import (
                panel_data,
                time_series,
                causal_inference,
                spatial,
                network,
                ml_bridge,
                econometric_completion,
            )
            from mcp_server.simulations import streaming

            results["tests"].append({"name": "Import all modules", "status": "PASS"})
        except Exception as e:
            results["passed"] = False
            results["tests"].append(
                {"name": "Import all modules", "status": "FAIL", "error": str(e)}
            )

        # Test 2: Create simple data and pass through components
        try:
            X = np.random.randn(100, 5)
            y = np.random.randn(100)

            # Test ml_bridge
            from mcp_server.ml_bridge import FeaturePipeline, FeatureConfig

            config = FeatureConfig(create_lags=False, create_interactions=False)
            pipeline = FeaturePipeline(config)
            X_transformed, _ = pipeline.fit_transform(X, y)

            results["tests"].append({"name": "Feature pipeline", "status": "PASS"})
        except Exception as e:
            results["passed"] = False
            results["tests"].append(
                {"name": "Feature pipeline", "status": "FAIL", "error": str(e)}
            )

        # Test 3: Integration module
        try:
            from mcp_server.integration import ModelEnsemble, Pipeline

            results["tests"].append({"name": "Integration module", "status": "PASS"})
        except Exception as e:
            results["passed"] = False
            results["tests"].append(
                {"name": "Integration module", "status": "FAIL", "error": str(e)}
            )

        logger.info(f"Integration test: {'PASSED' if results['passed'] else 'FAILED'}")

        return results

    def get_system_health(self) -> SystemHealth:
        """
        Get overall system health.

        Returns:
            SystemHealth
        """
        # Check all modules
        module_health = self.check_all_modules()

        # Determine overall status
        statuses = [health.status for health in module_health.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
            summary = "All modules healthy"
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
            unhealthy = [
                name
                for name, h in module_health.items()
                if h.status == HealthStatus.UNHEALTHY
            ]
            summary = f"Unhealthy modules: {', '.join(unhealthy)}"
        else:
            overall_status = HealthStatus.DEGRADED
            degraded = [
                name
                for name, h in module_health.items()
                if h.status == HealthStatus.DEGRADED
            ]
            summary = f"Degraded modules: {', '.join(degraded)}"

        health = SystemHealth(
            status=overall_status, modules=module_health, summary=summary
        )

        return health

    def generate_report(self) -> str:
        """
        Generate health report.

        Returns:
            Formatted report string
        """
        health = self.get_system_health()

        lines = [
            "=" * 60,
            "NBA MCP System Health Report",
            "=" * 60,
            f"Overall Status: {health.status.value.upper()}",
            f"Summary: {health.summary}",
            "",
            "Module Status:",
            "-" * 60,
        ]

        for name, module_health in health.modules.items():
            status_symbol = {
                HealthStatus.HEALTHY: "✓",
                HealthStatus.DEGRADED: "⚠",
                HealthStatus.UNHEALTHY: "✗",
                HealthStatus.UNKNOWN: "?",
            }.get(module_health.status, "?")

            lines.append(f"{status_symbol} {name:30s} {module_health.status.value}")

            if module_health.issues:
                for issue in module_health.issues:
                    lines.append(f"    Issue: {issue}")

            if module_health.warnings:
                for warning in module_health.warnings:
                    lines.append(f"    Warning: {warning}")

        lines.extend(["", "=" * 60])

        return "\n".join(lines)


def check_system_health() -> SystemHealth:
    """
    Convenience function to check system health.

    Returns:
        SystemHealth
    """
    validator = IntegrationValidator()
    return validator.get_system_health()


def print_health_report():
    """Print system health report"""
    validator = IntegrationValidator()
    print(validator.generate_report())


__all__ = [
    "HealthStatus",
    "ModuleHealth",
    "SystemHealth",
    "IntegrationValidator",
    "check_system_health",
    "print_health_report",
]
