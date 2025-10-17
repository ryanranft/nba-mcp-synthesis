#!/usr/bin/env python3
"""
ML-Based Anomaly Detection
Predictive alerting using statistical analysis and machine learning
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

# Try to import ML libraries (optional dependencies)
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""

    is_anomaly: bool
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # low, medium, high, critical
    confidence: float
    method: str
    timestamp: str
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        return {**asdict(self), "expected_range": list(self.expected_range)}


class StatisticalAnomalyDetector:
    """Statistical anomaly detection using Z-score and IQR methods"""

    def __init__(
        self,
        window_size: int = 100,
        z_score_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ):
        """
        Initialize detector

        Args:
            window_size: Number of data points to keep in history
            z_score_threshold: Standard deviations for anomaly threshold
            iqr_multiplier: IQR multiplier for outlier detection
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier
        self.history: Dict[str, deque] = {}

    def add_data_point(self, metric_name: str, value: float):
        """Add a data point to history"""
        if metric_name not in self.history:
            self.history[metric_name] = deque(maxlen=self.window_size)

        self.history[metric_name].append(value)

    def detect_zscore(
        self, metric_name: str, value: float, add_to_history: bool = True
    ) -> Optional[AnomalyResult]:
        """
        Detect anomalies using Z-score method

        Z-score = (value - mean) / std_dev
        Anomaly if |Z-score| > threshold
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available, Z-score detection disabled")
            return None

        if metric_name not in self.history or len(self.history[metric_name]) < 10:
            # Not enough data
            if add_to_history:
                self.add_data_point(metric_name, value)
            return None

        # Calculate statistics
        data = np.array(list(self.history[metric_name]))
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            # No variation in data
            return None

        # Calculate Z-score
        z_score = abs((value - mean) / std)

        # Add to history if requested
        if add_to_history:
            self.add_data_point(metric_name, value)

        # Check for anomaly
        is_anomaly = z_score > self.z_score_threshold

        if is_anomaly:
            # Determine severity
            if z_score > 5:
                severity = "critical"
            elif z_score > 4:
                severity = "high"
            elif z_score > 3.5:
                severity = "medium"
            else:
                severity = "low"

            # Calculate expected range (mean ± threshold * std)
            expected_min = mean - (self.z_score_threshold * std)
            expected_max = mean + (self.z_score_threshold * std)

            return AnomalyResult(
                is_anomaly=True,
                metric_name=metric_name,
                value=value,
                expected_range=(expected_min, expected_max),
                severity=severity,
                confidence=min(z_score / 5.0, 1.0),  # Normalize to 0-1
                method="z-score",
                timestamp=datetime.now().isoformat(),
                context={"z_score": z_score, "mean": mean, "std": std},
            )

        return None

    def detect_iqr(
        self, metric_name: str, value: float, add_to_history: bool = True
    ) -> Optional[AnomalyResult]:
        """
        Detect anomalies using IQR (Interquartile Range) method

        IQR = Q3 - Q1
        Outliers: value < Q1 - (multiplier * IQR) or value > Q3 + (multiplier * IQR)
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available, IQR detection disabled")
            return None

        if metric_name not in self.history or len(self.history[metric_name]) < 10:
            if add_to_history:
                self.add_data_point(metric_name, value)
            return None

        # Calculate quartiles
        data = np.array(list(self.history[metric_name]))
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1

        if iqr == 0:
            return None

        # Calculate bounds
        lower_bound = q1 - (self.iqr_multiplier * iqr)
        upper_bound = q3 + (self.iqr_multiplier * iqr)

        # Add to history if requested
        if add_to_history:
            self.add_data_point(metric_name, value)

        # Check for anomaly
        is_anomaly = value < lower_bound or value > upper_bound

        if is_anomaly:
            # Determine severity based on how far outside bounds
            distance = max(lower_bound - value, value - upper_bound, 0)
            relative_distance = distance / iqr if iqr > 0 else 0

            if relative_distance > 3:
                severity = "critical"
            elif relative_distance > 2:
                severity = "high"
            elif relative_distance > 1.5:
                severity = "medium"
            else:
                severity = "low"

            return AnomalyResult(
                is_anomaly=True,
                metric_name=metric_name,
                value=value,
                expected_range=(lower_bound, upper_bound),
                severity=severity,
                confidence=min(relative_distance / 3.0, 1.0),
                method="iqr",
                timestamp=datetime.now().isoformat(),
                context={"q1": q1, "q3": q3, "iqr": iqr},
            )

        return None

    def detect(
        self,
        metric_name: str,
        value: float,
        method: str = "both",
        add_to_history: bool = True,
    ) -> List[AnomalyResult]:
        """
        Detect anomalies using specified method(s)

        Args:
            metric_name: Name of the metric
            value: Current value
            method: Detection method ("zscore", "iqr", "both")
            add_to_history: Whether to add value to history

        Returns:
            List of anomaly results (empty if no anomalies)
        """
        results = []

        if method in ["zscore", "both"]:
            result = self.detect_zscore(metric_name, value, add_to_history=False)
            if result:
                results.append(result)

        if method in ["iqr", "both"]:
            result = self.detect_iqr(metric_name, value, add_to_history=False)
            if result:
                results.append(result)

        # Add to history once after all detections
        if add_to_history:
            self.add_data_point(metric_name, value)

        return results


