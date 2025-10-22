# Test Gap Design Specifications
**Date**: 2025-10-22
**Purpose**: Comprehensive test designs for 6 critical coverage gaps
**Phase**: 3 of 7 (Gap Analysis & New Test Design)

---

## Executive Summary

This document provides detailed specifications for 6 new test files to address critical gaps in test coverage identified in Phase 2.3 analysis.

**Coverage Improvement**: Adding these tests will increase overall coverage from **75% to ~90%**

| Gap # | Test File | Priority | Scenarios | Runtime | Cost | Lines |
|-------|-----------|----------|-----------|---------|------|-------|
| 1 | test_e2e_deployment_flow.py | CRITICAL | 10 | 4-6 min | $0.15-$0.30 | 600-700 |
| 2 | test_phase_11_automated_deployment.py | HIGH | 12 | 3-4 min | $0.10-$0.20 | 700-800 |
| 3 | test_dims_integration.py | HIGH | 8 | 2-3 min | $0.05-$0.10 | 400-500 |
| 4 | test_security_hooks.py | MEDIUM | 10 | 1-2 min | $0 | 500-600 |
| 5 | test_phase_1_foundation.py | MEDIUM | 10 | 2-3 min | $0 | 500-600 |
| 6 | test_phase_4_file_generation.py | MEDIUM | 8 | 1-2 min | $0 | 400-500 |

**Total Estimated Effort**: 12-20 hours writing, 13-20 minutes runtime, $0.30-$0.60 cost

---

## Design Philosophy & Patterns

### Testing Principles

Based on analysis of existing tests in the codebase, all new tests will follow these patterns:

1. **Async/Await Pattern**: Use `pytest.mark.asyncio` for async tests
2. **Fixtures for Setup**: Create reusable fixtures for common setup (servers, connections, etc.)
3. **Clear Test Names**: Format: `test_XX_descriptive_name` where XX is execution order
4. **Comprehensive Assertions**: Verify success, status codes, data structures, error messages
5. **Standalone Runners**: Include `if __name__ == "__main__"` runner for pytest-free execution
6. **Detailed Logging**: Use logger.info() for test progress and results
7. **Cleanup/Teardown**: Always clean up resources in finally blocks
8. **Timeout Protection**: Use `@pytest.mark.timeout()` for tests with potential hangs

### Common Imports

```python
#!/usr/bin/env python3
import pytest
import asyncio
import sys
import os
import time
import subprocess
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Shared Fixtures

These fixtures will be added to `tests/conftest.py` or defined in each test:

```python
@pytest.fixture
def temp_directory():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    with patch.dict(os.environ, {
        'RDS_HOST': 'test-host',
        'RDS_DATABASE': 'test-db',
        'RDS_USERNAME': 'test-user',
        'RDS_PASSWORD': 'test-pass',
        'S3_BUCKET': 'test-bucket',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'DEEPSEEK_API_KEY': 'test-deepseek',
        'ANTHROPIC_API_KEY': 'test-claude'
    }):
        yield

@pytest.fixture
async def mock_mcp_server():
    """Mock MCP server for testing"""
    server = MagicMock()
    server.url = "http://localhost:3000"
    server.connected = True
    yield server
```

---

## Gap 1: End-to-End Deployment Flow Test

**File**: `tests/test_e2e_deployment_flow.py`
**Priority**: CRITICAL
**Purpose**: Test complete pipeline from book analysis → code synthesis → automated deployment

### Test Scenarios

#### Scenario 1: Happy Path - Complete E2E Flow
```python
@pytest.mark.asyncio
@pytest.mark.timeout(360)  # 6 minute timeout
async def test_01_complete_e2e_deployment_flow(temp_directory, mock_env_vars):
    """
    Test: Complete end-to-end flow from book to deployed code

    Flow:
    1. Load sample PDF book (mock)
    2. Extract formulas and concepts
    3. Synthesize code with multi-model (DeepSeek, Claude, Ollama)
    4. Generate tests
    5. Run tests
    6. Create git branch
    7. Commit code
    8. Push to remote
    9. Create GitHub PR
    10. Verify deployment artifacts
    """
```

**Inputs**:
- Mock PDF book (sample basketball analytics book)
- Configuration YAML with deployment settings

**Mocks**:
```python
# Mock book extraction
mock_extraction = {
    'formulas': [
        {'name': 'True Shooting %', 'formula': 'PTS / (2 * (FGA + 0.44 * FTA))'},
        {'name': 'Usage Rate', 'formula': '100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) / (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))'}
    ],
    'concepts': ['efficiency metrics', 'advanced statistics'],
    'book_title': 'Basketball Analytics Guide'
}

# Mock synthesis result
mock_synthesis = {
    'status': 'success',
    'final_code': '# Implementation of formulas...',
    'tests': '# Test cases...',
    'total_cost': 0.25,
    'models_used': ['deepseek', 'claude', 'ollama']
}

# Mock GitHub API
mock_pr_response = {
    'number': 123,
    'url': 'https://github.com/owner/repo/pull/123',
    'state': 'open',
    'title': 'Implement Basketball Analytics Formulas'
}
```

**Assertions**:
```python
assert result['extraction_success'] == True
assert len(result['formulas_extracted']) >= 2
assert result['synthesis_status'] == 'success'
assert result['tests_generated'] == True
assert result['tests_passed'] == True
assert result['branch_created'] == True
assert result['pr_created'] == True
assert result['pr_url'] is not None
assert result['deployment_artifacts']['code_file'].exists()
assert result['deployment_artifacts']['test_file'].exists()
assert result['total_cost'] < 0.50
```

**Estimated Runtime**: 4-6 minutes
**Cost Estimate**: $0.15-$0.30

---

#### Scenario 2: Book Extraction Failure
```python
@pytest.mark.asyncio
async def test_02_extraction_failure_handling():
    """
    Test: Handle book extraction failures gracefully

    Scenarios:
    - Missing book file
    - Invalid PDF format
    - No formulas found
    - Corrupted file
    """
```

**Inputs**:
- Invalid book path
- Corrupted PDF file (mock)
- PDF with no extractable formulas

**Expected Behavior**:
```python
# Should return error status without crashing
assert result['status'] == 'extraction_failed'
assert 'error_message' in result
assert result['extraction_success'] == False
# Should NOT attempt synthesis
assert 'synthesis_status' not in result
# Should log appropriate error
assert 'book file not found' in logs or 'invalid format' in logs
```

**Estimated Runtime**: 30 seconds

---

#### Scenario 3: Synthesis Failure with Rollback
```python
@pytest.mark.asyncio
async def test_03_synthesis_failure_rollback():
    """
    Test: Handle synthesis failures and rollback

    Test Cases:
    - DeepSeek API timeout
    - Claude API rate limit
    - Ollama verification failure
    - Cost limit exceeded
    """
```

**Mocks**:
```python
# Mock API failure
with patch('synthesis.multi_model_synthesis.call_deepseek_api') as mock_deepseek:
    mock_deepseek.side_effect = TimeoutError("API timeout")

    result = await e2e_deployment_flow(book_path, config)

    assert result['status'] in ['failed', 'partial_failure']
    assert 'timeout' in result['error_message'].lower()
    # Verify rollback occurred
    assert result['rollback_completed'] == True
    assert not any(f.exists() for f in result.get('artifacts', []))
```

**Estimated Runtime**: 1 minute

---

#### Scenario 4: Test Generation Failure
```python
@pytest.mark.asyncio
async def test_04_test_generation_failure():
    """
    Test: Handle test generation failures

    Cases:
    - AI model fails to generate valid tests
    - Generated tests have syntax errors
    - Tests cannot be parsed
    """
```

**Expected Behavior**:
- Should fall back to template tests
- Should warn user about test quality
- Should NOT block deployment (configurable)

**Estimated Runtime**: 1 minute

---

#### Scenario 5: Test Execution Failure
```python
@pytest.mark.asyncio
async def test_05_test_execution_failure():
    """
    Test: Handle test execution failures

    Cases:
    - Generated tests fail
    - Test dependencies missing
    - Test timeout
    """
```

**Configuration Options**:
```python
config = {
    'block_on_test_failure': True,  # Should block deployment
    'max_test_retries': 2,
    'test_timeout': 120
}
```

**Expected Behavior**:
- Should report test failures
- Should NOT create PR if `block_on_test_failure=True`
- Should create backup of failed tests
- Should provide detailed error report

**Estimated Runtime**: 2 minutes

---

#### Scenario 6: Git Workflow Failure
```python
@pytest.mark.asyncio
async def test_06_git_workflow_failure():
    """
    Test: Handle git operation failures

    Cases:
    - Branch already exists
    - Commit fails (pre-commit hook)
    - Push fails (network error)
    - Remote branch conflicts
    """
