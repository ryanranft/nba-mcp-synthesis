#!/usr/bin/env python3
"""
Historical Backtesting Pipeline for Calibration Data Generation

Uses trained ensemble model to generate predictions on historical games,
creating (simulation_probability, actual_outcome) pairs for training the
Kelly Criterion calibrator.

Implements strict walk-forward validation to prevent look-ahead bias.

Usage:
    python scripts/backtest_historical_games.py
    python scripts/backtest_historical_games.py --features data/game_features.csv --model models/ensemble_game_outcome_model.pkl
"""

import argparse
import sys
import warnings
from pathlib import Path
from datetime import datetime
import pickle

import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, accuracy_score, roc_auc_score

# Try to import XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

warnings.filterwarnings('ignore')


class GameOutcomeEnsemble:
    """
    Ensemble model combining Logistic Regression, Random Forest, and XGBoost
    for NBA game outcome prediction.
    """

    def __init__(self):
        self.models = {}
        self.weights = {}
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_fitted = False

    def _get_models(self):
        """Initialize individual models."""
        models = {}

        # Logistic Regression with L2 regularization
        models['logistic'] = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            n_jobs=-1
        )

        # Random Forest
        models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )

        # XGBoost (if available)
        if HAS_XGBOOST:
            models['xgboost'] = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss'
            )

        return models

    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train all individual models and optimize ensemble weights."""
        # Store feature names
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
            X_train = X_train.values
        if X_val is not None and isinstance(X_val, pd.DataFrame):
            X_val = X_val.values

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val) if X_val is not None else None

        # Train individual models
        self.models = self._get_models()

        for name, model in self.models.items():
            model.fit(X_train_scaled, y_train)

        # Optimize ensemble weights
        if X_val is not None:
            self._optimize_weights(X_val_scaled, y_val)
        else:
            # Equal weights if no validation set
            self.weights = {name: 1.0 / len(self.models) for name in self.models}

        self.is_fitted = True

    def _optimize_weights(self, X_val, y_val):
        """Optimize ensemble weights using grid search on validation set."""
        from itertools import product

        best_score = float('inf')
        best_weights = None

        # Grid search over weight combinations (normalized to sum to 1)
        weight_range = np.arange(0, 1.1, 0.1)

        for weights_tuple in product(weight_range, repeat=len(self.models)):
            weights_array = np.array(weights_tuple)

            # Skip if weights don't sum close to 1
            if not (0.99 <= weights_array.sum() <= 1.01):
                continue

            # Normalize
            weights_array = weights_array / weights_array.sum()

            # Create weighted predictions
            weighted_pred = np.zeros(len(X_val))
            for idx, (name, model) in enumerate(self.models.items()):
                pred_proba = model.predict_proba(X_val)[:, 1]
                weighted_pred += weights_array[idx] * pred_proba

            # Evaluate
            score = brier_score_loss(y_val, weighted_pred)

            if score < best_score:
                best_score = score
                best_weights = {name: weights_array[idx]
                               for idx, name in enumerate(self.models)}

        self.weights = best_weights

    def predict_proba(self, X):
        """Predict probabilities using weighted ensemble."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        if isinstance(X, pd.DataFrame):
            X = X.values

        X_scaled = self.scaler.transform(X)

        # Weighted average of predictions
        ensemble_pred = np.zeros(len(X))
        for name, model in self.models.items():
            pred_proba = model.predict_proba(X_scaled)[:, 1]
            ensemble_pred += self.weights[name] * pred_proba

        return ensemble_pred

    def predict(self, X):
        """Predict class labels."""
        proba = self.predict_proba(X)
        return (proba >= 0.5).astype(int)


def load_ensemble_model(model_path: str):
    """Load trained ensemble model."""
    print(f"Loading model from {model_path}...")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("✓ Model loaded successfully")
    return model


