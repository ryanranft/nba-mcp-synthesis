#!/usr/bin/env python3
"""
Process player-season data from JSON input and append to CSV.
Usage: echo '<json_data>' | python3 fetch_player_seasons_simple.py
"""

import csv
import json
import sys
import os


def process_batch():
    """Read JSON from stdin and append to CSV."""

    output_file = "data/player_seasons_panel.csv"

    # Read JSON from stdin
    input_data = sys.stdin.read()

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not data.get("success"):
        print(f"Query failed: {data.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    rows = data.get("rows", [])

    if not rows:
        print("No rows in result", file=sys.stderr)
        return

    # Check if file exists
    file_exists = os.path.exists(output_file)

    # Append to CSV
    with open(output_file, "a", newline="") as csvfile:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)

    print(f"Appended {len(rows)} rows to {output_file}")


if __name__ == "__main__":
    process_batch()
