# Configuration Guide

## Overview

The NBA MCP Synthesis workflows use a centralized YAML configuration file for all settings.

**Config File:** `config/workflow_config.yaml`
**Loader:** `scripts/config_loader.py`

---

## Quick Start

### Using Configuration in Scripts

```python
from config_loader import ConfigLoader

# Load configuration
config = ConfigLoader()

# Get cost limit
limit = config.get_cost_limit('phase_2_analysis')
print(f"Phase 2 limit: ${limit:.2f}")

# Get model config
model_name = config.get_model_config('gemini', 'model_name')
print(f"Using model: {model_name}")

# Check feature flag
if config.is_feature_enabled('intelligent_plan_editor'):
    # Use advanced feature
    pass
```

### Environment Variable Overrides

```bash
# Override workflow mode
export NBA_MCP_WORKFLOW_MODE=A

# Override cost limit
export NBA_MCP_COST_LIMITS_TOTAL_WORKFLOW=100.00

# Override model name
export NBA_MCP_MODELS_GEMINI_MODEL_NAME=gemini-1.5-pro

# Run script (will use overrides)
python scripts/run_full_workflow.py --book "Machine Learning"
```

---

## Configuration Sections

### 1. Workflow Settings

```yaml
workflow:
  mode: B                          # A, B, or dual
  auto_implement: false            # Full automation (Tier 2+)
  prediction_enhancements: false   # BeyondMLR analysis (Tier 2+)
  test_book_limit: 1              # Books to analyze in test mode
  default_dry_run: false          # Enable dry-run by default
```

**Access:**
```python
mode = config.get_workflow_mode()
is_dry_run = config.is_dry_run_default()
```

---

### 2. Cost Limits

```yaml
cost_limits:
  phase_2_analysis: 30.00
  phase_3_synthesis: 20.00
  phase_3_5_modifications: 15.00
  phase_5_predictions: 10.00
  total_workflow: 75.00
  approval_threshold: 10.00
```

**Access:**
```python
limit = config.get_cost_limit('phase_2_analysis')
total = config.get_cost_limit('total_workflow')
```

**Environment Override:**
```bash
export NBA_MCP_COST_LIMITS_PHASE_2_ANALYSIS=50.00
```

---

### 3. AI Models

```yaml
models:
  gemini:
    model_name: "gemini-2.0-flash-exp"
    temperature: 0.3
    max_tokens: 250000
    timeout_seconds: 180
    pricing:
      input_low_tier: 1.25
      output_low_tier: 2.50

  claude:
    model_name: "claude-sonnet-4"
    temperature: 0.3
    max_tokens: 200000
    timeout_seconds: 180
    pricing:
      input: 3.00
      output: 15.00

  gpt4:
    model_name: "gpt-4-turbo"
    temperature: 0.3
    max_tokens: 128000
    timeout_seconds: 180
    pricing:
      input: 10.00
      output: 30.00
```

**Access:**
```python
model_name = config.get_model_config('gemini', 'model_name')
temperature = config.get_model_config('gemini', 'temperature')
max_tokens = config.get_model_config('claude', 'max_tokens')
```

**Environment Override:**
```bash
export NBA_MCP_MODELS_GEMINI_MODEL_NAME=gemini-1.5-pro
export NBA_MCP_MODELS_CLAUDE_TEMPERATURE=0.5
```

---

### 4. Phase Settings

```yaml
phases:
  phase_2:
    use_high_context: true
    max_chars_per_book: 1000000
    max_tokens_per_book: 250000
    min_recommendations: 10
    max_recommendations: 60
    convergence_threshold: 0.85
    max_iterations: 3

  phase_3:
    similarity_threshold: 0.80
    min_confidence: 0.70
    synthesis_models: "claude,gpt4"

  phase_4:
    output_dir: "implementation_plans"
    generate_tests: true
    generate_sql: true
    tier_1_file_count: 6
    tier_2_file_count: 3

  phase_8_5:
    syntax_check: true
    test_discovery: true
    import_check: true
    sql_validation: true
    run_tests: false
    fail_on_error: false
```

