# Next Steps: Security Scanning Setup

## Quick Start (5 Minutes)

The security scanning infrastructure has been implemented. Follow these steps to activate it:

### 1. Install Security Tools

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Run the automated installer
./scripts/setup_security_scanning.sh

# This will install:
# - git-secrets (secret pattern detection)
# - trufflehog (comprehensive scanning)
# - pre-commit (hook manager)
# - detect-secrets (secret detection)
```

### 2. Verify Installation

```bash
# Test that everything works
python3 scripts/test_security_scanning.py

# Expected output:
# ✅ PASS git-secrets
# ✅ PASS detect-secrets
# ⚠️  PASS trufflehog (optional)
# ✅ PASS pre-commit
# ✅ PASS baseline
# ✅ PASS patterns
```

### 3. Run Initial Validation

```bash
# Check for existing issues
python3 scripts/validate_secrets_security.py

# Review the generated report
cat security_audit_report.md
```

## What Gets Protected

### Pre-commit Hooks (Local)

When you run `git commit`, these checks automatically run:

1. **detect-secrets**: Scans for API keys, passwords, tokens
2. **bandit**: Checks for Python security issues
3. **black**: Ensures code formatting
4. **custom checks**: File sizes, naming conventions

### GitHub Actions (CI/CD)

When you push to GitHub:

1. **trufflehog**: Scans full git history for secrets
2. **git-secrets**: Pattern-based detection
3. **Trivy**: Dependency vulnerabilities
4. **Validation**: Checks secrets manager usage

## Files Created

✅ All configuration files are in place:

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Pre-commit hook configuration |
| `.git-secrets-patterns` | Custom secret patterns |
| `.env.example` | Environment template |
| `scripts/setup_security_scanning.sh` | Automated installer |
| `scripts/validate_secrets_security.py` | Validation script |
| `scripts/test_security_scanning.py` | Test suite |
| `.github/workflows/secrets-scan.yml` | Dedicated secret scanning |
| `.github/workflows/ci-cd.yml` | Enhanced with secret detection |
| `docs/SECURITY_SCANNING_GUIDE.md` | Comprehensive guide |

## Known Issues to Fix

The validation found **15 issues** that should be addressed:

### Critical (Fix before committing)

1. **Hardcoded DeepSeek API key** in `scripts/focused_working_model_workflow.py:196`
2. **Hardcoded Grafana password** in `scripts/generate_production_config.py:362`
3. **Test password** in `mcp_server/security_scanner_advanced.py:495`

### Medium (Clean up)

4. **Orphaned .env files** (5 files) - should be removed
5. **Direct os.getenv()** usage (4 files) - consider refactoring
6. **load_dotenv()** usage (3 files) - consider migrating

## Quick Fix Commands

### Fix Hardcoded Secrets

```bash
# 1. Fix focused_working_model_workflow.py
# Replace line 196 with:
# from mcp_server.unified_secrets_manager import get_secret
# api_key = get_secret('DEEPSEEK_API_KEY')

# 2. Fix generate_production_config.py
# Replace line 362 with placeholder or secrets manager

# 3. Fix security_scanner_advanced.py
# Add comment: # pragma: allowlist secret
# Or use fake value: password = "test_password_not_real"
```

### Remove Orphaned Files

```bash
# Remove old .env files
rm -f .env.backup .env.workflow scripts/.env.workflow

# Keep .env.example (it's tracked)
# Keep .env if it contains real secrets (move to hierarchical structure)
```

## Test Your Setup

### 1. Test Pre-commit Hooks

```bash
# Create a test file with a fake secret
echo 'api_key = "AKIAIOSFODNN7EXAMPLE"' > test_secret.py

# Try to commit it (should be blocked)
git add test_secret.py
git commit -m "test: verify hooks work"

# Expected: Commit should be BLOCKED by detect-secrets

# Clean up
git reset HEAD test_secret.py
rm test_secret.py
```

### 2. Test on Existing Files

```bash
# Run pre-commit on all files
pre-commit run --all-files

# Review any findings
# Fix or add to baseline if false positives
```

### 3. Make Your First Protected Commit

```bash
# Stage security implementation files
git add .pre-commit-config.yaml
git add .git-secrets-patterns
git add .github/workflows/secrets-scan.yml
git add .github/workflows/ci-cd.yml
git add scripts/setup_security_scanning.sh
git add scripts/validate_secrets_security.py
git add scripts/test_security_scanning.py
git add .env.example
git add docs/SECURITY_SCANNING_GUIDE.md
git add README.md
git add requirements.txt
git add .gitignore
git add SECURITY_IMPLEMENTATION_SUMMARY.md
git add NEXT_STEPS_SECURITY.md

# Commit (hooks will run automatically)
git commit -m "feat: implement comprehensive security scanning

- Add pre-commit hooks with detect-secrets and bandit
- Enhance CI/CD with trufflehog and git-secrets
- Create validation and testing scripts
- Add comprehensive documentation
- Update .gitignore and requirements.txt"

# If successful, push to GitHub
git push origin main
```

## Getting Help

If you encounter issues:

### 1. Check Documentation

```bash
# Read the comprehensive guide
cat docs/SECURITY_SCANNING_GUIDE.md

# Check implementation summary
cat SECURITY_IMPLEMENTATION_SUMMARY.md
```

### 2. Run Diagnostics

```bash
# Test all tools
python3 scripts/test_security_scanning.py

# Check current status
python3 scripts/validate_secrets_security.py

# Audit permissions
./scripts/audit_secret_permissions.sh
```

### 3. Common Issues

**"git secrets: command not found"**
```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
./scripts/setup_security_scanning.sh
```

**"detect-secrets: command not found"**
```bash
# Install Python packages
pip3 install pre-commit detect-secrets bandit
```

**"Pre-commit hooks not running"**
```bash
# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

**"Too many false positives"**
```bash
# Update baseline
detect-secrets scan > .secrets.baseline
```

## What Happens Next

### When You Commit

1. Pre-commit hooks run automatically
2. Secrets are detected and blocked
3. You fix issues and retry
4. Commit succeeds when clean

### When You Push to GitHub

1. GitHub Actions start automatically
2. Full secret scanning runs
3. Security checks complete
4. PR can merge if all pass

### Ongoing

1. Hooks run on every commit
2. CI/CD scans every push
3. No secrets reach GitHub
4. Team stays secure

## Success Checklist

- [ ] Ran `./scripts/setup_security_scanning.sh`
- [ ] Verified with `python3 scripts/test_security_scanning.py`
- [ ] Fixed critical hardcoded secrets
- [ ] Removed orphaned .env files
- [ ] Tested pre-commit hooks
- [ ] Made first protected commit
- [ ] Pushed to GitHub successfully
- [ ] Read `docs/SECURITY_SCANNING_GUIDE.md`
- [ ] Team members informed

## Timeline

- **Install tools**: 5 minutes
- **Fix issues**: 15 minutes
- **Test setup**: 5 minutes
- **First commit**: 2 minutes
- **Total**: ~27 minutes

## Ready to Start?

Run the installation script now:

```bash
./scripts/setup_security_scanning.sh
```

Then follow the on-screen instructions!

---

**Questions?** See `docs/SECURITY_SCANNING_GUIDE.md` for detailed documentation.

**Issues?** Run `python3 scripts/test_security_scanning.py` for diagnostics.

**Emergency?** See "Emergency: Secret Leaked" section in the guide.

