# NBA MCP Server - Enhanced Features Documentation

## Overview

The NBA MCP Server has been enhanced with production-ready features based on Model Context Protocol best practices. This document covers all new capabilities added to the FastMCP implementation.

---

## 🎯 New Features

### 1. **Prompts** - Guided Query Templates

Prompts provide pre-built conversation starters that guide users on how to interact with your NBA data.

#### Available Prompts

##### `suggest_queries`
Shows users what NBA data is available and provides example queries.

**Usage in Claude Desktop:**
```
Use the "suggest_queries" prompt to see available NBA queries
```

##### `analyze_team_performance`
Generates a comprehensive team analysis template.

**Parameters:**
- `team_name` (required): NBA team name (e.g., "Lakers", "Warriors")
- `season` (optional): Season year (default: "2024")

**Example:**
```
Use the "analyze_team_performance" prompt with team_name="Lakers" and season="2024"
```

##### `compare_players`
Creates a detailed player comparison template.

**Parameters:**
- `player1` (required): First player name
- `player2` (required): Second player name
- `season` (optional): Season year (default: "2024")

**Example:**
```
Use the "compare_players" prompt with player1="LeBron James" and player2="Kevin Durant"
```

##### `game_analysis`
Provides a template for detailed game analysis.

**Parameters:**
- `game_id` (required): Unique game identifier

---

### 2. **Resource Templates** - Structured Data Access

#### `nba://database/schema`
Returns the complete database schema as a JSON resource.

**Usage:**
```python
# Access via resource URI
schema = await ctx.read_resource("nba://database/schema")
```

**Returns:**
```json
{
  "games": [
    {"name": "game_id", "type": "integer", "nullable": false},
    {"name": "season", "type": "integer", "nullable": false},
    ...
  ],
  "players": [...],
  ...
}
```

---

### 3. **Health Check Endpoints**

Production-ready health monitoring endpoints for load balancers and Kubernetes.

#### `/health` - Comprehensive Health Check

**Method:** GET
**Response:** JSON

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T12:00:00",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "components": {
    "database": {
      "status": "healthy",
      "message": "Connection successful"
    },
    "s3": {
      "status": "healthy",
      "message": "Connection successful"
    }
  }
}
```

**Status Codes:**
- `200` - Healthy or degraded (some components unhealthy)
- `503` - Unhealthy (critical components failing)

#### `/metrics` - Operational Metrics

**Method:** GET
**Response:** JSON with Prometheus-compatible metrics

**Example Response:**
```json
{
  "service": "nba-mcp-server",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "metrics": {
    "queries_total": 1523,
    "errors_total": 12,
    "success_rate": 0.992,
    "queries_per_minute": 25.38
  },
  "timestamp": "2025-10-10T12:00:00"
}
```

#### `/ready` - Kubernetes Readiness Probe

**Method:** GET
**Response:** JSON

**Example Response:**
```json
{
  "ready": true,
  "timestamp": "2025-10-10T12:00:00"
}
```

---

### 4. **Multi-Transport Support**

The server now supports three transport modes:

#### **STDIO** (Default - Claude Desktop)
```bash
python -m mcp_server.fastmcp_server
# or
MCP_TRANSPORT=stdio python -m mcp_server.fastmcp_server
```

#### **StreamableHTTP** (Production/Web)
```bash
python -m mcp_server.fastmcp_server streamable-http
# or
MCP_TRANSPORT=streamable-http python -m mcp_server.fastmcp_server
```

Access at:
- MCP Endpoint: `http://localhost:8000/mcp`
- Health Check: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- Readiness: `http://localhost:8000/ready`

#### **SSE** (Server-Sent Events)
```bash
python -m mcp_server.fastmcp_server sse
# or
MCP_TRANSPORT=sse python -m mcp_server.fastmcp_server
```

Access at: `http://localhost:8000/sse`

---

## 🚀 Deployment Guide

### Development (Claude Desktop)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nba-mcp": {
      "command": "python",
      "args": ["-m", "mcp_server.fastmcp_server"],
      "cwd": "/path/to/nba-mcp-synthesis",
      "env": {
        "RDS_HOST": "your-rds-host",
        "RDS_DATABASE": "nba_simulator",
        "RDS_USER": "your-user",
        "RDS_PASSWORD": "your-password",
        "S3_BUCKET": "your-s3-bucket",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Production (Docker)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000

# Set default transport
ENV MCP_TRANSPORT=streamable-http
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "-m", "mcp_server.fastmcp_server", "streamable-http"]
```

**Build and Run:**
```bash
docker build -t nba-mcp-server .
docker run -p 8000:8000 \
  -e RDS_HOST=your-rds-host \
  -e RDS_DATABASE=nba_simulator \
  -e RDS_USER=your-user \
  -e RDS_PASSWORD=your-password \
  -e S3_BUCKET=your-s3-bucket \
  -e AWS_REGION=us-east-1 \
  nba-mcp-server
