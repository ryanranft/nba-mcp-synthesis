"""
Unit Tests for Enhanced Ensemble Methods (Agent 11, Module 1)

Tests stacking, blending, and diversity metrics for ensemble models.
"""

import pytest
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from mcp_server.simulations.models.ensemble import (
    EnsembleMetrics,
    StackedEnsemble,
    BlendedEnsemble,
    EnsembleSimulator
)


class TestEnsembleMetrics:
    """Test EnsembleMetrics dataclass"""

    def test_ensemble_metrics_creation(self):
        """Test creating ensemble metrics"""
        metrics = EnsembleMetrics(
            diversity_score=0.75,
            avg_base_error=10.5,
            ensemble_error=8.2,
            improvement=0.22
        )
        assert metrics.diversity_score == 0.75
        assert metrics.avg_base_error == 10.5
        assert metrics.ensemble_error == 8.2
        assert metrics.improvement == 0.22
        assert isinstance(metrics.computed_at, datetime)

    def test_is_effective_true(self):
        """Test effective ensemble detection"""
        metrics = EnsembleMetrics(
            diversity_score=0.75,
            avg_base_error=10.0,
            ensemble_error=8.0,
            improvement=0.20  # 20% improvement
        )
        assert metrics.is_effective(min_improvement=0.05) is True

    def test_is_effective_false(self):
        """Test ineffective ensemble detection"""
        metrics = EnsembleMetrics(
            diversity_score=0.30,
            avg_base_error=10.0,
            ensemble_error=9.8,
            improvement=0.02  # Only 2% improvement
        )
        assert metrics.is_effective(min_improvement=0.05) is False

    def test_is_effective_custom_threshold(self):
        """Test effectiveness with custom threshold"""
        metrics = EnsembleMetrics(
            diversity_score=0.60,
            avg_base_error=10.0,
            ensemble_error=9.0,
            improvement=0.10  # 10% improvement
        )
        assert metrics.is_effective(min_improvement=0.05) is True
        assert metrics.is_effective(min_improvement=0.15) is False


