"""
Arbitrage Detector

Detects guaranteed profit opportunities (arbitrage) across multiple bookmakers.

Arbitrage exists when you can bet on all possible outcomes of an event and guarantee
a profit regardless of the result by exploiting price differences between bookmakers.

Example:
    DraftKings: Lakers +195 (implied prob: 33.9%)
    FanDuel: Warriors -180 (implied prob: 64.3%)
    Total implied prob: 98.2% < 100% → 1.8% arbitrage profit guaranteed!

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
import math

from mcp_server.connectors.odds_database_connector import OddsDatabaseConnector
from mcp_server.betting.odds_utilities import OddsUtilities

logger = logging.getLogger(__name__)


class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""

    def __init__(
        self,
        event_id: str,
        matchup: str,
        market_type: str,
        bookmaker_a: str,
        bookmaker_b: str,
        side_a: str,
        side_b: str,
        odds_a: float,
        odds_b: float,
        arb_percentage: float
    ):
        self.event_id = event_id
        self.matchup = matchup
        self.market_type = market_type
        self.bookmaker_a = bookmaker_a
        self.bookmaker_b = bookmaker_b
        self.side_a = side_a
        self.side_b = side_b
        self.odds_a = odds_a  # American odds
        self.odds_b = odds_b  # American odds
        self.arb_percentage = arb_percentage
        self.detected_at = datetime.now()

    def calculate_stakes(self, total_stake: float) -> Tuple[float, float, float]:
        """
        Calculate optimal stake allocation for arbitrage

        Args:
            total_stake: Total amount to invest across both bets

        Returns:
            Tuple of (stake_a, stake_b, guaranteed_profit)
        """
        decimal_a = OddsUtilities.american_to_decimal(self.odds_a)
        decimal_b = OddsUtilities.american_to_decimal(self.odds_b)

        # Calculate stake ratio
        # stake_a / stake_b = decimal_b / decimal_a
        stake_a = total_stake / (1 + (decimal_a / decimal_b))
        stake_b = total_stake - stake_a

        # Calculate guaranteed profit
        profit_if_a = (stake_a * decimal_a) - total_stake
        profit_if_b = (stake_b * decimal_b) - total_stake

        # Should be equal (or very close due to rounding)
        guaranteed_profit = min(profit_if_a, profit_if_b)

        return stake_a, stake_b, guaranteed_profit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'event_id': self.event_id,
            'matchup': self.matchup,
            'market_type': self.market_type,
            'bookmaker_a': self.bookmaker_a,
            'bookmaker_b': self.bookmaker_b,
            'side_a': self.side_a,
            'side_b': self.side_b,
            'odds_a': self.odds_a,
            'odds_b': self.odds_b,
            'arb_percentage': self.arb_percentage,
            'detected_at': self.detected_at.isoformat()
        }


class ArbitrageDetector:
    """
    Arbitrage opportunity detection across multiple bookmakers

    Usage:
        detector = ArbitrageDetector(min_profit=0.01)  # 1% minimum profit
        opportunities = detector.find_arbitrage_opportunities()

        for arb in opportunities:
            stakes = arb.calculate_stakes(total_stake=1000)
            print(f"Bet ${stakes[0]:.2f} on {arb.side_a} at {arb.bookmaker_a}")
            print(f"Bet ${stakes[1]:.2f} on {arb.side_b} at {arb.bookmaker_b}")
            print(f"Guaranteed profit: ${stakes[2]:.2f}")
    """

    def __init__(
        self,
        min_profit: float = 0.01,
        max_age_minutes: int = 5
    ):
        """
        Initialize arbitrage detector

        Args:
            min_profit: Minimum arbitrage profit percentage (default 1%)
            max_age_minutes: Maximum age of odds to consider (default 5 min)
        """
        self.min_profit = min_profit
        self.max_age_minutes = max_age_minutes
        self.odds_connector = OddsDatabaseConnector()

        logger.info(f"ArbitrageDetector initialized: min_profit={min_profit:.2%}")

    def find_arbitrage_opportunities(
        self,
        market: str = 'h2h',
        bookmakers: Optional[List[str]] = None
    ) -> List[ArbitrageOpportunity]:
        """
        Find all arbitrage opportunities for today's games

        Args:
            market: Market type ('h2h', 'spreads', 'totals')
            bookmakers: List of bookmakers to check (None = all available)

        Returns:
            List of ArbitrageOpportunity objects
        """
        if bookmakers is None:
            bookmakers = [
                'draftkings', 'fanduel', 'betmgm', 'pinnacle',
                'caesars', 'betrivers', 'bovada'
            ]

        opportunities = []

        # Get today's games
        games = self.odds_connector.get_todays_games()

        for game in games:
            try:
                event_id = game['event_id']
                matchup = f"{game['away_team']} @ {game['home_team']}"

                # Get odds for this game
                odds = self.odds_connector.get_latest_odds_for_game(
                    event_id,
                    market=market,
                    bookmaker_filter=bookmakers
                )

                if not odds:
                    continue

                # Group odds by bookmaker and outcome
                odds_by_bookmaker = self._group_odds_by_bookmaker(odds)

                # Find arbitrage across bookmakers
                arbs = self._detect_arbitrage_in_game(
                    event_id,
                    matchup,
                    market,
                    odds_by_bookmaker
                )

                opportunities.extend(arbs)

            except Exception as e:
                logger.error(f"Error detecting arbitrage for {game}: {e}")
                continue

        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities

    def _group_odds_by_bookmaker(
        self,
        odds: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Group odds by bookmaker and outcome

        Args:
            odds: List of odds dicts from OddsDatabaseConnector

        Returns:
            Dict: {bookmaker: {outcome: american_odds}}
        """
        grouped = {}

        for odd in odds:
            bookmaker = odd['bookmaker']
            outcome = odd['outcome_name']
            price = odd['price']

            if bookmaker not in grouped:
                grouped[bookmaker] = {}

            grouped[bookmaker][outcome] = price

        return grouped

    def _detect_arbitrage_in_game(
        self,
        event_id: str,
        matchup: str,
        market: str,
        odds_by_bookmaker: Dict[str, Dict[str, float]]
    ) -> List[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities for a single game

        Args:
            event_id: Event ID
            matchup: Game matchup string
            market: Market type
            odds_by_bookmaker: Odds grouped by bookmaker

        Returns:
            List of arbitrage opportunities found
        """
        opportunities = []

        # Get all outcomes (typically 2 for h2h market)
        all_outcomes = set()
        for book_odds in odds_by_bookmaker.values():
            all_outcomes.update(book_odds.keys())

        outcomes = list(all_outcomes)

        if len(outcomes) != 2:
            # Need exactly 2 outcomes for simple arbitrage
            return opportunities

        outcome_a, outcome_b = outcomes

        # Compare all bookmaker combinations
        bookmakers = list(odds_by_bookmaker.keys())

        for i, book_a in enumerate(bookmakers):
            for book_b in bookmakers[i:]:  # Avoid duplicate comparisons
                if book_a == book_b:
                    continue

                # Check if both bookmakers have both outcomes
                if (outcome_a not in odds_by_bookmaker[book_a] or
                    outcome_b not in odds_by_bookmaker[book_b]):
                    continue

                # Get odds
                odds_a_on_a = odds_by_bookmaker[book_a].get(outcome_a)
                odds_b_on_b = odds_by_bookmaker[book_b].get(outcome_b)

                if odds_a_on_a is None or odds_b_on_b is None:
                    continue

                # Calculate arbitrage percentage
                arb_pct = self._calculate_arbitrage_percentage(odds_a_on_a, odds_b_on_b)

                if arb_pct >= self.min_profit:
                    opp = ArbitrageOpportunity(
                        event_id=event_id,
                        matchup=matchup,
                        market_type=market,
                        bookmaker_a=book_a,
                        bookmaker_b=book_b,
                        side_a=outcome_a,
                        side_b=outcome_b,
                        odds_a=odds_a_on_a,
                        odds_b=odds_b_on_b,
                        arb_percentage=arb_pct
                    )
                    opportunities.append(opp)
                    logger.info(f"Arbitrage found: {matchup} - {arb_pct:.2%} profit")

        return opportunities

    def _calculate_arbitrage_percentage(
        self,
        american_odds_a: float,
        american_odds_b: float
    ) -> float:
        """
        Calculate arbitrage profit percentage

        Arbitrage exists when: (1/odds_a) + (1/odds_b) < 1

        Args:
            american_odds_a: American odds for outcome A
            american_odds_b: American odds for outcome B

        Returns:
            Arbitrage profit percentage (0.02 = 2% profit)
        """
        decimal_a = OddsUtilities.american_to_decimal(american_odds_a)
        decimal_b = OddsUtilities.american_to_decimal(american_odds_b)

        # Calculate total implied probability
        implied_total = (1 / decimal_a) + (1 / decimal_b)

        # Arbitrage percentage = 1 - implied_total
        # (positive value means arbitrage exists)
        arb_pct = 1 - implied_total

        return arb_pct

    def validate_arbitrage(
        self,
        opportunity: ArbitrageOpportunity
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate arbitrage opportunity is still valid

        Args:
            opportunity: ArbitrageOpportunity to validate

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Check age
        age = (datetime.now() - opportunity.detected_at).total_seconds() / 60
        if age > self.max_age_minutes:
            return False, f"Too old: {age:.1f} minutes"

        # Re-fetch current odds
        try:
            current_odds = self.odds_connector.get_latest_odds_for_game(
                opportunity.event_id,
                market=opportunity.market_type
            )

            if not current_odds:
                return False, "Odds no longer available"

            # Check if arbitrage still exists
            current_odds_dict = self._group_odds_by_bookmaker(current_odds)

            odds_a = current_odds_dict.get(opportunity.bookmaker_a, {}).get(opportunity.side_a)
            odds_b = current_odds_dict.get(opportunity.bookmaker_b, {}).get(opportunity.side_b)

            if odds_a is None or odds_b is None:
                return False, "One or more bookmakers no longer offering odds"

            current_arb = self._calculate_arbitrage_percentage(odds_a, odds_b)

            if current_arb < self.min_profit:
                return False, f"Arbitrage closed: {current_arb:.2%} < {self.min_profit:.2%}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def compare_live_to_pregame(
        self,
        event_id: str,
        pregame_simulation: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Compare live odds to pregame simulation probabilities

        Alerts when live odds have moved significantly from simulation expectations.

        Args:
            event_id: Event ID
            pregame_simulation: Dict of {team: win_probability}

        Returns:
            List of line movement alerts
        """
        alerts = []

        # Get current live odds
        current_odds = self.odds_connector.get_latest_odds_for_game(event_id)

        if not current_odds:
            return alerts

        for team, sim_prob in pregame_simulation.items():
            # Find odds for this team
            team_odds = [o for o in current_odds if o['outcome_name'] == team]

            if not team_odds:
                continue

            # Use best odds available
            best_odds = max(team_odds, key=lambda x: x['price'])
            decimal_odds = OddsUtilities.american_to_decimal(best_odds['price'])
            market_implied_prob = OddsUtilities.decimal_to_implied(decimal_odds)

            # Calculate deviation
            deviation = abs(market_implied_prob - sim_prob)

            # Alert if deviation > 10%
            if deviation > 0.10:
                alerts.append({
                    'team': team,
                    'sim_prob': sim_prob,
                    'market_prob': market_implied_prob,
                    'deviation': deviation,
                    'odds': best_odds['price'],
                    'bookmaker': best_odds['bookmaker']
                })

        return alerts

    def close(self):
        """Close database connections"""
        if hasattr(self, 'odds_connector'):
            self.odds_connector.close()


if __name__ == "__main__":
    # Test arbitrage detection
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical

    # Load secrets
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

    print("🔍 Testing Arbitrage Detector...\n")

    detector = ArbitrageDetector(min_profit=0.01)

    try:
        opportunities = detector.find_arbitrage_opportunities()

        print(f"📊 Found {len(opportunities)} arbitrage opportunities\n")

        for i, arb in enumerate(opportunities[:3], 1):
            print(f"Opportunity #{i}:")
            print(f"  {arb.matchup}")
            print(f"  {arb.bookmaker_a}: {arb.side_a} at {arb.odds_a:+.0f}")
            print(f"  {arb.bookmaker_b}: {arb.side_b} at {arb.odds_b:+.0f}")
            print(f"  Profit: {arb.arb_percentage:.2%}")

            stake_a, stake_b, profit = arb.calculate_stakes(1000)
            print(f"  Stakes (for $1000 total):")
            print(f"    ${stake_a:.2f} on {arb.side_a}")
            print(f"    ${stake_b:.2f} on {arb.side_b}")
            print(f"  Guaranteed profit: ${profit:.2f}\n")

        if not opportunities:
            print("ℹ️  No arbitrage opportunities found (likely no games today or odds are efficient)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        detector.close()