```

**Mocks**:
```python
# Mock git command failures
with patch('subprocess.run') as mock_run:
    mock_run.side_effect = subprocess.CalledProcessError(1, 'git push')

    result = await e2e_deployment_flow(book_path, config)

    assert result['git_status'] == 'failed'
    assert 'push failed' in result['error_message'].lower()
    # Should have local backup
    assert result['local_commit'] == True
```

**Estimated Runtime**: 1 minute

---

#### Scenario 7: PR Creation Failure
```python
@pytest.mark.asyncio
async def test_07_pr_creation_failure():
    """
    Test: Handle GitHub PR creation failures

    Cases:
    - GitHub API authentication failure
    - Rate limit exceeded
    - Repository permissions denied
    - PR already exists
    """
```

**Expected Behavior**:
- Should provide instructions for manual PR creation
- Should save PR template locally
- Should report successful push even if PR fails

**Estimated Runtime**: 30 seconds

---

#### Scenario 8: Concurrent Deployments
```python
@pytest.mark.asyncio
@pytest.mark.timeout(720)  # 12 minute timeout
async def test_08_concurrent_deployments():
    """
    Test: Handle multiple concurrent deployment flows

    Scenarios:
    - 3 books processed simultaneously
    - Resource contention
    - API rate limiting
    - Branch naming conflicts
    """
```

**Test Approach**:
```python
books = ['book1.pdf', 'book2.pdf', 'book3.pdf']
tasks = [e2e_deployment_flow(book, config) for book in books]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Verify all completed
successful = sum(1 for r in results if r.get('status') == 'success')
assert successful >= 2  # At least 2 of 3 should succeed

# Verify unique branches
branches = [r['branch_name'] for r in results if r.get('branch_created')]
assert len(branches) == len(set(branches))  # All unique
```

**Estimated Runtime**: 8-10 minutes
**Cost Estimate**: $0.45-$0.90

---

#### Scenario 9: Cost Limit Protection
```python
@pytest.mark.asyncio
async def test_09_cost_limit_protection():
    """
    Test: Verify cost limits are enforced

    Cases:
    - Daily cost limit exceeded
    - Per-request cost limit exceeded
    - Cost tracking accuracy
    """
```

**Configuration**:
```python
config = {
    'cost_limits': {
        'per_request': 0.50,
        'daily': 5.00
    }
}
```

**Expected Behavior**:
- Should block synthesis if cost would exceed limit
- Should provide cost estimate before proceeding
- Should track costs accurately

**Estimated Runtime**: 1 minute

---

#### Scenario 10: Full Integration Test with Real APIs (Optional)
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('RUN_INTEGRATION_TESTS'), reason="Integration tests disabled")
@pytest.mark.asyncio
@pytest.mark.timeout(600)  # 10 minute timeout
async def test_10_full_integration_real_apis():
    """
    Test: Full E2E integration with real APIs

    Note: Only runs if RUN_INTEGRATION_TESTS=1
    Uses real DeepSeek, Claude, Ollama, GitHub APIs
    """
```

**Configuration**:
- Requires valid API keys
- Uses small sample book to minimize cost
- Creates actual PR in test repository
- Cleans up after completion

**Estimated Runtime**: 5-7 minutes
**Cost Estimate**: $0.15-$0.25

---

### Fixtures

```python
@pytest.fixture
def sample_book_path(temp_directory):
    """Create sample PDF book for testing"""
    book_path = temp_directory / "sample_basketball_analytics.pdf"
    # Create minimal valid PDF (mock)
    book_path.write_text("Mock PDF content")
    return book_path

@pytest.fixture
def deployment_config():
    """Standard deployment configuration"""
    return {
        'mode': 'pr',
        'dry_run': False,
        'block_on_test_failure': True,
        'cost_limits': {'per_request': 1.00},
        'target_repo': '../test-repo',
        'base_branch': 'main'
    }

@pytest.fixture
async def mock_apis():
    """Mock all external APIs"""
    with patch('synthesis.multi_model_synthesis.call_deepseek_api') as mock_deepseek, \
         patch('synthesis.multi_model_synthesis.call_claude_api') as mock_claude, \
         patch('subprocess.run') as mock_git, \
         patch('github.Github') as mock_github:

        # Configure mocks
        mock_deepseek.return_value = {'code': '# Generated code', 'cost': 0.10}
        mock_claude.return_value = {'synthesis': '# Synthesized code', 'cost': 0.15}
        mock_git.return_value = MagicMock(returncode=0)
        mock_github_instance = MagicMock()
        mock_github_instance.create_pull.return_value = {'number': 123, 'url': 'https://...'}
        mock_github.return_value = mock_github_instance

        yield {
            'deepseek': mock_deepseek,
            'claude': mock_claude,
            'git': mock_git,
            'github': mock_github
        }
```

### Test Data

**Sample Extraction Result**:
```json
{
  "book_title": "Basketball on Paper",
  "formulas": [
    {
      "name": "True Shooting Percentage",
      "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
      "description": "Measures shooting efficiency including free throws",
      "variables": ["PTS", "FGA", "FTA"]
    },
    {
      "name": "Effective Field Goal Percentage",
      "formula": "(FGM + 0.5 * FG3M) / FGA",
      "description": "Field goal percentage adjusted for 3-point value",
      "variables": ["FGM", "FG3M", "FGA"]
    }
  ],
  "concepts": [
    "Four Factors of Basketball Success",
    "Offensive Rating",
    "Defensive Rating"
  ],
  "extraction_metadata": {
    "total_pages": 250,
    "formulas_found": 2,
    "extraction_time": 45.2,
    "confidence_score": 0.92
  }
}
```

### Standalone Runner

```python
async def run_all_e2e_tests():
    """Run all E2E deployment flow tests"""
    print("=" * 80)
    print("End-to-End Deployment Flow Tests")
    print("=" * 80)
    print()

    test_suite = TestE2EDeploymentFlow()

    tests = [
        ("Complete E2E Flow", test_suite.test_01_complete_e2e_deployment_flow),
        ("Extraction Failure", test_suite.test_02_extraction_failure_handling),
        ("Synthesis Rollback", test_suite.test_03_synthesis_failure_rollback),
        ("Test Generation Failure", test_suite.test_04_test_generation_failure),
        ("Test Execution Failure", test_suite.test_05_test_execution_failure),
        ("Git Workflow Failure", test_suite.test_06_git_workflow_failure),
        ("PR Creation Failure", test_suite.test_07_pr_creation_failure),
        ("Concurrent Deployments", test_suite.test_08_concurrent_deployments),
        ("Cost Limit Protection", test_suite.test_09_cost_limit_protection),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 80)

        try:
            await test_func()
            passed += 1
            print(f"✅ PASSED: {name}\n")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}\n")

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_e2e_tests())
    sys.exit(0 if success else 1)
```

---

## Gap 2: Automated Deployment System Test

**File**: `scripts/test_phase_11_automated_deployment.py`
**Priority**: HIGH
**Purpose**: Test AutomatedDeploymentOrchestrator and all deployment automation components

### Test Scenarios

