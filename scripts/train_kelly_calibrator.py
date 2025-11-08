#!/usr/bin/env python3
"""
Kelly Criterion Calibrator Training

Trains the Bayesian calibrator on historical game predictions to correct
simulation bias (e.g., 90% sim → 60% reality). Uses the calibration data
generated from backtesting.

Usage:
    python scripts/train_kelly_calibrator.py
    python scripts/train_kelly_calibrator.py --data data/calibration_training_data.csv --output models/
"""

import argparse
import sys
import warnings
from pathlib import Path
from datetime import datetime
import dill as pickle
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.betting import BettingDecisionEngine, BayesianCalibrator

warnings.filterwarnings('ignore')


def load_calibration_data(data_path: str):
    """Load calibration training data."""
    print(f"Loading calibration data from {data_path}...")
    df = pd.read_csv(data_path)

    sim_probs = df['sim_prob'].values
    outcomes = df['outcome'].values

    print(f"✓ Loaded {len(df)} predictions")
    print(f"  Home win rate: {outcomes.mean():.1%}")
    print(f"  Prob range: [{sim_probs.min():.3f}, {sim_probs.max():.3f}]")

    return sim_probs, outcomes, df


def train_calibrator(sim_probs: np.ndarray, outcomes: np.ndarray, calibrator_type: str = 'bayesian'):
    """
    Train the Kelly Criterion calibrator.

    Args:
        sim_probs: Simulation probabilities
        outcomes: Actual outcomes (0 or 1)
        calibrator_type: 'bayesian' or 'isotonic'

    Returns:
        Trained BettingDecisionEngine
    """
    print(f"\nTraining {calibrator_type} calibrator...")
    print("-" * 80)

    # Initialize betting decision engine
    engine = BettingDecisionEngine(
        calibrator_type=calibrator_type,
        fractional_kelly=0.25,  # Quarter Kelly (conservative)
        adaptive_fractions=True,  # Adjust based on uncertainty
        max_kelly=0.40  # Maximum 40% of bankroll
    )

    # Train calibrator
    print("Training calibrator on historical data...")
    engine.train_calibrator(sim_probs=sim_probs, outcomes=outcomes)

    print("✓ Calibrator training complete!")

    return engine


def evaluate_calibration(
    engine: BettingDecisionEngine,
    sim_probs: np.ndarray,
    outcomes: np.ndarray,
    output_dir: Path
):
    """Evaluate calibration quality and generate diagnostic plots."""
    print("\n" + "=" * 80)
    print("Calibration Evaluation")
    print("=" * 80)

    # Generate calibrated probabilities
    print("\nGenerating calibrated probabilities...")
    calibrated_probs = np.array([
        engine.calibrator.calibrated_probability(p) for p in sim_probs
    ])

    # Compute metrics
    brier_uncalibrated = brier_score_loss(outcomes, sim_probs)
    brier_calibrated = brier_score_loss(outcomes, calibrated_probs)

    print(f"\nBrier Scores:")
    print(f"  Uncalibrated: {brier_uncalibrated:.4f}")
    print(f"  Calibrated:   {brier_calibrated:.4f}")
    print(f"  Improvement:  {(brier_uncalibrated - brier_calibrated):.4f} ({((brier_uncalibrated - brier_calibrated) / brier_uncalibrated * 100):.1f}%)")

    # Calibration quality assessment
    if hasattr(engine.calibrator, 'calibration_quality'):
        quality = engine.calibrator.calibration_quality()
        print(f"\nCalibration Quality Score: {quality:.4f}")

        if quality < 0.06:
            print("  ✓ EXCELLENT - Ready for 40% bets")
        elif quality < 0.10:
            print("  ✓ GOOD - Safe for betting")
        elif quality < 0.15:
            print("  ⚠ ACCEPTABLE - Use with caution")
        else:
            print("  ❌ POOR - Do NOT use for betting")

    # Plot calibration curves
    plot_calibration_comparison(sim_probs, calibrated_probs, outcomes, output_dir)

    # Plot calibration correction
    plot_calibration_correction(sim_probs, calibrated_probs, output_dir)

    # Uncertainty analysis (for Bayesian calibrator)
    if isinstance(engine.calibrator, BayesianCalibrator):
        plot_uncertainty_analysis(engine.calibrator, sim_probs, output_dir)

    return {
        'brier_uncalibrated': brier_uncalibrated,
        'brier_calibrated': brier_calibrated,
        'improvement': brier_uncalibrated - brier_calibrated,
        'improvement_pct': (brier_uncalibrated - brier_calibrated) / brier_uncalibrated * 100
    }


