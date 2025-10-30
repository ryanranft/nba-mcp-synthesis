#!/usr/bin/env python3
"""
Fetch focused player-season panel data (players with 5+ seasons)
This dataset is better suited for PPC (Player Performance Consistency) analysis.
"""

import json
import csv
from pathlib import Path

# This script is meant to be run with the MCP query results piped in
# Usage: Fetch data via MCP tools and save the JSON results to files,
# then this script combines them into a single CSV


def combine_batches_to_csv():
    """Combine JSON batch files into single CSV."""

    data_dir = Path("data/batches")
    output_file = Path("data/player_seasons_focused_panel.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_rows = []

    # Read all batch JSON files
    batch_files = sorted(data_dir.glob("batch_*.json"))

    if not batch_files:
        print(f"No batch files found in {data_dir}")
        return

    for batch_file in batch_files:
        print(f"Reading {batch_file.name}...")
        with open(batch_file) as f:
            data = json.load(f)
            if data.get("success") and "rows" in data:
                all_rows.extend(data["rows"])

    # Write to CSV
    if all_rows:
        print(f"\nWriting {len(all_rows)} records to {output_file}")
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = list(all_rows[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"✓ Successfully created {output_file}")
        print(f"  Total records: {len(all_rows)}")
        print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
    else:
        print("No data to write!")


if __name__ == "__main__":
    combine_batches_to_csv()
