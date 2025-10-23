#!/usr/bin/env python3
"""
Code Integration Analyzer

Analyzes existing code in target project to determine optimal integration strategy.
Uses AST parsing to understand existing code structure and recommend integration approach.

Features:
- AST-based Python code analysis
- Detects classes, functions, imports
- Identifies integration points
- Recommends integration strategies
- Detects potential conflicts
- Preserves existing functionality

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class IntegrationStrategy(Enum):
    """Integration strategies for new code"""

    CREATE_NEW_MODULE = "create_new_module"
    EXTEND_EXISTING_CLASS = "extend_existing_class"
    ADD_FUNCTION_TO_MODULE = "add_function_to_module"
    MODIFY_EXISTING_FUNCTION = "modify_existing_function"
    CREATE_SUBCLASS = "create_subclass"
    ADD_TO_EXISTING_FILE = "add_to_existing_file"
    REPLACE_MODULE = "replace_module"


@dataclass
class ModuleInfo:
    """Information about an existing module"""

    path: str
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    lines_of_code: int = 0
    complexity: str = "unknown"  # low, medium, high
    has_main: bool = False
    last_modified: Optional[float] = None


@dataclass
class IntegrationPoint:
    """Represents a potential integration point"""

    strategy: IntegrationStrategy
    target_file: Optional[str]
    target_class: Optional[str] = None
    target_function: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    reasoning: str = ""
    conflicts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class IntegrationPlan:
    """Complete integration plan for a recommendation"""

    primary_strategy: IntegrationStrategy
    integration_points: List[IntegrationPoint]
    new_files_needed: List[str]
    modifications_needed: List[str]
    potential_conflicts: List[str]
    safety_notes: List[str]


class CodeIntegrationAnalyzer:
    """
    Analyzes existing code to determine optimal integration strategy.

    Features:
    - Parse Python code using AST
    - Identify classes, functions, imports
    - Detect integration opportunities
    - Recommend strategies
    - Flag potential conflicts
    """

    def __init__(self, project_root: str = "../nba-simulator-aws"):
        """
        Initialize analyzer.

        Args:
            project_root: Path to target project
        """
        self.project_root = Path(project_root).resolve()
        self.module_cache: Dict[str, ModuleInfo] = {}

        logger.info(f"🔬 Code Integration Analyzer initialized")
        logger.info(f"   Project root: {self.project_root}")

    def analyze_integration(
        self, recommendation: Dict[str, Any], target_file: str
    ) -> IntegrationPlan:
        """
        Analyze how to integrate recommendation into target file.

        Args:
            recommendation: Recommendation dictionary
            target_file: Proposed target file path

        Returns:
            IntegrationPlan with strategy recommendations
        """
        title = recommendation.get("title", "Untitled")
        logger.info(f"🔍 Analyzing integration for: {title}")
        logger.info(f"   Target: {target_file}")

        # Check if target file exists
        target_path = Path(target_file)
        file_exists = target_path.exists()

        if file_exists:
            logger.info(f"   ✅ Target file exists - analyzing existing code")
            # Analyze existing module
            module_info = self._analyze_module(target_file)

            # Determine integration strategy
            integration_points = self._find_integration_points(
                recommendation, module_info
            )

            # Select primary strategy
            primary_strategy = self._select_primary_strategy(
                integration_points, module_info, recommendation
            )

            # Determine modifications needed
            modifications = self._determine_modifications(
                primary_strategy, integration_points, module_info
            )

            # Check for conflicts
            conflicts = self._check_conflicts(
                recommendation, module_info, integration_points
            )

            new_files = []

        else:
            logger.info(f"   ℹ️  Target file does not exist - will create new")
            # Create new module strategy
            primary_strategy = IntegrationStrategy.CREATE_NEW_MODULE

            integration_points = [
                IntegrationPoint(
                    strategy=IntegrationStrategy.CREATE_NEW_MODULE,
                    target_file=target_file,
                    confidence=1.0,
                    reasoning="Target file does not exist - creating new module",
                )
            ]

            modifications = []
            conflicts = []
            new_files = [target_file]

        # Generate safety notes
        safety_notes = self._generate_safety_notes(
            primary_strategy, file_exists, conflicts
        )

        plan = IntegrationPlan(
            primary_strategy=primary_strategy,
            integration_points=integration_points,
            new_files_needed=new_files,
            modifications_needed=modifications,
            potential_conflicts=conflicts,
            safety_notes=safety_notes,
        )

        logger.info(f"✅ Integration plan created")
        logger.info(f"   Strategy: {primary_strategy.value}")
        logger.info(f"   New files: {len(new_files)}")
        logger.info(f"   Modifications: {len(modifications)}")
        logger.info(f"   Conflicts: {len(conflicts)}")

        return plan

    def _analyze_module(self, file_path: str) -> ModuleInfo:
        """
        Analyze existing Python module using AST.

        Args:
            file_path: Path to Python file

        Returns:
            ModuleInfo with module details
        """
        # Check cache
        if file_path in self.module_cache:
            return self.module_cache[file_path]

        logger.info(f"   Parsing: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Parse AST
            tree = ast.parse(code)

            # Extract information
            classes = []
            functions = []
            imports = []
            docstring = ast.get_docstring(tree)
            has_main = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)

                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)

                    # Check for main function
                    if node.name == "main":
                        has_main = True

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    else:
                        if node.module:
                            imports.append(node.module)

            # Count lines
            lines_of_code = len(code.split("\n"))

            # Estimate complexity
            complexity = "low"
            if lines_of_code > 500:
                complexity = "high"
            elif lines_of_code > 200:
                complexity = "medium"

            # Get last modified time
            last_modified = Path(file_path).stat().st_mtime

            module_info = ModuleInfo(
                path=file_path,
                classes=classes,
                functions=functions,
                imports=list(set(imports)),
                docstring=docstring,
                lines_of_code=lines_of_code,
                complexity=complexity,
                has_main=has_main,
                last_modified=last_modified,
            )

            # Cache
            self.module_cache[file_path] = module_info

            logger.info(f"   ✅ Parsed successfully")
            logger.info(f"      Classes: {len(classes)}")
            logger.info(f"      Functions: {len(functions)}")
            logger.info(f"      LOC: {lines_of_code}")

            return module_info

        except Exception as e:
            logger.error(f"   ❌ Failed to parse {file_path}: {e}")
            # Return minimal info
            return ModuleInfo(path=file_path, complexity="unknown")

    def _find_integration_points(
        self, recommendation: Dict[str, Any], module_info: ModuleInfo
    ) -> List[IntegrationPoint]:
        """
        Find potential integration points in existing module.

        Args:
            recommendation: Recommendation dictionary
            module_info: Analyzed module information

        Returns:
            List of potential integration points
        """
        integration_points = []
        title = recommendation.get("title", "").lower()

        # Strategy 1: Extend existing class
        if module_info.classes:
            for class_name in module_info.classes:
                # Check if class name relates to recommendation
                similarity = self._calculate_similarity(title, class_name.lower())

                if similarity > 0.3:  # 30% similarity threshold
                    integration_points.append(
                        IntegrationPoint(
                            strategy=IntegrationStrategy.EXTEND_EXISTING_CLASS,
                            target_file=module_info.path,
                            target_class=class_name,
                            confidence=similarity,
                            reasoning=f"Extends existing class '{class_name}' (similarity: {similarity:.2f})",
                        )
                    )

        # Strategy 2: Add function to module
        if not module_info.classes or len(module_info.functions) > 3:
            # Module is function-based or has many functions
            integration_points.append(
                IntegrationPoint(
                    strategy=IntegrationStrategy.ADD_FUNCTION_TO_MODULE,
                    target_file=module_info.path,
                    confidence=0.7,
                    reasoning="Module is function-based, add new function(s)",
                )
            )

        # Strategy 3: Create new module (if existing is complex)
        if module_info.complexity == "high":
            integration_points.append(
                IntegrationPoint(
                    strategy=IntegrationStrategy.CREATE_NEW_MODULE,
                    target_file=None,
                    confidence=0.8,
                    reasoning=f"Existing module is complex ({module_info.lines_of_code} LOC), recommend new module",
                )
            )

        # Strategy 4: Add to existing file (if simple)
        if module_info.complexity == "low":
            integration_points.append(
                IntegrationPoint(
                    strategy=IntegrationStrategy.ADD_TO_EXISTING_FILE,
                    target_file=module_info.path,
                    confidence=0.9,
                    reasoning="Module is small and simple, safe to add code",
                )
            )

        return integration_points

    def _select_primary_strategy(
        self,
        integration_points: List[IntegrationPoint],
        module_info: ModuleInfo,
        recommendation: Dict[str, Any],
    ) -> IntegrationStrategy:
        """
        Select the best integration strategy.

        Args:
            integration_points: Available integration points
            module_info: Module information
            recommendation: Recommendation

        Returns:
            Best integration strategy
        """
        if not integration_points:
            return IntegrationStrategy.CREATE_NEW_MODULE

        # Sort by confidence
        sorted_points = sorted(
            integration_points, key=lambda x: x.confidence, reverse=True
        )

        # Return highest confidence strategy
        return sorted_points[0].strategy

    def _determine_modifications(
        self,
        primary_strategy: IntegrationStrategy,
        integration_points: List[IntegrationPoint],
        module_info: ModuleInfo,
    ) -> List[str]:
        """Determine what modifications are needed"""
        modifications = []

        if primary_strategy == IntegrationStrategy.EXTEND_EXISTING_CLASS:
            point = next(
                (p for p in integration_points if p.strategy == primary_strategy), None
            )
            if point and point.target_class:
                modifications.append(
                    f"Add methods to class '{point.target_class}' in {module_info.path}"
                )

        elif primary_strategy == IntegrationStrategy.ADD_FUNCTION_TO_MODULE:
            modifications.append(f"Add new function(s) to {module_info.path}")

        elif primary_strategy == IntegrationStrategy.ADD_TO_EXISTING_FILE:
            modifications.append(f"Add new class/functions to {module_info.path}")

        return modifications

    def _check_conflicts(
        self,
        recommendation: Dict[str, Any],
        module_info: ModuleInfo,
        integration_points: List[IntegrationPoint],
    ) -> List[str]:
        """Check for potential conflicts"""
        conflicts = []

        title = recommendation.get("title", "")

        # Check for name conflicts
        proposed_name = self._title_to_name(title)

        # Check against existing classes
        for class_name in module_info.classes:
            if proposed_name.lower() == class_name.lower():
                conflicts.append(
                    f"Name conflict: Proposed name '{proposed_name}' conflicts with existing class '{class_name}'"
                )

        # Check against existing functions
        for func_name in module_info.functions:
            if proposed_name.lower() == func_name.lower():
                conflicts.append(
                    f"Name conflict: Proposed name '{proposed_name}' conflicts with existing function '{func_name}'"
                )

        return conflicts

    def _generate_safety_notes(
        self, strategy: IntegrationStrategy, file_exists: bool, conflicts: List[str]
    ) -> List[str]:
        """Generate safety notes for integration"""
        notes = []

        if strategy == IntegrationStrategy.CREATE_NEW_MODULE:
            notes.append("✅ Creating new module - low risk")

        elif strategy in [
            IntegrationStrategy.EXTEND_EXISTING_CLASS,
            IntegrationStrategy.ADD_FUNCTION_TO_MODULE,
            IntegrationStrategy.ADD_TO_EXISTING_FILE,
        ]:
            notes.append("⚠️  Modifying existing file - review changes carefully")
            notes.append("💾 Backup existing file before modification")
            notes.append("🧪 Run existing tests to ensure no regressions")

        elif strategy == IntegrationStrategy.MODIFY_EXISTING_FUNCTION:
            notes.append("🚨 Modifying existing function - HIGH RISK")
            notes.append("✅ Ensure comprehensive tests exist")
            notes.append("📝 Document all changes")

        if conflicts:
            notes.append(f"⚠️  {len(conflicts)} potential conflict(s) detected")

        if file_exists:
            notes.append("📂 File exists - integration will merge with existing code")

        return notes

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple similarity between two strings.

        Args:
            text1: First string
            text2: Second string

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple word-based similarity
        words1 = set(text1.lower().split("_"))
        words2 = set(text2.lower().split("_"))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _title_to_name(self, title: str) -> str:
        """Convert title to potential class/function name"""
        import re

        # Remove special characters, convert to PascalCase
        words = re.sub(r"[^\w\s]", "", title).split()
        return "".join(word.capitalize() for word in words)

    def find_similar_modules(
        self, recommendation: Dict[str, Any], search_directory: str
    ) -> List[Tuple[str, float]]:
        """
        Find modules similar to recommendation in a directory.

        Args:
            recommendation: Recommendation dictionary
            search_directory: Directory to search

        Returns:
            List of (file_path, similarity_score) tuples
        """
        search_path = self.project_root / search_directory

        if not search_path.exists():
            return []

        title = recommendation.get("title", "").lower()
        description = recommendation.get("description", "").lower()
        search_text = f"{title} {description}"

        similar_modules = []

        # Find all Python files
        for py_file in search_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Analyze module
            module_info = self._analyze_module(str(py_file))

            # Calculate similarity based on:
            # 1. Filename similarity
            # 2. Docstring similarity
            # 3. Class/function names

            filename_sim = self._calculate_similarity(title, py_file.stem)

            docstring_sim = 0.0
            if module_info.docstring:
                docstring_sim = self._calculate_similarity(
                    search_text, module_info.docstring.lower()
                )

            names_sim = 0.0
            if module_info.classes or module_info.functions:
                all_names = " ".join(module_info.classes + module_info.functions)
                names_sim = self._calculate_similarity(search_text, all_names.lower())

            # Weighted average
            overall_sim = filename_sim * 0.4 + docstring_sim * 0.3 + names_sim * 0.3

            if overall_sim > 0.2:  # 20% threshold
                similar_modules.append((str(py_file), overall_sim))

        # Sort by similarity
        similar_modules.sort(key=lambda x: x[1], reverse=True)

        return similar_modules


def main():
    """CLI for testing analyzer"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Analyze code integration")
    parser.add_argument(
        "--recommendation", required=True, help="Path to recommendation JSON"
    )
    parser.add_argument("--target-file", required=True, help="Target file path")
    parser.add_argument(
        "--project-root", default="../nba-simulator-aws", help="Project root"
    )
    args = parser.parse_args()

    # Load recommendation
    with open(args.recommendation, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        rec = data[0]
    elif isinstance(data, dict) and "recommendations" in data:
        rec = data["recommendations"][0]
    else:
        rec = data

    # Analyze
    analyzer = CodeIntegrationAnalyzer(project_root=args.project_root)
    plan = analyzer.analyze_integration(rec, args.target_file)

    # Display results
    print(f"\n{'='*60}")
    print(f"Integration Plan for: {rec.get('title', 'Untitled')}")
    print(f"{'='*60}\n")

    print(f"Primary Strategy: {plan.primary_strategy.value}\n")

    print(f"Integration Points: {len(plan.integration_points)}")
    for i, point in enumerate(plan.integration_points, 1):
        print(f"\n  {i}. {point.strategy.value}")
        print(f"     Confidence: {point.confidence:.2f}")
        print(f"     Reasoning: {point.reasoning}")

    if plan.new_files_needed:
        print(f"\nNew Files:")
        for f in plan.new_files_needed:
            print(f"  - {f}")

    if plan.modifications_needed:
        print(f"\nModifications:")
        for m in plan.modifications_needed:
            print(f"  - {m}")

    if plan.potential_conflicts:
        print(f"\nPotential Conflicts:")
        for c in plan.potential_conflicts:
            print(f"  ⚠️  {c}")

    if plan.safety_notes:
        print(f"\nSafety Notes:")
        for note in plan.safety_notes:
            print(f"  {note}")


if __name__ == "__main__":
    main()
