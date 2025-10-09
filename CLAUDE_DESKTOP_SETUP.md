# Claude Desktop MCP Server Setup

## Overview
This guide shows how to configure the NBA MCP Server with Claude Desktop.

## Prerequisites
- Claude Desktop installed
- Python 3.8+ with dependencies installed
- Environment variables configured in `.env`

## Setup Steps

### 1. Locate Claude Desktop Config File

The config file location depends on your OS:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 2. Add MCP Server Configuration

Open the Claude Desktop config file and add the NBA MCP server configuration.

**Option A: Copy from template (Recommended)**

We've provided a template at `claude_desktop_config.json` in this project. You need to:

1. Copy the content from `claude_desktop_config.json`
2. Replace the `${VARIABLE}` placeholders with actual values from your `.env` file
3. Merge it into your Claude Desktop config

**Option B: Manual configuration**

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "python3",
      "args": [
        "/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py"
      ],
      "env": {
        "RDS_HOST": "your-rds-host.rds.amazonaws.com",
        "RDS_PORT": "5432",
        "RDS_DATABASE": "your-database-name",
        "RDS_USERNAME": "your-username",
        "RDS_PASSWORD": "your-password",
        "S3_BUCKET": "your-s3-bucket",
        "S3_REGION": "us-east-1",
        "DEEPSEEK_API_KEY": "your-deepseek-key",
        "ANTHROPIC_API_KEY": "your-anthropic-key"
      }
    }
  }
}
```

**Important:** Replace all the placeholder values with your actual credentials from `.env`.

### 3. Restart Claude Desktop

After saving the config file, restart Claude Desktop completely:
1. Quit Claude Desktop (Cmd+Q on macOS)
2. Reopen Claude Desktop

### 4. Verify Installation

In Claude Desktop, try asking:
- "What MCP tools are available?"
- "List tables in the NBA database"
- "Query the database for player stats"

If configured correctly, Claude will have access to:
- `query_database` - Execute SQL queries
- `list_tables` - List all database tables
- `get_table_schema` - Get schema for specific tables
- `list_s3_files` - List files in S3 bucket

## Available Tools

### query_database
Execute SQL queries on the NBA database.

**Example:**
```
Can you query the database to find the top 10 players by points?
```

### list_tables
List all tables in the NBA database.

**Example:**
```
What tables are available in the NBA database?
```

### get_table_schema
Get the schema for a specific table.

**Example:**
```
What's the schema for the player_stats table?
```

### list_s3_files
List files in the S3 bucket.

**Example:**
```
Show me the first 10 JSON files in the S3 bucket
```

## Troubleshooting

### Server Not Starting

1. **Check Python path:**
   ```bash
   which python3
   ```
   Update the `command` in config if needed.

2. **Check file path:**
   Verify the absolute path to `server_simple.py` is correct.

3. **Check environment variables:**
   Ensure all required variables are set and correct.

4. **Check logs:**
   Claude Desktop logs are usually at:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### Connection Errors

1. **Test connections manually:**
   ```bash
   cd /Users/ryanranft/nba-mcp-synthesis
   python tests/test_connections.py
   ```

2. **Verify credentials:**
   Make sure RDS, S3, and API credentials are valid.

3. **Check network:**
   Ensure you can reach AWS services and API endpoints.

### Tools Not Appearing

1. Verify the config JSON is valid (use a JSON validator)
2. Check that there are no syntax errors
3. Make sure you restarted Claude Desktop after changes
4. Check Claude Desktop logs for errors

## Security Notes

- **Never commit the config file with real credentials to git**
- The config file contains sensitive credentials
- Keep it secure and local only
- Use environment variables or secrets management in production

## Advanced Usage

### Using the Full Server

For more advanced features, you can use the full server implementation:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "python3",
      "args": [
        "/Users/ryanranft/nba-mcp-synthesis/mcp_server/server.py"
      ],
      "env": {
        ...
      }
    }
  }
}
```

This provides additional tools:
- AWS Glue integration
- Slack notifications
- Advanced file operations
- Synthesis actions

### Multiple Servers

You can configure multiple MCP servers:

```json
{
  "mcpServers": {
    "nba-mcp-server": { ... },
    "another-server": { ... }
  }
}
```

## Support

For issues or questions:
1. Check the main README.md
2. Review test results: `python tests/test_connections.py`
3. Check logs in Claude Desktop
4. Verify all dependencies: `pip install -r requirements.txt`