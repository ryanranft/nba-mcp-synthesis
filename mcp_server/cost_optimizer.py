"""
Cost Optimization Tools

Optimize cloud costs and resource usage:
- Cost tracking
- Resource right-sizing
- Waste detection
- Optimization recommendations
- Budget forecasting
- Cost allocation

Features:
- AWS cost analysis
- Unused resource detection
- Reserved instance recommendations
- Storage optimization
- Compute right-sizing
- Cost alerts

Use Cases:
- Monthly cost reviews
- Budget planning
- Resource cleanup
- Cost allocation by team
- Optimization opportunities
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """AWS resource types"""
    EC2 = "ec2"
    RDS = "rds"
    S3 = "s3"
    LAMBDA = "lambda"
    GLUE = "glue"
    EBS = "ebs"


class OptimizationPriority(Enum):
    """Optimization priority"""
    CRITICAL = "critical"  # High cost, easy fix
    HIGH = "high"         # Significant savings
    MEDIUM = "medium"     # Moderate savings
    LOW = "low"          # Small savings


@dataclass
class CostItem:
    """Individual cost item"""
    service: str
    resource_id: str
    resource_type: ResourceType
    monthly_cost: float
    region: str
    tags: Dict[str, str] = field(default_factory=dict)
    last_used: Optional[datetime] = None


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation"""
    title: str
    description: str
    priority: OptimizationPriority
    estimated_monthly_savings: float
    resource_type: ResourceType
    affected_resources: List[str]
    action_required: str
    risk_level: str  # low, medium, high
    implementation_effort: str  # easy, moderate, complex


class CostAnalyzer:
    """Analyze AWS costs"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        try:
            self.ce_client = boto3.client('ce', region_name=region)
            self.ec2_client = boto3.client('ec2', region_name=region)
            self.rds_client = boto3.client('rds', region_name=region)
            self.s3_client = boto3.client('s3')
        except Exception as e:
            logger.warning(f"Could not initialize AWS clients: {e}")
            self.ce_client = None
            self.ec2_client = None
            self.rds_client = None
            self.s3_client = None
    
    def get_monthly_costs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get monthly costs by service"""
        if not self.ce_client:
            logger.warning("Cost Explorer client not available")
            return {}
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            costs = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    costs[service] = costs.get(service, 0) + amount
            
            return costs
        except ClientError as e:
            logger.error(f"Error fetching costs: {e}")
            return {}
    
    def get_cost_forecast(self, days: int = 30) -> float:
        """Forecast costs for next N days"""
        if not self.ce_client:
            return 0.0
        
        try:
            end_date = datetime.now() + timedelta(days=days)
            
            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': datetime.now().strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
            
            return float(response['Total']['Amount'])
        except ClientError as e:
            logger.error(f"Error forecasting costs: {e}")
            return 0.0


