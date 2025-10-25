# Advanced Topics - NBA MCP Data Validation

**Phase 10A Week 2 - Agent 4: Advanced Integrations**

Complete guide to advanced data validation topics including Great Expectations integration, custom patterns, and production deployment.

---

## Table of Contents

1. [Great Expectations Integration](#great-expectations-integration)
2. [Custom Checkpoint Creation](#custom-checkpoint-creation)
3. [Advanced Validation Patterns](#advanced-validation-patterns)
4. [Performance Optimization](#performance-optimization)
5. [Distributed Validation](#distributed-validation)
6. [Custom Expectations](#custom-expectations)
7. [Integration Patterns](#integration-patterns)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Great Expectations Integration

### Quick Start

```python
from mcp_server.ge_integration import GreatExpectationsIntegration

# Initialize integration
ge = GreatExpectationsIntegration()

# Run a checkpoint
result = ge.run_checkpoint("player_stats_checkpoint")

# Check results
if result.success:
    print(f"✅ Validation passed: {result.pass_rate:.1%}")
else:
    print(f"❌ Validation failed: {result.failed_expectations} expectations failed")
```

### Available Checkpoints

1. **`player_stats_checkpoint`** - NBA player statistics validation
2. **`game_data_checkpoint`** - Game data validation
3. **`team_data_checkpoint`** - Team metadata validation

### Running All Checkpoints

```python
# Run all checkpoints
results = ge.run_all_checkpoints()

# Aggregate results
aggregate = ge.aggregate_results(results)

print(f"Overall pass rate: {aggregate['overall_pass_rate']:.1%}")
print(f"Total expectations: {aggregate['total_expectations']}")
print(f"Passed: {aggregate['passed_expectations']}")
print(f"Failed: {aggregate['failed_expectations']}")
```

### Checkpoint Configuration

Checkpoints are defined in YAML files under `great_expectations/checkpoints/`:

```yaml
name: custom_checkpoint
config_version: 1.0
class_name: SimpleCheckpoint

validations:
  - batch_request:
      datasource_name: nba_postgres
      data_asset_name: your_table
    expectation_suite_name: your_suite

action_list:
  - name: store_validation_result
  - name: update_data_docs
  - name: send_slack_notification_on_validation_result
```

---

## Custom Checkpoint Creation

### Step 1: Create Expectation Suite

```python
# Create custom expectations
import great_expectations as gx

context = gx.get_context()

# Create suite
suite = context.add_expectation_suite("custom_suite")

# Add expectations
suite.add_expectation(
    expectation_configuration={
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "player_id"},
    }
)

# Save suite
context.save_expectation_suite(suite)
```

### Step 2: Create Checkpoint YAML

```yaml
# great_expectations/checkpoints/custom_checkpoint.yml
name: custom_checkpoint
config_version: 1.0
class_name: SimpleCheckpoint

validations:
  - batch_request:
      datasource_name: nba_postgres
      data_asset_name: my_custom_table
    expectation_suite_name: custom_suite
```

### Step 3: Run Custom Checkpoint

```python
from mcp_server.ge_integration import GreatExpectationsIntegration

ge = GreatExpectationsIntegration()
result = ge.run_checkpoint("custom_checkpoint")
```

---

## Advanced Validation Patterns

### Pattern 1: Multi-Stage Validation

Validate data through multiple stages with increasing rigor:

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig

# Configure multi-stage pipeline
config = PipelineConfig(
    enable_quality_checks=True,
    enable_profiling=True,
    enable_integrity_checks=True,
    quality_threshold=0.95,
)

pipeline = DataValidationPipeline(config=config)

# Run validation
result = pipeline.validate(data=df, dataset_name="player_stats")

# Check each stage
for stage in result.stage_results:
    print(f"{stage.stage_name}: {stage.status}")
```

### Pattern 2: Progressive Validation

Start with basic checks, add complexity:

```python
# Stage 1: Basic checks
basic_result = pipeline.validate_ingestion(df)

if basic_result.passed:
    # Stage 2: Schema validation
    schema_result = pipeline.validate_schema(df)

    if schema_result.passed:
        # Stage 3: Quality checks
        quality_result = pipeline.validate_quality(df)
```

### Pattern 3: Conditional Validation

Validate based on data characteristics:

```python
# Profile first
profiler = DataProfiler()
profile = profiler.profile_dataset(df, "player_stats")

# Conditional validation based on profile
if profile.row_count > 10000:
    # Use sampling for large datasets
    sample = df.sample(n=1000)
    result = pipeline.validate(sample, "player_stats_sample")
else:
    # Validate full dataset
    result = pipeline.validate(df, "player_stats")
```

---

## Performance Optimization

### Optimization 1: Sampling Large Datasets

```python
# Sample large datasets before validation
if len(df) > 100000:
    sample_df = df.sample(n=10000, random_state=42)
    result = pipeline.validate(sample_df, "large_dataset_sample")
```

### Optimization 2: Parallel Validation

```python
import concurrent.futures

def validate_dataset(dataset_info):
    name, df = dataset_info
    return pipeline.validate(df, name)

# Validate multiple datasets in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    datasets = [("ds1", df1), ("ds2", df2), ("ds3", df3)]
    results = list(executor.map(validate_dataset, datasets))
```

### Optimization 3: Caching Validation Results

```python
from functools import lru_cache
import hashlib

def get_dataframe_hash(df):
    """Generate hash of dataframe for caching"""
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()

@lru_cache(maxsize=100)
def cached_validation(df_hash, dataset_name):
    """Cached validation (use with caution)"""
    # Validation logic here
    pass
```

---

## Distributed Validation

### Using Dask for Large-Scale Validation

```python
import dask.dataframe as dd

# Load large dataset with Dask
dask_df = dd.read_csv("large_dataset.csv")

# Validate partitions
def validate_partition(partition_df):
    return pipeline.validate(partition_df, "partition")

# Map validation across partitions
results = dask_df.map_partitions(validate_partition).compute()
```

### AWS Glue Integration

```python
# Validate data in AWS Glue job
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Initialize
sc = SparkContext()
glueContext = GlueContext(sc)

# Read data
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="nba_data",
    table_name="player_stats"
)

# Convert to pandas for validation
df = datasource.toDF().toPandas()

# Validate
result = pipeline.validate(df, "glue_player_stats")
```

---

## Custom Expectations

### Creating Custom NBA Expectations

```python
from great_expectations.expectations import ExpectationConfiguration

class ExpectNBAPlayerStats:
    """Custom expectations for NBA player statistics"""

    @staticmethod
    def expect_valid_field_goal_percentage(column):
        """FG% should be between 0 and 1"""
        return ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": column,
                "min_value": 0.0,
                "max_value": 1.0,
            }
        )

    @staticmethod
    def expect_valid_ppg(column):
        """PPG should be between 0 and 50"""
        return ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": column,
                "min_value": 0.0,
                "max_value": 50.0,
            }
        )

# Use custom expectations
suite.add_expectation(
    ExpectNBAPlayerStats.expect_valid_field_goal_percentage("fg_pct")
)
```

---

## Integration Patterns

### Pattern 1: CI/CD Integration

```yaml
# .github/workflows/data_validation.yml
name: Data Validation

on:
  push:
    branches: [main]
  schedule:
    - cron: "0 2 * * *"  # Daily at 2 AM UTC

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run Data Validation
        run: |
          python -m mcp_server.ge_integration run_all_checkpoints

      - name: Check Results
        run: |
          # Fail if validation failed
          if [ $? -ne 0 ]; then
            echo "Data validation failed!"
            exit 1
          fi
```

### Pattern 2: Real-Time Validation

```python
# Validate data as it arrives
from flask import Flask, request, jsonify

app = Flask(__name__)
pipeline = DataValidationPipeline()

@app.route("/validate", methods=["POST"])
def validate_data():
    """API endpoint for real-time validation"""
    data = request.json
    df = pd.DataFrame(data)

    result = pipeline.validate(df, "realtime_data")

    return jsonify({
        "status": result.validation_status,
        "pass_rate": result.pass_rate,
        "failed_checks": result.failed_checks,
    })
```

### Pattern 3: Scheduled Validation

```python
from apscheduler.schedulers.background import BackgroundScheduler

def scheduled_validation():
    """Run validation on schedule"""
    ge = GreatExpectationsIntegration()
    results = ge.run_all_checkpoints()

    # Send alerts if failures
    for result in results:
        if not result.success:
            send_alert(f"Validation failed: {result.checkpoint_name}")

# Schedule daily validation
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_validation, 'cron', hour=2)
scheduler.start()
```

---

## Troubleshooting Guide

### Issue 1: Great Expectations Not Found

**Symptom:** `ModuleNotFoundError: No module named 'great_expectations'`

**Solution:**
```bash
pip install great-expectations
```

### Issue 2: Checkpoint Not Found

**Symptom:** `DataValidationError: Checkpoint 'xyz' not found`

**Solution:**
1. Verify checkpoint exists: `ls great_expectations/checkpoints/`
2. Check file name matches: `xyz.yml`
3. Reload integration: `ge = GreatExpectationsIntegration()`

### Issue 3: Low Validation Pass Rate

**Symptom:** Unexpectedly low pass rates

**Solution:**
1. Check failed expectation details:
```python
result = ge.run_checkpoint("player_stats_checkpoint")

for detail in result.failed_expectation_details:
    print(f"Failed: {detail['expectation_type']}")
    print(f"Kwargs: {detail['kwargs']}")
```

2. Adjust thresholds in checkpoint YAML or expectations
3. Profile data to understand distributions

### Issue 4: Slow Validation Performance

**Symptom:** Validation taking too long

**Solutions:**
1. **Sample large datasets:**
```python
if len(df) > 100000:
    df = df.sample(n=10000)
```

2. **Disable unnecessary checks:**
```python
config = PipelineConfig(
    enable_profiling=False,  # Disable if not needed
    enable_integrity_checks=False,
)
```

3. **Use parallel validation** (see Performance Optimization section)

### Issue 5: Memory Issues with Large Datasets

**Symptom:** `MemoryError` or OOM kills

**Solutions:**
1. **Process in chunks:**
```python
for chunk in pd.read_csv("large_file.csv", chunksize=10000):
    result = pipeline.validate(chunk, "chunk")
```

2. **Use Dask** for distributed processing
3. **Increase system memory** or **use cloud resources**

---

## Best Practices

1. **Start Simple**: Begin with basic checks, add complexity incrementally
2. **Version Control**: Store expectation suites and checkpoints in git
3. **Monitor Trends**: Track validation pass rates over time
4. **Alert Appropriately**: Don't alert on every warning, only critical failures
5. **Document Expectations**: Add metadata to explain why each check exists
6. **Test Your Validations**: Write tests for your validation logic
7. **Review Regularly**: Periodically review and update validation rules
8. **Use Data Profiling**: Profile first to understand data before adding checks

---

## Additional Resources

- [Great Expectations Documentation](https://docs.greatexpectations.io/)
- [Main README](README.md) - Basic usage guide
- [Integration Tests](../../tests/integration/test_full_validation_pipeline.py) - Examples
- [Checkpoint Examples](../../great_expectations/checkpoints/) - YAML templates

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
**Phase:** 10A Week 2 - Agent 4
