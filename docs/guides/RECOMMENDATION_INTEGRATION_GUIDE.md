# Recommendation Integration System - Usage Guide

**Created:** October 12, 2025
**Purpose:** Comprehensive guide for using the Recommendation Integration System
**Version:** 1.0

---

## Overview

The Recommendation Integration System automatically organizes book recommendations and integrates them with the NBA Simulator AWS project. It maps recommendations to project phases, detects conflicts, applies safe updates, and tracks implementation status across both projects.

---

## System Components

### 1. PhaseMapper (`scripts/phase_mapper.py`)
Maps book recommendations to NBA Simulator AWS phases (0-9) based on keyword matching and semantic analysis.

**Key Features:**
- Intelligent phase mapping using keyword analysis
- Support for multiple phase matches
- Phase information retrieval
- Distribution analysis

### 2. RecommendationIntegrator (`scripts/recommendation_integrator.py`)
Integrates recommendations into the NBA Simulator AWS project by generating phase-specific enhancement documents.

**Key Features:**
- Loads recommendations from master database
- Organizes recommendations by phase
- Generates phase enhancement documents
- Creates integration summaries

### 3. PlanOverrideManager (`scripts/plan_override_manager.py`)
Manages plan overrides when new recommendations suggest better approaches than existing plans.

**Key Features:**
- Conflict detection between recommendations and existing plans
- Safe automatic updates for non-conflicting changes
- Manual review flagging for conflicts
- Change tracking and logging

### 4. CrossProjectTracker (`scripts/cross_project_tracker.py`)
Tracks implementation status across both NBA MCP Synthesis and NBA Simulator AWS projects.

**Key Features:**
- Scans both projects for implementation status
- Finds shared implementations
- Generates unified status reports
- Tracks cross-project progress

### 5. Main Integration Workflow (`scripts/integrate_recommendations.py`)
Orchestrates the complete integration process.

**Key Features:**
- Runs all integration steps in sequence
- Generates comprehensive reports
- Handles errors gracefully
- Provides detailed progress feedback

---

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **NBA MCP Synthesis** project at `/Users/ryanranft/nba-mcp-synthesis`
3. **NBA Simulator AWS** project at `/Users/ryanranft/nba-simulator-aws`
4. **Master recommendations** file at `analysis_results/master_recommendations.json`

### Basic Usage

```bash
# Run the complete integration workflow
cd /Users/ryanranft/nba-mcp-synthesis
python3 scripts/integrate_recommendations.py
```

### Individual Component Usage

```bash
# Test PhaseMapper
python3 scripts/phase_mapper.py

# Test RecommendationIntegrator
python3 scripts/recommendation_integrator.py

# Test PlanOverrideManager
python3 scripts/plan_override_manager.py

# Test CrossProjectTracker
python3 scripts/cross_project_tracker.py
```

---

## Detailed Usage

### Phase Mapping

The PhaseMapper automatically maps recommendations to phases based on keywords:

```python
from scripts.phase_mapper import PhaseMapper

mapper = PhaseMapper()

# Map a recommendation
rec = {
    'title': 'Implement data validation pipeline',
    'reasoning': 'Quality checks needed for incoming data'
}
phases = mapper.map_recommendation_to_phase(rec)
print(f"Maps to phases: {phases}")  # [1] - Phase 1: Data Quality

# Get phase information
info = mapper.get_phase_info(1)
print(f"Phase 1: {info['description']}")
```

**Phase Mapping Rules:**
- **Phase 0:** Data Collection (scraping, APIs, sources)
- **Phase 1:** Data Quality & Integration (validation, cleaning)
- **Phase 2:** AWS Glue ETL (transformation, pipelines)
- **Phase 3:** Database Infrastructure (PostgreSQL, RDS, schema)
- **Phase 4:** Simulation Engine (temporal, panel data)
- **Phase 5:** Machine Learning Models (training, prediction)
- **Phase 6:** Optional Enhancements (UI, dashboards)
- **Phase 7:** Betting Odds Integration (sportsbook data)
- **Phase 8:** Recursive Data Discovery (analysis, insights)
- **Phase 9:** System Architecture (infrastructure, deployment)

### Recommendation Integration

The RecommendationIntegrator processes recommendations and generates phase documents:

```python
from scripts.recommendation_integrator import RecommendationIntegrator

integrator = RecommendationIntegrator(
    simulator_path="/Users/ryanranft/nba-simulator-aws",
    synthesis_path="/Users/ryanranft/nba-mcp-synthesis"
)

# Load recommendations
master_recs = integrator.load_master_recommendations()

# Map to phases
phase_recs = integrator.create_phase_recommendations(master_recs)

# Generate phase documents
generated_files = integrator.generate_phase_enhancement_docs(phase_recs)
```