def plot_calibration_comparison(
    sim_probs: np.ndarray,
    calibrated_probs: np.ndarray,
    outcomes: np.ndarray,
    output_dir: Path
):
    """Plot before/after calibration curves."""
    # Compute calibration curves
    prob_true_uncal, prob_pred_uncal = calibration_curve(outcomes, sim_probs, n_bins=10)
    prob_true_cal, prob_pred_cal = calibration_curve(outcomes, calibrated_probs, n_bins=10)

    # Compute Brier scores
    brier_uncal = brier_score_loss(outcomes, sim_probs)
    brier_cal = brier_score_loss(outcomes, calibrated_probs)

    plt.figure(figsize=(10, 8))

    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', linewidth=2)
    plt.plot(prob_pred_uncal, prob_true_uncal, 'rs-',
             label=f'Before Calibration (Brier: {brier_uncal:.4f})',
             linewidth=2, markersize=8, alpha=0.7)
    plt.plot(prob_pred_cal, prob_true_cal, 'go-',
             label=f'After Calibration (Brier: {brier_cal:.4f})',
             linewidth=2, markersize=8)

    plt.xlabel('Predicted Probability', fontsize=13)
    plt.ylabel('Actual Frequency', fontsize=13)
    plt.title('Calibration Curve: Before vs After', fontsize=15, fontweight='bold')
    plt.legend(fontsize=11, loc='best')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(output_dir / 'calibration_comparison.png', dpi=150)
    print(f"\n✓ Saved calibration comparison to {output_dir}/calibration_comparison.png")


def plot_calibration_correction(
    sim_probs: np.ndarray,
    calibrated_probs: np.ndarray,
    output_dir: Path
):
    """Plot how calibration corrects probabilities."""
    # Sort for smooth plotting
    sorted_idx = np.argsort(sim_probs)
    sim_sorted = sim_probs[sorted_idx]
    cal_sorted = calibrated_probs[sorted_idx]

    plt.figure(figsize=(10, 8))

    plt.plot([0, 1], [0, 1], 'k--', label='No Correction', linewidth=2)
    plt.plot(sim_sorted, cal_sorted, 'b-', label='Calibration Function', linewidth=2)

    plt.fill_between(sim_sorted, sim_sorted, cal_sorted, alpha=0.2, color='blue',
                     label='Correction Amount')

    plt.xlabel('Uncalibrated Probability', fontsize=13)
    plt.ylabel('Calibrated Probability', fontsize=13)
    plt.title('Calibration Correction Function', fontsize=15, fontweight='bold')
    plt.legend(fontsize=11, loc='best')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(output_dir / 'calibration_correction.png', dpi=150)
    print(f"✓ Saved calibration correction to {output_dir}/calibration_correction.png")


def plot_uncertainty_analysis(calibrator: BayesianCalibrator, sim_probs: np.ndarray, output_dir: Path):
    """Plot uncertainty estimates from Bayesian calibrator."""
    # Sample test probabilities
    test_probs = np.linspace(0.1, 0.9, 50)

    calibrated = []
    uncertainties = []

    for p in test_probs:
        cal_p = calibrator.calibrated_probability(p)
        unc = calibrator.calibration_uncertainty(p)
        calibrated.append(cal_p)
        uncertainties.append(unc)

    calibrated = np.array(calibrated)
    uncertainties = np.array(uncertainties)

    plt.figure(figsize=(10, 8))

    plt.plot(test_probs, calibrated, 'b-', linewidth=2, label='Calibrated Probability')
    plt.fill_between(test_probs,
                     calibrated - uncertainties,
                     calibrated + uncertainties,
                     alpha=0.3, color='blue', label='±1 Uncertainty')

    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect Calibration')

    plt.xlabel('Simulation Probability', fontsize=13)
    plt.ylabel('Calibrated Probability', fontsize=13)
    plt.title('Bayesian Calibration with Uncertainty', fontsize=15, fontweight='bold')
    plt.legend(fontsize=11, loc='best')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(output_dir / 'bayesian_uncertainty.png', dpi=150)
    print(f"✓ Saved uncertainty analysis to {output_dir}/bayesian_uncertainty.png")