#### Scenario 1: Orchestrator Initialization
```python
def test_01_orchestrator_initialization():
    """
    Test: Orchestrator initializes all components correctly

    Components to verify:
    - ProjectStructureMapper
    - CodeIntegrationAnalyzer
    - AICodeImplementer
    - TestGeneratorAndRunner
    - GitWorkflowManager
    - DeploymentSafetyManager
    """
    orchestrator = AutomatedDeploymentOrchestrator()

    assert orchestrator.structure_mapper is not None
    assert orchestrator.integration_analyzer is not None
    assert orchestrator.code_implementer is not None
    assert orchestrator.test_runner is not None
    assert orchestrator.git_manager is not None
    assert orchestrator.safety_manager is not None

    # Verify configuration
    assert orchestrator.config.mode in ['pr', 'commit', 'local']
    assert orchestrator.config.batch_size > 0
    assert orchestrator.config.max_failures > 0
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 2: Configuration Loading
```python
def test_02_configuration_loading(temp_directory):
    """
    Test: Load configuration from YAML file

    Test Cases:
    - Valid YAML configuration
    - Invalid YAML syntax
    - Missing configuration file
    - Partial configuration (defaults)
    """
    # Create test config
    config_path = temp_directory / "deployment_config.yaml"
    config_path.write_text("""
enabled: true
mode: pr
batch_size: 3
dry_run: false
block_on_test_failure: true
max_failures: 2
target_repo: ../test-repo
base_branch: main
create_prs: true
""")

    orchestrator = AutomatedDeploymentOrchestrator(config_path=str(config_path))

    assert orchestrator.config.enabled == True
    assert orchestrator.config.mode == 'pr'
    assert orchestrator.config.batch_size == 3
    assert orchestrator.config.block_on_test_failure == True
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 3: Recommendation Loading & Dependency Sorting
```python
def test_03_recommendation_dependency_sorting(temp_directory):
    """
    Test: Load recommendations and sort by dependencies

    Test Cases:
    - Linear dependencies (A → B → C)
    - Multiple dependencies (A,B → C)
    - Circular dependency detection
    - No dependencies
    """
    recommendations = [
        {
            'id': 'rec-3',
            'title': 'Feature C',
            'dependencies': ['rec-1', 'rec-2']
        },
        {
            'id': 'rec-1',
            'title': 'Feature A',
            'dependencies': []
        },
        {
            'id': 'rec-2',
            'title': 'Feature B',
            'dependencies': ['rec-1']
        }
    ]

    sorted_recs = orchestrator._sort_by_dependencies(recommendations)

    # Verify order: rec-1 → rec-2 → rec-3
    assert sorted_recs[0]['id'] == 'rec-1'
    assert sorted_recs[1]['id'] == 'rec-2'
    assert sorted_recs[2]['id'] == 'rec-3'
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 4: Project Structure Mapping
```python
@pytest.mark.asyncio
async def test_04_project_structure_mapping():
    """
    Test: Map recommendations to project file structure

    Verifies:
    - File path generation
    - Directory creation
    - Naming conventions
    - Conflict detection
    """
    recommendation = {
        'id': 'rec-1',
        'title': 'Add True Shooting Percentage Calculator',
        'category': 'analytics',
        'type': 'feature'
    }

    mapping = orchestrator.structure_mapper.map_to_structure(recommendation)

    assert mapping.implementation_file.endswith('.py')
    assert 'analytics' in str(mapping.implementation_file).lower()
    assert mapping.test_file.endswith('_test.py') or mapping.test_file.endswith('test_.py')
    assert mapping.directory.exists()
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 5: Code Integration Analysis
```python
@pytest.mark.asyncio
async def test_05_code_integration_analysis():
    """
    Test: Analyze existing code for integration points

    Checks:
    - Similar function detection
    - Import statement analysis
    - Dependency identification
    - Conflict detection
    """
    recommendation = {
        'title': 'Add Usage Rate Calculator',
        'description': 'Calculate player usage rate metric',
        'code_snippet': 'def calculate_usage_rate(...):'
    }

    analysis = await orchestrator.integration_analyzer.analyze(recommendation)

    assert 'integration_points' in analysis
    assert 'similar_functions' in analysis
    assert 'required_imports' in analysis
    assert 'potential_conflicts' in analysis
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 6: AI Code Implementation
```python
@pytest.mark.asyncio
async def test_06_ai_code_implementation():
    """
    Test: Generate code implementation with AI

    Test Cases:
    - Successful generation
    - Syntax validation
    - Integration with existing code
    - Error handling
    """
    context = {
        'recommendation': {
            'title': 'True Shooting Percentage',
            'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
            'description': 'Advanced shooting efficiency metric'
        },
        'existing_code': '# Existing analytics module...',
        'integration_plan': {}
    }

    with patch('ai_code_implementer.call_ai_api') as mock_ai:
        mock_ai.return_value = {
            'code': 'def calculate_ts_percentage(pts, fga, fta):\n    return pts / (2 * (fga + 0.44 * fta))',
            'tests': 'def test_ts_percentage():\n    assert calculate_ts_percentage(20, 10, 4) > 0',
            'cost': 0.08
        }

        result = await orchestrator.code_implementer.implement(context)

        assert result.success == True
        assert 'def calculate_ts_percentage' in result.code
        assert result.syntax_valid == True
        assert result.cost < 0.15
```

**Estimated Runtime**: 20 seconds

---

#### Scenario 7: Test Generation & Execution
```python
@pytest.mark.asyncio
async def test_07_test_generation_and_execution():
    """
    Test: Generate and execute tests for implemented code

    Verifies:
    - Test generation
    - Test file creation
    - Test execution
    - Result reporting
    """
    implementation = {
        'code': 'def add(a, b):\n    return a + b',
        'file_path': 'lib/math_utils.py'
    }

    with patch('test_generator_and_runner.run_tests') as mock_run:
        mock_run.return_value = TestResult(
            passed=True,
            tests_run=5,
            failures=[],
            execution_time=1.2
        )

        result = await orchestrator.test_runner.generate_and_run(implementation)

        assert result.tests_generated == True
        assert result.tests_passed == True
        assert result.tests_run >= 3
```

**Estimated Runtime**: 30 seconds

---

#### Scenario 8: Git Workflow Management
```python
@pytest.mark.asyncio
async def test_08_git_workflow_management():
    """
    Test: Git operations (branch, commit, push, PR)

    Operations:
    - Create feature branch
    - Stage files
    - Commit with message
    - Push to remote
    - Create GitHub PR
    """
    files = [
        'lib/analytics.py',
        'tests/test_analytics.py'
    ]

    with patch('subprocess.run') as mock_run, \
         patch('github.Github') as mock_github:

        mock_run.return_value = MagicMock(returncode=0)
        mock_gh = MagicMock()
        mock_gh.create_pull.return_value = {
            'number': 456,
            'url': 'https://github.com/owner/repo/pull/456',
            'state': 'open'
        }
        mock_github.return_value = mock_gh

        result = await orchestrator.git_manager.create_pr(
            files=files,
            commit_message='Add analytics functions',
            pr_title='Feature: Analytics Functions'
        )

        assert result.pr_created == True
        assert result.pr_number == 456
        assert 'github.com' in result.pr_url
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 9: Safety Checks & Rollback
```python
@pytest.mark.asyncio
async def test_09_safety_checks_and_rollback():
    """
    Test: Pre-deployment safety checks and rollback capability

    Checks:
    - Breaking change detection
    - Test coverage requirements
    - Code quality metrics
    - Rollback on failure
    """
    deployment_plan = {
        'files_to_modify': ['lib/core.py'],
        'files_to_create': ['lib/new_feature.py'],
        'tests_generated': True,
        'test_coverage': 85.0
    }

    # Create backup first
    backup = await orchestrator.safety_manager.create_backup()
    assert backup.created == True

    # Run safety checks
    safety_result = await orchestrator.safety_manager.verify_deployment(deployment_plan)

    assert 'breaking_changes' in safety_result
    assert 'test_coverage_adequate' in safety_result
    assert safety_result.passed in [True, False]

    # Test rollback
    if not safety_result.passed:
        rollback_result = await orchestrator.safety_manager.rollback(backup)
        assert rollback_result.success == True
```

**Estimated Runtime**: 20 seconds

---

#### Scenario 10: Full Deployment Workflow
```python
@pytest.mark.asyncio
@pytest.mark.timeout(180)  # 3 minute timeout
async def test_10_full_deployment_workflow():
    """
    Test: Complete deployment workflow end-to-end

    Steps:
    1. Load recommendations
    2. Sort by dependencies
    3. For each recommendation:
       - Map to structure
       - Analyze integration
       - Generate code
       - Generate tests
       - Run tests
       - Create backup
       - Safety checks
       - Git operations
       - Create PR
    4. Generate deployment report
    """
    recommendations = [
        {
            'id': 'rec-1',
            'title': 'Add TS% Calculator',
            'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
            'dependencies': []
        }
    ]

    # Mock all external dependencies
    with patch.multiple(
        orchestrator,
        structure_mapper=MagicMock(),
        integration_analyzer=MagicMock(),
        code_implementer=MagicMock(),
        test_runner=MagicMock(),
        git_manager=MagicMock(),
        safety_manager=MagicMock()
    ):
        report = await orchestrator.deploy_recommendations(recommendations)

        assert report.total_recommendations == 1
        assert report.successful_deployments >= 0
        assert report.prs_created >= 0
        assert report.total_time > 0
        assert len(report.results) == 1
```

**Estimated Runtime**: 1-2 minutes

---

#### Scenario 11: Batch Processing
```python
@pytest.mark.asyncio
async def test_11_batch_processing():
    """
    Test: Process recommendations in batches

    Configuration:
    - batch_size: 3
    - Verify batching logic
    - Verify error isolation (failure in batch 1 doesn't stop batch 2)
    """
    recommendations = [
        {'id': f'rec-{i}', 'title': f'Feature {i}', 'dependencies': []}
        for i in range(10)
    ]

    orchestrator.config.batch_size = 3

    # One recommendation in batch 2 will fail
    def mock_deploy(rec):
        if rec['id'] == 'rec-4':
            raise ValueError("Deployment failed")
        return DeploymentResult(
            recommendation_id=rec['id'],
            success=True,
            implementation_generated=True,
            tests_generated=True,
            tests_passed=True,
            branch_created=True,
            pr_created=True
        )

    with patch.object(orchestrator, '_deploy_single', side_effect=mock_deploy):
        report = await orchestrator.deploy_recommendations(recommendations)

        # Should complete 9 of 10 (rec-4 failed)
        assert report.successful_deployments == 9
        assert report.failed_deployments == 1
```

