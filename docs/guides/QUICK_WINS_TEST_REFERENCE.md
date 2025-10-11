# Quick Wins Testing - Quick Reference Card

**Date:** October 10, 2025
**Status:** 🎯 Ready to Test
**Time Required:** ~45 minutes

---

## Setup (5 minutes)

```bash
# 1. Verify environment
echo $RDS_HOST && echo $MCP_TOOL_CONCURRENCY

# 2. Install Claude Desktop config
cd /Users/ryanranft/nba-mcp-synthesis
./setup_claude_desktop.sh

# 3. Restart Claude Desktop
# Cmd+Q, then reopen

# 4. Watch logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

---

## Test Prompts (Copy-Paste Ready)

### Quick Win #1: Standardized Response Types

**Test 1: Success Response**
```
Using the NBA MCP tools, list all tables in the database.
After you get the result, show me the exact raw response structure including timestamp, request_id, success, message, and data.
```

**Expected:**
- ✅ `success: true`
- ✅ `message` (human-readable)
- ✅ `data` (results)
- ✅ `timestamp` (ISO 8601)
- ✅ `request_id` (UUID)

**Test 2: Error Response**
```
Using the NBA MCP tools, execute this SQL query:
DROP TABLE games;

Show me the exact error response with all fields.
```

**Expected:**
- ✅ `success: false`
- ✅ `error` (message)
- ✅ `error_type: "ValidationError"`
- ✅ `timestamp` (ISO 8601)
- ✅ `request_id` (UUID)
- ✅ `details` (validation errors)

**Test 3: Request ID Uniqueness**
```
Using the NBA MCP tools:
1. List all tables (first request)
2. List all tables again (second request)

Compare the request_ids. They should be different.
```

**Expected:**
- ✅ Two different UUIDs

---

### Quick Win #2: Async Semaphore

**Test 1: Check Logs**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log | grep -i concurrency
```

**Expected:**
```
MCP tool concurrency limit set to: 5
```

**Test 2: Concurrent Queries**
```
Using the NBA MCP tools, execute these 6 queries as quickly as possible:
1. SELECT COUNT(*) FROM games WHERE season=2020
2. SELECT COUNT(*) FROM games WHERE season=2021
3. SELECT COUNT(*) FROM games WHERE season=2022
4. SELECT COUNT(*) FROM games WHERE season=2023
5. SELECT COUNT(*) FROM games WHERE season=2024
6. SELECT COUNT(*) FROM games WHERE season=2019

Tell me if all queries completed successfully.
```

**Expected:**
- ✅ All 6 queries complete
- ✅ Max 5 concurrent (check logs)
- ✅ No rate limiting errors

**Test 3: Change Limit**
```bash
export MCP_TOOL_CONCURRENCY=3
# Restart Claude Desktop
# Check logs - should show: "limit set to: 3"
```

---

### Quick Win #3: Pydantic Validation

**Test 1: SQL Injection - DROP**
```
Using the NBA MCP tools, execute:
DROP TABLE games;
```

**Expected:**
- ✅ Rejected with "Forbidden SQL operation: DROP"

**Test 2: SQL Injection - DELETE**
```
Using the NBA MCP tools, execute:
DELETE FROM games WHERE season=2020;
```

**Expected:**
- ✅ Rejected with "Forbidden SQL operation: DELETE"

**Test 3: SQL Injection - UPDATE**
```
Using the NBA MCP tools, execute:
UPDATE games SET home_score=100 WHERE game_id=1;
```

**Expected:**
- ✅ Rejected with "Forbidden SQL operation: UPDATE"

**Test 4: SQL Injection - INSERT**
```
Using the NBA MCP tools, execute:
INSERT INTO games VALUES (1, 'LAL', 'BOS');
```

**Expected:**
- ✅ Rejected with "Forbidden SQL operation: INSERT"

**Test 5: Negative Parameter**
```
Using the NBA MCP tools, execute:
SELECT * FROM games
But set max_rows to -10.

Show me the validation error.
```

**Expected:**
- ✅ Rejected with "greater than or equal to 1"

**Test 6: Excessive Parameter**
```
Using the NBA MCP tools, execute:
SELECT * FROM games
But set max_rows to 999999.

Show me the validation error.
```

