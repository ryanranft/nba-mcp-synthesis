# Claude Desktop Testing Guide - Quick Wins Validation

**Date:** October 10, 2025
**Status:** 🎯 Ready to Execute
**Purpose:** Step-by-step guide for testing Quick Wins with Claude Desktop

---

## Overview

This guide provides step-by-step instructions to test all 3 Quick Wins from the Graphiti MCP analysis in Claude Desktop.

**What We're Testing:**
1. ✅ Standardized Response Types (request_id, timestamps, error classification)
2. ✅ Async Semaphore (concurrency limiting with `MCP_TOOL_CONCURRENCY=5`)
3. ✅ Pydantic Validation (automatic parameter validation with security checks)

---

## Step 1: Pre-Flight Checks (5 minutes)

### 1.1 Verify Environment Variables

```bash
# Check critical environment variables
echo "RDS_HOST: $RDS_HOST"
echo "RDS_DATABASE: $RDS_DATABASE"
echo "S3_BUCKET: $S3_BUCKET"
echo "MCP_TOOL_CONCURRENCY: ${MCP_TOOL_CONCURRENCY:-5 (default)}"
```

**Expected:**
- All variables should have values
- `MCP_TOOL_CONCURRENCY` should be 5 (or your custom value)

**If variables are missing:**

```bash
# Add to ~/.zshrc (or ~/.bash_profile)
cat >> ~/.zshrc << 'EOF'

# NBA MCP Environment Variables
export RDS_HOST="your-rds-host.region.rds.amazonaws.com"
export RDS_PORT="5432"
export RDS_DATABASE="nba_simulator"
export RDS_USERNAME="postgres"
export RDS_PASSWORD="your-password"
export S3_BUCKET="your-s3-bucket"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export GLUE_DATABASE="nba_raw_data"

# Quick Wins Configuration
export MCP_TOOL_CONCURRENCY=5
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true

EOF

# Apply changes
source ~/.zshrc

# Verify
echo "RDS_HOST: $RDS_HOST"
```