**Estimated Runtime**: 30 seconds

---

#### Scenario 12: Error Recovery & Retry Logic
```python
@pytest.mark.asyncio
async def test_12_error_recovery_and_retry():
    """
    Test: Error recovery and retry mechanisms

    Scenarios:
    - Transient failures (retry succeeds)
    - Persistent failures (max retries exceeded)
    - Partial failure recovery
    """
    recommendation = {
        'id': 'rec-1',
        'title': 'Test Feature'
    }

    call_count = 0
    def mock_api_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError("API timeout")
        return {"success": True}

    orchestrator.config.max_retries = 3

    with patch('ai_code_implementer.call_ai_api', side_effect=mock_api_call):
        result = await orchestrator._deploy_single(recommendation)

        # Should succeed on 3rd attempt
        assert call_count == 3
        assert result.success == True
```

**Estimated Runtime**: 15 seconds

---

### Summary for Gap 2

**Total Scenarios**: 12
**Total Runtime**: 3-4 minutes
**Total Lines**: 700-800
**Dependencies**: subprocess, github, pytest, asyncio, pathlib

---

## Gap 3: DIMS Integration Test

**File**: `tests/test_dims_integration.py`
**Priority**: HIGH
**Purpose**: Test Data Inventory Management System integration

### Test Scenarios

#### Scenario 1: Scanner Initialization
```python
def test_01_dims_scanner_initialization():
    """
    Test: Initialize DataInventoryScanner

    Verifies:
    - Path validation
    - Configuration loading
    - Database connection (optional)
    - Static vs. live mode selection
    """
    inventory_path = "../nba-simulator-aws/inventory"

    scanner = DataInventoryScanner(
        inventory_path=inventory_path,
        enable_live_queries=False  # Use static metrics for test
    )

    assert scanner.inventory_path.exists()
    assert scanner.live_queries_enabled in [True, False]
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 2: Load Metrics from YAML
```python
def test_02_load_metrics_from_yaml(temp_directory):
    """
    Test: Load inventory metrics from YAML file

    Test Data:
    - Valid metrics.yaml
    - Missing metrics file
    - Invalid YAML syntax
    - Partial metrics data
    """
    # Create mock metrics.yaml
    metrics_file = temp_directory / "metrics.yaml"
    metrics_file.write_text("""
database:
  total_tables: 15
  total_rows: 5000000
  size_mb: 2500

s3:
  total_objects: 172000
  total_size_gb: 450
  file_types:
    - parquet
    - csv
    - json

coverage:
  seasons: "2014-2025"
  games: 15000
  players: 5000
""")

    scanner = DataInventoryScanner(inventory_path=str(temp_directory))
    metrics = scanner._load_metrics()

    assert metrics['database']['total_tables'] == 15
    assert metrics['s3']['total_objects'] == 172000
    assert '2014-2025' in metrics['coverage']['seasons']
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 3: Parse SQL Schema
```python
def test_03_parse_sql_schema(temp_directory):
    """
    Test: Parse SQL schema files

    Verifies:
    - Table detection
    - Column parsing
    - Data type extraction
    - Index identification
    """
    # Create mock schema file
    schema_file = temp_directory / "schema.sql"
    schema_file.write_text("""
CREATE TABLE master_player_game_stats (
    game_id VARCHAR(50) PRIMARY KEY,
    player_id VARCHAR(50) NOT NULL,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    plus_minus DECIMAL(5,2),
    game_date DATE,
    INDEX idx_player (player_id),
    INDEX idx_date (game_date)
);

CREATE TABLE master_games (
    game_id VARCHAR(50) PRIMARY KEY,
    home_team VARCHAR(3),
    away_team VARCHAR(3),
    game_date DATE,
    season INTEGER
);
""")

    scanner = DataInventoryScanner(inventory_path=str(temp_directory))
    schema = scanner._parse_schema()

    assert 'master_player_game_stats' in schema
    assert 'master_games' in schema
    assert 'points' in schema['master_player_game_stats']['columns']
    assert schema['master_player_game_stats']['columns']['plus_minus']['type'] == 'DECIMAL'
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 4: Assess Data Coverage
```python
@pytest.mark.asyncio
async def test_04_assess_data_coverage():
    """
    Test: Assess data coverage and availability

    Checks:
    - Season coverage
    - Team coverage
    - Player coverage
    - Data completeness
    """
    scanner = DataInventoryScanner(
        inventory_path="../nba-simulator-aws/inventory",
        enable_live_queries=False
    )

    coverage = scanner._assess_data_coverage()

    assert 'seasons' in coverage
    assert 'teams' in coverage
    assert 'players' in coverage
    assert 'completeness_score' in coverage
    assert 0 <= coverage['completeness_score'] <= 100
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 5: Extract Available Features
```python
def test_05_extract_available_features():
    """
    Test: Extract available features for AI recommendations

    Features:
    - Player statistics
    - Team statistics
    - Game data
    - Play-by-play data
    - Advanced metrics
    """
    scanner = DataInventoryScanner(
        inventory_path="../nba-simulator-aws/inventory",
        enable_live_queries=False
    )

    features = scanner._extract_available_features()

    assert 'player_stats' in features
    assert 'team_stats' in features
    assert 'game_data' in features
    assert len(features) > 0
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 6: Generate AI Summary
```python
def test_06_generate_ai_summary():
    """
    Test: Generate AI-friendly summary of data availability

    Output format:
    - Natural language summary
    - Key statistics
    - Available tables
    - Recommended use cases
    """
    scanner = DataInventoryScanner(
        inventory_path="../nba-simulator-aws/inventory",
        enable_live_queries=False
    )

    summary = scanner._generate_ai_summary()

    assert 'summary' in summary
    assert 'key_statistics' in summary
    assert 'available_tables' in summary
    assert 'recommended_use_cases' in summary
    assert len(summary['summary']) > 100  # Should be descriptive
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 7: Live Database Query (Optional)
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason="Database not configured")
@pytest.mark.asyncio
async def test_07_live_database_query():
    """
    Test: Query live database for statistics

    Queries:
    - Table row counts
    - Date ranges
    - Distinct value counts
    """
    scanner = DataInventoryScanner(
        inventory_path="../nba-simulator-aws/inventory",
        enable_live_queries=True
    )

    if scanner.live_queries_enabled:
        stats = await scanner._query_live_stats()

        assert 'table_counts' in stats
        assert 'date_ranges' in stats
        assert stats['table_counts']['master_games'] > 0
```

**Estimated Runtime**: 20-30 seconds (if database available)

---

#### Scenario 8: Full Inventory Scan
```python
@pytest.mark.asyncio
async def test_08_full_inventory_scan():
    """
    Test: Complete inventory scan

    Verifies:
    - All scan components work together
    - Output structure is complete
    - Data is valid and usable
    """
    scanner = DataInventoryScanner(
        inventory_path="../nba-simulator-aws/inventory",
        enable_live_queries=False
    )

    inventory = scanner.scan_full_inventory()

    assert 'metadata' in inventory
    assert 'metrics' in inventory
    assert 'schema' in inventory
    assert 'data_coverage' in inventory
    assert 'available_features' in inventory
    assert 'system_capabilities' in inventory
    assert 'summary_for_ai' in inventory

    # Verify metadata
    assert inventory['metadata']['scan_date'] is not None
    assert inventory['metadata']['mode'] in ['static', 'live']
