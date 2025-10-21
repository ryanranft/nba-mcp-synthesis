#!/usr/bin/env python3
"""
Audit Recommendations by Target Project

Scans all recommendation READMEs to determine which project they target:
- nba-simulator-aws (the NBA prediction system)
- nba-mcp-synthesis (this MCP system)
- both
- unclear
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_recommendation(rec_dir: Path) -> dict:
    """Analyze a single recommendation directory."""
    readme = rec_dir / "README.md"

    if not readme.exists():
        return {
            "name": rec_dir.name,
            "target": "no_readme",
            "confidence": "none"
        }

    content = readme.read_text().lower()

    # Keywords for each target
    simulator_keywords = [
        "nba-simulator-aws",
        "nba simulator",
        "simulator",
        "prediction system",
        "game prediction",
        "player performance",
        "nba analytics",
        "betting",
        "odds"
    ]

    mcp_keywords = [
        "nba-mcp-synthesis",
        "mcp system",
        "mcp server",
        "book analysis",
        "recommendation generation",
        "workflow",
        "convergence"
    ]

    # Count mentions
    simulator_score = sum(1 for kw in simulator_keywords if kw in content)
    mcp_score = sum(1 for kw in mcp_keywords if kw in content)

    # Determine target
    if simulator_score > 0 and mcp_score == 0:
        target = "nba-simulator-aws"
        confidence = "high" if simulator_score >= 3 else "medium"
    elif mcp_score > 0 and simulator_score == 0:
        target = "nba-mcp-synthesis"
        confidence = "high" if mcp_score >= 3 else "medium"
    elif simulator_score > 0 and mcp_score > 0:
        if simulator_score > mcp_score * 2:
            target = "nba-simulator-aws"
            confidence = "medium"
        elif mcp_score > simulator_score * 2:
            target = "nba-mcp-synthesis"
            confidence = "medium"
        else:
            target = "both"
            confidence = "low"
    else:
        target = "unclear"
        confidence = "none"

    return {
        "name": rec_dir.name,
        "target": target,
        "confidence": confidence,
        "simulator_score": simulator_score,
        "mcp_score": mcp_score
    }

def main():
    """Main audit function."""
    recommendations_dir = Path("implementation_plans/recommendations")

    if not recommendations_dir.exists():
        print(f"❌ Directory not found: {recommendations_dir}")
        return

    rec_dirs = sorted([d for d in recommendations_dir.iterdir() if d.is_dir()])

    print(f"📊 Auditing {len(rec_dirs)} recommendations...")
    print()

    # Analyze all recommendations
    results = []
    for rec_dir in rec_dirs:
        result = analyze_recommendation(rec_dir)
        results.append(result)

    # Aggregate stats
    by_target = defaultdict(list)
    for result in results:
        by_target[result["target"]].append(result["name"])

    # Print summary
    print("=" * 70)
    print("RECOMMENDATION TARGET AUDIT")
    print("=" * 70)
    print()

    print(f"Total Recommendations: {len(results)}")
    print()

    print("Distribution by Target:")
    print("-" * 70)
    for target, recs in sorted(by_target.items()):
        percentage = (len(recs) / len(results)) * 100
        print(f"  {target:25s}: {len(recs):3d} ({percentage:5.1f}%)")
    print()

    # Show MCP-specific recommendations if any
    if by_target["nba-mcp-synthesis"]:
        print("=" * 70)
        print("MCP-SPECIFIC RECOMMENDATIONS")
        print("=" * 70)
        for rec in by_target["nba-mcp-synthesis"][:10]:
            print(f"  - {rec}")
        if len(by_target["nba-mcp-synthesis"]) > 10:
            print(f"  ... and {len(by_target['nba-mcp-synthesis']) - 10} more")
        print()

    # Show unclear ones
    if by_target["unclear"]:
        print("=" * 70)
        print("UNCLEAR TARGET (needs review)")
        print("=" * 70)
        for rec in by_target["unclear"][:20]:
            print(f"  - {rec}")
        if len(by_target["unclear"]) > 20:
            print(f"  ... and {len(by_target['unclear']) - 20} more")
        print()

    # Save detailed results
    output_file = Path("RECOMMENDATION_AUDIT_RESULTS.json")
    with open(output_file, 'w') as f:
        json.dump({
            "total": len(results),
            "by_target": {k: len(v) for k, v in by_target.items()},
            "details": results
        }, f, indent=2)

    print(f"📄 Detailed results saved to: {output_file}")
    print()

    # Recommendation
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)

    if by_target["nba-mcp-synthesis"] == 0:
        print("⚠️  NO MCP-specific recommendations found!")
        print("   All recommendations target nba-simulator-aws")
        print()
        print("   Next step: Generate MCP-specific recommendations from books")
        print("   about ML systems, software engineering, MLOps, etc.")
    else:
        print(f"✅ Found {len(by_target['nba-mcp-synthesis'])} MCP-specific recommendations")

    print("=" * 70)

if __name__ == "__main__":
    main()



