"""Data Drift Detection - BOOK RECOMMENDATION 2"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class DataDriftDetector:
    """Detect statistical drift in data distributions"""

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize drift detector

        Args:
            significance_level: P-value threshold for drift detection
        """
        self.significance_level = significance_level
        self.reference_stats = {}
        self.drift_history = []

    def set_reference(self, data: Dict[str, List[float]], name: str = "baseline"):
        """
        Set reference distribution

        Args:
            data: Dictionary of feature name -> values
            name: Name for this reference
        """
        self.reference_stats[name] = {}

        for feature, values in data.items():
            self.reference_stats[name][feature] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "count": len(values),
                "distribution": np.array(values),
            }

        logger.info(f"✅ Reference set for {len(data)} features: {name}")

    def detect_drift_ks(
        self, current_data: List[float], reference_data: List[float]
    ) -> Dict[str, Any]:
        """
        Detect drift using Kolmogorov-Smirnov test

        Args:
            current_data: Current data distribution
            reference_data: Reference data distribution

        Returns:
            Drift detection results
        """
        statistic, pvalue = stats.ks_2samp(current_data, reference_data)

        drift_detected = pvalue < self.significance_level

        return {
            "test": "Kolmogorov-Smirnov",
            "statistic": float(statistic),
            "pvalue": float(pvalue),
            "drift_detected": drift_detected,
            "severity": (
                "high" if pvalue < 0.01 else ("medium" if drift_detected else "low")
            ),
        }

    def detect_drift_psi(
        self, current_data: List[float], reference_data: List[float], bins: int = 10
    ) -> Dict[str, Any]:
        """
        Detect drift using Population Stability Index (PSI)

        Args:
            current_data: Current data distribution
            reference_data: Reference data distribution
            bins: Number of bins for histogram

        Returns:
            PSI value and interpretation
        """
        # Calculate histograms
        ref_counts, bin_edges = np.histogram(reference_data, bins=bins)
        curr_counts, _ = np.histogram(current_data, bins=bin_edges)

        # Normalize to get percentages
        ref_pct = (
            ref_counts / len(reference_data)
        ) + 1e-10  # Add small value to avoid log(0)
        curr_pct = (curr_counts / len(current_data)) + 1e-10

        # Calculate PSI
        psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))

        # Interpret PSI
        # PSI < 0.1: No significant change
        # 0.1 <= PSI < 0.2: Small change
        # PSI >= 0.2: Significant change (drift detected)

        drift_detected = psi >= 0.1
        severity = "high" if psi >= 0.2 else ("medium" if psi >= 0.1 else "low")

        return {
            "test": "Population Stability Index",
            "psi": float(psi),
            "drift_detected": drift_detected,
            "severity": severity,
            "interpretation": self._interpret_psi(psi),
        }

    def _interpret_psi(self, psi: float) -> str:
        """Interpret PSI value"""
        if psi < 0.1:
            return "No significant change"
        elif psi < 0.2:
            return "Small change - monitor"
        else:
            return "Significant drift - investigate!"

    def check_all_features(
        self, current_data: Dict[str, List[float]], reference_name: str = "baseline"
    ) -> Dict[str, Any]:
        """
        Check drift for all features

        Args:
            current_data: Current data
            reference_name: Name of reference to compare against

        Returns:
            Drift detection results for all features
        """
        if reference_name not in self.reference_stats:
            raise ValueError(f"Reference '{reference_name}' not found")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "reference": reference_name,
            "features": {},
            "overall_drift": False,
            "drifted_features": [],
        }

        reference = self.reference_stats[reference_name]

        for feature, curr_values in current_data.items():
            if feature not in reference:
                logger.warning(f"⚠️  Feature {feature} not in reference - skipping")
                continue

            ref_values = reference[feature]["distribution"]

            # Run both tests
            ks_result = self.detect_drift_ks(curr_values, ref_values)
            psi_result = self.detect_drift_psi(curr_values, ref_values)

            # Combine results
            drift_detected = ks_result["drift_detected"] or psi_result["drift_detected"]

            results["features"][feature] = {
                "ks_test": ks_result,
                "psi_test": psi_result,
                "drift_detected": drift_detected,
                "current_mean": float(np.mean(curr_values)),
                "reference_mean": reference[feature]["mean"],
                "mean_change": float(np.mean(curr_values) - reference[feature]["mean"]),
            }

            if drift_detected:
                results["overall_drift"] = True
                results["drifted_features"].append(feature)
                logger.warning(f"🚨 Drift detected in feature: {feature}")

        # Store in history
        self.drift_history.append(results)

        # Alert if drift detected
        if results["overall_drift"]:
            logger.error(
                f"🚨 DATA DRIFT DETECTED! "
                f"{len(results['drifted_features'])} features drifted: "
                f"{', '.join(results['drifted_features'])}"
            )

            # Send alert
            from mcp_server.alerting import alert, AlertSeverity

            alert(
                "Data Drift Detected",
                f"Drift detected in {len(results['drifted_features'])} features",
                AlertSeverity.CRITICAL,
            )

        return results

    def get_drift_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get drift summary for recent period

        Args:
            days: Number of days to analyze

        Returns:
            Drift summary
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        recent_drifts = [
            d
            for d in self.drift_history
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]

        if not recent_drifts:
            return {"message": "No drift checks in specified period"}

        # Count drifts per feature
        feature_drifts = {}
        for drift in recent_drifts:
            for feature in drift["drifted_features"]:
                feature_drifts[feature] = feature_drifts.get(feature, 0) + 1

        return {
            "period_days": days,
            "total_checks": len(recent_drifts),
            "checks_with_drift": sum(1 for d in recent_drifts if d["overall_drift"]),
            "features_with_drift": feature_drifts,
            "most_drifted_features": sorted(
                feature_drifts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }


# Global drift detector
_drift_detector = None


def get_drift_detector() -> DataDriftDetector:
    """Get global drift detector"""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = DataDriftDetector()
    return _drift_detector


# Scheduled drift check
def scheduled_drift_check():
    """Run scheduled drift detection"""
    logger.info("🔄 Running scheduled drift check...")

    detector = get_drift_detector()

    # TODO: Fetch current data from database
    # TODO: Compare against reference
    # This would be run daily via cron/Airflow

    logger.info("✅ Drift check complete")


# Example usage
if __name__ == "__main__":
    detector = DataDriftDetector()

    # Set reference data
    reference = {
        "points_per_game": [20, 22, 19, 21, 23, 20, 22],
        "assists_per_game": [5, 6, 5, 7, 6, 5, 6],
        "rebounds_per_game": [8, 9, 7, 8, 9, 8, 7],
    }
    detector.set_reference(reference)

    # Check current data
    current = {
        "points_per_game": [15, 16, 14, 15, 16],  # Drifted down
        "assists_per_game": [5, 6, 5, 6, 5],  # No drift
        "rebounds_per_game": [8, 9, 8, 7, 9],  # No drift
    }

    results = detector.check_all_features(current)
    print(f"Drift detected: {results['overall_drift']}")
    print(f"Drifted features: {results['drifted_features']}")