**Access:**
```python
use_high_context = config.get_phase_config('phase_2', 'use_high_context')
similarity = config.get_phase_config('phase_3', 'similarity_threshold')
output_dir = config.get_phase_config('phase_4', 'output_dir')
```

---

### 5. Safety Features

```yaml
safety:
  rollback:
    enabled: true
    backup_before_phase: true
    backup_retention_days: 7

  error_recovery:
    enabled: true
    max_retries: 3
    api_timeout_backoff: 2
    rate_limit_backoff: 60
    network_error_backoff: 5

  cost_tracking:
    enabled: true
    save_reports: true
    report_dir: "cost_tracker"
```

**Access:**
```python
rollback_enabled = config.get_safety_config('rollback', 'enabled')
max_retries = config.get_safety_config('error_recovery', 'max_retries')
save_reports = config.get_safety_config('cost_tracking', 'save_reports')
```

---

### 6. Paths

```yaml
paths:
  mcp_synthesis: "/Users/ryanranft/nba-mcp-synthesis"
  simulator_aws: "/Users/ryanranft/nba-simulator-aws"
  analysis_results: "analysis_results"
  implementation_plans: "implementation_plans"
  books_s3_bucket: "nba-mcp-books"
  books_s3_prefix: "books/"
  backups_dir: "backups"
```

**Access:**
```python
project_root = config.get_path('mcp_synthesis')
output_dir = config.get_path('implementation_plans')
backups = config.get_path('backups_dir')
```

---

### 7. Feature Flags

```yaml
features:
  intelligent_plan_editor: false   # Tier 2
  smart_integrator: false          # Tier 2
  prediction_analyzer: false       # Tier 2
  status_tracking: false           # Tier 2
  conflict_resolution: false       # Tier 3
```

**Access:**
```python
if config.is_feature_enabled('intelligent_plan_editor'):
    # Use Tier 2+ feature
    pass
```

**Enable for Testing:**
```bash
export NBA_MCP_FEATURES_SMART_INTEGRATOR=true
```

---

## Advanced Usage

### Custom Config Path

```python
from pathlib import Path
from config_loader import ConfigLoader

# Load from custom location
config = ConfigLoader(config_path=Path("custom_config.yaml"))
```

### Singleton Pattern

```python
# Use global config instance
from config_loader import get_config

config = get_config()  # Always returns same instance
```

### Convenience Functions

```python
from config_loader import (
    get_cost_limit,
    get_model_config,
    get_phase_config,
    is_feature_enabled
)

# Direct access
limit = get_cost_limit('phase_2_analysis')
model = get_model_config('gemini', 'model_name')
threshold = get_phase_config('phase_3', 'similarity_threshold')
enabled = is_feature_enabled('smart_integrator')
```

---

## Environment Variables

All config values can be overridden with environment variables using this pattern:

```
NBA_MCP_<SECTION>_<SUBSECTION>_<KEY>=<VALUE>
```

**Examples:**

```bash
# Workflow settings
export NBA_MCP_WORKFLOW_MODE=A
export NBA_MCP_WORKFLOW_AUTO_IMPLEMENT=true

# Cost limits
export NBA_MCP_COST_LIMITS_TOTAL_WORKFLOW=100.00
export NBA_MCP_COST_LIMITS_PHASE_2_ANALYSIS=50.00

# Model config
export NBA_MCP_MODELS_GEMINI_MODEL_NAME=gemini-1.5-pro
export NBA_MCP_MODELS_CLAUDE_MAX_TOKENS=150000

# Phase config
export NBA_MCP_PHASES_PHASE_2_USE_HIGH_CONTEXT=false
export NBA_MCP_PHASES_PHASE_3_SIMILARITY_THRESHOLD=0.75

# Feature flags
export NBA_MCP_FEATURES_SMART_INTEGRATOR=true
export NBA_MCP_FEATURES_INTELLIGENT_PLAN_EDITOR=true
```

---

## Tier 0 vs Tier 1+ Settings

