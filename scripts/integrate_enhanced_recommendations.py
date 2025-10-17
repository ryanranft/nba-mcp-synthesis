#!/usr/bin/env python3
"""
Enhanced Recommendations Integrator

This script integrates enhanced recommendations (with GitHub code examples)
into existing project codebases.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedRecommendationsIntegrator:
    """
    Integrates enhanced recommendations with GitHub code examples into project codebases.
    """

    def __init__(self, synthesis_path: str, simulator_path: str):
        self.synthesis_path = Path(synthesis_path)
        self.simulator_path = Path(simulator_path)

        # Ensure paths exist
        if not self.synthesis_path.exists():
            raise ValueError(f"Synthesis path does not exist: {synthesis_path}")
        if not self.simulator_path.exists():
            raise ValueError(f"Simulator path does not exist: {simulator_path}")

        logger.info(
            f"Initialized integrator with paths: {synthesis_path}, {simulator_path}"
        )

    async def integrate_enhanced_recommendations(
        self,
        enhanced_analysis_path: str,
        github_integration_path: str,
        output_dir: str = "integrated_recommendations",
    ) -> Dict[str, Any]:
        """
        Integrate enhanced recommendations with GitHub code examples.

        Args:
            enhanced_analysis_path: Path to enhanced analysis results
            github_integration_path: Path to GitHub integration results
            output_dir: Directory to save integrated results

        Returns:
            Dictionary with integration results
        """
        logger.info(
            "🔗 Integrating enhanced recommendations with GitHub code examples..."
        )

        os.makedirs(output_dir, exist_ok=True)

        # Load enhanced analysis results
        enhanced_analysis = await self._load_analysis_results(enhanced_analysis_path)

        # Load GitHub integration results
        github_integration = await self._load_github_integration(
            github_integration_path
        )

        # Integrate recommendations
        integrated_recommendations = await self._integrate_recommendations(
            enhanced_analysis, github_integration
        )

        # Generate implementation plans
        implementation_plans = await self._generate_implementation_plans(
            integrated_recommendations
        )

        # Create project structure recommendations
        project_structure = await self._create_project_structure_recommendations(
            integrated_recommendations
        )

        # Compile final results
        integration_results = {
            "timestamp": datetime.now().isoformat(),
            "book_title": enhanced_analysis.get("book_title", "Unknown"),
            "enhanced_recommendations": integrated_recommendations,
            "implementation_plans": implementation_plans,
            "project_structure": project_structure,
            "statistics": {
                "total_recommendations": len(integrated_recommendations),
                "recommendations_with_code": len(
                    [r for r in integrated_recommendations if r.get("code_examples")]
                ),
                "total_code_examples": sum(
                    len(r.get("code_examples", [])) for r in integrated_recommendations
                ),
                "repositories_referenced": len(
                    set(
                        r.get("repository", "")
                        for r in integrated_recommendations
                        if r.get("repository")
                    )
                ),
            },
        }

        # Save integration results
        output_file = os.path.join(output_dir, "enhanced_integration_results.json")
        with open(output_file, "w") as f:
            json.dump(integration_results, f, indent=2)

        logger.info(
            f"✅ Integration complete: {integration_results['statistics']['total_recommendations']} recommendations integrated"
        )
        return integration_results

    async def _load_analysis_results(self, analysis_path: str) -> Dict[str, Any]:
        """Load enhanced analysis results."""
        if os.path.exists(analysis_path):
            with open(analysis_path, "r") as f:
                return json.load(f)
        return {}

    async def _load_github_integration(self, github_path: str) -> Dict[str, Any]:
        """Load GitHub integration results."""
        if os.path.exists(github_path):
            with open(github_path, "r") as f:
                return json.load(f)
        return {}

    async def _integrate_recommendations(
        self, enhanced_analysis: Dict, github_integration: Dict
    ) -> List[Dict]:
        """Integrate enhanced recommendations with GitHub code examples."""
        integrated_recommendations = []

        # Get enhanced recommendations from analysis
        enhanced_recommendations = enhanced_analysis.get("enhanced_recommendations", [])

        # Get code examples from GitHub integration
        code_examples = github_integration.get("examples", [])

        # Create a mapping of concepts to code examples
        concept_to_examples = {}
        for example in code_examples:
            concept = example.get("concept", "unknown")
            if concept not in concept_to_examples:
                concept_to_examples[concept] = []
            concept_to_examples[concept].append(example)

        # Integrate recommendations with code examples
        for rec in enhanced_recommendations:
            integrated_rec = rec.copy()

            # Find relevant code examples
            relevant_examples = []
            rec_description = rec.get("description", "").lower()

            for concept, examples in concept_to_examples.items():
                if concept.lower() in rec_description or any(
                    keyword in rec_description for keyword in concept.split("-")
                ):
                    relevant_examples.extend(examples)

            # Add code examples to recommendation
            if relevant_examples:
                integrated_rec["code_examples"] = relevant_examples
                integrated_rec["implementation_guidance"] = (
                    f"See {len(relevant_examples)} code examples from GitHub repositories"
                )

                # Add implementation priority based on code examples
                priority_scores = [
                    self._calculate_priority_score(ex) for ex in relevant_examples
                ]
                integrated_rec["implementation_priority"] = (
                    max(priority_scores) if priority_scores else "medium"
                )

            integrated_recommendations.append(integrated_rec)

        return integrated_recommendations

    def _calculate_priority_score(self, example: Dict) -> str:
        """Calculate implementation priority based on code example."""
        priority = example.get("priority", "medium")
        repo_priority = example.get("repository_priority", "medium")

        # Combine priorities
        if priority == "critical" or repo_priority == "critical":
            return "critical"
        elif priority == "high" or repo_priority == "high":
            return "high"
        else:
            return "medium"

    async def _generate_implementation_plans(
        self, integrated_recommendations: List[Dict]
    ) -> List[Dict]:
        """Generate implementation plans for integrated recommendations."""
        implementation_plans = []

        # Group recommendations by priority
        priority_groups = {"critical": [], "high": [], "medium": [], "low": []}

        for rec in integrated_recommendations:
            priority = rec.get("implementation_priority", "medium")
            priority_groups[priority].append(rec)

        # Create implementation plans for each priority group
        for priority, recommendations in priority_groups.items():
            if recommendations:
                plan = {
                    "priority": priority,
                    "recommendations": recommendations,
                    "implementation_order": self._determine_implementation_order(
                        recommendations
                    ),
                    "estimated_effort": self._estimate_implementation_effort(
                        recommendations
                    ),
                    "dependencies": self._identify_dependencies(recommendations),
                }
                implementation_plans.append(plan)

        return implementation_plans

    def _determine_implementation_order(self, recommendations: List[Dict]) -> List[str]:
        """Determine the order for implementing recommendations."""
        # Simple ordering based on recommendation ID and dependencies
        return [rec.get("id", f"rec_{i}") for i, rec in enumerate(recommendations)]

    def _estimate_implementation_effort(self, recommendations: List[Dict]) -> str:
        """Estimate implementation effort for a group of recommendations."""
        total_examples = sum(
            len(rec.get("code_examples", [])) for rec in recommendations
        )

        if total_examples > 10:
            return "high"
        elif total_examples > 5:
            return "medium"
        else:
            return "low"

    def _identify_dependencies(self, recommendations: List[Dict]) -> List[str]:
        """Identify dependencies between recommendations."""
        dependencies = []

        # Simple dependency identification based on concepts
        concepts = [rec.get("concept", "") for rec in recommendations]

        # Machine learning dependencies
        if "machine-learning" in concepts and "data-preprocessing" not in concepts:
            dependencies.append("data-preprocessing")

        if "deep-learning" in concepts and "machine-learning" not in concepts:
            dependencies.append("machine-learning")

        return dependencies

    async def _create_project_structure_recommendations(
        self, integrated_recommendations: List[Dict]
    ) -> Dict[str, Any]:
        """Create project structure recommendations based on integrated recommendations."""
        project_structure = {
            "directories": [],
            "files": [],
            "dependencies": [],
            "configuration": {},
        }

        # Analyze recommendations to suggest project structure
        concepts = set()
        repositories = set()

        for rec in integrated_recommendations:
            if rec.get("concept"):
                concepts.add(rec["concept"])

            for example in rec.get("code_examples", []):
                if example.get("repository"):
                    repositories.add(example["repository"])

        # Suggest directory structure based on concepts
        if "machine-learning" in concepts:
            project_structure["directories"].extend(
                [
                    "src/ml/",
                    "src/ml/models/",
                    "src/ml/data/",
                    "src/ml/utils/",
                    "tests/ml/",
                    "notebooks/ml/",
                ]
            )

        if "deep-learning" in concepts:
            project_structure["directories"].extend(
                [
                    "src/deep_learning/",
                    "src/deep_learning/models/",
                    "src/deep_learning/training/",
                    "src/deep_learning/inference/",
                    "models/",
                    "data/raw/",
                    "data/processed/",
                ]
            )

        if "mlops" in concepts or "production" in concepts:
            project_structure["directories"].extend(
                ["deployment/", "monitoring/", "pipeline/", "config/", "scripts/"]
            )

        # Suggest files based on repositories
        for repo in repositories:
            if "handson-ml3" in repo:
                project_structure["files"].append("src/ml/handson_ml3_examples.py")
            elif "pyprobml" in repo:
                project_structure["files"].append("src/ml/probabilistic_models.py")
            elif "d2l-en" in repo:
                project_structure["files"].append(
                    "src/deep_learning/d2l_implementations.py"
                )

        # Suggest dependencies based on concepts
        if "machine-learning" in concepts:
            project_structure["dependencies"].extend(
                ["scikit-learn", "pandas", "numpy", "matplotlib", "seaborn"]
            )

        if "deep-learning" in concepts:
            project_structure["dependencies"].extend(
                ["torch", "tensorflow", "keras", "transformers"]
            )

        if "bayesian" in concepts:
            project_structure["dependencies"].extend(["pymc", "pyro", "arviz"])

        # Remove duplicates
        project_structure["directories"] = list(set(project_structure["directories"]))
        project_structure["files"] = list(set(project_structure["files"]))
        project_structure["dependencies"] = list(set(project_structure["dependencies"]))

        return project_structure

    async def generate_implementation_scripts(
        self, integration_results: Dict, output_dir: str
    ) -> List[str]:
        """Generate implementation scripts based on integration results."""
        scripts = []

        implementation_plans = integration_results.get("implementation_plans", [])
        project_structure = integration_results.get("project_structure", {})

        # Generate directory creation script
        dir_script = self._generate_directory_script(
            project_structure["directories"], output_dir
        )
        scripts.append(dir_script)

        # Generate dependency installation script
        deps_script = self._generate_dependencies_script(
            project_structure["dependencies"], output_dir
        )
        scripts.append(deps_script)

        # Generate implementation scripts for each priority
        for plan in implementation_plans:
            impl_script = self._generate_implementation_script(plan, output_dir)
            scripts.append(impl_script)

        return scripts

    def _generate_directory_script(
        self, directories: List[str], output_dir: str
    ) -> str:
        """Generate script to create project directories."""
        script_content = f"""#!/bin/bash
