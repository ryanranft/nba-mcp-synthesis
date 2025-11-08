#!/usr/bin/env python3
"""
Automated Daily Report Generator

Generates comprehensive daily reports for NBA betting system including:
- Performance summary (ROI, win rate, Sharpe ratio)
- Recent bets with outcomes
- Alert summary
- Calibration quality metrics
- Risk metrics

Can be run manually or scheduled via cron for automated delivery.

Usage:
------
    # Generate report (print to console)
    python scripts/generate_daily_report.py

    # Send via email
    python scripts/generate_daily_report.py --email

    # Send via Slack
    python scripts/generate_daily_report.py --slack

    # Send via both channels
    python scripts/generate_daily_report.py --email --slack

    # Custom date range
    python scripts/generate_daily_report.py --days 7

    # Save to file
    python scripts/generate_daily_report.py --output daily_report.html

Cron Setup:
-----------
    # Send daily report at 9 AM via email
    0 9 * * * cd /path/to/nba-mcp-synthesis && python scripts/generate_daily_report.py --email

    # Send weekly summary on Mondays
    0 9 * * 1 cd /path/to/nba-mcp-synthesis && python scripts/generate_daily_report.py --days 7 --slack

Environment Variables:
----------------------
    SMTP_HOST: SMTP server for email
    SMTP_PORT: SMTP port (default: 587)
    SMTP_USER: SMTP username
    SMTP_PASSWORD: SMTP password
    EMAIL_FROM: Sender email
    EMAIL_TO: Recipient emails (comma-separated)
    SLACK_WEBHOOK_URL: Slack webhook URL
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
import argparse
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.betting.paper_trading import (
    PaperTradingEngine,
    BetStatus
)
from mcp_server.betting.probability_calibration import SimulationCalibrator
from mcp_server.betting.alert_system import AlertSystem, AlertLevel
from mcp_server.betting.notifications import NotificationManager


# ============================================================================
# Report Generation Functions
# ============================================================================

def generate_performance_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate performance summary section

    Args:
        stats: Performance statistics from PaperTradingEngine

    Returns:
        Summary dict
    """
    return {
        'bankroll': stats['bankroll'],
        'bankroll_change': stats['total_profit_loss'],
        'bankroll_change_pct': stats['bankroll_change_pct'],
        'roi': stats['roi'],
        'win_rate': stats['win_rate'],
        'sharpe_ratio': stats['sharpe_ratio'],
        'total_bets': stats['total_bets'],
        'total_won': stats['total_won'],
        'total_lost': stats['total_lost'],
        'total_staked': stats['total_staked'],
        'avg_bet': stats['avg_bet'],
        'avg_edge': stats['avg_edge'],
        'avg_clv': stats['avg_clv'],
        'max_drawdown': stats['max_drawdown'],
        'current_streak': stats['current_streak']
    }


def generate_recent_bets_summary(all_bets: List[Any], days: int = 1) -> List[Dict[str, Any]]:
    """
    Generate recent bets summary

    Args:
        all_bets: List of all bets
        days: Number of days to look back

    Returns:
        List of bet summaries
    """
    cutoff = datetime.now() - timedelta(days=days)

    recent_bets = [
        bet for bet in all_bets
        if bet.timestamp >= cutoff
    ]

    # Sort by timestamp descending
    recent_bets = sorted(recent_bets, key=lambda x: x.timestamp, reverse=True)

    return [
        {
            'timestamp': bet.timestamp,
            'game_id': bet.game_id,
            'bet_type': bet.bet_type.value,
            'amount': bet.amount,
            'odds': bet.odds,
            'edge': bet.edge,
            'status': bet.status.value,
            'profit_loss': bet.profit_loss if bet.profit_loss else 0,
            'clv': bet.clv if bet.clv else 0
        }
        for bet in recent_bets
    ]


def generate_alert_summary(alert_system: AlertSystem, hours: int = 24) -> Dict[str, Any]:
    """
    Generate alert summary

    Args:
        alert_system: AlertSystem instance
        hours: Hours to look back

    Returns:
        Alert summary dict
    """
    return alert_system.get_alert_summary(hours=hours)


