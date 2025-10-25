# Data Validation Workflow Patterns

**Phase 10A Week 2 - Agent 4 - Phase 5: Extended Testing**

Common workflow patterns and best practices for NBA MCP data validation.

---

## Table of Contents

1. [Overview](#overview)
2. [Basic Workflows](#basic-workflows)
3. [Advanced Workflows](#advanced-workflows)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Integration Patterns](#integration-patterns)
6. [Best Practices](#best-practices)

---

## Overview

This document describes common patterns for using the data validation infrastructure in production scenarios.

### Common Use Cases

- **Data ingestion validation**: Validate incoming data before storage
- **ETL pipeline quality gates**: Ensure data quality between pipeline stages
- **CI/CD data checks**: Automated validation in deployment workflows
- **Scheduled data audits**: Regular quality monitoring
- **Manual data exploration**: Interactive validation during analysis

---

## Basic Workflows

### Pattern 1: Simple Validation

**Use Case**: Quick validation of incoming data

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline
import pandas as df

# Load data
df = pd.read_csv('player_stats.csv')

# Validate
pipeline = DataValidationPipeline()
result = pipeline.validate(df, 'player_stats')

# Check result
if result.passed:
    print("✓ Validation passed")
    # Proceed with data
else:
    print(f"✗ Validation failed: {len(result.issues)} issues")
    # Handle errors
```

### Pattern 2: Validation with Cleaning

**Use Case**: Clean data before validation for better quality

```python
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_validation_pipeline import DataValidationPipeline

# Clean data first
cleaner = DataCleaner()
cleaned_df, report = cleaner.clean(
    df,
    remove_outliers=True,
    outlier_method=OutlierMethod.IQR,
    impute_missing=True,
    imputation_strategy=ImputationStrategy.MEDIAN,
)

# Then validate
pipeline = DataValidationPipeline()
result = pipeline.validate(cleaned_df, 'player_stats')
```

### Pattern 3: Validation with Profiling

**Use Case**: Understand data characteristics before validation

```python
from mcp_server.data_profiler import DataProfiler
from mcp_server.data_validation_pipeline import DataValidationPipeline

# Profile data
profiler = DataProfiler()
profile = profiler.profile(df)

# Check quality score
quality_score = profiler.calculate_quality_score(df)
print(f"Quality Score: {quality_score:.2%}")

# Validate if quality acceptable
if quality_score >= 0.85:
    pipeline = DataValidationPipeline()
    result = pipeline.validate(df, 'player_stats')
```

---

## Advanced Workflows

### Pattern 4: Multi-Stage Validation

**Use Case**: Progressive validation with checkpoints

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig

# Configure pipeline stages
config = PipelineConfig(
    enable_schema_validation=True,
    enable_quality_check=True,
    enable_business_rules=True,
    enable_profiling=True,
    min_quality_score=0.90,
)

pipeline = DataValidationPipeline(config=config)

# Validate
result = pipeline.validate(df, 'player_stats')

# Check each stage
print(f"Final Stage: {result.current_stage.value}")
print(f"Quality Score: {result.quality_score:.2%}")
print(f"Issues: {len(result.issues)}")
```

### Pattern 5: Batch Processing

**Use Case**: Validate large datasets in chunks

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline

pipeline = DataValidationPipeline()

# Process in batches
batch_size = 50_000
results = []

for i in range(0, len(large_df), batch_size):
    batch = large_df.iloc[i:i+batch_size]
    result = pipeline.validate(batch, 'player_stats')
    results.append(result)

    print(f"Batch {i//batch_size + 1}: {result.quality_score:.2%}")

# Aggregate results
all_passed = all(r.passed for r in results)
avg_quality = sum(r.quality_score for r in results) / len(results)
```

### Pattern 6: Conditional Validation

**Use Case**: Different validation rules based on data characteristics

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig

# Determine validation strictness based on data
if df['season'].max() >= 2024:
    # Stricter validation for recent data
    config = PipelineConfig(min_quality_score=0.95)
else:
    # Relaxed validation for historical data
    config = PipelineConfig(min_quality_score=0.85)

pipeline = DataValidationPipeline(config=config)
result = pipeline.validate(df, 'player_stats')
```

---

## Error Handling Patterns

### Pattern 7: Graceful Degradation

**Use Case**: Continue processing even if validation fails

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline

pipeline = DataValidationPipeline()

try:
    result = pipeline.validate(df, 'player_stats')

    if result.passed:
        # Full validation passed - use all data
        process_data(df)
    else:
        # Partial failure - filter to valid rows only
        valid_df = filter_valid_rows(df, result.issues)
        process_data(valid_df)

except Exception as e:
    # Catastrophic failure - log and skip
    logger.error(f"Validation failed: {e}")
    # Alert monitoring
    send_alert("Data validation error", str(e))
```

### Pattern 8: Retry with Fallback

**Use Case**: Retry validation with relaxed criteria

```python
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig

# Try strict validation
strict_config = PipelineConfig(min_quality_score=0.95)
pipeline = DataValidationPipeline(config=strict_config)
result = pipeline.validate(df, 'player_stats')

if not result.passed:
    # Retry with relaxed criteria
    relaxed_config = PipelineConfig(min_quality_score=0.85)
    pipeline = DataValidationPipeline(config=relaxed_config)
    result = pipeline.validate(df, 'player_stats')

    if result.passed:
        logger.warning("Passed with relaxed criteria")
    else:
        logger.error("Failed even with relaxed criteria")
```

---

## Integration Patterns

### Pattern 9: CI/CD Integration

**Use Case**: Automated validation in GitHub Actions

```python
# validate_data.py
import sys
from mcp_server.data_validation_pipeline import DataValidationPipeline

def main():
    df = load_data()
    pipeline = DataValidationPipeline()
    result = pipeline.validate(df, 'player_stats')

    # Print results for CI
    print(f"::set-output name=quality_score::{result.quality_score:.2%}")
    print(f"::set-output name=issues::{len(result.issues)}")

    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)

if __name__ == "__main__":
    main()
```

```yaml
# .github/workflows/validate_data.yml
name: Data Validation

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate data
        id: validate
        run: python validate_data.py
      - name: Comment PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Data validation failed. Quality score: ${{ steps.validate.outputs.quality_score }}'
            })
```

### Pattern 10: Airflow Integration

**Use Case**: Data validation in Apache Airflow DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from mcp_server.data_validation_pipeline import DataValidationPipeline

def validate_data_task(**context):
    # Load data from XCom or external source
    df = context['task_instance'].xcom_pull(task_ids='load_data')

    # Validate
    pipeline = DataValidationPipeline()
    result = pipeline.validate(df, 'player_stats')

    # Push results to XCom
    context['task_instance'].xcom_push(key='validation_result', value={
        'passed': result.passed,
        'quality_score': result.quality_score,
        'issues': len(result.issues)
    })

    # Fail task if validation failed
    if not result.passed:
        raise ValueError(f"Validation failed: {len(result.issues)} issues")

with DAG('nba_data_pipeline', ...) as dag:
    load = PythonOperator(task_id='load_data', ...)
    validate = PythonOperator(task_id='validate_data', python_callable=validate_data_task)
    process = PythonOperator(task_id='process_data', ...)

    load >> validate >> process
```

---

## Best Practices

### 1. Always Validate Before Storage

```python
# Good
result = pipeline.validate(df, 'player_stats')
if result.passed:
    df.to_sql('player_stats', engine)
else:
    logger.error(f"Validation failed: {len(result.issues)} issues")

# Bad
df.to_sql('player_stats', engine)  # No validation!
```

### 2. Log Validation Results

```python
import logging

logger = logging.getLogger(__name__)

result = pipeline.validate(df, 'player_stats')

logger.info(f"Validation complete: passed={result.passed}, "
            f"quality={result.quality_score:.2%}, "
            f"issues={len(result.issues)}")

if result.issues:
    logger.warning(f"Issues found: {result.issues[:5]}")  # Log first 5
```

### 3. Monitor Quality Over Time

```python
from datetime import datetime
import json

# Track quality metrics
metrics = {
    'timestamp': datetime.now().isoformat(),
    'dataset_size': len(df),
    'quality_score': result.quality_score,
    'validation_passed': result.passed,
    'issues_count': len(result.issues),
}

# Store for trending
with open('validation_metrics.jsonl', 'a') as f:
    f.write(json.dumps(metrics) + '\n')
```

### 4. Cache Validation Results

```python
import hashlib
import json

def get_dataframe_hash(df):
    """Get deterministic hash of DataFrame"""
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()

def validate_with_cache(df, dataset_type):
    df_hash = get_dataframe_hash(df)
    cache_key = f"validation_{dataset_type}_{df_hash}"

    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # Validate
    pipeline = DataValidationPipeline()
    result = pipeline.validate(df, dataset_type)

    # Cache result
    cache.set(cache_key, result, timeout=3600)
    return result
```

### 5. Use Configuration Files

```yaml
# validation_config.yaml
validation:
  player_stats:
    enable_schema_validation: true
    enable_quality_check: true
    enable_business_rules: true
    min_quality_score: 0.90

  game_data:
    enable_schema_validation: true
    enable_quality_check: true
    enable_business_rules: false
    min_quality_score: 0.85
```

```python
import yaml
from mcp_server.data_validation_pipeline import PipelineConfig, DataValidationPipeline

# Load config
with open('validation_config.yaml') as f:
    config_data = yaml.safe_load(f)

# Create pipeline
dataset_type = 'player_stats'
config_dict = config_data['validation'][dataset_type]
config = PipelineConfig(**config_dict)
pipeline = DataValidationPipeline(config=config)
```

---

**Last Updated**: 2025-10-25
**Version**: 1.0.0
**Contact**: NBA MCP Synthesis Team
