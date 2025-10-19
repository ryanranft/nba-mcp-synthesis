# Git History Scrubbing Guide

**Purpose**: Remove Google Cloud IDs from Git history  
**Created**: 2025-10-18  
**Based On**: Previous successful scrub (commit 9e4ed46)

---

## Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Run the automated scrubbing script
./scripts/scrub_google_cloud_ids.sh
```

This script will:
- ✅ Create automatic backup
- ✅ Scrub all Google Cloud IDs from history
- ✅ Use BFG if available (faster) or git filter-branch (slower)
- ✅ Clean up refs and run garbage collection
- ✅ Verify removal

### Option 2: Manual Process

If you prefer manual control, follow these steps:

#### Step 1: Create Backup

```bash
# Full repository backup
cp -r /Users/ryanranft/nba-mcp-synthesis /Users/ryanranft/nba-mcp-synthesis-backup-$(date +%Y%m%d)
```

#### Step 2: Choose Method

**Method A: BFG Repo-Cleaner (Fastest)**

```bash
# Install BFG
brew install bfg

# Create replacement file
cat > replacements.txt << 'EOF'
${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}==>${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}==>${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}
${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}==>${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
EOF

# Clone as mirror
cd ..
git clone --mirror nba-mcp-synthesis nba-mcp-synthesis-mirror.git
cd nba-mcp-synthesis-mirror.git

# Run BFG
bfg --replace-text ../replacements.txt

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Push changes
git push

# Return to original repo
cd ../nba-mcp-synthesis
git fetch origin
git reset --hard origin/main
```

**Method B: git filter-branch (Slower but Always Available)**

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Remove specific files from history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch BILLING_REPORT_20251018.md billing_report_20251018.json' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up refs
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

#### Step 3: Verify Removal

```bash
# Search for any remaining occurrences
git log --all -S "${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}"
git log --all -S "${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}"

# Should return no results
```

#### Step 4: Force Push

```bash
# WARNING: This rewrites history on GitHub!
git push origin --force --all
git push origin --force --tags
```

---

## Files Affected

These files currently contain Google Cloud IDs:

| File | Occurrences | Action |
|------|-------------|--------|
| `BILLING_SETUP_STATUS.md` | 10 | Replace or remove |
| `docs/BIGQUERY_BILLING_SETUP.md` | 21 | Replace or remove |
| `BILLING_QUICK_REFERENCE.md` | 7 | Replace or remove |
| `BILLING_REPORT_20251018.md` | 4 | Remove from history |
| `billing_report_20251018.json` | 3 | Remove from history |
| `scripts/check_gemini_costs.py` | 1 | Replace with env var |

**Total**: 46 occurrences across 6 files, 4 commits

---

## Replacement Patterns

Use these environment variables instead of hardcoded IDs:

```bash
# Instead of: ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
# Use: ${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}

# Instead of: ${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}
# Use: ${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}

# Instead of: ${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
# Use: ${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
```

### Create .env.google_cloud (Already in .gitignore)

```bash
# This file should NOT be committed
cat > .env.google_cloud << 'EOF'
GOOGLE_CLOUD_PROJECT_ID_PRIMARY=${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}
GOOGLE_CLOUD_PROJECT_ID_SECONDARY=${GOOGLE_CLOUD_PROJECT_ID_SECONDARY}
GOOGLE_CLOUD_BILLING_ACCOUNT_ID=${GOOGLE_CLOUD_BILLING_ACCOUNT_ID}
EOF

# Verify it's ignored
git check-ignore .env.google_cloud  # Should match
```

---

## Verification Checklist

After scrubbing, verify these items:

### 1. History is Clean
```bash
# No results should be found
git log --all --source --full-history -S "${GOOGLE_CLOUD_PROJECT_ID_PRIMARY}"
git grep "gen-lang-client" $(git rev-list --all)
```

### 2. Repository Still Works
```bash
# Run tests
python3 -m pytest tests/ -v

# Check scripts
python3 scripts/check_gemini_costs.py --check-setup
```

### 3. Security Scans Pass
```bash
# Run security validation
python3 scripts/validate_secrets_security.py

# Check with trufflehog
trufflehog git file://. --only-verified
```

### 4. Documentation Updated
- [ ] Files use environment variables
- [ ] .env.google_cloud created (not committed)
- [ ] README updated with setup instructions
- [ ] Security audit report updated

---

## Post-Scrub Actions

### For Solo Developer (You)

1. **Force push to GitHub**:
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

2. **Update any local clones on other machines**:
   ```bash
   # On other machines, you'll need to reset
   git fetch origin
   git reset --hard origin/main
   ```

### For Team Repository (If Applicable)

1. **Notify all collaborators BEFORE force pushing**:
   - Email/Slack: "Git history will be rewritten at [TIME]"
   - Provide these instructions

2. **After force push, collaborators must**:
   ```bash
   # Do NOT merge or pull - instead reset
   git fetch origin
   git reset --hard origin/main
   
   # Or re-clone entirely
   rm -rf nba-mcp-synthesis
   git clone [repo-url]
   ```

3. **Update any open pull requests**:
   - They will need to be rebased
   - Coordinate timing

---

## Troubleshooting

### Issue: "refusing to update checked out branch"

```bash
# You're in a bare repository or have detached HEAD
git checkout main
git reset --hard origin/main
```

### Issue: "remote: error: GH013: Repository rule violations"

GitHub's push protection detected secrets. This means:
- The scrubbing was incomplete
- Re-run the scrubbing process
- Verify with: `git log --all -S "sensitive-string"`

### Issue: "fatal: ambiguous argument 'refs/original'"

The refs were already cleaned. This is safe to ignore.

### Issue: Files disappeared after scrubbing

If you used Method B (remove files), they're gone from history. To restore:
- Manually recreate them with placeholders
- Or recover from your backup

---

## Cost of Not Scrubbing

If you choose not to scrub history:

**Risks**:
- ⚠️ Project IDs remain publicly visible (MEDIUM risk)
- ⚠️ Billing account ID remains publicly visible (MEDIUM risk)
- ⚠️ Could be used for reconnaissance
- ⚠️ Could be combined with other leaked data

**Mitigations**:
- ✅ Enable Google Cloud billing alerts
- ✅ Monitor activity logs regularly
- ✅ Rotate identifiers if suspicious activity detected
- ✅ Keep API keys and secrets properly secured

---

## Previous Successful Scrubs

This repository has been successfully scrubbed before:

**Commit 9e4ed46** (October 2025)
- Removed hardcoded AWS credentials
- Used git filter-branch method
- Force pushed to GitHub
- No issues encountered

**Reference**: See `SECURITY_DEPLOYMENT_COMPLETE.md` for details

---

## Related Documentation

- [SECURITY_AUDIT_20251018.md](SECURITY_AUDIT_20251018.md) - Current security audit
- [SECURITY_DEPLOYMENT_COMPLETE.md](SECURITY_DEPLOYMENT_COMPLETE.md) - Previous scrubbing
- [docs/SECURITY_SCANNING_GUIDE.md](docs/SECURITY_SCANNING_GUIDE.md) - Emergency procedures

---

## Support

If you encounter issues:

1. Check your backup: `ls -la ../nba-mcp-synthesis-backup-*`
2. Review the security guides mentioned above
3. Test in backup before applying to main repository

---

**Last Updated**: 2025-10-18  
**Script Location**: `scripts/scrub_google_cloud_ids.sh`  
**Automated**: ✅ Yes

