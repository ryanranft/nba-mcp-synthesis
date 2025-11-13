"""
Message Templates

HTML and plain text templates for betting notification emails.

Templates:
- Top Picks Email: Daily top 3 betting recommendations
- Arbitrage Alert: Time-sensitive arbitrage opportunities
- Daily Summary: Performance and opportunity overview
- Weekly Report: Weekly performance summary

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def format_top_picks_email(
    picks: List[Dict[str, Any]], summary: Dict[str, Any], bankroll: float = 10000.0
) -> Tuple[str, str, str]:
    """
    Format top betting picks as email

    Args:
        picks: List of top picks from OddsIntegration.get_top_picks()
        summary: Summary dict from generate_betting_recommendations()
        bankroll: Current bankroll

    Returns:
        Tuple of (subject, html_body, plain_text_body)
    """
    today = datetime.now().strftime("%A, %B %d, %Y")
    subject = f"🏀 NBA Betting Picks - {datetime.now().strftime('%B %d, %Y')}"

    # HTML body
    html = f"""
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #34a853;
            margin-top: 30px;
        }}
        .pick {{
            background-color: #f8f9fa;
            border-left: 4px solid #1a73e8;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .pick-header {{
            font-size: 18px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 10px;
        }}
        .pick-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .metric {{
            background-color: white;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
        }}
        .edge-high {{ color: #34a853; }}
        .edge-medium {{ color: #fbbc04; }}
        .edge-low {{ color: #ea4335; }}
        .summary {{
            background-color: #e8f0fe;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffbb00;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA Betting Recommendations</h1>
        <p><strong>Date:</strong> {today}</p>
        <p><strong>Bankroll:</strong> ${bankroll:,.0f}</p>

        <h2>Top {len(picks)} Picks for Today</h2>
"""

    # Add each pick
    for i, pick in enumerate(picks, 1):
        edge_class = (
            "edge-high"
            if pick["edge"] > 0.07
            else ("edge-medium" if pick["edge"] > 0.04 else "edge-low")
        )
        game_time = pick.get("game_time", "TBD")

        html += f"""
        <div class="pick">
            <div class="pick-header">
                #{i}. {pick['matchup']}
                <span style="float: right; font-size: 14px; color: #666;">{game_time}</span>
            </div>
            <div style="font-size: 16px; margin: 10px 0;">
                <strong>BET:</strong> ${pick['recommended_stake']:.0f} on <strong>{pick['bet_side']}</strong> at {pick['odds_american']:+.0f}
            </div>
            <div class="pick-details">
                <div class="metric">
                    <div class="metric-label">Edge</div>
                    <div class="metric-value {edge_class}">{pick['edge']:.1%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">ML Probability</div>
                    <div class="metric-value">{pick['ml_prob']:.1%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Kelly %</div>
                    <div class="metric-value">{pick['kelly_fraction']:.2%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Confidence</div>
                    <div class="metric-value">{pick.get('confidence', 0):.0%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Expected Value</div>
                    <div class="metric-value">${pick['ev'] * pick['recommended_stake']:.2f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Bookmaker</div>
                    <div class="metric-value" style="font-size: 14px;">{pick['bookmaker']}</div>
                </div>
            </div>
        </div>
"""

    # Add summary
    html += f"""
        <h2>Portfolio Summary</h2>
        <div class="summary">
            <div class="summary-grid">
                <div class="metric">
                    <div class="metric-label">Total Bets</div>
                    <div class="metric-value">{summary['total_bets']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Stake</div>
                    <div class="metric-value">${summary['total_stake']:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Bankroll Exposure</div>
                    <div class="metric-value">{summary['bankroll_exposure']:.1%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Expected Value</div>
                    <div class="metric-value" style="color: #34a853;">${summary['total_ev']:,.2f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Average Edge</div>
                    <div class="metric-value">{summary['avg_edge']:.2%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Average Kelly</div>
                    <div class="metric-value">{summary['avg_kelly']:.2%}</div>
                </div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ Risk Management:</strong> These recommendations are based on statistical models and should not be the sole basis for betting decisions. Always bet responsibly and never risk more than you can afford to lose.
        </div>

        <div class="footer">
            🤖 Automated by NBA MCP Synthesis<br>
            Powered by Claude Code | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

    # Plain text version
    plain = f"""
NBA BETTING RECOMMENDATIONS
{today}
Bankroll: ${bankroll:,.0f}

TOP {len(picks)} PICKS FOR TODAY
{'='*60}

"""

    for i, pick in enumerate(picks, 1):
        game_time = pick.get("game_time", "TBD")
        plain += f"""
#{i}. {pick['matchup']} - {game_time}
BET: ${pick['recommended_stake']:.0f} on {pick['bet_side']} at {pick['odds_american']:+.0f}

Edge: {pick['edge']:.2%}  |  ML Prob: {pick['ml_prob']:.1%}  |  Kelly: {pick['kelly_fraction']:.2%}
Confidence: {pick.get('confidence', 0):.0%}  |  EV: ${pick['ev'] * pick['recommended_stake']:.2f}
Bookmaker: {pick['bookmaker']}

"""

    plain += f"""
PORTFOLIO SUMMARY
{'='*60}
Total Bets: {summary['total_bets']}
Total Stake: ${summary['total_stake']:,.0f} ({summary['bankroll_exposure']:.1%} of bankroll)
Expected Value: ${summary['total_ev']:,.2f}
Average Edge: {summary['avg_edge']:.2%}
Average Kelly: {summary['avg_kelly']:.2%}

---
🤖 Automated by NBA MCP Synthesis
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return subject, html, plain


def format_arbitrage_alert(arb: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Format arbitrage opportunity as urgent email

    Args:
        arb: Arbitrage opportunity dict with keys:
            - matchup: Game matchup
            - market_type: Market type
            - bookmaker_a, bookmaker_b: Bookmakers
            - odds_a, odds_b: Odds
            - arb_percentage: Guaranteed profit %
            - bet_amount_a, bet_amount_b: Recommended stakes
            - guaranteed_profit: Profit amount

    Returns:
        Tuple of (subject, html_body, plain_text_body)
    """
    subject = (
        f"🚨 ARBITRAGE ALERT: {arb['matchup']} - {arb['arb_percentage']:.2%} Profit"
    )

    html = f"""
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff3cd;
        }}
        .alert {{
            background-color: white;
            border: 3px solid #ea4335;
            border-radius: 8px;
            padding: 25px;
        }}
        h1 {{
            color: #ea4335;
            text-align: center;
            font-size: 28px;
            margin-bottom: 20px;
        }}
        .game {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .arbitrage-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .arbitrage-table th {{
            background-color: #1a73e8;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .arbitrage-table td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        .profit {{
            background-color: #34a853;
            color: white;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .urgency {{
            background-color: #ea4335;
            color: white;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="alert">
        <h1>🚨 LIVE ARBITRAGE OPPORTUNITY</h1>

        <div class="game">
            {arb['matchup']}
        </div>

        <table class="arbitrage-table">
            <tr>
                <th>Bookmaker</th>
                <th>Side</th>
                <th>Odds</th>
                <th>Stake</th>
            </tr>
            <tr>
                <td><strong>{arb['bookmaker_a']}</strong></td>
                <td>{arb['side_a']}</td>
                <td>{arb['odds_a']:+.0f}</td>
                <td>${arb['bet_amount_a']:,.0f}</td>
            </tr>
            <tr>
                <td><strong>{arb['bookmaker_b']}</strong></td>
                <td>{arb['side_b']}</td>
                <td>{arb['odds_b']:+.0f}</td>
                <td>${arb['bet_amount_b']:,.0f}</td>
            </tr>
        </table>

        <div class="profit">
            GUARANTEED PROFIT: ${arb['guaranteed_profit']:,.2f} ({arb['arb_percentage']:.2%})
        </div>

        <div class="urgency">
            ⏰ TIME-SENSITIVE: Arbitrage opportunities close quickly. Act within 5 minutes.
        </div>

        <div class="footer">
            Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            🤖 NBA MCP Synthesis Arbitrage Scanner
        </div>
    </div>
</body>
</html>
"""

    plain = f"""
🚨 ARBITRAGE OPPORTUNITY DETECTED 🚨

Game: {arb['matchup']}
Market: {arb['market_type']}

BOOKMAKER A: {arb['bookmaker_a']}
Side: {arb['side_a']}
Odds: {arb['odds_a']:+.0f}
Stake: ${arb['bet_amount_a']:,.0f}

BOOKMAKER B: {arb['bookmaker_b']}
Side: {arb['side_b']}
Odds: {arb['odds_b']:+.0f}
Stake: ${arb['bet_amount_b']:,.0f}

GUARANTEED PROFIT: ${arb['guaranteed_profit']:,.2f} ({arb['arb_percentage']:.2%})

⏰ TIME-SENSITIVE: Act within 5 minutes

---
Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 NBA MCP Synthesis
"""

    return subject, html, plain


def format_daily_summary(
    stats: Dict[str, Any], picks_count: int = 0, arb_count: int = 0
) -> Tuple[str, str, str]:
    """
    Format daily summary email

    Args:
        stats: Daily statistics dict
        picks_count: Number of picks generated
        arb_count: Number of arbitrage opportunities found

    Returns:
        Tuple of (subject, html_body, plain_text_body)
    """
    subject = f"📊 Daily Summary - {datetime.now().strftime('%B %d, %Y')}"

    html = f"""
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ color: #1a73e8; }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1a73e8;
        }}
    </style>
</head>
<body>
    <h1>📊 Daily Summary</h1>
    <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>

    <div class="stat-grid">
        <div class="stat-box">
            <div class="stat-label">Picks Generated</div>
            <div class="stat-value">{picks_count}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Arbitrage Found</div>
            <div class="stat-value">{arb_count}</div>
        </div>
    </div>

    <p>Have a great day!</p>
    <p style="font-size: 12px; color: #666;">🤖 NBA MCP Synthesis</p>
</body>
</html>
"""

    plain = f"""
DAILY SUMMARY - {datetime.now().strftime('%B %d, %Y')}

Picks Generated: {picks_count}
Arbitrage Opportunities: {arb_count}

---
🤖 NBA MCP Synthesis
"""

    return subject, html, plain


if __name__ == "__main__":
    # Test templates
    print("Testing message templates...\n")

    # Test top picks
    mock_picks = [
        {
            "matchup": "Lakers vs Warriors",
            "bet_side": "Lakers",
            "odds_american": -110,
            "recommended_stake": 183.0,
            "edge": 0.107,
            "ml_prob": 0.652,
            "kelly_fraction": 0.032,
            "confidence": 0.87,
            "ev": 0.107,
            "bookmaker": "DraftKings",
            "game_time": "7:00 PM ET",
        }
    ]

    mock_summary = {
        "total_bets": 3,
        "total_stake": 456.0,
        "total_ev": 37.42,
        "avg_edge": 0.074,
        "avg_kelly": 0.025,
        "bankroll_exposure": 0.091,
    }

    subject, html, plain = format_top_picks_email(mock_picks, mock_summary, 5000.0)
    print(f"✅ Top Picks Email - Subject: {subject}")
    print(f"   HTML length: {len(html)} chars")
    print(f"   Plain length: {len(plain)} chars")
    print()

    # Test arbitrage alert
    mock_arb = {
        "matchup": "Heat vs Nuggets",
        "market_type": "h2h",
        "bookmaker_a": "DraftKings",
        "bookmaker_b": "FanDuel",
        "side_a": "Heat",
        "side_b": "Nuggets",
        "odds_a": 195,
        "odds_b": -180,
        "arb_percentage": 0.024,
        "bet_amount_a": 500,
        "bet_amount_b": 512,
        "guaranteed_profit": 24.0,
    }

    subject, html, plain = format_arbitrage_alert(mock_arb)
    print(f"✅ Arbitrage Alert - Subject: {subject}")
    print(f"   HTML length: {len(html)} chars")
    print()

    print("✅ All templates tested successfully!")
