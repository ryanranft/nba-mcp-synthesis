"""
Enhanced Ensemble Methods (Agent 11, Module 1)

Provides advanced ensemble techniques for NBA game simulation including
stacking, blending, dynamic weighting, and diversity metrics.

Integrates with:
- Agent 2 (Monitoring): Track ensemble performance
- Agent 4 (Validation): Validate ensemble predictions
- Agent 9 (Performance): Profile ensemble operations
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings

logger = logging.getLogger(__name__)


@dataclass
class EnsembleMetrics:
    """Metrics for ensemble performance"""

    diversity_score: float  # Higher is better (less correlated)
    avg_base_error: float  # Average error of base models
    ensemble_error: float  # Error of ensemble
    improvement: float  # Percentage improvement over avg base
    computed_at: datetime = field(default_factory=datetime.now)

    def is_effective(self, min_improvement: float = 0.05) -> bool:
        """Check if ensemble provides meaningful improvement"""
        return self.improvement >= min_improvement


class StackedEnsemble(BaseEstimator, RegressorMixin):
    """
    Stacked ensemble that trains a meta-learner on base model predictions.

    Two-level architecture:
    - Level 0: Base models make predictions
    - Level 1: Meta-learner combines base predictions
    """

    def __init__(
        self,
        base_models: List[BaseEstimator],
        meta_learner: Optional[BaseEstimator] = None,
        use_probas: bool = False,
        cv_folds: int = 5,
    ):
        """
        Initialize stacked ensemble.

        Args:
            base_models: List of base estimators
            meta_learner: Meta-learner (default: LinearRegression)
            use_probas: Use probability estimates if available
            cv_folds: Cross-validation folds for meta-features
        """
        self.base_models = base_models
        self.meta_learner = meta_learner or LinearRegression()
        self.use_probas = use_probas
        self.cv_folds = cv_folds
        self.is_fitted_ = False

    def fit(self, X, y):
        """
        Fit stacked ensemble.

        Args:
            X: Training features
            y: Training target

        Returns:
            self
        """
        # Fit base models
        for model in self.base_models:
            model.fit(X, y)

        # Generate meta-features using cross-validation
        meta_features = self._generate_meta_features(X, y)

        # Fit meta-learner
        self.meta_learner.fit(meta_features, y)

        self.is_fitted_ = True
        return self

    def _generate_meta_features(self, X, y) -> np.ndarray:
        """
        Generate meta-features from base model predictions.

        Args:
            X: Features
            y: Target

        Returns:
            Meta-features array
        """
        meta_features = []

        for model in self.base_models:
            # Use cross-validation to generate out-of-fold predictions
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                preds = cross_val_predict(model, X, y, cv=self.cv_folds)
            meta_features.append(preds.reshape(-1, 1))

        return np.hstack(meta_features)

    def predict(self, X):
        """
        Make predictions using stacked ensemble.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before prediction")

        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            preds = model.predict(X)
            base_predictions.append(preds.reshape(-1, 1))

        meta_features = np.hstack(base_predictions)

        # Get meta-learner prediction
        return self.meta_learner.predict(meta_features)


