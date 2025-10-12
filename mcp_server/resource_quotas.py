"""
Resource Quotas & Limits Module
Enforces quotas on API calls, storage, compute, and prevents abuse.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be limited"""
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    COMPUTE_HOURS = "compute_hours"
    PREDICTIONS = "predictions"
    DATA_TRANSFER_GB = "data_transfer_gb"


@dataclass
class ResourceQuota:
    """Quota configuration for a resource"""
    resource_type: ResourceType
    limit: float
    period: str  # 'hour', 'day', 'month'
    current_usage: float = 0.0
    reset_at: Optional[datetime] = None


class QuotaExceededException(Exception):
    """Raised when a resource quota is exceeded"""
    pass


class ResourceQuotaManager:
    """Manages resource quotas and enforces limits"""

    def __init__(self):
        """Initialize resource quota manager"""
        self.quotas: Dict[str, Dict[ResourceType, ResourceQuota]] = {}

        # Default quotas per tier
        self.tier_quotas = {
            "free": {
                ResourceType.API_CALLS: ResourceQuota(
                    ResourceType.API_CALLS, 1000, 'day'
                ),
                ResourceType.STORAGE_GB: ResourceQuota(
                    ResourceType.STORAGE_GB, 1.0, 'month'
                ),
                ResourceType.PREDICTIONS: ResourceQuota(
                    ResourceType.PREDICTIONS, 100, 'hour'
                ),
            },
            "basic": {
                ResourceType.API_CALLS: ResourceQuota(
                    ResourceType.API_CALLS, 10000, 'day'
                ),
                ResourceType.STORAGE_GB: ResourceQuota(
                    ResourceType.STORAGE_GB, 10.0, 'month'
                ),
                ResourceType.PREDICTIONS: ResourceQuota(
                    ResourceType.PREDICTIONS, 1000, 'hour'
                ),
                ResourceType.COMPUTE_HOURS: ResourceQuota(
                    ResourceType.COMPUTE_HOURS, 10, 'month'
                ),
            },
            "premium": {
                ResourceType.API_CALLS: ResourceQuota(
                    ResourceType.API_CALLS, 100000, 'day'
                ),
                ResourceType.STORAGE_GB: ResourceQuota(
                    ResourceType.STORAGE_GB, 100.0, 'month'
                ),
                ResourceType.PREDICTIONS: ResourceQuota(
                    ResourceType.PREDICTIONS, 10000, 'hour'
                ),
                ResourceType.COMPUTE_HOURS: ResourceQuota(
                    ResourceType.COMPUTE_HOURS, 100, 'month'
                ),
                ResourceType.DATA_TRANSFER_GB: ResourceQuota(
                    ResourceType.DATA_TRANSFER_GB, 500, 'month'
                ),
            }
        }

    def set_user_tier(self, user_id: str, tier: str):
        """
        Set user tier and initialize quotas.

        Args:
            user_id: User identifier
            tier: Tier name ('free', 'basic', 'premium')
        """
        if tier not in self.tier_quotas:
            raise ValueError(f"Invalid tier: {tier}")

        # Deep copy quotas for the user
        self.quotas[user_id] = {}
        for resource_type, quota in self.tier_quotas[tier].items():
            self.quotas[user_id][resource_type] = ResourceQuota(
                resource_type=quota.resource_type,
                limit=quota.limit,
                period=quota.period,
                current_usage=0.0,
                reset_at=self._calculate_reset_time(quota.period)
            )

        logger.info(f"Set {user_id} to {tier} tier with {len(self.quotas[user_id])} quotas")

    def _calculate_reset_time(self, period: str) -> datetime:
        """Calculate when quota should reset"""
        now = datetime.utcnow()
        if period == 'hour':
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif period == 'day':
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'month':
            if now.month == 12:
                return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return now + timedelta(days=30)

    def check_and_consume(
        self,
        user_id: str,
        resource_type: ResourceType,
        amount: float = 1.0
    ) -> bool:
        """
        Check if user has quota and consume it.

        Args:
            user_id: User identifier
            resource_type: Type of resource
            amount: Amount to consume

        Returns:
            True if quota available and consumed

        Raises:
            QuotaExceededException: If quota exceeded
        """
        # Initialize user if not exists (default to free tier)
        if user_id not in self.quotas:
            self.set_user_tier(user_id, 'free')

        # Check if resource type exists for user
        if resource_type not in self.quotas[user_id]:
            logger.warning(f"No quota for {resource_type} for user {user_id}")
            return True  # Allow if no quota set

        quota = self.quotas[user_id][resource_type]

        # Check if quota needs reset
        if quota.reset_at and datetime.utcnow() >= quota.reset_at:
            quota.current_usage = 0.0
            quota.reset_at = self._calculate_reset_time(quota.period)
            logger.info(f"Reset {resource_type} quota for {user_id}")

        # Check if would exceed quota
        if quota.current_usage + amount > quota.limit:
            raise QuotaExceededException(
                f"Quota exceeded for {resource_type}: "
                f"{quota.current_usage + amount:.2f}/{quota.limit} "
                f"(resets at {quota.reset_at})"
            )

        # Consume quota
        quota.current_usage += amount
        logger.debug(
            f"Consumed {amount} {resource_type} for {user_id}: "
            f"{quota.current_usage:.2f}/{quota.limit}"
        )

        return True

    def get_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get current usage for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of resource usage
        """
        if user_id not in self.quotas:
            return {"error": "User not found"}

        usage = {}
        for resource_type, quota in self.quotas[user_id].items():
            usage[resource_type.value] = {
                "current": quota.current_usage,
                "limit": quota.limit,
                "percentage": (quota.current_usage / quota.limit * 100) if quota.limit > 0 else 0,
                "period": quota.period,
                "reset_at": quota.reset_at.isoformat() if quota.reset_at else None
            }

        return usage

    def set_custom_quota(
        self,
        user_id: str,
        resource_type: ResourceType,
        limit: float,
        period: str = 'month'
    ):
        """
        Set custom quota for a user.

        Args:
            user_id: User identifier
            resource_type: Type of resource
            limit: Quota limit
            period: Reset period
        """
        if user_id not in self.quotas:
            self.quotas[user_id] = {}

        self.quotas[user_id][resource_type] = ResourceQuota(
            resource_type=resource_type,
            limit=limit,
            period=period,
            current_usage=0.0,
            reset_at=self._calculate_reset_time(period)
        )

        logger.info(f"Set custom quota for {user_id}: {resource_type.value}={limit}/{period}")

    def get_all_users_usage(self) -> Dict[str, Dict]:
        """Get usage for all users"""
        return {
            user_id: self.get_usage(user_id)
            for user_id in self.quotas.keys()
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("RESOURCE QUOTAS & LIMITS DEMO")
    print("=" * 80)

    manager = ResourceQuotaManager()

    # Set up users
    print("\n" + "=" * 80)
    print("SETTING UP USERS")
    print("=" * 80)

    manager.set_user_tier("free_user", "free")
    manager.set_user_tier("basic_user", "basic")
    manager.set_user_tier("premium_user", "premium")

    print("\n✅ Created 3 users with different tiers")

    # Check usage
    print("\n" + "=" * 80)
    print("INITIAL USAGE (FREE USER)")
    print("=" * 80)

    usage = manager.get_usage("free_user")
    for resource, details in usage.items():
        print(f"\n{resource}:")
        print(f"  Usage: {details['current']}/{details['limit']} ({details['percentage']:.1f}%)")
        print(f"  Period: {details['period']}")

    # Simulate usage
    print("\n" + "=" * 80)
    print("SIMULATING API CALLS")
    print("=" * 80)

    for i in range(5):
        try:
            manager.check_and_consume("free_user", ResourceType.API_CALLS, 250)
            usage = manager.get_usage("free_user")
            api_usage = usage[ResourceType.API_CALLS.value]
            print(f"✅ Batch {i+1}: {api_usage['current']}/{api_usage['limit']} API calls")
        except QuotaExceededException as e:
            print(f"❌ Batch {i+1}: {e}")
            break

    # Test custom quota
    print("\n" + "=" * 80)
    print("SETTING CUSTOM QUOTA")
    print("=" * 80)

    manager.set_custom_quota(
        "free_user",
        ResourceType.PREDICTIONS,
        limit=500,
        period='day'
    )
    print("✅ Set custom prediction quota for free_user: 500/day")

    # All users usage
    print("\n" + "=" * 80)
    print("ALL USERS USAGE SUMMARY")
    print("=" * 80)

    all_usage = manager.get_all_users_usage()
    for user_id, usage in all_usage.items():
        print(f"\n{user_id}:")
        for resource, details in usage.items():
            if details['percentage'] > 0:  # Only show used resources
                print(f"  - {resource}: {details['percentage']:.1f}% used")

    print("\n" + "=" * 80)
    print("Resource Quotas Demo Complete!")
    print("=" * 80)

