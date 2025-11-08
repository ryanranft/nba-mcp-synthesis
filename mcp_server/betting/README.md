# Econometric-Enhanced Kelly Criterion for Sports Betting

## Overview

This module implements a **safe, econometrically-sound betting system** that addresses the critical flaw in standard Kelly Criterion: **the assumption of perfect probability calibration**.

### The Problem You Identified

> "If my 10,000 simulations say 90% win rate but reality is only 60%, Kelly will recommend catastrophic overbetting."

**You're absolutely right.** Standard Kelly assumes your probabilities are perfectly calibrated. This module solves that problem.

### The Solution

This system:
1. ✅ **Calibrates** simulation probabilities against historical reality (Bayesian & Isotonic methods)
2. ✅ **Quantifies uncertainty** using Bayesian posteriors
3. ✅ **Adjusts Kelly fractions** based on model uncertainty
4. ✅ **Validates edge** through Closing Line Value (CLV) tracking
5. ✅ **Detects market inefficiencies** via cointegration tests
6. ✅ **Protects against drawdowns** with adaptive risk management

---

## Quick Start

### Installation

```bash
# Add to requirements.txt
scikit-learn>=1.3.0      # For isotonic calibration
pymc>=5.0.0              # For Bayesian calibration
arviz>=0.16.0            # For Bayesian diagnostics
statsmodels>=0.14.0      # For market efficiency tests

# Install
pip install scikit-learn pymc arviz statsmodels
```

### Basic Usage

```python
from mcp_server.betting import BettingDecisionEngine
import numpy as np

# 1. Initialize engine
engine = BettingDecisionEngine(
    calibrator_type='bayesian',  # or 'isotonic'
    fractional_kelly=0.25,        # Start with quarter Kelly
    adaptive_fractions=True,      # Increase as model proves itself
)

# 2. Train calibrator on historical data
# CRITICAL: You MUST train the calibrator first!
engine.train_calibrator(
    sim_probs=np.array([0.85, 0.75, 0.90, 0.65, 0.80, ...]),  # Your simulation estimates
    outcomes=np.array([1, 0, 1, 0, 1, ...])                    # Actual results (1=win, 0=loss)
)

# 3. Make betting decision
decision = engine.decide(
    sim_prob=0.90,           # Your 10k simulation says 90%
    odds=1.50,                # Current market odds
    away_odds=2.80,           # Away odds (for vig removal)
    bankroll=10000,           # Current bankroll
    game_id="LAL_vs_GSW"
)

# 4. Check decision
if decision['should_bet']:
    print(f"✓ BET ${decision['bet_amount']:.2f} at {decision['odds']}")
    print(f"  Edge: {decision['edge']:.1%}")
    print(f"  Confidence: {decision['confidence']:.1%}")
    print(f"  Kelly: {decision['kelly_fraction']:.1%}")
else:
    print(f"✗ NO BET: {decision['reason']}")

# 5. Update with outcome after game
engine.update_outcome(
    game_id="LAL_vs_GSW",
    outcome=1,              # 1 = won, 0 = lost
    closing_odds=1.45       # Closing line (for CLV tracking)
)

# 6. Check performance
summary = engine.performance_summary()
print(f"ROI: {summary['roi']:.1%}")
print(f"CLV: {summary['clv_stats']['average_clv']:.1%}")
print(f"Brier: {summary['calibration_brier']:.3f}")
```

---

## When Can I Safely Bet 40% of Bankroll?

**Short answer:** Rarely, and only when ALL these conditions are met:

```python
criteria = engine.get_large_bet_criteria(sim_prob, odds, away_odds)

if criteria['safe_for_large_bet']:
    print("✓ Safe to bet 40% of bankroll")
else:
    print(f"✗ Missing: {criteria['reason']}")
```

**Required Criteria:**
- ✅ Calibrated probability > 88%
- ✅ Calibrated edge > 20%
- ✅ Uncertainty (σ) < 2%
- ✅ Brier score < 0.06 (excellent calibration)
- ✅ CLV > 5% over 100+ bets
- ✅ No current drawdown > 10%

**Reality:** Most bets will be 5-25% of bankroll. A 40% bet requires an exceptional edge that's been validated by sharp money.

---

## Module Structure

```
mcp_server/betting/
├── __init__.py                     # Main exports
├── README.md                        # This file
├── probability_calibration.py      # Calibration (Bayesian + Isotonic)
├── odds_utilities.py                # Vig removal, edge calculation
├── kelly_criterion.py               # Uncertainty-adjusted Kelly
├── market_analysis.py               # CLV tracker, market efficiency
└── betting_decision.py              # Complete pipeline (USE THIS!)
```

---

## Key Components

### 1. Probability Calibration

**Problem:** Your simulation says 90%, but reality is 82%

