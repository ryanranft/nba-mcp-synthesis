#!/usr/bin/env python3
"""
Project Structure Mapper

Maps recommendations to optimal locations in the nba-simulator-aws project.
Analyzes recommendation metadata to determine correct directory structure.

Features:
- Intelligent mapping based on recommendation content
- Detects file type (Python, SQL, config, etc.)
- Returns full paths for implementation
- Suggests test locations
- Handles multi-file recommendations

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """File types for generated code"""

    PYTHON = "python"
    SQL = "sql"
    YAML = "yaml"
    JSON = "json"
    BASH = "bash"
    MARKDOWN = "markdown"


class RecommendationType(Enum):
    """Types of recommendations"""

    ML_MODEL = "ml_model"
    DATA_PROCESSING = "data_processing"
    ETL_PIPELINE = "etl_pipeline"
    DATABASE = "database"
    API = "api"
    MONITORING = "monitoring"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    VALIDATION = "validation"
    GENERAL = "general"


@dataclass
class FileMapping:
    """Represents a file mapping for a recommendation"""

    file_type: FileType
    target_directory: str
    filename: str
    full_path: str
    test_directory: Optional[str] = None
    test_filename: Optional[str] = None
    test_full_path: Optional[str] = None
    related_files: List[str] = None  # SQL, config, etc.


class ProjectStructureMapper:
    """
    Maps recommendations to correct locations in nba-simulator-aws project.

    Uses intelligent analysis of recommendation content to determine:
    - Target directory
    - Filename
    - File type
    - Test location
    - Related files
    """

    # Keyword patterns for recommendation type detection
    TYPE_PATTERNS = {
        RecommendationType.ML_MODEL: [
            "model",
            "training",
            "prediction",
            "classifier",
            "regression",
            "neural",
            "machine learning",
            "ml",
            "scikit",
            "tensorflow",
            "keras",
            "pytorch",
            "xgboost",
            "random forest",
            "gradient boost",
        ],
        RecommendationType.DATA_PROCESSING: [
            "etl",
            "transform",
            "clean",
            "preprocess",
            "feature engineering",
            "data quality",
            "normalization",
            "aggregation",
            "feature store",
        ],
        RecommendationType.ETL_PIPELINE: [
            "pipeline",
            "scraper",
            "crawler",
            "extract",
            "incremental",
            "scrape",
            "fetch",
            "download",
            "sync",
            "collect",
        ],
        RecommendationType.DATABASE: [
            "database",
            "schema",
            "migration",
            "table",
            "index",
            "query",
            "sql",
            "postgres",
            "rds",
            "stored procedure",
            "view",
        ],
        RecommendationType.API: [
            "api",
            "endpoint",
            "route",
            "rest",
            "fastapi",
            "flask",
            "service",
            "mcp",
            "server",
        ],
        RecommendationType.MONITORING: [
            "monitor",
            "logging",
            "metrics",
            "alert",
            "dashboard",
            "observability",
            "tracking",
            "telemetry",
            "health",
        ],
        RecommendationType.TESTING: [
            "test",
            "validation",
            "verify",
            "check",
            "quality assurance",
            "pytest",
            "unit test",
            "integration test",
        ],
        RecommendationType.DEPLOYMENT: [
            "deploy",
            "docker",
            "kubernetes",
            "cicd",
            "automation",
            "lambda",
            "aws",
            "cloud",
            "container",
        ],
        RecommendationType.ANALYSIS: [
            "analysis",
            "statistical",
            "bayesian",
            "econometric",
            "causal",
            "panel data",
            "regression analysis",
            "hypothesis test",
        ],
        RecommendationType.AUTOMATION: [
            "automate",
            "schedule",
            "cron",
            "workflow",
            "orchestrat",
            "batch",
            "task",
            "job",
        ],
        RecommendationType.INTEGRATION: [
            "integrat",
            "multi-source",
            "combine",
            "merge",
            "consolidat",
            "unified",
            "cross-validate",
        ],
        RecommendationType.VALIDATION: [
            "validat",
            "check",
            "verify",
            "audit",
            "quality control",
            "cross-check",
            "reconcil",
        ],
    }

    # Directory mappings for nba-simulator-aws
    DIRECTORY_MAPPINGS = {
        RecommendationType.ML_MODEL: "scripts/ml",
        RecommendationType.DATA_PROCESSING: "scripts/ml",
        RecommendationType.ETL_PIPELINE: "scripts/etl",
        RecommendationType.DATABASE: "scripts/db",
        RecommendationType.API: "mcp_server",
        RecommendationType.MONITORING: "scripts/monitoring",
        RecommendationType.TESTING: "tests",
        RecommendationType.DEPLOYMENT: "scripts/deployment",
        RecommendationType.ANALYSIS: "scripts/analysis",
        RecommendationType.AUTOMATION: "scripts/automation",
        RecommendationType.INTEGRATION: "scripts/integration",
        RecommendationType.VALIDATION: "scripts/validation",
        RecommendationType.GENERAL: "scripts",
    }

    def __init__(self, target_project: str = "../nba-simulator-aws"):
        """
        Initialize mapper.

        Args:
            target_project: Path to nba-simulator-aws project
        """
        self.target_project = Path(target_project).resolve()

        if not self.target_project.exists():
            logger.warning(f"⚠️  Target project not found: {self.target_project}")
            logger.warning("   Mapper will return paths, but they may not exist yet")

        logger.info(f"🗺️  Project Structure Mapper initialized")
        logger.info(f"   Target project: {self.target_project}")

    def map_recommendation(self, recommendation: Dict[str, Any]) -> FileMapping:
        """
        Map a recommendation to project structure.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            FileMapping with target locations
        """
        title = recommendation.get("title", "Untitled")
        logger.info(f"🔍 Mapping: {title}")

        # Detect recommendation type
        rec_type = self._detect_recommendation_type(recommendation)
        logger.info(f"   Type: {rec_type.value}")

        # Detect file type
        file_type = self._detect_file_type(recommendation, rec_type)
        logger.info(f"   File type: {file_type.value}")

        # Get target directory
        target_dir = self._get_target_directory(rec_type, recommendation)
        logger.info(f"   Directory: {target_dir}")

        # Generate filename
        filename = self._generate_filename(recommendation, file_type, rec_type)
        logger.info(f"   Filename: {filename}")

        # Build full path
        full_path = str(self.target_project / target_dir / filename)

        # Determine test location
        test_dir, test_filename, test_full_path = self._get_test_location(
            filename, target_dir, file_type
        )

        # Detect related files (SQL, config, etc.)
        related_files = self._detect_related_files(recommendation, rec_type)

        mapping = FileMapping(
            file_type=file_type,
            target_directory=target_dir,
            filename=filename,
            full_path=full_path,
            test_directory=test_dir,
            test_filename=test_filename,
            test_full_path=test_full_path,
            related_files=related_files,
        )

        logger.info(f"✅ Mapped to: {full_path}")
        if test_full_path:
            logger.info(f"   Test: {test_full_path}")

        return mapping

    def _detect_recommendation_type(self, rec: Dict[str, Any]) -> RecommendationType:
        """Detect recommendation type from content"""
        text = (
            rec.get("title", "")
            + " "
            + rec.get("description", "")
            + " "
            + rec.get("technical_details", "")
            + " "
            + " ".join(rec.get("implementation_steps", []))
        ).lower()

        # Score each type
        scores = {}
        for rec_type, keywords in self.TYPE_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            scores[rec_type] = score

        # Return type with highest score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                return best_type[0]

        return RecommendationType.GENERAL

    def _detect_file_type(
        self, rec: Dict[str, Any], rec_type: RecommendationType
    ) -> FileType:
        """Detect primary file type needed"""
        text = (rec.get("title", "") + " " + rec.get("technical_details", "")).lower()

        # SQL if database-related
        if rec_type == RecommendationType.DATABASE or "sql" in text or "query" in text:
            return FileType.SQL

        # YAML if config-related
        if "config" in text or "yaml" in text or "settings" in text:
            return FileType.YAML

        # Bash if automation script
        if "bash" in text or "shell" in text or ".sh" in text:
            return FileType.BASH

        # Default to Python
        return FileType.PYTHON

    def _get_target_directory(
        self, rec_type: RecommendationType, rec: Dict[str, Any]
    ) -> str:
        """Get target directory for recommendation"""
        base_dir = self.DIRECTORY_MAPPINGS.get(rec_type, "scripts")

        # For ETL, check if it's a specific subdirectory
        if rec_type == RecommendationType.ETL_PIPELINE:
            text = rec.get("title", "").lower()
            if "basketball reference" in text or "bref" in text or "bbref" in text:
                return "scripts/etl"
            elif "espn" in text:
                return "scripts/etl"
            elif "hoopr" in text:
                return "scripts/etl"

        # For ML, check if it's feature engineering or model
        if rec_type == RecommendationType.ML_MODEL:
            text = rec.get("title", "").lower()
            if "feature" in text and ("store" in text or "engineering" in text):
                return "scripts/ml"

        return base_dir

    def _generate_filename(
        self, rec: Dict[str, Any], file_type: FileType, rec_type: RecommendationType
    ) -> str:
        """Generate filename from recommendation"""
        title = rec.get("title", "untitled")

        # Convert title to filename
        # Remove special characters, convert to snake_case
        filename = re.sub(r"[^\w\s-]", "", title.lower())
        filename = re.sub(r"[-\s]+", "_", filename)
        filename = filename.strip("_")[:60]  # Limit length

        # Add appropriate extension
        if file_type == FileType.PYTHON:
            return f"{filename}.py"
        elif file_type == FileType.SQL:
            return f"{filename}.sql"
        elif file_type == FileType.YAML:
            return f"{filename}.yaml"
        elif file_type == FileType.JSON:
            return f"{filename}.json"
        elif file_type == FileType.BASH:
            return f"{filename}.sh"
        elif file_type == FileType.MARKDOWN:
            return f"{filename}.md"
        else:
            return f"{filename}.txt"

    def _get_test_location(
        self, filename: str, target_dir: str, file_type: FileType
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Determine test file location"""
        # Only generate tests for Python files
        if file_type != FileType.PYTHON:
            return None, None, None

        # Test directory
        test_dir = "tests"

        # Test filename (prepend with test_)
        if filename.startswith("test_"):
            test_filename = filename
        else:
            base_name = filename.replace(".py", "")
            test_filename = f"test_{base_name}.py"

        # Full path
        test_full_path = str(self.target_project / test_dir / test_filename)

        return test_dir, test_filename, test_full_path

    def _detect_related_files(
        self, rec: Dict[str, Any], rec_type: RecommendationType
    ) -> List[str]:
        """Detect if recommendation needs related files (SQL, config, etc.)"""
        related = []

        text = (
            rec.get("description", "") + " " + rec.get("technical_details", "")
        ).lower()

        # SQL file needed?
        if "database" in text or "table" in text or "query" in text:
            if rec_type != RecommendationType.DATABASE:  # Only if not already SQL
                title = rec.get("title", "untitled")
                sql_filename = self._generate_filename(rec, FileType.SQL, rec_type)
                sql_path = str(self.target_project / "sql" / sql_filename)
                related.append(sql_path)

        # Config file needed?
        if "config" in text or "settings" in text:
            title = rec.get("title", "untitled")
            config_filename = self._generate_filename(rec, FileType.YAML, rec_type)
            config_path = str(self.target_project / "config" / config_filename)
            related.append(config_path)

        return related if related else None

    def validate_mapping(self, mapping: FileMapping) -> Tuple[bool, List[str]]:
        """
        Validate a file mapping.

        Args:
            mapping: FileMapping to validate

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check if target directory exists
        target_path = Path(mapping.full_path).parent
        if not target_path.exists():
            issues.append(f"Target directory does not exist: {target_path}")

        # Check if file already exists
        if Path(mapping.full_path).exists():
            issues.append(f"File already exists: {mapping.full_path}")

        # Check if test directory exists
        if mapping.test_full_path:
            test_path = Path(mapping.test_full_path).parent
            if not test_path.exists():
                issues.append(f"Test directory does not exist: {test_path}")

        # Check for related files directory existence
        if mapping.related_files:
            for related_file in mapping.related_files:
                related_path = Path(related_file).parent
                if not related_path.exists():
                    issues.append(
                        f"Related file directory does not exist: {related_path}"
                    )

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_existing_modules(self, directory: str) -> List[str]:
        """
        Get list of existing Python modules in a directory.

        Args:
            directory: Directory path relative to target project

        Returns:
            List of Python file paths
        """
        target_dir = self.target_project / directory

        if not target_dir.exists():
            return []

        # Find all .py files
        python_files = list(target_dir.glob("*.py"))

        # Exclude __init__.py and __pycache__
        python_files = [
            str(f.relative_to(self.target_project))
            for f in python_files
            if f.name != "__init__.py" and "__pycache__" not in str(f)
        ]

        return sorted(python_files)


def main():
    """CLI for testing structure mapper"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Map recommendations to project structure"
    )
    parser.add_argument(
        "--recommendation", required=True, help="Path to recommendation JSON"
    )
    parser.add_argument(
        "--target-project", default="../nba-simulator-aws", help="Target project path"
    )
    args = parser.parse_args()

    # Load recommendation
    with open(args.recommendation, "r") as f:
        data = json.load(f)

    # Handle different formats
    if isinstance(data, dict) and "recommendations" in data:
        recommendations = data["recommendations"]
    elif isinstance(data, list):
        recommendations = data
    else:
        recommendations = [data]

    # Map each recommendation
    mapper = ProjectStructureMapper(target_project=args.target_project)

    for rec in recommendations[:5]:  # Limit to first 5
        print(f"\n{'='*60}")
        print(f"Recommendation: {rec.get('title', 'Untitled')}")
        print(f"{'='*60}")

        mapping = mapper.map_recommendation(rec)

        print(f"\nFile Type: {mapping.file_type.value}")
        print(f"Target: {mapping.full_path}")

        if mapping.test_full_path:
            print(f"Test: {mapping.test_full_path}")

        if mapping.related_files:
            print(f"\nRelated files:")
            for rf in mapping.related_files:
                print(f"  - {rf}")

        # Validate
        is_valid, issues = mapper.validate_mapping(mapping)
        print(f"\nValid: {is_valid}")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")


if __name__ == "__main__":
    main()
