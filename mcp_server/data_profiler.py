"""
Data Profiler Module
Automated data profiling and drift detection for NBA MCP system.

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive profiling: statistics, quality metrics, distribution analysis, drift detection.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext
    from mcp_server.monitoring import get_health_monitor

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriftMethod(Enum):
    """Drift detection methods"""

    KL_DIVERGENCE = "kl_divergence"
    KS_TEST = "ks_test"
    PSI = "psi"  # Population Stability Index


@dataclass
class ColumnProfile:
    """Profile for a single column"""

    name: str
    dtype: str
    count: int
    unique_count: int
    null_count: int
    null_percentage: float

    # Numeric stats
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

    # Categorical stats
    mode: Optional[Any] = None
    mode_frequency: Optional[int] = None
    cardinality: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "dtype": self.dtype,
            "count": self.count,
            "unique_count": self.unique_count,
            "null_count": self.null_count,
            "null_percentage": self.null_percentage,
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "min": self.min_value,
            "max": self.max_value,
            "q25": self.q25,
            "q75": self.q75,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "mode": str(self.mode) if self.mode is not None else None,
            "mode_frequency": self.mode_frequency,
            "cardinality": self.cardinality,
        }


@dataclass
class DataProfile:
    """Complete data profile"""

    dataset_name: str
    timestamp: datetime
    row_count: int
    column_count: int
    memory_usage_mb: float
    columns: List[ColumnProfile] = dc_field(default_factory=list)
    correlations: Optional[Dict[str, Dict[str, float]]] = None
    quality_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp.isoformat(),
            "row_count": self.row_count,
            "column_count": self.column_count,
            "memory_usage_mb": self.memory_usage_mb,
            "columns": [col.to_dict() for col in self.columns],
            "correlations": self.correlations,
            "quality_score": self.quality_score,
        }


@dataclass
class DriftResult:
    """Result of drift detection"""

    column: str
    method: DriftMethod
    drift_detected: bool
    drift_score: float
    threshold: float
    details: Dict[str, Any] = dc_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "column": self.column,
            "method": self.method.value,
            "drift_detected": self.drift_detected,
            "drift_score": self.drift_score,
            "threshold": self.threshold,
            "details": self.details,
        }


class DataProfiler:
    """
    Automated data profiling and drift detection.

    Provides comprehensive profiling:
    - Statistical summaries
    - Data quality metrics
    - Distribution analysis
    - Drift detection (KL divergence, KS test, PSI)
    - NBA-specific templates
    """

    def __init__(self):
        """Initialize data profiler"""
        self.profile_history: List[DataProfile] = []
        logger.info("DataProfiler initialized")

    @handle_errors(reraise=True, notify=False)
    def profile_column(self, df: pd.DataFrame, column: str) -> ColumnProfile:
        """
        Profile a single column.

        Args:
            df: DataFrame containing the column
            column: Column name to profile

        Returns:
            ColumnProfile object
        """
        series = df[column]

        profile = ColumnProfile(
            name=column,
            dtype=str(series.dtype),
            count=len(series),
            unique_count=series.nunique(),
            null_count=series.isnull().sum(),
            null_percentage=series.isnull().sum() / len(series) if len(series) > 0 else 0,
        )

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(series):
            profile.mean = float(series.mean()) if not series.isnull().all() else None
            profile.median = float(series.median()) if not series.isnull().all() else None
            profile.std = float(series.std()) if not series.isnull().all() else None
            profile.min_value = float(series.min()) if not series.isnull().all() else None
            profile.max_value = float(series.max()) if not series.isnull().all() else None
            profile.q25 = float(series.quantile(0.25)) if not series.isnull().all() else None
            profile.q75 = float(series.quantile(0.75)) if not series.isnull().all() else None

            # Skewness and kurtosis
            try:
                profile.skewness = float(series.skew())
                profile.kurtosis = float(series.kurtosis())
            except:
                pass

        # Categorical statistics
        if not series.empty:
            mode_values = series.mode()
            if len(mode_values) > 0:
                profile.mode = mode_values[0]
                profile.mode_frequency = int((series == profile.mode).sum())
                profile.cardinality = profile.unique_count

        return profile

    @handle_errors(reraise=True, notify=False)
    def profile(self, df: pd.DataFrame, dataset_name: str = "dataset") -> DataProfile:
        """
        Profile entire DataFrame.

        Args:
            df: DataFrame to profile
            dataset_name: Name of the dataset

        Returns:
            DataProfile object
        """
        # Basic metadata
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

        profile = DataProfile(
            dataset_name=dataset_name,
            timestamp=datetime.now(),
            row_count=len(df),
            column_count=len(df.columns),
            memory_usage_mb=memory_mb,
        )

        # Profile each column
        for col in df.columns:
            col_profile = self.profile_column(df, col)
            profile.columns.append(col_profile)

        # Calculate correlations for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            profile.correlations = {
                col: corr_matrix[col].to_dict() for col in numeric_cols
            }

        # Calculate quality score
        profile.quality_score = self._calculate_quality_score(df, profile)

        # Save to history
        self.profile_history.append(profile)

        # Track metrics if Week 1 available
        if WEEK1_AVAILABLE:
            self._track_metrics(profile)

        return profile

    def _calculate_quality_score(self, df: pd.DataFrame, profile: DataProfile) -> float:
        """Calculate overall data quality score"""
        scores = []

        # Completeness score (inverse of null percentage)
        total_values = df.shape[0] * df.shape[1]
        null_values = sum(col.null_count for col in profile.columns)
        completeness = 1 - (null_values / total_values if total_values > 0 else 0)
        scores.append(completeness)

        # Uniqueness score (average unique ratio for applicable columns)
        uniqueness_scores = []
        for col in profile.columns:
            if col.count > 0 and col.cardinality is not None:
                unique_ratio = col.unique_count / col.count
                uniqueness_scores.append(unique_ratio)

        if uniqueness_scores:
            scores.append(np.mean(uniqueness_scores))

        # Overall quality score
        return float(np.mean(scores)) if scores else 1.0

    @handle_errors(reraise=True, notify=False)
    def detect_drift_kl_divergence(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column: str,
        threshold: float = 0.1,
        bins: int = 10,
    ) -> DriftResult:
        """
        Detect drift using KL divergence.

        Args:
            reference_data: Reference dataset
            current_data: Current dataset to compare
            column: Column to check
            threshold: Drift threshold
            bins: Number of bins for histogram

        Returns:
            DriftResult object
        """
        # Create histograms
        ref_values = reference_data[column].dropna()
        cur_values = current_data[column].dropna()

        # Define common bins
        min_val = min(ref_values.min(), cur_values.min())
        max_val = max(ref_values.max(), cur_values.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        # Calculate histograms
        ref_hist, _ = np.histogram(ref_values, bins=bin_edges, density=True)
        cur_hist, _ = np.histogram(cur_values, bins=bin_edges, density=True)

        # Normalize to probabilities
        ref_hist = ref_hist / ref_hist.sum() if ref_hist.sum() > 0 else ref_hist
        cur_hist = cur_hist / cur_hist.sum() if cur_hist.sum() > 0 else cur_hist

        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        ref_hist = ref_hist + epsilon
        cur_hist = cur_hist + epsilon

        # Calculate KL divergence using Jensen-Shannon distance
        kl_div = jensenshannon(ref_hist, cur_hist) ** 2

        drift_detected = bool(kl_div > threshold)

        return DriftResult(
            column=column,
            method=DriftMethod.KL_DIVERGENCE,
            drift_detected=drift_detected,
            drift_score=float(kl_div),
            threshold=threshold,
            details={
                "reference_mean": float(ref_values.mean()),
                "current_mean": float(cur_values.mean()),
                "reference_std": float(ref_values.std()),
                "current_std": float(cur_values.std()),
            },
        )

    @handle_errors(reraise=True, notify=False)
    def detect_drift_ks_test(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column: str,
        threshold: float = 0.05,
    ) -> DriftResult:
        """
        Detect drift using Kolmogorov-Smirnov test.

        Args:
            reference_data: Reference dataset
            current_data: Current dataset to compare
            column: Column to check
            threshold: p-value threshold (default: 0.05)

        Returns:
            DriftResult object
        """
        ref_values = reference_data[column].dropna()
        cur_values = current_data[column].dropna()

        # Perform KS test
        ks_statistic, p_value = stats.ks_2samp(ref_values, cur_values)

        # Drift detected if p-value < threshold (reject null hypothesis)
        drift_detected = bool(p_value < threshold)

        return DriftResult(
            column=column,
            method=DriftMethod.KS_TEST,
            drift_detected=drift_detected,
            drift_score=float(ks_statistic),
            threshold=threshold,
            details={
                "p_value": float(p_value),
                "reference_mean": float(ref_values.mean()),
                "current_mean": float(cur_values.mean()),
            },
        )

    @handle_errors(reraise=True, notify=False)
    def detect_drift_psi(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column: str,
        threshold: float = 0.2,
        bins: int = 10,
    ) -> DriftResult:
        """
        Detect drift using Population Stability Index (PSI).

        Args:
            reference_data: Reference dataset
            current_data: Current dataset to compare
            column: Column to check
            threshold: PSI threshold (0.1=small, 0.2=medium, 0.25+=large shift)
            bins: Number of bins

        Returns:
            DriftResult object
        """
        ref_values = reference_data[column].dropna()
        cur_values = current_data[column].dropna()

        # Define bins based on reference data
        _, bin_edges = np.histogram(ref_values, bins=bins)

        # Calculate distributions
        ref_dist, _ = np.histogram(ref_values, bins=bin_edges)
        cur_dist, _ = np.histogram(cur_values, bins=bin_edges)

        # Convert to percentages
        ref_pct = ref_dist / len(ref_values)
        cur_pct = cur_dist / len(cur_values)

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
        cur_pct = np.where(cur_pct == 0, epsilon, cur_pct)

        # Calculate PSI
        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))

        drift_detected = bool(psi > threshold)

        return DriftResult(
            column=column,
            method=DriftMethod.PSI,
            drift_detected=drift_detected,
            drift_score=float(psi),
            threshold=threshold,
            details={
                "interpretation": (
                    "No significant change"
                    if psi < 0.1
                    else "Small change"
                    if psi < 0.2
                    else "Medium change"
                    if psi < 0.25
                    else "Large change"
                ),
            },
        )

    @handle_errors(reraise=True, notify=False)
    def detect_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: DriftMethod = DriftMethod.KL_DIVERGENCE,
        threshold: Optional[float] = None,
    ) -> List[DriftResult]:
        """
        Detect drift across multiple columns.

        Args:
            reference_data: Reference dataset
            current_data: Current dataset to compare
            columns: Columns to check (None = all numeric)
            method: Drift detection method
            threshold: Custom threshold (None = use defaults)

        Returns:
            List of DriftResult objects
        """
        if columns is None:
            # Only check numeric columns
            columns = reference_data.select_dtypes(include=[np.number]).columns.tolist()

        results = []

        for col in columns:
            if col not in reference_data.columns or col not in current_data.columns:
                logger.warning(f"Column '{col}' not found in both datasets")
                continue

            try:
                if method == DriftMethod.KL_DIVERGENCE:
                    thresh = threshold if threshold is not None else 0.1
                    result = self.detect_drift_kl_divergence(
                        reference_data, current_data, col, threshold=thresh
                    )
                elif method == DriftMethod.KS_TEST:
                    thresh = threshold if threshold is not None else 0.05
                    result = self.detect_drift_ks_test(
                        reference_data, current_data, col, threshold=thresh
                    )
                elif method == DriftMethod.PSI:
                    thresh = threshold if threshold is not None else 0.2
                    result = self.detect_drift_psi(
                        reference_data, current_data, col, threshold=thresh
                    )
                else:
                    raise ValueError(f"Unknown drift method: {method}")

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to detect drift for column '{col}': {e}")

        return results

    def profile_nba_player_stats(self, df: pd.DataFrame) -> DataProfile:
        """
        Profile NBA player statistics with domain-specific checks.

        Args:
            df: DataFrame with player stats

        Returns:
            DataProfile with NBA-specific insights
        """
        profile = self.profile(df, dataset_name="nba_player_stats")

        # Add NBA-specific validations
        expected_columns = ["ppg", "rpg", "apg", "fg_pct", "games_played"]
        missing_cols = [col for col in expected_columns if col not in df.columns]

        if missing_cols:
            logger.warning(f"Missing expected NBA columns: {missing_cols}")

        return profile

    def profile_nba_game_data(self, df: pd.DataFrame) -> DataProfile:
        """
        Profile NBA game data with domain-specific checks.

        Args:
            df: DataFrame with game data

        Returns:
            DataProfile with NBA-specific insights
        """
        profile = self.profile(df, dataset_name="nba_game_data")

        # Add NBA-specific validations
        expected_columns = ["home_score", "away_score", "date", "home_team", "away_team"]
        missing_cols = [col for col in expected_columns if col not in df.columns]

        if missing_cols:
            logger.warning(f"Missing expected NBA columns: {missing_cols}")

        return profile

    def profile_nba_team_data(self, df: pd.DataFrame) -> DataProfile:
        """
        Profile NBA team data with domain-specific checks.

        Args:
            df: DataFrame with team data

        Returns:
            DataProfile with NBA-specific insights
        """
        profile = self.profile(df, dataset_name="nba_team_data")

        # Add NBA-specific validations
        expected_columns = ["team_name", "wins", "losses", "win_pct", "conference"]
        missing_cols = [col for col in expected_columns if col not in df.columns]

        if missing_cols:
            logger.warning(f"Missing expected NBA columns: {missing_cols}")

        return profile

    def _track_metrics(self, profile: DataProfile) -> None:
        """Track profiling metrics with Week 1 monitoring"""
        try:
            monitor = get_health_monitor()
            dataset = profile.dataset_name

            monitor.track_metric(f"profiling.{dataset}.row_count", profile.row_count)
            monitor.track_metric(f"profiling.{dataset}.column_count", profile.column_count)
            monitor.track_metric(f"profiling.{dataset}.memory_mb", profile.memory_usage_mb)
            monitor.track_metric(f"profiling.{dataset}.quality_score", profile.quality_score)

        except Exception as e:
            logger.error(f"Failed to track metrics: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get profiling statistics"""
        if not self.profile_history:
            return {
                "total_profiles": 0,
                "avg_quality_score": 0.0,
            }

        return {
            "total_profiles": len(self.profile_history),
            "avg_quality_score": np.mean([p.quality_score for p in self.profile_history]),
            "datasets_profiled": list(set(p.dataset_name for p in self.profile_history)),
        }
