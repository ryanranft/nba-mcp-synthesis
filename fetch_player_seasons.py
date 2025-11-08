#!/usr/bin/env python3
"""
Fetch player-season panel data from MCP database in small batches
and write directly to CSV to avoid context overflow.
"""

import csv
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def fetch_player_seasons():
    """Fetch player-season data in batches and write to CSV."""

    # Configuration
    batch_size = 100
    total_records = 3338
    output_file = "data/player_seasons_panel.csv"

    # SQL query template
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

    print(f"Fetching {total_records} player-seasons in batches of {batch_size}...")
    print(f"Output: {output_file}")

    # Connect to MCP server
    server_params = StdioServerParameters(
        command="uv", args=["run", "mcp_server/nba_server.py"], env=None
    )

    total_fetched = 0
    header_written = False

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            with open(output_file, "w", newline="") as csvfile:
                writer = None

                # Fetch in batches
                for offset in range(0, total_records, batch_size):
                    query = query_template.format(limit=batch_size, offset=offset)

                    # Call query_database tool
                    result = await session.call_tool(
                        "query_database", arguments={"sql": query}
                    )

                    # Parse result
                    if result.content:
                        data = json.loads(result.content[0].text)

                        if data.get("success") and "rows" in data:
                            rows = data["rows"]

                            if rows:
                                # Write header on first batch
                                if not header_written:
                                    fieldnames = list(rows[0].keys())
                                    writer = csv.DictWriter(
                                        csvfile, fieldnames=fieldnames
                                    )
                                    writer.writeheader()
                                    header_written = True

                                # Write rows
                                writer.writerows(rows)
                                total_fetched += len(rows)

                                print(
                                    f"  Fetched {total_fetched}/{total_records} records ({offset + batch_size} offset)"
                                )
                        else:
                            print(
                                f"Error in batch at offset {offset}: {data.get('error', 'Unknown error')}"
                            )
                            sys.exit(1)

    print(f"\n✓ Successfully fetched {total_fetched} player-seasons")
    print(f"  Saved to: {output_file}")
    return total_fetched


if __name__ == "__main__":
    import asyncio

    asyncio.run(fetch_player_seasons())
