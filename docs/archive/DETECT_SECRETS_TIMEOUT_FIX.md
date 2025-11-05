# detect-secrets Timeout Fix - Summary

**Date:** October 26, 2025
**Issue:** detect-secrets scan hung for 4 hours, consuming 100% CPU with 12 multiprocessing workers
**Status:** ✅ Fixed

---

## Problem Analysis

### What Happened
- A `detect-secrets` security scan was triggered at 12:51 PM via Claude Code
- Command: `git show be0dd5c | detect-secrets scan --all-files --`
- The scan spawned 12 Python multiprocessing workers
- Each worker consumed 82-87% CPU
- Process hung for 4+ hours with no timeout protection
- System became unresponsive, fan running at maximum speed

### Root Causes
1. **Incorrect flag usage**: `--all-files` flag scanned entire repository instead of just the commit
2. **No timeout protection**: detect-secrets has no built-in timeout mechanism
3. **Large repository**: nba-simulator-aws has 1758 markdown files (252 MB)
4. **Multiprocessing deadlock**: Workers likely got stuck on large files or complex patterns

### Impact
- **CPU:** 0% idle → 100% utilization
- **Load Average:** 162.41 (normally < 10)
- **Memory:** 94GB used (near maximum)
- **Duration:** 4 hours before manual kill required

---

## Solution Implemented

### 1. Timeout Wrapper Script ✅
**File:** `scripts/detect_secrets_with_timeout.sh`

**Features:**
- Automatic timeout (default: 5 minutes, configurable)
- Progress logging to `/tmp/detect-secrets-scan.log`
- Warning for `--all-files` usage
- Clean process termination (SIGTERM → SIGKILL)
- Helpful error messages and recovery instructions

**Usage:**
```bash
# Default 5-minute timeout
./scripts/detect_secrets_with_timeout.sh -- scan --baseline .secrets.baseline

# Custom timeout
./scripts/detect_secrets_with_timeout.sh --timeout 600 -- scan --all-files

# With logging
./scripts/detect_secrets_with_timeout.sh --log ~/scan.log -- scan mcp_server/
```

**Exit Codes:**
- `0`: No secrets found (success)
- `1`: Secrets detected (normal detect-secrets behavior)
- `124`: Scan timed out (killed after timeout)

### 2. Pre-commit Configuration Update ✅
**File:** `.pre-commit-config.yaml`

**Changes:**
- Added warning comments about `--all-files` flag
- Documented that pre-commit automatically scans only staged files
- Added optional `--max-file-size` parameter suggestion
- Enabled verbose mode for better debugging

**Before:**
```yaml
- id: detect-secrets
  args: ["--baseline", ".secrets.baseline"]
```

**After:**
```yaml
# NOTE: Do NOT use --all-files flag - it scans entire repo and can hang!
# Pre-commit automatically scans only staged files, which is correct behavior.
- id: detect-secrets
  args: ["--baseline", ".secrets.baseline"]
  # Optional: Add --max-file-size if scans are slow
  # args: ["--baseline", ".secrets.baseline", "--max-file-size", "100000"]
  verbose: true
```

### 3. Documentation Updates ✅
**File:** `docs/SECURITY_SCANNING_GUIDE.md`

**Added Sections:**
- **"detect-secrets Taking Too Long or Hanging"**
  - Symptoms checklist
  - Common causes
  - Immediate fix (kill process instructions)
  - Prevention with timeout wrapper
  - Long-term solutions

- **"When to Use --all-files"**
  - ✅ Appropriate use cases
  - ❌ When NOT to use
  - Warning about performance impact

**Key Guidelines:**
```bash
# ✅ GOOD: Scan staged files only (automatic)
git add file.py
git commit -m "message"  # pre-commit runs detect-secrets automatically

# ✅ GOOD: Initial baseline
detect-secrets scan > .secrets.baseline

# ❌ BAD: Using --all-files in pre-commit
detect-secrets scan --all-files  # Scans ENTIRE repo every commit

# ❌ BAD: Piping git show with --all-files
git show <commit> | detect-secrets scan --all-files  # Redundant and slow
```

---

## Testing Results

### Test 1: Help Message ✅
```bash
./scripts/detect_secrets_with_timeout.sh --help
# Output: Detailed usage instructions
```

