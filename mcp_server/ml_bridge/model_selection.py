"""
Model Selection and Cross-Validation (Agent 17, Module 3)

Comprehensive model selection framework:
- Time series cross-validation
- Panel data cross-validation
- Hyperparameter tuning
- Model comparison (ML vs econometric)
- Performance metrics
- Model diagnostics

Integrates with:
- hybrid_models: Evaluate hybrid approaches
- prophet_integration: Time series CV
- econometric methods: Compare with ML
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from enum import Enum
import time

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

# Try to import sklearn (optional)
try:
    from sklearn.model_selection import (
        KFold,
        TimeSeriesSplit,
        GroupKFold,
        cross_val_score,
        cross_validate,
    )
    from sklearn.metrics import (
        mean_squared_error,
        mean_absolute_error,
        r2_score,
        mean_absolute_percentage_error,
    )
    from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, cross-validation limited")


class CVStrategy(Enum):
    """Cross-validation strategies"""

    K_FOLD = "k_fold"  # Standard k-fold
    TIME_SERIES = "time_series"  # Expanding window
    GROUP = "group"  # Group by player/team
    BLOCKED = "blocked"  # Block by season/month


@dataclass
class CVConfig:
    """Cross-validation configuration"""

    strategy: CVStrategy = CVStrategy.TIME_SERIES
    n_splits: int = 5
    test_size: Optional[float] = 0.2  # For train/test split
    shuffle: bool = False  # For k-fold

    # Time series specific
    max_train_size: Optional[int] = None  # Limit training window
    gap: int = 0  # Gap between train and test

    # Group specific
    groups: Optional[List[str]] = None  # Player/team IDs


@dataclass
class ModelPerformance:
    """Model performance metrics"""

    model_name: str

    # Fit metrics
    train_score: float
    test_score: float
    cv_scores: List[float] = field(default_factory=list)

    # Error metrics
    rmse: float = 0.0
    mae: float = 0.0
    mape: Optional[float] = None
    r2: float = 0.0

    # Timing
    fit_time: float = 0.0
    predict_time: float = 0.0

    # Additional metrics
    aic: Optional[float] = None
    bic: Optional[float] = None

    @property
    def cv_mean(self) -> float:
        """Mean CV score"""
        return float(np.mean(self.cv_scores)) if self.cv_scores else 0.0

    @property
    def cv_std(self) -> float:
        """Std of CV scores"""
        return float(np.std(self.cv_scores)) if self.cv_scores else 0.0

    @property
    def overfit_gap(self) -> float:
        """Gap between train and test (overfitting indicator)"""
        return self.train_score - self.test_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "model_name": self.model_name,
            "train_score": self.train_score,
            "test_score": self.test_score,
            "cv_mean": self.cv_mean,
            "cv_std": self.cv_std,
            "rmse": self.rmse,
            "mae": self.mae,
            "mape": self.mape,
            "r2": self.r2,
            "overfit_gap": self.overfit_gap,
            "fit_time": self.fit_time,
        }


class CrossValidator:
    """
    Cross-validation for time series and panel data.

    Features:
    - Multiple CV strategies
    - Time-aware splitting
    - Group-based splitting (by player/team)
    - Custom scorers
    - Parallel execution (if joblib available)
    """

    def __init__(self, config: Optional[CVConfig] = None):
        """Initialize cross-validator"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for CrossValidator")

        self.config = config or CVConfig()
        logger.info(
            f"CrossValidator initialized with {self.config.strategy.value} strategy"
        )

    def create_splitter(self) -> Any:
        """Create sklearn splitter based on strategy"""
        if self.config.strategy == CVStrategy.K_FOLD:
            return KFold(
                n_splits=self.config.n_splits,
                shuffle=self.config.shuffle,
                random_state=42,
            )

        elif self.config.strategy == CVStrategy.TIME_SERIES:
            return TimeSeriesSplit(
                n_splits=self.config.n_splits,
                max_train_size=self.config.max_train_size,
                gap=self.config.gap,
            )

        elif self.config.strategy == CVStrategy.GROUP:
            return GroupKFold(n_splits=self.config.n_splits)

        else:
            # Default to time series
            return TimeSeriesSplit(n_splits=self.config.n_splits)

    def cross_validate_model(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        groups: Optional[np.ndarray] = None,
        scoring: Union[str, Callable] = "r2",
    ) -> Dict[str, Any]:
        """
        Perform cross-validation on model.

        Args:
            model: Model with fit/predict interface
            X: Feature matrix
            y: Target vector
            groups: Group labels (for GroupKFold)
            scoring: Scoring metric

        Returns:
            Dictionary with CV results
        """
        splitter = self.create_splitter()

        # Run cross-validation
        if self.config.strategy == CVStrategy.GROUP and groups is not None:
            cv_results = cross_validate(
                model,
                X,
                y,
                cv=splitter,
                groups=groups,
                scoring=scoring,
                return_train_score=True,
                n_jobs=-1,
            )
        else:
            cv_results = cross_validate(
                model,
                X,
                y,
                cv=splitter,
                scoring=scoring,
                return_train_score=True,
                n_jobs=-1,
            )

        # Extract scores
        test_scores = cv_results["test_score"]
        train_scores = cv_results["train_score"]

        logger.info(f"CV: {np.mean(test_scores):.4f} ± {np.std(test_scores):.4f}")

        return {
            "test_scores": test_scores.tolist(),
            "train_scores": train_scores.tolist(),
            "mean_test_score": float(np.mean(test_scores)),
            "std_test_score": float(np.std(test_scores)),
            "mean_train_score": float(np.mean(train_scores)),
            "fit_times": cv_results["fit_time"].tolist(),
        }

    def walk_forward_validation(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        initial_train_size: int,
        step_size: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Walk-forward time series validation.

        Args:
            model: Model to evaluate
            X: Feature matrix
            y: Target vector
            initial_train_size: Initial training set size
            step_size: How many samples to add each iteration

        Returns:
            List of results for each step
        """
        results = []
        n_samples = len(X)

        current_train_size = initial_train_size

        while current_train_size + step_size < n_samples:
            # Train on expanding window
            X_train = X[:current_train_size]
            y_train = y[:current_train_size]

            # Test on next step
            X_test = X[current_train_size : current_train_size + step_size]
            y_test = y[current_train_size : current_train_size + step_size]

            # Fit and predict
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)

            results.append(
                {
                    "train_size": current_train_size,
                    "test_size": step_size,
                    "mse": float(mse),
                    "mae": float(mae),
                }
            )

            current_train_size += step_size

        logger.info(f"Walk-forward validation: {len(results)} steps")

        return results


class HyperparameterTuner:
    """
    Hyperparameter tuning for models.

    Features:
    - Grid search
    - Random search
    - Time series aware CV
    - Custom parameter spaces
    """

    def __init__(self, cv_config: Optional[CVConfig] = None):
        """Initialize hyperparameter tuner"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for HyperparameterTuner")

        self.cv_config = cv_config or CVConfig()
        self.best_params_: Optional[Dict[str, Any]] = None
        self.best_score_: Optional[float] = None

        logger.info("HyperparameterTuner initialized")

    def grid_search(
        self,
        model: Any,
        param_grid: Dict[str, List[Any]],
        X: np.ndarray,
        y: np.ndarray,
        scoring: str = "r2",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        Perform grid search.

        Args:
            model: Base model
            param_grid: Parameter grid
            X: Features
            y: Target
            scoring: Scoring metric
            n_jobs: Parallel jobs

        Returns:
            Best parameters and score
        """
        cv = CrossValidator(self.cv_config).create_splitter()

        search = GridSearchCV(
            model, param_grid, cv=cv, scoring=scoring, n_jobs=n_jobs, verbose=1
        )

        logger.info(f"Running grid search with {len(param_grid)} parameters")
        search.fit(X, y)

        self.best_params_ = search.best_params_
        self.best_score_ = search.best_score_

        logger.info(f"Best score: {self.best_score_:.4f}")
        logger.info(f"Best params: {self.best_params_}")

        return {
            "best_params": self.best_params_,
            "best_score": float(self.best_score_),
            "cv_results": search.cv_results_,
        }

    def random_search(
        self,
        model: Any,
        param_distributions: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        n_iter: int = 10,
        scoring: str = "r2",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        Perform randomized search.

        Args:
            model: Base model
            param_distributions: Parameter distributions
            X: Features
            y: Target
            n_iter: Number of iterations
            scoring: Scoring metric
            n_jobs: Parallel jobs

        Returns:
            Best parameters and score
        """
        cv = CrossValidator(self.cv_config).create_splitter()

        search = RandomizedSearchCV(
            model,
            param_distributions,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            n_jobs=n_jobs,
            random_state=42,
            verbose=1,
        )

        logger.info(f"Running random search with {n_iter} iterations")
        search.fit(X, y)

        self.best_params_ = search.best_params_
        self.best_score_ = search.best_score_

        logger.info(f"Best score: {self.best_score_:.4f}")
        logger.info(f"Best params: {self.best_params_}")

        return {
            "best_params": self.best_params_,
            "best_score": float(self.best_score_),
            "cv_results": search.cv_results_,
        }


class ModelComparator:
    """
    Compare multiple models on same dataset.

    Features:
    - Fair comparison (same CV splits)
    - Statistical significance testing
    - Performance rankings
    - Visualization of results
    """

    def __init__(self, cv_config: Optional[CVConfig] = None):
        """Initialize model comparator"""
        self.cv_config = cv_config or CVConfig()
        self.results: Dict[str, ModelPerformance] = {}

        logger.info("ModelComparator initialized")

    def evaluate_model(
        self,
        name: str,
        model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        groups: Optional[np.ndarray] = None,
    ) -> ModelPerformance:
        """
        Evaluate a single model.

        Args:
            name: Model name
            model: Model instance
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            groups: Optional groups for CV

        Returns:
            ModelPerformance object
        """
        logger.info(f"Evaluating model: {name}")

        # Fit model
        start_fit = time.time()
        model.fit(X_train, y_train)
        fit_time = time.time() - start_fit

        # Predict
        start_pred = time.time()
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        predict_time = time.time() - start_pred

        # Calculate metrics
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        mae = mean_absolute_error(y_test, y_test_pred)

        # MAPE (handle division by zero)
        try:
            mape = mean_absolute_percentage_error(y_test, y_test_pred)
        except:
            mape = None

        # Cross-validation
        if SKLEARN_AVAILABLE:
            cv_validator = CrossValidator(self.cv_config)
            cv_results = cv_validator.cross_validate_model(
                model, X_train, y_train, groups=groups
            )
            cv_scores = cv_results["test_scores"]
        else:
            cv_scores = []

        # Create performance object
        performance = ModelPerformance(
            model_name=name,
            train_score=train_r2,
            test_score=test_r2,
            cv_scores=cv_scores,
            rmse=rmse,
            mae=mae,
            mape=mape,
            r2=test_r2,
            fit_time=fit_time,
            predict_time=predict_time,
        )

        self.results[name] = performance

        logger.info(f"{name} - Test R²: {test_r2:.4f}, RMSE: {rmse:.4f}")

        return performance

    def compare_models(
        self,
        models: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        groups: Optional[np.ndarray] = None,
    ) -> Dict[str, ModelPerformance]:
        """
        Compare multiple models.

        Args:
            models: Dictionary of {name: model}
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            groups: Optional groups

        Returns:
            Dictionary of {name: performance}
        """
        self.results = {}

        for name, model in models.items():
            self.evaluate_model(name, model, X_train, y_train, X_test, y_test, groups)

        return self.results

    def get_rankings(self, metric: str = "test_score") -> List[Tuple[str, float]]:
        """
        Get model rankings by metric.

        Args:
            metric: Metric to rank by

        Returns:
            List of (model_name, score) sorted by score
        """
        rankings = []

        for name, perf in self.results.items():
            if metric == "test_score":
                score = perf.test_score
            elif metric == "cv_mean":
                score = perf.cv_mean
            elif metric == "rmse":
                score = -perf.rmse  # Negative so higher is better
            elif metric == "mae":
                score = -perf.mae
            else:
                score = perf.test_score

            rankings.append((name, score))

        rankings.sort(key=lambda x: x[1], reverse=True)

        return rankings

    def test_significance(self, model1_name: str, model2_name: str) -> Dict[str, Any]:
        """
        Test if difference between two models is statistically significant.

        Uses paired t-test on CV scores.

        Args:
            model1_name: First model name
            model2_name: Second model name

        Returns:
            Dictionary with t-statistic and p-value
        """
        if model1_name not in self.results or model2_name not in self.results:
            return {}

        scores1 = self.results[model1_name].cv_scores
        scores2 = self.results[model2_name].cv_scores

        if len(scores1) != len(scores2) or len(scores1) == 0:
            logger.warning("Cannot perform significance test: incompatible CV scores")
            return {}

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(scores1, scores2)

        result = {
            "model1": model1_name,
            "model2": model2_name,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "better_model": (
                model1_name if np.mean(scores1) > np.mean(scores2) else model2_name
            ),
        }

        logger.info(f"Significance test: {model1_name} vs {model2_name}")
        logger.info(f"p-value: {p_value:.4f}, significant: {result['significant']}")

        return result

    def summary_table(self) -> Dict[str, Dict[str, Any]]:
        """
        Create summary table of all model results.

        Returns:
            Dictionary of {model_name: metrics}
        """
        return {name: perf.to_dict() for name, perf in self.results.items()}


def calculate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, n_params: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive prediction metrics.

    Args:
        y_true: True values
        y_pred: Predicted values
        n_params: Number of parameters (for AIC/BIC)

    Returns:
        Dictionary of metrics
    """
    metrics = {}

    # Basic metrics
    metrics["mse"] = float(mean_squared_error(y_true, y_pred))
    metrics["rmse"] = float(np.sqrt(metrics["mse"]))
    metrics["mae"] = float(mean_absolute_error(y_true, y_pred))
    metrics["r2"] = float(r2_score(y_true, y_pred))

    # MAPE
    try:
        if SKLEARN_AVAILABLE:
            metrics["mape"] = float(mean_absolute_percentage_error(y_true, y_pred))
        else:
            # Manual MAPE
            mask = y_true != 0
            metrics["mape"] = float(
                np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            )
    except:
        metrics["mape"] = None

    # Information criteria (if n_params provided)
    if n_params is not None:
        n = len(y_true)
        residuals = y_true - y_pred
        rss = np.sum(residuals**2)

        # AIC = 2k + n*ln(RSS/n)
        metrics["aic"] = float(2 * n_params + n * np.log(rss / n))

        # BIC = k*ln(n) + n*ln(RSS/n)
        metrics["bic"] = float(n_params * np.log(n) + n * np.log(rss / n))

    return metrics


__all__ = [
    "CVStrategy",
    "CVConfig",
    "ModelPerformance",
    "CrossValidator",
    "HyperparameterTuner",
    "ModelComparator",
    "calculate_metrics",
]
