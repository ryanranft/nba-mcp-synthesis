#!/usr/bin/env python3
"""
Create 3 training datasets for model comparison:
1. Baseline: Remove all player features (91 features)
2. Selected: Keep only top 10 player features (111 features)
3. Full: All features (130 features)
"""

import json
import pandas as pd
from pathlib import Path

def load_feature_analysis():
    """Load feature importance analysis."""
    with open('reports/feature_importance_analysis.json') as f:
        analysis = json.load(f)
    return analysis

def create_datasets():
    """Create 3 training datasets."""
    print("="*80)
    print("Creating Training Datasets")
    print("="*80)

    # Load full feature dataset
    print("\nLoading full feature dataset...")
    df = pd.read_csv('data/game_features_with_players.csv')
    print(f"✓ Loaded {len(df)} games with {len(df.columns)} columns")

    # Load feature importance analysis
    print("\nLoading feature analysis...")
    analysis = load_feature_analysis()
    top10_player_features = analysis['top10_player_features']
    remove_player_features = analysis['remove_player_features']
    print(f"✓ Top 10 player features: {len(top10_player_features)}")
    print(f"✓ Bottom 19 player features: {len(remove_player_features)}")

    # Identify metadata columns
    metadata_cols = [
        'game_id', 'game_date', 'season', 'home_team_id', 'away_team_id',
        'home_win', 'home_score', 'away_score'
    ]

    # Get all player features
    all_player_features = [col for col in df.columns if col.startswith('player__')]
    print(f"\nTotal player features in dataset: {len(all_player_features)}")

    # Get non-player feature columns
    non_player_features = [
        col for col in df.columns
        if col not in metadata_cols and not col.startswith('player__')
    ]
    print(f"Non-player features: {len(non_player_features)}")

    # Dataset 1: Baseline (no player features)
    print("\n" + "="*80)
    print("Dataset 1: Baseline (No Player Features)")
    print("="*80)
    baseline_cols = metadata_cols + non_player_features
    df_baseline = df[baseline_cols].copy()
    print(f"Features: {len(baseline_cols) - len(metadata_cols)} ({len(baseline_cols)} total with metadata)")
    print(f"Columns: {baseline_cols[:5]}... (showing first 5)")

    output_path = Path('data/baseline_features.csv')
    df_baseline.to_csv(output_path, index=False)
    print(f"✓ Saved to {output_path}")

    # Dataset 2: Selected (top 10 player features)
    print("\n" + "="*80)
    print("Dataset 2: Selected Features (Top 10 Player Features)")
    print("="*80)

    # Verify top 10 features exist in dataset
    missing_features = [f for f in top10_player_features if f not in df.columns]
    if missing_features:
        print(f"⚠️  Warning: {len(missing_features)} top features not in dataset:")
        print(f"   {missing_features}")

    available_top10 = [f for f in top10_player_features if f in df.columns]
    print(f"Top 10 features available: {len(available_top10)}")

    selected_cols = metadata_cols + non_player_features + available_top10
    df_selected = df[selected_cols].copy()
    print(f"Features: {len(selected_cols) - len(metadata_cols)} ({len(selected_cols)} total with metadata)")
    print(f"\nTop 10 player features:")
    for i, feat in enumerate(available_top10, 1):
        print(f"  {i:2d}. {feat}")

    output_path = Path('data/selected_features.csv')
    df_selected.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")

    # Dataset 3: Full (all features)
    print("\n" + "="*80)
    print("Dataset 3: Full Features (All Features)")
    print("="*80)
    output_path = Path('data/full_features.csv')
    df.to_csv(output_path, index=False)
    print(f"Features: {len(df.columns) - len(metadata_cols)} ({len(df.columns)} total with metadata)")
    print(f"✓ Saved to {output_path}")

    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"Baseline:  {len(baseline_cols) - len(metadata_cols)} features → data/baseline_features.csv")
    print(f"Selected:  {len(selected_cols) - len(metadata_cols)} features → data/selected_features.csv")
    print(f"Full:      {len(df.columns) - len(metadata_cols)} features → data/full_features.csv")
    print(f"\nAll datasets contain {len(df)} games")
    print(f"Metadata columns (8): {', '.join(metadata_cols)}")

    # Verify file sizes
    print("\n" + "="*80)
    print("File Sizes")
    print("="*80)
    for name, path in [
        ('Baseline', 'data/baseline_features.csv'),
        ('Selected', 'data/selected_features.csv'),
        ('Full', 'data/full_features.csv')
    ]:
        size_mb = Path(path).stat().st_size / (1024 * 1024)
        print(f"{name:10s} {size_mb:6.2f} MB  ({path})")

    print("\n✓ All datasets created successfully!")
    print("\nNext step: Train 3 model configurations (Phase 3)")

if __name__ == '__main__':
    create_datasets()
