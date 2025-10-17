#!/usr/bin/env python3
"""
Code Example Generator for Enhanced Book Analysis

This script extracts relevant code examples from GitHub repositories
based on book analysis results and key concepts.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeExampleGenerator:
    """
    Generates code examples from GitHub repositories based on book analysis.
    """

    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.github_mappings = self._load_github_mappings()

    def _load_github_mappings(self) -> Dict:
        """Load GitHub repository mappings."""
        config_path = "config/github_repo_mappings.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    async def generate_code_examples(
        self, analysis_results: Dict, output_dir: str
    ) -> Dict[str, Any]:
        """
        Generate code examples from GitHub repositories based on analysis results.

        Args:
            analysis_results: Results from enhanced book analysis
            output_dir: Directory to save generated examples

        Returns:
            Dictionary with generated code examples
        """
        logger.info("🔍 Generating code examples from GitHub repositories...")

        os.makedirs(output_dir, exist_ok=True)

        code_examples = {
            "timestamp": datetime.now().isoformat(),
            "book_title": analysis_results.get("book_title", "Unknown"),
            "examples": [],
            "summary": {
                "total_examples": 0,
                "repositories_used": [],
                "concepts_covered": [],
            },
        }

        # Extract key concepts from analysis
        key_concepts = analysis_results.get("key_concepts", [])
        relevant_repos = analysis_results.get("relevant_repositories", [])

        for repo in relevant_repos:
            repo_name = repo["name"]
            repo_metadata = repo["metadata"]

            logger.info(f"📚 Processing repository: {repo_name}")

            try:
                # Extract code examples for this repository
                examples = await self._extract_repo_code_examples(
                    repo_name, repo_metadata, key_concepts
                )

                if examples:
                    code_examples["examples"].extend(examples)
                    code_examples["summary"]["repositories_used"].append(repo_name)

                    # Track concepts covered
                    for example in examples:
                        if (
                            example.get("concept")
                            not in code_examples["summary"]["concepts_covered"]
                        ):
                            code_examples["summary"]["concepts_covered"].append(
                                example.get("concept")
                            )

            except Exception as e:
                logger.error(f"Failed to process repository {repo_name}: {e}")

        # Update summary
        code_examples["summary"]["total_examples"] = len(code_examples["examples"])

        # Save code examples
        output_file = os.path.join(
            output_dir,
            f"code_examples_{analysis_results.get('book_title', 'unknown').replace(' ', '_')}.json",
        )
        with open(output_file, "w") as f:
            json.dump(code_examples, f, indent=2)

        logger.info(f"✅ Generated {len(code_examples['examples'])} code examples")
        return code_examples

    async def _extract_repo_code_examples(
        self, repo_name: str, repo_metadata: Dict, key_concepts: List[str]
    ) -> List[Dict]:
        """Extract code examples from a specific repository."""
        examples = []

        s3_path = repo_metadata.get("s3_path")
        if not s3_path:
            return examples

        try:
            # Read repository content from S3
            repo_content = await self._read_repository_content(s3_path)

            # Extract examples for each key concept
            for concept in key_concepts:
                concept_examples = await self._search_concept_examples(
                    repo_content, concept, repo_name, repo_metadata
                )
                examples.extend(concept_examples)

        except Exception as e:
            logger.error(f"Failed to extract examples from {repo_name}: {e}")

        return examples

    async def _read_repository_content(self, s3_path: str) -> str:
        """Read repository content from S3 using MCP tools."""
        try:
            # This would use MCP tools to read from S3
            # For now, return a placeholder
            return f"Repository content from {s3_path}"
        except Exception as e:
            logger.error(f"Failed to read repository content from {s3_path}: {e}")
            return ""

    async def _search_concept_examples(
        self, repo_content: str, concept: str, repo_name: str, repo_metadata: Dict
    ) -> List[Dict]:
        """Search for code examples related to a specific concept."""
        examples = []

        # Define search patterns for different concepts
        concept_patterns = {
            "machine-learning": [
                r"class.*Classifier",
                r"def.*fit\(",
                r"def.*predict\(",
                r"from sklearn",
                r"import.*sklearn",
            ],
            "deep-learning": [
                r"import torch",
                r"import tensorflow",
                r"class.*Model",
                r"def.*forward\(",
                r"nn\.Module",
            ],
            "neural-networks": [
                r"class.*Network",
                r"def.*forward\(",
                r"nn\.Linear",
                r"nn\.ReLU",
                r"torch\.nn",
            ],
            "regression": [
                r"LinearRegression",
                r"def.*regress",
                r"from sklearn\.linear_model",
                r"Ridge",
                r"Lasso",
            ],
            "classification": [
                r"RandomForestClassifier",
                r"SVC",
                r"LogisticRegression",
                r"def.*classify",
                r"from sklearn\.ensemble",
            ],
            "clustering": [
                r"KMeans",
                r"DBSCAN",
                r"def.*cluster",
                r"from sklearn\.cluster",
            ],
            "bayesian": [
                r"import pymc",
                r"import pyro",
                r"def.*bayesian",
                r"posterior",
                r"prior",
            ],
            "reinforcement-learning": [
                r"class.*Agent",
                r"def.*q_learning",
                r"def.*policy",
                r"import gym",
                r"env\.step",
            ],
            "computer-vision": [
                r"import cv2",
                r"import PIL",
                r"def.*detect",
                r"def.*segment",
                r"torchvision",
            ],
            "natural-language-processing": [
                r"import nltk",
                r"import spacy",
                r"def.*tokenize",
                r"def.*embed",
                r"transformers",
            ],
        }

        # Get patterns for the concept
        patterns = concept_patterns.get(
            concept, [f"def.*{concept}", f"class.*{concept}"]
        )

        # Search for patterns in content
        for pattern in patterns:
            matches = re.finditer(pattern, repo_content, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 200)
                end = min(len(repo_content), match.end() + 200)
                context = repo_content[start:end]

                # Extract code snippet
                code_snippet = self._extract_code_snippet(
                    context, match.start() - start
                )

                if code_snippet:
                    examples.append(
                        {
                            "concept": concept,
                            "repository": repo_name,
                            "code_snippet": code_snippet,
                            "pattern_matched": pattern,
                            "context": context,
                            "file_path": f"example_{concept}_{len(examples)}.py",
                            "description": f"Implementation example for {concept} from {repo_name}",
                            "priority": repo_metadata.get("priority", "medium"),
                            "s3_path": repo_metadata.get("s3_path"),
                        }
                    )

        return examples

    def _extract_code_snippet(self, context: str, match_position: int) -> Optional[str]:
        """Extract a clean code snippet from context."""
        lines = context.split("\n")

        # Find the line containing the match
        current_pos = 0
        match_line = 0

        for i, line in enumerate(lines):
            if current_pos <= match_position < current_pos + len(line) + 1:
                match_line = i
                break
            current_pos += len(line) + 1

        # Extract surrounding lines (5 lines before and after)
        start_line = max(0, match_line - 5)
        end_line = min(len(lines), match_line + 6)

        snippet_lines = lines[start_line:end_line]

        # Clean up the snippet
        snippet = "\n".join(snippet_lines).strip()

        # Basic validation - should contain some code
        if len(snippet) > 50 and (
            "def " in snippet or "class " in snippet or "import " in snippet
        ):
            return snippet

        return None

    async def generate_concept_summary(
        self, code_examples: Dict, output_dir: str
    ) -> Dict[str, Any]:
        """Generate a summary of concepts and their implementations."""
        concept_summary = {
            "timestamp": datetime.now().isoformat(),
            "concepts": {},
            "repositories": {},
            "statistics": {
                "total_examples": len(code_examples.get("examples", [])),
                "total_concepts": 0,
                "total_repositories": 0,
            },
        }

        # Group examples by concept
        for example in code_examples.get("examples", []):
            concept = example.get("concept", "unknown")
            repo = example.get("repository", "unknown")

            # Add to concept summary
            if concept not in concept_summary["concepts"]:
                concept_summary["concepts"][concept] = {
                    "examples": [],
                    "repositories": set(),
                    "total_examples": 0,
                }

            concept_summary["concepts"][concept]["examples"].append(example)
            concept_summary["concepts"][concept]["repositories"].add(repo)
            concept_summary["concepts"][concept]["total_examples"] += 1

            # Add to repository summary
            if repo not in concept_summary["repositories"]:
                concept_summary["repositories"][repo] = {
                    "examples": [],
                    "concepts": set(),
                    "total_examples": 0,
                }

            concept_summary["repositories"][repo]["examples"].append(example)
            concept_summary["repositories"][repo]["concepts"].add(concept)
            concept_summary["repositories"][repo]["total_examples"] += 1

        # Convert sets to lists for JSON serialization
        for concept_data in concept_summary["concepts"].values():
            concept_data["repositories"] = list(concept_data["repositories"])

        for repo_data in concept_summary["repositories"].values():
            repo_data["concepts"] = list(repo_data["concepts"])

        # Update statistics
        concept_summary["statistics"]["total_concepts"] = len(
            concept_summary["concepts"]
        )
        concept_summary["statistics"]["total_repositories"] = len(
            concept_summary["repositories"]
        )

        # Save concept summary
        summary_file = os.path.join(output_dir, "concept_summary.json")
        with open(summary_file, "w") as f:
            json.dump(concept_summary, f, indent=2)

        logger.info(
            f"✅ Generated concept summary: {concept_summary['statistics']['total_concepts']} concepts, {concept_summary['statistics']['total_repositories']} repositories"
        )

        return concept_summary


async def main():
    """Main function to generate code examples."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    generator = CodeExampleGenerator()

    # Mock analysis results
    analysis_results = {
        "book_title": "Hands-On Machine Learning",
        "key_concepts": ["machine-learning", "scikit-learn", "tensorflow", "keras"],
        "relevant_repositories": [
            {
                "name": "handson-ml3",
                "metadata": {
                    "s3_path": "textbook-code/machine-learning/handson-ml3_complete.txt",
                    "priority": "critical",
                },
            }
        ],
    }

    output_dir = "code_examples"
    code_examples = await generator.generate_code_examples(analysis_results, output_dir)
    concept_summary = await generator.generate_concept_summary(
        code_examples, output_dir
    )

    print("✅ Code example generation completed!")


if __name__ == "__main__":
    asyncio.run(main())
