"""
Cost Monitoring & AWS Budgets
Tracks infrastructure costs, sets budgets, and provides cost optimization recommendations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CostAlertLevel(Enum):
    """Cost alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostMetric:
    """Cost metric for a service"""

    service_name: str
    cost_usd: float
    usage_amount: float
    usage_unit: str
    time_period: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Budget:
    """Budget configuration"""

    budget_name: str
    monthly_limit_usd: float
    alert_thresholds: List[float]  # e.g., [0.5, 0.8, 1.0] for 50%, 80%, 100%
    services: List[str]  # Services included in budget
    current_spend: float = 0.0
    alerts_sent: List[str] = field(default_factory=list)


class CostMonitoringManager:
    """Manages cost tracking, budgets, and alerts"""

    def __init__(self):
        self.cost_history: List[CostMetric] = []
        self.budgets: Dict[str, Budget] = {}
        self.cost_recommendations: List[str] = []

    def track_cost(
        self,
        service_name: str,
        cost_usd: float,
        usage_amount: float,
        usage_unit: str,
        time_period: str = "hourly",
    ):
        """
        Track cost for a service.

        Args:
            service_name: Name of AWS service (e.g., "EC2", "RDS", "S3")
            cost_usd: Cost in USD
            usage_amount: Amount of usage
            usage_unit: Unit of usage (e.g., "GB", "hours", "requests")
            time_period: Time period (hourly, daily, monthly)
        """
        metric = CostMetric(
            service_name=service_name,
            cost_usd=cost_usd,
            usage_amount=usage_amount,
            usage_unit=usage_unit,
            time_period=time_period,
        )

        self.cost_history.append(metric)
        logger.info(
            f"Cost tracked: {service_name} = ${cost_usd:.2f} ({usage_amount} {usage_unit})"
        )

        # Update budgets
        self._update_budgets(service_name, cost_usd)

    def create_budget(
        self,
        budget_name: str,
        monthly_limit_usd: float,
        alert_thresholds: List[float],
        services: List[str],
    ) -> bool:
        """
        Create a new budget.

        Args:
            budget_name: Unique budget identifier
            monthly_limit_usd: Monthly spending limit
            alert_thresholds: List of alert thresholds (0-1)
            services: List of service names to include

        Returns:
            True if budget created
        """
        budget = Budget(
            budget_name=budget_name,
            monthly_limit_usd=monthly_limit_usd,
            alert_thresholds=sorted(alert_thresholds),
            services=services,
        )

        self.budgets[budget_name] = budget
        logger.info(
            f"Budget '{budget_name}' created: ${monthly_limit_usd}/month for {services}"
        )
        return True

    def _update_budgets(self, service_name: str, cost_usd: float):
        """Update budget spending and check alerts"""
        for budget_name, budget in self.budgets.items():
            if service_name in budget.services:
                budget.current_spend += cost_usd
                self._check_budget_alerts(budget)

    def _check_budget_alerts(self, budget: Budget):
        """Check if budget thresholds are exceeded"""
        spend_ratio = budget.current_spend / budget.monthly_limit_usd

        for threshold in budget.alert_thresholds:
            alert_key = f"{budget.budget_name}_{threshold}"

            if spend_ratio >= threshold and alert_key not in budget.alerts_sent:
                self._send_budget_alert(budget, threshold, spend_ratio)
                budget.alerts_sent.append(alert_key)

    def _send_budget_alert(self, budget: Budget, threshold: float, actual_ratio: float):
        """Send budget alert"""
        if threshold >= 1.0:
            level = CostAlertLevel.CRITICAL
        elif threshold >= 0.8:
            level = CostAlertLevel.WARNING
        else:
            level = CostAlertLevel.INFO

        logger.warning(
            f"[{level.value.upper()}] Budget '{budget.budget_name}' alert: "
            f"${budget.current_spend:.2f} / ${budget.monthly_limit_usd:.2f} "
            f"({actual_ratio:.1%} of limit, threshold: {threshold:.1%})"
        )

    def get_monthly_costs(self) -> Dict[str, float]:
        """Get costs by service for current month"""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        costs = {}
        for metric in self.cost_history:
            metric_time = datetime.fromisoformat(metric.timestamp)
            if metric_time >= month_start:
                costs[metric.service_name] = (
                    costs.get(metric.service_name, 0) + metric.cost_usd
                )

        return costs

    def get_budget_status(self, budget_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific budget"""
        if budget_name not in self.budgets:
            return None

        budget = self.budgets[budget_name]
        spend_ratio = budget.current_spend / budget.monthly_limit_usd
        remaining = budget.monthly_limit_usd - budget.current_spend

        return {
            "budget_name": budget.budget_name,
            "monthly_limit": budget.monthly_limit_usd,
            "current_spend": budget.current_spend,
            "remaining": remaining,
            "spend_percentage": spend_ratio * 100,
            "status": (
                "CRITICAL"
                if spend_ratio >= 1.0
                else "WARNING" if spend_ratio >= 0.8 else "OK"
            ),
            "services": budget.services,
            "alerts_sent": len(budget.alerts_sent),
        }

    def get_all_budgets_status(self) -> List[Dict[str, Any]]:
        """Get status of all budgets"""
        return [self.get_budget_status(name) for name in self.budgets.keys()]

    def analyze_cost_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze cost trends over specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        daily_costs = {}
        service_costs = {}

        for metric in self.cost_history:
            metric_time = datetime.fromisoformat(metric.timestamp)
            if metric_time >= cutoff_date:
                # Daily costs
                day_key = metric_time.date().isoformat()
                daily_costs[day_key] = daily_costs.get(day_key, 0) + metric.cost_usd

                # Service costs
                service_costs[metric.service_name] = (
                    service_costs.get(metric.service_name, 0) + metric.cost_usd
                )

        total_cost = sum(daily_costs.values())
        avg_daily_cost = total_cost / days if days > 0 else 0

        # Identify top costly services
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        return {
            "period_days": days,
            "total_cost": total_cost,
            "avg_daily_cost": avg_daily_cost,
            "daily_breakdown": daily_costs,
            "top_services": dict(top_services),
        }

    def generate_cost_optimization_recommendations(self) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        monthly_costs = self.get_monthly_costs()

        # Check for high RDS costs
        if "RDS" in monthly_costs and monthly_costs["RDS"] > 500:
            recommendations.append(
                "Consider using Aurora Serverless or RDS Reserved Instances for RDS cost savings (up to 60% discount)"
            )

        # Check for high EC2 costs
        if "EC2" in monthly_costs and monthly_costs["EC2"] > 300:
            recommendations.append(
                "Review EC2 instance types and consider rightsizing or Spot Instances for non-critical workloads"
            )

        # Check for high S3 costs
        if "S3" in monthly_costs and monthly_costs["S3"] > 100:
            recommendations.append(
                "Implement S3 lifecycle policies to move old data to Glacier or Intelligent-Tiering"
            )

        # Check for high data transfer costs
        if "DataTransfer" in monthly_costs and monthly_costs["DataTransfer"] > 100:
            recommendations.append(
                "Review data transfer patterns and consider using CloudFront CDN to reduce egress costs"
            )

        self.cost_recommendations = recommendations
        return recommendations


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("COST MONITORING & BUDGETS DEMO")
    print("=" * 80)

    cost_mgr = CostMonitoringManager()

    # Create budgets
    cost_mgr.create_budget(
        budget_name="monthly_infrastructure",
        monthly_limit_usd=1000.0,
        alert_thresholds=[0.5, 0.8, 0.9, 1.0],
        services=["EC2", "RDS", "S3"],
    )

    cost_mgr.create_budget(
        budget_name="ml_training",
        monthly_limit_usd=500.0,
        alert_thresholds=[0.75, 1.0],
        services=["EC2", "SageMaker"],
    )

    print("\n✅ Created 2 budgets")

    # Simulate cost tracking
    print("\n" + "=" * 80)
    print("TRACKING COSTS")
    print("=" * 80)

    # Track various costs
    cost_mgr.track_cost("EC2", 45.50, 24, "hours", "daily")
    cost_mgr.track_cost("RDS", 32.00, 24, "hours", "daily")
    cost_mgr.track_cost("S3", 8.75, 850, "GB", "daily")
    cost_mgr.track_cost("EC2", 450.00, 720, "hours", "monthly")  # Will trigger alerts
    cost_mgr.track_cost("RDS", 320.00, 720, "hours", "monthly")
    cost_mgr.track_cost("S3", 87.50, 8500, "GB", "monthly")

    # Check budget status
    print("\n" + "=" * 80)
    print("BUDGET STATUS")
    print("=" * 80)

    for budget_status in cost_mgr.get_all_budgets_status():
        print(f"\n💰 {budget_status['budget_name']}")
        print(f"   Limit: ${budget_status['monthly_limit']:.2f}/month")
        print(
            f"   Spent: ${budget_status['current_spend']:.2f} ({budget_status['spend_percentage']:.1f}%)"
        )
        print(f"   Remaining: ${budget_status['remaining']:.2f}")
        print(f"   Status: {budget_status['status']}")
        print(f"   Alerts Sent: {budget_status['alerts_sent']}")

    # Cost trends
    print("\n" + "=" * 80)
    print("COST TRENDS (Last 7 Days)")
    print("=" * 80)

    trends = cost_mgr.analyze_cost_trends(days=7)
    print(f"\nTotal Cost: ${trends['total_cost']:.2f}")
    print(f"Avg Daily Cost: ${trends['avg_daily_cost']:.2f}")
    print(f"\nTop Services:")
    for service, cost in trends["top_services"].items():
        print(f"  - {service}: ${cost:.2f}")

    # Recommendations
    print("\n" + "=" * 80)
    print("COST OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)

    recommendations = cost_mgr.generate_cost_optimization_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")

    print("\n" + "=" * 80)
    print("Cost Monitoring Demo Complete!")
    print("=" * 80)
