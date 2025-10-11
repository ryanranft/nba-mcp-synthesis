# Context Emergency Procedures

**Purpose**: Emergency procedures when context limits are approached or exceeded
**Last Updated**: 2025-10-11
**Status**: Active emergency guide

---

## 🚨 Overview

This guide provides step-by-step procedures for handling context emergencies when:
- Session context approaches 10K token limit
- Critical work must continue without interruption
- Context budget is severely exceeded
- System performance degrades due to context overload

**When to Use**: Immediately when context usage exceeds 9K tokens or shows red alerts in dashboard.

---

## 📊 Emergency Levels

### Level 1: Warning (8-9K tokens)

**Status**: Approaching limit, preventive action recommended

**Actions**:
1. Check current budget status
   ```bash
   ./scripts/track_context_budget.sh --session
   ```

2. Review dashboard for warnings
   ```bash
   ./scripts/context_dashboard.sh
   ```

3. Identify largest contributors
   ```bash
   ./scripts/monitor_file_sizes.sh
   ```

4. Apply quick optimizations (see below)

**Time to Act**: Within next 1-2 operations

---

### Level 2: Critical (9-10K tokens)

**Status**: At limit, immediate action required

**Actions**:
1. Stop all non-essential operations
2. Checkpoint current session
   ```bash
   ./scripts/checkpoint_session.sh
   ```

3. Run emergency context reduction
   ```bash
   ./scripts/emergency_context_reduce.sh
   ```

4. Archive unnecessary data
   ```bash
   ./scripts/session_archive.sh --force
   ```

**Time to Act**: Immediately

---

### Level 3: Emergency (>10K tokens)

**Status**: Limit exceeded, risk of degraded performance

**Actions**:
1. **IMMEDIATE**: Save all work
   ```bash
   git add -A
   git commit -m "checkpoint: Emergency save before context reset"
   ```

2. Create emergency session summary
   ```bash
   echo "## Emergency Context Reset - $(date)" > .ai/emergency_$(date +%Y%m%d_%H%M%S).md
   echo "Current state: [brief description]" >> .ai/emergency_$(date +%Y%m%d_%H%M%S).md
   echo "Next steps: [what to do after reset]" >> .ai/emergency_$(date +%Y%m%d_%H%M%S).md
   ```

3. Hard reset session
   ```bash
   ./scripts/session_start.sh --force-reset
   ```

4. Continue from emergency summary

**Time to Act**: RIGHT NOW

---

## ⚡ Quick Emergency Procedures

### Procedure A: Emergency Context Reduction (5 minutes)

**Use When**: Warning level (8-9K tokens)

**Steps**:
```bash
# 1. Check current state
./scripts/context_dashboard.sh

# 2. Run emergency reduction
./scripts/emergency_context_reduce.sh

# 3. Verify reduction
./scripts/track_context_budget.sh --session

# 4. Continue work with reduced context
```

**Expected Outcome**: Reduce context by 30-50% (2-4K tokens)

---

### Procedure B: Session Checkpoint & Continue (10 minutes)

**Use When**: Critical level (9-10K tokens)

**Steps**:
```bash
# 1. Create checkpoint
./scripts/checkpoint_session.sh

# 2. Archive old sessions
./scripts/session_archive.sh --force

# 3. Regenerate current-session.md
./scripts/session_start.sh --minimal

# 4. Load checkpoint for context
cat .ai/checkpoints/latest.md
```

**Expected Outcome**: Fresh session with minimal context (~1K tokens), checkpoint for reference

---

### Procedure C: Hard Reset & Resume (15 minutes)

**Use When**: Emergency level (>10K tokens)

**Steps**:
```bash
# 1. Save all work immediately
git add -A
git commit -m "checkpoint: Pre-reset save"

# 2. Document current state
cat > .ai/resume_point_$(date +%Y%m%d_%H%M%S).md <<EOF
# Resume Point - $(date)

## Current Task
[What you were doing]

## Progress So Far
[What's been completed]

## Next Steps
[What to do next]

## Key Files
[List of files being worked on]
EOF

# 3. Hard reset
./scripts/session_start.sh --force-reset

# 4. Read resume point (small file)
cat .ai/resume_point_*.md | tail -1

# 5. Continue from resume point
```

**Expected Outcome**: Complete session reset (~300 tokens), work resumable from resume point

---

## 🛠️ Emergency Optimization Techniques

### Technique 1: Aggressive File Reduction

**Problem**: Large files consuming excessive context

