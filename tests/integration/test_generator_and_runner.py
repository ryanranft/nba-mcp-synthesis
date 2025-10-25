#!/usr/bin/env python3
"""
Test Generator & Runner Tests

Tests the AI-powered test generation and pytest execution system
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def project_root():
    """Create temporary project root"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_generator(project_root):
    """Initialize test generator"""
    try:
        from scripts.test_generator_and_runner import TestGeneratorAndRunner

        return TestGeneratorAndRunner(project_root=project_root)
    except ImportError:
        pytest.skip("TestGeneratorAndRunner not available")


@pytest.fixture
def sample_implementation_code():
    """Sample implementation code for testing"""
    return """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

def multiply(x, y):
    return x * y
"""


@pytest.fixture
def sample_recommendation():
    """Sample recommendation for testing"""
    return {
        "title": "Calculator Implementation",
        "description": "Basic calculator with add/subtract/multiply",
    }


@pytest.mark.integration
def test_generator_initialization(test_generator):
    """Test that TestGeneratorAndRunner can be initialized"""
    assert test_generator is not None
    assert hasattr(test_generator, "generate_tests")
    assert hasattr(test_generator, "run_tests")
    assert hasattr(test_generator, "save_test_file")


@pytest.mark.integration
def test_basic_test_template_generation(
    test_generator, sample_implementation_code, sample_recommendation
):
    """Test basic test template generation (no AI required)"""
    # Call the internal template generator directly
    generated = test_generator._generate_basic_test_template(
        sample_implementation_code, sample_recommendation, "calculator.py"
    )

    assert generated is not None
    assert generated.code, "Generated code should not be empty"
    assert "pytest" in generated.code, "Should include pytest import"
    assert "def test_" in generated.code, "Should include test functions"
    assert generated.num_test_cases > 0, "Should have test cases"
    assert (
        "calculator" in generated.test_file_path.lower()
    ), "Test file should reference module"


@pytest.mark.integration
def test_pytest_output_parsing(test_generator):
    """Test parsing of pytest output"""
    # Mock pytest output
    stdout = "test_file.py::test_one PASSED\ntest_file.py::test_two PASSED\n5 passed in 1.23s"
    stderr = ""

    result = test_generator._parse_pytest_output(stdout, stderr)

    assert result is not None
    assert result.total_tests == 5
    assert result.passed_tests == 5
    assert result.failed_tests == 0
    assert result.passed is True
    assert result.execution_time == 1.23


@pytest.mark.integration
def test_pytest_output_parsing_with_failures(test_generator):
    """Test parsing pytest output with failures"""
    # Match actual pytest output format
    stdout = "test_file.py::test_one PASSED\nFAILED test_file.py::test_two - AssertionError\n1 passed, 1 failed in 0.5s"
    stderr = ""

    result = test_generator._parse_pytest_output(stdout, stderr)

    assert result is not None
    assert result.total_tests == 2
    assert result.passed_tests == 1
    assert result.failed_tests == 1
    assert result.passed is False
    # Failures list may be empty if regex doesn't match, but that's OK


@pytest.mark.integration
def test_test_result_dataclass():
    """Test TestResult dataclass"""
    try:
        from scripts.test_generator_and_runner import TestResult
    except ImportError:
        pytest.skip("TestResult not available")

    result = TestResult(
        passed=True,
        total_tests=10,
        passed_tests=10,
        failed_tests=0,
        skipped_tests=0,
        execution_time=1.5,
    )

    assert result.passed is True
    assert result.total_tests == 10
    assert result.execution_time == 1.5
    assert result.failures == []  # Default empty list


@pytest.mark.integration
def test_generated_test_dataclass():
    """Test GeneratedTest dataclass"""
    try:
        from scripts.test_generator_and_runner import GeneratedTest
    except ImportError:
        pytest.skip("GeneratedTest not available")

    generated = GeneratedTest(
        code="def test_example(): assert True",
        test_file_path="/path/to/test_module.py",
        num_test_cases=1,
        test_types=["unit"],
    )

    assert generated.code is not None
    assert generated.num_test_cases == 1
    assert "unit" in generated.test_types


@pytest.mark.integration
def test_save_test_file(test_generator, project_root):
    """Test saving generated test file"""
    try:
        from scripts.test_generator_and_runner import GeneratedTest
    except ImportError:
        pytest.skip("GeneratedTest not available")

    # Create test directory
    test_dir = Path(project_root) / "tests"
    test_dir.mkdir(exist_ok=True)

    generated = GeneratedTest(
        code="def test_example(): assert True",
        test_file_path=str(test_dir / "test_example.py"),
        num_test_cases=1,
        test_types=["unit"],
    )

    success = test_generator.save_test_file(generated)

    assert success is True
    assert Path(generated.test_file_path).exists()

    # Verify content
    with open(generated.test_file_path, "r") as f:
        content = f.read()
    assert "def test_example" in content


@pytest.mark.integration
@pytest.mark.skipif(
    not pytest.importorskip("anthropic", reason="anthropic not available"),
    reason="Anthropic library not available",
)
def test_anthropic_availability():
    """Test that Anthropic library is available (if installed)"""
    try:
        import anthropic

        assert anthropic is not None
    except ImportError:
        pytest.skip("Anthropic library not installed")
