# Security Protocol Deployment Plan
## NBA Simulator AWS Project

**Date**: October 17, 2025
**Source**: nba-mcp-synthesis
**Target**: nba-simulator-aws
**Status**: Ready to Deploy

---

## 📋 Pre-Deployment Assessment

### ✅ Source Project (nba-mcp-synthesis)
- ✅ Security protocol fully implemented
- ✅ All tools installed and tested
- ✅ GitHub Actions workflows active
- ✅ Pre-commit hooks configured
- ✅ S3 validation working
- ✅ Documentation complete

### ✅ Target Project (nba-simulator-aws)
- ✅ Project exists: `/Users/ryanranft/nba-simulator-aws`
- ✅ Git repository initialized
- ✅ Has `.env` file (will be removed)
- ✅ Has `.env.example` (will be preserved)
- ❌ No `.github/workflows` directory (will be created)
- ❌ No pre-commit setup (will be added)
- ❌ No security scanning (will be deployed)

### ✅ Hierarchical Secrets Structure
Already supports nba-simulator-aws:
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/
  big_cat_bets_simulators/NBA/
    nba-simulator-aws/
      .env.nba_simulator_aws.production/
      .env.nba_simulator_aws.development/
      .env.nba_simulator_aws.test/
```

---

## 🚀 Deployment Plan

### Phase 1: Copy Security Files

**Configuration Files**:
- `.pre-commit-config.yaml`
- `.git-secrets-patterns`
- `pyproject.toml` (Bandit config)

**Scripts**:
- `scripts/setup_security_scanning.sh`
- `scripts/validate_secrets_security.py`
- `scripts/test_security_scanning.py`
- `scripts/validate_s3_public_access.py`

**Documentation**:
- `docs/SECURITY_SCANNING_GUIDE.md`

**GitHub Actions**:
- `.github/workflows/secrets-scan.yml`
- `.github/workflows/ci-cd.yml` (or merge security job)

### Phase 2: Update Project Files

**`.gitignore`**: Add security patterns
```gitignore
# Security scanning
.secrets.baseline
security_audit_report.md
s3_security_audit_report.md

# Environment files
.env
.env.*
!.env.example
```

**`requirements.txt`**: Add security packages
```
pre-commit>=3.6.0
detect-secrets>=1.4.0
bandit>=1.7.5
boto3>=1.26.0
```

**`README.md`**: Add security section (optional)

### Phase 3: Install & Configure

1. **Install security tools**:
   ```bash
   cd /Users/ryanranft/nba-simulator-aws
   ./scripts/setup_security_scanning.sh
   ```

2. **Initialize git-secrets**:
   ```bash
   git secrets --install
   git secrets --register-aws
   ```

3. **Generate baseline**:
   ```bash
   detect-secrets scan > .secrets.baseline
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Phase 4: Clean Up Secrets

1. **Backup existing .env**:
   ```bash
   cp .env .env.backup.$(date +%Y%m%d)
   ```

2. **Remove .env file**:
   ```bash
   rm .env
   ```

3. **Verify hierarchical secrets**:
   ```bash
   ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/.env.nba_simulator_aws.production/
   ```

### Phase 5: Validate Security

1. **Run security validation**:
   ```bash
   python3 scripts/validate_secrets_security.py
   ```

2. **Test S3 access**:
   ```bash
   python3 scripts/validate_s3_public_access.py
   ```

3. **Test pre-commit hooks**:
   ```bash
   pre-commit run --all-files
   ```

4. **Test tool installation**:
   ```bash
   python3 scripts/test_security_scanning.py
   ```

### Phase 6: Commit & Push

1. **Review changes**:
   ```bash
   git status
   git diff .gitignore
   git diff requirements.txt
   ```

2. **Stage security files**:
   ```bash
   git add .pre-commit-config.yaml .git-secrets-patterns pyproject.toml
   git add .github/workflows/
   git add scripts/setup_security_scanning.sh scripts/validate_*
   git add docs/SECURITY_SCANNING_GUIDE.md
   git add .gitignore requirements.txt
   ```

3. **Commit**:
   ```bash
   git commit -m "feat: implement comprehensive security scanning

- Added pre-commit hooks (detect-secrets, bandit)
- Implemented S3 public access validation
- Enhanced GitHub Actions with security workflows
- Removed .env file (use hierarchical secrets)
- Added security documentation

Security layers:
- Layer 1: Pre-commit hooks (local)
- Layer 2: CI/CD scanning (GitHub Actions)
- Layer 3: Hierarchical secrets management
- Layer 4: S3 public access validation
"
   ```

