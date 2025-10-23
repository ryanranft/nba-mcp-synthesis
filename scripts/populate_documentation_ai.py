#!/usr/bin/env python3
"""
Populate documentation files using AI (Claude 3.7 Sonnet).

This script:
1. Finds all directories with metadata.json
2. Reads templates
3. Uses Claude AI to generate comprehensive documentation
4. Writes README.md, USAGE_GUIDE.md, EXAMPLES.md (if CRITICAL)
5. Tracks progress and handles rate limits
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

try:
    from anthropic import AsyncAnthropic
except ImportError:
    print("❌ Error: anthropic package not installed")
    print("Run: pip install anthropic")
    exit(1)


# Load README template
README_TEMPLATE = """# {title}

**Status:** {status}
**Priority:** {priority}
**Category:** {category}
**Phase:** Phase {phase}
**Estimated Time:** TBD
**Dependencies:** TBD

---

## Overview

### What This Implements
{description}

### Key Benefits
- TBD

### When to Use This
- TBD

---

## Technical Details

### Architecture
TBD

### Implementation Components
TBD

### Technology Stack
- Languages: Python 3.11
- Frameworks: FastAPI
- AWS Services: TBD
- Libraries: TBD

---

## Implementation Guide

### Prerequisites
- [ ] Phase {phase} foundation complete
- [ ] Dependencies installed

### Step-by-Step Implementation

#### Step 1: Setup
```bash
# TBD
```

---

## Panel Data Integration

### How This Works with Panel Data

**Panel data structure:**
```
(game_id, timestamp) -> player_stats
```

**Integration points:**
TBD

---

## Code Examples

### Basic Usage
```python
# TBD
```

---

## Workflow References

**Related Workflows:**
- TBD

---

## Performance & Costs

### Performance Metrics
- TBD

### Cost Analysis
- TBD

---

## Troubleshooting

### Common Issues
TBD

---

**Last Updated:** {date}
**Maintained By:** NBA Simulator Team
"""


USAGE_GUIDE_TEMPLATE = """# {title} - Usage Guide

**Quick Start:** See below for 2-minute setup
**Full Documentation:** [README.md](README.md)

---

## Quick Start

### Installation
```bash
pip install package-name
```

### Minimal Example
```python
# TBD
```

---

## API Reference

### Main Classes

TBD

---

## Configuration Reference

TBD

---

## Output Interpretation

TBD

---

## Advanced Usage

TBD

---

## Troubleshooting

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Last Updated:** {date}
**Version:** 1.0.0
"""


class DocumentationPopulator:
    """Populate documentation using AI."""

    def __init__(self, api_key: Optional[str] = None, dry_run: bool = False):
        """Initialize with Anthropic API key."""
        self.dry_run = dry_run

        if not dry_run:
            if api_key:
                self.client = AsyncAnthropic(api_key=api_key)
            else:
                # Will use ANTHROPIC_API_KEY environment variable
                self.client = AsyncAnthropic()

        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_cost": 0.0,
        }

    async def populate_readme(
        self, metadata: Dict, rec_path: Path, codebase_context: str = ""
    ) -> bool:
        """Generate README.md using AI."""

        if self.dry_run:
            print(f"   [DRY RUN] Would generate README.md")
            return True

        prompt = f"""You are a technical documentation expert for an NBA simulation system built on AWS.

Generate a comprehensive README.md file for this recommendation:

**Title:** {metadata['title']}
**Priority:** {metadata['priority']}
**Category:** {metadata['category']}
**Phase:** Phase {metadata['phase_id']}
**Description:** {metadata['description']}

**Technical Details:** {metadata.get('technical_details', 'N/A')}

**Implementation Steps:**
{chr(10).join(['- ' + str(step) for step in metadata.get('implementation_steps', [])])}

**System Context:**
- Project: NBA Simulator AWS (panel data basketball simulation)
- Stack: Python 3.11, FastAPI, PostgreSQL, AWS Lambda/RDS/S3
- Data Structure: (game_id, timestamp) -> player_stats (panel data)
- ML Framework: scikit-learn, XGBoost, PyTorch

**Requirements:**
1. Write ~400 lines of comprehensive documentation
2. Include real, working code examples (Python)
3. Provide step-by-step implementation guide
4. Explain panel data integration
5. Include troubleshooting section
6. Use markdown formatting
7. Be specific and actionable

**Structure to follow:**
- Overview (~50 lines)
- Technical Details (~100 lines)
- Implementation Guide (~100 lines)
- Panel Data Integration (~50 lines)
- Code Examples (~50 lines)
- Workflow References (~20 lines)
- Performance & Costs (~20 lines)
- Troubleshooting (~30 lines)

Generate the complete README.md content now. Use markdown formatting.
Start with: # {metadata['title']}
"""

        try:
            response = await self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            self.stats["total_cost"] += cost

            # Write README.md
            readme_path = rec_path / "README.md"
            with open(readme_path, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"   ❌ Error generating README: {e}")
            return False

    async def populate_usage_guide(self, metadata: Dict, rec_path: Path) -> bool:
        """Generate USAGE_GUIDE.md using AI."""

        if self.dry_run:
            print(f"   [DRY RUN] Would generate USAGE_GUIDE.md")
            return True

        prompt = f"""Generate a comprehensive USAGE_GUIDE.md for: {metadata['title']}

