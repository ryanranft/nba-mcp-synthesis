#!/usr/bin/env python3
"""
Test Enhanced Feature Extraction

Validates that the FeatureExtractor now produces 83 features matching
the batch feature preparation format.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
from mcp_server.betting.feature_extractor import FeatureExtractor
import psycopg2


def test_feature_extraction():
    """Test that feature extraction produces 83 features"""
    print("=" * 80)
    print("Enhanced Feature Extraction Validation")
    print("=" * 80)
    print()

    # Load database credentials
    print("Loading secrets...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    db_config = get_database_config()
    print("✓ Secrets loaded")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**db_config)
    print("✓ Connected")
    print()

    # Initialize feature extractor
    print("Initializing FeatureExtractor...")
    extractor = FeatureExtractor(conn)
    print("✓ FeatureExtractor initialized")
    print()

    # Get a recent game to test with
    print("Finding a recent game to test...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            home_team_id,
            away_team_id,
            game_date,
            season
        FROM games
        WHERE home_score IS NOT NULL
        AND season = '2024-25'
        ORDER BY game_date DESC
        LIMIT 1
    """)
    game = cursor.fetchone()

    if not game:
        print("❌ No recent games found")
        return False

    home_team_id, away_team_id, game_date, season = game
    print(f"✓ Testing with game: {home_team_id} vs {away_team_id} on {game_date}")
    print()

    # Extract features
    print("Extracting features...")
    features = extractor.extract_game_features(
        home_team_id=int(home_team_id),
        away_team_id=int(away_team_id),
        game_date=str(game_date)
    )
    print(f"✓ Extracted {len(features)} features")
    print()

    # Analyze features
    print("=" * 80)
    print("FEATURE ANALYSIS")
    print("=" * 80)
    print()

    # Group features by category
    categories = {
        'Rolling Stats (L5)': [k for k in features.keys() if '_l5' in k],
        'Rolling Stats (L10)': [k for k in features.keys() if '_l10' in k],
        'Rolling Stats (L20)': [k for k in features.keys() if '_l20' in k],
        'Location-Specific': [k for k in features.keys() if ('ppg_home' in k or 'ppg_away' in k or '_games' in k) and '_l' not in k],
        'Recent Form': [k for k in features.keys() if 'form_l5' in k],
        'Season Progress': [k for k in features.keys() if 'season_progress' in k],
        'Head-to-Head': [k for k in features.keys() if 'h2h_' in k],
        'Rest & Fatigue (rest__)': [k for k in features.keys() if k.startswith('rest__')],
        'Rest & Fatigue (base__)': [k for k in features.keys() if k.startswith('base__')],
        'Games Played': [k for k in features.keys() if 'games_played' in k]
    }

    for category, feature_list in categories.items():
        if feature_list:
            print(f"{category}: {len(feature_list)} features")
            for feat in sorted(feature_list)[:5]:  # Show first 5
                value = features[feat]
                print(f"  - {feat}: {value:.4f}" if isinstance(value, (int, float)) else f"  - {feat}: {value}")
            if len(feature_list) > 5:
                print(f"  ... and {len(feature_list) - 5} more")
            print()

    # Expected features (from batch script)
    expected_feature_count = 83
    actual_feature_count = len(features)

    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    print(f"Expected features: {expected_feature_count}")
    print(f"Actual features:   {actual_feature_count}")
    print()

    if actual_feature_count >= expected_feature_count:
        print("✅ SUCCESS: Feature extraction produces expected number of features!")
        print()
        success = True
    else:
        print(f"❌ FAILED: Missing {expected_feature_count - actual_feature_count} features")
        print()
        success = False

    # Show all feature names for debugging
    print("All feature names:")
    print("-" * 80)
    for i, feat in enumerate(sorted(features.keys()), 1):
        print(f"{i:3d}. {feat}")

    print()
    conn.close()
    return success


if __name__ == '__main__':
    success = test_feature_extraction()
    sys.exit(0 if success else 1)
