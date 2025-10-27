#!/usr/bin/env python3
"""
Test Generator & Runner

Generates comprehensive pytest test suites using AI and executes them.
Blocks deployment if tests fail.

Features:
- AI-powered test generation
- Unit, integration, and edge case tests
- Pytest execution
- Result parsing and reporting
- Coverage analysis

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import os
import sys
import subprocess
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import hierarchical secrets helper
from mcp_server.env_helper import get_api_key

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import Anthropic
try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("⚠️  Anthropic library not available")


@dataclass
class TestResult:
    """Result of test execution"""

    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    failures: List[str] = field(default_factory=list)
    output: str = ""


@dataclass
class GeneratedTest:
    """Generated test code"""

    code: str
    test_file_path: str
    num_test_cases: int
    test_types: List[str]  # unit, integration, edge_case


class TestGeneratorAndRunner:
    """
    Generates and runs pytest tests for implementations.

    Features:
    - AI-powered test generation
    - Comprehensive test suites
    - Pytest execution
    - Result reporting
    """

    def __init__(
        self,
        project_root: str = "../nba-simulator-aws",
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """
        Initialize Test Generator & Runner.

        Args:
            project_root: Path to project
            model: Claude model for test generation
        """
        self.project_root = Path(project_root).resolve()
        self.model = model

        # Initialize Claude client with hierarchical secrets
        api_key = get_api_key("ANTHROPIC")
        if api_key and ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=api_key)
            logger.info(f"🧪 Test Generator & Runner initialized")
            logger.info(f"   Model: {self.model}")
        else:
            self.client = None
            logger.warning("⚠️  Claude client not available for test generation")
            if not api_key:
                logger.warning("   Reason: ANTHROPIC_API_KEY not found in secrets")
            if not ANTHROPIC_AVAILABLE:
                logger.warning("   Reason: anthropic package not installed")

    def generate_tests(
        self, implementation_code: str, recommendation: Dict[str, Any], module_path: str
    ) -> Optional[GeneratedTest]:
        """
        Generate comprehensive test suite using AI.

        Args:
            implementation_code: The code to test
            recommendation: Recommendation dictionary
            module_path: Path to module being tested

        Returns:
            GeneratedTest with test code
        """
        if not self.client:
            logger.warning("⚠️  Cannot generate tests - Claude client not available")
            return self._generate_basic_test_template(
                implementation_code, recommendation, module_path
            )

        title = recommendation.get("title", "Untitled")
        logger.info(f"🧪 Generating tests for: {title}")

        try:
            # Build test generation prompt
            prompt = self._build_test_generation_prompt(
                implementation_code, recommendation, module_path
            )

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,  # Increased to handle larger test files with many test cases
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            test_code = response.content[0].text.strip()

            # Extract code from markdown if present (handle both complete and incomplete fences)
            # Try complete fence first (```python ... ```)
            code_match = re.search(r"```python\n(.*?)```", test_code, re.DOTALL)
            if code_match:
                test_code = code_match.group(1).strip()
            else:
                # Try incomplete fence (```python ... with no closing)
                code_match = re.search(r"```python\n(.*)", test_code, re.DOTALL)
                if code_match:
                    test_code = code_match.group(1).strip()
                # Also check for just ```\n without python keyword
                elif test_code.startswith("```"):
                    # Strip opening fence and any closing fence
                    test_code = re.sub(r"^```[a-z]*\n", "", test_code)
                    test_code = re.sub(r"\n```$", "", test_code).strip()

            # Count test cases
            num_tests = test_code.count("def test_")

            # Determine test file path
            module_name = Path(module_path).stem
            test_file_path = str(self.project_root / "tests" / f"test_{module_name}.py")

            logger.info(f"   ✅ Generated {num_tests} test cases")

            return GeneratedTest(
                code=test_code,
                test_file_path=test_file_path,
                num_test_cases=num_tests,
                test_types=["unit", "integration", "edge_case"],
            )

        except Exception as e:
            logger.error(f"❌ Failed to generate tests: {e}")
            return self._generate_basic_test_template(
                implementation_code, recommendation, module_path
            )

    def _build_test_generation_prompt(
        self, implementation_code: str, recommendation: Dict[str, Any], module_path: str
    ) -> str:
        """Build prompt for test generation"""
        title = recommendation.get("title", "Untitled")
        description = recommendation.get("description", "")

        # Extract module name and classes/functions
        module_name = Path(module_path).stem
        classes = re.findall(r"class (\w+)", implementation_code)
        functions = re.findall(r"def (\w+)", implementation_code)

        # Determine correct import path based on module location
        module_path_obj = Path(module_path)
        if self.project_root in module_path_obj.parents:
            # Get relative path from project root
            rel_path = module_path_obj.relative_to(self.project_root)
            # Convert to import path (remove .py, replace / with .)
            import_path = str(rel_path.with_suffix("")).replace("/", ".")
        else:
            # Fallback to simple module name
            import_path = module_name

        # Get the directory containing the module for path manipulation
        module_dir = (
            module_path_obj.parent.relative_to(self.project_root)
            if self.project_root in module_path_obj.parents
            else Path("scripts")
        )
        module_dir_str = str(module_dir)

        prompt = f"""Generate a comprehensive pytest test suite for the following Python module.

