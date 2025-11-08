#!/usr/bin/env python3
"""
Analyze feature importance from trained ensemble model.
Extract top player features for selective feature engineering.
"""

import sys
import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add scripts directory to path to import GameOutcomeEnsemble
sys.path.insert(0, str(Path(__file__).parent))
from train_game_outcome_model import GameOutcomeEnsemble

def load_model(model_path):
    """Load trained ensemble model."""
    with open(model_path, 'rb') as f:
        ensemble = pickle.load(f)
    return ensemble

def get_feature_importance(ensemble, feature_names):
    """Extract feature importance from ensemble models."""

    # Random Forest importance
    rf_importance = ensemble.models['random_forest'].feature_importances_

    # XGBoost importance (if available)
    if 'xgboost' in ensemble.models:
        xgb_importance = ensemble.models['xgboost'].feature_importances_
    else:
        xgb_importance = np.zeros(len(feature_names))

    # Logistic Regression - use coefficient magnitudes
    lr_importance = np.abs(ensemble.models['logistic'].coef_[0])

    # Create DataFrame
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'rf_importance': rf_importance,
        'xgb_importance': xgb_importance,
        'lr_importance': lr_importance
    })

    # Calculate average importance (weighted by ensemble weights)
    # Get actual weights from the trained model
    w_lr = ensemble.weights.get('logistic', 0.0)
    w_rf = ensemble.weights.get('random_forest', 0.0)
    w_xgb = ensemble.weights.get('xgboost', 0.0)

    print(f"\nEnsemble weights used:")
    print(f"  Logistic: {w_lr:.3f}")
    print(f"  Random Forest: {w_rf:.3f}")
    print(f"  XGBoost: {w_xgb:.3f}")

    importance_df['weighted_avg'] = (
        w_lr * importance_df['lr_importance'] +
        w_rf * importance_df['rf_importance'] +
        w_xgb * importance_df['xgb_importance']
    )

    # Sort by weighted average
    importance_df = importance_df.sort_values('weighted_avg', ascending=False)

    return importance_df

def identify_player_features(importance_df):
    """Identify player-related features."""
    player_keywords = [
        'top1', 'top2', 'top3', 'top5',
        'roster_per', 'injury', 'stars', 'bench',
        'ppg_advantage'
    ]

    is_player_feature = importance_df['feature'].apply(
        lambda x: any(keyword in x.lower() for keyword in player_keywords)
    )

    player_features = importance_df[is_player_feature].copy()
    return player_features

def main():
    # Paths
    model_path = Path('models/ensemble_game_outcome_model.pkl')
    metadata_path = Path('models/model_metadata.json')
    output_path = Path('reports/feature_importance_analysis.json')

    print("="*80)
    print("Feature Importance Analysis")
    print("="*80)

    # Load model
    print("\nLoading ensemble model...")
    ensemble = load_model(model_path)
    print("✓ Model loaded")

    # Get feature names from ensemble
    print("\nLoading feature names...")
    feature_names = ensemble.feature_names
    print(f"✓ Loaded {len(feature_names)} features")

    # Get importance
    print("\nCalculating feature importance...")
    importance_df = get_feature_importance(ensemble, feature_names)
    print("✓ Importance calculated")

    # Identify player features
    print("\nIdentifying player features...")
    player_features = identify_player_features(importance_df)
    print(f"✓ Found {len(player_features)} player features")

    # Display top 20 overall features
    print("\n" + "="*80)
    print("Top 20 Features (Overall)")
    print("="*80)
    print(importance_df[['feature', 'weighted_avg', 'rf_importance', 'xgb_importance']].head(20).to_string(index=False))

    # Display all player features sorted by importance
    print("\n" + "="*80)
    print(f"Player Features (All {len(player_features)})")
    print("="*80)
    print(player_features[['feature', 'weighted_avg', 'rf_importance', 'xgb_importance']].to_string(index=False))

    # Top 10 player features
    top10_player = player_features.head(10)
    print("\n" + "="*80)
    print("Top 10 Player Features (Selected for Retention)")
    print("="*80)
    print(top10_player[['feature', 'weighted_avg']].to_string(index=False))

    # Bottom 19 player features (to remove)
    bottom_player = player_features.tail(len(player_features) - 10)
    print("\n" + "="*80)
    print(f"Bottom {len(bottom_player)} Player Features (To Remove)")
    print("="*80)
    print(bottom_player[['feature', 'weighted_avg']].to_string(index=False))

    # Save analysis
    analysis_results = {
        'total_features': len(feature_names),
        'player_features_total': len(player_features),
        'top10_player_features': top10_player['feature'].tolist(),
        'remove_player_features': bottom_player['feature'].tolist(),
        'top_20_overall': importance_df.head(20)['feature'].tolist(),
        'feature_importance_stats': {
            'player_features_avg_importance': float(player_features['weighted_avg'].mean()),
            'non_player_features_avg_importance': float(importance_df[~importance_df['feature'].isin(player_features['feature'])]['weighted_avg'].mean()),
            'top10_player_avg_importance': float(top10_player['weighted_avg'].mean()),
            'bottom_player_avg_importance': float(bottom_player['weighted_avg'].mean())
        }
    }

    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    print(f"\n✓ Analysis saved to {output_path}")

    # Summary statistics
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)
    print(f"Total features: {len(feature_names)}")
    print(f"Player features: {len(player_features)}")
    print(f"Top 10 player features avg importance: {analysis_results['feature_importance_stats']['top10_player_avg_importance']:.6f}")
    print(f"Bottom {len(bottom_player)} player features avg importance: {analysis_results['feature_importance_stats']['bottom_player_avg_importance']:.6f}")
    print(f"Non-player features avg importance: {analysis_results['feature_importance_stats']['non_player_features_avg_importance']:.6f}")
    print(f"\nRecommendation: Remove {len(bottom_player)} low-importance player features")
    print(f"New feature count: {len(feature_names)} - {len(bottom_player)} = {len(feature_names) - len(bottom_player)}")

if __name__ == '__main__':
    main()