### Test 2: Dependency Check ✅
```bash
# Installed coreutils for gtimeout command
brew install coreutils
# Result: gtimeout available at /opt/homebrew/bin/gtimeout
```

### Test 3: Real Scan with Timeout ✅
```bash
./scripts/detect_secrets_with_timeout.sh -t 30 -- scan scripts/detect_secrets_with_timeout.sh
# Result: Completed in <1 second, no secrets detected, log created
```

### Test 4: Log File Verification ✅
```bash
cat /tmp/detect-secrets-scan.log
# Shows: Start time, timeout, command, output, end time, exit code
```

---

## Files Modified

| File | Lines Changed | Status |
|------|--------------|---------|
| `scripts/detect_secrets_with_timeout.sh` | +237 (new) | ✅ Created |
| `.pre-commit-config.yaml` | +7, -2 | ✅ Updated |
| `docs/SECURITY_SCANNING_GUIDE.md` | +84, -6 | ✅ Updated |
| `DETECT_SECRETS_TIMEOUT_FIX.md` | +292 (new) | ✅ Created |

**Total:** 4 files, 620 lines added/modified

---

## Prevention Measures

### For Developers
1. **Use timeout wrapper** for manual scans:
   ```bash
   ./scripts/detect_secrets_with_timeout.sh -- scan --baseline .secrets.baseline
   ```

2. **Never use `--all-files`** unless necessary:
   - Only for initial baseline creation
   - Only on small repositories (< 100 files)
   - Always with timeout protection

3. **Check for hanging processes**:
   ```bash
   ps aux | grep detect-secrets
   # Kill if running > 10 minutes
   ```

4. **Monitor system resources**:
   ```bash
   top -l 1 | head -10
   # Check CPU idle% and load average
   ```

### For CI/CD
- Pre-commit hooks automatically scan only staged files (efficient)
- No `--all-files` flag in `.pre-commit-config.yaml`
- Verbose mode enabled for debugging
- Consider adding explicit timeout in GitHub Actions

---

## Lessons Learned

1. **Always add timeout protection** for potentially long-running operations
2. **Understand flag behavior** before using them (--all-files scans ENTIRE repo)
3. **Monitor background processes** - don't let them run unchecked
4. **Document common issues** so others can fix them quickly
5. **Test on small scale** before running on large repositories

---

## Quick Reference

### If detect-secrets Hangs Again

**Immediate Action (< 1 minute):**
```bash
# Find and kill the process
ps aux | grep detect-secrets
kill <PID>
```

**Proper Way to Scan (recommended):**
```bash
# Use timeout wrapper
./scripts/detect_secrets_with_timeout.sh -- scan --baseline .secrets.baseline
```

**For Large Repositories:**
```bash
# Increase timeout to 10 minutes
./scripts/detect_secrets_with_timeout.sh --timeout 600 -- scan --baseline .secrets.baseline

# Or scan in batches
detect-secrets scan mcp_server/ --baseline .secrets.baseline
detect-secrets scan scripts/ --baseline .secrets.baseline
```

**Emergency Kill All:**
```bash
# Nuclear option - kills ALL detect-secrets processes
pkill -9 -f detect-secrets
```

---

## Next Steps

### Recommended (Future Enhancements)
1. Add automatic monitoring script to detect long-running scans
2. Integrate timeout wrapper into pre-commit hooks directly
3. Add metrics/telemetry for scan duration
4. Create GitHub Action with timeout protection
5. Add progress bar for long scans

### Optional
- Investigate detect-secrets performance with large files
- Consider alternative secret scanning tools
- Implement parallel scanning with better resource limits
- Add caching to speed up repeated scans

---

## Support

**If you encounter hanging scans:**
1. Check this document first
2. Use timeout wrapper: `./scripts/detect_secrets_with_timeout.sh`
3. Check documentation: `docs/SECURITY_SCANNING_GUIDE.md`
4. Manual kill instructions above

**For questions:**
- Review: `docs/SECURITY_SCANNING_GUIDE.md`
- Script help: `./scripts/detect_secrets_with_timeout.sh --help`

---

**Status:** ✅ Issue resolved, prevention measures in place, documentation complete.

**Last Updated:** October 26, 2025