def test_large_bet_criteria(engine: BettingDecisionEngine, output_dir: Path):
    """Test when the system would recommend 40% bets."""
    print("\n" + "=" * 80)
    print("Large Bet Criteria Analysis")
    print("=" * 80)

    # Test various probabilities
    test_cases = [
        (0.88, 2.2, 1.9),  # 88% prob, +120/-110 odds
        (0.90, 2.0, 1.95),  # 90% prob, Even/-105 odds
        (0.85, 2.5, 1.85),  # 85% prob, +150/-118 odds
        (0.75, 1.8, 2.0),   # 75% prob, -125/+100 odds
    ]

    print("\nTesting criteria for 40% bet recommendation:")
    print("-" * 80)

    for sim_prob, home_odds, away_odds in test_cases:
        result = engine.get_large_bet_criteria(sim_prob, home_odds, away_odds)

        print(f"\nSim Prob: {sim_prob:.1%}, Odds: {home_odds:.2f} / {away_odds:.2f}")
        print(f"  Calibrated Prob: {result['criteria']['calibrated_prob']['value']:.1%}")
        print(f"  Edge: {result['criteria']['edge']['value']:.1%}")
        print(f"  Uncertainty: {result['criteria']['uncertainty']['value']:.1%}")
        print(f"  Brier Score: {result['criteria']['calibration_brier']['value']:.4f}")
        print(f"  Safe for 40%: {'✓ YES' if result['safe_for_large_bet'] else '✗ NO'}")
        if not result['safe_for_large_bet']:
            print(f"  Reason: {result['reason']}")


def main():
    parser = argparse.ArgumentParser(
        description="Train Kelly Criterion calibrator"
    )
    parser.add_argument(
        '--data',
        default='data/calibration_training_data.csv',
        help='Path to calibration training data CSV'
    )
    parser.add_argument(
        '--calibrator-type',
        default='bayesian',
        choices=['bayesian', 'isotonic'],
        help='Type of calibrator to use'
    )
    parser.add_argument(
        '--output',
        default='models/',
        help='Output directory for calibrated model'
    )
    parser.add_argument(
        '--plots-dir',
        default='plots/',
        help='Directory for diagnostic plots'
    )

    args = parser.parse_args()

    # Create output directories
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    plots_dir = Path(args.plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Kelly Criterion Calibrator Training")
    print("=" * 80)
    print(f"Calibration Data: {args.data}")
    print(f"Calibrator Type: {args.calibrator_type}")
    print(f"Output: {args.output}")
    print()

    # Load data
    sim_probs, outcomes, df = load_calibration_data(args.data)

    # Train calibrator
    engine = train_calibrator(sim_probs, outcomes, args.calibrator_type)

    # Evaluate calibration
    metrics = evaluate_calibration(engine, sim_probs, outcomes, plots_dir)

    # Test large bet criteria
    test_large_bet_criteria(engine, plots_dir)

    # Save calibrated engine
    print(f"\nSaving calibrated engine to {output_dir}/calibrated_kelly_engine.pkl...")
    with open(output_dir / 'calibrated_kelly_engine.pkl', 'wb') as f:
        pickle.dump(engine, f)
    print("✓ Saved successfully")

    # Save metadata
    metadata = {
        'training_date': datetime.now().isoformat(),
        'calibrator_type': args.calibrator_type,
        'training_samples': len(sim_probs),
        'brier_uncalibrated': metrics['brier_uncalibrated'],
        'brier_calibrated': metrics['brier_calibrated'],
        'improvement': metrics['improvement'],
        'improvement_pct': metrics['improvement_pct'],
        'fractional_kelly': engine.fractional_kelly,
        'max_kelly': engine.kelly_calc.max_kelly
    }

    with open(output_dir / 'calibrator_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to {output_dir}/calibrator_metadata.json")

    # Summary
    print("\n" + "=" * 80)
    print("Calibrator Training Complete!")
    print("=" * 80)
    print(f"Brier Score Improvement: {metrics['improvement']:.4f} ({metrics['improvement_pct']:.1f}%)")
    print(f"Final Brier Score: {metrics['brier_calibrated']:.4f}")

    if metrics['brier_calibrated'] < 0.06:
        print("\n✓ EXCELLENT calibration - Ready for production!")
    elif metrics['brier_calibrated'] < 0.10:
        print("\n✓ GOOD calibration - Safe for betting")
    elif metrics['brier_calibrated'] < 0.15:
        print("\n⚠ ACCEPTABLE calibration - Use with caution")
    else:
        print("\n❌ POOR calibration - Consider collecting more data")

    print("\nNext steps:")
    print("  1. Run: python scripts/test_calibrated_system.py")
    print("  2. This will validate the complete betting system")
    print(f"  3. Review calibration plots in {plots_dir}/")


if __name__ == '__main__':
    main()
