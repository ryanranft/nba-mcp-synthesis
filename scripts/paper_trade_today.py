#!/usr/bin/env python3
"""
Paper Trade Today's Games

Fetches today's NBA games, runs predictions through the calibrated Kelly
betting engine, and places paper bets for recommended opportunities.

This script is the main entry point for daily paper trading workflow:
1. Load calibrated Kelly engine
2. Fetch today's games from database
3. Extract features for each game
4. Run betting decision logic
5. Place paper bets for recommendations
6. Display summary

Usage:
------
    # Paper trade all today's games
    python scripts/paper_trade_today.py

    # Paper trade specific game
    python scripts/paper_trade_today.py --game-id LAL_vs_GSW_20250105

    # Dry run (show recommendations without recording)
    python scripts/paper_trade_today.py --dry-run

    # Use custom odds (for testing)
    python scripts/paper_trade_today.py --home LAL --away GSW --home-odds 1.90 --away-odds 2.00

Output:
-------
    Paper Betting Recommendations for 2025-01-05
    ============================================

    Game 1: LAL vs GSW
    ------------------
    Home (LAL): 1.90 | Away (GSW): 2.00
    Simulation: 65.2% home win
    Edge: 10.7%
    ✅ RECOMMENDATION: BET $183 on HOME (LAL) at 1.90
    Reason: Strong edge (10.7%) + good calibration

    Game 2: BOS vs PHX
    ------------------
    Home (BOS): 1.75 | Away (PHX): 2.20
    Simulation: 58.1% home win
    Edge: 1.6%
    ❌ SKIP: Edge too small (1.6% < 5% threshold)

    Summary:
    --------
    - Games analyzed: 12
    - Bets recommended: 2
    - Total stake: $350
    - Current bankroll: $10,000
    - Available: $9,650
"""

import sys
import os
import argparse
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import warnings

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.betting.paper_trading import PaperTradingEngine, BetType
from mcp_server.betting.betting_decision import BettingDecisionEngine
from mcp_server.betting.feature_extractor import FeatureExtractor
from mcp_server.betting.notifications import NotificationManager
from mcp_server.betting.alert_system import AlertSystem
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
import psycopg2


def load_betting_engine(engine_path: str = "models/calibrated_kelly_engine.pkl"):
    """Load calibrated Kelly betting engine"""
    try:
        import dill as pickle
    except ImportError:
        print("❌ Error: dill package required. Run: pip install dill")
        sys.exit(1)

    if not os.path.exists(engine_path):
        print(f"❌ Error: Engine not found at {engine_path}")
        print("   Run: python scripts/train_kelly_calibrator.py")
        sys.exit(1)

    with open(engine_path, 'rb') as f:
        engine = pickle.load(f)

    return engine


def fetch_todays_games(db_conn) -> List[Dict[str, Any]]:
    """
    Fetch today's NBA games from database

    Returns list of games with:
    - game_id
    - home_team_id
    - away_team_id
    - home_team_name
    - away_team_name
    - game_date
    """
    cursor = db_conn.cursor()

    # Get today's games (games scheduled for today)
    today = date.today().strftime('%Y-%m-%d')

    query = """
        SELECT
            g.game_id,
            g.home_team_id,
            g.visitor_team_id as away_team_id,
            ht.full_name as home_team_name,
            vt.full_name as away_team_name,
            g.game_date
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams vt ON g.visitor_team_id = vt.team_id
        WHERE g.game_date = %s
        AND g.home_team_pts IS NULL  -- Game not played yet
        ORDER BY g.game_date
    """

    cursor.execute(query, (today,))
    games = cursor.fetchall()

    return [
        {
            'game_id': g[0],
            'home_team_id': g[1],
            'away_team_id': g[2],
            'home_team_name': g[3],
            'away_team_name': g[4],
            'game_date': g[5]
        }
        for g in games
    ]


