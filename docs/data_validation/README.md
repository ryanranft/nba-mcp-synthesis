# NBA MCP Data Validation System

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**

Complete data validation infrastructure for the NBA MCP Synthesis project.

---

## Overview

This system provides comprehensive data validation, quality checking, profiling, and integrity verification for NBA datasets. It integrates with CI/CD pipelines for automated validation and monitoring.

### Key Components

1. **Data Validation Pipeline** (`mcp_server/data_validation_pipeline.py`)
   - Multi-stage validation (ingestion → schema → quality → business rules)
   - Configurable thresholds and checks
   - Automated reporting and metrics

2. **Data Quality Checker** (`mcp_server/data_quality.py`)
   - 24 Great Expectations-inspired expectation methods
   - Quality score calculation
   - Automated quality reports

3. **Data Cleaning** (`mcp_server/data_cleaning.py`)
   - 3 outlier detection methods (IQR, Z-score, Isolation Forest)
   - 6 imputation strategies
   - 3 scaling methods
   - Duplicate and type handling

4. **Data Profiler** (`mcp_server/data_profiler.py`)
   - Statistical profiling (mean, median, std, skew, kurtosis)
   - Quality metrics calculation
   - 3 drift detection methods (KL divergence, KS test, PSI)
   - NBA-specific templates

5. **Integrity Checker** (`mcp_server/integrity_checker.py`)
   - Referential integrity validation
   - Cross-field mathematical relationships
   - Temporal consistency
   - NBA-specific business rules

---

## Quick Start

### Basic Usage

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
import pandas as pd

# Create sample data
player_data = pd.DataFrame({
    'player_id': [1, 2, 3],
    'player_name': ['Player1', 'Player2', 'Player3'],
    'ppg': [25.0, 28.0, 22.0],
    'games_played': [75, 68, 80],
})

# Configure pipeline
config = PipelineConfig(
    enable_schema_validation=True,
    enable_quality_check=True,
    enable_business_rules=True,
    min_quality_score=0.9,
)

# Run validation
pipeline = DataValidationPipeline(config=config)
result = pipeline.validate(player_data, 'player_stats')

print(f"Passed: {result.passed}")
print(f"Issues: {len(result.issues)}")
```

### Data Cleaning

```python
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy

cleaner = DataCleaner()

# Clean data with defaults
cleaned_df, report = cleaner.clean(
    df,
    remove_outliers=True,
    outlier_method=OutlierMethod.IQR,
    impute_missing=True,
    imputation_strategy=ImputationStrategy.MEDIAN,
    remove_dupes=True,
)

print(f"Rows removed: {report.rows_removed}")
print(f"Outliers: {report.outliers_removed}")
print(f"Missing imputed: {report.missing_values_imputed}")
```

### Data Profiling

```python
from mcp_server.data_profiler import DataProfiler

profiler = DataProfiler()

# Profile NBA player stats
profile = profiler.profile_nba_player_stats(player_data)

print(f"Quality Score: {profile.quality_score:.2%}")
print(f"Columns: {len(profile.columns)}")
```

### Drift Detection

```python
from mcp_server.data_profiler import DataProfiler, DriftMethod

profiler = DataProfiler()

# Detect drift between reference and current data
drift_results = profiler.detect_drift(
    reference_data,
    current_data,
    columns=['ppg', 'rpg', 'apg'],
    method=DriftMethod.KL_DIVERGENCE,
)

for result in drift_results:
    if result.drift_detected:
        print(f"⚠️  Drift detected in {result.column}: {result.drift_score:.4f}")
```

### Integrity Checking

```python
from mcp_server.integrity_checker import IntegrityChecker

checker = IntegrityChecker()

# Check NBA player data integrity
report = checker.check(player_data, 'player_data', checks=['nba_player'])

if not report.passed:
    print(f"Violations: {report.violation_count}")
    for violation in report.violations:
        print(f"  - {violation.message}")
