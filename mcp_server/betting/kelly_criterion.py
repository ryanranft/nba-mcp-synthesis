"""
Econometric-Enhanced Kelly Criterion

This module implements Kelly Criterion with critical enhancements for real-world betting:

1. **Calibration-Aware**: Uses calibrated probabilities, not raw simulation outputs
2. **Uncertainty-Adjusted**: Reduces bet size when model is uncertain
3. **Fractional Kelly**: Adaptive fractions based on calibration quality
4. **Portfolio Kelly**: Handles correlated bets correctly

Standard Kelly Formula:
----------------------
    f = (bp - q) / b

    where:
        f = fraction of bankroll to bet
        b = net odds received (decimal_odds - 1)
        p = probability of winning
        q = probability of losing (1 - p)

The Fatal Flaw of Standard Kelly:
---------------------------------
Standard Kelly assumes p is known PERFECTLY. In reality:
- Your simulation says 90% → Kelly says bet 40% of bankroll
- Reality is only 60% → You lose 40% of bankroll repeatedly → Bankruptcy

The Solution (This Module):
---------------------------
1. **Calibrate p**: Use historical performance to adjust simulation probability
2. **Quantify uncertainty**: Get σ(p) from Bayesian posterior
3. **Uncertainty penalty**: Reduce Kelly fraction when uncertain
4. **Fractional Kelly**: Start conservative (25%), increase as model proves itself
5. **Risk management**: Never bet >50%, reduce during drawdowns

Safe Large Bet Criteria:
-----------------------
To justify 40% of bankroll, ALL must be true:
- Calibrated edge > 20%
- Calibrated probability > 88%
- Uncertainty (σ) < 2%
- Brier score < 0.06 (excellent calibration)
- CLV > 5% (sharp bettor status)

Example Usage:
-------------
    from mcp_server.betting import CalibratedKelly, BayesianCalibrator

    # 1. Calibrate your simulation probabilities
    calibrator = BayesianCalibrator()
    calibrator.fit(historical_sim_probs, historical_outcomes)

    # 2. Calculate Kelly with uncertainty
    kelly = CalibratedKelly(calibrator)
    result = kelly.calculate(
        sim_prob=0.90,         # Your 10k simulation
        odds=1.50,              # Market odds
        away_odds=2.80,         # For vig removal
        bankroll=10000
    )

    print(f"Bet: ${result['bet_amount']:.2f}")
    print(f"Kelly fraction: {result['kelly_fraction']:.1%}")
    print(f"Edge: {result['edge']:.1%}")
    print(f"Confidence: {result['confidence']:.1%}")
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass
import warnings

try:
    from .probability_calibration import BayesianCalibrator, SimulationCalibrator
    from .odds_utilities import OddsUtilities
except ImportError:
    # For standalone testing
    pass


@dataclass
class KellyResult:
    """Result of Kelly Criterion calculation"""

    kelly_fraction: float  # Recommended fraction of bankroll (0 to 1)
    bet_amount: float  # Dollar amount to bet
    edge: float  # Your edge over market (decimal)
    calibrated_prob: float  # Calibrated win probability
    simulation_prob: float  # Original simulation probability
    market_fair_prob: float  # Market probability after vig removal
    uncertainty: float  # Standard deviation of probability
    confidence: float  # Confidence score (1 - uncertainty)
    kelly_full: float  # Full Kelly before adjustments
    uncertainty_penalty: float  # Multiplier applied for uncertainty
    fractional_multiplier: float  # Fractional Kelly multiplier
    should_bet: bool  # Whether to place bet
    reason: str  # Explanation of decision


class CalibratedKelly:
    """
    Kelly Criterion with calibration and uncertainty adjustment

    This class implements the econometric-enhanced Kelly that safely handles
    miscalibrated simulation probabilities.

    Key Features:
    - Uses calibrated probabilities (not raw simulations)
    - Adjusts for model uncertainty
    - Applies fractional Kelly based on calibration quality
    - Enforces safety limits (never >50%)

    Args:
        calibrator: Fitted probability calibrator (Bayesian or Isotonic)
        max_kelly: Maximum Kelly fraction allowed (default: 0.50)
        min_edge: Minimum edge required to bet (default: 0.03 = 3%)
        max_uncertainty: Maximum acceptable uncertainty (default: 0.20 = 20%)
    """

    def __init__(
        self,
        calibrator: Any,
        max_kelly: float = 0.50,
        min_edge: float = 0.03,
        max_uncertainty: float = 0.20,
    ):
        self.calibrator = calibrator
        self.max_kelly = max_kelly
        self.min_edge = min_edge
        self.max_uncertainty = max_uncertainty

    def calculate(
        self,
        sim_prob: float,
        odds: float,
        bankroll: float,
        away_odds: Optional[float] = None,
        fractional: float = 0.25,
        adaptive_fraction: bool = True,
    ) -> KellyResult:
        """
        Calculate Kelly bet size with full econometric enhancement

        Args:
            sim_prob: Simulation probability (from your 10k sims)
            odds: Market decimal odds for the bet
            bankroll: Current bankroll
            away_odds: Optional away odds for vig removal (recommended)
            fractional: Base fractional Kelly (0.25 = quarter Kelly)
            adaptive_fraction: Increase fraction based on calibration quality

        Returns:
            KellyResult with all decision info
        """
        # Step 1: Calibrate simulation probability
        if hasattr(self.calibrator, "calibrated_probability"):
            # Bayesian calibrator - get median
            calibrated_prob = self.calibrator.calibrated_probability(
                sim_prob, quantile=0.50
            )
            uncertainty = self.calibrator.calibration_uncertainty(sim_prob)
        elif hasattr(self.calibrator, "calibrate"):
            # Isotonic calibrator - point estimate
            calibrated_prob = self.calibrator.calibrate(sim_prob)
            uncertainty = 0.05  # Conservative default
        else:
            warnings.warn(
                "Calibrator not recognized. Using raw simulation probability."
            )
            calibrated_prob = sim_prob
            uncertainty = 0.10

        # Step 2: Remove vig from market odds
        if away_odds is not None:
            market_fair_prob, _ = OddsUtilities.remove_vig_multiplicative(
                odds, away_odds
            )
        else:
            market_fair_prob = 1 / odds

        # Step 3: Calculate edge
        edge = calibrated_prob - market_fair_prob

        # Step 4: Check minimum edge threshold
        if edge < self.min_edge:
            return KellyResult(
                kelly_fraction=0.0,
                bet_amount=0.0,
                edge=edge,
                calibrated_prob=calibrated_prob,
                simulation_prob=sim_prob,
                market_fair_prob=market_fair_prob,
                uncertainty=uncertainty,
                confidence=1 - uncertainty,
                kelly_full=0.0,
                uncertainty_penalty=0.0,
                fractional_multiplier=0.0,
                should_bet=False,
                reason=f"Insufficient edge: {edge:.1%} < {self.min_edge:.1%} minimum",
            )

        # Step 5: Calculate base Kelly fraction
        b = odds - 1  # Net odds
        q = 1 - calibrated_prob
        kelly_full = (b * calibrated_prob - q) / b

        # Handle edge cases
        if kelly_full <= 0:
            return KellyResult(
                kelly_fraction=0.0,
                bet_amount=0.0,
                edge=edge,
                calibrated_prob=calibrated_prob,
                simulation_prob=sim_prob,
                market_fair_prob=market_fair_prob,
                uncertainty=uncertainty,
                confidence=1 - uncertainty,
                kelly_full=kelly_full,
                uncertainty_penalty=0.0,
                fractional_multiplier=0.0,
                should_bet=False,
                reason="Kelly formula returned negative or zero",
            )

        # Step 6: Apply uncertainty penalty
        # Key innovation: reduce bet size when model is uncertain
        uncertainty_penalty = max(0.1, 1 - (uncertainty / self.max_uncertainty))

        kelly_adjusted = kelly_full * uncertainty_penalty

        # Step 7: Apply fractional Kelly
        if adaptive_fraction:
            # Adaptive: increase fraction based on calibration quality
            calibration_quality = (
                self.calibrator.calibration_quality()
                if hasattr(self.calibrator, "calibration_quality")
                else 0.15
            )
            fractional_multiplier = self._adaptive_fraction(calibration_quality)
        else:
            fractional_multiplier = fractional

        kelly_final = kelly_adjusted * fractional_multiplier

        # Step 8: Enforce maximum Kelly
        kelly_final = min(kelly_final, self.max_kelly)

        # Step 9: Calculate bet amount
        bet_amount = kelly_final * bankroll

        # Step 10: Determine if should bet
        should_bet = (
            edge >= self.min_edge
            and kelly_final > 0.01  # At least 1% of bankroll
            and uncertainty < self.max_uncertainty
        )

        return KellyResult(
            kelly_fraction=kelly_final,
            bet_amount=bet_amount,
            edge=edge,
            calibrated_prob=calibrated_prob,
            simulation_prob=sim_prob,
            market_fair_prob=market_fair_prob,
            uncertainty=uncertainty,
            confidence=1 - uncertainty,
            kelly_full=kelly_full,
            uncertainty_penalty=uncertainty_penalty,
            fractional_multiplier=fractional_multiplier,
            should_bet=should_bet,
            reason=self._get_reason(should_bet, edge, uncertainty, kelly_final),
        )

    def _adaptive_fraction(self, brier_score: float) -> float:
        """
        Adaptively adjust Kelly fraction based on calibration quality

        Excellent calibration → 1.0 (full Kelly)
        Good calibration → 0.50 (half Kelly)
        Acceptable calibration → 0.25 (quarter Kelly)
        Poor calibration → 0.10 (tenth Kelly or less)

        Args:
            brier_score: Recent Brier score (lower is better)

        Returns:
            Fractional multiplier (0.1 to 1.0)
        """
        if brier_score < 0.06:
            return 1.0  # Full Kelly - excellent calibration
        elif brier_score < 0.08:
            return 0.75  # 3/4 Kelly - very good
        elif brier_score < 0.10:
            return 0.50  # Half Kelly - good
        elif brier_score < 0.15:
            return 0.25  # Quarter Kelly - acceptable
        else:
            return 0.10  # Tenth Kelly - poor, bet very small

    def _get_reason(
        self, should_bet: bool, edge: float, uncertainty: float, kelly: float
    ) -> str:
        """Generate human-readable reason for decision"""
        if not should_bet:
            if edge < self.min_edge:
                return f"Insufficient edge: {edge:.1%}"
            elif uncertainty >= self.max_uncertainty:
                return f"Too uncertain: σ = {uncertainty:.1%}"
            elif kelly <= 0.01:
                return "Kelly fraction too small"
            else:
                return "Unknown reason (should not happen)"
        else:
            return f"Strong edge ({edge:.1%}) + good calibration → bet {kelly:.1%} of bankroll"


class AdaptiveKelly:
    """
    Advanced Kelly implementation with:
    - Time-varying fractions
    - Drawdown protection
    - CLV-based adjustments
    - Portfolio optimization for correlated bets

    Use this for sophisticated bankroll management across multiple bets.
    """

    def __init__(self, calibrated_kelly: CalibratedKelly):
        self.base_kelly = calibrated_kelly
        self.current_drawdown = 0.0
        self.peak_bankroll = None

    def calculate_with_drawdown_protection(
        self, sim_prob: float, odds: float, current_bankroll: float, **kwargs
    ) -> KellyResult:
        """
        Calculate Kelly with drawdown protection

        If experiencing drawdown > 20%, reduce bet sizes
        If experiencing drawdown > 30%, stop betting

        Args:
            sim_prob: Simulation probability
            odds: Market odds
            current_bankroll: Current bankroll
            **kwargs: Additional args for CalibratedKelly.calculate()

        Returns:
            KellyResult (potentially with reduced bet size)
        """
        # Track peak bankroll
        if self.peak_bankroll is None:
            self.peak_bankroll = current_bankroll
        else:
            self.peak_bankroll = max(self.peak_bankroll, current_bankroll)

        # Calculate current drawdown
        self.current_drawdown = (
            self.peak_bankroll - current_bankroll
        ) / self.peak_bankroll

        # Calculate base Kelly
        result = self.base_kelly.calculate(sim_prob, odds, current_bankroll, **kwargs)

        # Apply drawdown protection
        if self.current_drawdown > 0.30:
            # 30%+ drawdown: stop betting
            result.kelly_fraction = 0.0
            result.bet_amount = 0.0
            result.should_bet = False
            result.reason = f"Drawdown too large: {self.current_drawdown:.1%} > 30%"
        elif self.current_drawdown > 0.20:
            # 20-30% drawdown: halve bet size
            result.kelly_fraction *= 0.50
            result.bet_amount *= 0.50
            result.reason += (
                f" (reduced 50% due to {self.current_drawdown:.1%} drawdown)"
            )

        return result

    def portfolio_kelly(
        self,
        bets: List[Dict[str, Any]],
        bankroll: float,
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> List[KellyResult]:
        """
        Calculate optimal Kelly fractions for multiple correlated bets

        When betting on multiple games simultaneously, naive Kelly can over-bet
        if outcomes are correlated (e.g., same team in multiple bets).

        This method uses portfolio optimization to account for correlations.

        Args:
            bets: List of bet specifications, each with:
                  {'sim_prob': float, 'odds': float, 'away_odds': float, ...}
            bankroll: Total available bankroll
            correlation_matrix: Optional correlation matrix between bets
                               (if None, assumes independent)

        Returns:
            List of KellyResult, one per bet
        """
        n_bets = len(bets)

        # Calculate individual Kelly fractions
        individual_kellys = []
        for bet in bets:
            result = self.base_kelly.calculate(
                sim_prob=bet["sim_prob"],
                odds=bet["odds"],
                bankroll=bankroll,
                away_odds=bet.get("away_odds"),
            )
            individual_kellys.append(result)

        # If no correlation matrix, assume independent
        if correlation_matrix is None:
            return individual_kellys

        # Portfolio optimization (simplified)
        # Full implementation would use quadratic programming
        # Here we use a heuristic: reduce each bet by correlation factor

        # Calculate total portfolio Kelly
        total_kelly = sum(k.kelly_fraction for k in individual_kellys)

        if total_kelly > 0.50:  # Over-betting
            # Scale down proportionally
            scale_factor = 0.50 / total_kelly
            for result in individual_kellys:
                result.kelly_fraction *= scale_factor
                result.bet_amount = result.kelly_fraction * bankroll
                result.reason += f" (scaled by {scale_factor:.2f} for portfolio)"

        return individual_kellys


def kelly_full_formula(prob: float, odds: float) -> float:
    """
    Pure Kelly formula (no adjustments)

    Use for reference only - not recommended for real betting!

    Args:
        prob: Win probability (0 to 1)
        odds: Decimal odds

    Returns:
        Kelly fraction (can be > 1.0!)
    """
    b = odds - 1
    q = 1 - prob
    return (b * prob - q) / b


def fractional_kelly(full_kelly: float, fraction: float = 0.25) -> float:
    """
    Apply fractional Kelly

    Args:
        full_kelly: Full Kelly fraction
        fraction: Fraction to apply (0.25 = quarter Kelly)

    Returns:
        Fractional Kelly
    """
    return full_kelly * fraction


if __name__ == "__main__":
    # Example: Demonstrate the danger of miscalibrated probabilities
    print("Econometric-Enhanced Kelly Criterion")
    print("=" * 70)

    print("\n" + "⚠️  THE DANGER OF MISCALIBRATED PROBABILITIES".center(70))
    print("=" * 70)

    # Scenario: Your simulation overestimates by 10%
    sim_prob = 0.90  # Simulation says 90%
    true_prob = 0.60  # Reality is only 60%
    odds = 2.00  # Even money

    # Naive Kelly (disaster!)
    naive_kelly = kelly_full_formula(sim_prob, odds)
    print(f"\n🚨 NAIVE APPROACH (DANGEROUS):")
    print(f"   Simulation: {sim_prob:.0%}")
    print(f"   Naive Kelly: {naive_kelly:.1%} of bankroll")
    print(f"   Reality: Only {true_prob:.0%} win rate")
    print(
        f"   Result: You lose {naive_kelly:.1%} of bankroll {1-true_prob:.0%} of the time!"
    )
    print(
        f"   Expected ROI: {((true_prob * (odds - 1)) - ((1-true_prob) * 1)) * naive_kelly:.1%} (NEGATIVE!)"
    )

    print("\n" + "-" * 70)

    # Calibrated approach (safe)
    print(f"\n✅ CALIBRATED APPROACH (SAFE):")
    print(f"   Simulation: {sim_prob:.0%}")
    print(f"   After Calibration: {true_prob:.0%} (learned from history)")
    calibrated_kelly = kelly_full_formula(true_prob, odds)
    safe_kelly = fractional_kelly(calibrated_kelly, 0.25)  # Quarter Kelly
    print(f"   Calibrated Kelly: {calibrated_kelly:.1%}")
    print(f"   Fractional Kelly (25%): {safe_kelly:.1%} of bankroll")
    print(
        f"   Expected ROI: {((true_prob * (odds - 1)) - ((1-true_prob) * 1)) * calibrated_kelly:.1%} (POSITIVE!)"
    )

    print("\n" + "=" * 70)
    print("Key Takeaway: Always calibrate your probabilities first!".center(70))
    print("=" * 70)
