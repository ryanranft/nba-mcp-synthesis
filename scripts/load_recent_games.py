#!/usr/bin/env python3
"""
NBA MCP Synthesis - Load Recent Games

Fetches recent games from ESPN API and loads them into the local database.

Usage:
    python scripts/load_recent_games.py --days 7          # Load last 7 days
    python scripts/load_recent_games.py --days 30 --full  # Load with all data
    python scripts/load_recent_games.py --date 2024-01-15 # Load specific date

Author: NBA MCP Synthesis Team
Date: 2025-01-07
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install with: pip install requests")
    sys.exit(1)


class ESPNDataFetcher:
    """Fetches NBA data from ESPN API."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

    def get_games_for_date(self, date: str) -> List[Dict]:
        """
        Fetch all games for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of game dictionaries with IDs and metadata
        """
        url = f"{self.BASE_URL}/scoreboard"
        params = {'dates': date.replace('-', '')}  # ESPN wants YYYYMMDD

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = []
            for event in data.get('events', []):
                game_id = event.get('id')
                competitions = event.get('competitions', [{}])[0]

                game_info = {
                    'game_id': game_id,
                    'game_date': date,
                    'season': event.get('season', {}).get('year'),
                    'season_type': event.get('season', {}).get('type'),
                    'status': competitions.get('status', {}).get('type', {}).get('name'),
                    'home_team': competitions.get('competitors', [{}])[0].get('team', {}).get('displayName'),
                    'away_team': competitions.get('competitors', [{}])[1].get('team', {}).get('displayName'),
                    'home_team_id': int(competitions.get('competitors', [{}])[0].get('team', {}).get('id', 0)),
                    'away_team_id': int(competitions.get('competitors', [{}])[1].get('team', {}).get('id', 0)),
                    'home_score': int(competitions.get('competitors', [{}])[0].get('score', 0)),
                    'away_score': int(competitions.get('competitors', [{}])[1].get('score', 0)),
                }
                games.append(game_info)

            return games

        except requests.RequestException as e:
            print(f"   ❌ Error fetching games for {date}: {e}")
            return []

    def get_play_by_play(self, game_id: str) -> Optional[List[Dict]]:
        """
        Fetch play-by-play events for a specific game.

        Args:
            game_id: ESPN game ID

        Returns:
            List of play-by-play event dictionaries or None if error
        """
        url = f"{self.BASE_URL}/summary"
        params = {'event': game_id}

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Extract play-by-play events
            plays = []
            for play_data in data.get('plays', []):
                for play in play_data.get('items', []):
                    event = {
                        'game_id': game_id,
                        'sequence_number': play.get('sequenceNumber'),
                        'type_id': play.get('type', {}).get('id'),
                        'type_text': play.get('type', {}).get('text'),
                        'text': play.get('text'),
                        'period': play.get('period', {}).get('number'),
                        'clock_display_value': play.get('clock', {}).get('displayValue'),
                        'team_id': play.get('team', {}).get('id'),
                        'scoring_play': 1 if play.get('scoringPlay') else 0,
                        'shooting_play': 1 if play.get('shootingPlay') else 0,
                        'score_value': play.get('scoreValue', 0),
                        'home_score': play.get('homeScore'),
                        'away_score': play.get('awayScore'),
                        'coordinate_x': play.get('coordinate', {}).get('x'),
                        'coordinate_y': play.get('coordinate', {}).get('y'),
                    }

                    # Extract athlete IDs (up to 3 participants)
                    participants = play.get('participants', [])
                    for i, participant in enumerate(participants[:3]):
                        event[f'athlete_id_{i+1}'] = participant.get('athlete', {}).get('id')

                    plays.append(event)

            return plays if plays else None

        except requests.RequestException as e:
            print(f"      ❌ Error fetching play-by-play for game {game_id}: {e}")
            return None


