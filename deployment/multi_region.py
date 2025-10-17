#!/usr/bin/env python3
"""
Multi-Region Deployment Support
Deploy and manage NBA MCP Synthesis across multiple AWS regions
"""

import os
import json
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RegionStatus(Enum):
    """Status of deployment in a region"""

    INACTIVE = "inactive"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILING = "failing"


class FailoverStrategy(Enum):
    """Failover strategy"""

    ACTIVE_PASSIVE = "active-passive"
    ACTIVE_ACTIVE = "active-active"
    NEAREST_REGION = "nearest-region"


@dataclass
class RegionConfig:
    """Configuration for a region"""

    region_name: str
    priority: int  # 1 = primary, 2 = secondary, etc.
    status: RegionStatus = RegionStatus.INACTIVE
    endpoint_url: Optional[str] = None
    health_check_url: Optional[str] = None
    last_health_check: Optional[str] = None
    is_healthy: bool = False


@dataclass
class MultiRegionDeployment:
    """Multi-region deployment configuration"""

    deployment_id: str
    name: str
    regions: List[RegionConfig]
    failover_strategy: FailoverStrategy
    primary_region: str
    replication_enabled: bool = True
    auto_failover: bool = True


class MultiRegionManager:
    """Manages multi-region deployments"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "multi_region_config.json"
        )
        self.deployments: Dict[str, MultiRegionDeployment] = {}
        self.aws_clients: Dict[str, Any] = {}

        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)

                for deployment_data in data.get("deployments", []):
                    regions = [RegionConfig(**r) for r in deployment_data["regions"]]
                    deployment = MultiRegionDeployment(
                        deployment_id=deployment_data["deployment_id"],
                        name=deployment_data["name"],
                        regions=regions,
                        failover_strategy=FailoverStrategy(
                            deployment_data["failover_strategy"]
                        ),
                        primary_region=deployment_data["primary_region"],
                        replication_enabled=deployment_data.get(
                            "replication_enabled", True
                        ),
                        auto_failover=deployment_data.get("auto_failover", True),
                    )
                    self.deployments[deployment.deployment_id] = deployment

                logger.info(f"Loaded {len(self.deployments)} deployments")
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def _save_config(self):
        """Save configuration to file"""
        try:
            data = {
                "deployments": [
                    {
                        **asdict(d),
                        "regions": [asdict(r) for r in d.regions],
                        "failover_strategy": d.failover_strategy.value,
                    }
                    for d in self.deployments.values()
                ]
            }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def create_deployment(
        self,
        deployment_id: str,
        name: str,
        regions: List[str],
        primary_region: str,
        failover_strategy: FailoverStrategy = FailoverStrategy.ACTIVE_PASSIVE,
    ) -> MultiRegionDeployment:
        """
        Create a new multi-region deployment

        Args:
            deployment_id: Unique deployment identifier
            name: Deployment name
            regions: List of AWS region names
            primary_region: Primary region name
            failover_strategy: Failover strategy

        Returns:
            Created deployment
        """
        region_configs = [
            RegionConfig(
                region_name=region,
                priority=1 if region == primary_region else (regions.index(region) + 2),
                status=RegionStatus.INACTIVE,
            )
            for region in regions
        ]

        deployment = MultiRegionDeployment(
            deployment_id=deployment_id,
            name=name,
            regions=region_configs,
            failover_strategy=failover_strategy,
            primary_region=primary_region,
        )

        self.deployments[deployment_id] = deployment
        self._save_config()

        logger.info(f"Created multi-region deployment: {deployment_id}")
        return deployment

    def check_region_health(self, region_config: RegionConfig) -> bool:
        """Check health of a region"""
        if not region_config.health_check_url:
            return False

        try:
            import requests

            response = requests.get(region_config.health_check_url, timeout=5)
            is_healthy = response.status_code == 200
            region_config.is_healthy = is_healthy
            region_config.last_health_check = datetime.now().isoformat()
            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed for {region_config.region_name}: {e}")
            region_config.is_healthy = False
            region_config.last_health_check = datetime.now().isoformat()
            return False

    def get_active_region(self, deployment_id: str) -> Optional[RegionConfig]:
        """Get currently active region for deployment"""
        if deployment_id not in self.deployments:
            return None

        deployment = self.deployments[deployment_id]

        # Find highest priority healthy region
        sorted_regions = sorted(deployment.regions, key=lambda r: r.priority)

        for region in sorted_regions:
            if region.status == RegionStatus.ACTIVE and region.is_healthy:
                return region

        return None

    def failover(self, deployment_id: str, to_region: Optional[str] = None) -> bool:
        """
        Perform failover to another region

        Args:
            deployment_id: Deployment identifier
            to_region: Target region (if None, auto-select next healthy region)

        Returns:
            True if failover successful
        """
        if deployment_id not in self.deployments:
            logger.error(f"Deployment not found: {deployment_id}")
            return False

        deployment = self.deployments[deployment_id]

        # Find current active region
        current = self.get_active_region(deployment_id)

        # Find target region
        if to_region:
            target = next(
                (r for r in deployment.regions if r.region_name == to_region), None
            )
        else:
            # Auto-select next highest priority healthy region
            sorted_regions = sorted(deployment.regions, key=lambda r: r.priority)
            target = next(
                (
                    r
                    for r in sorted_regions
                    if r.region_name != current.region_name and r.is_healthy
                ),
                None,
            )

        if not target:
            logger.error("No suitable failover region found")
            return False

        # Perform failover
        logger.info(
            f"Failing over from {current.region_name if current else 'none'} to {target.region_name}"
        )

        if current:
            current.status = RegionStatus.INACTIVE

        target.status = RegionStatus.ACTIVE
        self._save_config()

        logger.info(f"Failover complete to {target.region_name}")
        return True


# Global instance
_multi_region_instance: Optional[MultiRegionManager] = None


def get_multi_region_manager() -> MultiRegionManager:
    """Get or create global multi-region manager"""
    global _multi_region_instance

    if _multi_region_instance is None:
        _multi_region_instance = MultiRegionManager()

    return _multi_region_instance


# CLI for testing
if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Region Deployment - Demo")
    print("=" * 70)
    print()

    # Create manager
    manager = MultiRegionManager()

    # Create deployment
    print("Creating multi-region deployment...")
    deployment = manager.create_deployment(
        deployment_id="nba-mcp-prod",
        name="NBA MCP Production",
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        primary_region="us-east-1",
        failover_strategy=FailoverStrategy.ACTIVE_PASSIVE,
    )

    print(f"  ✅ Created deployment: {deployment.deployment_id}")
    print(f"  Primary region: {deployment.primary_region}")
    print(f"  Failover strategy: {deployment.failover_strategy.value}")
    print()

    # Show regions
    print("Configured regions:")
    for region in deployment.regions:
        print(
            f"  - {region.region_name} (priority: {region.priority}, status: {region.status.value})"
        )

    print()
    print("=" * 70)
    print("✅ Multi-Region Deployment demo complete!")
    print("=" * 70)
