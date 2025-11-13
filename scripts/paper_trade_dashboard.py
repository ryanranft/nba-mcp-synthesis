#!/usr/bin/env python3
"""
Paper Trading Dashboard

Displays comprehensive performance metrics for paper trading system.
Shows win rate, ROI, Sharpe ratio, CLV, bankroll history, and recent bets.

Usage:
------
    # Show dashboard
    python scripts/paper_trade_dashboard.py

    # Show detailed bet history
    python scripts/paper_trade_dashboard.py --detailed

    # Export to CSV
    python scripts/paper_trade_dashboard.py --export bets.csv

    # Show only recent N bets
    python scripts/paper_trade_dashboard.py --recent 10

Example Output:
---------------
    ╔════════════════════════════════════════════════════════════════════╗
    ║              PAPER TRADING PERFORMANCE DASHBOARD                   ║
    ║                     2025-01-05 14:30:00                           ║
    ╚════════════════════════════════════════════════════════════════════╝

    📊 OVERALL PERFORMANCE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Starting Bankroll:     $10,000.00
    Current Bankroll:      $10,850.50
    Total Profit/Loss:     $850.50 (+8.51%)
    ROI:                   12.3%
    Sharpe Ratio:          1.85

    📈 BET STATISTICS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total Bets:            47
    Won:                   28 (59.6%)
    Lost:                  19 (40.4%)
    Pushed:                0 (0.0%)
    Pending:               5

    Average Bet:           $183.45
    Average Odds:          1.93
    Average Edge:          7.2%
    Average CLV:           +2.8%

    🎯 RISK METRICS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Max Drawdown:          -$250.00 (-2.5%)
    Current Streak:        +3 wins
    Largest Win:           $450.00
    Largest Loss:          -$200.00

    📋 RECENT BETS (Last 5)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    2025-01-05 | LAL vs GSW  | HOME | $180 @ 1.90 | ✓ WON  | +$162.00
    2025-01-04 | BOS vs PHX  | HOME | $200 @ 1.85 | ✗ LOST | -$200.00
    2025-01-04 | MIA vs DEN  | HOME | $150 @ 2.00 | ✓ WON  | +$150.00
    2025-01-03 | CHI vs NYK  | HOME | $175 @ 1.95 | ✓ WON  | +$166.25
    2025-01-03 | DAL vs LAC  | HOME | $190 @ 1.88 | ✗ LOST | -$190.00
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import csv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.betting.paper_trading import PaperTradingEngine, PaperBet, BetStatus


def print_header():
    """Print dashboard header"""
    print("\n")
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 15 + "PAPER TRADING PERFORMANCE DASHBOARD" + " " * 20 + "║")
    print(
        "║" + " " * 24 + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " * 25 + "║"
    )
    print("╚" + "═" * 70 + "╝")


def print_section_header(title: str):
    """Print section header"""
    print(f"\n{title}")
    print("━" * 70)


def format_currency(amount: float) -> str:
    """Format currency with color"""
    if amount > 0:
        return f"${amount:,.2f} (+{amount / 10000 * 100:.2f}%)"
    elif amount < 0:
        return f"-${abs(amount):,.2f} ({amount / 10000 * 100:.2f}%)"
    else:
        return f"${amount:,.2f} (0.00%)"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage"""
    return f"{value * 100:.{decimals}f}%"


def print_overall_performance(engine: PaperTradingEngine, stats: Dict[str, Any]):
    """Print overall performance metrics"""
    print_section_header("📊 OVERALL PERFORMANCE")

    starting = engine.starting_bankroll
    current = engine.current_bankroll
    pl = stats["total_profit_loss"]
    pl_pct = stats["bankroll_change_pct"]

    print(f"Starting Bankroll:     ${starting:,.2f}")
    print(f"Current Bankroll:      ${current:,.2f}")

    if pl > 0:
        print(f"Total Profit/Loss:     ${pl:,.2f} (+{pl_pct:.2%}) ✅")
    elif pl < 0:
        print(f"Total Profit/Loss:     -${abs(pl):,.2f} ({pl_pct:.2%}) ❌")
    else:
        print(f"Total Profit/Loss:     ${pl:,.2f} ({pl_pct:.2%})")

    print(f"ROI:                   {format_percentage(stats['roi'], 1)}")
    print(f"Sharpe Ratio:          {stats['sharpe_ratio']:.2f}")