**Solution**:
```bash
# Find files >200 lines
find . -name "*.md" -exec wc -l {} + | awk '$1 > 200 {print $2, $1}' | sort -n -k2 -r

# Split large files
for file in $(find . -name "*.md" -exec wc -l {} + | awk '$1 > 200 {print $2}'); do
    echo "Consider splitting: $file"
done

# Or use emergency reduction script
./scripts/emergency_context_reduce.sh --split-large-files
```

---

### Technique 2: Temporary Gitignore

**Problem**: Too many files in active workspace

**Solution**:
```bash
# Temporarily gitignore non-essential files
cat >> .gitignore <<EOF
# Temporary emergency gitignore
docs/analysis/*
docs/archive/*
test_results/*
*.log
EOF

# Clean git cache
git rm -r --cached .
git add .
```

**Restore Later**: Remove temporary entries from .gitignore

---

### Technique 3: Symbolic Link Strategy

**Problem**: Need access to files without loading full content

**Solution**:
```bash
# Create reference directory with links
mkdir -p .ai/references
ln -s ../../docs/guides/ .ai/references/guides
ln -s ../../docs/plans/ .ai/references/plans

# Access via links (doesn't load content)
ls .ai/references/guides/  # Shows files without reading them
```

---

### Technique 4: Differential Updates

**Problem**: Status files require frequent updates

**Solution**:
```bash
# Instead of editing full file, append diff
echo "## Update $(date +%Y-%m-%d_%H:%M)" >> project/status/updates_$(date +%Y-%m-%d).diff
echo "+ Added feature X" >> project/status/updates_$(date +%Y-%m-%d).diff
echo "- Removed deprecated Y" >> project/status/updates_$(date +%Y-%m-%d).diff

# Apply diffs later when context allows
```

---

### Technique 5: Minimal Templates

**Problem**: Creating files from scratch uses too much context

**Solution**:
```bash
# Use ultra-minimal templates
cat > .ai/templates/minimal_session.md <<EOF
# Session $(date +%Y-%m-%d)
Goals:
Status:
Next:
EOF

# Quick file creation (50 tokens vs 300)
cp .ai/templates/minimal_session.md .ai/daily/session.md
```

---

## 📋 Emergency Checklist

### Pre-Emergency Preparation

- [ ] Baselines established: `./scripts/establish_baselines.sh`
- [ ] Monitoring active: `./scripts/weekly_health_check.sh`
- [ ] Budget tracking configured: `.ai/permanent/context_budget.json` exists
- [ ] Emergency scripts tested: All scripts executable and working

### During Emergency

- [ ] Current budget status checked
- [ ] Emergency level identified (Warning/Critical/Emergency)
- [ ] Appropriate procedure selected
- [ ] Work saved/committed before major actions
- [ ] Emergency procedure executed
- [ ] Reduction verified
- [ ] Ready to continue work

### Post-Emergency Review

- [ ] Root cause identified
- [ ] Preventive measures implemented
- [ ] Documentation updated
- [ ] Team notified (if applicable)
- [ ] Lessons learned recorded

---

## 🔍 Emergency Diagnostics

### Quick Diagnostic Commands

```bash
# Check current context usage
./scripts/context_dashboard.sh

# Identify problem files
./scripts/monitor_file_sizes.sh | grep "ERROR\|WARNING"

# Check git status (uncommitted changes?)
git status --short

# Find largest markdown files
find . -name "*.md" -exec wc -l {} + | sort -n -k1 -r | head -20

# Check daily sessions accumulation
ls -la .ai/daily/*.md | wc -l
```

### Diagnostic Decision Tree

```
Context >8K tokens?
├─ Yes → Check what's consuming context
│  ├─ Session file large? → Regenerate with ./scripts/session_start.sh
│  ├─ Many daily sessions? → Archive with ./scripts/session_archive.sh
│  ├─ Status files large? → Split into focused files
│  └─ Unknown? → Run full diagnostic: ./scripts/track_context_budget.sh --analyze
│
└─ No → Continue normal operations, monitor dashboard
```

---

## 🎯 Prevention Strategies

### Daily Prevention

1. **Monitor dashboard daily**
   ```bash
   ./scripts/context_dashboard.sh
   ```

2. **Track budget throughout session**
   ```bash
   ./scripts/track_context_budget.sh --session
   ```

3. **Use append-only logs** (never read progress.log)

4. **Check file sizes before commit**
   ```bash
   ./scripts/monitor_file_sizes.sh
   ```

### Weekly Prevention

1. **Run comprehensive health check**
   ```bash
   ./scripts/weekly_health_check.sh
   ```

