"""
Odds Database Connector

Connects to PostgreSQL 'odds' schema to retrieve betting odds data
collected by the autonomous odds-api scraper system.

This connector provides access to:
- Latest odds for today's games
- Multi-bookmaker odds comparison
- Consensus odds calculation
- Line shopping across sportsbooks
- Odds freshness monitoring

Database Schema: odds schema with tables:
- odds.events: Game metadata
- odds.odds_snapshots: Temporal odds storage (partitioned by month)
- odds.bookmakers: Sportsbook reference
- odds.market_types: Market catalog

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)


class OddsDatabaseConnector:
    """
    PostgreSQL connector for odds database queries

    Connects to the same RDS PostgreSQL database as nba-mcp-synthesis
    but queries the 'odds' schema populated by the odds-api scraper.
    """

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Initialize odds database connector

        Args:
            db_config: Database configuration dict with keys:
                - host: PostgreSQL host
                - port: PostgreSQL port
                - database: Database name
                - user: Database username
                - password: Database password

                If not provided, reads from environment variables loaded
                by unified_secrets_manager
        """
        if db_config is None:
            # Read from environment variables (loaded by unified_secrets_manager)
            db_config = {
                'host': os.getenv('RDS_HOST') or os.getenv('DB_HOST'),
                'port': int(os.getenv('RDS_PORT', os.getenv('DB_PORT', '5432'))),
                'database': os.getenv('RDS_DATABASE') or os.getenv('DB_NAME'),
                'user': os.getenv('RDS_USERNAME') or os.getenv('DB_USER'),
                'password': os.getenv('RDS_PASSWORD') or os.getenv('DB_PASSWORD'),
            }

        self.db_config = db_config
        self._conn = None

        # Validate configuration
        if not all([db_config.get('host'), db_config.get('database'),
                    db_config.get('user'), db_config.get('password')]):
            raise ValueError("Database configuration incomplete. Ensure secrets are loaded.")

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection (creates if needed)"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    cursor_factory=RealDictCursor
                )
                logger.info("Connected to odds database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._conn

    def close(self):
        """Close database connection"""
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.info("Closed database connection")

    def get_todays_games(self) -> List[Dict[str, Any]]:
        """
        Get all games scheduled for today

        Returns:
            List of dicts with keys:
                - event_id: Odds API event ID
                - home_team: Home team name
                - away_team: Away team name
                - commence_time: Game start time
        """
        query = """
        SELECT
            event_id,
            home_team,
            away_team,
            commence_time
        FROM odds.events
        WHERE commence_time::date = CURRENT_DATE
        ORDER BY commence_time;
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                logger.info(f"Found {len(results)} games for today")
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching today's games: {e}")
            return []

    def get_latest_odds_for_game(
        self,
        event_id: str,
        market: str = 'h2h',
        bookmaker_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get latest odds for a specific game

        Args:
            event_id: Odds API event ID
            market: Market type ('h2h', 'spreads', 'totals')
            bookmaker_filter: Optional list of bookmaker keys to filter
                            (e.g., ['draftkings', 'fanduel', 'betmgm'])

        Returns:
            List of dicts with keys:
                - bookmaker: Bookmaker name
                - bookmaker_key: Bookmaker key
                - outcome_name: Team/outcome name
                - price: Odds (American format)
                - point: Spread/total value (if applicable)
                - fetched_at: When odds were captured
        """
        query = """
        SELECT DISTINCT ON (b.bookmaker_key, os.outcome_name)
            b.bookmaker_title AS bookmaker,
            b.bookmaker_key,
            os.outcome_name,
            os.price,
            os.point,
            os.fetched_at
        FROM odds.odds_snapshots os
        JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
        JOIN odds.market_types m ON os.market_type_id = m.market_type_id
        WHERE os.event_id = %s
          AND m.market_key = %s
        """

        params = [event_id, market]

        if bookmaker_filter:
            placeholders = ','.join(['%s'] * len(bookmaker_filter))
            query += f" AND b.bookmaker_key IN ({placeholders})"
            params.extend(bookmaker_filter)

        query += """
        ORDER BY b.bookmaker_key, os.outcome_name, os.fetched_at DESC;
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                logger.debug(f"Found {len(results)} odds for event {event_id}, market {market}")
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching odds for event {event_id}: {e}")
            return []

    def get_all_odds_today(
        self,
        market: str = 'h2h',
        top_bookmakers: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get latest odds for all today's games

        Args:
            market: Market type ('h2h', 'spreads', 'totals')
            top_bookmakers: Optional list of bookmaker keys to filter
                          Defaults to: ['draftkings', 'fanduel', 'betmgm', 'pinnacle']

        Returns:
            Dict mapping event_id to list of odds dicts
        """
        if top_bookmakers is None:
            top_bookmakers = ['draftkings', 'fanduel', 'betmgm', 'pinnacle']

        games = self.get_todays_games()
        all_odds = {}

        for game in games:
            event_id = game['event_id']
            odds = self.get_latest_odds_for_game(
                event_id,
                market=market,
                bookmaker_filter=top_bookmakers
            )
            if odds:
                all_odds[event_id] = {
                    'game_info': game,
                    'odds': odds
                }

        logger.info(f"Retrieved odds for {len(all_odds)} games")
        return all_odds

    def get_best_odds_by_bookmaker(
        self,
        event_id: str,
        market: str = 'h2h'
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare odds across bookmakers for line shopping

        Args:
            event_id: Odds API event ID
            market: Market type

        Returns:
            Dict mapping outcome_name to dict with:
                - best_price: Best odds available
                - best_bookmaker: Bookmaker offering best odds
                - all_bookmakers: List of all bookmaker offers
        """
        odds = self.get_latest_odds_for_game(event_id, market)

        comparison = {}
        for odd in odds:
            outcome = odd['outcome_name']
            if outcome not in comparison:
                comparison[outcome] = {
                    'best_price': odd['price'],
                    'best_bookmaker': odd['bookmaker'],
                    'all_bookmakers': []
                }

            comparison[outcome]['all_bookmakers'].append({
                'bookmaker': odd['bookmaker'],
                'price': odd['price'],
                'point': odd.get('point')
            })

            # Track best price (highest for positive odds, closest to 100 for negative)
            current_best = comparison[outcome]['best_price']
            new_price = odd['price']

            if self._is_better_price(new_price, current_best):
                comparison[outcome]['best_price'] = new_price
                comparison[outcome]['best_bookmaker'] = odd['bookmaker']

        return comparison

    def _is_better_price(self, new_price: float, current_best: float) -> bool:
        """
        Compare American odds to determine which is better for bettor

        For positive odds (+150): Higher is better
        For negative odds (-110): Closer to -100 is better (less risk)
        """
        # Both positive: higher is better
        if new_price > 0 and current_best > 0:
            return new_price > current_best
        # Both negative: closer to -100 is better
        elif new_price < 0 and current_best < 0:
            return new_price > current_best  # -105 > -110
        # Mixed: positive is generally better
        else:
            return new_price > current_best

    def get_consensus_odds(
        self,
        event_id: str,
        market: str = 'h2h'
    ) -> Dict[str, float]:
        """
        Calculate consensus (average) odds across top bookmakers

        Args:
            event_id: Odds API event ID
            market: Market type

        Returns:
            Dict mapping outcome_name to average American odds
        """
        odds = self.get_latest_odds_for_game(
            event_id,
            market,
            bookmaker_filter=['draftkings', 'fanduel', 'betmgm']
        )

        if not odds:
            return {}

        # Group by outcome
        outcomes = {}
        for odd in odds:
            outcome = odd['outcome_name']
            if outcome not in outcomes:
                outcomes[outcome] = []
            outcomes[outcome].append(odd['price'])

        # Calculate averages
        consensus = {}
        for outcome, prices in outcomes.items():
            consensus[outcome] = sum(prices) / len(prices)

        return consensus

    def check_odds_freshness(self, max_age_minutes: int = 10) -> Dict[str, Any]:
        """
        Check if odds data is fresh (recently updated)

        Args:
            max_age_minutes: Maximum acceptable age in minutes

        Returns:
            Dict with:
                - is_fresh: Boolean
                - latest_update: Timestamp of most recent odds
                - age_minutes: Age of data in minutes
                - stale_games: List of event_ids with stale data
        """
        query = """
        SELECT
            e.event_id,
            e.home_team,
            e.away_team,
            MAX(os.fetched_at) AS latest_update,
            EXTRACT(EPOCH FROM (NOW() - MAX(os.fetched_at)))/60 AS age_minutes
        FROM odds.events e
        LEFT JOIN odds.odds_snapshots os ON e.event_id = os.event_id
        WHERE e.commence_time::date = CURRENT_DATE
        GROUP BY e.event_id, e.home_team, e.away_team
        HAVING MAX(os.fetched_at) IS NOT NULL
        ORDER BY age_minutes DESC;
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()

                if not results:
                    return {
                        'is_fresh': False,
                        'latest_update': None,
                        'age_minutes': None,
                        'stale_games': [],
                        'message': 'No odds data found for today'
                    }

                stale_games = [
                    {
                        'event_id': row['event_id'],
                        'matchup': f"{row['away_team']} @ {row['home_team']}",
                        'age_minutes': float(row['age_minutes'])
                    }
                    for row in results
                    if float(row['age_minutes']) > max_age_minutes
                ]

                latest = results[0]
                return {
                    'is_fresh': len(stale_games) == 0,
                    'latest_update': latest['latest_update'],
                    'age_minutes': float(latest['age_minutes']),
                    'stale_games': stale_games,
                    'total_games': len(results)
                }
        except Exception as e:
            logger.error(f"Error checking odds freshness: {e}")
            return {
                'is_fresh': False,
                'latest_update': None,
                'age_minutes': None,
                'stale_games': [],
                'error': str(e)
            }

    def map_game_to_event_id(
        self,
        game_date: str,
        home_team: str,
        away_team: str
    ) -> Optional[str]:
        """
        Map nba-mcp-synthesis game to odds event_id

        Handles team name variations (e.g., "Los Angeles Lakers" vs "Lakers")

        Args:
            game_date: Game date (YYYY-MM-DD)
            home_team: Home team name
            away_team: Away team name

        Returns:
            event_id if found, None otherwise
        """
        # Try exact match first
        query = """
        SELECT event_id
        FROM odds.events
        WHERE commence_time::date = %s
          AND home_team ILIKE %s
          AND away_team ILIKE %s
        LIMIT 1;
        """

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Try exact match
                cur.execute(query, (game_date, home_team, away_team))
                result = cur.fetchone()
                if result:
                    return result['event_id']

                # Try partial match (handles name variations)
                query_partial = """
                SELECT event_id
                FROM odds.events
                WHERE commence_time::date = %s
                  AND (home_team ILIKE %s OR home_team ILIKE %s)
                  AND (away_team ILIKE %s OR away_team ILIKE %s)
                LIMIT 1;
                """

                home_partial = f"%{home_team.split()[-1]}%"  # Last word (e.g., "Lakers")
                away_partial = f"%{away_team.split()[-1]}%"

                cur.execute(query_partial, (
                    game_date,
                    home_team, home_partial,
                    away_team, away_partial
                ))
                result = cur.fetchone()

                if result:
                    logger.info(f"Mapped {away_team} @ {home_team} to event {result['event_id']}")
                    return result['event_id']
                else:
                    logger.warning(f"No event_id found for {away_team} @ {home_team} on {game_date}")
                    return None

        except Exception as e:
            logger.error(f"Error mapping game to event_id: {e}")
            return None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Test the connector
    import sys
    sys.path.insert(0, '/Users/ryanranft/nba-mcp-synthesis')

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical

    # Load secrets
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')

    # Test connector
    with OddsDatabaseConnector() as connector:
        print("✅ Connected to odds database\n")

        # Check freshness
        freshness = connector.check_odds_freshness()
        print(f"📊 Odds Freshness:")
        print(f"  Fresh: {freshness['is_fresh']}")
        print(f"  Latest update: {freshness.get('latest_update')}")
        age = freshness.get('age_minutes')
        if age is not None:
            print(f"  Age: {age:.1f} minutes")
        else:
            print(f"  Age: N/A (no data)")
        print(f"  Total games: {freshness.get('total_games', 0)}")
        if 'message' in freshness:
            print(f"  Message: {freshness['message']}\n")
        else:
            print()

        # Get today's games
        games = connector.get_todays_games()
        print(f"🏀 Today's Games: {len(games)}")
        for game in games[:3]:
            print(f"  {game['away_team']} @ {game['home_team']} - {game['commence_time']}")

        if games:
            # Get odds for first game
            event_id = games[0]['event_id']
            print(f"\n💰 Latest odds for {games[0]['away_team']} @ {games[0]['home_team']}:")
            odds = connector.get_latest_odds_for_game(event_id)
            for odd in odds[:6]:
                print(f"  {odd['bookmaker']}: {odd['outcome_name']} at {odd['price']}")
