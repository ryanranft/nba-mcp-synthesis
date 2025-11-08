"""
Multi-Model Ensemble Framework for NBA Analytics.

This module provides ensemble methods for combining predictions from multiple models:
- Simple averaging
- Weighted averaging
- Model stacking (meta-learning)
- Dynamic model selection
- Out-of-sample validation

Key Features:
- Combine any model types (ARIMA, VAR, regression, Bayesian, etc.)
- Automatic weight optimization
- Cross-validation for ensemble training
- Uncertainty quantification
- Model diversity metrics

Use Cases:
- Improving prediction accuracy
- Reducing overfitting risk
- Combining complementary models
- Robust forecasting

Examples
--------

1. Simple Ensemble Averaging:

>>> from mcp_server.ensemble import SimpleEnsemble
>>> from mcp_server.econometric_suite import EconometricSuite
>>>
>>> # Fit multiple models
>>> suite1 = EconometricSuite(data=df, target='points')
>>> model1 = suite1.time_series_analysis(method='arima')
>>>
>>> suite2 = EconometricSuite(data=df, target='points')
>>> model2 = suite2.time_series_analysis(method='var')
>>>
>>> # Create ensemble
>>> ensemble = SimpleEnsemble([model1, model2])
>>> predictions = ensemble.predict(n_steps=10)

2. Weighted Ensemble:

>>> from mcp_server.ensemble import WeightedEnsemble
>>>
>>> ensemble = WeightedEnsemble(
...     models=[model1, model2, model3],
...     weights=[0.5, 0.3, 0.2]  # Or optimize automatically
... )
>>> predictions = ensemble.predict(n_steps=10)

3. Stacking Ensemble:

>>> from mcp_server.ensemble import StackingEnsemble
>>>
>>> ensemble = StackingEnsemble(
...     base_models=[model1, model2, model3],
...     meta_model='ridge'  # Meta-learner
... )
>>> ensemble.fit(X_train, y_train)
>>> predictions = ensemble.predict(X_test)

Author: Claude Code
Date: November 2025
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)


@dataclass
class EnsembleResult:
    """Results from ensemble prediction."""

    predictions: np.ndarray  # Ensemble predictions
    model_predictions: List[np.ndarray]  # Individual model predictions
    weights: Optional[np.ndarray] = None  # Model weights (if applicable)
    uncertainty: Optional[np.ndarray] = None  # Prediction uncertainty
    metrics: Dict[str, float] = field(default_factory=dict)
    n_models: int = 0


class SimpleEnsemble:
    """
    Simple ensemble using unweighted averaging.

    Fast and robust baseline ensemble method.
    """

    def __init__(self, models: List[Any]):
        """
        Initialize simple ensemble.

        Args:
            models: List of fitted models or model results
        """
        if not models:
            raise ValueError("Need at least one model")

        self.models = models
        self.n_models = len(models)

        logger.info(f"SimpleEnsemble initialized with {self.n_models} models")

    def predict(
        self, n_steps: int = 10, return_individual: bool = False, **kwargs
    ) -> Union[np.ndarray, EnsembleResult]:
        """
        Generate ensemble predictions via simple averaging.

        Args:
            n_steps: Number of steps to predict
            return_individual: If True, return EnsembleResult with individual predictions
            **kwargs: Additional arguments for model prediction

        Returns:
            Array of predictions or EnsembleResult object
        """
        predictions_list = []

        for i, model in enumerate(self.models):
            try:
                # Try different prediction methods
                if hasattr(model, "forecast"):
                    pred = model.forecast(steps=n_steps, **kwargs)
                elif hasattr(model, "predict"):
                    pred = model.predict(n_steps=n_steps, **kwargs)
                elif hasattr(model, "result") and hasattr(model.result, "forecast"):
                    pred = model.result.forecast(steps=n_steps)
                else:
                    logger.warning(f"Model {i} has no prediction method")
                    continue

                # Handle different return types
                if isinstance(pred, tuple):
                    pred = pred[0]  # Take mean if (mean, std) returned
                elif hasattr(pred, "values"):
                    pred = pred.values  # pandas Series/DataFrame
                elif hasattr(pred, "mean"):
                    pred = pred.mean(axis=0)  # Multiple samples

                predictions_list.append(np.asarray(pred).flatten()[:n_steps])

            except Exception as e:
                logger.warning(f"Model {i} prediction failed: {e}")

        if not predictions_list:
            raise ValueError("No models produced valid predictions")

        # Simple average
        ensemble_pred = np.mean(predictions_list, axis=0)

        # Calculate uncertainty as standard deviation across models
        uncertainty = np.std(predictions_list, axis=0)

        if return_individual:
            return EnsembleResult(
                predictions=ensemble_pred,
                model_predictions=predictions_list,
                weights=np.ones(len(predictions_list)) / len(predictions_list),
                uncertainty=uncertainty,
                n_models=len(predictions_list),
                metrics={"ensemble_method": "simple_average"},
            )
        else:
            return ensemble_pred

    def evaluate(
        self, y_true: np.ndarray, n_steps: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Evaluate ensemble performance.

        Args:
            y_true: True values
            n_steps: Number of steps (default: length of y_true)

        Returns:
            Dictionary of evaluation metrics
        """
        if n_steps is None:
            n_steps = len(y_true)

        result = self.predict(n_steps=n_steps, return_individual=True)

        metrics = {
            "rmse": np.sqrt(mean_squared_error(y_true, result.predictions)),
            "mae": mean_absolute_error(y_true, result.predictions),
            "n_models": result.n_models,
        }

        # Individual model performance
        for i, pred in enumerate(result.model_predictions):
            metrics[f"model_{i}_rmse"] = np.sqrt(mean_squared_error(y_true, pred))

        return metrics


