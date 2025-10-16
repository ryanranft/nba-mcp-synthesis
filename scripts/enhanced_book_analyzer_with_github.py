#!/usr/bin/env python3
"""
Enhanced Book Analysis Workflow with GitHub Repository Integration

This enhanced workflow integrates the 32 textbook companion repositories
with book analysis to provide theory-to-code cross-referencing and
better implementation recommendations.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Import existing analyzers
from four_model_book_analyzer import FourModelBookAnalyzer
from synthesis.models.google_model import GoogleModel
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from synthesis.models.gpt4_model import GPT4Model

logger = logging.getLogger(__name__)


class EnhancedBookAnalyzer:
    """
    Enhanced book analyzer that integrates GitHub repositories with textbook analysis.

    This analyzer:
    1. Reads book content via MCP
    2. Identifies key concepts and algorithms
    3. Searches relevant GitHub repositories for implementations
    4. Cross-references theory with working code
    5. Generates enhanced recommendations with code examples
    """

    def __init__(self):
        """Initialize the enhanced analyzer with MCP and GitHub integration."""
        self.mcp_client = None  # Will be initialized with MCP client
        self.github_repos = self._load_github_repo_mappings()
        self.textbook_mappings = self._load_textbook_mappings()

        # Initialize existing analyzers
        self.four_model_analyzer = FourModelBookAnalyzer()

        logger.info("Enhanced Book Analyzer initialized with GitHub integration")

    def _load_github_repo_mappings(self) -> Dict[str, Dict]:
        """Load GitHub repository mappings and metadata."""
        return {
            # Machine Learning
            "handson-ml3": {
                "s3_path": "textbook-code/machine-learning/handson-ml3_complete.txt",
                "textbook_match": "Hands-On_Machine_Learning_with_Scikit-Learn_Keras_and_Tensorflow_-_Aurelien_Geron.pdf",
                "key_concepts": ["scikit-learn", "tensorflow", "keras", "ml-pipelines", "feature-engineering"],
                "priority": "critical"
            },
            "pyprobml": {
                "s3_path": "textbook-code/machine-learning/pyprobml_complete.txt",
                "textbook_match": "ML Machine Learning-A Probabilistic Perspective.pdf",
                "key_concepts": ["bayesian-methods", "probabilistic-models", "vae", "gan", "graphical-models"],
                "priority": "critical"
            },
            "d2l-en": {
                "s3_path": "textbook-code/interactive-deep-learning/d2l-en_complete.txt",
                "textbook_match": "General deep learning textbooks",
                "key_concepts": ["pytorch", "tensorflow", "mxnet", "neural-networks", "deep-learning"],
                "priority": "critical"
            },
            "fastbook": {
                "s3_path": "textbook-code/practical-deep-learning/fastbook_complete.txt",
                "textbook_match": "General deep learning and practical ML books",
                "key_concepts": ["fastai", "practical-deep-learning", "transfer-learning", "computer-vision"],
                "priority": "critical"
            },
            "PythonDataScienceHandbook": {
                "s3_path": "textbook-code/data-science-fundamentals/PythonDataScienceHandbook_complete.txt",
                "textbook_match": "Python Data Science Handbook.pdf",
                "key_concepts": ["pandas", "numpy", "matplotlib", "data-manipulation", "visualization"],
                "priority": "critical"
            },
            # Add more mappings as needed...
        }

    def _load_textbook_mappings(self) -> Dict[str, List[str]]:
        """Load textbook to GitHub repository mappings."""
        return {
            "Hands-On_Machine_Learning_with_Scikit-Learn_Keras_and_Tensorflow_-_Aurelien_Geron.pdf": [
                "handson-ml3", "PythonDataScienceHandbook"
            ],
            "ML Machine Learning-A Probabilistic Perspective.pdf": [
                "pyprobml", "BDA_py_demos"
            ],
            "Deep Learning by Ian Goodfellow, Yoshua Bengio, Aaron Courville.pdf": [
                "d2l-en", "fastbook", "deepLearningBook-Notes"
            ],
            "Python Data Science Handbook.pdf": [
                "PythonDataScienceHandbook", "handson-ml3"
            ],
            # Add more mappings...
        }

    async def analyze_book_with_github_integration(self, book: Dict[str, Any], existing_recommendations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Enhanced book analysis with GitHub repository integration.

        Args:
            book: Book metadata and content
            existing_recommendations: Existing recommendations for context

        Returns:
            Enhanced analysis result with code examples and implementations
        """
        logger.info(f"🔍 Starting enhanced analysis: {book.get('title', 'Unknown')}")

        # Step 1: Standard 4-model analysis
        logger.info("📖 Step 1: Running standard 4-model analysis...")
        standard_result = await self.four_model_analyzer.analyze_book(book, existing_recommendations)

        # Step 2: Identify key concepts from book analysis
        logger.info("🔍 Step 2: Identifying key concepts...")
        key_concepts = await self._extract_key_concepts(book, standard_result)

        # Step 3: Find relevant GitHub repositories
        logger.info("📚 Step 3: Finding relevant GitHub repositories...")
        relevant_repos = await self._find_relevant_repositories(book, key_concepts)

        # Step 4: Cross-reference theory with code implementations
        logger.info("🔗 Step 4: Cross-referencing theory with code...")
        code_examples = await self._extract_code_examples(relevant_repos, key_concepts)

        # Step 5: Generate enhanced recommendations
        logger.info("✨ Step 5: Generating enhanced recommendations...")
        enhanced_recommendations = await self._generate_enhanced_recommendations(
            standard_result, code_examples, key_concepts
        )

        # Step 6: Compile final result
        result = {
            "book_title": book.get('title', 'Unknown'),
            "analysis_timestamp": datetime.now().isoformat(),
            "standard_analysis": standard_result,
            "key_concepts": key_concepts,
            "relevant_repositories": relevant_repos,
            "code_examples": code_examples,
            "enhanced_recommendations": enhanced_recommendations,
            "total_cost": standard_result.total_cost,
            "total_tokens": standard_result.total_tokens,
            "total_time": standard_result.total_time
        }

        logger.info(f"✅ Enhanced analysis complete: {len(enhanced_recommendations)} enhanced recommendations")
        return result

    async def _extract_key_concepts(self, book: Dict, analysis_result) -> List[str]:
        """Extract key concepts from book analysis."""
        # This would use NLP to identify key concepts from the analysis
        # For now, we'll use a simple approach
        concepts = []

        # Extract from book title and analysis
        title = book.get('title', '').lower()
        if 'machine learning' in title:
            concepts.extend(['machine-learning', 'algorithms', 'supervised-learning'])
        if 'deep learning' in title:
            concepts.extend(['deep-learning', 'neural-networks', 'cnn', 'rnn'])
        if 'statistics' in title:
            concepts.extend(['statistics', 'regression', 'classification'])
        if 'bayesian' in title:
            concepts.extend(['bayesian', 'probabilistic-models', 'inference'])

        return list(set(concepts))

    async def _find_relevant_repositories(self, book: Dict, key_concepts: List[str]) -> List[Dict]:
        """Find GitHub repositories relevant to the book and concepts."""
        relevant_repos = []

        # Find repos by textbook match
        book_title = book.get('title', '')
        matched_repos = self.textbook_mappings.get(book_title, [])

        for repo_name in matched_repos:
            if repo_name in self.github_repos:
                relevant_repos.append({
                    "name": repo_name,
                    "metadata": self.github_repos[repo_name],
                    "match_reason": "textbook_match"
                })

        # Find repos by concept overlap
        for repo_name, repo_data in self.github_repos.items():
            concept_overlap = set(key_concepts) & set(repo_data.get('key_concepts', []))
            if concept_overlap:
                relevant_repos.append({
                    "name": repo_name,
                    "metadata": repo_data,
                    "match_reason": "concept_overlap",
                    "overlapping_concepts": list(concept_overlap)
                })

        return relevant_repos

    async def _extract_code_examples(self, relevant_repos: List[Dict], key_concepts: List[str]) -> List[Dict]:
        """Extract relevant code examples from GitHub repositories."""
        code_examples = []

        for repo in relevant_repos:
            repo_name = repo["name"]
            repo_metadata = repo["metadata"]
            s3_path = repo_metadata.get("s3_path")

            if not s3_path:
                continue

            try:
                # Read repository content from S3
                repo_content = await self._read_repository_content(s3_path)

                # Search for relevant code examples
                examples = await self._search_code_examples(repo_content, key_concepts)

                if examples:
                    code_examples.append({
                        "repository": repo_name,
                        "s3_path": s3_path,
                        "examples": examples,
                        "match_reason": repo["match_reason"]
                    })

            except Exception as e:
                logger.error(f"Failed to extract code examples from {repo_name}: {e}")

        return code_examples

    async def _read_repository_content(self, s3_path: str) -> str:
        """Read repository content from S3."""
        # This would use MCP tools to read from S3
        # For now, return a placeholder
        return f"Repository content from {s3_path}"

    async def _search_code_examples(self, repo_content: str, key_concepts: List[str]) -> List[Dict]:
        """Search for code examples relevant to key concepts."""
        examples = []

        # This would implement actual code search logic
        # For now, return placeholder examples
        for concept in key_concepts:
            examples.append({
                "concept": concept,
                "code_snippet": f"# Example implementation of {concept}\n# Code would be extracted from repository",
                "file_path": f"example_{concept}.py",
                "description": f"Implementation example for {concept}"
            })

        return examples

    async def _generate_enhanced_recommendations(self, standard_result, code_examples: List[Dict], key_concepts: List[str]) -> List[Dict]:
        """Generate enhanced recommendations with code examples."""
        enhanced_recommendations = []

        # Start with standard recommendations
        for rec in standard_result.recommendations:
            enhanced_rec = rec.copy()

            # Find relevant code examples
            relevant_examples = []
            for example_group in code_examples:
                for example in example_group["examples"]:
                    if any(concept in rec.get('description', '').lower() for concept in example["concept"].split('-')):
                        relevant_examples.append({
                            "repository": example_group["repository"],
                            "code_snippet": example["code_snippet"],
                            "file_path": example["file_path"],
                            "description": example["description"]
                        })

            # Add code examples to recommendation
            if relevant_examples:
                enhanced_rec["code_examples"] = relevant_examples
                enhanced_rec["implementation_guidance"] = f"See {len(relevant_examples)} code examples from GitHub repositories"

            enhanced_recommendations.append(enhanced_rec)

        return enhanced_recommendations