class TestStackedEnsemble:
    """Test StackedEnsemble class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return X, y

    @pytest.fixture
    def base_models(self):
        """Create base models for ensemble"""
        return [
            LinearRegression(),
            Ridge(alpha=1.0),
            DecisionTreeRegressor(max_depth=3, random_state=42)
        ]

    def test_stacked_ensemble_initialization(self, base_models):
        """Test initializing stacked ensemble"""
        ensemble = StackedEnsemble(base_models)
        assert len(ensemble.base_models) == 3
        assert ensemble.meta_learner is not None
        assert ensemble.cv_folds == 5
        assert ensemble.is_fitted_ is False

    def test_stacked_ensemble_fit(self, base_models, sample_data):
        """Test fitting stacked ensemble"""
        X, y = sample_data
        ensemble = StackedEnsemble(base_models)
        ensemble.fit(X, y)
        assert ensemble.is_fitted_ is True

    def test_stacked_ensemble_predict(self, base_models, sample_data):
        """Test making predictions with stacked ensemble"""
        X, y = sample_data
        ensemble = StackedEnsemble(base_models)
        ensemble.fit(X, y)

        predictions = ensemble.predict(X[:10])
        assert len(predictions) == 10
        assert predictions.shape == (10,)

    def test_stacked_ensemble_predict_unfitted(self, base_models):
        """Test prediction fails on unfitted model"""
        X = np.random.randn(10, 5)
        ensemble = StackedEnsemble(base_models)

        with pytest.raises(ValueError, match="must be fitted"):
            ensemble.predict(X)

    def test_stacked_ensemble_custom_meta_learner(self, base_models, sample_data):
        """Test stacked ensemble with custom meta-learner"""
        X, y = sample_data
        meta = Ridge(alpha=0.5)
        ensemble = StackedEnsemble(base_models, meta_learner=meta)
        ensemble.fit(X, y)

        predictions = ensemble.predict(X[:10])
        assert len(predictions) == 10

    def test_stacked_ensemble_accuracy(self, base_models, sample_data):
        """Test stacked ensemble improves accuracy"""
        X, y = sample_data

        # Train base models individually
        base_errors = []
        for model in base_models:
            model_copy = type(model)(**model.get_params())
            model_copy.fit(X, y)
            preds = model_copy.predict(X)
            error = np.mean((preds - y) ** 2)
            base_errors.append(error)

        # Train stacked ensemble
        ensemble = StackedEnsemble([
            LinearRegression(),
            Ridge(alpha=1.0),
            DecisionTreeRegressor(max_depth=3, random_state=42)
        ])
        ensemble.fit(X, y)
        ensemble_preds = ensemble.predict(X)
        ensemble_error = np.mean((ensemble_preds - y) ** 2)

        # Ensemble should be better than average base model
        avg_base_error = np.mean(base_errors)
        assert ensemble_error <= avg_base_error


class TestBlendedEnsemble:
    """Test BlendedEnsemble class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return X, y

    @pytest.fixture
    def base_models(self):
        """Create base models for ensemble"""
        return [
            LinearRegression(),
            Ridge(alpha=1.0),
            DecisionTreeRegressor(max_depth=3, random_state=42)
        ]

    def test_blended_ensemble_initialization(self, base_models):
        """Test initializing blended ensemble"""
        ensemble = BlendedEnsemble(base_models)
        assert len(ensemble.base_models) == 3
        assert ensemble.blend_fraction == 0.2
        assert ensemble.optimize_weights is True
        assert ensemble.weights_ is None
        assert ensemble.is_fitted_ is False

    def test_blended_ensemble_fit(self, base_models, sample_data):
        """Test fitting blended ensemble"""
        X, y = sample_data
        ensemble = BlendedEnsemble(base_models)
        ensemble.fit(X, y)
        assert ensemble.is_fitted_ is True
        assert ensemble.weights_ is not None
        assert len(ensemble.weights_) == 3

    def test_blended_ensemble_weights_sum_to_one(self, base_models, sample_data):
        """Test blend weights sum to 1.0"""
        X, y = sample_data
        ensemble = BlendedEnsemble(base_models)
        ensemble.fit(X, y)
        assert np.isclose(np.sum(ensemble.weights_), 1.0)

    def test_blended_ensemble_predict(self, base_models, sample_data):
        """Test making predictions with blended ensemble"""
        X, y = sample_data
        ensemble = BlendedEnsemble(base_models)
        ensemble.fit(X, y)

        predictions = ensemble.predict(X[:10])
        assert len(predictions) == 10
        assert predictions.shape == (10,)

    def test_blended_ensemble_predict_unfitted(self, base_models):
        """Test prediction fails on unfitted model"""
        X = np.random.randn(10, 5)
        ensemble = BlendedEnsemble(base_models)

        with pytest.raises(ValueError, match="must be fitted"):
            ensemble.predict(X)

    def test_blended_ensemble_equal_weights(self, base_models, sample_data):
        """Test blended ensemble with equal weights"""
        X, y = sample_data
        ensemble = BlendedEnsemble(base_models, optimize_weights=False)
        ensemble.fit(X, y)

        # Weights should be equal
        expected_weight = 1.0 / len(base_models)
        assert np.allclose(ensemble.weights_, expected_weight)

    def test_blended_ensemble_get_weights(self, base_models, sample_data):
        """Test getting model weights"""
        X, y = sample_data
        ensemble = BlendedEnsemble(base_models)
        ensemble.fit(X, y)

        weights_dict = ensemble.get_weights()
        assert len(weights_dict) == 3
        assert 'model_0' in weights_dict
        assert 'model_1' in weights_dict
        assert 'model_2' in weights_dict
        assert all(isinstance(v, float) for v in weights_dict.values())

    def test_blended_ensemble_get_weights_unfitted(self, base_models):
        """Test getting weights from unfitted model"""
        ensemble = BlendedEnsemble(base_models)
        weights = ensemble.get_weights()
        assert weights == {}


