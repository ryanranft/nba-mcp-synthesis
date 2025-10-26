"""
Model Monitoring & Drift Detection

Provides production-ready model monitoring with drift detection, performance tracking,
and automated alerting. Integrates with Week 1 infrastructure and MLflow for comprehensive
observability.

Week 1 Integration:
- @handle_errors for automatic error handling
- track_metric for monitoring metrics
- @require_permission for access control

MLflow Integration:
- Log drift metrics to MLflow
- Track performance over time
- Alert history logging

Features:
- Feature drift detection (KS test, PSI, KL divergence)
- Prediction drift detection
- Performance tracking (accuracy, latency, error rate)
- Alert generation with configurable thresholds
- Comprehensive metrics storage
- Thread-safe operations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import threading
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict

# Week 1 imports
try:
    from mcp_server.error_handling import handle_errors, NBAMCPError
    from mcp_server.monitoring import track_metric
    from mcp_server.rbac import require_permission, Permission
    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False
    # Fallback decorators
    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func
        return decorator
    def track_metric(metric_name):
        def decorator(func):
            return func
        return decorator
    def require_permission(permission):
        def decorator(func):
            return func
        return decorator
    class Permission:
        READ = "read"
        WRITE = "write"

# MLflow imports
try:
    from mcp_server.mlflow_integration import get_mlflow_tracker
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriftMethod(Enum):
    """Drift detection method"""

    KS_TEST = "ks_test"  # Kolmogorov-Smirnov test
    PSI = "psi"  # Population Stability Index
    KL_DIVERGENCE = "kl_divergence"  # Kullback-Leibler divergence


class AlertSeverity(Enum):
    """Alert severity level"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Type of monitoring alert"""

    FEATURE_DRIFT = "feature_drift"
    PREDICTION_DRIFT = "prediction_drift"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"


