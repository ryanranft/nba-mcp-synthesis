#!/usr/bin/env python3
"""
Ensemble Model Training for NBA Game Outcome Prediction

Trains Logistic Regression, Random Forest, and XGBoost models, then creates
an optimized weighted ensemble for predicting game outcomes.

Usage:
    python scripts/train_game_outcome_model.py
    python scripts/train_game_outcome_model.py --features data/game_features.csv --output models/
"""

import argparse
import sys
import warnings
from pathlib import Path
from datetime import datetime
import pickle
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
    classification_report,
    confusion_matrix,
)
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import xgboost as xgb

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("Warning: XGBoost not installed. Install with: pip install xgboost")

warnings.filterwarnings("ignore")


class GameOutcomeEnsemble:
    """
    Ensemble model combining Logistic Regression, Random Forest, and XGBoost
    for NBA game outcome prediction.
    """

    def __init__(self, use_stacking=False, meta_learner_type="logistic"):
        """
        Initialize ensemble model.

        Args:
            use_stacking: If True, use stacking meta-learner instead of weighted average
            meta_learner_type: Type of meta-learner ('logistic', 'ridge', or 'both')
        """
        self.models = {}
        self.weights = {}
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_fitted = False

        # Stacking configuration
        self.use_stacking = use_stacking
        self.meta_learner_type = meta_learner_type
        self.meta_learner = None
        self.meta_learners = {}  # For 'both' option

    def _get_models(self):
        """Initialize individual models."""
        models = {}

        # Logistic Regression with L2 regularization
        models["logistic"] = LogisticRegression(
            C=1.0, max_iter=1000, random_state=42, n_jobs=-1
        )

        # Random Forest
        models["random_forest"] = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )

        # XGBoost (if available)
        if HAS_XGBOOST:
            models["xgboost"] = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric="logloss",
            )
        else:
            print("⚠ XGBoost not available, using LR + RF only")

        return models

    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train all individual models and optimize ensemble weights.

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional, for weight optimization)
            y_val: Validation labels (optional)
        """
        print("Training Ensemble Model")
        print("=" * 80)

        # Store feature names
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
            X_train = X_train.values
        if X_val is not None and isinstance(X_val, pd.DataFrame):
            X_val = X_val.values

        # Scale features
        print("Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val) if X_val is not None else None

        # Train individual models
        self.models = self._get_models()

        for name, model in self.models.items():
            print(f"\nTraining {name}...")
            model.fit(X_train_scaled, y_train)

            # Evaluate on training set
            train_pred_proba = model.predict_proba(X_train_scaled)[:, 1]
            train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
            train_auc = roc_auc_score(y_train, train_pred_proba)
            train_brier = brier_score_loss(y_train, train_pred_proba)

            print(
                f"  Train - Accuracy: {train_acc:.4f}, AUC: {train_auc:.4f}, Brier: {train_brier:.4f}"
            )

            # Evaluate on validation set if provided
            if X_val is not None:
                val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
                val_acc = accuracy_score(y_val, model.predict(X_val_scaled))
                val_auc = roc_auc_score(y_val, val_pred_proba)
                val_brier = brier_score_loss(y_val, val_pred_proba)

                print(
                    f"  Val   - Accuracy: {val_acc:.4f}, AUC: {val_auc:.4f}, Brier: {val_brier:.4f}"
                )

        # Optimize ensemble (stacking or weighted average)
        if X_val is not None:
            if self.use_stacking:
                # Train stacking meta-learner
                self._fit_stacking(X_train_scaled, y_train, X_val_scaled, y_val)
            else:
                # Traditional weighted ensemble
                print("\nOptimizing ensemble weights...")
                self._optimize_weights(X_val_scaled, y_val)

                print("\nOptimal weights:")
                for name, weight in self.weights.items():
                    print(f"  {name}: {weight:.3f}")
        else:
            if self.use_stacking:
                raise ValueError("Stacking requires validation set (X_val, y_val)")
            # Equal weights if no validation set
            self.weights = {name: 1.0 / len(self.models) for name in self.models}

        self.is_fitted = True
        ensemble_type = "stacking" if self.use_stacking else "weighted"
        print(f"\n✓ {ensemble_type.capitalize()} ensemble training complete!")

    def _optimize_weights(self, X_val, y_val):
        """Optimize ensemble weights using grid search on validation set."""
        from itertools import product

        best_score = float("inf")
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
                best_weights = {
                    name: weights_array[idx] for idx, name in enumerate(self.models)
                }

        self.weights = best_weights

    def _generate_meta_features(self, X, y, n_folds=5):
        """
        Generate meta-features using k-fold cross-validation.

        Args:
            X: Training features (scaled)
            y: Training labels
            n_folds: Number of CV folds

        Returns:
            Meta-features array (n_samples, n_models)
        """
        n_samples = len(X)
        n_models = len(self.models)
        meta_features = np.zeros((n_samples, n_models))

        kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)

        print(f"  Generating meta-features using {n_folds}-fold CV...")

        for fold_idx, (train_idx, val_idx) in enumerate(kfold.split(X)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train = (
                y.iloc[train_idx] if isinstance(y, pd.Series) else y[train_idx]
            )

            # Train base models on fold
            for model_idx, (name, model) in enumerate(self.models.items()):
                model_copy = clone(model)
                model_copy.fit(X_fold_train, y_fold_train)

                # Predict on validation fold
                pred_proba = model_copy.predict_proba(X_fold_val)[:, 1]
                meta_features[val_idx, model_idx] = pred_proba

        print(f"  ✓ Meta-features generated: shape {meta_features.shape}")
        return meta_features

    def _get_base_predictions(self, X):
        """
        Get predictions from all base models.

        Args:
            X: Features (scaled)

        Returns:
            Array of base model predictions (n_samples, n_models)
        """
        predictions = np.zeros((len(X), len(self.models)))

        for idx, (name, model) in enumerate(self.models.items()):
            predictions[:, idx] = model.predict_proba(X)[:, 1]

        return predictions

    def _fit_stacking(self, X_train, y_train, X_val, y_val):
        """
        Train stacking meta-learner(s).

        Args:
            X_train: Training features (scaled)
            y_train: Training labels
            X_val: Validation features (scaled)
            y_val: Validation labels
        """
        print("\nTraining stacking meta-learner...")

        # Generate meta-features from training data
        meta_features_train = self._generate_meta_features(X_train, y_train)

        # Get base predictions on validation set
        meta_features_val = self._get_base_predictions(X_val)

        # Train meta-learner(s)
        if self.meta_learner_type == "both":
            # Train both and compare
            print("\n  Training Logistic Regression meta-learner...")
            meta_logistic = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
            meta_logistic.fit(meta_features_train, y_train)

            val_pred_logistic = meta_logistic.predict_proba(meta_features_val)[:, 1]
            brier_logistic = brier_score_loss(y_val, val_pred_logistic)
            acc_logistic = accuracy_score(y_val, (val_pred_logistic >= 0.5).astype(int))

            print(
                f"    Val - Accuracy: {acc_logistic:.4f}, Brier: {brier_logistic:.4f}"
            )

            print("\n  Training Ridge meta-learner...")
            meta_ridge = Ridge(alpha=1.0, random_state=42)
            meta_ridge.fit(meta_features_train, y_train)

            val_pred_ridge = meta_ridge.predict(meta_features_val)
            val_pred_ridge = np.clip(val_pred_ridge, 0, 1)  # Clip to [0, 1] range
            brier_ridge = brier_score_loss(y_val, val_pred_ridge)
            acc_ridge = accuracy_score(y_val, (val_pred_ridge >= 0.5).astype(int))

            print(f"    Val - Accuracy: {acc_ridge:.4f}, Brier: {brier_ridge:.4f}")

            # Store both
            self.meta_learners = {"logistic": meta_logistic, "ridge": meta_ridge}

            # Select best based on Brier score
            if brier_logistic < brier_ridge:
                self.meta_learner = meta_logistic
                best_name = "logistic"
                best_brier = brier_logistic
            else:
                self.meta_learner = meta_ridge
                best_name = "ridge"
                best_brier = brier_ridge

            print(f"\n  ✓ Best meta-learner: {best_name} (Brier: {best_brier:.4f})")

        elif self.meta_learner_type == "ridge":
            print("\n  Training Ridge meta-learner...")
            self.meta_learner = Ridge(alpha=1.0, random_state=42)
            self.meta_learner.fit(meta_features_train, y_train)

            val_pred = self.meta_learner.predict(meta_features_val)
            val_pred = np.clip(val_pred, 0, 1)
            brier = brier_score_loss(y_val, val_pred)
            acc = accuracy_score(y_val, (val_pred >= 0.5).astype(int))

            print(f"    Val - Accuracy: {acc:.4f}, Brier: {brier:.4f}")

        else:  # logistic (default)
            print("\n  Training Logistic Regression meta-learner...")
            self.meta_learner = LogisticRegression(
                C=1.0, max_iter=1000, random_state=42
            )
            self.meta_learner.fit(meta_features_train, y_train)

            val_pred = self.meta_learner.predict_proba(meta_features_val)[:, 1]
            brier = brier_score_loss(y_val, val_pred)
            acc = accuracy_score(y_val, (val_pred >= 0.5).astype(int))

            print(f"    Val - Accuracy: {acc:.4f}, Brier: {brier:.4f}")

        print("  ✓ Stacking meta-learner trained!")

    def predict_proba(self, X):
        """Predict probabilities using weighted ensemble or stacking meta-learner."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        if isinstance(X, pd.DataFrame):
            X = X.values

        X_scaled = self.scaler.transform(X)

        if self.use_stacking:
            # Get base model predictions as meta-features
            meta_features = self._get_base_predictions(X_scaled)

            # Predict using meta-learner
            if isinstance(self.meta_learner, Ridge):
                # Ridge outputs continuous values, clip to [0, 1]
                ensemble_pred = self.meta_learner.predict(meta_features)
                ensemble_pred = np.clip(ensemble_pred, 0, 1)
            else:
                # LogisticRegression outputs probabilities
                ensemble_pred = self.meta_learner.predict_proba(meta_features)[:, 1]
        else:
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

    def get_feature_importance(self):
        """Get feature importance from tree-based models."""
        importance_dict = {}

        if "random_forest" in self.models:
            importance_dict["random_forest"] = self.models[
                "random_forest"
            ].feature_importances_

        if "xgboost" in self.models:
            importance_dict["xgboost"] = self.models["xgboost"].feature_importances_

        return importance_dict


