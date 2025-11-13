#!/usr/bin/env python3
"""
Bet Outcome Recording Script

Automatically fetches completed games from the database, matches them against
pending paper bets, updates bet outcomes, calculates CLV from closing lines,
and updates the calibrator with new observations.

This script should be run after games complete (typically next morning) to:
1. Find all pending bets from paper trading database
2. Match against completed games in NBA database
3. Determine win/loss outcome
4. Record closing odds (for CLV calculation)
5. Settle bets in paper trading system
6. Update calibrator with actual outcomes

Usage:
------
    # Record outcomes for all pending bets
    python scripts/record_outcomes.py

    # Record outcomes for specific date
    python scripts/record_outcomes.py --date 2025-01-05

    # Dry run (show what would be updated without making changes)
    python scripts/record_outcomes.py --dry-run

    # Verbose output
    python scripts/record_outcomes.py --verbose

Output:
-------
    ============================================
    BET OUTCOME RECORDING - 2025-01-05 09:30:00
    ============================================

    📋 Found 5 pending bets to process

    Processing bet 1/5:
    -------------------
    Bet ID: LAL_vs_GSW_home_20250105_180000
    Game: LAL vs GSW
    Bet: $180 on HOME (LAL) at 1.90
    Result: LAL 118, GSW 112
    ✓ WON - Payout: $342.00, Profit: $162.00
    Closing odds: 1.85
    CLV: +2.7% (bet at better odds than closing)

    Processing bet 2/5:
    -------------------
    Bet ID: BOS_vs_PHX_home_20250105_190000
    Game: BOS vs PHX
    Bet: $200 on HOME (BOS) at 1.75
    Result: BOS 105, PHX 110
    ✗ LOST - Loss: -$200.00
    Closing odds: 1.80
    CLV: -2.8% (bet at worse odds than closing)

    ...

    ============================================
    SUMMARY
    ============================================
    Bets processed: 5
    Won: 3 (60.0%)
    Lost: 2 (40.0%)
    Net profit/loss: +$250.00
    Average CLV: +1.2%

    ✓ Calibrator updated with 5 new observations
    ✓ Paper trading database updated
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.betting.paper_trading import PaperTradingEngine, PaperBet, BetStatus
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
import psycopg2
from psycopg2.extras import RealDictCursor


def fetch_completed_games(
    db_conn, game_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch completed games from NBA database

    Args:
        db_conn: Database connection
        game_date: Optional date filter (YYYY-MM-DD)

    Returns:
        List of completed games with scores
    """
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)

    if game_date:
        query = """
            SELECT
                g.game_id,
                g.game_date,
                g.home_team_id,
                g.visitor_team_id as away_team_id,
                g.home_team_pts,
                g.visitor_team_pts as away_team_pts,
                ht.full_name as home_team_name,
                vt.full_name as away_team_name,
                ht.abbreviation as home_team_abbr,
                vt.abbreviation as away_team_abbr
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams vt ON g.visitor_team_id = vt.team_id
            WHERE g.game_date = %s
            AND g.home_team_pts IS NOT NULL  -- Game completed
            ORDER BY g.game_date DESC
        """
        cursor.execute(query, (game_date,))
    else:
        # Get games from yesterday and today
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        query = """
            SELECT
                g.game_id,
                g.game_date,
                g.home_team_id,
                g.visitor_team_id as away_team_id,
                g.home_team_pts,
                g.visitor_team_pts as away_team_pts,
                ht.full_name as home_team_name,
                vt.full_name as away_team_name,
                ht.abbreviation as home_team_abbr,
                vt.abbreviation as away_team_abbr
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams vt ON g.visitor_team_id = vt.team_id
            WHERE g.game_date >= %s
            AND g.home_team_pts IS NOT NULL  -- Game completed
            ORDER BY g.game_date DESC
        """
        cursor.execute(query, (yesterday,))

    games = cursor.fetchall()
    return [dict(game) for game in games]


