"""
Probability Calibration Module

Addresses the critical flaw in using raw simulation probabilities for Kelly Criterion:
if your 10k simulations say 90% win rate but reality is 60%, Kelly will recommend
catastrophic overbetting.

This module provides:
1. Historical calibration tracking (Brier score, log loss, calibration slope)
2. Isotonic regression calibration (non-parametric, preserves ranking)
3. Bayesian calibration (provides uncertainty quantification)
4. Calibration quality monitoring

Key Insight:
-----------
Standard Kelly assumes P(win) is known perfectly. In reality, we have an estimate
P_sim(win) that may be biased. This module learns the mapping:
    P_true(win) = f(P_sim(win))
from historical data, where f() is learned via isotonic regression or Bayesian methods.

Example:
-------
    calibrator = SimulationCalibrator()

    # Train on historical data
    calibrator.fit(
        sim_probs=[0.90, 0.85, 0.75, ...],  # Your simulation estimates
        outcomes=[1, 1, 0, ...]              # Actual results (1=win, 0=loss)
    )

    # Calibrate new prediction
    sim_prob = 0.90  # Your simulation says 90%
    calibrated_prob = calibrator.calibrate(sim_prob)
    print(f"Calibrated: {calibrated_prob:.1%}")  # Might be 82% if you overestimate

    # Check calibration quality
    brier = calibrator.calibration_quality()
    if brier < 0.10:
        print("Well calibrated - safe to use for Kelly")
    else:
        print("Poorly calibrated - DO NOT BET")
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
import warnings

# Try to import sklearn for isotonic regression
try:
    from sklearn.isotonic import IsotonicRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available. Isotonic calibration disabled.")

# Try to import PyMC for Bayesian calibration
try:
    import pymc as pm
    import arviz as az
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    warnings.warn("PyMC not available. Bayesian calibration disabled.")


@dataclass
class CalibrationRecord:
    """Single prediction-outcome pair for tracking"""
    date: datetime
    game_id: str
    simulation_prob: float
    vegas_implied_prob: Optional[float]
    actual_outcome: int  # 1 = win, 0 = loss
    brier_score: float = field(init=False)
    log_loss: float = field(init=False)

    def __post_init__(self):
        """Calculate metrics"""
        self.brier_score = (self.simulation_prob - self.actual_outcome) ** 2

        # Log loss with clipping to avoid log(0)
        p = np.clip(self.simulation_prob, 1e-15, 1 - 1e-15)
        if self.actual_outcome == 1:
            self.log_loss = -np.log(p)
        else:
            self.log_loss = -np.log(1 - p)


class CalibrationDatabase:
    """
    Stores historical predictions and outcomes for calibration learning

    This database tracks every prediction you make, enabling:
    - Learning calibration curves over time
    - Monitoring calibration drift
    - Validating model performance
    """

    def __init__(self):
        self.records: List[CalibrationRecord] = []

    def add_record(
        self,
        date: datetime,
        game_id: str,
        simulation_prob: float,
        actual_outcome: int,
        vegas_implied_prob: Optional[float] = None,
    ):
        """Add a new prediction-outcome pair"""
        record = CalibrationRecord(
            date=date,
            game_id=game_id,
            simulation_prob=simulation_prob,
            vegas_implied_prob=vegas_implied_prob,
            actual_outcome=actual_outcome,
        )
        self.records.append(record)

    def get_recent(self, n: int = 100) -> List[CalibrationRecord]:
        """Get most recent N records"""
        return self.records[-n:]

    def get_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get simulation probs and outcomes as arrays"""
        sim_probs = np.array([r.simulation_prob for r in self.records])
        outcomes = np.array([r.actual_outcome for r in self.records])
        return sim_probs, outcomes

    def average_brier_score(self, recent_n: int = 100) -> float:
        """
        Calculate average Brier score over recent predictions

        Brier Score = Mean((prediction - outcome)²)
        - Perfect: 0.0
        - Good: < 0.10
        - Acceptable: < 0.15
        - Poor: > 0.15

        Returns 0.15 (acceptable threshold) when no data exists to avoid
        blocking all betting on freshly initialized calibrators.
        """
        recent = self.get_recent(recent_n)
        if not recent:
            warnings.warn(
                "No calibration data available. Returning default Brier score of 0.15 "
                "(acceptable threshold). Add observations via add_observation() to get "
                "accurate calibration quality metrics.",
                UserWarning
            )
            return 0.15  # Acceptable threshold - allows betting with caution
        return np.mean([r.brier_score for r in recent])

    def average_log_loss(self, recent_n: int = 100) -> float:
        """
        Calculate average log loss over recent predictions

        Returns 0.70 (approximately random guessing threshold) when no data
        exists to avoid blocking all betting on freshly initialized calibrators.
        """
        recent = self.get_recent(recent_n)
        if not recent:
            warnings.warn(
                "No calibration data available. Returning default log loss of 0.70 "
                "(random guessing threshold). Add observations via add_observation() "
                "to get accurate calibration quality metrics.",
                UserWarning
            )
            return 0.70  # Random guessing threshold - allows betting with caution
        return np.mean([r.log_loss for r in recent])

    def calibration_slope(self) -> float:
        """
        Calculate calibration slope via linear regression

        Perfect calibration: slope = 1.0
        Overconfident: slope < 1.0
        Underconfident: slope > 1.0
        """
        if len(self.records) < 10:
            return np.nan

        sim_probs, outcomes = self.get_arrays()

        # Simple linear regression: outcome = α + β * sim_prob
        slope, intercept = np.polyfit(sim_probs, outcomes, 1)
        return slope

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for analysis"""
        return pd.DataFrame([
            {
                'date': r.date,
                'game_id': r.game_id,
                'simulation_prob': r.simulation_prob,
                'vegas_implied_prob': r.vegas_implied_prob,
                'actual_outcome': r.actual_outcome,
                'brier_score': r.brier_score,
                'log_loss': r.log_loss,
            }
            for r in self.records
        ])


class SimulationCalibrator:
    """
    Isotonic Regression Calibrator for simulation probabilities

    Uses non-parametric isotonic regression to learn the calibration mapping:
        P_calibrated = f(P_simulation)

    Benefits:
    - Non-parametric (no assumptions about functional form)
    - Monotonic (preserves probability ordering)
    - Resistant to overfitting
    - Fast inference

    Example:
    -------
        calibrator = SimulationCalibrator()
        calibrator.fit(
            sim_probs=[0.60, 0.70, 0.80, 0.90],
            outcomes=[0, 1, 0, 1]  # Historical results
        )

        # Calibrate new prediction
        calibrated = calibrator.calibrate(0.85)  # Adjusts for bias
    """

    def __init__(self):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for Isotonic calibration. Install with: pip install scikit-learn")

        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.is_fitted = False
        self.database = CalibrationDatabase()

    def fit(self, sim_probs: np.ndarray, outcomes: np.ndarray):
        """
        Fit calibrator on historical data

        Args:
            sim_probs: Simulation probabilities (0 to 1)
            outcomes: Actual outcomes (0 or 1)
        """
        sim_probs = np.asarray(sim_probs)
        outcomes = np.asarray(outcomes)

        if len(sim_probs) < 10:
            warnings.warn("Less than 10 samples for calibration. Results may be unreliable.")

        self.calibrator.fit(sim_probs, outcomes)
        self.is_fitted = True

    def calibrate(self, sim_prob: float) -> float:
        """
        Convert simulation probability to calibrated probability

        Args:
            sim_prob: Raw simulation probability (0 to 1)

        Returns:
            Calibrated probability (0 to 1)
        """
        if not self.is_fitted:
            warnings.warn("Calibrator not fitted. Returning uncalibrated probability.")
            return sim_prob

        # Ensure scalar input
        result = self.calibrator.transform([sim_prob])[0]
        return float(np.clip(result, 0.0, 1.0))

    def calibrate_batch(self, sim_probs: np.ndarray) -> np.ndarray:
        """Calibrate multiple probabilities at once"""
        if not self.is_fitted:
            return sim_probs

        return self.calibrator.transform(sim_probs)

    def calibration_quality(self, recent_n: int = 100) -> float:
        """
        Return Brier score over recent predictions

        < 0.10: Excellent calibration
        < 0.15: Acceptable
        > 0.15: Poor - do not bet
        """
        return self.database.average_brier_score(recent_n)

    def add_observation(
        self,
        date: datetime,
        game_id: str,
        sim_prob: float,
        outcome: int,
        vegas_implied: Optional[float] = None,
    ):
        """Add new observation and update database"""
        self.database.add_record(date, game_id, sim_prob, outcome, vegas_implied)

    def refit_recent(self, recent_n: int = 500):
        """Re-train calibrator on recent data (handles drift)"""
        recent = self.database.get_recent(recent_n)
        if len(recent) < 50:
            warnings.warn("Insufficient data for refitting")
            return

        sim_probs = np.array([r.simulation_prob for r in recent])
        outcomes = np.array([r.actual_outcome for r in recent])
        self.fit(sim_probs, outcomes)


class BayesianCalibrator:
    """
    Bayesian Calibrator for simulation probabilities

    Uses Bayesian logistic regression to learn calibration mapping with uncertainty:
        logit(P_true) ~ Normal(α + β * logit(P_sim), σ)

    Benefits over isotonic regression:
    - Provides full posterior distribution (uncertainty quantification)
    - Handles limited data better (regularization via priors)
    - Can quantify confidence in calibration
    - Enables uncertainty-adjusted Kelly Criterion

    The key difference: instead of a point estimate, you get a distribution
    over possible true probabilities, which can be used to adjust Kelly fractions.

    Example:
    -------
        calibrator = BayesianCalibrator()
        calibrator.fit(sim_probs, outcomes, draws=2000)

        # Get full posterior distribution
        p_distribution = calibrator.predict_distribution(0.90)
        print(f"Mean: {p_distribution.mean():.1%}")
        print(f"5th-95th percentile: {np.percentile(p_distribution, [5, 95])}")

        # Conservative estimate (25th percentile)
        p_conservative = calibrator.calibrated_probability(0.90, quantile=0.25)
    """

    def __init__(self):
        if not PYMC_AVAILABLE:
            raise ImportError("PyMC required for Bayesian calibration. Install with: pip install pymc")

        self.trace = None
        self.model = None
        self.is_fitted = False
        self.database = CalibrationDatabase()

    def fit(
        self,
        sim_probs: np.ndarray,
        outcomes: np.ndarray,
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 2,
    ):
        """
        Fit Bayesian calibration model

        Args:
            sim_probs: Simulation probabilities
            outcomes: Actual outcomes (0 or 1)
            draws: Number of posterior samples
            tune: Number of tuning steps
            chains: Number of MCMC chains
        """
        sim_probs = np.asarray(sim_probs)
        outcomes = np.asarray(outcomes)

        if len(sim_probs) < 20:
            warnings.warn("Less than 20 samples. Bayesian calibration may be unstable.")

        # Logit transform simulation probabilities
        # Clip to avoid log(0) or log(1)
        sim_probs_clipped = np.clip(sim_probs, 0.01, 0.99)
        logit_sim = np.log(sim_probs_clipped / (1 - sim_probs_clipped))

        with pm.Model() as model:
            # Priors
            # α (intercept): should be ~0 if unbiased
            alpha = pm.Normal('intercept', mu=0, sigma=1)

            # β (slope): should be ~1 if well-calibrated
            beta = pm.Normal('slope', mu=1, sigma=0.5)

            # Calibrated logit
            logit_p_true = alpha + beta * logit_sim

            # Likelihood
            pm.Bernoulli('outcome', logit_p=logit_p_true, observed=outcomes)

            # Sample posterior
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                return_inferencedata=True,
                progressbar=False,  # Silence output
            )

        self.model = model
        self.trace = trace
        self.is_fitted = True

    def predict_distribution(self, sim_prob: float, n_samples: int = 2000) -> np.ndarray:
        """
        Get full posterior distribution of true probability

        Args:
            sim_prob: Simulation probability
            n_samples: Number of posterior samples to return

        Returns:
            Array of posterior samples for true probability
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Logit transform
        sim_prob_clipped = np.clip(sim_prob, 0.01, 0.99)
        logit_sim = np.log(sim_prob_clipped / (1 - sim_prob_clipped))

        # Get posterior samples
        alpha_samples = self.trace.posterior['intercept'].values.flatten()[:n_samples]
        beta_samples = self.trace.posterior['slope'].values.flatten()[:n_samples]

        # Posterior predictive
        logit_p_samples = alpha_samples + beta_samples * logit_sim

        # Convert back to probability
        p_samples = 1 / (1 + np.exp(-logit_p_samples))

        return p_samples

    def calibrated_probability(self, sim_prob: float, quantile: float = 0.50) -> float:
        """
        Get calibrated probability at specified quantile

        Args:
            sim_prob: Simulation probability
            quantile: Which quantile to return
                      0.50 = median (balanced)
                      0.25 = conservative (lower bound)
                      0.75 = aggressive (upper bound)

        Returns:
            Calibrated probability at quantile
        """
        p_distribution = self.predict_distribution(sim_prob)
        return float(np.quantile(p_distribution, quantile))

    def calibration_uncertainty(self, sim_prob: float) -> float:
        """
        Get standard deviation of calibrated probability

        High uncertainty → reduce Kelly fraction
        Low uncertainty → can use larger Kelly fraction
        """
        p_distribution = self.predict_distribution(sim_prob)
        return float(np.std(p_distribution))

    def calibration_interval(self, sim_prob: float, alpha: float = 0.05) -> Tuple[float, float]:
        """
        Get credible interval for calibrated probability

        Args:
            sim_prob: Simulation probability
            alpha: Significance level (0.05 = 95% interval)

        Returns:
            (lower_bound, upper_bound) tuple
        """
        p_distribution = self.predict_distribution(sim_prob)
        lower = np.quantile(p_distribution, alpha / 2)
        upper = np.quantile(p_distribution, 1 - alpha / 2)
        return (float(lower), float(upper))

    def diagnostics(self) -> Dict[str, Any]:
        """
        Return MCMC diagnostics

        Check for convergence issues:
        - Rhat should be < 1.01 (closer to 1.0 is better)
        - ESS should be > 400 (higher is better)
        - Divergences should be 0
        """
        if not self.is_fitted:
            return {}

        summary = az.summary(self.trace)

        return {
            'intercept_rhat': float(summary.loc['intercept', 'r_hat']),
            'slope_rhat': float(summary.loc['slope', 'r_hat']),
            'intercept_ess': float(summary.loc['intercept', 'ess_bulk']),
            'slope_ess': float(summary.loc['slope', 'ess_bulk']),
            'divergences': int(self.trace.sample_stats['diverging'].sum().values),
        }

    def calibration_quality(self, recent_n: int = 100) -> float:
        """Return Brier score over recent predictions"""
        return self.database.average_brier_score(recent_n)

    def add_observation(
        self,
        date: datetime,
        game_id: str,
        sim_prob: float,
        outcome: int,
        vegas_implied: Optional[float] = None,
    ):
        """Add observation to database"""
        self.database.add_record(date, game_id, sim_prob, outcome, vegas_implied)


