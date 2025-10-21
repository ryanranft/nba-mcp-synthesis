#!/usr/bin/env python3
"""
Dependency Tracker

Builds dependency graph for NBA simulator recommendations.
Detects dependencies, checks for cycles, and generates implementation order.

Usage:
    python3 scripts/dependency_tracker.py \\
        --synthesis implementation_plans/consolidated_recommendations.json \\
        --output DEPENDENCY_GRAPH.md
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DependencyTracker:
    """Track and analyze dependencies between recommendations."""

    def __init__(self, recommendations: List[Dict]):
        """
        Initialize dependency tracker.

        Args:
            recommendations: List of recommendation dictionaries
        """
        self.recommendations = recommendations
        self.graph = defaultdict(set)  # rec_id -> set of dependencies
        self.reverse_graph = defaultdict(set)  # rec_id -> set of dependents
        self.rec_by_title = {}  # title -> rec_id mapping
        self.circular_deps = []

        # Build title index
        for idx, rec in enumerate(recommendations, 1):
            rec_id = f"rec_{idx:03d}"
            title = rec.get('title', '').lower()
            self.rec_by_title[title] = rec_id

        logger.info(f"Initialized tracker with {len(recommendations)} recommendations")

    def extract_dependencies(self, rec: Dict, rec_idx: int) -> Set[str]:
        """
        Extract dependencies from recommendation.

        Looks for:
        - Explicit dependencies field
        - References in description/technical details
        - Keywords like "requires", "depends on", "after implementing"

        Args:
            rec: Recommendation dictionary
            rec_idx: Recommendation index (1-based)

        Returns:
            Set of dependency rec_ids
        """
        deps = set()

        # 1. Explicit dependencies field
        explicit_deps = rec.get('dependencies', [])
        for dep_title in explicit_deps:
            dep_title_lower = dep_title.lower().strip()
            if dep_title_lower in self.rec_by_title:
                deps.add(self.rec_by_title[dep_title_lower])

        # 2. Text pattern matching
        text = f"{rec.get('description', '')} {rec.get('technical_details', '')}"
        text_lower = text.lower()

        # Pattern 1: "requires rec_XXX"
        for match in re.finditer(r'requires?\s+rec[_-]?(\d+)', text_lower):
            dep_id = f"rec_{int(match.group(1)):03d}"
            if dep_id != f"rec_{rec_idx:03d}":  # Avoid self-dependency
                deps.add(dep_id)

        # Pattern 2: "depends on rec_XXX"
        for match in re.finditer(r'depends?\s+on\s+rec[_-]?(\d+)', text_lower):
            dep_id = f"rec_{int(match.group(1)):03d}"
            if dep_id != f"rec_{rec_idx:03d}":
                deps.add(dep_id)

        # Pattern 3: "after implementing rec_XXX"
        for match in re.finditer(r'after\s+implementing\s+rec[_-]?(\d+)', text_lower):
            dep_id = f"rec_{int(match.group(1)):03d}"
            if dep_id != f"rec_{rec_idx:03d}":
                deps.add(dep_id)

        return deps

    def build_dependency_graph(self):
        """Build dependency graph for all recommendations."""
        logger.info("Building dependency graph...")

        for idx, rec in enumerate(self.recommendations, 1):
            rec_id = f"rec_{idx:03d}"
            deps = self.extract_dependencies(rec, idx)

            if deps:
                self.graph[rec_id] = deps
                for dep_id in deps:
                    self.reverse_graph[dep_id].add(rec_id)

                logger.info(f"  {rec_id}: {len(deps)} dependencies")

        logger.info(f"✅ Graph built: {len(self.graph)} nodes with dependencies")

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.

        Returns:
            List of circular dependency chains
        """
        logger.info("Checking for circular dependencies...")

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            """DFS to detect cycles."""
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in self.graph.get(node, []):
                dfs(dep, path.copy())

            rec_stack.remove(node)

        # Check all nodes
        for rec_id in range(1, len(self.recommendations) + 1):
            node = f"rec_{rec_id:03d}"
            if node not in visited:
                dfs(node, [])

        self.circular_deps = cycles

        if cycles:
            logger.warning(f"⚠️  Found {len(cycles)} circular dependencies")
        else:
            logger.info("✅ No circular dependencies found")

        return cycles

    def generate_implementation_order(self) -> List[str]:
        """
        Generate implementation order using topological sort (Kahn's algorithm).

        Returns:
            Ordered list of rec_ids
        """
        logger.info("Generating implementation order...")

        # Calculate in-degree for each node
        in_degree = defaultdict(int)
        all_recs = [f"rec_{i:03d}" for i in range(1, len(self.recommendations) + 1)]

        for rec_id in all_recs:
            in_degree[rec_id] = len(self.graph.get(rec_id, []))

        # Queue with nodes having 0 in-degree
        queue = deque([rec_id for rec_id in all_recs if in_degree[rec_id] == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)

            # Reduce in-degree for dependents
            for dependent in self.reverse_graph.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all nodes are in order, there's a cycle
        if len(order) < len(all_recs):
            logger.warning(f"⚠️  Could not order all recommendations (cycle detected)")
            # Add remaining nodes
            remaining = [r for r in all_recs if r not in order]
            order.extend(remaining)

        logger.info(f"✅ Generated implementation order ({len(order)} recommendations)")
        return order

    def generate_mermaid_diagram(self, output_file: str):
        """
        Generate Mermaid diagram of dependency graph.

        Args:
            output_file: Path to output markdown file
        """
        logger.info(f"Generating Mermaid diagram...")

        # Limit to recommendations with dependencies for readability
        nodes_with_deps = {k for k, v in self.graph.items() if v}
        all_involved = nodes_with_deps.copy()
        for deps in self.graph.values():
            all_involved.update(deps)

        # If too many nodes, sample
        if len(all_involved) > 50:
            logger.info(f"  Limiting diagram to 50 most connected nodes")
            # Sort by number of connections
            node_connections = {
                node: len(self.graph.get(node, [])) + len(self.reverse_graph.get(node, []))
                for node in all_involved
            }
            all_involved = set(sorted(node_connections, key=node_connections.get, reverse=True)[:50])

        mermaid_content = "```mermaid\ngraph TD\n"

        # Add nodes
        for rec_id in sorted(all_involved):
            rec_idx = int(rec_id.split('_')[1])
            title = self.recommendations[rec_idx - 1].get('title', 'Unknown')
            title_short = title[:40] + "..." if len(title) > 40 else title
            mermaid_content += f"    {rec_id}[\"{rec_id}: {title_short}\"]\n"

        # Add edges
        for rec_id in sorted(all_involved):
            for dep_id in sorted(self.graph.get(rec_id, [])):
                if dep_id in all_involved:
                    mermaid_content += f"    {rec_id} --> {dep_id}\n"

        mermaid_content += "```\n"

        # Create full markdown document
        markdown_content = f"""# Dependency Graph

**Generated:** {self._get_timestamp()}
**Total Recommendations:** {len(self.recommendations)}
**Recommendations with Dependencies:** {len(self.graph)}

---

## Overview

This document visualizes the dependencies between recommendations for the NBA Simulator AWS project.

**Key Statistics:**
- Total recommendations: {len(self.recommendations)}
- Recommendations with dependencies: {len(self.graph)}
- Total dependency edges: {sum(len(deps) for deps in self.graph.values())}
- Circular dependencies: {len(self.circular_deps)}

---

## Dependency Graph

{mermaid_content}

---

## Circular Dependencies

"""

        if self.circular_deps:
            markdown_content += f"⚠️ **Found {len(self.circular_deps)} circular dependencies:**\n\n"
            for i, cycle in enumerate(self.circular_deps, 1):
                markdown_content += f"### Cycle {i}\n\n"
                markdown_content += " → ".join(cycle) + f" → {cycle[0]}\n\n"
        else:
            markdown_content += "✅ **No circular dependencies detected.**\n\n"

        markdown_content += """
---

## Implementation Order

See [PRIORITY_ACTION_LIST.md](PRIORITY_ACTION_LIST.md) for the recommended implementation order.

---

## Dependencies by Recommendation

"""

        # List all dependencies
        for rec_id in sorted(self.graph.keys()):
            rec_idx = int(rec_id.split('_')[1])
            title = self.recommendations[rec_idx - 1].get('title', 'Unknown')
            deps = sorted(self.graph[rec_id])

            markdown_content += f"### {rec_id}: {title}\n\n"
            markdown_content += f"**Depends on:**\n"
            for dep_id in deps:
                dep_idx = int(dep_id.split('_')[1])
                dep_title = self.recommendations[dep_idx - 1].get('title', 'Unknown')
                markdown_content += f"- {dep_id}: {dep_title}\n"
            markdown_content += "\n"

        markdown_content += """
---

**Generated by:** Dependency Tracker
**Last Updated:** """ + self._get_timestamp()

        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(markdown_content)

        logger.info(f"✅ Saved Mermaid diagram to {output_file}")

    def _get_timestamp(self) -> str:
        """Get formatted timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%B %d, %Y at %H:%M:%S')


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Track dependencies between recommendations")
    parser.add_argument('--synthesis', required=True, help='Path to consolidated_recommendations.json')
    parser.add_argument('--output', default='DEPENDENCY_GRAPH.md', help='Output markdown file')

    args = parser.parse_args()

    # Load recommendations
    with open(args.synthesis, 'r') as f:
        data = json.load(f)
    recommendations = data.get('recommendations', [])

    # Build tracker
    tracker = DependencyTracker(recommendations)

    # Build graph
    tracker.build_dependency_graph()

    # Detect circular dependencies
    cycles = tracker.detect_circular_dependencies()

    # Generate implementation order
    order = tracker.generate_implementation_order()

    # Generate Mermaid diagram
    tracker.generate_mermaid_diagram(args.output)

    # Print summary
    print(f"\n" + "=" * 80)
    print(f"✅ DEPENDENCY ANALYSIS COMPLETE")
    print(f"=" * 80)
    print(f"Total recommendations: {len(recommendations)}")
    print(f"Recommendations with dependencies: {len(tracker.graph)}")
    print(f"Total dependency edges: {sum(len(deps) for deps in tracker.graph.values())}")
    print(f"Circular dependencies: {len(cycles)}")
    print(f"\nOutput: {args.output}")
    print(f"=" * 80)


if __name__ == "__main__":
    main()




