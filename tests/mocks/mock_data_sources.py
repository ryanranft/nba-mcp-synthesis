#!/usr/bin/env python3
"""
Mock Data Sources

Provides mock implementations of external data sources
for testing without requiring actual database/API connections.

Phase 10A Week 2 - Agent 4 - Advanced Integrations

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd


# NBA team data
NBA_TEAMS = [
    ("Atlanta Hawks", "Eastern", "Southeast"),
    ("Boston Celtics", "Eastern", "Atlantic"),
    ("Brooklyn Nets", "Eastern", "Atlantic"),
    ("Charlotte Hornets", "Eastern", "Southeast"),
    ("Chicago Bulls", "Eastern", "Central"),
    ("Cleveland Cavaliers", "Eastern", "Central"),
    ("Dallas Mavericks", "Western", "Southwest"),
    ("Denver Nuggets", "Western", "Northwest"),
    ("Detroit Pistons", "Eastern", "Central"),
    ("Golden State Warriors", "Western", "Pacific"),
    ("Houston Rockets", "Western", "Southwest"),
    ("Indiana Pacers", "Eastern", "Central"),
    ("LA Clippers", "Western", "Pacific"),
    ("Los Angeles Lakers", "Western", "Pacific"),
    ("Memphis Grizzlies", "Western", "Southwest"),
    ("Miami Heat", "Eastern", "Southeast"),
    ("Milwaukee Bucks", "Eastern", "Central"),
    ("Minnesota Timberwolves", "Western", "Northwest"),
    ("New Orleans Pelicans", "Western", "Southwest"),
    ("New York Knicks", "Eastern", "Atlantic"),
    ("Oklahoma City Thunder", "Western", "Northwest"),
    ("Orlando Magic", "Eastern", "Southeast"),
    ("Philadelphia 76ers", "Eastern", "Atlantic"),
    ("Phoenix Suns", "Western", "Pacific"),
    ("Portland Trail Blazers", "Western", "Northwest"),
    ("Sacramento Kings", "Western", "Pacific"),
    ("San Antonio Spurs", "Western", "Southwest"),
    ("Toronto Raptors", "Eastern", "Atlantic"),
    ("Utah Jazz", "Western", "Northwest"),
    ("Washington Wizards", "Eastern", "Southeast"),
]

# Sample player names
PLAYER_NAMES = [
    "LeBron James",
    "Stephen Curry",
    "Kevin Durant",
    "Giannis Antetokounmpo",
    "Luka Doncic",
    "Nikola Jokic",
    "Joel Embiid",
    "Jayson Tatum",
    "Anthony Davis",
    "Damian Lillard",
    "Jimmy Butler",
    "Kawhi Leonard",
    "Ja Morant",
    "Devin Booker",
    "Trae Young",
    "Donovan Mitchell",
    "Anthony Edwards",
    "Zion Williamson",
    "LaMelo Ball",
    "Paolo Banchero",
]


def generate_sample_player_stats(
    num_players: int = 100,
    season: str = "2024-25",
) -> pd.DataFrame:
    """
    Generate sample NBA player statistics.

    Args:
        num_players: Number of players to generate
        season: NBA season

    Returns:
        DataFrame with player statistics
    """
    data = []

    for i in range(num_players):
        # Select player name (cycle through or generate)
        if i < len(PLAYER_NAMES):
            player_name = PLAYER_NAMES[i]
        else:
            player_name = f"Player {i + 1}"

        # Generate realistic stats
        games_played = random.randint(40, 82)
        ppg = round(random.uniform(5.0, 30.0), 1)
        rpg = round(random.uniform(2.0, 12.0), 1)
        apg = round(random.uniform(1.0, 10.0), 1)
        fg_pct = round(random.uniform(0.35, 0.55), 3)
        three_p_pct = round(random.uniform(0.25, 0.45), 3)
        ft_pct = round(random.uniform(0.70, 0.95), 3)

        data.append(
            {
                "player_id": f"player_{i + 1:04d}",
                "player_name": player_name,
                "season": season,
                "games_played": games_played,
                "ppg": ppg,
                "rpg": rpg,
                "apg": apg,
                "fg_pct": fg_pct,
                "three_p_pct": three_p_pct,
                "ft_pct": ft_pct,
            }
        )

    return pd.DataFrame(data)


def generate_sample_game_data(
    num_games: int = 100,
    season: str = "2024-25",
    start_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Generate sample NBA game data.

    Args:
        num_games: Number of games to generate
        season: NBA season
        start_date: Starting date for games

    Returns:
        DataFrame with game data
    """
    if start_date is None:
        start_date = datetime(2024, 10, 15)  # Season opener

    data = []

    for i in range(num_games):
        # Random teams
        home_team_idx = random.randint(0, len(NBA_TEAMS) - 1)
        away_team_idx = random.randint(0, len(NBA_TEAMS) - 1)

        # Ensure different teams
        while away_team_idx == home_team_idx:
            away_team_idx = random.randint(0, len(NBA_TEAMS) - 1)

        home_team = NBA_TEAMS[home_team_idx][0]
        away_team = NBA_TEAMS[away_team_idx][0]

        # Generate scores (realistic range)
        home_score = random.randint(85, 130)
        away_score = random.randint(85, 130)

        # Game date (increment by 1-3 days)
        game_date = start_date + timedelta(days=i * random.randint(1, 3))

        # Attendance (realistic range)
        attendance = random.randint(15000, 20000)

        # Game state
        game_state = random.choice(
            ["final", "final", "final", "in_progress", "scheduled"]
        )

        data.append(
            {
                "game_id": f"game_{i + 1:06d}",
                "season": season,
                "game_date": game_date.strftime("%Y-%m-%d"),
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score if game_state == "final" else None,
                "away_score": away_score if game_state == "final" else None,
                "attendance": attendance if game_state != "scheduled" else None,
                "game_state": game_state,
            }
        )

    return pd.DataFrame(data)


