# Docker Secrets Management

This document describes how to manage secrets in Docker environments using the unified secrets management system.

## Overview

The Docker secrets management system provides:
- Secure secret storage using Docker secrets
- Environment variable fallback for development
- Health checks and dependency waiting
- Multi-environment support (dev/prod/test)
- Automated secret validation

## Directory Structure

```
docker/
├── load_secrets_docker.py    # Docker secrets loader
├── entrypoint.sh            # Container entrypoint
├── manage_secrets.sh        # Secrets management script
├── docker-compose.dev.yml   # Development environment
├── docker-compose.prod.yml  # Production environment
└── docker-compose.test.yml  # Testing environment

secrets/
├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── DB_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env
├── SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
├── LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
├── LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
└── LINEAR_PROJECT_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env
```

## Quick Start

1. **Initialize secrets directory:**
   ```bash
   ./docker/manage_secrets.sh init
   ```

2. **Add your real secrets:**
   ```bash
   # Edit the .env files in the secrets/ directory
   vim secrets/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env
   ```

3. **Validate secrets:**
   ```bash
   ./docker/manage_secrets.sh validate
   ```

4. **Build and start services:**
   ```bash
   ./docker/manage_secrets.sh build
   ./docker/manage_secrets.sh start dev
   ```

## Secret Management

### Adding Secrets

1. Create a new `.env` file in the `secrets/` directory
2. Add the secret value to the file
3. Update the appropriate Docker Compose file to include the secret
4. Update the `load_secrets_docker.py` script if needed

### Updating Secrets

1. Edit the `.env` file in the `secrets/` directory
2. Restart the affected services:
   ```bash
   ./docker/manage_secrets.sh stop dev
   ./docker/manage_secrets.sh start dev
   ```

### Removing Secrets

1. Remove the `.env` file from the `secrets/` directory
2. Update the Docker Compose file to remove the secret reference
3. Update the `load_secrets_docker.py` script if needed

## Environment-Specific Configuration

### Development Environment

- Uses Docker Compose with volume mounts for live code changes
- Includes PostgreSQL and Redis for local development
- Secrets are loaded from local files

### Production Environment

- Uses Docker Compose with resource limits
- Includes PostgreSQL and Redis with production settings
- Secrets are loaded from Docker secrets

### Testing Environment

- Uses Docker Compose with test-specific configuration
- Includes test databases and mock services
- Secrets are loaded from test-specific files

## Health Checks

All services include health checks:

- **Application**: HTTP health check on port 8000
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command

## Security Considerations

1. **File Permissions**: Secrets are stored with restrictive permissions (600)
2. **Docker Secrets**: Production secrets are loaded from Docker secrets
3. **Environment Variables**: Development secrets are loaded from environment variables
4. **Network Isolation**: Services are isolated in a dedicated Docker network

## Troubleshooting

### Common Issues

1. **Missing Secrets**
   - Run `./docker/manage_secrets.sh validate` to check for missing secrets
   - Ensure all required secrets are present in the `secrets/` directory

2. **Permission Denied**
   - Run `./docker/manage_secrets.sh init` to set correct permissions
   - Ensure the script has execute permissions

3. **Service Won't Start**
   - Check logs: `./docker/manage_secrets.sh logs dev`
   - Verify all dependencies are running
   - Check health check status

4. **Database Connection Issues**
   - Ensure PostgreSQL is running and accessible
   - Check database credentials in secrets
   - Verify network connectivity

### Debugging

1. **Check service status:**
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. **View logs:**
   ```bash
   ./docker/manage_secrets.sh logs dev
   ```

3. **Execute commands in container:**
   ```bash
   docker exec -it nba-mcp-synthesis-dev bash
   ```

4. **Check secrets:**
   ```bash
   docker exec -it nba-mcp-synthesis-dev env | grep -E "(GOOGLE|ANTHROPIC|DEEPSEEK|OPENAI|DB|SLACK|LINEAR)_"
   ```

## Best Practices

1. **Never commit secrets to version control**
2. **Use different secrets for different environments**
3. **Regularly rotate secrets**
4. **Monitor secret usage and access**
5. **Use least privilege principle for secret access**
6. **Implement proper logging and auditing**
7. **Test secret changes in development first**
8. **Use Docker secrets for production deployments**
9. **Implement proper backup and recovery procedures**
10. **Regularly review and update security policies**