```

---

## CI/CD Integration

### Automated Workflows

Three GitHub Actions workflows automate data validation:

#### 1. Data Quality CI (`.github/workflows/data_quality_ci.yml`)

Triggers on:
- Push/PR to `main` or `develop` with data changes
- Manual dispatch with quality threshold parameter

Runs:
- All data validation tests (74 tests)
- Quality threshold validation
- Coverage reporting

#### 2. Feature Store CI (`.github/workflows/feature_store_ci.yml`)

Triggers on:
- Changes to `feature_store.py`
- Manual dispatch

Runs:
- Feature store tests
- Feature definition validation
- Compatibility checks
- Deployment hook testing

#### 3. Scheduled Data Validation (`.github/workflows/data_validation.yml`)

Triggers on:
- Daily at 2 AM UTC (after data load)
- Manual dispatch with dataset path parameter

Runs:
- Full validation pipeline
- Data profiling
- Drift detection
- Integrity checks
- Uploads validation results as artifacts

### Manual Trigger

```bash
# Trigger data quality CI with custom threshold
gh workflow run data_quality_ci.yml -f quality_threshold=0.95

# Trigger scheduled validation with custom dataset
gh workflow run data_validation.yml -f dataset_path=data/player_stats.csv -f enable_profiling=true
```

---

## Great Expectations Integration

### Expectation Suites

Three pre-configured expectation suites are available:

1. **Player Stats Suite** (`great_expectations/expectations/player_stats_suite.json`)
   - 19 expectations covering player statistics
   - Validates PPG, RPG, APG, FG%, games played
   - Ensures reasonable ranges and distributions

2. **Game Data Suite** (`great_expectations/expectations/game_data_suite.json`)
   - 15 expectations for game data
   - Validates scores, dates, teams
   - Checks for reasonable score ranges (50-200)

3. **Team Data Suite** (`great_expectations/expectations/team_data_suite.json`)
   - 16 expectations for team data
   - Validates wins, losses, win percentage
   - Ensures exactly 30 teams
   - Checks conference values (East/West)

### Using Great Expectations

```python
import great_expectations as gx

context = gx.get_context()

# Load expectation suite
suite = context.get_expectation_suite("player_stats_suite")

# Validate data
results = context.run_validation_operator(
    "action_list_operator",
    assets_to_validate=[player_data],
    expectation_suite_name="player_stats_suite",
)

print(f"Success: {results.success}")
```

### Python Integration Module (NEW - Phase 4)

A simplified Python API for Great Expectations:

```python
from mcp_server.ge_integration import GreatExpectationsIntegration

# Initialize integration
ge = GreatExpectationsIntegration()

# Run a checkpoint
result = ge.run_checkpoint("player_stats_checkpoint")

# Check results
if result.success:
    print(f"✅ Validation passed: {result.pass_rate:.1%}")
    print(f"Expectations: {result.passed_expectations}/{result.total_expectations}")
else:
    print(f"❌ Validation failed")
    print(f"Failed expectations: {result.failed_expectations}")
    for detail in result.failed_expectation_details:
        print(f"  - {detail['expectation_type']}")

# Run all checkpoints
all_results = ge.run_all_checkpoints()

# Aggregate results
aggregate = ge.aggregate_results(all_results)
print(f"Overall pass rate: {aggregate['overall_pass_rate']:.1%}")
```

### Available Checkpoints (NEW - Phase 4)

Three pre-configured checkpoints are available:

1. **`player_stats_checkpoint`** - Player statistics validation
   - Validates completeness, ranges, distributions
   - Daily schedule: 2 AM UTC
   - Slack notifications on failure

2. **`game_data_checkpoint`** - Game data validation
   - Validates scores, dates, team references
   - Hourly during game days
   - Email on critical failures

3. **`team_data_checkpoint`** - Team metadata validation
   - Validates 30 NBA teams
   - Daily schedule: 3 AM UTC
   - High threshold (95%) due to static nature

**See [ADVANCED_TOPICS.md](ADVANCED_TOPICS.md) for custom checkpoint creation and advanced patterns.
```

---

## Test Coverage

### Test Suites

All modules have comprehensive test coverage:

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| data_validation_pipeline.py | 20 | 95%+ | ✅ |
| data_cleaning.py | 18 | 95%+ | ✅ |
| data_profiler.py | 18 | 95%+ | ✅ |
| integrity_checker.py | 18 | 95%+ | ✅ |
| **Total** | **74** | **95%+** | ✅ |

### Running Tests

```bash
# Run all data validation tests
pytest tests/test_data_validation_pipeline.py tests/test_data_cleaning.py tests/test_data_profiler.py tests/test_integrity_checker.py -v

# Run with coverage
pytest tests/test_data_*.py --cov=mcp_server --cov-report=html

# Run specific module tests
pytest tests/test_data_profiler.py -v
```

---

## Configuration

### Pipeline Configuration