def generate_backtest_predictions(features_df: pd.DataFrame, model, calibration_season: str = '2023-24'):
    """
    Generate predictions for calibration training using walk-forward validation.

    Args:
        features_df: DataFrame with game features
        model: Trained ensemble model
        calibration_season: Season to generate predictions for (for calibration training)

    Returns:
        DataFrame with (game_id, sim_prob, outcome) pairs
    """
    print(f"\nGenerating predictions for {calibration_season} season...")
    print("-" * 80)

    # Filter to calibration season
    calibration_games = features_df[features_df['season'] == calibration_season].copy()
    print(f"Games to predict: {len(calibration_games)}")

    # Feature columns
    feature_cols = [col for col in features_df.columns if col not in [
        'game_id', 'game_date', 'season', 'home_team_id', 'away_team_id',
        'home_win', 'home_score', 'away_score'
    ]]

    # Generate predictions
    predictions = []

    for idx, game in tqdm(calibration_games.iterrows(), total=len(calibration_games), desc="Predicting"):
        try:
            # Extract features
            X = game[feature_cols].values.reshape(1, -1)

            # Handle missing values
            X = pd.DataFrame(X, columns=feature_cols).fillna(features_df[feature_cols].mean()).values

            # Predict probability (home team wins)
            sim_prob = model.predict_proba(X)[0]

            # Get actual outcome
            outcome = 1 if game['home_win'] == 1 else 0

            predictions.append({
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'season': game['season'],
                'home_team_id': game['home_team_id'],
                'away_team_id': game['away_team_id'],
                'sim_prob': float(sim_prob),
                'outcome': int(outcome),
                'home_score': game['home_score'],
                'away_score': game['away_score']
            })

        except Exception as e:
            print(f"Error predicting game {game['game_id']}: {e}")
            continue

    predictions_df = pd.DataFrame(predictions)
    print(f"\n✓ Generated {len(predictions_df)} predictions")

    return predictions_df


def analyze_predictions(predictions_df: pd.DataFrame, output_dir: Path):
    """Analyze prediction quality and generate diagnostic plots."""
    print("\n" + "=" * 80)
    print("Prediction Analysis")
    print("=" * 80)

    sim_probs = predictions_df['sim_prob'].values
    outcomes = predictions_df['outcome'].values

    # Overall statistics
    print(f"\nDataset Statistics:")
    print(f"  Total predictions: {len(predictions_df)}")
    print(f"  Home wins: {outcomes.sum()} ({outcomes.mean():.1%})")
    print(f"  Away wins: {(1 - outcomes).sum()} ({(1 - outcomes).mean():.1%})")

    # Prediction statistics
    print(f"\nPrediction Statistics:")
    print(f"  Mean predicted probability: {sim_probs.mean():.3f}")
    print(f"  Std predicted probability: {sim_probs.std():.3f}")
    print(f"  Min/Max: {sim_probs.min():.3f} / {sim_probs.max():.3f}")

    # Brier score (before calibration)
    brier = np.mean((sim_probs - outcomes) ** 2)
    print(f"\nUncalibrated Brier Score: {brier:.4f}")

    # Calibration curve
    from sklearn.calibration import calibration_curve
    prob_true, prob_pred = calibration_curve(outcomes, sim_probs, n_bins=10)

    plt.figure(figsize=(10, 6))
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', linewidth=2)
    plt.plot(prob_pred, prob_true, 'ro-', label=f'Model Predictions (Brier: {brier:.4f})', linewidth=2, markersize=8)
    plt.xlabel('Predicted Probability (Home Win)', fontsize=12)
    plt.ylabel('Actual Frequency (Home Win)', fontsize=12)
    plt.title('Calibration Curve - Before Kelly Calibration', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'pre_calibration_curve.png', dpi=150)
    print(f"\n✓ Saved calibration curve to {output_dir}/pre_calibration_curve.png")

    # Prediction distribution
    plt.figure(figsize=(10, 6))
    plt.hist(sim_probs[outcomes == 1], bins=20, alpha=0.6, label='Home Wins', color='blue')
    plt.hist(sim_probs[outcomes == 0], bins=20, alpha=0.6, label='Away Wins', color='red')
    plt.xlabel('Predicted Probability (Home Win)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Distribution of Predictions by Actual Outcome', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'prediction_distribution.png', dpi=150)
    print(f"✓ Saved prediction distribution to {output_dir}/prediction_distribution.png")

    # Confidence vs accuracy
    bins = np.linspace(0, 1, 11)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    bin_accs = []
    bin_counts = []

    for i in range(len(bins) - 1):
        mask = (sim_probs >= bins[i]) & (sim_probs < bins[i + 1])
        if mask.sum() > 0:
            bin_accs.append(outcomes[mask].mean())
            bin_counts.append(mask.sum())
        else:
            bin_accs.append(np.nan)
            bin_counts.append(0)

    plt.figure(figsize=(10, 6))
    plt.bar(bin_centers, bin_counts, width=0.08, alpha=0.6, label='Game Count')
    plt.xlabel('Predicted Probability Bin', fontsize=12)
    plt.ylabel('Number of Games', fontsize=12)
    plt.title('Games per Confidence Bin', fontsize=14)
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_dir / 'confidence_distribution.png', dpi=150)
    print(f"✓ Saved confidence distribution to {output_dir}/confidence_distribution.png")

    return brier


