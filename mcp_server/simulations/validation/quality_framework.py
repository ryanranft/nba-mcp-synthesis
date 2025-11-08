"""
Simulation Quality Framework (Agent 10, Module 2)

Provides quality metrics, realism scoring, and variance analysis
for NBA game simulations.

Integrates with:
- Agent 2 (Monitoring): Track quality metrics
- Agent 4 (Data Validation): Historical data comparison
- Agent 9 (Performance): Profile quality checks
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for simulation results"""
    realism_score: float  # 0.0 to 1.0
    variance_score: float  # Measure of appropriate variability
    historical_alignment: float  # Match with historical data
    anomaly_count: int  # Number of detected anomalies
    computed_at: datetime = field(default_factory=datetime.now)

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """Check if metrics indicate high quality"""
        return (self.realism_score >= threshold and
                self.historical_alignment >= threshold and
                self.anomaly_count == 0)


@dataclass
class HistoricalStats:
    """Historical statistics for comparison"""
    stat_name: str
    mean: float
    std: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_50: float
    percentile_75: float

    def is_within_range(self, value: float, std_devs: float = 3.0) -> bool:
        """Check if value is within expected range"""
        lower_bound = self.mean - (std_devs * self.std)
        upper_bound = self.mean + (std_devs * self.std)
        return lower_bound <= value <= upper_bound


