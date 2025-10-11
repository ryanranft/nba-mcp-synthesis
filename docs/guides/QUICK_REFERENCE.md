# NBA MCP Server - Quick Reference Card

## 🚀 Starting the Server

```bash
# Claude Desktop (default)
python -m mcp_server.fastmcp_server

# Production HTTP
python -m mcp_server.fastmcp_server streamable-http

# SSE Mode
python -m mcp_server.fastmcp_server sse

# Via environment variable
export MCP_TRANSPORT=streamable-http
python -m mcp_server.fastmcp_server
```

---

## 🎯 Using Prompts in Claude

```
# Show available queries
Use the "suggest_queries" prompt

# Analyze a team
Use the "analyze_team_performance" prompt with team_name="Lakers" and season="2024"

# Compare players
Use the "compare_players" prompt with player1="LeBron James" and player2="Kevin Durant"

# Analyze a game
Use the "game_analysis" prompt with game_id="12345"
```

---

## 🔧 Available Tools

| Tool | Purpose |
|------|---------|
| `query_database` | Execute SQL queries (SELECT only) |
| `list_tables` | List all database tables |
| `get_table_schema` | Get column definitions for a table |
| `list_s3_files` | List files in S3 data lake |

---

## 📦 Available Resources

| URI Pattern | Description |
|-------------|-------------|
| `s3://{bucket}/{key}` | Fetch S3 file contents |
| `nba://database/schema` | Get complete database schema |

---

## 🏥 Health Endpoints

```bash
# Health check with component status
curl http://localhost:8000/health | jq

# Operational metrics
curl http://localhost:8000/metrics | jq

# Readiness probe
curl http://localhost:8000/ready | jq
```

---

## 🧪 Running Tests

```bash
# Test enhancements (6 tests)
python scripts/test_enhancements.py

# Full test suite (10 tests)
python scripts/overnight_test_suite.py

# All tests should pass: 16/16 ✅
```

---

## 🐳 Docker Commands

```bash
# Build
docker build -t nba-mcp-server .

# Run
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e RDS_HOST=your-host \
  -e RDS_DATABASE=nba_simulator \
  nba-mcp-server

# Health check
docker run --health-cmd="curl -f http://localhost:8000/health || exit 1"
```

---

## ☸️ Kubernetes Quick Deploy

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml

# Check health
kubectl get pods
kubectl logs -f deployment/nba-mcp-server

# Access service
kubectl port-forward svc/nba-mcp-service 8000:80
```

---

## 🔍 Troubleshooting

```bash
# Check server can start
python -m mcp_server.fastmcp_server --help

# Test database connection
python -c "from mcp_server.connectors.rds_connector import RDSConnector; import asyncio; print(asyncio.run(RDSConnector().execute_query('SELECT 1')))"

# Verify prompts loaded
python -c "from mcp_server import fastmcp_server; import asyncio; print(asyncio.run(fastmcp_server.mcp.list_prompts()))"

# Check health endpoint
curl http://localhost:8000/health
```

---

## 📊 Example Queries

```sql
-- Top 10 scorers
SELECT player_name, AVG(points) as ppg
FROM player_stats
WHERE season = 2024
GROUP BY player_name
ORDER BY ppg DESC
LIMIT 10;

-- Team win-loss records
SELECT team, COUNT(*) as wins
FROM games
WHERE season = 2024 AND winner = team
GROUP BY team
ORDER BY wins DESC;

-- Player efficiency
SELECT player_name,
       SUM(points + rebounds + assists) / COUNT(*) as efficiency
FROM player_stats
WHERE season = 2024
GROUP BY player_name
ORDER BY efficiency DESC
LIMIT 20;
```

---

## 🎓 Claude Desktop Config

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
        "S3_BUCKET": "your-s3-bucket"
      }
    }
  }
}
```

---

## 🔐 Environment Variables

```bash
# Database
RDS_HOST=your-rds-endpoint
RDS_PORT=5432
RDS_DATABASE=nba_simulator
RDS_USER=your-username
RDS_PASSWORD=your-password

# S3
S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Server
MCP_TRANSPORT=stdio|sse|streamable-http
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000
FASTMCP_DEBUG=false
FASTMCP_LOG_LEVEL=INFO
```

---

## 📈 Monitoring

```yaml
# Prometheus scrape config
scrape_configs:
  - job_name: 'nba-mcp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

---

## 🎯 Common Tasks

### Add a new prompt
```python
@mcp.prompt()
async def my_new_prompt(param: str) -> list[dict]:
    return [{
        "role": "user",
        "content": {"type": "text", "text": f"Your prompt for {param}"}
    }]
```

### Add a new resource template
```python
@mcp.resource("nba://resource/{id}")
async def my_resource(id: str, ctx: Context) -> str:
    # Fetch and return data
    return json.dumps(data)
```

### Add a new tool
```python
@mcp.tool()
async def my_tool(params: MyParams, ctx: Context) -> MyResult:
    await ctx.info("Starting...")
    # Your logic here
    return MyResult(...)
```

---

## 📚 Documentation

- **Full Guide:** `MCP_ENHANCEMENTS.md`
- **Summary:** `ENHANCEMENTS_COMPLETE.md`
- **This Card:** `QUICK_REFERENCE.md`
- **Setup:** `SETUP_COMPLETE_SUMMARY.md`

---

## ✅ Status Check

```bash
# Quick verification
python -c "
from mcp_server import fastmcp_server
print(f'✓ Tools: {len(fastmcp_server.mcp._tool_manager._tools)}')
print(f'✓ Prompts: {len(fastmcp_server.mcp._prompt_manager._prompts)}')
print(f'✓ Templates: {len(fastmcp_server.mcp._resource_manager._templates)}')
print(f'✓ Routes: {len(fastmcp_server.mcp._custom_starlette_routes)}')
"

# Expected output:
# ✓ Tools: 4
# ✓ Prompts: 4
# ✓ Templates: 2
# ✓ Routes: 3
```

---

**🏀 Ready to analyze NBA data!**
