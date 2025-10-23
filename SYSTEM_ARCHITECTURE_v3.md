# NBA MCP Synthesis System - Architecture v3.0

Complete system architecture documentation for the enhanced Tier 3 system.

**Version:** 3.0
**Date:** October 19, 2025
**Status:** Production Ready ✅

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│         NBA MCP Synthesis System v3.0                       │
│         Tiered Implementation Complete                       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌───▼────┐         ┌───▼────┐
   │ Tier 0  │         │ Tier 1 │         │ Tier 2 │
   │ Safety  │         │ Speed  │         │   AI   │
   └────┬────┘         └───┬────┘         └───┬────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
                      ┌────▼────┐
                      │ Tier 3  │
                      │  Obs.   │
                      └─────────┘
```

---

## Component Architecture

### Layer 1: Core Workflow

```
┌─────────────────────────────────────────────────────────┐
│                  run_full_workflow.py                   │
│                  (Main Orchestrator)                    │
└──────────┬──────────────────────────────────┬──────────┘
           │                                  │
    ┌──────▼──────┐                    ┌─────▼──────┐
    │   Phase     │                    │  Phase     │
    │  Manager    │                    │  Status    │
    └──────┬──────┘                    └─────┬──────┘
           │                                  │
    ┌──────▼────────────────────────────────▼──────┐
    │         Individual Phase Scripts              │
    │  - phase1_book_discovery.py                   │
    │  - phase2_book_analysis.py (enhanced)         │
    │  - phase3_synthesis.py                        │
    │  - phase3_5_ai_plan_modification.py           │
    │  - phase4_file_generation.py                  │
    └───────────────────────────────────────────────┘
```

### Layer 2: AI Intelligence (Tier 2)

```
┌─────────────────────────────────────────────────────────┐
│            HighContextBookAnalyzer                      │
│         (Multi-model AI Analysis)                       │
└──────┬──────────────────────────────────────┬──────────┘
       │                                      │
┌──────▼──────┐                        ┌─────▼──────┐
│   Gemini    │                        │   Claude   │
│  2.0 Flash  │                        │ Sonnet 4   │
│   (Fast)    │                        │ (Quality)  │
└──────┬──────┘                        └─────┬──────┘
       │                                     │
       └─────────────┬───────────────────────┘
                     │
            ┌────────▼─────────┐
            │   Consensus      │
            │   Synthesis      │
            │ (Conflict Res.)  │
            └──────────────────┘
```

### Layer 3: Tier 3 Observability

```
┌─────────────────────────────────────────────────────────┐
│              Workflow Monitor (Flask)                   │
│              http://localhost:8080                      │
└──────┬──────────────────────────────────────┬──────────┘
       │                                      │
┌──────▼──────────┐              ┌───────────▼─────────┐
│    Resource     │              │   Dependency        │
│    Monitor      │              │   Visualizer        │
│  (API/Disk/Mem) │              │  (Mermaid Graphs)   │
└──────┬──────────┘              └───────────┬─────────┘
       │                                     │
┌──────▼──────────┐              ┌───────────▼─────────┐
│    Version      │              │   A/B Testing       │
│    Tracker      │              │   Framework         │
│  (Metadata)     │              │  (Model Compare)    │
└─────────────────┘              └─────────────────────┘
```

### Layer 4: Data & Storage

```
┌─────────────────────────────────────────────────────────┐
│                   File System                           │
└───────────┬─────────────────────────────────┬───────────┘
            │                                 │
    ┌───────▼────────┐              ┌────────▼──────────┐
    │  Result Cache  │              │   Checkpoints     │
    │   (Tier 1)     │              │   (Tier 1)        │
    │  - Analysis    │              │  - Phase state    │
    │  - Synthesis   │              │  - Resume support │
    └────────┬───────┘              └────────┬──────────┘
             │                               │
    ┌────────▼────────┐              ┌──────▼───────────┐
    │ Analysis Results│              │  Implementation  │
    │  - JSON files   │              │     Plans        │
    │  - Trackers     │              │  - Formatted     │
    └─────────────────┘              └──────────────────┘
```

---

## Data Flow

### Book Analysis Flow

```
┌──────────┐
│  Books   │ (51 technical books, S3)
│  (S3)    │
└────┬─────┘
     │
     ▼
┌──────────────┐
│  Discovery   │ Phase 1: List & validate books
│   Phase 1    │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│   Analysis   │ Phase 2: AI analysis with convergence
│   Phase 2    │ - Gemini + Claude
└─────┬────────┘ - Up to 200 iterations
      │          - Cache for speed
      ▼
