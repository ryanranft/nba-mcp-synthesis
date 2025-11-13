"""
Multi-Model Ensemble System (Agent 19, Module 1)

Combine predictions from multiple models across the toolkit:
- Econometric + ML ensembles
- Time series + spatial ensembles
- Network + simulation ensembles
- Weighted averaging, stacking, voting
- Model selection based on context
- Uncertainty quantification

Integrates with:
- ml_bridge: Hybrid models and stacking
- All models: Universal ensemble framework
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from enum import Enum

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class EnsembleMethod(Enum):
    """Ensemble combination methods"""

    AVERAGE = "average"  # Simple average
    WEIGHTED_AVERAGE = "weighted_average"  # Weighted by performance
    MEDIAN = "median"  # Median prediction
    STACKING = "stacking"  # Meta-learner
    VOTING = "voting"  # Majority vote (classification)
    BEST_MODEL = "best_model"  # Select single best


@dataclass
class EnsembleConfig:
    """Configuration for ensemble"""

    method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE

    # Weights (for weighted average)
    model_weights: Optional[Dict[str, float]] = None

    # Weight calculation
    weight_by: str = "test_score"  # test_score, cv_score, aic, bic

    # Stacking
    meta_learner: Optional[Any] = None

    # Selection
    selection_metric: str = "rmse"  # rmse, mae, r2

    # Uncertainty
    compute_uncertainty: bool = True
    confidence_level: float = 0.95


@dataclass
class EnsemblePrediction:
    """Ensemble prediction result"""

    predictions: np.ndarray

    # Individual model predictions
    model_predictions: Dict[str, np.ndarray] = field(default_factory=dict)

    # Uncertainty
    std_errors: Optional[np.ndarray] = None
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]] = None

    # Weights used
    model_weights: Optional[Dict[str, float]] = None

    # Best model (if selection used)
    best_model_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "predictions": self.predictions.tolist(),
            "model_predictions": {
                name: preds.tolist() for name, preds in self.model_predictions.items()
            },
            "has_uncertainty": self.std_errors is not None,
            "model_weights": self.model_weights,
            "best_model": self.best_model_name,
        }


class ModelEnsemble:
    """
    Multi-model ensemble system.

    Features:
    - Combine predictions from diverse models
    - Automatic weight optimization
    - Uncertainty quantification
    - Model selection based on context
    """

    def __init__(self, config: Optional[EnsembleConfig] = None):
        """Initialize ensemble"""
        self.config = config or EnsembleConfig()
        self.models: Dict[str, Any] = {}
        self.model_scores: Dict[str, float] = {}
        self.is_fitted = False

        logger.info(
            f"ModelEnsemble initialized with method: {self.config.method.value}"
        )

    def add_model(self, name: str, model: Any, score: Optional[float] = None):
        """
        Add model to ensemble.

        Args:
            name: Model identifier
            model: Fitted model with predict() method
            score: Performance score (higher is better)
        """
        self.models[name] = model
        if score is not None:
            self.model_scores[name] = score

        logger.info(f"Added model '{name}' to ensemble")

    def _calculate_weights(self) -> Dict[str, float]:
        """
        Calculate ensemble weights from model scores.

        Returns:
            Dictionary of model weights (sum to 1)
        """
        if self.config.model_weights is not None:
            # Use specified weights
            weights = self.config.model_weights.copy()
        elif self.model_scores:
            # Calculate from scores
            scores = np.array(list(self.model_scores.values()))

            # Convert to weights (softmax for positive)
            if np.all(scores > 0):
                exp_scores = np.exp(scores - np.max(scores))  # Numerical stability
                weights_array = exp_scores / np.sum(exp_scores)
            else:
                # Rank-based weights
                ranks = stats.rankdata(scores)
                weights_array = ranks / np.sum(ranks)

            weights = dict(zip(self.model_scores.keys(), weights_array))
        else:
            # Equal weights
            n = len(self.models)
            weights = {name: 1.0 / n for name in self.models.keys()}

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def predict(
        self, X: np.ndarray, return_details: bool = False
    ) -> Union[np.ndarray, EnsemblePrediction]:
        """
        Generate ensemble predictions.

        Args:
            X: Feature matrix
            return_details: Return full EnsemblePrediction object

        Returns:
            Predictions array or EnsemblePrediction object
        """
        if not self.models:
            raise ValueError("No models in ensemble")

        # Collect predictions from all models
        all_predictions = {}

        for name, model in self.models.items():
            try:
                preds = model.predict(X)
                all_predictions[name] = preds
            except Exception as e:
                logger.warning(f"Model '{name}' prediction failed: {e}")

        if not all_predictions:
            raise ValueError("No models produced predictions")

        # Combine predictions based on method
        if self.config.method == EnsembleMethod.AVERAGE:
            predictions = self._average_predictions(all_predictions)
            weights = {name: 1.0 / len(all_predictions) for name in all_predictions}

        elif self.config.method == EnsembleMethod.WEIGHTED_AVERAGE:
            weights = self._calculate_weights()
            predictions = self._weighted_average_predictions(all_predictions, weights)

        elif self.config.method == EnsembleMethod.MEDIAN:
            predictions = self._median_predictions(all_predictions)
            weights = None

        elif self.config.method == EnsembleMethod.BEST_MODEL:
            predictions, best_model = self._best_model_prediction(all_predictions)
            weights = None
        else:
            predictions = self._average_predictions(all_predictions)
            weights = None

        # Calculate uncertainty if requested
        if self.config.compute_uncertainty:
            std_errors, ci = self._calculate_uncertainty(all_predictions, predictions)
        else:
            std_errors, ci = None, None

        if return_details:
            result = EnsemblePrediction(
                predictions=predictions,
                model_predictions=all_predictions,
                std_errors=std_errors,
                confidence_intervals=ci,
                model_weights=weights,
                best_model_name=(
                    best_model
                    if self.config.method == EnsembleMethod.BEST_MODEL
                    else None
                ),
            )
            return result
        else:
            return predictions

    def _average_predictions(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Simple average of predictions"""
        pred_matrix = np.column_stack(list(predictions.values()))
        return np.mean(pred_matrix, axis=1)

    def _weighted_average_predictions(
        self, predictions: Dict[str, np.ndarray], weights: Dict[str, float]
    ) -> np.ndarray:
        """Weighted average of predictions"""
        weighted_sum = np.zeros(len(next(iter(predictions.values()))))

        for name, preds in predictions.items():
            weight = weights.get(name, 0.0)
            weighted_sum += weight * preds

        return weighted_sum

    def _median_predictions(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Median of predictions"""
        pred_matrix = np.column_stack(list(predictions.values()))
        return np.median(pred_matrix, axis=1)

    def _best_model_prediction(
        self, predictions: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, str]:
        """Select best model's predictions"""
        if self.model_scores:
            best_model = max(self.model_scores.items(), key=lambda x: x[1])[0]
        else:
            best_model = next(iter(predictions.keys()))

        return predictions[best_model], best_model

    def _calculate_uncertainty(
        self, all_predictions: Dict[str, np.ndarray], ensemble_pred: np.ndarray
    ) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Calculate prediction uncertainty.

        Uses variance across models as measure of uncertainty.
        """
        pred_matrix = np.column_stack(list(all_predictions.values()))

        # Standard error (standard deviation across models)
        std_errors = np.std(pred_matrix, axis=1)

        # Confidence intervals
        z_score = stats.norm.ppf((1 + self.config.confidence_level) / 2)
        lower = ensemble_pred - z_score * std_errors
        upper = ensemble_pred + z_score * std_errors

        return std_errors, (lower, upper)

    def evaluate(self, X: np.ndarray, y_true: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate ensemble performance.

        Args:
            X: Features
            y_true: True values

        Returns:
            Dictionary with metrics
        """
        # Ensemble predictions
        ensemble_pred = self.predict(X)

        # Individual model predictions
        individual_metrics = {}
        for name, model in self.models.items():
            try:
                preds = model.predict(X)
                rmse = np.sqrt(np.mean((y_true - preds) ** 2))
                mae = np.mean(np.abs(y_true - preds))
                individual_metrics[name] = {"rmse": rmse, "mae": mae}
            except:
                individual_metrics[name] = {"rmse": np.inf, "mae": np.inf}

        # Ensemble metrics
        ensemble_rmse = np.sqrt(np.mean((y_true - ensemble_pred) ** 2))
        ensemble_mae = np.mean(np.abs(y_true - ensemble_pred))

        # Best individual model
        best_model = min(individual_metrics.items(), key=lambda x: x[1]["rmse"])

        results = {
            "ensemble_rmse": ensemble_rmse,
            "ensemble_mae": ensemble_mae,
            "individual_metrics": individual_metrics,
            "best_individual_model": best_model[0],
            "best_individual_rmse": best_model[1]["rmse"],
            "improvement_over_best": (best_model[1]["rmse"] - ensemble_rmse)
            / best_model[1]["rmse"],
        }

        logger.info(
            f"Ensemble RMSE: {ensemble_rmse:.4f}, Best individual: {best_model[1]['rmse']:.4f}"
        )

        return results


class ContextualEnsemble:
    """
    Context-aware ensemble that selects models based on input characteristics.

    Example: Use spatial models for location-based predictions,
             time series models for temporal predictions, etc.
    """

    def __init__(self):
        """Initialize contextual ensemble"""
        self.model_groups: Dict[str, ModelEnsemble] = {}
        self.context_selector: Optional[Callable] = None

        logger.info("ContextualEnsemble initialized")

    def add_model_group(self, context: str, ensemble: ModelEnsemble):
        """
        Add model ensemble for specific context.

        Args:
            context: Context identifier
            ensemble: ModelEnsemble for this context
        """
        self.model_groups[context] = ensemble
        logger.info(f"Added model group for context: {context}")

    def set_context_selector(self, selector: Callable):
        """
        Set function to select context from input.

        Args:
            selector: Function X -> context_name
        """
        self.context_selector = selector

    def predict(self, X: np.ndarray, context: Optional[str] = None) -> np.ndarray:
        """
        Predict with context selection.

        Args:
            X: Features
            context: Optional context override

        Returns:
            Predictions
        """
        if context is None and self.context_selector is not None:
            context = self.context_selector(X)
        elif context is None:
            # Default to first available context
            context = next(iter(self.model_groups.keys()))

        if context not in self.model_groups:
            raise ValueError(f"Unknown context: {context}")

        ensemble = self.model_groups[context]
        return ensemble.predict(X)


def create_ensemble(
    models: Dict[str, Any],
    scores: Optional[Dict[str, float]] = None,
    method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE,
) -> ModelEnsemble:
    """
    Convenience function to create ensemble.

    Args:
        models: Dictionary of {name: model}
        scores: Optional scores for weighting
        method: Ensemble method

    Returns:
        ModelEnsemble
    """
    config = EnsembleConfig(method=method)
    ensemble = ModelEnsemble(config)

    for name, model in models.items():
        score = scores.get(name) if scores else None
        ensemble.add_model(name, model, score)

    return ensemble


__all__ = [
    "EnsembleMethod",
    "EnsembleConfig",
    "EnsemblePrediction",
    "ModelEnsemble",
    "ContextualEnsemble",
    "create_ensemble",
]