def get_mock_odds(home_team: str, away_team: str) -> Dict[str, float]:
    """
    Get mock odds for testing

    In production, this would query an odds API (e.g., The Odds API)
    For now, returns reasonable mock odds
    """
    # Mock odds based on typical NBA lines
    # Home court advantage typically ~3 points = ~1.80-1.85 odds
    return {
        'home_odds': 1.90,
        'away_odds': 2.00
    }


def extract_game_features(
    game: Dict[str, Any],
    feature_extractor: FeatureExtractor,
    ensemble_model
) -> Dict[str, Any]:
    """
    Extract features for a game using FeatureExtractor and run prediction

    Args:
        game: Game dictionary with team IDs and date
        feature_extractor: FeatureExtractor instance
        ensemble_model: Trained ensemble model for prediction

    Returns:
        Dictionary with features and sim_prob
    """
    import numpy as np

    # Extract features from database
    features = feature_extractor.extract_game_features(
        home_team_id=game['home_team_id'],
        away_team_id=game['away_team_id'],
        game_date=game['game_date'].strftime('%Y-%m-%d') if hasattr(game['game_date'], 'strftime') else str(game['game_date'])
    )

    # Run ensemble model to get home win probability
    # Convert features dict to numpy array in correct order
    # Note: This assumes the model was trained with specific feature order
    # In production, you'd load the feature names from model metadata

    try:
        # Try to predict with the model
        feature_array = np.array([list(features.values())])
        sim_prob = ensemble_model.predict_proba(feature_array)[0][1]  # P(home win)
    except Exception as e:
        # Fallback to simple heuristic if model prediction fails
        print(f"   ⚠️ Model prediction failed: {e}")
        print(f"   Using heuristic based on team stats")

        # Simple heuristic: home team has 55% baseline + adjustments
        home_win_pct = features.get('home_win_pct', 0.5)
        away_win_pct = features.get('away_win_pct', 0.5)
        sim_prob = 0.55 + 0.2 * (home_win_pct - away_win_pct)
        sim_prob = np.clip(sim_prob, 0.3, 0.8)  # Keep reasonable

    features['sim_prob'] = sim_prob
    return features


def make_betting_decision(
    engine: BettingDecisionEngine,
    game: Dict[str, Any],
    odds: Dict[str, float],
    features: Dict[str, Any],
    bankroll: float
) -> Dict[str, Any]:
    """
    Make betting decision for a game

    Returns decision dict with:
    - should_bet: bool
    - bet_amount: float
    - bet_side: 'home' or 'away'
    - odds: float
    - edge: float
    - reason: str
    """
    game_id = f"{game['home_team_name']}_vs_{game['away_team_name']}_{game['game_date'].strftime('%Y%m%d')}"

    # Run decision engine
    decision = engine.decide(
        sim_prob=features['sim_prob'],
        odds=odds['home_odds'],
        away_odds=odds['away_odds'],
        bankroll=bankroll,
        game_id=game_id,
        date=datetime.now()
    )

    return decision