class ResourceOptimizer:
    """Find optimization opportunities"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        try:
            self.ec2_client = boto3.client('ec2', region_name=region)
            self.rds_client = boto3.client('rds', region_name=region)
            self.s3_client = boto3.client('s3')
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        except Exception as e:
            logger.warning(f"Could not initialize AWS clients: {e}")
            self.ec2_client = None
            self.rds_client = None
            self.s3_client = None
            self.cloudwatch = None
    
    def find_idle_ec2_instances(self) -> List[OptimizationRecommendation]:
        """Find idle EC2 instances"""
        if not self.ec2_client:
            return []
        
        recommendations = []
        
        try:
            instances = self.ec2_client.describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'running':
                        continue
                    
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    # Check CPU utilization
                    avg_cpu = self._get_avg_cpu_utilization(instance_id, days=7)
                    
                    if avg_cpu < 5.0:  # Less than 5% CPU
                        # Estimate cost (simplified)
                        monthly_cost = self._estimate_ec2_cost(instance_type)
                        
                        recommendations.append(OptimizationRecommendation(
                            title=f"Idle EC2 Instance: {instance_id}",
                            description=f"Instance {instance_id} ({instance_type}) has been idle (CPU < 5%) for 7 days",
                            priority=OptimizationPriority.HIGH,
                            estimated_monthly_savings=monthly_cost,
                            resource_type=ResourceType.EC2,
                            affected_resources=[instance_id],
                            action_required="Stop or terminate instance if no longer needed",
                            risk_level="low",
                            implementation_effort="easy"
                        ))
        except ClientError as e:
            logger.error(f"Error finding idle instances: {e}")
        
        return recommendations
    
    def find_unattached_volumes(self) -> List[OptimizationRecommendation]:
        """Find unattached EBS volumes"""
        if not self.ec2_client:
            return []
        
        recommendations = []
        
        try:
            volumes = self.ec2_client.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            
            for volume in volumes['Volumes']:
                volume_id = volume['VolumeId']
                size_gb = volume['Size']
                volume_type = volume['VolumeType']
                
                # Estimate cost
                monthly_cost = self._estimate_ebs_cost(size_gb, volume_type)
                
                recommendations.append(OptimizationRecommendation(
                    title=f"Unattached EBS Volume: {volume_id}",
                    description=f"Volume {volume_id} ({size_gb}GB {volume_type}) is not attached to any instance",
                    priority=OptimizationPriority.MEDIUM,
                    estimated_monthly_savings=monthly_cost,
                    resource_type=ResourceType.EBS,
                    affected_resources=[volume_id],
                    action_required="Create snapshot and delete volume if not needed",
                    risk_level="medium",
                    implementation_effort="easy"
                ))
        except ClientError as e:
            logger.error(f"Error finding unattached volumes: {e}")
        
        return recommendations
    
    def find_old_snapshots(self, days_old: int = 90) -> List[OptimizationRecommendation]:
        """Find old EBS snapshots"""
        if not self.ec2_client:
            return []
        
        recommendations = []
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            snapshots = self.ec2_client.describe_snapshots(OwnerIds=['self'])
            
            old_snapshots = []
            total_size = 0
            
            for snapshot in snapshots['Snapshots']:
                start_time = snapshot['StartTime'].replace(tzinfo=None)
                if start_time < cutoff_date:
                    old_snapshots.append(snapshot['SnapshotId'])
                    total_size += snapshot['VolumeSize']
            
            if old_snapshots:
                monthly_cost = total_size * 0.05  # $0.05 per GB-month
                
                recommendations.append(OptimizationRecommendation(
                    title=f"Old Snapshots ({len(old_snapshots)} snapshots)",
                    description=f"Found {len(old_snapshots)} snapshots older than {days_old} days ({total_size}GB total)",
                    priority=OptimizationPriority.MEDIUM,
                    estimated_monthly_savings=monthly_cost,
                    resource_type=ResourceType.EBS,
                    affected_resources=old_snapshots[:10],  # Show first 10
                    action_required="Review and delete snapshots that are no longer needed",
                    risk_level="medium",
                    implementation_effort="moderate"
                ))
        except ClientError as e:
            logger.error(f"Error finding old snapshots: {e}")
        
        return recommendations
    
    def find_oversized_rds(self) -> List[OptimizationRecommendation]:
        """Find over-provisioned RDS instances"""
        if not self.rds_client:
            return []
        
        recommendations = []
        
        try:
            instances = self.rds_client.describe_db_instances()
            
            for instance in instances['DBInstances']:
                db_id = instance['DBInstanceIdentifier']
                instance_class = instance['DBInstanceClass']
                
                # Check CPU and connections
                avg_cpu = self._get_rds_avg_cpu(db_id, days=7)
                
                if avg_cpu < 20.0:  # Less than 20% CPU
                    # Suggest downsize
                    smaller_class = self._suggest_smaller_rds_class(instance_class)
                    if smaller_class:
                        current_cost = self._estimate_rds_cost(instance_class)
                        new_cost = self._estimate_rds_cost(smaller_class)
                        savings = current_cost - new_cost
                        
                        recommendations.append(OptimizationRecommendation(
                            title=f"Over-provisioned RDS: {db_id}",
                            description=f"RDS instance {db_id} ({instance_class}) has low utilization (CPU < 20%)",
                            priority=OptimizationPriority.HIGH,
                            estimated_monthly_savings=savings,
                            resource_type=ResourceType.RDS,
                            affected_resources=[db_id],
                            action_required=f"Consider downsizing to {smaller_class}",
                            risk_level="medium",
                            implementation_effort="moderate"
                        ))
        except ClientError as e:
            logger.error(f"Error analyzing RDS instances: {e}")
        
        return recommendations
    
    def find_unused_s3_buckets(self, days_inactive: int = 90) -> List[OptimizationRecommendation]:
        """Find unused S3 buckets"""
        if not self.s3_client:
            return []
        
        recommendations = []
        cutoff_date = datetime.now() - timedelta(days=days_inactive)
        
        try:
            buckets = self.s3_client.list_buckets()
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                # Check last access time (simplified)
                # In production, use S3 access logs or CloudTrail
                
                try:
                    # Get bucket size
                    size_bytes = self._get_bucket_size(bucket_name)
                    size_gb = size_bytes / (1024**3)
                    
                    if size_gb < 1 and bucket['CreationDate'].replace(tzinfo=None) < cutoff_date:
                        monthly_cost = size_gb * 0.023  # S3 Standard pricing
                        
                        recommendations.append(OptimizationRecommendation(
                            title=f"Small/Unused S3 Bucket: {bucket_name}",
                            description=f"Bucket {bucket_name} is small ({size_gb:.2f}GB) and may be unused",
                            priority=OptimizationPriority.LOW,
                            estimated_monthly_savings=monthly_cost,
                            resource_type=ResourceType.S3,
                            affected_resources=[bucket_name],
                            action_required="Review and delete if no longer needed",
                            risk_level="medium",
                            implementation_effort="easy"
                        ))
                except:
                    pass
        except ClientError as e:
            logger.error(f"Error analyzing S3 buckets: {e}")
        
        return recommendations
    
    def _get_avg_cpu_utilization(self, instance_id: str, days: int = 7) -> float:
        """Get average CPU utilization for EC2 instance"""
        if not self.cloudwatch:
            return 0.0
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
            return 0.0
        except:
            return 0.0
    
    def _get_rds_avg_cpu(self, db_id: str, days: int = 7) -> float:
        """Get average CPU for RDS instance"""
        if not self.cloudwatch:
            return 0.0
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
            return 0.0
        except:
            return 0.0
    
    def _estimate_ec2_cost(self, instance_type: str) -> float:
        """Estimate monthly EC2 cost (simplified)"""
        # Simplified pricing (actual prices vary by region)
        pricing = {
            't2.micro': 8.47,
            't2.small': 16.93,
            't2.medium': 33.87,
            't3.medium': 30.37,
            't3.large': 60.74,
            'c6i.4xlarge': 491.52,
            'c6i.8xlarge': 983.04
        }
        return pricing.get(instance_type, 50.0)  # Default estimate
    
    def _estimate_ebs_cost(self, size_gb: int, volume_type: str) -> float:
        """Estimate monthly EBS cost"""
        pricing_per_gb = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025
        }
        price = pricing_per_gb.get(volume_type, 0.10)
        return size_gb * price
    
    def _estimate_rds_cost(self, instance_class: str) -> float:
        """Estimate monthly RDS cost"""
        pricing = {
            'db.t3.micro': 13.14,
            'db.t3.small': 26.28,
            'db.t3.medium': 52.56,
            'db.t3.large': 105.12,
            'db.r5.large': 173.01,
            'db.r5.xlarge': 346.02
        }
        return pricing.get(instance_class, 100.0)
    
    def _suggest_smaller_rds_class(self, current_class: str) -> Optional[str]:
        """Suggest smaller RDS instance class"""
        size_order = [
            'db.t3.micro', 'db.t3.small', 'db.t3.medium',
            'db.t3.large', 'db.r5.large', 'db.r5.xlarge'
        ]
        
        try:
            current_idx = size_order.index(current_class)
            if current_idx > 0:
                return size_order[current_idx - 1]
        except ValueError:
            pass
        
        return None
    
    def _get_bucket_size(self, bucket_name: str) -> int:
        """Get S3 bucket size in bytes (simplified)"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            total_size = sum(obj['Size'] for obj in response.get('Contents', []))
            return total_size
        except:
            return 0


