"""
Quantile Regression (Agent 18, Module 3)

Analyze effects across the conditional distribution:
- Quantile regression estimation
- Conditional quantile functions
- Heterogeneous treatment effects
- Quantile treatment effects (QTE)
- Inter-quantile range analysis
- Quantile-specific inference

NBA Applications:
- Effect of minutes on PPG at different skill levels
- Coaching effects on high vs low performers
- Training effects across ability distribution
- Age effects on performance quantiles

Integrates with:
- panel_data: Panel quantile regression
- causal_inference: Quantile treatment effects
- ml_bridge: Hybrid quantile models
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
from scipy import stats
from scipy.optimize import minimize

logger = logging.getLogger(__name__)

# Try to import statsmodels (optional)
try:
    from statsmodels.regression.quantile_regression import QuantReg
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, quantile regression features limited")


@dataclass
class QuantileRegressionResult:
    """Results from quantile regression"""

    quantile: float
    coefficients: np.ndarray
    fitted_values: np.ndarray
    residuals: np.ndarray

    # Standard errors and inference
    std_errors: Optional[np.ndarray] = None
    t_stats: Optional[np.ndarray] = None
    p_values: Optional[np.ndarray] = None

    # Model fit
    pseudo_r2: float = 0.0
    n_obs: int = 0

    # Feature names
    feature_names: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'quantile': self.quantile,
            'coefficients': self.coefficients.tolist(),
            'pseudo_r2': self.pseudo_r2,
            'n_obs': self.n_obs
        }

        if self.feature_names:
            result['coef_dict'] = dict(zip(self.feature_names, self.coefficients))

        if self.std_errors is not None:
            result['std_errors'] = self.std_errors.tolist()

        return result

    def summary(self) -> str:
        """Create summary string"""
        lines = [
            f"Quantile Regression (τ={self.quantile:.2f})",
            "=" * 50,
            f"Number of observations: {self.n_obs}",
            f"Pseudo R²: {self.pseudo_r2:.4f}",
            "",
            "Coefficients:"
        ]

        for i, coef in enumerate(self.coefficients):
            name = self.feature_names[i] if self.feature_names else f"X{i}"
            if self.std_errors is not None:
                se = self.std_errors[i]
                t_stat = self.t_stats[i] if self.t_stats is not None else 0.0
                lines.append(f"  {name:20s}: {coef:10.4f} ({se:.4f}) [t={t_stat:.2f}]")
            else:
                lines.append(f"  {name:20s}: {coef:10.4f}")

        return "\n".join(lines)


@dataclass
class QuantileProcessResult:
    """Results from quantile process (multiple quantiles)"""

    quantiles: List[float]
    results: List[QuantileRegressionResult]

    # Coefficient paths across quantiles
    coefficient_paths: Optional[Dict[str, List[float]]] = None

    def get_coefficient_path(self, feature_name: str) -> Tuple[List[float], List[float]]:
        """
        Get coefficient path for a feature across quantiles.

        Args:
            feature_name: Feature name

        Returns:
            (quantiles, coefficients)
        """
        coefficients = []

        for result in self.results:
            if result.feature_names and feature_name in result.feature_names:
                idx = result.feature_names.index(feature_name)
                coefficients.append(result.coefficients[idx])
            else:
                coefficients.append(0.0)

        return self.quantiles, coefficients

    def test_coefficient_equality(
        self,
        feature_name: str
    ) -> Dict[str, Any]:
        """
        Test if coefficient is constant across quantiles.

        Returns:
            Dictionary with test results
        """
        quantiles, coefficients = self.get_coefficient_path(feature_name)

        # Simple variance test
        coef_variance = np.var(coefficients)
        coef_mean = np.mean(coefficients)
        cv = coef_variance / (abs(coef_mean) + 1e-8)  # Coefficient of variation

        # If CV is low, likely constant
        is_constant = cv < 0.1

        return {
            'feature': feature_name,
            'is_constant': is_constant,
            'coefficient_variance': coef_variance,
            'coefficient_mean': coef_mean,
            'coefficient_of_variation': cv
        }


class QuantileRegression:
    """
    Quantile regression estimator.

    Minimizes check function:
    ρ_τ(u) = u(τ - I(u < 0))

    Estimates conditional quantiles Q_τ(Y|X) = X'β_τ
    """

    def __init__(self, quantile: float = 0.5):
        """
        Initialize quantile regression.

        Args:
            quantile: Quantile to estimate (0-1)
        """
        if not 0 < quantile < 1:
            raise ValueError("Quantile must be between 0 and 1")

        self.quantile = quantile
        self.coefficients_: Optional[np.ndarray] = None
        self.is_fitted = False

        logger.info(f"QuantileRegression initialized for quantile {quantile}")

    def _check_function(self, residuals: np.ndarray) -> float:
        """
        Check function (quantile loss).

        Args:
            residuals: Residuals (y - X'β)

        Returns:
            Check function value
        """
        return np.sum(np.where(
            residuals >= 0,
            self.quantile * residuals,
            (self.quantile - 1) * residuals
        ))

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> 'QuantileRegression':
        """
        Fit quantile regression.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target variable (n_samples,)
            feature_names: Optional feature names

        Returns:
            Self for chaining
        """
        if STATSMODELS_AVAILABLE:
            # Use statsmodels implementation
            model = QuantReg(y, X)
            result = model.fit(q=self.quantile)
            self.coefficients_ = result.params
            self.statsmodels_result_ = result
            self.feature_names_ = feature_names

            logger.info(f"Quantile regression fitted (τ={self.quantile:.2f})")

        else:
            # Manual implementation using scipy optimize
            self.coefficients_ = self._manual_fit(X, y)
            self.feature_names_ = feature_names

            logger.info(f"Quantile regression fitted manually (τ={self.quantile:.2f})")

        self.is_fitted = True
        return self

    def _manual_fit(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> np.ndarray:
        """
        Manual quantile regression using scipy.optimize.

        Args:
            X: Features
            y: Target

        Returns:
            Coefficients
        """
        # Objective function
        def objective(beta):
            residuals = y - X @ beta
            return self._check_function(residuals)

        # Initial guess (OLS)
        beta_init = np.linalg.lstsq(X, y, rcond=None)[0]

        # Optimize
        result = minimize(
            objective,
            beta_init,
            method='SLSQP',
            options={'disp': False}
        )

        return result.x

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict conditional quantiles.

        Args:
            X: Feature matrix

        Returns:
            Predicted quantiles
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        return X @ self.coefficients_

    def get_result(
        self,
        X: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None
    ) -> QuantileRegressionResult:
        """
        Get detailed result object.

        Args:
            X: Training features (for fitted values)
            y: Training target (for residuals)

        Returns:
            QuantileRegressionResult
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        fitted_values = self.predict(X) if X is not None else np.array([])
        residuals = y - fitted_values if y is not None and len(fitted_values) > 0 else np.array([])

        # Pseudo R²
        if len(residuals) > 0 and y is not None:
            rho_model = self._check_function(residuals)
            rho_null = self._check_function(y - np.quantile(y, self.quantile))
            pseudo_r2 = 1 - (rho_model / rho_null) if rho_null > 0 else 0.0
        else:
            pseudo_r2 = 0.0

        # Standard errors (if statsmodels available)
        if STATSMODELS_AVAILABLE and hasattr(self, 'statsmodels_result_'):
            std_errors = self.statsmodels_result_.bse
            t_stats = self.statsmodels_result_.tvalues
            p_values = self.statsmodels_result_.pvalues
        else:
            std_errors = None
            t_stats = None
            p_values = None

        result = QuantileRegressionResult(
            quantile=self.quantile,
            coefficients=self.coefficients_,
            fitted_values=fitted_values,
            residuals=residuals,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            pseudo_r2=pseudo_r2,
            n_obs=len(y) if y is not None else 0,
            feature_names=self.feature_names_ if hasattr(self, 'feature_names_') else None
        )

        return result


class QuantileProcess:
    """
    Estimate quantile regression at multiple quantiles.

    Provides:
    - Coefficient paths across quantiles
    - Tests for heterogeneity
    - Inter-quantile range
    """

    def __init__(
        self,
        quantiles: Optional[List[float]] = None
    ):
        """
        Initialize quantile process.

        Args:
            quantiles: List of quantiles to estimate (default: deciles)
        """
        if quantiles is None:
            quantiles = np.arange(0.1, 1.0, 0.1).tolist()

        self.quantiles = quantiles
        self.models: Dict[float, QuantileRegression] = {}
        self.is_fitted = False

        logger.info(f"QuantileProcess initialized with {len(quantiles)} quantiles")

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> 'QuantileProcess':
        """
        Fit quantile regressions at all quantiles.

        Args:
            X: Features
            y: Target
            feature_names: Optional feature names

        Returns:
            Self for chaining
        """
        for q in self.quantiles:
            model = QuantileRegression(quantile=q)
            model.fit(X, y, feature_names)
            self.models[q] = model

        self.is_fitted = True
        logger.info(f"Quantile process fitted at {len(self.quantiles)} quantiles")

        return self

    def predict(
        self,
        X: np.ndarray,
        quantile: Optional[float] = None
    ) -> Union[np.ndarray, Dict[float, np.ndarray]]:
        """
        Predict at specified quantile(s).

        Args:
            X: Features
            quantile: Specific quantile (None = all)

        Returns:
            Predictions (array or dict)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        if quantile is not None:
            if quantile not in self.models:
                raise ValueError(f"Quantile {quantile} not estimated")
            return self.models[quantile].predict(X)
        else:
            return {q: model.predict(X) for q, model in self.models.items()}

    def get_results(
        self,
        X: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None
    ) -> QuantileProcessResult:
        """
        Get results for all quantiles.

        Args:
            X: Training features
            y: Training target

        Returns:
            QuantileProcessResult
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        results = [
            self.models[q].get_result(X, y)
            for q in self.quantiles
        ]

        return QuantileProcessResult(
            quantiles=self.quantiles,
            results=results
        )

    def get_inter_quantile_range(
        self,
        X: np.ndarray,
        lower_quantile: float = 0.25,
        upper_quantile: float = 0.75
    ) -> np.ndarray:
        """
        Calculate inter-quantile range.

        Args:
            X: Features
            lower_quantile: Lower quantile
            upper_quantile: Upper quantile

        Returns:
            IQR for each observation
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        if lower_quantile not in self.models or upper_quantile not in self.models:
            raise ValueError("Specified quantiles not estimated")

        lower_pred = self.models[lower_quantile].predict(X)
        upper_pred = self.models[upper_quantile].predict(X)

        return upper_pred - lower_pred


class QuantileTreatmentEffect:
    """
    Quantile Treatment Effects (QTE).

    Estimate treatment effects at different quantiles of the outcome distribution.
    Allows for heterogeneous treatment effects across ability levels.
    """

    def __init__(
        self,
        quantiles: Optional[List[float]] = None
    ):
        """
        Initialize QTE estimator.

        Args:
            quantiles: Quantiles to estimate
        """
        self.quantiles = quantiles or [0.25, 0.5, 0.75]
        self.qte_: Dict[float, float] = {}
        self.is_fitted = False

        logger.info("QuantileTreatmentEffect initialized")

    def estimate(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        outcome: np.ndarray
    ) -> Dict[float, float]:
        """
        Estimate QTE.

        Args:
            X: Covariates
            treatment: Treatment indicator
            outcome: Outcome variable

        Returns:
            Dictionary of {quantile: treatment_effect}
        """
        # Include treatment in X
        X_with_treatment = np.column_stack([X, treatment])

        for q in self.quantiles:
            # Fit quantile regression including treatment
            qr = QuantileRegression(quantile=q)
            qr.fit(X_with_treatment, outcome)

            # Treatment effect is coefficient on treatment
            treatment_effect = qr.coefficients_[-1]  # Last coefficient

            self.qte_[q] = treatment_effect

        self.is_fitted = True

        logger.info(f"QTE estimated at {len(self.quantiles)} quantiles")

        return self.qte_

    def test_constant_effect(self) -> Dict[str, Any]:
        """
        Test if treatment effect is constant across quantiles.

        Returns:
            Test results
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        effects = list(self.qte_.values())

        # Variance of effects
        effect_variance = np.var(effects)
        effect_mean = np.mean(effects)

        # If variance is low relative to mean, likely constant
        cv = effect_variance / (abs(effect_mean) + 1e-8)

        return {
            'is_constant': cv < 0.1,
            'effect_variance': effect_variance,
            'effect_mean': effect_mean,
            'coefficient_of_variation': cv,
            'effects_by_quantile': self.qte_
        }


def estimate_quantile_regression(
    X: np.ndarray,
    y: np.ndarray,
    quantiles: Union[float, List[float]] = 0.5,
    feature_names: Optional[List[str]] = None
) -> Union[QuantileRegressionResult, QuantileProcessResult]:
    """
    Convenience function for quantile regression.

    Args:
        X: Features
        y: Target
        quantiles: Single quantile or list
        feature_names: Optional feature names

    Returns:
        Result object (single or process)
    """
    if isinstance(quantiles, float):
        # Single quantile
        model = QuantileRegression(quantile=quantiles)
        model.fit(X, y, feature_names)
        return model.get_result(X, y)
    else:
        # Multiple quantiles
        process = QuantileProcess(quantiles=quantiles)
        process.fit(X, y, feature_names)
        return process.get_results(X, y)


__all__ = [
    'QuantileRegressionResult',
    'QuantileProcessResult',
    'QuantileRegression',
    'QuantileProcess',
    'QuantileTreatmentEffect',
    'estimate_quantile_regression',
]
