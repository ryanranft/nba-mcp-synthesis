"""
Odds Integration Layer

Combines ML predictions with live odds data to generate betting recommendations.

This module bridges the gap between:
- ML prediction system (generates win probabilities)
- Live odds database (OddsDatabaseConnector)
- Existing betting utilities (odds_utilities, kelly_criterion)

Architecture:
    ML Predictions → Live Odds → Edge Calculation → Kelly Sizing → Recommendations

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import os

from mcp_server.connectors.odds_database_connector import OddsDatabaseConnector
from mcp_server.betting.odds_utilities import OddsUtilities

# Import Kelly Criterion if available
try:
    from mcp_server.betting.kelly_criterion import CalibratedKelly

    KELLY_AVAILABLE = True
except ImportError:
    KELLY_AVAILABLE = False
    logging.warning("Kelly Criterion module not available")

logger = logging.getLogger(__name__)


class OddsIntegration:
    """
    Integration layer for combining ML predictions with live odds

    Usage:
        integrator = OddsIntegration(bankroll=5000.0)

        # Combine predictions with odds
        recommendations = integrator.generate_betting_recommendations(
            predictions=ml_predictions,
            min_edge=0.03,
            market='h2h'
        )

        # Get top picks
        top_picks = integrator.get_top_picks(recommendations, n=3)
    """

    def __init__(
        self,
        bankroll: float = 10000.0,
        min_edge: float = 0.03,
        max_bet_fraction: float = 0.05,
        use_kelly: bool = True,
    ):
        """
        Initialize odds integration

        Args:
            bankroll: Total bankroll for betting
            min_edge: Minimum edge required to bet (default 3%)
            max_bet_fraction: Maximum fraction of bankroll per bet (default 5%)
            use_kelly: Use Kelly Criterion for position sizing
        """
        self.bankroll = bankroll
        self.min_edge = min_edge
        self.max_bet_fraction = max_bet_fraction
        self.use_kelly = use_kelly and KELLY_AVAILABLE

        # Initialize connectors
        self.odds_connector = OddsDatabaseConnector()

        # Initialize Kelly if available
        if self.use_kelly and KELLY_AVAILABLE:
            try:
                self.kelly = CalibratedKelly(bankroll=bankroll)
                logger.info("Kelly Criterion initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Kelly: {e}")
                self.use_kelly = False

        logger.info(
            f"OddsIntegration initialized: bankroll=${bankroll:,.0f}, min_edge={min_edge:.1%}"
        )

    def combine_predictions_with_odds(
        self,
        predictions: List[Dict[str, Any]],
        market: str = "h2h",
        bookmaker_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Combine ML predictions with live odds

        Args:
            predictions: List of prediction dicts with keys:
                - game_id: Game identifier
                - game_date: Game date (YYYY-MM-DD)
                - home_team: Home team name
                - away_team: Away team name
                - prob_home: Probability of home team winning (0-1)
                - prob_away: Probability of away team winning (0-1)
                - confidence: Model confidence score (0-1)
            market: Market type ('h2h', 'spreads', 'totals')
            bookmaker_filter: Optional list of bookmakers to use

        Returns:
            List of combined prediction + odds dicts
        """
        if bookmaker_filter is None:
            bookmaker_filter = ["draftkings", "fanduel", "betmgm", "pinnacle"]

        combined = []

        for pred in predictions:
            try:
                # Map game to event_id
                event_id = self.odds_connector.map_game_to_event_id(
                    pred["game_date"], pred["home_team"], pred["away_team"]
                )

                if not event_id:
                    logger.warning(
                        f"No event_id found for {pred['away_team']} @ {pred['home_team']}"
                    )
                    continue

                # Get latest odds
                odds = self.odds_connector.get_latest_odds_for_game(
                    event_id, market=market, bookmaker_filter=bookmaker_filter
                )

                if not odds:
                    logger.warning(f"No odds found for event {event_id}")
                    continue

                # Get best odds for each outcome
                best_odds = self.odds_connector.get_best_odds_by_bookmaker(
                    event_id, market=market
                )

                # Combine with prediction
                combined_item = {
                    **pred,  # Include all prediction fields
                    "event_id": event_id,
                    "market": market,
                    "odds_raw": odds,
                    "best_odds": best_odds,
                    "odds_fetched_at": datetime.now(),
                }

                combined.append(combined_item)

            except Exception as e:
                logger.error(f"Error combining prediction with odds: {e}")
                continue

        logger.info(f"Combined {len(combined)} predictions with odds")
        return combined

    def calculate_edges(
        self, combined_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate betting edges for each outcome

        Args:
            combined_data: Output from combine_predictions_with_odds()

        Returns:
            Same data with added edge calculations
        """
        results = []

        for item in combined_data:
            try:
                best_odds = item["best_odds"]
                prob_home = item["prob_home"]
                prob_away = item.get("prob_away", 1 - prob_home)

                # Calculate edges for home and away
                edges = {}

                # Home team edge
                if item["home_team"] in best_odds:
                    home_odds_american = best_odds[item["home_team"]]["best_price"]
                    home_odds_decimal = OddsUtilities.american_to_decimal(
                        home_odds_american
                    )

                    # Calculate edge: your_prob - implied_prob
                    implied_prob = OddsUtilities.decimal_to_implied(home_odds_decimal)
                    home_edge = prob_home - implied_prob

                    edges["home"] = {
                        "team": item["home_team"],
                        "ml_prob": prob_home,
                        "odds_american": home_odds_american,
                        "odds_decimal": home_odds_decimal,
                        "edge": home_edge,
                        "ev": (prob_home * home_odds_decimal) - 1,  # Expected value
                        "bookmaker": best_odds[item["home_team"]]["best_bookmaker"],
                    }

                # Away team edge
                if item["away_team"] in best_odds:
                    away_odds_american = best_odds[item["away_team"]]["best_price"]
                    away_odds_decimal = OddsUtilities.american_to_decimal(
                        away_odds_american
                    )

                    implied_prob = OddsUtilities.decimal_to_implied(away_odds_decimal)
                    away_edge = prob_away - implied_prob

                    edges["away"] = {
                        "team": item["away_team"],
                        "ml_prob": prob_away,
                        "odds_american": away_odds_american,
                        "odds_decimal": away_odds_decimal,
                        "edge": away_edge,
                        "ev": (prob_away * away_odds_decimal) - 1,
                        "bookmaker": best_odds[item["away_team"]]["best_bookmaker"],
                    }

                item["edges"] = edges
                results.append(item)

            except Exception as e:
                logger.error(f"Error calculating edges: {e}")
                continue

        return results

    def find_positive_ev_bets(
        self, data_with_edges: List[Dict[str, Any]], min_edge: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter for positive EV betting opportunities

        Args:
            data_with_edges: Output from calculate_edges()
            min_edge: Minimum edge threshold (uses self.min_edge if None)

        Returns:
            List of positive EV bets with metadata
        """
        if min_edge is None:
            min_edge = self.min_edge

        positive_ev_bets = []

        for item in data_with_edges:
            edges = item.get("edges", {})

            # Check home team edge
            if "home" in edges and edges["home"]["edge"] >= min_edge:
                bet = {
                    "game_id": item["game_id"],
                    "event_id": item["event_id"],
                    "game_date": item["game_date"],
                    "matchup": f"{item['away_team']} @ {item['home_team']}",
                    "bet_side": item["home_team"],
                    "bet_type": "home",
                    **edges["home"],
                    "confidence": item.get("confidence", 0.0),
                    "game_time": item.get("commence_time", None),
                }
                positive_ev_bets.append(bet)

            # Check away team edge
            if "away" in edges and edges["away"]["edge"] >= min_edge:
                bet = {
                    "game_id": item["game_id"],
                    "event_id": item["event_id"],
                    "game_date": item["game_date"],
                    "matchup": f"{item['away_team']} @ {item['home_team']}",
                    "bet_side": item["away_team"],
                    "bet_type": "away",
                    **edges["away"],
                    "confidence": item.get("confidence", 0.0),
                    "game_time": item.get("commence_time", None),
                }
                positive_ev_bets.append(bet)

        logger.info(
            f"Found {len(positive_ev_bets)} positive EV bets (min edge: {min_edge:.1%})"
        )
        return positive_ev_bets

    def apply_kelly_criterion(
        self, positive_ev_bets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply Kelly Criterion for position sizing

        Args:
            positive_ev_bets: Output from find_positive_ev_bets()

        Returns:
            Same bets with added 'kelly_fraction' and 'recommended_stake' fields
        """
        if not self.use_kelly:
            logger.warning("Kelly Criterion not available, using flat 2% stakes")
            for bet in positive_ev_bets:
                bet["kelly_fraction"] = 0.02
                bet["recommended_stake"] = self.bankroll * 0.02
            return positive_ev_bets

        for bet in positive_ev_bets:
            try:
                # Calculate Kelly fraction
                kelly_fraction = self.kelly.calculate_kelly(
                    probability=bet["ml_prob"], decimal_odds=bet["odds_decimal"]
                )

                # Apply Kelly adjustments (fractional Kelly, max bet limits)
                adjusted_fraction = self.kelly.apply_adjustments(kelly_fraction)

                # Cap at max_bet_fraction
                final_fraction = min(adjusted_fraction, self.max_bet_fraction)

                # Calculate recommended stake
                recommended_stake = self.bankroll * final_fraction

                bet["kelly_fraction"] = final_fraction
                bet["kelly_raw"] = kelly_fraction
                bet["recommended_stake"] = recommended_stake

            except Exception as e:
                logger.error(f"Error calculating Kelly for bet: {e}")
                # Fallback to conservative 2%
                bet["kelly_fraction"] = 0.02
                bet["recommended_stake"] = self.bankroll * 0.02

        return positive_ev_bets

    def generate_betting_recommendations(
        self,
        predictions: List[Dict[str, Any]],
        min_edge: Optional[float] = None,
        market: str = "h2h",
    ) -> Dict[str, Any]:
        """
        Complete workflow: predictions → odds → edges → Kelly → recommendations

        Args:
            predictions: ML predictions
            min_edge: Minimum edge threshold
            market: Market type

        Returns:
            Dict with:
                - recommendations: List of betting recommendations
                - summary: Summary statistics
                - metadata: Workflow metadata
        """
        logger.info("Generating betting recommendations...")

        # Step 1: Combine predictions with odds
        combined = self.combine_predictions_with_odds(predictions, market=market)

        if not combined:
            logger.warning("No games with odds available")
            return {
                "recommendations": [],
                "summary": {"total_bets": 0, "total_stake": 0, "total_ev": 0},
                "metadata": {"games_processed": 0, "games_with_odds": 0},
            }

        # Step 2: Calculate edges
        with_edges = self.calculate_edges(combined)

        # Step 3: Filter for positive EV
        positive_ev = self.find_positive_ev_bets(with_edges, min_edge=min_edge)

        # Step 4: Apply Kelly Criterion
        recommendations = self.apply_kelly_criterion(positive_ev)

        # Step 5: Generate summary
        summary = {
            "total_bets": len(recommendations),
            "total_stake": sum(bet["recommended_stake"] for bet in recommendations),
            "total_ev": sum(
                bet["ev"] * bet["recommended_stake"] for bet in recommendations
            ),
            "avg_edge": (
                sum(bet["edge"] for bet in recommendations) / len(recommendations)
                if recommendations
                else 0
            ),
            "avg_kelly": (
                sum(bet["kelly_fraction"] for bet in recommendations)
                / len(recommendations)
                if recommendations
                else 0
            ),
            "bankroll_exposure": (
                sum(bet["recommended_stake"] for bet in recommendations) / self.bankroll
                if self.bankroll > 0
                else 0
            ),
        }

        metadata = {
            "games_processed": len(predictions),
            "games_with_odds": len(combined),
            "positive_ev_bets": len(positive_ev),
            "min_edge_used": min_edge or self.min_edge,
            "market": market,
            "generated_at": datetime.now().isoformat(),
        }

        logger.info(f"Generated {len(recommendations)} recommendations")
        logger.info(
            f"Total stake: ${summary['total_stake']:,.0f} ({summary['bankroll_exposure']:.1%} of bankroll)"
        )
        logger.info(f"Expected value: ${summary['total_ev']:,.2f}")

        return {
            "recommendations": recommendations,
            "summary": summary,
            "metadata": metadata,
        }

    def get_top_picks(
        self, recommendations_dict: Dict[str, Any], n: int = 3, sort_by: str = "edge"
    ) -> List[Dict[str, Any]]:
        """
        Get top N betting picks

        Args:
            recommendations_dict: Output from generate_betting_recommendations()
            n: Number of top picks to return
            sort_by: Sort criterion ('edge', 'ev', 'kelly', 'confidence')

        Returns:
            List of top N recommendations sorted by criterion
        """
        recommendations = recommendations_dict.get("recommendations", [])

        if not recommendations:
            return []

        # Sort by criterion
        if sort_by == "edge":
            sorted_recs = sorted(recommendations, key=lambda x: x["edge"], reverse=True)
        elif sort_by == "ev":
            sorted_recs = sorted(recommendations, key=lambda x: x["ev"], reverse=True)
        elif sort_by == "kelly":
            sorted_recs = sorted(
                recommendations, key=lambda x: x["kelly_fraction"], reverse=True
            )
        elif sort_by == "confidence":
            sorted_recs = sorted(
                recommendations, key=lambda x: x["confidence"], reverse=True
            )
        else:
            sorted_recs = recommendations

        return sorted_recs[:n]

    def close(self):
        """Close database connections"""
        if hasattr(self, "odds_connector"):
            self.odds_connector.close()


if __name__ == "__main__":
    # Test the integration
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical

    # Load secrets
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

    # Create test prediction
    mock_predictions = [
        {
            "game_id": "test_001",
            "game_date": "2025-01-06",
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "prob_home": 0.58,
            "prob_away": 0.42,
            "confidence": 0.85,
        }
    ]

    # Test integration
    integrator = OddsIntegration(bankroll=5000.0, min_edge=0.03)

    print("🔧 Testing Odds Integration...")
    print()

    try:
        results = integrator.generate_betting_recommendations(
            predictions=mock_predictions, min_edge=0.03
        )

        print(f"📊 Results:")
        print(f"  Games processed: {results['metadata']['games_processed']}")
        print(f"  Games with odds: {results['metadata']['games_with_odds']}")
        print(f"  Positive EV bets: {results['metadata']['positive_ev_bets']}")
        print(f"  Recommendations: {results['summary']['total_bets']}")
        print()

        if results["recommendations"]:
            print("💰 Top Recommendations:")
            top_picks = integrator.get_top_picks(results, n=3)
            for i, pick in enumerate(top_picks, 1):
                print(f"{i}. {pick['bet_side']} ({pick['matchup']})")
                print(
                    f"   Edge: {pick['edge']:.2%} | Kelly: {pick['kelly_fraction']:.2%} | Stake: ${pick['recommended_stake']:.0f}"
                )
        else:
            print("ℹ️  No betting opportunities found (likely no games today)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        integrator.close()