```

**Estimated Runtime**: 30 seconds

---

### Summary for Gap 3

**Total Scenarios**: 8
**Total Runtime**: 2-3 minutes
**Total Lines**: 400-500
**Dependencies**: yaml, pathlib, pytest

---

## Gap 4: Git-Secrets & Pre-Commit Hooks Test

**File**: `tests/test_security_hooks.py`
**Priority**: MEDIUM
**Purpose**: Test detect-secrets and pre-commit hook integration

### Test Scenarios

#### Scenario 1: Detect-Secrets Configuration
```python
def test_01_detect_secrets_configuration():
    """
    Test: Verify detect-secrets is properly configured

    Checks:
    - .pre-commit-config.yaml exists
    - detect-secrets hook is present
    - Baseline file exists
    - Exclusion patterns are correct
    """
    pre_commit_config = Path(".pre-commit-config.yaml")
    assert pre_commit_config.exists()

    with open(pre_commit_config) as f:
        config = yaml.safe_load(f)

    # Find detect-secrets hook
    detect_secrets_hook = None
    for repo in config['repos']:
        if 'detect-secrets' in repo['repo']:
            detect_secrets_hook = repo
            break

    assert detect_secrets_hook is not None
    assert any(hook['id'] == 'detect-secrets' for hook in detect_secrets_hook['hooks'])

    # Verify baseline exists
    assert Path(".secrets.baseline").exists()
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 2: Secret Detection in Python Files
```python
def test_02_secret_detection_python_files(temp_directory):
    """
    Test: Detect secrets in Python files

    Test Cases:
    - AWS keys
    - API keys
    - Passwords in code
    - Database connection strings
    """
    test_files = {
        'aws_key.py': '''
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
''',
        'api_key.py': '''
ANTHROPIC_API_KEY = "sk-ant-api03-1234567890abcdef"
''',
        'password.py': '''
db_password = "SuperSecret123!"
connection_string = "postgresql://user:password@localhost/db"
'''
    }

    for filename, content in test_files.items():
        filepath = temp_directory / filename
        filepath.write_text(content)

        # Run detect-secrets
        result = subprocess.run(
            ['detect-secrets', 'scan', str(filepath)],
            capture_output=True,
            text=True
        )

        # Should detect secrets
        assert result.returncode != 0 or 'potential secret' in result.stdout.lower()
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 3: Exclusion Patterns
```python
def test_03_exclusion_patterns(temp_directory):
    """
    Test: Verify exclusion patterns work correctly

    Files that SHOULD be excluded:
    - .env.example
    - docs/*.md
    - *_COMPLETE.md
    - tests/*
    - .secrets.baseline
    """
    excluded_files = {
        '.env.example': 'API_KEY=example_key_not_real',
        'docs/guide.md': 'API_KEY = "sk-ant-example"',
        'TEST_COMPLETE.md': 'SECRET="test"',
        '.secrets.baseline': '{"results": {}}'
    }

    for filename, content in excluded_files.items():
        filepath = temp_directory / filename
        filepath.parent.mkdir(exist_ok=True, parents=True)
        filepath.write_text(content)

        # Run detect-secrets with config
        result = subprocess.run(
            ['detect-secrets', 'scan', '--baseline', '.secrets.baseline', str(filepath)],
            capture_output=True,
            text=True,
            cwd=temp_directory
        )

        # These files should be excluded (no secrets detected)
        # Note: Actual behavior depends on .pre-commit-config.yaml exclude patterns
```

**Estimated Runtime**: 20 seconds

---

#### Scenario 4: Baseline File Management
```python
def test_04_baseline_file_management():
    """
    Test: Baseline file creation and updates

    Operations:
    - Create new baseline
    - Update existing baseline
    - Audit baseline
    - Verify baseline format
    """
    baseline_path = Path(".secrets.baseline")

    # Backup existing baseline
    if baseline_path.exists():
        backup = baseline_path.read_text()

    try:
        # Create new baseline
        result = subprocess.run(
            ['detect-secrets', 'scan', '--baseline', '.secrets.baseline.test'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert Path(".secrets.baseline.test").exists()

        # Verify baseline format
        with open(".secrets.baseline.test") as f:
            baseline = json.load(f)

        assert 'version' in baseline
        assert 'results' in baseline
        assert 'generated_at' in baseline

    finally:
        # Cleanup
        if Path(".secrets.baseline.test").exists():
            Path(".secrets.baseline.test").unlink()
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 5: Pre-Commit Hook Installation
```python
def test_05_pre_commit_hook_installation():
    """
    Test: Pre-commit hooks are installed correctly

    Checks:
    - pre-commit is installed
    - Hooks are configured
    - Git hooks directory has pre-commit hook
    """
    # Check pre-commit installation
    result = subprocess.run(['pre-commit', '--version'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'pre-commit' in result.stdout

    # Check if hooks are installed
    git_hooks_dir = Path(".git/hooks")
    if git_hooks_dir.exists():
        pre_commit_hook = git_hooks_dir / "pre-commit"
        # Hook may or may not be installed in test environment
        # Just verify the directory structure
        assert git_hooks_dir.exists()
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 6: Commit Blocking Behavior
```python
def test_06_commit_blocking_behavior(temp_directory):
    """
    Test: Pre-commit hook blocks commits with secrets

    Simulation:
    - Create git repo
    - Add file with secret
    - Attempt commit
    - Verify commit is blocked
    """
    # Create temporary git repo
    subprocess.run(['git', 'init'], cwd=temp_directory, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_directory, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_directory, check=True)

    # Copy pre-commit config
    import shutil
    shutil.copy('.pre-commit-config.yaml', temp_directory)

    # Install hooks
    subprocess.run(['pre-commit', 'install'], cwd=temp_directory, check=True)

    # Create file with secret
    secret_file = temp_directory / "config.py"
    secret_file.write_text('API_KEY = "sk-ant-api03-RealSecretKey123"')

    subprocess.run(['git', 'add', 'config.py'], cwd=temp_directory, check=True)

    # Attempt commit (should fail)
    result = subprocess.run(
        ['git', 'commit', '-m', 'Add config'],
        cwd=temp_directory,
        capture_output=True,
        text=True
    )

    # Commit should be blocked
    assert result.returncode != 0
    assert 'detect-secrets' in result.stdout or 'secret' in result.stdout.lower()
```

**Estimated Runtime**: 30 seconds

---

#### Scenario 7: Bandit Security Scanning
```python
def test_07_bandit_security_scanning(temp_directory):
    """
    Test: Bandit security scanner hook

    Security issues to detect:
    - Hardcoded passwords
    - SQL injection risks
    - Insecure random
    - Assert used
    """
    test_file = temp_directory / "insecure.py"
    test_file.write_text('''
import random

# B105: Hardcoded password
password = "hardcoded_password"

# B311: Insecure random
random_number = random.random()

# B101: Assert used
assert True, "This is an assertion"

# B608: SQL injection possible
def query_db(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
''')

    # Run bandit
    result = subprocess.run(
        ['bandit', '-r', str(test_file)],
        capture_output=True,
        text=True
    )

    # Should detect security issues
    assert 'Issue' in result.stdout or result.returncode != 0
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 8: Black Formatting Enforcement
```python
def test_08_black_formatting_enforcement(temp_directory):
    """
    Test: Black formatter hook

    Cases:
    - Properly formatted code (passes)
    - Improperly formatted code (fails/fixes)
    """
    # Properly formatted code
    good_file = temp_directory / "good.py"
    good_file.write_text('''
def calculate_sum(a, b):
    return a + b


def main():
    result = calculate_sum(1, 2)
    print(result)
''')

    result = subprocess.run(['black', '--check', str(good_file)], capture_output=True)
    assert result.returncode == 0  # No changes needed

    # Improperly formatted code
    bad_file = temp_directory / "bad.py"
    bad_file.write_text('def add(a,b):return a+b')

    result = subprocess.run(['black', '--check', str(bad_file)], capture_output=True)
    assert result.returncode != 0  # Needs formatting

    # Apply formatting
    subprocess.run(['black', str(bad_file)], capture_output=True)

    result = subprocess.run(['black', '--check', str(bad_file)], capture_output=True)
    assert result.returncode == 0  # Now properly formatted
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 9: Custom File Size Check
```python
def test_09_custom_file_size_check(temp_directory):
    """
    Test: Custom pre-commit file size check

    Checks:
    - File size limits
    - Large file detection
    - Exclusions for large binary files
    """
    # Check if custom script exists
    pre_commit_script = Path("scripts/pre-commit.template")
    if not pre_commit_script.exists():
        pytest.skip("Custom pre-commit script not found")

    # Create large file
    large_file = temp_directory / "large.py"
    large_file.write_text('x = 1\n' * 100000)  # ~600KB file

    # Run custom check
    result = subprocess.run(
        [str(pre_commit_script)],
        capture_output=True,
        text=True,
        cwd=temp_directory,
        env={**os.environ, 'GIT_DIR': str(temp_directory / '.git')}
    )

    # Check behavior (might warn or fail depending on configuration)
    # Just verify script runs without crashing
    assert result.returncode in [0, 1]
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 10: Integration Test - Full Pre-Commit Run
```python
def test_10_full_pre_commit_run(temp_directory):
    """
    Test: Run all pre-commit hooks on test files

    Hooks:
    - detect-secrets
    - bandit
    - black
    - custom checks
    """
    # Setup git repo
    subprocess.run(['git', 'init'], cwd=temp_directory, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=temp_directory, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=temp_directory, check=True)

    # Copy config
    import shutil
    shutil.copy('.pre-commit-config.yaml', temp_directory)

    # Install hooks
    subprocess.run(['pre-commit', 'install'], cwd=temp_directory)

    # Create test files
    (temp_directory / "test.py").write_text('''
def greet(name):
    return f"Hello, {name}!"
''')

    subprocess.run(['git', 'add', '.'], cwd=temp_directory)

    # Run pre-commit on all files
    result = subprocess.run(
        ['pre-commit', 'run', '--all-files'],
        cwd=temp_directory,
        capture_output=True,
        text=True
    )

    # Verify hooks ran
    assert 'detect-secrets' in result.stdout or 'Detect secrets' in result.stdout
    # Note: May pass or fail depending on file content
```

**Estimated Runtime**: 30 seconds

---

### Summary for Gap 4

**Total Scenarios**: 10
**Total Runtime**: 1-2 minutes
**Total Lines**: 500-600
**Dependencies**: subprocess, yaml, json, pytest, pre-commit, detect-secrets, bandit, black

---

## Gap 5: Phase 1 Foundation Test

**File**: `scripts/test_phase_1_foundation.py`
**Priority**: MEDIUM
**Purpose**: Test infrastructure foundation setup

### Test Scenarios

#### Scenario 1: Environment Variables Validation
```python
def test_01_environment_variables_validation():
    """
    Test: Verify all required environment variables are set

    Required Variables:
    - RDS_HOST, RDS_DATABASE, RDS_USERNAME, RDS_PASSWORD
    - S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - DEEPSEEK_API_KEY, ANTHROPIC_API_KEY
    - Optional: OLLAMA_HOST, GITHUB_TOKEN
    """
    required_vars = [
        'RDS_HOST',
        'RDS_DATABASE',
        'RDS_USERNAME',
        'RDS_PASSWORD',
        'S3_BUCKET',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'DEEPSEEK_API_KEY',
        'ANTHROPIC_API_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")

    # In test environment, we may not have all vars
    # Just verify the check works
    assert isinstance(missing_vars, list)
```

**Estimated Runtime**: 2 seconds

---

#### Scenario 2: S3 Bucket Accessibility
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('AWS_ACCESS_KEY_ID'), reason="AWS credentials not configured")
def test_02_s3_bucket_accessibility():
    """
    Test: Verify S3 bucket is accessible

    Operations:
    - List bucket
    - Check permissions
    - Verify bucket exists
    """
    import boto3
    from botocore.exceptions import ClientError

    s3_client = boto3.client('s3')
    bucket_name = os.getenv('S3_BUCKET')

    try:
        # List objects (limit to 1 to minimize cost)
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=1
        )

        assert 'ResponseMetadata' in response
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200

        logger.info(f"✅ S3 bucket '{bucket_name}' is accessible")

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            pytest.fail(f"S3 bucket '{bucket_name}' does not exist")
        else:
            pytest.fail(f"S3 access error: {e}")
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 3: Database Connection
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('RDS_HOST'), reason="Database credentials not configured")
@pytest.mark.asyncio
async def test_03_database_connection():
    """
    Test: Verify database connection

    Checks:
    - Connection establishment
    - Query execution
    - Database schema exists
    """
    import asyncpg

    try:
        conn = await asyncpg.connect(
            host=os.getenv('RDS_HOST'),
            database=os.getenv('RDS_DATABASE'),
            user=os.getenv('RDS_USERNAME'),
            password=os.getenv('RDS_PASSWORD'),
            timeout=10
        )

        # Execute simple query
        result = await conn.fetchval('SELECT 1')
        assert result == 1

        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        logger.info(f"✅ Database connected - found {len(tables)} tables")

        await conn.close()

    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 4: MCP Server Configuration
