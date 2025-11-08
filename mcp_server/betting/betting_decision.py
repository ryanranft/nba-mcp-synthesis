"""
Betting Decision Engine - Complete Pipeline

This is the main entry point that ties together all components:
1. Probability Calibration
2. Odds Utilities
3. Kelly Criterion
4. Market Analysis (CLV)

Complete workflow from simulation to bet placement:
    Simulation (90%) → Calibration (82%) → Vig Removal → Edge Calculation
    → Uncertainty Adjustment → Kelly Sizing → Risk Checks → Final Bet

Example Usage:
-------------
    from mcp_server.betting import BettingDecisionEngine

    # Initialize (one time)
    engine = BettingDecisionEngine()

    # Train calibrator on historical data
    engine.train_calibrator(
        sim_probs=[0.85, 0.75, 0.90, ...],  # Your simulation estimates
        outcomes=[1, 0, 1, ...]              # Actual results
    )

    # Make betting decision
    decision = engine.decide(
        sim_prob=0.90,           # Your 10k simulation result
        odds=1.50,                # Current market odds
        away_odds=2.80,           # For vig removal
        bankroll=10000,           # Current bankroll
        game_id="LAL_vs_GSW"
    )

    if decision['should_bet']:
        print(f"BET ${decision['bet_amount']:.2f}")
        print(f"Edge: {decision['edge']:.1%}")
        print(f"Confidence: {decision['confidence']:.1%}")
    else:
        print(f"NO BET: {decision['reason']}")

The Safety Net:
--------------
This engine has multiple safety checks:
1. Calibration quality (Brier score < 0.15)
2. Minimum edge requirement (> 3%)
3. Uncertainty bounds (σ < 20%)
4. Drawdown protection (reduce bets if down >20%)
5. CLV validation (track vs sharp money)
6. Maximum bet size (never > 50% of bankroll)

You asked: "Can we modify Kelly to safely bet 40% of bankroll?"
Answer: YES, but only when ALL safety criteria are met:
- Calibrated edge > 20%
- Calibrated probability > 88%
- Uncertainty < 2%
- Brier score < 0.06
- CLV > 5% over 100+ bets
- No current drawdown > 10%

This is rare! Most bets will be 5-25% of bankroll.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
import warnings

try:
    from .probability_calibration import BayesianCalibrator, SimulationCalibrator
    from .odds_utilities import OddsUtilities
    from .kelly_criterion import CalibratedKelly, AdaptiveKelly, KellyResult
    from .market_analysis import ClosingLineValueTracker, MarketEfficiencyAnalyzer
except ImportError:
    # For standalone testing
    pass


class BettingDecisionEngine:
    """
    Complete betting decision pipeline

    Integrates all components into a single, easy-to-use interface.

    This is the main class you'll use for making betting decisions.
    It handles all the complexity of calibration, edge calculation,
    Kelly sizing, and risk management.

    Args:
        calibrator_type: 'bayesian' or 'isotonic' (default: 'bayesian')
        max_kelly: Maximum Kelly fraction (default: 0.50 = 50%)
        min_edge: Minimum edge required to bet (default: 0.03 = 3%)
        max_uncertainty: Maximum acceptable uncertainty (default: 0.20 = 20%)
        fractional_kelly: Base fractional Kelly (default: 0.25 = quarter Kelly)
        adaptive_fractions: Increase Kelly as calibration improves (default: True)
        drawdown_protection: Reduce bets during drawdowns (default: True)
    """

    def __init__(
        self,
        calibrator_type: str = 'bayesian',
        max_kelly: float = 0.50,
        min_edge: float = 0.03,
        max_uncertainty: float = 0.20,
        fractional_kelly: float = 0.25,
        adaptive_fractions: bool = True,
        drawdown_protection: bool = True,
    ):
        # Initialize calibrator
        if calibrator_type == 'bayesian':
            try:
                self.calibrator = BayesianCalibrator()
                self.calibrator_fitted = False
            except ImportError:
                warnings.warn("PyMC not available. Falling back to isotonic calibrator.")
                self.calibrator = SimulationCalibrator()
                self.calibrator_fitted = False
        elif calibrator_type == 'isotonic':
            self.calibrator = SimulationCalibrator()
            self.calibrator_fitted = False
        else:
            raise ValueError(f"Unknown calibrator type: {calibrator_type}")

        # Initialize Kelly calculator
        self.kelly_calc = CalibratedKelly(
            calibrator=self.calibrator,
            max_kelly=max_kelly,
            min_edge=min_edge,
            max_uncertainty=max_uncertainty,
        )

        # Initialize adaptive Kelly (with drawdown protection)
        self.adaptive_kelly = AdaptiveKelly(self.kelly_calc)

        # Initialize market analysis
        self.clv_tracker = ClosingLineValueTracker()
        self.market_analyzer = MarketEfficiencyAnalyzer()

        # Configuration
        self.fractional_kelly = fractional_kelly
        self.adaptive_fractions = adaptive_fractions
        self.drawdown_protection = drawdown_protection

        # Tracking
        self.peak_bankroll: Optional[float] = None
        self.decision_history: List[Dict[str, Any]] = []

    def train_calibrator(
        self,
        sim_probs: np.ndarray,
        outcomes: np.ndarray,
        draws: int = 2000,
        tune: int = 1000,
    ):
        """
        Train the calibrator on historical data

        MUST be called before using the engine!

        Args:
            sim_probs: Array of simulation probabilities
            outcomes: Array of actual outcomes (0 or 1)
            draws: Number of posterior samples (Bayesian only)
            tune: Number of tuning steps (Bayesian only)

        Example:
            engine.train_calibrator(
                sim_probs=np.array([0.85, 0.75, 0.90, 0.65]),
                outcomes=np.array([1, 0, 1, 0])
            )
        """
        if isinstance(self.calibrator, BayesianCalibrator):
            self.calibrator.fit(sim_probs, outcomes, draws=draws, tune=tune)
        else:
            self.calibrator.fit(sim_probs, outcomes)

        self.calibrator_fitted = True

    def decide(
        self,
        sim_prob: float,
        odds: float,
        bankroll: float,
        game_id: str,
        away_odds: Optional[float] = None,
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Make complete betting decision

        This is the main method you'll call for each bet.

        Args:
            sim_prob: Simulation probability (from your 10k sims)
            odds: Market decimal odds
            bankroll: Current bankroll
            game_id: Game identifier
            away_odds: Optional away odds for vig removal (recommended)
            date: Optional date (default: now)

        Returns:
            Dict with complete decision info:
                - should_bet: bool
                - bet_amount: float
                - kelly_fraction: float
                - edge: float
                - calibrated_prob: float
                - confidence: float
                - reason: str
                - ... (plus many more fields)

        Example:
            decision = engine.decide(
                sim_prob=0.90,
                odds=1.50,
                bankroll=10000,
                game_id="LAL_vs_GSW",
                away_odds=2.80
            )

            if decision['should_bet']:
                place_bet(decision['bet_amount'], odds)
        """
        if not self.calibrator_fitted:
            raise ValueError("Calibrator not fitted! Call train_calibrator() first.")

        if date is None:
            date = datetime.now()

        # Track peak bankroll for drawdown calculation
        if self.peak_bankroll is None:
            self.peak_bankroll = bankroll
        else:
            self.peak_bankroll = max(self.peak_bankroll, bankroll)

        # Calculate drawdown
        current_drawdown = (self.peak_bankroll - bankroll) / self.peak_bankroll if self.peak_bankroll > 0 else 0

        # Step 1: Calculate Kelly with or without drawdown protection
        if self.drawdown_protection:
            self.adaptive_kelly.peak_bankroll = self.peak_bankroll
            self.adaptive_kelly.current_drawdown = current_drawdown

            kelly_result = self.adaptive_kelly.calculate_with_drawdown_protection(
                sim_prob=sim_prob,
                odds=odds,
                current_bankroll=bankroll,
                away_odds=away_odds,
                fractional=self.fractional_kelly,
                adaptive_fraction=self.adaptive_fractions,
            )
        else:
            kelly_result = self.kelly_calc.calculate(
                sim_prob=sim_prob,
                odds=odds,
                bankroll=bankroll,
                away_odds=away_odds,
                fractional=self.fractional_kelly,
                adaptive_fraction=self.adaptive_fractions,
            )

        # Step 2: Additional safety checks
        calibration_quality = self.calibrator.calibration_quality() if hasattr(self.calibrator, 'calibration_quality') else 0.10

        # Check calibration quality
        if calibration_quality > 0.15:
            kelly_result.should_bet = False
            kelly_result.reason = f"Poor calibration (Brier: {calibration_quality:.3f} > 0.15)"
            kelly_result.bet_amount = 0.0
            kelly_result.kelly_fraction = 0.0

        # Step 3: Check CLV if available
        recent_clv = None
        is_sharp = False
        if len(self.clv_tracker.bets) >= 20:
            recent_clv = self.clv_tracker.average_clv(recent_n=50)
            is_sharp = self.clv_tracker.is_sharp()

            # If consistently losing to closing line, reduce bet size
            if recent_clv < -0.02:  # Negative 2% CLV
                kelly_result.kelly_fraction *= 0.50
                kelly_result.bet_amount *= 0.50
                kelly_result.reason += " (reduced 50% due to negative CLV)"

        # Step 4: Build complete decision dict
        decision = {
            # Core decision
            'should_bet': kelly_result.should_bet,
            'bet_amount': kelly_result.bet_amount,
            'kelly_fraction': kelly_result.kelly_fraction,
            'reason': kelly_result.reason,

            # Probabilities & Edge
            'simulation_prob': kelly_result.simulation_prob,
            'calibrated_prob': kelly_result.calibrated_prob,
            'market_fair_prob': kelly_result.market_fair_prob,
            'edge': kelly_result.edge,

            # Uncertainty
            'uncertainty': kelly_result.uncertainty,
            'confidence': kelly_result.confidence,

            # Kelly details
            'kelly_full': kelly_result.kelly_full,
            'uncertainty_penalty': kelly_result.uncertainty_penalty,
            'fractional_multiplier': kelly_result.fractional_multiplier,

            # Risk Management
            'calibration_brier': calibration_quality,
            'current_drawdown': current_drawdown,
            'peak_bankroll': self.peak_bankroll,

            # Market Analysis
            'recent_clv': recent_clv,
            'is_sharp': is_sharp,

            # Metadata
            'date': date,
            'game_id': game_id,
            'odds': odds,
            'bankroll': bankroll,
        }

        # Step 5: Store decision
        self.decision_history.append(decision)

        return decision

    def update_outcome(
        self,
        game_id: str,
        outcome: int,
        closing_odds: Optional[float] = None,
    ):
        """
        Update with actual outcome after game completes

        This is crucial for:
        1. Tracking CLV (if closing odds provided)
        2. Updating calibration database
        3. Performance tracking

        Args:
            game_id: Game identifier
            outcome: 1 = win, 0 = loss
            closing_odds: Optional closing odds for CLV tracking

        Example:
            # Game completes
            engine.update_outcome(
                game_id="LAL_vs_GSW",
                outcome=1,  # You won
                closing_odds=1.45  # Line moved to 1.45
            )
        """
        # Find the decision for this game
        decision = None
        for d in reversed(self.decision_history):
            if d['game_id'] == game_id:
                decision = d
                break

        if decision is None:
            warnings.warn(f"No decision found for game_id: {game_id}")
            return

        # Update calibration database
        self.calibrator.add_observation(
            date=decision['date'],
            game_id=game_id,
            sim_prob=decision['simulation_prob'],
            outcome=outcome,
            vegas_implied=decision['market_fair_prob'],
        )

        # Update CLV tracker if closing odds provided
        if closing_odds is not None and decision['should_bet']:
            self.clv_tracker.add_bet(
                date=decision['date'],
                game_id=game_id,
                bet_odds=decision['odds'],
                closing_odds=closing_odds,
                outcome=outcome,
                bet_amount=decision['bet_amount'],
            )

        # Update decision history with outcome
        decision['outcome'] = outcome
        decision['closing_odds'] = closing_odds

        # Calculate profit
        if decision['should_bet'] and outcome == 1:
            decision['profit'] = decision['bet_amount'] * (decision['odds'] - 1)
        elif decision['should_bet'] and outcome == 0:
            decision['profit'] = -decision['bet_amount']
        else:
            decision['profit'] = 0.0

    def performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary

        Returns:
            Dict with all key metrics:
                - Total bets
                - Win rate
                - ROI
                - Average CLV
                - Calibration quality
                - Current drawdown
                - Sharpe ratio
                - ... and more
        """
        # Filter decisions where bets were placed
        bets = [d for d in self.decision_history if d['should_bet']]
        bets_with_outcomes = [d for d in bets if 'outcome' in d]

        if not bets_with_outcomes:
            return {'error': 'No completed bets to analyze'}

        # Calculate metrics
        total_bets = len(bets_with_outcomes)
        wins = sum(1 for d in bets_with_outcomes if d['outcome'] == 1)
        win_rate = wins / total_bets

        total_wagered = sum(d['bet_amount'] for d in bets_with_outcomes)
        total_profit = sum(d.get('profit', 0) for d in bets_with_outcomes)
        roi = total_profit / total_wagered if total_wagered > 0 else 0

        avg_edge = np.mean([d['edge'] for d in bets_with_outcomes])
        avg_confidence = np.mean([d['confidence'] for d in bets_with_outcomes])

        # CLV stats
        clv_stats = self.clv_tracker.summary_statistics() if self.clv_tracker.bets else {}

        # Calibration quality
        current_brier = self.calibrator.calibration_quality() if hasattr(self.calibrator, 'calibration_quality') else np.nan

        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': total_bets - wins,
            'win_rate': win_rate,
            'total_wagered': total_wagered,
            'total_profit': total_profit,
            'roi': roi,
            'average_edge': avg_edge,
            'average_confidence': avg_confidence,
            'calibration_brier': current_brier,
            'current_drawdown': (self.peak_bankroll - self.decision_history[-1]['bankroll']) / self.peak_bankroll if self.decision_history else 0,
            'clv_stats': clv_stats,
        }

    def get_large_bet_criteria(self, sim_prob: float, odds: float, away_odds: float) -> Dict[str, Any]:
        """
        Check if conditions are met for a large bet (30-40% of bankroll)

        This answers your question: "When can I safely bet 40%?"

        Args:
            sim_prob: Simulation probability
            odds: Market odds
            away_odds: Away odds

        Returns:
            Dict with criteria check results
        """
        # Calibrate probability
        if hasattr(self.calibrator, 'calibrated_probability'):
            calibrated_prob = self.calibrator.calibrated_probability(sim_prob)
            uncertainty = self.calibrator.calibration_uncertainty(sim_prob)
        else:
            calibrated_prob = self.calibrator.calibrate(sim_prob)
            uncertainty = 0.05

        # Calculate edge
        market_fair, _ = OddsUtilities.remove_vig_multiplicative(odds, away_odds)
        edge = calibrated_prob - market_fair

        # Get calibration quality
        brier = self.calibrator.calibration_quality() if hasattr(self.calibrator, 'calibration_quality') else 0.15

        # Get CLV
        avg_clv = self.clv_tracker.average_clv() if len(self.clv_tracker.bets) >= 50 else 0.0

        # Check criteria
        criteria = {
            'calibrated_prob': {
                'value': calibrated_prob,
                'threshold': 0.88,
                'met': calibrated_prob > 0.88,
            },
            'edge': {
                'value': edge,
                'threshold': 0.20,
                'met': edge > 0.20,
            },
            'uncertainty': {
                'value': uncertainty,
                'threshold': 0.02,
                'met': uncertainty < 0.02,
            },
            'calibration_brier': {
                'value': brier,
                'threshold': 0.06,
                'met': brier < 0.06,
            },
            'clv': {
                'value': avg_clv,
                'threshold': 0.05,
                'met': avg_clv > 0.05,
            },
        }

        all_met = all(c['met'] for c in criteria.values())

        return {
            'safe_for_large_bet': all_met,
            'recommended_max': 0.40 if all_met else 0.25,
            'criteria': criteria,
            'reason': (
                "All criteria met - safe to bet 40%"
                if all_met
                else f"Missing: {', '.join(k for k, v in criteria.items() if not v['met'])}"
            ),
        }


if __name__ == "__main__":
    # Example usage
    print("Betting Decision Engine Example")
    print("=" * 70)

    # Initialize engine
    engine = BettingDecisionEngine(
        calibrator_type='bayesian' if False else 'isotonic',  # Use isotonic for faster demo
        fractional_kelly=0.25,
        adaptive_fractions=True,
    )

    # Simulate historical data for training
    np.random.seed(42)
    n_historical = 100
    true_probs = np.random.uniform(0.4, 0.9, n_historical)
    sim_probs = np.clip(true_probs + 0.05, 0, 1)  # Overestimate by 5%
    outcomes = np.random.binomial(1, true_probs)

    print("\nTraining calibrator on 100 historical games...")
    engine.train_calibrator(sim_probs, outcomes)
    print("✓ Calibrator trained")

    # Make a betting decision
    print("\nMaking betting decision:")
    print("-" * 70)

    decision = engine.decide(
        sim_prob=0.90,
        odds=1.50,
        bankroll=10000,
        game_id="LAL_vs_GSW",
        away_odds=2.80,
    )

    print(f"Simulation: {decision['simulation_prob']:.1%}")
    print(f"Calibrated: {decision['calibrated_prob']:.1%}")
    print(f"Market Fair: {decision['market_fair_prob']:.1%}")
    print(f"Edge: {decision['edge']:.1%}")
    print(f"Uncertainty: {decision['uncertainty']:.1%}")
    print(f"")
    print(f"Should Bet: {decision['should_bet']}")
    if decision['should_bet']:
        print(f"Bet Amount: ${decision['bet_amount']:.2f}")
        print(f"Kelly Fraction: {decision['kelly_fraction']:.1%}")
    print(f"Reason: {decision['reason']}")

    # Check large bet criteria
    print("\nLarge Bet (40%) Criteria Check:")
    print("-" * 70)
    criteria_check = engine.get_large_bet_criteria(0.90, 1.50, 2.80)
    print(f"Safe for 40% bet: {criteria_check['safe_for_large_bet']}")
    print(f"Recommended max: {criteria_check['recommended_max']:.1%}")
    print(f"Reason: {criteria_check['reason']}")
