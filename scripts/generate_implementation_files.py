#!/usr/bin/env python3
"""
MCP-Based Implementation File Generator

Generates implementation files (Python, SQL, CloudFormation, tests) for book recommendations
using the NBA MCP server to query database context and generate realistic implementations.

Uses:
- MCP tools to query NBA database schema
- Templates for consistent file generation
- Phase-aware file placement
- Dependency analysis
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPImplementationGenerator:
    """
    Generates implementation files using MCP server for context.
    """

    def __init__(self, mcp_server_url: str, output_base: str, templates_dir: str):
        """
        Initialize generator.

        Args:
            mcp_server_url: URL of MCP server (e.g., http://localhost:8000)
            output_base: Base directory for generated files
            templates_dir: Directory containing templates
        """
        self.mcp_server_url = mcp_server_url
        self.output_base = Path(output_base)
        self.templates_dir = Path(templates_dir)
        self.mcp_available = False

        # Load templates
        self.templates = self._load_templates()

        logger.info(f"Initialized generator with output base: {output_base}")

    def _load_templates(self) -> Dict[str, str]:
        """Load all templates from templates directory."""
        templates = {}
        template_files = {
            "python": "implementation_script.py.template",
            "test": "test_script.py.template",
            "sql": "sql_migration.sql.template",
            "cloudformation": "cloudformation.yaml.template",
        }

        for key, filename in template_files.items():
            template_path = self.templates_dir / filename
            if template_path.exists():
                with open(template_path, "r") as f:
                    templates[key] = f.read()
                logger.info(f"Loaded template: {key}")
            else:
                logger.warning(f"Template not found: {template_path}")

        return templates

    async def check_mcp_server(self) -> bool:
        """Check if MCP server is available."""
        try:
            # Try to import MCP client
            # For now, we'll generate files without MCP context
            # In production, this would query the MCP server
            logger.info(f"Checking MCP server at {self.mcp_server_url}...")
            self.mcp_available = False  # Set to True when MCP is integrated
            return self.mcp_available
        except Exception as e:
            logger.warning(f"MCP server not available: {e}")
            return False

    async def query_database_context(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query MCP server for database context relevant to recommendation.

        Args:
            rec: Recommendation dictionary

        Returns:
            dict: Database context (tables, schemas, sample data)
        """
        if not self.mcp_available:
            return self._generate_mock_context(rec)

        # TODO: Implement actual MCP queries
        # - list_tables
        # - get_table_schema for relevant tables
        # - query_database for sample data
        # - list_s3_files for existing resources

        return {}

    def _generate_mock_context(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock database context for testing."""
        return {
            "tables": ["games", "players", "teams", "player_stats"],
            "relevant_tables": self._identify_relevant_tables(rec),
            "sample_data": {},
            "s3_resources": [],
        }

    def _identify_relevant_tables(self, rec: Dict[str, Any]) -> List[str]:
        """Identify relevant database tables based on recommendation."""
        rec_text = f"{rec['title']} {rec.get('reasoning', '')}".lower()

        table_keywords = {
            "games": ["game", "match", "simulation"],
            "players": ["player", "athlete"],
            "teams": ["team", "franchise"],
            "player_stats": ["stats", "statistics", "metrics", "performance"],
            "betting_odds": ["betting", "odds", "gambling"],
            "features": ["feature", "engineering"],
            "models": ["model", "ml", "machine learning", "prediction"],
        }

        relevant = []
        for table, keywords in table_keywords.items():
            if any(kw in rec_text for kw in keywords):
                relevant.append(table)

        return relevant if relevant else ["games", "players"]

    def _to_class_name(self, title: str) -> str:
        """Convert recommendation title to Python class name."""
        # Remove special characters and convert to PascalCase
        words = re.sub(r"[^a-zA-Z0-9\s]", "", title).split()
        return "".join(word.capitalize() for word in words)

    def _to_snake_case(self, title: str) -> str:
        """Convert recommendation title to snake_case."""
        # Remove special characters and convert to snake_case
        words = re.sub(r"[^a-zA-Z0-9\s]", "", title).lower().split()
        return "_".join(words)

    def _determine_file_types(self, rec: Dict[str, Any]) -> List[str]:
        """Determine which file types to generate based on recommendation."""
        rec_text = f"{rec['title']} {rec.get('reasoning', '')}".lower()

        file_types = ["python", "test"]  # Always generate Python and tests

        # Add SQL if database-related
        if any(
            kw in rec_text
            for kw in ["database", "table", "schema", "sql", "migration", "data"]
        ):
            file_types.append("sql")

        # Add CloudFormation if infrastructure-related
        if any(
            kw in rec_text
            for kw in [
                "infrastructure",
                "aws",
                "deployment",
                "lambda",
                "s3",
                "rds",
                "cloudformation",
            ]
        ):
            file_types.append("cloudformation")

        return file_types

    def _get_phase_subdirectory(self, rec: Dict[str, Any], phase: int) -> Optional[str]:
        """
        Determine the subdirectory within a phase for this recommendation.

        Args:
            rec: Recommendation dictionary
            phase: Phase number

        Returns:
            str: Subdirectory path (e.g., '5.1_feature_engineering') or None
        """
        rec_text = f"{rec['title']} {rec.get('reasoning', '')}".lower()

        # Phase-specific subdirectory mappings
        phase_subdirs = {
            1: {
                "1.1_data_validation": ["validation", "statistical", "hypothesis"],
                "1.2_quality_checks": ["quality", "econometric", "checks"],
            },
            2: {
                "2.1_feature_engineering": ["feature", "engineering"],
                "2.2_statistical_pipelines": ["statistical", "pipeline"],
                "2.3_data_processing": ["processing", "etl", "transformation"],
            },
            3: {"3.1_database_monitoring": ["database", "monitoring", "dashboard"]},
            4: {"4.1_simulation_data": ["simulation", "panel", "temporal"]},
            5: {
                "5.1_feature_engineering": ["feature", "engineering"],
                "5.2_model_management": ["model", "versioning", "registry", "mlflow"],
                "5.3_model_operations": [
                    "deployment",
                    "serving",
                    "inference",
                    "retraining",
                ],
                "5.4_model_analysis": [
                    "analysis",
                    "explainability",
                    "shap",
                    "interpretability",
                ],
                "5.5_experimentation": ["experiment", "a/b test", "testing"],
            },
            6: {
                "6.1_monitoring_dashboards": [
                    "monitoring",
                    "dashboard",
                    "observability",
                ],
                "6.2_experiment_tracking": ["experiment", "tracking", "mlflow"],
            },
            8: {
                "8.1_statistical_frameworks": ["statistical", "framework", "bayesian"],
                "8.2_data_analysis": ["analysis", "time series", "econometric"],
                "8.3_model_validation": ["validation", "testing"],
                "8.4_reporting_dashboards": ["reporting", "dashboard", "visualization"],
            },
            9: {
                "9.1_deployment_strategies": ["deployment", "shadow", "strategy"],
                "9.2_system_monitoring": ["system", "monitoring", "infrastructure"],
            },
        }

        if phase not in phase_subdirs:
            return None

        # Find best matching subdirectory
        best_match = None
        best_score = 0

        for subdir, keywords in phase_subdirs[phase].items():
            score = sum(1 for kw in keywords if kw in rec_text)
            if score > best_score:
                best_score = score
                best_match = subdir

        return best_match

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables."""
        result = template
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))

        # Remove unreplaced placeholders (optional sections)
        result = re.sub(r"\{\{[^}]+\}\}", "# TODO: Implement this section", result)

        return result

    async def generate_files_for_recommendation(
        self, rec: Dict[str, Any], phase: int
    ) -> Dict[str, List[str]]:
        """
        Generate all implementation files for a recommendation.

        Args:
            rec: Recommendation dictionary
            phase: Phase number

        Returns:
            dict: {'generated_files': [paths], 'errors': [errors]}
        """
        logger.info(f"Generating files for: {rec['title']} (Phase {phase})")

        generated_files = []
        errors = []

        # Get database context from MCP
        db_context = await self.query_database_context(rec)

        # Determine file types to generate
        file_types = self._determine_file_types(rec)
        logger.info(f"  File types: {file_types}")

        # Determine subdirectory
        subdir = self._get_phase_subdirectory(rec, phase)
        if subdir:
            output_dir = self.output_base / f"phase_{phase}" / subdir
            logger.info(f"  Output directory: {output_dir}")
        else:
            output_dir = self.output_base / f"phase_{phase}"
            logger.info(f"  Output directory (no subdir): {output_dir}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare template context
        class_name = self._to_class_name(rec["title"])
        snake_name = self._to_snake_case(rec["title"])

        context = {
            "rec_id": rec["id"],
            "rec_title": rec["title"],
            "class_name": class_name,
            "priority": rec.get("category", "unknown").upper(),
            "source_book": ", ".join(rec.get("source_books", ["Unknown"])),
            "description": rec.get("reasoning", "No description available"),
            "expected_impact": rec.get("impact", "MEDIUM"),
            "time_estimate": rec.get("time_estimate", "1 week"),
            "generated_date": datetime.now().isoformat(),
            "table_name": db_context.get("relevant_tables", ["data"])[0],
            "setup_logic": "pass  # TODO: Implement setup",
            "prerequisite_validation": "pass  # TODO: Validate prerequisites",
            "main_logic": "pass  # TODO: Implement main logic",
            "results_dict": "",
            "cleanup_logic": "pass  # TODO: Implement cleanup",
            "test_config": "",
            "specific_tests": "",
            "cleanup_verification": "pass",
            "integration_config": "",
            "e2e_verification": "pass",
            "integration_tests": "",
            "migration_up_logic": "-- TODO: Add migration logic",
            "migration_down_logic": "-- TODO: Add rollback logic",
            "migration_version": datetime.now().strftime("%Y%m%d%H%M%S"),
            "prerequisites": "-- None",
            "post_migration_steps": "-- None",
            "migration_file": f"{snake_name}_migration",
            "parameters": "# TODO: Add parameters",
            "resources": "# TODO: Add resources",
            "outputs": "# TODO: Add outputs",
            "bucket_suffix": snake_name,
            "function_name": snake_name,
            "policy_name": f"{class_name}Policy",
        }

        # Generate each file type
        for file_type in file_types:
            try:
                if file_type == "python":
                    filename = f"implement_{rec['id']}.py"
                    content = self._render_template(self.templates["python"], context)
                elif file_type == "test":
                    filename = f"test_{rec['id']}.py"
                    content = self._render_template(self.templates["test"], context)
                elif file_type == "sql":
                    filename = f"{rec['id']}_migration.sql"
                    content = self._render_template(self.templates["sql"], context)
                elif file_type == "cloudformation":
                    filename = f"{rec['id']}_infrastructure.yaml"
                    content = self._render_template(
                        self.templates["cloudformation"], context
                    )
                else:
                    continue

                # Write file
                file_path = output_dir / filename
                with open(file_path, "w") as f:
                    f.write(content)

                # Make Python files executable
                if file_type in ["python", "test"]:
                    os.chmod(file_path, 0o755)

                generated_files.append(str(file_path))
                logger.info(f"  ✅ Generated: {filename}")

            except Exception as e:
                error_msg = f"Failed to generate {file_type} for {rec['id']}: {e}"
                logger.error(f"  ❌ {error_msg}")
                errors.append(error_msg)

        # Generate IMPLEMENTATION_GUIDE.md
        try:
            guide_content = self._generate_implementation_guide(
                rec, generated_files, phase, subdir
            )
            guide_path = output_dir / f"{rec['id']}_IMPLEMENTATION_GUIDE.md"
            with open(guide_path, "w") as f:
                f.write(guide_content)
            generated_files.append(str(guide_path))
            logger.info(f"  ✅ Generated: IMPLEMENTATION_GUIDE.md")
        except Exception as e:
            errors.append(f"Failed to generate implementation guide: {e}")

        return {
            "generated_files": generated_files,
            "errors": errors,
            "recommendation_id": rec["id"],
            "phase": phase,
            "subdirectory": subdir,
        }

    def _generate_implementation_guide(
        self,
        rec: Dict[str, Any],
        generated_files: List[str],
        phase: int,
        subdir: Optional[str],
    ) -> str:
        """Generate implementation guide markdown."""
        guide = f"""# Implementation Guide: {rec['title']}

**Recommendation ID:** {rec['id']}
**Priority:** {rec.get('category', 'unknown').upper()}
**Phase:** {phase}
**Subdirectory:** {subdir or 'N/A'}
**Generated:** {datetime.now().isoformat()}

---

## Overview

{rec.get('reasoning', 'No description available')}

**Expected Impact:** {rec.get('impact', 'MEDIUM')}
**Time Estimate:** {rec.get('time_estimate', '1 week')}
**Source Book:** {', '.join(rec.get('source_books', ['Unknown']))}

---

## Generated Files

"""

        for file_path in generated_files:
            filename = Path(file_path).name
            guide += f"- `{filename}`\n"

        guide += f"""
---

## Implementation Steps

### 1. Review Generated Files

Review all generated files to understand the implementation structure:
- Python implementation script
- Test suite
- SQL migrations (if applicable)
- CloudFormation infrastructure (if applicable)

### 2. Customize Implementation

Fill in the TODO sections in each file:
- `implement_{rec['id']}.py`: Main implementation logic
- `test_{rec['id']}.py`: Test cases
- SQL/CloudFormation: Specific configurations

### 3. Set Up Prerequisites

Ensure all prerequisites are met:
- Database access configured
- AWS credentials set up
- Required Python packages installed
- MCP server running (if needed)

### 4. Run Tests

```bash
python test_{rec['id']}.py
```

### 5. Execute Implementation

```bash
python implement_{rec['id']}.py
```

### 6. Deploy Infrastructure (if applicable)

```bash
aws cloudformation create-stack \\
  --stack-name nba-simulator-{rec['id']} \\
  --template-body file://{rec['id']}_infrastructure.yaml \\
  --parameters ParameterKey=Environment,ParameterValue=dev
```

### 7. Run Migrations (if applicable)

```bash
psql -d nba_simulator -f {rec['id']}_migration.sql
```

---

## Verification

After implementation:
1. Run all tests and ensure they pass
2. Verify database changes (if applicable)
3. Check CloudWatch logs for any errors
4. Monitor system metrics
5. Update recommendation status in master_recommendations.json

---

## Rollback

If issues occur:
1. Run rollback migration (if applicable)
2. Delete CloudFormation stack
3. Restore from backup (if needed)
4. Document issues for future reference

---

## See Also

- [Phase {phase} Overview](/Users/ryanranft/nba-simulator-aws/docs/phases/phase_{phase}/)
- [Master Recommendations](/Users/ryanranft/nba-mcp-synthesis/analysis_results/master_recommendations.json)
- [Book Analysis Results](/Users/ryanranft/nba-mcp-synthesis/analysis_results/)
"""

        return guide

    async def generate_for_all_recommendations(
        self, recommendations_file: str
    ) -> Dict[str, Any]:
        """
        Generate implementation files for all recommendations.

        Args:
            recommendations_file: Path to master_recommendations.json

        Returns:
            dict: Summary of generation results
        """
        logger.info("=" * 80)
        logger.info("Starting implementation file generation for all recommendations")
        logger.info("=" * 80)

        # Load recommendations
        with open(recommendations_file, "r") as f:
            data = json.load(f)

        recommendations = data.get("recommendations", [])
        logger.info(f"Loaded {len(recommendations)} recommendations")

        # Check MCP server
        await self.check_mcp_server()

        # Import phase mapper
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from phase_mapper import PhaseMapper

        phase_mapper = PhaseMapper()

        # Generate files for each recommendation
        results = []
        total_files = 0
        total_errors = 0

        for rec in recommendations:
            # Map to phases
            phases = phase_mapper.map_recommendation_to_phase(rec)

            for phase in phases:
                result = await self.generate_files_for_recommendation(rec, phase)
                results.append(result)
                total_files += len(result["generated_files"])
                total_errors += len(result["errors"])

        summary = {
            "total_recommendations": len(recommendations),
            "total_files_generated": total_files,
            "total_errors": total_errors,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

        # Save summary
        summary_file = (
            self.output_base.parent / "implementation_generation_summary.json"
        )
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("=" * 80)
        logger.info(f"Generation complete!")
        logger.info(f"  Total files generated: {total_files}")
        logger.info(f"  Total errors: {total_errors}")
        logger.info(f"  Summary saved to: {summary_file}")
        logger.info("=" * 80)

        return summary


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate implementation files from book recommendations"
    )
    parser.add_argument(
        "--recommendations",
        default="analysis_results/master_recommendations.json",
        help="Path to master recommendations file",
    )
    parser.add_argument(
        "--output-base",
        default="/Users/ryanranft/nba-simulator-aws/docs/phases",
        help="Base directory for generated files",
    )
    parser.add_argument(
        "--templates-dir", default="templates", help="Directory containing templates"
    )
    parser.add_argument(
        "--mcp-server", default="http://localhost:8000", help="MCP server URL"
    )

    args = parser.parse_args()

    generator = MCPImplementationGenerator(
        mcp_server_url=args.mcp_server,
        output_base=args.output_base,
        templates_dir=args.templates_dir,
    )

    summary = await generator.generate_for_all_recommendations(args.recommendations)

    if summary["total_errors"] > 0:
        logger.warning(f"⚠️  Completed with {summary['total_errors']} errors")
        sys.exit(1)
    else:
        logger.info("✅ All files generated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