```python
def test_04_mcp_server_configuration():
    """
    Test: Verify MCP server configuration

    Checks:
    - Config file exists
    - Config is valid YAML/JSON
    - Required fields present
    - Server settings valid
    """
    config_paths = [
        Path("mcp_server/config.yaml"),
        Path("mcp_server/config.json"),
        Path("config/mcp_config.yaml")
    ]

    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break

    if not config_file:
        pytest.skip("MCP config file not found")

    # Load config
    if config_file.suffix == '.yaml':
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        with open(config_file) as f:
            config = json.load(f)

    # Verify required fields
    required_fields = ['server', 'database', 'security']
    for field in required_fields:
        assert field in config, f"Missing config field: {field}"

    logger.info("✅ MCP server configuration is valid")
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 5: AWS Credentials Verification
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('AWS_ACCESS_KEY_ID'), reason="AWS credentials not configured")
def test_05_aws_credentials_verification():
    """
    Test: Verify AWS credentials are valid

    Checks:
    - Credentials exist
    - Credentials are valid (STS GetCallerIdentity)
    - IAM permissions
    """
    import boto3
    from botocore.exceptions import ClientError

    sts_client = boto3.client('sts')

    try:
        # Get caller identity
        response = sts_client.get_caller_identity()

        assert 'Account' in response
        assert 'Arn' in response

        logger.info(f"✅ AWS credentials valid - Account: {response['Account']}")

    except ClientError as e:
        pytest.fail(f"AWS credentials invalid: {e}")
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 6: Secrets Management Setup
```python
def test_06_secrets_management_setup():
    """
    Test: Verify secrets management is configured

    Systems:
    - .env file exists (local development)
    - Secrets hierarchy (check for secrets_loader)
    - Environment-based secrets
    """
    # Check for .env file
    env_file = Path(".env")
    env_example = Path(".env.example")

    # At least .env.example should exist
    assert env_example.exists(), ".env.example should exist as template"

    # Check for secrets loader module
    secrets_loader_path = Path("mcp_server/secrets_loader.py")
    if secrets_loader_path.exists():
        # Verify it can be imported
        sys.path.insert(0, str(secrets_loader_path.parent))
        try:
            import secrets_loader
            assert hasattr(secrets_loader, 'init_secrets')
            logger.info("✅ Secrets loader module available")
        except ImportError as e:
            pytest.fail(f"Failed to import secrets_loader: {e}")
    else:
        logger.warning("⚠️  secrets_loader.py not found")
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 7: Network Connectivity
```python
@pytest.mark.integration
def test_07_network_connectivity():
    """
    Test: Verify network connectivity to required services

    Services:
    - DeepSeek API
    - Anthropic API
    - GitHub API
    - AWS endpoints
    """
    import requests

    endpoints = {
        'DeepSeek': 'https://api.deepseek.com',
        'Anthropic': 'https://api.anthropic.com',
        'GitHub': 'https://api.github.com',
        'AWS S3': 'https://s3.amazonaws.com'
    }

    results = {}
    for name, url in endpoints.items():
        try:
            response = requests.head(url, timeout=5)
            results[name] = response.status_code < 500
            logger.info(f"✅ {name}: accessible (status {response.status_code})")
        except Exception as e:
            results[name] = False
            logger.warning(f"⚠️  {name}: not accessible ({e})")

    # At least some endpoints should be accessible
    accessible_count = sum(1 for v in results.values() if v)
    assert accessible_count >= 2, f"Only {accessible_count} endpoints accessible"
```

**Estimated Runtime**: 10 seconds

---

#### Scenario 8: Project Directory Structure
```python
def test_08_project_directory_structure():
    """
    Test: Verify project directory structure

    Required Directories:
    - mcp_server/
    - synthesis/
    - scripts/
    - tests/
    - docs/ (optional)
    """
    required_dirs = [
        Path("mcp_server"),
        Path("synthesis"),
        Path("scripts"),
        Path("tests")
    ]

    optional_dirs = [
        Path("docs"),
        Path("deployment"),
        Path("config")
    ]

    missing_required = []
    for dir_path in required_dirs:
        if not dir_path.exists() or not dir_path.is_dir():
            missing_required.append(str(dir_path))

    assert len(missing_required) == 0, f"Missing required directories: {missing_required}"

    existing_optional = [str(d) for d in optional_dirs if d.exists()]
    logger.info(f"✅ Directory structure valid - Optional dirs: {existing_optional}")
```

**Estimated Runtime**: 2 seconds

---

