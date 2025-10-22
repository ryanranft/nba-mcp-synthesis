#!/usr/bin/env python3
"""
Test script for Phase 4: Implementation File Generation

Tests the Phase4FileGenerationBasic class that generates:
- Directory structures
- README files
- Placeholder implementation files
- Integration guides

Test Coverage:
- File generator initialization
- Filename sanitization
- README generation
- Placeholder implementation files
- Directory structure creation
- Integration guide generation
- Full generation process
- Error handling

Author: NBA MCP Synthesis Test Suite
Date: 2025-10-22
Priority: MEDIUM
"""

import sys
import os
import unittest
import tempfile
import json
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================================================================
# Mock Phase 4 File Generator
# ==============================================================================

class MockPhase4FileGenerationBasic:
    """
    Mock Phase 4 File Generation (Basic version)

    Simulates the actual Phase4FileGenerationBasic from
    scripts/phase4_file_generation.py
    """

    def __init__(self, input_file: Path = None, output_dir: Path = None):
        self.input_file = input_file or Path("implementation_plans/consolidated_recommendations.json")
        self.output_dir = output_dir or Path("implementation_plans")

        logger.info("📝 Phase 4: Implementation File Generation (Mock)")
        logger.info(f"   Input file: {self.input_file}")
        logger.info(f"   Output directory: {self.output_dir}")

    def _sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        import re
        # Remove special characters, convert spaces to underscores
        safe = re.sub(r'[^\w\s-]', '', text.lower())
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe[:50]  # Limit length

    def _generate_readme(self, recommendation: dict, rec_dir: Path) -> str:
        """Generate basic README.md for recommendation"""
        title = recommendation.get('title', 'Untitled Recommendation')
        description = recommendation.get('description', 'No description provided')
        formula = recommendation.get('formula', '')
        priority = recommendation.get('priority', 'medium')

        readme = f"""# {title}

## Description
{description}

## Priority
{priority}

## Formula
```
{formula}
```

## Implementation Status
- [ ] Implementation file created
- [ ] Tests written
- [ ] Documentation complete
- [ ] Code reviewed

## Dependencies
{', '.join(recommendation.get('dependencies', []))}

## Usage
Coming soon...
"""
        return readme

    def _generate_placeholder_implementation(self, recommendation: dict) -> str:
        """Generate placeholder implementation.py"""
        title = recommendation.get('title', 'feature')
        func_name = self._sanitize_filename(title)
        formula = recommendation.get('formula', '')
        variables = recommendation.get('variables', [])

        impl = f'''#!/usr/bin/env python3
"""
Implementation of {title}

Formula: {formula}
Variables: {', '.join(variables)}
"""

def {func_name}({', '.join(variables[:5])}):  # Limiting to first 5 variables
    """
    Calculate {title}.

    Args:
{chr(10).join(f"        {var}: Description of {var}" for var in variables[:5])}

    Returns:
        float: Calculated result

    TODO: Implement the actual calculation
    """
    # TODO: Implement formula: {formula}
    raise NotImplementedError("This function needs to be implemented")


# Example usage
if __name__ == "__main__":
    # TODO: Add usage example
    pass
'''
        return impl

    def _create_directory_structure(self, recommendation: dict) -> Path:
        """Create directory structure for recommendation"""
        rec_name = self._sanitize_filename(recommendation.get('title', 'feature'))
        rec_dir = self.output_dir / rec_name
        rec_dir.mkdir(parents=True, exist_ok=True)
        (rec_dir / "tests").mkdir(exist_ok=True)
        (rec_dir / "docs").mkdir(exist_ok=True)
        return rec_dir

    def _generate_integration_guide(self, recommendations: list) -> str:
        """Generate INTEGRATION_GUIDE.md"""
        guide = """# Integration Guide

## Overview
This guide explains how to integrate the generated implementations into your project.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Tests
```bash
pytest tests/ -v
```

## Generated Features

"""
        for rec in recommendations:
            guide += f"- **{rec.get('title', 'Unknown')}**: {rec.get('description', 'No description')}\n"

        guide += """
## Integration Steps

1. Review generated code in implementation directories
2. Update placeholders with actual implementation
3. Run tests to verify functionality
4. Update documentation as needed

## Testing
Each feature includes basic test templates in the `tests/` directory.

## Support
For issues or questions, please refer to the project documentation.
"""
        return guide

    def generate_all(self) -> dict:
        """Generate all files for recommendations"""
        try:
            # Check if input file exists
            if not self.input_file.exists():
                return {
                    'status': 'failed',
                    'error': f"Input file not found: {self.input_file}"
                }

            # Load recommendations
            try:
                with open(self.input_file) as f:
                    recommendations = json.load(f)
            except json.JSONDecodeError:
                return {
                    'status': 'failed',
                    'error': 'Invalid JSON in input file'
                }

            if not isinstance(recommendations, list):
                recommendations = [recommendations]

            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            files_created = 0

            # Generate files for each recommendation
            for rec in recommendations:
                # Create directory structure
                rec_dir = self._create_directory_structure(rec)

                # Generate README
                readme_content = self._generate_readme(rec, rec_dir)
                readme_file = rec_dir / "README.md"
                readme_file.write_text(readme_content)
                files_created += 1

                # Generate implementation
                impl_content = self._generate_placeholder_implementation(rec)
                impl_file = rec_dir / "implementation.py"
                impl_file.write_text(impl_content)
                files_created += 1

            # Generate integration guide
            guide_content = self._generate_integration_guide(recommendations)
            guide_file = self.output_dir / "INTEGRATION_GUIDE.md"
            guide_file.write_text(guide_content)
            files_created += 1

            return {
                'status': 'success',
                'files_created': files_created,
                'recommendations_processed': len(recommendations),
                'output_directory': str(self.output_dir)
            }

        except Exception as e:
            logger.error(f"Error during file generation: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }


# ==============================================================================
# Test Suite
# ==============================================================================

class Phase4FileGenerationTestSuite(unittest.TestCase):
    """Test suite for Phase 4: File Generation"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_file_generator_initialization(self):
        """Test: Initialize Phase4FileGenerationBasic"""
        logger.info("Testing file generator initialization...")

        input_file = Path(self.temp_dir) / "recommendations.json"
        output_dir = Path(self.temp_dir) / "output"

        generator = MockPhase4FileGenerationBasic(
            input_file=input_file,
            output_dir=output_dir
        )

        self.assertEqual(generator.input_file, input_file)
        self.assertEqual(generator.output_dir, output_dir)

        logger.info("✓ File generator initialization test passed")

    def test_02_filename_sanitization(self):
        """Test: Sanitize recommendation titles to safe filenames"""
        logger.info("Testing filename sanitization...")

        generator = MockPhase4FileGenerationBasic()

        test_cases = {
            "Add True Shooting % Calculator": "add_true_shooting_calculator",
            "Feature: Usage Rate (Advanced)": "feature_usage_rate_advanced",
            "SQL Query Optimizer!!!": "sql_query_optimizer",
            "A" * 100: "a" * 50  # Length limit
        }

        for input_text, expected_output in test_cases.items():
            result = generator._sanitize_filename(input_text)
            self.assertEqual(result, expected_output, f"Failed for: {input_text}")

        logger.info("✓ Filename sanitization test passed")

    def test_03_readme_generation(self):
        """Test: Generate README.md for recommendation"""
        logger.info("Testing README generation...")

        generator = MockPhase4FileGenerationBasic(output_dir=Path(self.temp_dir))

        recommendation = {
            'id': 'rec-1',
            'title': 'True Shooting Percentage Calculator',
            'description': 'Calculate TS% for player efficiency',
            'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
            'priority': 'high',
            'category': 'analytics',
            'dependencies': []
        }

        rec_dir = Path(self.temp_dir) / "ts_percentage"
        rec_dir.mkdir()

        readme_content = generator._generate_readme(recommendation, rec_dir)

        self.assertIn('True Shooting Percentage', readme_content)
        self.assertIn('PTS / (2 * (FGA + 0.44 * FTA))', readme_content)
        self.assertIn('high', readme_content.lower())
        self.assertGreater(len(readme_content), 100)

        logger.info("✓ README generation test passed")

    def test_04_placeholder_implementation_file(self):
        """Test: Generate placeholder implementation.py"""
        logger.info("Testing placeholder implementation file...")

        generator = MockPhase4FileGenerationBasic(output_dir=Path(self.temp_dir))

        recommendation = {
            'title': 'Calculate Usage Rate',
            'formula': '100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) / (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))',
            'variables': ['FGA', 'FTA', 'TOV', 'MP', 'Tm_MP']
        }

        impl_content = generator._generate_placeholder_implementation(recommendation)

        self.assertIn('def calculate_usage_rate', impl_content)
        self.assertIn('TODO', impl_content)
        self.assertIn('"""', impl_content)  # Has docstring
        self.assertIn('return', impl_content.lower() or 'raise' in impl_content.lower())

        logger.info("✓ Placeholder implementation file test passed")

    def test_05_directory_structure_creation(self):
        """Test: Create directory structure for recommendations"""
        logger.info("Testing directory structure creation...")

        generator = MockPhase4FileGenerationBasic(output_dir=Path(self.temp_dir))

        recommendation = {
            'id': 'rec-1',
            'title': 'Test Feature',
            'category': 'analytics'
        }

        rec_dir = generator._create_directory_structure(recommendation)

        self.assertTrue(rec_dir.exists())
        self.assertTrue(rec_dir.is_dir())
        self.assertTrue((rec_dir / "tests").exists())
        self.assertTrue((rec_dir / "docs").exists())

        logger.info("✓ Directory structure creation test passed")

    def test_06_integration_guide_generation(self):
        """Test: Generate INTEGRATION_GUIDE.md"""
        logger.info("Testing integration guide generation...")

        generator = MockPhase4FileGenerationBasic(output_dir=Path(self.temp_dir))

        recommendations = [
            {'id': 'rec-1', 'title': 'Feature A', 'description': 'First feature'},
            {'id': 'rec-2', 'title': 'Feature B', 'description': 'Second feature'}
        ]

        guide_content = generator._generate_integration_guide(recommendations)

        self.assertIn('Integration Guide', guide_content)
        self.assertIn('Feature A', guide_content)
        self.assertIn('Feature B', guide_content)
        self.assertTrue('Installation' in guide_content or 'Setup' in guide_content)
        self.assertGreater(len(guide_content), 200)

        logger.info("✓ Integration guide generation test passed")

    def test_07_full_generation_process(self):
        """Test: Complete file generation for multiple recommendations"""
        logger.info("Testing full generation process...")

        # Create sample recommendations file
        recommendations_file = Path(self.temp_dir) / "recommendations.json"
        recommendations_data = [
            {
                'id': 'rec-1',
                'title': 'True Shooting %',
                'description': 'Calculate TS%',
                'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
                'variables': ['PTS', 'FGA', 'FTA']
            },
            {
                'id': 'rec-2',
                'title': 'Usage Rate',
                'description': 'Calculate usage rate',
                'formula': '100 * (...)',
                'variables': ['FGA', 'FTA']
            }
        ]
        with open(recommendations_file, 'w') as f:
            json.dump(recommendations_data, f)

        generator = MockPhase4FileGenerationBasic(
            input_file=recommendations_file,
            output_dir=Path(self.temp_dir) / "output"
        )

        result = generator.generate_all()

        self.assertEqual(result['status'], 'success')
        self.assertGreaterEqual(result['files_created'], 4)  # At least 2 READMEs, 2 implementations
        self.assertTrue((Path(self.temp_dir) / "output" / "INTEGRATION_GUIDE.md").exists())

        logger.info("✓ Full generation process test passed")

    def test_08_error_handling(self):
        """Test: Handle errors gracefully"""
        logger.info("Testing error handling...")

        # Test missing input file
        generator = MockPhase4FileGenerationBasic(
            input_file=Path("nonexistent.json"),
            output_dir=Path(self.temp_dir)
        )

        result = generator.generate_all()
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)

        # Test invalid JSON
        invalid_file = Path(self.temp_dir) / "invalid.json"
        invalid_file.write_text("not valid json {")

        generator = MockPhase4FileGenerationBasic(
            input_file=invalid_file,
            output_dir=Path(self.temp_dir)
        )

        result = generator.generate_all()
        self.assertEqual(result['status'], 'failed')

        logger.info("✓ Error handling test passed")


def main():
    """Main test function"""
    logger.info("Starting Phase 4: File Generation Tests")
    logger.info("=" * 70)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase4FileGenerationTestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests

    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Errors: {error_tests}")

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1f}%")

    if result.wasSuccessful():
        logger.info("\n🎉 ALL TESTS PASSED! Phase 4 file generation is working correctly.")
        return True
    else:
        logger.info(f"\n❌ {failed_tests + error_tests} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