# Generated directory creation script
# Created: {datetime.now().isoformat()}

echo "Creating project directories..."

"""

        for directory in directories:
            script_content += f"mkdir -p {directory}\n"

        script_content += """
echo "Directories created successfully!"
"""

        script_path = os.path.join(output_dir, "create_directories.sh")
        with open(script_path, "w") as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        return script_path

    def _generate_dependencies_script(
        self, dependencies: List[str], output_dir: str
    ) -> str:
        """Generate script to install dependencies."""
        script_content = f"""#!/bin/bash
# Generated dependencies installation script
# Created: {datetime.now().isoformat()}

echo "Installing project dependencies..."

pip install --upgrade pip

"""

        for dep in dependencies:
            script_content += f"pip install {dep}\n"

        script_content += """
echo "Dependencies installed successfully!"
"""

        script_path = os.path.join(output_dir, "install_dependencies.sh")
        with open(script_path, "w") as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        return script_path

    def _generate_implementation_script(self, plan: Dict, output_dir: str) -> str:
        """Generate implementation script for a specific plan."""
        priority = plan["priority"]
        recommendations = plan["recommendations"]

        script_content = f"""#!/bin/bash
# Generated implementation script for {priority} priority recommendations
# Created: {datetime.now().isoformat()}

echo "Implementing {priority} priority recommendations..."