┌──────────────┐
│  Synthesis   │ Phase 3: Consensus & deduplication
│   Phase 3    │ - Merge recommendations
└─────┬────────┘ - Quality scoring
      │
      ▼
┌──────────────┐
│ AI Mods      │ Phase 3.5: Intelligent plan editing
│  Phase 3.5   │ - Gap detection
└─────┬────────┘ - Duplicate removal
      │
      ▼
┌──────────────┐
│ File Gen     │ Phase 4: Generate implementation files
│  Phase 4     │ - README, code, tests
└─────┬────────┘ - Version tracking
      │
      ▼
┌──────────────┐
│ Integration  │ Phase 9: Deploy to nba-simulator-aws
│  Phase 9     │
└──────────────┘
```

### Real-Time Monitoring Flow

```
┌─────────────┐         ┌──────────────┐
│  Workflow   │ ─HTTP─> │  Dashboard   │
│  Runner     │ <─JSON─ │  (Browser)   │
└──────┬──────┘         └──────────────┘
       │                       ▲
       │ Updates               │ Auto-refresh
       │                       │ (2 seconds)
       ▼                       │
┌──────────────┐         ┌─────┴──────┐
│   Workflow   │ ─State─>│   Flask    │
│   Monitor    │         │   Server   │
└──────┬───────┘         └────────────┘
       │
       ▼
┌──────────────┐
│  Resource    │ - API quotas
│  Monitor     │ - Disk space
└──────────────┘ - Memory
```

---

## Component Details

### 1. HighContextBookAnalyzer

**Purpose:** Multi-model AI analysis with convergence

**Key Features:**
- Model selection (Gemini/Claude/Both)
- Consensus synthesis
- Convergence detection
- Cost tracking
- Cache integration

**Configuration:**
```python
analyzer = HighContextBookAnalyzer(
    model_combination='gemini+claude',
    consensus_threshold=0.70,
    max_iterations=200
)
```

**Output:**
```json
{
  "book_title": "...",
  "recommendations": [...],
  "convergence_tracker": {
    "iterations_completed": 15,
    "convergence_achieved": true,
    "final_count": 43
  },
  "cost": {
    "total": 2.35,
    "gemini": 1.80,
    "claude": 0.55
  }
}
```

---

### 2. Resource Monitor

**Purpose:** Prevent API/disk/memory issues

**Monitors:**
- Gemini quota: 1M tokens/min
- Claude quota: 20K tokens/min
- Disk space: Alert < 10GB
- Memory: Alert > 90%

**Thresholds:**
- 🟢 Normal: < 80%
- 🟡 Warning: 80-95%
- 🔴 Critical: > 95% (throttle)

**Integration:**
```python
from resource_monitor import ResourceMonitor

monitor = ResourceMonitor()

# Check before API call
allowed, reason = monitor.check_api_quota('gemini', tokens=50000)
if not allowed:
    monitor.wait_if_throttled()

# Track after call
monitor.track_api_usage('gemini', tokens=50000)
```

---

### 3. Workflow Monitor

**Purpose:** Real-time dashboard

**Tech Stack:**
- Backend: Flask + Python
- Frontend: HTML + CSS + JavaScript
- Updates: REST API (2-second polling)

**API Endpoints:**
- `GET /api/status` - Workflow state
- `GET /api/phases` - Phase progress
- `GET /api/cost` - Cost tracking
- `GET /api/system` - Resource metrics
- `POST /api/update` - Update state

**Dashboard Sections:**
- Phase progress bars
- Cost tracking graph
- API quota meters
- System health indicators
- Recent alerts list

---

### 4. Dependency Visualizer

**Purpose:** Phase dependency analysis

**Outputs:**
1. **Phase Dependency Graph** (Mermaid)
   ```mermaid
   graph TD
       phase_0 --> phase_1
       phase_1 --> phase_2
       phase_2 --> phase_3
   ```

2. **Data Flow Diagram** (Mermaid)
3. **Critical Path Report** (Markdown)
4. **Bottleneck Analysis** (JSON)

**Usage:**
```bash
# Generate all
python3 scripts/dependency_visualizer.py --export visualizations/