class TestEnsembleSimulator:
    """Test EnsembleSimulator class"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return X, y

    @pytest.fixture
    def base_models(self):
        """Create base models"""
        return [
            LinearRegression(),
            Ridge(alpha=1.0)
        ]

    def test_simulator_initialization_default(self):
        """Test initializing simulator with defaults"""
        simulator = EnsembleSimulator()
        assert simulator.base_models is not None
        assert len(simulator.base_models) == 2  # Default models
        assert simulator.ensemble_type == "stacking"
        assert simulator.enable_monitoring is True
        assert simulator.predictions_count == 0

    def test_simulator_initialization_custom(self, base_models):
        """Test initializing simulator with custom models"""
        simulator = EnsembleSimulator(
            base_models=base_models,
            ensemble_type="blending"
        )
        assert len(simulator.base_models) == 2
        assert simulator.ensemble_type == "blending"

    def test_simulator_fit_stacking(self, base_models, sample_data):
        """Test fitting simulator with stacking"""
        X, y = sample_data
        simulator = EnsembleSimulator(
            base_models=base_models,
            ensemble_type="stacking"
        )
        simulator.fit(X, y)
        assert simulator.ensemble_model is not None
        assert isinstance(simulator.ensemble_model, StackedEnsemble)

    def test_simulator_fit_blending(self, base_models, sample_data):
        """Test fitting simulator with blending"""
        X, y = sample_data
        simulator = EnsembleSimulator(
            base_models=base_models,
            ensemble_type="blending"
        )
        simulator.fit(X, y)
        assert simulator.ensemble_model is not None
        assert isinstance(simulator.ensemble_model, BlendedEnsemble)

    def test_simulator_fit_invalid_type(self, base_models, sample_data):
        """Test fitting with invalid ensemble type"""
        X, y = sample_data
        simulator = EnsembleSimulator(
            base_models=base_models,
            ensemble_type="invalid"
        )
        with pytest.raises(ValueError, match="Unknown ensemble type"):
            simulator.fit(X, y)

    def test_simulator_predict(self, base_models, sample_data):
        """Test making predictions with simulator"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)

        predictions = simulator.predict(X[:10])
        assert len(predictions) == 10
        assert simulator.predictions_count == 10

    def test_simulator_predict_unfitted(self, base_models):
        """Test prediction fails on unfitted simulator"""
        X = np.random.randn(10, 5)
        simulator = EnsembleSimulator(base_models=base_models)

        with pytest.raises(ValueError, match="must be fitted"):
            simulator.predict(X)

    def test_simulator_compute_diversity(self, base_models, sample_data):
        """Test computing diversity score"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)

        diversity = simulator.compute_diversity(X, y)
        assert 0.0 <= diversity <= 1.0
        assert len(simulator.diversity_scores) == 1

    def test_simulator_evaluate_ensemble(self, base_models, sample_data):
        """Test evaluating ensemble performance"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)

        metrics = simulator.evaluate_ensemble(X, y)
        assert isinstance(metrics, EnsembleMetrics)
        assert 0.0 <= metrics.diversity_score <= 1.0
        assert metrics.avg_base_error >= 0.0
        assert metrics.ensemble_error >= 0.0
        assert -1.0 <= metrics.improvement <= 1.0

    def test_simulator_get_statistics(self, base_models, sample_data):
        """Test getting simulator statistics"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)
        simulator.predict(X[:10])
        simulator.compute_diversity(X, y)

        stats = simulator.get_statistics()
        assert stats['ensemble_type'] == 'stacking'
        assert stats['n_base_models'] == 2
        assert stats['predictions_made'] == 10
        assert stats['avg_diversity'] > 0.0
        assert stats['diversity_samples'] == 1

    def test_simulator_multiple_predictions_count(self, base_models, sample_data):
        """Test prediction counter increments correctly"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)

        simulator.predict(X[:10])
        assert simulator.predictions_count == 10

        simulator.predict(X[:5])
        assert simulator.predictions_count == 15

        simulator.predict(X[:20])
        assert simulator.predictions_count == 35

    def test_simulator_diversity_tracking(self, base_models, sample_data):
        """Test diversity score tracking over multiple calls"""
        X, y = sample_data
        simulator = EnsembleSimulator(base_models=base_models)
        simulator.fit(X, y)

        simulator.compute_diversity(X, y)
        simulator.compute_diversity(X, y)
        simulator.compute_diversity(X, y)

        assert len(simulator.diversity_scores) == 3
        stats = simulator.get_statistics()
        assert stats['diversity_samples'] == 3
