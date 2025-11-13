"""
Matching Methods for Causal Inference (Agent 18, Module 2)

Matching estimators for treatment effects:
- Propensity Score Matching (PSM)
- Kernel Matching
- Nearest Neighbor Matching
- Covariate Matching
- Mahalanobis Distance Matching
- Balance diagnostics

NBA Applications:
- Coaching change effects
- Trade impact analysis
- Playing time effects
- Training regimen effects
- Injury recovery comparisons

Integrates with:
- causal_inference: Treatment effect estimation
- panel_data: Panel matching
- ml_bridge: ML for propensity scores
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from enum import Enum

import numpy as np
from scipy import stats
from scipy.spatial.distance import cdist, mahalanobis

logger = logging.getLogger(__name__)

# Try to import sklearn (optional)
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, matching methods limited")


class MatchingMethod(Enum):
    """Matching method types"""

    PROPENSITY_SCORE = "propensity_score"
    NEAREST_NEIGHBOR = "nearest_neighbor"
    KERNEL = "kernel"
    RADIUS = "radius"
    MAHALANOBIS = "mahalanobis"
    COVARIATE = "covariate"


class KernelType(Enum):
    """Kernel function types"""

    GAUSSIAN = "gaussian"
    EPANECHNIKOV = "epanechnikov"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"


@dataclass
class MatchingConfig:
    """Configuration for matching estimators"""

    method: MatchingMethod = MatchingMethod.PROPENSITY_SCORE

    # Propensity score settings
    ps_model: str = "logistic"  # logistic, probit, ml
    ps_caliper: Optional[float] = 0.1  # Maximum distance for matches

    # Nearest neighbor settings
    n_neighbors: int = 1
    replace: bool = False  # Matching with replacement

    # Kernel settings
    kernel_type: KernelType = KernelType.GAUSSIAN
    bandwidth: float = 0.1

    # Radius matching
    radius: float = 0.1

    # Common support
    enforce_common_support: bool = True
    trim_percentage: float = 0.01  # Trim top/bottom %


@dataclass
class MatchingResult:
    """Results from matching analysis"""

    # Treatment effect estimates
    att: float  # Average Treatment Effect on Treated
    ate: Optional[float] = None  # Average Treatment Effect
    atc: Optional[float] = None  # Average Treatment Effect on Controls

    # Standard errors
    se_att: Optional[float] = None
    se_ate: Optional[float] = None

    # Matching statistics
    n_treated: int = 0
    n_control: int = 0
    n_matched: int = 0

    # Balance statistics
    balance_before: Optional[Dict[str, float]] = None
    balance_after: Optional[Dict[str, float]] = None

    # Matched pairs
    matched_indices: Optional[Dict[int, List[int]]] = (
        None  # treated_idx -> [control_idx]
    )

    # Propensity scores
    propensity_scores: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "att": self.att,
            "ate": self.ate,
            "atc": self.atc,
            "se_att": self.se_att,
            "n_treated": self.n_treated,
            "n_control": self.n_control,
            "n_matched": self.n_matched,
            "has_balance_stats": self.balance_before is not None,
        }


class PropensityScoreMatcher:
    """
    Propensity Score Matching (PSM).

    Two-step procedure:
    1. Estimate propensity scores P(D=1|X) using logistic regression
    2. Match treated and control units with similar propensity scores

    Features:
    - Caliper matching (maximum distance)
    - Common support enforcement
    - Balance checking
    - Various matching algorithms (NN, kernel, radius)
    """

    def __init__(self, config: Optional[MatchingConfig] = None):
        """Initialize PSM"""
        self.config = config or MatchingConfig()
        self.propensity_model = None
        self.is_fitted = False

        logger.info("PropensityScoreMatcher initialized")

    def estimate_propensity_scores(
        self, X: np.ndarray, treatment: np.ndarray
    ) -> np.ndarray:
        """
        Estimate propensity scores.

        Args:
            X: Covariates (n_samples, n_features)
            treatment: Treatment indicator (n_samples,)

        Returns:
            Propensity scores (n_samples,)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for propensity score estimation")

        # Fit logistic regression
        self.propensity_model = LogisticRegression(max_iter=1000, random_state=42)
        self.propensity_model.fit(X, treatment)

        # Predict propensity scores
        ps = self.propensity_model.predict_proba(X)[:, 1]

        logger.info(
            f"Propensity scores: mean={ps.mean():.3f}, min={ps.min():.3f}, max={ps.max():.3f}"
        )

        return ps

    def enforce_common_support(
        self, ps: np.ndarray, treatment: np.ndarray
    ) -> np.ndarray:
        """
        Enforce common support (overlap) requirement.

        Args:
            ps: Propensity scores
            treatment: Treatment indicator

        Returns:
            Boolean mask for common support region
        """
        ps_treated = ps[treatment == 1]
        ps_control = ps[treatment == 0]

        # Find overlap region
        min_treated = np.min(ps_treated)
        max_treated = np.max(ps_treated)
        min_control = np.min(ps_control)
        max_control = np.max(ps_control)

        lower_bound = max(min_treated, min_control)
        upper_bound = min(max_treated, max_control)

        # Trim tails if specified
        if self.config.trim_percentage > 0:
            trim = self.config.trim_percentage
            lower_bound = max(lower_bound, np.percentile(ps, trim * 100))
            upper_bound = min(upper_bound, np.percentile(ps, (1 - trim) * 100))

        common_support = (ps >= lower_bound) & (ps <= upper_bound)

        n_dropped = np.sum(~common_support)
        logger.info(f"Common support: dropped {n_dropped} observations")

        return common_support

    def match_nearest_neighbor(
        self, ps: np.ndarray, treatment: np.ndarray, outcome: np.ndarray
    ) -> MatchingResult:
        """
        Nearest neighbor matching on propensity scores.

        Args:
            ps: Propensity scores
            treatment: Treatment indicator
            outcome: Outcome variable

        Returns:
            MatchingResult
        """
        treated_idx = np.where(treatment == 1)[0]
        control_idx = np.where(treatment == 0)[0]

        ps_treated = ps[treated_idx]
        ps_control = ps[control_idx]

        # Find matches
        matched_indices = {}
        used_controls = set()

        for i, t_idx in enumerate(treated_idx):
            # Calculate distances
            distances = np.abs(ps_control - ps_treated[i])

            # Apply caliper if specified
            if self.config.ps_caliper is not None:
                valid = distances <= self.config.ps_caliper
                if not np.any(valid):
                    continue  # No valid matches within caliper
                distances = np.where(valid, distances, np.inf)

            # Find k nearest neighbors
            k = self.config.n_neighbors
            sorted_idx = np.argsort(distances)

            matches = []
            for idx in sorted_idx:
                if len(matches) >= k:
                    break

                c_idx = control_idx[idx]

                # Check if already used (if without replacement)
                if not self.config.replace and c_idx in used_controls:
                    continue

                if distances[idx] < np.inf:
                    matches.append(c_idx)
                    used_controls.add(c_idx)

            if matches:
                matched_indices[t_idx] = matches

        # Calculate ATT
        att_values = []
        for t_idx, c_indices in matched_indices.items():
            treated_outcome = outcome[t_idx]
            control_outcomes = outcome[c_indices]
            att_values.append(treated_outcome - np.mean(control_outcomes))

        att = np.mean(att_values) if att_values else 0.0
        se_att = (
            np.std(att_values) / np.sqrt(len(att_values))
            if len(att_values) > 1
            else None
        )

        result = MatchingResult(
            att=att,
            se_att=se_att,
            n_treated=len(treated_idx),
            n_control=len(control_idx),
            n_matched=len(matched_indices),
            matched_indices=matched_indices,
            propensity_scores=ps,
        )

        logger.info(f"NN Matching: ATT={att:.4f}, SE={se_att:.4f if se_att else 0:.4f}")
        logger.info(f"Matched {len(matched_indices)}/{len(treated_idx)} treated units")

        return result

    def match_kernel(
        self, ps: np.ndarray, treatment: np.ndarray, outcome: np.ndarray
    ) -> MatchingResult:
        """
        Kernel matching on propensity scores.

        Weighted average of all controls, with weights based on kernel function.

        Args:
            ps: Propensity scores
            treatment: Treatment indicator
            outcome: Outcome variable

        Returns:
            MatchingResult
        """
        treated_idx = np.where(treatment == 1)[0]
        control_idx = np.where(treatment == 0)[0]

        ps_treated = ps[treated_idx]
        ps_control = ps[control_idx]

        # Calculate kernel weights
        att_values = []

        for i, t_idx in enumerate(treated_idx):
            # Distances to all controls
            distances = np.abs(ps_control - ps_treated[i])

            # Kernel weights
            weights = self._kernel_function(distances / self.config.bandwidth)
            weights = weights / np.sum(weights) if np.sum(weights) > 0 else weights

            # Weighted average of control outcomes
            treated_outcome = outcome[t_idx]
            weighted_control = np.sum(weights * outcome[control_idx])

            att_values.append(treated_outcome - weighted_control)

        att = np.mean(att_values) if att_values else 0.0
        se_att = (
            np.std(att_values) / np.sqrt(len(att_values))
            if len(att_values) > 1
            else None
        )

        result = MatchingResult(
            att=att,
            se_att=se_att,
            n_treated=len(treated_idx),
            n_control=len(control_idx),
            n_matched=len(treated_idx),  # All treated are matched
            propensity_scores=ps,
        )

        logger.info(
            f"Kernel Matching: ATT={att:.4f}, SE={se_att:.4f if se_att else 0:.4f}"
        )

        return result

    def _kernel_function(self, u: np.ndarray) -> np.ndarray:
        """Kernel function"""
        if self.config.kernel_type == KernelType.GAUSSIAN:
            return np.exp(-0.5 * u**2) / np.sqrt(2 * np.pi)
        elif self.config.kernel_type == KernelType.EPANECHNIKOV:
            return np.where(np.abs(u) <= 1, 0.75 * (1 - u**2), 0)
        elif self.config.kernel_type == KernelType.UNIFORM:
            return np.where(np.abs(u) <= 1, 0.5, 0)
        elif self.config.kernel_type == KernelType.TRIANGULAR:
            return np.where(np.abs(u) <= 1, 1 - np.abs(u), 0)
        else:
            return np.exp(-0.5 * u**2) / np.sqrt(2 * np.pi)

    def match(
        self, X: np.ndarray, treatment: np.ndarray, outcome: np.ndarray
    ) -> MatchingResult:
        """
        Perform propensity score matching.

        Args:
            X: Covariates
            treatment: Treatment indicator
            outcome: Outcome variable

        Returns:
            MatchingResult
        """
        # Estimate propensity scores
        ps = self.estimate_propensity_scores(X, treatment)

        # Enforce common support
        if self.config.enforce_common_support:
            common_support = self.enforce_common_support(ps, treatment)
            X = X[common_support]
            treatment = treatment[common_support]
            outcome = outcome[common_support]
            ps = ps[common_support]

        # Match based on method
        if (
            self.config.method == MatchingMethod.NEAREST_NEIGHBOR
            or self.config.method == MatchingMethod.PROPENSITY_SCORE
        ):
            result = self.match_nearest_neighbor(ps, treatment, outcome)
        elif self.config.method == MatchingMethod.KERNEL:
            result = self.match_kernel(ps, treatment, outcome)
        else:
            result = self.match_nearest_neighbor(ps, treatment, outcome)

        # Calculate balance
        result.balance_before = self.calculate_balance(X, treatment, None)
        if result.matched_indices:
            result.balance_after = self.calculate_balance_after_matching(
                X, treatment, result.matched_indices
            )

        self.is_fitted = True

        return result

    def calculate_balance(
        self, X: np.ndarray, treatment: np.ndarray, weights: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Calculate covariate balance (standardized mean differences).

        Args:
            X: Covariates
            treatment: Treatment indicator
            weights: Optional weights

        Returns:
            Dictionary of standardized mean differences by feature
        """
        treated_mask = treatment == 1
        control_mask = treatment == 0

        balance = {}

        for j in range(X.shape[1]):
            if weights is not None:
                mean_treated = np.average(
                    X[treated_mask, j], weights=weights[treated_mask]
                )
                mean_control = np.average(
                    X[control_mask, j], weights=weights[control_mask]
                )
                var_treated = np.average(
                    (X[treated_mask, j] - mean_treated) ** 2,
                    weights=weights[treated_mask],
                )
                var_control = np.average(
                    (X[control_mask, j] - mean_control) ** 2,
                    weights=weights[control_mask],
                )
            else:
                mean_treated = np.mean(X[treated_mask, j])
                mean_control = np.mean(X[control_mask, j])
                var_treated = np.var(X[treated_mask, j])
                var_control = np.var(X[control_mask, j])

            pooled_std = np.sqrt((var_treated + var_control) / 2)
            smd = (mean_treated - mean_control) / pooled_std if pooled_std > 0 else 0.0

            balance[f"feature_{j}"] = abs(smd)

        return balance

    def calculate_balance_after_matching(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        matched_indices: Dict[int, List[int]],
    ) -> Dict[str, float]:
        """Calculate balance after matching"""
        # Extract matched sample
        treated_idx = list(matched_indices.keys())
        control_idx = [idx for indices in matched_indices.values() for idx in indices]

        X_matched_treated = X[treated_idx]
        X_matched_control = X[control_idx]

        balance = {}

        for j in range(X.shape[1]):
            mean_treated = np.mean(X_matched_treated[:, j])
            mean_control = np.mean(X_matched_control[:, j])
            var_treated = np.var(X_matched_treated[:, j])
            var_control = np.var(X_matched_control[:, j])

            pooled_std = np.sqrt((var_treated + var_control) / 2)
            smd = (mean_treated - mean_control) / pooled_std if pooled_std > 0 else 0.0

            balance[f"feature_{j}"] = abs(smd)

        return balance


class MahalanobisDistanceMatcher:
    """
    Mahalanobis distance matching.

    Matches on weighted distance that accounts for covariance structure.
    More robust to scale differences than Euclidean distance.
    """

    def __init__(self, n_neighbors: int = 1, caliper: Optional[float] = None):
        """Initialize Mahalanobis matcher"""
        self.n_neighbors = n_neighbors
        self.caliper = caliper
        self.cov_inv_ = None

        logger.info("MahalanobisDistanceMatcher initialized")

    def match(
        self, X: np.ndarray, treatment: np.ndarray, outcome: np.ndarray
    ) -> MatchingResult:
        """
        Match using Mahalanobis distance.

        Args:
            X: Covariates
            treatment: Treatment indicator
            outcome: Outcome variable

        Returns:
            MatchingResult
        """
        treated_idx = np.where(treatment == 1)[0]
        control_idx = np.where(treatment == 0)[0]

        # Compute covariance matrix
        cov = np.cov(X.T)
        try:
            self.cov_inv_ = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            # Singular matrix, use pseudo-inverse
            self.cov_inv_ = np.linalg.pinv(cov)

        # Find matches
        matched_indices = {}

        for t_idx in treated_idx:
            # Calculate Mahalanobis distances to all controls
            distances = np.array(
                [
                    mahalanobis(X[t_idx], X[c_idx], self.cov_inv_)
                    for c_idx in control_idx
                ]
            )

            # Apply caliper if specified
            if self.caliper is not None:
                valid = distances <= self.caliper
                if not np.any(valid):
                    continue
                distances = np.where(valid, distances, np.inf)

            # Find nearest neighbors
            sorted_idx = np.argsort(distances)
            matches = [
                control_idx[idx]
                for idx in sorted_idx[: self.n_neighbors]
                if distances[idx] < np.inf
            ]

            if matches:
                matched_indices[t_idx] = matches

        # Calculate ATT
        att_values = []
        for t_idx, c_indices in matched_indices.items():
            treated_outcome = outcome[t_idx]
            control_outcomes = outcome[c_indices]
            att_values.append(treated_outcome - np.mean(control_outcomes))

        att = np.mean(att_values) if att_values else 0.0
        se_att = (
            np.std(att_values) / np.sqrt(len(att_values))
            if len(att_values) > 1
            else None
        )

        result = MatchingResult(
            att=att,
            se_att=se_att,
            n_treated=len(treated_idx),
            n_control=len(control_idx),
            n_matched=len(matched_indices),
            matched_indices=matched_indices,
        )

        logger.info(
            f"Mahalanobis Matching: ATT={att:.4f}, SE={se_att:.4f if se_att else 0:.4f}"
        )
        logger.info(f"Matched {len(matched_indices)}/{len(treated_idx)} treated units")

        return result


def estimate_treatment_effect(
    X: np.ndarray,
    treatment: np.ndarray,
    outcome: np.ndarray,
    method: MatchingMethod = MatchingMethod.PROPENSITY_SCORE,
    config: Optional[MatchingConfig] = None,
) -> MatchingResult:
    """
    Convenience function to estimate treatment effects using matching.

    Args:
        X: Covariates
        treatment: Treatment indicator (0/1)
        outcome: Outcome variable
        method: Matching method
        config: Optional configuration

    Returns:
        MatchingResult with treatment effect estimates
    """
    if config is None:
        config = MatchingConfig(method=method)
    else:
        config.method = method

    if method in [
        MatchingMethod.PROPENSITY_SCORE,
        MatchingMethod.NEAREST_NEIGHBOR,
        MatchingMethod.KERNEL,
    ]:
        matcher = PropensityScoreMatcher(config)
        return matcher.match(X, treatment, outcome)

    elif method == MatchingMethod.MAHALANOBIS:
        matcher = MahalanobisDistanceMatcher(
            n_neighbors=config.n_neighbors, caliper=config.ps_caliper
        )
        return matcher.match(X, treatment, outcome)

    else:
        raise ValueError(f"Unknown matching method: {method}")


__all__ = [
    "MatchingMethod",
    "KernelType",
    "MatchingConfig",
    "MatchingResult",
    "PropensityScoreMatcher",
    "MahalanobisDistanceMatcher",
    "estimate_treatment_effect",
]