**Output Files:**
- `docs/phases/phase_X/RECOMMENDATIONS_FROM_BOOKS.md` - Phase-specific recommendations

### Plan Override Management

The PlanOverrideManager analyzes conflicts and applies safe updates:

```python
from scripts.plan_override_manager import PlanOverrideManager

mgr = PlanOverrideManager("/Users/ryanranft/nba-simulator-aws")

# Analyze conflicts
analysis = mgr.analyze_plan_conflicts(phase_num, recommendations)

# Propose updates
proposal = mgr.propose_plan_updates(phase_num, analysis)

# Apply safe updates
results = mgr.apply_safe_updates(phase_num, proposal)
```

**Conflict Types:**
- **Conflicts:** Require manual review (opposing approaches)
- **Enhancements:** Applied automatically (improvements to existing)
- **New Additions:** Applied automatically (new features)

### Cross-Project Tracking

The CrossProjectTracker monitors implementation across both projects:

```python
from scripts.cross_project_tracker import CrossProjectTracker

tracker = CrossProjectTracker(
    synthesis_path="/Users/ryanranft/nba-mcp-synthesis",
    simulator_path="/Users/ryanranft/nba-simulator-aws"
)

# Scan both projects
scan_results = tracker.scan_both_projects()

# Generate unified status
content = tracker.generate_unified_status(scan_results)

# Save status report
tracker.save_unified_status(scan_results, "CROSS_PROJECT_IMPLEMENTATION_STATUS.md")
```

---

## Output Files

### Generated Files

1. **Phase Enhancement Documents**
   ```
   nba-simulator-aws/docs/phases/
   ├── phase_0/RECOMMENDATIONS_FROM_BOOKS.md
   ├── phase_1/RECOMMENDATIONS_FROM_BOOKS.md
   ├── phase_2/RECOMMENDATIONS_FROM_BOOKS.md
   ├── ...
   └── phase_9/RECOMMENDATIONS_FROM_BOOKS.md
   ```

2. **Proposed Updates** (if conflicts exist)
   ```
   nba-simulator-aws/docs/phases/
   ├── phase_X/PROPOSED_UPDATES.md
   ```

3. **Cross-Project Status**
   ```
   nba-mcp-synthesis/CROSS_PROJECT_IMPLEMENTATION_STATUS.md
   ```

4. **Integration Summary**
   ```
   nba-mcp-synthesis/integration_summary.md
   ```

### File Contents

#### Phase Enhancement Document
```markdown
# Phase X - Book Recommendations

**Generated:** 2025-10-12T...
**Source:** Technical book analysis (N books)
**Total Recommendations:** N

## Critical Recommendations (N)
## Important Recommendations (N)
## Nice-to-Have Recommendations (N)

## Implementation Priority
1. Address all Critical items first
2. Then Important items
3. Finally Nice-to-Have items
```

#### Proposed Updates Document
```markdown
# Phase X - Proposed Updates

**Action Required:** Yes/No

## Conflicts Requiring Manual Review
## Enhancements Applied Automatically
## New Additions Applied Automatically

## Next Steps
1. Review conflicts
2. Verify enhancements
3. Validate additions
```

#### Cross-Project Status
```markdown
# Cross-Project Implementation Status

## Project Overview
### NBA MCP Synthesis
### NBA Simulator AWS

## Shared Implementations
## Recommendations Status
## Implementation Progress
```

---

## Configuration

### Environment Variables

The system uses hardcoded paths but can be configured:

```python
# In integrate_recommendations.py
synthesis_path = "/Users/ryanranft/nba-mcp-synthesis"
simulator_path = "/Users/ryanranft/nba-simulator-aws"
```

### Phase Keywords

Customize phase mapping by modifying keywords in `PhaseMapper`:

```python
self.phase_keywords = {
    0: ["data collection", "scraping", "ingestion", "sources"],
    1: ["data quality", "validation", "integration", "deduplication"],
    # ... add more keywords as needed
}
```

### Conflict Detection

Customize conflict detection patterns in `PlanOverrideManager`:

```python
conflict_patterns = [
    (r'use (\w+)', r'use (?!\1)\w+'),
    (r'postgresql', r'mysql|mongodb|sqlite'),
    # ... add more patterns
]
```

---

## Testing

### Run All Tests

```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 -m pytest tests/test_recommendation_integration.py -v
```

### Run Individual Component Tests

```bash
# Test PhaseMapper
python3 -m pytest tests/test_recommendation_integration.py::TestPhaseMapper -v

# Test RecommendationIntegrator
python3 -m pytest tests/test_recommendation_integration.py::TestRecommendationIntegrator -v

# Test PlanOverrideManager
python3 -m pytest tests/test_recommendation_integration.py::TestPlanOverrideManager -v

# Test CrossProjectTracker
python3 -m pytest tests/test_recommendation_integration.py::TestCrossProjectTracker -v
```

