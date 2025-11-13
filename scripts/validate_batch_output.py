#!/usr/bin/env python3
"""
Validate Batch Feature Generation Output

Checks that the batch-generated features are correct and ready for model training.

Usage:
    python scripts/validate_batch_output.py
    python scripts/validate_batch_output.py --file data/game_features_with_players.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np


def validate_batch_output(file_path: str) -> bool:
    """
    Validate batch feature output file

    Returns:
        True if validation passes, False otherwise
    """
    print("=" * 80)
    print("Batch Feature Output Validation")
    print("=" * 80)
    print()

    # Check file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    print(f"✅ File exists: {file_path}")
    print()

    # Load data
    print("Loading CSV...")
    try:
        df = pd.read_csv(file_path)
        print(f"✅ Successfully loaded {len(df)} rows")
        print()
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False

    # Validate basic structure
    print("Validating structure...")
    print("-" * 80)

    # Expected metadata columns
    expected_metadata = [
        "game_id",
        "game_date",
        "season",
        "home_team_id",
        "away_team_id",
        "home_win",
        "home_score",
        "away_score",
    ]

    missing_metadata = [col for col in expected_metadata if col not in df.columns]
    if missing_metadata:
        print(f"❌ Missing metadata columns: {missing_metadata}")
        return False

    print(f"✅ All metadata columns present ({len(expected_metadata)} columns)")

    # Check for player features
    player_features = [col for col in df.columns if col.startswith("player__")]

    if len(player_features) == 0:
        print("❌ No player features found!")
        return False

    print(f"✅ Found {len(player_features)} player features")

    # Expected player features
    expected_player_prefixes = [
        "player__home_top1_ppg",
        "player__home_top2_ppg",
        "player__home_top3_ppg",
        "player__away_top1_ppg",
        "player__away_top2_ppg",
        "player__away_top3_ppg",
        "player__home_roster_per",
        "player__away_roster_per",
        "player__home_bench_ppg",
        "player__away_bench_ppg",
        "player__top5_ppg_advantage",
    ]

    missing_player = []
    for prefix in expected_player_prefixes:
        if not any(col.startswith(prefix) for col in player_features):
            missing_player.append(prefix)

    if missing_player:
        print(f"⚠️  Missing expected player features: {missing_player}")
    else:
        print(f"✅ All expected player feature types present")

    print()

    # Validate feature counts
    print("Feature Counts:")
    print("-" * 80)

    total_features = len(df.columns) - len(expected_metadata)
    print(f"  Total columns: {len(df.columns)}")
    print(f"  Metadata columns: {len(expected_metadata)}")
    print(f"  Feature columns: {total_features}")
    print(f"  Player features: {len(player_features)}")
    print(f"  Team features: {total_features - len(player_features)}")

    if total_features < 120:
        print(f"⚠️  Expected ~130 features, got {total_features}")
    else:
        print(f"✅ Feature count looks good ({total_features} features)")

    print()

    # Check for missing values
    print("Data Quality Checks:")
    print("-" * 80)

    # Check critical features for missing values
    critical_features = ["home_win", "home_score", "away_score"]

    for col in critical_features:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(
                f"⚠️  {col} has {null_count} missing values ({null_count/len(df)*100:.1f}%)"
            )
        else:
            print(f"✅ {col} has no missing values")

    # Check player features for excessive nulls
    player_null_pct = {}
    for col in player_features[:10]:  # Check first 10 player features
        null_pct = df[col].isnull().sum() / len(df) * 100
        if null_pct > 50:
            player_null_pct[col] = null_pct

    if player_null_pct:
        print(f"⚠️  Some player features have >50% null values:")
        for col, pct in player_null_pct.items():
            print(f"     {col}: {pct:.1f}% null")
    else:
        print(f"✅ Player features have <50% null values (acceptable)")

    print()

    # Validate value ranges
    print("Value Range Validation:")
    print("-" * 80)

    # PPG features should be 5-50 range
    ppg_features = [col for col in player_features if "_ppg" in col and "_top" in col]

    issues = []
    for col in ppg_features[:6]:  # Check first 6 PPG features
        values = df[col].dropna()
        if len(values) > 0:
            min_val = values.min()
            max_val = values.max()
            mean_val = values.mean()

            if min_val < 0 or max_val > 60:
                issues.append(f"{col}: range [{min_val:.1f}, {max_val:.1f}]")
            else:
                print(
                    f"✅ {col}: mean={mean_val:.1f}, range=[{min_val:.1f}, {max_val:.1f}]"
                )

    if issues:
        print("\n⚠️  PPG features with unusual ranges:")
        for issue in issues:
            print(f"     {issue}")

    print()

    # Season distribution
    print("Season Distribution:")
    print("-" * 80)
    season_counts = df["season"].value_counts().sort_index()
    for season, count in season_counts.items():
        print(f"  {season}: {count} games")

    print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    validation_passed = (
        len(df) > 0
        and len(player_features) >= 20
        and total_features >= 120
        and len(missing_metadata) == 0
    )

    if validation_passed:
        print("✅ VALIDATION PASSED")
        print()
        print(f"Dataset ready for training:")
        print(f"  - {len(df)} games")
        print(
            f"  - {total_features} features (including {len(player_features)} player features)"
        )
        print(f"  - {len(season_counts)} seasons")
        print()
        print("Next step:")
        print("  python scripts/train_game_outcome_model.py \\")
        print(f"      --input {file_path} \\")
        print("      --output models/ensemble_with_players.pkl \\")
        print("      --test-season 2024-25")
        return True
    else:
        print("❌ VALIDATION FAILED")
        print()
        print("Issues detected:")
        if len(df) == 0:
            print("  - Empty dataset")
        if len(player_features) < 20:
            print(f"  - Insufficient player features ({len(player_features)} < 20)")
        if total_features < 120:
            print(f"  - Insufficient total features ({total_features} < 120)")
        if len(missing_metadata) > 0:
            print(f"  - Missing metadata columns: {missing_metadata}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate batch feature generation output"
    )
    parser.add_argument(
        "--file",
        default="data/game_features_with_players.csv",
        help="Path to batch output CSV file",
    )

    args = parser.parse_args()

    success = validate_batch_output(args.file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
