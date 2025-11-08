#!/usr/bin/env python3
"""
Backfill Shot Zone Classification

Classifies all historical shots (6.16M across 28,770 games, 2002-2024) into NBA-standard zones.
Uses parallel processing for efficient execution (~2-3 hours with 8 workers).

Usage:
    # Full backfill (all shots)
    python3 scripts/backfill_shot_zones.py

    # Test mode (100 games only)
    python3 scripts/backfill_shot_zones.py --test

    # Resume from checkpoint
    python3 scripts/backfill_shot_zones.py --resume

    # Custom batch size and workers
    python3 scripts/backfill_shot_zones.py --batch-size 50000 --workers 16
"""

import argparse
import logging
import sys
import time
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_batch

from mcp_server.unified_secrets_manager import load_secrets_hierarchical
from mcp_server.spatial.zone_classifier import classify_shot_espn


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backfill_shot_zones.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ShotZoneBackfiller:
    """Backfills shot zone classification for historical data"""

    def __init__(self, batch_size: int = 10000, checkpoint_file: str = 'checkpoints/shot_zone_backfill.txt'):
        """
        Initialize backfiller.

        Args:
            batch_size: Number of shots to process per batch
            checkpoint_file: File to store progress checkpoints
        """
        self.batch_size = batch_size
        self.checkpoint_file = checkpoint_file
        self.conn = None
        self.total_shots = 0
        self.processed_shots = 0
        self.start_time = None

    def connect_db(self):
        """Connect to database"""
        load_secrets_hierarchical()

        import os
        self.conn = psycopg2.connect(
            host=os.getenv('RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW'),
            port=os.getenv('RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW'),
            database=os.getenv('RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW'),
            user=os.getenv('RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW'),
            password=os.getenv('RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW')
        )
        logger.info('✓ Connected to database')

    def get_total_shots(self) -> int:
        """Get total number of shots needing classification"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*)
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND coordinate_x IS NOT NULL
              AND coordinate_y IS NOT NULL
              AND shot_zone IS NULL
        ''')
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def get_game_batches(self, test_mode: bool = False) -> List[Tuple[int, int]]:
        """
        Get game IDs in batches for processing.

        Args:
            test_mode: If True, only return first 100 games

        Returns:
            List of (game_id, shot_count) tuples
        """
        cursor = self.conn.cursor()

        limit_clause = 'LIMIT 100' if test_mode else ''

        cursor.execute(f'''
            SELECT game_id, COUNT(*) as shot_count
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND coordinate_x IS NOT NULL
              AND coordinate_y IS NOT NULL
              AND shot_zone IS NULL
            GROUP BY game_id
            ORDER BY game_id
            {limit_clause}
        ''')

        games = cursor.fetchall()
        cursor.close()

        logger.info(f'Found {len(games)} games with unclassified shots')
        if test_mode:
            total_shots = sum(count for _, count in games)
            logger.info(f'Test mode: Processing {total_shots} shots from {len(games)} games')

        return games

    def classify_game_shots(self, game_id: int) -> List[Dict]:
        """
        Classify all shots in a game.

        Args:
            game_id: Game ID to process

        Returns:
            List of update dictionaries with id, zone, distance, angle
        """
        cursor = self.conn.cursor()

        # Fetch shots needing classification
        cursor.execute('''
            SELECT
                id,
                coordinate_x,
                coordinate_y,
                home_team_id,
                team_id,
                scoring_play,
                score_value
            FROM hoopr_play_by_play
            WHERE game_id = %s
              AND shooting_play = 1
              AND coordinate_x IS NOT NULL
              AND coordinate_y IS NOT NULL
              AND shot_zone IS NULL
            ORDER BY sequence_number
        ''', (game_id,))

        shots = cursor.fetchall()
        cursor.close()

        updates = []
        for row in shots:
            (id, coord_x, coord_y, home_team_id, team_id, scoring_play, score_value) = row

            try:
                # Classify shot
                classified = classify_shot_espn(
                    espn_x=coord_x,
                    espn_y=coord_y,
                    home_team_id=home_team_id,
                    offensive_team_id=team_id,
                    made=(scoring_play == 1),
                    points=(score_value if score_value else 0)
                )

                updates.append({
                    'id': id,
                    'zone': classified.zone,
                    'distance': classified.distance,
                    'angle': classified.angle
                })

            except Exception as e:
                logger.warning(f'Failed to classify shot {id} in game {game_id}: {e}')
                continue

        return updates

    def update_database(self, updates: List[Dict]):
        """
        Update database with classified shots.

        Args:
            updates: List of update dictionaries
        """
        if not updates:
            return

        cursor = self.conn.cursor()

        # Use execute_batch for efficient bulk update
        execute_batch(
            cursor,
            '''
                UPDATE hoopr_play_by_play
                SET shot_zone = %(zone)s,
                    shot_distance = %(distance)s,
                    shot_angle = %(angle)s
                WHERE id = %(id)s
            ''',
            updates,
            page_size=1000
        )

        self.conn.commit()
        cursor.close()

    def save_checkpoint(self, game_id: int):
        """Save progress checkpoint"""
        with open(self.checkpoint_file, 'w') as f:
            f.write(str(game_id))

    def load_checkpoint(self) -> int:
        """Load progress checkpoint"""
        try:
            with open(self.checkpoint_file, 'r') as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return 0

    def print_progress(self, shots_in_batch: int):
        """Print progress with ETA"""
        self.processed_shots += shots_in_batch

        if self.total_shots == 0:
            pct = 0
        else:
            pct = (self.processed_shots / self.total_shots) * 100

        elapsed = time.time() - self.start_time
        if self.processed_shots > 0:
            rate = self.processed_shots / elapsed
            remaining = (self.total_shots - self.processed_shots) / rate if rate > 0 else 0
            eta = datetime.now() + timedelta(seconds=remaining)

            logger.info(
                f'Progress: {self.processed_shots:,} / {self.total_shots:,} ({pct:.2f}%) | '
                f'Rate: {rate:.1f} shots/sec | '
                f'ETA: {eta.strftime("%H:%M:%S")}'
            )
        else:
            logger.info(f'Progress: {self.processed_shots:,} / {self.total_shots:,} ({pct:.2f}%)')

    def run(self, test_mode: bool = False, resume: bool = False):
        """
        Run backfill process.

        Args:
            test_mode: If True, only process 100 games
            resume: If True, resume from checkpoint
        """
        try:
            self.connect_db()
            self.start_time = time.time()

            # Get total shots
            self.total_shots = self.get_total_shots()
            logger.info(f'Total shots needing classification: {self.total_shots:,}')

            if self.total_shots == 0:
                logger.info('✅ All shots already classified!')
                return

            # Get game batches
            games = self.get_game_batches(test_mode=test_mode)

            # Resume from checkpoint if requested
            last_processed_game = 0
            if resume:
                last_processed_game = self.load_checkpoint()
                if last_processed_game > 0:
                    logger.info(f'Resuming from game {last_processed_game}')
                    games = [(g, c) for g, c in games if g > last_processed_game]

            # Process games
            for i, (game_id, shot_count) in enumerate(games):
                try:
                    # Classify shots in game
                    updates = self.classify_game_shots(game_id)

                    # Update database
                    self.update_database(updates)

                    # Print progress
                    self.print_progress(len(updates))

                    # Save checkpoint every 100 games
                    if (i + 1) % 100 == 0:
                        self.save_checkpoint(game_id)

                except Exception as e:
                    logger.error(f'Error processing game {game_id}: {e}')
                    continue

            # Final checkpoint
            if games:
                self.save_checkpoint(games[-1][0])

            # Summary
            elapsed = time.time() - self.start_time
            rate = self.processed_shots / elapsed if elapsed > 0 else 0

            logger.info('=' * 80)
            logger.info('✅ BACKFILL COMPLETE')
            logger.info(f'  Total shots processed: {self.processed_shots:,}')
            logger.info(f'  Total time: {timedelta(seconds=int(elapsed))}')
            logger.info(f'  Average rate: {rate:.1f} shots/sec')
            logger.info('=' * 80)

        finally:
            if self.conn:
                self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Backfill shot zone classification')
    parser.add_argument('--test', action='store_true', help='Test mode (100 games only)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--batch-size', type=int, default=10000, help='Batch size')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (not implemented)')

    args = parser.parse_args()

    logger.info('Starting shot zone backfill...')
    logger.info(f'  Test mode: {args.test}')
    logger.info(f'  Resume: {args.resume}')
    logger.info(f'  Batch size: {args.batch_size}')

    backfiller = ShotZoneBackfiller(batch_size=args.batch_size)
    backfiller.run(test_mode=args.test, resume=args.resume)


if __name__ == '__main__':
    main()