def generate_calibration_summary(calibrator: SimulationCalibrator) -> Dict[str, Any]:
    """
    Generate calibration summary

    Args:
        calibrator: SimulationCalibrator instance

    Returns:
        Calibration summary dict
    """
    brier = calibrator.calibration_quality(method='brier')
    log_loss = calibrator.calibration_quality(method='log_loss')

    num_records = 0
    if calibrator.calibration_db:
        num_records = len(calibrator.calibration_db.get_all_records())

    return {
        'brier_score': brier,
        'log_loss': log_loss,
        'num_predictions': num_records,
        'quality': 'Excellent' if brier < 0.10 else 'Good' if brier < 0.15 else 'Acceptable' if brier < 0.20 else 'Poor'
    }


# ============================================================================
# Report Formatting Functions
# ============================================================================

def format_report_plain_text(
    performance: Dict[str, Any],
    recent_bets: List[Dict[str, Any]],
    alerts: Dict[str, Any],
    calibration: Dict[str, Any],
    days: int = 1
) -> str:
    """
    Format report as plain text

    Args:
        performance: Performance summary
        recent_bets: Recent bets
        alerts: Alert summary
        calibration: Calibration summary
        days: Report period in days

    Returns:
        Plain text report
    """
    report = []

    # Header
    report.append("=" * 70)
    report.append("NBA BETTING SYSTEM - DAILY REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Period: Last {days} day(s)")
    report.append("=" * 70)
    report.append("")

    # Alert Status
    report.append("ALERT STATUS")
    report.append("-" * 70)
    if alerts['has_critical']:
        report.append(f"🔴 CRITICAL ALERTS: {alerts['critical']}")
    if alerts['has_warnings']:
        report.append(f"🟡 WARNINGS: {alerts['warnings']}")
    if not alerts['has_critical'] and not alerts['has_warnings']:
        report.append("✅ All systems healthy")
    report.append("")

    # Performance Summary
    report.append("PERFORMANCE SUMMARY")
    report.append("-" * 70)
    report.append(f"Current Bankroll:       ${performance['bankroll']:,.2f}")
    report.append(f"Profit/Loss:            ${performance['bankroll_change']:,.2f} ({performance['bankroll_change_pct']*100:+.1f}%)")
    report.append(f"ROI:                    {performance['roi']*100:.1f}%")
    report.append(f"Win Rate:               {performance['win_rate']*100:.1f}%")
    report.append(f"Sharpe Ratio:           {performance['sharpe_ratio']:.2f}")
    report.append("")

    # Bet Statistics
    report.append("BET STATISTICS")
    report.append("-" * 70)
    report.append(f"Total Bets:             {performance['total_bets']}")
    report.append(f"Won / Lost:             {performance['total_won']} / {performance['total_lost']}")
    report.append(f"Total Staked:           ${performance['total_staked']:,.2f}")
    report.append(f"Average Bet Size:       ${performance['avg_bet']:,.2f}")
    report.append(f"Average Edge:           {performance['avg_edge']*100:.1f}%")
    report.append(f"Average CLV:            {performance['avg_clv']*100:+.1f}%")
    report.append("")

    # Risk Metrics
    report.append("RISK METRICS")
    report.append("-" * 70)
    max_dd_pct = abs(performance['max_drawdown']) / performance['bankroll'] if performance['bankroll'] > 0 else 0
    report.append(f"Max Drawdown:           {max_dd_pct*100:.1f}%")
    report.append(f"Current Streak:         {performance['current_streak']:+d}")
    report.append("")

    # Calibration Quality
    report.append("CALIBRATION QUALITY")
    report.append("-" * 70)
    report.append(f"Brier Score:            {calibration['brier_score']:.4f} ({calibration['quality']})")
    report.append(f"Log Loss:               {calibration['log_loss']:.4f}")
    report.append(f"Total Predictions:      {calibration['num_predictions']}")
    report.append("")

    # Recent Bets
    if recent_bets:
        report.append(f"RECENT BETS (Last {days} day(s))")
        report.append("-" * 70)

        for bet in recent_bets[:10]:  # Show max 10
            status_icon = "✅" if bet['status'] == 'won' else "❌" if bet['status'] == 'lost' else "⏳"
            report.append(
                f"{status_icon} {bet['timestamp'].strftime('%m-%d %H:%M')} | "
                f"{bet['game_id'][:20]:20s} | "
                f"{bet['bet_type']:4s} | "
                f"${bet['amount']:6.2f} @ {bet['odds']:.2f} | "
                f"Edge: {bet['edge']*100:4.1f}% | "
                f"P/L: ${bet['profit_loss']:+7.2f}"
            )

        if len(recent_bets) > 10:
            report.append(f"... and {len(recent_bets) - 10} more bets")
        report.append("")

    # Footer
    report.append("=" * 70)
    report.append("This is an automated report from your NBA betting system.")
    report.append("=" * 70)

    return "\n".join(report)


