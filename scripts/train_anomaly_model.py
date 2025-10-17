#!/usr/bin/env python3
"""
Train Anomaly Detection Models
Builds baseline models from historical metrics data
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from monitoring.anomaly_detector import AnomalyDetectionSystem

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_historical_metrics(metrics_file: str) -> Dict[str, List[float]]:
    """
    Load historical metrics from JSON file

    Expected format:
    {
        "metric_name": [value1, value2, ...],
        ...
    }
    """
    if not os.path.exists(metrics_file):
        logger.error(f"Metrics file not found: {metrics_file}")
        return {}

    with open(metrics_file, "r") as f:
        data = json.load(f)

    return data


def generate_sample_metrics() -> Dict[str, List[float]]:
    """Generate sample metrics for testing"""
    import numpy as np

    np.random.seed(42)

    return {
        "response_time_ms": np.random.normal(250, 50, 1000).tolist(),
        "error_rate_percent": np.random.exponential(2, 1000).tolist(),
        "requests_per_second": np.random.normal(10, 2, 1000).tolist(),
        "cost_per_request": np.random.normal(0.012, 0.003, 1000).tolist(),
        "cache_hit_rate": np.random.beta(7, 3, 1000).tolist() * 100,
        "tokens_per_request": np.random.normal(2000, 400, 1000).tolist(),
    }


def train_models(
    historical_metrics: Dict[str, List[float]], output_dir: str
) -> AnomalyDetectionSystem:
    """
    Train anomaly detection models

    Args:
        historical_metrics: Dictionary of metric_name -> list of values
        output_dir: Directory to save trained models

    Returns:
        Trained anomaly detection system
    """
    logger.info("Initializing anomaly detection system...")
    detector = AnomalyDetectionSystem(
        enable_statistical=True, enable_timeseries=True, models_dir=output_dir
    )

    # Train with historical data
    logger.info(
        f"Training with historical data for {len(historical_metrics)} metrics..."
    )

    for metric_name, values in historical_metrics.items():
        logger.info(f"  Training {metric_name}: {len(values)} data points")

        for value in values:
            # Add to both detectors
            if detector.statistical_detector:
                detector.statistical_detector.add_data_point(metric_name, value)

            if detector.timeseries_detector:
                detector.timeseries_detector.add_data_point(metric_name, value)

    logger.info("Training complete!")

    # Save baselines
    logger.info("Saving baselines...")
    detector.save_baselines()

    return detector


def validate_models(
    detector: AnomalyDetectionSystem, validation_metrics: Dict[str, List[float]]
) -> Dict[str, int]:
    """
    Validate trained models with validation data

    Args:
        detector: Trained detector
        validation_metrics: Validation metrics

    Returns:
        Dictionary of anomaly counts per metric
    """
    logger.info("Validating models...")

    anomaly_counts = {}

    for metric_name, values in validation_metrics.items():
        anomaly_count = 0

        for value in values:
            anomalies = detector.detect_anomalies({metric_name: value})
            if anomalies:
                anomaly_count += 1

        anomaly_counts[metric_name] = anomaly_count

        anomaly_rate = (anomaly_count / len(values)) * 100 if values else 0
        logger.info(
            f"  {metric_name}: {anomaly_count}/{len(values)} anomalies ({anomaly_rate:.1f}%)"
        )

    return anomaly_counts


def main():
    parser = argparse.ArgumentParser(description="Train anomaly detection models")
    parser.add_argument(
        "--metrics-file", help="JSON file with historical metrics", default=None
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save trained models",
        default="monitoring/models",
    )
    parser.add_argument(
        "--use-sample-data",
        action="store_true",
        help="Use generated sample data for testing",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Run validation after training"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NBA MCP Synthesis - Anomaly Detection Model Training")
    print("=" * 70)
    print()

    # Load or generate metrics
    if args.use_sample_data or not args.metrics_file:
        logger.info("Generating sample metrics data...")
        historical_metrics = generate_sample_metrics()
    else:
        logger.info(f"Loading metrics from {args.metrics_file}...")
        historical_metrics = load_historical_metrics(args.metrics_file)

    if not historical_metrics:
        logger.error("No metrics data available")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Train models
    detector = train_models(historical_metrics, args.output_dir)

    # Validation
    if args.validate:
        print()
        logger.info("Running validation...")

        # Use same data for validation (in production, use separate validation set)
        validation_metrics = {
            name: values[-100:] for name, values in historical_metrics.items()
        }

        anomaly_counts = validate_models(detector, validation_metrics)

    print()
    print("=" * 70)
    print("✅ Model training complete!")
    print()
    print(f"Models saved to: {args.output_dir}")
    print()
    print("To use the trained models:")
    print("  from monitoring.anomaly_detector import get_anomaly_detector")
    print("  detector = get_anomaly_detector()")
    print("  detector.load_baselines()")
    print("=" * 70)


if __name__ == "__main__":
    main()
