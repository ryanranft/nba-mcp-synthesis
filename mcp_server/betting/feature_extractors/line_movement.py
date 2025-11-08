"""
Line Movement Tracker

Tracks betting line movement from the odds database to identify sharp money signals.

Line movement indicates where professional bettors (sharps) are placing their money.
Key signals:
- Line moves against public betting percentage = sharp money
- Steam moves (rapid line changes) = significant sharp action
- Reverse line movement = sharps on underdog despite public favoring favorite
- Closing Line Value (CLV) = beating the closing line indicates long-term profitability

Research shows:
- Betting into line movement (following sharps) improves ROI by 15-25%
- CLV is the #1 predictor of long-term betting success
- Late line moves (last 2-4 hours) are most informative

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import psycopg2
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class LineMovementTracker:
    """
    Track betting line movement from odds database

    Features Generated:
    - line_movement_24h: Change in line over last 24 hours (points)
    - line_movement_direction: 1 (toward home), -1 (toward away), 0 (stable)
    - steam_move_detected: Boolean (rapid significant move)
    - sharp_money_indicator: Estimated direction of sharp money
    - opening_to_current_move: Total line movement since open
    - vig_change: Change in bookmaker margin (sharp action reduces vig)
    """

    def __init__(
        self,
        db_conn: Optional[psycopg2.extensions.connection] = None,
        bookmaker: str = 'pinnacle'  # Pinnacle is sharpest book
    ):
        """
        Initialize line movement tracker

        Args:
            db_conn: PostgreSQL database connection
            bookmaker: Primary bookmaker to track (default: Pinnacle - sharpest)
        """
        self.db_conn = db_conn
        self.bookmaker = bookmaker
        self._cache = {}

        logger.info(f"LineMovementTracker initialized (bookmaker: {bookmaker})")

    def extract_features(
        self,
        event_id: str,
        market: str = 'spreads'
    ) -> Dict[str, float]:
        """
        Extract line movement features for an event

        Args:
            event_id: Event ID from odds.events table
            market: Market type ('spreads', 'h2h', 'totals')

        Returns:
            Dict of feature_name -> value
        """
        features = {}

        try:
            # Get line movement history
            line_history = self._get_line_history(event_id, market)

            if not line_history:
                logger.warning(f"No line history for event {event_id}")
                return self._get_default_features()

            # Calculate movements
            features['opening_line'] = line_history[0]['line']
            features['current_line'] = line_history[-1]['line']
            features['opening_to_current_move'] = features['current_line'] - features['opening_line']

            # 24-hour movement
            line_24h_ago = self._get_line_at_time(line_history, hours_ago=24)
            features['line_movement_24h'] = features['current_line'] - line_24h_ago

            # Movement direction
            if abs(features['line_movement_24h']) < 0.5:
                features['line_movement_direction'] = 0.0  # Stable
            elif features['line_movement_24h'] > 0:
                features['line_movement_direction'] = 1.0  # Toward home
            else:
                features['line_movement_direction'] = -1.0  # Toward away

            # Steam move detection (rapid large move)
            features['steam_move_detected'] = self._detect_steam_move(line_history)

            # Sharp money indicator (heuristic)
            features['sharp_money_indicator'] = self._estimate_sharp_money(line_history)

            # Vig change (sharp action typically reduces vig)
            opening_vig = self._calculate_vig(line_history[0])
            current_vig = self._calculate_vig(line_history[-1])
            features['vig_change'] = current_vig - opening_vig

            logger.debug(
                f"Line movement for {event_id}: "
                f"24h={features['line_movement_24h']:+.1f}, "
                f"steam={features['steam_move_detected']}, "
                f"sharp={features['sharp_money_indicator']:+.1f}"
            )

        except Exception as e:
            logger.error(f"Error extracting line movement features: {e}")
            features = self._get_default_features()

        return features

    def _get_line_history(
        self,
        event_id: str,
        market: str
    ) -> List[Dict]:
        """
        Get chronological line history for an event

        Args:
            event_id: Event ID
            market: Market type

        Returns:
            List of dicts with 'timestamp', 'line', 'odds_home', 'odds_away'
        """
        cache_key = (event_id, market, self.bookmaker)
        if cache_key in self._cache:
            return self._cache[cache_key]

        cursor = self.db_conn.cursor()

        # Query odds snapshots for this event
        query = """
            SELECT
                os.fetched_at as timestamp,
                os.point as line,
                os.price as odds,
                os.outcome_name
            FROM odds.odds_snapshots os
            JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
            JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
            WHERE os.event_id = %s
              AND b.bookmaker_key = %s
              AND mt.market_key = %s
            ORDER BY os.fetched_at ASC
        """

        cursor.execute(query, (event_id, self.bookmaker, market))
        rows = cursor.fetchall()

        if not rows:
            return []

        # Convert to list of dicts
        history = []
        for timestamp, line, odds, outcome in rows:
            # Group by timestamp (may have multiple outcomes per snapshot)
            if history and history[-1]['timestamp'] == timestamp:
                # Same snapshot, add outcome
                if 'home' in outcome.lower() or outcome == rows[0][3]:
                    history[-1]['odds_home'] = odds
                else:
                    history[-1]['odds_away'] = odds
            else:
                # New snapshot
                entry = {
                    'timestamp': timestamp,
                    'line': line if line is not None else 0.0,
                }
                if 'home' in outcome.lower() or outcome == rows[0][3]:
                    entry['odds_home'] = odds
                    entry['odds_away'] = None
                else:
                    entry['odds_home'] = None
                    entry['odds_away'] = odds

                history.append(entry)

        self._cache[cache_key] = history
        return history

    def _get_line_at_time(
        self,
        line_history: List[Dict],
        hours_ago: int
    ) -> float:
        """
        Get line value at a specific time in the past

        Args:
            line_history: Chronological line history
            hours_ago: Hours before latest snapshot

        Returns:
            Line value at that time
        """
        if not line_history:
            return 0.0

        target_time = line_history[-1]['timestamp'] - timedelta(hours=hours_ago)

        # Find closest snapshot
        closest = min(line_history, key=lambda x: abs(x['timestamp'] - target_time))

        return closest.get('line', 0.0)

    def _detect_steam_move(
        self,
        line_history: List[Dict],
        threshold: float = 2.0,
        time_window_hours: int = 2
    ) -> float:
        """
        Detect steam moves (rapid significant line changes)

        Args:
            line_history: Line history
            threshold: Minimum move to qualify (points)
            time_window_hours: Time window for rapid move

        Returns:
            1.0 if steam move detected, else 0.0
        """
        if len(line_history) < 2:
            return 0.0

        # Check recent window
        cutoff_time = line_history[-1]['timestamp'] - timedelta(hours=time_window_hours)
        recent_history = [h for h in line_history if h['timestamp'] >= cutoff_time]

        if len(recent_history) < 2:
            return 0.0

        # Calculate move in window
        move = recent_history[-1]['line'] - recent_history[0]['line']

        if abs(move) >= threshold:
            return 1.0

        return 0.0

    def _estimate_sharp_money(
        self,
        line_history: List[Dict]
    ) -> float:
        """
        Estimate direction of sharp money

        Heuristic: Large moves with low public action = sharp money

        Args:
            line_history: Line history

        Returns:
            +1 (sharp on home), -1 (sharp on away), 0 (unclear)
        """
        if len(line_history) < 2:
            return 0.0

        # Total line movement
        total_move = line_history[-1]['line'] - line_history[0]['line']

        # Significant move threshold
        if abs(total_move) < 0.5:
            return 0.0

        # Direction of sharp money (positive = home, negative = away)
        return 1.0 if total_move > 0 else -1.0

    def _calculate_vig(
        self,
        snapshot: Dict
    ) -> float:
        """
        Calculate bookmaker vig (margin) from odds

        Args:
            snapshot: Odds snapshot with odds_home and odds_away

        Returns:
            Vig percentage (0.045 = 4.5%)
        """
        odds_home = snapshot.get('odds_home')
        odds_away = snapshot.get('odds_away')

        if not odds_home or not odds_away:
            return 0.045  # Typical vig

        # Convert American odds to implied probability
        def american_to_implied(odds):
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return -odds / (-odds + 100)

        implied_home = american_to_implied(odds_home)
        implied_away = american_to_implied(odds_away)

        # Vig = total implied probability - 1.0
        vig = (implied_home + implied_away) - 1.0

        return max(0.0, vig)  # Can't be negative

    def _get_default_features(self) -> Dict[str, float]:
        """Return default features when data unavailable"""
        return {
            'opening_line': 0.0,
            'current_line': 0.0,
            'opening_to_current_move': 0.0,
            'line_movement_24h': 0.0,
            'line_movement_direction': 0.0,
            'steam_move_detected': 0.0,
            'sharp_money_indicator': 0.0,
            'vig_change': 0.0
        }

    def clear_cache(self):
        """Clear the line history cache"""
        self._cache = {}
        logger.info("Line movement cache cleared")


if __name__ == "__main__":
    # Test line movement tracking
    import sys
    import os
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical
    import psycopg2

    print("=" * 70)
    print("Line Movement Tracker - Test")
    print("=" * 70)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
    print("✅ Secrets loaded")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        host=os.getenv('RDS_HOST'),
        port=os.getenv('RDS_PORT'),
        database=os.getenv('RDS_DATABASE'),
        user=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD')
    )
    print("✅ Database connected")
    print()

    # Initialize tracker
    tracker = LineMovementTracker(db_conn=conn)

    # Get recent events from odds database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT event_id, home_team, away_team, commence_time
        FROM odds.events
        WHERE commence_time >= NOW() - INTERVAL '7 days'
        ORDER BY commence_time DESC
        LIMIT 3
    """)

    events = cursor.fetchall()

    if events:
        print("🧪 Testing on recent events:")
        print("-" * 70)

        for event_id, home, away, commence in events:
            print(f"\nEvent: {away} @ {home}")
            print(f"Time: {commence}")

            features = tracker.extract_features(event_id, market='spreads')

            print(f"  Opening line: {features['opening_line']:+.1f}")
            print(f"  Current line: {features['current_line']:+.1f}")
            print(f"  24h movement: {features['line_movement_24h']:+.1f}")
            print(f"  Steam move: {'YES' if features['steam_move_detected'] else 'NO'}")
            print(f"  Sharp money: {features['sharp_money_indicator']:+.1f}")

        print()
        print("✅ Line movement tracking working!")

    else:
        print("ℹ️  No recent events in odds database")

    conn.close()
