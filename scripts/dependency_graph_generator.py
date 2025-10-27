#!/usr/bin/env python3
"""
Dependency Graph Generator for NBA MCP Synthesis Recommendations

This module analyzes dependencies between recommendations and generates:
1. Dependency graphs (directed acyclic graphs)
2. Optimal implementation order (topological sort)
3. Circular dependency detection
4. Visual exports (graphviz, mermaid)

Features:
- Automatic dependency extraction from recommendation text
- Keyword-based dependency detection
- Priority-aware ordering
- Multiple export formats
- Dependency validation

Author: NBA MCP Synthesis Team
Date: 2025-10-21
"""

import json
import logging
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a dependency relationship between recommendations"""

    source_id: str
    target_id: str
    dependency_type: str  # 'requires', 'builds_on', 'optional', 'conflicts'
    confidence: float  # 0.0 to 1.0
    reason: str  # Why this dependency was detected

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RecommendationNode:
    """Represents a recommendation in the dependency graph"""

    rec_id: str
    title: str
    priority: str
    category: str
    dependencies: List[str]  # IDs of recommendations this depends on
    dependents: List[str]  # IDs of recommendations that depend on this
    depth: int = 0  # Depth in dependency tree (0 = no dependencies)
    implementation_order: int = -1  # Position in optimal implementation order

    def to_dict(self) -> Dict:
        return asdict(self)


class DependencyGraphGenerator:
    """Generates and analyzes dependency graphs for recommendations"""

    # Keywords that indicate dependencies
    DEPENDENCY_KEYWORDS = {
        "requires": ["requires", "needs", "depends on", "prerequisite", "must have"],
        "builds_on": ["builds on", "extends", "enhances", "improves", "based on"],
        "optional": ["optionally", "can use", "may leverage", "works with"],
        "conflicts": ["conflicts with", "incompatible with", "cannot use with"],
    }

    # Technical concepts that often indicate dependencies
    TECHNICAL_DEPENDENCIES = {
        "feature_store": [
            "feature engineering",
            "feature extraction",
            "data preprocessing",
        ],
        "data_pipeline": ["etl", "data ingestion", "data collection"],
        "model_training": [
            "data preprocessing",
            "feature engineering",
            "data pipeline",
        ],
        "model_deployment": ["model training", "model evaluation", "model validation"],
        "monitoring": ["model deployment", "prediction api", "production system"],
        "ab_testing": ["model deployment", "prediction api", "monitoring"],
    }

    def __init__(self, recommendations: List[Dict]):
        """
        Initialize dependency graph generator

        Args:
            recommendations: List of recommendation dictionaries
        """
        self.recommendations = recommendations
        self.nodes: Dict[str, RecommendationNode] = {}
        self.dependencies: List[Dependency] = []
        self.graph: Dict[str, List[str]] = defaultdict(list)  # Adjacency list
        self.reverse_graph: Dict[str, List[str]] = defaultdict(
            list
        )  # Reverse adjacency list

        logger.info(
            f"📊 Initialized DependencyGraphGenerator with {len(recommendations)} recommendations"
        )

    def build_graph(self, min_confidence: float = 0.5) -> Dict[str, RecommendationNode]:
        """
        Build complete dependency graph

        Args:
            min_confidence: Minimum confidence threshold for dependencies (0.0-1.0)

        Returns:
            Dictionary of recommendation nodes by ID
        """
        logger.info("🔨 Building dependency graph...")

        # Step 1: Create nodes for all recommendations
        self._create_nodes()

        # Step 2: Detect dependencies between recommendations
        self._detect_dependencies()

        # Step 3: Filter by confidence threshold
        self._filter_dependencies(min_confidence)

        # Step 4: Build adjacency lists
        self._build_adjacency_lists()

        # Step 5: Calculate depths
        self._calculate_depths()

        # Step 6: Detect circular dependencies
        cycles = self._detect_cycles()
        if cycles:
            logger.warning(f"⚠️  Detected {len(cycles)} circular dependencies")
            for cycle in cycles:
                logger.warning(f"   Cycle: {' → '.join(cycle)}")

        # Step 7: Calculate implementation order
        self._calculate_implementation_order()

        logger.info(
            f"✅ Graph built: {len(self.nodes)} nodes, {len(self.dependencies)} dependencies"
        )

        return self.nodes

    def _create_nodes(self):
        """Create recommendation nodes"""
        for rec in self.recommendations:
            rec_id = rec.get(
                "recommendation_id",
                rec.get("id", f"rec_{rec.get('title', 'unknown')[:20]}"),
            )

            node = RecommendationNode(
                rec_id=rec_id,
                title=rec.get("title", "Unknown"),
                priority=rec.get("priority", "MEDIUM"),
                category=rec.get("priority_score", {}).get("category", "Unknown"),
                dependencies=[],
                dependents=[],
            )

            self.nodes[rec_id] = node

    def _detect_dependencies(self):
        """Detect dependencies between recommendations"""
        logger.info("🔍 Detecting dependencies...")

        for source_rec in self.recommendations:
            source_id = source_rec.get("recommendation_id", source_rec.get("id", ""))

            # Extract text to analyze for dependencies
            text_to_analyze = self._get_text_for_analysis(source_rec)

            # Check against all other recommendations
            for target_rec in self.recommendations:
                if source_rec == target_rec:
                    continue

                target_id = target_rec.get(
                    "recommendation_id", target_rec.get("id", "")
                )

                # Detect dependency
                dependency = self._check_dependency(
                    source_rec, target_rec, text_to_analyze
                )
                if dependency:
                    self.dependencies.append(dependency)

        logger.info(f"   Found {len(self.dependencies)} potential dependencies")

    def _get_text_for_analysis(self, rec: Dict) -> str:
        """Get all text from recommendation for dependency analysis"""
        text_parts = []

        # Title
        if "title" in rec:
            text_parts.append(rec["title"])

        # Description
        if "description" in rec:
            text_parts.append(rec["description"])

        # Implementation steps
        if "implementation_steps" in rec:
            steps = rec["implementation_steps"]
            if isinstance(steps, list):
                text_parts.extend(steps)

        # Technical details
        if "technical_details" in rec:
            text_parts.append(rec["technical_details"])

        return " ".join(text_parts).lower()

    def _check_dependency(
        self, source: Dict, target: Dict, source_text: str
    ) -> Optional[Dependency]:
        """
        Check if source recommendation depends on target recommendation

        Args:
            source: Source recommendation
            target: Target recommendation
            source_text: Preprocessed text from source recommendation

        Returns:
            Dependency object if dependency detected, None otherwise
        """
        source_id = source.get("recommendation_id", source.get("id", ""))
        target_id = target.get("recommendation_id", target.get("id", ""))
        target_title = target.get("title", "").lower()

        # Check for explicit keyword dependencies
        for dep_type, keywords in self.DEPENDENCY_KEYWORDS.items():
            for keyword in keywords:
                pattern = rf"{keyword}\s+.*?{re.escape(target_title[:20])}"
                if re.search(pattern, source_text, re.IGNORECASE):
                    return Dependency(
                        source_id=source_id,
                        target_id=target_id,
                        dependency_type=dep_type,
                        confidence=0.9,
                        reason=f"Explicit keyword '{keyword}' found referencing '{target_title}'",
                    )

        # Check for technical concept dependencies
        source_concepts = self._extract_concepts(source_text)
        target_concepts = self._extract_concepts(target.get("title", "").lower())

        for concept, prerequisites in self.TECHNICAL_DEPENDENCIES.items():
            if concept in source_concepts:
                for prereq in prerequisites:
                    if any(prereq in tc for tc in target_concepts):
                        return Dependency(
                            source_id=source_id,
                            target_id=target_id,
                            dependency_type="builds_on",
                            confidence=0.7,
                            reason=f"'{concept}' typically builds on '{prereq}'",
                        )

        # Check for title substring matching (lower confidence)
        target_keywords = set(target_title.split())
        source_keywords = set(source_text.split())

        # If target title words appear frequently in source, might be a dependency
        if len(target_keywords) > 2:
            matches = target_keywords.intersection(source_keywords)
            if len(matches) >= len(target_keywords) * 0.6:
                return Dependency(
                    source_id=source_id,
                    target_id=target_id,
                    dependency_type="optional",
                    confidence=0.5,
                    reason=f"Similar concepts mentioned (keywords: {', '.join(list(matches)[:3])})",
                )

        return None

    def _extract_concepts(self, text: str) -> Set[str]:
        """Extract technical concepts from text"""
        concepts = set()

        # Normalize text
        text = text.lower()

        # Check for each technical concept
        for concept in self.TECHNICAL_DEPENDENCIES.keys():
            if concept.replace("_", " ") in text:
                concepts.add(concept)

        # Also check for common ML/data concepts
        common_concepts = [
            "feature store",
            "data pipeline",
            "model training",
            "model deployment",
            "monitoring",
            "ab testing",
            "etl",
            "preprocessing",
            "feature engineering",
            "prediction api",
            "database",
            "data validation",
            "testing",
            "deployment",
        ]

        for concept in common_concepts:
            if concept in text:
                concepts.add(concept.replace(" ", "_"))

        return concepts

    def _filter_dependencies(self, min_confidence: float):
        """Filter dependencies by confidence threshold"""
        original_count = len(self.dependencies)
        self.dependencies = [
            d for d in self.dependencies if d.confidence >= min_confidence
        ]
        filtered_count = original_count - len(self.dependencies)

        if filtered_count > 0:
            logger.info(
                f"   Filtered out {filtered_count} low-confidence dependencies (< {min_confidence})"
            )

    def _build_adjacency_lists(self):
        """Build adjacency lists from dependencies"""
        for dep in self.dependencies:
            # Skip conflicts
            if dep.dependency_type == "conflicts":
                continue

            # Add to graph (source depends on target, so edge from target to source)
            self.graph[dep.target_id].append(dep.source_id)
            self.reverse_graph[dep.source_id].append(dep.target_id)

            # Update nodes
            if dep.source_id in self.nodes:
                self.nodes[dep.source_id].dependencies.append(dep.target_id)
            if dep.target_id in self.nodes:
                self.nodes[dep.target_id].dependents.append(dep.source_id)

    def _calculate_depths(self):
        """Calculate depth of each node in dependency tree"""
        # Use BFS to calculate depths
        depths = {}

        # Find all nodes with no dependencies (depth 0)
        queue = deque()
        for rec_id, node in self.nodes.items():
            if len(node.dependencies) == 0:
                depths[rec_id] = 0
                queue.append(rec_id)

        # BFS to calculate depths
        while queue:
            current_id = queue.popleft()
            current_depth = depths[current_id]

            # Update all dependents
            for dependent_id in self.nodes[current_id].dependents:
                # Depth is max of all dependency depths + 1
                dep_depths = [
                    depths.get(dep, 0) for dep in self.nodes[dependent_id].dependencies
                ]
                new_depth = max(dep_depths) + 1 if dep_depths else 1

                if dependent_id not in depths or new_depth > depths[dependent_id]:
                    depths[dependent_id] = new_depth
                    queue.append(dependent_id)

        # Update nodes
        for rec_id, depth in depths.items():
            self.nodes[rec_id].depth = depth

    def _detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS

        Returns:
            List of cycles (each cycle is a list of recommendation IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            # Visit all dependencies
            for dep_id in self.nodes[node_id].dependencies:
                if dep_id not in visited:
                    dfs(dep_id, path.copy())
                elif dep_id in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    cycles.append([self.nodes[n].title for n in cycle])

            rec_stack.remove(node_id)

        # Check each node
        for rec_id in self.nodes:
            if rec_id not in visited:
                dfs(rec_id, [])

        return cycles

    def _calculate_implementation_order(self):
        """Calculate optimal implementation order using topological sort"""
        # Kahn's algorithm for topological sort
        in_degree = {
            rec_id: len(node.dependencies) for rec_id, node in self.nodes.items()
        }
        queue = deque([rec_id for rec_id, degree in in_degree.items() if degree == 0])

        order = []

        while queue:
            # Sort by priority (CRITICAL first) and then by category
            queue = deque(
                sorted(
                    queue,
                    key=lambda x: (
                        self._priority_rank(self.nodes[x].priority),
                        self._category_rank(self.nodes[x].category),
                    ),
                )
            )

            current_id = queue.popleft()
            order.append(current_id)

            # Reduce in-degree of dependents
            for dependent_id in self.nodes[current_id].dependents:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # Update nodes with implementation order
        for i, rec_id in enumerate(order):
            self.nodes[rec_id].implementation_order = i + 1

        logger.info(
            f"   Calculated implementation order for {len(order)} recommendations"
        )

    def _priority_rank(self, priority: str) -> int:
        """Convert priority to numeric rank (lower is higher priority)"""
        priority_map = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }
        return priority_map.get(priority, 4)

    def _category_rank(self, category: str) -> int:
        """Convert category to numeric rank (lower is higher priority)"""
        category_map = {
            "Quick Win": 0,
            "Strategic Project": 1,
            "Medium Priority": 2,
            "Low Priority": 3,
        }
        return category_map.get(category, 4)

    def export_to_graphviz(self, output_file: str, max_nodes: int = 50):
        """
        Export dependency graph to Graphviz DOT format

        Args:
            output_file: Path to output .dot file
            max_nodes: Maximum number of nodes to include (for readability)
        """
        logger.info(f"📤 Exporting to Graphviz: {output_file}")

        # Select top nodes by implementation order
        top_nodes = sorted(
            self.nodes.items(),
            key=lambda x: (
                x[1].implementation_order if x[1].implementation_order > 0 else 999
            ),
        )[:max_nodes]

        top_node_ids = set(rec_id for rec_id, _ in top_nodes)

        lines = [
            "digraph RecommendationDependencies {",
            "    rankdir=LR;",
            "    node [shape=box, style=rounded];",
            "",
        ]

        # Add nodes
        for rec_id, node in top_nodes:
            color = self._get_priority_color(node.priority)
            label = node.title[:40] + "..." if len(node.title) > 40 else node.title

            lines.append(
                f'    "{rec_id}" [label="{label}", fillcolor="{color}", style="rounded,filled"];'
            )

        lines.append("")

        # Add edges (only for nodes in top_nodes)
        for dep in self.dependencies:
            if dep.source_id in top_node_ids and dep.target_id in top_node_ids:
                style = (
                    "solid"
                    if dep.dependency_type in ["requires", "builds_on"]
                    else "dashed"
                )
                label = dep.dependency_type

                lines.append(
                    f'    "{dep.target_id}" -> "{dep.source_id}" [label="{label}", style="{style}"];'
                )

        lines.append("}")

        # Write to file
        Path(output_file).write_text("\n".join(lines))
        logger.info(f"✅ Graphviz export complete: {len(top_nodes)} nodes")

    def export_to_mermaid(self, output_file: str, max_nodes: int = 30):
        """
        Export dependency graph to Mermaid format

        Args:
            output_file: Path to output .mmd file
            max_nodes: Maximum number of nodes to include
        """
        logger.info(f"📤 Exporting to Mermaid: {output_file}")

        # Select top nodes by implementation order
        top_nodes = sorted(
            self.nodes.items(),
            key=lambda x: (
                x[1].implementation_order if x[1].implementation_order > 0 else 999
            ),
        )[:max_nodes]

        top_node_ids = set(rec_id for rec_id, _ in top_nodes)

        lines = [
            "graph LR",
            "",
        ]

        # Add nodes with labels
        for rec_id, node in top_nodes:
            label = node.title[:30] + "..." if len(node.title) > 30 else node.title
            safe_id = rec_id.replace("-", "_").replace(".", "_")

            lines.append(f'    {safe_id}["{label}"]')

        lines.append("")

        # Add edges
        for dep in self.dependencies:
            if dep.source_id in top_node_ids and dep.target_id in top_node_ids:
                source_safe = dep.source_id.replace("-", "_").replace(".", "_")
                target_safe = dep.target_id.replace("-", "_").replace(".", "_")

                arrow = (
                    "-->"
                    if dep.dependency_type in ["requires", "builds_on"]
                    else "-..->"
                )
                lines.append(f"    {target_safe} {arrow} {source_safe}")

        lines.append("")

        # Add styling
        lines.extend(
            [
                "classDef critical fill:#ff6b6b",
                "classDef high fill:#ffa500",
                "classDef medium fill:#4ecdc4",
                "classDef low fill:#95e1d3",
            ]
        )

        # Write to file
        Path(output_file).write_text("\n".join(lines))
        logger.info(f"✅ Mermaid export complete: {len(top_nodes)} nodes")

    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level"""
        colors = {
            "CRITICAL": "#ff6b6b",
            "HIGH": "#ffa500",
            "MEDIUM": "#4ecdc4",
            "LOW": "#95e1d3",
        }
        return colors.get(priority, "#cccccc")

    def export_implementation_order(self, output_file: str):
        """
        Export recommended implementation order to markdown

        Args:
            output_file: Path to output .md file
        """
        logger.info(f"📤 Exporting implementation order: {output_file}")

        # Sort by implementation order
        ordered_nodes = sorted(
            self.nodes.values(),
            key=lambda x: x.implementation_order if x.implementation_order > 0 else 999,
        )

        lines = [
            "# Recommended Implementation Order",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            f"**Total Recommendations**: {len(self.nodes)}",
            f"**Total Dependencies**: {len(self.dependencies)}",
            "",
            "---",
            "",
            "## Implementation Order",
            "",
            "Recommendations are ordered based on:",
            "1. Dependencies (prerequisites first)",
            "2. Priority tier (CRITICAL → HIGH → MEDIUM → LOW)",
            "3. Category (Quick Wins → Strategic Projects → Medium Priority)",
            "",
            "| Order | ID | Title | Priority | Category | Dependencies |",
            "|-------|-----|-------|----------|----------|--------------|",
        ]

        for node in ordered_nodes:
            if node.implementation_order > 0:
                dep_count = len(node.dependencies)
                dep_text = (
                    f"{dep_count} dependencies" if dep_count > 0 else "No dependencies"
                )

                lines.append(
                    f"| {node.implementation_order} | `{node.rec_id}` | {node.title[:50]} | "
                    f"{node.priority} | {node.category} | {dep_text} |"
                )

        lines.extend(
            [
                "",
                "## Dependency Depth Analysis",
                "",
                "Depth indicates how many layers of dependencies a recommendation has:",
                "",
            ]
        )

        # Group by depth
        by_depth = defaultdict(list)
        for node in self.nodes.values():
            by_depth[node.depth].append(node)

        for depth in sorted(by_depth.keys()):
            nodes_at_depth = by_depth[depth]
            lines.append(f"### Depth {depth} ({len(nodes_at_depth)} recommendations)")
            lines.append("")

            if depth == 0:
                lines.append(
                    "These have no dependencies and can be started immediately."
                )
            else:
                lines.append(f"These require {depth} layer(s) of prerequisites.")

            lines.append("")

            for node in sorted(
                nodes_at_depth, key=lambda x: self._priority_rank(x.priority)
            )[:10]:
                lines.append(f"- **{node.title}** ({node.priority}, {node.category})")

            if len(nodes_at_depth) > 10:
                lines.append(f"- ... and {len(nodes_at_depth) - 10} more")

            lines.append("")

        # Write to file
        Path(output_file).write_text("\n".join(lines))
        logger.info(f"✅ Implementation order export complete")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dependency graph"""
        stats = {
            "total_recommendations": len(self.nodes),
            "total_dependencies": len(self.dependencies),
            "by_type": defaultdict(int),
            "by_depth": defaultdict(int),
            "average_dependencies_per_rec": 0,
            "max_depth": 0,
            "recommendations_with_no_dependencies": 0,
            "recommendations_with_dependencies": 0,
        }

        # Count by dependency type
        for dep in self.dependencies:
            stats["by_type"][dep.dependency_type] += 1

        # Count by depth
        total_deps = 0
        for node in self.nodes.values():
            stats["by_depth"][node.depth] += 1
            total_deps += len(node.dependencies)

            if node.depth > stats["max_depth"]:
                stats["max_depth"] = node.depth

            if len(node.dependencies) == 0:
                stats["recommendations_with_no_dependencies"] += 1
            else:
                stats["recommendations_with_dependencies"] += 1

        if len(self.nodes) > 0:
            stats["average_dependencies_per_rec"] = total_deps / len(self.nodes)

        return dict(stats)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate dependency graphs for NBA MCP recommendations"
    )
    parser.add_argument(
        "--recommendations", required=True, help="Path to recommendations JSON file"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold for dependencies (0.0-1.0)",
    )
    parser.add_argument("--graphviz", help="Output path for Graphviz DOT file")
    parser.add_argument("--mermaid", help="Output path for Mermaid diagram file")
    parser.add_argument("--order", help="Output path for implementation order markdown")
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=50,
        help="Maximum nodes to include in visual exports",
    )

    args = parser.parse_args()

    # Load recommendations
    logger.info(f"📖 Loading recommendations from: {args.recommendations}")
    with open(args.recommendations, "r") as f:
        data = json.load(f)

    # Handle different JSON formats
    if isinstance(data, list):
        recommendations = data
    elif isinstance(data, dict):
        if "recommendations" in data:
            recommendations = data["recommendations"]
        else:
            recommendations = [data]
    else:
        logger.error("❌ Invalid JSON format")
        return 1

    logger.info(f"📊 Loaded {len(recommendations)} recommendations")

    # Build dependency graph
    generator = DependencyGraphGenerator(recommendations)
    nodes = generator.build_graph(min_confidence=args.min_confidence)

    # Print statistics
    stats = generator.get_statistics()
    logger.info("")
    logger.info("📊 Dependency Graph Statistics:")
    logger.info(f"   Total recommendations: {stats['total_recommendations']}")
    logger.info(f"   Total dependencies: {stats['total_dependencies']}")
    logger.info(
        f"   Avg dependencies per rec: {stats['average_dependencies_per_rec']:.1f}"
    )
    logger.info(f"   Max depth: {stats['max_depth']}")
    logger.info(f"   No dependencies: {stats['recommendations_with_no_dependencies']}")
    logger.info(f"   With dependencies: {stats['recommendations_with_dependencies']}")
    logger.info("")
    logger.info("   Dependencies by type:")
    for dep_type, count in stats["by_type"].items():
        logger.info(f"     - {dep_type}: {count}")

    # Export to formats
    if args.graphviz:
        generator.export_to_graphviz(args.graphviz, max_nodes=args.max_nodes)

    if args.mermaid:
        generator.export_to_mermaid(args.mermaid, max_nodes=args.max_nodes)

    if args.order:
        generator.export_implementation_order(args.order)

    logger.info("✅ Dependency graph generation complete!")

    return 0


if __name__ == "__main__":
    exit(main())
