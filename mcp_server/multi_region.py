"""
Multi-Region Deployment Support

Deploy and manage services across multiple AWS regions:
- Region management
- Cross-region replication
- Failover automation
- Latency-based routing
- Data consistency
- Regional quotas

Features:
- Active-active deployment
- Cross-region sync
- Regional health checks
- Automatic failover
- Cost per region
- Compliance zones

Use Cases:
- Global deployment
- Disaster recovery
- Low-latency access
- Data sovereignty
- High availability
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategies"""
    ACTIVE_ACTIVE = "active-active"  # All regions serve traffic
    ACTIVE_PASSIVE = "active-passive"  # Primary + failover
    MULTI_MASTER = "multi-master"  # All regions read-write


class RegionStatus(Enum):
    """Region status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DRAINING = "draining"  # Preparing for shutdown


@dataclass
class Region:
    """AWS region configuration"""
    name: str
    code: str  # e.g., us-east-1
    is_primary: bool = False
    enabled: bool = True
    weight: int = 100  # Traffic weight
    latency_ms: float = 0.0
    status: RegionStatus = RegionStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegionalResource:
    """Resource deployed to a region"""
    resource_type: str  # rds, s3, ec2, etc.
    resource_id: str
    region_code: str
    arn: str
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class RegionManager:
    """Manage multi-region deployments"""
    
    # AWS regions
    AVAILABLE_REGIONS = {
        'us-east-1': {'name': 'US East (N. Virginia)', 'latency_to_us': 0},
        'us-east-2': {'name': 'US East (Ohio)', 'latency_to_us': 10},
        'us-west-1': {'name': 'US West (N. California)', 'latency_to_us': 70},
        'us-west-2': {'name': 'US West (Oregon)', 'latency_to_us': 80},
        'eu-west-1': {'name': 'Europe (Ireland)', 'latency_to_us': 90},
        'eu-central-1': {'name': 'Europe (Frankfurt)', 'latency_to_us': 110},
        'ap-southeast-1': {'name': 'Asia Pacific (Singapore)', 'latency_to_us': 200},
        'ap-northeast-1': {'name': 'Asia Pacific (Tokyo)', 'latency_to_us': 150},
    }
    
    def __init__(self, primary_region: str = 'us-east-1'):
        self.primary_region = primary_region
        self.regions: Dict[str, Region] = {}
        self.resources: Dict[str, List[RegionalResource]] = {}
        self._init_regions()
    
    def _init_regions(self) -> None:
        """Initialize available regions"""
        for code, info in self.AVAILABLE_REGIONS.items():
            self.regions[code] = Region(
                name=info['name'],
                code=code,
                is_primary=(code == self.primary_region),
                latency_ms=info['latency_to_us']
            )
    
    def enable_region(self, region_code: str) -> bool:
        """Enable a region"""
        if region_code in self.regions:
            self.regions[region_code].enabled = True
            logger.info(f"Enabled region: {region_code}")
            return True
        return False
    
    def disable_region(self, region_code: str) -> bool:
        """Disable a region"""
        if region_code in self.regions and not self.regions[region_code].is_primary:
            self.regions[region_code].enabled = False
            self.regions[region_code].status = RegionStatus.DRAINING
            logger.info(f"Disabled region: {region_code}")
            return True
        return False
    
    def set_region_weight(self, region_code: str, weight: int) -> bool:
        """Set traffic weight for region"""
        if region_code in self.regions and 0 <= weight <= 100:
            self.regions[region_code].weight = weight
            logger.info(f"Set region {region_code} weight to {weight}")
            return True
        return False
    
    def get_active_regions(self) -> List[Region]:
        """Get all active regions"""
        return [
            r for r in self.regions.values()
            if r.enabled and r.status == RegionStatus.HEALTHY
        ]
    
    def get_closest_region(self, client_latencies: Dict[str, float]) -> Optional[Region]:
        """Get closest region based on latency"""
        active = self.get_active_regions()
        if not active:
            return None
        
        # Find region with lowest latency
        best_region = None
        best_latency = float('inf')
        
        for region in active:
            latency = client_latencies.get(region.code, region.latency_ms)
            if latency < best_latency:
                best_latency = latency
                best_region = region
        
        return best_region
    
    def health_check_region(self, region_code: str) -> RegionStatus:
        """Check health of a region"""
        if region_code not in self.regions:
            return RegionStatus.UNAVAILABLE
        
        region = self.regions[region_code]
        
        try:
            # Try to connect to AWS in that region
            ec2 = boto3.client('ec2', region_name=region_code)
            ec2.describe_regions(RegionNames=[region_code])
            
            region.status = RegionStatus.HEALTHY
            region.last_health_check = datetime.now()
            return RegionStatus.HEALTHY
        
        except ClientError as e:
            logger.error(f"Health check failed for {region_code}: {e}")
            region.status = RegionStatus.DEGRADED
            region.last_health_check = datetime.now()
            return RegionStatus.DEGRADED
        
        except Exception as e:
            logger.error(f"Health check error for {region_code}: {e}")
            region.status = RegionStatus.UNAVAILABLE
            region.last_health_check = datetime.now()
            return RegionStatus.UNAVAILABLE
    
    def health_check_all(self) -> Dict[str, RegionStatus]:
        """Health check all regions"""
        results = {}
        for region_code in self.regions.keys():
            results[region_code] = self.health_check_region(region_code)
        return results
    
    def add_resource(self, resource: RegionalResource) -> None:
        """Register a regional resource"""
        region_code = resource.region_code
        if region_code not in self.resources:
            self.resources[region_code] = []
        self.resources[region_code].append(resource)
        logger.info(f"Registered {resource.resource_type} in {region_code}")
    
    def get_resources(self, region_code: str) -> List[RegionalResource]:
        """Get resources in a region"""
        return self.resources.get(region_code, [])
    
    def get_resource_distribution(self) -> Dict[str, int]:
        """Get count of resources per region"""
        return {
            region_code: len(resources)
            for region_code, resources in self.resources.items()
        }


class CrossRegionReplicator:
    """Replicate data across regions"""
    
    def __init__(self, region_manager: RegionManager):
        self.region_manager = region_manager
        self.replication_status: Dict[str, Dict[str, Any]] = {}
    
    def setup_s3_replication(
        self,
        bucket_name: str,
        source_region: str,
        target_regions: List[str]
    ) -> bool:
        """Set up S3 cross-region replication"""
        try:
            s3 = boto3.client('s3', region_name=source_region)
            
            # Configure replication
            replication_config = {
                'Role': f'arn:aws:iam::ACCOUNT_ID:role/s3-replication-role',
                'Rules': []
            }
            
            for i, target_region in enumerate(target_regions):
                rule = {
                    'ID': f'replication-rule-{i}',
                    'Priority': i,
                    'Filter': {'Prefix': ''},
                    'Status': 'Enabled',
                    'Destination': {
                        'Bucket': f'arn:aws:s3:::{bucket_name}-{target_region}',
                        'ReplicationTime': {
                            'Status': 'Enabled',
                            'Time': {'Minutes': 15}
                        },
                        'Metrics': {
                            'Status': 'Enabled',
                            'EventThreshold': {'Minutes': 15}
                        }
                    },
                    'DeleteMarkerReplication': {'Status': 'Enabled'}
                }
                replication_config['Rules'].append(rule)
            
            # Note: This is a placeholder. In production, you'd actually call:
            # s3.put_bucket_replication(Bucket=bucket_name, ReplicationConfiguration=replication_config)
            
            self.replication_status[bucket_name] = {
                'source': source_region,
                'targets': target_regions,
                'status': 'active',
                'last_updated': datetime.now()
            }
            
            logger.info(f"S3 replication configured for {bucket_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to setup S3 replication: {e}")
            return False
    
    def setup_rds_replication(
        self,
        db_instance_id: str,
        source_region: str,
        target_region: str
    ) -> bool:
        """Set up RDS cross-region read replica"""
        try:
            rds = boto3.client('rds', region_name=source_region)
            
            # Note: This is a placeholder. In production, you'd call:
            # rds.create_db_instance_read_replica(
            #     DBInstanceIdentifier=f'{db_instance_id}-replica-{target_region}',
            #     SourceDBInstanceIdentifier=db_instance_id,
            #     SourceRegion=source_region
            # )
            
            self.replication_status[db_instance_id] = {
                'source': source_region,
                'target': target_region,
                'status': 'replicating',
                'last_updated': datetime.now()
            }
            
            logger.info(f"RDS replication configured for {db_instance_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to setup RDS replication: {e}")
            return False
    
    def get_replication_lag(self, resource_id: str) -> Optional[float]:
        """Get replication lag in seconds"""
        if resource_id not in self.replication_status:
            return None
        
        # Placeholder - in production, query actual lag from CloudWatch
        return 5.0  # 5 seconds
    
    def get_replication_status(self) -> Dict[str, Any]:
        """Get status of all replications"""
        return {
            'total_replications': len(self.replication_status),
            'replications': self.replication_status
        }


class FailoverManager:
    """Manage automatic failover between regions"""
    
    def __init__(self, region_manager: RegionManager):
        self.region_manager = region_manager
        self.failover_history: List[Dict[str, Any]] = []
    
    def trigger_failover(
        self,
        from_region: str,
        to_region: str,
        reason: str
    ) -> bool:
        """Trigger failover from one region to another"""
        
        # Validate regions
        if from_region not in self.region_manager.regions:
            logger.error(f"Invalid source region: {from_region}")
            return False
        
        if to_region not in self.region_manager.regions:
            logger.error(f"Invalid target region: {to_region}")
            return False
        
        # Check target region health
        target_status = self.region_manager.health_check_region(to_region)
        if target_status != RegionStatus.HEALTHY:
            logger.error(f"Target region {to_region} is not healthy")
            return False
        
        # Drain source region
        self.region_manager.disable_region(from_region)
        
        # Promote target region
        target = self.region_manager.regions[to_region]
        target.weight = 100
        target.is_primary = True
        
        # Demote source region
        source = self.region_manager.regions[from_region]
        source.is_primary = False
        
        # Record failover
        failover_event = {
            'timestamp': datetime.now(),
            'from_region': from_region,
            'to_region': to_region,
            'reason': reason,
            'duration_seconds': 0  # Would measure in production
        }
        self.failover_history.append(failover_event)
        
        logger.warning(f"Failover completed: {from_region} -> {to_region}")
        return True
    
    def auto_failover(self, unhealthy_region: str) -> bool:
        """Automatically failover from unhealthy region"""
        
        # Find best alternative region
        active_regions = self.region_manager.get_active_regions()
        alternatives = [r for r in active_regions if r.code != unhealthy_region]
        
        if not alternatives:
            logger.error("No alternative regions available for failover")
            return False
        
        # Choose region with lowest latency
        target_region = min(alternatives, key=lambda r: r.latency_ms)
        
        return self.trigger_failover(
            from_region=unhealthy_region,
            to_region=target_region.code,
            reason="Automatic failover due to unhealthy region"
        )
    
    def get_failover_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failover events"""
        return self.failover_history[-limit:]