### Tier 0 (Current)
- Uses config for: cost limits, model settings, phase settings, safety
- **Hardcoded in scripts:** parallel execution, caching, checkpoints
- Feature flags are defined but not used

### Tier 1 (Next)
- All settings from config
- Enables: parallel execution, caching, checkpoints, monitoring
- Feature flags control new behaviors

### Tier 2+
- Advanced features enabled via flags
- Intelligent plan editor, smart integrator, prediction analyzer
- A/B testing for model combinations

---

## Validation

The config file is validated when loaded. If any errors occur:

1. Warning is logged
2. Default values are used
3. Script continues (graceful degradation)

**Manual Validation:**

```python
from config_loader import ConfigLoader

config = ConfigLoader()

# Check if config loaded successfully
if config.config_path.exists():
    print("✅ Config loaded successfully")
else:
    print("⚠️  Using default config")
```

---

## Best Practices

### 1. Don't Hardcode Values

❌ **Bad:**
```python
COST_LIMIT = 30.00
MODEL_NAME = "gemini-2.0-flash-exp"
```

✅ **Good:**
```python
from config_loader import get_config

config = get_config()
cost_limit = config.get_cost_limit('phase_2_analysis')
model_name = config.get_model_config('gemini', 'model_name')
```

### 2. Use Type-Safe Accessors

❌ **Bad:**
```python
limit = config.get('cost_limits', 'phase_2_analysis')  # Returns Any
```

✅ **Good:**
```python
limit = config.get_cost_limit('phase_2_analysis')  # Returns float
```

### 3. Provide Defaults

```python
# Good: Provides fallback if key missing
value = config.get('some', 'nested', 'key', default='fallback')
```

### 4. Environment Variables for Secrets

```yaml
# Don't put secrets in config file
# Use environment variables instead
models:
  gemini:
    api_key: "${GEMINI_API_KEY}"  # Will be loaded from env
```

---

## Troubleshooting

### Config Not Loading

```python
# Debug config loading
import logging
logging.basicConfig(level=logging.DEBUG)

from config_loader import ConfigLoader
config = ConfigLoader()
# Will show detailed loading info
```

### Values Not Updating

```bash
# Check environment variables
env | grep NBA_MCP

# Clear any conflicting vars
unset NBA_MCP_WORKFLOW_MODE
```

### Path Issues

```python
# Check if paths exist
config = ConfigLoader()
project_root = config.get_path('mcp_synthesis')
print(f"Project root exists: {project_root.exists()}")
```

---

## Examples

### Example 1: Custom Test Run

```python
#!/usr/bin/env python3
from config_loader import ConfigLoader

config = ConfigLoader()

# Override settings for test
os.environ['NBA_MCP_COST_LIMITS_TOTAL_WORKFLOW'] = '10.00'
os.environ['NBA_MCP_WORKFLOW_TEST_BOOK_LIMIT'] = '1'

# Run workflow with custom settings
# ... (workflow code)
```

### Example 2: Multi-Environment Setup

```bash
# Development
export NBA_MCP_WORKFLOW_MODE=B
export NBA_MCP_COST_LIMITS_TOTAL_WORKFLOW=75.00

# Production
export NBA_MCP_WORKFLOW_MODE=dual
export NBA_MCP_COST_LIMITS_TOTAL_WORKFLOW=500.00
export NBA_MCP_FEATURES_SMART_INTEGRATOR=true
```

### Example 3: Testing Feature Flags

```python
#!/usr/bin/env python3
from config_loader import get_config

config = get_config()

# Enable Tier 2 features for testing
os.environ['NBA_MCP_FEATURES_INTELLIGENT_PLAN_EDITOR'] = 'true'
os.environ['NBA_MCP_FEATURES_SMART_INTEGRATOR'] = 'true'

if config.is_feature_enabled('smart_integrator'):
    print("✅ Smart integrator enabled")
    # Use advanced feature
```

---

**Last Updated:** 2025-10-18
**Version:** Tier 0 Day 4
**Status:** ✅ Configuration System Complete