class BlendedEnsemble(BaseEstimator, RegressorMixin):
    """
    Blended ensemble that combines base models using learned weights.

    Unlike stacking, blending uses a holdout set to learn weights.
    """

    def __init__(
        self,
        base_models: List[BaseEstimator],
        blend_fraction: float = 0.2,
        optimize_weights: bool = True,
    ):
        """
        Initialize blended ensemble.

        Args:
            base_models: List of base estimators
            blend_fraction: Fraction of data for blending
            optimize_weights: Optimize weights vs equal weighting
        """
        self.base_models = base_models
        self.blend_fraction = blend_fraction
        self.optimize_weights = optimize_weights
        self.weights_ = None
        self.is_fitted_ = False

    def fit(self, X, y):
        """
        Fit blended ensemble.

        Args:
            X: Training features
            y: Training target

        Returns:
            self
        """
        # Split data for training and blending
        n_samples = len(X)
        n_blend = int(n_samples * self.blend_fraction)
        n_train = n_samples - n_blend

        X_train, X_blend = X[:n_train], X[n_train:]
        y_train, y_blend = y[:n_train], y[n_train:]

        # Train base models on training set
        for model in self.base_models:
            model.fit(X_train, y_train)

        # Get predictions on blend set
        blend_predictions = []
        for model in self.base_models:
            preds = model.predict(X_blend)
            blend_predictions.append(preds)

        blend_predictions = np.array(blend_predictions).T

        # Learn weights
        if self.optimize_weights:
            self.weights_ = self._optimize_weights(blend_predictions, y_blend)
        else:
            # Equal weights
            self.weights_ = np.ones(len(self.base_models)) / len(self.base_models)

        self.is_fitted_ = True
        return self

    def _optimize_weights(self, predictions: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Optimize blend weights to minimize error.

        Args:
            predictions: Base model predictions (n_samples, n_models)
            y: True values

        Returns:
            Optimized weights
        """
        from scipy.optimize import minimize

        def objective(weights):
            weights = np.maximum(weights, 0)  # Ensure non-negative
            weights = weights / weights.sum()  # Normalize
            ensemble_pred = predictions @ weights
            return np.mean((ensemble_pred - y) ** 2)

        # Initial equal weights
        initial_weights = np.ones(len(self.base_models)) / len(self.base_models)

        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=[(0, 1)] * len(self.base_models),
            constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        )

        return result.x

    def predict(self, X):
        """
        Make predictions using blended ensemble.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before prediction")

        # Get base model predictions
        predictions = []
        for model in self.base_models:
            preds = model.predict(X)
            predictions.append(preds)

        predictions = np.array(predictions).T

        # Weighted combination
        return predictions @ self.weights_

    def get_weights(self) -> Dict[str, float]:
        """Get model weights"""
        if self.weights_ is None:
            return {}

        return {f"model_{i}": float(w) for i, w in enumerate(self.weights_)}


class EnsembleSimulator:
    """
    Main ensemble simulator with stacking, blending, and dynamic weighting.

    Features:
    - Multiple ensemble strategies
    - Diversity metrics
    - Dynamic weight adaptation
    - Performance monitoring
    """

    def __init__(
        self,
        base_models: Optional[List[BaseEstimator]] = None,
        ensemble_type: str = "stacking",
        enable_monitoring: bool = True,
    ):
        """
        Initialize ensemble simulator.

        Args:
            base_models: List of base models (creates defaults if None)
            ensemble_type: 'stacking', 'blending', or 'voting'
            enable_monitoring: Enable performance monitoring
        """
        self.base_models = base_models or self._create_default_models()
        self.ensemble_type = ensemble_type
        self.enable_monitoring = enable_monitoring
        self.ensemble_model = None
        self.predictions_count = 0
        self.diversity_scores = []

    def _create_default_models(self) -> List[BaseEstimator]:
        """Create default base models"""
        return [
            LinearRegression(),
            RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
        ]

    def fit(self, X, y):
        """
        Fit ensemble simulator.

        Args:
            X: Training features
            y: Training target

        Returns:
            self
        """
        if self.ensemble_type == "stacking":
            self.ensemble_model = StackedEnsemble(self.base_models)
        elif self.ensemble_type == "blending":
            self.ensemble_model = BlendedEnsemble(self.base_models)
        else:
            raise ValueError(f"Unknown ensemble type: {self.ensemble_type}")

        self.ensemble_model.fit(X, y)
        return self

    def predict(self, X):
        """
        Make predictions using ensemble.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if self.ensemble_model is None:
            raise ValueError("Model must be fitted before prediction")

        predictions = self.ensemble_model.predict(X)
        self.predictions_count += len(predictions)

        return predictions

    def compute_diversity(self, X, y) -> float:
        """
        Compute ensemble diversity score.

        Higher diversity indicates less correlation between base models,
        which generally leads to better ensemble performance.

        Args:
            X: Features
            y: Target

        Returns:
            Diversity score (0 to 1, higher is better)
        """
        # Get predictions from each base model
        predictions = []
        for model in self.base_models:
            preds = model.predict(X)
            predictions.append(preds)

        predictions = np.array(predictions)

        # Compute pairwise correlation
        n_models = len(self.base_models)
        correlations = []

        for i in range(n_models):
            for j in range(i + 1, n_models):
                corr = np.corrcoef(predictions[i], predictions[j])[0, 1]
                correlations.append(abs(corr))

        # Diversity is inverse of average correlation
        avg_correlation = np.mean(correlations) if correlations else 0.0
        diversity_score = 1.0 - avg_correlation

        self.diversity_scores.append(diversity_score)
        return diversity_score

    def evaluate_ensemble(self, X, y) -> EnsembleMetrics:
        """
        Evaluate ensemble performance.

        Args:
            X: Features
            y: Target

        Returns:
            EnsembleMetrics
        """
        # Get ensemble predictions
        ensemble_preds = self.predict(X)
        ensemble_error = np.mean((ensemble_preds - y) ** 2)

        # Get base model errors
        base_errors = []
        for model in self.base_models:
            preds = model.predict(X)
            error = np.mean((preds - y) ** 2)
            base_errors.append(error)

        avg_base_error = np.mean(base_errors)

        # Compute improvement
        improvement = (
            (avg_base_error - ensemble_error) / avg_base_error
            if avg_base_error > 0
            else 0.0
        )

        # Compute diversity
        diversity = self.compute_diversity(X, y)

        return EnsembleMetrics(
            diversity_score=diversity,
            avg_base_error=avg_base_error,
            ensemble_error=ensemble_error,
            improvement=improvement,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get ensemble statistics"""
        return {
            "ensemble_type": self.ensemble_type,
            "n_base_models": len(self.base_models),
            "predictions_made": self.predictions_count,
            "avg_diversity": (
                np.mean(self.diversity_scores) if self.diversity_scores else 0.0
            ),
            "diversity_samples": len(self.diversity_scores),
        }
