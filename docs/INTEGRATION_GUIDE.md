# Integration Guide: Kelly Criterion with Your 10k Simulation Engine

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# All dependencies should already be in requirements.txt
pip install scikit-learn  # If not already installed

# Verify installation
python -c "from mcp_server.betting import BettingDecisionEngine; print('✓ Ready')"
```

### Step 2: Run Test Suite

```bash
python scripts/test_kelly_criterion.py
```

Expected output:
```
✅ ALL TESTS PASSED
✓ System is working correctly!
✓ Ready for integration with your 10k simulation engine
```

---

## Integration Pattern

### Your Current Workflow (Assumed)

```python
# Your existing simulation code
def run_game_simulation(home_team, away_team, n_sims=10000):
    """
    Run Monte Carlo simulation
    Returns win probabilities based on simulation results
    """
    results = []
    for _ in range(n_sims):
        outcome = simulate_single_game(home_team, away_team)
        results.append(outcome)

    home_wins = sum(1 for r in results if r == 'home')
    home_win_prob = home_wins / n_sims

    return {
        'home_win_prob': home_win_prob,
        'away_win_prob': 1 - home_win_prob,
        'simulation_results': results
    }

# Current usage
sim_result = run_game_simulation("LAL", "GSW", n_sims=10000)
print(f"Home win probability: {sim_result['home_win_prob']:.1%}")

# Now what? How much should I bet? ← THIS IS WHAT WE SOLVE
```

### NEW: Integrated Workflow

```python
from mcp_server.betting import BettingDecisionEngine

# ============================================
# ONE-TIME SETUP (Do this once)
# ============================================

# 1. Initialize engine
betting_engine = BettingDecisionEngine(
    calibrator_type='isotonic',  # Fast, or use 'bayesian' for uncertainty quantification
    fractional_kelly=0.25,        # Start with quarter Kelly
    adaptive_fractions=True       # Increase as model proves itself
)

# 2. Train calibrator on historical data
# Load your historical simulations and actual outcomes
historical_data = load_historical_simulation_data()  # Your function

betting_engine.train_calibrator(
    sim_probs=historical_data['simulation_probabilities'],
    outcomes=historical_data['actual_outcomes']
)

print("✓ Calibrator trained")

# ============================================
# EVERY GAME (Your betting loop)
# ============================================

def make_betting_decision(home_team, away_team, current_bankroll):
    """
    Complete pipeline: Simulation → Calibration → Kelly → Bet Size
    """
    # 1. Run your simulation (unchanged)
    sim_result = run_game_simulation(home_team, away_team, n_sims=10000)

    # 2. Fetch current market odds
    odds_data = fetch_market_odds(home_team, away_team)  # Your odds API

    # 3. Get betting decision from Kelly engine
    decision = betting_engine.decide(
        sim_prob=sim_result['home_win_prob'],
        odds=odds_data['home_decimal_odds'],
        away_odds=odds_data['away_decimal_odds'],
        bankroll=current_bankroll,
        game_id=f"{home_team}_vs_{away_team}_{datetime.now().strftime('%Y%m%d')}"
    )

    # 4. Decision made!
    return decision

# Example usage
decision = make_betting_decision("LAL", "GSW", current_bankroll=10000)

if decision['should_bet']:
    print(f"✓ BET ${decision['bet_amount']:.2f} on {home_team}")
    print(f"  Odds: {decision['odds']}")
    print(f"  Edge: {decision['edge']:.1%}")
    print(f"  Confidence: {decision['confidence']:.1%}")

    # Place bet via your betting platform
    place_bet(
        team=home_team,
        amount=decision['bet_amount'],
        odds=decision['odds']
    )
else:
    print(f"✗ NO BET: {decision['reason']}")

# 5. After game completes, update engine
engine.update_outcome(
    game_id=decision['game_id'],
    outcome=1 if home_team_won else 0,
    closing_odds=fetch_closing_odds(home_team, away_team)
)
```

---

## Detailed Integration Steps

### 1. Prepare Historical Data for Calibration

You need two arrays:
1. **Your simulation probabilities** (what your 10k sims said)
2. **Actual outcomes** (what really happened)

```python
import pandas as pd
import numpy as np

def prepare_calibration_data():
    """
    Extract historical simulation results and outcomes

    Required format:
        sim_probs: np.array of float (0 to 1)
        outcomes: np.array of int (0 or 1)
    """
    # Load your historical data (adjust to your data source)
    # This could be from:
    # - CSV files of past predictions
    # - Database query
    # - Saved simulation results

    historical_games = pd.read_csv('historical_predictions.csv')

    # Extract arrays
    sim_probs = historical_games['simulation_win_prob'].values
    outcomes = historical_games['actual_outcome'].values  # 1 = win, 0 = loss

    # Validate
    assert len(sim_probs) == len(outcomes), "Arrays must be same length"
    assert all(0 <= p <= 1 for p in sim_probs), "Probabilities must be 0-1"
    assert all(o in [0, 1] for o in outcomes), "Outcomes must be 0 or 1"

    print(f"Loaded {len(sim_probs)} historical games")
    print(f"Average simulation prob: {sim_probs.mean():.1%}")
    print(f"Actual win rate: {outcomes.mean():.1%}")
    print(f"Bias: {(sim_probs.mean() - outcomes.mean()):.1%}")

    return sim_probs, outcomes

