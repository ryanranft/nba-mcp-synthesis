"""A/B Testing Framework - IMPORTANT & BOOK RECOMMENDATION 7"""
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class Variant:
    """A/B test variant"""
    name: str
    model_version: str
    traffic_percentage: float
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)


@dataclass
class ABTest:
    """A/B test configuration"""
    name: str
    description: str
    variants: List[Variant]
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "running"  # running, completed, cancelled
    winner: Optional[str] = None
    
    def get_variant(self, user_id: str) -> Variant:
        """
        Assign a variant to a user (consistent assignment)
        
        Args:
            user_id: User identifier
            
        Returns:
            Assigned variant
        """
        # Use hash for consistent assignment
        hash_value = hash(f"{self.name}_{user_id}") % 100
        
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.traffic_percentage * 100
            if hash_value < cumulative:
                return variant
        
        # Fallback to first variant
        return self.variants[0]


class ABTestManager:
    """Manage A/B tests"""
    
    def __init__(self):
        self.tests: Dict[str, ABTest] = {}
    
    def create_test(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        duration_days: Optional[int] = None
    ) -> ABTest:
        """
        Create a new A/B test
        
        Args:
            name: Test name
            description: Test description
            variants: List of variant configurations
            duration_days: Optional test duration
            
        Returns:
            Created test
        """
        # Validate traffic percentages
        total_traffic = sum(v['traffic_percentage'] for v in variants)
        if not (0.99 <= total_traffic <= 1.01):  # Allow for rounding errors
            raise ValueError(f"Traffic percentages must sum to 1.0, got {total_traffic}")
        
        # Create variant objects
        variant_objects = [
            Variant(
                name=v['name'],
                model_version=v['model_version'],
                traffic_percentage=v['traffic_percentage']
            )
            for v in variants
        ]
        
        # Calculate end date
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days) if duration_days else None
        
        # Create test
        test = ABTest(
            name=name,
            description=description,
            variants=variant_objects,
            start_date=start_date,
            end_date=end_date
        )
        
        self.tests[name] = test
        logger.info(f"✅ Created A/B test: {name} with {len(variants)} variants")
        
        return test
    
    def get_variant_for_user(self, test_name: str, user_id: str) -> Optional[Variant]:
        """Get assigned variant for a user"""
        if test_name not in self.tests:
            logger.warning(f"⚠️  Test {test_name} not found")
            return None
        
        test = self.tests[test_name]
        
        if test.status != "running":
            logger.warning(f"⚠️  Test {test_name} is not running (status: {test.status})")
            return None
        
        return test.get_variant(user_id)
    
    def record_metric(
        self,
        test_name: str,
        variant_name: str,
        metric_name: str,
        value: float
    ):
        """Record a metric for a variant"""
        if test_name not in self.tests:
            logger.warning(f"⚠️  Test {test_name} not found")
            return
        
        test = self.tests[test_name]
        
        for variant in test.variants:
            if variant.name == variant_name:
                variant.record_metric(metric_name, value)
                logger.debug(f"📊 Recorded {metric_name}={value} for {variant_name}")
                return
        
        logger.warning(f"⚠️  Variant {variant_name} not found in test {test_name}")
    
    def analyze_test(self, test_name: str) -> Dict[str, Any]:
        """
        Analyze A/B test results
        
        Args:
            test_name: Test name
            
        Returns:
            Analysis results
        """
        if test_name not in self.tests:
            return {"error": f"Test {test_name} not found"}
        
        test = self.tests[test_name]
        results = {
            "test_name": test_name,
            "status": test.status,
            "start_date": test.start_date.isoformat(),
            "variants": {},
            "statistical_significance": {}
        }
        
        # Analyze each variant
        for variant in test.variants:
            variant_stats = {}
            
            for metric_name, values in variant.metrics.items():
                if values:
                    variant_stats[metric_name] = {
                        "count": len(values),
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values))
                    }
            
            results["variants"][variant.name] = {
                "model_version": variant.model_version,
                "traffic_percentage": variant.traffic_percentage,
                "metrics": variant_stats
            }
        
        # Statistical significance testing (compare variants)
        if len(test.variants) == 2:
            results["statistical_significance"] = self._compare_variants(
                test.variants[0],
                test.variants[1]
            )
        
        return results
    
    def _compare_variants(self, variant_a: Variant, variant_b: Variant) -> Dict[str, Any]:
        """
        Compare two variants using t-test
        
        Args:
            variant_a: First variant
            variant_b: Second variant
            
        Returns:
            Statistical comparison results
        """
        comparisons = {}
        
        # Compare each common metric
        common_metrics = set(variant_a.metrics.keys()) & set(variant_b.metrics.keys())
        
        for metric_name in common_metrics:
            values_a = variant_a.metrics[metric_name]
            values_b = variant_b.metrics[metric_name]
            
            if len(values_a) < 2 or len(values_b) < 2:
                comparisons[metric_name] = {
                    "error": "Insufficient data for statistical test"
                }
                continue
            
            # Perform t-test
            t_statistic, p_value = stats.ttest_ind(values_a, values_b)
            
            # Calculate effect size (Cohen's d)
            mean_diff = np.mean(values_a) - np.mean(values_b)
            pooled_std = np.sqrt(
                (np.std(values_a)**2 + np.std(values_b)**2) / 2
            )
            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
            
            comparisons[metric_name] = {
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "cohens_d": float(cohens_d),
                "effect_size": self._interpret_effect_size(cohens_d),
                "winner": variant_a.name if mean_diff > 0 else variant_b.name,
                "improvement": abs(float(mean_diff))
            }
        
        return comparisons
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def declare_winner(self, test_name: str, winner_variant: str):
        """
        Declare a winner and stop the test
        
        Args:
            test_name: Test name
            winner_variant: Winning variant name
        """
        if test_name not in self.tests:
            logger.error(f"❌ Test {test_name} not found")
            return
        
        test = self.tests[test_name]
        test.status = "completed"
        test.winner = winner_variant
        test.end_date = datetime.utcnow()
        
        logger.info(f"🎉 Test {test_name} completed - Winner: {winner_variant}")
        
        # Send alert
        from mcp_server.alerting import alert, AlertSeverity
        alert(
            f"A/B Test Complete: {test_name}",
            f"Winner: {winner_variant}",
            AlertSeverity.INFO
        )
    
    def get_test_summary(self, test_name: str) -> str:
        """Generate human-readable test summary"""
        analysis = self.analyze_test(test_name)
        
        if "error" in analysis:
            return f"❌ {analysis['error']}"
        
        summary = f"""
🧪 A/B TEST SUMMARY: {test_name}
{'='*60}

Status: {analysis['status']}
Start Date: {analysis['start_date']}

VARIANTS:
"""
        
        for variant_name, variant_data in analysis['variants'].items():
            summary += f"\n📊 {variant_name}:"
            summary += f"\n   Model: {variant_data['model_version']}"
            summary += f"\n   Traffic: {variant_data['traffic_percentage']:.1%}"
            summary += "\n   Metrics:"
            
            for metric_name, metric_stats in variant_data['metrics'].items():
                summary += f"\n   - {metric_name}: {metric_stats['mean']:.4f} (n={metric_stats['count']})"
        
        if analysis.get('statistical_significance'):
            summary += "\n\nSTATISTICAL SIGNIFICANCE:"
            
            for metric, comparison in analysis['statistical_significance'].items():
                if 'error' in comparison:
                    continue
                
                summary += f"\n\n📈 {metric}:"
                summary += f"\n   Winner: {comparison['winner']}"
                summary += f"\n   Improvement: {comparison['improvement']:.4f}"
                summary += f"\n   P-value: {comparison['p_value']:.4f}"
                summary += f"\n   Significant: {'✅ Yes' if comparison['significant'] else '❌ No'}"
                summary += f"\n   Effect Size: {comparison['effect_size']}"
        
        summary += f"\n\n{'='*60}\n"
        
        return summary


# Global A/B test manager
_ab_test_manager = None


def get_ab_test_manager() -> ABTestManager:
    """Get global A/B test manager"""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager


# Example usage
if __name__ == "__main__":
    manager = ABTestManager()
    
    # Create a test
    test = manager.create_test(
        name="model_comparison_v1_v2",
        description="Compare model v1.0 vs v2.0",
        variants=[
            {
                "name": "control",
                "model_version": "v1.0",
                "traffic_percentage": 0.5
            },
            {
                "name": "treatment",
                "model_version": "v2.0",
                "traffic_percentage": 0.5
            }
        ],
        duration_days=7
    )
    
    # Simulate some metrics
    for i in range(100):
        variant = test.get_variant(f"user_{i}")
        
        # Simulate accuracy metric (v2 slightly better)
        if variant.name == "control":
            accuracy = random.gauss(0.80, 0.05)
        else:
            accuracy = random.gauss(0.85, 0.05)
        
        manager.record_metric(
            "model_comparison_v1_v2",
            variant.name,
            "accuracy",
            accuracy
        )
    
    # Analyze
    summary = manager.get_test_summary("model_comparison_v1_v2")
    print(summary)