4. **Push**:
   ```bash
   git push origin main
   ```

---

## 🎯 Automated Deployment

**Use the deployment script**:
```bash
cd /Users/ryanranft/nba-mcp-synthesis
./scripts/deploy_security_to_simulator.sh
```

This script automates all the steps above:
- ✅ Verifies source files
- ✅ Verifies target project
- ✅ Backs up existing .env
- ✅ Copies all security files
- ✅ Updates .gitignore and requirements.txt
- ✅ Installs security tools
- ✅ Runs initial validation
- ✅ Provides git status summary

---

## ✅ Success Criteria

After deployment, the nba-simulator-aws project should have:

- ✅ Pre-commit hooks active
- ✅ GitHub Actions security workflows
- ✅ S3 validation script working
- ✅ No .env file in repository
- ✅ All secrets in hierarchical structure
- ✅ Security documentation available
- ✅ Clean git history (no secrets)
- ✅ All security tests passing

---

## 🔍 Validation Checklist

### Local Validation
```bash
cd /Users/ryanranft/nba-simulator-aws

# 1. Pre-commit hooks installed
[ -f .git/hooks/pre-commit ] && echo "✅ Pre-commit hooks" || echo "❌ No hooks"

# 2. Security tools installed
git secrets --version && echo "✅ git-secrets" || echo "❌ git-secrets"
detect-secrets --version && echo "✅ detect-secrets" || echo "❌ detect-secrets"
pre-commit --version && echo "✅ pre-commit" || echo "❌ pre-commit"

# 3. Scripts executable
[ -x scripts/validate_secrets_security.py ] && echo "✅ Scripts" || echo "❌ Scripts"

# 4. No .env file
[ ! -f .env ] && echo "✅ No .env" || echo "❌ .env exists"

# 5. Baseline exists
[ -f .secrets.baseline ] && echo "✅ Baseline" || echo "❌ No baseline"
```

### CI/CD Validation
```bash
# 1. Workflows exist
[ -f .github/workflows/secrets-scan.yml ] && echo "✅ Workflows" || echo "❌ No workflows"

# 2. GitHub Actions will run on next push
git log --oneline -1
```

### Secrets Validation
```bash
# 1. Hierarchical secrets directory exists
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/.env.nba_simulator_aws.production/

# 2. Run security scan
python3 scripts/validate_secrets_security.py

# 3. Check S3 access
python3 scripts/validate_s3_public_access.py
```

---

## 🚨 Important Notes

### 1. Existing .env File
- **Will be backed up** to `.env.backup.TIMESTAMP`
- **Will be removed** from repository
- **Secrets should be moved** to hierarchical structure

### 2. GitHub Secrets
Ensure these secrets are configured in GitHub repo settings:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (optional, defaults to us-east-1)

### 3. S3 Buckets
The S3 validator will check buckets mentioned in:
- Environment variables with pattern `*_BUCKET_*`
- Environment variables with pattern `S3_*`

### 4. Unified Secrets Manager
If nba-simulator-aws doesn't have `mcp_server/unified_secrets_manager.py`, it will be copied from nba-mcp-synthesis.

---

## 📚 Documentation

After deployment, developers should read:
1. **`docs/SECURITY_SCANNING_GUIDE.md`** - Complete security guide
2. **Security section in README.md** - Quick reference
3. **`.pre-commit-config.yaml`** - Hook configuration
4. **`.git-secrets-patterns`** - Custom patterns

---

## 🔧 Troubleshooting

### Issue: pre-commit fails to install
**Solution**:
```bash
pip install --upgrade pre-commit
pre-commit clean
pre-commit install
```

### Issue: git-secrets not found
**Solution**:
```bash
# macOS
brew install git-secrets

# Linux
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
sudo make install
```

### Issue: S3 validation fails
**Solution**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Set credentials if needed
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Re-run validation
python3 scripts/validate_s3_public_access.py
```

### Issue: Secrets not loading
**Solution**:
```bash
# Verify hierarchical structure
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/.env.nba_simulator_aws.production/

# Check permissions
chmod 700 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/.env.nba_simulator_aws.production/
chmod 600 /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/.env.nba_simulator_aws.production/*.env
```

---

## 🎉 Post-Deployment

After successful deployment:

1. ✅ **Test locally**: Commit a test file to verify hooks work
2. ✅ **Test CI/CD**: Push to GitHub and verify Actions pass
3. ✅ **Validate S3**: Ensure all buckets are private
4. ✅ **Update team**: Share security guide with team
5. ✅ **Monitor**: Check GitHub Security tab for alerts

---

**Status**: ✅ Ready to deploy with automated script!