### 1.2 Verify MCP Server Runs Locally

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Test server initialization (should show Quick Win #2 log)
python -c "
from mcp_server.server import NBAMCPServer
import asyncio

async def test():
    server = NBAMCPServer()
    print(f'✅ Server initialized')
    print(f'✅ Concurrency limit: {server.tool_semaphore._value}')

asyncio.run(test())
"
```

**Expected Output:**
```
MCP tool concurrency limit set to: 5
✅ Server initialized
✅ Concurrency limit: 5
```

**If this fails:**
- Check dependencies: `pip install mcp pydantic asyncpg boto3`
- Check syntax errors in recently modified files
- Review error messages and fix imports

### 1.3 Install Claude Desktop Configuration

```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Run setup script
./setup_claude_desktop.sh
```

**Expected Output:**
```
========================================
Claude Desktop MCP Setup
========================================

✅ Claude Desktop found

📝 Installing NBA MCP Server configuration...
✅ Configuration installed

========================================
✅ Setup Complete!
========================================

Next steps:
1. Restart Claude Desktop (quit and reopen)
2. Look for the MCP tools icon (🔌) in Claude
3. Try a test query:
   'Using the NBA MCP tools, list the available databases'

Configuration file: /Users/ryanranft/Library/Application Support/Claude/claude_desktop_config.json
```

### 1.4 Restart Claude Desktop

1. **Completely quit Claude Desktop:**
   - Press `Cmd+Q` (or File → Quit)
   - Wait 5 seconds to ensure clean shutdown

2. **Reopen Claude Desktop:**
   - Open from Applications folder
   - Wait 10-15 seconds for MCP servers to initialize

3. **Verify MCP Server Connected:**
   - Look for MCP tools indicator (🔌 icon in toolbar or tools panel)
   - Should show "nba-mcp-synthesis" as available server
   - Status should be "Connected" or "Active"

**If MCP server doesn't show up:**
```bash
# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Look for errors like:
# - "Failed to start MCP server"
# - Python import errors
# - Missing environment variables
```

---

## Step 2: Basic Connectivity Tests (5 minutes)

### Test 2.1: Verify MCP Tools Are Available

**Copy-paste this into Claude Desktop:**

```
What MCP tools do you have available? List all the tools from the nba-mcp-synthesis server.
```

**Expected Response:**
Claude should list tools including:
- `query_database` - Execute SQL SELECT queries
- `get_table_schema` - Get table schema information
- `list_tables` - List all database tables
- `list_s3_files` - List S3 bucket files
- `fetch_s3_file` - Fetch S3 file content
- (and others)

**✅ Pass Criteria:**
- Claude responds with list of MCP tools
- Tools include database, S3, file, and action tools
- No error messages about server connection

### Test 2.2: Simple Database Query

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, list all tables in the database.
```

**Expected Response:**
Claude should:
1. Call the `list_tables` tool
2. Show you the list of tables (e.g., games, player_stats, teams, etc.)
3. Tell you how many tables exist

**✅ Pass Criteria:**
- Query executes successfully
- Claude shows table names
- No error messages

**If this fails:**
- Check RDS credentials in environment variables
- Verify RDS host is accessible: `ping your-rds-host.region.rds.amazonaws.com`
- Check database exists: `psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DATABASE -c "SELECT 1"`

---

## Step 3: Quick Win #1 - Standardized Response Types (10 minutes)

### Test 3.1: Success Response Format

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, list all tables in the database.

After you get the result, show me the exact raw response structure you received from the tool. I want to see all the fields including timestamp, request_id, success, message, and data.
```

**Expected Response Structure:**

Claude should show you a response like:
```json
{
  "success": true,
  "message": "Found 8 tables",
  "data": {
    "tables": ["games", "player_stats", "teams", ...],
    "table_count": 8
  },
  "timestamp": "2025-10-10T03:22:25.299112Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**✅ Pass Criteria:**
- [ ] Response has `success: true` field
- [ ] Response has `message` field (human-readable)
- [ ] Response has `data` field with actual results
- [ ] Response has `timestamp` in ISO 8601 format (ends with Z)
- [ ] Response has `request_id` in UUID format
- [ ] All 5 fields are present

**📝 Record Results:**
```
Test 3.1 - Success Response Format: [PASS/FAIL]
Notes: _______________________
```

### Test 3.2: Error Response Format

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute this SQL query:
DROP TABLE games;

Show me the exact error response you received, including all fields like success, error, error_type, timestamp, request_id, and details.
```

**Expected Response Structure:**

Claude should show you an error response like:
```json
{
  "success": false,
  "error": "Invalid parameters: 1 validation error for QueryDatabaseParams\nsql_query\n  Forbidden SQL operation: DROP. Only SELECT queries are allowed.",
  "error_type": "ValidationError",
  "timestamp": "2025-10-10T03:22:25.299112Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "validation_errors": [
      {
        "loc": ["sql_query"],
        "msg": "Forbidden SQL operation: DROP. Only SELECT queries are allowed.",
        "type": "value_error"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Response has `success: false` field
- [ ] Response has `error` field (human-readable error message)
- [ ] Response has `error_type: "ValidationError"`
- [ ] Response has `timestamp` in ISO 8601 format
- [ ] Response has `request_id` in UUID format
- [ ] Response has `details` field with validation error details
- [ ] Details include field location `["sql_query"]`
- [ ] Details mention "Forbidden SQL operation: DROP"

**📝 Record Results:**
```
Test 3.2 - Error Response Format: [PASS/FAIL]
Notes: _______________________
```

### Test 3.3: Request ID Uniqueness

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, I want to test request ID uniqueness:

1. First request: List all tables
2. Second request: List all tables again

Show me both request_ids side by side. They should be different UUIDs.
```

**Expected Response:**

Claude should show:
```
First request_id:  550e8400-e29b-41d4-a716-446655440000
Second request_id: 661f9511-f39c-52e5-b827-557766551111
```

**✅ Pass Criteria:**
- [ ] First request has a valid UUID
- [ ] Second request has a different UUID
- [ ] Both UUIDs are in correct format (8-4-4-4-12 hex digits)

**📝 Record Results:**
```
Test 3.3 - Request ID Uniqueness: [PASS/FAIL]
Notes: _______________________
```

---

## Step 4: Quick Win #2 - Async Semaphore (10 minutes)

### Test 4.1: Check Concurrency Limit in Logs

**Open a terminal and run:**

```bash
# View MCP server logs (in real-time)
tail -f ~/Library/Logs/Claude/mcp*.log | grep -i concurrency
```

**Expected Output:**
```
{"timestamp": "2025-10-10T03:22:25Z", "level": "INFO", "message": "MCP tool concurrency limit set to: 5"}
```

**✅ Pass Criteria:**
- [ ] Log message shows concurrency limit
- [ ] Limit is 5 (or your configured value)
- [ ] Message appears during server startup

**📝 Record Results:**
```
Test 4.1 - Concurrency Limit Logged: [PASS/FAIL]
Configured limit: _______
```

### Test 4.2: Concurrent Requests

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, I want to test concurrency limiting.

Execute these 6 queries as quickly as possible:
1. SELECT COUNT(*) FROM games WHERE season=2020
2. SELECT COUNT(*) FROM games WHERE season=2021
3. SELECT COUNT(*) FROM games WHERE season=2022
4. SELECT COUNT(*) FROM games WHERE season=2023
5. SELECT COUNT(*) FROM games WHERE season=2024
6. SELECT COUNT(*) FROM games WHERE season=2019

Tell me if all queries completed successfully.
```

**Expected Behavior:**
- All 6 queries complete successfully
- With semaphore limit of 5, maximum 5 should run concurrently
- 6th query waits for one of the first 5 to finish

**In terminal, watch logs:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log | grep "Tool executed"
```

**Expected Log Pattern:**
You should see execution logs with timestamps showing staggered completion (not all at exact same time).

**✅ Pass Criteria:**
- [ ] All 6 queries complete successfully
- [ ] No rate limiting errors
- [ ] No database connection pool exhaustion
- [ ] Logs show staggered execution (not simultaneous)

**📝 Record Results:**
```
Test 4.2 - Concurrent Requests: [PASS/FAIL]
All queries succeeded: [YES/NO]
Observed concurrency limit working: [YES/NO]
```

### Test 4.3: Change Concurrency Limit

**In terminal:**

```bash
# Test with different concurrency limit
export MCP_TOOL_CONCURRENCY=3

# Restart Claude Desktop (Cmd+Q, reopen)
# Wait for MCP server to initialize

# Check logs
tail -f ~/Library/Logs/Claude/mcp*.log | grep -i concurrency
```

**Expected Output:**
```
{"message": "MCP tool concurrency limit set to: 3"}
```

**Then in Claude Desktop, repeat Test 4.2 with 6 queries.**

**Expected:**
- Server uses new limit (3)
- Queries still complete successfully
- More staggered execution due to lower limit

**Reset to default:**
```bash
export MCP_TOOL_CONCURRENCY=5
# Restart Claude Desktop
```

**✅ Pass Criteria:**
- [ ] Concurrency limit changes based on environment variable
- [ ] Queries still work with new limit
- [ ] Logs reflect new limit

**📝 Record Results:**
```
Test 4.3 - Configurable Concurrency: [PASS/FAIL]
Successfully changed limit: [YES/NO]
```

---

## Step 5: Quick Win #3 - Pydantic Validation (15 minutes)

### Test 5.1: SQL Injection Prevention

**Test 5.1a: Forbidden Keyword - DROP**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute this SQL:
DROP TABLE games;

Show me the exact error response with all validation details.
```

**Expected Error:**
```json
{
  "success": false,
  "error": "Invalid parameters: ...",
  "error_type": "ValidationError",
  "details": {
    "validation_errors": [
      {
        "loc": ["sql_query"],
        "msg": "Forbidden SQL operation: DROP. Only SELECT queries are allowed.",
        "type": "value_error"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Query is rejected BEFORE execution
- [ ] Error type is "ValidationError"
- [ ] Error mentions "Forbidden SQL operation: DROP"
- [ ] Details show field location ["sql_query"]

**Test 5.1b: Forbidden Keyword - DELETE**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
DELETE FROM games WHERE season=2020;
```

**✅ Pass Criteria:**
- [ ] Query is rejected
- [ ] Error mentions "Forbidden SQL operation: DELETE"

**Test 5.1c: Forbidden Keyword - UPDATE**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
UPDATE games SET home_score=100 WHERE game_id=1;
```

**✅ Pass Criteria:**
- [ ] Query is rejected
- [ ] Error mentions "Forbidden SQL operation: UPDATE"

**Test 5.1d: Forbidden Keyword - INSERT**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
INSERT INTO games VALUES (1, 'LAL', 'BOS');
```

**✅ Pass Criteria:**
- [ ] Query is rejected
- [ ] Error mentions "Forbidden SQL operation: INSERT"

**📝 Record Results:**
```
Test 5.1 - SQL Injection Prevention: [PASS/FAIL]
DROP blocked: [YES/NO]
DELETE blocked: [YES/NO]
UPDATE blocked: [YES/NO]
INSERT blocked: [YES/NO]
```

### Test 5.2: Parameter Range Validation

**Test 5.2a: Negative max_rows**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, I want to test parameter validation.

Execute: SELECT * FROM games
But set max_rows to -10 (negative number).

Show me the validation error.
```

**Expected Error:**
```json
{
  "success": false,
  "error_type": "ValidationError",
  "details": {
    "validation_errors": [
      {
        "loc": ["max_rows"],
        "msg": "ensure this value is greater than or equal to 1",
        "type": "value_error.number.not_ge"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Parameter is rejected
- [ ] Error mentions "greater than or equal to 1"
- [ ] Field location is ["max_rows"]

**Test 5.2b: Excessive max_rows**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
SELECT * FROM games
But set max_rows to 999999 (way too high).

Show me the validation error.
```

**Expected Error:**
```json
{
  "details": {
    "validation_errors": [
      {
        "loc": ["max_rows"],
        "msg": "ensure this value is less than or equal to 10000"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Parameter is rejected
- [ ] Error mentions "less than or equal to 10000"

**📝 Record Results:**
```
Test 5.2 - Parameter Range Validation: [PASS/FAIL]
Negative value blocked: [YES/NO]
Excessive value blocked: [YES/NO]
```

### Test 5.3: Table Name Validation (SQL Injection)

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, get the schema for this table:
games; DROP TABLE users--

Show me the validation error.
```

**Expected Error:**
```json
{
  "success": false,
  "error_type": "ValidationError",
  "details": {
    "validation_errors": [
      {
        "loc": ["table_name"],
        "msg": "string does not match regex"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Table name is rejected
- [ ] Error mentions regex/pattern validation
- [ ] SQL injection attempt prevented

**📝 Record Results:**
```
Test 5.3 - Table Name Validation: [PASS/FAIL]
SQL injection blocked: [YES/NO]
```

### Test 5.4: Path Traversal Prevention

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, list S3 files with prefix:
../../sensitive/data

Show me the validation error.
```

**Expected Error:**
```json
{
  "success": false,
  "error_type": "ValidationError",
  "details": {
    "validation_errors": [
      {
        "loc": ["prefix"],
        "msg": "Path traversal not allowed in prefix"
      }
    ]
  }
}
```

**✅ Pass Criteria:**
- [ ] Prefix is rejected
- [ ] Error mentions "Path traversal not allowed"

**📝 Record Results:**
```
Test 5.4 - Path Traversal Prevention: [PASS/FAIL]
Attack blocked: [YES/NO]
```

### Test 5.5: Valid Queries (No False Positives)

**Test 5.5a: Valid SELECT Query**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
SELECT * FROM games WHERE season=2024 LIMIT 10;
```

**Expected:**
- Query executes successfully
- Returns 10 rows of data
- No validation errors

**✅ Pass Criteria:**
- [ ] Query executes successfully
- [ ] Returns success response
- [ ] Data is returned

**Test 5.5b: Valid WITH Query (CTE)**

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute:
WITH recent_games AS (
  SELECT * FROM games WHERE season=2024 LIMIT 100
)
SELECT COUNT(*) FROM recent_games;
```

**Expected:**
- Query executes successfully (WITH is allowed)
- Returns count
- No validation errors

**✅ Pass Criteria:**
- [ ] WITH query executes successfully
- [ ] Returns count result
- [ ] No false positive rejections

**📝 Record Results:**
```
Test 5.5 - Valid Queries: [PASS/FAIL]
SELECT query works: [YES/NO]
WITH query works: [YES/NO]
No false positives: [YES/NO]
```

---

## Step 6: Combined Integration Test (5 minutes)

### Test 6.1: All Quick Wins Together

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, I want to test all 3 Quick Wins working together:

1. Execute a valid query: SELECT * FROM games LIMIT 5
   - Check: standardized response with request_id and timestamp

2. Execute an invalid query: DROP TABLE games
   - Check: ValidationError with detailed error info

3. Execute these 3 queries concurrently:
   - SELECT COUNT(*) FROM games
   - SELECT COUNT(*) FROM player_stats
   - SELECT COUNT(*) FROM teams
   - Check: concurrency limit respected

Show me the raw responses for each test.
```

**Expected:**
1. Valid query returns success response with all fields
2. Invalid query returns validation error with details
3. Concurrent queries all succeed

**✅ Pass Criteria:**
- [ ] All 3 Quick Wins working simultaneously
- [ ] Valid query has standardized response format
- [ ] Invalid query has validation error with details
- [ ] Concurrent queries respect semaphore limit
- [ ] All responses have timestamps and request IDs

**📝 Record Results:**
```
Test 6.1 - Combined Integration: [PASS/FAIL]
All Quick Wins working: [YES/NO]
No conflicts or issues: [YES/NO]
```

---

## Step 7: Performance Validation (5 minutes)

### Test 7.1: Response Time Overhead

**Copy-paste this into Claude Desktop:**

```
Using the NBA MCP tools, execute this query 3 times:
SELECT * FROM games LIMIT 100;

For each execution, tell me the execution_time from the response data field.
Calculate the average execution time.
```

**Expected:**
- Each query takes ~250-260ms
- Average is consistent (±10ms)
- Overhead from Quick Wins is <5ms

**✅ Pass Criteria:**
- [ ] Queries execute in reasonable time
- [ ] Performance is consistent across runs
- [ ] No noticeable slowdown

**📝 Record Results:**
```
Test 7.1 - Performance Overhead: [PASS/FAIL]
Average execution time: _______ ms
Overhead acceptable: [YES/NO]
```

---

## Final Checklist

### Quick Win #1: Standardized Response Types
- [ ] Test 3.1: Success response format - PASS
- [ ] Test 3.2: Error response format - PASS
- [ ] Test 3.3: Request ID uniqueness - PASS

### Quick Win #2: Async Semaphore
- [ ] Test 4.1: Concurrency limit logged - PASS
- [ ] Test 4.2: Concurrent requests limited - PASS
- [ ] Test 4.3: Configurable via environment - PASS

### Quick Win #3: Pydantic Validation
- [ ] Test 5.1: SQL injection prevention (4 keywords) - PASS
- [ ] Test 5.2: Parameter range validation - PASS
- [ ] Test 5.3: Table name validation - PASS
- [ ] Test 5.4: Path traversal prevention - PASS
- [ ] Test 5.5: Valid queries (no false positives) - PASS

### Integration & Performance
- [ ] Test 6.1: Combined integration test - PASS
- [ ] Test 7.1: Performance overhead acceptable - PASS

---

## Test Results Summary

### Overall Status: [PASS/FAIL]

**Quick Win #1 (Standardized Response Types):**
- Status: ______
- Issues: ______
- Notes: ______

**Quick Win #2 (Async Semaphore):**
- Status: ______
- Issues: ______
- Notes: ______

**Quick Win #3 (Pydantic Validation):**
- Status: ______
- Issues: ______
- Notes: ______

### Issues Encountered

1. Issue: _______________
   - Severity: [CRITICAL/HIGH/MEDIUM/LOW]
   - Resolution: _______________

2. Issue: _______________
   - Severity: [CRITICAL/HIGH/MEDIUM/LOW]
   - Resolution: _______________

### Recommendations

Based on testing:
- _______________
- _______________
- _______________

---

## Next Steps

After completing all tests:

1. **If all tests PASS:**
   - ✅ Mark "Test with Claude Desktop" todo as completed
   - 📝 Create final test results document
   - 🔍 Proceed to Option 3: Analyze more MCP repositories

2. **If any tests FAIL:**
   - 🐛 Document failures in detail
   - 🔧 Fix issues in code
   - 🔄 Re-run failed tests
   - ✅ Once all pass, proceed to next step

---

**🎯 Ready to Start Testing!**

Follow the steps in order, record results in the checkboxes and notes sections, and create a final summary when complete.
