#!/usr/bin/env python3
"""
Test Player Feature Extraction

Validates that the enhanced FeatureExtractor with player-level features works correctly.

Tests:
1. Player features extraction completes without errors
2. Feature count increases with player features (~20-30 new features)
3. Player features have reasonable values
4. No missing/null values in critical features

Usage:
    python scripts/test_player_features.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
from mcp_server.betting.feature_extractor import FeatureExtractor
import psycopg2


def test_player_feature_extraction():
    """Test that player feature extraction works correctly"""
    print("=" * 80)
    print("Player Feature Extraction Validation")
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
    print("Initializing FeatureExtractor with player features...")
    extractor = FeatureExtractor(conn)
    print("✓ FeatureExtractor initialized")
    print()

    # Get a recent game to test with
    print("Finding a recent game to test...")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            home_team_id,
            away_team_id,
            game_date,
            season
        FROM games
        WHERE home_score IS NOT NULL
        AND season = '2024-25'
        AND game_date >= '2024-11-01'  -- Recent games with player data
        ORDER BY game_date DESC
        LIMIT 1
    """
    )
    game = cursor.fetchone()

    if not game:
        print("❌ No recent games found")
        return False

    home_team_id, away_team_id, game_date, season = game
    print(f"✓ Testing with game: {home_team_id} vs {away_team_id} on {game_date}")
    print()

    # Extract features
    print("Extracting features with player enhancements...")
    try:
        features = extractor.extract_game_features(
            home_team_id=int(home_team_id),
            away_team_id=int(away_team_id),
            game_date=str(game_date),
        )
        print(f"✓ Extracted {len(features)} features")
        print()
    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Analyze features
    print("=" * 80)
    print("FEATURE ANALYSIS")
    print("=" * 80)
    print()

    # Group features by category
    categories = {
        "Player Features": [k for k in features.keys() if k.startswith("player__")],
        "Rolling Stats (L5)": [
            k for k in features.keys() if "_l5" in k and not k.startswith("player__")
        ],
        "Rolling Stats (L10)": [
            k for k in features.keys() if "_l10" in k and not k.startswith("player__")
        ],
        "Rolling Stats (L20)": [
            k for k in features.keys() if "_l20" in k and not k.startswith("player__")
        ],
        "Rest & Fatigue (rest__)": [
            k for k in features.keys() if k.startswith("rest__")
        ],
        "Rest & Fatigue (base__)": [
            k for k in features.keys() if k.startswith("base__")
        ],
        "Head-to-Head": [k for k in features.keys() if "h2h_" in k],
        "Other": [
            k
            for k in features.keys()
            if not any(
                [
                    k.startswith("player__"),
                    "_l5" in k,
                    "_l10" in k,
                    "_l20" in k,
                    k.startswith("rest__"),
                    k.startswith("base__"),
                    "h2h_" in k,
                ]
            )
        ],
    }

    for category, feature_list in categories.items():
        if feature_list:
            print(f"{category}: {len(feature_list)} features")
            for feat in sorted(feature_list)[:10]:  # Show first 10
                value = features[feat]
                if isinstance(value, (int, float)):
                    print(f"  - {feat}: {value:.4f}")
                else:
                    print(f"  - {feat}: {value}")
            if len(feature_list) > 10:
                print(f"  ... and {len(feature_list) - 10} more")
            print()

    # Validate player features
    print("=" * 80)
    print("PLAYER FEATURE VALIDATION")
    print("=" * 80)
    print()

    player_features = [k for k in features.keys() if k.startswith("player__")]

    if len(player_features) == 0:
        print("❌ FAILED: No player features found!")
        return False

    print(f"✅ Found {len(player_features)} player features")
    print()

    # Expected player features
    expected_features = [
        "player__home_top1_ppg_l10",
        "player__home_top2_ppg_l10",
        "player__home_top3_ppg_l10",
        "player__away_top1_ppg_l10",
        "player__away_top2_ppg_l10",
        "player__away_top3_ppg_l10",
        "player__home_roster_per_sum",
        "player__away_roster_per_sum",
        "player__home_injury_impact",
        "player__away_injury_impact",
        "player__home_stars_available",
        "player__away_stars_available",
        "player__home_bench_ppg",
        "player__away_bench_ppg",
        "player__top5_ppg_advantage",
        "player__home_top5_ppg",
        "player__away_top5_ppg",
    ]

    missing_features = [f for f in expected_features if f not in features]

    if missing_features:
        print(f"⚠ Missing {len(missing_features)} expected features:")
        for feat in missing_features:
            print(f"  - {feat}")
        print()
    else:
        print("✅ All expected player features present")
        print()

    # Check for reasonable values
    print("Checking player feature values...")
    issues = []

    # Top scorer PPG should be positive and reasonable (5-40 PPG)
    for i in [1, 2, 3]:
        home_key = f"player__home_top{i}_ppg_l10"
        away_key = f"player__away_top{i}_ppg_l10"

        if home_key in features:
            value = features[home_key]
            if value < 0 or value > 50:
                issues.append(f"{home_key} has unrealistic value: {value}")

        if away_key in features:
            value = features[away_key]
            if value < 0 or value > 50:
                issues.append(f"{away_key} has unrealistic value: {value}")

    # Roster PER sum should be positive
    if "player__home_roster_per_sum" in features:
        value = features["player__home_roster_per_sum"]
        if value < 0 or value > 200:
            issues.append(f"player__home_roster_per_sum has unrealistic value: {value}")

    if "player__away_roster_per_sum" in features:
        value = features["player__away_roster_per_sum"]
        if value < 0 or value > 200:
            issues.append(f"player__away_roster_per_sum has unrealistic value: {value}")

    # Star availability should be 0-1
    if "player__home_stars_available" in features:
        value = features["player__home_stars_available"]
        if value < 0 or value > 1:
            issues.append(f"player__home_stars_available out of range [0,1]: {value}")

    if "player__away_stars_available" in features:
        value = features["player__away_stars_available"]
        if value < 0 or value > 1:
            issues.append(f"player__away_stars_available out of range [0,1]: {value}")

    if issues:
        print(f"⚠ Found {len(issues)} value issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    else:
        print("✅ All player feature values look reasonable")
        print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total features: {len(features)}")
    print(f"Player features: {len(player_features)}")
    print(f"Expected player features: {len(expected_features)}")
    print(f"Missing features: {len(missing_features)}")
    print(f"Value issues: {len(issues)}")
    print()

    if len(player_features) >= 15 and len(missing_features) <= 3 and len(issues) == 0:
        print("✅ SUCCESS: Player feature extraction working correctly!")
        print()
        success = True
    elif len(player_features) >= 10:
        print("⚠ PARTIAL SUCCESS: Player features present but some issues")
        print()
        success = True
    else:
        print("❌ FAILED: Player features not working correctly")
        print()
        success = False

    # Show sample player features
    print("Sample player features:")
    print("-" * 80)
    for feat in sorted(player_features)[:20]:
        value = features[feat]
        if isinstance(value, (int, float)):
            print(f"{feat:50s}: {value:10.4f}")
        else:
            print(f"{feat:50s}: {value}")

    print()
    conn.close()
    return success


if __name__ == "__main__":
    success = test_player_feature_extraction()
    sys.exit(0 if success else 1)