### Test Coverage

```bash
python3 -m pytest tests/test_recommendation_integration.py --cov=scripts --cov-report=html
```

---

## Troubleshooting

### Common Issues

#### 1. "No recommendations found"
**Cause:** Missing or empty `master_recommendations.json`
**Solution:** Ensure recommendations file exists and contains data

```bash
# Check if file exists
ls -la analysis_results/master_recommendations.json

# Check file content
cat analysis_results/master_recommendations.json
```

#### 2. "Simulator path does not exist"
**Cause:** NBA Simulator AWS project not found
**Solution:** Verify project path and structure

```bash
# Check if simulator project exists
ls -la /Users/ryanranft/nba-simulator-aws

# Check phase directories
ls -la /Users/ryanranft/nba-simulator-aws/docs/phases/
```

#### 3. "No phase match found"
**Cause:** Recommendation doesn't match any phase keywords
**Solution:** Review recommendation text or add keywords

```python
# Check what phases a recommendation maps to
from scripts.phase_mapper import PhaseMapper
mapper = PhaseMapper()
phases = mapper.map_recommendation_to_phase({'title': 'Your recommendation'})
print(f"Maps to: {phases}")
```

#### 4. "Error writing phase recommendations"
**Cause:** Permission issues or missing directories
**Solution:** Check permissions and create directories

```bash
# Check permissions
ls -la /Users/ryanranft/nba-simulator-aws/docs/phases/

# Create missing directories
mkdir -p /Users/ryanranft/nba-simulator-aws/docs/phases/phase_X
```

### Debug Mode

Enable debug logging for detailed output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Verification

Check generated files manually:

```bash
# Check phase documents
ls -la /Users/ryanranft/nba-simulator-aws/docs/phases/phase_*/RECOMMENDATIONS_FROM_BOOKS.md

# Check status reports
ls -la /Users/ryanranft/nba-mcp-synthesis/CROSS_PROJECT_IMPLEMENTATION_STATUS.md
ls -la /Users/ryanranft/nba-mcp-synthesis/integration_summary.md
```

---

## Advanced Usage

### Custom Phase Mapping

Create custom phase mapping logic:

```python
class CustomPhaseMapper(PhaseMapper):
    def map_recommendation_to_phase(self, rec):
        # Custom logic here
        if 'custom_keyword' in rec['title'].lower():
            return [0]  # Map to Phase 0
        return super().map_recommendation_to_phase(rec)
```

### Batch Processing

Process multiple recommendation sets:

```python
# Process multiple recommendation files
recommendation_files = ['recs1.json', 'recs2.json', 'recs3.json']

for file in recommendation_files:
    # Load and process each file
    with open(file, 'r') as f:
        recs = json.load(f)

    # Process recommendations
    phase_recs = integrator.create_phase_recommendations(recs)
    integrator.generate_phase_enhancement_docs(phase_recs)
```

### Integration with CI/CD

Add to GitHub Actions workflow:

```yaml
name: Recommendation Integration
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  integrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Integration
        run: |
          python3 scripts/integrate_recommendations.py
      - name: Commit Changes
        run: |
          git add .
          git commit -m "Update recommendations" || true
          git push
```

---

## Best Practices

### 1. Regular Integration
- Run integration after adding new recommendations
- Schedule daily/weekly integration runs
- Monitor for conflicts and resolve promptly

### 2. Conflict Resolution
- Review conflicts manually before applying
- Document resolution decisions
- Update phase plans as needed

### 3. Phase Organization
- Keep phase keywords up to date
- Add new keywords as project evolves
- Review phase mappings regularly

### 4. Documentation
- Keep generated documents current
- Review phase enhancement documents
- Update cross-project status regularly

### 5. Testing
- Test integration after changes
- Verify generated files
- Check for conflicts and errors

---

## Support

### Getting Help

1. **Check logs** - Look for error messages in console output
2. **Review generated files** - Check if files were created correctly
3. **Run tests** - Verify system components work
4. **Check permissions** - Ensure write access to directories

### Reporting Issues

When reporting issues, include:
- Error messages
- Generated log output
- File structure
- Steps to reproduce

### Contributing

To contribute improvements:
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

## Changelog

### Version 1.0 (October 12, 2025)
- Initial release
- PhaseMapper with keyword-based mapping
- RecommendationIntegrator with phase document generation
- PlanOverrideManager with conflict detection
- CrossProjectTracker with unified status reporting
- Complete integration workflow
- Comprehensive test suite
- Documentation and usage guide

---

*This guide was generated by the Recommendation Integration System.*