@dataclass
class DriftResult:
    """Result from drift detection"""

    feature_name: str
    method: DriftMethod
    drift_score: float
    threshold: float
    is_drift: bool
    p_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    total_predictions: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Monitoring alert"""

    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


@dataclass
class PredictionRecord:
    """Record of a single prediction for monitoring"""

    prediction_id: str
    model_id: str
    model_version: str
    features: Dict[str, Any]
    prediction: Any
    actual: Optional[Any] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class ModelMonitor:
    """
    Production model monitoring with drift detection and alerting.

    Features:
    - Feature and prediction drift detection
    - Performance tracking over time
    - Alert generation with configurable thresholds
    - MLflow integration for metrics logging
    - Week 1 integration (error handling, metrics, RBAC)

    Example:
        >>> monitor = ModelMonitor(
        ...     model_id="my_model",
        ...     model_version="v1.0",
        ...     enable_mlflow=True
        ... )
        >>>
        >>> # Log predictions
        >>> monitor.log_prediction(
        ...     prediction_id="pred_123",
        ...     features={"feature1": 0.5, "feature2": 1.2},
        ...     prediction=0.8,
        ...     latency_ms=45.2
        ... )
        >>>
        >>> # Check for drift
        >>> drift_results = monitor.detect_feature_drift(
        ...     reference_data=reference_df,
        ...     current_data=current_df,
        ...     method=DriftMethod.KS_TEST
        ... )
        >>>
        >>> # Get alerts
        >>> alerts = monitor.get_alerts(severity=AlertSeverity.CRITICAL)
    """

    def __init__(
        self,
        model_id: str,
        model_version: str,
        drift_threshold: float = 0.05,
        performance_threshold: float = 0.1,
        error_rate_threshold: float = 0.1,
        latency_threshold_ms: float = 1000.0,
        enable_mlflow: bool = False,
        mlflow_experiment: Optional[str] = None,
        alert_callback: Optional[Callable[[Alert], None]] = None,
        mock_mode: bool = False
    ):
        """
        Initialize model monitor.

        Args:
            model_id: Unique model identifier
            model_version: Model version
            drift_threshold: Threshold for drift detection (default: 0.05)
            performance_threshold: Threshold for performance degradation (default: 0.1)
            error_rate_threshold: Threshold for error rate alerts (default: 0.1)
            latency_threshold_ms: Threshold for latency alerts in ms (default: 1000.0)
            enable_mlflow: Enable MLflow integration
            mlflow_experiment: MLflow experiment name
            alert_callback: Optional callback function for alerts
            mock_mode: Enable mock mode for testing
        """
        self.model_id = model_id
        self.model_version = model_version
        self.drift_threshold = drift_threshold
        self.performance_threshold = performance_threshold
        self.error_rate_threshold = error_rate_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE and not mock_mode
        self.alert_callback = alert_callback
        self.mock_mode = mock_mode

        # Storage
        self.prediction_history: List[PredictionRecord] = []
        self.drift_history: List[DriftResult] = []
        self.performance_history: List[PerformanceMetrics] = []
        self.alerts: List[Alert] = []

        # Reference data for drift detection
        self.reference_features: Optional[pd.DataFrame] = None
        self.reference_predictions: Optional[np.ndarray] = None

        # Thread safety
        self.lock = threading.Lock()

        # MLflow setup
        self.mlflow_tracker = None
        if self.enable_mlflow:
            try:
                experiment_name = mlflow_experiment or f"monitoring_{model_id}"
                self.mlflow_tracker = get_mlflow_tracker(
                    experiment_name=experiment_name,
                    mock_mode=mock_mode
                )
                logger.info(f"MLflow tracking enabled for {model_id}")
            except Exception as e:
                logger.warning(f"Could not initialize MLflow tracker: {e}")
                self.enable_mlflow = False

        logger.info(
            f"ModelMonitor initialized for {model_id}:{model_version} "
            f"(drift_threshold={drift_threshold}, mock_mode={mock_mode})"
        )

    @handle_errors(reraise=True, notify=True)
    @track_metric("model_monitor.log_prediction")
    def log_prediction(
        self,
        prediction_id: str,
        features: Dict[str, Any],
        prediction: Any,
        actual: Optional[Any] = None,
        latency_ms: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """
        Log a prediction for monitoring.

        Args:
            prediction_id: Unique prediction identifier
            features: Input features used for prediction
            prediction: Model prediction
            actual: Actual value (for performance tracking)
            latency_ms: Prediction latency in milliseconds
            error: Error message if prediction failed
        """
        record = PredictionRecord(
            prediction_id=prediction_id,
            model_id=self.model_id,
            model_version=self.model_version,
            features=features,
            prediction=prediction,
            actual=actual,
            latency_ms=latency_ms,
            error=error
        )

        with self.lock:
            self.prediction_history.append(record)

        # Check for performance issues
        if latency_ms > self.latency_threshold_ms:
            self._generate_alert(
                alert_type=AlertType.HIGH_LATENCY,
                severity=AlertSeverity.WARNING,
                message=f"High latency detected: {latency_ms:.2f}ms",
                details={
                    "prediction_id": prediction_id,
                    "latency_ms": latency_ms,
                    "threshold_ms": self.latency_threshold_ms
                }
            )

        if error:
            self._generate_alert(
                alert_type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.WARNING,
                message=f"Prediction error: {error}",
                details={
                    "prediction_id": prediction_id,
                    "error": error
                }
            )

        # Log to MLflow
        if self.enable_mlflow and self.mlflow_tracker:
            try:
                with self.mlflow_tracker.start_run(f"prediction_{prediction_id}") as run_id:
                    self.mlflow_tracker.log_metrics({
                        "latency_ms": latency_ms,
                        "has_error": 1.0 if error else 0.0
                    })
                    if actual is not None and isinstance(prediction, (int, float)) and isinstance(actual, (int, float)):
                        self.mlflow_tracker.log_metric("absolute_error", abs(prediction - actual))
            except Exception as e:
                logger.warning(f"Could not log prediction to MLflow: {e}")

        logger.debug(f"Logged prediction {prediction_id} (latency={latency_ms:.2f}ms)")

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    @track_metric("model_monitor.set_reference_data")
    def set_reference_data(
        self,
        features: pd.DataFrame,
        predictions: Optional[np.ndarray] = None
    ) -> None:
        """
        Set reference data for drift detection.

        Args:
            features: Reference feature data
            predictions: Reference predictions (optional)
        """
        with self.lock:
            self.reference_features = features.copy()
            if predictions is not None:
                self.reference_predictions = predictions.copy()

        logger.info(
            f"Reference data set: {len(features)} samples, "
            f"{len(features.columns)} features"
        )

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.READ)
    @track_metric("model_monitor.detect_feature_drift")
    def detect_feature_drift(
        self,
        current_data: pd.DataFrame,
        method: DriftMethod = DriftMethod.KS_TEST,
        features: Optional[List[str]] = None
    ) -> List[DriftResult]:
        """
        Detect feature drift using specified method.

        Args:
            current_data: Current feature data to compare
            method: Drift detection method
            features: Specific features to check (default: all)

        Returns:
            List of drift results for each feature
        """
        if self.reference_features is None:
            raise ValueError("Reference data not set. Call set_reference_data() first.")

        features_to_check = features or list(self.reference_features.columns)
        results = []

        for feature in features_to_check:
            if feature not in self.reference_features.columns:
                logger.warning(f"Feature {feature} not in reference data, skipping")
                continue

            if feature not in current_data.columns:
                logger.warning(f"Feature {feature} not in current data, skipping")
                continue

            reference = self.reference_features[feature].dropna()
            current = current_data[feature].dropna()

            if len(reference) == 0 or len(current) == 0:
                logger.warning(f"Empty data for feature {feature}, skipping")
                continue

            # Detect drift based on method
            if method == DriftMethod.KS_TEST:
                drift_score, p_value, is_drift = self._ks_test(reference, current)
                result = DriftResult(
                    feature_name=feature,
                    method=method,
                    drift_score=drift_score,
                    threshold=self.drift_threshold,
                    is_drift=is_drift,
                    p_value=p_value
                )
            elif method == DriftMethod.PSI:
                drift_score = self._psi(reference, current)
                result = DriftResult(
                    feature_name=feature,
                    method=method,
                    drift_score=drift_score,
                    threshold=self.drift_threshold,
                    is_drift=drift_score > self.drift_threshold
                )
            elif method == DriftMethod.KL_DIVERGENCE:
                drift_score = self._kl_divergence(reference, current)
                result = DriftResult(
                    feature_name=feature,
                    method=method,
                    drift_score=drift_score,
                    threshold=self.drift_threshold,
                    is_drift=drift_score > self.drift_threshold
                )
            else:
                raise ValueError(f"Unknown drift method: {method}")

            results.append(result)

            with self.lock:
                self.drift_history.append(result)

            # Generate alert if drift detected
            if result.is_drift:
                self._generate_alert(
                    alert_type=AlertType.FEATURE_DRIFT,
                    severity=AlertSeverity.WARNING,
                    message=f"Feature drift detected: {feature}",
                    details={
                        "feature": feature,
                        "method": method.value,
                        "drift_score": drift_score,
                        "threshold": self.drift_threshold,
                        "p_value": result.p_value
                    }
                )

        # Log to MLflow
        if self.enable_mlflow and self.mlflow_tracker:
            try:
                drift_count = sum(1 for r in results if r.is_drift)
                with self.mlflow_tracker.start_run(f"drift_check_{datetime.now().isoformat()}") as run_id:
                    self.mlflow_tracker.log_metrics({
                        "features_checked": len(results),
                        "features_drifted": drift_count,
                        "drift_rate": drift_count / len(results) if results else 0.0
                    })
            except Exception as e:
                logger.warning(f"Could not log drift metrics to MLflow: {e}")

        logger.info(
            f"Drift detection complete: {len(results)} features checked, "
            f"{sum(1 for r in results if r.is_drift)} drifted"
        )

        return results

    def _ks_test(
        self,
        reference: pd.Series,
        current: pd.Series
    ) -> Tuple[float, float, bool]:
        """
        Kolmogorov-Smirnov test for drift detection.

        Args:
            reference: Reference distribution
            current: Current distribution

        Returns:
            Tuple of (statistic, p_value, is_drift)
        """
        statistic, p_value = stats.ks_2samp(reference, current)
        is_drift = p_value < self.drift_threshold
        return statistic, p_value, is_drift

    def _psi(
        self,
        reference: pd.Series,
        current: pd.Series,
        n_bins: int = 10
    ) -> float:
        """
        Population Stability Index (PSI) for drift detection.

        Args:
            reference: Reference distribution
            current: Current distribution
            n_bins: Number of bins for discretization

        Returns:
            PSI value
        """
        # Create bins based on reference data
        bins = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
        bins = np.unique(bins)  # Remove duplicates

        if len(bins) < 2:
            return 0.0

        # Calculate frequencies
        ref_freq, _ = np.histogram(reference, bins=bins)
        cur_freq, _ = np.histogram(current, bins=bins)

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        ref_freq = ref_freq + epsilon
        cur_freq = cur_freq + epsilon

        # Normalize to probabilities
        ref_prob = ref_freq / np.sum(ref_freq)
        cur_prob = cur_freq / np.sum(cur_freq)

        # Calculate PSI
        psi = np.sum((cur_prob - ref_prob) * np.log(cur_prob / ref_prob))

        return float(psi)

    def _kl_divergence(
        self,
        reference: pd.Series,
        current: pd.Series,
        n_bins: int = 10
    ) -> float:
        """
        Kullback-Leibler divergence for drift detection.

        Args:
            reference: Reference distribution
            current: Current distribution
            n_bins: Number of bins for discretization

        Returns:
            KL divergence value
        """
        # Create bins based on reference data
        bins = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
        bins = np.unique(bins)

        if len(bins) < 2:
            return 0.0

        # Calculate frequencies
        ref_freq, _ = np.histogram(reference, bins=bins)
        cur_freq, _ = np.histogram(current, bins=bins)

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        ref_freq = ref_freq + epsilon
        cur_freq = cur_freq + epsilon

        # Normalize to probabilities
        ref_prob = ref_freq / np.sum(ref_freq)
        cur_prob = cur_freq / np.sum(cur_freq)

        # Calculate KL divergence
        kl_div = np.sum(cur_prob * np.log(cur_prob / ref_prob))

        return float(kl_div)

    @handle_errors(reraise=True, notify=True)
    @require_permission(Permission.READ)
    @track_metric("model_monitor.calculate_performance")
    def calculate_performance(
        self,
        window_hours: int = 24
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics for recent predictions.

        Args:
            window_hours: Time window in hours for metrics calculation

        Returns:
            Performance metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)

        with self.lock:
            recent_predictions = [
                p for p in self.prediction_history
                if p.timestamp >= cutoff_time
            ]

        if not recent_predictions:
            return PerformanceMetrics()

        # Calculate metrics
        total = len(recent_predictions)
        errors = sum(1 for p in recent_predictions if p.error is not None)
        error_rate = errors / total if total > 0 else 0.0

        avg_latency = (
            sum(p.latency_ms for p in recent_predictions) / total
            if total > 0 else 0.0
        )

        # Calculate accuracy if we have actuals
        predictions_with_actuals = [
            p for p in recent_predictions
            if p.actual is not None and p.error is None
        ]

        accuracy = None
        if predictions_with_actuals:
            # For classification (assuming binary or matching predictions)
            correct = sum(
                1 for p in predictions_with_actuals
                if (isinstance(p.prediction, (int, float)) and
                    isinstance(p.actual, (int, float)) and
                    abs(p.prediction - p.actual) < 0.5)  # Threshold for classification
            )
            accuracy = correct / len(predictions_with_actuals)

        metrics = PerformanceMetrics(
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            error_rate=error_rate,
            total_predictions=total
        )

        with self.lock:
            self.performance_history.append(metrics)

        # Check for performance degradation
        if error_rate > self.error_rate_threshold:
            self._generate_alert(
                alert_type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.CRITICAL,
                message=f"High error rate: {error_rate:.2%}",
                details={
                    "error_rate": error_rate,
                    "threshold": self.error_rate_threshold,
                    "window_hours": window_hours,
                    "total_predictions": total
                }
            )

        # Log to MLflow
        if self.enable_mlflow and self.mlflow_tracker:
            try:
                with self.mlflow_tracker.start_run(f"performance_{datetime.now().isoformat()}") as run_id:
                    metrics_dict = {
                        "avg_latency_ms": avg_latency,
                        "error_rate": error_rate,
                        "total_predictions": float(total)
                    }
                    if accuracy is not None:
                        metrics_dict["accuracy"] = accuracy
                    self.mlflow_tracker.log_metrics(metrics_dict)
            except Exception as e:
                logger.warning(f"Could not log performance metrics to MLflow: {e}")

        logger.info(
            f"Performance calculated: accuracy={accuracy}, "
            f"error_rate={error_rate:.2%}, latency={avg_latency:.2f}ms"
        )

        return metrics

    def _generate_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Generate a monitoring alert.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            details: Additional details
        """
        alert_id = f"{alert_type.value}_{datetime.now().isoformat()}"

        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details
        )

        with self.lock:
            self.alerts.append(alert)

        logger.warning(f"Alert generated [{severity.value}]: {message}")

        # Call alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        acknowledged: Optional[bool] = None,
        hours: Optional[int] = None
    ) -> List[Alert]:
        """
        Get monitoring alerts with optional filtering.

        Args:
            severity: Filter by severity
            alert_type: Filter by alert type
            acknowledged: Filter by acknowledgment status
            hours: Filter by time window in hours

        Returns:
            List of matching alerts
        """
        with self.lock:
            alerts = self.alerts.copy()

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            alerts = [a for a in alerts if a.timestamp >= cutoff]

        return alerts

    @handle_errors(reraise=True, notify=False)
    @require_permission(Permission.WRITE)
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if acknowledged, False if not found
        """
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    logger.info(f"Alert acknowledged: {alert_id}")
                    return True

        return False

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_drift_history(
        self,
        feature: Optional[str] = None,
        hours: Optional[int] = None
    ) -> List[DriftResult]:
        """
        Get drift detection history.

        Args:
            feature: Filter by feature name
            hours: Filter by time window in hours

        Returns:
            List of drift results
        """
        with self.lock:
            history = self.drift_history.copy()

        if feature:
            history = [d for d in history if d.feature_name == feature]

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            history = [d for d in history if d.timestamp >= cutoff]

        return history

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_performance_history(
        self,
        hours: Optional[int] = None
    ) -> List[PerformanceMetrics]:
        """
        Get performance metrics history.

        Args:
            hours: Filter by time window in hours

        Returns:
            List of performance metrics
        """
        with self.lock:
            history = self.performance_history.copy()

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            history = [p for p in history if p.timestamp >= cutoff]

        return history

    @handle_errors(reraise=False, notify=False)
    @require_permission(Permission.READ)
    def get_prediction_history(
        self,
        hours: Optional[int] = None,
        include_errors: bool = True
    ) -> List[PredictionRecord]:
        """
        Get prediction history.

        Args:
            hours: Filter by time window in hours
            include_errors: Include predictions with errors

        Returns:
            List of prediction records
        """
        with self.lock:
            history = self.prediction_history.copy()

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            history = [p for p in history if p.timestamp >= cutoff]

        if not include_errors:
            history = [p for p in history if p.error is None]

        return history