# Module: {module_name}
# Feature: {title}
# Description: {description}

## Implementation Code

```python
{implementation_code[:4000]}  # Truncated if too long
```

## Requirements

Generate a complete pytest test file with:

1. **Fixtures**: Create pytest fixtures for:
   - Test instances of classes
   - Mock data
   - Database connections (if needed)
   - File system mocks (if needed)

2. **Unit Tests**: Test individual functions/methods:
   - Normal operation with valid inputs
   - Return values and types
   - State changes
   - Method calls

3. **Integration Tests**: Test component interactions:
   - Multiple functions working together
   - Database operations (if applicable)
   - File I/O (if applicable)

4. **Edge Case Tests**: Test boundary conditions:
   - Empty inputs
   - None values
   - Invalid types
   - Large values
   - Negative values

5. **Error Handling Tests**: Test exception handling:
   - Expected exceptions
   - Error messages
   - Graceful degradation

## Test Structure

IMPORTANT: The module is located at {module_dir_str}/{module_name}.py
You MUST use this exact import statement:

```python
#!/usr/bin/env python3
\"\"\"
Tests for {module_name}
\"\"\"

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add module directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / '{module_dir_str}'))

# Import from the module
from {module_name} import [classes/functions to test]


@pytest.fixture
def fixture_name():
    \"\"\"Fixture description\"\"\"
    # Setup
    yield value
    # Teardown


def test_[feature]_[scenario]():
    \"\"\"Test description\"\"\"
    # Arrange
    # Act
    # Assert
    assert expected == actual
```

## Critical Import Requirements

- ALWAYS include the sys.path.insert line EXACTLY as shown above
- The path manipulation is: sys.path.insert(0, str(Path(__file__).parent.parent / '{module_dir_str}'))
- Then import using: from {module_name} import ...
- Do NOT use: from {import_path} import ... (this will fail)
- Do NOT skip the path manipulation code

## Important

- Generate ONLY the test code, no explanations
- Use descriptive test names: test_[function]_[scenario]_[expected_result]
- Include docstrings for all tests
- Use pytest.mark.parametrize for similar test cases
- Mock external dependencies (databases, APIs, file systems)
- Test both success and failure paths
- Generate at least 10-15 test cases
- Use proper assertions (assert, pytest.raises, etc.)

Generate the complete test suite now:"""

        return prompt

    def _generate_basic_test_template(
        self, implementation_code: str, recommendation: Dict[str, Any], module_path: str
    ) -> GeneratedTest:
        """Generate basic test template as fallback"""
        module_name = Path(module_path).stem
        title = recommendation.get("title", "Untitled")

        # Extract classes and functions
        classes = re.findall(r"class (\w+)", implementation_code)
        functions = re.findall(r"def (\w+)", implementation_code)

        # Get module directory for path manipulation
        module_path_obj = Path(module_path)
        if self.project_root in module_path_obj.parents:
            module_dir = module_path_obj.parent.relative_to(self.project_root)
            module_dir_str = str(module_dir)
        else:
            module_dir_str = "scripts"

        test_code = f'''#!/usr/bin/env python3
"""
Tests for {module_name}

