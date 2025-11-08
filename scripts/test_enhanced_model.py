#!/usr/bin/env python3
"""
Quick validation test for enhanced stacking model

Tests that the new stacking ensemble works end-to-end with enhanced features.
"""

import sys
from pathlib import Path
import pickle
import psycopg2

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import GameOutcomeEnsemble from training script
from train_game_outcome_model import GameOutcomeEnsemble

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
from mcp_server.betting.feature_extractor import FeatureExtractor

def main():
    print("=" * 80)
    print("Enhanced Stacking Model - End-to-End Validation Test")
    print("=" * 80)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
    print("✓ Secrets loaded\n")

    # Connect to database
    print("🔌 Connecting to database...")
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config)
    print("✓ Database connected\n")

    # Initialize feature extractor
    print("🔧 Initializing enhanced feature extractor...")
    extractor = FeatureExtractor(conn)
    print("✓ Feature extractor initialized (with RestFatigueExtractor)\n")

    # Load stacking model
    print("📊 Loading stacking ensemble model...")
    with open('models/ensemble_game_outcome_model.pkl', 'rb') as f:
        model = pickle.load(f)

    print(f"✓ Model loaded:")
    print(f"  - Type: {'Stacking' if model.use_stacking else 'Weighted'}")
    if model.use_stacking:
        print(f"  - Meta-learner: {model.meta_learner.__class__.__name__}")
    print()

    # Get a recent game for testing
    print("🏀 Fetching recent game for testing...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            game_id,
            game_date,
            home_team_id,
            away_team_id,
            home_score,
            away_score
        FROM games
        WHERE home_score IS NOT NULL
          AND away_score IS NOT NULL
          AND game_date IS NOT NULL
        ORDER BY game_date DESC
        LIMIT 1
    """)
    game = cursor.fetchone()

    if not game:
        print("❌ No recent games found")
        return

    game_id, game_date, home_id, away_id, home_score, away_score = game
    home_won = home_score > away_score

    print(f"✓ Testing on game from {game_date}")
    print(f"  Home Team ID: {home_id} (Score: {home_score})")
    print(f"  Away Team ID: {away_id} (Score: {away_score})")
    print(f"  Actual Result: {'Home Win' if home_won else 'Away Win'}\n")

    # Extract features
    print("⚙️  Extracting enhanced features...")
    features = extractor.extract_game_features(
        home_team_id=home_id,
        away_team_id=away_id,
        game_date=str(game_date)
    )

    print(f"✓ Extracted {len(features)} features")
    print(f"  - rest__ features: {sum(1 for k in features.keys() if k.startswith('rest__'))}")
    print(f"  - base__ features: {sum(1 for k in features.keys() if k.startswith('base__'))}")
    print()

    # Make prediction
    print("🎯 Making prediction...")
    import pandas as pd
    import numpy as np

    # Convert to DataFrame
    features_df = pd.DataFrame([features])

    # Remove metadata columns
    feature_cols = [col for col in features_df.columns if col not in [
        'game_id', 'game_date', 'season', 'home_team_id', 'away_team_id'
    ]]

    X = features_df[feature_cols].fillna(0).values

    # Predict
    home_win_prob = model.predict_proba(X)[0]

    print(f"✓ Prediction complete!")
    print(f"  Home Win Probability: {home_win_prob:.1%}")
    print(f"  Away Win Probability: {(1-home_win_prob):.1%}")
    print(f"  Prediction: {'Home Win' if home_win_prob > 0.5 else 'Away Win'}")
    print(f"  Actual: {'Home Win' if home_won else 'Away Win'}")
    print(f"  Correct: {'✅ YES' if (home_win_prob > 0.5) == home_won else '❌ NO'}")
    print()

    # Feature breakdown
    print("📊 Enhanced Features Sample:")
    rest_features = {k: v for k, v in features.items() if k.startswith('rest__')}
    for key, value in list(rest_features.items())[:5]:
        print(f"  {key}: {value}")

    if len(rest_features) > 5:
        print(f"  ... and {len(rest_features) - 5} more rest/fatigue features")

    print()
    print("=" * 80)
    print("✅ End-to-End Validation PASSED!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Enhanced feature extraction: ✓")
    print(f"  - RestFatigueExtractor integration: ✓")
    print(f"  - Stacking ensemble prediction: ✓")
    print(f"  - Feature count: {len(feature_cols)}")
    print(f"  - Model type: {model.meta_learner.__class__.__name__} stacking")
    print()

    conn.close()


if __name__ == '__main__':
    main()
