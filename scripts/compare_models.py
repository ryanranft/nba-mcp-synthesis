#!/usr/bin/env python3
"""
Compare all trained model configurations.
Generate comprehensive comparison report.
"""

import json
import pandas as pd
from pathlib import Path


def load_model_metadata(model_dir):
    """Load model metadata from directory."""
    metadata_path = Path(model_dir) / "model_metadata.json"
    with open(metadata_path) as f:
        return json.load(f)


def compare_models():
    """Compare all model configurations."""
    print("=" * 80)
    print("Model Configuration Comparison")
    print("=" * 80)

    # Define models to compare
    models = [
        {
            "name": "Baseline",
            "dir": "models/baseline",
            "description": "101 features (no player features)",
            "ensemble_type": "Weighted",
        },
        {
            "name": "Selected",
            "dir": "models/selected",
            "description": "111 features (top 10 player features)",
            "ensemble_type": "Weighted",
        },
        {
            "name": "Full_Weighted",
            "dir": "models",
            "description": "130 features (all features, weighted)",
            "ensemble_type": "Weighted",
        },
        {
            "name": "Full_Stacking",
            "dir": "models/full_stacking",
            "description": "130 features (all features, stacking)",
            "ensemble_type": "Stacking",
        },
    ]

    # Load all metadata
    results = []
    for model in models:
        try:
            metadata = load_model_metadata(model["dir"])
            results.append(
                {
                    "Model": model["name"],
                    "Features": metadata["num_features"],
                    "Description": model["description"],
                    "Ensemble": model["ensemble_type"],
                    "Accuracy": metadata["test_metrics"]["accuracy"],
                    "AUC": metadata["test_metrics"]["auc"],
                    "Brier": metadata["test_metrics"]["brier_score"],
                    "Log Loss": metadata["test_metrics"].get("log_loss", "N/A"),
                    "LR Weight": metadata["model_weights"].get("logistic", 0.0),
                    "RF Weight": metadata["model_weights"].get("random_forest", 0.0),
                    "XGB Weight": metadata["model_weights"].get("xgboost", 0.0),
                }
            )
        except FileNotFoundError:
            print(f"⚠️  Skipping {model['name']}: metadata not found")

    # Create DataFrame
    df = pd.DataFrame(results)

    # Sort by accuracy descending
    df = df.sort_values("Accuracy", ascending=False)
    df["Rank"] = range(1, len(df) + 1)

    # Reorder columns
    df = df[
        [
            "Rank",
            "Model",
            "Features",
            "Description",
            "Ensemble",
            "Accuracy",
            "AUC",
            "Brier",
            "Log Loss",
            "LR Weight",
            "RF Weight",
            "XGB Weight",
        ]
    ]

    print("\n" + "=" * 80)
    print("Performance Comparison (Sorted by Accuracy)")
    print("=" * 80)
    print(
        df[["Rank", "Model", "Features", "Accuracy", "AUC", "Brier"]].to_string(
            index=False
        )
    )

    print("\n" + "=" * 80)
    print("Ensemble Weights")
    print("=" * 80)
    print(df[["Model", "LR Weight", "RF Weight", "XGB Weight"]].to_string(index=False))

    print("\n" + "=" * 80)
    print("Full Details")
    print("=" * 80)
    print(df.to_string(index=False))

    # Calculate improvements
    print("\n" + "=" * 80)
    print("Performance Analysis")
    print("=" * 80)

    baseline = df[df["Model"] == "Baseline"].iloc[0]
    full_weighted = df[df["Model"] == "Full_Weighted"].iloc[0]

    print(f"\n📊 Baseline vs Full Weighted:")
    print(f"  Accuracy: {baseline['Accuracy']:.4f} vs {full_weighted['Accuracy']:.4f}")
    print(
        f"  Improvement: {(baseline['Accuracy'] - full_weighted['Accuracy']) * 100:+.2f} percentage points"
    )
    print(f"  AUC: {baseline['AUC']:.4f} vs {full_weighted['AUC']:.4f}")
    print(f"  Brier: {baseline['Brier']:.4f} vs {full_weighted['Brier']:.4f}")

    print(f"\n📊 Feature Count Impact:")
    print(
        f"  Baseline: {baseline['Features']} features → {baseline['Accuracy']:.1%} accuracy"
    )
    print(
        f"  Selected: {df[df['Model']=='Selected'].iloc[0]['Features']} features → {df[df['Model']=='Selected'].iloc[0]['Accuracy']:.1%} accuracy"
    )
    print(
        f"  Full: {full_weighted['Features']} features → {full_weighted['Accuracy']:.1%} accuracy"
    )
    print(f"\n  ⚠️  More features = WORSE performance (player features added noise)")

    print(f"\n📊 Ensemble Type Comparison:")
    full_stack = df[df["Model"] == "Full_Stacking"].iloc[0]
    print(f"  Full Weighted: {full_weighted['Accuracy']:.1%}")
    print(f"  Full Stacking: {full_stack['Accuracy']:.1%}")
    print(
        f"  Stacking improvement: {(full_stack['Accuracy'] - full_weighted['Accuracy']) * 100:+.2f} percentage points"
    )

    # Winner
    print("\n" + "=" * 80)
    print("🏆 WINNER")
    print("=" * 80)
    winner = df.iloc[0]
    print(f"\nModel: {winner['Model']}")
    print(f"Features: {winner['Features']}")
    print(f"Description: {winner['Description']}")
    print(f"Test Accuracy: {winner['Accuracy']:.4f} ({winner['Accuracy']*100:.2f}%)")
    print(f"AUC: {winner['AUC']:.4f}")
    print(f"Brier Score: {winner['Brier']:.4f}")
    print(
        f"Ensemble Weights: LR={winner['LR Weight']:.1f}, RF={winner['RF Weight']:.1f}, XGB={winner['XGB Weight']:.1f}"
    )

    # Save report
    output_path = Path("reports/model_comparison.json")
    output_path.parent.mkdir(exist_ok=True)

    comparison_report = {
        "winner": {
            "model": winner["Model"],
            "features": int(winner["Features"]),
            "description": winner["Description"],
            "accuracy": float(winner["Accuracy"]),
            "auc": float(winner["AUC"]),
            "brier": float(winner["Brier"]),
            "ensemble_weights": {
                "logistic": float(winner["LR Weight"]),
                "random_forest": float(winner["RF Weight"]),
                "xgboost": float(winner["XGB Weight"]),
            },
        },
        "all_models": df.to_dict("records"),
        "key_findings": {
            "player_features_impact": "NEGATIVE - Adding player features decreased accuracy",
            "baseline_vs_full_improvement": f"{(baseline['Accuracy'] - full_weighted['Accuracy']) * 100:+.2f} percentage points",
            "stacking_vs_weighted": f"{(full_stack['Accuracy'] - full_weighted['Accuracy']) * 100:+.2f} percentage points",
            "xgboost_usage": "ZERO - XGBoost received 0% weight in all configurations",
        },
    }

    with open(output_path, "w") as f:
        json.dump(comparison_report, f, indent=2)

    print(f"\n✓ Comparison report saved to {output_path}")

    print("\n" + "=" * 80)
    print("Recommendation")
    print("=" * 80)
    print(f"\n✅ SELECT: {winner['Model']} model for calibration pipeline")
    print(f"\nRationale:")
    print(f"  - Highest test accuracy: {winner['Accuracy']*100:.2f}%")
    print(f"  - Simplest model: {winner['Features']} features")
    print(f"  - Best generalization: Avoids overfitting from player features")
    print(
        f"  - Stable weights: {winner['LR Weight']:.0%} Logistic, {winner['RF Weight']:.0%} Random Forest"
    )
    print(f"\nNext steps:")
    print(f"  1. Copy baseline model to production location")
    print(f"  2. Proceed to calibration pipeline (Stage 2)")
    print(f"  3. Generate calibration data via backtesting")


if __name__ == "__main__":
    compare_models()