This is an API reference and configuration guide (~300 lines).

Include:
1. Quick Start (~30 lines)
2. API Reference (~100 lines) - Classes, methods, parameters
3. Configuration Reference (~50 lines) - YAML/ENV examples
4. Output Interpretation (~50 lines) - Response structures
5. Advanced Usage (~40 lines) - Async, batch, streaming
6. Troubleshooting (~30 lines) - Common issues

Use markdown. Include working code examples in Python.
Start with: # {metadata['title']} - Usage Guide
"""

        try:
            response = await self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=3072,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            self.stats["total_cost"] += cost

            # Write USAGE_GUIDE.md
            usage_path = rec_path / "USAGE_GUIDE.md"
            with open(usage_path, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"   ❌ Error generating USAGE_GUIDE: {e}")
            return False

    async def populate_single_recommendation(
        self, metadata_file: Path, skip_existing: bool = True
    ) -> bool:
        """Populate documentation for a single recommendation."""

        rec_path = metadata_file.parent

        # Load metadata
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        title = metadata.get("title", "Unknown")
        priority = metadata.get("priority", "UNKNOWN")

        print(f"📝 {metadata.get('full_id', '?')}: {title} ({priority})")

        # Check if already populated (skip if README > 100 lines)
        readme_path = rec_path / "README.md"
        if skip_existing and readme_path.exists():
            with open(readme_path, "r") as f:
                lines = f.readlines()
                if len(lines) > 100:
                    print(f"   ⏭️  Skipped (already populated)")
                    self.stats["skipped"] += 1
                    return True

        # Generate README.md
        success_readme = await self.populate_readme(metadata, rec_path)

        # Generate USAGE_GUIDE.md
        success_usage = await self.populate_usage_guide(metadata, rec_path)

        # Generate EXAMPLES.md for CRITICAL items
        # (TODO: implement if needed)

        self.stats["processed"] += 1

        if success_readme and success_usage:
            print(f"   ✅ Complete")
            self.stats["success"] += 1
            return True
        else:
            print(f"   ⚠️  Partial (some files failed)")
            self.stats["failed"] += 1
            return False

    async def populate_by_priority(
        self, base_path: Path, priority: str, batch_size: int = 5
    ):
        """Populate all recommendations with specific priority."""

        print()
        print("=" * 80)
        print(f"📚 Populating {priority} Recommendations")
        print("=" * 80)
        print()

        # Find all metadata.json files with this priority
        metadata_files = []
        for metadata_file in base_path.rglob("metadata.json"):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            if metadata.get("priority") == priority:
                metadata_files.append(metadata_file)

        print(f"Found {len(metadata_files)} {priority} recommendations")
        print()

        # Process in batches to avoid rate limits
        for i in range(0, len(metadata_files), batch_size):
            batch = metadata_files[i : i + batch_size]

            print(
                f"Batch {i//batch_size + 1}/{(len(metadata_files)-1)//batch_size + 1}"
            )

            tasks = []
            for metadata_file in batch:
                task = self.populate_single_recommendation(metadata_file)
                tasks.append(task)

            # Run batch in parallel
            await asyncio.gather(*tasks)

            # Rate limiting: wait 2 seconds between batches
            if i + batch_size < len(metadata_files):
                await asyncio.sleep(2)

        print()
        print(f"✅ {priority} recommendations complete")
        print()


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Populate documentation using AI")
    parser.add_argument(
        "--nba-simulator",
        default="/Users/ryanranft/nba-simulator-aws",
        help="Path to nba-simulator-aws project",
    )
    parser.add_argument(
        "--priority",
        choices=["CRITICAL", "IMPORTANT", "NICE_TO_HAVE", "ALL"],
        default="CRITICAL",
        help="Which priority level to process",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of recommendations to process in parallel",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without calling AI",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip recommendations that already have documentation",
    )

    args = parser.parse_args()

    base_path = Path(args.nba_simulator) / "docs" / "phases"

    # Initialize populator
    populator = DocumentationPopulator(dry_run=args.dry_run)

    # Process by priority
    priorities = (
        ["CRITICAL", "IMPORTANT", "NICE_TO_HAVE"]
        if args.priority == "ALL"
        else [args.priority]
    )

    start_time = time.time()

    for priority in priorities:
        await populator.populate_by_priority(base_path, priority, args.batch_size)

    # Print summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()
    print(f"Processed: {populator.stats['processed']}")
    print(f"Success: {populator.stats['success']}")
    print(f"Failed: {populator.stats['failed']}")
    print(f"Skipped: {populator.stats['skipped']}")
    print()
    print(f"Total Cost: ${populator.stats['total_cost']:.2f}")
    print(f"Time Elapsed: {time.time() - start_time:.1f}s")
    print()
    print("✅ Documentation population complete!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
