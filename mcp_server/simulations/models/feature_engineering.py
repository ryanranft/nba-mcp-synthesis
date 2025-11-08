"""
Advanced Feature Engineering (Agent 11, Module 3)

Provides feature engineering utilities for NBA game simulation including
time-based features, interaction features, and domain-specific transformations.

Integrates with:
- Agent 2 (Monitoring): Track feature generation metrics
- Agent 4 (Data Validation): Validate feature quality
- Agent 9 (Performance): Profile feature computation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression

logger = logging.getLogger(__name__)


@dataclass
class FeatureSet:
    """Container for engineered features"""
    features: pd.DataFrame
    feature_names: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_shape(self) -> Tuple[int, int]:
        """Get feature matrix shape"""
        return self.features.shape

    def get_feature_count(self) -> int:
        """Get number of features"""
        return len(self.feature_names)


class TimeBasedFeatureGenerator:
    """
    Generate time-based features for game prediction.

    Features include:
    - Rolling statistics (mean, std, min, max)
    - Momentum indicators (win streaks, trend)
    - Recent form (last N games performance)
    """

    def __init__(self, windows: List[int] = None):
        """
        Initialize time-based feature generator.

        Args:
            windows: List of window sizes for rolling features
        """
        self.windows = windows or [3, 5, 10]
        self.features_generated = 0

    def create_rolling_features(
        self,
        data: pd.DataFrame,
        columns: List[str],
        agg_funcs: List[str] = None
    ) -> pd.DataFrame:
        """
        Create rolling window features.

        Args:
            data: Input DataFrame with time-series data
            columns: Columns to create rolling features for
            agg_funcs: Aggregation functions (mean, std, min, max)

        Returns:
            DataFrame with rolling features
        """
        if agg_funcs is None:
            agg_funcs = ['mean', 'std']

        features = pd.DataFrame(index=data.index)

        for col in columns:
            if col not in data.columns:
                logger.warning(f"Column {col} not found in data")
                continue

            for window in self.windows:
                for func in agg_funcs:
                    feature_name = f"{col}_roll_{window}_{func}"
                    if func == 'mean':
                        features[feature_name] = data[col].rolling(window=window, min_periods=1).mean()
                    elif func == 'std':
                        features[feature_name] = data[col].rolling(window=window, min_periods=1).std()
                    elif func == 'min':
                        features[feature_name] = data[col].rolling(window=window, min_periods=1).min()
                    elif func == 'max':
                        features[feature_name] = data[col].rolling(window=window, min_periods=1).max()

        self.features_generated += len(features.columns)
        return features

    def create_momentum_features(
        self,
        data: pd.DataFrame,
        win_column: str = 'win'
    ) -> pd.DataFrame:
        """
        Create momentum-based features.

        Args:
            data: Input DataFrame with win/loss data
            win_column: Column indicating wins (1) or losses (0)

        Returns:
            DataFrame with momentum features
        """
        features = pd.DataFrame(index=data.index)

        if win_column not in data.columns:
            logger.warning(f"Column {win_column} not found in data")
            return features

        # Win streak (consecutive wins)
        features['win_streak'] = (
            data[win_column]
            .groupby((data[win_column] != data[win_column].shift()).cumsum())
            .cumsum()
        )

        # Recent win percentage
        for window in self.windows:
            features[f'win_pct_last_{window}'] = (
                data[win_column]
                .rolling(window=window, min_periods=1)
                .mean()
            )

        self.features_generated += len(features.columns)
        return features


class InteractionFeatureGenerator:
    """
    Generate interaction features between different variables.

    Useful for capturing team matchups and contextual effects.
    """

    def __init__(self):
        """Initialize interaction feature generator"""
        self.features_generated = 0

    def create_ratio_features(
        self,
        data: pd.DataFrame,
        numerator_cols: List[str],
        denominator_cols: List[str]
    ) -> pd.DataFrame:
        """
        Create ratio features between columns.

        Args:
            data: Input DataFrame
            numerator_cols: Numerator columns
            denominator_cols: Denominator columns

        Returns:
            DataFrame with ratio features
        """
        features = pd.DataFrame(index=data.index)

        for num_col in numerator_cols:
            for denom_col in denominator_cols:
                if num_col in data.columns and denom_col in data.columns:
                    feature_name = f"{num_col}_per_{denom_col}"
                    # Avoid division by zero
                    features[feature_name] = data[num_col] / (data[denom_col] + 1e-6)

        self.features_generated += len(features.columns)
        return features

    def create_difference_features(
        self,
        data: pd.DataFrame,
        col_pairs: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Create difference features between column pairs.

        Args:
            data: Input DataFrame
            col_pairs: List of (col1, col2) pairs

        Returns:
            DataFrame with difference features
        """
        features = pd.DataFrame(index=data.index)

        for col1, col2 in col_pairs:
            if col1 in data.columns and col2 in data.columns:
                feature_name = f"{col1}_minus_{col2}"
                features[feature_name] = data[col1] - data[col2]

        self.features_generated += len(features.columns)
        return features

    def create_product_features(
        self,
        data: pd.DataFrame,
        col_pairs: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Create product features between column pairs.

        Args:
            data: Input DataFrame
            col_pairs: List of (col1, col2) pairs

        Returns:
            DataFrame with product features
        """
        features = pd.DataFrame(index=data.index)

        for col1, col2 in col_pairs:
            if col1 in data.columns and col2 in data.columns:
                feature_name = f"{col1}_times_{col2}"
                features[feature_name] = data[col1] * data[col2]

        self.features_generated += len(features.columns)
        return features


class DomainFeatureGenerator:
    """
    Generate domain-specific NBA features.

    Includes features like:
    - Home court advantage
    - Rest days effect
    - Travel distance
    - Back-to-back games
    """

    def __init__(self):
        """Initialize domain feature generator"""
        self.features_generated = 0

    def create_home_advantage_features(
        self,
        data: pd.DataFrame,
        is_home_col: str = 'is_home'
    ) -> pd.DataFrame:
        """
        Create home court advantage features.

        Args:
            data: Input DataFrame
            is_home_col: Column indicating home games

        Returns:
            DataFrame with home advantage features
        """
        features = pd.DataFrame(index=data.index)

        if is_home_col in data.columns:
            features['is_home'] = data[is_home_col].astype(int)
            # Home win percentage
            features['home_win_pct'] = (
                data.groupby('team_id')[is_home_col]
                .expanding()
                .mean()
                .reset_index(level=0, drop=True)
            ) if 'team_id' in data.columns else data[is_home_col]

        self.features_generated += len(features.columns)
        return features

    def create_rest_features(
        self,
        data: pd.DataFrame,
        date_col: str = 'game_date'
    ) -> pd.DataFrame:
        """
        Create rest days features.

        Args:
            data: Input DataFrame
            date_col: Column with game dates

        Returns:
            DataFrame with rest features
        """
        features = pd.DataFrame(index=data.index)

        if date_col in data.columns:
            # Convert to datetime if needed
            dates = pd.to_datetime(data[date_col])
            # Days since last game
            features['days_rest'] = dates.diff().dt.days.fillna(3)
            # Back-to-back indicator
            features['is_back_to_back'] = (features['days_rest'] <= 1).astype(int)

        self.features_generated += len(features.columns)
        return features


class FeatureScaler:
    """
    Scale features using various methods.

    Supports:
    - StandardScaler (z-score normalization)
    - MinMaxScaler (range [0, 1])
    - RobustScaler (median and IQR)
    """

    def __init__(self, method: str = 'standard'):
        """
        Initialize feature scaler.

        Args:
            method: Scaling method ('standard', 'minmax', 'robust')
        """
        self.method = method
        self.scaler = None
        self._initialize_scaler()

    def _initialize_scaler(self):
        """Initialize the appropriate scaler"""
        if self.method == 'standard':
            self.scaler = StandardScaler()
        elif self.method == 'minmax':
            self.scaler = MinMaxScaler()
        elif self.method == 'robust':
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {self.method}")

    def fit_transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Fit scaler and transform features.

        Args:
            X: Features to scale

        Returns:
            Scaled features
        """
        return self.scaler.fit_transform(X)

    def transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Transform features using fitted scaler.

        Args:
            X: Features to scale

        Returns:
            Scaled features
        """
        if self.scaler is None:
            raise ValueError("Scaler must be fitted before transform")
        return self.scaler.transform(X)


class FeatureSelector:
    """
    Select most important features using various methods.

    Supports:
    - Mutual information
    - Variance threshold
    - K-best selection
    """

    def __init__(self, method: str = 'mutual_info', k: int = 10):
        """
        Initialize feature selector.

        Args:
            method: Selection method ('mutual_info', 'k_best')
            k: Number of features to select
        """
        self.method = method
        self.k = k
        self.selector = None
        self.selected_features = []

    def fit_select(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Fit selector and select features.

        Args:
            X: Features
            y: Target variable
            feature_names: Optional feature names

        Returns:
            (selected_features, selected_feature_names)
        """
        if self.method == 'mutual_info':
            self.selector = SelectKBest(mutual_info_regression, k=min(self.k, X.shape[1]))
        else:
            self.selector = SelectKBest(k=min(self.k, X.shape[1]))

        X_selected = self.selector.fit_transform(X, y)

        # Get selected feature names
        if feature_names is not None:
            mask = self.selector.get_support()
            self.selected_features = [
                name for name, selected in zip(feature_names, mask) if selected
            ]
        else:
            self.selected_features = [f"feature_{i}" for i in range(X_selected.shape[1])]

        return X_selected, self.selected_features

    def transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Transform features using fitted selector.

        Args:
            X: Features to select from

        Returns:
            Selected features
        """
        if self.selector is None:
            raise ValueError("Selector must be fitted before transform")
        return self.selector.transform(X)