```

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nba-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nba-mcp-server
  template:
    metadata:
      labels:
        app: nba-mcp-server
    spec:
      containers:
      - name: nba-mcp
        image: nba-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_TRANSPORT
          value: "streamable-http"
        - name: FASTMCP_HOST
          value: "0.0.0.0"
        - name: FASTMCP_PORT
          value: "8000"
        - name: RDS_HOST
          valueFrom:
            secretKeyRef:
              name: nba-mcp-secrets
              key: rds-host
        # Add other env vars from secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: nba-mcp-service
spec:
  selector:
    app: nba-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 🔐 Authentication Setup (Future)

The FastMCP framework supports OAuth and Bearer token authentication. To enable:

### 1. Create Auth Settings

Create `auth_config.py`:
```python
from mcp.server.auth.settings import AuthSettings

auth_settings = AuthSettings(
    issuer_url="https://auth.yourcompany.com",
    resource_server_url="https://nba-mcp.yourcompany.com",
    required_scopes=["nba:read", "nba:query"],
    service_documentation_url="https://docs.yourcompany.com/nba-mcp"
)
```

### 2. Update Server Configuration

In `fastmcp_server.py`:
```python
mcp = FastMCP(
    name="nba-mcp-fastmcp",
    auth=auth_settings,
    token_verifier=your_token_verifier,  # Implement JWT verification
    # ... other settings
)
```

### 3. Implement Token Verifier

```python
from mcp.server.auth.provider import TokenVerifier

class JWTTokenVerifier(TokenVerifier):
    async def verify(self, token: str) -> dict:
        # Implement JWT verification logic
        # Return user info if valid, raise exception if invalid
        pass
```

---

## 📊 Monitoring Integration

### Prometheus Metrics

The `/metrics` endpoint is compatible with Prometheus scraping.

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'nba-mcp-server'
    static_configs:
      - targets: ['nba-mcp-service:80']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard

Create a dashboard with these queries:
```promql
# Query rate
rate(queries_total[5m])

# Error rate
rate(errors_total[5m])

# Success rate
queries_total - errors_total / queries_total

# Uptime
uptime_seconds
```

---

## 🧪 Testing New Features

### Test Prompts
```bash
# Run test script
python scripts/test_prompts.py
```

### Test Health Endpoints
```bash
# Health check
curl http://localhost:8000/health | jq

# Metrics
curl http://localhost:8000/metrics | jq

# Readiness
curl http://localhost:8000/ready | jq
```

### Test StreamableHTTP Transport
```bash
# Start server
python -m mcp_server.fastmcp_server streamable-http

# In another terminal, test endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "list_tools"}'
```

---

## 📈 Performance Tuning

### Environment Variables

Configure via `.env` or environment:

```bash
# Server settings
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8000
FASTMCP_DEBUG=false
FASTMCP_LOG_LEVEL=INFO

# Database connection pool
RDS_POOL_SIZE=10
RDS_MAX_OVERFLOW=20
RDS_POOL_TIMEOUT=30

# Query limits
MAX_QUERY_ROWS=10000
QUERY_TIMEOUT=30
```

### Resource Limits

For production deployments:
- **Memory**: 512Mi minimum, 1Gi recommended
- **CPU**: 250m minimum, 500m recommended
- **Replicas**: 3+ for high availability

---

## 🔍 Troubleshooting

### Common Issues

#### Health Check Fails
```bash
# Check logs
kubectl logs -f deployment/nba-mcp-server

# Check database connectivity
python -c "from mcp_server.connectors.rds_connector import RDSConnector; \
  import asyncio; \
  asyncio.run(RDSConnector().execute_query('SELECT 1'))"
```

#### Prompts Not Showing in Claude
1. Restart Claude Desktop
2. Check server logs for prompt registration
3. Verify prompts are listed: Use "list prompts" in Claude

#### Transport Mode Issues
```bash
# Verify transport setting
echo $MCP_TRANSPORT

# Check port availability
netstat -an | grep 8000

# Test with curl
curl -v http://localhost:8000/health
```

---

## 📚 Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [NBA MCP Test Suite](./scripts/overnight_test_suite.py)
- [Configuration Guide](./SETUP_COMPLETE_SUMMARY.md)

---

## 🎉 Summary of Enhancements

✅ **4 Prompts** - Guided query templates for common NBA analyses
✅ **3 Health Endpoints** - Production monitoring (/health, /metrics, /ready)
✅ **Multi-Transport Support** - stdio, SSE, StreamableHTTP
✅ **Resource Template** - Database schema as resource
✅ **Improved Error Handling** - Structured logging with context
✅ **Docker Support** - Production-ready containerization
✅ **Kubernetes Ready** - Health probes and service definitions
✅ **Metrics Tracking** - Query counts, error rates, uptime

---

**Next Steps:**
1. Test prompts in Claude Desktop
2. Deploy to production with StreamableHTTP
3. Set up monitoring with Prometheus/Grafana
4. Implement authentication for production use