def print_bet_statistics(engine: PaperTradingEngine, stats: Dict[str, Any]):
    """Print bet statistics"""
    print_section_header("📈 BET STATISTICS")

    total_bets = stats["total_bets"]
    won = stats["total_won"]
    lost = stats["total_lost"]
    pushed = stats["total_pushed"]

    if total_bets > 0:
        won_pct = won / total_bets
        lost_pct = lost / total_bets
        pushed_pct = pushed / total_bets
    else:
        won_pct = lost_pct = pushed_pct = 0

    print(f"Total Bets:            {total_bets}")
    print(f"Won:                   {won} ({format_percentage(won_pct)})")
    print(f"Lost:                  {lost} ({format_percentage(lost_pct)})")
    print(f"Pushed:                {pushed} ({format_percentage(pushed_pct)})")

    # Pending bets
    pending = engine.db.get_pending_bets()
    print(f"Pending:               {len(pending)}")

    print(f"\nAverage Bet:           ${stats['avg_bet']:.2f}")
    print(f"Average Odds:          {stats['avg_odds']:.2f}")
    print(f"Average Edge:          {format_percentage(stats['avg_edge'])}")

    if stats["avg_clv"] != 0:
        clv_sign = "+" if stats["avg_clv"] > 0 else ""
        print(f"Average CLV:           {clv_sign}{format_percentage(stats['avg_clv'])}")
    else:
        print(f"Average CLV:           N/A (no closing lines recorded)")


def print_risk_metrics(stats: Dict[str, Any], bets: List[PaperBet]):
    """Print risk metrics"""
    print_section_header("🎯 RISK METRICS")

    max_dd = stats["max_drawdown"]
    if max_dd < 0:
        max_dd_pct = max_dd / 10000  # Assuming $10k bankroll
        print(f"Max Drawdown:          -${abs(max_dd):,.2f} ({max_dd_pct:.1%})")
    else:
        print(f"Max Drawdown:          $0.00 (0.0%)")

    # Current streak
    streak = stats["current_streak"]
    if streak > 0:
        print(f"Current Streak:        +{streak} wins 🔥")
    elif streak < 0:
        print(f"Current Streak:        {streak} losses")
    else:
        print(f"Current Streak:        None")

    # Largest win/loss
    settled_bets = [b for b in bets if b.profit_loss is not None]
    if settled_bets:
        largest_win = max(settled_bets, key=lambda b: b.profit_loss or 0)
        largest_loss = min(settled_bets, key=lambda b: b.profit_loss or 0)

        print(f"Largest Win:           ${largest_win.profit_loss:,.2f}")
        print(f"Largest Loss:          ${largest_loss.profit_loss:,.2f}")


def print_recent_bets(bets: List[PaperBet], n: int = 5):
    """Print recent bets"""
    print_section_header(f"📋 RECENT BETS (Last {n})")

    if not bets:
        print("No bets recorded yet")
        return

    recent = bets[:n]

    # Print header
    print(
        f"{'Date':<12} | {'Game':<20} | {'Side':<4} | {'Bet':<15} | {'Result':<8} | {'P/L':<12}"
    )
    print("-" * 70)

    for bet in recent:
        date_str = bet.timestamp.strftime("%Y-%m-%d")

        # Parse game ID to extract teams
        game_parts = bet.game_id.split("_vs_")
        if len(game_parts) == 2:
            home_team = game_parts[0].split("_")[-1]  # Last part before _vs_
            away_parts = game_parts[1].split("_")
            away_team = away_parts[0] if away_parts else "???"
            game_str = f"{home_team} vs {away_team}"
        else:
            game_str = bet.game_id[:20]

        side_str = bet.bet_type.value.upper()
        bet_str = f"${bet.amount:.0f} @ {bet.odds:.2f}"

        if bet.status == BetStatus.WON:
            result_str = "✓ WON"
            pl_str = f"+${bet.profit_loss:,.2f}" if bet.profit_loss else "N/A"
        elif bet.status == BetStatus.LOST:
            result_str = "✗ LOST"
            pl_str = f"-${abs(bet.profit_loss):,.2f}" if bet.profit_loss else "N/A"
        elif bet.status == BetStatus.PUSHED:
            result_str = "⊘ PUSH"
            pl_str = "$0.00"
        else:
            result_str = "⏳ PENDING"
            pl_str = "---"

        print(
            f"{date_str:<12} | {game_str:<20} | {side_str:<4} | {bet_str:<15} | {result_str:<8} | {pl_str:<12}"
        )


