"""
NBA MCP Betting Module - Econometric-Enhanced Kelly Criterion

This module implements a sophisticated betting framework that addresses the critical flaw
in standard Kelly Criterion: the assumption of perfect probability calibration.

Key Components:
---------------
1. probability_calibration.py - Calibrates simulation probabilities against historical reality
2. odds_utilities.py - Vig removal, implied probabilities, fair odds calculation
3. market_analysis.py - Market efficiency tests, cointegration, CLV tracking
4. kelly_criterion.py - Core Kelly implementation with uncertainty adjustment
5. bankroll_management.py - Risk management, drawdown protection, VaR
6. betting_decision.py - End-to-end betting pipeline
7. backtesting.py - Historical validation and walk-forward testing

The Econometric Enhancement:
---------------------------
Unlike naive Kelly which uses raw probabilities, this system:
- Calibrates probabilities using Bayesian methods (accounts for model uncertainty)
- Validates edge through Closing Line Value (CLV) tracking
- Detects market inefficiencies via cointegration tests
- Adjusts bet sizing based on calibration quality
- Only recommends large bets (30-40%) when all criteria are met

Example Usage:
-------------
    from mcp_server.betting import BettingDecisionEngine

    engine = BettingDecisionEngine()
    decision = engine.make_betting_decision(
        game_id="LAL_vs_GSW_2024",
        simulation_prob=0.90,  # Your 10k sim result
        bankroll=10000
    )

    if decision['bet']:
        print(f"Bet ${decision['amount']:.2f} at odds {decision['odds']}")
        print(f"Edge: {decision['edge']:.1%}, Confidence: {decision['confidence']:.1%}")
    else:
        print(f"No bet: {decision['reason']}")

Safety Features:
---------------
- Never bets >50% of bankroll on single game
- Reduces bet size during drawdowns (>20%)
- Stops betting if calibration degrades (Brier >0.15)
- Requires minimum 3% edge before placing bet
- Validates with CLV before recommending large bets

Author: NBA MCP Analytics Team
Version: 1.0.0
"""

__version__ = "1.0.0"

from typing import Dict, List, Optional, Tuple, Any

# Import key classes
from .probability_calibration import (
    BayesianCalibrator,
    SimulationCalibrator,
    CalibrationDatabase,
    CalibrationRecord,
)

from .odds_utilities import (
    OddsUtilities,
    OddsConverter,
    OddsFormat,
    VigRemovalMethod,
)

from .kelly_criterion import (
    CalibratedKelly,
    AdaptiveKelly,
    KellyResult,
    kelly_full_formula,
    fractional_kelly,
)

from .market_analysis import (
    ClosingLineValueTracker,
    MarketEfficiencyAnalyzer,
    BetRecord,
)

from .betting_decision import (
    BettingDecisionEngine,
)

# Core exports
__all__ = [
    # Main Interface
    "BettingDecisionEngine",
    # Calibration
    "BayesianCalibrator",
    "SimulationCalibrator",
    "CalibrationDatabase",
    "CalibrationRecord",
    # Kelly Criterion
    "CalibratedKelly",
    "AdaptiveKelly",
    "KellyResult",
    "kelly_full_formula",
    "fractional_kelly",
    # Odds Utilities
    "OddsUtilities",
    "OddsConverter",
    "OddsFormat",
    "VigRemovalMethod",
    # Market Analysis
    "ClosingLineValueTracker",
    "MarketEfficiencyAnalyzer",
    "BetRecord",
]

# Version info
VERSION = __version__