def print_game_recommendation(
    game: Dict[str, Any],
    decision: Dict[str, Any],
    odds: Dict[str, float],
    features: Dict[str, Any],
    game_num: int
):
    """Print formatted betting recommendation"""
    print(f"\n{'=' * 70}")
    print(f"Game {game_num}: {game['home_team_name']} vs {game['away_team_name']}")
    print(f"{'=' * 70}")
    print(f"Home ({game['home_team_name']}): {odds['home_odds']:.2f} | Away ({game['away_team_name']}): {odds['away_odds']:.2f}")
    print(f"Simulation: {features['sim_prob']:.1%} home win")

    if decision['should_bet']:
        print(f"Edge: {decision['edge']:.1%}")
        print(f"✅ RECOMMENDATION: BET ${decision['bet_amount']:.2f} on HOME at {decision['odds']:.2f}")
        print(f"   Reason: {decision.get('reason', 'N/A')}")
    else:
        print(f"❌ SKIP: {decision.get('reason', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="Paper trade today's NBA games")
    parser.add_argument('--engine', default='models/calibrated_kelly_engine.pkl',
                        help='Path to calibrated Kelly engine')
    parser.add_argument('--db-path', default='data/paper_trades.db',
                        help='Path to paper trading database')
    parser.add_argument('--bankroll', type=float, default=10000,
                        help='Starting bankroll (only for new database)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show recommendations without recording bets')
    parser.add_argument('--game-id', help='Process specific game only')
    parser.add_argument('--home', help='Home team abbreviation (for testing)')
    parser.add_argument('--away', help='Away team abbreviation (for testing)')
    parser.add_argument('--home-odds', type=float, help='Home team odds (for testing)')
    parser.add_argument('--away-odds', type=float, help='Away team odds (for testing)')
    parser.add_argument('--sms', action='store_true',
                        help='Send SMS notification for bet recommendations')
    parser.add_argument('--sms-critical-only', action='store_true',
                        help='Only send SMS for high-value bets (edge >= 10%%)')

    args = parser.parse_args()

    print("=" * 70)
    print(f"Paper Trading - {date.today().strftime('%Y-%m-%d')}")
    print("=" * 70)

    # Load betting engine
    print("\n📊 Loading calibrated Kelly engine...")
    engine = load_betting_engine(args.engine)
    print(f"   ✓ Engine loaded from {args.engine}")

    # Load ensemble model for predictions
    print("\n📈 Loading ensemble model...")
    try:
        import pickle
        with open('models/ensemble_game_outcome_model.pkl', 'rb') as f:
            ensemble_model = pickle.load(f)
        print(f"   ✓ Ensemble model loaded")
    except Exception as e:
        print(f"   ⚠️ Failed to load ensemble model: {e}")
        print(f"   Will use heuristic predictions")
        ensemble_model = None

    # Initialize paper trading
    print(f"\n💰 Initializing paper trading engine...")
    paper_engine = PaperTradingEngine(
        starting_bankroll=args.bankroll,
        db_path=args.db_path
    )
    print(f"   ✓ Current bankroll: ${paper_engine.current_bankroll:,.2f}")

    # Fetch games
    if args.home and args.away:
        # Manual game entry for testing
        print(f"\n🏀 Testing with manual game: {args.home} vs {args.away}")
        games = [{
            'game_id': f'{args.home}_vs_{args.away}_TEST',
            'home_team_id': args.home,
            'away_team_id': args.away,
            'home_team_name': args.home,
            'away_team_name': args.away,
            'game_date': datetime.now()
        }]

        # Use provided odds or mock
        odds = {
            'home_odds': args.home_odds or 1.90,
            'away_odds': args.away_odds or 2.00
        }
        games_odds = [(games[0], odds)]
        feature_extractor = None  # Will use mock features in manual mode

    else:
        # Fetch from database
        print("\n🏀 Fetching today's games from database...")
        try:
            load_secrets_hierarchical()
            db_config = {
                'host': os.getenv('RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW'),
                'port': os.getenv('RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW', '5432'),
                'database': os.getenv('RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW'),
                'user': os.getenv('RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW'),
                'password': os.getenv('RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW')
            }

            db_conn = psycopg2.connect(**db_config)
            feature_extractor = FeatureExtractor(db_conn)
            games = fetch_todays_games(db_conn)
            print(f"   ✓ Found {len(games)} games scheduled for today")

            if not games:
                print("\n⚠️  No games scheduled for today. Try manual mode with --home/--away")
                return 0

            # Get odds for each game (mock for now)
            games_odds = [(game, get_mock_odds(game['home_team_name'], game['away_team_name']))
                          for game in games]

        except Exception as e:
            print(f"\n⚠️  Database connection failed: {e}")
            print("   Using mock data for demonstration")
            games = []
            games_odds = []
            db_conn = None
            feature_extractor = None

    # Process each game
    print("\n" + "=" * 70)
    print("BETTING RECOMMENDATIONS")
    print("=" * 70)

    recommendations = []
    total_stake = 0

    for i, (game, odds) in enumerate(games_odds, 1):
        # Extract features (real or mock)
        if feature_extractor and ensemble_model:
            # Use real feature extraction
            features = extract_game_features(game, feature_extractor, ensemble_model)
        else:
            # Fallback to simple mock
            import numpy as np
            np.random.seed(hash(game['game_id']) % (2**32))
            features = {
                'sim_prob': np.random.uniform(0.50, 0.70),  # Mock probability
                'home_win_pct': 0.6,
                'away_win_pct': 0.5
            }

        # Make betting decision
        decision = make_betting_decision(
            engine=engine,
            game=game,
            odds=odds,
            features=features,
            bankroll=paper_engine.current_bankroll
        )

        # Print recommendation
        print_game_recommendation(game, decision, odds, features, i)

        # Track recommendation
        if decision['should_bet']:
            recommendations.append({
                'game': game,
                'decision': decision,
                'odds': odds,
                'features': features
            })
            total_stake += decision['bet_amount']

    # Place paper bets (unless dry run)
    if recommendations and not args.dry_run:
        print("\n" + "=" * 70)
        print("PLACING PAPER BETS")
        print("=" * 70)

        for i, rec in enumerate(recommendations, 1):
            game = rec['game']
            decision = rec['decision']
            odds = rec['odds']
            features = rec['features']

            try:
                bet = paper_engine.place_bet(
                    game_id=decision['game_id'],
                    bet_type='home',  # Currently only home bets supported
                    amount=decision['bet_amount'],
                    odds=decision['odds'],
                    sim_prob=features['sim_prob'],
                    edge=decision['edge'],
                    kelly_fraction=decision.get('kelly_fraction'),
                    notes=f"Paper trade: {game['home_team_name']} vs {game['away_team_name']}"
                )
                print(f"   ✓ Bet {i}: ${bet.amount:.2f} on {game['home_team_name']} (ID: {bet.bet_id})")
            except Exception as e:
                print(f"   ✗ Bet {i} failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Games analyzed: {len(games_odds)}")
    print(f"Bets recommended: {len(recommendations)}")
    print(f"Total stake: ${total_stake:.2f}")
    print(f"Current bankroll: ${paper_engine.current_bankroll:,.2f}")
    print(f"Available after bets: ${paper_engine.current_bankroll - total_stake:,.2f}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No bets recorded")
    elif recommendations:
        print(f"\n✅ Paper bets recorded to {args.db_path}")
        print("   Check results later with: python scripts/paper_trade_dashboard.py")

    # Send SMS notification if requested
    if args.sms and recommendations and not args.dry_run:
        print("\n📱 Sending SMS notification...")
        try:
            # Initialize notification manager
            notifier = NotificationManager(config={
                'sms': {'enabled': True}
            })

            # Filter recommendations for SMS (critical only if flag set)
            sms_recs = recommendations
            if args.sms_critical_only:
                sms_recs = [r for r in recommendations if r['decision']['edge'] >= 0.10]

            if sms_recs:
                # Build SMS message
                msg_lines = [f"🏀 NBA Bets Today ({len(sms_recs)})"]
                for rec in sms_recs[:3]:  # Max 3 bets in SMS
                    game = rec['game']
                    decision = rec['decision']
                    msg_lines.append(
                        f"${decision['bet_amount']:.0f} on {game['home_team_name']} "
                        f"({decision['edge']:.1%} edge)"
                    )
                if len(sms_recs) > 3:
                    msg_lines.append(f"...+{len(sms_recs) - 3} more")

                msg_lines.append(f"Total: ${total_stake:.0f}")
                sms_message = "\n".join(msg_lines)

                # Send SMS
                result = notifier.send_message(
                    subject="NBA Betting",
                    message=sms_message,
                    channels=['sms']
                )

                if result.get('sms', {}).success:
                    print("   ✓ SMS sent successfully")
                else:
                    print(f"   ✗ SMS failed: {result.get('sms', {}).error}")
            else:
                print("   ℹ️  No qualifying bets for SMS (critical threshold not met)")

        except Exception as e:
            print(f"   ✗ SMS notification failed: {e}")

    # Close database connection
    if 'db_conn' in locals() and db_conn:
        db_conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