# Just summary
python3 scripts/dependency_visualizer.py
```

---

### 5. Version Tracker

**Purpose:** Add metadata to generated files

**File Header Template:**
```python
"""
Generated by: NBA MCP Synthesis System v3.0
Generated at: 2025-10-19T12:00:00Z
Generator: phase4_file_generation.py

Source Books:
- Book 1 (hash: abc123)
- Book 2 (hash: def456)

Models Used:
- Gemini: gemini-2.0-flash-exp
- Claude: claude-sonnet-4

Regenerate: python scripts/run_full_workflow.py ...
"""
```

**Supports:**
- Python files (.py)
- Markdown files (.md)
- JSON files (metadata field)

---

### 6. A/B Testing Framework

**Purpose:** Compare model configurations

**Predefined Tests:**
- `gemini_only` vs `claude_only`
- Consensus 70% vs 85%
- Speed vs quality tradeoffs

**Metrics:**
- Recommendations found
- Cost per recommendation
- Processing time
- Quality scores

**Integration:**
```python
from ab_testing_framework import ABTestingFramework

framework = ABTestingFramework()
results = await framework.run_comparison_test(
    config_names=['gemini_only', 'claude_only'],
    book_paths=['book1.txt', 'book2.txt'],
    book_titles=['Book 1', 'Book 2']
)

report = framework.generate_comparison_report(results)
```

---

## Tier Summary

### Tier 0: Safety & Validation ✅

**Features:**
- Cost limits enforcement
- Dry-run mode
- Rollback capabilities
- Pre-integration validation

**Status:** Complete

---

### Tier 1: Performance & Reliability ✅

**Features:**
- Result caching (7-day TTL)
- Checkpoint system (resume support)
- Parallel execution (4 workers)
- Configuration management (YAML)

**Status:** Complete

---

### Tier 2: AI Intelligence Layer ✅

**Features:**
- Phase 3.5 AI Plan Modifications
- Smart Integrator
- Conflict Resolution
- Intelligent Plan Editor
- Phase Status Tracking

**Status:** Complete

---

### Tier 3: Observability & Optimization ✅

**Features:**
- Resource Monitoring
- Real-time Dashboard
- Dependency Visualization
- Version Tracking
- A/B Testing Framework
- Convergence Enhancement

**Status:** Complete (convergence run optional)

---

## Configuration Hierarchy

```
config/
└── workflow_config.yaml
    ├── workflow settings
    ├── cost_limits (Tier 0)
    ├── models configuration
    ├── phase_2
    │   ├── convergence (Tier 3)
    │   └── max_iterations: 200
    ├── cache (Tier 1)
    ├── checkpoints (Tier 1)
    ├── resource_monitoring (Tier 3)
    ├── ab_testing (Tier 3)
    └── features (Tier 2)
```

**Key Config Sections:**

1. **Cost Limits:**
   ```yaml
   cost_limits:
     phase_2_analysis: 300.00
     total_workflow: 400.00
   ```

2. **Convergence:**
   ```yaml
   phases:
     phase_2:
       convergence:
         max_iterations: 200
         force_convergence: true
   ```

3. **Resource Monitoring:**
   ```yaml
   resource_monitoring:
     enabled: true
     gemini_quota: 1000000
     claude_quota: 20000
   ```

---

## Error Handling & Recovery

### Error Recovery Flow

```
┌──────────────┐
│   Error      │
│   Detected   │
└──────┬───────┘
       │
       ▼
┌──────────────┐      Yes
│  Retryable?  │──────────> Retry with backoff
└──────┬───────┘
       │ No
       ▼
┌──────────────┐
│  Save State  │ Checkpoint system
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Log Error   │ Full stack trace
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Alert      │ Dashboard + logs
│   User       │
└──────────────┘
```

### Retry Strategies

```python
RETRY_CONFIG = {
    'api_timeout': {
        'retries': 3,
        'backoff': 2  # seconds
    },
    'rate_limit': {
        'retries': 5,
        'backoff': 60
    },
    'network_error': {
        'retries': 3,
        'backoff': 5
    }
}
```

---

## Performance Characteristics

### Book Analysis Performance

**Single Book (without cache):**
- Gemini only: ~30-45 seconds
- Claude only: ~60-90 seconds
- Gemini+Claude consensus: ~45-75 seconds

**Single Book (with cache, 12 iterations):**
- Cache hit: ~5-10 seconds
- Partial cache: ~15-30 seconds

**51 Books (parallel, 4 workers):**
- Without convergence: ~30-45 minutes
- With convergence (200 iter): ~10-15 hours

### Resource Usage

**Memory:**
- Baseline: ~500 MB
- Per worker: ~200 MB
- Peak (4 workers): ~1.5 GB

**Disk:**
- Cache: ~2-5 GB
- Results: ~500 MB - 1 GB
- Total: ~3-7 GB

**Network:**
- Gemini: ~500 KB/request
- Claude: ~300 KB/request
- Peak rate: ~2 MB/minute

---

## Security Considerations

### API Keys

```bash
# Stored in environment variables
export GEMINI_API_KEY="..."
export CLAUDE_API_KEY="..."

