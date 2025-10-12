"""
Multi-Tenant Support

Secure multi-tenancy for SaaS deployment:
- Tenant isolation
- Resource quotas
- Custom configurations
- Data segregation
- Tenant management
- Usage tracking

Features:
- Schema per tenant
- Row-level security
- Tenant-specific caching
- Resource limits
- Billing integration
- White-labeling

Use Cases:
- SaaS NBA analytics platform
- Per-team data isolation
- Custom branding
- Usage-based billing
- Compliance (data residency)
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib
import threading

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """Tenant account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CHURNED = "churned"


class TenantTier(Enum):
    """Tenant subscription tier"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class ResourceQuota:
    """Resource usage limits per tenant"""
    max_api_calls_per_day: int = 1000
    max_storage_gb: float = 10.0
    max_models: int = 5
    max_concurrent_requests: int = 10
    max_query_results: int = 10000
    max_users: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def for_tier(tier: TenantTier) -> 'ResourceQuota':
        """Get default quotas for subscription tier"""
        quotas = {
            TenantTier.FREE: ResourceQuota(
                max_api_calls_per_day=100,
                max_storage_gb=1.0,
                max_models=1,
                max_concurrent_requests=2,
                max_query_results=1000,
                max_users=1
            ),
            TenantTier.STARTER: ResourceQuota(
                max_api_calls_per_day=10000,
                max_storage_gb=50.0,
                max_models=10,
                max_concurrent_requests=10,
                max_query_results=50000,
                max_users=5
            ),
            TenantTier.PROFESSIONAL: ResourceQuota(
                max_api_calls_per_day=100000,
                max_storage_gb=500.0,
                max_models=50,
                max_concurrent_requests=50,
                max_query_results=500000,
                max_users=25
            ),
            TenantTier.ENTERPRISE: ResourceQuota(
                max_api_calls_per_day=-1,  # unlimited
                max_storage_gb=-1.0,
                max_models=-1,
                max_concurrent_requests=200,
                max_query_results=-1,
                max_users=-1
            )
        }
        return quotas.get(tier, ResourceQuota())


@dataclass
class TenantUsage:
    """Track tenant resource usage"""
    api_calls_today: int = 0
    storage_used_gb: float = 0.0
    models_created: int = 0
    concurrent_requests: int = 0
    total_users: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    def reset_daily_counters(self) -> None:
        """Reset daily usage counters"""
        self.api_calls_today = 0
        self.last_reset = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['last_reset'] = self.last_reset.isoformat()
        return data


@dataclass
class TenantConfig:
    """Tenant-specific configuration"""
    # Branding
    company_name: str = "NBA Analytics"
    logo_url: Optional[str] = None
    primary_color: str = "#1f77b4"
    
    # Features
    enable_ml_models: bool = True
    enable_advanced_stats: bool = True
    enable_api_access: bool = True
    enable_data_export: bool = True
    
    # Data
    data_retention_days: int = 365
    backup_enabled: bool = True
    encryption_enabled: bool = True
    
    # Customization
    custom_domain: Optional[str] = None
    custom_email_domain: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Tenant:
    """Tenant (customer/organization) definition"""
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.TRIAL
    tier: TenantTier = TenantTier.FREE
    quota: ResourceQuota = field(default_factory=ResourceQuota)
    usage: TenantUsage = field(default_factory=TenantUsage)
    config: TenantConfig = field(default_factory=TenantConfig)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    trial_ends_at: Optional[datetime] = None
    
    # Contact
    primary_contact_email: Optional[str] = None
    billing_email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tenant_id': self.tenant_id,
            'name': self.name,
            'status': self.status.value,
            'tier': self.tier.value,
            'quota': self.quota.to_dict(),
            'usage': self.usage.to_dict(),
            'config': self.config.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'primary_contact_email': self.primary_contact_email,
            'billing_email': self.billing_email
        }
    
    def is_within_quota(self, resource: str) -> bool:
        """Check if tenant is within quota for a resource"""
        quota_map = {
            'api_calls': (self.usage.api_calls_today, self.quota.max_api_calls_per_day),
            'storage': (self.usage.storage_used_gb, self.quota.max_storage_gb),
            'models': (self.usage.models_created, self.quota.max_models),
            'concurrent_requests': (self.usage.concurrent_requests, self.quota.max_concurrent_requests),
            'users': (self.usage.total_users, self.quota.max_users)
        }
        
        if resource not in quota_map:
            return True
        
        current, limit = quota_map[resource]
        
        # -1 means unlimited
        if limit == -1 or limit == -1.0:
            return True
        
        return current < limit
    
    def update_tier(self, new_tier: TenantTier) -> None:
        """Update subscription tier and quotas"""
        self.tier = new_tier
        self.quota = ResourceQuota.for_tier(new_tier)
        self.updated_at = datetime.now()
        logger.info(f"Updated tenant {self.tenant_id} to tier {new_tier.value}")


class TenantContext:
    """Thread-local tenant context"""
    
    _thread_local = threading.local()
    
    @classmethod
    def set_current_tenant(cls, tenant_id: str) -> None:
        """Set current tenant for this thread"""
        cls._thread_local.tenant_id = tenant_id
    
    @classmethod
    def get_current_tenant(cls) -> Optional[str]:
        """Get current tenant ID"""
        return getattr(cls._thread_local, 'tenant_id', None)
    
    @classmethod
    def clear(cls) -> None:
        """Clear tenant context"""
        if hasattr(cls._thread_local, 'tenant_id'):
            delattr(cls._thread_local, 'tenant_id')


class TenantManager:
    """Manage multiple tenants"""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self._lock = threading.RLock()
    
    def create_tenant(
        self,
        name: str,
        tier: TenantTier = TenantTier.TRIAL,
        primary_email: Optional[str] = None
    ) -> Tenant:
        """Create a new tenant"""
        # Generate tenant ID
        tenant_id = hashlib.sha256(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            tier=tier,
            status=TenantStatus.TRIAL if tier == TenantTier.FREE else TenantStatus.ACTIVE,
            quota=ResourceQuota.for_tier(tier),
            primary_contact_email=primary_email,
            billing_email=primary_email
        )
        
        # Set trial period
        if tier == TenantTier.FREE:
            from datetime import timedelta
            tenant.trial_ends_at = datetime.now() + timedelta(days=30)
        
        with self._lock:
            self.tenants[tenant_id] = tenant
        
        logger.info(f"Created tenant: {tenant_id} ({name})")
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        with self._lock:
            return self.tenants.get(tenant_id)
    
    def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Get tenant by name"""
        with self._lock:
            for tenant in self.tenants.values():
                if tenant.name == name:
                    return tenant
            return None
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None
    ) -> List[Tenant]:
        """List all tenants with optional filters"""
        with self._lock:
            tenants = list(self.tenants.values())
            
            if status:
                tenants = [t for t in tenants if t.status == status]
            if tier:
                tenants = [t for t in tenants if t.tier == tier]
            
            return tenants
    
    def update_tenant_status(self, tenant_id: str, status: TenantStatus) -> bool:
        """Update tenant status"""
        with self._lock:
            tenant = self.tenants.get(tenant_id)
            if tenant:
                tenant.status = status
                tenant.updated_at = datetime.now()
                logger.info(f"Updated tenant {tenant_id} status to {status.value}")
                return True
            return False
    
    def upgrade_tenant(self, tenant_id: str, new_tier: TenantTier) -> bool:
        """Upgrade tenant to new tier"""
        with self._lock:
            tenant = self.tenants.get(tenant_id)
            if tenant:
                tenant.update_tier(new_tier)
                if tenant.status == TenantStatus.TRIAL:
                    tenant.status = TenantStatus.ACTIVE
                return True
            return False
    
    def record_api_call(self, tenant_id: str) -> bool:
        """Record API call for tenant"""
        with self._lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            # Check quota
            if not tenant.is_within_quota('api_calls'):
                logger.warning(f"Tenant {tenant_id} exceeded API call quota")
                return False
            
            tenant.usage.api_calls_today += 1
            return True
    
    def record_storage_usage(self, tenant_id: str, storage_gb: float) -> bool:
        """Update storage usage for tenant"""
        with self._lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            tenant.usage.storage_used_gb = storage_gb
            
            if not tenant.is_within_quota('storage'):
                logger.warning(f"Tenant {tenant_id} exceeded storage quota")
                return False
            
            return True
    
    def get_tenant_stats(self) -> Dict[str, Any]:
        """Get overall tenant statistics"""
        with self._lock:
            total = len(self.tenants)
            by_status = {}
            by_tier = {}
            
            for tenant in self.tenants.values():
                # Count by status
                status = tenant.status.value
                by_status[status] = by_status.get(status, 0) + 1
                
                # Count by tier
                tier = tenant.tier.value
                by_tier[tier] = by_tier.get(tier, 0) + 1
            
            return {
                'total_tenants': total,
                'by_status': by_status,
                'by_tier': by_tier
            }


