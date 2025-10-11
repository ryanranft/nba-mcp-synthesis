# Daily Sessions Index

**Purpose**: Navigate daily session logs
**Last Updated**: 2025-10-11
**Retention**: 7 days local, then archive to S3

---

## 📁 Directory Contents

### Templates
- **[template.md](template.md)** - Template for creating new daily session logs

### Active Sessions
*Daily session files are gitignored and created on-demand with `./scripts/session_start.sh --new-session`*

**Current sessions will appear here when created**:
- Format: `YYYY-MM-DD-session-N.md`
- Location: `.ai/daily/`
- Tracked: No (gitignored)

---

## 🔄 Session Workflow

### Create New Session File
```bash
./scripts/session_start.sh --new-session
# Creates: .ai/daily/YYYY-MM-DD-session-1.md
```

### List Active Sessions
```bash
ls -la .ai/daily/*.md | grep -v template | grep -v index
```

### Archive Old Sessions
```bash
./scripts/session_archive.sh            # Archive locally
./scripts/session_archive.sh --to-s3    # Archive to S3
```

---

## 📊 Session Management

### Retention Policy
- **Active**: Current day + last 7 days
- **Archive**: Moved to `.ai/archive/` after 7 days
- **S3 Backup**: Optional upload for long-term storage
- **Cleanup**: Automatic via `session_archive.sh`

### Session Frequency
- **Typical**: 1-3 sessions per day
- **Format**: Structured using template.md
- **Content**: Detailed work logs, decisions, issues

---

## 🎯 Context Optimization

**Token Usage**:
- This index: ~20 tokens
- Individual session: 200-500 tokens
- Gitignored: Never loaded unless explicitly requested

**Best Practice**: Don't read old sessions unless needed for specific context

---

## 📚 Related Files

- **[../current-session.md](../current-session.md)** - Compact auto-generated summary
- **[../index.md](../index.md)** - Main session management guide
- **[template.md](template.md)** - Session template structure

---

**Note**: Daily sessions are detailed logs for human reference. AI sessions should use `current-session.md` for compact context.