# Never committed to git
# Use .env file (gitignored)
```

### Dashboard Security

**⚠️ WARNING:**
- No authentication
- Localhost only (127.0.0.1)
- Do not expose to internet

**For Remote Access:**
```bash
# Use SSH tunnel
ssh -L 8080:localhost:8080 user@server
```

---

## Deployment Options

### Option 1: Local Development

```bash
# Run everything locally
python3 scripts/workflow_monitor.py &
python3 scripts/run_full_workflow.py --book "All Books"
```

### Option 2: Server Deployment

```bash
# On server
screen -S dashboard
python3 scripts/workflow_monitor.py

# Detach: Ctrl+A, D
# Reattach: screen -r dashboard

# Run workflow
screen -S workflow
python3 scripts/run_full_workflow.py --book "All Books" --parallel
```

### Option 3: Docker (Future)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY scripts/ scripts/
CMD ["python3", "scripts/workflow_monitor.py"]
```

---

## Monitoring & Logging

### Log Files

```
logs/
├── workflow.log                  # Main workflow
├── phase_2_analysis.log         # Book analysis
├── phase_3_synthesis.log        # Synthesis
├── resource_monitor.log         # Resource monitoring
├── workflow_monitor.log         # Dashboard
└── cost_tracker.log             # Cost tracking
```

### Log Levels

- **DEBUG:** Detailed internal operations
- **INFO:** Normal progress updates
- **WARNING:** Non-critical issues
- **ERROR:** Critical failures

### Metrics Tracked

1. **Performance:**
   - Books processed per hour
   - Recommendations per book
   - Cache hit rate
   - API response times

2. **Costs:**
   - Cost per book
   - Cost per recommendation
   - Cost per phase
   - Total cost vs budget

3. **System:**
   - API quota usage
   - Disk space trends
   - Memory usage patterns
   - Error rates

---

## Testing Strategy

### Integration Tests

```bash
# Run all Tier 3 tests
python3 scripts/test_tier3_integration.py

# With verbose output
python3 scripts/test_tier3_integration.py --verbose
```

**Tests Cover:**
- Resource Monitor: API/disk/memory tracking
- Workflow Monitor: State management
- Dependency Visualizer: Graph generation
- Version Tracker: Header generation
- A/B Testing: Configuration handling
- Component Integration: Cross-component calls

### Manual Testing

```bash
# 1. Start dashboard
python3 scripts/workflow_monitor.py

# 2. Run single book analysis
python3 scripts/run_full_workflow.py --book "Test Book"

# 3. Check dashboard at http://localhost:8080

# 4. Verify logs
tail -f logs/workflow.log
```

---

## Maintenance

### Cache Management

```bash
# View cache size
du -sh cache/

# Clear old cache (> 7 days)
find cache/ -type f -mtime +7 -delete

# Clear all cache
rm -rf cache/*
```

### Checkpoint Management

```bash
# List checkpoints
ls -lh checkpoints/

# Remove old checkpoints
find checkpoints/ -type f -mtime +1 -delete
```

### Log Rotation

```bash
# Archive old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log

# Or use logrotate
```

---

## Future Enhancements (Optional)

1. **Multi-user Dashboard:** WebSocket for real-time updates
2. **Advanced A/B Testing:** Bayesian optimization
3. **Auto-tuning:** ML-based parameter optimization
4. **Distributed Execution:** Kubernetes deployment
5. **Advanced Caching:** Redis for shared cache
6. **Real-time Notifications:** Slack/email alerts
7. **Advanced Visualization:** D3.js interactive graphs

---

## References

- **Main Docs:** `TIER3_COMPLETE.md`
- **Dashboard Guide:** `DASHBOARD_USAGE_GUIDE.md`
- **Convergence Guide:** `CONVERGENCE_ENHANCEMENT_GUIDE.md`
- **Implementation Plan:** `complete-book-analysis-system.plan.md`
- **Background Agent:** `BACKGROUND_AGENT_INSTRUCTIONS.md`

---

**System Status:** Production Ready ✅
**Version:** NBA MCP Synthesis System v3.0
**Date:** October 19, 2025