**Solution:** Learn calibration mapping from historical data

```python
from mcp_server.betting import BayesianCalibrator

calibrator = BayesianCalibrator()
calibrator.fit(sim_probs, outcomes, draws=2000)

# Get calibrated probability with uncertainty
p_calibrated = calibrator.calibrated_probability(0.90, quantile=0.50)  # Median
p_uncertainty = calibrator.calibration_uncertainty(0.90)

print(f"Simulation: 90%")
print(f"Calibrated: {p_calibrated:.1%}")
print(f"Uncertainty: ±{p_uncertainty:.1%}")
```

**Bayesian vs Isotonic:**
- **Bayesian:** Provides uncertainty quantification (use for Kelly)
- **Isotonic:** Faster, no uncertainty (use for quick calibration)

### 2. Odds Utilities

**Problem:** Bookmakers add vig, making naive probabilities wrong

**Solution:** Remove vig to get fair market probability

```python
from mcp_server.betting import OddsUtilities

# Remove vig
home_fair, away_fair = OddsUtilities.remove_vig_multiplicative(
    home_odds=1.91,  # 52.4% implied
    away_odds=1.91   # 52.4% implied
    # Sum: 104.8% (4.8% vig)
)

print(f"Fair probabilities: {home_fair:.1%}, {away_fair:.1%}")
# Output: 50.0%, 50.0%

# Calculate edge
edge = OddsUtilities.calculate_edge(
    your_probability=0.85,
    market_odds=1.50,
    away_odds=2.80
)

print(f"Your edge: {edge:.1%}")
```

### 3. Kelly Criterion

**Problem:** Standard Kelly over-bets when probabilities are uncertain

**Solution:** Uncertainty-adjusted Kelly with fractional sizing

```python
from mcp_server.betting import CalibratedKelly

kelly = CalibratedKelly(calibrator)

result = kelly.calculate(
    sim_prob=0.90,
    odds=1.50,
    bankroll=10000,
    away_odds=2.80,
    fractional=0.25,           # Quarter Kelly
    adaptive_fraction=True      # Increase as model improves
)

print(f"Kelly fraction: {result.kelly_fraction:.1%}")
print(f"Bet amount: ${result.bet_amount:.2f}")
print(f"Uncertainty penalty: {result.uncertainty_penalty:.2f}x")
```

**Adaptive Fractions:**
- Brier < 0.06: 100% Kelly (full Kelly)
- Brier < 0.08: 75% Kelly
- Brier < 0.10: 50% Kelly (half Kelly)
- Brier < 0.15: 25% Kelly (quarter Kelly)
- Brier > 0.15: 10% Kelly (very conservative)

### 4. Market Analysis

**Problem:** How do you know if your edge is real?

**Solution:** Track Closing Line Value (CLV)

```python
from mcp_server.betting import ClosingLineValueTracker

tracker = ClosingLineValueTracker()

# Track bets
tracker.add_bet(
    date=datetime.now(),
    game_id="LAL_vs_GSW",
    bet_odds=2.00,      # You bet at 2.00
    closing_odds=1.80    # Closed at 1.80 (sharp money agrees!)
)

# Check if sharp
if tracker.is_sharp():
    print("✓ You're beating sharp money - edge is real!")
else:
    print("✗ Losing to closing line - recalibrate model")

print(f"Average CLV: {tracker.average_clv():.1%}")
```

**CLV Interpretation:**
- **> 2%**: Sharp bettor (trust your edge)
- **0-2%**: Marginal edge (be careful)
- **< 0%**: No edge (DO NOT BET - recalibrate!)

---

## Safety Features

This system has multiple layers of protection:

1. **Calibration Quality Check**: Won't bet if Brier score > 0.15
2. **Minimum Edge Requirement**: Requires at least 3% edge
3. **Uncertainty Bounds**: Reduces bet size when uncertain
4. **Maximum Kelly**: Never bets > 50% of bankroll
5. **Drawdown Protection**: Reduces bets when down > 20%, stops at > 30%
6. **CLV Validation**: Reduces bet size if losing to closing line

---

## Example Scenario: Your 90% Simulation

Let's walk through your specific case:

```python
# Your simulation
sim_prob = 0.90  # 9,000 of 10,000 sims won

# Market
home_odds = 1.50  # (66.7% implied)
away_odds = 2.80  # (35.7% implied)

# Bankroll
bankroll = 10000

# Decision pipeline
engine = BettingDecisionEngine()
engine.train_calibrator(historical_sim_probs, historical_outcomes)

decision = engine.decide(
    sim_prob=0.90,
    odds=1.50,
    away_odds=2.80,
    bankroll=10000,
    game_id="example"
)

print(decision)
```

