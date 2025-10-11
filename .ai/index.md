# AI Session Management Guide

**Purpose**: Complete guide to session management and context optimization
**Last Updated**: 2025-10-11
**Status**: Active reference

---

## 🚀 IMPORTANT: Read This First

**For Claude/AI Sessions**: Before starting any work, read:
1. **This file** - Session management guide
2. **[CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md](../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Daily operations, decision tree, systematic approach

**Quick Start**:
```bash
./scripts/session_start.sh  # Generate current-session.md
cat .ai/current-session.md  # Read compact context (~300 tokens)
```

---

## 🎯 Overview

The AI session management system provides structured, context-optimized session tracking to minimize token usage while maintaining full project accessibility.

### Key Benefits
- **94% reduction** in session start context (5000 → 300 tokens)
- **85% reduction** in status check context (1000 → 150 tokens)
- **99% reduction** in tool lookup context (1000 → 10 tokens)
- **Overall**: 80-93% reduction in context usage

---

## 📁 Directory Structure

### `.ai/` Directory Layout
```
.ai/
├── current-session.md          # Active session state (~80 tokens)
├── index.md                    # This guide
├── daily/                      # Daily session logs
│   ├── template.md            # Session template
│   ├── 2025-10-11-session-1.md # Today's sessions
│   └── index.md               # Daily sessions index
├── monthly/                    # Monthly summaries
│   ├── template.md            # Monthly template
│   └── index.md               # Monthly index
├── permanent/                  # Permanent references
│   ├── tool-registry.md       # Searchable tool list
│   ├── architecture.md        # Architecture decisions
│   └── index.md               # Permanent index
└── archive/                    # Archived sessions (gitignored)
```

---

## 🚀 Quick Start

### Starting a New Session
```bash
# Basic session start
./scripts/session_start.sh

# Create new daily session file
./scripts/session_start.sh --new-session

# Run health checks
./scripts/session_start.sh --health-check

# Restore session from S3
./scripts/session_start.sh --restore=2025-10-10-session-1.md
```

### Reading Session Context
```bash
# Current session state (most important)
cat .ai/current-session.md

# Today's detailed log
cat .ai/daily/2025-10-11-session-1.md

# Tool registry
cat .ai/permanent/tool-registry.md
```

---

## 📊 Session Types

### Daily Sessions
**Purpose**: Detailed daily work logs
**Location**: `.ai/daily/`
**Retention**: 7 days (then archived)
**Context Cost**: 200-500 tokens per file

**When to Use**:
- Detailed work logging
- Problem-solving notes
- Implementation decisions
- Debugging sessions

**Template**: `.ai/daily/template.md`

### Monthly Summaries
**Purpose**: High-level monthly progress
**Location**: `.ai/monthly/`
**Retention**: 3 months (then archived)
**Context Cost**: 300-600 tokens per file

**When to Use**:
- Monthly progress reviews
- Strategic planning
- Major milestone summaries
- Performance metrics

**Template**: `.ai/monthly/template.md`

### Permanent References
**Purpose**: Long-term architectural decisions
**Location**: `.ai/permanent/`
**Retention**: Permanent
**Context Cost**: 100-800 tokens per file

**When to Use**:
- Architecture decisions
- Tool registry
- Best practices
- System design

---

## 🔄 Session Workflow

### Daily Workflow
1. **Start Session**: `./scripts/session_start.sh`
2. **Read Context**: `cat .ai/current-session.md`
3. **Work**: Use daily session file for detailed logging
4. **End Session**: Archive if needed

### Weekly Workflow
1. **Review**: Check daily sessions
2. **Archive**: `./scripts/session_archive.sh`
3. **Plan**: Update next week's focus

### Monthly Workflow
1. **Summarize**: Create monthly summary
2. **Archive**: Move old sessions to S3
3. **Plan**: Update monthly goals

---

## 📦 Archive Management

### Local Archive
**Location**: `.ai/archive/`
**Purpose**: Short-term local storage
**Retention**: 7 days for daily, 3 months for monthly

### S3 Archive (Optional)
**Purpose**: Long-term storage
**Cost**: ~$0.0005/month
**Retention**: Unlimited

**Setup**:
```bash
# Set S3 bucket name
export NBA_MCP_S3_BUCKET=nba-mcp-sessions

# Archive to S3
./scripts/session_archive.sh --to-s3

# Restore from S3
./scripts/session_start.sh --restore=2025-10-10-session-1.md
```

---

## 🛠️ Scripts Reference

### session_start.sh
**Purpose**: Start new session and generate context

**Options**:
- `--new-session`: Create new daily session file
- `--restore=ID`: Restore session from S3
- `--health-check`: Run comprehensive health checks
- `--help`: Show help message

**Examples**:
```bash
./scripts/session_start.sh                    # Basic start
./scripts/session_start.sh --new-session      # Create new daily file
./scripts/session_start.sh --health-check     # Run diagnostics
./scripts/session_start.sh --restore=2025-10-10-session-1.md
```

### session_archive.sh
**Purpose**: Archive old sessions

**Options**:
- `--to-s3`: Upload to S3
- `--monthly`: Include monthly summaries
- `--dry-run`: Preview without archiving

**Examples**:
```bash
./scripts/session_archive.sh                  # Local archive
./scripts/session_archive.sh --to-s3          # S3 archive
./scripts/session_archive.sh --dry-run        # Preview
```

---

## 🔍 Context Optimization

### Token Usage by Operation

| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| Session Start | 5000+ | ~300 | 94% ↓ |
| Status Check | 1000+ | ~150 | 85% ↓ |
| Tool Lookup | 1000+ | ~10 | 99% ↓ |
| Overall Session | 30-50K | 3-10K | 80-93% ↓ |

### Optimization Strategies

1. **Index-Based Navigation**: Use indexes to find specific information
2. **Focused Context**: Load only what you need
3. **Archive Strategy**: Move historical data out of active context
4. **Template System**: Consistent structure reduces cognitive load

---

## 📈 Best Practices

### Session Management
- **Start each day** with `./scripts/session_start.sh`
- **Read current-session.md** for quick context
- **Use daily files** for detailed logging
- **Archive regularly** to maintain performance

### Context Usage
- **Use indexes** to navigate efficiently
- **Load specific files** rather than browsing
- **Reference tool registry** for tool lookups
- **Check PROJECT_STATUS.md** for current status

### Archive Strategy
- **Archive daily sessions** after 7 days
- **Archive monthly summaries** after 3 months
- **Use S3** for long-term storage (optional)
- **Keep permanent references** always available

---

## 🚨 Troubleshooting

### Common Issues

**Session start fails**:
```bash
# Run health check
./scripts/session_start.sh --health-check

# Check git status
git status

# Verify .ai directory
ls -la .ai/
```

**S3 restore fails**:
```bash
# Check AWS CLI
aws --version

# Check credentials
aws sts get-caller-identity

# Check bucket access
aws s3 ls s3://nba-mcp-sessions/
```

**Context too large**:
```bash
# Archive old sessions
./scripts/session_archive.sh

# Check archive status
ls -la .ai/archive/

# Clean up temporary files
find . -name "*.tmp" -delete
```

### Health Check Results

**All checks pass**: ✅ Ready to work
**Git issues**: ❌ Fix git repository
**Missing files**: ⚠️ Run setup scripts
**S3 issues**: ⚠️ Optional - system works without S3

---

## 📊 Metrics & Monitoring

### Session Metrics
- **Sessions per day**: Track daily activity
- **Context usage**: Monitor token consumption
- **Archive frequency**: Ensure regular cleanup
- **S3 usage**: Monitor storage costs

### Performance Metrics
- **Session start time**: <10 seconds
- **Context generation**: <5 seconds
- **Archive time**: <30 seconds
- **Restore time**: <60 seconds

---

## 🔗 Related Documentation

### Project Status
- **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Current project status
- **[project/status/index.md](../project/status/index.md)** - Detailed status tracking

### Context Optimization
- **[docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md](../docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md)** - Best practices
- **[docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md](../docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md)** - Implementation plan

### Tool Reference
- **[.ai/permanent/tool-registry.md](permanent/tool-registry.md)** - Complete tool list
- **[docs/guides/QUICK_REFERENCE.md](../docs/guides/QUICK_REFERENCE.md)** - Quick commands

---

## 🎯 Success Criteria

### Context Optimization Goals
- ✅ Session start: <300 tokens (vs 5000+ before)
- ✅ Status check: <150 tokens (vs 1000+ before)
- ✅ Tool lookup: <10 tokens (vs 1000+ before)
- ✅ Overall savings: 80-93% reduction

### System Health Goals
- ✅ All health checks pass
- ✅ S3 integration working (optional)
- ✅ Archive process automated
- ✅ Session restoration functional

---

**Note**: This guide is part of Phase 5 of the Context Optimization plan. Use it to maximize the benefits of the session management system.