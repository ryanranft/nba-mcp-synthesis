#!/usr/bin/env python3
"""
Automated fetching using saved MCP results.
This script is designed to work with manually saved MCP query results.
"""

import json
import csv
import sys
from pathlib import Path


def main():
    """Process MCP results from stdin and append to batch file."""

    if len(sys.argv) < 2:
        print("Usage: <mcp_query_output> | python3 automated_fetch.py <batch_number>")
        sys.exit(1)

    batch_num = sys.argv[1]
    output_dir = Path("data/batches")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"batch_{batch_num}.json"

    # Read JSON from stdin
    input_data = sys.stdin.read()

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Save to file
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    if data.get("success"):
        rows = data.get("rows", [])
        print(f"✓ Saved batch {batch_num}: {len(rows)} records to {output_file}")
    else:
        print(
            f"✗ Batch {batch_num} failed: {data.get('error', 'Unknown error')}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