class TimeSeriesAnomalyDetector:
    """Time-series based anomaly detection with trend analysis"""

    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.timeseries_data: Dict[str, List[Tuple[datetime, float]]] = {}

    def add_data_point(
        self, metric_name: str, value: float, timestamp: Optional[datetime] = None
    ):
        """Add time-stamped data point"""
        if metric_name not in self.timeseries_data:
            self.timeseries_data[metric_name] = []

        ts = timestamp or datetime.now()
        self.timeseries_data[metric_name].append((ts, value))

        # Clean old data
        cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
        self.timeseries_data[metric_name] = [
            (t, v) for t, v in self.timeseries_data[metric_name] if t > cutoff
        ]

    def detect_trend_deviation(
        self, metric_name: str, value: float, deviation_threshold: float = 0.3
    ) -> Optional[AnomalyResult]:
        """
        Detect if current value deviates significantly from recent trend

        Args:
            metric_name: Metric name
            value: Current value
            deviation_threshold: Threshold for deviation (0.3 = 30%)

        Returns:
            Anomaly result if deviation detected
        """
        if not SCIPY_AVAILABLE:
            return None

        if (
            metric_name not in self.timeseries_data
            or len(self.timeseries_data[metric_name]) < 5
        ):
            self.add_data_point(metric_name, value)
            return None

        # Get recent data
        data = self.timeseries_data[metric_name]
        values = np.array([v for _, v in data])

        # Calculate trend (simple linear regression)
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

        # Predict next value based on trend
        predicted = slope * len(values) + intercept

        if predicted == 0:
            return None

        # Calculate deviation
        deviation = abs((value - predicted) / predicted)

        # Add to history
        self.add_data_point(metric_name, value)

        # Check for anomaly
        if deviation > deviation_threshold:
            if deviation > 0.8:
                severity = "critical"
            elif deviation > 0.6:
                severity = "high"
            elif deviation > 0.4:
                severity = "medium"
            else:
                severity = "low"

            # Calculate expected range
            margin = predicted * deviation_threshold
            expected_min = predicted - margin
            expected_max = predicted + margin

            return AnomalyResult(
                is_anomaly=True,
                metric_name=metric_name,
                value=value,
                expected_range=(expected_min, expected_max),
                severity=severity,
                confidence=min(deviation / 0.8, 1.0),
                method="trend-deviation",
                timestamp=datetime.now().isoformat(),
                context={
                    "predicted": predicted,
                    "deviation": deviation,
                    "trend_slope": slope,
                    "r_squared": r_value**2,
                },
            )

        return None