def load_and_prepare_data(features_path: str):
    """Load features and prepare train/val/test splits."""
    print("Loading features...")
    df = pd.read_csv(features_path)
    print(f"✓ Loaded {len(df)} games")

    # Remove metadata columns
    feature_cols = [
        col
        for col in df.columns
        if col
        not in [
            "game_id",
            "game_date",
            "season",
            "home_team_id",
            "away_team_id",
            "home_win",
            "home_score",
            "away_score",
        ]
    ]

    X = df[feature_cols]
    y = df["home_win"]

    # Handle missing values
    X = X.fillna(X.mean())

    # Split by season (temporal split)
    train_mask = df["season"].isin(["2021-22", "2022-23"])
    val_mask = df["season"] == "2023-24"
    test_mask = df["season"] == "2024-25"

    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"\nData splits:")
    print(f"  Train (2021-22, 2022-23): {len(X_train)} games")
    print(f"  Val (2023-24): {len(X_val)} games")
    print(f"  Test (2024-25): {len(X_test)} games")
    print(f"  Features: {len(feature_cols)}")

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols


def evaluate_model(model, X_test, y_test, output_dir):
    """Comprehensive model evaluation."""
    print("\n" + "=" * 80)
    print("Model Evaluation on Test Set (2024-25)")
    print("=" * 80)

    # Predictions
    y_pred_proba = model.predict_proba(X_test)
    y_pred = model.predict(X_test)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    logloss = log_loss(y_test, y_pred_proba)

    print(f"\nOverall Performance:")
    print(f"  Accuracy: {accuracy:.4f} ({accuracy:.1%})")
    print(f"  AUC-ROC: {auc:.4f}")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  Log Loss: {logloss:.4f}")

    # Classification report
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Away Win", "Home Win"]))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"  True Away Wins: {cm[0, 0]}, Predicted as Home: {cm[0, 1]}")
    print(f"  True Home Wins: {cm[1, 1]}, Predicted as Away: {cm[1, 0]}")

    # Save confusion matrix plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Away Win", "Home Win"],
        yticklabels=["Away Win", "Home Win"],
    )
    plt.title("Confusion Matrix - Test Set")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(output_dir / "confusion_matrix.png", dpi=150)
    print(f"\n✓ Saved confusion matrix to {output_dir}/confusion_matrix.png")

    # Calibration curve
    from sklearn.calibration import calibration_curve

    prob_true, prob_pred = calibration_curve(y_test, y_pred_proba, n_bins=10)

    plt.figure(figsize=(8, 6))
    plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    plt.plot(prob_pred, prob_true, "bo-", label=f"Model (Brier: {brier:.4f})")
    plt.xlabel("Predicted Probability")
    plt.ylabel("True Probability")
    plt.title("Calibration Curve - Test Set")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "calibration_curve.png", dpi=150)
    print(f"✓ Saved calibration curve to {output_dir}/calibration_curve.png")

    return {"accuracy": accuracy, "auc": auc, "brier_score": brier, "log_loss": logloss}