class DatabaseLoader:
    """Loads NBA data into PostgreSQL database."""

    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    def load_game(self, game: Dict) -> bool:
        """Load game metadata into games table."""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO games (
                    game_id, game_date, season, season_type,
                    home_team, away_team, home_team_id, away_team_id,
                    home_score, away_score
                ) VALUES (
                    %(game_id)s, %(game_date)s, %(season)s, %(season_type)s,
                    %(home_team)s, %(away_team)s, %(home_team_id)s, %(away_team_id)s,
                    %(home_score)s, %(away_score)s
                )
                ON CONFLICT (game_id) DO UPDATE SET
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    updated_at = CURRENT_TIMESTAMP
            """, game)

            self.conn.commit()
            return True

        except Exception as e:
            print(f"      ❌ Error loading game {game['game_id']}: {e}")
            self.conn.rollback()
            return False

    def load_play_by_play(self, game_id: str, plays: List[Dict]) -> int:
        """Load play-by-play events into hoopr_play_by_play table."""
        if not plays:
            return 0

        cursor = self.conn.cursor()

        try:
            execute_batch(
                cursor,
                """
                    INSERT INTO hoopr_play_by_play (
                        game_id, sequence_number, type_id, type_text, text,
                        period, clock_display_value, team_id,
                        scoring_play, shooting_play, score_value,
                        home_score, away_score,
                        coordinate_x, coordinate_y,
                        athlete_id_1, athlete_id_2, athlete_id_3
                    ) VALUES (
                        %(game_id)s, %(sequence_number)s, %(type_id)s, %(type_text)s, %(text)s,
                        %(period)s, %(clock_display_value)s, %(team_id)s,
                        %(scoring_play)s, %(shooting_play)s, %(score_value)s,
                        %(home_score)s, %(away_score)s,
                        %(coordinate_x)s, %(coordinate_y)s,
                        %(athlete_id_1)s, %(athlete_id_2)s, %(athlete_id_3)s
                    )
                    ON CONFLICT (game_id, sequence_number) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP
                """,
                plays,
                page_size=1000
            )

            self.conn.commit()
            return len(plays)

        except Exception as e:
            print(f"      ❌ Error loading play-by-play for game {game_id}: {e}")
            self.conn.rollback()
            return 0


def main():
    parser = argparse.ArgumentParser(description='Load recent NBA games into local database')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to load (default: 7)')
    parser.add_argument('--date', type=str,
                        help='Specific date to load (YYYY-MM-DD)')
    parser.add_argument('--full', action='store_true',
                        help='Load full play-by-play data (default: games only)')
    parser.add_argument('--context', default='development',
                        choices=['development', 'production'],
                        help='Database context (default: development)')

    args = parser.parse_args()

    print("=" * 70)
    print("NBA MCP Synthesis - Load Recent Games")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Context: {args.context}")

    # Determine date range
    if args.date:
        dates = [args.date]
        print(f"Loading data for: {args.date}")
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                 for i in range(args.days + 1)]
        print(f"Loading data for: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    print(f"Mode: {'Full (play-by-play)' if args.full else 'Games only'}")

    # Load credentials and connect
    print(f"\n🔐 Loading {args.context} credentials...")
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', args.context)
    config = get_database_config()

    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=int(config['port']),
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        print(f"✅ Connected to {config['database']}")
    except psycopg2.OperationalError as e:
        print(f"❌ Failed to connect: {e}")
        print("\n💡 Make sure PostgreSQL is running: docker-compose up -d postgres")
        sys.exit(1)

    # Initialize fetcher and loader
    fetcher = ESPNDataFetcher()
    loader = DatabaseLoader(conn)

    # Process each date
    total_games = 0
    total_plays = 0

    print("\n📥 Fetching and loading data...")
    for date in dates:
        print(f"\n📅 {date}")

        # Fetch games for date
        games = fetcher.get_games_for_date(date)
        if not games:
            print("   ℹ️  No games found")
            continue

        print(f"   Found {len(games)} game(s)")

        # Load each game
        for game in games:
            print(f"   🏀 {game['away_team']} @ {game['home_team']}")

            # Load game metadata
            if loader.load_game(game):
                total_games += 1
                print(f"      ✅ Game metadata loaded")

                # Load play-by-play if requested
                if args.full and game['status'] == 'STATUS_FINAL':
                    plays = fetcher.get_play_by_play(game['game_id'])
                    if plays:
                        plays_loaded = loader.load_play_by_play(game['game_id'], plays)
                        total_plays += plays_loaded
                        print(f"      ✅ {plays_loaded} plays loaded")
                    else:
                        print(f"      ⚠️  No play-by-play data available")
                elif args.full:
                    print(f"      ℹ️  Game not final, skipping play-by-play")
            else:
                print(f"      ❌ Failed to load game")

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Loading complete!")
    print(f"   Games loaded: {total_games}")
    if args.full:
        print(f"   Plays loaded: {total_plays:,}")
    print("=" * 70)

    # Suggest next steps
    if total_games > 0:
        print("\n💡 Next steps:")
        print("   1. Validate database: python scripts/init_local_database.py --stats")
        if not args.full:
            print("   2. Load full play-by-play: python scripts/load_recent_games.py --days 7 --full")
        print("   3. Start using the local database with --context development")

    conn.close()


if __name__ == '__main__':
    main()