# Use it
sim_probs, outcomes = prepare_calibration_data()

# Train engine
engine = BettingDecisionEngine()
engine.train_calibrator(sim_probs, outcomes)
```

### 2. Connect to Odds API

You need current market odds. Options:

**Option A: The Odds API** (Recommended)
```python
import requests

def fetch_odds_from_api(home_team, away_team):
    """
    Fetch odds from The Odds API or similar
    """
    # Your existing Odds API connector
    from mcp_server.connectors.odds_api_connector import OddsAPIConnector

    connector = OddsAPIConnector()
    odds_data = connector.get_odds()

    # Find the specific game
    for game in odds_data:
        if game['home_team'] == home_team and game['away_team'] == away_team:
            return {
                'home_decimal_odds': game['home_odds'],
                'away_decimal_odds': game['away_odds'],
                'timestamp': game['timestamp']
            }

    raise ValueError(f"No odds found for {home_team} vs {away_team}")

# Usage
odds = fetch_odds_from_api("LAL", "GSW")
print(f"Home: {odds['home_decimal_odds']}, Away: {odds['away_decimal_odds']}")
```

**Option B: Manual Input** (For testing)
```python
def manual_odds_input():
    """For testing without API"""
    return {
        'home_decimal_odds': 1.50,
        'away_decimal_odds': 2.80
    }
```

### 3. Track Performance Over Time

```python
def track_betting_performance(engine):
    """
    Monitor system performance to validate edge
    """
    summary = engine.performance_summary()

    print("=" * 60)
    print("BETTING PERFORMANCE SUMMARY")
    print("=" * 60)

    if 'error' not in summary:
        print(f"Total Bets: {summary['total_bets']}")
        print(f"Win Rate: {summary['win_rate']:.1%}")
        print(f"ROI: {summary['roi']:.1%}")
        print(f"")
        print(f"Average Edge: {summary['average_edge']:.1%}")
        print(f"Calibration (Brier): {summary['calibration_brier']:.3f}")
        print(f"")

        if 'clv_stats' in summary:
            clv_stats = summary['clv_stats']
            print(f"Average CLV: {clv_stats.get('average_clv', 0):.1%}")
            print(f"Is Sharp: {clv_stats.get('is_sharp', False)}")

    print("=" * 60)

# Call after every N games
track_betting_performance(betting_engine)
```

---

## Complete Example Script

```python
#!/usr/bin/env python3
"""
Complete integration example
Shows how to connect Kelly engine with your simulation
"""

from mcp_server.betting import BettingDecisionEngine
import numpy as np
from datetime import datetime

# ============================================
# YOUR SIMULATION CODE (Unchanged)
# ============================================

def run_10k_game_simulation(home_team, away_team):
    """
    Your existing Monte Carlo simulation
    Replace this with your actual simulation code
    """
    # Placeholder: Replace with your actual simulation
    home_win_prob = np.random.uniform(0.45, 0.85)  # Your simulation result

    return {
        'home_win_prob': home_win_prob,
        'away_win_prob': 1 - home_win_prob
    }

# ============================================
# KELLY ENGINE INTEGRATION
# ============================================

class BettingSystem:
    def __init__(self, initial_bankroll=10000):
        self.engine = BettingDecisionEngine(
            calibrator_type='isotonic',
            fractional_kelly=0.25,
            adaptive_fractions=True
        )
        self.bankroll = initial_bankroll
        self.bets = []

    def train_from_history(self, historical_sim_probs, historical_outcomes):
        """Train calibrator on historical data"""
        self.engine.train_calibrator(historical_sim_probs, historical_outcomes)
        print("✓ Calibrator trained on historical data")

    def analyze_game(self, home_team, away_team, odds_data):
        """
        Complete pipeline: Simulation → Calibration → Decision
        """
        # 1. Run simulation
        sim_result = run_10k_game_simulation(home_team, away_team)

        # 2. Get betting decision
        decision = self.engine.decide(
            sim_prob=sim_result['home_win_prob'],
            odds=odds_data['home_odds'],
            away_odds=odds_data['away_odds'],
            bankroll=self.bankroll,
            game_id=f"{home_team}_vs_{away_team}"
        )

        return decision

    def place_bet(self, decision):
        """Execute betting decision"""
        if decision['should_bet']:
            self.bets.append(decision)
            print(f"✓ BET PLACED: ${decision['bet_amount']:.2f}")
            return True
        else:
            print(f"✗ NO BET: {decision['reason']}")
            return False

    def update_result(self, game_id, outcome, closing_odds):
        """Update after game completes"""
        self.engine.update_outcome(game_id, outcome, closing_odds)

        # Update bankroll
        for bet in self.bets:
            if bet['game_id'] == game_id:
                if outcome == 1:
                    profit = bet['bet_amount'] * (bet['odds'] - 1)
                    self.bankroll += profit
                else:
                    self.bankroll -= bet['bet_amount']
                break

    def get_performance(self):
        """Get performance summary"""
        return self.engine.performance_summary()

# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    # 1. Initialize system
    system = BettingSystem(initial_bankroll=10000)

    # 2. Train on historical data (one time)
    # Replace with your actual historical data
    historical_sims = np.random.uniform(0.45, 0.95, 100)
    historical_outcomes = np.random.binomial(1, historical_sims)
    system.train_from_history(historical_sims, historical_outcomes)

    # 3. Analyze today's games
    games_today = [
        {
            'home': 'LAL',
            'away': 'GSW',
            'odds': {'home_odds': 1.50, 'away_odds': 2.80}
        },
        {
            'home': 'BOS',
            'away': 'MIA',
            'odds': {'home_odds': 1.75, 'away_odds': 2.20}
        }
    ]

    for game in games_today:
        print(f"\n{'='*60}")
        print(f"Analyzing: {game['home']} vs {game['away']}")
        print('=' * 60)

        decision = system.analyze_game(
            game['home'],
            game['away'],
            game['odds']
        )

        if decision['should_bet']:
            print(f"Simulation: {decision['simulation_prob']:.1%}")
            print(f"Calibrated: {decision['calibrated_prob']:.1%}")
            print(f"Edge: {decision['edge']:.1%}")
            print(f"Bet: ${decision['bet_amount']:.2f}")

            system.place_bet(decision)

    # 4. After games complete, update
    # system.update_result('LAL_vs_GSW', outcome=1, closing_odds=1.45)

    # 5. Check performance
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    perf = system.get_performance()
    print(f"Current Bankroll: ${system.bankroll:.2f}")
```

---

## Testing & Validation

### Phase 1: Historical Validation (Week 1)

```python
# Test on past games where you know outcomes
def validate_on_historical_data():
    engine = BettingDecisionEngine()

    # Load historical data
    historical = load_past_seasons(seasons=['2023-24'])

    # Train calibrator
    train_data = historical[historical['season'] == '2022-23']
    engine.train_calibrator(
        train_data['sim_probs'].values,
        train_data['outcomes'].values
    )

    # Test on 2023-24 season
    test_data = historical[historical['season'] == '2023-24']

    hypothetical_bankroll = 10000
    for _, game in test_data.iterrows():
        decision = engine.decide(
            sim_prob=game['sim_prob'],
            odds=game['home_odds'],
            away_odds=game['away_odds'],
            bankroll=hypothetical_bankroll,
            game_id=game['game_id']
        )

        if decision['should_bet']:
            if game['outcome'] == 1:
                hypothetical_bankroll += decision['bet_amount'] * (decision['odds'] - 1)
            else:
                hypothetical_bankroll -= decision['bet_amount']

    roi = (hypothetical_bankroll - 10000) / 10000
    print(f"Historical ROI: {roi:.1%}")

    if roi > 0.05:
        print("✓ System shows positive edge on historical data")
    else:
        print("✗ Recalibrate model before live deployment")
```

### Phase 2: Paper Trading (Week 2-4)

```python
# Track hypothetical bets for 50-100 games
paper_trading_log = []

for game in upcoming_games:
    decision = engine.decide(...)

    paper_trading_log.append({
        'game_id': game['id'],
        'decision': decision,
        'timestamp': datetime.now()
    })

    # After game
    actual_outcome = get_game_result(game['id'])
    decision['actual_outcome'] = actual_outcome

# Analyze after 50 games
analyze_paper_trading_results(paper_trading_log)

# Only go live if:
# - ROI > 5%
# - CLV > 2%
# - Brier < 0.10
```

---

## Next Steps

1. ✅ **Test suite passed** - System validated
2. 📝 **Prepare historical data** - Extract simulation results + outcomes
3. 🔧 **Train calibrator** - Run on historical data
4. 🧪 **Historical validation** - Test on past season
5. 📄 **Paper trade** - 50-100 games without real money
6. 💰 **Go live** - Start with small bankroll
7. 📊 **Monitor** - Track CLV, ROI, calibration drift

---

## Troubleshooting

### Problem: Calibration quality poor (Brier > 0.15)

**Solution:**
- Check if you have enough historical data (need 50+ games minimum)
- Verify simulation probabilities are correct
- Consider if your simulation methodology needs improvement

### Problem: Negative CLV consistently

**Solution:**
- Your edge is not real
- Recalibrate simulation model
- May need better features or more sophisticated simulation

### Problem: Recommended bets too small

**Solution:**
- This is intentional (system is conservative)
- As you prove edge (positive CLV over 50+ bets), fractions increase
- Start with quarter Kelly, increase to half Kelly after validation

---

## Support

- **Full Documentation**: `/mcp_server/betting/README.md`
- **Test Suite**: `scripts/test_kelly_criterion.py`
- **Implementation Guide**: `/docs/KELLY_CRITERION_IMPLEMENTATION.md`

Ready to integrate? Start with Step 1 above! 🚀