class CostOptimizer:
    """Main cost optimizer"""
    
    def __init__(self, region: str = "us-east-1"):
        self.analyzer = CostAnalyzer(region)
        self.optimizer = ResourceOptimizer(region)
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        recommendations = []
        
        # Find optimization opportunities
        recommendations.extend(self.optimizer.find_idle_ec2_instances())
        recommendations.extend(self.optimizer.find_unattached_volumes())
        recommendations.extend(self.optimizer.find_old_snapshots())
        recommendations.extend(self.optimizer.find_oversized_rds())
        recommendations.extend(self.optimizer.find_unused_s3_buckets())
        
        # Calculate totals
        total_savings = sum(r.estimated_monthly_savings for r in recommendations)
        
        # Group by priority
        by_priority = {}
        for rec in recommendations:
            priority = rec.priority.value
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(rec)
        
        return {
            'total_recommendations': len(recommendations),
            'total_monthly_savings': round(total_savings, 2),
            'annual_savings': round(total_savings * 12, 2),
            'by_priority': {
                priority: {
                    'count': len(recs),
                    'savings': round(sum(r.estimated_monthly_savings for r in recs), 2)
                }
                for priority, recs in by_priority.items()
            },
            'recommendations': [
                {
                    'title': r.title,
                    'priority': r.priority.value,
                    'savings': round(r.estimated_monthly_savings, 2),
                    'action': r.action_required,
                    'effort': r.implementation_effort
                }
                for r in sorted(recommendations, key=lambda x: x.estimated_monthly_savings, reverse=True)
            ]
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Cost Optimization Demo ===\n")
    
    # Create optimizer
    optimizer = CostOptimizer()
    
    # Generate report
    print("--- Generating Optimization Report ---\n")
    report = optimizer.generate_optimization_report()
    
    print(f"Total Recommendations: {report['total_recommendations']}")
    print(f"Estimated Monthly Savings: ${report['total_monthly_savings']:.2f}")
    print(f"Estimated Annual Savings: ${report['annual_savings']:.2f}")
    
    print("\n--- By Priority ---")
    for priority, data in sorted(report['by_priority'].items()):
        print(f"{priority.upper()}: {data['count']} items (${data['savings']:.2f}/month)")
    
    print("\n--- Top Recommendations ---")
    for i, rec in enumerate(report['recommendations'][:5], 1):
        print(f"\n{i}. {rec['title']}")
        print(f"   Priority: {rec['priority'].upper()}")
        print(f"   Savings: ${rec['savings']:.2f}/month")
        print(f"   Action: {rec['action']}")
        print(f"   Effort: {rec['effort']}")
    
    print("\n=== Demo Complete ===")