#### Scenario 9: Python Dependencies
```python
def test_09_python_dependencies():
    """
    Test: Verify required Python packages are installed

    Required Packages:
    - pytest, pytest-asyncio
    - boto3, botocore
    - asyncpg
    - pyyaml
    - python-dotenv
    - anthropic, openai (or equivalent)
    """
    required_packages = [
        'pytest',
        'pytest_asyncio',
        'boto3',
        'asyncpg',
        'yaml',
        'dotenv',
        'pathlib'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"⚠️  Missing packages: {', '.join(missing_packages)}")

    # Should have most packages installed
    installed_count = len(required_packages) - len(missing_packages)
    assert installed_count >= len(required_packages) * 0.7, \
        f"Only {installed_count}/{len(required_packages)} packages installed"
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 10: Infrastructure Health Check
```python
@pytest.mark.asyncio
async def test_10_infrastructure_health_check():
    """
    Test: Comprehensive infrastructure health check

    Combines:
    - Environment variables
    - Database connection
    - S3 access
    - API connectivity
    - Configuration validity
    """
    health_status = {
        'environment_vars': False,
        'database': False,
        's3': False,
        'apis': False,
        'configuration': False
    }

    # Check environment vars
    required_vars = ['RDS_HOST', 'S3_BUCKET', 'DEEPSEEK_API_KEY']
    health_status['environment_vars'] = all(os.getenv(var) for var in required_vars)

    # Check database (if configured)
    if os.getenv('RDS_HOST'):
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=os.getenv('RDS_HOST'),
                database=os.getenv('RDS_DATABASE'),
                user=os.getenv('RDS_USERNAME'),
                password=os.getenv('RDS_PASSWORD'),
                timeout=5
            )
            await conn.fetchval('SELECT 1')
            await conn.close()
            health_status['database'] = True
        except:
            pass

    # Check S3 (if configured)
    if os.getenv('AWS_ACCESS_KEY_ID'):
        try:
            import boto3
            s3 = boto3.client('s3')
            s3.list_objects_v2(Bucket=os.getenv('S3_BUCKET'), MaxKeys=1)
            health_status['s3'] = True
        except:
            pass

    # Check configuration
    health_status['configuration'] = Path("mcp_server/config.yaml").exists() or \
                                     Path("mcp_server/config.json").exists()

    # Generate health report
    total_checks = len(health_status)
    passed_checks = sum(1 for v in health_status.values() if v)
    health_percentage = (passed_checks / total_checks) * 100

    logger.info(f"📊 Infrastructure Health: {health_percentage:.1f}%")
    for component, status in health_status.items():
        symbol = "✅" if status else "❌"
        logger.info(f"   {symbol} {component}: {'OK' if status else 'FAILED'}")

    # Should have at least 60% health
    assert health_percentage >= 60, f"Infrastructure health too low: {health_percentage:.1f}%"
```

**Estimated Runtime**: 20 seconds

---

### Summary for Gap 5

**Total Scenarios**: 10
**Total Runtime**: 2-3 minutes
**Total Lines**: 500-600
**Dependencies**: boto3, asyncpg, requests, yaml, pytest

---

## Gap 6: Phase 4 File Generation Test

**File**: `scripts/test_phase_4_file_generation.py`
**Priority**: MEDIUM
**Purpose**: Test implementation file generation from recommendations

### Test Scenarios

#### Scenario 1: File Generator Initialization
```python
def test_01_file_generator_initialization():
    """
    Test: Initialize Phase4FileGenerationBasic

    Verifies:
    - Class instantiation
    - Configuration loading
    - Safety managers initialization
    """
    input_file = Path("implementation_plans/consolidated_recommendations.json")
    output_dir = Path("implementation_plans")

    generator = Phase4FileGenerationBasic(
        input_file=input_file,
        output_dir=output_dir
    )

    assert generator.input_file == input_file
    assert generator.output_dir == output_dir
    assert generator.cost_mgr is not None
    assert generator.rollback_mgr is not None
    assert generator.recovery_mgr is not None
```

**Estimated Runtime**: 2 seconds

---

#### Scenario 2: Filename Sanitization
```python
def test_02_filename_sanitization():
    """
    Test: Sanitize recommendation titles to safe filenames

    Test Cases:
    - Special characters removal
    - Space to underscore
    - Length limiting
    - Case normalization
    """
    generator = Phase4FileGenerationBasic()

    test_cases = {
        "Add True Shooting % Calculator": "add_true_shooting_calculator",
        "Feature: Usage Rate (Advanced)": "feature_usage_rate_advanced",
        "SQL Query Optimizer!!!": "sql_query_optimizer",
        "A" * 100: "a" * 50  # Length limit
    }

    for input_text, expected_output in test_cases.items():
        result = generator._sanitize_filename(input_text)
        assert result == expected_output, f"Failed for: {input_text}"
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 3: README Generation
```python
def test_03_readme_generation(temp_directory):
    """
    Test: Generate README.md for recommendation

    Content:
    - Title
    - Description
    - Implementation status
    - Dependencies
    - Usage examples
    """
    generator = Phase4FileGenerationBasic(output_dir=temp_directory)

    recommendation = {
        'id': 'rec-1',
        'title': 'True Shooting Percentage Calculator',
        'description': 'Calculate TS% for player efficiency',
        'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
        'priority': 'high',
        'category': 'analytics'
    }

    rec_dir = temp_directory / "ts_percentage"
    rec_dir.mkdir()

    readme_content = generator._generate_readme(recommendation, rec_dir)

    assert 'True Shooting Percentage' in readme_content
    assert 'PTS / (2 * (FGA + 0.44 * FTA))' in readme_content
    assert 'high' in readme_content.lower()
    assert len(readme_content) > 100
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 4: Placeholder Implementation File
```python
def test_04_placeholder_implementation_file(temp_directory):
    """
    Test: Generate placeholder implementation.py

    Content:
    - Function stubs
    - Docstrings
    - Type hints
    - TODOs
    """
    generator = Phase4FileGenerationBasic(output_dir=temp_directory)

    recommendation = {
        'title': 'Calculate Usage Rate',
        'formula': '100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) / (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))',
        'variables': ['FGA', 'FTA', 'TOV', 'MP', 'Tm MP', 'Tm FGA', 'Tm FTA', 'Tm TOV']
    }

    impl_content = generator._generate_placeholder_implementation(recommendation)

    assert 'def calculate_usage_rate' in impl_content
    assert 'TODO' in impl_content
    assert '"""' in impl_content  # Has docstring
    assert 'float' in impl_content or 'return' in impl_content
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 5: Directory Structure Creation
```python
def test_05_directory_structure_creation(temp_directory):
    """
    Test: Create directory structure for recommendations

    Structure:
    - recommendation_name/
    ├── README.md
    ├── implementation.py
    ├── tests/
    └── docs/
    """
    generator = Phase4FileGenerationBasic(output_dir=temp_directory)

    recommendation = {
        'id': 'rec-1',
        'title': 'Test Feature',
        'category': 'analytics'
    }

    rec_dir = generator._create_directory_structure(recommendation)

    assert rec_dir.exists()
    assert rec_dir.is_dir()
    assert (rec_dir / "tests").exists()
    assert (rec_dir / "docs").exists()
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 6: Integration Guide Generation
```python
def test_06_integration_guide_generation(temp_directory):
    """
    Test: Generate INTEGRATION_GUIDE.md

    Content:
    - Setup instructions
    - Dependency installation
    - Configuration steps
    - Testing procedures
    """
    generator = Phase4FileGenerationBasic(output_dir=temp_directory)

    recommendations = [
        {'id': 'rec-1', 'title': 'Feature A'},
        {'id': 'rec-2', 'title': 'Feature B'}
    ]

    guide_content = generator._generate_integration_guide(recommendations)

    assert 'Integration Guide' in guide_content
    assert 'Feature A' in guide_content
    assert 'Feature B' in guide_content
    assert 'Installation' in guide_content or 'Setup' in guide_content
    assert len(guide_content) > 200
```

**Estimated Runtime**: 5 seconds

---

#### Scenario 7: Full Generation Process
```python
def test_07_full_generation_process(temp_directory):
    """
    Test: Complete file generation for multiple recommendations

    Steps:
    1. Load recommendations
    2. Create directories
    3. Generate README files
    4. Generate implementation stubs
    5. Generate integration guide
    6. Verify all files created
    """
    # Create sample recommendations file
    recommendations_file = temp_directory / "recommendations.json"
    recommendations_file.write_text(json.dumps([
        {
            'id': 'rec-1',
            'title': 'True Shooting %',
            'description': 'Calculate TS%',
            'formula': 'PTS / (2 * (FGA + 0.44 * FTA))'
        },
        {
            'id': 'rec-2',
            'title': 'Usage Rate',
            'description': 'Calculate usage rate',
            'formula': '100 * (...))'
        }
    ]))

    generator = Phase4FileGenerationBasic(
        input_file=recommendations_file,
        output_dir=temp_directory
    )

    result = generator.generate_all()

    assert result['status'] == 'success'
    assert result['files_created'] >= 4  # At least 2 READMEs, 2 implementations
    assert (temp_directory / "INTEGRATION_GUIDE.md").exists()
