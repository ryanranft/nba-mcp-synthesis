#!/usr/bin/env python3
"""
Fetch player-season panel data and process for GMM analysis.
This script is designed to be called with batch information.
"""

import csv
import json
import sys
import os
from pathlib import Path


def main():
    """Fetch and process player-season panel data."""

    # Configuration
    total_records = 3338
    batch_size = 50  # Smaller batches to avoid context overflow
    output_file = Path("data/player_seasons_panel.csv")

    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file if present
    if output_file.exists():
        output_file.unlink()
        print(f"Removed existing file: {output_file}")

    print(f"=" * 60)
    print(f"Fetching {total_records} player-seasons")
    print(f"Batch size: {batch_size}")
    print(f"Total batches: {(total_records + batch_size - 1) // batch_size}")
    print(f"Output: {output_file}")
    print(f"=" * 60)

    # Query template
    query_template = """
SELECT
    athlete_id::text as player_id,
    CASE
        WHEN EXTRACT(MONTH FROM DATE(game_date)) >= 10 THEN
            EXTRACT(YEAR FROM DATE(game_date))
        ELSE EXTRACT(YEAR FROM DATE(game_date)) - 1
    END as season_year,
    CASE
        WHEN EXTRACT(MONTH FROM DATE(game_date)) >= 10 THEN
            EXTRACT(YEAR FROM DATE(game_date))::text || '-' ||
            RIGHT((EXTRACT(YEAR FROM DATE(game_date)) + 1)::text, 2)
        ELSE
            (EXTRACT(YEAR FROM DATE(game_date)) - 1)::text || '-' ||
            RIGHT(EXTRACT(YEAR FROM DATE(game_date))::text, 2)
    END as season,
    COUNT(*) as games_played,
    ROUND(AVG(points)::numeric, 2) as ppg,
    ROUND(AVG(assists)::numeric, 2) as apg,
    ROUND(AVG(rebounds)::numeric, 2) as rpg,
    ROUND(AVG(minutes)::numeric, 2) as mpg,
    ROUND(SUM(points)::numeric, 0) as total_points,
    ROUND(AVG(CASE WHEN starter = 1 THEN 1.0 ELSE 0.0 END)::numeric, 3) as starter_pct,
    COUNT(DISTINCT team_id) as teams_played_for
FROM hoopr_player_box
WHERE game_date >= '2015-10-01'
    AND game_date < '2024-07-01'
    AND season_type = 2
    AND minutes > 5
    AND active = 1
GROUP BY athlete_id, season_year, season
HAVING COUNT(*) >= 10
ORDER BY athlete_id, season_year
LIMIT {limit} OFFSET {offset}
"""

    # Generate all queries
    queries_file = Path("data/fetch_queries.json")
    queries = []

    for batch_num in range((total_records + batch_size - 1) // batch_size):
        offset = batch_num * batch_size
        query = query_template.format(limit=batch_size, offset=offset).strip()
        queries.append(
            {
                "batch": batch_num + 1,
                "offset": offset,
                "limit": batch_size,
                "query": query,
            }
        )

    # Save queries to file
    with open(queries_file, "w") as f:
        json.dump(queries, f, indent=2)

    print(f"\nGenerated {len(queries)} queries")
    print(f"Saved to: {queries_file}")
    print(f"\nTo fetch data, run these queries via MCP and pipe results to:")
    print(f"  python3 fetch_player_seasons_simple.py")
    print(f"\nOr use the batch fetcher script.")

    return queries_file


if __name__ == "__main__":
    main()