class WeightedEnsemble:
    """
    Weighted ensemble with optimized or manual weights.

    Uses inverse error weighting or cross-validation to optimize weights.
    """

    def __init__(
        self,
        models: List[Any],
        weights: Optional[np.ndarray] = None,
        optimize_weights: bool = True,
    ):
        """
        Initialize weighted ensemble.

        Args:
            models: List of fitted models
            weights: Manual weights (if None, will be optimized)
            optimize_weights: Whether to optimize weights automatically
        """
        if not models:
            raise ValueError("Need at least one model")

        self.models = models
        self.n_models = len(models)
        self.optimize_weights = optimize_weights

        if weights is not None:
            if len(weights) != self.n_models:
                raise ValueError(
                    f"Weights length {len(weights)} != n_models {self.n_models}"
                )
            self.weights = np.array(weights)
            self.weights = self.weights / self.weights.sum()  # Normalize
        else:
            # Equal weights initially
            self.weights = np.ones(self.n_models) / self.n_models

        logger.info(f"WeightedEnsemble initialized with {self.n_models} models")

    def fit_weights(
        self, y_train: np.ndarray, predictions: List[np.ndarray]
    ) -> np.ndarray:
        """
        Optimize weights based on validation performance.

        Args:
            y_train: Training targets
            predictions: List of predictions from each model

        Returns:
            Optimized weights
        """
        n_models = len(predictions)

        # Compute inverse RMSE as weights (better models get higher weight)
        rmse_scores = []
        for pred in predictions:
            pred = pred[: len(y_train)]  # Align lengths
            rmse = np.sqrt(mean_squared_error(y_train, pred))
            rmse_scores.append(rmse)

        rmse_scores = np.array(rmse_scores)

        # Inverse weighting (add small constant to avoid division by zero)
        inv_rmse = 1.0 / (rmse_scores + 1e-6)
        weights = inv_rmse / inv_rmse.sum()

        logger.info(f"Optimized weights: {weights}")

        return weights

    def predict(
        self, n_steps: int = 10, return_individual: bool = False, **kwargs
    ) -> Union[np.ndarray, EnsembleResult]:
        """
        Generate weighted ensemble predictions.

        Args:
            n_steps: Number of steps to predict
            return_individual: If True, return EnsembleResult
            **kwargs: Additional arguments for model prediction

        Returns:
            Array of predictions or EnsembleResult object
        """
        predictions_list = []

        for i, model in enumerate(self.models):
            try:
                if hasattr(model, "forecast"):
                    pred = model.forecast(steps=n_steps, **kwargs)
                elif hasattr(model, "predict"):
                    pred = model.predict(n_steps=n_steps, **kwargs)
                else:
                    continue

                # Normalize prediction format
                if isinstance(pred, tuple):
                    pred = pred[0]
                elif hasattr(pred, "values"):
                    pred = pred.values
                elif hasattr(pred, "mean"):
                    pred = pred.mean(axis=0)

                predictions_list.append(np.asarray(pred).flatten()[:n_steps])

            except Exception as e:
                logger.warning(f"Model {i} prediction failed: {e}")

        if not predictions_list:
            raise ValueError("No models produced valid predictions")

        # Ensure weights match number of successful predictions
        active_weights = self.weights[: len(predictions_list)]
        active_weights = active_weights / active_weights.sum()

        # Weighted average
        ensemble_pred = np.average(predictions_list, axis=0, weights=active_weights)

        # Uncertainty (weighted std)
        squared_diffs = [(pred - ensemble_pred) ** 2 for pred in predictions_list]
        uncertainty = np.sqrt(np.average(squared_diffs, axis=0, weights=active_weights))

        if return_individual:
            return EnsembleResult(
                predictions=ensemble_pred,
                model_predictions=predictions_list,
                weights=active_weights,
                uncertainty=uncertainty,
                n_models=len(predictions_list),
                metrics={"ensemble_method": "weighted_average"},
            )
        else:
            return ensemble_pred