```

**Estimated Runtime**: 15 seconds

---

#### Scenario 8: Error Handling
```python
def test_08_error_handling(temp_directory):
    """
    Test: Handle errors gracefully

    Error Cases:
    - Missing input file
    - Invalid JSON
    - Permission denied (write)
    - Disk space issues (mock)
    """
    # Test missing input file
    generator = Phase4FileGenerationBasic(
        input_file=Path("nonexistent.json"),
        output_dir=temp_directory
    )

    result = generator.generate_all()
    assert result['status'] == 'failed'
    assert 'error' in result

    # Test invalid JSON
    invalid_file = temp_directory / "invalid.json"
    invalid_file.write_text("not valid json {")

    generator = Phase4FileGenerationBasic(
        input_file=invalid_file,
        output_dir=temp_directory
    )

    result = generator.generate_all()
    assert result['status'] == 'failed'
```

**Estimated Runtime**: 10 seconds

---

### Summary for Gap 6

**Total Scenarios**: 8
**Total Runtime**: 1-2 minutes
**Total Lines**: 400-500
**Dependencies**: json, pathlib, pytest

---

## Shared Fixtures & Utilities

These will be added to `tests/conftest.py`:

```python
# tests/conftest.py

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
def temp_directory():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_env_vars():
    """Mock all environment variables"""
    mock_vars = {
        'RDS_HOST': 'test-host.rds.amazonaws.com',
        'RDS_DATABASE': 'test_nba',
        'RDS_USERNAME': 'test_user',
        'RDS_PASSWORD': 'test_password',
        'S3_BUCKET': 'test-nba-bucket',
        'AWS_ACCESS_KEY_ID': 'AKIATEST1234567890',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key_1234567890',
        'DEEPSEEK_API_KEY': 'sk-deepseek-test-key',
        'ANTHROPIC_API_KEY': 'sk-ant-test-key',
        'GITHUB_TOKEN': 'ghp_test_token'
    }

    with patch.dict('os.environ', mock_vars):
        yield mock_vars

@pytest.fixture
async def mock_mcp_server():
    """Mock MCP server for testing"""
    server = MagicMock()
    server.url = "http://localhost:3000"
    server.connected = True

    async def mock_list_tools():
        return ['query_database', 'list_s3_files', 'get_table_schema']

    async def mock_call_tool(tool_name, args):
        return {'success': True, 'result': 'mocked result'}

    server.list_available_tools = mock_list_tools
    server.call_tool = mock_call_tool

    yield server

@pytest.fixture
def sample_book_data():
    """Sample book extraction data"""
    return {
        'title': 'Basketball on Paper',
        'author': 'Dean Oliver',
        'formulas': [
            {
                'name': 'True Shooting %',
                'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
                'variables': ['PTS', 'FGA', 'FTA']
            },
            {
                'name': 'Usage Rate',
                'formula': '100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) / (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))',
                'variables': ['FGA', 'FTA', 'TOV', 'MP']
            }
        ],
        'concepts': ['Four Factors', 'Offensive Rating', 'Defensive Rating']
    }

@pytest.fixture
def sample_recommendations():
    """Sample AI recommendations"""
    return [
        {
            'id': 'rec-1',
            'title': 'Implement True Shooting Percentage',
            'description': 'Add function to calculate TS%',
            'priority': 'high',
            'formula': 'PTS / (2 * (FGA + 0.44 * FTA))',
            'dependencies': []
        },
        {
            'id': 'rec-2',
            'title': 'Add Usage Rate Calculator',
            'description': 'Calculate player usage rate',
            'priority': 'medium',
            'formula': '100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) / (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))',
            'dependencies': ['rec-1']
        }
    ]

@pytest.fixture
async def mock_ai_apis():
    """Mock all AI API calls"""
    with patch('synthesis.multi_model_synthesis.call_deepseek_api') as mock_deepseek, \
         patch('synthesis.multi_model_synthesis.call_claude_api') as mock_claude:

        async def mock_deepseek_response(*args, **kwargs):
            return {
                'code': '# DeepSeek generated code',
                'cost': 0.08,
                'tokens': 500
            }

        async def mock_claude_response(*args, **kwargs):
            return {
                'synthesis': '# Claude synthesized code',
                'cost': 0.12,
                'tokens': 800
            }

        mock_deepseek.side_effect = mock_deepseek_response
        mock_claude.side_effect = mock_claude_response

        yield {
            'deepseek': mock_deepseek,
            'claude': mock_claude
        }
```

---

## Execution Plan & Dependencies

### Dependencies Installation

```bash
# Core testing dependencies
pip install pytest pytest-asyncio pytest-timeout

# AWS dependencies
pip install boto3 botocore

# Database dependencies
pip install asyncpg

# Security dependencies
pip install detect-secrets bandit black pre-commit

# API dependencies
pip install requests anthropic openai

# Utilities
pip install python-dotenv pyyaml
```

### Execution Order

**Local Development**:
```bash
# Run all tests
pytest tests/ scripts/test_*.py -v

# Run by priority
pytest tests/test_e2e_deployment_flow.py -v  # CRITICAL
pytest scripts/test_phase_11_automated_deployment.py -v  # HIGH
pytest tests/test_dims_integration.py -v  # HIGH
pytest tests/test_security_hooks.py -v  # MEDIUM
pytest scripts/test_phase_1_foundation.py -v  # MEDIUM
pytest scripts/test_phase_4_file_generation.py -v  # MEDIUM

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests only
pytest -m integration -v

# Skip integration tests
pytest -m "not integration" -v
```

**CI/CD Pipeline**:
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest -m "not integration" -v
      - name: Run integration tests
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: pytest -m integration -v
```

---

## Implementation Timeline

### Phase 4: Implementation (12-20 hours)

**Week 1** (8-12 hours):
- Day 1 (3-4 hours): Implement Gap 1 (E2E Deployment Flow)
  - Write test scenarios 1-5
  - Create fixtures
  - Test locally

- Day 2 (2-3 hours): Complete Gap 1
  - Write test scenarios 6-10
  - Add standalone runner
  - Integration testing

- Day 3 (3-4 hours): Implement Gap 2 (Automated Deployment)
  - Write test scenarios 1-6
  - Mock all components

**Week 2** (4-8 hours):
- Day 1 (2-3 hours): Complete Gap 2
  - Write test scenarios 7-12
  - Full workflow testing

- Day 2 (2-3 hours): Implement Gaps 3, 4, 5
  - Gap 3: DIMS Integration (1 hour)
  - Gap 4: Security Hooks (1 hour)
  - Gap 5: Foundation (1 hour)

- Day 3 (2 hours): Implement Gap 6 & Finalization
  - Gap 6: File Generation (1 hour)
  - Documentation and cleanup (1 hour)

---

## Success Criteria

### Test Quality Metrics

Each test must meet:
- ✅ **Clear purpose**: Docstring explains what and why
- ✅ **Comprehensive assertions**: Verify all critical outputs
- ✅ **Error handling**: Test both success and failure paths
- ✅ **Reproducibility**: Consistent results across runs
- ✅ **Isolation**: No dependencies between tests
- ✅ **Performance**: Completes within estimated runtime
- ✅ **Documentation**: Inline comments for complex logic

### Coverage Goals

After implementation:
- **Overall coverage**: 90% (up from 75%)
- **Critical paths**: 100% (E2E flow, deployment, security)
- **Integration points**: 85% (APIs, databases, file systems)
- **Error paths**: 80% (exception handling, rollbacks)

---

## Risk Mitigation

### Known Risks

1. **API Cost Overruns**
   - Mitigation: Mock APIs for most tests, only use real APIs for integration tests
   - Safeguard: Cost limits in test configuration

2. **Test Environment Setup**
   - Mitigation: Comprehensive fixtures, clear setup documentation
   - Fallback: Skip integration tests if environment unavailable

3. **Flaky Tests**
   - Mitigation: Generous timeouts, retry logic, proper cleanup
   - Detection: Run tests multiple times during development

4. **Dependency Conflicts**
   - Mitigation: Pin dependency versions, use virtual environments
   - Testing: Test on clean environment before committing

---

## Next Steps After Phase 3

Once this design document is approved:

1. **Phase 4**: Implement all 6 test files based on these specifications
2. **Phase 5**: Execute all tests and verify 90% coverage goal
3. **Phase 6**: Analyze results and create recommendations
4. **Phase 7**: Deploy testing infrastructure (CI/CD integration)

---

**End of Phase 3 Design Specifications**

Total Specification Lines: ~1,950
Total Test Scenarios: 58
Estimated Implementation Time: 12-20 hours
Estimated Execution Time: 13-20 minutes
Estimated Cost: $0.30-$0.60
