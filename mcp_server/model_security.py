"""
Model Security Module
Protects against model poisoning, adversarial attacks, and data integrity issues.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelSecurityManager:
    """Manages model security including poisoning detection and validation"""

    def __init__(self, trusted_models_registry: Optional[str] = None):
        """
        Initialize model security manager.

        Args:
            trusted_models_registry: Path to file containing trusted model hashes
        """
        self.trusted_models_registry = trusted_models_registry or "model_registry.json"
        self.trusted_models = self._load_trusted_models()

    def _load_trusted_models(self) -> Dict[str, Any]:
        """Load trusted model registry from file"""
        try:
            if Path(self.trusted_models_registry).exists():
                with open(self.trusted_models_registry, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading trusted models registry: {e}")
            return {}

    def _save_trusted_models(self):
        """Save trusted models registry to file"""
        try:
            with open(self.trusted_models_registry, 'w') as f:
                json.dump(self.trusted_models, f, indent=2)
            logger.info("Trusted models registry saved")
        except Exception as e:
            logger.error(f"Error saving trusted models registry: {e}")

    def calculate_model_hash(self, model_path: str) -> str:
        """
        Calculate SHA256 hash of model file.

        Args:
            model_path: Path to model file

        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(model_path, "rb") as f:
                # Read in 64kb chunks for large models
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating model hash: {e}")
            raise

    def register_trusted_model(
        self,
        model_name: str,
        model_path: str,
        version: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a model as trusted by storing its hash.

        Args:
            model_name: Name/identifier for the model
            model_path: Path to model file
            version: Model version
            metadata: Optional metadata (author, date, purpose, etc.)

        Returns:
            True if registration successful
        """
        try:
            model_hash = self.calculate_model_hash(model_path)

            self.trusted_models[model_name] = {
                "hash": model_hash,
                "version": version,
                "path": model_path,
                "registered_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }

            self._save_trusted_models()
            logger.info(f"Model '{model_name}' v{version} registered as trusted")
            return True

        except Exception as e:
            logger.error(f"Error registering trusted model: {e}")
            return False

    def verify_model_integrity(self, model_name: str, model_path: str) -> bool:
        """
        Verify a model hasn't been tampered with by comparing hash.

        Args:
            model_name: Name of model to verify
            model_path: Path to model file

        Returns:
            True if model matches trusted hash, False otherwise
        """
        if model_name not in self.trusted_models:
            logger.warning(f"Model '{model_name}' not in trusted registry")
            return False

        try:
            current_hash = self.calculate_model_hash(model_path)
            trusted_hash = self.trusted_models[model_name]["hash"]

            if current_hash == trusted_hash:
                logger.info(f"Model '{model_name}' integrity verified ✓")
                return True
            else:
                logger.error(
                    f"Model '{model_name}' integrity check FAILED! "
                    f"Hash mismatch: expected {trusted_hash[:16]}..., "
                    f"got {current_hash[:16]}..."
                )
                return False

        except Exception as e:
            logger.error(f"Error verifying model integrity: {e}")
            return False

    def detect_data_poisoning(
        self,
        training_data: np.ndarray,
        labels: np.ndarray,
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detect potential data poisoning by analyzing statistical anomalies.

        Args:
            training_data: Training features array
            labels: Training labels array
            threshold: Anomaly detection threshold (default 5%)

        Returns:
            Dict with poisoning detection results
        """
        results = {
            "is_poisoned": False,
            "anomalies_detected": [],
            "confidence": 0.0
        }

        try:
            # 1. Check for duplicate samples (potential backdoor)
            unique_samples = len(np.unique(training_data, axis=0))
            total_samples = len(training_data)
            duplicate_ratio = 1 - (unique_samples / total_samples)

            if duplicate_ratio > threshold:
                results["anomalies_detected"].append({
                    "type": "high_duplicate_ratio",
                    "value": duplicate_ratio,
                    "threshold": threshold,
                    "severity": "HIGH"
                })

            # 2. Check label distribution (class imbalance attacks)
            unique_labels, label_counts = np.unique(labels, return_counts=True)
            label_distribution = label_counts / total_samples

            # Check if any class is suspiciously underrepresented
            min_class_ratio = np.min(label_distribution)
            if min_class_ratio < threshold / 2:
                results["anomalies_detected"].append({
                    "type": "extreme_class_imbalance",
                    "value": min_class_ratio,
                    "threshold": threshold / 2,
                    "severity": "MEDIUM"
                })

            # 3. Check for outliers in feature space
            feature_means = np.mean(training_data, axis=0)
            feature_stds = np.std(training_data, axis=0)

            # Z-score method for outlier detection
            z_scores = np.abs((training_data - feature_means) / (feature_stds + 1e-10))
            outlier_mask = np.any(z_scores > 3, axis=1)
            outlier_ratio = np.sum(outlier_mask) / total_samples

            if outlier_ratio > threshold:
                results["anomalies_detected"].append({
                    "type": "high_outlier_ratio",
                    "value": outlier_ratio,
                    "threshold": threshold,
                    "severity": "MEDIUM"
                })

            # 4. Check for correlated mislabeling
            # (advanced: would require validation set comparison)

            # Determine if poisoned
            if results["anomalies_detected"]:
                results["is_poisoned"] = True
                high_severity_count = sum(
                    1 for a in results["anomalies_detected"]
                    if a["severity"] == "HIGH"
                )
                results["confidence"] = min(
                    0.3 + (high_severity_count * 0.2) +
                    (len(results["anomalies_detected"]) * 0.1),
                    1.0
                )

            logger.info(
                f"Data poisoning detection complete: "
                f"{'POISONED' if results['is_poisoned'] else 'CLEAN'} "
                f"(confidence: {results['confidence']:.2%})"
            )

        except Exception as e:
            logger.error(f"Error in data poisoning detection: {e}")
            results["error"] = str(e)

        return results

    def validate_input_data(
        self,
        input_data: np.ndarray,
        reference_stats: Optional[Dict] = None
    ) -> bool:
        """
        Validate input data against expected distribution.
        Detects adversarial examples and out-of-distribution inputs.

        Args:
            input_data: Input features to validate
            reference_stats: Reference statistics (mean, std, min, max per feature)

        Returns:
            True if data passes validation
        """
        if reference_stats is None:
            logger.warning("No reference stats provided, skipping validation")
            return True

        try:
            # Check feature dimensions
            expected_features = reference_stats.get("n_features")
            if expected_features and input_data.shape[1] != expected_features:
                logger.error(
                    f"Feature dimension mismatch: expected {expected_features}, "
                    f"got {input_data.shape[1]}"
                )
                return False

            # Check value ranges
            for i in range(input_data.shape[1]):
                feature_values = input_data[:, i]
                ref_min = reference_stats.get(f"feature_{i}_min")
                ref_max = reference_stats.get(f"feature_{i}_max")

                if ref_min is not None and np.any(feature_values < ref_min * 0.8):
                    logger.warning(f"Feature {i} has values below expected range")
                    return False

                if ref_max is not None and np.any(feature_values > ref_max * 1.2):
                    logger.warning(f"Feature {i} has values above expected range")
                    return False

            logger.info("Input data validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating input data: {e}")
            return False

    def audit_model_usage(
        self,
        model_name: str,
        user_id: str,
        input_hash: str,
        prediction: Any
    ):
        """
        Audit model usage for security monitoring.

        Args:
            model_name: Name of model used
            user_id: User who made the request
            input_hash: Hash of input data
            prediction: Model prediction result
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_name": model_name,
            "user_id": user_id,
            "input_hash": input_hash,
            "prediction_type": type(prediction).__name__
        }

        # Log to audit trail (in production, send to CloudWatch/S3)
        logger.info(f"Model usage audit: {json.dumps(audit_entry)}")


# Example usage
if __name__ == "__main__":
    # Initialize security manager
    security_mgr = ModelSecurityManager()

    # Example 1: Register a trusted model
    print("=" * 60)
    print("Example 1: Register Trusted Model")
    print("=" * 60)

    # Simulate creating a model file
    test_model_path = "/tmp/test_model.pkl"
    with open(test_model_path, 'wb') as f:
        f.write(b"test model weights")

    security_mgr.register_trusted_model(
        model_name="nba_prediction_model",
        model_path=test_model_path,
        version="1.0.0",
        metadata={
            "author": "ML Team",
            "purpose": "NBA game outcome prediction",
            "training_date": "2025-10-01"
        }
    )

    # Example 2: Verify model integrity
    print("\n" + "=" * 60)
    print("Example 2: Verify Model Integrity")
    print("=" * 60)

    is_valid = security_mgr.verify_model_integrity(
        model_name="nba_prediction_model",
        model_path=test_model_path
    )
    print(f"Model integrity check: {'PASSED' if is_valid else 'FAILED'}")

    # Simulate tampering
    print("\nSimulating model tampering...")
    with open(test_model_path, 'ab') as f:
        f.write(b"malicious code")

    is_valid = security_mgr.verify_model_integrity(
        model_name="nba_prediction_model",
        model_path=test_model_path
    )
    print(f"Model integrity check after tampering: {'PASSED' if is_valid else 'FAILED'}")

    # Example 3: Detect data poisoning
    print("\n" + "=" * 60)
    print("Example 3: Detect Data Poisoning")
    print("=" * 60)

    # Clean training data
    clean_data = np.random.randn(1000, 10)
    clean_labels = np.random.randint(0, 2, 1000)

    results = security_mgr.detect_data_poisoning(clean_data, clean_labels)
    print(f"Clean data check: {'POISONED' if results['is_poisoned'] else 'CLEAN'}")

    # Poisoned training data (with many duplicates)
    poisoned_data = np.vstack([
        clean_data,
        np.tile(clean_data[0], (100, 1))  # Add 100 duplicate backdoor samples
    ])
    poisoned_labels = np.concatenate([clean_labels, np.ones(100)])

    results = security_mgr.detect_data_poisoning(poisoned_data, poisoned_labels)
    print(f"\nPoisoned data check: {'POISONED' if results['is_poisoned'] else 'CLEAN'}")
    print(f"Confidence: {results['confidence']:.2%}")
    print(f"Anomalies detected: {len(results['anomalies_detected'])}")
    for anomaly in results['anomalies_detected']:
        print(f"  - {anomaly['type']}: {anomaly['value']:.4f} (severity: {anomaly['severity']})")

    # Example 4: Validate input data
    print("\n" + "=" * 60)
    print("Example 4: Validate Input Data")
    print("=" * 60)

    reference_stats = {
        "n_features": 10,
        "feature_0_min": -3.0,
        "feature_0_max": 3.0,
        "feature_1_min": -3.0,
        "feature_1_max": 3.0,
    }

    # Valid input
    valid_input = np.random.randn(5, 10)
    is_valid = security_mgr.validate_input_data(valid_input, reference_stats)
    print(f"Valid input check: {'PASSED' if is_valid else 'FAILED'}")

    # Adversarial input (out of range)
    adversarial_input = np.random.randn(5, 10) * 10  # 10x larger values
    is_valid = security_mgr.validate_input_data(adversarial_input, reference_stats)
    print(f"Adversarial input check: {'PASSED' if is_valid else 'FAILED'}")

    print("\n" + "=" * 60)
    print("Model Security Checks Complete!")
    print("=" * 60)

