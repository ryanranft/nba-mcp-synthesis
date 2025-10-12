"""
Advanced Anomaly Detection Module
Multiple algorithms for detecting anomalies in data and predictions.
"""

import logging
from typing import Dict, Optional, Any, List
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Advanced anomaly detection with multiple algorithms"""

    def __init__(self):
        """Initialize anomaly detector"""
        self.historical_data: List[float] = []
        self.anomalies_detected: List[Dict] = []

    def add_observation(self, value: float):
        """Add observation to historical data"""
        self.historical_data.append(value)

    def detect_zscore(
        self,
        value: float,
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies using Z-score method.

        Args:
            value: Value to check
            threshold: Z-score threshold (default 3.0)

        Returns:
            Detection result
        """
        if len(self.historical_data) < 2:
            return {"is_anomaly": False, "reason": "Insufficient data"}

        mean = statistics.mean(self.historical_data)
        stdev = statistics.stdev(self.historical_data)

        if stdev == 0:
            return {"is_anomaly": False, "reason": "Zero variance"}

        z_score = (value - mean) / stdev
        is_anomaly = abs(z_score) > threshold

        result = {
            "is_anomaly": is_anomaly,
            "method": "z-score",
            "z_score": z_score,
            "threshold": threshold,
            "value": value,
            "mean": mean,
            "stdev": stdev
        }

        if is_anomaly:
            self.anomalies_detected.append(result)
            logger.warning(f"Z-score anomaly detected: {value} (z={z_score:.2f})")

        return result

    def detect_iqr(
        self,
        value: float,
        multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect anomalies using Interquartile Range (IQR) method.

        Args:
            value: Value to check
            multiplier: IQR multiplier (default 1.5)

        Returns:
            Detection result
        """
        if len(self.historical_data) < 4:
            return {"is_anomaly": False, "reason": "Insufficient data"}

        sorted_data = sorted(self.historical_data)
        n = len(sorted_data)
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        is_anomaly = value < lower_bound or value > upper_bound

        result = {
            "is_anomaly": is_anomaly,
            "method": "iqr",
            "value": value,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        }

        if is_anomaly:
            self.anomalies_detected.append(result)
            logger.warning(
                f"IQR anomaly detected: {value} "
                f"(bounds: [{lower_bound:.2f}, {upper_bound:.2f}])"
            )

        return result

    def detect_moving_average(
        self,
        value: float,
        window: int = 10,
        threshold_std: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies using moving average deviation.

        Args:
            value: Value to check
            window: Moving average window size
            threshold_std: Standard deviation threshold

        Returns:
            Detection result
        """
        if len(self.historical_data) < window:
            return {"is_anomaly": False, "reason": "Insufficient data for window"}

        recent = self.historical_data[-window:]
        ma = statistics.mean(recent)
        ma_std = statistics.stdev(recent) if len(recent) > 1 else 0

        if ma_std == 0:
            return {"is_anomaly": False, "reason": "Zero variance in window"}

        deviation = abs(value - ma) / ma_std
        is_anomaly = deviation > threshold_std

        result = {
            "is_anomaly": is_anomaly,
            "method": "moving_average",
            "value": value,
            "moving_average": ma,
            "moving_std": ma_std,
            "deviation": deviation,
            "threshold": threshold_std
        }

        if is_anomaly:
            self.anomalies_detected.append(result)
            logger.warning(
                f"Moving average anomaly detected: {value} "
                f"(deviation: {deviation:.2f} std)"
            )

        return result

    def detect_ensemble(
        self,
        value: float
    ) -> Dict[str, Any]:
        """
        Detect anomalies using ensemble of methods.

        Args:
            value: Value to check

        Returns:
            Ensemble detection result
        """
        zscore_result = self.detect_zscore(value)
        iqr_result = self.detect_iqr(value)
        ma_result = self.detect_moving_average(value)

        # Count votes
        votes = sum([
            zscore_result.get("is_anomaly", False),
            iqr_result.get("is_anomaly", False),
            ma_result.get("is_anomaly", False)
        ])

        is_anomaly = votes >= 2  # Majority vote

        result = {
            "is_anomaly": is_anomaly,
            "method": "ensemble",
            "value": value,
            "votes": votes,
            "total_methods": 3,
            "methods": {
                "z-score": zscore_result.get("is_anomaly", False),
                "iqr": iqr_result.get("is_anomaly", False),
                "moving_average": ma_result.get("is_anomaly", False)
            }
        }

        if is_anomaly:
            logger.warning(f"Ensemble anomaly detected: {value} ({votes}/3 votes)")

        return result

    def get_anomaly_report(self) -> Dict[str, Any]:
        """Get anomaly detection report"""
        if not self.anomalies_detected:
            return {
                "total_anomalies": 0,
                "total_observations": len(self.historical_data)
            }

        methods = {}
        for anomaly in self.anomalies_detected:
            method = anomaly.get("method", "unknown")
            methods[method] = methods.get(method, 0) + 1

        return {
            "total_anomalies": len(self.anomalies_detected),
            "total_observations": len(self.historical_data),
            "anomaly_rate": len(self.anomalies_detected) / len(self.historical_data) * 100 if self.historical_data else 0,
            "by_method": methods,
            "recent_anomalies": self.anomalies_detected[-5:]
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("ADVANCED ANOMALY DETECTION DEMO")
    print("=" * 80)

    detector = AnomalyDetector()

    # Add normal data
    print("\n" + "=" * 80)
    print("ADDING NORMAL OBSERVATIONS")
    print("=" * 80)

    import random
    normal_data = [random.gauss(100, 10) for _ in range(100)]
    for value in normal_data:
        detector.add_observation(value)

    print(f"✅ Added {len(normal_data)} normal observations (mean≈100, std≈10)")

    # Test anomalies
    print("\n" + "=" * 80)
    print("TESTING ANOMALY DETECTION")
    print("=" * 80)

    test_values = [
        ("Normal", 105),
        ("Mild Outlier", 130),
        ("Strong Outlier", 160),
        ("Extreme Low", 40)
    ]

    for label, value in test_values:
        print(f"\n{label}: {value}")

        # Z-score
        z_result = detector.detect_zscore(value)
        print(f"  Z-score: {'❌ ANOMALY' if z_result['is_anomaly'] else '✅ Normal'} "
              f"(z={z_result.get('z_score', 0):.2f})")

        # IQR
        iqr_result = detector.detect_iqr(value)
        print(f"  IQR:     {'❌ ANOMALY' if iqr_result['is_anomaly'] else '✅ Normal'}")

        # Moving Average
        ma_result = detector.detect_moving_average(value)
        print(f"  MA:      {'❌ ANOMALY' if ma_result['is_anomaly'] else '✅ Normal'}")

        # Ensemble
        ensemble_result = detector.detect_ensemble(value)
        print(f"  Ensemble: {'❌ ANOMALY' if ensemble_result['is_anomaly'] else '✅ Normal'} "
              f"({ensemble_result['votes']}/3 votes)")

    # Anomaly report
    print("\n" + "=" * 80)
    print("ANOMALY DETECTION REPORT")
    print("=" * 80)

    report = detector.get_anomaly_report()
    print(f"\nTotal Observations: {report['total_observations']}")
    print(f"Total Anomalies: {report['total_anomalies']}")
    print(f"Anomaly Rate: {report['anomaly_rate']:.2f}%")
    print(f"\nBy Method:")
    for method, count in report['by_method'].items():
        print(f"  - {method}: {count}")

    print("\n" + "=" * 80)
    print("Anomaly Detection Demo Complete!")
    print("=" * 80)

