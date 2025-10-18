# Kubernetes Secrets Management

This document describes how to manage secrets in Kubernetes environments using the unified secrets management system.

## Overview

The Kubernetes secrets management system provides:
- Secure secret storage using Kubernetes secrets
- Init container for secret loading
- Multi-environment support (prod/dev/test)
- Network policies for security
- Persistent storage for databases
- Ingress configuration with TLS

## Directory Structure

```
k8s/
├── namespace.yaml           # Namespace definitions
├── secrets-prod.yaml        # Production secrets
├── secrets-dev.yaml         # Development secrets
├── secrets-test.yaml        # Testing secrets
├── init-container.yaml      # Init container configuration
├── deployment.yaml          # Main application deployment
├── database.yaml           # Database deployments
├── ingress.yaml            # Ingress and network policies
├── manage_k8s.sh           # Kubernetes management script
└── README.md               # This documentation

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

1. **Initialize Kubernetes resources:**
   ```bash
   ./k8s/manage_k8s.sh init
   ```

2. **Deploy for production:**
   ```bash
   ./k8s/manage_k8s.sh deploy prod
   ```

3. **Check deployment status:**
   ```bash
   ./k8s/manage_k8s.sh status prod
   ```

4. **View logs:**
   ```bash
   ./k8s/manage_k8s.sh logs prod
   ```

## Secret Management

### Adding Secrets

1. Create a new secret in the appropriate YAML file
2. Base64 encode the secret value
3. Update the secret manifest
4. Apply the changes:
   ```bash
   kubectl apply -f k8s/secrets-prod.yaml
   ```

### Updating Secrets

1. Edit the secret in the YAML file
2. Base64 encode the new value
3. Apply the changes:
   ```bash
   kubectl apply -f k8s/secrets-prod.yaml
   ```
4. Restart the affected pods:
   ```bash
   kubectl rollout restart deployment nba-mcp-synthesis -n nba-mcp-synthesis
   ```

### Removing Secrets

1. Remove the secret from the YAML file
2. Apply the changes:
   ```bash
   kubectl apply -f k8s/secrets-prod.yaml
   ```
3. Restart the affected pods:
   ```bash
   kubectl rollout restart deployment nba-mcp-synthesis -n nba-mcp-synthesis
   ```

## Environment-Specific Configuration

### Production Environment

- Uses `nba-mcp-synthesis` namespace
- Includes PostgreSQL and Redis with persistent storage
- Network policies for security
- Ingress with TLS termination
- Resource limits and requests

### Development Environment

- Uses `nba-mcp-synthesis-dev` namespace
- Includes PostgreSQL and Redis for development
- Less restrictive resource limits
- Development-specific secrets

### Testing Environment

- Uses `nba-mcp-synthesis-test` namespace
- Includes test databases and mock services
- Test-specific secrets with mock values
- Minimal resource requirements

## Init Container

The init container is responsible for:
- Loading secrets from Kubernetes secrets
- Waiting for dependencies (database, Redis)
- Running health checks
- Exporting secrets to shared volume

## Security Considerations

1. **Secrets**: Stored as Kubernetes secrets with base64 encoding
2. **Network Policies**: Restrict network traffic between pods
3. **RBAC**: Role-based access control for secret access
4. **TLS**: Ingress with TLS termination
5. **Non-root**: Containers run as non-root user
6. **Resource Limits**: Prevent resource exhaustion

## Troubleshooting

### Common Issues

1. **Missing Secrets**
   - Check if secrets exist: `kubectl get secrets -n nba-mcp-synthesis`
   - Verify secret values are base64 encoded
   - Check secret references in deployment

2. **Pod Won't Start**
   - Check pod status: `kubectl get pods -n nba-mcp-synthesis`
   - View pod logs: `kubectl logs <pod-name> -n nba-mcp-synthesis`
   - Check init container logs: `kubectl logs <pod-name> -c secrets-loader -n nba-mcp-synthesis`

3. **Database Connection Issues**
   - Ensure PostgreSQL is running: `kubectl get pods -n nba-mcp-synthesis`
   - Check database secrets: `kubectl get secret nba-mcp-synthesis-db-secrets -n nba-mcp-synthesis -o yaml`
   - Verify network policies allow communication

4. **Ingress Issues**
   - Check ingress status: `kubectl get ingress -n nba-mcp-synthesis`
   - Verify TLS certificate: `kubectl get certificate -n nba-mcp-synthesis`
   - Check ingress controller logs

### Debugging

1. **Check pod status:**
   ```bash
   kubectl get pods -n nba-mcp-synthesis
   ```

2. **View pod logs:**
   ```bash
   kubectl logs <pod-name> -n nba-mcp-synthesis
   ```

3. **Execute commands in pod:**
   ```bash
   kubectl exec -it <pod-name> -n nba-mcp-synthesis -- bash
   ```

4. **Check secrets:**
   ```bash
   kubectl get secret nba-mcp-synthesis-secrets -n nba-mcp-synthesis -o yaml
   ```

5. **Check services:**
   ```bash
   kubectl get services -n nba-mcp-synthesis
   ```

6. **Check ingress:**
   ```bash
   kubectl get ingress -n nba-mcp-synthesis
   ```

## Best Practices

1. **Never commit secrets to version control**
2. **Use different secrets for different environments**
3. **Regularly rotate secrets**
4. **Monitor secret usage and access**
5. **Use least privilege principle for secret access**
6. **Implement proper logging and auditing**
7. **Test secret changes in development first**
8. **Use Kubernetes secrets for production deployments**
9. **Implement proper backup and recovery procedures**
10. **Regularly review and update security policies**
11. **Use network policies to restrict traffic**
12. **Implement proper resource limits and requests**
13. **Use persistent volumes for database storage**
14. **Implement proper health checks and probes**
15. **Use TLS for all external communication**


