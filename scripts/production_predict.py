#!/usr/bin/env python3
"""
Production NBA Game Prediction & Betting Decision System

Uses trained ensemble model + calibrated Kelly engine to make betting decisions
on live NBA games.

Usage:
    # Predict single game
    python scripts/production_predict.py --home LAL --away GSW --odds 1.9 --away-odds 2.0

    # Predict from today's schedule
    python scripts/production_predict.py --date 2025-04-15

    # Batch predict from CSV
    python scripts/production_predict.py --games-file today_games.csv
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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp_server.betting import BettingDecisionEngine
    HAS_BETTING_ENGINE = True
except ImportError:
    HAS_BETTING_ENGINE = False
    print("Warning: Betting engine not available")

try:
    from mcp_server.betting.feature_extractor import FeatureExtractor
    from mcp_server.unified_secrets_manager import load_secrets_hierarchical
    import psycopg2
    import os
    HAS_DATABASE = True
except ImportError as e:
    HAS_DATABASE = False
    print(f"Warning: Database integration not available: {e}")

warnings.filterwarnings('ignore')


class ProductionPredictor:
    """Production prediction system."""

    def __init__(self, model_path: str, engine_path: str):
        """
        Initialize production predictor.

        Args:
            model_path: Path to trained ensemble model
            engine_path: Path to calibrated Kelly engine
        """
        print("Loading production models...")

        # Load ensemble model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        print(f"✓ Loaded ensemble model from {model_path}")

        # Load calibrated Kelly engine
        with open(engine_path, 'rb') as f:
            self.engine = pickle.load(f)
        print(f"✓ Loaded Kelly engine from {engine_path}")

        self.feature_names = self.model.feature_names if hasattr(self.model, 'feature_names') else None

    def predict_game(
        self,
        home_team: str,
        away_team: str,
        home_features: dict,
        away_features: dict,
        odds: float,
        away_odds: float,
        bankroll: float = 10000
    ) -> dict:
        """
        Make prediction and betting decision for a single game.

        Args:
            home_team: Home team ID
            away_team: Away team ID
            home_features: Dictionary of home team features
            away_features: Dictionary of away team features
            odds: Decimal odds for home team
            away_odds: Decimal odds for away team
            bankroll: Current bankroll

        Returns:
            Dictionary with prediction, calibrated probability, and betting decision
        """
        # Construct feature vector
        features = self._construct_feature_vector(home_features, away_features)

        # Get model prediction (uncalibrated probability)
        sim_prob = self.model.predict_proba(features)[0]

        # Get betting decision (includes calibration)
        game_id = f"{home_team}_vs_{away_team}_{datetime.now().strftime('%Y%m%d')}"

        decision = self.engine.decide(
            sim_prob=sim_prob,
            odds=odds,
            away_odds=away_odds,
            bankroll=bankroll,
            game_id=game_id
        )

        # Add metadata
        decision.update({
            'home_team': home_team,
            'away_team': away_team,
            'prediction_time': datetime.now().isoformat(),
            'uncalibrated_prob': sim_prob
        })

        return decision

    def _construct_feature_vector(self, home_features: dict, away_features: dict) -> np.ndarray:
        """Construct feature vector from team statistics."""
        # This is a simplified version - in production, you'd extract actual features
        # from recent team performance using the same logic as prepare_game_features.py

        if self.feature_names:
            # Use model's expected features
            features = []
            for feat_name in self.feature_names:
                if feat_name.startswith('home_'):
                    key = feat_name[5:]  # Remove 'home_' prefix
                    features.append(home_features.get(key, 0))
                elif feat_name.startswith('away_'):
                    key = feat_name[5:]  # Remove 'away_' prefix
                    features.append(away_features.get(key, 0))
                else:
                    # Other features (h2h, rest days, etc.)
                    features.append(0)  # Default

            return np.array(features).reshape(1, -1)
        else:
            # Fallback: use provided features directly
            all_features = {**{f"home_{k}": v for k, v in home_features.items()},
                          **{f"away_{k}": v for k, v in away_features.items()}}
            return np.array(list(all_features.values())).reshape(1, -1)

    def predict_games_batch(self, games_df: pd.DataFrame, bankroll: float = 10000) -> pd.DataFrame:
        """
        Predict multiple games from DataFrame.

        Args:
            games_df: DataFrame with columns: home_team, away_team, odds, away_odds, + features
            bankroll: Current bankroll

        Returns:
            DataFrame with predictions and betting decisions
        """
        predictions = []

        for _, game in games_df.iterrows():
            # Extract features (simplified - would need full feature extraction)
            home_features = {k.replace('home_', ''): v
                           for k, v in game.items() if k.startswith('home_')}
            away_features = {k.replace('away_', ''): v
                           for k, v in game.items() if k.startswith('away_')}

            # Make prediction
            pred = self.predict_game(
                home_team=game['home_team'],
                away_team=game['away_team'],
                home_features=home_features,
                away_features=away_features,
                odds=game['odds'],
                away_odds=game['away_odds'],
                bankroll=bankroll
            )

            predictions.append(pred)

        return pd.DataFrame(predictions)

    def format_betting_recommendation(self, decision: dict) -> str:
        """Format betting decision as human-readable text."""
        output = []
        output.append("=" * 80)
        output.append(f"🏀 {decision['home_team']} vs {decision['away_team']}")
        output.append("=" * 80)

        output.append(f"\n📊 Prediction:")
        output.append(f"  Uncalibrated Probability: {decision['uncalibrated_prob']:.1%}")
        output.append(f"  Calibrated Probability: {decision['calibrated_prob']:.1%}")
        output.append(f"  Market Odds: {decision['odds']:.2f} ({1/decision['odds']:.1%})")

        output.append(f"\n💰 Betting Decision:")
        if decision['should_bet']:
            output.append(f"  ✓ RECOMMEND BET")
            output.append(f"  Bet Amount: ${decision['bet_amount']:.2f} ({decision['bet_amount']/decision.get('bankroll', 10000):.1%} of bankroll)")
            output.append(f"  Expected Edge: {decision['edge']:.2%}")
            output.append(f"  Kelly Fraction: {decision['kelly_fraction']:.1%}")

            output.append(f"\n  If WIN:")
            output.append(f"    Profit: ${decision['bet_amount'] * (decision['odds'] - 1):.2f}")
            output.append(f"  If LOSE:")
            output.append(f"    Loss: ${decision['bet_amount']:.2f}")

            # Large bet warning
            if decision['bet_amount'] / decision.get('bankroll', 10000) > 0.25:
                output.append(f"\n  ⚠️  LARGE BET (>{int(decision['bet_amount']/decision.get('bankroll', 10000)*100)}% of bankroll)")
                output.append(f"  Make sure all criteria are met:")
                output.append(f"    - Calibrated prob > 88%: {decision['calibrated_prob'] > 0.88}")
                output.append(f"    - Edge > 20%: {decision['edge'] > 0.20}")
                output.append(f"    - High confidence: Review uncertainty")
        else:
            output.append(f"  ✗ DO NOT BET")
            output.append(f"  Reason: {decision.get('reason', 'No edge detected')}")
            output.append(f"  Edge: {decision.get('edge', 0):.2%}")

        output.append(f"\n" + "-" * 80)

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Production NBA game prediction and betting decisions"
    )
    parser.add_argument(
        '--model',
        default='models/ensemble_game_outcome_model.pkl',
        help='Path to trained ensemble model'
    )
    parser.add_argument(
        '--engine',
        default='models/calibrated_kelly_engine.pkl',
        help='Path to calibrated Kelly engine'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=10000,
        help='Current bankroll in dollars'
    )

    # Single game prediction
    parser.add_argument('--home', help='Home team abbreviation (e.g., LAL)')
    parser.add_argument('--away', help='Away team abbreviation (e.g., GSW)')
    parser.add_argument('--home-team-id', type=int, help='Home team ID (for database mode)')
    parser.add_argument('--away-team-id', type=int, help='Away team ID (for database mode)')
    parser.add_argument('--game-date', help='Game date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--odds', type=float, help='Decimal odds for home team')
    parser.add_argument('--away-odds', type=float, help='Decimal odds for away team')

    # Database mode
    parser.add_argument('--use-database', action='store_true',
                        help='Use real features from database instead of placeholders')

    # Batch prediction
    parser.add_argument('--games-file', help='CSV file with games to predict')
    parser.add_argument('--output', help='Output file for predictions')

    args = parser.parse_args()

    print("=" * 80)
    print("NBA Production Prediction System")
    print("=" * 80)

    # Initialize predictor
    predictor = ProductionPredictor(args.model, args.engine)

    print(f"\nBankroll: ${args.bankroll:,.2f}")
    print()

    # Single game prediction
    if args.home and args.away and args.odds and args.away_odds:
        print("Mode: Single Game Prediction")
        print("-" * 80)

        # Feature extraction: database or placeholders
        if args.use_database and HAS_DATABASE:
            if not args.home_team_id or not args.away_team_id:
                print("❌ Error: --home-team-id and --away-team-id required with --use-database")
                return 1

            print("✓ Using real features from database")

            # Connect to database
            load_secrets_hierarchical()
            db_conn = psycopg2.connect(
                host=os.getenv('RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW'),
                port=os.getenv('RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW', '5432'),
                database=os.getenv('RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW'),
                user=os.getenv('RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW'),
                password=os.getenv('RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW')
            )

            # Extract features
            extractor = FeatureExtractor(db_conn)
            game_date = args.game_date or datetime.now().strftime('%Y-%m-%d')

            print(f"  Extracting features for {args.home} vs {args.away} on {game_date}")
            features = extractor.extract_game_features(
                home_team_id=args.home_team_id,
                away_team_id=args.away_team_id,
                game_date=game_date
            )

            # Split into home and away features (predict_game expects separate dicts)
            home_features = {k.replace('home_', ''): v for k, v in features.items() if k.startswith('home_')}
            away_features = {k.replace('away_', ''): v for k, v in features.items() if k.startswith('away_')}

            db_conn.close()

        else:
            if args.use_database:
                print("⚠️  Database not available - falling back to placeholder features")
            else:
                print("⚠️  Using simplified features (use --use-database for real data)")

            home_features = {
                'ppg_l10': 115.0,
                'fg_pct_l10': 0.475,
                'three_pt_pct_l10': 0.365,
                'form_l5': 0.6
            }

            away_features = {
                'ppg_l10': 110.0,
                'fg_pct_l10': 0.460,
                'three_pt_pct_l10': 0.350,
                'form_l5': 0.4
            }

        decision = predictor.predict_game(
            home_team=args.home,
            away_team=args.away,
            home_features=home_features,
            away_features=away_features,
            odds=args.odds,
            away_odds=args.away_odds,
            bankroll=args.bankroll
        )

        # Print recommendation
        print(predictor.format_betting_recommendation(decision))

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(decision, f, indent=2)
            print(f"\n✓ Saved prediction to {args.output}")

    # Batch prediction
    elif args.games_file:
        print(f"Mode: Batch Prediction from {args.games_file}")
        print("-" * 80)

        games_df = pd.read_csv(args.games_file)
        print(f"Loaded {len(games_df)} games")

        predictions_df = predictor.predict_games_batch(games_df, args.bankroll)

        # Print summary
        bet_count = predictions_df['should_bet'].sum()
        total_bet_amount = predictions_df[predictions_df['should_bet']]['bet_amount'].sum()

        print(f"\nBatch Prediction Summary:")
        print(f"  Games analyzed: {len(predictions_df)}")
        print(f"  Recommended bets: {bet_count}")
        print(f"  Total bet amount: ${total_bet_amount:.2f} ({total_bet_amount/args.bankroll:.1%} of bankroll)")

        # Print each recommendation
        for _, decision in predictions_df.iterrows():
            if decision['should_bet']:
                print(predictor.format_betting_recommendation(decision.to_dict()))

        # Save to file
        if args.output:
            predictions_df.to_csv(args.output, index=False)
            print(f"\n✓ Saved all predictions to {args.output}")

    else:
        print("Error: Must provide either (--home, --away, --odds, --away-odds) or --games-file")
        parser.print_help()
        sys.exit(1)

    print("\n✓ Prediction complete")


if __name__ == '__main__':
    main()