2. **Archive old sessions**
   ```bash
   ./scripts/session_archive.sh
   ```

3. **Update baselines**
   ```bash
   ./scripts/establish_baselines.sh --force
   ```

4. **Review budget compliance**
   ```bash
   ./scripts/track_context_budget.sh --weekly-report
   ```

---

## 📊 Emergency Metrics

### Track Emergency Frequency

Keep log of emergencies:
```bash
# When emergency occurs
echo "$(date +%Y-%m-%d): Emergency - Level [1/2/3] - Reason: [description]" >> .ai/monitoring/emergencies.log

# Review frequency
cat .ai/monitoring/emergencies.log | wc -l  # Total emergencies
cat .ai/monitoring/emergencies.log | grep "$(date +%Y-%m)" | wc -l  # This month
```

### Target Metrics

- **Emergency Frequency**: <1 per month (target: 0)
- **Time to Resolve**: <15 minutes per emergency
- **Context Reduction**: 30-50% per emergency procedure
- **Work Loss**: 0% (all work saved before emergency procedures)

---

## 🚀 Advanced Emergency Techniques

### Technique: Context Streaming

For very large operations that must continue:

```bash
# Split work into micro-sessions
# Session 1: Planning only (2K tokens)
# Session 2: Implementation part 1 (3K tokens)
# Session 3: Implementation part 2 (3K tokens)
# Session 4: Testing and documentation (2K tokens)

# Each session stays well under limit
```

### Technique: Lazy Loading

Load content only when absolutely needed:

```bash
# Don't do this:
cat docs/guides/*.md  # Loads everything

# Do this:
ls docs/guides/  # See what's available
cat docs/guides/specific_guide.md  # Load only what's needed
```

### Technique: Context Swapping

Swap out less-needed context:

```bash
# Archive current work state
./scripts/checkpoint_session.sh --swap-out

# Load different context
./scripts/session_start.sh --context=minimal

# Do work requiring different context

# Restore original context
./scripts/checkpoint_session.sh --swap-in
```

---

## 📚 Emergency Reference Card

### Quick Commands

| Emergency | Command | Time |
|-----------|---------|------|
| Check Status | `./scripts/context_dashboard.sh` | 5s |
| Quick Reduction | `./scripts/emergency_context_reduce.sh` | 2m |
| Checkpoint | `./scripts/checkpoint_session.sh` | 1m |
| Hard Reset | `./scripts/session_start.sh --force-reset` | 30s |
| Archive All | `./scripts/session_archive.sh --force` | 1m |

### Emergency Contacts

- **Documentation**: `docs/guides/CONTEXT_BUDGET_GUIDE.md`
- **Operations Guide**: `CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md`
- **Health Check**: `./scripts/weekly_health_check.sh`
- **Monitoring**: `.ai/monitoring/` directory

---

## 🎓 Training Scenarios

### Scenario 1: Slow Context Creep

**Situation**: Context gradually increased from 5K to 9K over 2 hours

**Response**:
1. Identify: Run diagnostic to find cause
2. Act: Apply appropriate reduction technique
3. Prevent: Implement monitoring for early detection

### Scenario 2: Sudden Context Spike

**Situation**: Single operation caused context to jump from 6K to 11K

**Response**:
1. Immediate: Hard reset (Procedure C)
2. Investigation: Identify what caused spike
3. Prevention: Add check to prevent recurrence

### Scenario 3: Cannot Reduce Further

**Situation**: Context at 9K, all optimizations applied, still need to continue

**Response**:
1. Accept: Work in micro-sessions
2. Checkpoint: After each small operation
3. Reassess: After completing current critical task

---

## ⚠️ Important Warnings

### DO NOT ❌

1. ❌ **Ignore warnings** - Address issues early
2. ❌ **Skip checkpoints** - Always save before emergency procedures
3. ❌ **Delete files** - Archive instead
4. ❌ **Panic** - Follow procedures calmly
5. ❌ **Continue unchecked** - Monitor budget continuously

### DO ✅

1. ✅ **Act early** - Address warnings before critical
2. ✅ **Save work** - Commit before major changes
3. ✅ **Follow procedures** - Use established protocols
4. ✅ **Document** - Record what happened and why
5. ✅ **Prevent recurrence** - Implement preventive measures

---

**Last Updated**: 2025-10-11
**Version**: 1.0
**Status**: Active emergency procedures

**Remember**: The best emergency is the one that never happens. Monitor proactively, optimize continuously, and maintain healthy context budgets.

**For immediate help**: `./scripts/emergency_context_reduce.sh --help`
