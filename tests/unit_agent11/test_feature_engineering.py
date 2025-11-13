"""
Unit Tests for Advanced Feature Engineering (Agent 11, Module 3)

Tests time-based features, interaction features, and domain-specific transformations.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from mcp_server.simulations.models.feature_engineering import (
    FeatureSet,
    TimeBasedFeatureGenerator,
    InteractionFeatureGenerator,
    DomainFeatureGenerator,
    FeatureScaler,
    FeatureSelector,
)


class TestFeatureSet:
    """Test FeatureSet dataclass"""

    def test_feature_set_creation(self):
        """Test creating feature set"""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        feature_set = FeatureSet(
            features=df, feature_names=["a", "b"], metadata={"source": "test"}
        )
        assert feature_set.features.shape == (3, 2)
        assert feature_set.feature_names == ["a", "b"]
        assert feature_set.metadata["source"] == "test"
        assert isinstance(feature_set.created_at, datetime)

    def test_get_shape(self):
        """Test getting feature matrix shape"""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        feature_set = FeatureSet(features=df, feature_names=["a", "b"])
        assert feature_set.get_shape() == (3, 2)

    def test_get_feature_count(self):
        """Test getting feature count"""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        feature_set = FeatureSet(features=df, feature_names=["a", "b", "c"])
        assert feature_set.get_feature_count() == 3


class TestTimeBasedFeatureGenerator:
    """Test TimeBasedFeatureGenerator class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample time-series data"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "points": np.random.randint(80, 120, 20),
                "rebounds": np.random.randint(40, 50, 20),
                "win": [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
            }
        )

    def test_generator_initialization(self):
        """Test initializing time-based feature generator"""
        gen = TimeBasedFeatureGenerator(windows=[3, 5])
        assert gen.windows == [3, 5]
        assert gen.features_generated == 0

    def test_generator_default_windows(self):
        """Test default window sizes"""
        gen = TimeBasedFeatureGenerator()
        assert gen.windows == [3, 5, 10]

    def test_create_rolling_features(self, sample_data):
        """Test creating rolling features"""
        gen = TimeBasedFeatureGenerator(windows=[3, 5])
        features = gen.create_rolling_features(
            sample_data, columns=["points"], agg_funcs=["mean", "std"]
        )
        # Should have 2 windows * 2 agg funcs = 4 features
        assert len(features.columns) == 4
        assert "points_roll_3_mean" in features.columns
        assert "points_roll_5_std" in features.columns

    def test_rolling_features_missing_column(self, sample_data):
        """Test handling missing columns"""
        gen = TimeBasedFeatureGenerator()
        features = gen.create_rolling_features(sample_data, columns=["nonexistent"])
        assert features.shape[1] == 0

    def test_create_momentum_features(self, sample_data):
        """Test creating momentum features"""
        gen = TimeBasedFeatureGenerator(windows=[3, 5])
        features = gen.create_momentum_features(sample_data, win_column="win")
        # Should have win_streak + 2 win_pct features
        assert "win_streak" in features.columns
        assert "win_pct_last_3" in features.columns
        assert "win_pct_last_5" in features.columns

    def test_momentum_features_missing_column(self, sample_data):
        """Test momentum features with missing column"""
        gen = TimeBasedFeatureGenerator()
        features = gen.create_momentum_features(sample_data, win_column="nonexistent")
        assert features.shape[1] == 0


class TestInteractionFeatureGenerator:
    """Test InteractionFeatureGenerator class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data"""
        return pd.DataFrame(
            {
                "points": [100, 110, 90, 105],
                "possessions": [100, 105, 95, 100],
                "minutes": [240, 240, 240, 240],
            }
        )

    def test_generator_initialization(self):
        """Test initializing interaction feature generator"""
        gen = InteractionFeatureGenerator()
        assert gen.features_generated == 0

    def test_create_ratio_features(self, sample_data):
        """Test creating ratio features"""
        gen = InteractionFeatureGenerator()
        features = gen.create_ratio_features(
            sample_data, numerator_cols=["points"], denominator_cols=["possessions"]
        )
        assert "points_per_possessions" in features.columns
        assert features.shape[0] == 4

    def test_create_difference_features(self, sample_data):
        """Test creating difference features"""
        gen = InteractionFeatureGenerator()
        features = gen.create_difference_features(
            sample_data, col_pairs=[("points", "possessions")]
        )
        assert "points_minus_possessions" in features.columns

    def test_create_product_features(self, sample_data):
        """Test creating product features"""
        gen = InteractionFeatureGenerator()
        features = gen.create_product_features(
            sample_data, col_pairs=[("points", "possessions")]
        )
        assert "points_times_possessions" in features.columns

    def test_multiple_ratio_pairs(self, sample_data):
        """Test creating multiple ratio features"""
        gen = InteractionFeatureGenerator()
        features = gen.create_ratio_features(
            sample_data,
            numerator_cols=["points", "possessions"],
            denominator_cols=["minutes"],
        )
        assert "points_per_minutes" in features.columns
        assert "possessions_per_minutes" in features.columns
        assert features.shape[1] == 2