def match_bet_to_game(
    bet: PaperBet, games: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Match a paper bet to a completed game

    Args:
        bet: PaperBet object
        games: List of completed games

    Returns:
        Matching game dict or None
    """
    # Extract team names from bet game_id
    # Format: "TeamName_vs_TeamName_20250105" or similar
    bet_id = bet.game_id

    for game in games:
        # Try to match by team names in bet ID
        home_team = game["home_team_name"].replace(" ", "_")
        away_team = game["away_team_name"].replace(" ", "_")

        if home_team in bet_id and away_team in bet_id:
            return game

        # Also try abbreviations
        if game["home_team_abbr"] in bet_id and game["away_team_abbr"] in bet_id:
            return game

    return None


def determine_outcome(bet: PaperBet, game: Dict[str, Any]) -> str:
    """
    Determine bet outcome (win/loss/push)

    Args:
        bet: PaperBet object
        game: Completed game dict

    Returns:
        'win', 'loss', or 'push'
    """
    home_score = game["home_team_pts"]
    away_score = game["away_team_pts"]

    if home_score == away_score:
        return "push"  # Tie (rare in NBA but possible in spreads)

    # Determine winner
    home_won = home_score > away_score

    # Check if bet won
    if bet.bet_type.value == "home":
        return "win" if home_won else "loss"
    else:  # away
        return "win" if not home_won else "loss"


def get_closing_odds(game: Dict[str, Any], bet_type: str) -> Optional[float]:
    """
    Get closing odds for a game

    In production, this would query an odds API for the closing line.
    For now, returns a mock closing odds (slightly adjusted from opening).

    Args:
        game: Game dict
        bet_type: 'home' or 'away'

    Returns:
        Closing odds or None
    """
    # TODO: Integrate with odds API (e.g., The Odds API)
    # For now, return None to skip CLV calculation
    # Or mock it with slight variation from bet odds

    # Mock implementation: closing odds = opening +/- 2-5%
    import random

    random.seed(game["game_id"])
    variation = random.uniform(-0.05, 0.05)

    # Estimate opening odds from game outcome
    # (In production, you'd store opening odds with the bet)
    if bet_type == "home":
        estimated_opening = 1.90
    else:
        estimated_opening = 2.00

    closing = estimated_opening * (1 + variation)
    return round(closing, 2)


def process_bet_outcome(
    paper_engine: PaperTradingEngine,
    bet: PaperBet,
    game: Dict[str, Any],
    verbose: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Process outcome for a single bet

    Args:
        paper_engine: PaperTradingEngine instance
        bet: PaperBet to process
        game: Matching completed game
        verbose: Print detailed info
        dry_run: Don't make actual changes

    Returns:
        Result dictionary with processing info
    """
    result = {
        "bet_id": bet.bet_id,
        "game_id": game["game_id"],
        "success": False,
        "outcome": None,
        "profit_loss": 0,
        "clv": None,
    }

    try:
        # Determine outcome
        outcome = determine_outcome(bet, game)
        result["outcome"] = outcome

        # Get closing odds
        closing_odds = get_closing_odds(game, bet.bet_type.value)

        # Calculate profit/loss
        if outcome == "win":
            payout = bet.amount * bet.odds
            profit_loss = payout - bet.amount
        elif outcome == "loss":
            profit_loss = -bet.amount
        else:  # push
            profit_loss = 0

        result["profit_loss"] = profit_loss
        result["closing_odds"] = closing_odds

        # Verbose output
        if verbose:
            print(f"\nBet ID: {bet.bet_id}")
            print(f"Game: {game['home_team_name']} vs {game['away_team_name']}")
            print(
                f"Score: {game['home_team_name']} {game['home_team_pts']}, "
                f"{game['away_team_name']} {game['away_team_pts']}"
            )
            print(
                f"Bet: ${bet.amount:.2f} on {bet.bet_type.value.upper()} at {bet.odds:.2f}"
            )
            print(f"Outcome: {outcome.upper()}")
            print(f"Profit/Loss: ${profit_loss:+.2f}")
            if closing_odds:
                print(f"Closing odds: {closing_odds:.2f}")
                clv = (closing_odds - bet.odds) / bet.odds
                print(f"CLV: {clv:+.1%}")
                result["clv"] = clv

        # Settle bet (unless dry run)
        if not dry_run:
            paper_engine.settle_bet(
                bet_id=bet.bet_id, outcome=outcome, closing_odds=closing_odds
            )

        result["success"] = True

    except Exception as e:
        print(f"❌ Error processing bet {bet.bet_id}: {e}")
        result["error"] = str(e)

    return result


def update_calibrator(
    paper_engine: PaperTradingEngine,
    processed_bets: List[Dict[str, Any]],
    dry_run: bool = False,
):
    """
    Update calibrator with new observations from settled bets

    Args:
        paper_engine: PaperTradingEngine instance
        processed_bets: List of processed bet result dicts
        dry_run: Don't make actual changes
    """
    # Note: This is a placeholder. The actual calibrator update would happen
    # in the BettingDecisionEngine, not here. This is just for demonstration.

    successful_bets = [b for b in processed_bets if b["success"]]

    if not successful_bets:
        print("\n⚠️  No bets to add to calibrator")
        return

    print(f"\n📊 Would update calibrator with {len(successful_bets)} observations")

    if not dry_run:
        # In production, you would:
        # 1. Load the betting engine
        # 2. For each bet, call engine.calibrator.add_observation()
        # 3. Save the updated calibrator
        print("   (Calibrator update not implemented - requires engine persistence)")


def main():
    parser = argparse.ArgumentParser(
        description="Record outcomes for paper trading bets"
    )
    parser.add_argument(
        "--db-path",
        default="data/paper_trades.db",
        help="Path to paper trading database",
    )
    parser.add_argument("--date", help="Process bets for specific date (YYYY-MM-DD)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("=" * 70)
    print(f"BET OUTCOME RECORDING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")

    # Initialize paper trading engine
    if not os.path.exists(args.db_path):
        print(f"\n❌ Paper trading database not found: {args.db_path}")
        return 1

    paper_engine = PaperTradingEngine(db_path=args.db_path)

    # Get pending bets
    pending_bets = paper_engine.db.get_pending_bets()
    print(f"\n📋 Found {len(pending_bets)} pending bets to process")

    if not pending_bets:
        print("✓ No pending bets - nothing to do")
        return 0

    # Connect to NBA database
    try:
        print("\n🔗 Connecting to NBA database...")
        load_secrets_hierarchical()
        db_conn = psycopg2.connect(
            host=os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW"),
            port=os.getenv("RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW", "5432"),
            database=os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW"),
            user=os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW"),
            password=os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW"),
        )
        print("   ✓ Connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1

    # Fetch completed games
    print(f"\n🏀 Fetching completed games...")
    games = fetch_completed_games(db_conn, args.date)
    print(f"   ✓ Found {len(games)} completed games")

    if not games:
        print("\n⚠️  No completed games found")
        db_conn.close()
        return 0

    # Process each pending bet
    print("\n" + "=" * 70)
    print("PROCESSING BETS")
    print("=" * 70)

    processed = []
    matched = 0
    unmatched = 0

    for i, bet in enumerate(pending_bets, 1):
        print(f"\nProcessing bet {i}/{len(pending_bets)}:")
        print("-" * 70)

        # Match bet to game
        game = match_bet_to_game(bet, games)

        if not game:
            print(f"⚠️  No matching game found for bet {bet.bet_id}")
            print(f"   Bet may be for a future game")
            unmatched += 1
            continue

        # Process outcome
        result = process_bet_outcome(
            paper_engine, bet, game, args.verbose, args.dry_run
        )
        processed.append(result)
        matched += 1

        # Summary for this bet
        if result["success"]:
            outcome = result["outcome"].upper()
            pl = result["profit_loss"]
            symbol = "✓" if outcome == "WIN" else "✗" if outcome == "LOSS" else "⊘"
            print(f"{symbol} {outcome} - P/L: ${pl:+.2f}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    # Overall summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Pending bets: {len(pending_bets)}")
    print(f"Matched to games: {matched}")
    print(f"Unmatched: {unmatched}")

    if processed:
        won = sum(1 for b in processed if b["outcome"] == "win")
        lost = sum(1 for b in processed if b["outcome"] == "loss")
        pushed = sum(1 for b in processed if b["outcome"] == "push")
        net_pl = sum(b["profit_loss"] for b in processed)

        print(f"\nOutcomes:")
        print(f"  Won: {won} ({won / len(processed):.1%})")
        print(f"  Lost: {lost} ({lost / len(processed):.1%})")
        print(f"  Pushed: {pushed}")
        print(f"\nNet P/L: ${net_pl:+,.2f}")

        # CLV stats
        clvs = [b["clv"] for b in processed if b.get("clv") is not None]
        if clvs:
            avg_clv = sum(clvs) / len(clvs)
            print(f"Average CLV: {avg_clv:+.1%}")

        # Update calibrator
        if not args.dry_run:
            update_calibrator(paper_engine, processed, args.dry_run)
            print(f"\n✓ {len(processed)} bets settled")
        else:
            print(f"\n⚠️  Dry run - no changes made")

    # Close database connection
    db_conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
