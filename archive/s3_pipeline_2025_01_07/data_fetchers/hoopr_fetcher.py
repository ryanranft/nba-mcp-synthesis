#!/usr/bin/env python3
"""
hoopR Data Fetcher

Fetches NBA game data from ESPN API (hoopR-compatible).
This module provides Python access to the same ESPN data that hoopR uses.

Usage:
    from mcp_server.data_fetchers import HoopRFetcher

    fetcher = HoopRFetcher()

    # Get yesterday's games
    games = fetcher.get_games_for_date('2024-12-02')

    # Fetch play-by-play for a specific game
    pbp_data = fetcher.fetch_play_by_play(game_id=401584889)
"""

import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class HoopRFetcher:
    """Fetches NBA data from ESPN API (hoopR-compatible)"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize fetcher.

        Args:
            rate_limit_delay: Seconds to wait between API requests (default: 1.0)
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; NBA-MCP-Synthesis/1.0)"}
        )

    def get_games_for_date(self, date: str) -> List[Dict]:
        """
        Get all games for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of game dictionaries with game_id, home_team, away_team, status
        """
        try:
            url = f"{self.BASE_URL}/scoreboard"
            params = {"dates": date.replace("-", "")}  # ESPN uses YYYYMMDD format

            logger.info(f"Fetching games for {date} from ESPN API...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            games = []
            for event in data.get("events", []):
                game_id = event.get("id")
                status = event.get("status", {}).get("type", {}).get("name", "unknown")

                competitions = event.get("competitions", [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get("competitors", [])

                home_team = None
                away_team = None
                for competitor in competitors:
                    team_info = {
                        "id": competitor.get("team", {}).get("id"),
                        "name": competitor.get("team", {}).get("displayName"),
                        "abbreviation": competitor.get("team", {}).get("abbreviation"),
                        "score": competitor.get("score"),
                    }

                    if competitor.get("homeAway") == "home":
                        home_team = team_info
                    else:
                        away_team = team_info

                games.append(
                    {
                        "game_id": game_id,
                        "date": date,
                        "status": status,
                        "home_team": home_team,
                        "away_team": away_team,
                        "venue": competition.get("venue", {}).get("fullName"),
                        "attendance": competition.get("attendance"),
                    }
                )

            logger.info(f"✓ Found {len(games)} games for {date}")
            return games

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch games for {date}: {e}")
            return []

    def fetch_play_by_play(self, game_id: str) -> Optional[Dict]:
        """
        Fetch play-by-play data for a game.

        Args:
            game_id: ESPN game ID

        Returns:
            Dictionary with game metadata and play-by-play events
        """
        try:
            url = f"{self.BASE_URL}/summary"
            params = {"event": game_id}

            logger.info(f"Fetching play-by-play for game {game_id}...")

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            # Extract game metadata
            header = data.get("header", {})
            competitions = header.get("competitions", [{}])[0]

            game_data = {
                "game_id": game_id,
                "date": header.get("competitions", [{}])[0].get("date"),
                "season": header.get("season", {}).get("year"),
                "season_type": header.get("season", {}).get("type"),
                "venue": competitions.get("venue", {}).get("fullName"),
                "attendance": competitions.get("attendance"),
                "events": [],
            }

            # Extract play-by-play events
            plays = data.get("plays", [])

            for play in plays:
                event = {
                    "id": play.get("id"),
                    "sequence_number": play.get("sequenceNumber"),
                    "type": play.get("type", {}).get("text"),
                    "text": play.get("text"),
                    "period": play.get("period", {}).get("number"),
                    "clock": play.get("clock", {}).get("displayValue"),
                    "team_id": (
                        play.get("team", {}).get("id") if play.get("team") else None
                    ),
                    "scoring_play": 1 if play.get("scoringPlay") else 0,
                    "shooting_play": 1 if play.get("shootingPlay") else 0,
                    "score_value": play.get("scoreValue"),
                    "home_score": play.get("homeScore"),
                    "away_score": play.get("awayScore"),
                }

                # Extract coordinates if available
                coordinate_data = play.get("coordinate")
                if coordinate_data:
                    event["coordinate_x"] = coordinate_data.get("x")
                    event["coordinate_y"] = coordinate_data.get("y")
                else:
                    event["coordinate_x"] = None
                    event["coordinate_y"] = None

                # Extract participants (players)
                participants = play.get("participants", [])
                if participants:
                    event["athlete_id"] = participants[0].get("athlete", {}).get("id")
                else:
                    event["athlete_id"] = None

                game_data["events"].append(event)

            logger.info(
                f"✓ Fetched {len(game_data['events'])} events for game {game_id}"
            )
            return game_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch play-by-play for game {game_id}: {e}")
            return None

    def get_yesterday_games(self) -> List[str]:
        """
        Get game IDs for yesterday's completed games.

        Returns:
            List of game IDs
        """
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        games = self.get_games_for_date(yesterday)

        # Filter for completed games only
        completed_games = [
            g["game_id"] for g in games if g["status"] in ["STATUS_FINAL", "final"]
        ]

        logger.info(f"Found {len(completed_games)} completed games for {yesterday}")
        return completed_games

    def fetch_games_batch(self, game_ids: List[str]) -> List[Dict]:
        """
        Fetch play-by-play data for multiple games.

        Args:
            game_ids: List of ESPN game IDs

        Returns:
            List of game data dictionaries
        """
        games_data = []

        for i, game_id in enumerate(game_ids, 1):
            logger.info(f"Fetching game {i}/{len(game_ids)}: {game_id}")

            game_data = self.fetch_play_by_play(game_id)
            if game_data:
                games_data.append(game_data)

        logger.info(
            f"✓ Successfully fetched {len(games_data)} of {len(game_ids)} games"
        )
        return games_data
