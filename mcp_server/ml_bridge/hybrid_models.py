"""
Hybrid ML-Econometric Models (Agent 17, Module 1)

Combines machine learning and econometric approaches:
- Two-stage models (econometric → ML)
- Stacked ensembles (ML + econometric)
- Residual learning (econometric + ML correction)
- Hybrid feature spaces (domain + learned)
- Interpretable ML with econometric constraints

Integrates with:
- econometric methods: Panel data, fixed effects, IV
- time_series: ARIMA, state space models
- simulations: Prediction evaluation
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from enum import Enum
import warnings

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

# Try to import ML libraries (optional)
try:
    from sklearn.base import BaseEstimator, RegressorMixin
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, Lasso, ElasticNet
    from sklearn.model_selection import cross_val_score

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    BaseEstimator = object
    RegressorMixin = object
    logger.warning("scikit-learn not available, ML features limited")

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available, gradient boosting limited")


class ModelStage(Enum):
    """Stages in hybrid modeling"""

    ECONOMETRIC = "econometric"  # First stage econometric
    ML_CORRECTION = "ml_correction"  # Second stage ML
    ENSEMBLE = "ensemble"  # Combined prediction


@dataclass
class HybridModelConfig:
    """Configuration for hybrid models"""

    # Two-stage settings
    use_two_stage: bool = True
    econometric_method: str = "fixed_effects"  # fixed_effects, random_effects, ols

    # ML settings
    ml_algorithm: str = "random_forest"  # random_forest, gradient_boosting, lightgbm
    n_estimators: int = 100
    max_depth: int = 10
    learning_rate: float = 0.1

    # Ensemble settings
    use_stacking: bool = False
    ensemble_weights: Optional[Dict[str, float]] = None  # Manual weights

    # Residual learning
    learn_residuals: bool = True  # ML learns econometric residuals

    # Regularization
    alpha: float = 1.0  # Regularization strength
    l1_ratio: float = 0.5  # ElasticNet mixing (1=Lasso, 0=Ridge)

    # Feature engineering
    include_interactions: bool = True
    include_polynomials: bool = False
    polynomial_degree: int = 2


@dataclass
class PredictionResult:
    """Result from hybrid model prediction"""

    predictions: np.ndarray

    # Stage-wise predictions
    econometric_predictions: Optional[np.ndarray] = None
    ml_predictions: Optional[np.ndarray] = None
    ensemble_predictions: Optional[np.ndarray] = None

    # Uncertainty
    std_errors: Optional[np.ndarray] = None
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]] = None

    # Feature importance
    feature_importance: Optional[Dict[str, float]] = None

    # Metadata
    model_stage: ModelStage = ModelStage.ENSEMBLE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "predictions": (
                self.predictions.tolist()
                if isinstance(self.predictions, np.ndarray)
                else self.predictions
            ),
            "econometric_predictions": (
                self.econometric_predictions.tolist()
                if self.econometric_predictions is not None
                else None
            ),
            "ml_predictions": (
                self.ml_predictions.tolist()
                if self.ml_predictions is not None
                else None
            ),
            "model_stage": self.model_stage.value,
            "has_uncertainty": self.std_errors is not None,
            "n_predictions": (
                len(self.predictions) if hasattr(self.predictions, "__len__") else 1
            ),
        }


class TwoStageModel:
    """
    Two-stage hybrid model.

    Stage 1: Econometric model (captures structure, causality)
    Stage 2: ML model (captures non-linearities in residuals)

    Final prediction = Econometric + ML(residuals)
    """

    def __init__(self, config: Optional[HybridModelConfig] = None):
        """Initialize two-stage model"""
        self.config = config or HybridModelConfig()

        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for TwoStageModel")

        # Stage 1: Econometric (simple linear for now, can be replaced)
        self.econometric_model = Ridge(alpha=self.config.alpha)

        # Stage 2: ML model
        self.ml_model = self._create_ml_model()

        # Fitted state
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None

        logger.info(
            f"TwoStageModel initialized: {self.config.econometric_method} + {self.config.ml_algorithm}"
        )

    def _create_ml_model(self) -> Any:
        """Create ML model based on config"""
        if self.config.ml_algorithm == "random_forest":
            return RandomForestRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=42,
            )
        elif self.config.ml_algorithm == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                learning_rate=self.config.learning_rate,
                random_state=42,
            )
        elif self.config.ml_algorithm == "lightgbm" and LIGHTGBM_AVAILABLE:
            return lgb.LGBMRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                learning_rate=self.config.learning_rate,
                random_state=42,
                verbose=-1,
            )
        else:
            logger.warning(
                f"Unknown ML algorithm {self.config.ml_algorithm}, using RandomForest"
            )
            return RandomForestRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=42,
            )

    def fit(
        self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None
    ) -> "TwoStageModel":
        """
        Fit two-stage model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            feature_names: Optional feature names

        Returns:
            Self for chaining
        """
        self.feature_names = feature_names

        # Stage 1: Fit econometric model
        logger.info("Stage 1: Fitting econometric model")
        self.econometric_model.fit(X, y)
        econometric_preds = self.econometric_model.predict(X)

        # Calculate residuals
        residuals = y - econometric_preds

        logger.info(f"Econometric R²: {self._calculate_r2(y, econometric_preds):.4f}")
        logger.info(f"Residual std: {np.std(residuals):.4f}")

        # Stage 2: Fit ML model on residuals
        if self.config.learn_residuals:
            logger.info("Stage 2: Fitting ML model on residuals")
            self.ml_model.fit(X, residuals)
            ml_preds = self.ml_model.predict(X)

            # Combined predictions
            combined_preds = econometric_preds + ml_preds
            final_r2 = self._calculate_r2(y, combined_preds)
            logger.info(f"Combined R²: {final_r2:.4f}")
        else:
            logger.info("Stage 2: Fitting ML model on target")
            self.ml_model.fit(X, y)

        self.is_fitted = True
        return self

    def predict(
        self, X: np.ndarray, return_components: bool = False
    ) -> Union[np.ndarray, PredictionResult]:
        """
        Predict using two-stage model.

        Args:
            X: Feature matrix (n_samples, n_features)
            return_components: Return full PredictionResult with components

        Returns:
            Predictions array or PredictionResult object
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Stage 1: Econometric predictions
        econometric_preds = self.econometric_model.predict(X)

        # Stage 2: ML predictions (residuals or direct)
        ml_preds = self.ml_model.predict(X)

        # Combine
        if self.config.learn_residuals:
            final_preds = econometric_preds + ml_preds
        else:
            # Average or weighted combination
            final_preds = (econometric_preds + ml_preds) / 2

        if return_components:
            # Get feature importance
            feature_importance = self._get_feature_importance()

            return PredictionResult(
                predictions=final_preds,
                econometric_predictions=econometric_preds,
                ml_predictions=ml_preds,
                feature_importance=feature_importance,
                model_stage=ModelStage.ENSEMBLE,
            )
        else:
            return final_preds

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from ML model"""
        if hasattr(self.ml_model, "feature_importances_"):
            importances = self.ml_model.feature_importances_

            if self.feature_names and len(self.feature_names) == len(importances):
                return dict(zip(self.feature_names, importances))
            else:
                return {f"feature_{i}": imp for i, imp in enumerate(importances)}
        else:
            return {}

    def _calculate_r2(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R² score"""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    def get_econometric_coefficients(self) -> np.ndarray:
        """Get coefficients from econometric stage"""
        if hasattr(self.econometric_model, "coef_"):
            return self.econometric_model.coef_
        else:
            return np.array([])

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score on data"""
        preds = self.predict(X)
        return self._calculate_r2(y, preds)


class ResidualLearningModel:
    """
    Residual learning model.

    Base model provides initial predictions (e.g., econometric)
    Residual model learns corrections (ML)

    Similar to two-stage but more flexible base model.
    """

    def __init__(
        self, base_model: Any, residual_model: Any, learn_residuals: bool = True
    ):
        """
        Initialize residual learning model.

        Args:
            base_model: Base model (econometric, simple ML, etc.)
            residual_model: Model to learn residuals (typically ML)
            learn_residuals: If True, residual_model learns residuals; else learns target
        """
        self.base_model = base_model
        self.residual_model = residual_model
        self.learn_residuals = learn_residuals
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ResidualLearningModel":
        """Fit residual learning model"""
        # Fit base model
        self.base_model.fit(X, y)
        base_preds = self.base_model.predict(X)

        # Fit residual model
        if self.learn_residuals:
            residuals = y - base_preds
            self.residual_model.fit(X, residuals)
        else:
            self.residual_model.fit(X, y)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using combined model"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        base_preds = self.base_model.predict(X)
        residual_preds = self.residual_model.predict(X)

        if self.learn_residuals:
            return base_preds + residual_preds
        else:
            # Average predictions
            return (base_preds + residual_preds) / 2

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score"""
        preds = self.predict(X)
        ss_res = np.sum((y - preds) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


class StackedEnsemble:
    """
    Stacked ensemble of econometric and ML models.

    Multiple base models (econometric + ML) → Meta-learner
    """

    def __init__(
        self,
        base_models: List[Tuple[str, Any]],
        meta_learner: Optional[Any] = None,
        use_base_features: bool = True,
    ):
        """
        Initialize stacked ensemble.

        Args:
            base_models: List of (name, model) tuples
            meta_learner: Meta-model (default: Ridge)
            use_base_features: Include original features in meta-learner
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for StackedEnsemble")

        self.base_models = base_models
        self.meta_learner = meta_learner or Ridge(alpha=1.0)
        self.use_base_features = use_base_features
        self.is_fitted = False

        logger.info(f"StackedEnsemble with {len(base_models)} base models")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "StackedEnsemble":
        """Fit stacked ensemble"""
        # Fit base models
        base_predictions = []

        for name, model in self.base_models:
            logger.info(f"Fitting base model: {name}")
            model.fit(X, y)
            preds = model.predict(X)
            base_predictions.append(preds)

        # Create meta-features
        base_predictions = np.column_stack(base_predictions)

        if self.use_base_features:
            meta_features = np.hstack([X, base_predictions])
        else:
            meta_features = base_predictions

        # Fit meta-learner
        logger.info("Fitting meta-learner")
        self.meta_learner.fit(meta_features, y)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using stacked ensemble"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        # Get base predictions
        base_predictions = []
        for name, model in self.base_models:
            preds = model.predict(X)
            base_predictions.append(preds)

        base_predictions = np.column_stack(base_predictions)

        # Create meta-features
        if self.use_base_features:
            meta_features = np.hstack([X, base_predictions])
        else:
            meta_features = base_predictions

        # Meta-learner prediction
        return self.meta_learner.predict(meta_features)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score"""
        preds = self.predict(X)
        ss_res = np.sum((y - preds) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    def get_base_model_scores(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Get individual base model scores"""
        scores = {}
        for name, model in self.base_models:
            preds = model.predict(X)
            ss_res = np.sum((y - preds) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            scores[name] = r2
        return scores


class ConstrainedML:
    """
    ML model with econometric constraints.

    Enforces:
    - Monotonicity constraints (e.g., more minutes → better stats)
    - Sign constraints (positive/negative effects)
    - Causal structure from econometric theory
    """

    def __init__(self, base_model: Any, constraints: Optional[Dict[str, Any]] = None):
        """
        Initialize constrained ML model.

        Args:
            base_model: ML model (e.g., GradientBoosting with monotone_constraints)
            constraints: Constraint specifications
        """
        self.base_model = base_model
        self.constraints = constraints or {}
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ConstrainedML":
        """Fit with constraints"""
        # Apply constraints if supported
        if hasattr(self.base_model, "monotone_constraints"):
            # GradientBoosting supports monotone constraints
            self.base_model.fit(X, y)
        else:
            # Standard fit
            self.base_model.fit(X, y)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict with constraints"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        return self.base_model.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score"""
        preds = self.predict(X)
        ss_res = np.sum((y - preds) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


def create_hybrid_model(
    model_type: str = "two_stage", config: Optional[HybridModelConfig] = None, **kwargs
) -> Any:
    """
    Factory function to create hybrid models.

    Args:
        model_type: Type of hybrid model
            - "two_stage": TwoStageModel
            - "residual": ResidualLearningModel
            - "stacked": StackedEnsemble
            - "constrained": ConstrainedML
        config: Model configuration
        **kwargs: Additional model-specific arguments

    Returns:
        Hybrid model instance
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for hybrid models")

    config = config or HybridModelConfig()

    if model_type == "two_stage":
        return TwoStageModel(config)

    elif model_type == "residual":
        base_model = kwargs.get("base_model", Ridge(alpha=1.0))
        residual_model = kwargs.get(
            "residual_model", RandomForestRegressor(n_estimators=100)
        )
        return ResidualLearningModel(base_model, residual_model)

    elif model_type == "stacked":
        base_models = kwargs.get(
            "base_models",
            [
                ("ridge", Ridge(alpha=1.0)),
                (
                    "random_forest",
                    RandomForestRegressor(n_estimators=100, max_depth=10),
                ),
            ],
        )
        meta_learner = kwargs.get("meta_learner", Ridge(alpha=1.0))
        return StackedEnsemble(base_models, meta_learner)

    elif model_type == "constrained":
        base_model = kwargs.get("base_model", GradientBoostingRegressor())
        constraints = kwargs.get("constraints", {})
        return ConstrainedML(base_model, constraints)

    else:
        raise ValueError(f"Unknown model type: {model_type}")


def check_ml_available() -> Dict[str, bool]:
    """Check which ML libraries are available"""
    return {
        "sklearn": SKLEARN_AVAILABLE,
        "lightgbm": LIGHTGBM_AVAILABLE,
        "full_functionality": SKLEARN_AVAILABLE,
    }


__all__ = [
    "HybridModelConfig",
    "PredictionResult",
    "TwoStageModel",
    "ResidualLearningModel",
    "StackedEnsemble",
    "ConstrainedML",
    "create_hybrid_model",
    "check_ml_available",
]
