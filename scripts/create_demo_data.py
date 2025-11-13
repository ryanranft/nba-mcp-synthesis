#!/usr/bin/env python3
"""
Create Demo Data for Dashboard Testing

Generates realistic paper trading data and calibration records
for testing the monitoring dashboard.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from random import random, randint, choice, uniform
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.betting.paper_trading import PaperTradingEngine, BetStatus
from mcp_server.betting.probability_calibration import SimulationCalibrator


def create_demo_bets(num_bets: int = 50):
    """Create demo betting data"""
    print(f"📊 Creating {num_bets} demo bets...")

    engine = PaperTradingEngine(starting_bankroll=10000, db_path="data/paper_trades.db")

    # Team pairs for games
    matchups = [
        ("LAL", "GSW"),
        ("BOS", "MIA"),
        ("MIL", "PHI"),
        ("DEN", "LAC"),
        ("PHX", "DAL"),
        ("BKN", "NYK"),
        ("CHI", "CLE"),
        ("TOR", "ATL"),
        ("MEM", "POR"),
        ("SAC", "UTA"),
    ]

    # Simulate betting over 30 days
    start_date = datetime.now() - timedelta(days=30)

    bet_count = 0
    win_count = 0

    for i in range(num_bets):
        # Random date within last 30 days
        days_ago = randint(0, 29)
        bet_date = start_date + timedelta(days=days_ago, hours=randint(12, 22))

        # Random matchup
        home, away = choice(matchups)
        game_id = f"{home}_vs_{away}_{bet_date.strftime('%Y%m%d')}"

        # Random bet details
        bet_type = choice(["home", "away"])
        odds = uniform(1.70, 2.50)
        sim_prob = uniform(0.50, 0.75)
        edge = sim_prob * odds - 1

        # Kelly fraction suggests bet size
        kelly_fraction = 0.25  # Quarter Kelly
        optimal_kelly = edge / (odds - 1) if odds > 1 else 0
        bet_amount = min(
            max(engine.current_bankroll * optimal_kelly * kelly_fraction, 50),
            engine.current_bankroll * 0.10,
        )

        # Create bet
        try:
            bet = engine.place_bet(
                game_id=game_id,
                bet_type=bet_type,
                amount=bet_amount,
                odds=odds,
                sim_prob=sim_prob,
                edge=edge,
                kelly_fraction=kelly_fraction,
                notes=f"Demo bet {i+1}",
            )

            # Settle bet (win/loss based on simulation probability with some noise)
            # Add slight underestimation to make it realistic
            actual_win_prob = sim_prob * 0.95  # Slight miscalibration

            if random() < actual_win_prob:
                outcome = "win"
                win_count += 1
            else:
                outcome = "loss"

            # Random closing odds for CLV calculation
            closing_odds = odds * uniform(0.95, 1.05)

            # Settle the bet
            engine.settle_bet(
                bet_id=bet.bet_id, outcome=outcome, closing_odds=closing_odds
            )

            bet_count += 1

        except Exception as e:
            print(f"  ⚠️  Skipped bet {i+1}: {e}")
            continue

    # Get final stats
    stats = engine.get_performance_stats()

    print(f"\n✅ Created {bet_count} bets")
    print(f"   Win Rate: {stats['win_rate']*100:.1f}%")
    print(f"   Final Bankroll: ${stats['bankroll']:,.2f}")
    print(f"   ROI: {stats['roi']*100:+.1f}%")
    print(f"   Sharpe Ratio: {stats['sharpe_ratio']:.2f}")


def create_demo_calibration(num_predictions: int = 100):
    """Create demo calibration data"""
    print(f"\n🎯 Creating {num_predictions} calibration records...")

    calibrator = SimulationCalibrator()

    # Generate predictions with slight miscalibration
    sim_probs = []
    outcomes = []

    for i in range(num_predictions):
        # Predicted probability
        sim_prob = uniform(0.45, 0.80)
        sim_probs.append(sim_prob)

        # Actual outcome (add miscalibration - overconfidence)
        # True probability is slightly lower than predicted
        true_prob = sim_prob * 0.95
        actual_outcome = 1 if random() < true_prob else 0
        outcomes.append(actual_outcome)

        # Random game
        game_id = f"DEMO_GAME_{i:04d}"

        # Vegas implied probability (market is usually well calibrated)
        vegas_odds = uniform(1.80, 2.20)
        vegas_prob = 1 / vegas_odds

        # Add to database
        calibrator.calibration_db.add_record(
            date=datetime.now() - timedelta(days=randint(0, 29)),
            game_id=game_id,
            simulation_prob=sim_prob,
            actual_outcome=actual_outcome,
            vegas_implied_prob=vegas_prob,
        )

    # Fit the calibrator
    calibrator.fit(np.array(sim_probs), np.array(outcomes))

    # Calculate calibration quality
    brier = calibrator.calibration_quality()

    print(f"✅ Created {num_predictions} calibration records")
    print(f"   Brier Score: {brier:.4f}")

    quality = "Excellent" if brier < 0.10 else "Good" if brier < 0.15 else "Acceptable"
    print(f"   Quality: {quality}")


def main():
    """Generate all demo data"""
    print("=" * 60)
    print("Creating Demo Data for Dashboard Testing")
    print("=" * 60)
    print()

    # Create paper trading data
    create_demo_bets(num_bets=50)

    # Create calibration data
    create_demo_calibration(num_predictions=100)

    print()
    print("=" * 60)
    print("✅ Demo data creation complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Launch dashboard: ./scripts/launch_dashboard.sh")
    print("  2. View at: http://localhost:8501")
    print()


if __name__ == "__main__":
    main()