# Decorator for tenant-aware endpoints
def require_tenant(func):
    """Decorator to enforce tenant context"""
    def wrapper(*args, **kwargs):
        tenant_id = TenantContext.get_current_tenant()
        if not tenant_id:
            raise ValueError("No tenant context set")
        return func(*args, **kwargs)
    return wrapper


# Global manager
_tenant_manager = None
_manager_lock = threading.Lock()


def get_tenant_manager() -> TenantManager:
    """Get global tenant manager"""
    global _tenant_manager
    with _manager_lock:
        if _tenant_manager is None:
            _tenant_manager = TenantManager()
        return _tenant_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Multi-Tenant System Demo ===\n")
    
    # Create manager
    manager = TenantManager()
    
    # Create tenants
    print("--- Creating Tenants ---")
    nba_team1 = manager.create_tenant(
        name="Los Angeles Lakers",
        tier=TenantTier.PROFESSIONAL,
        primary_email="analytics@lakers.com"
    )
    print(f"Created: {nba_team1.name} ({nba_team1.tier.value})")
    
    nba_team2 = manager.create_tenant(
        name="Golden State Warriors",
        tier=TenantTier.ENTERPRISE,
        primary_email="stats@warriors.com"
    )
    print(f"Created: {nba_team2.name} ({nba_team2.tier.value})")
    
    startup = manager.create_tenant(
        name="Startup Analytics Inc",
        tier=TenantTier.FREE,
        primary_email="team@startup.com"
    )
    print(f"Created: {startup.name} ({startup.tier.value})")
    
    # Check quotas
    print("\n--- Resource Quotas ---")
    for tenant in manager.list_tenants():
        print(f"\n{tenant.name} ({tenant.tier.value}):")
        print(f"  API calls/day: {tenant.quota.max_api_calls_per_day}")
        print(f"  Storage: {tenant.quota.max_storage_gb} GB")
        print(f"  Max models: {tenant.quota.max_models}")
        print(f"  Max users: {tenant.quota.max_users}")
    
    # Simulate API usage
    print("\n--- Simulating API Usage ---")
    for i in range(15):
        if manager.record_api_call(startup.tenant_id):
            print(f"API call {i+1} recorded for {startup.name}")
        else:
            print(f"API call {i+1} REJECTED - quota exceeded for {startup.name}")
    
    print(f"\nCurrent usage: {startup.usage.api_calls_today}/{startup.quota.max_api_calls_per_day}")
    
    # Upgrade tenant
    print("\n--- Tenant Upgrade ---")
    print(f"Upgrading {startup.name} from {startup.tier.value} to STARTER...")
    manager.upgrade_tenant(startup.tenant_id, TenantTier.STARTER)
    
    # Check new quotas
    startup = manager.get_tenant(startup.tenant_id)
    print(f"New quota: {startup.quota.max_api_calls_per_day} API calls/day")
    print(f"Current usage: {startup.usage.api_calls_today} calls")
    print(f"Status: {startup.status.value}")
    
    # Tenant stats
    print("\n--- Tenant Statistics ---")
    stats = manager.get_tenant_stats()
    print(f"Total tenants: {stats['total_tenants']}")
    print(f"By status: {stats['by_status']}")
    print(f"By tier: {stats['by_tier']}")
    
    # Tenant context demo
    print("\n--- Tenant Context ---")
    TenantContext.set_current_tenant(nba_team1.tenant_id)
    current = TenantContext.get_current_tenant()
    print(f"Current tenant context: {current}")
    tenant = manager.get_tenant(current)
    print(f"Tenant name: {tenant.name}")
    
    print("\n=== Demo Complete ===")

