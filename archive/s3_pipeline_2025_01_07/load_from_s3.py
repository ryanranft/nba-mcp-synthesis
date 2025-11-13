#!/usr/bin/env python3
"""
Load NBA Data from S3 to Database

Loads scraped game data from S3 and inserts into PostgreSQL database.
Automatically classifies shot zones during insertion.

Usage:
    # Load yesterday's data
    python3 scripts/load_from_s3.py

    # Load specific date
    python3 scripts/load_from_s3.py --date 2024-12-02

    # Dry run (no database changes)
    python3 scripts/load_from_s3.py --dry-run
"""

import argparse
import logging
import sys
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.connectors.s3_connector import S3Connector
from mcp_server.spatial.zone_classifier import classify_shot_espn


# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "load_from_s3.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class S3DatabaseLoader:
    """Loads NBA data from S3 into PostgreSQL"""

    def __init__(self, bucket_name: str, dry_run: bool = False):
        """
        Initialize loader.

        Args:
            bucket_name: S3 bucket name
            dry_run: If True, do not write to database
        """
        self.bucket_name = bucket_name
        self.dry_run = dry_run
        self.conn = None
        self.s3 = S3Connector(bucket_name=bucket_name)

        self.games_loaded = 0
        self.events_inserted = 0
        self.shots_classified = 0
        self.errors = []

    def connect_db(self):
        """Connect to database"""
        load_secrets_hierarchical()

        self.conn = psycopg2.connect(
            host=os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW"),
            port=os.getenv("RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW"),
            database=os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW"),
            user=os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW"),
            password=os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW"),
        )
        logger.info("✓ Connected to database")

    def classify_shots(self, events: List[Dict], game_data: Dict) -> List[Dict]:
        """
        Classify shot zones for shooting events.

        Args:
            events: List of play-by-play events
            game_data: Game metadata (to extract home_team_id)

        Returns:
            Events with shot_zone, shot_distance, shot_angle populated
        """
        # Extract home team ID from game data
        home_team_id = game_data.get("home_team", {}).get("id")

        classified_events = []

        for event in events:
            # Check if this is a shooting event
            if event.get("shooting_play") != 1:
                classified_events.append(event)
                continue

            # Check if coordinates are available
            coord_x = event.get("coordinate_x")
            coord_y = event.get("coordinate_y")

            if coord_x is None or coord_y is None:
                classified_events.append(event)
                continue

            try:
                # Classify shot zone
                classified = classify_shot_espn(
                    espn_x=coord_x,
                    espn_y=coord_y,
                    home_team_id=home_team_id,
                    offensive_team_id=event.get("team_id"),
                    made=(event.get("scoring_play") == 1),
                    points=(event.get("score_value") or 0),
                )

                # Add classification to event
                event["shot_zone"] = classified.zone
                event["shot_distance"] = classified.distance
                event["shot_angle"] = classified.angle

                self.shots_classified += 1

            except Exception as e:
                logger.warning(
                    f'Failed to classify shot in event {event.get("id")}: {e}'
                )

            classified_events.append(event)

        return classified_events

    def insert_game_data(self, game_data: Dict):
        """
        Insert game data into database.

        Args:
            game_data: Dictionary with game metadata and events
        """
        if self.dry_run:
            logger.info(
                f'DRY RUN: Would insert {len(game_data.get("events", []))} events'
            )
            return

        cursor = self.conn.cursor()

        try:
            # Insert game metadata (if not exists)
            game_id = game_data["game_id"]

            cursor.execute(
                """
                INSERT INTO hoopr_schedule (
                    game_id, date, season, season_type,
                    home_team_id, away_team_id, venue, attendance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO NOTHING
            """,
                (
                    game_id,
                    game_data.get("date"),
                    game_data.get("season"),
                    game_data.get("season_type"),
                    game_data.get("home_team", {}).get("id"),
                    game_data.get("away_team", {}).get("id"),
                    game_data.get("venue"),
                    game_data.get("attendance"),
                ),
            )

            # Insert play-by-play events
            events = game_data.get("events", [])

            if events:
                execute_batch(
                    cursor,
                    """
                        INSERT INTO hoopr_play_by_play (
                            id, game_id, sequence_number, type, text,
                            period, clock, team_id, scoring_play, shooting_play,
                            score_value, home_score, away_score,
                            coordinate_x, coordinate_y, athlete_id,
                            shot_zone, shot_distance, shot_angle,
                            home_team_id
                        ) VALUES (
                            %(id)s, %(game_id)s, %(sequence_number)s, %(type)s, %(text)s,
                            %(period)s, %(clock)s, %(team_id)s, %(scoring_play)s, %(shooting_play)s,
                            %(score_value)s, %(home_score)s, %(away_score)s,
                            %(coordinate_x)s, %(coordinate_y)s, %(athlete_id)s,
                            %(shot_zone)s, %(shot_distance)s, %(shot_angle)s,
                            %(home_team_id)s
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            shot_zone = EXCLUDED.shot_zone,
                            shot_distance = EXCLUDED.shot_distance,
                            shot_angle = EXCLUDED.shot_angle
                    """,
                    [
                        {
                            **event,
                            "game_id": game_id,
                            "home_team_id": game_data.get("home_team", {}).get("id"),
                        }
                        for event in events
                    ],
                    page_size=1000,
                )

            self.conn.commit()
            self.events_inserted += len(events)
            self.games_loaded += 1

            logger.info(f"✓ Loaded game {game_id}: {len(events)} events")

        except Exception as e:
            logger.error(f"Failed to insert game {game_id}: {e}")
            self.conn.rollback()
            self.errors.append(f"Game {game_id}: {str(e)}")
            raise

        finally:
            cursor.close()

    def load_date(self, target_date: datetime):
        """
        Load all games for a specific date from S3.

        Args:
            target_date: Date to load
        """
        date_str = target_date.strftime("%Y-%m-%d")

        logger.info("=" * 80)
        logger.info(f"S3 → DATABASE LOAD - {date_str}")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("DRY RUN MODE - No database changes will be made")

        # Download game data from S3
        s3_key = f"daily/{date_str}/games.json"
        local_file = f"/tmp/nba_data/games_{date_str}.json"

        logger.info(f"Downloading s3://{self.bucket_name}/{s3_key}...")

        Path(local_file).parent.mkdir(parents=True, exist_ok=True)

        # Use S3Connector to download
        if not self.s3.download_file(s3_key, local_file):
            logger.error(f"Failed to download data from S3")
            return

        # Load JSON data
        with open(local_file) as f:
            data = json.load(f)

        games = data.get("games", [])
        logger.info(f"Found {len(games)} games in S3 data")

        # Process each game
        for i, game_data in enumerate(games, 1):
            logger.info(f'Processing game {i}/{len(games)}: {game_data.get("game_id")}')

            try:
                # Classify shots
                events = game_data.get("events", [])
                logger.info(f"  Classifying shots in {len(events)} events...")
                classified_events = self.classify_shots(events, game_data)
                game_data["events"] = classified_events

                # Insert into database
                self.insert_game_data(game_data)

            except Exception as e:
                logger.error(f'Error processing game {game_data.get("game_id")}: {e}')
                self.errors.append(f'Game {game_data.get("game_id")}: {str(e)}')
                continue

        # Clean up local file
        Path(local_file).unlink(missing_ok=True)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print load summary report"""
        logger.info("=" * 80)
        logger.info("LOAD SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Games loaded: {self.games_loaded}")
        logger.info(f"Events inserted: {self.events_inserted}")
        logger.info(f"Shots classified: {self.shots_classified}")

        if self.errors:
            logger.warning(f"Errors encountered: {len(self.errors)}")
            for error in self.errors[:10]:
                logger.warning(f"  - {error}")
            if len(self.errors) > 10:
                logger.warning(f"  ... and {len(self.errors) - 10} more errors")
        else:
            logger.info("✅ No errors encountered")

        logger.info("=" * 80)

    def run(self, target_date: Optional[datetime] = None):
        """
        Run S3 load.

        Args:
            target_date: Date to load (default: yesterday)
        """
        try:
            if not self.dry_run:
                self.connect_db()

            # Default to yesterday if no date specified
            if target_date is None:
                target_date = datetime.now() - timedelta(days=1)

            # Load the target date
            self.load_date(target_date)

        finally:
            if self.conn:
                self.conn.close()


def main():
    parser = argparse.ArgumentParser(description="Load NBA data from S3 to database")
    parser.add_argument(
        "--date", help="Date to load (YYYY-MM-DD), defaults to yesterday"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no database changes)"
    )
    parser.add_argument(
        "--bucket",
        default="nba-mcp-synthesis-data",
        help="S3 bucket name (default: nba-mcp-synthesis-data)",
    )

    args = parser.parse_args()

    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = None  # Will default to yesterday

    # Run loader
    loader = S3DatabaseLoader(bucket_name=args.bucket, dry_run=args.dry_run)
    loader.run(target_date=target_date)


if __name__ == "__main__":
    main()
