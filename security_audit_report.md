# Security Audit Report

Generated: 2025-10-17 15:13:49

## Summary

⚠️  **Found 7 potential security issues**

## 1. Hardcoded Secrets Scan

✅ No hardcoded secrets detected

## 2. Secrets Manager Usage

### Direct os.getenv() Usage (4 files)

These files use `os.getenv()` without importing unified_secrets_manager:

- `mcp_server/config.py`
- `mcp_server/caching_strategy.py`
- `mcp_server/fastmcp_settings.py`
- `mcp_server/unified_configuration_manager.py`

**Action Required**: Import and use `unified_secrets_manager.get_secret()`

### load_dotenv() Usage (3 files)

These files use `load_dotenv()` instead of hierarchical loading:

- `mcp_server/server.py`
- `mcp_server/config.py`
- `mcp_server/server_simple.py`

**Action Required**: Replace with `load_secrets_hierarchical()`

## 3. Orphaned .env Files

✅ No orphaned .env files found

## 4. Recommendations

1. **Use hierarchical secrets structure** for all sensitive data
2. **Import unified_secrets_manager** in all Python files accessing secrets
3. **Run pre-commit hooks** before committing: `pre-commit run --all-files`
4. **Audit permissions** regularly: `./scripts/audit_secret_permissions.sh`
5. **Review .secrets.baseline** for false positives

## 5. Next Steps

```bash
# Fix hardcoded secrets
# Replace with unified_secrets_manager calls

# Re-run validation
python scripts/validate_secrets_security.py

# Run pre-commit checks
pre-commit run --all-files
```