def main():
    parser = argparse.ArgumentParser(
        description="Train ensemble model for NBA game outcome prediction"
    )
    parser.add_argument(
        "--features", default="data/game_features.csv", help="Path to features CSV file"
    )
    parser.add_argument(
        "--output", default="models/", help="Output directory for models and plots"
    )
    parser.add_argument(
        "--use-stacking",
        action="store_true",
        help="Use stacking meta-learner instead of weighted ensemble",
    )
    parser.add_argument(
        "--meta-learner",
        choices=["logistic", "ridge", "both"],
        default="both",
        help="Type of meta-learner for stacking (default: both - compare and select best)",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("NBA Game Outcome Ensemble Model Training")
    print("=" * 80)
    print(f"Features: {args.features}")
    print(f"Output: {args.output}")
    print(f"Ensemble Type: {'Stacking' if args.use_stacking else 'Weighted'}")
    if args.use_stacking:
        print(f"Meta-learner: {args.meta_learner}")
    print()

    # Load and prepare data
    X_train, y_train, X_val, y_val, X_test, y_test, feature_names = (
        load_and_prepare_data(args.features)
    )

    # Train ensemble
    ensemble = GameOutcomeEnsemble(
        use_stacking=args.use_stacking, meta_learner_type=args.meta_learner
    )
    ensemble.fit(X_train, y_train, X_val, y_val)

    # Evaluate
    metrics = evaluate_model(ensemble, X_test, y_test, output_dir)

    # Save models
    print("\nSaving models...")
    with open(output_dir / "ensemble_game_outcome_model.pkl", "wb") as f:
        pickle.dump(ensemble, f)
    print(f"✓ Saved ensemble model to {output_dir}/ensemble_game_outcome_model.pkl")

    # Save metadata
    metadata = {
        "training_date": datetime.now().isoformat(),
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "num_features": len(feature_names),
        "feature_names": feature_names,
        "ensemble_type": "stacking" if ensemble.use_stacking else "weighted",
        "model_weights": ensemble.weights,
        "test_metrics": metrics,
    }

    # Add stacking-specific metadata
    if ensemble.use_stacking:
        metadata["meta_learner_type"] = ensemble.meta_learner_type
        metadata["meta_learner_class"] = ensemble.meta_learner.__class__.__name__
        if ensemble.meta_learners:
            metadata["all_meta_learners"] = list(ensemble.meta_learners.keys())

    with open(output_dir / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to {output_dir}/model_metadata.json")

    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print(f"Test Accuracy: {metrics['accuracy']:.1%}")
    print(f"Test AUC: {metrics['auc']:.4f}")
    print(f"Brier Score: {metrics['brier_score']:.4f}")
    print()
    print("Next steps:")
    print("  1. Run: python scripts/backtest_historical_games.py")
    print("  2. This will generate predictions for calibration training")


if __name__ == "__main__":
    main()
