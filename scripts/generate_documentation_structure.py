#!/usr/bin/env python3
"""
Generate complete documentation structure for all 270 recommendations.

This script:
1. Reads master_recommendations.json
2. Maps recommendations to phases
3. Creates directory structure
4. Generates metadata.json files
5. Creates placeholder documentation files
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import re


def slugify(text: str) -> str:
    """Convert text to snake_case slug for directory names."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and hyphens with underscores
    text = re.sub(r"[\s\-]+", "_", text)
    # Remove special characters
    text = re.sub(r"[^\w_]", "", text)
    # Remove multiple underscores
    text = re.sub(r"_+", "_", text)
    # Remove leading/trailing underscores
    text = text.strip("_")
    return text


def map_category_to_phase(category: str) -> int:
    """Map recommendation category to phase number."""
    mapping = {
        # Core categories
        "ML": 5,
        "Machine Learning": 5,
        "Infrastructure": 8,
        "Security": 8,
        "Data": 1,
        "Data Processing": 1,
        "Monitoring": 9,
        "Testing": 7,
        "Architecture": 0,
        "Performance": 8,
        "Statistics": 4,
        "Business": 6,
        # Priority-based fallbacks (lowercase)
        "critical": 0,
        "important": 0,
        "nice_to_have": 0,
        # Default
        "UNKNOWN": 0,
    }

    return mapping.get(category, 0)


def generate_documentation_structure(
    master_recs_path: str, nba_simulator_path: str, dry_run: bool = False
):
    """Generate directory structure for all recommendations."""

    print("=" * 80)
    print("📚 DOCUMENTATION STRUCTURE GENERATOR")
    print("=" * 80)
    print()

    # Load master recommendations
    print(f"📖 Loading recommendations from: {master_recs_path}")
    with open(master_recs_path, "r") as f:
        data = json.load(f)
        recommendations = data.get("recommendations", [])

    print(f"✅ Loaded {len(recommendations)} recommendations")
    print()

    # Statistics
    stats = {
        "total": len(recommendations),
        "by_phase": {},
        "by_priority": {},
        "by_category": {},
        "created_dirs": 0,
        "created_files": 0,
    }

    base_path = Path(nba_simulator_path) / "docs" / "phases"

    # Group recommendations by phase
    phase_recommendations = {}

    for idx, rec in enumerate(recommendations):
        category = rec.get("category", "UNKNOWN")
        phase = map_category_to_phase(category)
        priority = rec.get("priority", "UNKNOWN")

        # Update stats
        stats["by_phase"][phase] = stats["by_phase"].get(phase, 0) + 1
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        if phase not in phase_recommendations:
            phase_recommendations[phase] = []

        phase_recommendations[phase].append(
            {
                "index": idx,
                "recommendation": rec,
                "phase": phase,
            }
        )

    # Create directories for each phase
    for phase in sorted(phase_recommendations.keys()):
        recs = phase_recommendations[phase]
        phase_path = base_path / f"phase_{phase}"

        print(f"📁 Phase {phase}: {len(recs)} recommendations")

        for sub_idx, item in enumerate(recs):
            rec = item["recommendation"]
            global_idx = item["index"]

            title = rec.get("title", f"recommendation_{global_idx}")
            if isinstance(title, dict):
                title = title.get("text", f"recommendation_{global_idx}")
            title = str(title)

            # Create directory name
            slug = slugify(title)
            dir_name = f"{phase}.{sub_idx + 1}_{slug}"

            rec_path = phase_path / dir_name

            if dry_run:
                print(f"   [DRY RUN] Would create: {rec_path}")
                continue

            # Create directory
            rec_path.mkdir(parents=True, exist_ok=True)
            stats["created_dirs"] += 1

            # Create metadata.json
            description = rec.get("description", "")
            if isinstance(description, dict):
                description = description.get("text", "")
            description = str(description)

            metadata = {
                "recommendation_id": global_idx,
                "phase_id": phase,
                "sub_phase_id": sub_idx + 1,
                "full_id": f"{phase}.{sub_idx + 1}",
                "title": title,
                "category": rec.get("category", "UNKNOWN"),
                "priority": rec.get("priority", "UNKNOWN"),
                "description": description,
                "directory": str(rec_path.relative_to(base_path)),
                "technical_details": rec.get("technical_details", ""),
                "implementation_steps": rec.get("implementation_steps", []),
            }

            metadata_file = rec_path / "metadata.json"
            with open(metadata_file, "w") as mf:
                json.dump(metadata, mf, indent=2)
            stats["created_files"] += 1

            # Create placeholder files
            placeholder_files = [
                "README.md",
                "USAGE_GUIDE.md",
            ]

            # Add EXAMPLES.md for CRITICAL items
            if metadata["priority"] == "CRITICAL":
                placeholder_files.append("EXAMPLES.md")

            for filename in placeholder_files:
                filepath = rec_path / filename
                if not filepath.exists():
                    with open(filepath, "w") as f:
                        f.write(f"# {title}\n\n")
                        f.write(f"**Status:** 🔴 Documentation in progress\n\n")
                        f.write(
                            f"<!-- Auto-generated placeholder by generate_documentation_structure.py -->\n"
                        )
                    stats["created_files"] += 1

            print(f"   ✅ {dir_name}")

        print()

    # Print summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()

    print(f"Total Recommendations: {stats['total']}")
    print()

    print("By Phase:")
    for phase in sorted(stats["by_phase"].keys()):
        count = stats["by_phase"][phase]
        print(f"  Phase {phase}: {count} recommendations")
    print()

    print("By Priority:")
    for priority in sorted(stats["by_priority"].keys()):
        count = stats["by_priority"][priority]
        print(f"  {priority}: {count}")
    print()

    print("By Category (Top 10):")
    sorted_categories = sorted(
        stats["by_category"].items(), key=lambda x: x[1], reverse=True
    )
    for category, count in sorted_categories[:10]:
        print(f"  {category}: {count}")
    print()

    if not dry_run:
        print(f"Created Directories: {stats['created_dirs']}")
        print(f"Created Files: {stats['created_files']}")
        print()
        print("✅ Documentation structure generation complete!")
    else:
        print("🔍 Dry run complete. Run without --dry-run to create files.")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate documentation structure for all recommendations"
    )
    parser.add_argument(
        "--master-recs",
        default="analysis_results/master_recommendations.json",
        help="Path to master_recommendations.json",
    )
    parser.add_argument(
        "--nba-simulator",
        default="/Users/ryanranft/nba-simulator-aws",
        help="Path to nba-simulator-aws project",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating files",
    )

    args = parser.parse_args()

    generate_documentation_structure(args.master_recs, args.nba_simulator, args.dry_run)