class TestDomainFeatureGenerator:
    """Test DomainFeatureGenerator class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample NBA game data"""
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in [0, 1, 3, 4, 7]]
        return pd.DataFrame(
            {
                "team_id": ["LAL", "LAL", "LAL", "LAL", "LAL"],
                "is_home": [1, 0, 1, 0, 1],
                "game_date": dates,
            }
        )

    def test_generator_initialization(self):
        """Test initializing domain feature generator"""
        gen = DomainFeatureGenerator()
        assert gen.features_generated == 0

    def test_create_home_advantage_features(self, sample_data):
        """Test creating home advantage features"""
        gen = DomainFeatureGenerator()
        features = gen.create_home_advantage_features(sample_data)
        assert "is_home" in features.columns
        assert features["is_home"].dtype in [int, np.int64, np.int32]

    def test_create_rest_features(self, sample_data):
        """Test creating rest features"""
        gen = DomainFeatureGenerator()
        features = gen.create_rest_features(sample_data, date_col="game_date")
        assert "days_rest" in features.columns
        assert "is_back_to_back" in features.columns

    def test_back_to_back_detection(self, sample_data):
        """Test back-to-back game detection"""
        gen = DomainFeatureGenerator()
        features = gen.create_rest_features(sample_data, date_col="game_date")
        # Second game is 1 day after first, so it's back-to-back
        assert features["is_back_to_back"].iloc[1] == 1
        # Third game is 2 days after second, so not back-to-back
        assert features["is_back_to_back"].iloc[2] == 0


class TestFeatureScaler:
    """Test FeatureScaler class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data"""
        np.random.seed(42)
        return np.random.randn(100, 5)

    def test_scaler_initialization_standard(self):
        """Test initializing standard scaler"""
        scaler = FeatureScaler(method="standard")
        assert scaler.method == "standard"
        assert scaler.scaler is not None

    def test_scaler_initialization_minmax(self):
        """Test initializing minmax scaler"""
        scaler = FeatureScaler(method="minmax")
        assert scaler.method == "minmax"

    def test_scaler_initialization_robust(self):
        """Test initializing robust scaler"""
        scaler = FeatureScaler(method="robust")
        assert scaler.method == "robust"

    def test_scaler_invalid_method(self):
        """Test invalid scaling method"""
        with pytest.raises(ValueError, match="Unknown scaling method"):
            FeatureScaler(method="invalid")

    def test_fit_transform_standard(self, sample_data):
        """Test fit_transform with standard scaler"""
        scaler = FeatureScaler(method="standard")
        scaled = scaler.fit_transform(sample_data)
        assert scaled.shape == sample_data.shape
        # Standard scaling should have mean ~0 and std ~1
        assert np.abs(scaled.mean()) < 0.1
        assert np.abs(scaled.std() - 1.0) < 0.1

    def test_fit_transform_minmax(self, sample_data):
        """Test fit_transform with minmax scaler"""
        scaler = FeatureScaler(method="minmax")
        scaled = scaler.fit_transform(sample_data)
        # MinMax scaling should be in [0, 1]
        assert scaled.min() >= 0.0
        assert scaled.max() <= 1.0

    def test_transform_after_fit(self, sample_data):
        """Test transform after fit_transform"""
        scaler = FeatureScaler(method="standard")
        scaler.fit_transform(sample_data[:80])
        scaled = scaler.transform(sample_data[80:])
        assert scaled.shape == (20, 5)

    def test_scaler_with_dataframe(self):
        """Test scaler with pandas DataFrame"""
        df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
        scaler = FeatureScaler(method="standard")
        scaled = scaler.fit_transform(df)
        assert scaled.shape == (4, 2)


class TestFeatureSelector:
    """Test FeatureSelector class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with target"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        # y depends strongly on first 3 features
        y = X[:, 0] * 2 + X[:, 1] * 3 + X[:, 2] * 1.5 + np.random.randn(100) * 0.1
        return X, y

    def test_selector_initialization(self):
        """Test initializing feature selector"""
        selector = FeatureSelector(method="mutual_info", k=5)
        assert selector.method == "mutual_info"
        assert selector.k == 5
        assert selector.selector is None

    def test_fit_select(self, sample_data):
        """Test fitting and selecting features"""
        X, y = sample_data
        selector = FeatureSelector(method="mutual_info", k=5)
        X_selected, feature_names = selector.fit_select(X, y)
        assert X_selected.shape == (100, 5)
        assert len(feature_names) == 5

    def test_fit_select_with_feature_names(self, sample_data):
        """Test fit_select with custom feature names"""
        X, y = sample_data
        feature_names = [f"feature_{i}" for i in range(10)]
        selector = FeatureSelector(k=3)
        X_selected, selected_names = selector.fit_select(X, y, feature_names)
        assert X_selected.shape == (100, 3)
        assert len(selected_names) == 3
        assert all(name in feature_names for name in selected_names)

    def test_transform_after_fit(self, sample_data):
        """Test transform after fit_select"""
        X, y = sample_data
        selector = FeatureSelector(k=5)
        selector.fit_select(X[:80], y[:80])
        X_selected = selector.transform(X[80:])
        assert X_selected.shape == (20, 5)

    def test_selector_k_larger_than_features(self, sample_data):
        """Test selector when k is larger than number of features"""
        X, y = sample_data
        selector = FeatureSelector(k=20)  # More than 10 features available
        X_selected, _ = selector.fit_select(X, y)
        # Should select all 10 features
        assert X_selected.shape == (100, 10)