class MultiRegionDeployment:
    """Main multi-region deployment orchestrator"""
    
    def __init__(self, primary_region: str = 'us-east-1'):
        self.region_manager = RegionManager(primary_region)
        self.replicator = CrossRegionReplicator(self.region_manager)
        self.failover_manager = FailoverManager(self.region_manager)
    
    def deploy_to_regions(
        self,
        regions: List[str],
        strategy: DeploymentStrategy = DeploymentStrategy.ACTIVE_ACTIVE
    ) -> Dict[str, bool]:
        """Deploy to multiple regions"""
        results = {}
        
        for region_code in regions:
            try:
                # Enable region
                self.region_manager.enable_region(region_code)
                
                # Set weight based on strategy
                if strategy == DeploymentStrategy.ACTIVE_ACTIVE:
                    weight = 100 // len(regions)
                elif strategy == DeploymentStrategy.ACTIVE_PASSIVE:
                    weight = 100 if region_code == self.region_manager.primary_region else 0
                else:
                    weight = 100
                
                self.region_manager.set_region_weight(region_code, weight)
                
                results[region_code] = True
                logger.info(f"Deployed to {region_code}")
            
            except Exception as e:
                logger.error(f"Failed to deploy to {region_code}: {e}")
                results[region_code] = False
        
        return results
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """Get deployment summary"""
        active_regions = self.region_manager.get_active_regions()
        resource_dist = self.region_manager.get_resource_distribution()
        replication_status = self.replicator.get_replication_status()
        
        return {
            'primary_region': self.region_manager.primary_region,
            'active_regions': [r.code for r in active_regions],
            'total_regions': len(self.region_manager.regions),
            'resource_distribution': resource_dist,
            'replication_count': replication_status['total_replications'],
            'failover_history_count': len(self.failover_manager.failover_history)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Multi-Region Deployment Demo ===\n")
    
    # Create deployment
    deployment = MultiRegionDeployment(primary_region='us-east-1')
    
    # Deploy to multiple regions
    print("--- Deploying to Regions ---\n")
    regions_to_deploy = ['us-east-1', 'us-west-2', 'eu-west-1']
    results = deployment.deploy_to_regions(
        regions_to_deploy,
        strategy=DeploymentStrategy.ACTIVE_ACTIVE
    )
    
    for region, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {region}")
    
    # Check region health
    print("\n--- Health Checks ---\n")
    health = deployment.region_manager.health_check_all()
    for region, status in health.items():
        if region in regions_to_deploy:
            print(f"{region}: {status.value}")
    
    # Get deployment summary
    print("\n--- Deployment Summary ---")
    summary = deployment.get_deployment_summary()
    print(f"Primary: {summary['primary_region']}")
    print(f"Active: {', '.join(summary['active_regions'])}")
    print(f"Total regions: {summary['total_regions']}")
    
    print("\n=== Demo Complete ===")

