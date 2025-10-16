# NBA MCP Server API Reference API Documentation

## Overview
Complete API reference for NBA MCP Server

## Authentication
## API Key Authentication

All API requests require authentication using an API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.nba-mcp-server.com/endpoint
```

## Rate Limiting

API requests are rate limited:
- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1000 requests/hour
- **Enterprise**: Custom limits

## Security

- All communications use HTTPS
- API keys are encrypted
- Regular security audits
- GDPR compliant

## Endpoints
## Core Endpoints

### Formula Calculations
- `POST /api/formulas/calculate` - Calculate formulas
- `GET /api/formulas/list` - List available formulas
- `POST /api/formulas/validate` - Validate formula syntax

### Data Access
- `GET /api/data/players` - Get player data
- `GET /api/data/games` - Get game data
- `GET /api/data/teams` - Get team data

### Analysis Tools
- `POST /api/analysis/statistical` - Statistical analysis
- `POST /api/analysis/predictive` - Predictive analytics
- `GET /api/analysis/visualizations` - Generate visualizations

### Monitoring
- `GET /api/monitoring/status` - System status
- `POST /api/monitoring/metrics` - Record metrics
- `GET /api/monitoring/reports` - Performance reports

## Parameters
## Common Parameters

### Formula Parameters
- `formula_name`: Name of the formula to calculate
- `parameters`: Dictionary of formula parameters
- `options`: Additional calculation options

### Data Parameters
- `limit`: Maximum number of results
- `offset`: Number of results to skip
- `filters`: Data filtering criteria
- `sort`: Sorting criteria

### Analysis Parameters
- `analysis_type`: Type of analysis to perform
- `data`: Input data for analysis
- `options`: Analysis configuration options

## Parameter Validation

All parameters are validated using Pydantic models:
- **Type Checking**: Automatic type validation
- **Range Validation**: Min/max value checking
- **Format Validation**: String format validation
- **Required Fields**: Mandatory parameter checking

## Response Formats
## Standard Response Format

All API responses follow a consistent format:

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456",
    "version": "1.0.0"
  }
}
```

## Error Response Format

Error responses include detailed error information:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter value",
    "details": {
      "field": "formula_name",
      "value": "invalid_formula"
    }
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Data Formats

- **JSON**: Primary data format
- **CSV**: Export format for data
- **XML**: Legacy format support
- **Binary**: High-performance binary format

## Error Handling
## HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Error Types

### Validation Errors
- Invalid parameter values
- Missing required parameters
- Type mismatches

### Authentication Errors
- Invalid API key
- Expired credentials
- Insufficient permissions

### Rate Limit Errors
- Too many requests
- Quota exceeded
- Throttling applied

### Server Errors
- Internal processing errors
- Database connection issues
- Service unavailable

## Rate Limiting
## Rate Limits

### Free Tier
- **100 requests/hour**
- **1000 requests/day**
- **Basic support**

### Pro Tier
- **1000 requests/hour**
- **10000 requests/day**
- **Priority support**
- **Advanced features**

### Enterprise Tier
- **Custom limits**
- **Unlimited requests**
- **Dedicated support**
- **Custom integrations**

## Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Handling Rate Limits

When rate limits are exceeded:

1. **Wait**: Wait for the reset time
2. **Upgrade**: Upgrade to a higher tier
3. **Optimize**: Reduce request frequency
4. **Cache**: Implement response caching

## Examples
## Python Examples

### Basic Formula Calculation

```python
import requests

# Calculate Player Efficiency Rating
response = requests.post(
    "https://api.nba-mcp-server.com/api/formulas/calculate",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "formula_name": "player_efficiency_rating",
        "parameters": {
            "points": 25,
            "rebounds": 8,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "fgm": 10,
            "fga": 20,
            "ftm": 5,
            "fta": 6
        }
    }
)

result = response.json()
print(f"PER: {result['data']['per']:.2f}")
```

### Data Retrieval

```python
# Get player statistics
response = requests.get(
    "https://api.nba-mcp-server.com/api/data/players",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    params={
        "season": "2023-24",
        "team": "Lakers",
        "limit": 50
    }
)

players = response.json()['data']
for player in players:
    print(f"{player['name']}: {player['points_per_game']} PPG")
```

## JavaScript Examples

### Formula Calculation

```javascript
// Calculate True Shooting Percentage
const response = await fetch('https://api.nba-mcp-server.com/api/formulas/calculate', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    formula_name: 'true_shooting_percentage',
    parameters: {
      points: 25,
      fga: 20,
      fta: 6
    }
  })
});

const result = await response.json();
console.log(`TS%: ${result.data.ts_percentage.toFixed(3)}`);
```