def format_report_html(
    performance: Dict[str, Any],
    recent_bets: List[Dict[str, Any]],
    alerts: Dict[str, Any],
    calibration: Dict[str, Any],
    days: int = 1
) -> str:
    """
    Format report as HTML

    Args:
        performance: Performance summary
        recent_bets: Recent bets
        alerts: Alert summary
        calibration: Calibration summary
        days: Report period in days

    Returns:
        HTML report
    """
    # Determine alert color
    if alerts['has_critical']:
        alert_color = '#d9534f'
        alert_status = f"🔴 CRITICAL: {alerts['critical']} alerts"
    elif alerts['has_warnings']:
        alert_color = '#f0ad4e'
        alert_status = f"🟡 WARNING: {alerts['warnings']} alerts"
    else:
        alert_color = '#5cb85c'
        alert_status = "✅ All systems healthy"

    # ROI color
    roi_color = '#5cb85c' if performance['roi'] > 0 else '#d9534f'

    # Calibration color
    cal_color = '#5cb85c' if calibration['brier_score'] < 0.15 else '#f0ad4e' if calibration['brier_score'] < 0.20 else '#d9534f'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #555;
                margin-top: 30px;
                border-bottom: 2px solid #ddd;
                padding-bottom: 5px;
            }}
            .alert-box {{
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                background-color: {alert_color};
                color: white;
                font-weight: bold;
            }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .metric-card {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #4CAF50;
            }}
            .metric-label {{
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .won {{ color: #5cb85c; }}
            .lost {{ color: #d9534f; }}
            .pending {{ color: #f0ad4e; }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ddd;
                color: #666;
                font-size: 12px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏀 NBA Betting System - Daily Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Period:</strong> Last {days} day(s)</p>

            <div class="alert-box">
                {alert_status}
            </div>

            <h2>📊 Performance Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Current Bankroll</div>
                    <div class="metric-value">${performance['bankroll']:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit/Loss</div>
                    <div class="metric-value" style="color: {roi_color};">
                        ${performance['bankroll_change']:+,.2f}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">ROI</div>
                    <div class="metric-value" style="color: {roi_color};">
                        {performance['roi']*100:.1f}%
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{performance['win_rate']*100:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{performance['sharpe_ratio']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg CLV</div>
                    <div class="metric-value">{performance['avg_clv']*100:+.1f}%</div>
                </div>
            </div>

            <h2>🎯 Calibration Quality</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Brier Score</div>
                    <div class="metric-value" style="color: {cal_color};">
                        {calibration['brier_score']:.4f}
                    </div>
                    <div style="font-size: 12px; margin-top: 5px;">{calibration['quality']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Log Loss</div>
                    <div class="metric-value">{calibration['log_loss']:.4f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Predictions</div>
                    <div class="metric-value">{calibration['num_predictions']}</div>
                </div>
            </div>

            <h2>🎲 Recent Bets</h2>
    """

    if recent_bets:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Odds</th>
                        <th>Status</th>
                        <th>P/L</th>
                    </tr>
                </thead>
                <tbody>
        """

        for bet in recent_bets[:20]:  # Show max 20
            status_class = bet['status']
            status_icon = "✅" if bet['status'] == 'won' else "❌" if bet['status'] == 'lost' else "⏳"

            html += f"""
                    <tr>
                        <td>{bet['timestamp'].strftime('%m-%d %H:%M')}</td>
                        <td>{bet['game_id'][:30]}</td>
                        <td>{bet['bet_type']}</td>
                        <td>${bet['amount']:.2f}</td>
                        <td>{bet['odds']:.2f}</td>
                        <td class="{status_class}">{status_icon} {bet['status']}</td>
                        <td class="{'won' if bet['profit_loss'] > 0 else 'lost'}">
                            ${bet['profit_loss']:+.2f}
                        </td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        """
    else:
        html += "<p>No bets placed in this period.</p>"

    html += f"""
            <div class="footer">
                This is an automated report from your NBA betting system.<br>
                For questions or issues, check the monitoring dashboard.
            </div>
        </div>
    </body>
    </html>
    """

    return html


# ============================================================================
# Main Report Generation
# ============================================================================

def generate_report(
    days: int = 1,
    output_format: Literal['text', 'html', 'both'] = 'both'
) -> Dict[str, str]:
    """
    Generate daily report

    Args:
        days: Number of days to include in report
        output_format: 'text', 'html', or 'both'

    Returns:
        Dict with 'text' and/or 'html' keys
    """
    # Load data
    engine = PaperTradingEngine(
        starting_bankroll=10000,
        db_path="data/paper_trades.db"
    )

    calibrator = SimulationCalibrator(db_path="data/calibration.db")
    alert_system = AlertSystem(db_path="data/alerts.db")

    # Generate summaries
    stats = engine.get_performance_stats()
    performance = generate_performance_summary(stats)

    all_bets = engine.db.get_all_bets()
    recent_bets = generate_recent_bets_summary(all_bets, days=days)

    alerts = generate_alert_summary(alert_system, hours=days*24)
    calibration = generate_calibration_summary(calibrator)

    # Format report
    reports = {}

    if output_format in ['text', 'both']:
        reports['text'] = format_report_plain_text(
            performance, recent_bets, alerts, calibration, days
        )

    if output_format in ['html', 'both']:
        reports['html'] = format_report_html(
            performance, recent_bets, alerts, calibration, days
        )

    return reports


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(
        description="Generate automated daily report for NBA betting system"
    )

    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days to include in report (default: 1)'
    )

    parser.add_argument(
        '--email',
        action='store_true',
        help='Send report via email'
    )

    parser.add_argument(
        '--slack',
        action='store_true',
        help='Send report via Slack'
    )

    parser.add_argument(
        '--sms',
        action='store_true',
        help='Send report via SMS/text message'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Save report to file (HTML format)'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'html', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    args = parser.parse_args()

    # Generate report
    print(f"📊 Generating {args.days}-day report...")
    reports = generate_report(days=args.days, output_format=args.format)

    # Print to console
    if 'text' in reports:
        print("\n" + reports['text'])

    # Save to file
    if args.output:
        if 'html' not in reports:
            print("❌ HTML format not generated. Use --format html or both")
        else:
            output_path = Path(args.output)
            output_path.write_text(reports['html'])
            print(f"\n✅ Report saved to: {output_path}")

    # Send via email/Slack/SMS
    if args.email or args.slack or args.sms:
        print("\n📨 Sending notifications...")

        channels = []
        if args.email:
            channels.append('email')
        if args.slack:
            channels.append('slack')
        if args.sms:
            channels.append('sms')

        try:
            notifier = NotificationManager(config={
                'email': {
                    'enabled': args.email,
                },
                'slack': {
                    'enabled': args.slack,
                },
                'sms': {
                    'enabled': args.sms,
                }
            })

            subject = f"NBA Betting System - {args.days}-Day Report"

            # Send HTML via email, text via Slack/SMS
            results = {}

            if args.email and 'email' in notifier.notifiers:
                result = notifier.notifiers['email'].send(
                    subject=subject,
                    body=reports.get('html', reports.get('text', '')),
                    html='html' in reports
                )
                results['email'] = result

            if args.slack and 'slack' in notifier.notifiers:
                result = notifier.notifiers['slack'].send(
                    message=reports.get('text', ''),
                    title=subject
                )
                results['slack'] = result

            if args.sms and 'sms' in notifier.notifiers:
                # For SMS, send a short summary
                from mcp_server.betting.paper_trading import PaperTradingEngine
                engine = PaperTradingEngine(starting_bankroll=10000, db_path="data/paper_trades.db")
                stats = engine.get_performance_stats()
                sms_text = f"NBA Betting {args.days}d: ROI {stats['roi']*100:.1f}%, WR {stats['win_rate']*100:.1f}%, Bankroll ${stats['bankroll']:,.0f}"
                result = notifier.notifiers['sms'].send(sms_text)
                results['sms'] = result

            # Print results
            for channel, result in results.items():
                if result.success:
                    print(f"  ✅ {channel}: Sent successfully")
                else:
                    print(f"  ❌ {channel}: Failed - {result.error}")

        except Exception as e:
            print(f"❌ Failed to send notifications: {e}")
            print("💡 Make sure environment variables are set (SMTP_HOST, SLACK_WEBHOOK_URL, TWILIO credentials, etc.)")


if __name__ == "__main__":
    main()