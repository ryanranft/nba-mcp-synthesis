#!/usr/bin/env python3
"""
Dependency Visualization System

Generates visualizations of phase dependencies, critical paths, and data flow.
Supports Mermaid diagrams and exports to multiple formats.

Author: NBA MCP Synthesis System
Version: 3.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DependencyVisualizer:
    """Generate dependency visualizations for workflow phases."""

    def __init__(self):
        """Initialize Dependency Visualizer."""
        self.phases = self._get_phase_definitions()
        logger.info("Dependency Visualizer initialized")

    def _get_phase_definitions(self) -> Dict:
        """
        Get phase definitions with dependencies.

        Returns:
            Dict of phase definitions
        """
        return {
            "phase_0": {
                "name": "Phase 0: Discovery",
                "description": "Initial project discovery",
                "dependencies": [],
            },
            "phase_1": {
                "name": "Phase 1: Book Discovery",
                "description": "Discover technical books",
                "dependencies": ["phase_0"],
            },
            "phase_2": {
                "name": "Phase 2: Book Analysis",
                "description": "Analyze books with AI",
                "dependencies": ["phase_1"],
                "critical": True,
            },
            "phase_3": {
                "name": "Phase 3: Synthesis",
                "description": "Synthesize recommendations",
                "dependencies": ["phase_2"],
                "critical": True,
            },
            "phase_3.5": {
                "name": "Phase 3.5: AI Modifications",
                "description": "AI-powered plan modifications",
                "dependencies": ["phase_3"],
                "critical": True,
            },
            "phase_4": {
                "name": "Phase 4: File Generation",
                "description": "Generate implementation files",
                "dependencies": ["phase_3.5"],
            },
            "phase_5": {
                "name": "Phase 5: Index Updates",
                "description": "Update documentation indexes",
                "dependencies": ["phase_4"],
            },
            "phase_6": {
                "name": "Phase 6: Status Reports",
                "description": "Generate status reports",
                "dependencies": ["phase_5"],
            },
            "phase_7": {
                "name": "Phase 7: Sequence Optimization",
                "description": "Optimize implementation sequence",
                "dependencies": ["phase_6"],
            },
            "phase_8": {
                "name": "Phase 8: Progress Tracking",
                "description": "Setup progress tracking",
                "dependencies": ["phase_7"],
            },
            "phase_8.5": {
                "name": "Phase 8.5: Pre-Integration Validation",
                "description": "Validate before integration",
                "dependencies": ["phase_4"],
            },
            "phase_9": {
                "name": "Phase 9: Integration",
                "description": "Integrate with nba-simulator-aws",
                "dependencies": ["phase_8", "phase_8.5"],
            },
        }

    def generate_mermaid_diagram(
        self, show_critical: bool = True, output_path: Optional[Path] = None
    ) -> str:
        """
        Generate Mermaid dependency diagram.

        Args:
            show_critical: Highlight critical path
            output_path: Optional path to save diagram

        Returns:
            Mermaid diagram as string
        """
        diagram = ["```mermaid", "graph TD"]

        # Add nodes
        for phase_id, phase_data in self.phases.items():
            node_id = phase_id.replace(".", "_").replace(" ", "_")
            name = phase_data["name"]

            # Add node
            diagram.append(f'    {node_id}["{name}"]')

        # Add edges
        for phase_id, phase_data in self.phases.items():
            node_id = phase_id.replace(".", "_").replace(" ", "_")
            dependencies = phase_data.get("dependencies", [])

            for dep in dependencies:
                dep_id = dep.replace(".", "_").replace(" ", "_")
                diagram.append(f"    {dep_id} --> {node_id}")

        # Add styling for critical path
        if show_critical:
            diagram.append("")
            diagram.append("    %% Critical Path Styling")
            for phase_id, phase_data in self.phases.items():
                if phase_data.get("critical"):
                    node_id = phase_id.replace(".", "_").replace(" ", "_")
                    diagram.append(
                        f"    style {node_id} fill:#ff9800,stroke:#f57c00,stroke-width:3px"
                    )

        diagram.append("```")
        result = "\n".join(diagram)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result)
            logger.info(f"Mermaid diagram saved to {output_path}")

        return result

    def generate_data_flow_diagram(self, output_path: Optional[Path] = None) -> str:
        """
        Generate data flow diagram.

        Args:
            output_path: Optional path to save diagram

        Returns:
            Mermaid diagram as string
        """
        diagram = [
            "```mermaid",
            "graph LR",
            '    Books["📚 Technical Books<br/>(51 books)"]',
            '    Analysis["🔍 AI Analysis<br/>(Gemini + Claude)"]',
            '    Recs["📝 Recommendations<br/>(300-400 items)"]',
            '    Synthesis["🔨 Synthesis<br/>(AI Consensus)"]',
            '    Plans["📋 Implementation Plans<br/>(Phase-mapped)"]',
            '    Mods["🤖 AI Modifications<br/>(ADD/MODIFY/DELETE)"]',
            '    Files["📄 Generated Files<br/>(Code + Tests + Docs)"]',
            '    Validation["✅ Validation<br/>(Syntax + Imports)"]',
            '    Integration["🔗 Integration<br/>(nba-simulator-aws)"]',
            "",
            "    Books --> Analysis",
            "    Analysis --> Recs",
            "    Recs --> Synthesis",
            "    Synthesis --> Plans",
            "    Plans --> Mods",
            "    Mods --> Files",
            "    Files --> Validation",
            "    Validation --> Integration",
            "",
            "    style Books fill:#e3f2fd",
            "    style Analysis fill:#fff3e0",
            "    style Synthesis fill:#fff3e0",
            "    style Mods fill:#f3e5f5",
            "    style Validation fill:#e8f5e9",
            "    style Integration fill:#e8f5e9",
            "```",
        ]

        result = "\n".join(diagram)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result)
            logger.info(f"Data flow diagram saved to {output_path}")

        return result

    def identify_critical_path(self) -> List[str]:
        """
        Identify critical path through phases.

        Returns:
            List of phase IDs in critical path
        """
        # Build graph
        graph = {}
        for phase_id, phase_data in self.phases.items():
            graph[phase_id] = phase_data.get("dependencies", [])

        # Find longest path using DFS
        def dfs(node: str, visited: Set[str], path: List[str]) -> List[str]:
            visited.add(node)
            path.append(node)

            longest = path.copy()

            # Find dependents
            dependents = [p for p, deps in graph.items() if node in deps]

            for dependent in dependents:
                if dependent not in visited:
                    sub_path = dfs(dependent, visited.copy(), path.copy())
                    if len(sub_path) > len(longest):
                        longest = sub_path

            return longest

        # Start from phases with no dependencies
        root_phases = [p for p, deps in graph.items() if not deps]

        longest_path = []
        for root in root_phases:
            path = dfs(root, set(), [])
            if len(path) > len(longest_path):
                longest_path = path

        logger.info(f"Critical path identified: {len(longest_path)} phases")
        return longest_path

    def analyze_bottlenecks(self) -> List[Dict]:
        """
        Identify potential bottlenecks in workflow.

        Returns:
            List of bottleneck analyses
        """
        bottlenecks = []

        # Count how many phases depend on each phase
        dependency_count = {}
        for phase_id, phase_data in self.phases.items():
            for dep in phase_data.get("dependencies", []):
                dependency_count[dep] = dependency_count.get(dep, 0) + 1

        # Identify bottlenecks (phases with many dependents)
        for phase_id, count in dependency_count.items():
            if count >= 2:
                phase_data = self.phases.get(phase_id, {})
                bottlenecks.append(
                    {
                        "phase": phase_id,
                        "name": phase_data.get("name", phase_id),
                        "dependent_count": count,
                        "reason": f"{count} phases depend on this phase",
                    }
                )

        # Sort by dependency count
        bottlenecks.sort(key=lambda x: x["dependent_count"], reverse=True)

        logger.info(f"Identified {len(bottlenecks)} bottlenecks")
        return bottlenecks

    def generate_optimization_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate optimization recommendations report.

        Args:
            output_path: Optional path to save report

        Returns:
            Report as markdown string
        """
        critical_path = self.identify_critical_path()
        bottlenecks = self.analyze_bottlenecks()

        report = [
            "# Workflow Optimization Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Critical Path",
            "",
            "The critical path represents the longest sequence of dependent phases:",
            "",
        ]

        for i, phase_id in enumerate(critical_path, 1):
            phase_data = self.phases.get(phase_id, {})
            name = phase_data.get("name", phase_id)
            report.append(f"{i}. **{name}** (`{phase_id}`)")

        report.extend(
            [
                "",
                f"**Total phases in critical path:** {len(critical_path)}",
                "",
                "## Bottlenecks",
                "",
            ]
        )

        if bottlenecks:
            report.append("Phases with multiple dependents (potential bottlenecks):")
            report.append("")

            for bottleneck in bottlenecks:
                report.append(f"### {bottleneck['name']}")
                report.append(f"- **Phase ID:** `{bottleneck['phase']}`")
                report.append(
                    f"- **Dependent phases:** {bottleneck['dependent_count']}"
                )
                report.append(f"- **Impact:** {bottleneck['reason']}")
                report.append("")
        else:
            report.append("No significant bottlenecks identified.")
            report.append("")

        report.extend(
            [
                "## Parallelization Opportunities",
                "",
                "Phases that can run in parallel (no dependencies between them):",
                "",
            ]
        )

        # Find phases with no dependencies between them
        parallel_groups = []
        processed = set()

        for phase_id in self.phases:
            if phase_id in processed:
                continue

            phase_deps = set(self.phases[phase_id].get("dependencies", []))
            parallel_group = [phase_id]
            processed.add(phase_id)

            for other_id in self.phases:
                if other_id in processed:
                    continue

                other_deps = set(self.phases[other_id].get("dependencies", []))

                # Check if they can run in parallel
                if (
                    phase_id not in other_deps
                    and other_id not in phase_deps
                    and phase_deps == other_deps
                ):
                    parallel_group.append(other_id)
                    processed.add(other_id)

            if len(parallel_group) > 1:
                parallel_groups.append(parallel_group)

        if parallel_groups:
            for i, group in enumerate(parallel_groups, 1):
                report.append(f"**Group {i}:**")
                for phase_id in group:
                    name = self.phases[phase_id].get("name", phase_id)
                    report.append(f"- {name} (`{phase_id}`)")
                report.append("")
        else:
            report.append("No parallelization opportunities identified.")
            report.append("")

        report.extend(
            [
                "## Recommendations",
                "",
                "1. **Focus on Critical Path:** Optimize phases in the critical path first",
                "2. **Parallelize Where Possible:** Run independent phases concurrently",
                "3. **Monitor Bottlenecks:** Watch phases with many dependents",
                "4. **Cache Aggressively:** Use caching to speed up expensive operations",
                "",
            ]
        )

        result = "\n".join(report)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result)
            logger.info(f"Optimization report saved to {output_path}")

        return result

    def export_all(self, output_dir: Path):
        """
        Export all visualizations and reports.

        Args:
            output_dir: Directory to save outputs
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting visualizations to {output_dir}")

        # Generate all diagrams
        self.generate_mermaid_diagram(
            show_critical=True, output_path=output_dir / "phase_dependencies.md"
        )

        self.generate_data_flow_diagram(output_path=output_dir / "data_flow.md")

        self.generate_optimization_report(
            output_path=output_dir / "optimization_report.md"
        )

        # Export phase definitions as JSON
        with open(output_dir / "phase_definitions.json", "w") as f:
            json.dump(self.phases, f, indent=2)

        logger.info("All visualizations exported successfully")

    def print_summary(self):
        """Print summary of dependency analysis."""
        critical_path = self.identify_critical_path()
        bottlenecks = self.analyze_bottlenecks()

        print("\n" + "=" * 60)
        print("📊 Dependency Analysis Summary")
        print("=" * 60)

        print(f"\n📋 Total Phases: {len(self.phases)}")
        print(f"🎯 Critical Path Length: {len(critical_path)} phases")
        print(f"⚠️  Bottlenecks: {len(bottlenecks)}")

        if critical_path:
            print("\n🔴 Critical Path:")
            for phase_id in critical_path:
                name = self.phases[phase_id].get("name", phase_id)
                print(f"  → {name}")

        if bottlenecks:
            print("\n⚠️  Top Bottlenecks:")
            for bottleneck in bottlenecks[:3]:
                print(
                    f"  • {bottleneck['name']}: {bottleneck['dependent_count']} dependents"
                )

        print("\n" + "=" * 60 + "\n")


def main():
    """Test dependency visualization."""
    import argparse

    parser = argparse.ArgumentParser(description="Dependency Visualizer")
    parser.add_argument("--export", type=Path, help="Export all to directory")
    parser.add_argument("--diagram", type=Path, help="Generate Mermaid diagram")
    parser.add_argument("--flow", type=Path, help="Generate data flow diagram")
    parser.add_argument("--report", type=Path, help="Generate optimization report")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    visualizer = DependencyVisualizer()

    if args.export:
        visualizer.export_all(args.export)
        print(f"\n✅ All visualizations exported to {args.export}")
    elif args.diagram:
        visualizer.generate_mermaid_diagram(output_path=args.diagram)
        print(f"\n✅ Mermaid diagram saved to {args.diagram}")
    elif args.flow:
        visualizer.generate_data_flow_diagram(output_path=args.flow)
        print(f"\n✅ Data flow diagram saved to {args.flow}")
    elif args.report:
        visualizer.generate_optimization_report(output_path=args.report)
        print(f"\n✅ Optimization report saved to {args.report}")
    else:
        visualizer.print_summary()


if __name__ == "__main__":
    main()
