# Basketball Reference Integration

## Overview
Basketball Reference connector enables scraping and importing NBA statistics from Basketball-Reference.com.

## Configuration

### Environment Variables
```bash
BR_API_KEY=your_api_key_here
BR_RATE_LIMIT=60  # requests per minute
BR_CACHE_TTL=3600  # seconds
```

## Usage

### Fetching Player Stats
```python
from mcp_server.basketball_reference import BasketballReferenceConnector

br = BasketballReferenceConnector(api_key=os.getenv("BR_API_KEY"))
player_stats = await br.get_player_stats(player_name="LeBron James", season="2023-24")
```

### Fetching Team Stats
```python
team_stats = await br.get_team_stats(team_name="Lakers", season="2023-24")
```

## Testing
Run tests with:
```bash
pytest tests/test_basketball_reference.py
```

## Features
- Player statistics scraping
- Team performance metrics
- Historical data access
- Advanced metrics calculation
- Automatic rate limiting
- Response caching

## Dependencies
- beautifulsoup4>=4.12.0
- requests>=2.31.0
- pandas>=2.1.0

## Rate Limiting
Respects Basketball-Reference's rate limits automatically.

