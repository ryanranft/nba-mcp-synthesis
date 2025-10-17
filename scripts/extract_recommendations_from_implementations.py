#!/usr/bin/env python3
"""
Extract recommendation data from implementation files in nba-simulator-aws.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any


def extract_recommendation_from_file(file_path: str) -> Dict[str, Any]:
    """Extract recommendation data from a single implementation file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract recommendation ID from filename
        filename = os.path.basename(file_path)
        rec_id_match = re.search(r"implement_(.+)\.py", filename)
        rec_id = rec_id_match.group(1) if rec_id_match else filename

        # Extract data from docstring
        docstring_match = re.search(r'"""\s*(.*?)\s*"""', content, re.DOTALL)
        if not docstring_match:
            return None

        docstring = docstring_match.group(1)

        # Extract fields using regex patterns
        title_match = re.search(r"Implementation Script:\s*(.+)", docstring)
        title = title_match.group(1).strip() if title_match else "Unknown Title"

        rec_id_match = re.search(r"Recommendation ID:\s*(.+)", docstring)
        extracted_id = rec_id_match.group(1).strip() if rec_id_match else rec_id

        priority_match = re.search(r"Priority:\s*(.+)", docstring)
        priority = priority_match.group(1).strip() if priority_match else "MEDIUM"

        source_match = re.search(r"Source Book:\s*(.+)", docstring)
        source_book = (
            source_match.group(1).strip() if source_match else "Unknown Source"
        )

        generated_match = re.search(r"Generated:\s*(.+)", docstring)
        generated = generated_match.group(1).strip() if generated_match else None

        impact_match = re.search(r"Expected Impact:\s*(.+)", docstring)
        impact = impact_match.group(1).strip() if impact_match else "MEDIUM"

        time_match = re.search(r"Time Estimate:\s*(.+)", docstring)
        time_estimate = time_match.group(1).strip() if time_match else "Unknown"

        # Extract phase from directory path
        phase_match = re.search(r"/phase_(\d+)/", file_path)
        phase = int(phase_match.group(1)) if phase_match else 0

        # Extract description (everything after "Description:" until next field)
        desc_match = re.search(
            r"Description:\s*(.*?)(?=\n[A-Z][a-z]+:|$)", docstring, re.DOTALL
        )
        description = desc_match.group(1).strip() if desc_match else ""

        return {
            "id": extracted_id,
            "title": title,
            "description": description,
            "priority": priority,
            "source_books": [source_book],
            "phase": phase,
            "category": "ML",  # Default category
            "time_estimate": time_estimate,
            "expected_impact": impact,
            "generated": generated,
            "file_path": file_path,
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def extract_all_recommendations(simulator_path: str) -> List[Dict[str, Any]]:
    """Extract recommendations from all implementation files."""
    recommendations = []

    # Find all implement_*.py files
    phases_dir = Path(simulator_path) / "docs" / "phases"

    if not phases_dir.exists():
        print(f"Phases directory not found: {phases_dir}")
        return recommendations

    for phase_dir in phases_dir.iterdir():
        if phase_dir.is_dir() and phase_dir.name.startswith("phase_"):
            for py_file in phase_dir.glob("implement_*.py"):
                rec = extract_recommendation_from_file(str(py_file))
                if rec:
                    recommendations.append(rec)

    return recommendations


def main():
    """Main function to extract recommendations."""
    simulator_path = "/Users/ryanranft/nba-simulator-aws"

    print("Extracting recommendations from implementation files...")
    recommendations = extract_all_recommendations(simulator_path)

    print(f"Found {len(recommendations)} recommendations")

    # Save to file
    output_file = "analysis_results/extracted_recommendations_from_implementations.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(
            {
                "metadata": {
                    "total_recommendations": len(recommendations),
                    "extraction_timestamp": "2025-01-15T00:00:00Z",
                    "source": "implementation_files",
                },
                "recommendations": recommendations,
            },
            f,
            indent=2,
        )

    print(f"Saved to {output_file}")

    # Print summary by phase
    phase_counts = {}
    for rec in recommendations:
        phase = rec.get("phase", 0)
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    print("\nRecommendations by phase:")
    for phase in sorted(phase_counts.keys()):
        print(f"  Phase {phase}: {phase_counts[phase]} recommendations")


if __name__ == "__main__":
    main()
