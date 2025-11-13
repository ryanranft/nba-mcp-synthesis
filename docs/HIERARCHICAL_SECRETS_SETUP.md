# Hierarchical Secrets Setup - MCP Database Connection

## Purpose

This guide provides step-by-step instructions for setting up hierarchical secrets to connect the NBA MCP server to your local PostgreSQL database. This is a focused, practical guide for resolving the "0 tables" issue with the MCP server.

For comprehensive information about the entire secrets management system, see [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md).

## Quick Start

If your NBA MCP server is returning 0 tables, follow these steps:

### 1. Verify Your Database Connection

First, confirm your PostgreSQL database is accessible:

```bash
# Check PostgreSQL is running
pg_isready

# Verify database exists
psql -l | grep bigcatbets

# Check tables exist
psql -U ryanranft -d bigcatbets -c "\dt nba.*"
```

### 2. Create Hierarchical Secrets Directory

Create the directory structure for WORKFLOW context credentials:

```bash
mkdir -p "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"
```

### 3. Create Credential Files

Create 5 `.env` files with your database connection parameters:

```bash
cd "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"

# Database name
echo "bigcatbets" > RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Username
echo "ryanranft" > RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Password
echo "Threespades" > RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Host
echo "localhost" > RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Port
echo "5432" > RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

### 4. Verify Files Were Created

```bash
ls -la "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"
```

You should see 5 `.env` files.

### 5. Restart Claude Desktop

The MCP server only loads credentials when Claude Desktop starts:

1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. The MCP server will load the new credentials automatically

### 6. Test the Connection

After Claude Desktop restarts, test the connection:

```python
# In Claude Code conversation:
mcp__nba-mcp-server__list_tables()
```

You should now see tables from your `bigcatbets` database instead of 0 tables.

## How It Works

### Architecture Overview

```
Claude Desktop
    ↓ (starts)
nba-mcp-synthesis MCP Server
    ↓ (loads credentials from)
env_helper.py
    ↓ (reads hierarchical variables)
unified_secrets_manager.py
    ↓ (loads from file system)
RDS_*_NBA_MCP_SYNTHESIS_WORKFLOW.env files
    ↓ (creates connection)
RDSConnector → PostgreSQL Database
```

### Environment Variable Resolution

The MCP server looks for credentials in this order:

1. **WORKFLOW context** (production): `RDS_*_NBA_MCP_SYNTHESIS_WORKFLOW`
2. **DEVELOPMENT context**: `RDS_*_NBA_MCP_SYNTHESIS_DEVELOPMENT`
3. **PRODUCTION context**: `RDS_*_NBA_MCP_SYNTHESIS_PRODUCTION`
4. **Old naming convention**: `RDS_*` (deprecated)
5. **Default values**: Hardcoded fallbacks (usually wrong)

By creating WORKFLOW context files, we ensure the MCP server connects to your local database.

### File Naming Convention

Each credential file follows this pattern:

```
{SERVICE}_{RESOURCE_TYPE}_{PROJECT}_{CONTEXT}.env
```

Examples:
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env`

This naming convention ensures:
- No conflicts between projects
- Clear ownership and purpose
- AI assistants can understand context
- Easy to audit and manage

## Troubleshooting

### Still Getting 0 Tables?

**Check 1: Files exist and have content**
```bash
for file in RDS_*_NBA_MCP_SYNTHESIS_WORKFLOW.env; do
  echo "$file: $(cat $file)"
done
```

**Check 2: Claude Desktop fully restarted**
- Use Activity Monitor (macOS) to verify Claude isn't running
- Look for both "Claude" and any Python processes

**Check 3: Database credentials are correct**
```bash
# Test connection manually
psql -U ryanranft -h localhost -p 5432 -d bigcatbets -c "SELECT 1;"
```

**Check 4: MCP server logs**
```bash
# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp-server-nba-mcp-server.log
```

### Wrong Database Name

If you're using a different database name (not `bigcatbets`):

```bash
# Update the database name file
echo "your_database_name" > RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

### Different PostgreSQL Port

If PostgreSQL is running on a non-standard port:

```bash
# Update the port file
echo "5433" > RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

### Remote Database

If connecting to a remote PostgreSQL instance:

```bash
# Update host
echo "your-db-host.example.com" > RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env

# Update port if needed
echo "5432" > RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

## Context Types

The hierarchical system supports three contexts:

### WORKFLOW (Production)

Location:
```
.env.nba_mcp_synthesis.workflow/
```

Use for:
- Production workflows
- MCP server default context
- Automated processes
- Live database connections

### DEVELOPMENT (Local Development)

Location:
```
.env.nba_mcp_synthesis.development/
```

Use for:
- Local development
- Testing changes
- Development databases
- Isolated from production

### TEST (Testing)

Location:
```
.env.nba_mcp_synthesis.test/
```

Use for:
- Automated tests
- Mock credentials
- CI/CD pipelines
- Test databases

## Setting Up Multiple Contexts

If you need different credentials for development vs workflow:

```bash
# Create development context directory
mkdir -p "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development"

cd "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.development"

# Development database credentials
echo "bigcatbets_dev" > RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
echo "dev_user" > RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
echo "dev_password" > RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
echo "localhost" > RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
echo "5432" > RDS_PORT_NBA_MCP_SYNTHESIS_DEVELOPMENT.env
```

## Security Considerations

### File Permissions

Set restrictive permissions on credential files:

```bash
# Directory permissions (owner only)
chmod 700 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"

# File permissions (owner read/write only)
chmod 600 "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"/*.env
```

### Git Ignore

Ensure credentials never go into version control:

```bash
# In nba-mcp-synthesis/.gitignore
/Users/ryanranft/Desktop/++/
.env.*.workflow/
.env.*.development/
.env.*.production/
*.env
```

### Plaintext Warning

These credential files contain plaintext passwords. This is acceptable for:
- Local development
- Single-user systems
- Non-production environments

For production deployments, consider:
- AWS Secrets Manager
- HashiCorp Vault
- Encrypted credential stores

## Integration with Existing System

This setup integrates with the existing nba-mcp-synthesis secrets system:

### Related Files

- **MCP Server Entry Point**: `mcp_server/server_simple.py`
- **Environment Helper**: `mcp_server/env_helper.py`
- **Secrets Manager**: `mcp_server/unified_secrets_manager.py`
- **Database Connector**: `mcp_server/connectors/rds_connector.py`

### Claude Desktop Configuration

Your Claude Desktop config already points to the MCP server:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
      "args": ["/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py"],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "AWS_REGION": "us-east-1",
        "S3_BUCKET": "nba-sim-raw-data-lake"
      }
    }
  }
}
```

No changes to this configuration are needed - the MCP server automatically loads credentials from the hierarchical directory structure.

## Advanced Usage

### Switching Contexts

To switch which context the MCP server uses, you can set environment variables in the Claude Desktop config:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
      "args": ["/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py"],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "NBA_MCP_CONTEXT": "development",
        "AWS_REGION": "us-east-1",
        "S3_BUCKET": "nba-sim-raw-data-lake"
      }
    }
  }
}
```

### Validating Credentials

Test credentials before restarting Claude Desktop:

```bash
# Test database connection
psql -U $(cat RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env) \
     -h $(cat RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env) \
     -p $(cat RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env) \
     -d $(cat RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env) \
     -c "SELECT current_database();"
```

### Backup and Restore

Before making changes, backup your credentials:

```bash
# Backup
cp -r "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow" \
     "/Users/ryanranft/Desktop/++/backups/.env.nba_mcp_synthesis.workflow.$(date +%Y%m%d_%H%M%S)"

# Restore
cp -r "/Users/ryanranft/Desktop/++/backups/.env.nba_mcp_synthesis.workflow.20241112_204530" \
     "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow"
```

## Related Documentation

- **Comprehensive Secrets Guide**: [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Troubleshooting**: [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- **Quick Reference**: In the secrets directory (`++/.../nba-mcp-synthesis/.env.nba_mcp_synthesis.workflow/README.md`)

## Summary

By following this guide, you've:

1. ✅ Created the hierarchical secrets directory structure
2. ✅ Configured 5 credential files with your database connection info
3. ✅ Set up the WORKFLOW context for the MCP server
4. ✅ Fixed the "0 tables" issue with the NBA MCP server

The MCP server now connects to your `bigcatbets` database and can access all tables in the `nba` schema.

## Change Log

- **2024-11-12**: Initial setup - Fixed NBA MCP database connection issue
  - Created WORKFLOW context credentials
  - Documented troubleshooting steps
  - Added quick start guide

---

*This is a practical, focused guide for MCP database connections. For the complete secrets management system, see [SECRETS_MANAGEMENT_GUIDE.md](SECRETS_MANAGEMENT_GUIDE.md).*