def print_pending_bets(bets: List[PaperBet]):
    """Print pending bets"""
    if not bets:
        return

    print_section_header(f"⏳ PENDING BETS ({len(bets)})")

    print(
        f"{'Date':<12} | {'Game':<25} | {'Side':<4} | {'Bet':<15} | {'Expected Edge':<12}"
    )
    print("-" * 70)

    for bet in bets:
        date_str = bet.timestamp.strftime("%Y-%m-%d")

        # Parse game ID
        game_parts = bet.game_id.split("_vs_")
        if len(game_parts) == 2:
            home_team = game_parts[0].split("_")[-1]
            away_parts = game_parts[1].split("_")
            away_team = away_parts[0] if away_parts else "???"
            game_str = f"{home_team} vs {away_team}"
        else:
            game_str = bet.game_id[:25]

        side_str = bet.bet_type.value.upper()
        bet_str = f"${bet.amount:.0f} @ {bet.odds:.2f}"
        edge_str = f"{bet.edge:.1%}" if bet.edge else "N/A"

        print(
            f"{date_str:<12} | {game_str:<25} | {side_str:<4} | {bet_str:<15} | {edge_str:<12}"
        )

    print(f"\nTotal pending stake: ${sum(b.amount for b in bets):,.2f}")


def export_to_csv(bets: List[PaperBet], filename: str):
    """Export bets to CSV"""
    if not bets:
        print("❌ No bets to export")
        return

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Date",
                "Game ID",
                "Bet Type",
                "Amount",
                "Odds",
                "Sim Prob",
                "Edge",
                "Status",
                "Outcome",
                "Profit/Loss",
                "Closing Odds",
                "CLV",
                "Kelly Fraction",
                "Bankroll at Bet",
                "Notes",
            ]
        )

        # Data
        for bet in bets:
            writer.writerow(
                [
                    bet.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    bet.game_id,
                    bet.bet_type.value,
                    f"{bet.amount:.2f}",
                    f"{bet.odds:.2f}",
                    f"{bet.sim_prob:.4f}" if bet.sim_prob else "",
                    f"{bet.edge:.4f}" if bet.edge else "",
                    bet.status.value,
                    bet.outcome or "",
                    f"{bet.profit_loss:.2f}" if bet.profit_loss is not None else "",
                    f"{bet.closing_odds:.2f}" if bet.closing_odds else "",
                    f"{bet.clv:.4f}" if bet.clv else "",
                    f"{bet.kelly_fraction:.4f}" if bet.kelly_fraction else "",
                    f"{bet.bankroll_at_bet:.2f}" if bet.bankroll_at_bet else "",
                    bet.notes or "",
                ]
            )

    print(f"✅ Exported {len(bets)} bets to {filename}")


def print_calibration_warning(stats: Dict[str, Any]):
    """Print warning if calibration seems off"""
    # If win rate is significantly different from expected (based on odds)
    if stats["total_bets"] >= 20:  # Need enough data
        win_rate = stats["win_rate"]
        avg_odds = stats["avg_odds"]

        # Expected win rate from odds (accounting for vig)
        expected_win_rate = 1 / avg_odds * 0.95  # Approximate vig adjustment

        diff = abs(win_rate - expected_win_rate)
        if diff > 0.15:  # More than 15% deviation
            print("\n⚠️  CALIBRATION WARNING")
            print("━" * 70)
            print(f"Actual win rate ({win_rate:.1%}) differs significantly from")
            print(f"expected win rate based on odds ({expected_win_rate:.1%}).")
            print("Consider retraining calibrator with recent data.")


def main():
    parser = argparse.ArgumentParser(description="Paper trading performance dashboard")
    parser.add_argument(
        "--db-path",
        default="data/paper_trades.db",
        help="Path to paper trading database",
    )
    parser.add_argument(
        "--detailed", action="store_true", help="Show detailed bet history"
    )
    parser.add_argument(
        "--recent", type=int, default=10, help="Number of recent bets to show"
    )
    parser.add_argument("--export", metavar="FILE", help="Export bets to CSV file")

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.db_path):
        print(f"❌ Paper trading database not found: {args.db_path}")
        print("   Run: python scripts/paper_trade_today.py")
        return 1

    # Load paper trading engine
    engine = PaperTradingEngine(db_path=args.db_path)

    # Get all bets
    all_bets = engine.db.get_all_bets()
    pending_bets = engine.db.get_pending_bets()

    # Get performance stats
    stats = engine.get_performance_stats()

    # Print dashboard
    print_header()
    print_overall_performance(engine, stats)
    print_bet_statistics(engine, stats)
    print_risk_metrics(stats, all_bets)
    print_recent_bets(all_bets, n=args.recent)

    # Show pending bets
    if pending_bets:
        print_pending_bets(pending_bets)

    # Calibration warning
    print_calibration_warning(stats)

    # Detailed history
    if args.detailed:
        print_section_header("📜 COMPLETE BET HISTORY")
        print_recent_bets(all_bets, n=len(all_bets))

    # Export to CSV
    if args.export:
        export_to_csv(all_bets, args.export)

    print("\n" + "=" * 70)
    print(f"Dashboard generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