class AnomalyDetectionSystem:
    """Unified anomaly detection system"""

    def __init__(
        self,
        enable_statistical: bool = True,
        enable_timeseries: bool = True,
        models_dir: Optional[str] = None,
    ):
        self.enable_statistical = enable_statistical and SCIPY_AVAILABLE
        self.enable_timeseries = enable_timeseries and SCIPY_AVAILABLE

        if not SCIPY_AVAILABLE:
            logger.warning(
                "scipy not installed. Statistical anomaly detection disabled."
            )
            logger.warning("To enable: pip install scipy")

        self.statistical_detector = (
            StatisticalAnomalyDetector() if self.enable_statistical else None
        )
        self.timeseries_detector = (
            TimeSeriesAnomalyDetector() if self.enable_timeseries else None
        )

        self.models_dir = models_dir or os.path.join(
            os.path.dirname(__file__), "models"
        )
        os.makedirs(self.models_dir, exist_ok=True)

    def detect_anomalies(self, metrics: Dict[str, float]) -> List[AnomalyResult]:
        """
        Detect anomalies across multiple metrics

        Args:
            metrics: Dictionary of metric_name -> value

        Returns:
            List of anomaly results
        """
        anomalies = []

        for metric_name, value in metrics.items():
            # Statistical detection
            if self.statistical_detector:
                results = self.statistical_detector.detect(metric_name, value)
                anomalies.extend(results)

            # Time-series detection
            if self.timeseries_detector:
                result = self.timeseries_detector.detect_trend_deviation(
                    metric_name, value
                )
                if result:
                    anomalies.append(result)

        return anomalies

    def save_baselines(self, filename: str = "baselines.json"):
        """Save current baselines to file"""
        filepath = os.path.join(self.models_dir, filename)

        baselines = {}

        if self.statistical_detector:
            for metric_name, history in self.statistical_detector.history.items():
                if len(history) > 0:
                    baselines[metric_name] = {
                        "mean": float(np.mean(list(history))),
                        "std": float(np.std(list(history))),
                        "min": float(np.min(list(history))),
                        "max": float(np.max(list(history))),
                    }

        with open(filepath, "w") as f:
            json.dump(baselines, f, indent=2)

        logger.info(f"Saved baselines to {filepath}")

    def load_baselines(self, filename: str = "baselines.json"):
        """Load baselines from file"""
        filepath = os.path.join(self.models_dir, filename)

        if not os.path.exists(filepath):
            logger.warning(f"Baseline file not found: {filepath}")
            return

        with open(filepath, "r") as f:
            baselines = json.load(f)

        logger.info(f"Loaded baselines for {len(baselines)} metrics")


# Global instance
_detector_instance: Optional[AnomalyDetectionSystem] = None


def get_anomaly_detector() -> AnomalyDetectionSystem:
    """Get or create global anomaly detector"""
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = AnomalyDetectionSystem()

    return _detector_instance


# CLI for testing
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("NBA MCP Synthesis - Anomaly Detection Test")
    print("=" * 70)
    print()

    if not SCIPY_AVAILABLE:
        print("❌ scipy not installed")
        print()
        print("To install: pip install scipy")
        sys.exit(1)

    print("✅ scipy available")
    print()

    # Create detector
    detector = AnomalyDetectionSystem()

    # Simulate normal data
    print("Training with normal data...")
    np.random.seed(42)
    normal_data = np.random.normal(100, 10, 50)

    for i, value in enumerate(normal_data):
        detector.detect_anomalies({"response_time": value})

    print(f"  Trained with {len(normal_data)} data points")
    print()

    # Test with anomalies
    print("Testing anomaly detection...")
    test_cases = [
        ("Normal", 105),
        ("Slight anomaly", 130),
        ("Clear anomaly", 200),
        ("Critical anomaly", 300),
    ]

    for label, value in test_cases:
        anomalies = detector.detect_anomalies({"response_time": value})

        if anomalies:
            for anomaly in anomalies:
                print(f"  🚨 {label}: {value}")
                print(f"     Severity: {anomaly.severity}")
                print(f"     Confidence: {anomaly.confidence:.2%}")
                print(f"     Method: {anomaly.method}")
                print(
                    f"     Expected: {anomaly.expected_range[0]:.1f} - {anomaly.expected_range[1]:.1f}"
                )
        else:
            print(f"  ✅ {label}: {value} (normal)")

    print()
    print("=" * 70)
    print("✅ Anomaly detection test complete!")
    print("=" * 70)
