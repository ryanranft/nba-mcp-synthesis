#!/usr/bin/env python3
"""
Fix unclassified shots by inferring missing team_id from play-by-play context.

This script addresses 82 legitimate shot attempts from 2003-2004 era games
that have NULL team_id values, preventing shot zone classification.

Strategy:
- For free throws: Look back to find the foul call and use that team_id
- For field goals: Find previous play by same athlete and use that team_id
- For edge cases: Look at next play or game context
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)


def get_unclassified_shots(conn):
    """Get all legitimate shots that remain unclassified."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                id, game_id, team_id, home_team_id, athlete_id_1,
                sequence_number, type_text, text,
                coordinate_x, coordinate_y
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND coordinate_x IS NOT NULL
              AND coordinate_y IS NOT NULL
              AND shot_zone IS NULL
              AND team_id IS NULL
            ORDER BY game_id, sequence_number
        """
        )
        return cur.fetchall()


def infer_team_id_from_foul(conn, game_id, sequence_number):
    """Infer team_id by looking back to find the foul call before a free throw."""
    with conn.cursor() as cur:
        # Look for foul calls before this sequence
        cur.execute(
            """
            SELECT team_id
            FROM hoopr_play_by_play
            WHERE game_id = %s
              AND sequence_number < %s
              AND type_text ILIKE '%%foul%%'
              AND team_id IS NOT NULL
            ORDER BY sequence_number DESC
            LIMIT 1
        """,
            (game_id, sequence_number),
        )

        result = cur.fetchone()
        return result[0] if result else None


def infer_team_id_from_athlete(conn, game_id, athlete_id, sequence_number):
    """Infer team_id by finding previous play by the same athlete."""
    with conn.cursor() as cur:
        # Look for previous play by same athlete
        cur.execute(
            """
            SELECT team_id
            FROM hoopr_play_by_play
            WHERE game_id = %s
              AND athlete_id_1 = %s
              AND sequence_number < %s
              AND team_id IS NOT NULL
            ORDER BY sequence_number DESC
            LIMIT 1
        """,
            (game_id, athlete_id, sequence_number),
        )

        result = cur.fetchone()
        return result[0] if result else None


def infer_team_id_from_next_play(conn, game_id, athlete_id, sequence_number):
    """Infer team_id by looking at next play by the same athlete."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT team_id
            FROM hoopr_play_by_play
            WHERE game_id = %s
              AND athlete_id_1 = %s
              AND sequence_number > %s
              AND team_id IS NOT NULL
            ORDER BY sequence_number ASC
            LIMIT 1
        """,
            (game_id, athlete_id, sequence_number),
        )

        result = cur.fetchone()
        return result[0] if result else None


def infer_team_id(conn, shot):
    """
    Infer missing team_id using multiple strategies.

    Returns: (inferred_team_id, inference_method)
    """
    game_id = shot["game_id"]
    sequence_number = shot["sequence_number"]
    athlete_id = shot["athlete_id_1"]
    type_text = shot["type_text"] or ""

    # Strategy 1: For free throws, look back to foul call
    if "free throw" in type_text.lower():
        team_id = infer_team_id_from_foul(conn, game_id, sequence_number)
        if team_id:
            return team_id, "foul_lookback"

    # Strategy 2: Find previous play by same athlete
    if athlete_id:
        team_id = infer_team_id_from_athlete(conn, game_id, athlete_id, sequence_number)
        if team_id:
            return team_id, "athlete_previous"

    # Strategy 3: Find next play by same athlete
    if athlete_id:
        team_id = infer_team_id_from_next_play(
            conn, game_id, athlete_id, sequence_number
        )
        if team_id:
            return team_id, "athlete_next"

    # Strategy 4: Use home team as fallback (50% guess)
    # Only use if coordinates suggest home basket
    if shot["home_team_id"]:
        # ESPN coordinates: negative Y typically means home basket end
        if shot["coordinate_y"] and shot["coordinate_y"] < 0:
            return shot["home_team_id"], "home_guess"

    return None, "failed"


def update_team_id(conn, shot_id, team_id):
    """Update team_id for a specific shot."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE hoopr_play_by_play
            SET team_id = %s
            WHERE id = %s
        """,
            (team_id, shot_id),
        )


def main():
    print("=" * 80)
    print("Fix Unclassified Shots - Infer Missing team_id")
    print("=" * 80)
    print()

    # Load secrets and connect to database
    print("Loading database credentials...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    config = get_database_config()

    print("Connecting to database...")
    conn = psycopg2.connect(**config)
    conn.autocommit = False  # Use transaction

    try:
        # Get unclassified shots
        print("\nFetching unclassified shots...")
        shots = get_unclassified_shots(conn)
        print(f"Found {len(shots)} unclassified shots with NULL team_id")

        if len(shots) == 0:
            print("\n✅ No unclassified shots found! All shots have team_id.")
            return

        print("\n" + "-" * 80)
        print("Inferring missing team_id values...")
        print("-" * 80)

        # Track results
        inference_results = {
            "foul_lookback": 0,
            "athlete_previous": 0,
            "athlete_next": 0,
            "home_guess": 0,
            "failed": 0,
        }

        updates = []

        # Process each shot
        for i, shot in enumerate(shots, 1):
            shot_id = shot["id"]
            game_id = shot["game_id"]
            seq = shot["sequence_number"]
            type_text = (shot["type_text"] or "No Shot")[:30]

            # Infer team_id
            inferred_team_id, method = infer_team_id(conn, shot)

            inference_results[method] += 1

            if inferred_team_id:
                updates.append((shot_id, inferred_team_id, method))
                status = f"✅ {method}: team_id={inferred_team_id}"
            else:
                status = "❌ Could not infer"

            # Print progress
            if i <= 10 or i % 10 == 0 or i == len(shots):
                print(
                    f"[{i:2d}/{len(shots)}] Game {game_id} seq={seq} {type_text:30s} {status}"
                )

        print("\n" + "=" * 80)
        print("Inference Summary:")
        print("=" * 80)
        for method, count in inference_results.items():
            print(f"  {method:20s}: {count:3d} shots")
        print(f"  {'TOTAL':20s}: {len(shots):3d} shots")
        print()

        # Preview updates
        print(f"Ready to update {len(updates)} shots with inferred team_id")

        if len(updates) == 0:
            print("\n⚠️  No team_id values could be inferred. Manual review required.")
            conn.rollback()
            return

        # Ask for confirmation
        print("\nPreview of first 5 updates:")
        for shot_id, team_id, method in updates[:5]:
            shot = next(s for s in shots if s["id"] == shot_id)
            print(
                f"  Shot {shot_id}: game={shot['game_id']}, team_id={team_id} (via {method})"
            )

        response = input("\nProceed with updates? (yes/no): ").strip().lower()

        if response != "yes":
            print("❌ Update cancelled by user")
            conn.rollback()
            return

        # Apply updates
        print("\nApplying updates...")
        for shot_id, team_id, method in updates:
            update_team_id(conn, shot_id, team_id)

        # Commit transaction
        conn.commit()
        print(f"✅ Updated {len(updates)} shots with inferred team_id")

        # Verify results
        print("\nVerifying updates...")
        remaining = get_unclassified_shots(conn)
        print(f"Remaining unclassified shots: {len(remaining)}")

        if len(remaining) == 0:
            print("\n🎉 SUCCESS! All shots now have team_id and can be classified.")
        else:
            print(f"\n⚠️  {len(remaining)} shots still need manual review:")
            for shot in remaining[:5]:
                print(
                    f"   Shot {shot['id']}: game={shot['game_id']}, athlete={shot['athlete_id_1']}"
                )

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()
        print("\nDatabase connection closed")


if __name__ == "__main__":
    main()