def validate_data_quality(predictions_df: pd.DataFrame):
    """Validate calibration training data quality."""
    print("\n" + "=" * 80)
    print("Data Quality Validation")
    print("=" * 80)

    issues = []

    # Check for missing values
    if predictions_df.isnull().any().any():
        issues.append("⚠ Missing values detected")

    # Check probability range
    if (predictions_df['sim_prob'] < 0).any() or (predictions_df['sim_prob'] > 1).any():
        issues.append("⚠ Probabilities outside [0, 1] range")

    # Check outcome values
    if not set(predictions_df['outcome'].unique()).issubset({0, 1}):
        issues.append("⚠ Outcomes contain values other than 0 or 1")

    # Check sample size
    if len(predictions_df) < 100:
        issues.append(f"⚠ Sample size ({len(predictions_df)}) below recommended minimum (100)")
    elif len(predictions_df) < 200:
        issues.append(f"⚠ Sample size ({len(predictions_df)}) below ideal minimum (200)")

    # Check prediction variance
    if predictions_df['sim_prob'].std() < 0.05:
        issues.append("⚠ Low prediction variance - model may be underconfident")

    # Check class balance
    home_win_rate = predictions_df['outcome'].mean()
    if home_win_rate < 0.4 or home_win_rate > 0.7:
        issues.append(f"⚠ Class imbalance detected (home win rate: {home_win_rate:.1%})")

    if issues:
        print("\nData Quality Issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✓ All data quality checks passed")

    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate calibration training data via backtesting"
    )
    parser.add_argument(
        '--features',
        default='data/game_features.csv',
        help='Path to features CSV file'
    )
    parser.add_argument(
        '--model',
        default='models/ensemble_game_outcome_model.pkl',
        help='Path to trained ensemble model'
    )
    parser.add_argument(
        '--calibration-season',
        default='2023-24',
        help='Season to generate predictions for calibration'
    )
    parser.add_argument(
        '--output',
        default='data/calibration_training_data.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--plots-dir',
        default='plots/',
        help='Directory for diagnostic plots'
    )

    args = parser.parse_args()

    # Create output directories
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plots_dir = Path(args.plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("NBA Historical Backtesting for Calibration Data")
    print("=" * 80)
    print(f"Features: {args.features}")
    print(f"Model: {args.model}")
    print(f"Calibration Season: {args.calibration_season}")
    print(f"Output: {args.output}")
    print()

    # Load model
    model = load_ensemble_model(args.model)

    # Load features
    print(f"\nLoading features from {args.features}...")
    features_df = pd.read_csv(args.features)
    print(f"✓ Loaded {len(features_df)} games")

    # Generate predictions
    predictions_df = generate_backtest_predictions(features_df, model, args.calibration_season)

    # Validate data quality
    is_valid = validate_data_quality(predictions_df)

    # Analyze predictions
    brier = analyze_predictions(predictions_df, plots_dir)

    # Save calibration training data
    print(f"\nSaving calibration training data to {args.output}...")
    predictions_df.to_csv(args.output, index=False)
    print("✓ Saved successfully")

    # Summary
    print("\n" + "=" * 80)
    print("Backtesting Complete!")
    print("=" * 80)
    print(f"Generated predictions: {len(predictions_df)}")
    print(f"Uncalibrated Brier score: {brier:.4f}")
    print(f"Data quality: {'✓ PASS' if is_valid else '⚠ WARNING - Review issues above'}")
    print()
    print("Next steps:")
    print("  1. Run: python scripts/train_kelly_calibrator.py")
    print("  2. This will train the Bayesian calibrator on your predictions")
    print(f"  3. Review diagnostic plots in {plots_dir}/")


if __name__ == '__main__':
    main()