```python
from mcp_server.data_validation_pipeline import PipelineConfig

config = PipelineConfig(
    # Stage enablement
    enable_schema_validation=True,
    enable_quality_check=True,
    enable_business_rules=True,
    enable_profiling=False,

    # Quality thresholds
    min_quality_score=0.9,
    max_null_percentage=0.05,
    max_duplicate_percentage=0.01,

    # NBA-specific thresholds
    max_points_per_game=200.0,
    max_field_goal_percentage=1.0,

    # Pipeline behavior
    fail_on_critical=True,
    fail_on_error=False,
    continue_on_warning=True,

    # Output settings
    save_results=True,
    output_dir=Path("validation_results"),
)
```

---

## NBA-Specific Features

### Player Stats Validation

- Field goal percentage calculation (FGM / FGA = FG%)
- Points calculation (PPG × Games = Total Points)
- Games played range (0-82)
- Minutes per game range (0-48)

### Game Data Validation

- Home and away teams must be different
- Scores must be non-negative
- Dates must be valid and within NBA history (1946-present)
- Scores typically range 80-130 (allows 50-200)

### Team Data Validation

- Win percentage calculation (Wins / (Wins + Losses))
- Exactly 30 teams expected
- Valid conference values (East/West)
- Wins and losses range (0-82)

---

## Monitoring & Metrics

### Week 1 Integration

All modules integrate with Week 1's monitoring infrastructure:

```python
from mcp_server.monitoring import get_health_monitor

monitor = get_health_monitor()

# Metrics tracked automatically:
# - validation.{dataset}.passed
# - validation.{dataset}.duration_seconds
# - validation.{dataset}.critical_issues
# - data_cleaning.outliers_removed
# - profiling.{dataset}.quality_score
# - integrity.{dataset}.violations
```

### Quality Metrics

- **Completeness**: Inverse of null percentage
- **Uniqueness**: Average unique ratio across columns
- **Quality Score**: Combined metric (0.0-1.0)
- **Drift Score**: KL divergence, KS statistic, or PSI value

---

## Best Practices

### 1. Run Validation Early

```python
# Validate data immediately after loading
result = pipeline.validate(df, 'dataset_name')
if not result.passed:
    raise ValueError(f"Validation failed: {len(result.critical_issues)} critical issues")
```

### 2. Profile Before and After Cleaning

```python
# Profile before cleaning
profile_before = profiler.profile(df, 'before_cleaning')

# Clean data
cleaned_df, report = cleaner.clean(df)

# Profile after cleaning
profile_after = profiler.profile(cleaned_df, 'after_cleaning')

print(f"Quality improvement: {profile_after.quality_score - profile_before.quality_score:.2%}")
```

### 3. Monitor Drift Continuously

```python
# Store reference profile
reference_profile = profiler.profile(reference_data, 'reference')

# Check drift regularly
drift_results = profiler.detect_drift(reference_data, current_data)

if any(r.drift_detected for r in drift_results):
    # Alert or retrain model
    send_alert("Data drift detected!")
```

### 4. Use Integrity Checks in Production

```python
# Before processing data in production
integrity_report = checker.check(df, 'production_data', checks=['nba_player'])

if not integrity_report.passed:
    # Log violations and reject data
    logger.error(f"Integrity violations: {integrity_report.violation_count}")
    raise DataIntegrityError("Data failed integrity checks")
```

---

## Troubleshooting

### Common Issues

**Issue**: Validation fails with "Missing column"
**Solution**: Check schema definition matches actual data columns

**Issue**: High drift scores on identical data
**Solution**: Use same random seed or identical data copies for testing

**Issue**: Integrity checks fail for valid data
**Solution**: Adjust business rule thresholds in configuration

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Run validation with debug logging
result = pipeline.validate(df, 'test_data')
```

---

## API Reference

See individual module documentation:
- [Data Validation Pipeline](../../mcp_server/data_validation_pipeline.py)
- [Data Quality](../../mcp_server/data_quality.py)
- [Data Cleaning](../../mcp_server/data_cleaning.py)
- [Data Profiler](../../mcp_server/data_profiler.py)
- [Integrity Checker](../../mcp_server/integrity_checker.py)

---

## Contributing

When adding new validation rules:

1. Add expectation method to appropriate module
2. Write comprehensive tests
3. Update expectation suite JSON
4. Document in this README
5. Test in CI/CD pipeline

---

## License

Part of the NBA MCP Synthesis project.

---

**Last Updated**: October 25, 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