"""

        for rec in recommendations:
            rec_id = rec.get("id", "unknown")
            description = rec.get("description", "No description")

            script_content += f"""
# Implementation: {rec_id}
# Description: {description}

"""

            # Add code examples if available
            for example in rec.get("code_examples", []):
                code_snippet = example.get("code_snippet", "")
                if code_snippet:
                    script_content += f"""
# Code example from {example.get('repository', 'unknown')}:
cat > {example.get('file_path', f'{rec_id}_example.py')} << 'EOF'
{code_snippet}
EOF

"""

        script_content += """
echo "Implementation completed successfully!"
"""

        script_path = os.path.join(
            output_dir, f"implement_{priority}_recommendations.sh"
        )
        with open(script_path, "w") as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        return script_path


async def main():
    """Main function to run enhanced recommendations integration."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    integrator = EnhancedRecommendationsIntegrator(
        synthesis_path="/Users/ryanranft/nba-mcp-synthesis",
        simulator_path="/Users/ryanranft/nba-simulator-aws",
    )

    # Mock paths
    enhanced_analysis_path = "analysis_results/enhanced/sample_analysis.json"
    github_integration_path = (
        "analysis_results/github_integration/sample_integration.json"
    )

    # Create mock data for demonstration
    os.makedirs("analysis_results/enhanced", exist_ok=True)
    os.makedirs("analysis_results/github_integration", exist_ok=True)

    mock_analysis = {
        "book_title": "Hands-On Machine Learning",
        "enhanced_recommendations": [
            {
                "id": "rec_001",
                "description": "Implement machine learning pipeline with scikit-learn",
                "concept": "machine-learning",
                "priority": "high",
            }
        ],
    }

    mock_integration = {
        "examples": [
            {
                "concept": "machine-learning",
                "repository": "handson-ml3",
                "code_snippet": "from sklearn.ensemble import RandomForestClassifier\nclf = RandomForestClassifier()",
                "file_path": "ml_example.py",
                "priority": "critical",
            }
        ]
    }

    with open(enhanced_analysis_path, "w") as f:
        json.dump(mock_analysis, f, indent=2)

    with open(github_integration_path, "w") as f:
        json.dump(mock_integration, f, indent=2)

    # Run integration
    results = await integrator.integrate_enhanced_recommendations(
        enhanced_analysis_path, github_integration_path
    )

    # Generate implementation scripts
    scripts = await integrator.generate_implementation_scripts(
        results, "implementation_scripts"
    )

    print(f"✅ Enhanced recommendations integration completed!")
    print(f"   Generated {len(scripts)} implementation scripts")


if __name__ == "__main__":
    asyncio.run(main())