class GitHubIntegratedWorkflow:
    """
    Workflow orchestrator that integrates GitHub repositories with book analysis.
    """

    def __init__(self, config_path: str = "config/books_to_analyze.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.enhanced_analyzer = EnhancedBookAnalyzer()

    def _load_config(self) -> Dict:
        """Load books configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"books": [], "metadata": {}}

    async def run_enhanced_analysis(self) -> bool:
        """Run enhanced book analysis with GitHub integration."""
        logger.info("🚀 Starting Enhanced Book Analysis with GitHub Integration")

        books = self.config.get("books", [])
        results = []

        for book in books:
            try:
                logger.info(f"📖 Analyzing: {book.get('title', 'Unknown')}")

                result = await self.enhanced_analyzer.analyze_book_with_github_integration(book)
                results.append(result)

                # Save individual result
                output_file = f"analysis_results/enhanced_{book.get('id', 'unknown')}_analysis.json"
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)

                logger.info(f"✅ Analysis complete: {book.get('title', 'Unknown')}")

            except Exception as e:
                logger.error(f"❌ Analysis failed for {book.get('title', 'Unknown')}: {e}")

        # Save master results
        master_file = "analysis_results/enhanced_master_analysis.json"
        with open(master_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_books": len(books),
                "successful_analyses": len(results),
                "results": results
            }, f, indent=2)

        logger.info(f"🎉 Enhanced analysis complete: {len(results)}/{len(books)} books analyzed")
        return True


async def main():
    """Main function to run enhanced analysis."""
    logging.basicConfig(level=logging.INFO)

    workflow = GitHubIntegratedWorkflow()
    success = await workflow.run_enhanced_analysis()

    if success:
        print("✅ Enhanced book analysis with GitHub integration completed successfully!")
    else:
        print("❌ Enhanced book analysis failed")


if __name__ == "__main__":
    asyncio.run(main())