class SimulationQualityChecker:
    """
    Checks simulation quality using realism scores, variance analysis,
    and historical data validation.

    Features:
    - Realism scoring (0.0 to 1.0)
    - Variance analysis
    - Historical alignment checks
    - Anomaly detection
    """

    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize quality checker.

        Args:
            historical_data: Historical game data for comparison
        """
        self.historical_data = historical_data
        self.historical_stats: Dict[str, HistoricalStats] = {}
        self.quality_checks_performed = 0

        if historical_data is not None:
            self._compute_historical_stats()

    def _compute_historical_stats(self):
        """Compute statistical summaries from historical data"""
        if self.historical_data is None or self.historical_data.empty:
            return

        # Compute stats for key metrics
        for column in self.historical_data.columns:
            if pd.api.types.is_numeric_dtype(self.historical_data[column]):
                data = self.historical_data[column].dropna()
                if len(data) > 0:
                    self.historical_stats[column] = HistoricalStats(
                        stat_name=column,
                        mean=float(data.mean()),
                        std=float(data.std()),
                        min_value=float(data.min()),
                        max_value=float(data.max()),
                        percentile_25=float(data.quantile(0.25)),
                        percentile_50=float(data.quantile(0.50)),
                        percentile_75=float(data.quantile(0.75))
                    )

    def compute_realism_score(
        self,
        simulated_data: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute realism score by comparing simulation to historical data.

        Args:
            simulated_data: Dict of stat_name -> value
            weights: Optional weights for each stat

        Returns:
            Realism score between 0.0 and 1.0
        """
        if not self.historical_stats:
            logger.warning("No historical stats available for realism scoring")
            return 0.5  # Neutral score

        if weights is None:
            weights = {k: 1.0 for k in simulated_data.keys()}

        scores = []
        total_weight = 0.0

        for stat_name, sim_value in simulated_data.items():
            if stat_name in self.historical_stats:
                hist_stat = self.historical_stats[stat_name]
                weight = weights.get(stat_name, 1.0)

                # Compute how many std devs away from mean
                if hist_stat.std > 0:
                    z_score = abs((sim_value - hist_stat.mean) / hist_stat.std)
                    # Convert z-score to similarity score (0-1)
                    # z=0 → score=1.0, z=3 → score≈0.0
                    similarity = max(0.0, 1.0 - (z_score / 3.0))
                    scores.append(similarity * weight)
                    total_weight += weight
                else:
                    # If std=0, check exact match
                    if sim_value == hist_stat.mean:
                        scores.append(1.0 * weight)
                        total_weight += weight

        if total_weight == 0:
            return 0.5

        realism_score = sum(scores) / total_weight
        self.quality_checks_performed += 1

        return realism_score

    def analyze_variance(
        self,
        simulation_runs: List[Dict[str, float]],
        expected_variance: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Analyze variance across multiple simulation runs.

        Args:
            simulation_runs: List of simulation results
            expected_variance: Expected variance for each stat

        Returns:
            Variance score between 0.0 and 1.0
        """
        if len(simulation_runs) < 2:
            return 0.5  # Need multiple runs for variance

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(simulation_runs)

        variance_scores = []

        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                observed_var = df[column].var()

                # Get expected variance from historical or provided
                if expected_variance and column in expected_variance:
                    expected_var = expected_variance[column]
                elif column in self.historical_stats:
                    expected_var = self.historical_stats[column].std ** 2
                else:
                    continue

                if expected_var == 0:
                    if observed_var == 0:
                        variance_scores.append(1.0)
                    else:
                        variance_scores.append(0.5)
                else:
                    # Compare observed to expected variance
                    # Closer to 1.0 is better
                    ratio = observed_var / expected_var
                    # Score is higher when ratio is close to 1.0
                    score = 1.0 - min(abs(ratio - 1.0), 1.0)
                    variance_scores.append(score)

        if not variance_scores:
            return 0.5

        self.quality_checks_performed += 1
        return sum(variance_scores) / len(variance_scores)

    def validate_historical_alignment(
        self,
        simulated_stats: Dict[str, float],
        std_devs_threshold: float = 3.0
    ) -> Tuple[float, List[str]]:
        """
        Validate that simulated stats align with historical ranges.

        Args:
            simulated_stats: Simulated statistics
            std_devs_threshold: Number of std devs for outlier detection

        Returns:
            (alignment_score, list_of_anomalies)
        """
        if not self.historical_stats:
            return 0.5, []

        in_range_count = 0
        total_count = 0
        anomalies = []

        for stat_name, sim_value in simulated_stats.items():
            if stat_name in self.historical_stats:
                hist_stat = self.historical_stats[stat_name]
                total_count += 1

                if hist_stat.is_within_range(sim_value, std_devs_threshold):
                    in_range_count += 1
                else:
                    anomalies.append(f"{stat_name}: {sim_value} (expected {hist_stat.mean:.2f} ± {hist_stat.std:.2f})")

        if total_count == 0:
            return 0.5, []

        alignment_score = in_range_count / total_count
        self.quality_checks_performed += 1

        return alignment_score, anomalies

    def detect_anomalies(
        self,
        simulated_data: Dict[str, float],
        threshold: float = 3.0
    ) -> List[str]:
        """
        Detect statistical anomalies in simulated data.

        Args:
            simulated_data: Simulated statistics
            threshold: Z-score threshold for anomaly

        Returns:
            List of detected anomalies
        """
        anomalies = []

        for stat_name, value in simulated_data.items():
            if stat_name in self.historical_stats:
                hist_stat = self.historical_stats[stat_name]

                if hist_stat.std > 0:
                    z_score = abs((value - hist_stat.mean) / hist_stat.std)
                    if z_score > threshold:
                        anomalies.append(
                            f"{stat_name}: z-score={z_score:.2f} (value={value}, mean={hist_stat.mean:.2f})"
                        )

        self.quality_checks_performed += 1
        return anomalies

    def compute_quality_metrics(
        self,
        simulated_data: Dict[str, float],
        simulation_runs: Optional[List[Dict[str, float]]] = None
    ) -> QualityMetrics:
        """
        Compute comprehensive quality metrics for simulation.

        Args:
            simulated_data: Single simulation result
            simulation_runs: Multiple runs for variance analysis

        Returns:
            QualityMetrics object
        """
        # Compute realism score
        realism_score = self.compute_realism_score(simulated_data)

        # Compute variance score if multiple runs provided
        if simulation_runs and len(simulation_runs) > 1:
            variance_score = self.analyze_variance(simulation_runs)
        else:
            variance_score = 0.5  # Neutral

        # Validate historical alignment
        alignment_score, anomalies = self.validate_historical_alignment(simulated_data)

        return QualityMetrics(
            realism_score=realism_score,
            variance_score=variance_score,
            historical_alignment=alignment_score,
            anomaly_count=len(anomalies)
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get quality checker statistics.

        Returns:
            Dict with statistics
        """
        return {
            'total_checks': self.quality_checks_performed,
            'historical_stats_available': len(self.historical_stats),
            'has_historical_data': self.historical_data is not None
        }