class StackingEnsemble:
    """
    Stacking ensemble using meta-learning.

    Trains a meta-model on base model predictions.
    """

    def __init__(
        self,
        base_models: List[Any],
        meta_model: Union[str, Any] = "ridge",
        cv_folds: int = 5,
    ):
        """
        Initialize stacking ensemble.

        Args:
            base_models: List of base models
            meta_model: Meta-learner ('ridge', 'lasso', or sklearn model)
            cv_folds: Number of CV folds for meta-training
        """
        if not base_models:
            raise ValueError("Need at least one base model")

        self.base_models = base_models
        self.n_models = len(base_models)
        self.cv_folds = cv_folds

        # Initialize meta-model
        if isinstance(meta_model, str):
            if meta_model == "ridge":
                self.meta_model = Ridge(alpha=1.0)
            elif meta_model == "lasso":
                self.meta_model = Lasso(alpha=1.0)
            else:
                raise ValueError(f"Unknown meta_model: {meta_model}")
        else:
            self.meta_model = meta_model

        self.is_fitted = False

        logger.info(
            f"StackingEnsemble initialized: {self.n_models} base models, meta={type(self.meta_model).__name__}"
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "StackingEnsemble":
        """
        Fit stacking ensemble on training data.

        Args:
            X: Training features
            y: Training targets

        Returns:
            Self
        """
        logger.info("Fitting stacking ensemble...")

        # Generate meta-features via cross-validation
        meta_features = self._generate_meta_features(X, y)

        # Train meta-model on meta-features
        self.meta_model.fit(meta_features, y)

        self.is_fitted = True

        logger.info("Stacking ensemble fitted successfully")

        return self

    def _generate_meta_features(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Generate meta-features using cross-validation.

        Args:
            X: Features
            y: Targets

        Returns:
            Meta-features (n_samples x n_models)
        """
        n_samples = len(X)
        meta_features = np.zeros((n_samples, self.n_models))

        kfold = KFold(n_splits=self.cv_folds, shuffle=True, random_state=42)

        for fold_idx, (train_idx, val_idx) in enumerate(kfold.split(X)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train = y[train_idx]

            # Train each base model and predict on validation set
            for model_idx, model in enumerate(self.base_models):
                try:
                    # Fit model
                    if hasattr(model, "fit"):
                        model.fit(X_train, y_train)

                    # Predict
                    if hasattr(model, "predict"):
                        pred = model.predict(X_val)
                    else:
                        continue

                    meta_features[val_idx, model_idx] = pred.flatten()

                except Exception as e:
                    logger.warning(
                        f"Base model {model_idx} failed in fold {fold_idx}: {e}"
                    )

        return meta_features

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate stacked predictions.

        Args:
            X: Features

        Returns:
            Predictions
        """
        if not self.is_fitted:
            raise ValueError("Ensemble not fitted. Call fit() first.")

        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            try:
                if hasattr(model, "predict"):
                    pred = model.predict(X)
                    base_predictions.append(pred.flatten())
            except Exception as e:
                logger.warning(f"Base model prediction failed: {e}")

        if not base_predictions:
            raise ValueError("No base models produced predictions")

        # Stack predictions as meta-features
        meta_features = np.column_stack(base_predictions)

        # Meta-model prediction
        ensemble_pred = self.meta_model.predict(meta_features)

        return ensemble_pred


class DynamicEnsemble:
    """
    Dynamic ensemble with adaptive model selection.

    Selects best models dynamically based on recent performance.
    """

    def __init__(
        self,
        models: List[Any],
        window_size: int = 10,
        selection_metric: str = "mae",
        top_k: int = 3,
    ):
        """
        Initialize dynamic ensemble.

        Args:
            models: List of models
            window_size: Window size for performance tracking
            selection_metric: Metric for model selection ('mae', 'rmse')
            top_k: Number of top models to use
        """
        if not models:
            raise ValueError("Need at least one model")

        self.models = models
        self.n_models = len(models)
        self.window_size = window_size
        self.selection_metric = selection_metric
        self.top_k = min(top_k, self.n_models)

        # Performance tracking
        self.performance_history = [[] for _ in range(self.n_models)]

        logger.info(
            f"DynamicEnsemble initialized: {self.n_models} models, top_k={top_k}"
        )

    def update_performance(self, y_true: float, predictions: List[float]) -> None:
        """
        Update performance history with new observation.

        Args:
            y_true: True value
            predictions: List of model predictions
        """
        for i, pred in enumerate(predictions):
            if self.selection_metric == "mae":
                error = abs(y_true - pred)
            elif self.selection_metric == "rmse":
                error = (y_true - pred) ** 2
            else:
                error = abs(y_true - pred)

            self.performance_history[i].append(error)

            # Maintain window size
            if len(self.performance_history[i]) > self.window_size:
                self.performance_history[i].pop(0)

    def select_models(self) -> List[int]:
        """
        Select top-k models based on recent performance.

        Returns:
            Indices of selected models
        """
        if all(len(h) == 0 for h in self.performance_history):
            # No history yet, use all models
            return list(range(min(self.top_k, self.n_models)))

        # Compute average error for each model
        avg_errors = []
        for i in range(self.n_models):
            if len(self.performance_history[i]) > 0:
                avg_error = np.mean(self.performance_history[i])
            else:
                avg_error = float("inf")
            avg_errors.append(avg_error)

        # Select top-k models (lowest error)
        selected_indices = np.argsort(avg_errors)[: self.top_k]

        return list(selected_indices)

    def predict(self, n_steps: int = 1, **kwargs) -> Tuple[np.ndarray, List[int]]:
        """
        Generate dynamic ensemble prediction.

        Args:
            n_steps: Number of steps
            **kwargs: Additional arguments

        Returns:
            Tuple of (predictions, selected_model_indices)
        """
        # Select best models
        selected = self.select_models()

        logger.info(f"Selected models: {selected}")

        # Get predictions from selected models
        predictions_list = []
        for idx in selected:
            model = self.models[idx]
            try:
                if hasattr(model, "forecast"):
                    pred = model.forecast(steps=n_steps, **kwargs)
                elif hasattr(model, "predict"):
                    pred = model.predict(n_steps=n_steps, **kwargs)
                else:
                    continue

                if isinstance(pred, tuple):
                    pred = pred[0]

                predictions_list.append(np.asarray(pred).flatten()[:n_steps])

            except Exception as e:
                logger.warning(f"Model {idx} failed: {e}")

        if not predictions_list:
            raise ValueError("No selected models produced predictions")

        # Average selected models
        ensemble_pred = np.mean(predictions_list, axis=0)

        return ensemble_pred, selected


__all__ = [
    "SimpleEnsemble",
    "WeightedEnsemble",
    "StackingEnsemble",
    "DynamicEnsemble",
    "EnsembleResult",
]
