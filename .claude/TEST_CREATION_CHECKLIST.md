# Test Creation Checklist for Claude Code

## MANDATORY: Check Before Creating New Tests

Before creating any new test file or adding tests to existing files, **ALWAYS** follow this checklist:

## Step 1: Identify Duplicate Tests

```bash
# Check for duplicate test names across all test files
grep -h "def test_" tests/test_*.py | sed 's/.*def //' | sed 's/(.*$//' | sort | uniq -d

# If any duplicates are found, DO NOT create new test file
# Instead, add tests to the existing file that contains related tests
```

## Step 2: Determine Correct Test File Location

### Integration Tests → `tests/test_econometric_integration_workflows.py`
**Use when**: Testing complete workflows across multiple modules
- End-to-end pipelines
- Cross-module interactions
- Data flow validation
- Suite integration testing

**Current Test Classes**:
- TestCrossModuleWorkflows
- TestEconometricSuiteIntegration
- TestDataFlowValidation
- TestErrorHandlingEdgeCases
- TestPlayerPerformancePipeline
- TestTeamStrategyPipeline
- TestPanelDataPipeline
- TestEnsembleForecastingPipeline
- TestCrossMethodIntegration
- TestPipelineRobustness

### Unit Tests → `tests/test_<module_name>.py`
**Use when**: Testing individual module functionality
- Single function/method testing
- Module-specific edge cases
- Isolated component validation

### Database Tests → `tests/test_database_integration.py`
**Use when**: Testing database connectivity and operations

### Notebook Tests → `tests/notebooks/test_notebook_execution.py`
**Use when**: Testing Jupyter notebook execution

## Step 3: Check for Similar Fixtures

```bash
# Find existing fixtures that might be reusable
grep -n "@pytest.fixture" tests/test_econometric_integration_workflows.py

# Common fixtures already available:
# - time_series_data
# - panel_data
# - survival_data
# - causal_data
# - player_stats_data
# - team_games_data
```

**DO NOT** create duplicate fixtures. Reuse existing ones or consolidate if similar.

## Step 4: Verify Test Naming Conventions

Test names should be:
- ✅ Descriptive: `test_complete_player_analysis_pipeline`
- ✅ Specific: `test_arima_forecast_with_exogenous_variables`
- ✅ Unique: No duplicates across entire test suite
- ❌ Generic: `test_basic`, `test_simple`, `test_1`

## Step 5: Check Test Organization

**Before adding tests, verify**:
```bash
# Count tests per file to ensure no file is too large
wc -l tests/test_*.py

# Target: Keep integration test file under 2000 lines
# If approaching limit, consider splitting by functional area
```

## Step 6: Run Duplicate Detection Script

```bash
# Use this command to check for any potential issues
python << 'EOF'
import os
from collections import defaultdict

test_names = defaultdict(list)
for root, dirs, files in os.walk('tests'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath) as f:
                for line in f:
                    if 'def test_' in line:
                        name = line.split('def ')[1].split('(')[0]
                        test_names[name].append(filepath)

duplicates = {k: v for k, v in test_names.items() if len(v) > 1}
if duplicates:
    print("DUPLICATES FOUND:")
    for name, files in duplicates.items():
        print(f"  {name}:")
        for f in files:
            print(f"    - {f}")
else:
    print("✓ No duplicate test names found")
EOF
```

## Step 7: Validate Before Committing

```bash
# Always run the affected test file before committing
pytest tests/test_econometric_integration_workflows.py -v

# Verify no regressions
pytest tests/ -k "integration" --tb=short
```

## Common Mistakes to Avoid

### ❌ DON'T: Create separate E2E test file
```python
# BAD: Creating tests/test_e2e_pipelines.py
# This creates maintenance overhead and duplicate test execution
```

### ✅ DO: Add to existing integration file
```python
# GOOD: Add new test class to tests/test_econometric_integration_workflows.py
class TestNewIntegrationScenario:
    """Add to existing file with clear documentation"""
    def test_new_workflow(self):
        ...
```

### ❌ DON'T: Duplicate fixtures
```python
# BAD: Creating same fixture in multiple files
@pytest.fixture
def player_stats_data():  # Already exists elsewhere!
    ...
```

### ✅ DO: Reuse or consolidate fixtures
```python
# GOOD: Import from conftest.py or reuse existing fixture
from tests.test_econometric_integration_workflows import player_stats_data
```

### ❌ DON'T: Create generic test names
```python
# BAD: Unclear what this tests
def test_pipeline():
    ...
```

### ✅ DO: Use descriptive names
```python
# GOOD: Clear and specific
def test_player_performance_arima_forecast_pipeline():
    ...
```

## Test File Size Guidelines

- **Unit tests**: 200-500 lines per module
- **Integration tests**: 1000-2000 lines (consolidated file)
- **E2E tests**: Include in integration file, not separate

If integration file exceeds 2000 lines, consider splitting by:
- Functional area (time series, causal, panel)
- Complexity (basic workflows, advanced workflows)
- Speed (fast tests, slow tests)

## Pre-Merge Checklist

Before merging any test PR:

- [ ] Ran duplicate detection script
- [ ] Verified no duplicate test names
- [ ] Reused existing fixtures where possible
- [ ] Followed naming conventions
- [ ] All tests passing locally
- [ ] Test execution time is reasonable (<30s for integration suite)
- [ ] Documentation updated if needed

## Quick Reference Commands

```bash
# Check for duplicate test names
grep -rh "def test_" tests/ | sort | uniq -d

# List all test files and line counts
wc -l tests/test_*.py

# Run specific test file
pytest tests/test_econometric_integration_workflows.py -v

# Run with test name pattern
pytest tests/ -k "player_performance" -v

# Get test count per file
for f in tests/test_*.py; do echo "$f: $(grep -c 'def test_' $f)"; done
```

## Summary: The Golden Rule

**Before creating any new test:**
1. Check for duplicates (name and functionality)
2. Add to existing integration file if it's an integration/E2E test
3. Reuse fixtures
4. Use descriptive names
5. Run the test suite to verify

**Remember**: One comprehensive integration test file is better than many scattered files!
