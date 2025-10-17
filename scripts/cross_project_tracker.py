#!/usr/bin/env python3
"""
Cross-Project Tracker for Recommendation Organization & Integration System

Tracks recommendations and implementation status across both projects.
"""

import json
import os
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CrossProjectTracker:
    """
    Tracks recommendations across nba-mcp-synthesis and nba-simulator-aws.
    """

    def __init__(self, synthesis_path: str, simulator_path: str):
        self.synthesis_path = synthesis_path
        self.simulator_path = simulator_path

        # Ensure paths exist
        if not os.path.exists(synthesis_path):
            raise ValueError(f"Synthesis path does not exist: {synthesis_path}")
        if not os.path.exists(simulator_path):
            raise ValueError(f"Simulator path does not exist: {simulator_path}")

    def scan_both_projects(self) -> Dict[str, Any]:
        """
        Scan both projects for implementation status.

        Returns:
            dict: {
                'synthesis': {...},
                'simulator': {...},
                'shared': {...}
            }
        """
        logger.info("Scanning both projects for implementation status...")

        synthesis_status = self._scan_project(self.synthesis_path, "NBA MCP Synthesis")
        simulator_status = self._scan_project(self.simulator_path, "NBA Simulator AWS")

        shared = self._find_shared_implementations(synthesis_status, simulator_status)

        scan_results = {
            "synthesis": synthesis_status,
            "simulator": simulator_status,
            "shared": shared,
            "scan_date": datetime.now().isoformat(),
        }

        logger.info(
            f"Scan complete: {synthesis_status['modules']} synthesis modules, {simulator_status['modules']} simulator modules"
        )

        return scan_results

    def _scan_project(self, project_path: str, project_name: str) -> Dict[str, Any]:
        """Scan a single project for implementation status."""
        logger.info(f"Scanning {project_name} at {project_path}")

        status = {
            "project_name": project_name,
            "project_path": project_path,
            "modules": [],
            "features": [],
            "files": 0,
            "recommendations_implemented": 0,
            "technologies": set(),
            "last_scan": datetime.now().isoformat(),
        }

        try:
            # Count files
            status["files"] = self._count_files(project_path)

            # Find modules
            status["modules"] = self._find_modules(project_path)

            # Find features
            status["features"] = self._find_features(project_path)

            # Find technologies
            status["technologies"] = self._find_technologies(project_path)

            # Count implemented recommendations
            status["recommendations_implemented"] = (
                self._count_implemented_recommendations(project_path)
            )

        except Exception as e:
            logger.error(f"Error scanning {project_name}: {e}")
            status["error"] = str(e)

        return status

    def _count_files(self, project_path: str) -> int:
        """Count files in project with exclusions for performance."""
        try:
            # Use a much simpler approach - just count Python files in top 2 levels
            result = subprocess.run(
                [
                    "find",
                    project_path,
                    "-maxdepth",
                    "2",  # Only 2 levels deep
                    "-type",
                    "f",
                    "-name",
                    "*.py",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                files = result.stdout.strip().split("\n")
                return len([f for f in files if f])  # Filter out empty strings
            else:
                logger.warning(f"File count failed: {result.stderr}")
                return 0

        except Exception as e:
            logger.warning(f"Error counting files: {e}")
            return 0

    def _find_modules(self, project_path: str) -> List[str]:
        """Find Python modules in project."""
        modules = []

        try:
            for root, dirs, files in os.walk(project_path):
                # Calculate depth and limit it
                depth = root[len(project_path) :].count(os.sep)
                if depth >= 3:  # Limit to 3 levels deep
                    dirs[:] = []
                    continue

                # Skip hidden directories and common non-module directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["__pycache__", "node_modules", "venv", "env"]
                ]

                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        module_path = os.path.relpath(
                            os.path.join(root, file), project_path
                        )
                        module_name = (
                            module_path.replace("/", ".")
                            .replace("\\", ".")
                            .replace(".py", "")
                        )
                        modules.append(module_name)

            # Limit to reasonable number
            return modules[:50]

        except Exception as e:
            logger.warning(f"Error finding modules: {e}")
            return []

    def _find_features(self, project_path: str) -> List[str]:
        """Find features implemented in project."""
        features = []

        # Look for common feature indicators
        feature_indicators = [
            "class",
            "def",
            "function",
            "api",
            "endpoint",
            "service",
            "model",
            "database",
            "ml",
            "analysis",
            "recommendation",
        ]

        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read().lower()

                                # Extract class and function names
                                import re

                                classes = re.findall(r"class\s+(\w+)", content)
                                functions = re.findall(r"def\s+(\w+)", content)

                                features.extend(classes)
                                features.extend(functions)

                        except Exception:
                            continue

            # Remove duplicates and limit
            unique_features = list(set(features))[:30]
            return unique_features

        except Exception as e:
            logger.warning(f"Error finding features: {e}")
            return []

    def _find_technologies(self, project_path: str) -> set:
        """Find technologies used in project."""
        technologies = set()

        # Check for common technology indicators
        tech_files = {
            "requirements.txt": "Python",
            "package.json": "Node.js",
            "Dockerfile": "Docker",
            "docker-compose.yml": "Docker Compose",
            "terraform": "Terraform",
            "kubernetes": "Kubernetes",
            "aws": "AWS",
            "postgresql": "PostgreSQL",
            "redis": "Redis",
            "mlflow": "MLflow",
            "pandas": "Pandas",
            "numpy": "NumPy",
            "scikit-learn": "Scikit-learn",
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
        }

        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    file_lower = file.lower()

                    # Check file names
                    for tech_file, tech_name in tech_files.items():
                        if tech_file in file_lower:
                            technologies.add(tech_name)

                    # Check file content for technology mentions
                    if file.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml")):
                        try:
                            file_path = os.path.join(root, file)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read().lower()

                                for tech_keyword, tech_name in tech_files.items():
                                    if tech_keyword in content:
                                        technologies.add(tech_name)

                        except Exception:
                            continue

            return technologies

        except Exception as e:
            logger.warning(f"Error finding technologies: {e}")
            return set()

    def _count_implemented_recommendations(self, project_path: str) -> int:
        """Count implemented recommendations in project."""
        count = 0

        try:
            # Look for recommendation implementation indicators
            implementation_indicators = [
                "recommendation",
                "implemented",
                "completed",
                "done",
                "model versioning",
                "data validation",
                "mlflow",
                "monitoring",
            ]

            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    if file.endswith((".py", ".md")):
                        try:
                            file_path = os.path.join(root, file)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read().lower()

                                for indicator in implementation_indicators:
                                    if indicator in content:
                                        count += 1
                                        break  # Count file only once

                        except Exception:
                            continue

            return count

        except Exception as e:
            logger.warning(f"Error counting implemented recommendations: {e}")
            return 0

    def _find_shared_implementations(
        self, synthesis_status: Dict[str, Any], simulator_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find shared implementations between projects."""
        shared = {
            "shared_modules": [],
            "shared_features": [],
            "shared_technologies": [],
            "integration_points": [],
        }

        # Find shared technologies
        synthesis_tech = synthesis_status.get("technologies", set())
        simulator_tech = simulator_status.get("technologies", set())
        shared["shared_technologies"] = list(
            synthesis_tech.intersection(simulator_tech)
        )

        # Find shared features
        synthesis_features = set(synthesis_status.get("features", []))
        simulator_features = set(simulator_status.get("features", []))
        shared["shared_features"] = list(
            synthesis_features.intersection(simulator_features)
        )

        # Find integration points
        integration_keywords = ["mcp", "api", "integration", "shared", "common"]
        synthesis_modules = synthesis_status.get("modules", [])
        simulator_modules = simulator_status.get("modules", [])

        for module in synthesis_modules:
            if any(keyword in module.lower() for keyword in integration_keywords):
                shared["integration_points"].append(f"synthesis:{module}")

        for module in simulator_modules:
            if any(keyword in module.lower() for keyword in integration_keywords):
                shared["integration_points"].append(f"simulator:{module}")

        return shared

    def generate_unified_status(self, scan_results: Dict[str, Any]) -> str:
        """
        Generate unified implementation status report.

        Args:
            scan_results: Results from scan_both_projects()

        Returns:
            str: Generated report content
        """
        synthesis = scan_results["synthesis"]
        simulator = scan_results["simulator"]
        shared = scan_results["shared"]

        content = f"""# Cross-Project Implementation Status

**Generated:** {scan_results['scan_date']}

---

## Overview

This report tracks implementation status across both NBA MCP Synthesis and NBA Simulator AWS projects.

### Key Metrics

- **Total Files:** {synthesis.get('files', 0) + simulator.get('files', 0)}
- **Total Modules:** {len(synthesis.get('modules', [])) + len(simulator.get('modules', []))}
- **Total Features:** {len(synthesis.get('features', [])) + len(simulator.get('features', []))}
- **Shared Technologies:** {len(shared.get('shared_technologies', []))}

---

## NBA MCP Synthesis

- **Modules:** {len(synthesis.get('modules', []))}
- **Features:** {len(synthesis.get('features', []))}
- **Files:** {synthesis.get('files', 0)}
- **Recommendations Implemented:** {synthesis.get('recommendations_implemented', 0)}
- **Technologies:** {', '.join(sorted(synthesis.get('technologies', [])))}

### Key Modules

{self._format_module_list(synthesis.get('modules', [])[:10])}

### Key Features

{self._format_feature_list(synthesis.get('features', [])[:10])}

---

## NBA Simulator AWS

- **Modules:** {len(simulator.get('modules', []))}
- **Features:** {len(simulator.get('features', []))}
- **Files:** {simulator.get('files', 0)}
- **Recommendations Implemented:** {simulator.get('recommendations_implemented', 0)}
- **Technologies:** {', '.join(sorted(simulator.get('technologies', [])))}

### Key Modules

{self._format_module_list(simulator.get('modules', [])[:10])}

### Key Features

{self._format_feature_list(simulator.get('features', [])[:10])}

---

## Shared Implementations

### Shared Technologies

{self._format_technology_list(shared.get('shared_technologies', []))}

### Shared Features

{self._format_feature_list(shared.get('shared_features', []))}

### Integration Points

{self._format_integration_points(shared.get('integration_points', []))}

---

## Implementation Status by Category

### Critical Recommendations

| Recommendation | Synthesis Status | Simulator Status | Overall Status |
|---------------|------------------|------------------|----------------|
{self._format_status_table(scan_results, 'critical')}

### Important Recommendations

| Recommendation | Synthesis Status | Simulator Status | Overall Status |
|---------------|------------------|------------------|----------------|
{self._format_status_table(scan_results, 'important')}

### Nice-to-Have Recommendations

| Recommendation | Synthesis Status | Simulator Status | Overall Status |
|---------------|------------------|------------------|----------------|
{self._format_status_table(scan_results, 'nice_to_have')}

---

## Next Steps

### Immediate Actions

1. **Review Integration Points**
   - Examine shared technologies and features
   - Identify opportunities for better integration
   - Plan cross-project improvements

2. **Track Implementation Progress**
   - Monitor recommendation completion
   - Update status regularly
   - Identify blockers and dependencies

3. **Optimize Shared Resources**
   - Leverage shared technologies
   - Reduce duplication
   - Improve cross-project communication

### Long-term Actions

1. **Enhance Cross-Project Integration**
   - Implement shared libraries
   - Standardize APIs and interfaces
   - Create unified documentation

2. **Improve Status Tracking**
   - Automate status updates
   - Create dashboards
   - Implement notification systems

---

## Files Generated

- **Cross-Project Status:** `CROSS_PROJECT_IMPLEMENTATION_STATUS.md`
- **Integration Summary:** `integration_summary.md`
- **Phase Enhancement Docs:** `nba-simulator-aws/docs/phases/phase_X/RECOMMENDATIONS_FROM_BOOKS.md`

---

*This report was generated by the Cross-Project Tracker.*
"""

        return content

    def _format_module_list(self, modules: List[str]) -> str:
        """Format module list for display."""
        if not modules:
            return "- No modules found"

        return "\n".join(f"- {module}" for module in modules)

    def _format_feature_list(self, features: List[str]) -> str:
        """Format feature list for display."""
        if not features:
            return "- No features found"

        return "\n".join(f"- {feature}" for feature in features)

    def _format_technology_list(self, technologies: List[str]) -> str:
        """Format technology list for display."""
        if not technologies:
            return "- No shared technologies found"

        return "\n".join(f"- {tech}" for tech in sorted(technologies))

    def _format_integration_points(self, points: List[str]) -> str:
        """Format integration points for display."""
        if not points:
            return "- No integration points found"

        return "\n".join(f"- {point}" for point in points)

    def _format_status_table(self, scan_results: Dict[str, Any], category: str) -> str:
        """Format status table for recommendations."""
        # This would be populated with actual recommendation data
        # For now, return placeholder
        return "| TBD | TBD | TBD | TBD |"

    def save_unified_status(
        self, scan_results: Dict[str, Any], output_path: str
    ) -> None:
        """Save unified status report to file."""
        content = self.generate_unified_status(scan_results)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            f.write(content)

        logger.info(f"Saved unified status report: {output_path}")


def test_cross_project_tracker():
    """Test the CrossProjectTracker functionality."""
    # Create test directories
    test_synthesis = "/tmp/test_synthesis"
    test_simulator = "/tmp/test_simulator"

    os.makedirs(test_synthesis, exist_ok=True)
    os.makedirs(test_simulator, exist_ok=True)

    # Create test files
    test_files = [
        (test_synthesis, "requirements.txt", "pandas\nnumpy\nmlflow"),
        (
            test_synthesis,
            "main.py",
            "class RecommendationSystem:\n    def analyze(self): pass",
        ),
        (test_simulator, "requirements.txt", "pandas\nscikit-learn\naws-sdk"),
        (test_simulator, "model.py", "class MLModel:\n    def train(self): pass"),
    ]

    for base_path, filename, content in test_files:
        file_path = os.path.join(base_path, filename)
        with open(file_path, "w") as f:
            f.write(content)

    # Test tracker
    tracker = CrossProjectTracker(test_synthesis, test_simulator)

    print("🧪 Testing CrossProjectTracker...")

    # Scan both projects
    scan_results = tracker.scan_both_projects()
    print(
        f"  Synthesis: {scan_results['synthesis']['files']} files, {len(scan_results['synthesis']['modules'])} modules"
    )
    print(
        f"  Simulator: {scan_results['simulator']['files']} files, {len(scan_results['simulator']['modules'])} modules"
    )
    print(
        f"  Shared technologies: {len(scan_results['shared']['shared_technologies'])}"
    )

    # Generate unified status
    status_report = tracker.generate_unified_status(scan_results)
    print(f"  Generated status report ({len(status_report)} chars)")

    # Cleanup
    import shutil

    shutil.rmtree(test_synthesis)
    shutil.rmtree(test_simulator)

    print("✅ CrossProjectTracker test completed!")


if __name__ == "__main__":
    test_cross_project_tracker()
