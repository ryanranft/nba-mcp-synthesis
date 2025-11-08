#!/usr/bin/env python3
"""
Daily NBA Data Synchronization Script

Automatically fetches and processes new NBA games daily:
- Fetches yesterday's completed games from hoopR/ESPN
- Downloads play-by-play events
- Classifies shot zones automatically
- Updates database with new data
- Generates daily summary report

Usage:
    # Sync yesterday's games
    python3 scripts/daily_data_sync.py

    # Sync specific date
    python3 scripts/daily_data_sync.py --date 2024-12-01

    # Dry run (no database updates)
    python3 scripts/daily_data_sync.py --dry-run

Schedule with cron:
    0 6 * * * /path/to/run_daily_sync.sh
"""

import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.spatial.zone_classifier import classify_shot_espn


# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'daily_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyDataSync:
    """Syncs daily NBA data from hoopR/ESPN to database"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize sync manager.

        Args:
            dry_run: If True, do not upload to S3
        """
        self.dry_run = dry_run
        self.games_processed = 0
        self.events_inserted = 0
        self.errors = []

    def get_yesterday_games(self) -> List[str]:
        """
        Get game IDs for yesterday's completed games.

        Returns:
            List of game IDs
        """
        from mcp_server.data_fetchers import HoopRFetcher

        fetcher = HoopRFetcher()
        game_ids = fetcher.get_yesterday_games()

        logger.info(f'Found {len(game_ids)} completed games from ESPN API')
        return game_ids

    def fetch_game_data(self, game_id: str) -> Optional[Dict]:
        """
        Fetch play-by-play data for a game.

        Args:
            game_id: Game ID to fetch

        Returns:
            Dictionary with game data including play-by-play events
        """
        from mcp_server.data_fetchers import HoopRFetcher

        fetcher = HoopRFetcher()
        game_data = fetcher.fetch_play_by_play(game_id)

        return game_data

    def classify_shots(self, events: List[Dict]) -> List[Dict]:
        """
        Classify shot zones for shooting events.

        Args:
            events: List of play-by-play events

        Returns:
            Events with shot_zone, shot_distance, shot_angle populated
        """
        classified_events = []

        for event in events:
            # Check if this is a shooting event
            if event.get('shooting_play') != 1:
                classified_events.append(event)
                continue

            # Check if coordinates are available
            coord_x = event.get('coordinate_x')
            coord_y = event.get('coordinate_y')

            if coord_x is None or coord_y is None:
                classified_events.append(event)
                continue

            try:
                # Classify shot zone
                classified = classify_shot_espn(
                    espn_x=coord_x,
                    espn_y=coord_y,
                    home_team_id=event.get('home_team_id'),
                    offensive_team_id=event.get('team_id'),
                    made=(event.get('scoring_play') == 1),
                    points=(event.get('score_value') or 0)
                )

                # Add classification to event
                event['shot_zone'] = classified.zone
                event['shot_distance'] = classified.distance
                event['shot_angle'] = classified.angle

                self.shots_classified += 1

            except Exception as e:
                logger.warning(f'Failed to classify shot in event {event.get("id")}: {e}')

            classified_events.append(event)

        return classified_events

    def upload_to_s3(self, games_data: List[Dict], date: str):
        """
        Upload game data to S3.

        Args:
            games_data: List of game dictionaries
            date: Date string (YYYY-MM-DD)
        """
        if self.dry_run:
            logger.info(f'DRY RUN: Would upload {len(games_data)} games to S3')
            return

        from mcp_server.connectors.s3_connector import S3Connector

        # Get S3 bucket name from environment or use default
        bucket_name = os.getenv('S3_BUCKET_NBA_MCP_SYNTHESIS', 'nba-mcp-synthesis-data')

        s3 = S3Connector(bucket_name=bucket_name)

        # Upload game data
        s3_key = s3.upload_game_data(date=date, games_data=games_data)

        if s3_key:
            logger.info(f'✅ Uploaded data to s3://{bucket_name}/{s3_key}')
        else:
            logger.error(f'Failed to upload data to S3')
            self.errors.append(f'S3 upload failed for {date}')

    def sync_date(self, target_date: datetime):
        """
        Sync all games for a specific date.

        WORKFLOW:
        1. Fetch games from ESPN API (local scraping)
        2. Fetch play-by-play data for each game
        3. Upload scraped data to S3
        4. (Database loading done separately by load_from_s3.py)

        Args:
            target_date: Date to sync (typically yesterday)
        """
        date_str = target_date.strftime('%Y-%m-%d')

        logger.info('=' * 80)
        logger.info(f'DAILY DATA SYNC - {date_str}')
        logger.info('=' * 80)
        logger.info('WORKFLOW: Local Scraping → S3 Upload')
        logger.info('=' * 80)

        if self.dry_run:
            logger.info('DRY RUN MODE - No S3 uploads will be made')

        # Step 1: Get games for target date
        logger.info(f'Step 1: Fetching games from ESPN API for {date_str}...')

        from mcp_server.data_fetchers import HoopRFetcher

        fetcher = HoopRFetcher()
        games_list = fetcher.get_games_for_date(date_str)

        # Filter for completed games only
        completed_games = [g for g in games_list if g['status'] in ['STATUS_FINAL', 'final']]
        game_ids = [g['game_id'] for g in completed_games]

        if not game_ids:
            logger.info('No completed games found for this date')
            return

        logger.info(f'Found {len(game_ids)} completed games to process')

        # Step 2: Fetch play-by-play data for each game
        logger.info(f'Step 2: Fetching play-by-play data from ESPN API...')

        games_data = []

        for i, game_id in enumerate(game_ids, 1):
            logger.info(f'Processing game {i}/{len(game_ids)}: {game_id}')

            try:
                # Fetch game data
                game_data = self.fetch_game_data(game_id)

                if not game_data:
                    logger.warning(f'No data retrieved for game {game_id}')
                    self.errors.append(f'Game {game_id}: No data')
                    continue

                # Add game metadata from initial fetch
                game_info = next((g for g in completed_games if g['game_id'] == game_id), {})
                game_data['home_team'] = game_info.get('home_team')
                game_data['away_team'] = game_info.get('away_team')

                # Store for batch upload
                games_data.append(game_data)

                self.games_processed += 1
                self.events_inserted += len(game_data.get('events', []))

            except Exception as e:
                logger.error(f'Error processing game {game_id}: {e}')
                self.errors.append(f'Game {game_id}: {str(e)}')
                continue

        # Step 3: Upload to S3
        if games_data:
            logger.info(f'Step 3: Uploading {len(games_data)} games to S3...')
            self.upload_to_s3(games_data, date_str)
        else:
            logger.warning('No games to upload')

        # Generate summary
        self.print_summary()

    def print_summary(self):
        """Print sync summary report"""
        logger.info('=' * 80)
        logger.info('SYNC SUMMARY')
        logger.info('=' * 80)
        logger.info(f'Games processed: {self.games_processed}')
        logger.info(f'Events inserted: {self.events_inserted}')
        logger.info(f'Shots classified: {self.shots_classified}')

        if self.errors:
            logger.warning(f'Errors encountered: {len(self.errors)}')
            for error in self.errors[:10]:  # Show first 10 errors
                logger.warning(f'  - {error}')
            if len(self.errors) > 10:
                logger.warning(f'  ... and {len(self.errors) - 10} more errors')
        else:
            logger.info('✅ No errors encountered')

        logger.info('=' * 80)

    def run(self, target_date: Optional[datetime] = None):
        """
        Run daily sync.

        WORKFLOW:
        1. Scrape data locally from ESPN API
        2. Upload to S3
        3. (Database loading happens separately via load_from_s3.py)

        Args:
            target_date: Date to sync (default: yesterday)
        """
        # Load AWS credentials for S3
        load_secrets_hierarchical()

        # Default to yesterday if no date specified
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        # Sync the target date
        self.sync_date(target_date)


def main():
    parser = argparse.ArgumentParser(description='Daily NBA data synchronization')
    parser.add_argument('--date', help='Date to sync (YYYY-MM-DD), defaults to yesterday')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no database changes)')

    args = parser.parse_args()

    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error(f'Invalid date format: {args.date}. Use YYYY-MM-DD')
            sys.exit(1)
    else:
        target_date = None  # Will default to yesterday

    # Run sync
    syncer = DailyDataSync(dry_run=args.dry_run)
    syncer.run(target_date=target_date)


if __name__ == '__main__':
    main()
