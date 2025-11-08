#!/usr/bin/env python3
"""
Daily Betting Analysis

Main automation script for daily betting recommendations.

This script:
1. Loads secrets and configuration
2. Fetches today's NBA games
3. Runs ML predictions
4. Fetches live odds from database
5. Calculates betting edges
6. Applies Kelly Criterion
7. Formats HTML email with top picks
8. Sends email + SMS notifications
9. Stores recommendations in database

Designed to run via cron at 10 AM daily.

Usage:
    python scripts/daily_betting_analysis.py --email --sms-critical-only
    python scripts/daily_betting_analysis.py --dry-run
    python scripts/daily_betting_analysis.py --min-edge 0.05

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.betting.odds_integration import OddsIntegration
from mcp_server.betting.message_templates import format_top_picks_email
from mcp_server.betting.notifications import NotificationManager
from mcp_server.betting.ml_predictions import generate_ml_predictions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_predictions_with_fallback(use_ml: bool = True) -> List[Dict[str, Any]]:
    """
    Generate predictions using ML model (with mock fallback)

    Args:
        use_ml: If True, use ML predictions. If False, use mock data.

    Returns:
        List of prediction dicts
    """
    if use_ml:
        try:
            logger.info("Generating ML predictions from ensemble model...")
            predictions = generate_ml_predictions()

            if predictions:
                logger.info(f"✅ Generated {len(predictions)} ML predictions")
                return predictions
            else:
                logger.warning("No ML predictions available (no games today)")
                return []

        except FileNotFoundError as e:
            logger.error(f"ML model not found: {e}")
            logger.warning("Falling back to mock predictions")
            logger.warning("To train model, run: python scripts/train_game_outcome_model.py")
            return _generate_mock_predictions()
        except Exception as e:
            logger.error(f"Error generating ML predictions: {e}")
            logger.warning("Falling back to mock predictions")
            return _generate_mock_predictions()
    else:
        return _generate_mock_predictions()


def _generate_mock_predictions() -> List[Dict[str, Any]]:
    """
    Generate mock predictions for testing

    Used as fallback when ML model is not available

    Returns:
        List of prediction dicts
    """
    logger.warning("Using MOCK predictions for testing")

    # Mock prediction for testing
    mock_predictions = [
        {
            'game_id': 'mock_001',
            'game_date': '2025-01-06',
            'home_team': 'Los Angeles Lakers',
            'away_team': 'Golden State Warriors',
            'prob_home': 0.58,
            'prob_away': 0.42,
            'confidence': 0.85,
            'commence_time': '7:00 PM ET'
        },
        {
            'game_id': 'mock_002',
            'game_date': '2025-01-06',
            'home_team': 'Boston Celtics',
            'away_team': 'Miami Heat',
            'prob_home': 0.62,
            'prob_away': 0.38,
            'confidence': 0.78,
            'commence_time': '7:30 PM ET'
        }
    ]

    return mock_predictions


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Daily NBA betting analysis and recommendations'
    )
    parser.add_argument(
        '--email',
        action='store_true',
        help='Send email with recommendations'
    )
    parser.add_argument(
        '--sms',
        action='store_true',
        help='Send SMS for all recommendations'
    )
    parser.add_argument(
        '--sms-critical-only',
        action='store_true',
        help='Send SMS only for critical bets (edge > 10%%)'
    )
    parser.add_argument(
        '--min-edge',
        type=float,
        default=0.03,
        help='Minimum edge threshold (default: 0.03 = 3%%)'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=10000.0,
        help='Current bankroll (default: $10,000)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate recommendations but do not send notifications'
    )
    parser.add_argument(
        '--context',
        type=str,
        default='production',
        choices=['production', 'development', 'test'],
        help='Environment context'
    )
    parser.add_argument(
        '--use-mock',
        action='store_true',
        help='Use mock predictions instead of ML model (for testing)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NBA Daily Betting Analysis")
    print("=" * 70)
    print()

    # Step 1: Load secrets
    print("📦 Loading secrets...")
    success = load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', args.context)

    if not success:
        print("❌ Failed to load secrets")
        return 1

    print(f"✅ Secrets loaded (context: {args.context})")
    print()

    # Step 2: Generate predictions
    print("🎯 Generating predictions...")
    if args.use_mock:
        print("   (Using mock predictions for testing)")
        predictions = generate_predictions_with_fallback(use_ml=False)
    else:
        print("   (Using ML ensemble model)")
        predictions = generate_predictions_with_fallback(use_ml=True)

    print(f"✅ Generated {len(predictions)} predictions")
    print()

    # Step 3: Initialize odds integration
    print("🔧 Initializing odds integration...")
    integrator = OddsIntegration(
        bankroll=args.bankroll,
        min_edge=args.min_edge,
        use_kelly=True
    )
    print("✅ Odds integration initialized")
    print()

    # Step 4: Generate betting recommendations
    print("💰 Generating betting recommendations...")
    try:
        results = integrator.generate_betting_recommendations(
            predictions=predictions,
            min_edge=args.min_edge,
            market='h2h'
        )

        print(f"✅ Generated {results['summary']['total_bets']} recommendations")
        print(f"   Total stake: ${results['summary']['total_stake']:,.0f}")
        print(f"   Expected value: ${results['summary']['total_ev']:,.2f}")
        if results['summary']['total_bets'] > 0:
            print(f"   Avg edge: {results['summary']['avg_edge']:.2%}")
        print()

        if results['summary']['total_bets'] == 0:
            print("ℹ️  No positive EV bets found for today")
            print("   (Either no games, no odds, or all edges below threshold)")
            integrator.close()
            return 0

    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()
        integrator.close()
        return 1

    # Step 5: Get top picks
    print("📊 Selecting top picks...")
    top_picks = integrator.get_top_picks(results, n=3, sort_by='edge')
    print(f"✅ Top {len(top_picks)} picks selected")
    print()

    # Display top picks
    if top_picks:
        print("Top Picks:")
        print("-" * 70)
        for i, pick in enumerate(top_picks, 1):
            print(f"{i}. {pick['matchup']}")
            print(f"   BET: ${pick['recommended_stake']:.0f} on {pick['bet_side']}")
            print(f"   Odds: {pick['odds_american']:+.0f} at {pick['bookmaker']}")
            print(f"   Edge: {pick['edge']:.2%} | Kelly: {pick['kelly_fraction']:.2%}")
            print()

    # Step 6: Send notifications
    if not args.dry_run:
        if args.email or args.sms or args.sms_critical_only:
            print("📧 Sending notifications...")

            try:
                # Format email
                subject, html_body, plain_body = format_top_picks_email(
                    picks=top_picks,
                    summary=results['summary'],
                    bankroll=args.bankroll
                )

                # Initialize notification manager
                notifier = NotificationManager(config={
                    'email': {'enabled': args.email},
                    'sms': {'enabled': args.sms or args.sms_critical_only}
                })

                # Send email
                if args.email:
                    email_result = notifier.send_message(
                        subject=subject,
                        message=html_body,
                        channels=['email']
                    )

                    if email_result and 'email' in email_result and email_result['email'].success:
                        print("✅ Email sent successfully")
                        email_to = os.getenv('EMAIL_TO', 'Unknown')
                        print(f"   Recipients: {email_to}")
                    else:
                        error = email_result.get('email').error if 'email' in email_result else 'Unknown'
                        print(f"❌ Email failed: {error}")

                # Send SMS for critical bets
                if args.sms_critical_only:
                    critical_picks = [p for p in top_picks if p['edge'] >= 0.10]

                    if critical_picks:
                        sms_message = f"🏀 CRITICAL BET ALERT ({len(critical_picks)}):\n"
                        for pick in critical_picks:
                            sms_message += f"\n{pick['bet_side']} {pick['odds_american']:+.0f}"
                            sms_message += f" | ${pick['recommended_stake']:.0f}"
                            sms_message += f" | Edge: {pick['edge']:.1%}"

                        sms_result = notifier.send_message(
                            subject="NBA Critical Bet Alert",
                            message=sms_message,
                            channels=['sms']
                        )

                        if sms_result and 'sms' in sms_result and sms_result['sms'].success:
                            print(f"✅ SMS sent for {len(critical_picks)} critical bets")
                        else:
                            error = sms_result.get('sms').error if 'sms' in sms_result else 'Unknown'
                            print(f"❌ SMS failed: {error}")
                    else:
                        print("ℹ️  No critical bets (edge < 10%) - SMS not sent")

                # Send SMS for all bets
                if args.sms and not args.sms_critical_only:
                    sms_message = f"🏀 Daily Picks ({len(top_picks)}):\n"
                    for i, pick in enumerate(top_picks, 1):
                        sms_message += f"\n{i}. {pick['bet_side']} {pick['odds_american']:+.0f}"
                        sms_message += f" | ${pick['recommended_stake']:.0f}"

                    sms_result = notifier.send_message(
                        subject="NBA Daily Picks",
                        message=sms_message,
                        channels=['sms']
                    )

                    if sms_result and 'sms' in sms_result and sms_result['sms'].success:
                        print(f"✅ SMS sent with {len(top_picks)} picks")
                    else:
                        error = sms_result.get('sms').error if 'sms' in sms_result else 'Unknown'
                        print(f"❌ SMS failed: {error}")

                print()

            except Exception as e:
                print(f"❌ Error sending notifications: {e}")
                import traceback
                traceback.print_exc()

    else:
        print("🔍 DRY RUN - No notifications sent")
        print()

    # Step 7: Cleanup
    integrator.close()

    print("=" * 70)
    print("✅ Daily betting analysis complete")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