def generate_sample_team_data(
    season: str = "2024-25",
) -> pd.DataFrame:
    """
    Generate sample NBA team data.

    Args:
        season: NBA season

    Returns:
        DataFrame with team data
    """
    data = []

    for i, (team_name, conference, division) in enumerate(NBA_TEAMS, start=1):
        # Generate realistic win-loss record
        games_played = random.randint(40, 82)
        wins = random.randint(15, 65)
        losses = games_played - wins
        win_pct = round(wins / games_played, 3) if games_played > 0 else 0.000

        # Extract city and team name
        city = " ".join(team_name.split()[:-1])
        name = team_name.split()[-1]

        data.append(
            {
                "team_id": f"team_{i:02d}",
                "team_name": team_name,
                "city": city,
                "name": name,
                "conference": conference,
                "division": division,
                "season": season,
                "wins": wins,
                "losses": losses,
                "win_pct": win_pct,
            }
        )

    return pd.DataFrame(data)


class MockPostgresConnection:
    """
    Mock PostgreSQL database connection.

    Simulates database queries for testing without actual database.
    """

    def __init__(self, db_name: str = "nba_simulator"):
        """
        Initialize mock Postgres connection.

        Args:
            db_name: Database name
        """
        self.db_name = db_name
        self.connected = True

        # Pre-generate sample data
        self.tables = {
            "player_stats": generate_sample_player_stats(num_players=200),
            "games": generate_sample_game_data(num_games=500),
            "teams": generate_sample_team_data(),
        }

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query (mock).

        Args:
            query: SQL query string

        Returns:
            DataFrame with query results
        """
        query_lower = query.lower()

        # Simple query parsing (mock)
        if "player_stats" in query_lower:
            return self.tables["player_stats"].copy()
        elif "games" in query_lower or "game" in query_lower:
            return self.tables["games"].copy()
        elif "teams" in query_lower or "team" in query_lower:
            return self.tables["teams"].copy()
        else:
            # Return empty DataFrame
            return pd.DataFrame()

    def get_table(self, table_name: str) -> pd.DataFrame:
        """
        Get entire table as DataFrame.

        Args:
            table_name: Name of table

        Returns:
            DataFrame with table data
        """
        if table_name in self.tables:
            return self.tables[table_name].copy()
        else:
            raise ValueError(f"Table '{table_name}' not found")

    def list_tables(self) -> List[str]:
        """List available tables"""
        return list(self.tables.keys())

    def close(self) -> None:
        """Close connection"""
        self.connected = False


class MockS3Client:
    """
    Mock AWS S3 client.

    Simulates S3 operations for testing without actual S3.
    """

    def __init__(self, bucket_name: str = "nba-data-bucket"):
        """
        Initialize mock S3 client.

        Args:
            bucket_name: S3 bucket name
        """
        self.bucket_name = bucket_name
        self.objects: Dict[str, bytes] = {}

    def put_object(self, key: str, body: bytes) -> None:
        """
        Upload object to S3 (mock).

        Args:
            key: Object key
            body: Object body (bytes)
        """
        self.objects[key] = body

    def get_object(self, key: str) -> bytes:
        """
        Download object from S3 (mock).

        Args:
            key: Object key

        Returns:
            Object body (bytes)

        Raises:
            KeyError: If object not found
        """
        if key not in self.objects:
            raise KeyError(f"Object '{key}' not found in bucket '{self.bucket_name}'")
        return self.objects[key]

    def list_objects(self, prefix: str = "") -> List[str]:
        """
        List objects in bucket (mock).

        Args:
            prefix: Key prefix filter

        Returns:
            List of object keys
        """
        if not prefix:
            return list(self.objects.keys())

        return [key for key in self.objects.keys() if key.startswith(prefix)]

    def delete_object(self, key: str) -> None:
        """
        Delete object from S3 (mock).

        Args:
            key: Object key
        """
        if key in self.objects:
            del self.objects[key]


class MockNBAApi:
    """
    Mock NBA API client.

    Simulates NBA API responses for testing without actual API calls.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize mock NBA API client.

        Args:
            api_key: API key (not used in mock)
        """
        self.api_key = api_key
        self.call_count = 0

    def get_player_stats(
        self,
        player_id: str,
        season: str = "2024-25",
    ) -> Dict[str, Any]:
        """
        Get player statistics (mock).

        Args:
            player_id: Player ID
            season: NBA season

        Returns:
            Player statistics dictionary
        """
        self.call_count += 1

        # Generate mock stats
        return {
            "player_id": player_id,
            "player_name": f"Player {player_id}",
            "season": season,
            "games_played": random.randint(40, 82),
            "ppg": round(random.uniform(10.0, 25.0), 1),
            "rpg": round(random.uniform(4.0, 10.0), 1),
            "apg": round(random.uniform(2.0, 8.0), 1),
        }

    def get_game_data(
        self,
        game_id: str,
    ) -> Dict[str, Any]:
        """
        Get game data (mock).

        Args:
            game_id: Game ID

        Returns:
            Game data dictionary
        """
        self.call_count += 1

        # Random teams
        home_team_idx = random.randint(0, len(NBA_TEAMS) - 1)
        away_team_idx = random.randint(0, len(NBA_TEAMS) - 1)

        return {
            "game_id": game_id,
            "home_team": NBA_TEAMS[home_team_idx][0],
            "away_team": NBA_TEAMS[away_team_idx][0],
            "home_score": random.randint(90, 120),
            "away_score": random.randint(90, 120),
            "game_date": datetime.now().strftime("%Y-%m-%d"),
            "game_state": "final",
        }

    def get_team_data(
        self,
        team_id: str,
    ) -> Dict[str, Any]:
        """
        Get team data (mock).

        Args:
            team_id: Team ID

        Returns:
            Team data dictionary
        """
        self.call_count += 1

        # Use team index from ID or random
        try:
            team_idx = int(team_id.split("_")[1]) - 1
            if team_idx < 0 or team_idx >= len(NBA_TEAMS):
                team_idx = 0
        except (IndexError, ValueError):
            team_idx = random.randint(0, len(NBA_TEAMS) - 1)

        team_name, conference, division = NBA_TEAMS[team_idx]
        games_played = random.randint(40, 82)
        wins = random.randint(20, 60)

        return {
            "team_id": team_id,
            "team_name": team_name,
            "conference": conference,
            "division": division,
            "wins": wins,
            "losses": games_played - wins,
            "win_pct": round(wins / games_played, 3),
        }

    def get_call_count(self) -> int:
        """Get number of API calls made"""
        return self.call_count

    def reset_call_count(self) -> None:
        """Reset API call counter"""
        self.call_count = 0
