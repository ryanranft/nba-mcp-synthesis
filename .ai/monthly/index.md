# Monthly Summaries Index

**Purpose**: Navigate monthly summary rollups
**Last Updated**: 2025-10-11
**Retention**: 3 months local, then archive to S3

---

## 📁 Directory Contents

### Templates
- **[template.md](template.md)** - Template for creating monthly summaries

### Active Summaries
*Monthly summary files are gitignored and created manually at month-end*

**Current summaries will appear here when created**:
- Format: `YYYY-MM-summary.md`
- Location: `.ai/monthly/`
- Tracked: No (gitignored)

---

## 🔄 Monthly Workflow

### Create Monthly Summary
```bash
# Create from template
cp .ai/monthly/template.md .ai/monthly/$(date +%Y-%m)-summary.md
vim .ai/monthly/$(date +%Y-%m)-summary.md
```

### List Summaries
```bash
ls -la .ai/monthly/*.md | grep -v template | grep -v index
```

### Archive Old Summaries
```bash
./scripts/session_archive.sh --monthly     # Include monthly in archive
./scripts/session_archive.sh --to-s3       # Archive to S3
```

---

## 📊 Summary Management

### Retention Policy
- **Active**: Current month + last 3 months
- **Archive**: Moved to `.ai/archive/` after 3 months
- **S3 Backup**: Optional upload for long-term storage
- **Cleanup**: Manual or via archive scripts

### Summary Frequency
- **Typical**: 1 summary per month
- **Format**: Structured using template.md
- **Content**: High-level progress, decisions, metrics

---

## 📈 What to Include

### Key Sections
- Executive summary (2-3 sentences)
- Completed sprints and deliverables
- Major milestones achieved
- Technical highlights
- Metrics dashboard
- Next month preview

### Data Sources
- Daily session files (`.ai/daily/`)
- Project status files (`project/status/`)
- Git commit history
- Progress logs (`project/tracking/`)

---

## 🎯 Context Optimization

**Token Usage**:
- This index: ~20 tokens
- Individual summary: 300-600 tokens
- Gitignored: Never loaded unless explicitly requested

**Best Practice**: Reference monthly summaries for strategic context, not daily details

---

## 📚 Related Files

- **[../current-session.md](../current-session.md)** - Daily session state
- **[../daily/](../daily/)** - Detailed daily session logs
- **[../index.md](../index.md)** - Main session management guide
- **[template.md](template.md)** - Monthly summary template

---

**Note**: Monthly summaries capture strategic progress. For tactical details, see daily session logs.