**Expected Output:**
```
Simulation: 90.0%
Calibrated: 85.0% (adjusted for historical bias)
Market Fair: 65.1% (after vig removal)
Edge: 19.9%
Uncertainty: 3.0%

Should Bet: True
Kelly Full: 55%
Uncertainty Penalty: 0.85x
Fractional Kelly: 0.50x (half Kelly due to Brier=0.08)
Final Kelly: 23.4%

Bet Amount: $2,340
Reason: Strong edge + good calibration
```

**Why not 40%?**
- Uncertainty (3%) is acceptable but not excellent (<2% needed)
- Need to validate with positive CLV over 100+ bets first
- Fractional Kelly is conservative until model proves itself

**After 100 bets with positive CLV:**
- Fractional multiplier increases to 0.75-1.0
- Bet size could reach 30-40% for similar edges

---

## Performance Tracking

```python
# Get comprehensive summary
summary = engine.performance_summary()

print(f"""
Total Bets: {summary['total_bets']}
Win Rate: {summary['win_rate']:.1%}
ROI: {summary['roi']:.1%}
Average Edge: {summary['average_edge']:.1%}
Calibration (Brier): {summary['calibration_brier']:.3f}
Average CLV: {summary['clv_stats']['average_clv']:.1%}
Is Sharp: {summary['clv_stats']['is_sharp']}
Current Drawdown: {summary['current_drawdown']:.1%}
""")
```

---

## Advanced Usage

### Custom Calibration

```python
from mcp_server.betting import BayesianCalibrator

calibrator = BayesianCalibrator()

# Fit with custom MCMC settings
calibrator.fit(
    sim_probs,
    outcomes,
    draws=4000,    # More samples (better but slower)
    tune=2000,     # More tuning
    chains=4       # More chains
)

# Check diagnostics
diag = calibrator.diagnostics()
print(f"Rhat: {diag['slope_rhat']:.4f}")  # Should be < 1.01
print(f"ESS: {diag['slope_ess']:.0f}")     # Should be > 400
print(f"Divergences: {diag['divergences']}")  # Should be 0
```

### Portfolio Kelly (Multiple Correlated Bets)

```python
from mcp_server.betting import AdaptiveKelly

adaptive_kelly = AdaptiveKelly(calibrated_kelly)

# Multiple bets on same slate
bets = [
    {'sim_prob': 0.85, 'odds': 1.50, 'away_odds': 2.80},
    {'sim_prob': 0.75, 'odds': 2.00, 'away_odds': 2.00},
    {'sim_prob': 0.65, 'odds': 2.50, 'away_odds': 1.60},
]

# Optimize Kelly across portfolio (accounts for correlation)
results = adaptive_kelly.portfolio_kelly(bets, bankroll=10000)

for i, result in enumerate(results):
    print(f"Bet {i+1}: ${result.bet_amount:.2f}")
```

### Market Efficiency Tests

```python
from mcp_server.betting import MarketEfficiencyAnalyzer

analyzer = MarketEfficiencyAnalyzer()

# Detect mispricing
result = analyzer.detect_mispricing(
    current_value=235,      # Current total
    historical_mean=215,    # Historical average
    historical_std=8,       # Historical std dev
    threshold=2.0           # Z-score threshold
)

if result['mispriced']:
    print(f"Mispricing detected: {result['direction']}")
    print(f"Z-score: {result['z_score']:.2f}")

# Cointegration test
result = analyzer.cointegration_test(
    series1=home_odds_history,
    series2=away_odds_history
)

if not result['cointegrated']:
    print("Market inefficiency: prices not cointegrated!")
```

---

## FAQ

### Q: Do I need to use Bayesian calibration?

**A:** No, isotonic calibration is simpler and faster. Use Bayesian if you want uncertainty quantification for Kelly adjustment.

### Q: How many historical games do I need?

**A:** Minimum 50 for isotonic, 100+ for Bayesian. More is better. Recalibrate every 6-12 months.

### Q: What if I don't have closing odds for CLV?

**A:** You can still use the system, but CLV validation is highly recommended. Without it, you won't know if your edge is real.

### Q: Can I use this for other sports?

**A:** Yes! The system is sport-agnostic. Just train the calibrator on your sport's historical data.

### Q: What's the minimum bankroll?

**A:** Technically any amount, but Kelly is designed for long-term growth. Minimum $1,000 recommended.

### Q: Should I always follow the recommendation?

**A:** The system is conservative by design. You can override, but track results to validate your intuition.

---

## References

- Kelly, J. L. (1956). "A New Interpretation of Information Rate"
- Thorp, E. O. (2006). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
- MacLean, L. C., Thorp, E. O., & Ziemba, W. T. (2011). "The Kelly Capital Growth Investment Criterion"

---

## License

Part of NBA MCP Analytics Platform
Version 1.0.0

For support, see main repository documentation.
