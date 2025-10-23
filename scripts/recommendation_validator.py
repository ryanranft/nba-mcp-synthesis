#!/usr/bin/env python3
"""
Automated Recommendation Validator

Validates recommendations for quality and feasibility before finalizing.

Validation Checks:
1. Library Compatibility - Verify libraries exist and work with Python 3.11+
2. Data References - Verify tables/columns exist in data inventory
3. Code Syntax - Validate code snippets are syntactically correct
4. Time Estimates - Check if time estimates are reasonable

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import re
import ast
import json
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""

    passed: bool
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]
    details: Dict[str, Any]


class RecommendationValidator:
    """
    Validates recommendations for quality and feasibility.

    Performs comprehensive validation including:
    - Library compatibility checking
    - Data reference verification
    - Code syntax validation
    - Time estimate reasonableness
    """

    def __init__(
        self,
        project_inventory: Optional[Dict] = None,
        requirements_file: Optional[str] = None,
    ):
        """
        Initialize validator.

        Args:
            project_inventory: Data inventory from data_inventory_scanner
            requirements_file: Path to requirements.txt for dependency checking
        """
        self.project_inventory = project_inventory
        self.requirements_file = requirements_file or "requirements.txt"

        # Load existing requirements if file exists
        self.existing_requirements = self._load_requirements()

        logger.info("✅ Recommendation Validator initialized")

    def _load_requirements(self) -> Dict[str, str]:
        """Load existing requirements from requirements.txt"""
        requirements = {}

        req_path = Path(self.requirements_file)
        if not req_path.exists():
            logger.warning(f"⚠️  Requirements file not found: {self.requirements_file}")
            return requirements

        with open(req_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Parse requirement (e.g., "package==1.2.3" or "package>=1.0")
                    match = re.match(r"([a-zA-Z0-9_-]+)", line)
                    if match:
                        package = match.group(1).lower()
                        requirements[package] = line

        logger.info(f"📦 Loaded {len(requirements)} existing requirements")
        return requirements

    def validate_recommendation(
        self, recommendation: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a single recommendation.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            ValidationResult with all validation checks
        """
        logger.info(f"🔍 Validating: {recommendation.get('title', 'Untitled')}")

        all_warnings = []
        all_errors = []
        all_suggestions = []
        all_details = {}

        # Check 1: Library Compatibility
        library_result = self.validate_libraries(recommendation)
        all_warnings.extend(library_result.warnings)
        all_errors.extend(library_result.errors)
        all_suggestions.extend(library_result.suggestions)
        all_details["libraries"] = library_result.details

        # Check 2: Data References
        data_result = self.validate_data_references(recommendation)
        all_warnings.extend(data_result.warnings)
        all_errors.extend(data_result.errors)
        all_suggestions.extend(data_result.suggestions)
        all_details["data_references"] = data_result.details

        # Check 3: Code Syntax
        code_result = self.validate_code_snippets(recommendation)
        all_warnings.extend(code_result.warnings)
        all_errors.extend(code_result.errors)
        all_suggestions.extend(code_result.suggestions)
        all_details["code_snippets"] = code_result.details

        # Check 4: Time Estimate
        time_result = self.validate_time_estimate(recommendation)
        all_warnings.extend(time_result.warnings)
        all_errors.extend(time_result.errors)
        all_suggestions.extend(time_result.suggestions)
        all_details["time_estimate"] = time_result.details

        # Overall result
        passed = len(all_errors) == 0

        return ValidationResult(
            passed=passed,
            warnings=all_warnings,
            errors=all_errors,
            suggestions=all_suggestions,
            details=all_details,
        )

    def validate_libraries(self, recommendation: Dict[str, Any]) -> ValidationResult:
        """
        Validate library compatibility.

        Checks:
        - Library exists on PyPI
        - Python 3.11+ compatibility
        - Conflicts with existing dependencies
        """
        warnings = []
        errors = []
        suggestions = []
        details = {}

        # Extract library names from technical details and description
        text = f"{recommendation.get('technical_details', '')} {recommendation.get('description', '')}"
        libraries = self._extract_libraries(text)

        if not libraries:
            details["libraries_found"] = []
            return ValidationResult(True, warnings, errors, suggestions, details)

        logger.info(
            f"📦 Found {len(libraries)} library references: {', '.join(libraries)}"
        )

        for lib in libraries:
            lib_lower = lib.lower().replace("-", "_").replace(" ", "_")

            # Check if already in requirements
            if lib_lower in self.existing_requirements:
                details[lib] = {
                    "status": "existing",
                    "version": self.existing_requirements[lib_lower],
                    "note": "Already in requirements.txt",
                }
                continue

            # Check PyPI
            pypi_info = self._check_pypi(lib)

            if not pypi_info["exists"]:
                errors.append(f"Library '{lib}' not found on PyPI")
                suggestions.append(f"Check if '{lib}' is the correct package name")
                details[lib] = {"status": "not_found", "pypi_exists": False}
                continue

            # Check Python version compatibility
            python_compat = self._check_python_compatibility(lib, pypi_info)

            details[lib] = {
                "status": "valid" if python_compat else "incompatible",
                "pypi_exists": True,
                "latest_version": pypi_info.get("version", "unknown"),
                "python_311_compatible": python_compat,
                "requires_python": pypi_info.get("requires_python", "unknown"),
            }

            if not python_compat:
                errors.append(
                    f"Library '{lib}' may not be compatible with Python 3.11+"
                )
                suggestions.append(f"Check for alternative libraries or newer versions")
            else:
                suggestions.append(
                    f"Add to requirements.txt: {lib}>={pypi_info.get('version', '0.0.0')}"
                )

        details["libraries_found"] = libraries
        passed = len(errors) == 0

        return ValidationResult(passed, warnings, errors, suggestions, details)

    def validate_data_references(
        self, recommendation: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate data table and column references.

        Checks if referenced tables/columns exist in data inventory.
        """
        warnings = []
        errors = []
        suggestions = []
        details = {}

        if not self.project_inventory:
            warnings.append("No project inventory provided - skipping data validation")
            return ValidationResult(True, warnings, errors, suggestions, details)

        # Extract table and column references
        text = f"{recommendation.get('description', '')} {recommendation.get('technical_details', '')}"
        data_refs = self._extract_data_references(text)

        if not data_refs:
            details["data_references_found"] = {}
            return ValidationResult(True, warnings, errors, suggestions, details)

        logger.info(f"📊 Found {len(data_refs)} data references")

        # Get schema from inventory
        schema = (
            self.project_inventory.get("data_inventory", {})
            .get("schema", {})
            .get("tables", {})
        )

        if not schema:
            warnings.append(
                "No database schema in inventory - cannot validate data references"
            )
            return ValidationResult(True, warnings, errors, suggestions, details)

        for table, columns in data_refs.items():
            if table not in schema:
                errors.append(f"Table '{table}' not found in database schema")
                suggestions.append(
                    f"Available tables: {', '.join(list(schema.keys())[:5])}"
                )
                details[table] = {"exists": False, "columns": {}}
                continue

            # Table exists - check columns
            table_columns = schema[table].get("column_names", [])
            column_validation = {}

            for col in columns:
                if col in table_columns:
                    column_validation[col] = {"exists": True, "status": "valid"}
                else:
                    column_validation[col] = {"exists": False, "status": "not_found"}
                    errors.append(f"Column '{col}' not found in table '{table}'")
                    suggestions.append(
                        f"Available columns in {table}: {', '.join(table_columns[:10])}"
                    )

            details[table] = {
                "exists": True,
                "columns": column_validation,
                "available_columns": table_columns,
            }

        details["data_references_found"] = data_refs
        passed = len(errors) == 0

        return ValidationResult(passed, warnings, errors, suggestions, details)

    def validate_code_snippets(
        self, recommendation: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate code snippets for syntax errors.

        Extracts and compiles Python code blocks.
        """
        warnings = []
        errors = []
        suggestions = []
        details = {}

        # Extract code snippets
        text = recommendation.get("technical_details", "")
        snippets = self._extract_code_blocks(text)

        if not snippets:
            details["snippets_found"] = 0
            return ValidationResult(True, warnings, errors, suggestions, details)

        logger.info(f"💻 Found {len(snippets)} code snippets")

        valid_count = 0
        for idx, snippet in enumerate(snippets):
            snippet_id = f"snippet_{idx + 1}"

            try:
                # Try to compile the code
                compile(snippet, f"<{snippet_id}>", "exec")

                details[snippet_id] = {
                    "valid": True,
                    "lines": len(snippet.split("\n")),
                    "error": None,
                }
                valid_count += 1

            except SyntaxError as e:
                details[snippet_id] = {
                    "valid": False,
                    "lines": len(snippet.split("\n")),
                    "error": str(e),
                    "line": e.lineno,
                }
                errors.append(
                    f"Syntax error in {snippet_id}: {e.msg} (line {e.lineno})"
                )
                suggestions.append(f"Review and fix syntax in {snippet_id}")

            except Exception as e:
                # Other compilation errors
                details[snippet_id] = {
                    "valid": False,
                    "lines": len(snippet.split("\n")),
                    "error": str(e),
                }
                warnings.append(f"Could not validate {snippet_id}: {e}")

        details["snippets_found"] = len(snippets)
        details["valid_snippets"] = valid_count
        passed = len(errors) == 0

        return ValidationResult(passed, warnings, errors, suggestions, details)

    def validate_time_estimate(
        self, recommendation: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate time estimate reasonableness.

        Checks if time estimate aligns with priority and complexity.
        """
        warnings = []
        errors = []
        suggestions = []
        details = {}

        estimate = recommendation.get("time_estimate", "")
        priority = recommendation.get("priority", "UNKNOWN")
        steps = recommendation.get("implementation_steps", [])

        # Extract hours
        hours = self._extract_hours(estimate)

        if hours == 0:
            warnings.append("No time estimate provided")
            details["hours"] = 0
            details["warnings"] = ["Missing time estimate"]
            return ValidationResult(True, warnings, errors, suggestions, details)

        details["hours"] = hours
        details["priority"] = priority
        details["steps"] = len(steps)
        details["hours_per_step"] = hours / len(steps) if steps else 0

        # Validation heuristics
        if hours < 2 and priority == "CRITICAL":
            warnings.append(
                f"CRITICAL priority with only {hours} hours seems underestimated"
            )
            suggestions.append(
                "Consider if this is truly a quick task or needs more time"
            )

        if hours > 40:
            warnings.append(f"Large time estimate ({hours} hours)")
            suggestions.append(
                "Consider breaking into multiple smaller recommendations"
            )

        if steps and hours / len(steps) > 10:
            warnings.append(f"Each step averages {hours / len(steps):.1f} hours")
            suggestions.append("Consider adding more granular implementation steps")

        if steps and hours / len(steps) < 0.5:
            warnings.append(
                f"Each step averages {hours / len(steps):.1f} hours - very detailed"
            )

        details["reasonable"] = len(warnings) == 0
        passed = len(errors) == 0

        return ValidationResult(passed, warnings, errors, suggestions, details)

    # ===== Helper Methods =====

    def _extract_libraries(self, text: str) -> List[str]:
        """Extract library names from text"""
        libraries = set()

        # Common Python libraries that might be mentioned
        library_patterns = [
            r"\b(scikit-learn|sklearn)\b",
            r"\b(tensorflow|tf)\b",
            r"\b(keras)\b",
            r"\b(pytorch|torch)\b",
            r"\b(numpy|np)\b",
            r"\b(pandas|pd)\b",
            r"\b(matplotlib|plt)\b",
            r"\b(seaborn|sns)\b",
            r"\b(xgboost)\b",
            r"\b(lightgbm)\b",
            r"\b(catboost)\b",
            r"\b(flask)\b",
            r"\b(fastapi)\b",
            r"\b(django)\b",
            r"\b(sqlalchemy)\b",
            r"\b(pytest)\b",
            r"\b(requests)\b",
            r"\b(boto3)\b",
            r"\b(pymupdf)\b",
            r"\b(anthropic)\b",
        ]

        for pattern in library_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                # Normalize library name
                if match in ["sklearn", "np", "pd", "plt", "sns", "tf"]:
                    # Map abbreviations to full names
                    mapping = {
                        "sklearn": "scikit-learn",
                        "np": "numpy",
                        "pd": "pandas",
                        "plt": "matplotlib",
                        "sns": "seaborn",
                        "tf": "tensorflow",
                    }
                    libraries.add(mapping.get(match, match))
                else:
                    libraries.add(match)

        return sorted(list(libraries))

    def _extract_data_references(self, text: str) -> Dict[str, List[str]]:
        """Extract table and column references from text"""
        references = {}

        # Pattern for table references (e.g., "master_player_game_stats table")
        table_pattern = r"\b(master_\w+)\b"
        tables = re.findall(table_pattern, text.lower())

        for table in set(tables):
            # Find columns mentioned near this table
            # Look for common column names
            column_pattern = r"\b(player_id|game_id|team_id|points|rebounds|assists|plus_minus|minutes_played|date|season)\b"

            # Search in context around table mention
            table_context_pattern = (
                f"{table}.*?(?:column|field|attribute).*?({column_pattern})"
            )
            context_matches = re.findall(table_context_pattern, text.lower())

            # Also search for columns without explicit table context
            all_columns = re.findall(column_pattern, text.lower())

            if table not in references:
                references[table] = []

            references[table].extend([col for col in all_columns])
            references[table] = list(set(references[table]))  # Deduplicate

        return references

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from text"""
        snippets = []

        # Find Python code blocks (```python ... ``` or ``` ... ```)
        code_block_pattern = r"```(?:python)?\s*(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        for match in matches:
            snippet = match.strip()
            if snippet and len(snippet) > 10:  # Ignore very short snippets
                snippets.append(snippet)

        return snippets

    def _extract_hours(self, estimate: str) -> float:
        """Extract hours from time estimate string"""
        # Match patterns like "12 hours", "8-10 hours", "1 day", etc.
        hour_pattern = r"(\d+(?:\.\d+)?)\s*(?:hour|hr|h)\b"
        day_pattern = r"(\d+(?:\.\d+)?)\s*day"

        hour_match = re.search(hour_pattern, estimate.lower())
        if hour_match:
            return float(hour_match.group(1))

        day_match = re.search(day_pattern, estimate.lower())
        if day_match:
            return float(day_match.group(1)) * 8  # 8 hours per day

        # Try to extract just a number
        number_pattern = r"(\d+(?:\.\d+)?)"
        number_match = re.search(number_pattern, estimate)
        if number_match:
            return float(number_match.group(1))

        return 0.0

    def _check_pypi(self, package: str) -> Dict[str, Any]:
        """Check if package exists on PyPI"""
        try:
            url = f"https://pypi.org/pypi/{package}/json"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                info = data.get("info", {})
                return {
                    "exists": True,
                    "version": info.get("version", "unknown"),
                    "requires_python": info.get("requires_python", "unknown"),
                    "summary": info.get("summary", ""),
                }
            else:
                return {"exists": False}

        except Exception as e:
            logger.warning(f"⚠️  Could not check PyPI for {package}: {e}")
            return {"exists": False, "error": str(e)}

    def _check_python_compatibility(self, package: str, pypi_info: Dict) -> bool:
        """Check if package is compatible with Python 3.11+"""
        requires_python = pypi_info.get("requires_python", "")

        if not requires_python or requires_python == "unknown":
            # No explicit requirement - assume compatible
            return True

        # Simple check: if requires_python includes 3.11 or higher
        # This is a heuristic - real check would parse version specifiers
        if "3.11" in requires_python or ">=3" in requires_python:
            return True

        if "<3.11" in requires_python or "<=3.10" in requires_python:
            return False

        # Default to assuming compatible
        return True

    def generate_validation_report(
        self, recommendation: Dict[str, Any], result: ValidationResult
    ) -> str:
        """Generate markdown validation report"""

        title = recommendation.get("title", "Untitled")
        status = "✅ PASSED" if result.passed else "❌ FAILED"

        report = f"""# Validation Report: {title}

## Overall Status: {status}

"""

        # Errors
        if result.errors:
            report += "## ❌ Errors\n\n"
            for error in result.errors:
                report += f"- {error}\n"
            report += "\n"

        # Warnings
        if result.warnings:
            report += "## ⚠️ Warnings\n\n"
            for warning in result.warnings:
                report += f"- {warning}\n"
            report += "\n"

        # Suggestions
        if result.suggestions:
            report += "## 💡 Suggestions\n\n"
            for suggestion in result.suggestions:
                report += f"- {suggestion}\n"
            report += "\n"

        # Detailed Results
        report += "## 📋 Detailed Validation Results\n\n"

        # Libraries
        if "libraries" in result.details:
            lib_details = result.details["libraries"]
            libs_found = lib_details.get("libraries_found", [])

            if libs_found:
                report += "### Library Compatibility\n\n"
                for lib in libs_found:
                    if lib in lib_details:
                        lib_info = lib_details[lib]
                        status_icon = (
                            "✅"
                            if lib_info.get("status") in ["valid", "existing"]
                            else "❌"
                        )
                        report += f"- {status_icon} **{lib}**: {lib_info.get('status', 'unknown')}\n"
                        if "version" in lib_info:
                            report += f"  - Version: {lib_info['version']}\n"
                        if "latest_version" in lib_info:
                            report += f"  - Latest: {lib_info['latest_version']}\n"
                report += "\n"

        # Data References
        if "data_references" in result.details:
            data_details = result.details["data_references"]
            data_refs = data_details.get("data_references_found", {})

            if data_refs:
                report += "### Data Reference Validation\n\n"
                for table, columns in data_refs.items():
                    if table in data_details:
                        table_info = data_details[table]
                        table_icon = "✅" if table_info.get("exists") else "❌"
                        report += f"- {table_icon} **Table: {table}**\n"

                        if "columns" in table_info:
                            for col, col_info in table_info["columns"].items():
                                col_icon = "✅" if col_info.get("exists") else "❌"
                                report += f"  - {col_icon} Column: {col}\n"
                report += "\n"

        # Code Snippets
        if "code_snippets" in result.details:
            code_details = result.details["code_snippets"]
            snippets_found = code_details.get("snippets_found", 0)

            if snippets_found > 0:
                report += f"### Code Snippet Validation ({snippets_found} found)\n\n"
                for key, snippet_info in code_details.items():
                    if key.startswith("snippet_"):
                        icon = "✅" if snippet_info.get("valid") else "❌"
                        report += f"- {icon} **{key}**: "
                        if snippet_info.get("valid"):
                            report += (
                                f"{snippet_info.get('lines', 0)} lines - Syntax valid\n"
                            )
                        else:
                            report += f"Syntax error - {snippet_info.get('error', 'Unknown error')}\n"
                report += "\n"

        # Time Estimate
        if "time_estimate" in result.details:
            time_details = result.details["time_estimate"]
            hours = time_details.get("hours", 0)
            reasonable = time_details.get("reasonable", True)

            report += "### Time Estimate Validation\n\n"
            icon = "✅" if reasonable else "⚠️"
            report += f"- {icon} Estimated hours: {hours}\n"
            report += f"- Priority: {time_details.get('priority', 'UNKNOWN')}\n"
            report += f"- Implementation steps: {time_details.get('steps', 0)}\n"
            if time_details.get("hours_per_step", 0) > 0:
                report += (
                    f"- Hours per step: {time_details.get('hours_per_step', 0):.1f}\n"
                )
            report += "\n"

        return report


def main():
    """CLI for testing recommendation validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate recommendation quality")
    parser.add_argument(
        "--recommendation", required=True, help="Path to recommendation JSON file"
    )
    parser.add_argument("--inventory", help="Path to project inventory JSON")
    parser.add_argument("--output", help="Output path for validation report")
    args = parser.parse_args()

    # Load recommendation
    with open(args.recommendation, "r") as f:
        recommendation = json.load(f)

    # Load inventory if provided
    inventory = None
    if args.inventory:
        with open(args.inventory, "r") as f:
            inventory = json.load(f)

    # Validate
    validator = RecommendationValidator(project_inventory=inventory)
    result = validator.validate_recommendation(recommendation)

    # Generate report
    report = validator.generate_validation_report(recommendation, result)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"✅ Validation report saved to: {args.output}")
    else:
        print(report)

    # Exit with error code if validation failed
    exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