Feature: {title}
"""

import pytest
import sys
from pathlib import Path

# Add module directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / '{module_dir_str}'))

from {module_name} import *


def test_{module_name}_imports():
    """Test that module imports successfully"""
    # This test verifies the module can be imported
    assert True


'''

        # Add basic tests for each class
        for cls in classes[:3]:  # Limit to first 3
            test_code += f'''
def test_{cls.lower()}_initialization():
    """Test {cls} can be initialized"""
    instance = {cls}()
    assert instance is not None


'''

        # Add basic tests for each function
        for func in functions[:5]:  # Limit to first 5
            if not func.startswith("_"):  # Skip private functions
                test_code += f'''
def test_{func}_exists():
    """Test {func} function exists"""
    assert callable({func})


'''

        test_file_path = str(self.project_root / "tests" / f"test_{module_name}.py")

        return GeneratedTest(
            code=test_code,
            test_file_path=test_file_path,
            num_test_cases=len(classes) + len(functions) + 1,
            test_types=["basic"],
        )

    def run_tests(
        self,
        test_file: str,
        pytest_args: Optional[List[str]] = None,
        timeout: int = 300,
    ) -> TestResult:
        """
        Run pytest tests.

        Args:
            test_file: Path to test file
            pytest_args: Additional pytest arguments
            timeout: Timeout in seconds

        Returns:
            TestResult with execution results
        """
        logger.info(f"🧪 Running tests: {Path(test_file).name}")

        # Build pytest command
        cmd = ["pytest", test_file, "-v", "--tb=short"]

        if pytest_args:
            cmd.extend(pytest_args)

        try:
            # Run pytest
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Parse output
            test_result = self._parse_pytest_output(result.stdout, result.stderr)

            if test_result.passed:
                logger.info(
                    f"   ✅ All tests passed ({test_result.passed_tests}/{test_result.total_tests})"
                )
            else:
                logger.error(
                    f"   ❌ Tests failed ({test_result.failed_tests}/{test_result.total_tests})"
                )
                for failure in test_result.failures[:3]:  # Show first 3
                    logger.error(f"      - {failure}")

            return test_result

        except subprocess.TimeoutExpired:
            logger.error(f"   ❌ Tests timed out after {timeout}s")
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=timeout,
                failures=["Test execution timed out"],
                output="",
            )

        except Exception as e:
            logger.error(f"   ❌ Failed to run tests: {e}")
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=0.0,
                failures=[str(e)],
                output="",
            )

    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestResult:
        """Parse pytest output to extract results"""
        combined_output = stdout + stderr

        # Extract test counts
        # Look for pattern like: "5 passed, 2 failed in 1.23s"
        match = re.search(
            r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?.* in ([\d.]+)s",
            combined_output,
        )

        if match:
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            skipped = int(match.group(3)) if match.group(3) else 0
            exec_time = float(match.group(4))

            total = passed + failed + skipped

            # Extract failure messages
            failures = re.findall(r"FAILED (.*?) -", combined_output)

            return TestResult(
                passed=(failed == 0),
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                execution_time=exec_time,
                failures=failures,
                output=combined_output,
            )
        else:
            # Could not parse - assume failure
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=0.0,
                failures=["Could not parse test results"],
                output=combined_output,
            )

    def save_test_file(self, generated_test: GeneratedTest) -> bool:
        """
        Save generated test to file.

        Args:
            generated_test: GeneratedTest object

        Returns:
            True if successful
        """
        try:
            test_path = Path(generated_test.test_file_path)
            test_path.parent.mkdir(parents=True, exist_ok=True)

            with open(test_path, "w") as f:
                f.write(generated_test.code)

            logger.info(f"💾 Saved test file: {test_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save test file: {e}")
            return False

    def generate_and_run_tests(
        self,
        implementation_code: str,
        recommendation: Dict[str, Any],
        module_path: str,
        block_on_failure: bool = True,
    ) -> Tuple[bool, Optional[TestResult]]:
        """
        Generate tests and run them (convenience method).

        Args:
            implementation_code: Code to test
            recommendation: Recommendation dictionary
            module_path: Module path
            block_on_failure: Block deployment if tests fail

        Returns:
            Tuple of (should_proceed, test_result)
        """
        # Generate tests
        generated_test = self.generate_tests(
            implementation_code, recommendation, module_path
        )

        if not generated_test:
            logger.error("❌ Failed to generate tests")
            return (not block_on_failure, None)

        # Save test file
        if not self.save_test_file(generated_test):
            logger.error("❌ Failed to save test file")
            return (not block_on_failure, None)

        # Run tests
        test_result = self.run_tests(generated_test.test_file_path)

        # Determine if should proceed
        should_proceed = test_result.passed or not block_on_failure

        return (should_proceed, test_result)


def main():
    """CLI for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Generator & Runner")
    parser.add_argument("--code-file", required=True, help="Implementation code file")
    parser.add_argument("--recommendation", required=True, help="Recommendation JSON")
    parser.add_argument(
        "--project-root", default="../nba-simulator-aws", help="Project root"
    )
    args = parser.parse_args()

    # Load code
    with open(args.code_file, "r") as f:
        code = f.read()

    # Load recommendation
    with open(args.recommendation, "r") as f:
        rec_data = json.load(f)
        rec = rec_data[0] if isinstance(rec_data, list) else rec_data

    # Initialize
    runner = TestGeneratorAndRunner(project_root=args.project_root)

    # Generate and run
    should_proceed, result = runner.generate_and_run_tests(
        implementation_code=code, recommendation=rec, module_path=args.code_file
    )

    print(f"\n{'='*60}")
    print(f"Test Results")
    print(f"{'='*60}\n")

    if result:
        print(f"Passed: {result.passed}")
        print(f"Total: {result.total_tests}")
        print(f"Passed: {result.passed_tests}")
        print(f"Failed: {result.failed_tests}")
        print(f"Skipped: {result.skipped_tests}")
        print(f"Time: {result.execution_time:.2f}s")

        if result.failures:
            print(f"\nFailures:")
            for failure in result.failures:
                print(f"  - {failure}")

    print(f"\nShould proceed with deployment: {should_proceed}")


if __name__ == "__main__":
    main()
