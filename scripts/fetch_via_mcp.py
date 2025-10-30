#!/usr/bin/env python3
"""
Generate SQL queries for fetching player-season data via MCP in batches.
"""

# Base query template
query_template = """
WITH player_seasons AS (
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
),
players_with_5plus_seasons AS (
    SELECT player_id
    FROM player_seasons
    GROUP BY player_id
    HAVING COUNT(*) >= 5
)
SELECT ps.*
FROM player_seasons ps
INNER JOIN players_with_5plus_seasons p5 ON ps.player_id = p5.player_id
ORDER BY ps.player_id, ps.season_year
LIMIT {limit} OFFSET {offset}
"""

# Generate queries for 4 batches
batch_size = 700
total_records = 2758
num_batches = (total_records + batch_size - 1) // batch_size

print(
    "Copy these queries and run them via MCP, saving results to data/batches/batch_N.json:\n"
)
print("=" * 70)

for i in range(num_batches):
    offset = i * batch_size
    query = query_template.format(limit=batch_size, offset=offset)
    print(f"\n### Batch {i+1} (offset {offset}, limit {batch_size}) ###")
    print(f"Save to: data/batches/batch_{i+1}.json")
    print("-" * 70)
    print(query.strip())
    print("=" * 70)
