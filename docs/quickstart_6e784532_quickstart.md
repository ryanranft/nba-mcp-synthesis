# NBA MCP Server Complete Documentation Quick Start Quick Start

## Installation
## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for development)

## Installation Methods

### Using pip (Recommended)

```bash
pip install nba-mcp-server
```

### From Source

```bash
git clone https://github.com/nba-mcp-server/nba-mcp-server.git
cd nba-mcp-server
pip install -e .
```

### Using Docker

```bash
docker pull nba-mcp-server:latest
docker run -p 8080:8080 nba-mcp-server
```

## Verification

Test your installation:

```python
import nba_mcp_server
print(nba_mcp_server.__version__)
```

## Basic Usage
## Quick Start

1. **Import the library**:
   ```python
   from nba_mcp_server import NBA_MCP_Server
   ```

2. **Initialize the server**:
   ```python
   server = NBA_MCP_Server()
   ```

3. **Calculate a formula**:
   ```python
   result = server.calculate_formula("per", {
       "points": 25,
       "rebounds": 8,
       "assists": 5
   })
   ```

4. **Access data**:
   ```python
   players = server.get_players(season="2023-24")
   ```

## Configuration

Set up your environment:

```python
# Set API key
os.environ["NBA_API_KEY"] = "your_api_key"

# Configure database
server.configure_database(
    host="localhost",
    port=5432,
    database="nba_data"
)
```

## First Example
## Complete Example

Here's a complete example that demonstrates the core functionality:

```python
from nba_mcp_server import NBA_MCP_Server

# Initialize server
server = NBA_MCP_Server()

# Get player data
player = server.get_player("LeBron James", season="2023-24")

# Calculate Player Efficiency Rating
per = server.calculate_formula("player_efficiency_rating", {
    "points": player["points_per_game"],
    "rebounds": player["rebounds_per_game"],
    "assists": player["assists_per_game"],
    "steals": player["steals_per_game"],
    "blocks": player["blocks_per_game"],
    "turnovers": player["turnovers_per_game"],
    "fgm": player["field_goals_made"],
    "fga": player["field_goals_attempted"],
    "ftm": player["free_throws_made"],
    "fta": player["free_throws_attempted"]
})

print(f"LeBron James PER: {per['per']:.2f}")

# Calculate True Shooting Percentage
ts_percentage = server.calculate_formula("true_shooting_percentage", {
    "points": player["points_per_game"],
    "fga": player["field_goals_attempted"],
    "fta": player["free_throws_attempted"]
})

print(f"LeBron James TS%: {ts_percentage['ts_percentage']:.3f}")
```

## Expected Output

```
LeBron James PER: 25.67
LeBron James TS%: 0.612
```

This example shows how to:
1. Initialize the server
2. Retrieve player data
3. Calculate advanced metrics
4. Display results

## Next Steps
## Continue Learning

1. **Intermediate Tutorial**: Learn advanced features
2. **API Documentation**: Explore API capabilities
3. **Examples**: Study code examples
4. **Community**: Join user community

## Practice Projects

1. **Player Analysis**: Analyze your favorite player
2. **Team Comparison**: Compare team performance
3. **Season Analysis**: Analyze a complete season
4. **Custom Metrics**: Create your own metrics
