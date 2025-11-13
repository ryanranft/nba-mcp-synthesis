"""
Feature Engineering for ML Models (Agent 17, Module 4)

Advanced feature creation for hybrid models:
- Time series features (lags, rolling stats, differences)
- Interaction features (pairwise, higher-order)
- Polynomial features
- Domain-specific NBA features
- Automated feature generation
- Feature selection and importance

Integrates with:
- hybrid_models: Provide features for ML
- panel_data: Player/team panel features
- time_series: Temporal feature engineering
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import sklearn (optional)
try:
    from sklearn.preprocessing import PolynomialFeatures, StandardScaler, MinMaxScaler
    from sklearn.feature_selection import (
        SelectKBest,
        f_regression,
        mutual_info_regression,
        RFE,
    )

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, feature engineering limited")


@dataclass
class FeatureConfig:
    """Configuration for feature engineering"""

    # Time series features
    create_lags: bool = True
    lag_periods: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 10])
    create_rolling: bool = True
    rolling_windows: List[int] = field(default_factory=lambda: [3, 5, 10, 20])
    create_differences: bool = True

    # Interaction features
    create_interactions: bool = True
    interaction_degree: int = 2  # Pairwise

    # Polynomial features
    create_polynomials: bool = False
    polynomial_degree: int = 2

    # NBA-specific
    create_efficiency_metrics: bool = True
    create_advanced_stats: bool = True
    create_pace_adjusted: bool = True

    # Feature selection
    select_features: bool = False
    n_features_to_select: Optional[int] = None
    selection_method: str = "f_regression"  # f_regression, mutual_info, rfe

    # Scaling
    scale_features: bool = True
    scaler_type: str = "standard"  # standard, minmax


class TimeSeriesFeatureCreator:
    """
    Create time series features.

    Features:
    - Lag features (past values)
    - Rolling statistics (mean, std, min, max)
    - Differences (first, second order)
    - Rate of change
    - Exponential moving averages
    """

    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize time series feature creator"""
        self.config = config or FeatureConfig()
        logger.info("TimeSeriesFeatureCreator initialized")

    def create_lag_features(
        self,
        data: Union[np.ndarray, pd.Series],
        lag_periods: Optional[List[int]] = None,
        fill_value: float = 0.0,
    ) -> np.ndarray:
        """
        Create lag features.

        Args:
            data: Time series data
            lag_periods: List of lag periods
            fill_value: Value for initial NaNs

        Returns:
            Array of lag features (n_samples, n_lags)
        """
        if lag_periods is None:
            lag_periods = self.config.lag_periods

        if isinstance(data, pd.Series):
            data = data.values

        lags = []
        for lag in lag_periods:
            lagged = np.roll(data, lag)
            lagged[:lag] = fill_value  # Fill initial values
            lags.append(lagged)

        return np.column_stack(lags)

    def create_rolling_features(
        self,
        data: Union[np.ndarray, pd.Series],
        windows: Optional[List[int]] = None,
        functions: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Create rolling window features.

        Args:
            data: Time series data
            windows: Window sizes
            functions: Functions to apply ('mean', 'std', 'min', 'max')

        Returns:
            Array of rolling features
        """
        if windows is None:
            windows = self.config.rolling_windows

        if functions is None:
            functions = ["mean", "std"]

        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        features = []

        for window in windows:
            for func in functions:
                if func == "mean":
                    feat = data.rolling(window=window, min_periods=1).mean().values
                elif func == "std":
                    feat = (
                        data.rolling(window=window, min_periods=1)
                        .std()
                        .fillna(0)
                        .values
                    )
                elif func == "min":
                    feat = data.rolling(window=window, min_periods=1).min().values
                elif func == "max":
                    feat = data.rolling(window=window, min_periods=1).max().values
                else:
                    continue

                features.append(feat)

        return np.column_stack(features)

    def create_difference_features(
        self, data: Union[np.ndarray, pd.Series], orders: List[int] = [1, 2]
    ) -> np.ndarray:
        """
        Create difference features.

        Args:
            data: Time series data
            orders: Difference orders (1=first difference, 2=second)

        Returns:
            Array of difference features
        """
        if isinstance(data, pd.Series):
            data = data.values

        differences = []

        for order in orders:
            diff = np.diff(data, n=order)
            # Pad with zeros to maintain length
            diff = np.concatenate([np.zeros(order), diff])
            differences.append(diff)

        return np.column_stack(differences)

    def create_ewm_features(
        self, data: Union[np.ndarray, pd.Series], spans: List[int] = [3, 10, 20]
    ) -> np.ndarray:
        """
        Create exponential weighted moving average features.

        Args:
            data: Time series data
            spans: EWM spans

        Returns:
            Array of EWM features
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        features = []

        for span in spans:
            ewm = data.ewm(span=span, min_periods=1).mean().values
            features.append(ewm)

        return np.column_stack(features)

    def create_all_ts_features(
        self,
        data: Union[np.ndarray, pd.Series],
        feature_names: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create all time series features.

        Args:
            data: Time series data
            feature_names: Base feature names

        Returns:
            (features_array, feature_names)
        """
        all_features = [
            (
                data.reshape(-1, 1)
                if isinstance(data, np.ndarray)
                else data.values.reshape(-1, 1)
            )
        ]
        names = [feature_names[0] if feature_names else "original"]

        # Lags
        if self.config.create_lags:
            lags = self.create_lag_features(data)
            all_features.append(lags)
            for i, lag in enumerate(self.config.lag_periods):
                names.append(f"lag_{lag}")

        # Rolling
        if self.config.create_rolling:
            rolling = self.create_rolling_features(data)
            all_features.append(rolling)
            for window in self.config.rolling_windows:
                for func in ["mean", "std"]:
                    names.append(f"rolling_{window}_{func}")

        # Differences
        if self.config.create_differences:
            diffs = self.create_difference_features(data)
            all_features.append(diffs)
            names.extend(["diff_1", "diff_2"])

        # Concatenate
        features = np.hstack(all_features)

        return features, names


class InteractionFeatureCreator:
    """
    Create interaction features.

    Features:
    - Pairwise products (X1 * X2)
    - Higher-order interactions
    - Ratio features (X1 / X2)
    - Domain-specific interactions
    """

    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize interaction feature creator"""
        self.config = config or FeatureConfig()
        logger.info("InteractionFeatureCreator initialized")

    def create_pairwise_products(
        self, X: np.ndarray, feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create pairwise product interactions.

        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Feature names

        Returns:
            (interaction_features, interaction_names)
        """
        n_samples, n_features = X.shape
        interactions = []
        interaction_names = []

        for i in range(n_features):
            for j in range(i + 1, n_features):
                interaction = X[:, i] * X[:, j]
                interactions.append(interaction)

                if feature_names:
                    interaction_names.append(f"{feature_names[i]}_x_{feature_names[j]}")
                else:
                    interaction_names.append(f"X{i}_x_X{j}")

        if interactions:
            interactions = np.column_stack(interactions)
        else:
            interactions = np.empty((n_samples, 0))

        return interactions, interaction_names

    def create_ratio_features(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        epsilon: float = 1e-8,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create ratio features (X1 / X2).

        Args:
            X: Feature matrix
            feature_names: Feature names
            epsilon: Small value to avoid division by zero

        Returns:
            (ratio_features, ratio_names)
        """
        n_samples, n_features = X.shape
        ratios = []
        ratio_names = []

        for i in range(n_features):
            for j in range(n_features):
                if i != j:
                    # Avoid division by zero
                    ratio = X[:, i] / (X[:, j] + epsilon)
                    ratios.append(ratio)

                    if feature_names:
                        ratio_names.append(f"{feature_names[i]}_div_{feature_names[j]}")
                    else:
                        ratio_names.append(f"X{i}_div_X{j}")

        if ratios:
            ratios = np.column_stack(ratios)
        else:
            ratios = np.empty((n_samples, 0))

        return ratios, ratio_names


class NBAFeatureCreator:
    """
    Create NBA-specific domain features.

    Features:
    - Efficiency metrics (PER approximation, TS%, USG%)
    - Advanced stats (BPM components, VORP proxies)
    - Pace adjustments
    - Matchup features
    """

    def __init__(self):
        """Initialize NBA feature creator"""
        logger.info("NBAFeatureCreator initialized")

    def create_true_shooting_pct(
        self,
        points: np.ndarray,
        fga: np.ndarray,
        fta: np.ndarray,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        Calculate True Shooting %.

        TS% = PTS / (2 * (FGA + 0.44 * FTA))

        Args:
            points: Points scored
            fga: Field goal attempts
            fta: Free throw attempts
            epsilon: Avoid division by zero

        Returns:
            True shooting percentage
        """
        denominator = 2 * (fga + 0.44 * fta) + epsilon
        ts_pct = points / denominator
        return np.clip(ts_pct, 0, 1.5)  # Cap at 150%

    def create_usage_rate(
        self,
        fga: np.ndarray,
        fta: np.ndarray,
        tov: np.ndarray,
        minutes: np.ndarray,
        team_minutes: np.ndarray,
        team_fga: np.ndarray,
        team_fta: np.ndarray,
        team_tov: np.ndarray,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        Calculate Usage Rate.

        USG% = 100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) /
                     (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))

        Args:
            fga: Player FGA
            fta: Player FTA
            tov: Player turnovers
            minutes: Player minutes
            team_minutes: Team minutes
            team_fga: Team FGA
            team_fta: Team FTA
            team_tov: Team turnovers
            epsilon: Avoid division by zero

        Returns:
            Usage rate
        """
        player_possessions = fga + 0.44 * fta + tov
        team_possessions = team_fga + 0.44 * team_fta + team_tov + epsilon

        usg = (
            100
            * (player_possessions * (team_minutes / 5))
            / (minutes * team_possessions + epsilon)
        )

        return np.clip(usg, 0, 100)

    def create_per_approximation(
        self,
        points: np.ndarray,
        rebounds: np.ndarray,
        assists: np.ndarray,
        steals: np.ndarray,
        blocks: np.ndarray,
        turnovers: np.ndarray,
        fga: np.ndarray,
        fg: np.ndarray,
        fta: np.ndarray,
        ft: np.ndarray,
        minutes: np.ndarray,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        Calculate simplified PER approximation.

        Simplified formula focusing on major contributions.

        Args:
            Various box score stats

        Returns:
            PER approximation
        """
        # Positive contributions
        positive = points + rebounds + assists + steals + blocks

        # Negative contributions
        negative = turnovers + (fga - fg) + (fta - ft) * 0.5

        # Per-minute rate
        per_minute = (positive - negative) / (minutes + epsilon)

        # Scale to ~15 average
        per = per_minute * 15 * 36  # Normalize to 36 minutes

        return np.clip(per, -10, 50)

    def create_pace_adjusted_stats(
        self, stat: np.ndarray, team_pace: np.ndarray, league_avg_pace: float = 100.0
    ) -> np.ndarray:
        """
        Adjust stats for pace.

        Pace-adjusted = stat * (league_pace / team_pace)

        Args:
            stat: Raw stat
            team_pace: Team pace
            league_avg_pace: League average pace

        Returns:
            Pace-adjusted stat
        """
        return stat * (league_avg_pace / (team_pace + 1e-8))


class FeatureSelector:
    """
    Select most important features.

    Methods:
    - Statistical tests (F-test, mutual information)
    - Recursive feature elimination (RFE)
    - Model-based importance
    """

    def __init__(self):
        """Initialize feature selector"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for FeatureSelector")

        logger.info("FeatureSelector initialized")

    def select_k_best(
        self, X: np.ndarray, y: np.ndarray, k: int, method: str = "f_regression"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Select k best features.

        Args:
            X: Feature matrix
            y: Target
            k: Number of features to select
            method: Selection method

        Returns:
            (selected_features, selected_indices)
        """
        if method == "f_regression":
            selector = SelectKBest(f_regression, k=k)
        elif method == "mutual_info":
            selector = SelectKBest(mutual_info_regression, k=k)
        else:
            selector = SelectKBest(f_regression, k=k)

        X_selected = selector.fit_transform(X, y)
        selected_indices = selector.get_support(indices=True)

        logger.info(f"Selected {k} features using {method}")

        return X_selected, selected_indices

    def recursive_elimination(
        self, X: np.ndarray, y: np.ndarray, estimator: Any, n_features: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recursive feature elimination.

        Args:
            X: Feature matrix
            y: Target
            estimator: Base estimator with coef_ or feature_importances_
            n_features: Number of features to select

        Returns:
            (selected_features, selected_indices)
        """
        selector = RFE(estimator, n_features_to_select=n_features)
        X_selected = selector.fit_transform(X, y)
        selected_indices = selector.get_support(indices=True)

        logger.info(f"RFE selected {n_features} features")

        return X_selected, selected_indices


class FeaturePipeline:
    """
    Complete feature engineering pipeline.

    Combines:
    - Time series features
    - Interactions
    - Polynomials
    - NBA domain features
    - Scaling
    - Selection
    """

    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize feature pipeline"""
        self.config = config or FeatureConfig()

        self.ts_creator = TimeSeriesFeatureCreator(config)
        self.interaction_creator = InteractionFeatureCreator(config)
        self.nba_creator = NBAFeatureCreator()

        self.scaler = None
        self.feature_names_: Optional[List[str]] = None
        self.selected_indices_: Optional[np.ndarray] = None

        logger.info("FeaturePipeline initialized")

    def fit_transform(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Fit and transform features.

        Args:
            X: Input features
            y: Target (for feature selection)
            feature_names: Feature names

        Returns:
            (transformed_features, feature_names)
        """
        if isinstance(X, pd.DataFrame):
            feature_names = X.columns.tolist()
            X = X.values

        all_features = [X]
        all_names = feature_names or [f"X{i}" for i in range(X.shape[1])]

        # Interactions
        if self.config.create_interactions:
            interactions, int_names = self.interaction_creator.create_pairwise_products(
                X, feature_names
            )
            if interactions.size > 0:
                all_features.append(interactions)
                all_names.extend(int_names)

        # Polynomials
        if self.config.create_polynomials and SKLEARN_AVAILABLE:
            poly = PolynomialFeatures(
                degree=self.config.polynomial_degree, include_bias=False
            )
            X_poly = poly.fit_transform(X)
            # Only add new features (not original)
            all_features.append(X_poly[:, X.shape[1] :])
            poly_names = [f"poly_{i}" for i in range(X_poly.shape[1] - X.shape[1])]
            all_names.extend(poly_names)

        # Combine
        X_combined = np.hstack(all_features)
        self.feature_names_ = all_names

        # Feature selection
        if self.config.select_features and y is not None and SKLEARN_AVAILABLE:
            k = self.config.n_features_to_select or min(50, X_combined.shape[1])
            selector = FeatureSelector()
            X_combined, self.selected_indices_ = selector.select_k_best(
                X_combined, y, k, self.config.selection_method
            )
            self.feature_names_ = [all_names[i] for i in self.selected_indices_]

        # Scaling
        if self.config.scale_features and SKLEARN_AVAILABLE:
            if self.config.scaler_type == "standard":
                self.scaler = StandardScaler()
            elif self.config.scaler_type == "minmax":
                self.scaler = MinMaxScaler()
            else:
                self.scaler = StandardScaler()

            X_combined = self.scaler.fit_transform(X_combined)

        logger.info(f"Created {X_combined.shape[1]} features")

        return X_combined, self.feature_names_

    def transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Transform new data using fitted pipeline.

        Args:
            X: Input features

        Returns:
            Transformed features
        """
        if isinstance(X, pd.DataFrame):
            X = X.values

        all_features = [X]

        # Interactions
        if self.config.create_interactions:
            interactions, _ = self.interaction_creator.create_pairwise_products(X)
            if interactions.size > 0:
                all_features.append(interactions)

        # Polynomials
        if self.config.create_polynomials and SKLEARN_AVAILABLE:
            poly = PolynomialFeatures(
                degree=self.config.polynomial_degree, include_bias=False
            )
            X_poly = poly.fit_transform(X)
            all_features.append(X_poly[:, X.shape[1] :])

        # Combine
        X_combined = np.hstack(all_features)

        # Select features
        if self.selected_indices_ is not None:
            X_combined = X_combined[:, self.selected_indices_]

        # Scale
        if self.scaler is not None:
            X_combined = self.scaler.transform(X_combined)

        return X_combined


__all__ = [
    "FeatureConfig",
    "TimeSeriesFeatureCreator",
    "InteractionFeatureCreator",
    "NBAFeatureCreator",
    "FeatureSelector",
    "FeaturePipeline",
]