**Expected:**
- ✅ Rejected with "less than or equal to 10000"

**Test 7: Table Name Injection**
```
Using the NBA MCP tools, get the schema for this table:
games; DROP TABLE users--

Show me the validation error.
```

**Expected:**
- ✅ Rejected with regex/pattern validation error

**Test 8: Path Traversal**
```
Using the NBA MCP tools, list S3 files with prefix:
../../sensitive/data

Show me the validation error.
```

**Expected:**
- ✅ Rejected with "Path traversal not allowed"

**Test 9: Valid SELECT (No False Positives)**
```
Using the NBA MCP tools, execute:
SELECT * FROM games WHERE season=2024 LIMIT 10;
```

**Expected:**
- ✅ Executes successfully
- ✅ Returns 10 rows

**Test 10: Valid WITH Query (No False Positives)**
```
Using the NBA MCP tools, execute:
WITH recent_games AS (
  SELECT * FROM games WHERE season=2024 LIMIT 100
)
SELECT COUNT(*) FROM recent_games;
```

**Expected:**
- ✅ Executes successfully
- ✅ Returns count

---

## Combined Integration Test

```
Using the NBA MCP tools, test all 3 Quick Wins:

1. Valid query: SELECT * FROM games LIMIT 5
   - Check: standardized response with request_id and timestamp

2. Invalid query: DROP TABLE games
   - Check: ValidationError with details

3. Concurrent queries:
   - SELECT COUNT(*) FROM games
   - SELECT COUNT(*) FROM player_stats
   - SELECT COUNT(*) FROM teams

Show me the raw responses.
```

**Expected:**
- ✅ All 3 Quick Wins working together
- ✅ No conflicts or errors

---

## Performance Check

```
Using the NBA MCP tools, execute 3 times:
SELECT * FROM games LIMIT 100;

Tell me the execution_time for each.
```

**Expected:**
- ✅ ~250-260ms per query
- ✅ Consistent timing
- ✅ <5ms overhead

---

## Troubleshooting

### MCP Server Not Showing
```bash
# Check config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Check logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Restart Claude Desktop
# Cmd+Q, reopen
```

### Environment Variables Missing
```bash
# Add to ~/.zshrc
export RDS_HOST="your-host"
export RDS_DATABASE="nba_simulator"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="your-password"
export S3_BUCKET="your-bucket"
export MCP_TOOL_CONCURRENCY=5

# Apply
source ~/.zshrc

# Restart Claude Desktop
```

### Server Crashes
```bash
# Test locally
python -c "
from mcp_server.server import NBAMCPServer
import asyncio
asyncio.run(NBAMCPServer().__init__())
"

# Check dependencies
pip install mcp pydantic asyncpg boto3

# Check imports
python -c "from mcp_server.responses import success_response"
python -c "from mcp_server.tools.params import QueryDatabaseParams"
```

---

## Quick Checklist

### Setup ✅
- [ ] Environment variables set
- [ ] Claude Desktop config installed
- [ ] Claude Desktop restarted
- [ ] MCP server connected

### Quick Win #1 ✅
- [ ] Success response format correct
- [ ] Error response format correct
- [ ] Request IDs unique

### Quick Win #2 ✅
- [ ] Concurrency limit logged
- [ ] Concurrent requests work
- [ ] Environment variable works

### Quick Win #3 ✅
- [ ] DROP blocked
- [ ] DELETE blocked
- [ ] UPDATE blocked
- [ ] INSERT blocked
- [ ] Negative parameter blocked
- [ ] Excessive parameter blocked
- [ ] Table name injection blocked
- [ ] Path traversal blocked
- [ ] Valid SELECT works
- [ ] Valid WITH works

### Integration ✅
- [ ] All Quick Wins work together
- [ ] Performance acceptable

---

## Success Criteria

**All Quick Wins Pass If:**
- All responses have standardized format
- All security validations work
- Concurrency limiting works
- No false positives on valid queries
- Performance overhead <5ms

---

## Next Steps

**After Testing:**
1. Mark "Test with Claude Desktop" as completed
2. Create final test results summary
3. Proceed to Option 3: Analyze more MCP repositories

---

**🎯 Print this card and keep it handy while testing!**

Total Test Time: ~45 minutes
Expected Result: All tests PASS ✅