def logit(p: np.ndarray) -> np.ndarray:
    """Logit transform: logit(p) = log(p / (1-p))"""
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return np.log(p / (1 - p))


def expit(x: np.ndarray) -> np.ndarray:
    """Inverse logit (sigmoid): expit(x) = 1 / (1 + exp(-x))"""
    return 1 / (1 + np.exp(-x))


if __name__ == "__main__":
    # Example usage
    print("Calibration Module Example")
    print("=" * 50)

    # Simulate historical data
    np.random.seed(42)
    n_games = 200

    # True probabilities (unknown in reality)
    true_probs = np.random.uniform(0.4, 0.9, n_games)

    # Simulation probabilities (biased - overestimate by 5%)
    sim_probs = np.clip(true_probs + 0.05, 0, 1)

    # Actual outcomes
    outcomes = np.random.binomial(1, true_probs)

    print(f"Generated {n_games} historical games")
    print(f"Average true probability: {true_probs.mean():.1%}")
    print(f"Average simulation probability: {sim_probs.mean():.1%}")
    print(f"Bias: +{(sim_probs.mean() - true_probs.mean()):.1%}\n")

    # Train isotonic calibrator
    if SKLEARN_AVAILABLE:
        print("Training Isotonic Calibrator...")
        iso_calibrator = SimulationCalibrator()
        iso_calibrator.fit(sim_probs, outcomes)

        # Test calibration
        test_sim_prob = 0.90
        test_calibrated = iso_calibrator.calibrate(test_sim_prob)
        print(f"Simulation: {test_sim_prob:.1%} → Calibrated: {test_calibrated:.1%}")

    # Train Bayesian calibrator
    if PYMC_AVAILABLE:
        print("\nTraining Bayesian Calibrator...")
        bayes_calibrator = BayesianCalibrator()
        bayes_calibrator.fit(sim_probs, outcomes, draws=1000, tune=500)

        # Test calibration with uncertainty
        test_sim_prob = 0.90
        p_dist = bayes_calibrator.predict_distribution(test_sim_prob, n_samples=1000)
        p_median = bayes_calibrator.calibrated_probability(test_sim_prob, quantile=0.50)
        p_uncertainty = bayes_calibrator.calibration_uncertainty(test_sim_prob)
        lower, upper = bayes_calibrator.calibration_interval(test_sim_prob)

        print(f"\nSimulation: {test_sim_prob:.1%}")
        print(f"Calibrated (median): {p_median:.1%}")
        print(f"Uncertainty (std): {p_uncertainty:.1%}")
        print(f"95% Credible Interval: [{lower:.1%}, {upper:.1%}]")

        # Diagnostics
        diag = bayes_calibrator.diagnostics()
        print(f"\nDiagnostics:")
        print(f"  Slope Rhat: {diag['slope_rhat']:.4f} (should be < 1.01)")
        print(f"  Slope ESS: {diag['slope_ess']:.0f} (should be > 400)")
        print(f"  Divergences: {diag['divergences']} (should be 0)")
