# Notion Integration

## Overview
Notion connector provides two-way sync between NBA analytics data and Notion databases.

## Configuration

### Environment Variables
```bash
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id
NOTION_VERSION=2022-06-28
```

## Usage

### Creating a Player Database Entry
```python
from mcp_server.notion_connector import NotionConnector

notion = NotionConnector(api_key=os.getenv("NOTION_API_KEY"))
await notion.create_player_page(
    player_name="Stephen Curry",
    stats={"ppg": 29.4, "apg": 6.3, "rpg": 4.5}
)
```

### Syncing Game Results
```python
await notion.sync_game_results(game_data)
```

## Testing
Run tests with:
```bash
pytest tests/test_notion_connector.py
```

## Features
- Player database management
- Game results tracking
- Analysis notes and insights
- Team performance dashboards
- Automated daily sync
- Rich text formatting

## Dependencies
- notion-client>=2.0.0
- requests>=2.31.0

## Setup
1. Create a Notion integration at https://www.notion.so/my-integrations
2. Share your database with the integration
3. Copy integration token to NOTION_API_KEY


